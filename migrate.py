# migrate.py
import logging
from sqlmodel import SQLModel
from app.db import engine
from app import models  # Asegura que todos los modelos estén importados

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Crea todas las tablas en la base de datos"""
    logger.info("Creando tablas...")
    SQLModel.metadata.create_all(engine)
    logger.info("¡Tablas creadas exitosamente!")

def drop_tables():
    """Elimina todas las tablas en la base de datos"""
    logger.info("Eliminando tablas...")
    SQLModel.metadata.drop_all(engine)
    logger.info("¡Tablas eliminadas exitosamente!")

def reset_tables():
    """Elimina y vuelve a crear todas las tablas"""
    drop_tables()
    create_tables()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Herramienta de migración para la base de datos")
    parser.add_argument("accion", choices=["create", "drop", "reset"], help="Acción a realizar")
    args = parser.parse_args()

    if args.accion == "create":
        create_tables()
    elif args.accion == "drop":
        drop_tables()
    elif args.accion == "reset":
        reset_tables()