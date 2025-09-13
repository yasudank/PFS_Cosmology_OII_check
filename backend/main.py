import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .database import SessionLocal, engine, Base

# Recreate the database
# NOTE: This will delete all existing data.
# For a production environment, a migration tool like Alembic should be used.
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
    Recursively scans the image directory on startup and registers the images in the database.
    """
    db = SessionLocal()
    try:
        supported_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        
        for root, _, files in os.walk(IMAGE_DIR):
            for filename in files:
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    # Path relative to the IMAGE_DIR, used as a unique identifier
                    relative_path = os.path.relpath(os.path.join(root, filename), IMAGE_DIR)
                    # Normalize path separators for cross-platform compatibility (URLs use '/')
                    unique_db_filename = relative_path.replace(os.path.sep, '/')

                    # Check if an image with this unique path is already in the DB
                    db_image = crud.get_image_by_filename(db, filename=unique_db_filename)
                    if not db_image:
                        # The path for the URL is based on the root IMAGE_DIR
                        url_path = os.path.join(IMAGE_DIR, unique_db_filename).replace(os.path.sep, '/')
                        image_create = schemas.ImageCreate(filename=unique_db_filename, path=url_path)
                        crud.create_image(db, image=image_create)
    finally:
        db.close()

@app.get("/api/images", response_model=List[schemas.Image])
def read_images(user_name: str = Query(..., min_length=1), skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    images = crud.get_images(db, user_name=user_name, skip=skip, limit=limit)
    return images

@app.get("/api/images/count")
def read_images_count(user_name: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    count = crud.get_images_count(db, user_name=user_name)
    return {"count": count}

@app.post("/api/images/{image_id}/rate", response_model=schemas.Rating)
def rate_image(image_id: int, rating_request: schemas.RatingRequest, db: Session = Depends(get_db)):
    # Pydantic model validation already checks if ratings are between 0 and 2.
    
    # Check if image exists
    db_image = crud.get_image(db, image_id=image_id)
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
        
    rating_data = schemas.RatingCreate(
        user_name=rating_request.user_name,
        rating1=rating_request.rating1,
        rating2=rating_request.rating2
    )
    
    new_rating = crud.create_rating(db, image_id=image_id, rating_data=rating_data)
    return new_rating

