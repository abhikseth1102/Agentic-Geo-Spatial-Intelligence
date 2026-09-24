import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

def train_fuel_model(data_path, output_model_path):
    print("Loading engineered data for Fuel Model...")
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return
        
    df = pd.read_csv(data_path)
    
    # Synthesize fuel consumption target (metric tons)
    # Fuel consumption roughly scales with distance, speed^2, and wave resistance
    df['fuel_consumption_tons'] = (
        (df['distance_nm'] * 0.1) + 
        (df['calculated_speed_knots'] ** 2 * 0.001) + 
        (df['wave_height_m'] * 0.5)
    )
    # Add noise
    df['fuel_consumption_tons'] += np.random.normal(0, 0.2, len(df))
    df['fuel_consumption_tons'] = df['fuel_consumption_tons'].clip(lower=0.1) # Minimum burn
    
    features = ['distance_nm', 'calculated_speed_knots', 'wave_height_m', 'wind_speed_knots', 'hex_congestion_count']
    
    X = df[features].fillna(0)
    y = df['fuel_consumption_tons']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Fuel Regressor...")
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Model MSE: {mse:.4f}")
    print(f"Model R2 Score: {r2:.4f}")
    
    # Save the model
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    joblib.dump(model, output_model_path)
    print(f"Fuel model saved to {output_model_path}")

if __name__ == "__main__":
    train_fuel_model('../data_pipeline/engineered_data.csv', 'fuel_model.pkl')
