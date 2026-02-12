# 🏥 Diabetes Prediction Pipeline with Apache Airflow

An automated machine learning pipeline built with **Apache Airflow** and **Docker** that predicts the likelihood of diabetes in patients using the Diabetes Prediction Dataset.

## 📋 Overview

This project implements a complete MLOps pipeline using Airflow to orchestrate a supervised binary classification workflow. The pipeline:

1. **Loads** the diabetes prediction dataset (CSV format)
2. **Preprocesses** data by encoding categoricals and scaling numerical features
3. **Trains** a Random Forest Classifier with balanced class weights
4. **Evaluates** the model with accuracy, ROC-AUC, confusion matrix, and feature importance scores
5. **Notifies** completion status

The pipeline runs entirely in Docker containers, making it reproducible and environment-agnostic.

## 🎯 ML Model

**Model Type:** Binary Classification (Random Forest Classifier)  
**Target Variable:** `diabetes` (0 = No Diabetes, 1 = Diabetes)  
**Input Features:** 8 features (gender, age, hypertension, heart_disease, smoking_history, bmi, HbA1c_level, blood_glucose_level)  
**Key Technique:** Stratified Train/Test Split (80/20) with StandardScaler for numerical normalization

### Key Design Decisions

- **Balanced Class Weights:** Handles the ~91% vs ~9% class imbalance in the raw data
- **StandardScaler:** Normalizes all numerical features to mean=0, std=1 for better convergence
- **LabelEncoder:** Encodes categorical columns (gender, smoking_history) to numerical values
- **XCom Serialization:** Passes DataFrames between Airflow tasks using base64-encoded pickle format

## 📁 Project Structure

```
Lab2/
├── dags/
│   ├── data/
│   │   └── diabetes_prediction_dataset.csv   # Input dataset (~100K rows, 9 columns)
│   ├── model/
│   │   └── diabetes_rf_model.sav              # Trained model + scaler (pickle format)
│   ├── src/
│   │   ├── __init__.py
│   │   └── lab.py                             # ML pipeline logic (5 tasks)
│   └── airflow.py                             # Airflow DAG definition
├── logs/                                       # Airflow task execution logs
├── plugins/                                    # Custom Airflow plugins (empty)
├── docker-compose.yaml                         # Docker services: Airflow, Postgres, Redis
├── README.md                                   # This file
└── .env                                        # Environment variables (AIRFLOW_UID)
```

## 🔧 Pipeline Tasks

### 1. **setup_directories** (BashOperator)
Creates the `/opt/airflow/dags/model` directory to store trained models.

### 2. **load_data_task** (PythonOperator)
Loads `dags/data/diabetes_prediction_dataset.csv` and pushes the raw DataFrame to XCom.

**Function:** `load_data(ti, file_path="dags/data/diabetes_prediction_dataset.csv")`

**Output:**
- Prints dataset shape, columns, and class distribution
- Serializes DataFrame using base64 pickle encoding

### 3. **preprocess_data_task** (PythonOperator)
Encodes categorical features, scales numerical features, and splits data into train/test sets.

**Function:** `preprocess_data(ti)`

**Processing Steps:**
- LabelEncode: `gender` and `smoking_history`
- StandardScale: All features except target
- Stratified Train/Test Split: 80/20 ratio to preserve class balance

**Output:** Scaler and split data (X_train_scaled, X_test_scaled, y_train, y_test)

### 4. **train_save_model_task** (PythonOperator)
Trains a Random Forest Classifier and saves model + scaler to disk.

**Function:** `train_save_model(ti)`

**Model Configuration:**
```python
RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_leaf=5,
    class_weight='balanced',  # Handles class imbalance
    random_state=42,
    n_jobs=-1  # Use all CPU cores
)
```

**Output:** Saves to `/opt/airflow/dags/model/diabetes_rf_model.sav`

### 5. **evaluate_model_task** (PythonOperator)
Loads the model and evaluates predictions on the test set.

**Function:** `evaluate_model(ti)`

**Evaluation Metrics:**
- **Accuracy:** Overall correctness (%)
- **ROC-AUC:** Area under the ROC curve (0-1 scale, 1.0 = perfect)
- **Confusion Matrix:** TN, FP, FN, TP breakdown
- **Classification Report:** Precision, Recall, F1-Score per class
- **Feature Importances:** Top contributing features

**Sample Output:**
```
========== 🩺 Diabetes Prediction - Model Evaluation ==========
✅ Accuracy  : 96.50%
✅ ROC-AUC   : 0.9850

Confusion Matrix (Rows=Actual, Cols=Predicted):
              Predicted No  Predicted Yes
Actual No   :     9120      180
Actual Yes  :     145       555

📊 Feature Importances (top to bottom):
  blood_glucose_level    : 0.3250
  HbA1c_level            : 0.2180
  age                    : 0.1850
  ...
```

### 6. **notify_task** (BashOperator)
Prints a success message confirming pipeline completion.

## 🚀 Getting Started

### Prerequisites

