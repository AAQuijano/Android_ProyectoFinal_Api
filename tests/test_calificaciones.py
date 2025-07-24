
import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session
from app.main_factory import create_app
from app import models
from app.db import engine
from app.auth import create_access_token
from datetime import date

@pytest.fixture
def test_app():
    return create_app()

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    models.SQLModel.metadata.create_all(engine)
    yield
    models.SQLModel.metadata.drop_all(engine)

@pytest.fixture
def profesor_y_token():
    with Session(engine) as session:
        user = models.User(
            name_complete="Profe Cal",
            name_user="profe_cal",
            cedula="90000000",
            email="profe@cal.com",
            gender="male",
            role="professor",
            specialization="Química",
            hashed_password="hashed"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token({
            "sub": user.name_user,
            "role": user.role,
            "user_id": user.user_id
        })
        return user, token

@pytest.fixture
def estudiante():
    with Session(engine) as session:
        user = models.User(
            name_complete="Estu",
            name_user="estu_cal",
            cedula="90111111",
            email="estu@cal.com",
            gender="female",
            role="student",
            hashed_password="hashed"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

@pytest.fixture
def materia(profesor_y_token):
    prof, _ = profesor_y_token
    with Session(engine) as session:
        score = models.Score(materia="Bioquímica", professor_id=prof.user_id)
        session.add(score)
        session.commit()
        session.refresh(score)
        return score

@pytest.mark.asyncio
async def test_crud_calificacion(test_app, profesor_y_token, estudiante, materia):
    prof, token = profesor_y_token

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "valor": 88.0,
            "fecha": str(date.today()),
            "tipo": "parcial",
            "comentario": "Buen desempeño",
            "student_id": estudiante.user_id,
            "score_id": materia.score_id,
            "professor_id": prof.user_id
        }

        # Crear
        r = await client.post("/calificaciones/", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 201
        data = r.json()
        calificacion_id = data["calificacion_id"]

        # Obtener
        r = await client.get(f"/calificaciones/{calificacion_id}")
        assert r.status_code == 200

        # Editar
        payload["valor"] = 95.0
        r = await client.patch(f"/calificaciones/{calificacion_id}", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["valor"] == 95.0

        # Eliminar
        r = await client.delete(f"/calificaciones/{calificacion_id}", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 204

@pytest.mark.asyncio
async def test_filtros_por_estudiante_y_materia(test_app, profesor_y_token, estudiante, materia):
    prof, token = profesor_y_token
    with Session(engine) as session:
        cal = models.Calificacion(
            valor=77.0,
            tipo="quiz",
            fecha=date.today(),
            student_id=estudiante.user_id,
            score_id=materia.score_id,
            professor_id=prof.user_id
        )
        session.add(cal)
        session.commit()

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get(f"/calificaciones/por_estudiante/{estudiante.user_id}", headers={"Authorization": f"Bearer {token}"})
        assert r1.status_code == 200
        assert len(r1.json()) >= 1

        r2 = await client.get(f"/calificaciones/por_materia/{materia.score_id}")
        assert r2.status_code == 200
        assert len(r2.json()) >= 1
