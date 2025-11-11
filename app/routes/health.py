from flask import Blueprint, jsonify

# Crear blueprint para rutas de salud
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de verificación de salud del servidor
    Retorna: {"status": "ok"}
    """
    return jsonify({"status": "ok"}), 200