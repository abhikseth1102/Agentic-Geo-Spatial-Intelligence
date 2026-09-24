import os
import csv
import math
from datetime import datetime, timedelta
import random

DATA_DIR = "data"
storm_path = {
    "2023-08-28": {"lat": 20.0, "lon": -85.0},
    "2023-08-29": {"lat": 24.5, "lon": -84.5},
    "2023-08-30": {"lat": 29.8, "lon": -83.6},
    "2023-08-31": {"lat": 33.5, "lon": -79.5}
}

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def generate_dataset(num_vessels=500):
    print("Generating simulated AIS dataset using pure python...")
    output_path = os.path.join(DATA_DIR, "AIS_Idalia_Simulated.csv")
    start_time = datetime(2023, 8, 28, 0, 0, 0)
    
    with open(output_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["MMSI", "BaseDateTime", "LAT", "LON", "SOG", "COG", "Heading", "VesselName", "VesselType", "DistanceToStorm_Miles", "DelayRisk"])
        
        for i in range(num_vessels):
            mmsi = f"MMSI_{100000 + i}"
            start_lat = random.uniform(20.0, 35.0)
            start_lon = random.uniform(-90.0, -75.0)
            base_speed = random.uniform(10.0, 20.0)
            course = random.uniform(0, 360)
            
            for hour in range(96):
                current_time = start_time + timedelta(hours=hour)
                date_str = current_time.strftime("%Y-%m-%d")
                lat = start_lat + (hour * (base_speed/60) * math.cos(math.radians(course)))
                lon = start_lon + (hour * (base_speed/60) * math.sin(math.radians(course)))
                storm_pos = storm_path.get(date_str, storm_path["2023-08-28"])
                dist_to_storm = haversine(lat, lon, storm_pos["lat"], storm_pos["lon"])
                
                actual_speed = base_speed
                delay_risk = 0
                if dist_to_storm < 150:
                    actual_speed = max(0, base_speed * (dist_to_storm / 150))
                    delay_risk = 1 if dist_to_storm < 75 else 0
                    
                writer.writerow([mmsi, current_time.strftime("%Y-%m-%dT%H:%M:%S"), round(lat, 4), round(lon, 4), round(actual_speed, 2), round(course, 1), round(course, 1), f"Vessel_{i}", random.choice([70, 80, 30]), round(dist_to_storm, 2), delay_risk])
                
    print(f"Dataset generated! (Saved to {output_path})")

if __name__ == "__main__":
    generate_dataset()
