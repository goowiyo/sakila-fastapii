from sqlalchemy import Column, Integer, SmallInteger, String, Boolean, DateTime, TIMESTAMP
from sqlalchemy.orm import relationship
from app.core.database import Base

class Customer(Base):
    __tablename__ = 'customer'
    
    customer_id = Column(SmallInteger, primary_key=True, autoincrement=True)
    store_id = Column(Integer, nullable=False, index=True)
    first_name = Column(String(45), nullable=False)
    last_name = Column(String(45), nullable=False, index=True)
    email = Column(String(50), nullable=True)
    address_id = Column(SmallInteger, nullable=False, index=True)
    active = Column(Boolean, nullable=False, default=True)
    create_date = Column(DateTime, nullable=False)
    last_update = Column(TIMESTAMP, nullable=True, server_default='CURRENT_TIMESTAMP')
    
    # Relationships
    # Rental and Payment relationships resolve from app/models/rental.py
    rentals = relationship("Rental", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
