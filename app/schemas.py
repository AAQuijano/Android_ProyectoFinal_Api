from datetime import date
from enum import Enum
from typing import Optional, Annotated, Union
from sqlmodel import SQLModel
from pydantic import EmailStr, StringConstraints

# Tipos validados con restricciones
CedulaStr = Annotated[str, StringConstraints(min_length=7, max_length=12)]
PhoneStr = Annotated[str, StringConstraints(min_length=7, max_length=15)]

# Enums de dominio
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class Role(str, Enum):
    STUDENT = "student"
    PROFESSOR = "professor"
    ADMIN = "admin"

# Tokens de autenticación
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(SQLModel):
    sub: str
    role: Role

class UserLogin(SQLModel):
    username: str
    password: str

# Registro genérico de usuario
class UserCreate(SQLModel):
    name_complete: str
    name_user: str
    cedula: CedulaStr
    email: EmailStr
    gender: Gender
    birth_date: Optional[date] = None
    password: str
    role: Role
    specialization: Optional[str] = None  # Solo para profesores

# Vistas públicas por rol
class StudentPublic(SQLModel):
    student_id: int
    name_complete: str
    name_user: str
    cedula: str
    email: str
    gender: str
    birth_date: Optional[date] = None
    age: Optional[int] = None
    role: str

class ProfessorPublic(SQLModel):
    professor_id: int
    name_complete: str
    name_user: str
    cedula: str
    email: str
    gender: str
    birth_date: Optional[date] = None
    age: Optional[int] = None
    role: str
    specialization: str

class AdminPublic(SQLModel):
    admin_id: int
    name_complete: str
    name_user: str
    cedula: str
    email: str
    gender: str
    birth_date: Optional[date] = None
    age: Optional[int] = None
    role: str

# Unión para uso genérico de respuestas
UserPublic = Union[StudentPublic, ProfessorPublic, AdminPublic]
