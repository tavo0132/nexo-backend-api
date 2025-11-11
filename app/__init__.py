from flask import Flask
from config import config
from app.extensions import init_app

def create_app(config_name='default'):
    """Factory function para crear la aplicación Flask"""
    
    # Crear instancia de Flask
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    init_app(app)
    
    # Importar modelos para que Alembic los detecte
    from app.models import User, AuthLocal
    
    # Registrar blueprints
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    
    # Configurar ruta estática para servir uploads
    import os
    from flask import send_from_directory
    
    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        """Servir archivos estáticos desde la carpeta uploads"""
        uploads_dir = os.path.join(app.root_path, '..', app.config['UPLOAD_ROOT'])
        return send_from_directory(uploads_dir, filename)
    
    return app