import pytest
from datetime import date
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session
from app import models
from app.db import engine


@pytest.mark.asyncio
async def test_token_invalido(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/usuarios/me", headers={"Authorization": "Bearer token_invalido"})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_estudiante_accede_a_recurso_admin(test_app, student_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/usuarios/", headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_tipo_calificacion_invalido(test_app, test_professor, professor_token, test_student):
    with Session(engine) as session:
        score = models.Score(materia="Física", professor_id=test_professor.user_id)
        session.add(score)
        session.commit()
        session.refresh(score)

    bad_data = {
        "valor": 75,
        "tipo": "invalido",  # tipo inválido
        "comentario": "Debe fallar",
        "student_id": test_student.user_id,
        "score_id": score.score_id,
        "fecha": str(date.today())
    }

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/calificaciones/", json=bad_data, headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 422


@pytest.mark.asyncio
async def test_eliminar_calificacion_otro_profesor(test_app, test_student, test_professor, professor_token, db):
    otro_profesor = models.User(
        name_complete="Otro Profesor",
        name_user="otro_prof",
        cedula="99999999",
        email="otro@prof.com",
        gender="male",
        role="professor",
        hashed_password="hashed"
    )
    db.add(otro_profesor)
    db.commit()
    db.refresh(otro_profesor)

    score = models.Score(materia="Química", professor_id=otro_profesor.user_id)
    db.add(score)
    db.commit()
    db.refresh(score)

    cal = models.Calificacion(
        valor=80,
        tipo=models.CalificacionTipo.PARCIAL,
        comentario="Nota externa",
        student_id=test_student.user_id,
        score_id=score.score_id,
        professor_id=otro_profesor.user_id
    )
    db.add(cal)
    db.commit()
    db.refresh(cal)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.delete(f"/calificaciones/{cal.calificacion_id}", headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 403
