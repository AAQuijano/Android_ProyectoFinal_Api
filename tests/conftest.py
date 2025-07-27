import pytest
from sqlmodel import Session, SQLModel
from app.db import engine
from app.auth.auth import create_access_token
from app import models
import warnings
from sqlalchemy import exc as sa_exc
from app.main_factory import create_app


@pytest.fixture
def test_app():
    return create_app()

@pytest.fixture
def db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(autouse=True)
def suppress_sqlalchemy_warnings():
    warnings.filterwarnings(
        "ignore",
        category=sa_exc.SAWarning,
        message="DELETE statement on table.*expected to delete.*"
    )

@pytest.fixture
def test_student(db: Session):
    student = models.User(
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
    return student

@pytest.fixture
def test_professor(db: Session):
    prof = models.User(
        name_complete="Profesor Test",
        name_user="prof_test",
        cedula="44444444",
        email="prof@test.com",
        gender="male",
        role="professor",
        hashed_password="hashed123"
    )
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return prof

@pytest.fixture
def test_admin(db: Session):
    admin = models.User(
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
    return admin

@pytest.fixture
def student_token(test_student):
    return create_access_token(
        data={
            "sub": test_student.name_user,
            "role": test_student.role,
            "user_id": test_student.user_id
        }
    )

@pytest.fixture
def professor_token(test_professor):
    return create_access_token(
        data={
            "sub": test_professor.name_user,
            "role": test_professor.role,
            "user_id": test_professor.user_id
        }
    )

@pytest.fixture
def admin_token(test_admin):
    return create_access_token(
        data={
            "sub": test_admin.name_user,
            "role": test_admin.role,
            "user_id": test_admin.user_id
        }
    )