# Archivo __init__.py para el módulo models
from .user import User
from .auth_local import AuthLocal
from .friendship import Friendship

__all__ = ['User', 'AuthLocal', 'Friendship']