from sqlmodel import SQLModel
from typing import Optional, Annotated
from datetime import datetime, timedelta, date
from jose import jwt
from enum import Enum
from pydantic import EmailStr, StringConstraints
from . import models
from .config import settings

# Tipos con restricciones usando Annotated
PhoneStr = Annotated[str, StringConstraints(min_length=7, max_length=15)]
CedulaStr = Annotated[str, StringConstraints(min_length=8, max_length=12)]

class Gender(str, Enum):
    MALE = "hombre"
    FEMALE = "mujer"


#Crear usuario y club
class Create_User(SQLModel):
    email: EmailStr
    first_name: str
    name_user: str
    gender: Gender
    birth_date: Optional[date] = None
    club_id: Optional[int] = None
    password: str

class UsersPublic(SQLModel):
    id: int
    email: str
    first_name: str
    name_user: str
    gender: str
    birth_date: Optional[date] = None
    club_id: Optional[int] = None

class UsersRead(SQLModel):
    id: int
    email: str
    first_name: str
    name_user: str
    gender: str
    birth_date: Optional[date] = None
    age: Optional[int] = None
    club_id: Optional[int] = None


class Create_Club(SQLModel):
    name_club: str
    sede: str
    id: Optional[int] = None
    

#Publico
class ClubsPublic(SQLModel):
    name_club: str
    sede: str
    id: Optional[int] = None

#Actualizar
class Club_Update(SQLModel):
    name_club: str | None = None
    sede: str | None = None

class UserUpdate(SQLModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    name_user: Optional[str] = None
    gender: Optional[Gender] = None
    birth_date: Optional[date] = None
    club_id: Optional[int] = None
    password: Optional[str] = None  # Opcional para actualizar contraseña



