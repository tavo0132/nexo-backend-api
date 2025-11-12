from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.mysql import CHAR
from app.extensions import db

class Friendship(db.Model):
    """
    Modelo para gestionar relaciones de amistad entre usuarios.
    
    Normalización: El par (user_a, user_b) se almacena siempre como (user_low_id, user_high_id)
    donde user_low_id < user_high_id para evitar duplicados.
    
    Estados posibles:
    - pending: Solicitud enviada, pendiente de respuesta
    - accepted: Amistad aceptada por ambos usuarios
    - rejected: Solicitud rechazada por el receptor
    - removed: Amistad eliminada por cualquiera de los dos
    """
    __tablename__ = 'friendships'
    
    # Columnas principales
    user_low_id = Column(CHAR(36), nullable=False, primary_key=True, comment="UUID del usuario con ID menor")
    user_high_id = Column(CHAR(36), nullable=False, primary_key=True, comment="UUID del usuario con ID mayor")
    status = Column(String(20), nullable=False, default='pending', comment="Estado: pending|accepted|rejected|removed")
    requested_by_id = Column(CHAR(36), nullable=False, comment="UUID del usuario que hizo la solicitud")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Fecha de creación de la relación")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Fecha de última actualización")
    
    # Constraints y índices
    __table_args__ = (
        UniqueConstraint('user_low_id', 'user_high_id', name='uq_friendship_pair'),
        Index('idx_friendship_user_low', 'user_low_id'),
        Index('idx_friendship_user_high', 'user_high_id'),
        Index('idx_friendship_status', 'status'),
        Index('idx_friendship_requested_by', 'requested_by_id'),
    )
    
    @staticmethod
    def normalize_user_pair(user_a_id, user_b_id):
        """
        Normaliza el par de usuarios ordenándolos por ID.
        Siempre retorna (user_low_id, user_high_id) donde user_low_id < user_high_id
        
        Args:
            user_a_id (str): UUID del primer usuario
            user_b_id (str): UUID del segundo usuario
            
        Returns:
            tuple: (user_low_id, user_high_id, is_swapped)
                   is_swapped indica si los IDs fueron intercambiados
        """
        if user_a_id < user_b_id:
            return user_a_id, user_b_id, False
        else:
            return user_b_id, user_a_id, True
    
    @classmethod
    def find_friendship(cls, user_a_id, user_b_id):
        """
        Busca una relación de amistad entre dos usuarios.
        
        Args:
            user_a_id (str): UUID del primer usuario
            user_b_id (str): UUID del segundo usuario
            
        Returns:
            Friendship: Instancia de la relación o None si no existe
        """
        user_low_id, user_high_id, _ = cls.normalize_user_pair(user_a_id, user_b_id)
        return cls.query.filter_by(user_low_id=user_low_id, user_high_id=user_high_id).first()
    
    def get_other_user_id(self, current_user_id):
        """
        Obtiene el ID del otro usuario en la relación.
        
        Args:
            current_user_id (str): UUID del usuario actual
            
        Returns:
            str: UUID del otro usuario en la relación
        """
        if current_user_id == self.user_low_id:
            return self.user_high_id
        elif current_user_id == self.user_high_id:
            return self.user_low_id
        else:
            raise ValueError("El usuario actual no participa en esta relación")
    
    def is_requested_by(self, user_id):
        """
        Verifica si la solicitud fue hecha por el usuario especificado.
        
        Args:
            user_id (str): UUID del usuario a verificar
            
        Returns:
            bool: True si el usuario hizo la solicitud, False en caso contrario
        """
        return self.requested_by_id == user_id
    
    def to_dict(self, current_user_id=None):
        """
        Convierte la instancia a diccionario para respuestas de API.
        
        Args:
            current_user_id (str, optional): UUID del usuario actual para determinar requested_by_me
            
        Returns:
            dict: Representación en diccionario de la relación
        """
        result = {
            'user_low_id': self.user_low_id,
            'user_high_id': self.user_high_id,
            'status': self.status,
            'requested_by_id': self.requested_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if current_user_id:
            result['other_user_id'] = self.get_other_user_id(current_user_id)
            result['requested_by_me'] = self.is_requested_by(current_user_id)
        
        return result
    
    def __repr__(self):
        return f'<Friendship {self.user_low_id}<->{self.user_high_id} status={self.status}>'