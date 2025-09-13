from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    path = Column(String)

    ratings = relationship("Rating", back_populates="image")

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"))
    user_name = Column(String, index=True)
    rating1 = Column(Integer)
    rating2 = Column(Integer)

    image = relationship("Image", back_populates="ratings")
