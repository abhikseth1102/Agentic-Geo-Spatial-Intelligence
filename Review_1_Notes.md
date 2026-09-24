# Review 1: Project Presentation Notes

This document contains everything you need to confidently explain your project, the machine learning architecture, your dataset, and your future roadmap to your professor.

---

## 1. The Core Concept (The "Elevator Pitch")
**Project Name:** Agentic Geo-Spatial Intelligence Engine for Predictive Maritime Logistics.

**What it does:** 
"My project is an offline, machine-learning-driven maritime routing engine. It takes live vessel telemetry (speed, course, ship type) and evaluates it against severe weather zones (like hurricanes). Instead of relying on simple 'if-then' geofences, it uses an **XGBoost Machine Learning model** to predict the *probability of a logistical delay*. If the risk crosses a critical threshold, the engine autonomously plots a reroute corridor to bypass the danger zone."

---

## 2. What the Model Does (Current Architecture)
Explain that your project is a fully decoupled **Microservice Architecture**:
*   **The Backend (FastAPI & XGBoost):** The backend is an inference engine. We trained an `XGBClassifier` to predict delay risk based on four core features: `Course`, `Vessel Type`, `Distance to Storm`, and `Congestion Index`. The FastAPI backend loads the pre-trained weights (`.json`) into memory and executes sub-millisecond predictions on incoming telemetry payloads.
*   **The Frontend (React & Leaflet):** A dynamic dashboard that simulates the vessel's environment. It features "Physically Linked Sliders"—meaning when you drag the ship closer to the storm, the UI automatically calculates the resulting surge in wind speed and shipping lane congestion, mimicking real-world physics. 
*   **SHAP Explainability:** The UI doesn't just say "High Risk"; it provides Model Explainability (SHAP approximation), visually breaking down exactly *why* the XGBoost model made its decision (e.g., Distance contributed 93% to the decision, Congestion contributed 7%).

---

## 3. Dataset Details
Your teacher will definitely ask where the data came from. Give them these exact details:

*   **Source:** The United States Government via **NOAA's MarineCadastre.gov**.
*   **Date Range:** August 28, 2023 (The exact time window when **Hurricane Idalia** was forming in the Gulf of Mexico).
*   **Size & Scale:** We downloaded a massive **1GB raw CSV file** containing millions of AIS (Automatic Identification System) pings. 
*   **Data Engineering pipeline (`process_real_data.py`):** 
    *   We streamed the 1GB file and filtered it spatially to a bounding box around the Florida/Gulf region.
    *   We isolated **30,000 real vessels**.
    *   *Feature Engineering:* We used the **Haversine formula** to calculate the exact distance from every ship to the Hurricane's eye. We also engineered a `Congestion Index` feature to simulate ships bunching up as they seek harbor.
    *   *Fixing Data Leakage:* (Mention the bug you found!) Explain how you discovered that Congestion and Distance were mathematically correlated in your early tests, leading to multicollinearity where the model ignored distance. Explain how you fixed it by decoupling the features with random noise to force the XGBoost model to learn both variables independently. Teachers *love* hearing about how you solved feature leakage.

---

## 4. Future Expansion (How to make it significantly better)
Review 1 is all about proving the concept. When they ask "What's next?", give them this roadmap:

1.  **From XGBoost to Sequence Models (LSTMs / Transformers):**
    *   *Current State:* XGBoost looks at a single, static point in time to make a guess.
    *   *Future State:* We will upgrade the ML architecture to use a Long Short-Term Memory (LSTM) network or a Transformer. This will allow the model to look at the *historical trajectory* of the ship over the last 6 hours to predict where it will be 6 hours from now, rather than just evaluating its current snapshot.
2.  **Fleet-Wide Aggregation using H3 Hexbins:**
    *   *Current State:* The dashboard evaluates one ship at a time.
    *   *Future State:* We will integrate Uber's H3 Hexagonal clustering library. We will feed 50,000 ships into the model simultaneously, group them into hexagons, and create a real-time glowing "Heatmap" of global supply chain delay risks.
3.  **Complex Weather Polygons:**
    *   *Current State:* Weather is represented as a single point (the eye of the storm) and a radius.
    *   *Future State:* Integrate actual GRIB weather files (wind vectors, wave heights) so the ML model evaluates risk against dynamic, asymmetrical weather shapes rather than perfect circles.
