import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlmodel import Session, select
from app.main_factory import create_app
from app import models
from app.db import engine
from app.auth import create_access_token

# Fixture de la aplicación para pruebas
@pytest.fixture
def test_app():
    return create_app()

# Base de datos para cada función
@pytest.fixture(scope="function", autouse=True)
def setup_db():
    models.SQLModel.metadata.create_all(engine)
    yield
    models.SQLModel.metadata.drop_all(engine)

# Usuarios de prueba
@pytest.fixture
def test_student():
    with Session(engine) as session:
        student = models.Student(
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
        professor = models.Professor(
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
        admin = models.Admin(
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

# Tokens
@pytest.fixture
def student_token(test_student):
    return create_access_token({
        "sub": test_student.name_user,
        "role": test_student.role,
        "user_id": test_student.student_id
    })

@pytest.fixture
def professor_token(test_professor):
    return create_access_token({
        "sub": test_professor.name_user,
        "role": test_professor.role,
        "user_id": test_professor.professor_id
    })

@pytest.fixture
def admin_token(test_admin):
    return create_access_token({
        "sub": test_admin.name_user,
        "role": test_admin.role,
        "user_id": test_admin.admin_id
    })

# ---- TESTS ----

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
        assert "student_id" in data

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
            f"/usuarios/{test_student.student_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name_user"] == "student_test"

@pytest.mark.asyncio
async def test_get_user_no_admin(test_app, student_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/usuarios/1",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_update_user_self(test_app, student_token, test_student):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/usuarios/{test_student.student_id}",
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
            f"/usuarios/{test_student.student_id}",
            json={"email": "updated@email.com"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == "updated@email.com"

@pytest.mark.asyncio
async def test_update_user_unauthorized(test_app):
    # 1. Crear estudiante
    with Session(engine) as session:
        student = models.Student(
            name_complete="Student X",
            name_user="student_x",
            cedula="11111111",
            email="studentx@example.com",
            gender="female",
            role="student",
            hashed_password="hashed123"
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        student_token = create_access_token({
            "sub": student.name_user,
            "role": student.role,
            "user_id": student.student_id
        })

    # 2. Crear profesor con ID distinto
    with Session(engine) as session:
        professor = models.Professor(
            name_complete="Profe Y",
            name_user="profe_y",
            cedula="99999999",
            email="profey@example.com",
            gender="male",
            role="professor",
            specialization="Math",
            hashed_password="hashed123"
        )
        session.add(professor)
        session.commit()
        session.refresh(professor)

    # 3. Intentar que el estudiante modifique al profesor
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/usuarios/{professor.professor_id}",
            json={"name_complete": "Should Fail"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        print("Status code:", response.status_code)
        print("Response body:", response.text)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Solo puedes modificar tu propio perfil" in response.json().get("detail", "")



@pytest.mark.asyncio
async def test_delete_user_as_admin(test_app, admin_token):
    # Crear el estudiante aquí
    with Session(engine) as session:
        student = models.Student(
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
        student_id = student.student_id

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/usuarios/{student_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.asyncio
async def test_delete_user_not_admin(test_app, student_token, test_professor):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/usuarios/{test_professor.professor_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


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
        assert len(data) == 3
        usernames = {user["name_user"] for user in data}
        assert "student_test" in usernames
        assert "professor_test" in usernames
        assert "admin_test" in usernames

@pytest.mark.asyncio
async def test_list_users_pagination(test_app, admin_token, test_student, test_professor, test_admin):
    with Session(engine) as session:
        for i in range(5):
            user = models.Student(
                name_complete=f"Extra Student {i}",
                name_user=f"extra_{i}",
                cedula=f"9999999{i}",
                email=f"extra{i}@test.com",
                gender="male",
                role="student",
                hashed_password="hashed123"
            )
            session.add(user)
        session.commit()

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/usuarios/",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"skip": 1, "limit": 3}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert all(
            "extra" in user["name_user"] or user["name_user"] in ["student_test", "professor_test", "admin_test"]
            for user in data
        )
