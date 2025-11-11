import os
import uuid
import mimetypes
from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import User, AuthLocal
from app.security import auth_required, hash_password, verify_password, is_valid_password, is_adult

# Crear blueprint para usuarios
users_bp = Blueprint('users', __name__, url_prefix='/users')

# Tipos MIME permitidos para imágenes
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
}

def is_valid_image(file):
    """
    Validar si el archivo es una imagen válida
    
    Args:
        file: Archivo de Flask FileStorage
        
    Returns:
        bool: True si es imagen válida, False si no
    """
    if not file or not file.filename:
        return False
    
    # Verificar MIME type
    mime_type = file.content_type
    if mime_type not in ALLOWED_MIME_TYPES:
        return False
    
    # Verificar extensión del archivo
    filename_lower = file.filename.lower()
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    return any(filename_lower.endswith(ext) for ext in allowed_extensions)

def save_avatar(file):
    """
    Guardar avatar en el sistema de archivos
    
    Args:
        file: Archivo de Flask FileStorage
        
    Returns:
        str: URL relativa del avatar guardado
        
    Raises:
        ValueError: Si hay error al guardar
    """
    try:
        # Generar nombre único para el archivo
        file_uuid = str(uuid.uuid4())
        file_extension = os.path.splitext(secure_filename(file.filename))[1].lower()
        filename = f"{file_uuid}{file_extension}"
        
        # Crear estructura de directorios {yyyy}/{mm}/
        now = datetime.now()
        year_dir = now.strftime('%Y')
        month_dir = now.strftime('%m')
        
        upload_dir = os.path.join(
            current_app.config['UPLOAD_ROOT'],
            year_dir,
            month_dir
        )
        
        # Crear directorios si no existen
        os.makedirs(upload_dir, exist_ok=True)
        
        # Ruta completa del archivo
        file_path = os.path.join(upload_dir, filename)
        
        # Guardar archivo
        file.save(file_path)
        
        # Retornar URL relativa
        return f"/uploads/{year_dir}/{month_dir}/{filename}"
        
    except Exception as e:
        raise ValueError(f"Error al guardar avatar: {str(e)}")

@users_bp.route('/me', methods=['GET'])
@auth_required
def get_my_profile(current_user):
    """
    Obtener perfil del usuario autenticado
    
    Returns:
        JSON: Datos completos del usuario
    """
    try:
        user_data = {
            "uuid": str(current_user.uuid),
            "username": current_user.username,
            "email": current_user.email,
            "first_name": getattr(current_user, 'first_name', None),
            "last_name": getattr(current_user, 'last_name', None),
            "birth_date": current_user.birth_date.isoformat() if current_user.birth_date else None,
            "avatar_url": getattr(current_user, 'avatar_url', None),
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
        
        return jsonify(user_data), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error al obtener perfil",
            "message": str(e)
        }), 500

