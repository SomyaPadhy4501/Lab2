# Airflow lab
### EPL Match Outcome Prediction with Airflow

This project uses Apache Airflow running on Docker to create an automated machine learning pipeline. The goal is to predict the outcome (Home Win, Draw, or Away Win) of English Premier League (EPL) matches.

The pipeline fetches historical match data, engineers features to represent team form, trains two separate models to predict home and away goals, and then derives the final match outcome from those goal predictions.

### ML Model

This project uses a supervised learning approach to predict match outcomes. A critical step is feature engineering, where we calculate a team's historical performance (e.g., average shots, goals in the last 5 games) to use as input. 

#### Prerequisites

Before using this script, make sure you have the following libraries installed:

- pandas
- scikit-learn (sklearn)

#### Usage

The machine learning logic is defined in dags/src/lab.py and includes:

- load_and_feature_engineer(): Loads the EPL dataset and creates historical, rolling-average features for each team to represent their recent form.

- preprocess_and_split_data(): Prepares the data for modeling by scaling features and splitting it into training and testing sets for both the home and away goal models.

- train_goal_models(): Trains two separate RandomForestRegressor models—one for predicting home goals and one for away goals—and saves them.

- evaluate_models(): Loads the trained models, makes goal predictions on the test set, derives the final match outcomes, and prints a final accuracy score and confusion matrix.

### Project Structure
Your project directory should be set up as follows for the pipeline to work correctly:
```
airflow_lab1/
├── dags/
│   ├── data/
│   │   └── E0.csv 
│   ├── model/
│   │   └── epl_goal_models.sav
│   ├── src/
│   │   └── lab.py
│   └── airflow.py
├── logs/
├── plugins/
├── .env               
└── docker-compose.yaml
```

### Airflow Setup

Use Airflow to author workflows as directed acyclic graphs (DAGs) of tasks. The Airflow scheduler executes your tasks on an array of workers while following the specified dependencies.

References

-   Product - https://airflow.apache.org/
-   Documentation - https://airflow.apache.org/docs/
-   Github - https://github.com/apache/airflow

#### Installation

Prerequisites: You should allocate at least 4GB memory for the Docker Engine (ideally 8GB).

Local

-   Docker Desktop Running

Cloud

-   Linux VM
-   SSH Connection
-   Installed Docker Engine - [Install using the convenience script](https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script)

#### Step-by-Step Instructions

1. Create a new directory

    ```bash
    mkdir -p ~/app
    cd ~/app
    ```

2. Running Airflow in Docker - [Refer](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#running-airflow-in-docker)

    a. You can check if you have enough memory by running this command

    ```bash
    docker run --rm "debian:bullseye-slim" bash -c 'numfmt --to iec $(echo $(($(getconf _PHYS_PAGES) * $(getconf PAGE_SIZE))))'
    ```

    b. Fetch [docker-compose.yaml](https://airflow.apache.org/docs/apache-airflow/2.5.1/docker-compose.yaml)

    ```bash
    curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.5.1/docker-compose.yaml'
    ```

    c. Setting the right Airflow user

    ```bash
    mkdir -p ./dags ./logs ./plugins ./working_data
    echo -e "AIRFLOW_UID=$(id -u)" > .env
    ```

    d. Update the following in docker-compose.yml

    ```bash
    # Donot load examples
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'

    # Additional python package
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:- pandas scikit-learn}

    # Output dir
    - ${AIRFLOW_PROJ_DIR:-.}/working_data:/opt/airflow/working_data

    # Change default admin credentials
    _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow2}
    _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow2}
    ```

    e. Initialize the database

    ```bash
    docker compose up airflow-init
    ```

    f. Running Airflow

    ```bash
    docker compose up
    ```

    Wait until terminal outputs

    `app-airflow-webserver-1  | 127.0.0.1 - - [17/Feb/2023:09:34:29 +0000] "GET /health HTTP/1.1" 200 141 "-" "curl/7.74.0"`

    g. Enable port forwarding

    h. Visit `localhost:8080` login with credentials set on step `2.d`

    i. Add Your Project Files
        
        - Place your EPL dataset (e.g., E0.csv) inside the dags/data/ directory.

        - Place your ML logic file (lab.py) inside the dags/src/ directory.

        - Place your DAG definition file (airflow.py) inside the dags/ directory.
        

3. Stop docker containers

    ```bash
    docker compose down
    ```

### Running the Pipeline

1. Initialize the Database (Run Once):

    From your airflow_lab1 terminal, run:

    ```
    docker compose up airflow-init
    ```

2. Start Airflow
    ```Bash
    docker compose up
    ```

3. Access Airflow UI
    
    `Open your web browser and go to http://localhost:8080. Log in with the default credentials (airflow / airflow).`

4. Trigger the DAG

    On the DAGs page, find the EPL_Goal_Prediction_Pipeline.

    Click the play button (▶️) to start a new run.

5. Check the Results

    Click on the DAG name to monitor its progress.

    Once the pipeline is complete, click on the final evaluate_models_task and view its Logs to see the model's final prediction accuracy and confusion matrix.

6. Stop Docker Containers
    When you are finished, stop the containers from your terminal:

     ```Bash
    docker compose down
    ```