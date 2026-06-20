from sqlalchemy import Column, Integer, SmallInteger, String, Text, Numeric, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class RatingEnum(str, enum.Enum):
    G = "G"
    PG = "PG"
    PG_13 = "PG-13"
    R = "R"
    NC_17 = "NC-17"

class FilmCategory(Base):
    __tablename__ = 'film_category'
    
    film_id = Column(SmallInteger, ForeignKey('film.film_id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('category.category_id'), primary_key=True)
    last_update = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    
    # Relationships
    film = relationship("Film", back_populates="film_categories")
    category = relationship("Category", back_populates="film_categories")

class Category(Base):
    __tablename__ = 'category'
    
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(25), nullable=False)
    last_update = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    
    # Relationships
    film_categories = relationship("FilmCategory", back_populates="category", cascade="all, delete-orphan")
    films = relationship("Film", secondary="film_category", back_populates="categories", viewonly=True)

class Film(Base):
    __tablename__ = 'film'
    
    film_id = Column(SmallInteger, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    release_year = Column(Integer, nullable=True)
    language_id = Column(Integer, nullable=False, index=True)
    original_language_id = Column(Integer, nullable=True, index=True)
    rental_duration = Column(Integer, nullable=False, default=3)
    rental_rate = Column(Numeric(4, 2), nullable=False, default=4.99)
    length = Column(SmallInteger, nullable=True)
    replacement_cost = Column(Numeric(5, 2), nullable=False, default=19.99)
    rating = Column(Enum(RatingEnum, values_callable=lambda x: [e.value for e in x]), nullable=True, default=RatingEnum.G)
    special_features = Column(String(255), nullable=True)
    last_update = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    
    # Relationships
    film_categories = relationship("FilmCategory", back_populates="film", cascade="all, delete-orphan")
    categories = relationship("Category", secondary="film_category", back_populates="films", viewonly=True)
    inventories = relationship("Inventory", back_populates="film", cascade="all, delete-orphan")

class Inventory(Base):
    __tablename__ = 'inventory'
    
    inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    film_id = Column(SmallInteger, ForeignKey('film.film_id'), nullable=False, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    last_update = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    
    # Relationships
    film = relationship("Film", back_populates="inventories")
    # Rental relationship will resolve from app/models/rental.py
    rentals = relationship("Rental", back_populates="inventory")
