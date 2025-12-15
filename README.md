# TFT ML Service
A Python microservice that uses K-Means Clustering to classify Teamfight Tactics (TFT) players into behavioral archetypes (e.g., "Bill Gates," "Hyper Roll"). This service powers the machine learning inference for the TFT Insight platform.

# Scripts Overview
1. collect_data.py (The ETL Pipeline)
This script builds the dataset required for training.

Fetches raw match history data from the Riot Games API.

Processes JSON responses into structured numerical features (Level, Gold Left, Board Value, etc.).

Saves the cleaned dataset to tft_match_data.csv.

2. train_model.py (The Training Pipeline)
This script creates the actual ML artifacts.

Loads the tft_match_data.csv dataset.

Normalizes the data using a StandardScaler to ensure fair weighting of features.

Trains a K-Means clustering model (k=5) using Scikit-Learn.

Exports the trained model (kmeans_model.pkl) and scaler (scaler.pkl) for use by the API.

# Quick Start
1. Setup Environment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

2. Run the Pipeline

# Step 1: Gather Data (Requires Riot API Key, you need to create a .env and set it to TFT_API_KEY)
python collect_data.py

# Step 2: Train Model
python train_model.py
3. Start the API
Bash

uvicorn app:app --reload

Tech Stack
Python 3.10+

FastAPI (Inference)

Scikit-Learn (Clustering)

Pandas (Data Manipulation)