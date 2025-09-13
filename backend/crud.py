from sqlalchemy.orm import Session
from . import models, schemas

def get_image(db: Session, image_id: int):
    return db.query(models.Image).filter(models.Image.id == image_id).first()

def get_image_by_filename(db: Session, filename: str):
    return db.query(models.Image).filter(models.Image.filename == filename).first()

def get_images(db: Session, user_name: str, skip: int = 0, limit: int = 10):
    """
    Get images that the specified user has not rated yet.
    """
    # Subquery to find all image_ids that the user has already rated
    rated_image_ids = db.query(models.Rating.image_id).filter(models.Rating.user_name == user_name)
    
    # Main query to find images that are not in the rated_image_ids subquery
    query = db.query(models.Image).filter(models.Image.id.notin_(rated_image_ids))
    
    return query.offset(skip).limit(limit).all()

def create_image(db: Session, image: schemas.ImageCreate):
    db_image = models.Image(filename=image.filename, path=image.path)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def create_rating(db: Session, image_id: int, rating_data: schemas.RatingCreate):
    """
    Create a new rating for an image by a user.
    """
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

def get_images_count(db: Session, user_name: str):
    """
    Get the count of images that the specified user has not rated yet.
    """
    rated_image_ids = db.query(models.Rating.image_id).filter(models.Rating.user_name == user_name)
    count = db.query(models.Image).filter(models.Image.id.notin_(rated_image_ids)).count()
    return count

