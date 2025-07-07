#from __future__ import annotations
from datetime import date
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from . import models, schemas, db
from typing import Annotated

# Configuración de dependencias
session_dep = Annotated[Session, Depends(db.get_db)]

app = FastAPI()

@app.get('/')
def root():
    return {'message': 'Hola es FastApi'}

@app.on_event('startup')
def on_startup():
    db.create_db_and_tables()


@app.post("/Users/", response_model=schemas.UsersPublic, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.Create_User, session: session_dep):
    try:
        # 1. Verificar si usuario ya existe
        existing_user = session.exec(
            select(models.Users).where(
                (models.Users.email == user.email) |
                (models.Users.name_user == user.name_user)
            )
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email o nombre de usuario ya están registrados"
            )

        # 2. Validar club_id si fue proporcionado
        if user.club_id is not None:
            club = session.get(models.Clubs, user.club_id)
            if not club:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No existe un club con ID {user.club_id}"
                )

        # 3. Hashear la contraseña
        hashed_password = models.pwd_context.hash(user.password)

        # 4. Preparar datos para el nuevo usuario
        user_data = user.dict(exclude={"password", "id"})
        user_data.update({
            "hashed_password": hashed_password,
            "age": calculate_age(user.birth_date) if user.birth_date else None
        })

        # 5. Crear y guardar el usuario
        db_user = models.Users(**user_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        
        return db_user

    except HTTPException:
        raise  # Re-lanzamos las excepciones HTTP que ya manejamos
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al crear el usuario: {str(e)}"
        )

def calculate_age(birth_date: date) -> int:
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day))

# @app.post("/Users/")
# def create_user(user: schemas.Create_User, session: session_dep):
#     try:
#         # 1. Verificar si usuario ya existe
#         existing_user = session.exec(
#             select(models.Users).where(
#                 (models.Users.email == user.email) |
#                 (models.Users.name_user == user.name_user)
#             )
#         ).first()
        
#         if existing_user:
#             raise HTTPException(status_code=400, detail="Usuario ya existe")
        
#         existing_club = session.exec(
#             select(models.Clubs).where(
#                 (models.Clubs.id == user.club_id)
#             )
#         ).first()
        
#         if existing_club == None:
#             raise HTTPException(status_code=400, detail="club no existe")

#         # 2. Hashear la contraseña ANTES de crear el modelo Users
#         hashed_password = models.pwd_context.hash(user.password)

#         # 3. Crear el diccionario de datos excluyendo el password plano
#         user_data = user.dict(exclude={"password"})
#         user_data["hashed_password"] = hashed_password

#         # 4. Calcular edad si hay fecha de nacimiento
#         if user.birth_date:
#             today = date.today()
#             user_data["age"] = today.year - user.birth_date.year - (
#                 (today.month, today.day) < (user.birth_date.month, user.birth_date.day))

#         # 5. Crear instancia del modelo Users con TODOS los campos requeridos
#         db_user = models.Users(**user_data)
#         session.add(db_user)
#         session.commit()
#         session.refresh(db_user)
#         return db_user

#     except Exception as e:
#         session.rollback()
#         raise HTTPException(status_code=500, detail=str(e))
    

# @app.post("/Users/", response_model=schemas.UsersPublic)
# def create_user(user: schemas.Create_User, session: session_dep):
#     # Verificación de usuario existente
#     existing_user = session.exec(
#         select(models.Users).where(
#             (models.Users.email == user.email) |
#             (models.Users.name_user == user.name_user)
#         )
#     ).first()
    
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Usuario ya existe")

#     # Crear usuario sin manejar relaciones directamente
#     user_data = user.dict(exclude={"password"})
#     user_data["hashed_password"] = models.pwd_context.hash(user.password)
    
#     db_user = models.Users(**user_data)
#     session.add(db_user)
#     session.commit()
#     session.refresh(db_user)
#     return db_user

