#usuarios.py
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from app import models, schemas
from app.db import get_db
from app.auth import get_current_user, get_current_admin_user
from typing import Annotated, Optional

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# Dependencias reutilizables
session_dep = Annotated[Session, Depends(get_db)]
user_dep = Annotated[models.User, Depends(get_current_user)]
admin_dep = Annotated[models.User, Depends(get_current_admin_user)]


def calculate_age(birth_date: Optional[date]) -> Optional[int]:
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


@router.post("/", response_model=schemas.UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, session: session_dep):
    try:
        # Verificar unicidad
        existing_user = session.exec(
            select(models.User).where(
                (models.User.email == user.email) |
                (models.User.name_user == user.name_user) |
                (models.User.cedula == user.cedula)
            )
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email, nombre de usuario o cédula ya están registrados"
            )

        # Validar especialización si es profesor
        if user.role == models.Role.PROFESSOR and not user.specialization:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Especialización requerida para profesores"
            )

        hashed_password = models.pwd_context.hash(user.password)
        age = calculate_age(user.birth_date)

        db_user = models.User(
            **user.model_dump(exclude={"password"}),
            hashed_password=hashed_password,
            age=age
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        return schemas.UserPublic.model_validate(db_user)

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {str(e)}"
        ) from e


@router.get("/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: user_dep):
    return schemas.UserPublic.model_validate(current_user)


@router.get("/{user_id}", response_model=schemas.UserPublic)
async def read_user(user_id: int, session: session_dep, current_user: user_dep):
    if current_user.role != models.Role.ADMIN and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este usuario"
        )
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return schemas.UserPublic.model_validate(user)


@router.patch("/{user_id}", response_model=schemas.UserPublic)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    session: session_dep,
    current_user: user_dep
):
    if current_user.role != models.Role.ADMIN and user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes modificar tu propio perfil"
        )

    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = user_update.model_dump(exclude_unset=True)
    if 'password' in update_data:
        update_data['hashed_password'] = models.pwd_context.hash(update_data.pop('password'))

    for key, value in update_data.items():
        setattr(user, key, value)

    session.commit()
    session.refresh(user)
    return schemas.UserPublic.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: session_dep, current_user: admin_dep):
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    session.delete(user)
    session.commit()


@router.get("/", response_model=list[schemas.UserPublic])
async def list_users(
    session: session_dep,
    current_user: admin_dep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100)
):
    users = session.exec(
        select(models.User).order_by(models.User.name_user).offset(skip).limit(limit)
    ).all()
    return [schemas.UserPublic.model_validate(u) for u in users]
