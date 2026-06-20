from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from decimal import Decimal

class DataIngestRequest(BaseModel):
    source: str = Field("manual", description="Data source identifier")
    data: List[Dict[str, Any]] = Field(..., description="Array of records to ingest")
    format: str = Field("json", description="Data format (json or csv)")

class IngestResponse(BaseModel):
    id: int
    source: str
    format: str
    status: str
    record_count: int
    created_at: datetime

class DataProcessRequest(BaseModel):
    ingestion_id: Optional[int] = Field(None, description="Process a specific ingestion by ID")
    all_pending: bool = Field(False, description="Process all pending ingestions")
    transformations: Optional[List[str]] = Field(None, description="Transformations to apply (clean, normalize, aggregate)")

class MetricResponse(BaseModel):
    id: int
    ingestion_id: Optional[int]
    metric_name: str
    metric_value: Decimal
    dimension: Optional[str]
    dimension_value: Optional[str]
    created_at: datetime

class ProcessResponse(BaseModel):
    status: str
    ingestion_ids: List[int]
    metrics_generated: int
    details: Dict[str, Any]

class ProcessedMetricsResponse(BaseModel):
    metrics: List[MetricResponse]
    total_count: int

class QualityMetricsResponse(BaseModel):
    total_ingested: int
    total_processed: int
    total_failed: int
    records_by_source: Dict[str, int]
    records_by_status: Dict[str, int]
