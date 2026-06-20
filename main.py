from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine as db_engine
from app.core.database import Base
from app.models import data_pipeline as pipeline_models
from app.api.film import router as film_router
from app.api.customer import router as customer_router
from app.api.rental import router as rental_router
from app.api.analytics import router as analytics_router
from app.api.ml import router as ml_router
from app.api.data_pipeline import router as data_pipeline_router
from sqlalchemy.exc import SQLAlchemyError
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sakila-fastapi")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Complete FastAPI backend for the Sakila DVD rental store, including CRUD, analytics, and ML demand prediction.",
    version="1.0.0"
)

# Create data pipeline tables on startup (if they don't exist)
@app.on_event("startup")
def create_pipeline_tables():
    try:
        Base.metadata.create_all(bind=db_engine, tables=[
            pipeline_models.DataIngestion.__table__,
            pipeline_models.ProcessedMetric.__table__,
        ])
    except Exception as e:
        logger.warning(f"Could not create pipeline tables: {e}. Ensure MySQL is running and sakila DB exists.")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database error handler
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database transaction failed. Check database logs or connection."}
    )

# Global generic error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"}
    )

# Mount API Routers
app.include_router(film_router, prefix=settings.API_V1_STR)
app.include_router(customer_router, prefix=settings.API_V1_STR)
app.include_router(rental_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(ml_router, prefix=settings.API_V1_STR)
app.include_router(data_pipeline_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
def index_redirect():
    """
    Redirect root path to interactive Swagger documentation page.
    """
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
