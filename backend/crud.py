from sqlalchemy.orm import Session, aliased
from . import models, schemas
from typing import List

def get_image(db: Session, image_id: int):
    return db.query(models.Image).filter(models.Image.id == image_id).first()

def get_image_by_filename(db: Session, filename: str):
    return db.query(models.Image).filter(models.Image.filename == filename).first()

def get_paginated_images_with_ratings(
    db: Session, user_name: str, filter: str, skip: int, limit: int
) -> schemas.PaginatedImageResponse:
    """
    Gets a paginated list of images, joining the user's ratings if they exist.
    Can be filtered to "all" or "unrated".
    """
    # Alias for the Rating model to use in the LEFT JOIN
    user_rating = aliased(models.Rating)

    # Base query for images
    query = db.query(
        models.Image,
        user_rating.rating1,
        user_rating.rating2
    ).outerjoin(
        user_rating,
        (models.Image.id == user_rating.image_id) & (user_rating.user_name == user_name)
    )

    # Apply filter
    if filter == "unrated":
        query = query.filter(user_rating.id == None)

    # Get total count for pagination
    total_count = query.count()

    # Get the paginated results
    results = query.order_by(models.Image.id).offset(skip).limit(limit).all()

    # Format the results into the Pydantic schema
    images_with_ratings: List[schemas.ImageWithRating] = []
    for image, rating1, rating2 in results:
        images_with_ratings.append(
            schemas.ImageWithRating(
                id=image.id,
                filename=image.filename,
                path=image.path,
                rating1=rating1,
                rating2=rating2,
            )
        )
    
    return schemas.PaginatedImageResponse(
        total_count=total_count, images=images_with_ratings
    )


def create_image(db: Session, image: schemas.ImageCreate):
    db_image = models.Image(filename=image.filename, path=image.path)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def upsert_rating(db: Session, image_id: int, rating_data: schemas.RatingCreate):
    """
    Creates a new rating or updates an existing one for a given user and image.
    """
    existing_rating = db.query(models.Rating).filter(
        models.Rating.image_id == image_id,
        models.Rating.user_name == rating_data.user_name
    ).first()

    if existing_rating:
        # Update existing rating
        existing_rating.rating1 = rating_data.rating1
        existing_rating.rating2 = rating_data.rating2
        db_rating = existing_rating
    else:
        # Create new rating
        db_rating = models.Rating(
            image_id=image_id,
            user_name=rating_data.user_name,
            rating1=rating_data.rating1,
            rating2=rating_data.rating2
        )
        db.add(db_rating)
    
    db.commit()
    db.refresh(db_rating)
    return db_rating