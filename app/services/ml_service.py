from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.schemas.ml import ModelMetrics, PredictRequest, PredictResponse
from fastapi import HTTPException
from typing import Dict, Any
import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

# Machine Learning imports
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

def get_ml_dataset(db: Session) -> pd.DataFrame:
    """
    Query MySQL Sakila database to build the ML training dataset.
    """
    # 1. Get global max rental date to use as reference for days_since_last_rental
    max_rental_res = db.execute(text("SELECT MAX(rental_date) FROM rental")).scalar()
    max_rental_date = max_rental_res if max_rental_res else datetime.now()

    # 2. Query film characteristics and rental counts
    query = text("""
        SELECT 
            f.film_id,
            f.length,
            f.rating,
            f.replacement_cost,
            f.rental_rate,
            c.name AS category,
            COUNT(r.rental_id) AS rental_count,
            MAX(r.rental_date) AS last_rental_date
        FROM film f
        LEFT JOIN film_category fc ON f.film_id = fc.film_id
        LEFT JOIN category c ON fc.category_id = c.category_id
        LEFT JOIN inventory i ON f.film_id = i.film_id
        LEFT JOIN rental r ON i.inventory_id = r.inventory_id
        GROUP BY f.film_id, c.name, f.length, f.rating, f.replacement_cost, f.rental_rate;
    """)
    
    # Read sql query into pandas DataFrame
    df = pd.read_sql(query, con=db.bind)
    
    # 3. Feature engineering: days_since_last_rental
    df['last_rental_date'] = pd.to_datetime(df['last_rental_date'])
    df['days_since_last_rental'] = (max_rental_date - df['last_rental_date']).dt.days
    
    # If never rented, impute days_since_last_rental with a large number (e.g. 365)
    df['days_since_last_rental'] = df['days_since_last_rental'].fillna(365.0)
    
    # Convert types
    df['length'] = pd.to_numeric(df['length'], errors='coerce')
    df['replacement_cost'] = pd.to_numeric(df['replacement_cost'], errors='coerce')
    df['rental_rate'] = pd.to_numeric(df['rental_rate'], errors='coerce')
    df['category'] = df['category'].fillna('Unknown')
    df['rating'] = df['rating'].fillna('G')
    
    return df

def train_ml_models(db: Session):
    """
    Extract data, preprocess features, train RF, XGBoost, and Linear Regression models,
    calculate evaluation metrics, and persist the pipelines and metrics metadata.
    """
    # 1. Fetch dataset
    df = get_ml_dataset(db)
    
    # 2. Extract features and target
    X = df[['category', 'length', 'rating', 'replacement_cost', 'rental_rate', 'days_since_last_rental']]
    y = df['rental_count']
    
    # 3. Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Create preprocessing pipelines
    numerical_features = ['length', 'replacement_cost', 'rental_rate', 'days_since_last_rental']
    categorical_features = ['category', 'rating']
    
    num_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    cat_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_pipeline, numerical_features),
            ('cat', cat_pipeline, categorical_features)
        ]
    )
    
    # 5. Define regression models
    models = {
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "XGBoost": XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "LinearRegression": LinearRegression()
    }
    
    trained_pipelines = {}
    metrics_metadata = {}
    
    # Ensure save directory exists
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    
    # 6. Fit and evaluate each model
    for name, model in models.items():
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model)
        ])
        
        # Train
        pipeline.fit(X_train, y_train)
        
        # Predict
        y_pred = pipeline.predict(X_test)
        
        # Compute metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        metrics_metadata[name] = {
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2)
        }
        
        # Persist model pipeline
        model_filename = os.path.join(settings.MODEL_DIR, f"{name.lower()}_model.joblib")
        joblib.dump(pipeline, model_filename)
        
    # Persist metrics metadata
    metrics_filename = os.path.join(settings.MODEL_DIR, "metrics.json")
    with open(metrics_filename, "w") as f:
        json.dump(metrics_metadata, f, indent=4)
        
    return metrics_metadata

