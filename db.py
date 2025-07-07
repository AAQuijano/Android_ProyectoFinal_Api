from sqlmodel import Session, create_engine, SQLModel
from .config import settings
from . import models


db_url = settings.DATABASE_URL
engine = create_engine(
    db_url,
    echo=True  # Muestra las queries en consola (útil para desarrollo)

)

#Definir sql,coneccion y session
def create_db_and_tables():
    models.SQLModel.metadata.create_all(engine)

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()








