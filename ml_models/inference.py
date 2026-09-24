import joblib
import numpy as np
import os

class MLInferenceEngine:
    def __init__(self, delay_model_path='delay_model.pkl', fuel_model_path='fuel_model.pkl'):
        # Ensure we can load models if they exist, otherwise we mock them for development
        self.delay_model_path = delay_model_path
        self.fuel_model_path = fuel_model_path
        
        # Load or mock Delay Model
        if os.path.exists(delay_model_path):
            self.delay_model = joblib.load(delay_model_path)
        else:
            print("Warning: Delay model not found. Using mocked inference.")
            self.delay_model = None
            
        # Load or mock Fuel Model
        if os.path.exists(fuel_model_path):
            self.fuel_model = joblib.load(fuel_model_path)
        else:
            print("Warning: Fuel model not found. Using mocked inference.")
            self.fuel_model = None

    def predict_delay_risk(self, distance_nm, hex_congestion_count, wind_speed_knots, wave_height_m, lat, lon):
        """
        Returns probability of delay (0.0 to 1.0)
        """
        if self.delay_model:
            features = np.array([[distance_nm, hex_congestion_count, wind_speed_knots, wave_height_m, lat, lon]])
            # predict_proba returns probability for class 0 and class 1. We want class 1 (delayed).
            prob = self.delay_model.predict_proba(features)[0][1]
            return float(prob)
        else:
            # Mocked logic based on heuristics
            risk = 0.1
            if hex_congestion_count > 10: risk += 0.4
            if wind_speed_knots > 20: risk += 0.3
            return min(risk, 0.99)

    def predict_fuel_consumption(self, distance_nm, calculated_speed_knots, wave_height_m, wind_speed_knots, hex_congestion_count):
        """
        Returns estimated fuel consumption in metric tons
        """
        if self.fuel_model:
            features = np.array([[distance_nm, calculated_speed_knots, wave_height_m, wind_speed_knots, hex_congestion_count]])
            fuel = self.fuel_model.predict(features)[0]
            return float(fuel)
        else:
            # Mocked logic
            return float((distance_nm * 0.1) + (calculated_speed_knots**2 * 0.001) + (wave_height_m * 0.5))

if __name__ == "__main__":
    engine = MLInferenceEngine()
    print("Testing Delay Risk:", engine.predict_delay_risk(50, 15, 25, 2.5, 57.0, 11.0))
    print("Testing Fuel Burn:", engine.predict_fuel_consumption(50, 12, 2.5, 25, 15))
