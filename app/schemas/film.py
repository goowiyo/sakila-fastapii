from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.film import RatingEnum

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=25)

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: int
    last_update: datetime

    class Config:
        from_attributes = True

class FilmBase(BaseModel):
    title: str = Field(..., max_length=128)
    description: Optional[str] = None
    release_year: Optional[int] = None
    language_id: int
    original_language_id: Optional[int] = None
    rental_duration: int = 3
    rental_rate: Decimal = Decimal("4.99")
    length: Optional[int] = None
    replacement_cost: Decimal = Decimal("19.99")
    rating: Optional[RatingEnum] = RatingEnum.G
    special_features: Optional[str] = None

class FilmCreate(FilmBase):
    category_ids: Optional[List[int]] = None

class FilmUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = None
    release_year: Optional[int] = None
    language_id: Optional[int] = None
    original_language_id: Optional[int] = None
    rental_duration: Optional[int] = None
    rental_rate: Optional[Decimal] = None
    length: Optional[int] = None
    replacement_cost: Optional[Decimal] = None
    rating: Optional[RatingEnum] = None
    special_features: Optional[str] = None
    category_ids: Optional[List[int]] = None

class FilmResponse(FilmBase):
    film_id: int
    last_update: datetime
    categories: List[CategoryResponse] = []

    class Config:
        from_attributes = True
