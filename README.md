# Backend FastAPI Sakila & Pipeline de Predicción de Demanda

Este proyecto es un backend completo desarrollado en FastAPI integrado con la clásica base de datos de alquiler de DVD Sakila (MySQL). Proporciona:
1. **API CRUD Core** para las entidades `Films` (Películas), `Customers` (Clientes) y `Rentals` (Alquileres).
2. **Reportes Analíticos** (Ingresos por categoría, inventario por tienda, tendencias mensuales).
3. **Pipeline de Machine Learning** utilizando scikit-learn y XGBoost para predecir la demanda de alquiler de películas.

---

## 📋 Requisitos y Dependencias

Todas las dependencias están definidas en `requirements.txt`. Los módulos clave son:
* **FastAPI y Uvicorn** - Framework web y servidor ASGI.
* **SQLAlchemy y PyMySQL** - Framework ORM y controlador de MySQL.
* **Scikit-learn, XGBoost, Pandas, NumPy, Joblib** - Manipulación de datasets, preprocesamiento, entrenamiento de modelos de regresión y persistencia de artefactos.

---

## 🚀 Instrucciones de Ejecución

### 1. Configurar el entorno
Asegúrate de que tu servidor MySQL esté ejecutándose en `localhost:3306` con la base de datos `sakila` cargada.
Por defecto, la aplicación se conecta utilizando `mysql+pymysql://root:@localhost:3306/sakila`. Para sobrescribir esto, define la variable de entorno:
```bash
# Windows PowerShell
$env:DATABASE_URL="mysql+pymysql://usuario:contraseña@localhost:3306/sakila"
```

### 2. Instalar dependencias
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
Una vez iniciada, abre [http://localhost:8000/docs](http://localhost:8000/docs) en tu navegador para interactuar con la página de documentación de Swagger.

---

## ⚙️ Pipeline de Machine Learning

El módulo de predicción de demanda compara los modelos **RandomForestRegressor**, **XGBoostRegressor** y **LinearRegression**.

### 1. Flujo de Procesamiento de Datos (ETL)
* El pipeline consulta las características y el historial de alquileres de las 1000 películas.
* Características extraídas: `length` (duración), `rating` (clasificación), `replacement_cost` (costo de reemplazo), `rental_rate` (tarifa de alquiler) y `category` (categoría).
* **Variable objetivo (Target)**: `rental_count` (el número de veces que se ha alquilado la película).
* **Lógica de Fecha de Referencia**: Dado que los datos históricos de Sakila terminan en 2006, la variable `days_since_last_rental` (días desde el último alquiler) se calcula con respecto a la fecha del último alquiler registrado en toda la base de datos (`2006-02-14`) en lugar de usar la hora actual del sistema, para garantizar que se capture la varianza del comportamiento.

### 2. Preprocesamiento y Codificación
* Los valores numéricos (`length`, `replacement_cost`, `rental_rate`, `days_since_last_rental`) se escalan usando `StandardScaler` e imputan con los valores medianos.
* Los atributos categóricos (`category`, `rating`) se procesan usando `OneHotEncoder` (con `handle_unknown='ignore'` e imputación por el valor más frecuente).
* Todo se estructura limpiamente en un único `ColumnTransformer` dentro del pipeline de entrenamiento del modelo.

### 3. Ajuste de Modelos y Persistencia de Métricas
El conjunto de datos se divide (80% entrenamiento, 20% prueba). Las métricas del modelo persistidas son:
* **MAE** (Error Absoluto Medio)
* **RMSE** (Raíz del Error Cuadrático Medio)
* **R²** (Coeficiente de Determinación)
Los objetos del pipeline entrenado y los archivos de evaluación del rendimiento se almacenan en `./app/models/saved_models`.

---

## 💡 Ejemplos de Solicitudes a Endpoints

### 1. Endpoints CRUD
* **Obtener Películas**:
  `GET /api/films/?skip=0&limit=5&title=ACADEMY`
* **Crear Película**:
  `POST /api/films/`
  ```json
  {
    "title": "AVATAR REBORN",
    "description": "Un drama futurista en una tierra mística.",
    "release_year": 2026,
    "language_id": 1,
    "rental_duration": 5,
    "rental_rate": 4.99,
    "length": 162,
    "replacement_cost": 29.99,
    "rating": "PG-13",
    "special_features": "Trailers,Behind the Scenes",
    "category_ids": [1, 2]
  }
  ```
* **Registrar Devolución de Alquiler** (Actualización de alquiler):
  `PUT /api/rentals/{rental_id}`
  ```json
  {
    "return_date": "2026-06-15T12:00:00"
  }
  ```

### 2. Endpoints de Analítica
* **Top 10 películas más rentadas**: `GET /api/analytics/top-films`
* **Ingresos por película**: `GET /api/analytics/revenue-by-film`
* **Ingresos por categoría**: `GET /api/analytics/revenue-by-category`
* **Tendencia de alquileres mensuales**: `GET /api/analytics/customer-activity`
* **Estado de disponibilidad del inventario**: `GET /api/analytics/inventory-availability`

### 3. Endpoints de Machine Learning
* **Entrenar modelos**:
  `POST /api/ml/train` -> Entrena y persiste los modelos, retornando métricas comparativas.
* **Obtener métricas persistidas**:
  `GET /api/ml/metrics` -> Retorna MAE, RMSE y R² de RandomForest, XGBoost y Linear Regression.
* **Predecir demanda**:
  `POST /api/ml/predict`
  * **Opción A** (Predecir para una película existente consultando sus atributos en la base de datos):
    ```json
    {
      "film_id": 1
    }
    ```
  * **Opción B** (Predecir para una película nueva hipotética usando atributos manuales):
    ```json
    {
      "category": "Action",
      "length": 120,
      "rating": "PG-13",
      "replacement_cost": 19.99,
      "rental_rate": 2.99,
      "days_since_last_rental": 10.0
    }
    ```
