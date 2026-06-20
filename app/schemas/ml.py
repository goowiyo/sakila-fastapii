from pydantic import BaseModel, Field
from typing import Optional, Dict, Union, Any

class ModelMetrics(BaseModel):
    mae: float
    rmse: float
    r2: float

class TrainResponse(BaseModel):
    status: str
    message: str
    metrics: Dict[str, ModelMetrics]

class MetricsResponse(BaseModel):
    status: str
    metrics: Dict[str, ModelMetrics]

class PredictRequest(BaseModel):
    film_id: Optional[int] = Field(None, description="Lookup features from database for this film ID")
    category: Optional[str] = Field(None, description="Category name (e.g. 'Action', 'Documentary')")
    length: Optional[int] = Field(None, description="Length of the film in minutes")
    rating: Optional[str] = Field(None, description="Rating enum (G, PG, PG-13, R, NC-17)")
    replacement_cost: Optional[float] = Field(None, description="Cost to replace the film")
    rental_rate: Optional[float] = Field(None, description="Daily rental rate of the film")
    days_since_last_rental: Optional[float] = Field(None, description="Number of days elapsed since the film was last rented")

class PredictResponse(BaseModel):
    film_id: Optional[int] = None
    input_features: Dict[str, Any]
    predictions: Dict[str, float]
    best_model: str
    recommended_prediction: float
