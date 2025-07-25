import pytest
from app.schemas import UserCreate
from app.models import Role, Gender
from datetime import date


def test_usercreate_validates_specialization_ok():
    user = UserCreate(
        name_complete="Ana Profe",
        name_user="ana_profe",
        cedula="1234567",
        email="ana@profe.com",
        gender=Gender.FEMALE,
        birth_date=date(1990, 5, 17),
        password="secure123",
        role=Role.PROFESSOR,
        specialization="Física"
    )
    assert user.specialization == "Física"


def test_usercreate_fails_without_specialization():
    with pytest.raises(ValueError) as excinfo:
        UserCreate(
            name_complete="Juan Profe",
            name_user="juan_profe",
            cedula="7654321",
            email="juan@profe.com",
            gender=Gender.MALE,
            birth_date=date(1985, 3, 9),
            password="clave456",
            role=Role.PROFESSOR,
            specialization=None
        )
    assert "Specialization is required for professors" in str(excinfo.value)
