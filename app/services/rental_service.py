from sqlalchemy.orm import Session
from app.models.rental import Rental, Payment, PaymentStatusEnum
from app.models.film import Inventory
from app.models.customer import Customer
from app.schemas.rental import RentalCreate, RentalUpdate
from fastapi import HTTPException
from datetime import datetime

def get_rental(db: Session, rental_id: int):
    """
    Retrieve a rental by its ID.
    """
    return db.query(Rental).filter(Rental.rental_id == rental_id).first()

def get_rentals(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve a list of rentals with pagination.
    """
    return db.query(Rental).offset(skip).limit(limit).all()

def create_rental(db: Session, rental_in: RentalCreate):
    """
    Create a new rental. Includes checks for customer active status and inventory availability.
    Optionally logs an initial payment if amount is provided.
    """
    # 1. Verify customer exists and is active
    customer = db.query(Customer).filter(Customer.customer_id == rental_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer with ID {rental_in.customer_id} not found")
    if not customer.active:
        raise HTTPException(status_code=400, detail="Customer is currently inactive")
        
    # 2. Verify inventory item exists
    inventory = db.query(Inventory).filter(Inventory.inventory_id == rental_in.inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail=f"Inventory item with ID {rental_in.inventory_id} not found")
        
    # 3. Check if inventory item is currently rented out (return_date is Null)
    active_rental = db.query(Rental).filter(
        Rental.inventory_id == rental_in.inventory_id,
        Rental.return_date.is_(None)
    ).first()
    if active_rental:
        raise HTTPException(status_code=400, detail="Inventory item is currently rented out")
        
    # 4. Create the rental record
    rental_date = rental_in.rental_date or datetime.now()
    db_rental = Rental(
        rental_date=rental_date,
        inventory_id=rental_in.inventory_id,
        customer_id=rental_in.customer_id,
        staff_id=rental_in.staff_id,
        return_date=None
    )
    db.add(db_rental)
    db.flush()  # Populate db_rental.rental_id
    
    # 5. Create associated payment if payment info is supplied
    if rental_in.amount is not None:
        pay_status = PaymentStatusEnum.CONFIRMED if rental_in.tx_hash else PaymentStatusEnum.PENDING
        db_payment = Payment(
            customer_id=rental_in.customer_id,
            staff_id=rental_in.staff_id,
            rental_id=db_rental.rental_id,
            amount=rental_in.amount,
            payment_date=rental_date,
            tx_hash=rental_in.tx_hash,
            wallet_address=rental_in.wallet_address,
            status=pay_status
        )
        db.add(db_payment)
        
    db.commit()
    db.refresh(db_rental)
    return db_rental

def update_rental(db: Session, rental_id: int, rental_in: RentalUpdate):
    """
    Update a rental record (e.g. to set return_date).
    """
    db_rental = get_rental(db, rental_id)
    if not db_rental:
        return None
        
    update_data = rental_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rental, key, value)
        
    db.commit()
    db.refresh(db_rental)
    return db_rental

def delete_rental(db: Session, rental_id: int):
    """
    Delete a rental by ID, nullifying or cleaning up associated payments.
    """
    db_rental = get_rental(db, rental_id)
    if not db_rental:
        return None
    
    # Clean up associated payments by setting their rental_id to Null
    # (or delete them if required, nullifying matches MySQL database constraints)
    for payment in db_rental.payments:
        payment.rental_id = None
        
    db.delete(db_rental)
    db.commit()
    return db_rental
