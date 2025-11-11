from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()

def init_app(app):
    """Inicializar las extensiones con la aplicación Flask"""
    db.init_app(app)
    migrate.init_app(app, db)