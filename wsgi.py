import os
from app import create_app

# Crear la aplicación
app = create_app(os.getenv('FLASK_ENV') or 'development')

if __name__ == '__main__':
    # Ejecutar el servidor de desarrollo
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )