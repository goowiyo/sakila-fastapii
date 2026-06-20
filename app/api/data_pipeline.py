from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import csv
import io
import json
from app.core.database import get_db
from app.schemas.data_pipeline import (
    DataIngestRequest, IngestResponse, DataProcessRequest,
    ProcessResponse, ProcessedMetricsResponse, MetricResponse,
    QualityMetricsResponse
)
from app.services import data_pipeline_service as dps
from app.models.data_pipeline import DataIngestion, ProcessedMetric

router = APIRouter(prefix="/data", tags=["data-pipeline"])


@router.post("/ingest", response_model=IngestResponse, status_code=201)
def ingest_data(payload: DataIngestRequest, db: Session = Depends(get_db)):
    ingestion = dps.ingest_data(db, payload)
    return IngestResponse(
        id=ingestion.id,
        source=ingestion.source,
        format=ingestion.format,
        status=ingestion.status,
        record_count=ingestion.record_count,
        created_at=ingestion.created_at
    )


@router.post("/ingest/csv", response_model=IngestResponse, status_code=201)
def ingest_csv(
    file: UploadFile = File(...),
    source: str = Query("manual", description="Data source identifier"),
    db: Session = Depends(get_db)
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    records = []
    for row in reader:
        records.append({k.strip(): v.strip() for k, v in row.items()})
    if not records:
        raise HTTPException(status_code=400, detail="CSV file is empty or has no data rows")
    request = DataIngestRequest(source=source, data=records, format="csv")
    ingestion = dps.ingest_data(db, request)
    return IngestResponse(
        id=ingestion.id,
        source=ingestion.source,
        format=ingestion.format,
        status=ingestion.status,
        record_count=ingestion.record_count,
        created_at=ingestion.created_at
    )


@router.post("/process", response_model=ProcessResponse)
def process_data(payload: DataProcessRequest, db: Session = Depends(get_db)):
    ingestions = []
    if payload.ingestion_id is not None:
        ing = db.query(DataIngestion).filter(DataIngestion.id == payload.ingestion_id).first()
        if not ing:
            raise HTTPException(status_code=404, detail=f"Ingestion with ID {payload.ingestion_id} not found")
        if ing.status == "processed":
            raise HTTPException(status_code=400, detail=f"Ingestion {payload.ingestion_id} already processed")
        ingestions = [ing]
    elif payload.all_pending:
        ingestions = db.query(DataIngestion).filter(
            DataIngestion.status.in_(["validated", "pending"])
        ).all()
        if not ingestions:
            raise HTTPException(status_code=400, detail="No pending ingestions to process")
    else:
        raise HTTPException(status_code=400, detail="Specify ingestion_id or set all_pending=true")
    total_metrics = 0
    processed_ids = []
    details = {}
    for ing in ingestions:
        metrics = dps.process_ingestion(db, ing)
        total_metrics += len(metrics)
        processed_ids.append(ing.id)
        details[str(ing.id)] = {
            "status": ing.status,
            "metrics_generated": len(metrics),
            "error": ing.error_message if ing.status == "failed" else None
        }
    return ProcessResponse(
        status="completed",
        ingestion_ids=processed_ids,
        metrics_generated=total_metrics,
        details=details
    )


@router.get("/results", response_model=ProcessedMetricsResponse)
def get_results(
    metric_name: Optional[str] = Query(None, description="Filter by metric name"),
    dimension: Optional[str] = Query(None, description="Filter by dimension"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    metrics, total = dps.get_metrics(db, metric_name=metric_name, dimension=dimension, limit=limit, offset=offset)
    return ProcessedMetricsResponse(
        metrics=[MetricResponse(
            id=m.id,
            ingestion_id=m.ingestion_id,
            metric_name=m.metric_name,
            metric_value=m.metric_value,
            dimension=m.dimension,
            dimension_value=m.dimension_value,
            created_at=m.created_at
        ) for m in metrics],
        total_count=total
    )


@router.get("/results/{metric_id}", response_model=MetricResponse)
def get_metric_by_id(metric_id: int, db: Session = Depends(get_db)):
    metric = db.query(ProcessedMetric).filter(ProcessedMetric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail=f"Metric with ID {metric_id} not found")
    return MetricResponse(
        id=metric.id,
        ingestion_id=metric.ingestion_id,
        metric_name=metric.metric_name,
        metric_value=metric.metric_value,
        dimension=metric.dimension,
        dimension_value=metric.dimension_value,
        created_at=metric.created_at
    )


@router.get("/quality", response_model=QualityMetricsResponse)
def get_quality_metrics(db: Session = Depends(get_db)):
    return dps.get_quality_metrics(db)


@router.get("/ingestions", response_model=List[IngestResponse])
def list_ingestions(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(DataIngestion)
    if status:
        query = query.filter(DataIngestion.status == status)
    ingestions = query.order_by(DataIngestion.created_at.desc()).offset(offset).limit(limit).all()
    return [IngestResponse(
        id=ing.id,
        source=ing.source,
        format=ing.format,
        status=ing.status,
        record_count=ing.record_count,
        created_at=ing.created_at
    ) for ing in ingestions]
