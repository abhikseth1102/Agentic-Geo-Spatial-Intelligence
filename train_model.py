import csv
import os
import random
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "AIS_Real_Processed.csv")

def train_and_evaluate():
    print("--- Phase 2-4: Geospatial Preprocessing & Machine Learning ---")
    print(f"Loading dataset: {DATA_FILE}")
    
    # We use pure python `csv` because Pandas C-extensions were blocked by Windows AppLocker
    X = []
    y = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Features: Base Speed (SOG), Course (COG), VesselType, DistanceToStorm
            # Since SOG represents actual speed (which was altered by the storm),
            # we should use a 'historical' or 'base' speed for prediction if possible,
            # but for this simplified EDA, we'll use SOG and Distance to predict DelayRisk.
            
            # To make it realistic for a prediction model: 
            # Can we predict delay risk based purely on: 
            # - Current distance to storm
            # - Vessel Type
            # - Current Course
            
            try:
                distance = float(row["DistanceToStorm_Miles"])
                course = float(row["COG"])
                vtype = float(row["VesselType"])
                congestion = float(row["CongestionIndex"])
                
                features = [
                    course,
                    vtype,
                    distance,
                    congestion
                ]
                
                label = int(row["DelayRisk"])
                
                X.append(features)
                y.append(label)
            except ValueError:
                continue
                
    print(f"Successfully loaded {len(X)} records.")
    
    # Time-ordered split (for a real dataset). 
    # Since our mock dataset is uniformly generated, we use a standard split here.
    print("Splitting dataset into Train and Test sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        max_depth=4,
        learning_rate=0.1,
        n_estimators=100,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    print("Evaluating Model on Test Data...")
    y_pred = model.predict(X_test)
    
    print("\n--- Model Performance Report ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Delay", "High Delay Risk"]))
    
    # Feature Importances
    importances = model.feature_importances_
    features_names = ["Course", "Vessel Type", "Distance To Storm", "Congestion Index"]
    print("\nFeature Importances (SHAP approximation):")
    for name, imp in zip(features_names, importances):
        print(f" - {name}: {imp*100:.1f}%")
        
    # Save the model for the FastAPI backend
    model_path = os.path.join(DATA_DIR, "xgb_delay_model.json")
    model.save_model(model_path)
    print(f"\nModel successfully saved to {model_path}")

if __name__ == "__main__":
    train_and_evaluate()
