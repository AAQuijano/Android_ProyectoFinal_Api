#schemas.py
from datetime import date
from enum import Enum
from typing import Optional, Annotated, Union
from sqlmodel import SQLModel
from pydantic import EmailStr, StringConstraints, field_validator
from app.models import Role, Gender, CalificacionTipo

# Tipos validados con restricciones
CedulaStr = Annotated[str, StringConstraints(min_length=7, max_length=12)]
PhoneStr = Annotated[str, StringConstraints(min_length=7, max_length=15)]

# ------------------------------------------
# Esquemas de Autenticación
# ------------------------------------------

class Token(SQLModel):
    """Esquema para respuesta de token de autenticación"""
    access_token: str
    token_type: str = "bearer"

class TokenData(SQLModel):
    """Datos contenidos en el token JWT"""
    sub: str
    role: Role

class UserLogin(SQLModel):
    """Esquema para el endpoint de login"""
    username: str
    password: str

# ------------------------------------------
# Esquemas de Usuario
# ------------------------------------------

class UserCreate(SQLModel):
    """Esquema para creación de usuarios"""
    name_complete: str
    name_user: str
    cedula: CedulaStr
    email: EmailStr
    gender: Gender
    birth_date: Optional[date] = None
    password: str
    role: Role
    specialization: Optional[str] = None

    @field_validator('specialization')
    def validate_specialization(cls, v, values):
        """Valida que los profesores tengan especialización"""
        if 'role' in values and values['role'] == Role.PROFESSOR and not v:
            raise ValueError("Specialization is required for professors")
        return v

class UserPublicBase(SQLModel):
    """Campos base compartidos para la vista pública de usuarios"""
    user_id: int
    name_complete: str
    name_user: str
    cedula: str
    email: str
    gender: Gender
    birth_date: Optional[date] = None
    age: Optional[int] = None
    role: Role

class UserPublic(UserPublicBase):
    """Esquema público completo para usuarios (incluye campos específicos por rol)"""
    specialization: Optional[str] = None

class UserUpdate(SQLModel):
    """Esquema para actualización parcial de usuarios"""
    name_complete: Optional[str] = None
    email: Optional[EmailStr] = None
    birth_date: Optional[date] = None
    specialization: Optional[str] = None
    password: Optional[str] = None


# ------------------------------------------
# Esquemas de Materias y Calificaciones
# ------------------------------------------

class ScoreBase(SQLModel):
    """Esquema base para materias"""
    materia: str
    description: Optional[str] = None

class ScoreCreate(ScoreBase):
    """Esquema para creación de materias"""
    professor_id: int

class ScorePublic(ScoreBase):
    """Esquema público para materias"""
    score_id: int
    professor_id: int

class CalificacionBase(SQLModel):
    """Esquema base para calificaciones"""
    valor: float
    tipo: CalificacionTipo
    fecha: date
    comentario: Optional[str] = None

class CalificacionCreate(CalificacionBase):
    """Esquema para creación de calificaciones"""
    student_id: int
    score_id: int
    professor_id: int

class CalificacionPublic(CalificacionBase):
    """Esquema público para calificaciones"""
    calificacion_id: int
    student_id: int
    score_id: int
    professor_id: int