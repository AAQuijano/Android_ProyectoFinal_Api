import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main_factory import create_app
from app import models
from app.db import get_db, engine
from app.auth import create_access_token

# Configuración inicial
app = create_app()
client = TestClient(app)

# Fixtures para la base de datos
@pytest.fixture(scope="function", autouse=True)
def setup_db():
    models.SQLModel.metadata.create_all(engine)
    yield
    models.SQLModel.metadata.drop_all(engine)

# Fixtures de datos
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

@pytest.fixture
def student_token(test_student):
    return create_access_token(
        data={
            "sub": test_student.name_user,
            "role": test_student.role,
            "user_id": test_student.student_id
        }
    )

@pytest.fixture
def admin_token(test_admin):
    return create_access_token(
        data={
            "sub": test_admin.name_user,
            "role": test_admin.role,
            "user_id": test_admin.admin_id
        }
    )

# ---- Tests ----
def test_create_user():
    response = client.post(
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

def test_read_current_user(student_token):
    response = client.get(
        "/usuarios/me",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name_user"] == "student_test"

def test_get_user_as_admin(admin_token, test_student):
    response = client.get(
        f"/usuarios/{test_student.student_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name_user"] == "student_test"

def test_get_user_no_admin(student_token):
    response = client.get(
        "/usuarios/1",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_delete_user_not_admin(student_token):
    response = client.delete(
        "/usuarios/1",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN