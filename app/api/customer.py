from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("/", response_model=List[CustomerResponse])
def read_customers(
    skip: int = 0,
    limit: int = 100,
    name: str = Query(None, description="Search term for customer first/last name"),
    db: Session = Depends(get_db)
):
    """
    Retrieve customers list with pagination and optional search query.
    """
    return customer_service.get_customers(db, skip=skip, limit=limit, name_query=name)

@router.get("/{customer_id}", response_model=CustomerResponse)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    """
    Retrieve details of a customer.
    """
    db_customer = customer_service.get_customer(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
    return db_customer

@router.post("/", response_model=CustomerResponse, status_code=201)
def create_customer(customer_in: CustomerCreate, db: Session = Depends(get_db)):
    """
    Register a new customer.
    """
    return customer_service.create_customer(db, customer_in=customer_in)

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, customer_in: CustomerUpdate, db: Session = Depends(get_db)):
    """
    Update a customer record.
    """
    db_customer = customer_service.update_customer(db, customer_id=customer_id, customer_in=customer_in)
    if not db_customer:
        raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
    return db_customer

@router.delete("/{customer_id}", response_model=CustomerResponse)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """
    Delete a customer record.
    """
    db_customer = customer_service.delete_customer(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
    return db_customer
