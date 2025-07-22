from sqlmodel import Session, create_engine, SQLModel
from .config import settings
from app import models
from contextvars import ContextVar

# Engine principal
db_url = settings.DATABASE_URL
engine = create_engine(
    db_url,
    echo=True,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)

# Engine de prueba (override)
engine_context: ContextVar[object] = ContextVar("engine_context", default=None)

# Crear tablas (para uso directo si necesario)
def create_db_and_tables():
    models.SQLModel.metadata.create_all(engine)

# Sesión de base de datos
def get_db():
    engine_override = engine_context.get()
    db = Session(engine_override or engine)
    try:
        yield db
    finally:
        db.close()






