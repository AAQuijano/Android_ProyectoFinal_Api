from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app import models, schemas
from ..config import settings
from ..db import get_db

# Configuración de seguridad
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Reutiliza el contexto de hash definido en models
pwd_context = models.pwd_context

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT de acceso
    
    Args:
        data: Datos a incluir en el token
        expires_delta: Tiempo de expiración del token
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Obtiene el usuario actual basado en el token JWT
    
    Args:
        token: Token JWT
        db: Sesión de base de datos
        
    Returns:
        Modelo de usuario autenticado
        
    Raises:
        HTTPException: Si las credenciales son inválidas
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Buscar usuario en la base de datos
    user = db.exec(
        select(models.User).where(
            (models.User.name_user == username) & 
            (models.User.user_id == user_id)
    )).first()
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Retorna el usuario actual si está activo
    
    Args:
        current_user: Usuario obtenido del token
        
    Returns:
        Modelo de usuario activo
    """
    return current_user

async def get_current_admin_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Verifica que el usuario actual sea administrador
    
    Args:
        current_user: Usuario obtenido del token
        
    Returns:
        Modelo de usuario administrador
        
    Raises:
        HTTPException: Si el usuario no es administrador
    """
    if current_user.role != models.Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user

async def get_current_professor_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Verifica que el usuario actual sea profesor
    
    Args:
        current_user: Usuario obtenido del token
        
    Returns:
        Modelo de usuario profesor
        
    Raises:
        HTTPException: Si el usuario no es profesor
    """
    if current_user.role != models.Role.PROFESSOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de profesor"
        )
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    if token is None:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            return None
    except JWTError:
        return None

    user = db.exec(
        select(models.User).where(
            (models.User.name_user == username) &
            (models.User.user_id == user_id)
        )
    ).first()

    return user
