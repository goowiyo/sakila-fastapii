from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from datetime import datetime

def get_customer(db: Session, customer_id: int):
    """
    Retrieve a customer by ID.
    """
    return db.query(Customer).filter(Customer.customer_id == customer_id).first()

def get_customers(db: Session, skip: int = 0, limit: int = 100, name_query: str = None):
    """
    Retrieve a list of customers with pagination and optional search by name.
    """
    query = db.query(Customer)
    if name_query:
        query = query.filter(
            or_(
                Customer.first_name.ilike(f"%{name_query}%"),
                Customer.last_name.ilike(f"%{name_query}%")
            )
        )
    return query.offset(skip).limit(limit).all()

def create_customer(db: Session, customer_in: CustomerCreate):
    """
    Create a new customer.
    """
    customer_data = customer_in.model_dump()
    customer_data["create_date"] = datetime.now()
    db_customer = Customer(**customer_data)
    
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def update_customer(db: Session, customer_id: int, customer_in: CustomerUpdate):
    """
    Update a customer's details.
    """
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None
    
    update_data = customer_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
        
    db.commit()
    db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int):
    """
    Delete a customer by ID.
    """
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None
    db.delete(db_customer)
    db.commit()
    return db_customer
