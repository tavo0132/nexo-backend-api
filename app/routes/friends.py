from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import User, Friendship
from app.security import auth_required
import uuid

# Crear blueprint para amistades
friends_bp = Blueprint('friends', __name__, url_prefix='/friends')

@friends_bp.route('', methods=['GET'])
@auth_required
def list_friendships(current_user):
    """
    Lista las relaciones de amistad del usuario logueado.
    
    Query Parameters:
    - status (opcional): Filtrar por estado (pending|accepted|rejected|removed)
    
    Respuesta:
    200: Lista de relaciones con información detallada
    400: Parámetros inválidos
    """
    try:
        # Obtener parámetro de filtro de estado
        status_filter = request.args.get('status', '').strip().lower()
        
        # Validar estado si se proporciona
        valid_statuses = ['pending', 'accepted', 'rejected', 'removed']
        if status_filter and status_filter not in valid_statuses:
            return jsonify({
                "error": "Estado inválido",
                "valid_statuses": valid_statuses
            }), 400
        
        # Construir consulta base - el usuario puede estar en cualquiera de las dos columnas
        query = Friendship.query.filter(
            (Friendship.user_low_id == current_user.uuid) | 
            (Friendship.user_high_id == current_user.uuid)
        )
        
        # Aplicar filtro de estado si se proporciona
        if status_filter:
            query = query.filter(Friendship.status == status_filter)
        
        # Ordenar por fecha de actualización (más recientes primero)
        friendships = query.order_by(Friendship.updated_at.desc()).all()
        
        # Convertir a lista de diccionarios con información adicional
        result = []
        for friendship in friendships:
            friendship_dict = friendship.to_dict(current_user.uuid)
            
            # Obtener información del otro usuario
            other_user_id = friendship.get_other_user_id(current_user.uuid)
            other_user = User.query.filter_by(uuid=other_user_id).first()
            
            if other_user:
                friendship_dict['other_user'] = {
                    'uuid': other_user.uuid,
                    'username': other_user.username,
                    'first_name': other_user.first_name,
                    'last_name': other_user.last_name,
                    'avatar_url': other_user.avatar_url
                }
            
            result.append(friendship_dict)
        
        return jsonify({
            "friendships": result,
            "count": len(result),
            "filter_applied": status_filter if status_filter else "none"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error al listar amistades: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@friends_bp.route('/request', methods=['POST'])
@auth_required
def send_friend_request(current_user):
    """
    Envía una solicitud de amistad a otro usuario.
    
    Body JSON:
    {
        "to_user_uuid": "uuid_del_usuario_destino"
    }
    
    Respuestas:
    201: Solicitud creada exitosamente
    200: Solicitud ya existía (idempotente)
    400: Auto-solicitud o datos inválidos
    404: Usuario destino no encontrado
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se enviaron datos JSON"}), 400
        
        to_user_uuid = data.get('to_user_uuid', '').strip()
        
        if not to_user_uuid:
            return jsonify({"error": "Campo to_user_uuid es requerido"}), 400
        
        # Validar que no sea auto-solicitud
        if to_user_uuid == current_user.uuid:
            return jsonify({
                "error": "No puedes enviarte una solicitud de amistad a ti mismo"
            }), 400
        
        # Verificar que el usuario destino existe
        target_user = User.query.filter_by(uuid=to_user_uuid).first()
        if not target_user:
            return jsonify({"error": "Usuario destino no encontrado"}), 404
        
        # Buscar relación existente
        existing_friendship = Friendship.find_friendship(current_user.uuid, to_user_uuid)
        
        if existing_friendship:
            # Si ya está pending y fue solicitada por el usuario actual, es idempotente
            if (existing_friendship.status == 'pending' and 
                existing_friendship.requested_by_id == current_user.uuid):
                return jsonify({
                    "message": "Solicitud de amistad ya existe",
                    "friendship": existing_friendship.to_dict(current_user.uuid)
                }), 200
            
            # Si está rejected o removed, cambiar a pending y actualizar requested_by_id
            if existing_friendship.status in ['rejected', 'removed']:
                existing_friendship.status = 'pending'
                existing_friendship.requested_by_id = current_user.uuid
                db.session.commit()
                
                return jsonify({
                    "message": "Solicitud de amistad enviada",
                    "friendship": existing_friendship.to_dict(current_user.uuid)
                }), 200
            
            # Si está accepted, informar que ya son amigos
            if existing_friendship.status == 'accepted':
                return jsonify({
                    "message": "Ya son amigos",
                    "friendship": existing_friendship.to_dict(current_user.uuid)
                }), 200
            
            # Si está pending pero solicitada por el otro usuario
            if (existing_friendship.status == 'pending' and 
                existing_friendship.requested_by_id != current_user.uuid):
                return jsonify({
                    "message": "Ya tienes una solicitud pendiente de este usuario",
                    "suggestion": "Puedes aceptarla usando POST /friends/accept",
                    "friendship": existing_friendship.to_dict(current_user.uuid)
                }), 200
        
        # Crear nueva relación de amistad
        user_low_id, user_high_id, _ = Friendship.normalize_user_pair(
            current_user.uuid, to_user_uuid
        )
        
        new_friendship = Friendship(
            user_low_id=user_low_id,
            user_high_id=user_high_id,
            status='pending',
            requested_by_id=current_user.uuid
        )
        
        db.session.add(new_friendship)
        db.session.commit()
        
        return jsonify({
            "message": "Solicitud de amistad enviada exitosamente",
            "friendship": new_friendship.to_dict(current_user.uuid)
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Error de integridad en la base de datos"}), 500
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al enviar solicitud de amistad: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@friends_bp.route('/accept', methods=['POST'])
@auth_required
def accept_friend_request(current_user):
    """
    Acepta una solicitud de amistad pendiente.
    
    Body JSON:
    {
        "user_uuid": "uuid_del_usuario_que_envió_la_solicitud"
    }
    
    Respuestas:
    200: Solicitud aceptada exitosamente
    400: Datos inválidos o no puedes aceptar tu propia solicitud
    403: No tienes permisos para aceptar esta solicitud
    404: Solicitud no encontrada o no está pendiente
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se enviaron datos JSON"}), 400
        
        user_uuid = data.get('user_uuid', '').strip()
        
        if not user_uuid:
            return jsonify({"error": "Campo user_uuid es requerido"}), 400
        
        # Buscar la relación existente
        friendship = Friendship.find_friendship(current_user.uuid, user_uuid)
        
        if not friendship:
            return jsonify({"error": "No existe una relación de amistad con este usuario"}), 404
        
        # Verificar que está en estado pending
        if friendship.status != 'pending':
            return jsonify({
                "error": f"La relación está en estado '{friendship.status}', no puede ser aceptada",
                "current_status": friendship.status
            }), 400
        
        # Verificar que el usuario actual es el receptor (no el que envió la solicitud)
        if friendship.requested_by_id == current_user.uuid:
            return jsonify({
                "error": "No puedes aceptar tu propia solicitud de amistad"
            }), 403
        
        # Aceptar la solicitud
        friendship.status = 'accepted'
        db.session.commit()
        
        return jsonify({
            "message": "Solicitud de amistad aceptada exitosamente",
            "friendship": friendship.to_dict(current_user.uuid)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al aceptar solicitud de amistad: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@friends_bp.route('/reject', methods=['POST'])
@auth_required
def reject_friend_request(current_user):
    """
    Rechaza una solicitud de amistad pendiente.
    
    Body JSON:
    {
        "user_uuid": "uuid_del_usuario_que_envió_la_solicitud"
    }
    
    Respuestas:
    200: Solicitud rechazada exitosamente
    400: Datos inválidos
    403: No tienes permisos para rechazar esta solicitud
    404: Solicitud no encontrada o no está pendiente
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se enviaron datos JSON"}), 400
        
        user_uuid = data.get('user_uuid', '').strip()
        
        if not user_uuid:
            return jsonify({"error": "Campo user_uuid es requerido"}), 400
        
        # Buscar la relación existente
        friendship = Friendship.find_friendship(current_user.uuid, user_uuid)
        
        if not friendship:
            return jsonify({"error": "No existe una relación de amistad con este usuario"}), 404
        
        # Verificar que está en estado pending
        if friendship.status != 'pending':
            return jsonify({
                "error": f"La relación está en estado '{friendship.status}', no puede ser rechazada",
                "current_status": friendship.status
            }), 400
        
        # Verificar que el usuario actual es el receptor (no el que envió la solicitud)
        if friendship.requested_by_id == current_user.uuid:
            return jsonify({
                "error": "No puedes rechazar tu propia solicitud de amistad"
            }), 403
        
        # Rechazar la solicitud
        friendship.status = 'rejected'
        db.session.commit()
        
        return jsonify({
            "message": "Solicitud de amistad rechazada",
            "friendship": friendship.to_dict(current_user.uuid)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al rechazar solicitud de amistad: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@friends_bp.route('/unfriend', methods=['POST'])
@auth_required
def unfriend_user(current_user):
    """
    Elimina una amistad existente (solo funciona si están en estado 'accepted').
    
    Body JSON:
    {
        "user_uuid": "uuid_del_usuario_a_eliminar_como_amigo"
    }
    
    Respuestas:
    200: Amistad eliminada exitosamente o estado actual informado
    400: Datos inválidos
    404: Relación no encontrada
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se enviaron datos JSON"}), 400
        
        user_uuid = data.get('user_uuid', '').strip()
        
        if not user_uuid:
            return jsonify({"error": "Campo user_uuid es requerido"}), 400
        
        # Buscar la relación existente
        friendship = Friendship.find_friendship(current_user.uuid, user_uuid)
        
        if not friendship:
            return jsonify({
                "error": "No existe una relación de amistad con este usuario",
                "action": "No hay relación que eliminar"
            }), 404
        
        # Si está accepted, cambiar a removed
        if friendship.status == 'accepted':
            friendship.status = 'removed'
            db.session.commit()
            
            return jsonify({
                "message": "Amistad eliminada exitosamente",
                "friendship": friendship.to_dict(current_user.uuid)
            }), 200
        
        # Si no está accepted, devolver estado actual (idempotente)
        else:
            return jsonify({
                "message": f"La relación ya está en estado '{friendship.status}'",
                "friendship": friendship.to_dict(current_user.uuid),
                "action": "Sin cambios realizados"
            }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar amistad: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500