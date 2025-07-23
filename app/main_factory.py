from datetime import date, timedelta
from contextlib import asynccontextmanager
from typing import Annotated, Union, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select, SQLModel

from app import models, schemas, auth
from app.db import get_db, engine as default_engine
from app.routes import usuarios

session_dep = Annotated[Session, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = getattr(app.state, "engine", default_engine)
    if getattr(app.state, "reset_db", False):
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield

def create_app(engine_override=None):
    app = FastAPI(lifespan=lifespan)
    if engine_override:
        print("⚙️ Usando engine de prueba")
        app.state.engine = engine_override

    @app.get('/')
    def root():
        return {'message': 'API de Gestión Académica'}

    @app.post("/token", response_model=schemas.Token)
    async def login_for_access_token(
        session: session_dep,
        form_data: OAuth2PasswordRequestForm = Depends()
    ):
        user_models = [models.Admin, models.Professor, models.Student]
        user = None
        for model in user_models:
            user = session.exec(select(model).where(model.name_user == form_data.username)).first()
            if user:
                break

        if not user or not user.verify_password(form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=auth.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={
                "sub": user.name_user,
                "role": user.role,
                "user_id": getattr(user, "admin_id", None) or 
                           getattr(user, "professor_id", None) or 
                           getattr(user, "student_id", None)
            },
            expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}

    #Routers
    app.include_router(usuarios.router)

    return app