def get_saved_metrics() -> Dict[str, Any]:
    """
    Retrieve comparative metrics of the saved models.
    """
    metrics_filename = os.path.join(settings.MODEL_DIR, "metrics.json")
    if not os.path.exists(metrics_filename):
        raise HTTPException(
            status_code=400, 
            detail="Models have not been trained yet. Please call POST /ml/train first."
        )
    
    with open(metrics_filename, "r") as f:
        return json.load(f)

def predict_demand(db: Session, request: PredictRequest) -> PredictResponse:
    """
    Predict rental demand for a film using all three saved models.
    Supports either database lookup via film_id or direct property inputs.
    """
    input_features = {}
    film_id = request.film_id
    
    # 1. Fetch film features from database if film_id is specified
    if film_id is not None:
        # Query database for the specified film's features
        max_rental_res = db.execute(text("SELECT MAX(rental_date) FROM rental")).scalar()
        max_rental_date = max_rental_res if max_rental_res else datetime.now()
        
        query = text("""
            SELECT 
                f.film_id,
                f.length,
                f.rating,
                f.replacement_cost,
                f.rental_rate,
                c.name AS category,
                MAX(r.rental_date) AS last_rental_date
            FROM film f
            LEFT JOIN film_category fc ON f.film_id = fc.film_id
            LEFT JOIN category c ON fc.category_id = c.category_id
            LEFT JOIN inventory i ON f.film_id = i.film_id
            LEFT JOIN rental r ON i.inventory_id = r.inventory_id
            WHERE f.film_id = :film_id
            GROUP BY f.film_id, c.name, f.length, f.rating, f.replacement_cost, f.rental_rate;
        """)
        
        result = db.execute(query, {"film_id": film_id}).mappings().first()
        if not result:
            raise HTTPException(status_code=404, detail=f"Film with ID {film_id} not found")
            
        last_date = result["last_rental_date"]
        days_since = (max_rental_date - last_date).days if last_date else 365.0
        
        input_features = {
            "category": result["category"] or "Unknown",
            "length": result["length"],
            "rating": result["rating"] or "G",
            "replacement_cost": float(result["replacement_cost"]),
            "rental_rate": float(result["rental_rate"]),
            "days_since_last_rental": float(days_since)
        }
    else:
        # Validate that all raw features are provided
        required_fields = ["category", "length", "rating", "replacement_cost", "rental_rate", "days_since_last_rental"]
        missing = [f for f in required_fields if getattr(request, f) is None]
        if missing:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing features for prediction: {missing}. Provide film_id or all feature values."
            )
            
        input_features = {
            "category": request.category,
            "length": request.length,
            "rating": request.rating,
            "replacement_cost": request.replacement_cost,
            "rental_rate": request.rental_rate,
            "days_since_last_rental": request.days_since_last_rental
        }

    # 2. Check if models exist
    models = ["randomforest", "xgboost", "linearregression"]
    predictions = {}
    
    for model_name in models:
        model_path = os.path.join(settings.MODEL_DIR, f"{model_name}_model.joblib")
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=400, 
                detail="Models have not been trained yet. Please call POST /ml/train first."
            )
            
        # Load and run prediction
        pipeline = joblib.load(model_path)
        
        # Convert input_features into a 1-row DataFrame
        input_df = pd.DataFrame([input_features])
        
        # Run prediction
        pred_val = pipeline.predict(input_df)[0]
        # Keep predictions non-negative since rental count cannot be negative
        predictions[model_name] = max(0.0, float(pred_val))

    # 3. Read metrics to identify the best model
    metrics = get_saved_metrics()
    
    # Best model has the lowest Mean Absolute Error (MAE)
    best_model_key = min(metrics.keys(), key=lambda k: metrics[k]["mae"])
    best_model_name = best_model_key.lower() # 'randomforest', 'xgboost', 'linearregression'
    
    # Find matching model prediction value
    recommended_prediction = predictions.get(best_model_name, predictions["randomforest"])

    return PredictResponse(
        film_id=film_id,
        input_features=input_features,
        predictions=predictions,
        best_model=best_model_key,
        recommended_prediction=recommended_prediction
    )
