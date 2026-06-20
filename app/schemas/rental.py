from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.rental import PaymentStatusEnum

class PaymentBase(BaseModel):
    customer_id: int
    staff_id: int
    amount: Decimal
    payment_date: datetime
    tx_hash: Optional[str] = Field(None, max_length=255)
    wallet_address: Optional[str] = Field(None, max_length=100)
    status: Optional[PaymentStatusEnum] = PaymentStatusEnum.PENDING

class PaymentCreate(PaymentBase):
    rental_id: Optional[int] = None

class PaymentResponse(PaymentBase):
    payment_id: int
    rental_id: Optional[int] = None
    last_update: Optional[datetime] = None

    class Config:
        from_attributes = True

class RentalBase(BaseModel):
    rental_date: datetime
    inventory_id: int
    customer_id: int
    return_date: Optional[datetime] = None
    staff_id: int

class RentalCreate(BaseModel):
    inventory_id: int
    customer_id: int
    staff_id: int
    rental_date: Optional[datetime] = None  # Defaults to current time if null
    # Optional direct payment creation properties
    amount: Optional[Decimal] = None
    tx_hash: Optional[str] = None
    wallet_address: Optional[str] = None

class RentalUpdate(BaseModel):
    rental_date: Optional[datetime] = None
    inventory_id: Optional[int] = None
    customer_id: Optional[int] = None
    return_date: Optional[datetime] = None
    staff_id: Optional[int] = None

class RentalResponse(RentalBase):
    rental_id: int
    last_update: datetime
    payments: List[PaymentResponse] = []

    class Config:
        from_attributes = True
