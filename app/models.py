from datetime import date
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from passlib.context import CryptContext
from enum import Enum

# Configuración de hasheo
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# Enums de uso general
class Role(str, Enum):
    STUDENT = "student"
    PROFESSOR = "professor"
    ADMIN = "admin"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class CalificacionTipo(str, Enum):
    PARCIAL = "parcial"
    NOTA_FINAL = "nota_final"
    PRACTICA = "practica"
    QUIZ = "quiz"
    LABORATORIO = "laboratorio"
    PROYECTO = "proyecto"
    SEMESTRAL = "semestral"
    TAREA = "tarea"
    PRESENTACION = "presentacion"

# Base para personas
class PersonBase(SQLModel):
    name_complete: str = Field(index=True)
    name_user: str = Field(unique=True, index=True)
    cedula: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    gender: Gender
    birth_date: Optional[date] = Field(default=None, index=True)
    age: Optional[int] = Field(default=None)

# Mixin para autenticación
class PasswordMixin:
    hashed_password: str

    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

# Relaciones entre estudiantes y materias
class StudentScoreLink(SQLModel, table=True):
    student_id: int = Field(foreign_key="student.student_id", primary_key=True)
    score_id: int = Field(foreign_key="score.score_id", primary_key=True)

# Modelos principales
class Student(PersonBase, PasswordMixin, table=True):
    student_id: Optional[int] = Field(default=None, primary_key=True)
    role: Role = Field(default=Role.STUDENT)
    scores: List["Score"] = Relationship(back_populates="students", link_model=StudentScoreLink)
    calificaciones: List["Calificacion"] = Relationship(back_populates="student")

class Professor(PersonBase, PasswordMixin, table=True):
    professor_id: Optional[int] = Field(default=None, primary_key=True)
    role: Role = Field(default=Role.PROFESSOR)
    specialization: str
    scores: List["Score"] = Relationship(back_populates="professor")
    calificaciones: List["Calificacion"] = Relationship(back_populates="professor")

class Admin(PersonBase, PasswordMixin, table=True):
    admin_id: Optional[int] = Field(default=None, primary_key=True)
    role: Role = Field(default=Role.ADMIN)

# Materias
class ScoreBase(SQLModel):
    materia: str = Field(index=True)
    description: Optional[str] = Field(default=None, max_length=500)

class Score(ScoreBase, table=True):
    score_id: Optional[int] = Field(default=None, primary_key=True)
    professor_id: Optional[int] = Field(default=None, foreign_key="professor.professor_id")
    professor: Optional[Professor] = Relationship(back_populates="scores")
    students: List[Student] = Relationship(back_populates="scores", link_model=StudentScoreLink)
    calificaciones: List["Calificacion"] = Relationship(back_populates="score")

# Calificaciones por materia
class Calificacion(SQLModel, table=True):
    calificacion_id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id")
    score_id: int = Field(foreign_key="score.score_id")
    professor_id: int = Field(foreign_key="professor.professor_id")
    valor: float = Field(ge=0, le=100)
    fecha: date = Field(default_factory=date.today)
    tipo: CalificacionTipo
    comentario: Optional[str] = Field(default=None, max_length=500)

    student: Student = Relationship(back_populates="calificaciones")
    score: Score = Relationship(back_populates="calificaciones")
    professor: Professor = Relationship(back_populates="calificaciones")



# class AulaBase(SQLModel):
#     aula_name: str = Field(index=True)
#     facultad: str = Field(index=True)

# class Aula(AulaBase, table=True):
#     aula_id: Optional[int] = Field(default=None, primary_key=True)
