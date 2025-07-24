import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session
from app.main_factory import create_app
from app import models
from app.db import engine

@pytest.fixture
def test_app():
    return create_app()

@pytest.mark.asyncio
async def test_inscribir_dos_veces(test_app, test_student, test_professor, professor_token):  # Cambiar student_token por professor_token
    with Session(engine) as session:
        score = models.Score(materia="Física I", professor_id=test_professor.user_id)
        session.add(score)
        session.commit()
        session.refresh(score)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post(
            f"/materias/{score.score_id}/inscribir?student_id={test_student.user_id}",
            headers={"Authorization": f"Bearer {professor_token}"}  # Usar professor_token
        )
        r2 = await client.post(
            f"/materias/{score.score_id}/inscribir?student_id={test_student.user_id}",
            headers={"Authorization": f"Bearer {professor_token}"}  # Usar professor_token
        )
        assert r1.status_code == 200
        assert r2.status_code == 409  # Cambiar a 409 que es más específico para conflictos

@pytest.mark.asyncio
async def test_inscribir_materia_inexistente(test_app, student_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/materias/9999/inscribirse", headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 404

@pytest.mark.asyncio
async def test_buscar_materia_por_id(test_app, test_professor, professor_token):
    with Session(engine) as session:
        score = models.Score(materia="Estadística", professor_id=test_professor.user_id)
        session.add(score)
        session.commit()
        session.refresh(score)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(f"/materias/{score.score_id}", headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 200
        assert r.json()["materia"] == "Estadística"

@pytest.mark.asyncio
async def test_filtrar_materias_por_estudiante(test_app, test_student, test_professor, student_token):
    with Session(engine) as session:
        score = models.Score(materia="Lógica", professor_id=test_professor.user_id)
        session.add(score)
        session.commit()
        session.refresh(score)
        link = models.StudentScoreLink(student_id=test_student.user_id, score_id=score.score_id)
        session.add(link)
        session.commit()

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(f"/materias/?estudiante_id={test_student.user_id}", headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 200
        assert any(m["materia"] == "Lógica" for m in r.json())