from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.ml import TrainResponse, MetricsResponse, PredictRequest, PredictResponse
from app.services import ml_service

router = APIRouter(prefix="/ml", tags=["machine-learning"])

@router.post("/train", response_model=TrainResponse)
def train_models(db: Session = Depends(get_db)):
    """
    Triggers the ETL dataset query, runs features preprocessing, trains Random Forest,
    XGBoost, and Linear Regression models, and saves them with evaluation metrics.
    """
    metrics = ml_service.train_ml_models(db)
    return TrainResponse(
        status="success",
        message="All models trained and persisted successfully.",
        metrics=metrics
    )

@router.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    """
    Retrieve performance evaluation metrics (MAE, RMSE, R2) for each model.
    """
    metrics = ml_service.get_saved_metrics()
    return MetricsResponse(
        status="success",
        metrics=metrics
    )

@router.post("/predict", response_model=PredictResponse)
def predict_demand(request: PredictRequest, db: Session = Depends(get_db)):
    """
    Predict movie demand (rental count) using the trained models.
    Supports either database lookup via 'film_id' or raw parameter input.
    """
    return ml_service.predict_demand(db, request=request)
