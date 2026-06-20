from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crear el motor de SQLAlchemy con pool pre-ping para manejar caídas de conexión en MySQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Generador de dependencia para obtener una sesión de base de datos.
    Asegura que la conexión se cierre una vez finalizada la solicitud.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
