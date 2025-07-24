#test_usuarios.py
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import date
from fastapi import status
from sqlmodel import Session, select
from app.main_factory import create_app
from app import models
from app.db import engine
from app.auth import create_access_token

@pytest.fixture
def test_app():
    return create_app()

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    models.SQLModel.metadata.create_all(engine)
    yield
    models.SQLModel.metadata.drop_all(engine)

@pytest.fixture
def test_student():
    with Session(engine) as session:
        student = models.User(
            name_complete="Student Test",
            name_user="student_test",
            cedula="22222222",
            email="student@test.com",
            gender="female",
            role="student",
            hashed_password="hashed123"
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        yield student
        session.delete(student)
        session.commit()

@pytest.fixture
def test_professor():
    with Session(engine) as session:
        professor = models.User(
            name_complete="Professor Test",
            name_user="professor_test",
            cedula="33333333",
            email="professor@test.com",
            gender="male",
            role="professor",
            specialization="Math",
            hashed_password="hashed123"
        )
        session.add(professor)
        session.commit()
        session.refresh(professor)
        yield professor
        session.delete(professor)
        session.commit()

@pytest.fixture
def test_admin():
    with Session(engine) as session:
        admin = models.User(
            name_complete="Admin Test",
            name_user="admin_test",
            cedula="11111111",
            email="admin@test.com",
            gender="male",
            role="admin",
            hashed_password="hashed123"
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        yield admin
        session.delete(admin)
        session.commit()

@pytest.fixture
def student_token(test_student):
    return create_access_token({
        "sub": test_student.name_user,
        "role": test_student.role,
        "user_id": test_student.user_id
    })

@pytest.fixture
def professor_token(test_professor):
    return create_access_token({
        "sub": test_professor.name_user,
        "role": test_professor.role,
        "user_id": test_professor.user_id
    })

@pytest.fixture
def admin_token(test_admin):
    return create_access_token({
        "sub": test_admin.name_user,
        "role": test_admin.role,
        "user_id": test_admin.user_id
    })

@pytest.mark.asyncio
async def test_create_user(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/usuarios/",
            json={
                "name_complete": "New User",
                "name_user": "new_user",
                "cedula": "12345678",
                "email": "new@user.com",
                "gender": "male",
                "birth_date": "1995-01-01",
                "password": "password123",
                "role": "student"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name_user"] == "new_user"
        assert "user_id" in data

@pytest.mark.asyncio
async def test_read_current_user(test_app, student_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/usuarios/me",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name_user"] == "student_test"

@pytest.mark.asyncio
async def test_get_user_as_admin(test_app, admin_token, test_student):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/usuarios/{test_student.user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name_user"] == "student_test"

@pytest.mark.asyncio
async def test_get_user_no_admin(test_app, student_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/usuarios/9999",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_update_user_self(test_app, student_token, test_student):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/usuarios/{test_student.user_id}",
            json={"name_complete": "Updated Name"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name_complete"] == "Updated Name"

@pytest.mark.asyncio
async def test_update_user_as_admin(test_app, admin_token, test_student):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/usuarios/{test_student.user_id}",
            json={"email": "updated@email.com"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == "updated@email.com"

@pytest.mark.asyncio
async def test_delete_user_as_admin(test_app, admin_token):
    with Session(engine) as session:
        student = models.User(
            name_complete="Student To Delete",
            name_user="del_user",
            cedula="22221111",
            email="del@test.com",
            gender="female",
            role="student",
            hashed_password="hashed123"
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        student_id = student.user_id

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/usuarios/{student_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.asyncio
async def test_list_users_as_admin(test_app, admin_token, test_student, test_professor, test_admin):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/usuarios/",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"skip": 0, "limit": 10}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        usernames = {user["name_user"] for user in data}
        assert "student_test" in usernames
        assert "professor_test" in usernames
        assert "admin_test" in usernames

@pytest.mark.asyncio
async def test_historial_dentro_de_usuarios(test_app, test_student, test_professor, student_token):
    # Crear materia y calificaciones
    with Session(engine) as session:
        score = models.Score(materia="Historia", professor_id=test_professor.user_id)
        session.add(score)
        session.commit()
        session.refresh(score)
        score_id = score.score_id  # 🔁 Ahora sí puedes usarlo

        for val in [70, 80, 90]:
            cal = models.Calificacion(
                valor=val,
                tipo=models.CalificacionTipo.QUIZ,
                fecha=date.today(),
                student_id=test_student.user_id,
                score_id=score_id,
                professor_id=test_professor.user_id
            )
            session.add(cal)
        session.commit()

    # Ejecutar la petición
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/usuarios/{test_student.user_id}/historial",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert any(d["materia"] == "Historia" for d in data)
        assert any(round(d["promedio"], 2) == 80.0 for d in data)

    # Limpieza final segura
    with Session(engine) as session:
        # Eliminar calificaciones asociadas
        stmt_cals = select(models.Calificacion).where(models.Calificacion.score_id == score_id)
        cals = session.exec(stmt_cals).all()
        for cal in cals:
            session.delete(cal)

        # Eliminar materia
        score = session.get(models.Score, score_id)
        if score:
            session.delete(score)
        session.commit()
