#from __future__ import annotations
from datetime import date
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from passlib.context import CryptContext

# Configuración de hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    truncate_error=True
)

# Modelos Base
class ClubsBase(SQLModel):
    name_club: str = Field(index=True)
    sede: str

class UsersBase(SQLModel):
    email: str = Field(unique=True, index=True)
    first_name: str = Field(index=True)
    name_user: str = Field(unique=True, index=True)
    gender: str
    birth_date: Optional[date] = Field(default=None, index=True)
    age: Optional[int] = Field(default=None, index=True)
    club_id: Optional[int] = Field(default=None, foreign_key="clubs.id")

# Modelos de Tabla
class Clubs(ClubsBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuarios: List["Users"] = Relationship(back_populates="club"
)

class Users(UsersBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    club: Optional["Clubs"] = Relationship(back_populates="usuarios")
    
    def verify_password(self, plain_password: str):
        return pwd_context.verify(plain_password, self.hashed_password)

# Resolver referencias circulares
# Users.update_forward_refs()
# Clubs.update_forward_refs()
# Asegúrate que la configuración sea consistente
# pwd_context = CryptContext(
#     schemes=["bcrypt"],
#     deprecated="auto",
#     bcrypt__rounds=12,
#     truncate_error=True  # Previene contraseñas demasiado largas
# )


# # Obejto: Modelos Base 
# class ClubsBase(SQLModel):
#     name_club: str = Field(index=True)
#     sede: str

# class UsersBase(SQLModel):
#     email: str = Field(unique=True, index=True)
#     first_name: str = Field(index=True)  # Primer nombre
#     #last_name: str = Field(index=True)  # Nuevo campo: Apellido
#     name_user: str = Field(unique=True, index=True)
#     #cedula: str = Field(unique=True, index=True)  # Nuevo campo: Cédula/DNI
#     #phone: str = Field(index=True)  # Nuevo campo: Teléfono
#     gender: str  # Nuevo campo: Género (podría ser Enum)
#     birth_date: Optional[date] = Field(default=None, index=True)  # Nuevo campo: Fecha nacimiento
#     age: Optional[int] = Field(default=None, index=True)  # Calculado a partir de birth_date
#     club_id: Optional[int] = Field(default=None, foreign_key="clubs.id")

# # Objeto: Modelos de Tabla
# class Clubs(ClubsBase, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     usuarios: List["Users"] = Relationship(back_populates="club", sa_relationship_kwargs={"lazy": "select"})
#     # Add Pydantic config to handle relationships
#     model_config = ConfigDict(arbitrary_types_allowed=True)

# class Users(UsersBase, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     hashed_password: str
#     club: Optional["Clubs"] = Relationship(back_populates="usuarios", sa_relationship_kwargs={"lazy": "select"})
#     # Add Pydantic config to handle relationships
#     model_config = ConfigDict(arbitrary_types_allowed=True)
#     #Metodo verificar pass
#     def verify_password(self, plain_password: str):
#         return pwd_context.verify(plain_password, self.hashed_password)
    

