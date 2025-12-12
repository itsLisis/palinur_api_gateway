# 🐳 Docker Setup - Palinur Dating App

## 📋 Prerequisitos

- Docker Desktop instalado
- Docker Compose instalado

## 🚀 Comandos para ejecutar

### Iniciar todos los servicios

```bash
cd palinur_api_gateway
docker-compose up --build
```

### Iniciar en background

```bash
docker-compose up -d --build
```

### Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Un servicio específico
docker-compose logs -f api-gateway
docker-compose logs -f auth-service
docker-compose logs -f user-service
docker-compose logs -f matching-service
docker-compose logs -f chat-service
docker-compose logs -f frontend
```

### Detener servicios

```bash
docker-compose down
```

### Detener y eliminar volúmenes (borrar DB)

```bash
docker-compose down -v
```

## 🏗️ Arquitectura de servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **postgres** | 5432 | Base de datos PostgreSQL |
| **auth-service** | 8001 | Autenticación y registro |
| **user-service** | 8002 | Gestión de perfiles |
| **matching-service** | 8003 | Sistema de matches |
| **chat-service** | 8004 | Chat en tiempo real |
| **api-gateway** | 8000 | Gateway principal |
| **frontend** | 3000 | Aplicación React |

## 🗄️ Bases de datos creadas

- `palinur_auth` - Usuarios y autenticación
- `palinur_user` - Perfiles de usuario
- `palinur_matching` - Matches y swipes
- `palinur_chat` - Mensajes de chat

## ⚙️ Variables de entorno

Asegúrate de tener archivos `.env` en cada servicio:

### Auth Service (`.env`)
```env
DATABASE_URL=postgresql://palinur:palinur123@postgres:5432/palinur_auth
SECRET_KEY=tu-secret-key
TURNSTILE_SECRET_KEY=tu-turnstile-key
```

### User Service (`.env`)
```env
DATABASE_URL=postgresql://palinur:palinur123@postgres:5432/palinur_user
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

### Matching Service (`.env`)
```env
DATABASE_URL=postgresql://palinur:palinur123@postgres:5432/palinur_matching
```

### Chat Service (`.env`)
```env
DATABASE_URL=postgresql://palinur:palinur123@postgres:5432/palinur_chat
```

### API Gateway (`.env`)
```env
AUTH_SERVICE_URL=http://auth-service:8001
USER_SERVICE_URL=http://user-service:8002
MATCHING_SERVICE_URL=http://matching-service:8003
CHAT_SERVICE_URL=http://chat-service:8004
SECRET_KEY=tu-secret-key
```

### Frontend (`.env`)
```env
REACT_APP_API_URL=http://localhost:8000
```

## 🔧 Troubleshooting

### Los servicios no inician
```bash
# Ver qué servicio está fallando
docker-compose ps

# Ver logs del servicio problemático
docker-compose logs nombre-servicio
```

### Reconstruir un servicio específico
```bash
docker-compose up -d --build --no-deps nombre-servicio
```

### Acceder al contenedor
```bash
docker exec -it palinur-api-gateway /bin/bash
```

### Acceder a PostgreSQL
```bash
docker exec -it palinur-postgres psql -U palinur -d palinur_auth
```

## 📊 Orden de inicio

El `docker-compose.yml` ya configura el orden correcto:
1. **postgres** (con healthcheck)
2. **auth-service**, **user-service**, **matching-service**, **chat-service**
3. **api-gateway**
4. **frontend**

