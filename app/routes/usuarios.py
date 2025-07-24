#usuarios.py
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from app import models, schemas
from app.db import get_db
from app.auth import get_current_user, get_current_admin_user
from typing import Annotated, Union, Optional

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# Dependencias reutilizables
session_dep = Annotated[Session, Depends(get_db)]
user_dep = Annotated[Union[models.Student,models.Professor,models.Admin], Depends(get_current_user)]
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


@router.patch("/{user_id}", response_model=schemas.UserPublic)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    session: session_dep,
    current_user: user_dep
):
    # 🔒 1. Validar permisos
    if current_user.role != models.Role.ADMIN:
        if (
            (current_user.role == models.Role.STUDENT and user_id != current_user.student_id)
            or (current_user.role == models.Role.PROFESSOR and user_id != current_user.professor_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes modificar tu propio perfil"
            )

    # 🔍 2. Buscar al usuario destino por ID en todos los modelos
    user = None
    for model in [models.Student, models.Professor, models.Admin]:
        user = session.get(model, user_id)
        if user:
            break

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 🔁 3. Aplicar cambios
    update_data = user_update.model_dump(exclude_unset=True)
    if 'password' in update_data:
        update_data['hashed_password'] = models.pwd_context.hash(update_data.pop('password'))

    for key, value in update_data.items():
        setattr(user, key, value)

    session.commit()
    session.refresh(user)

    # ✅ 4. Retornar con schema adecuado
    if isinstance(user, models.Student):
        return schemas.StudentPublic.model_validate(user)
    elif isinstance(user, models.Professor):
        return schemas.ProfessorPublic.model_validate(user)
    return schemas.AdminPublic.model_validate(user)



@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: session_dep,
    current_user: admin_dep
):
    # Verificar si el usuario existe antes de intentar eliminarlo
    user = None
    for model in [models.Student, models.Professor, models.Admin]:
        user = session.get(model, user_id)
        if user:
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Si existe, proceder con la eliminación
    session.delete(user)
    session.commit()
    return

@router.get("/", response_model=list[schemas.UserPublic])
async def list_users(
    session: session_dep,
    current_user: admin_dep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100)
):
    # Asegurarnos de que cada query aplica la paginación
    users = []
    for model in [models.Student, models.Professor, models.Admin]:
        query = select(model).order_by(model.name_user).offset(skip).limit(limit)
        result = session.exec(query)
        users.extend(result.all())
    
    return [
        schemas.StudentPublic.model_validate(u) if isinstance(u, models.Student)
        else schemas.ProfessorPublic.model_validate(u) if isinstance(u, models.Professor)
        else schemas.AdminPublic.model_validate(u)
        for u in users
    ]