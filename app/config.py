from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env"
    )

    def __init__(self, **values):
        super().__init__(**values)
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY no configurada en .env")
        if not self.DATABASE_URL.startswith(("postgresql://", "mysql://", "sqlite://", "mysql+pymysql://")):
            raise ValueError("DATABASE_URL debe comenzar con 'postgresql://', 'mysql://' o 'sqlite://'")

settings = Settings()