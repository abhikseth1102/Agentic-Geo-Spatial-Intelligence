import pandas as pd
import numpy as np
import h3
from haversine import haversine, Unit
import os
from datetime import datetime, timedelta

def generate_synthetic_telemetry(df_static, num_samples=25000):
    """
    The provided dataset contains static vessel data but lacks lat, lon, and timestamp.
    We will synthesize realistic trajectory data through the Kattegat Strait to enable our ML/Agentic pipeline.
    """
    print("Generating synthetic trajectory data for Kattegat Strait...")
    # Sample unique ships
    unique_ships = df_static['mmsi'].unique()
    num_ships = min(1000, len(unique_ships))
    sampled_ships = np.random.choice(unique_ships, num_ships, replace=False)
    
    rows_per_ship = num_samples // num_ships
    
    telemetry_data = []
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    
    # Kattegat Strait rough bounding box: Lat 56.0 - 58.0, Lon 10.0 - 12.0
    for ship in sampled_ships:
        # Start random point in the strait
        current_lat = np.random.uniform(56.0, 58.0)
        current_lon = np.random.uniform(10.0, 12.0)
        
        # Determine a general direction (drift) for this ship
        lat_drift = np.random.uniform(-0.02, 0.02)
        lon_drift = np.random.uniform(-0.02, 0.02)
        
        current_time = base_time + timedelta(hours=np.random.randint(0, 72))
        
        for _ in range(rows_per_ship):
            telemetry_data.append({
                'mmsi': ship,
                'lat': current_lat,
                'lon': current_lon,
                'timestamp': current_time
            })
            # Add some noise to the movement to simulate actual ship navigation
            current_lat += lat_drift + np.random.uniform(-0.002, 0.002)
            current_lon += lon_drift + np.random.uniform(-0.002, 0.002)
            # Update time by roughly 10-30 minutes per ping
            current_time += timedelta(minutes=np.random.randint(10, 30))
            
    df_telemetry = pd.DataFrame(telemetry_data)
    # Merge with static data to get ShipType, etc.
    df_full = df_telemetry.merge(df_static, on='mmsi', how='left')
    return df_full

def calculate_haversine(df):
    print("Calculating Haversine distances and speeds...")
    df = df.sort_values(by=['mmsi', 'timestamp']).reset_index(drop=True)
    
    # Shift to get previous lat/lon for the same ship
    df['prev_lat'] = df.groupby('mmsi')['lat'].shift(1)
    df['prev_lon'] = df.groupby('mmsi')['lon'].shift(1)
    df['prev_timestamp'] = df.groupby('mmsi')['timestamp'].shift(1)
    
    def calc_dist(row):
        if pd.isna(row['prev_lat']):
            return 0.0
        return haversine((row['lat'], row['lon']), (row['prev_lat'], row['prev_lon']), unit=Unit.NAUTICAL_MILES)
        
    df['distance_nm'] = df.apply(calc_dist, axis=1)
    
    # Calculate time difference in hours
    df['time_diff_hours'] = (df['timestamp'] - df['prev_timestamp']).dt.total_seconds() / 3600.0
    
    # Calculate speed in knots (NM / hour)
    df['calculated_speed_knots'] = np.where(df['time_diff_hours'] > 0, df['distance_nm'] / df['time_diff_hours'], 0.0)
    
    # Drop temp columns
    df = df.drop(columns=['prev_lat', 'prev_lon', 'prev_timestamp'])
    return df

def apply_h3_clustering(df, resolution=6):
    print(f"Applying H3 Geohash clustering at resolution {resolution}...")
    def get_hex(row):
        # Handle different h3-py API versions
        if hasattr(h3, 'latlng_to_cell'):
            return h3.latlng_to_cell(row['lat'], row['lon'], resolution)
        else:
            return h3.geo_to_h3(row['lat'], row['lon'], resolution)
            
    df['h3_hex_id'] = df.apply(get_hex, axis=1)
    return df

def main():
    raw_data_path = '../eda_dataset/ais_data.csv'
    output_path = 'engineered_data.csv'
    
    if not os.path.exists(raw_data_path):
        print(f"Error: Could not find raw data at {raw_data_path}")
        return
        
    print("Loading raw static AIS dataset...")
    df_static = pd.read_csv(raw_data_path)
    
    df_full = generate_synthetic_telemetry(df_static)
    df_full = calculate_haversine(df_full)
    df_full = apply_h3_clustering(df_full)
    
    # To simulate weather covariance and congestion, we add synthetic features for ML
    print("Synthesizing weather and congestion features...")
    # Count ships in the same hex at roughly the same time (simplified as count per hex)
    hex_counts = df_full['h3_hex_id'].value_counts().to_dict()
    df_full['hex_congestion_count'] = df_full['h3_hex_id'].map(hex_counts)
    
    # Synthetic weather: Wave height (0-5m) and Wind Speed (0-40 knots) based on location and time
    # We use a random distribution but slightly correlated with congestion to make ML learn
    df_full['wind_speed_knots'] = np.random.uniform(5, 35, size=len(df_full))
    df_full['wave_height_m'] = df_full['wind_speed_knots'] * 0.1 + np.random.uniform(0, 1, size=len(df_full))
    
    # Save the engineered dataset
    df_full.to_csv(output_path, index=False)
    print(f"Pipeline complete! Engineered dataset saved to {output_path} with {len(df_full)} rows.")
    print("Preview:")
    print(df_full[['mmsi', 'timestamp', 'lat', 'lon', 'distance_nm', 'calculated_speed_knots', 'h3_hex_id', 'hex_congestion_count', 'wind_speed_knots']].head())

if __name__ == "__main__":
    main()
