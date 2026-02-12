from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='Diabetes_Prediction_Pipeline',
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    doc_md="""
    ### 🩺 Diabetes Prediction Pipeline (Random Forest Classifier)

    This DAG implements a supervised binary classification pipeline
    using the Diabetes Prediction Dataset.

    **Pipeline Steps:**
    1. **Setup**: Creates required directories.
    2. **Load Data**: Reads `diabetes_prediction_dataset.csv` into memory.
    3. **Preprocess**: Encodes categoricals, scales features, splits train/test.
    4. **Train**: Trains a Random Forest Classifier and saves it to disk.
    5. **Evaluate**: Loads model, predicts, and prints accuracy + ROC-AUC + report.
    6. **Notify**: Confirms successful pipeline completion.
    """,
    tags=['diabetes', 'random-forest', 'classification', 'healthcare'],
) as dag:

    # Import functions from lab.py
    from src.lab import (
        load_data,
        preprocess_data,
        train_save_model,
        evaluate_model,
    )

    # ── Task 0: Setup ──────────────────────────────────────────────
    setup_directories_task = BashOperator(
        task_id='setup_directories',
        bash_command='mkdir -p /opt/airflow/dags/model && echo "📁 Directories ready."',
    )

    # ── Task 1: Load Data ──────────────────────────────────────────
    load_data_task = PythonOperator(
        task_id='load_data_task',
        python_callable=load_data,
    )

    # ── Task 2: Preprocess ─────────────────────────────────────────
    preprocess_data_task = PythonOperator(
        task_id='preprocess_data_task',
        python_callable=preprocess_data,
    )

    # ── Task 3: Train & Save Model ─────────────────────────────────
    train_save_model_task = PythonOperator(
        task_id='train_save_model_task',
        python_callable=train_save_model,
    )

    # ── Task 4: Evaluate Model ─────────────────────────────────────
    evaluate_model_task = PythonOperator(
        task_id='evaluate_model_task',
        python_callable=evaluate_model,
    )

    # ── Task 5: Notify ─────────────────────────────────────────────
    notify_task = BashOperator(
        task_id='notify_task',
        bash_command='echo "✅ Diabetes prediction pipeline finished successfully!"',
    )

    # ── Pipeline Dependencies ──────────────────────────────────────
    (
        setup_directories_task
        >> load_data_task
        >> preprocess_data_task
        >> train_save_model_task
        >> evaluate_model_task
        >> notify_task
    )
