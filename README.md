
# FastAPI + MySQL API

Este proyecto es una API desarrollada con [FastAPI](https://fastapi.tiangolo.com/) y conectada a una base de datos MySQL. Está preparada para ser desplegada en producción sobre AWS EC2 y RDS.

---

## 🚀 Características

- Autenticación JWT por roles (admin, profesor, estudiante)
- Gestión de usuarios, materias, calificaciones
- Cobertura de pruebas >90% con Pytest
- Docker y docker-compose opcional para entorno local
- Integrable fácilmente con frontend Android (Jetpack Compose)

---

## ⚙️ Requisitos

- Python 3.10+
- MySQL 8.x
- pip / venv
- (opcional) Docker y docker-compose

---

## 📦 Instalación local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo de entorno
cp .env.example .env  # o crea uno manualmente con tus variables
```

---

## 🚀 Ejecución

```bash
uvicorn app.main_factory:create_app --reload --host 0.0.0.0 --port 8000
```

Accede a:
- http://localhost:8000/docs
- http://localhost:8000/redoc

---

## 🧪 Pruebas

```bash
pytest --cov=app --cov-report=html
```

---

## ☁️ Despliegue en AWS EC2 + RDS

1. Crea una instancia EC2 (Ubuntu 22.04) y una base de datos MySQL en RDS.
2. Instala Python, venv y git en el servidor.
3. Clona este repositorio:

```bash
git clone https://github.com/AAQuijano/Android_ProyectoFinal_Api.git
cd Android_ProyectoFinal_Api
```

4. Configura entorno:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nano .env  # crea tus variables con credenciales reales
```

5. Lanza el servidor:

```bash
fastapi dev "main.py"
```

---

## 🔐 Seguridad

- Nunca subas `.env` a GitHub.
- Usa HTTPS con Nginx o CloudFront.
- Puedes conectar Secrets Manager o SSM Parameter Store para las claves.

---

## 📱 Frontend Android

Este backend está listo para integrarse con una app móvil en Jetpack Compose mediante autenticación JWT.
