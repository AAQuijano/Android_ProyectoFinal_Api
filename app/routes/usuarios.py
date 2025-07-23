#usuarios.py
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app import models, schemas
from app.db import get_db
from app.auth import get_current_user, get_current_admin_user
from typing import Annotated, Union, Optional

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# Dependencias reutilizables
session_dep = Annotated[Session, Depends(get_db)]
user_dep = Annotated[schemas.UserPublic, Depends(get_current_user)]
admin_dep = Annotated[schemas.UserPublic, Depends(get_current_admin_user)]


def calculate_age(birth_date: Optional[date]) -> Optional[int]:
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

@router.post(
    "/", 
    response_model=schemas.UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo usuario"

)
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
        

@router.get(
    "/me",
    response_model=schemas.UserPublic,
    summary="Obtener datos del usuario actual"
)
async def read_users_me(current_user: user_dep):
    """Devuelve los datos del usuario autenticado."""
    return current_user




@router.get(
    "/{user_id}",
    response_model=schemas.UserPublic,
    summary="Obtener usuario por ID"
)
async def read_user(
    user_id: int,
    session: session_dep,
    current_user: user_dep
):
    """Obtiene un usuario específico por ID (solo admin puede ver otros usuarios)."""
    if current_user.role != models.Role.ADMIN and getattr(current_user, "admin_id", None) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden ver otros usuarios"
        )

    user_models = {
        models.Role.STUDENT: models.Student,
        models.Role.PROFESSOR: models.Professor,
        models.Role.ADMIN: models.Admin
    }

    for role, model in user_models.items():
        user = session.get(model, user_id)
        if user:
            if role == models.Role.STUDENT:
                return schemas.StudentPublic.model_validate(user)
            elif role == models.Role.PROFESSOR:
                return schemas.ProfessorPublic.model_validate(user)
            else:
                return schemas.AdminPublic.model_validate(user)

    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@router.patch(
    "/{user_id}",
    response_model=schemas.UserPublic,
    summary="Actualizar usuario"
)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,  # Necesitarás crear este schema
    session: session_dep,
    current_user: user_dep
):
    """Actualiza datos de usuario (solo admin o el propio usuario)."""
    pass  # Implementar lógica similar a read_user pero con actualización

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario"
)
async def delete_user(
    user_id: int,
    session: session_dep,
    current_user: admin_dep  # Solo admin puede eliminar
):
    """Elimina un usuario (solo administradores)."""
    pass
