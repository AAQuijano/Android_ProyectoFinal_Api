from app.models import CalificacionTipo
import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session, select
from app.main_factory import create_app
from app import models
from app.db import engine
from datetime import date

@pytest.fixture
def test_app():
    return create_app()

@pytest.mark.asyncio
async def test_get_nonexistent_calificacion(test_app, student_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/calificaciones/9999", headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 404

@pytest.mark.asyncio
async def test_create_calificacion_invalid_tipo(test_app, test_student, test_professor, professor_token):
    with Session(engine) as session:
        score = models.Score(materia="Cálculo II", professor_id=test_professor.user_id)
        session.add(score)
        session.commit()
        session.refresh(score)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cal_data = {
            "valor": 95,
            "tipo": "examen_final",  # inválido
            "comentario": "Excelente",
            "student_id": test_student.user_id,
            "score_id": score.score_id
        }
        r = await client.post("/calificaciones/", json=cal_data, headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 422

@pytest.mark.asyncio
async def test_duplicate_calificacion_for_same_score(test_app, test_student, test_professor, professor_token):
    with Session(engine) as session:
        score = models.Score(materia="Química", professor_id=test_professor.user_id)
        session.add(score)
        session.commit()
        session.refresh(score)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cal_data = {
            "valor": 80,
            "tipo": CalificacionTipo.PARCIAL.value,
            "comentario": "Primera nota",
            "student_id": test_student.user_id,
            "score_id": score.score_id,
            "fecha": str(date.today())
            
        }
        r1 = await client.post("/calificaciones/", json=cal_data, headers={"Authorization": f"Bearer {professor_token}"})
        r2 = await client.post("/calificaciones/", json=cal_data, headers={"Authorization": f"Bearer {professor_token}"})
        assert r1.status_code == 201
        assert r2.status_code == 409, f"Se esperaba 409, se recibió {r2.status_code}: {r2.text}"
