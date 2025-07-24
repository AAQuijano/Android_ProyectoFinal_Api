#main_factory.py
from datetime import timedelta
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app import models, schemas, auth
from app.db import get_db, engine as default_engine
from app.routes import usuarios, materias, calificaciones

# Dependencias comunes
session_dep = Annotated[Session, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager para manejar el ciclo de vida de la aplicación"""
    engine = getattr(app.state, "engine", default_engine)
    if getattr(app.state, "reset_db", False):
        models.SQLModel.metadata.drop_all(engine)
    models.SQLModel.metadata.create_all(engine)
    yield

def create_app(engine_override=None):
    """Factory para crear la aplicación FastAPI"""
    app = FastAPI(
        title="API de Gestión Académica",
        description="Sistema integrado de gestión académica con autenticación JWT",
        version="1.0.0",
        lifespan=lifespan
    )
    # Middleware de CORS (para permitir frontend externo)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Cambiar en producción a dominios específicos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware de logging de peticiones
    @app.middleware("http")
    async def log_requests(request, call_next):
        print(f"➡️ {request.method} {request.url.path}")
        response = await call_next(request)
        print(f"⬅️ {response.status_code} {request.url.path}")
        return response


    # Configurar engine override para testing si es necesario
    if engine_override:
        print("⚙️ Usando engine de prueba")
        app.state.engine = engine_override

    @app.get("/", tags=["Root"])
    async def root():
        """Endpoint raíz de la API"""
        return {"message": "API de Gestión Académica"}

    @app.post("/token", response_model=schemas.Token, tags=["Autenticación"])
    async def login_for_access_token(
        session: session_dep,
        form_data: OAuth2PasswordRequestForm = Depends()
    ):
        """
        Endpoint para autenticación y obtención de token JWT.
        
        Args:
            username: Nombre de usuario
            password: Contraseña
        """
        # Buscar usuario en la base de datos
        user = session.exec(
            select(models.User).where(models.User.name_user == form_data.username)
        ).first()

        # Verificar credenciales
        if not user or not user.verify_password(form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generar token de acceso
        access_token_expires = timedelta(minutes=auth.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={
                "sub": user.name_user,
                "role": user.role,
                "user_id": user.user_id  # Usamos el campo unificado user_id
            },
            expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}

    #Incluir routers
    app.include_router(usuarios.router)
    app.include_router(materias.router)
    app.include_router(calificaciones.router)

    return app



    @app.get("/health", tags=["Sistema"])
    async def health_check():
        return {"status": "ok"}
