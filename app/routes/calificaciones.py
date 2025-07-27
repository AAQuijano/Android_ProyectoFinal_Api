
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from app import models, schemas
from app.db import get_db
from app.auth.auth import get_current_user, get_current_professor_user
from typing import Annotated, List

router = APIRouter(prefix="/calificaciones", tags=["calificaciones"])

session_dep = Annotated[Session, Depends(get_db)]
professor_dep = Annotated[models.User, Depends(get_current_professor_user)]
user_dep = Annotated[models.User, Depends(get_current_user)]


@router.post("/", response_model=schemas.CalificacionPublic, status_code=status.HTTP_201_CREATED)
def create_calificacion(cal: schemas.CalificacionCreate, session: session_dep, current_user: professor_dep):
    # Validar tipo de calificación
    try:
        cal.tipo = models.CalificacionTipo(cal.tipo)
    except ValueError:
        raise HTTPException(status_code=422, detail="Tipo de calificación inválido")

    # Validar duplicado
    existing_cal = session.exec(
        select(models.Calificacion).where(
            models.Calificacion.student_id == cal.student_id,
            models.Calificacion.score_id == cal.score_id,
            models.Calificacion.tipo == cal.tipo
        )
    ).first()

    if existing_cal:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una calificación de este tipo para el estudiante en esta materia"
        )

    # Crear la calificación con el profesor del token
    db_cal = models.Calificacion(
        **cal.model_dump(),
        professor_id=current_user.user_id  # Añadir el professor_id del usuario autenticado
    )

    session.add(db_cal)
    session.commit()
    session.refresh(db_cal)
    return db_cal

@router.get("/{calificacion_id}", response_model=schemas.CalificacionPublic)
def get_calificacion(calificacion_id: int, session: session_dep):
    cal = session.get(models.Calificacion, calificacion_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    return cal


@router.patch("/{calificacion_id}", response_model=schemas.CalificacionPublic)
def update_calificacion(calificacion_id: int, update: schemas.CalificacionCreate, session: session_dep, current_user: professor_dep):
    cal = session.get(models.Calificacion, calificacion_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    if cal.professor_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="No puedes modificar calificaciones de otro profesor")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cal, key, value)
    session.commit()
    session.refresh(cal)
    return cal


@router.delete("/{calificacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calificacion(calificacion_id: int, session: session_dep, current_user: professor_dep):
    cal = session.get(models.Calificacion, calificacion_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    if cal.professor_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="No puedes eliminar calificaciones de otro profesor")
    session.delete(cal)
    session.commit()


@router.get("/", response_model=List[schemas.CalificacionPublic])
def list_calificaciones(session: session_dep):
    return session.exec(select(models.Calificacion)).all()


@router.get("/por_estudiante/{student_id}", response_model=List[schemas.CalificacionPublic])
def calificaciones_por_estudiante(student_id: int, session: session_dep, current_user: user_dep):
    user = session.get(models.User, student_id)
    if not user or user.role != models.Role.STUDENT:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return session.exec(
        select(models.Calificacion).where(models.Calificacion.student_id == student_id)
    ).all()


@router.get("/por_materia/{score_id}", response_model=List[schemas.CalificacionPublic])
def calificaciones_por_materia(score_id: int, session: session_dep):
    return session.exec(
        select(models.Calificacion).where(models.Calificacion.score_id == score_id)
    ).all()
