import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# --- Robust Path Logic ---
# Get the absolute path of the project's root directory (one level up from 'backend')
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "image_rater.db")
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_PATH}"

DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)

if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()