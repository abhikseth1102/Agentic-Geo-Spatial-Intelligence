import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def train_delay_model(data_path, output_model_path):
    print("Loading engineered data...")
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return
        
    df = pd.read_csv(data_path)
    
    # Feature Selection
    # Target: We synthesize a binary target 'delayed' (1 if speed was impacted heavily by congestion/weather, else 0)
    # This simulates a ground-truth delay risk for the ML model to learn from our EDA features.
    
    # Let's say a ship is delayed if its speed is less than 50% of the average speed of its ShipType,
    # OR if it's in a highly congested hex with high wind.
    
    # Create target (0 or 1)
    df['is_delayed'] = ((df['calculated_speed_knots'] < 5.0) & (df['hex_congestion_count'] > 10)).astype(int)
    # Add some randomness to simulate real-world noise
    noise = np.random.uniform(0, 1, len(df))
    df.loc[(noise > 0.95), 'is_delayed'] = 1 - df.loc[(noise > 0.95), 'is_delayed']
    
    features = ['distance_nm', 'hex_congestion_count', 'wind_speed_knots', 'wave_height_m', 'lat', 'lon']
    
    X = df[features].fillna(0)
    y = df['is_delayed']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training XGBoost Delay Classifier...")
    model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Model Accuracy: {accuracy:.4f}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the model
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    joblib.dump(model, output_model_path)
    print(f"Delay model saved to {output_model_path}")

if __name__ == "__main__":
    import numpy as np # import here for the noise generation above
    train_delay_model('../data_pipeline/engineered_data.csv', 'delay_model.pkl')
