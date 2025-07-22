from datetime import date, timedelta
from contextlib import asynccontextmanager
from typing import Annotated, Union, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select, SQLModel

from app import models, schemas, auth
from app.db import get_db, engine as default_engine

session_dep = Annotated[Session, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def calculate_age(birth_date: Optional[date]) -> Optional[int]:
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

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

    @app.post("/usuarios/", 
             response_model=Union[schemas.StudentPublic, schemas.ProfessorPublic, schemas.AdminPublic], 
             status_code=status.HTTP_201_CREATED)
    def create_user(user: schemas.UserCreate, session: session_dep):
        try:
            # Validar rol primero
            try:
                role = models.Role(user.role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rol de usuario no válido"
                )

            # Verificar unicidad
            user_models = [models.Student, models.Professor, models.Admin]
            for model in user_models:
                existing_user = session.exec(
                    select(model).where(
                        (model.email == user.email) |
                        (model.name_user == user.name_user) |
                        (model.cedula == user.cedula)
                    )
                ).first()
                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="El email, nombre de usuario o cédula ya están registrados"
                    )

            user_data = user.model_dump(exclude={"password", "specialization"})
            user_data.update({
                "hashed_password": models.pwd_context.hash(user.password),
                "age": calculate_age(user.birth_date)
            })

            if role == models.Role.STUDENT:
                db_user = models.Student(**user_data)
            elif role == models.Role.PROFESSOR:
                if not user.specialization:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Especialización requerida para profesores"
                    )
                db_user = models.Professor(**user_data, specialization=user.specialization)
            elif role == models.Role.ADMIN:
                db_user = models.Admin(**user_data)

            session.add(db_user)
            session.commit()
            session.refresh(db_user)

            # Convertir a schema público según el rol
            if role == models.Role.STUDENT:
                return schemas.StudentPublic.model_validate(db_user)
            elif role == models.Role.PROFESSOR:
                return schemas.ProfessorPublic.model_validate(db_user)
            else:
                return schemas.AdminPublic.model_validate(db_user)

        except HTTPException:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear usuario: {str(e)}"
            ) from e

    return app
