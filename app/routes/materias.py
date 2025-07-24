
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, col
from app import models, schemas
from app.db import get_db
from app.auth import get_current_user, get_current_professor_user, get_current_admin_user
from typing import Annotated

router = APIRouter(prefix="/materias", tags=["materias"])

session_dep = Annotated[Session, Depends(get_db)]
professor_dep = Annotated[models.User, Depends(get_current_professor_user)]
admin_dep = Annotated[models.User, Depends(get_current_admin_user)]
user_dep = Annotated[models.User, Depends(get_current_user)]


@router.post("/", response_model=schemas.ScorePublic, status_code=status.HTTP_201_CREATED)
def create_score(score: schemas.ScoreCreate, session: session_dep, current_user: professor_dep):
    if current_user.user_id != score.professor_id:
        raise HTTPException(status_code=403, detail="No puedes registrar materias para otros profesores")
    db_score = models.Score(**score.model_dump())
    session.add(db_score)
    session.commit()
    session.refresh(db_score)
    return db_score


@router.get("/", response_model=list[schemas.ScorePublic])
def list_scores(session: session_dep):
    scores = session.exec(select(models.Score)).all()
    return scores


@router.get("/{score_id}", response_model=schemas.ScorePublic)
def get_score(score_id: int, session: session_dep):
    score = session.get(models.Score, score_id)
    if not score:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return score


@router.patch("/{score_id}", response_model=schemas.ScorePublic)
def update_score(score_id: int, score_update: schemas.ScoreCreate, session: session_dep, current_user: professor_dep):
    score = session.get(models.Score, score_id)
    if not score:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    if score.professor_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Solo puedes modificar tus propias materias")

    update_data = score_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(score, key, value)

    session.commit()
    session.refresh(score)
    return score


@router.delete("/{score_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_score(score_id: int, session: session_dep, current_user: professor_dep):
    score = session.get(models.Score, score_id)
    if not score:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    if score.professor_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Solo puedes eliminar tus propias materias")
    session.delete(score)
    session.commit()


@router.get("/{score_id}/estudiantes", response_model=list[schemas.UserPublic])
def list_score_students(score_id: int, session: session_dep, current_user: user_dep):
    score = session.get(models.Score, score_id)
    if not score:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return [schemas.UserPublic.model_validate(s) for s in score.students]


@router.post("/{score_id}/inscribir", status_code=status.HTTP_200_OK)
def enroll_student(score_id: int, student_id: int, session: session_dep, current_user: professor_dep):
    score = session.get(models.Score, score_id)
    student = session.get(models.User, student_id)
    if not score or not student:
        raise HTTPException(status_code=404, detail="Materia o estudiante no encontrado")
    if student in score.students:
        raise HTTPException(status_code=409, detail="El estudiante ya está inscrito en esta materia")
    score.students.append(student)
    session.commit()
    return {"message": "Estudiante inscrito exitosamente"}


@router.delete("/{score_id}/estudiantes/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def unenroll_student(score_id: int, student_id: int, session: session_dep, current_user: professor_dep):
    score = session.get(models.Score, score_id)
    if not score:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    student = next((s for s in score.students if s.user_id == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no inscrito")
    score.students.remove(student)
    session.commit()


@router.get("/{score_id}/calificaciones", response_model=list[schemas.CalificacionPublic])
def get_score_grades(score_id: int, session: session_dep, current_user: user_dep):
    score = session.get(models.Score, score_id)
    if not score:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return [schemas.CalificacionPublic.model_validate(c) for c in score.calificaciones]
