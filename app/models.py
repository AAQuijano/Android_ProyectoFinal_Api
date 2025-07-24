#models.py
from datetime import date
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from passlib.context import CryptContext
from enum import Enum

# Configuración de hasheo de contraseñas
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# Enumeradores para tipos predefinidos
class Role(str, Enum):
    """Roles disponibles en el sistema"""
    STUDENT = "student"
    PROFESSOR = "professor"
    ADMIN = "admin"

class Gender(str, Enum):
    """Géneros disponibles"""
    MALE = "male"
    FEMALE = "female"

class CalificacionTipo(str, Enum):
    """Tipos de calificaciones académicas"""
    PARCIAL = "parcial"
    NOTA_FINAL = "nota_final"
    PRACTICA = "practica"
    QUIZ = "quiz"
    LABORATORIO = "laboratorio"
    PROYECTO = "proyecto"
    SEMESTRAL = "semestral"
    TAREA = "tarea"
    PRESENTACION = "presentacion"


class StudentScoreLink(SQLModel, table=True):
    """Tabla de relación muchos-a-muchos entre estudiantes y materias"""
    student_id: int = Field(
        ..., 
        foreign_key="user.user_id", 
        primary_key=True,
        description="ID del estudiante"
    )
    score_id: int = Field(
        ..., 
        foreign_key="score.score_id", 
        primary_key=True,
        description="ID de la materia"
    )

class UserBase(SQLModel):
    """Campos base compartidos por todos los usuarios"""
    name_complete: str = Field(..., index=True, description="Nombre completo del usuario")
    name_user: str = Field(..., unique=True, index=True, description="Nombre de usuario para login")
    cedula: str = Field(..., unique=True, index=True, description="Número de identificación único")
    email: str = Field(..., unique=True, index=True, description="Correo electrónico")
    gender: Gender = Field(..., description="Género del usuario")
    birth_date: Optional[date] = Field(None, description="Fecha de nacimiento")
    age: Optional[int] = Field(None, description="Edad calculada automáticamente")
    role: Role = Field(..., index=True, description="Rol del usuario en el sistema")

class User(UserBase, table=True):
    """Modelo principal de usuario que representa todos los roles en el sistema"""
    user_id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(..., description="Contraseña hasheada")
    specialization: Optional[str] = Field(
        None, 
        description="Especialización profesional (solo para profesores)"
    )

    # Relaciones
    scores_as_professor: List["Score"] = Relationship(
        back_populates="professor",
        sa_relationship_kwargs={"foreign_keys": "Score.professor_id"}
    )
    scores_as_student: List["Score"] = Relationship(
        back_populates="students",
        link_model=StudentScoreLink
    )
    calificaciones_as_student: List["Calificacion"] = Relationship(
        back_populates="student",
        sa_relationship_kwargs={"foreign_keys": "Calificacion.student_id"}
    )
    calificaciones_as_professor: List["Calificacion"] = Relationship(
        back_populates="professor",
        sa_relationship_kwargs={"foreign_keys": "Calificacion.professor_id"}
    )

    # Métodos de seguridad
    def set_password(self, password: str):
        """Hashea y guarda la contraseña del usuario"""
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verifica si la contraseña coincide con el hash almacenado"""
        return pwd_context.verify(password, self.hashed_password)

    def __repr__(self):
        return f"<User {self.name_user} ({self.role})>"



class ScoreBase(SQLModel):
    """Campos base para las materias académicas"""
    materia: str = Field(..., index=True, description="Nombre de la materia")
    description: Optional[str] = Field(
        None, 
        max_length=500,
        description="Descripción detallada de la materia"
    )

class Score(ScoreBase, table=True):
    """Modelo completo para materias académicas"""
    score_id: Optional[int] = Field(default=None, primary_key=True)
    professor_id: int = Field(
        ..., 
        foreign_key="user.user_id",
        description="ID del profesor que imparte la materia"
    )
    
    # Relaciones
    professor: Optional["User"] = Relationship(
        back_populates="scores_as_professor"
    )
    students: List["User"] = Relationship(
        back_populates="scores_as_student",
        link_model=StudentScoreLink
    )
    calificaciones: List["Calificacion"] = Relationship(
        back_populates="score"
    )

class CalificacionBase(SQLModel):
    """Campos base para las calificaciones"""
    valor: float = Field(
        ..., 
        ge=0, 
        le=100,
        description="Valor numérico de la calificación (0-100)"
    )
    fecha: date = Field(
        default_factory=date.today,
        description="Fecha cuando se registró la calificación"
    )
    tipo: CalificacionTipo = Field(
        ..., 
        description="Tipo de evaluación/calificación"
    )
    comentario: Optional[str] = Field(
        None, 
        max_length=500,
        description="Comentarios adicionales sobre la calificación"
    )

class Calificacion(CalificacionBase, table=True):
    calificacion_id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(..., foreign_key="user.user_id")
    score_id: int = Field(..., foreign_key="score.score_id")
    professor_id: int = Field(..., foreign_key="user.user_id")

    student: Optional["User"] = Relationship(
        back_populates="calificaciones_as_student",
        sa_relationship_kwargs={"foreign_keys": "[Calificacion.student_id]"}
    )
    professor: Optional["User"] = Relationship(
        back_populates="calificaciones_as_professor",
        sa_relationship_kwargs={"foreign_keys": "[Calificacion.professor_id]"}
    )
    score: Optional["Score"] = Relationship(
        back_populates="calificaciones"
    )


