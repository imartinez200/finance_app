from sqlmodel import SQLModel, create_engine, Session
from app.config import settings
from app import models  # <-- IMPORTANTE: asegura que se registren en metadata


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