@users_bp.route('/me', methods=['PATCH'])
@auth_required
def update_my_profile(current_user):
    """
    Actualizar perfil del usuario autenticado
    
    Body JSON esperado:
    {
        "first_name": "string (opcional)",
        "last_name": "string (opcional)", 
        "email": "string (opcional)",
        "birth_date": "YYYY-MM-DD (opcional)",
        "username": "string (opcional)",
        "password": "string (opcional)"
    }
    
    Returns:
        JSON: Usuario actualizado o error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Datos requeridos",
                "message": "Proporciona al menos un campo para actualizar"
            }), 400
        
        # Campos que se pueden actualizar
        updatable_fields = {
            'first_name', 'last_name', 'email', 
            'birth_date', 'username', 'password'
        }
        
        # Verificar que al menos un campo válido esté presente
        valid_fields = set(data.keys()) & updatable_fields
        if not valid_fields:
            return jsonify({
                "error": "Campos inválidos",
                "message": f"Campos permitidos: {', '.join(updatable_fields)}"
            }), 400
        
        # Validar email si se está actualizando
        if 'email' in data:
            email = data['email'].strip().lower()
            if not email or '@' not in email:
                return jsonify({
                    "error": "Email inválido",
                    "message": "Proporciona un email válido"
                }), 422
            
            # Verificar unicidad del email
            if email != current_user.email.lower():
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    return jsonify({
                        "error": "Email ya registrado",
                        "message": "Este email ya está en uso por otro usuario"
                    }), 409
            
            current_user.email = email
        
        # Validar username si se está actualizando
        if 'username' in data:
            username = data['username'].strip()
            if not username or len(username) < 3:
                return jsonify({
                    "error": "Username inválido",
                    "message": "El username debe tener al menos 3 caracteres"
                }), 422
            
            # Verificar unicidad del username
            if username != current_user.username:
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    return jsonify({
                        "error": "Username ya registrado",
                        "message": "Este username ya está en uso por otro usuario"
                    }), 409
            
            current_user.username = username
        
        # Validar fecha de nacimiento si se está actualizando
        if 'birth_date' in data:
            try:
                birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
                
                # Verificar que sea mayor de edad
                if not is_adult(birth_date):
                    return jsonify({
                        "error": "Edad insuficiente",
                        "message": "Debes ser mayor de 18 años"
                    }), 422
                
                current_user.birth_date = birth_date
                
            except ValueError:
                return jsonify({
                    "error": "Fecha inválida",
                    "message": "Usa el formato YYYY-MM-DD para la fecha de nacimiento"
                }), 422
        
        # Actualizar nombres si se proporcionan
        if 'first_name' in data:
            first_name = data['first_name'].strip() if data['first_name'] else None
            if first_name and len(first_name) > 100:
                return jsonify({
                    "error": "Nombre muy largo",
                    "message": "El nombre no puede exceder 100 caracteres"
                }), 422
            current_user.first_name = first_name
        
        if 'last_name' in data:
            last_name = data['last_name'].strip() if data['last_name'] else None
            if last_name and len(last_name) > 100:
                return jsonify({
                    "error": "Apellido muy largo",
                    "message": "El apellido no puede exceder 100 caracteres"
                }), 422
            current_user.last_name = last_name
        
        # Validar y actualizar contraseña si se proporciona
        if 'password' in data:
            password = data['password']
            
            # Validar contraseña
            is_valid, message = is_valid_password(password)
            if not is_valid:
                return jsonify({
                    "error": "Contraseña inválida",
                    "message": message
                }), 422
            
            # Actualizar contraseña en tabla AuthLocal
            auth_local = AuthLocal.query.filter_by(user_uuid=current_user.uuid).first()
            if auth_local:
                auth_local.password_hash = hash_password(password)
        
        # Guardar cambios
        db.session.commit()
        
        # Retornar usuario actualizado
        user_data = {
            "uuid": str(current_user.uuid),
            "username": current_user.username,
            "email": current_user.email,
            "first_name": getattr(current_user, 'first_name', None),
            "last_name": getattr(current_user, 'last_name', None),
            "birth_date": current_user.birth_date.isoformat() if current_user.birth_date else None,
            "avatar_url": getattr(current_user, 'avatar_url', None)
        }
        
        return jsonify({
            "message": "Perfil actualizado exitosamente",
            "user": user_data
        }), 200
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            "error": "Error de unicidad",
            "message": "El email o username ya está registrado"
        }), 409
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Error al actualizar perfil",
            "message": str(e)
        }), 500

@users_bp.route('/me/avatar', methods=['PATCH'])
@auth_required  
def update_my_avatar(current_user):
    """
    Actualizar avatar del usuario autenticado
    
    Multipart form esperado:
    - avatar: archivo de imagen (JPG, PNG, GIF, WEBP)
    
    Returns:
        JSON: URL del avatar o error
    """
    try:
        # Verificar que se envió un archivo
        if 'avatar' not in request.files:
            return jsonify({
                "error": "Archivo requerido",
                "message": "Proporciona un archivo en el campo 'avatar'"
            }), 400
        
        file = request.files['avatar']
        
        # Verificar que el archivo no esté vacío
        if file.filename == '' or not file:
            return jsonify({
                "error": "Archivo vacío",
                "message": "Selecciona un archivo válido"
            }), 400
        
        # Verificar tamaño del archivo
        # Flask config MAX_CONTENT_LENGTH maneja esto automáticamente,
        # pero podemos hacer validación adicional
        file.seek(0, 2)  # Ir al final del archivo
        file_size = file.tell()
        file.seek(0)  # Volver al inicio
        
        max_size_bytes = current_app.config['MAX_AVATAR_MB'] * 1024 * 1024
        if file_size > max_size_bytes:
            return jsonify({
                "error": "Archivo muy grande", 
                "message": f"El archivo no puede exceder {current_app.config['MAX_AVATAR_MB']}MB"
            }), 413
        
        # Validar que sea una imagen
        if not is_valid_image(file):
            return jsonify({
                "error": "Tipo de archivo inválido",
                "message": "Solo se permiten imágenes (JPG, PNG, GIF, WEBP)"
            }), 422
        
        # Guardar el archivo
        try:
            avatar_url = save_avatar(file)
        except ValueError as e:
            return jsonify({
                "error": "Error al guardar archivo",
                "message": str(e)
            }), 500
        
        # Actualizar URL del avatar en la base de datos
        current_user.avatar_url = avatar_url
        db.session.commit()
        
        return jsonify({
            "message": "Avatar actualizado exitosamente",
            "avatar_url": avatar_url
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Error al actualizar avatar",
            "message": str(e)
        }), 500

@users_bp.route('/<user_uuid>', methods=['GET'])
@auth_required
def get_user_profile(current_user, user_uuid):
    """
    Obtener perfil público de un usuario por UUID
    
    Args:
        user_uuid (str): UUID del usuario a consultar
        
    Returns:
        JSON: Datos públicos del usuario
    """
    try:
        # Buscar usuario por UUID
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return jsonify({
                "error": "Usuario no encontrado",
                "message": "No existe un usuario con ese UUID"
            }), 404
        
        # Datos públicos del usuario (sin información sensible)
        user_data = {
            "uuid": str(user.uuid),
            "username": user.username,
            "first_name": getattr(user, 'first_name', None),
            "last_name": getattr(user, 'last_name', None),
            "avatar_url": getattr(user, 'avatar_url', None),
            # No incluir: email, birth_date, created_at para privacidad
        }
        
        return jsonify(user_data), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error al obtener usuario",
            "message": str(e)
        }), 500

@users_bp.route('/search', methods=['GET'])
@auth_required
def search_users(current_user):
    """
    Buscar usuarios por username, email o nombres
    
    Query parameters:
    - q: término de búsqueda (opcional)
    - limit: número máximo de resultados (default: 20, max: 100)
    - offset: número de resultados a saltar (default: 0)
    
    Returns:
        JSON: Array de usuarios encontrados
    """
    try:
        # Obtener parámetros de consulta
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 resultados
        offset = max(int(request.args.get('offset', 0)), 0)
        
        # Construir consulta base
        query = User.query
        
        # Si hay término de búsqueda, filtrar por username, email, nombres
        if query_term:
            search_pattern = f"%{query_term}%"
            query = query.filter(or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern)
            ))
        
        # Aplicar paginación y obtener resultados
        users = query.offset(offset).limit(limit).all()
        
        # Formatear resultados (solo datos públicos)
        users_data = []
        for user in users:
            user_data = {
                "uuid": str(user.uuid),
                "username": user.username,
                "first_name": getattr(user, 'first_name', None),
                "last_name": getattr(user, 'last_name', None),
                "avatar_url": getattr(user, 'avatar_url', None)
                # No incluir email, birth_date para privacidad
            }
            users_data.append(user_data)
        
        # Contar total de resultados para metadata
        total_count = query.count() if query_term else User.query.count()
        
        return jsonify({
            "users": users_data,
            "metadata": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "query": query_term
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Parámetros inválidos",
            "message": "limit y offset deben ser números enteros"
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Error en búsqueda",
            "message": str(e)
        }), 500