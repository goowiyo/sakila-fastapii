from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.rental import RentalCreate, RentalUpdate, RentalResponse
from app.services import rental_service

router = APIRouter(prefix="/rentals", tags=["rentals"])

@router.get("/", response_model=List[RentalResponse])
def read_rentals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve rentals list with pagination.
    """
    return rental_service.get_rentals(db, skip=skip, limit=limit)

@router.get("/{rental_id}", response_model=RentalResponse)
def read_rental(rental_id: int, db: Session = Depends(get_db)):
    """
    Retrieve details of a specific rental transaction.
    """
    db_rental = rental_service.get_rental(db, rental_id=rental_id)
    if not db_rental:
        raise HTTPException(status_code=404, detail=f"Rental with ID {rental_id} not found")
    return db_rental

@router.post("/", response_model=RentalResponse, status_code=201)
def create_rental(rental_in: RentalCreate, db: Session = Depends(get_db)):
    """
    Record a new rental transaction. Includes validation that the inventory item is currently available.
    """
    return rental_service.create_rental(db, rental_in=rental_in)

@router.put("/{rental_id}", response_model=RentalResponse)
def update_rental(rental_id: int, rental_in: RentalUpdate, db: Session = Depends(get_db)):
    """
    Update a rental record (commonly used to set return_date when movie is returned).
    """
    db_rental = rental_service.update_rental(db, rental_id=rental_id, rental_in=rental_in)
    if not db_rental:
        raise HTTPException(status_code=404, detail=f"Rental with ID {rental_id} not found")
    return db_rental

@router.delete("/{rental_id}", response_model=RentalResponse)
def delete_rental(rental_id: int, db: Session = Depends(get_db)):
    """
    Delete a rental record (associated payments will be updated accordingly).
    """
    db_rental = rental_service.delete_rental(db, rental_id=rental_id)
    if not db_rental:
        raise HTTPException(status_code=404, detail=f"Rental with ID {rental_id} not found")
    return db_rental