@app.post("/Clubs/", response_model=schemas.ClubsPublic, status_code=status.HTTP_201_CREATED)
def create_club(club: schemas.Create_Club, session: session_dep):
    try:
        # Verificar si el club ya existe
        existing_club = session.exec(
            select(models.Clubs).where(
                models.Clubs.name_club == club.name_club
            )
        ).first()
        
        if existing_club:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un club con el nombre {club.name_club}"
            )

        # Crear nuevo club
        db_club = models.Clubs(
            name_club=club.name_club,
            sede=club.sede
        )
        
        session.add(db_club)
        session.commit()
        session.refresh(db_club)
        
        return db_club

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear club: {str(e)}"
        )

@app.get("/Clubs/", response_model=list[schemas.ClubsPublic])
def read_clubs(
    session: session_dep,
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    clubs = session.exec(
        select(models.Clubs).offset(offset).limit(limit)
    ).all()
    return clubs


@app.get("/Clubs/{club_id}", response_model=schemas.ClubsPublic)
def read_club(club_id: int, session: session_dep):
    club = session.get(models.Clubs, club_id)
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club con ID {club_id} no encontrado"
        )
    return club

@app.patch("/Clubs/{club_id}", response_model=schemas.ClubsPublic)
def update_club(
    club_id: int,
    club_data: schemas.Club_Update,
    session: session_dep
):
    db_club = session.get(models.Clubs, club_id)
    if not db_club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club con ID {club_id} no encontrado"
        )
    
    club_dict = club_data.dict(exclude_unset=True)
    for key, value in club_dict.items():
        setattr(db_club, key, value)
    
    session.add(db_club)
    session.commit()
    session.refresh(db_club)
    return db_club


@app.get("/Users/", response_model=list[schemas.UsersRead])
def read_users(
    session: session_dep,
    offset: int = 0, 
    limit: Annotated[int, Query(le=100)] = 100
):
    # Operación de solo lectura no necesita transacción explícita
    users = session.exec(
        select(models.Users).offset(offset).limit(limit)
    ).all()
    return users

@app.get("/Users/{user_id}", response_model=schemas.UsersRead)
def read_user(user_id: int, session: session_dep):
    # Operación de solo lectura
    user = session.get(models.Users, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user

@app.patch("/Users/{user_id}", response_model=schemas.UsersPublic)
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    session: session_dep
):
    try:
        # 1. Obtener el usuario existente
        db_user = session.get(models.Users, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado"
            )

        # 2. Verificar unicidad de email/username si se actualizan
        update_data = user_data.dict(exclude_unset=True)
        
        if 'email' in update_data:
            existing_email = session.exec(
                select(models.Users).where(
                    (models.Users.email == update_data['email']) &
                    (models.Users.id != user_id)
                )
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El email ya está en uso por otro usuario"
                )

        if 'name_user' in update_data:
            existing_username = session.exec(
                select(models.Users).where(
                    (models.Users.name_user == update_data['name_user']) &
                    (models.Users.id != user_id)
                )
            ).first()
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El nombre de usuario ya está en uso"
                )

        # 3. Validar club_id si se proporciona
        if 'club_id' in update_data and update_data['club_id'] is not None:
            club = session.get(models.Clubs, update_data['club_id'])
            if not club:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No existe un club con ID {update_data['club_id']}"
                )
        
        if 'password' in update_data:
            db_user.hashed_password = models.pwd_context.hash(update_data.pop('password'))

        # 4. Actualizar campos
        for field, value in update_data.items():
            # Calcular edad si se actualiza birth_date
            if field == 'birth_date' and value is not None:
                today = date.today()
                age = today.year - value.year - (
                    (today.month, today.day) < (value.month, value.day))
                setattr(db_user, 'age', age)
            
            setattr(db_user, field, value)

        # 5. Guardar cambios
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        
        return db_user

    except HTTPException:
        raise  # Re-lanzamos excepciones HTTP que ya manejamos
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}"
        )