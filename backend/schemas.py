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

# Schema for the request body when creating a rating
class RatingRequest(BaseModel):
    user_name: str
    rating1: int = Field(..., ge=0, le=2)
    rating2: int = Field(..., ge=0, le=2)

