# 🌐 Nexo Backend - API REST para Gestión de Usuarios

Sistema backend completo con autenticación JWT, gestión de perfiles de usuario y sistema de amistades para aplicaciones sociales.

## 🌟 Características Principales

- **Autenticación JWT** con tokens seguros y renovación automática
- **Gestión de Perfiles** completa con validaciones avanzadas
- **Sistema de Upload** de avatares con validaciones MIME y tamaño
- **Búsqueda de Usuarios** con paginación y filtros
- **API RESTful** bien estructurada y documentada
- **Migraciones de BD** con Alembic para control de versiones

## 🚀 Inicio Rápido

### Prerrequisitos
```bash
# Python 3.8+
# MySQL Server (puerto 3307)
# Entorno virtual recomendado
```

### Instalación
```bash
# Clonar repositorio
git clone <tu-repo-url>
cd nexo-backend

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env  # Editar con tus credenciales

# Ejecutar migraciones
flask db upgrade

# Iniciar servidor
python wsgi.py
```

## 📁 Estructura del Proyecto

```
nexo-backend/
├── app/
│   ├── models/              # Modelos de datos
│   │   ├── user.py         # Modelo Usuario
│   │   └── auth_local.py   # Autenticación local
│   ├── routes/             # Endpoints de la API
│   │   ├── auth.py         # Autenticación (login/register)
│   │   ├── users.py        # Gestión de usuarios
│   │   └── health.py       # Health check
│   ├── __init__.py         # Factory de aplicación Flask
│   ├── extensions.py       # Extensiones (SQLAlchemy, etc.)
│   └── security.py         # JWT y seguridad
├── migrations/             # Migraciones Alembic
├── uploads/               # Archivos subidos (avatares)
├── config.py             # Configuración de la aplicación
├── wsgi.py              # Punto de entrada WSGI
└── requirements.txt     # Dependencias Python
```

## 🛠️ Tecnologías

- **Backend**: Flask 2.3.3
- **Base de Datos**: MySQL 9.5 + SQLAlchemy ORM
- **Autenticación**: JWT con PyJWT 2.8.0
- **Migraciones**: Alembic
- **Validación**: Argon2 para hashing de passwords
- **Testing**: Postman Collections

## 📋 Variables de Entorno

```env
# Base de datos
DB_HOST=localhost
DB_PORT=3307
DB_USER=nexo
DB_PASSWORD=tu_password
DB_NAME=nexo_dev

# JWT
JWT_SECRET_KEY=tu_clave_secreta_super_segura

# Uploads
UPLOAD_ROOT=uploads
MAX_AVATAR_MB=2

# Flask
FLASK_ENV=development
DEBUG=True
```

## ⚙️ Configuración de Base de Datos

1. **Crear base de datos**:
   ```sql
   CREATE DATABASE nexo_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'nexo'@'localhost' IDENTIFIED BY 'tu_password';
   GRANT ALL PRIVILEGES ON nexo_dev.* TO 'nexo'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. **Ejecutar migraciones**:
   ```bash
   flask db upgrade
   ```

## 🎯 Endpoints de la API

### 🔐 Autenticación
- **POST** `/auth/register` - Registro de usuarios
- **POST** `/auth/login` - Inicio de sesión (obtener JWT)

### 👤 Gestión de Usuarios
- **GET** `/users/me` - Perfil del usuario autenticado
- **PATCH** `/users/me` - Actualizar perfil
- **PATCH** `/users/me/avatar` - Subir avatar
- **GET** `/users/{uuid}` - Perfil público de usuario
- **GET** `/users/search?q=&limit=&offset=` - Búsqueda de usuarios

### 🏥 Monitoreo
- **GET** `/health` - Estado del servidor

## 🔧 Uso de la API

### Registro de Usuario
```bash
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan_perez",
    "email": "juan@example.com",
    "password": "MiPassword123!",
    "first_name": "Juan",
    "last_name": "Pérez",
    "birth_date": "1990-01-15"
  }'
