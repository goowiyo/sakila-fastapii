from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.film import FilmCreate, FilmUpdate, FilmResponse
from app.services import film_service

router = APIRouter(prefix="/films", tags=["films"])

@router.get("/", response_model=List[FilmResponse])
def read_films(
    skip: int = 0,
    limit: int = 100,
    title: str = Query(None, description="Search term for film title"),
    db: Session = Depends(get_db)
):
    """
    Retrieve films list with pagination and title search filtering.
    """
    return film_service.get_films(db, skip=skip, limit=limit, title_query=title)

@router.get("/{film_id}", response_model=FilmResponse)
def read_film(film_id: int, db: Session = Depends(get_db)):
    """
    Retrieve film details by its ID.
    """
    db_film = film_service.get_film(db, film_id=film_id)
    if not db_film:
        raise HTTPException(status_code=404, detail=f"Film with ID {film_id} not found")
    return db_film

@router.post("/", response_model=FilmResponse, status_code=201)
def create_film(film_in: FilmCreate, db: Session = Depends(get_db)):
    """
    Create a new film record.
    """
    return film_service.create_film(db, film_in=film_in)

@router.put("/{film_id}", response_model=FilmResponse)
def update_film(film_id: int, film_in: FilmUpdate, db: Session = Depends(get_db)):
    """
    Update a film record.
    """
    db_film = film_service.update_film(db, film_id=film_id, film_in=film_in)
    if not db_film:
        raise HTTPException(status_code=404, detail=f"Film with ID {film_id} not found")
    return db_film

@router.delete("/{film_id}", response_model=FilmResponse)
def delete_film(film_id: int, db: Session = Depends(get_db)):
    """
    Delete a film record.
    """
    db_film = film_service.delete_film(db, film_id=film_id)
    if not db_film:
        raise HTTPException(status_code=404, detail=f"Film with ID {film_id} not found")
    return db_film
