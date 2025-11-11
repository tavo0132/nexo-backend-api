import re
import jwt
import datetime as dt
from datetime import datetime, timedelta, date
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError
from flask import current_app

# Inicializar el hasher de Argon2
ph = PasswordHasher()

def hash_password(password: str) -> str:
    """
    Crear hash seguro de la contraseña usando Argon2
    
    Args:
        password (str): Contraseña en texto plano
        
    Returns:
        str: Hash de la contraseña
        
    Raises:
        HashingError: Si hay error al crear el hash
    """
    try:
        return ph.hash(password)
    except HashingError as e:
        raise ValueError(f"Error al crear hash de contraseña: {str(e)}")

def verify_password(password: str, password_hash: str) -> bool:
    """
    Verificar si la contraseña coincide con el hash
    
    Args:
        password (str): Contraseña en texto plano
        password_hash (str): Hash almacenado
        
    Returns:
        bool: True si coincide, False si no
    """
    try:
        ph.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False

def is_valid_password(password: str) -> tuple[bool, str]:
    """
    Validar que la contraseña cumpla con los requisitos de seguridad
    
    Requisitos:
    - Al menos 8 caracteres
    - Al menos una letra minúscula
    - Al menos una letra mayúscula  
    - Al menos un número
    - Al menos un carácter especial
    
    Args:
        password (str): Contraseña a validar
        
    Returns:
        tuple[bool, str]: (es_válida, mensaje_error)
    """
    if not password or len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una letra minúscula"
    
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una letra mayúscula"
    
    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?\":{}|<>)"
    
    return True, "Contraseña válida"

def is_adult(birth_date: date) -> bool:
    """
    Verificar si la persona es mayor de edad (18 años o más)
    
    Args:
        birth_date (date): Fecha de nacimiento
        
    Returns:
        bool: True si es mayor de edad, False si no
    """
    if not birth_date:
        return False
    
    today = date.today()
    age = today.year - birth_date.year
    
    # Ajustar si no ha cumplido años este año
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age >= 18

def make_access_token(user_uuid: str) -> str:
    """
    Generar token JWT de acceso
    
    Args:
        user_uuid (str): UUID del usuario
        
    Returns:
        str: Token JWT
        
    Raises:
        ValueError: Si hay error al generar el token
    """
    try:
        # Calcular tiempo de expiración usando UTC timezone
        expires_delta = timedelta(minutes=current_app.config['JWT_EXPIRES_MIN'])
        now_utc = dt.datetime.now(dt.timezone.utc)
        expires_at = now_utc + expires_delta
        
        # Payload del token
        payload = {
            'user_uuid': user_uuid,
            'exp': expires_at,
            'iat': now_utc,  # issued at
            'type': 'access_token'
        }
        
        # Generar token
        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET'],
            algorithm='HS256'
        )
        
        return token
    
    except Exception as e:
        raise ValueError(f"Error al generar token: {str(e)}")

def decode_access_token(token: str) -> dict:
    """
    Decodificar y validar token JWT
    
    Args:
        token (str): Token JWT
        
    Returns:
        dict: Payload del token si es válido
        
    Raises:
        jwt.InvalidTokenError: Si el token es inválido o expirado
    """
    try:
        # Validar que el token no esté vacío
        if not token or token.strip() == "":
            raise jwt.InvalidTokenError("Token vacío")
            
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET'],
            algorithms=['HS256']
        )
        
        # Verificar que sea un token de acceso
        if payload.get('type') != 'access_token':
            raise jwt.InvalidTokenError("Tipo de token inválido")
            
        # Verificar que tenga el campo user_uuid
        if not payload.get('user_uuid'):
            raise jwt.InvalidTokenError("Token sin user_uuid")
            
        return payload
    
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token expirado")
    except jwt.DecodeError:
        raise jwt.InvalidTokenError("Token mal formateado")
    except jwt.InvalidSignatureError:
        raise jwt.InvalidTokenError("Firma de token inválida")
    except jwt.InvalidTokenError:
        raise  # Re-raise custom InvalidTokenError
    except Exception as e:
        raise jwt.InvalidTokenError(f"Error al decodificar token: {str(e)}")

def auth_required(f):
    """
    Decorador para requerir autenticación JWT en rutas
    
    Extrae el token del header Authorization Bearer, lo valida y
    inyecta el usuario autenticado en la función decorada.
    
    Usage:
        @auth_required
        def protected_route(current_user):
            return {"message": f"Hola {current_user.username}"}
    """
    from functools import wraps
    from flask import request, jsonify
    from app.models.user import User
    
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Extraer token del header Authorization
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({
                    'error': 'Token de autorización requerido',
                    'message': 'Proporciona un token en el header Authorization'
                }), 401
            
            # Verificar formato Bearer
            try:
                scheme, token = auth_header.split(' ', 1)
                if scheme.lower() != 'bearer':
                    raise ValueError("Esquema inválido")
            except ValueError:
                return jsonify({
                    'error': 'Formato de autorización inválido',
                    'message': 'Usa el formato: Authorization: Bearer <token>'
                }), 401
            
            # Decodificar token
            try:
                payload = decode_access_token(token)
                user_uuid = payload['user_uuid']
            except jwt.InvalidTokenError as e:
                return jsonify({
                    'error': 'Token inválido',
                    'message': str(e)
                }), 401
            
            # Buscar usuario en base de datos
            current_user = User.query.filter_by(uuid=user_uuid).first()
            if not current_user:
                return jsonify({
                    'error': 'Usuario no encontrado',
                    'message': 'El token es válido pero el usuario no existe'
                }), 401
            
            # Inyectar usuario en la función
            return f(current_user, *args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'error': 'Error de autenticación',
                'message': f'Error interno: {str(e)}'
            }), 500
    
    return decorated