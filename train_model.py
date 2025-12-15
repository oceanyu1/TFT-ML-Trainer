import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib

# 1. LOAD DATA
# Use the file you just created. If you ran the 'nuke' script, use the clean version.
try:
    df = pd.read_csv("tft_match_data_clean.csv")
except FileNotFoundError:
    df = pd.read_csv("tft_match_data.csv")

print(f"Training model on {len(df)} player games...")

# 2. SELECT FEATURES
# These are the 5 numbers that define a "Playstyle"
features = [
    'level', 
    'gold_left', 
    'board_value', 
    'three_star_count', 
    'carry_unit_cost'
]

# 3. CLEANING & SCALING
# Fill missing values (just in case)
X = df[features].fillna(0)

# Normalize the data (so Gold=50 doesn't overpower Level=8)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. TRAIN THE MODEL (Clustering)
# We look for 5 distinct playstyles
kmeans = KMeans(n_clusters=5, random_state=42)
df['cluster_id'] = kmeans.fit_predict(X_scaled)

# 5. GENERATE READABLE REPORT
summary = df.groupby('cluster_id')[features].mean().reset_index()

print("\n--- CLUSTER ANALYSIS REPORT ---")
print(summary.to_string(formatters={
    'level': '{:,.2f}'.format,
    'gold_left': '{:,.1f}'.format,
    'board_value': '{:,.1f}'.format,
    'three_star_count': '{:,.2f}'.format,
    'carry_unit_cost': '{:,.2f}'.format
}))

# Check how many players fell into each bucket
print("\n--- PLAYER COUNT PER CLUSTER ---")
print(df['cluster_id'].value_counts().sort_index())

# 6. SAVE FOR BACKEND
joblib.dump(kmeans, "tft_kmeans_model.pkl")
joblib.dump(scaler, "tft_scaler.pkl")
print("\nModel saved successfully!")