import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List

import shutil
import subprocess
import datetime

from . import crud, models, schemas
from .database import SessionLocal, engine, Base, DATABASE_URL

# Recreate the database
# NOTE: This will delete all existing data.
# For a production environment, a migration tool like Alembic should be used.
# Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Add logging to display the connected database URL ---
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Application startup: Connecting to database at {engine.url}")
# ------------------------------------------------------

allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_DIR = "sample_images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# Mount the static directory with an absolute path
app.mount(f"/{IMAGE_DIR}", StaticFiles(directory=os.path.abspath(IMAGE_DIR)), name="images")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    """
    Application startup event:
    1. Back up the database.
    2. Scan the image directory and register images.
    """
    # --- 1. Automatic Backup Logic ---
    logger.info("Attempting to back up database...")
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db_backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if DATABASE_URL.startswith("sqlite"):
            db_path = DATABASE_URL.split(":///", 1)[1]
            if os.path.exists(db_path):
                backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
                shutil.copy2(db_path, backup_path)
                logger.info(f"Successfully created SQLite backup at {backup_path}")
            else:
                logger.warning(f"SQLite database file not found at {db_path}, skipping backup.")

        elif DATABASE_URL.startswith("postgresql"):
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")
            
            if not shutil.which("pg_dump"):
                 logger.error("pg_dump command not found. Please install PostgreSQL client tools and ensure it's in the system's PATH.")
            else:
                # Using a list of arguments is safer than a single command string
                dump_command = ["pg_dump", "--dbname=" + DATABASE_URL, "-f", backup_file, "--clean"]
                process = subprocess.run(dump_command, capture_output=True, text=True, check=False)
                if process.returncode == 0:
                    logger.info(f"Successfully created PostgreSQL dump at {backup_file}")
                else:
                    logger.error(f"pg_dump failed with exit code {process.returncode}: {process.stderr}")
        
    except Exception as e:
        logger.error(f"An error occurred during the backup process: {e}")

    # --- 2. Scan Image Directory ---
    logger.info("Scanning image directory...")
    db = SessionLocal()
    try:
        supported_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        
        for root, _, files in os.walk(IMAGE_DIR):
            for filename in files:
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    relative_path = os.path.relpath(os.path.join(root, filename), IMAGE_DIR)
                    unique_db_filename = relative_path.replace(os.path.sep, '/')

                    db_image = crud.get_image_by_filename(db, filename=unique_db_filename)
                    if not db_image:
                        url_path = os.path.join(IMAGE_DIR, unique_db_filename).replace(os.path.sep, '/')
                        image_create = schemas.ImageCreate(filename=unique_db_filename, path=url_path)
                        crud.create_image(db, image=image_create)
    finally:
        db.close()

@app.get("/api/images", response_model=schemas.PaginatedImageResponse)
def read_images(
    user_name: str = Query(..., min_length=1),
    filter: str = Query("all", enum=["all", "unrated"]),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    paginated_response = crud.get_paginated_images_with_ratings(
        db=db, user_name=user_name, filter=filter, skip=skip, limit=limit
    )
    # The total_count is removed from this response, it's now fetched from /api/counts
    return paginated_response

@app.get("/api/images/find", response_model=schemas.ImagePageResponse)
def find_image_by_filename(
    user_name: str = Query(..., min_length=1),
    filter: str = Query("all", enum=["all", "unrated"]),
    filename: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    page = crud.find_image_page(
        db=db, user_name=user_name, filter=filter, filename=filename, limit=limit
    )
    if page is None:
        raise HTTPException(
            status_code=404, 
            detail=f'Image with filename containing "{filename}" not found or does not match the current filter.'
        )
    return schemas.ImagePageResponse(page=page)

@app.get("/api/counts", response_model=schemas.CountsResponse)
def get_counts(user_name: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return crud.get_rating_counts(db=db, user_name=user_name)


@app.post("/api/images/{image_id}/rate", response_model=schemas.Rating)
def rate_image(image_id: int, rating_request: schemas.RatingRequest, db: Session = Depends(get_db)):
    # Check if image exists
    db_image = crud.get_image(db, image_id=image_id)
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
        
    rating_data = schemas.RatingCreate(
        user_name=rating_request.user_name,
        rating1=rating_request.rating1,
        rating2=rating_request.rating2
    )
    
    # Use upsert to create or update the rating
    new_or_updated_rating = crud.upsert_rating(db, image_id=image_id, rating_data=rating_data)
    return new_or_updated_rating


@app.get("/api/ratings/summary", response_model=schemas.PivotTableResponse)
def get_ratings_summary(db: Session = Depends(get_db)):
    pivot_data = crud.get_all_ratings_as_pivot_table(db)
    return pivot_data

