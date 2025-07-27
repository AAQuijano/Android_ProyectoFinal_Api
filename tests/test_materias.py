
import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session
from app.main_factory import create_app
from app import models
from app.db import engine
from app.auth.auth import create_access_token

@pytest.fixture
def test_app():
    return create_app()

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    models.SQLModel.metadata.create_all(engine)
    yield
    models.SQLModel.metadata.drop_all(engine)

@pytest.fixture
def test_professor():
    with Session(engine) as session:
        user = models.User(
            name_complete="Prof",
            name_user="prof_user",
            cedula="77777777",
            email="prof@example.com",
            gender="male",
            role="professor",
            specialization="Physics",
            hashed_password="hashed123"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

@pytest.fixture
def test_student():
    with Session(engine) as session:
        user = models.User(
            name_complete="Stud",
            name_user="stud_user",
            cedula="88888888",
            email="stud@example.com",
            gender="female",
            role="student",
            hashed_password="hashed123"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

@pytest.fixture
def professor_token(test_professor):
    return create_access_token({
        "sub": test_professor.name_user,
        "role": test_professor.role,
        "user_id": test_professor.user_id
    })

@pytest.mark.asyncio
async def test_crud_score(test_app, test_professor, professor_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Crear materia
        payload = {
            "materia": "Álgebra",
            "description": "Vectores y matrices",
            "professor_id": test_professor.user_id
        }
        response = await client.post("/materias/", json=payload, headers={"Authorization": f"Bearer {professor_token}"})
        assert response.status_code == 201
        score = response.json()
        score_id = score["score_id"]

        # Listar
        response = await client.get("/materias/")
        assert response.status_code == 200
        assert any(s["score_id"] == score_id for s in response.json())

        # Obtener individual
        response = await client.get(f"/materias/{score_id}")
        assert response.status_code == 200

        # Actualizar
        payload["description"] = "Actualizado"
        response = await client.patch(f"/materias/{score_id}", json=payload, headers={"Authorization": f"Bearer {professor_token}"})
        assert response.status_code == 200
        assert response.json()["description"] == "Actualizado"

        # Eliminar
        response = await client.delete(f"/materias/{score_id}", headers={"Authorization": f"Bearer {professor_token}"})
        assert response.status_code == 204

@pytest.mark.asyncio
async def test_inscripcion_y_desinscripcion(test_app, test_professor, test_student, professor_token):
    with Session(engine) as session:
        score = models.Score(materia="Física", professor_id=test_professor.user_id)
        session.add(score)
        session.commit()
        session.refresh(score)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Inscribir
        response = await client.post(
            f"/materias/{score.score_id}/inscribir?student_id={test_student.user_id}",
            headers={"Authorization": f"Bearer {professor_token}"}
        )
        assert response.status_code == 200

        # Ver inscritos
        response = await client.get(f"/materias/{score.score_id}/estudiantes", headers={"Authorization": f"Bearer {professor_token}"})
        assert response.status_code == 200
        assert any(s["user_id"] == test_student.user_id for s in response.json())

        # Desinscribir
        response = await client.delete(
            f"/materias/{score.score_id}/estudiantes/{test_student.user_id}",
            headers={"Authorization": f"Bearer {professor_token}"}
        )
        assert response.status_code == 204
