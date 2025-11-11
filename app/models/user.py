import uuid
from datetime import datetime
from app.extensions import db

class User(db.Model):
    """Modelo de usuario principal"""
    __tablename__ = 'users'
    
    # Clave primaria usando UUID
    uuid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Información básica del usuario
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=True)  # Opcional
    last_name = db.Column(db.String(100), nullable=True)   # Opcional
    
    # URL del avatar del usuario
    avatar_url = db.Column(db.String(500), nullable=True)
    
    # Fecha de nacimiento para validar mayoría de edad
    birth_date = db.Column(db.Date, nullable=False)
    
    # Estado del usuario
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relación con AuthLocal
    auth_local = db.relationship('AuthLocal', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convertir el usuario a diccionario (sin información sensible)"""
        return {
            'uuid': str(self.uuid),
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'avatar_url': self.avatar_url,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }