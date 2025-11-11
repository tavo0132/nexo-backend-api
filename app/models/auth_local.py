from datetime import datetime
from app.extensions import db

class AuthLocal(db.Model):
    """Modelo de autenticación local (usuario/contraseña)"""
    __tablename__ = 'auth_local'
    
    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con User (Foreign Key)
    user_uuid = db.Column(db.String(36), db.ForeignKey('users.uuid'), nullable=False, unique=True)
    
    # Hash de la contraseña usando Argon2
    password_hash = db.Column(db.Text, nullable=False)
    
    # Información de seguridad
    login_attempts = db.Column(db.Integer, default=0, nullable=False)
    last_login_attempt = db.Column(db.DateTime, nullable=True)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relación con User
    user = db.relationship('User', back_populates='auth_local')
    
    def __repr__(self):
        return f'<AuthLocal user_uuid={self.user_uuid}>'