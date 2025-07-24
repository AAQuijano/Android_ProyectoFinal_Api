from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app import models, schemas
from .config import settings
from .db import get_db

# Configuración de seguridad
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mapa de roles a modelos
ROLE_MODEL_MAP = {
    models.Role.STUDENT: models.Student,
    models.Role.PROFESSOR: models.Professor,
    models.Role.ADMIN: models.Admin,
}

# Reutiliza el contexto de hash definido en models
pwd_context = models.pwd_context

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        role_enum = models.Role(role)
        model = ROLE_MODEL_MAP[role_enum]
    except (ValueError, KeyError):
        raise credentials_exception

    user = db.exec(select(model).where(model.name_user == username)).first()
    if user is None:
        raise credentials_exception

    return user

# Reutilizable para endpoints que requieren autenticación básica
async def get_current_active_user(
    current_user: Union[models.Student, models.Professor, models.Admin] = Depends(get_current_user)
):
    return current_user

# Valida que el usuario sea administrador
async def get_current_admin_user(
    current_user: Union[models.Student, models.Professor, models.Admin] = Depends(get_current_user)
):
    if current_user.role != models.Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user

# Valida que el usuario sea profesor
async def get_current_professor_user(
    current_user: Union[models.Student, models.Professor, models.Admin] = Depends(get_current_user)
):
    if current_user.role != models.Role.PROFESSOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de profesor"
        )
    return current_user

