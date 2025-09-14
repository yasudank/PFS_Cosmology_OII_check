from pydantic import BaseModel, Field
from typing import List, Optional

# Schemas for Rating
class RatingBase(BaseModel):
    user_name: str
    rating1: int = Field(..., ge=0, le=2)
    rating2: int = Field(..., ge=0, le=2)

class RatingCreate(RatingBase):
    pass

class Rating(RatingBase):
    id: int
    image_id: int

    class Config:
        orm_mode = True

# Schemas for Image
class ImageBase(BaseModel):
    filename: str
    path: str

class ImageCreate(ImageBase):
    pass

class Image(ImageBase):
    id: int

    class Config:
        orm_mode = True

# Schema for returning an image with its rating for the current user
class ImageWithRating(Image):
    rating1: Optional[int] = None
    rating2: Optional[int] = None

# Schema for the paginated image list response
class PaginatedImageResponse(BaseModel):
    total_count: int
    images: List[ImageWithRating]

# Schema for the request body when creating/updating a rating
class RatingRequest(BaseModel):
    user_name: str
    rating1: int = Field(..., ge=0, le=2)
    rating2: int = Field(..., ge=0, le=2)

