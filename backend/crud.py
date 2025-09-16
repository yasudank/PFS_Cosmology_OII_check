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
    user_rating = aliased(models.Rating)

    query = db.query(
        models.Image,
        user_rating.rating1,
        user_rating.rating2
    ).outerjoin(
        user_rating,
        (models.Image.id == user_rating.image_id) & (user_rating.user_name == user_name)
    )

    if filter == "unrated":
        query = query.filter(user_rating.id == None)

    results = query.order_by(models.Image.id).offset(skip).limit(limit).all()

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
    
    return schemas.PaginatedImageResponse(images=images_with_ratings)


def get_rating_counts(db: Session, user_name: str) -> schemas.CountsResponse:
    """
    Gets the total number of images and the number of unrated images for a user.
    """
    total_images = db.query(models.Image).count()

    rated_image_ids = db.query(models.Rating.image_id).filter(models.Rating.user_name == user_name)
    unrated_images = db.query(models.Image).filter(models.Image.id.notin_(rated_image_ids)).count()

    return schemas.CountsResponse(total_images=total_images, unrated_images=unrated_images)


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

def get_all_ratings_as_pivot_table(db: Session) -> schemas.PivotTableResponse:
    """
    Fetches all ratings and transforms them into a pivot table format,
    with images as rows and users' ratings as columns.
    """
    all_ratings_flat = db.query(
        models.Image.filename,
        models.Rating.user_name,
        models.Rating.rating1,
        models.Rating.rating2
    ).join(models.Rating).all()

    # Intermediate structure: {filename: {user: {rating1: v, rating2: v}}}
    pivot_data = {}
    all_users = set()

    for filename, user_name, r1, r2 in all_ratings_flat:
        if filename not in pivot_data:
            pivot_data[filename] = {}
        pivot_data[filename][user_name] = {"rating1": r1, "rating2": r2}
        all_users.add(user_name)
    
    # Also get all images that might not have ratings yet
    all_images = db.query(models.Image.filename).all()
    for image_tuple in all_images:
        filename = image_tuple[0]
        if filename not in pivot_data:
            pivot_data[filename] = {}

    sorted_users = sorted(list(all_users))
    
    # Define headers
    headers = ["Filename", "Rated By (Count)"]
    for user in sorted_users:
        headers.append(f"{user}_rating1")
        headers.append(f"{user}_rating2")

    # Build rows
    rows = []
    sorted_filenames = sorted(pivot_data.keys())

    for filename in sorted_filenames:
        num_raters = len(pivot_data[filename])
        row_data = {
            "Filename": filename,
            "Rated By (Count)": num_raters
        }
        for user in sorted_users:
            user_ratings = pivot_data[filename].get(user, {})
            row_data[f"{user}_rating1"] = user_ratings.get("rating1")
            row_data[f"{user}_rating2"] = user_ratings.get("rating2")
        rows.append(row_data)

    return schemas.PivotTableResponse(headers=headers, rows=rows)