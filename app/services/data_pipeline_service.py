import json
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
from app.models.data_pipeline import DataIngestion, ProcessedMetric
from app.schemas.data_pipeline import DataIngestRequest

REQUIRED_FIELDS_BY_SOURCE = {
    "film": ["title", "language_id"],
    "rental": ["inventory_id", "customer_id"],
    "customer": ["first_name", "last_name", "email"],
    "payment": ["customer_id", "rental_id", "amount"],
    "default": []
}

def _validate_data(source: str, records: List[Dict[str, Any]]) -> Tuple[bool, Optional[str], int]:
    if not records:
        return False, "No records provided", 0
    required = REQUIRED_FIELDS_BY_SOURCE.get(source, REQUIRED_FIELDS_BY_SOURCE["default"])
    missing_fields = set()
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            return False, f"Record at index {i} is not a valid object", i
        for field in required:
            if field not in record or record[field] is None:
                missing_fields.add(field)
    if missing_fields:
        return False, f"Missing required fields: {', '.join(sorted(missing_fields))}", len(records)
    return True, None, len(records)

def ingest_data(db: Session, request: DataIngestRequest) -> DataIngestion:
    valid, error_msg, record_count = _validate_data(request.source, request.data)
    if not valid:
        raise HTTPException(status_code=400, detail=error_msg)
    ingestion = DataIngestion(
        source=request.source,
        format=request.format,
        status="validated",
        record_count=record_count,
        raw_payload=json.dumps(request.data, default=str),
        created_at=datetime.utcnow()
    )
    db.add(ingestion)
    db.commit()
    db.refresh(ingestion)
    return ingestion

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace(["", "N/A", "null", "None", "nan"], np.nan)
    for col in df.select_dtypes(include=[object]).columns:
        df[col] = df[col].astype(str).str.strip()
    return df

