from sqlalchemy import Column, Integer, String, Text, Numeric, TIMESTAMP, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class DataIngestion(Base):
    __tablename__ = 'raw_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False, default='manual')
    format = Column(String(20), nullable=False, default='json')
    status = Column(String(20), nullable=False, default='pending')
    record_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    raw_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    metrics = relationship("ProcessedMetric", back_populates="ingestion", cascade="all, delete-orphan")

class ProcessedMetric(Base):
    __tablename__ = 'processed_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingestion_id = Column(Integer, ForeignKey('raw_data.id'), nullable=True)
    metric_name = Column(String(200), nullable=False)
    metric_value = Column(Numeric(20, 6), nullable=False)
    dimension = Column(String(100), nullable=True)
    dimension_value = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    ingestion = relationship("DataIngestion", back_populates="metrics")
