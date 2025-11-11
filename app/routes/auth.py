from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import User, AuthLocal
from app.security import hash_password, verify_password, is_valid_password, is_adult, make_access_token

# Crear blueprint para autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registro de nuevo usuario
    
    Body JSON esperado:
    {
        "username": "string",
        "email": "string", 
        "password": "string",
        "first_name": "string",
        "last_name": "string",
        "birth_date": "YYYY-MM-DD"
    }
    
    Respuestas:
    201: {"user_uuid": "string"} - Usuario creado exitosamente
    400: {"error": "string"} - Datos faltantes o inválidos
    409: {"error": "string"} - Usuario o email ya existe
    422: {"error": "string"} - Validación fallida (menor de edad, password débil)
    500: {"error": "string"} - Error interno del servidor
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se enviaron datos JSON"}), 400
        
        # Validar campos requeridos
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'birth_date']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({"error": f"Campos requeridos faltantes: {', '.join(missing_fields)}"}), 400
        
        # Extraer datos
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()
        
        # Validar fecha de nacimiento
        try:
            birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        
        # Validar mayoría de edad
        if not is_adult(birth_date):
            return jsonify({"error": "Debe ser mayor de 18 años para registrarse"}), 422
        
        # Validar contraseña
        is_valid, password_message = is_valid_password(password)
        if not is_valid:
            return jsonify({"error": password_message}), 422
        
        # Verificar si el usuario o email ya existen
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return jsonify({"error": "El nombre de usuario ya está en uso"}), 409
            else:
                return jsonify({"error": "El email ya está registrado"}), 409
        
        # Crear hash de la contraseña
        password_hash = hash_password(password)
        
        # Crear usuario
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date
        )
        
        # Agregar a la sesión
        db.session.add(new_user)
        db.session.flush()  # Para obtener el uuid
        
        # Crear autenticación local
        auth_local = AuthLocal(
            user_uuid=new_user.uuid,
            password_hash=password_hash
        )
        
        db.session.add(auth_local)
        db.session.commit()
        
        return jsonify({"user_uuid": str(new_user.uuid)}), 201
    
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El usuario o email ya existe"}), 409
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error en registro: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Iniciar sesión de usuario
    
    Body JSON esperado:
    {
        "username": "string",  # username o email
        "password": "string"
    }
    
    Respuestas:
    200: {"access_token": "string"} - Login exitoso
    400: {"error": "string"} - Datos faltantes
    401: {"error": "string"} - Credenciales inválidas
    500: {"error": "string"} - Error interno del servidor
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se enviaron datos JSON"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Username y password son requeridos"}), 400
        
        # Buscar usuario por username o email
        user = User.query.filter(
            (User.username == username) | (User.email == username.lower())
        ).first()
        
        if not user or not user.is_active:
            return jsonify({"error": "Credenciales inválidas"}), 401
        
        # Verificar que tiene autenticación local
        if not user.auth_local:
            return jsonify({"error": "Credenciales inválidas"}), 401
        
        # Verificar si la cuenta está bloqueada
        if user.auth_local.is_locked:
            return jsonify({"error": "Cuenta bloqueada. Contacte al administrador"}), 401
        
        # Verificar contraseña
        if not verify_password(password, user.auth_local.password_hash):
            # Incrementar intentos fallidos
            user.auth_local.login_attempts += 1
            user.auth_local.last_login_attempt = datetime.utcnow()
            
            # Bloquear cuenta si hay demasiados intentos
            if user.auth_local.login_attempts >= 5:
                user.auth_local.is_locked = True
            
            db.session.commit()
            return jsonify({"error": "Credenciales inválidas"}), 401
        
        # Login exitoso - resetear intentos fallidos
        user.auth_local.login_attempts = 0
        user.auth_local.last_login_attempt = datetime.utcnow()
        db.session.commit()
        
        # Generar token de acceso
        access_token = make_access_token(str(user.uuid))
        
        return jsonify({"access_token": access_token}), 200
    
    except Exception as e:
        current_app.logger.error(f"Error en login: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Cerrar sesión de usuario
    
    Headers esperados:
    Authorization: Bearer <token>
    
    Respuestas:
    200: {"message": "string"} - Logout exitoso
    401: {"error": "string"} - Token inválido o faltante
    """
    try:
        # Obtener token del header Authorization
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token de autorización requerido"}), 401
        
        # En una implementación completa, aquí se invalidaría el token
        # Por ahora solo confirmamos que el token es válido
        from app.security import decode_access_token
        
        token = auth_header.split(' ')[1]
        payload = decode_access_token(token)
        
        # Si llegamos aquí, el token es válido
        return jsonify({"message": "Sesión cerrada exitosamente"}), 200
    
    except Exception as e:
        return jsonify({"error": "Token inválido"}), 401

@auth_bp.route('/test-auth', methods=['GET'])
def test_auth():
    """
    Ruta de prueba para validar el decorador @auth_required
    """
    from app.security import auth_required
    
    @auth_required
    def protected_test(current_user):
        return jsonify({
            "message": "Autenticación exitosa",
            "user": {
                "uuid": str(current_user.uuid),
                "username": current_user.username,
                "email": current_user.email
            }
        }), 200
    
    return protected_test()