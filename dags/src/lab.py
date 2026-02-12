import pandas as pd
import numpy as np
import pickle
import base64
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report,
    roc_auc_score
)


# --- Task 1: Load Data ---
def load_data(ti, file_path: str = "dags/data/diabetes_prediction_dataset.csv"):
    """
    Loads the diabetes prediction dataset from a CSV file and pushes
    it to XCom for the next task.
    """
    df = pd.read_csv(file_path)
    print(f"✅ Data loaded successfully. Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nClass distribution:\n{df['diabetes'].value_counts()}")

    serialized_data = base64.b64encode(pickle.dumps(df)).decode("ascii")
    ti.xcom_push(key='raw_data', value=serialized_data)


# --- Task 2: Preprocess Data ---
def preprocess_data(ti):
    """
    Pulls raw data from XCom, encodes categorical columns, scales
    numerical features, splits into train/test sets, and pushes
    the processed data forward.
    """
    serialized_data = ti.xcom_pull(key='raw_data', task_ids='load_data_task')
    df = pickle.loads(base64.b64decode(serialized_data))

    # Encode categorical columns
    le = LabelEncoder()
    df['gender'] = le.fit_transform(df['gender'])            # Female=0, Male=1, Other=2
    df['smoking_history'] = le.fit_transform(df['smoking_history'])  # encode all categories

    print(f"✅ Encoding done. Sample:\n{df.head(3)}")

    # Separate features and target
    X = df.drop(columns=['diabetes'])
    y = df['diabetes']

    # Train/test split (stratified to preserve class balance)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale numerical features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    print(f"✅ Train size: {X_train_scaled.shape}, Test size: {X_test_scaled.shape}")

    data_tuple = (X_train_scaled, X_test_scaled, y_train, y_test, scaler)
    serialized_output = base64.b64encode(pickle.dumps(data_tuple)).decode("ascii")
    ti.xcom_push(key='processed_data', value=serialized_output)


# --- Task 3: Train and Save Model ---
def train_save_model(ti):
    """
    Pulls processed data, trains a Random Forest Classifier,
    and saves the model + scaler to disk.
    """
    serialized_data = ti.xcom_pull(key='processed_data', task_ids='preprocess_data_task')
    (X_train_scaled, _, y_train, _, scaler) = pickle.loads(base64.b64decode(serialized_data))

    # Train Random Forest Classifier
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_leaf=5,
        class_weight='balanced',   # handles class imbalance (91% vs 9%)
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    print(f"✅ Model trained. Number of trees: {model.n_estimators}")

    # Save model and scaler together
    model_dir = "/opt/airflow/dags/model"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "diabetes_rf_model.sav")

    with open(model_path, "wb") as f:
        pickle.dump((model, scaler), f)

    print(f"✅ Model saved to {model_path}")

    # Push model path for evaluate task
    ti.xcom_push(key='model_path', value=model_path)


# --- Task 4: Evaluate Model ---
def evaluate_model(ti):
    """
    Loads the saved model, runs predictions on the test set,
    and prints accuracy, ROC-AUC, confusion matrix, and
    full classification report.
    """
    serialized_data = ti.xcom_pull(key='processed_data', task_ids='preprocess_data_task')
    (_, X_test_scaled, _, y_test, _) = pickle.loads(base64.b64decode(serialized_data))

    model_path = ti.xcom_pull(key='model_path', task_ids='train_save_model_task')
    model, _ = pickle.load(open(model_path, "rb"))

    # Predictions
    y_pred      = model.predict(X_test_scaled)
    y_pred_prob = model.predict_proba(X_test_scaled)[:, 1]

    # Metrics
    accuracy  = accuracy_score(y_test, y_pred)
    roc_auc   = roc_auc_score(y_test, y_pred_prob)
    cm        = confusion_matrix(y_test, y_pred)
    report    = classification_report(y_test, y_pred, target_names=['No Diabetes', 'Diabetes'])

    print("\n========== 🩺 Diabetes Prediction - Model Evaluation ==========")
    print(f"✅ Accuracy  : {accuracy:.2%}")
    print(f"✅ ROC-AUC   : {roc_auc:.4f}")
    print(f"\nConfusion Matrix (Rows=Actual, Cols=Predicted):")
    print(f"              Predicted No  Predicted Yes")
    print(f"Actual No   :     {cm[0][0]:<8}  {cm[0][1]}")
    print(f"Actual Yes  :     {cm[1][0]:<8}  {cm[1][1]}")
    print(f"\nClassification Report:\n{report}")
    print("================================================================")

    # Feature importance
    feature_names = ['gender', 'age', 'hypertension', 'heart_disease',
                     'smoking_history', 'bmi', 'HbA1c_level', 'blood_glucose_level']
    importances = model.feature_importances_
    sorted_idx  = np.argsort(importances)[::-1]

    print("\n📊 Feature Importances (top to bottom):")
    for i in sorted_idx:
        print(f"  {feature_names[i]:<25}: {importances[i]:.4f}")
