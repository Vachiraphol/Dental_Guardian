import os
from typing import Generator
from sqlmodel import Session, create_engine, SQLModel

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # กรณี Local Fallback
    DATABASE_URL = "sqlite:///./dental_guardian.db"
elif DATABASE_URL.startswith("postgres://"):
    # แปลง prefix ให้รองรับ SQLAlchemy
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ปรับ pool_pre_ping ป้องกันการหลุดของ Neon Serverless Connection
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session