- **Docker Desktop:** [Download here](https://www.docker.com/products/docker-desktop)
- **Memory:** Allocate at least 4GB to Docker (8GB recommended)
- **Disk Space:** ~2GB for Docker images and logs

### System Memory Check

```bash
docker run --rm "debian:bullseye-slim" bash -c 'numfmt --to iec $(echo $(($(getconf _PHYS_PAGES) * $(getconf PAGE_SIZE))))'
```

### Step-by-Step Installation

#### 1. Clone or Download the Repository

```bash
cd /path/to/Lab2
```

#### 2. Set Airflow UID

```bash
# macOS/Linux
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Windows (Git Bash or WSL)
echo "AIRFLOW_UID=50000" > .env
```

#### 3. Create Necessary Directories

```bash
mkdir -p dags logs plugins working_data
```

#### 4. Verify Docker Compose Installation

```bash
docker compose version
```

#### 5. Initialize Airflow Database

```bash
docker compose up airflow-init
```

**Wait for output:** `exited with code 0`

#### 6. Start Services

```bash
docker compose up -d
```

**Check status:**
```bash
docker compose ps
```

Expected output (all services healthy):
```
CONTAINER ID   IMAGE                      SERVICE             STATUS
abc123...      apache/airflow:2.9.2       airflow-webserver   Up 2 minutes (healthy)
def456...      apache/airflow:2.9.2       airflow-scheduler   Up 2 minutes (healthy)
ghi789...      apache/airflow:2.9.2       airflow-worker      Up 2 minutes (healthy)
jkl012...      postgres:13                postgres            Up 2 minutes (healthy)
mno345...      redis:7.2-bookworm         redis               Up 2 minutes (healthy)
```

#### 7. Access Airflow UI

Open your browser and navigate to:

```
http://localhost:8080
```

**Login Credentials:**
- **Username:** `airflow2`
- **Password:** `airflow2`

## 🎬 Running the Pipeline

### Option 1: Trigger via Airflow UI

1. On the **DAGs** page, find `Diabetes_Prediction_Pipeline`
2. Click the **play button** (▶️) on the right side
3. Click **Trigger DAG** in the dialog

### Option 2: Trigger via CLI

```bash
docker compose exec airflow-cli airflow dags trigger Diabetes_Prediction_Pipeline
```

### Monitor Pipeline Execution

1. Click on the DAG name (`Diabetes_Prediction_Pipeline`)
2. View the **Graph** tab to see task dependencies
3. Click individual tasks to view **Logs**
4. Check the **evaluate_model_task** logs for final metrics

## 📊 Viewing Results

After pipeline completion, check the **evaluate_model_task** logs:

```bash
# View logs directly
docker compose logs airflow-scheduler | grep -A 50 "evaluate_model_task"
```

Or navigate to the Airflow UI → DAG → Task Instance → Logs

## 🛠️ Troubleshooting

### Service Won't Start

**Problem:** `docker compose up` fails with memory error

**Solution:**
```bash
# Allocate more memory to Docker (in Docker Desktop preferences)
# Recommended: 8GB
```

### Postgres Connection Error

**Problem:** `could not translate host name postgres to address`

**Solution:**
```bash
# Restart containers
docker compose down
docker compose up -d
```

### Missing Data File

**Problem:** `FileNotFoundError: diabetes_prediction_dataset.csv`

**Ensure the file exists at:** `dags/data/diabetes_prediction_dataset.csv`

If missing, add your diabetes dataset CSV to the `dags/data/` directory.

### View Container Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f airflow-scheduler
```

## 📦 Dependencies

### Python Packages

```
pandas>=1.3.0          # Data manipulation
scikit-learn>=1.0.0    # ML models and metrics
numpy>=1.21.0          # Numerical computing
```

### Docker Services

- **apache/airflow:2.9.2** - Airflow with Python 3.11
- **postgres:13** - Metadata database
- **redis:7.2-bookworm** - Task message broker
- **celery** - Distributed task queue (included in Airflow)

## 🧹 Cleanup

### Stop Services (Keep Data)

```bash
docker compose down
```

### Stop Services (Delete All Data)

```bash
docker compose down -v
```

### Reset Pipeline State

```bash
# Delete logs
rm -rf logs/*

# Stop and remove containers
docker compose down -v
docker compose up airflow-init
```

## 🔗 References

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow Docker Compose Setup](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [scikit-learn RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
- [Diabetes Prediction Dataset](https://www.kaggle.com/datasets/iammustafatz/diabetes-prediction-dataset)

## 📝 Notes

- **Data Leakage Prevention:** Scaler is fit ONLY on training data and applied to test data
- **Class Imbalance:** Handled via `class_weight='balanced'` parameter
- **Reproducibility:** Random seeds (random_state=42) ensure consistent results
- **Logging:** All task outputs stored in `logs/` directory with DAG ID and run ID hierarchy

## 👨‍💻 Development

### Running Individual Tasks

```bash
# Trigger a specific task
docker compose exec airflow-cli airflow tasks test Diabetes_Prediction_Pipeline load_data_task 2025-01-01
```

### Viewing DAG Definition

```bash
# Check DAG syntax
docker compose exec airflow-cli airflow dags list

# Get DAG details
docker compose exec airflow-cli airflow dags info Diabetes_Prediction_Pipeline
```

### Modifying the Pipeline

1. Edit `dags/src/lab.py` or `dags/airflow.py`
2. Airflow auto-detects changes (check scheduler logs)
3. Trigger a new run to test changes

## 📜 License

This project is provided as-is for educational and development purposes.