def _compute_metrics(source: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
    metrics = []
    metrics.append({"metric_name": "total_records", "metric_value": len(df), "dimension": None, "dimension_value": None})
    metrics.append({"metric_name": "total_columns", "metric_value": len(df.columns), "dimension": None, "dimension_value": None})
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            metrics.append({
                "metric_name": "null_count",
                "metric_value": null_count,
                "dimension": "column",
                "dimension_value": col
            })
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        metrics.append({
            "metric_name": "avg",
            "metric_value": float(df[col].mean()) if not df[col].isna().all() else 0.0,
            "dimension": "column",
            "dimension_value": col
        })
        metrics.append({
            "metric_name": "sum",
            "metric_value": float(df[col].sum()) if not df[col].isna().all() else 0.0,
            "dimension": "column",
            "dimension_value": col
        })
        metrics.append({
            "metric_name": "min",
            "metric_value": float(df[col].min()) if not df[col].isna().all() else 0.0,
            "dimension": "column",
            "dimension_value": col
        })
        metrics.append({
            "metric_name": "max",
            "metric_value": float(df[col].max()) if not df[col].isna().all() else 0.0,
            "dimension": "column",
            "dimension_value": col
        })
    cat_cols = df.select_dtypes(include=[object]).columns
    for col in cat_cols:
        value_counts = df[col].value_counts().head(10)
        for val, count in value_counts.items():
            metrics.append({
                "metric_name": "top_values",
                "metric_value": int(count),
                "dimension": col,
                "dimension_value": str(val)
            })
    if source in ("rental", "payment"):
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower():
                try:
                    date_series = pd.to_datetime(df[col], errors='coerce')
                    date_series = date_series.dropna()
                    if not date_series.empty:
                        monthly = date_series.dt.to_period('M').value_counts().sort_index()
                        for period, count in monthly.items():
                            metrics.append({
                                "metric_name": "records_by_month",
                                "metric_value": int(count),
                                "dimension": col,
                                "dimension_value": str(period)
                            })
                except Exception:
                    pass
    return metrics

def _aggregate_data(source: str, df: pd.DataFrame, db: Session) -> List[ProcessedMetric]:
    if source == "film":
        if "rental_rate" in df.columns:
            try:
                df["rental_rate"] = pd.to_numeric(df["rental_rate"], errors='coerce')
                avg_rate = float(df["rental_rate"].mean())
                return [ProcessedMetric(
                    metric_name="avg_rental_rate",
                    metric_value=avg_rate,
                    dimension=None,
                    dimension_value=None
                )]
            except Exception:
                pass
    if source == "rental":
        for col in df.columns:
            if "date" in col.lower():
                try:
                    date_series = pd.to_datetime(df[col], errors='coerce').dropna()
                    if not date_series.empty:
                        daily_counts = date_series.value_counts().sort_index()
                        peak_day = daily_counts.idxmax()
                        peak_count = int(daily_counts.max())
                        return [ProcessedMetric(
                            metric_name="peak_rental_day_count",
                            metric_value=peak_count,
                            dimension="date",
                            dimension_value=str(peak_day.date())
                        )]
                except Exception:
                    pass
    if source == "payment":
        if "amount" in df.columns:
            try:
                df["amount"] = pd.to_numeric(df["amount"], errors='coerce')
                total_revenue = float(df["amount"].sum())
                return [ProcessedMetric(
                    metric_name="total_revenue",
                    metric_value=total_revenue,
                    dimension=None,
                    dimension_value=None
                )]
            except Exception:
                pass
    return []

def process_ingestion(db: Session, ingestion: DataIngestion) -> List[ProcessedMetric]:
    try:
        ingestion.status = "processing"
        db.commit()
        raw_data = json.loads(ingestion.raw_payload) if ingestion.raw_payload else []
        df = pd.DataFrame(raw_data)
        if df.empty:
            ingestion.status = "failed"
            ingestion.error_message = "No data to process"
            db.commit()
            return []
        df = _clean_dataframe(df)
        metrics_list = []
        computed_metrics = _compute_metrics(ingestion.source, df)
        for m in computed_metrics:
            metric = ProcessedMetric(
                ingestion_id=ingestion.id,
                metric_name=m["metric_name"],
                metric_value=m["metric_value"],
                dimension=m["dimension"],
                dimension_value=m["dimension_value"]
            )
            db.add(metric)
            metrics_list.append(metric)
        agg_metrics = _aggregate_data(ingestion.source, df, db)
        for m in agg_metrics:
            m.ingestion_id = ingestion.id
            db.add(m)
            metrics_list.append(m)
        ingestion.status = "processed"
        ingestion.processed_at = datetime.utcnow()
        db.commit()
        for m in metrics_list:
            db.refresh(m)
        return metrics_list
    except Exception as e:
        ingestion.status = "failed"
        ingestion.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

def get_metrics(db: Session, metric_name: Optional[str] = None, dimension: Optional[str] = None, limit: int = 100, offset: int = 0) -> Tuple[List[ProcessedMetric], int]:
    query = db.query(ProcessedMetric)
    if metric_name:
        query = query.filter(ProcessedMetric.metric_name == metric_name)
    if dimension:
        query = query.filter(ProcessedMetric.dimension == dimension)
    total = query.count()
    metrics = query.order_by(ProcessedMetric.created_at.desc()).offset(offset).limit(limit).all()
    return metrics, total

def get_quality_metrics(db: Session) -> Dict[str, Any]:
    total_ingested = db.query(func.count(DataIngestion.id)).scalar() or 0
    total_processed = db.query(func.count(DataIngestion.id)).filter(DataIngestion.status == "processed").scalar() or 0
    total_failed = db.query(func.count(DataIngestion.id)).filter(DataIngestion.status == "failed").scalar() or 0
    sources = db.query(DataIngestion.source, func.count(DataIngestion.id)).group_by(DataIngestion.source).all()
    statuses = db.query(DataIngestion.status, func.count(DataIngestion.id)).group_by(DataIngestion.status).all()
    return {
        "total_ingested": total_ingested,
        "total_processed": total_processed,
        "total_failed": total_failed,
        "records_by_source": {s: int(c) for s, c in sources},
        "records_by_status": {s: int(c) for s, c in statuses}
    }
