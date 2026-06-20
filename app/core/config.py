from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sakila FastAPI Backend"
    API_V1_STR: str = "/api"
    
    # Configuración de la URL de la base de datos
    # Valor por defecto: usuario root, sin contraseña en localhost, base de datos sakila
    DATABASE_URL: str = "mysql+pymysql://root:@localhost:3306/sakila"
    
    # Ruta donde se guardarán los archivos de los modelos ML y las métricas
    MODEL_DIR: str = "./app/models/saved_models"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
