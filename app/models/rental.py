from sqlalchemy import Column, Integer, SmallInteger, Numeric, String, DateTime, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class PaymentStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"

class Rental(Base):
    __tablename__ = 'rental'
    
    rental_id = Column(Integer, primary_key=True, autoincrement=True)
    rental_date = Column(DateTime, nullable=False, index=True)
    inventory_id = Column(Integer, ForeignKey('inventory.inventory_id'), nullable=False, index=True)
    customer_id = Column(SmallInteger, ForeignKey('customer.customer_id'), nullable=False, index=True)
    return_date = Column(DateTime, nullable=True)
    staff_id = Column(Integer, nullable=False, index=True)
    last_update = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    
    # Relationships
    inventory = relationship("Inventory", back_populates="rentals")
    customer = relationship("Customer", back_populates="rentals")
    payments = relationship("Payment", back_populates="rental")

class Payment(Base):
    __tablename__ = 'payment'
    
    payment_id = Column(SmallInteger, primary_key=True, autoincrement=True)
    customer_id = Column(SmallInteger, ForeignKey('customer.customer_id'), nullable=False, index=True)
    staff_id = Column(Integer, nullable=False, index=True)
    rental_id = Column(Integer, ForeignKey('rental.rental_id'), nullable=True, index=True)
    amount = Column(Numeric(5, 2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    last_update = Column(TIMESTAMP, nullable=True, server_default='CURRENT_TIMESTAMP')
    
    # Custom fields detected in DB schema
    tx_hash = Column(String(255), nullable=True)
    wallet_address = Column(String(100), nullable=True)
    status = Column(Enum(PaymentStatusEnum), nullable=True, default=PaymentStatusEnum.PENDING)
    
    # Relationships
    customer = relationship("Customer", back_populates="payments")
    rental = relationship("Rental", back_populates="payments")
