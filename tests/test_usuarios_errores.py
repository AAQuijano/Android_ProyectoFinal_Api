
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlmodel import Session
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
def admin_token():
    with Session(engine) as session:
        admin = models.User(
            name_complete="Admin",
            name_user="admin_user",
            cedula="10000001",
            email="admin@example.com",
            gender="male",
            role="admin",
            hashed_password="hashed123"
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return create_access_token({
            "sub": admin.name_user,
            "role": admin.role,
            "user_id": admin.user_id
        })

@pytest.mark.asyncio
async def test_duplicate_email(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name_complete": "User 1",
            "name_user": "user1",
            "cedula": "99999999",
            "email": "duplicate@test.com",
            "gender": "male",
            "birth_date": "1990-01-01",
            "password": "pass123",
            "role": "student"
        }
        await client.post("/usuarios/", json=payload)
        response = await client.post("/usuarios/", json=payload)
        assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_create_professor_without_specialization(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name_complete": "Prof Invalido",
            "name_user": "prof_fail",
            "cedula": "12345679",
            "email": "prof@example.com",
            "gender": "male",
            "birth_date": "1980-01-01",
            "password": "pass123",
            "role": "professor"
        }
        response = await client.post("/usuarios/", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_get_nonexistent_user(test_app, admin_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/usuarios/9999", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_nonexistent_user(test_app, admin_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete("/usuarios/9999", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_nonexistent_user(test_app, admin_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/usuarios/9999",
            json={"email": "update@test.com"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_list_users_no_admin_access(test_app):
    with Session(engine) as session:
        student = models.User(
            name_complete="NonAdmin",
            name_user="nonadmin",
            cedula="88888888",
            email="nonadmin@example.com",
            gender="female",
            role="student",
            hashed_password="hashed123"
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        token = create_access_token({
            "sub": student.name_user,
            "role": student.role,
            "user_id": student.user_id
        })

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/usuarios/", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
