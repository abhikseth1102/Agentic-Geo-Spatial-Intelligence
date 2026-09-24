import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import './index.css';

// Fix leaflet icon issue in react
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const RadarIcon = L.divIcon({
  className: 'radar-marker',
  html: `
    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10; display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; background: var(--bg-dark); border-radius: 50%; border: 2px solid var(--accent-blue); box-shadow: 0 0 15px var(--accent-blue);">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M2 21c4 0 7-2 9-2s5 2 9 2" />
        <path d="M3 17h18l-1.5-6h-15L3 17z" />
        <path d="M10 11V5h4v6" />
      </svg>
    </div>
    <div class="radar-pulse"></div>
  `,
  iconSize: [40, 40],
  iconAnchor: [20, 20]
});

function App() {
  const [loading, setLoading] = useState(false);
  const [evaluation, setEvaluation] = useState(null);

  // Mocked state of a vessel approaching a high-risk zone in Kattegat Strait
  const [telemetry, setTelemetry] = useState({
    mmsi: "MMSI_219019621",
    lat: 57.2,
    lon: 11.5,
    distance_nm: 10.0,
    speed: 3.5,
    congestion: 98,
    wind: 38.5,
    waves: 4.8,
    destination: "Gothenburg, SE"
  });

  // Calculate dynamic storm position based on slider distance (1 degree lat = ~60 nm)
  const storm_lat = telemetry.lat - (telemetry.distance_nm / 60.0);
  const storm_lon = telemetry.lon;

  // Simple parser to render markdown bullets and bold text from the backend
  const renderMarkdown = (text) => {
    return text.split('\n').map((line, i) => {
      if (line.trim().startsWith('- ')) {
        return <li key={i} dangerouslySetInnerHTML={{ __html: line.substring(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />;
      }
      return <p key={i} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />;
    });
  };

  const handleEvaluate = async () => {
    setLoading(true);
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
      const response = await axios.post(`${API_URL}/api/evaluate_route`, telemetry);
      setEvaluation(response.data);
    } catch (error) {
      console.error("Error evaluating route:", error);
      setEvaluation({
        status: "Error",
        alert: "Could not connect to Agent Engine Backend.",
        delay_risk_percent: 0,
        fuel_estimate_tons: 0
      });
    }
    setLoading(false);
  };

  // Physics simulation for dynamic slider linking
  const handleDistanceChange = (e) => {
    const dist = parseFloat(e.target.value);
    
    // Congestion increases as ships bunch up to avoid storm/seek harbor
    const newCongestion = Math.min(100, Math.max(0, Math.round(100 - (dist / 3.0))));
    
    // Wind increases exponentially as you approach the eye of the hurricane
    const newWind = Math.round(15 + 105 * Math.pow(Math.E, -dist / 50.0));
    
    setTelemetry({
      ...telemetry,
      distance_nm: dist,
      congestion: newCongestion,
      wind: newWind
    });
  };

  // Helper for drawing arrows on routes
  const RouteSegment = ({ p1, p2, color }) => {
    const midLat = (p1[0] + p2[0]) / 2;
    const midLon = (p1[1] + p2[1]) / 2;
    // Calculate angle for screen rotation (lat increases going UP, lon increases going RIGHT)
    const angle = Math.atan2(p1[0] - p2[0], p2[1] - p1[1]) * (180 / Math.PI);
    
    const arrowIcon = L.divIcon({
      className: 'route-arrow',
      html: `<div style="transform: rotate(${angle}deg); color: ${color}; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    return (
      <>
        <Polyline positions={[p1, p2]} color={color} dashArray={color.includes('rgba') ? "5, 10" : ""} weight={color.includes('rgba') ? 3 : 4} className={color.includes('rgba') ? "" : "route-glow"} />
        <Marker position={[midLat, midLon]} icon={arrowIcon} interactive={false} />
      </>
    );
  };

  const plannedP1 = [56.8, 11.2];
  const plannedP2 = [telemetry.lat, telemetry.lon];
  const plannedP3 = [57.7, 11.9];

  const rerouteP1 = [telemetry.lat, telemetry.lon];
  const rerouteP2 = [57.4, 10.5];
  const rerouteP3 = [57.8, 11.8];

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>Agentic Geo-Spatial Intelligence</h1>
        <div className="header-status">
          <div className="status-dot"></div>
          Live Orchestration Engine
        </div>
      </header>

      <main className="main-content">
        <div className="map-container">
          <MapContainer center={[57.2, 11.5]} zoom={7} scrollWheelZoom={true}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            {/* Dynamic Hurricane Weather Overlay */}
            <Circle 
              center={[storm_lat, storm_lon]} 
              radius={75 * 1852} /* 75 nm danger radius */
              pathOptions={{ color: 'var(--accent-red)', fillColor: 'var(--accent-red)', fillOpacity: 0.2 }}
            >
              <Popup>Simulated Hurricane Center</Popup>
            </Circle>

            {/* Current Vessel Position with Radar Pulse */}
            <Marker position={[telemetry.lat, telemetry.lon]} icon={RadarIcon}>
              <Popup>
                <strong>{telemetry.mmsi}</strong><br/>
                Speed: {telemetry.speed} kts<br/>
                Heading to: {telemetry.destination}
              </Popup>
            </Marker>
            
            {/* Original Planned Route (Red) with Arrows */}
            <RouteSegment p1={plannedP1} p2={plannedP2} color="rgba(239, 68, 68, 0.7)" />
            <RouteSegment p1={plannedP2} p2={plannedP3} color="rgba(239, 68, 68, 0.7)" />

            {/* Reroute (Green) with Arrows - Show only if evaluated and rerouted */}
            {evaluation && evaluation.status === "Rerouted" && (
              <>
                <RouteSegment p1={rerouteP1} p2={rerouteP2} color="#10b981" />
                <RouteSegment p1={rerouteP2} p2={rerouteP3} color="#10b981" />
              </>
            )}
          </MapContainer>
          
          {loading && (
            <div className="map-overlay">
              <span className="loader"></span>
              Orchestrating Autonomous Reroute...
            </div>
          )}
        </div>

        <aside className="panel">
          <div>
            <h2 className="panel-title">Simulation Controls</h2>
            <div className="slider-group">
              <label>Distance to Storm: {telemetry.distance_nm} nm</label>
              <input type="range" min="0" max="300" step="1" value={telemetry.distance_nm} onChange={handleDistanceChange} />
            </div>
            <div className="slider-group">
              <label>Congestion Index: {telemetry.congestion}</label>
              <input type="range" min="0" max="100" step="1" value={telemetry.congestion} onChange={(e) => setTelemetry({...telemetry, congestion: parseInt(e.target.value)})} />
            </div>
            <div className="slider-group">
              <label>Wind Speed: {telemetry.wind} kts</label>
              <input type="range" min="0" max="150" step="0.5" value={telemetry.wind} onChange={(e) => setTelemetry({...telemetry, wind: parseFloat(e.target.value)})} />
            </div>
          </div>
          
          <hr style={{borderColor: 'var(--glass-border)', margin: '1rem 0'}} />

          <div>
            <h2 className="panel-title">Vessel Telemetry</h2>
            <p style={{color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1rem'}}>
              ID: {telemetry.mmsi}
            </p>
            <div className="telemetry-grid">
              <div className="metric-card">
                <div className="metric-label">SOG (Knots)</div>
                <div className="metric-value">{telemetry.speed}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Congestion</div>
                <div className="metric-value">{telemetry.congestion} <span style={{fontSize:'0.875rem', color:'var(--accent-red)'}}>High</span></div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Wind (Kts)</div>
                <div className="metric-value">{telemetry.wind}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Waves (m)</div>
                <div className="metric-value">{telemetry.waves}</div>
              </div>
            </div>
          </div>

          <hr style={{borderColor: 'var(--glass-border)', margin: '1rem 0'}} />

          <div>
            <h2 className="panel-title">Agent Analysis</h2>
            {evaluation ? (
              <>
                <div className="telemetry-grid" style={{marginBottom: '1rem'}}>
                  <div className="metric-card">
                    <div className="metric-label">Delay Risk</div>
                    <div className="metric-value" style={{color: evaluation.delay_risk_percent > 70 ? 'var(--accent-red)' : 'var(--accent-green)'}}>
                      {evaluation.delay_risk_percent}%
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">Est. Fuel Burn</div>
                    <div className="metric-value">{evaluation.fuel_estimate_tons} T</div>
                  </div>
                  {evaluation.status === 'Rerouted' && (
                    <div className="metric-card" style={{gridColumn: 'span 2'}}>
                      <div className="metric-label">Fuel Saved (Avoiding Storm Resistance)</div>
                      <div className="metric-value" style={{color: '#10b981'}}>
                        + {Math.round(evaluation.fuel_estimate_tons * 0.42)} Tons
                      </div>
                    </div>
                  )}
                </div>

                <div className={`alert-box ${evaluation.status === 'Safe' ? 'safe' : ''}`}>
                  <div className="alert-title">
                    {evaluation.status === 'Rerouted' ? '⚠️ Autonomous Reroute Executed' : '✅ Route Safe'}
                  </div>
                  <div className="alert-content">
                    {evaluation.status === "Rerouted" && evaluation.alert.includes('- ') ? (
                      <ul>{renderMarkdown(evaluation.alert)}</ul>
                    ) : (
                      renderMarkdown(evaluation.alert)
                    )}
                  </div>
                </div>

                {evaluation.status === 'Rerouted' && (
                  <div style={{marginTop: '1rem', padding: '1rem', background: 'var(--glass-bg)', borderRadius: '8px', border: '1px solid var(--glass-border)'}}>
                    <h3 style={{fontSize: '0.875rem', marginBottom: '0.75rem', color: 'var(--text-secondary)'}}>Model Explainability (SHAP)</h3>
                    <div style={{marginBottom: '0.5rem'}}>
                      <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem'}}>
                        <span>Distance To Storm</span>
                        <span style={{color: 'var(--accent-red)'}}>94.0%</span>
                      </div>
                      <div style={{width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px'}}>
                        <div style={{width: '94%', height: '100%', background: 'var(--accent-red)', borderRadius: '3px'}}></div>
                      </div>
                    </div>
                    <div>
                      <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem'}}>
                        <span>Congestion Index</span>
                        <span style={{color: 'var(--accent-yellow)'}}>6.0%</span>
                      </div>
                      <div style={{width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px'}}>
                        <div style={{width: '6%', height: '100%', background: 'var(--accent-yellow)', borderRadius: '3px'}}></div>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p style={{color: 'var(--text-secondary)', fontSize: '0.875rem'}}>
                Awaiting orchestration engine execution.
              </p>
            )}
          </div>

          <button 
            className="btn-primary" 
            onClick={handleEvaluate}
            disabled={loading}
          >
            {loading ? <span className="loader"></span> : "Trigger AI Orchestration"}
          </button>
        </aside>
      </main>
    </div>
  );
}

export default App;
