import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nexo-secret-key-default'
    
    # Configuración de base de datos
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = os.environ.get('DB_PORT') or '3307'
    DB_USER = os.environ.get('DB_USER') or 'nexo'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'nexo2020'
    DB_NAME = os.environ.get('DB_NAME') or 'nexo_dev'
    
    # URI de conexión a MySQL
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración JWT
    JWT_SECRET = os.environ.get('JWT_SECRET') or 'nexo-jwt-default-secret'
    JWT_EXPIRES_MIN = int(os.environ.get('JWT_EXPIRES_MIN') or 60)
    
    # Configuración de Flask
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configuración del servidor
    HOST = os.environ.get('HOST') or '127.0.0.1'
    PORT = int(os.environ.get('PORT') or 5000)
    
    # Configuración de uploads y archivos
    UPLOAD_ROOT = os.environ.get('UPLOAD_ROOT') or 'uploads'
    MAX_AVATAR_MB = int(os.environ.get('MAX_AVATAR_MB') or 2)
    MAX_CONTENT_LENGTH = MAX_AVATAR_MB * 1024 * 1024  # Conversión a bytes

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    DEVELOPMENT = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    DEVELOPMENT = False

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}