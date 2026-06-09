import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

os.makedirs("data",   exist_ok=True)
os.makedirs("static", exist_ok=True)

DATABASE_URL = "sqlite:///./data/brewconnect.db"
engine       = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models import User, Interest, ActiveSession  # noqa
    Base.metadata.create_all(bind=engine)
    print("[OK] Database ready")