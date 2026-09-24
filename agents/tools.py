from langchain_core.tools import tool
import sys
import os

# Add ml_models to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml_models')))
try:
    from inference import MLInferenceEngine
    inference_engine = MLInferenceEngine(
        delay_model_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'delay_model.pkl')),
        fuel_model_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'fuel_model.pkl'))
    )
except ImportError:
    print("Could not import MLInferenceEngine, using mock implementation for tools.")
    inference_engine = None

@tool
def evaluate_delay_risk(distance_nm: float, hex_congestion_count: int, wind_speed_knots: float, wave_height_m: float, lat: float, lon: float) -> float:
    """
    Evaluates the mathematical probability (0.0 to 1.0) of a shipping delay 
    given the current navigation parameters and environmental metrics.
    """
    if inference_engine:
        return inference_engine.predict_delay_risk(distance_nm, hex_congestion_count, wind_speed_knots, wave_height_m, lat, lon)
    return 0.85 # Mock high risk

@tool
def calculate_fuel_consumption(distance_nm: float, calculated_speed_knots: float, wave_height_m: float, wind_speed_knots: float, hex_congestion_count: int) -> float:
    """
    Calculates the expected fuel consumption in metric tons.
    """
    if inference_engine:
        return inference_engine.predict_fuel_consumption(distance_nm, calculated_speed_knots, wave_height_m, wind_speed_knots, hex_congestion_count)
    return 12.4 # Mock value

@tool
def find_alternative_routes(current_lat: float, current_lon: float, destination: str) -> str:
    """
    Simulates an external API call to OpenStreetMap OSRM or maritime routing graph 
    to find alternative paths to avoid congestion.
    """
    # In a production environment, this would hit a routing API.
    # Here we simulate the logic for Kattegat Strait alternatives.
    return f"""
    Found 3 alternative routes to {destination}:
    Route A: Great Belt (Storebælt) - +14 NM, -45% Congestion Risk
    Route B: Little Belt (Lillebælt) - +28 NM, -80% Congestion Risk (Draft Restrictions Apply)
    Route C: Drop Anchor & Wait - +0 NM, +24 Hours Delay
    """
