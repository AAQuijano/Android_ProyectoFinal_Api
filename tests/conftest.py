import pytest
from sqlmodel import Session, select
from app.auth import create_access_token
from app import models
@pytest.fixture
async def test_student(db: Session):
    student = models.Student(
        name_complete="Estudiante Test",
        name_user="student_test",
        cedula="11111111",
        email="student@test.com",
        gender="male",
        role="student",
        hashed_password="hashed123"
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    yield student
    db.delete(student)
    db.commit()

@pytest.fixture
async def test_other_student(db: Session):
    student = models.Student(
        name_complete="Otro Estudiante",
        name_user="other_student",
        cedula="22222222",
        email="other@test.com",
        gender="female",
        role="student",
        hashed_password="hashed123"
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    yield student
    db.delete(student)
    db.commit()

@pytest.fixture
async def test_admin(db: Session):
    admin = models.Admin(
        name_complete="Admin Test",
        name_user="admin_test",
        cedula="33333333",
        email="admin@test.com",
        gender="male",
        role="admin",
        hashed_password="hashed123"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    yield admin
    db.delete(admin)
    db.commit()

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