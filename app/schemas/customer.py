from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    store_id: int
    first_name: str = Field(..., max_length=45)
    last_name: str = Field(..., max_length=45)
    email: Optional[str] = Field(None, max_length=50)
    address_id: int
    active: bool = True

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    store_id: Optional[int] = None
    first_name: Optional[str] = Field(None, max_length=45)
    last_name: Optional[str] = Field(None, max_length=45)
    email: Optional[str] = Field(None, max_length=50)
    address_id: Optional[int] = None
    active: Optional[bool] = None

class CustomerResponse(CustomerBase):
    customer_id: int
    create_date: datetime
    last_update: Optional[datetime] = None

    class Config:
        from_attributes = True