```

### Login y Obtener Token
```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan@example.com",
    "password": "MiPassword123!"
  }'
```

### Usar Token en Requests
```bash
curl -X GET http://127.0.0.1:5000/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

## 📊 Validaciones Implementadas

### Usuario y Perfil
- ✅ **Email único** - No duplicados (409 Conflict)
- ✅ **Mayoría de edad** - Validación de birth_date
- ✅ **Password seguro** - Reglas de complejidad
- ✅ **Campos requeridos** - Validación de campos obligatorios

### Upload de Avatares
- ✅ **Tipos MIME** - Solo imágenes (JPG, PNG, GIF, WEBP)
- ✅ **Tamaño máximo** - Límite de 2MB (413 Payload Too Large)
- ✅ **Nombres únicos** - UUID para evitar conflictos
- ✅ **Estructura organizada** - `/uploads/{yyyy}/{mm}/`

## 🧪 Testing con Postman

El proyecto incluye una colección completa de Postman con:

- ✅ **Casos exitosos** (200 OK)
- ✅ **Validaciones de conflicto** (409 Conflict)
- ✅ **Errores de validación** (422 Unprocessable Entity)
- ✅ **Límites de tamaño** (413 Payload Too Large)
- ✅ **Autenticación requerida** (401 Unauthorized)

### Casos de Prueba Principales
1. Registro de usuario válido ⇒ 201
2. Email duplicado ⇒ 409
3. Login exitoso ⇒ 200 + token
4. Obtener perfil ⇒ 200
5. Actualizar perfil ⇒ 200
6. Subir avatar válido ⇒ 200
7. Avatar tipo incorrecto ⇒ 422
8. Avatar demasiado grande ⇒ 413
9. Búsqueda con resultados ⇒ 200
10. Búsqueda sin resultados ⇒ 200 + array vacío

## 📈 Estructura de Respuestas

### Respuesta Exitosa
```json
{
  "user": {
    "uuid": "12345678-1234-1234-1234-123456789abc",
    "username": "juan_perez",
    "email": "juan@example.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "avatar_url": "/uploads/2025/11/avatar-uuid.jpg",
    "birth_date": "1990-01-15"
  }
}
```

### Respuesta de Error
```json
{
  "error": "El email ya existe",
  "details": "Un usuario con este email ya está registrado"
}
```

## 🔒 Seguridad

- **JWT Tokens** con expiración de 60 minutos
- **Hash Argon2** para contraseñas
- **Validación MIME** para uploads
- **Sanitización** de inputs (strip, lower)
- **Timezone UTC** para consistencia global

## 📂 Gestión de Archivos

Los avatares se organizan automáticamente:
```
uploads/
└── 2025/
    └── 11/
        ├── uuid1.jpg
        ├── uuid2.png
        └── uuid3.webp
```

## 🚨 Códigos de Estado HTTP

- **200** OK - Operación exitosa
- **201** Created - Recurso creado
- **400** Bad Request - Datos inválidos
- **401** Unauthorized - Token requerido/inválido
- **403** Forbidden - Permisos insuficientes
- **409** Conflict - Recurso duplicado
- **413** Payload Too Large - Archivo muy grande
- **422** Unprocessable Entity - Validación fallida
- **500** Internal Server Error - Error del servidor

## 🔄 Roadmap

### ✅ Etapa 1: Base
- Sistema de autenticación básico

### ✅ Etapa 2: Perfiles (Actual)
- Gestión completa de perfiles
- Sistema de avatares
- Búsqueda de usuarios

### 🚧 Etapa 3: Amistades (Próximo)
- Sistema de solicitudes de amistad
- Estados de relación (pending/accepted/rejected)
- Gestión de amigos

## 📞 Soporte

Para reportar issues o contribuir:
1. Crear issue en GitHub
2. Fork del repositorio
3. Pull request con mejoras

---

**Desarrollado con ❤️ para crear conexiones sociales**