from sqlalchemy.orm import Session, aliased
from . import models, schemas
from typing import List, Optional
import math

def get_image(db: Session, image_id: int):
    return db.query(models.Image).filter(models.Image.id == image_id).first()

def get_image_by_filename(db: Session, filename: str):
    return db.query(models.Image).filter(models.Image.filename == filename).first()

def get_paginated_images_with_ratings(
    db: Session, user_name: str, filter: str, skip: int, limit: int, directory: Optional[str] = None
) -> schemas.PaginatedImageResponse:
    """
    Gets a paginated list of images, joining the user's ratings if they exist.
    Can be filtered to "all" or "unrated".
    Can be filtered by a specific subdirectory.
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

    if directory:
        query = query.filter(models.Image.filename.startswith(directory + '/'))

    if filter == "unrated":
        query = query.filter(user_rating.id == None)

    results = query.order_by(models.Image.filename).offset(skip).limit(limit).all()

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

def find_image_page(
    db: Session, user_name: str, filter: str, filename: str, limit: int, directory: Optional[str] = None
) -> Optional[int]:
    """
    Finds the page number for a given image filename based on the user, filter, and directory.
    """
    # 1. Find the target image to get its ID.
    # Use .like() for partial matching, but prioritize exact matches first.
    exact_match_query = db.query(models.Image.id).filter(models.Image.filename == filename)
    if directory:
        exact_match_query = exact_match_query.filter(models.Image.filename.startswith(directory + '/'))
    
    exact_match = exact_match_query.first()

    if exact_match:
        target_image_id = exact_match[0]
    else:
        # Fallback to partial match if no exact match is found
        partial_match_query = db.query(models.Image.id).filter(models.Image.filename.like(f"%{filename}%"))
        if directory:
            partial_match_query = partial_match_query.filter(models.Image.filename.startswith(directory + '/'))

        partial_match = partial_match_query.first()
        if not partial_match:
            return None
        target_image_id = partial_match[0]


    # 2. Build the same base query as get_paginated_images_with_ratings
    user_rating = aliased(models.Rating)
    query = db.query(models.Image.id).outerjoin(
        user_rating,
        (models.Image.id == user_rating.image_id) & (user_rating.user_name == user_name)
    )

    if directory:
        query = query.filter(models.Image.filename.startswith(directory + '/'))

    if filter == "unrated":
        query = query.filter(user_rating.id == None)

    # 3. Get the sorted list of all image IDs for this filter
    all_image_ids = [row[0] for row in query.order_by(models.Image.filename).all()]

    # 4. Find the index of our target image in the list
    try:
        index = all_image_ids.index(target_image_id)
    except ValueError:
        # The image exists but does not match the current filter (e.g., searching for a rated image in the 'unrated' filter)
        return None

    # 5. Calculate the page number
    page = math.floor(index / limit) + 1
    return page

def get_rating_counts(db: Session, user_name: str, directory: Optional[str] = None) -> schemas.CountsResponse:
    """
    Gets the total number of images and the number of unrated images for a user,
    optionally filtered by a directory.
    """
    base_query = db.query(models.Image)
    if directory:
        base_query = base_query.filter(models.Image.filename.startswith(directory + '/'))

    total_images = base_query.count()

    rated_image_ids = db.query(models.Rating.image_id).filter(models.Rating.user_name == user_name)
    
    unrated_query = base_query.filter(models.Image.id.notin_(rated_image_ids))
    unrated_images = unrated_query.count()

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
