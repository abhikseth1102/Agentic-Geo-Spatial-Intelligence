import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, Polygon } from 'react-leaflet';
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

// Helper for H3-style Hexbins
const generateHexagons = () => {
  const hexes = [];
  const centerLat = 57.2;
  const centerLon = 11.5;
  for(let i=0; i<40; i++) {
      const hLat = centerLat + (Math.random() - 0.5) * 2.0;
      const hLon = centerLon + (Math.random() - 0.5) * 3.5;
      const points = [];
      const r = 0.05; // size of hex
      for(let j=0; j<6; j++) {
          const theta = (j * Math.PI) / 3;
          points.push([hLat + r * Math.sin(theta), hLon + r * Math.cos(theta) * 1.8]);
      }
      // Simulate congestion zones
      const isDense = Math.random() > 0.7;
      const color = isDense ? 'rgba(239, 68, 68, 0.4)' : 'rgba(16, 185, 129, 0.15)'; // Red or Green
      hexes.push({ points, color });
  }
  return hexes;
};

function App() {
  const [loading, setLoading] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  const [hexagons] = useState(generateHexagons());
  
  // Animation state
  const [isPlaying, setIsPlaying] = useState(false);
  const simRef = useRef(null);

  const [telemetry, setTelemetry] = useState({
    mmsi: "MMSI_219019621",
    lat: 57.2,
    lon: 11.5,
    distance_nm: 250.0,
    speed: 14.5,
    congestion: 20,
    wind: 15.0,
    waves: 1.2,
    destination: "Gothenburg, SE"
  });

  const storm_lat = telemetry.lat - (telemetry.distance_nm / 60.0);
  const storm_lon = telemetry.lon;

  const renderMarkdown = (text) => {
    return text.split('\n').map((line, i) => {
      if (line.trim().startsWith('- ')) {
        return <li key={i} dangerouslySetInnerHTML={{ __html: line.substring(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />;
      }
      return <p key={i} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />;
    });
  };

  const handleEvaluate = async (currentTelemetry = telemetry) => {
    setLoading(true);
    try {
      const rawUrl = import.meta.env.VITE_API_URL || 'http://localhost:8080';
      const API_URL = rawUrl.replace(/\/$/, "");
      const response = await axios.post(`${API_URL}/api/evaluate_route`, currentTelemetry);
      setEvaluation(response.data);
      if (response.data.status === 'Rerouted') {
        setIsPlaying(false); // Stop simulation if rerouted
      }
    } catch (error) {
      console.error("Error evaluating route:", error);
      setEvaluation({
        status: "Error",
        alert: "Could not connect to Agent Engine Backend.",
        delay_risk_percent: 0,
        fuel_estimate_tons: 0
      });
      setIsPlaying(false);
    }
    setLoading(false);
  };

  const updatePhysics = (dist) => {
    const newCongestion = Math.min(100, Math.max(0, Math.round(100 - (dist / 3.0))));
    const newWind = Math.round(15 + 105 * Math.pow(Math.E, -dist / 50.0));
    const newWaves = Math.round(1.0 + 8.0 * Math.pow(Math.E, -dist / 60.0));
    
    return {
      ...telemetry,
      distance_nm: dist,
      congestion: newCongestion,
      wind: newWind,
      waves: newWaves
    };
  };

  const handleDistanceChange = (e) => {
    setTelemetry(updatePhysics(parseFloat(e.target.value)));
    setEvaluation(null); // reset evaluation when manually moved
  };

  // Playback Simulation Logic
  useEffect(() => {
    if (isPlaying) {
      simRef.current = setInterval(() => {
        setTelemetry((prev) => {
          const nextDist = prev.distance_nm - 5;
          if (nextDist <= 140 && !evaluation) {
            // Auto-trigger evaluation when entering danger zone
            const updated = updatePhysics(nextDist);
            handleEvaluate(updated);
            return updated;
          }
          if (nextDist <= 10) {
            setIsPlaying(false);
            return prev;
          }
          return updatePhysics(nextDist);
        });
      }, 300);
    } else {
      clearInterval(simRef.current);
    }
    return () => clearInterval(simRef.current);
  }, [isPlaying, evaluation]);

  const RouteSegment = ({ p1, p2, color }) => {
    const midLat = (p1[0] + p2[0]) / 2;
    const midLon = (p1[1] + p2[1]) / 2;
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
      <header className="header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div>
          <h1>Agentic Geo-Spatial Intelligence</h1>
          <div className="header-status">
            <div className={`status-dot ${isPlaying ? 'pulse' : ''}`}></div>
            {isPlaying ? 'Live Simulation Active' : 'Live Orchestration Engine'}
          </div>
        </div>
        <button 
          className="btn-primary" 
          style={{background: isPlaying ? 'var(--accent-red)' : 'var(--accent-blue)'}}
          onClick={() => { setIsPlaying(!isPlaying); setEvaluation(null); }}
        >
          {isPlaying ? '⏹ Stop Playback' : '▶ Play Simulation'}
        </button>
      </header>

      <main className="main-content">
        <div className="map-container">
          <MapContainer center={[57.2, 11.5]} zoom={7} scrollWheelZoom={true}>
            <TileLayer
              attribution='&copy; OpenStreetMap contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            {/* Global Fleet H3 Hexbin Layer */}
            {hexagons.map((hex, i) => (
              <Polygon key={`hex-${i}`} positions={hex.points} pathOptions={{ color: hex.color, fillColor: hex.color, fillOpacity: 0.4, weight: 1 }} />
            ))}
            
            {/* Multi-Variate Weather Overlays */}
            {/* Outer Gale Winds */}
            <Circle center={[storm_lat, storm_lon]} radius={150 * 1852} pathOptions={{ color: 'var(--accent-yellow)', fillColor: 'var(--accent-yellow)', fillOpacity: 0.1, dashArray: "10, 10" }} />
            {/* High Waves Zone */}
            <Circle center={[storm_lat, storm_lon]} radius={100 * 1852} pathOptions={{ color: '#f97316', fillColor: '#f97316', fillOpacity: 0.2 }} />
            {/* Hurricane Eye */}
            <Circle center={[storm_lat, storm_lon]} radius={75 * 1852} pathOptions={{ color: 'var(--accent-red)', fillColor: 'var(--accent-red)', fillOpacity: 0.4 }}>
              <Popup>Simulated Hurricane Center (Cat 4)</Popup>
            </Circle>

            {/* Current Vessel */}
            <Marker position={[telemetry.lat, telemetry.lon]} icon={RadarIcon}>
              <Popup>
                <strong>{telemetry.mmsi}</strong><br/>
                Speed: {telemetry.speed} kts<br/>
                Heading to: {telemetry.destination}
              </Popup>
            </Marker>
            
            {/* Routes */}
            <RouteSegment p1={plannedP1} p2={plannedP2} color="rgba(239, 68, 68, 0.7)" />
            <RouteSegment p1={plannedP2} p2={plannedP3} color="rgba(239, 68, 68, 0.7)" />

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

        <aside className="panel" style={{overflowY: 'auto'}}>
          <div>
            <h2 className="panel-title">Simulation Controls</h2>
            <div className="slider-group">
              <label>Distance to Storm: {telemetry.distance_nm} nm</label>
              <input type="range" min="0" max="300" step="1" value={telemetry.distance_nm} onChange={handleDistanceChange} disabled={isPlaying} />
            </div>
            <div className="slider-group">
              <label>Congestion Index: {telemetry.congestion}</label>
              <input type="range" min="0" max="100" step="1" value={telemetry.congestion} readOnly />
            </div>
          </div>
          
          <hr style={{borderColor: 'var(--glass-border)', margin: '1rem 0'}} />

          <div>
            <h2 className="panel-title">Vessel Telemetry</h2>
            <div className="telemetry-grid">
              <div className="metric-card">
                <div className="metric-label">SOG (Knots)</div>
                <div className="metric-value">{telemetry.speed}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Congestion</div>
                <div className="metric-value">{telemetry.congestion}</div>
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
                    <div className="metric-label">Est. Fuel</div>
                    <div className="metric-value">{evaluation.fuel_estimate_tons} T</div>
                  </div>
                  {evaluation.status === 'Rerouted' && (
                    <div className="metric-card" style={{gridColumn: 'span 2'}}>
                      <div className="metric-label">Fuel Saved (Avoiding Storm)</div>
                      <div className="metric-value" style={{color: '#10b981'}}>
                        + {Math.round(evaluation.fuel_estimate_tons * 0.42)} Tons
                      </div>
                    </div>
                  )}
                </div>

                <div className={`alert-box ${evaluation.status === 'Safe' ? 'safe' : ''}`}>
                  <div className="alert-title">
                    {evaluation.status === 'Rerouted' ? '⚠️ AI Reroute Executed' : '✅ Route Safe'}
                  </div>
                  <div className="alert-content">
                    {evaluation.status === "Rerouted" && evaluation.alert.includes('- ') ? (
                      <ul>{renderMarkdown(evaluation.alert)}</ul>
                    ) : (
                      renderMarkdown(evaluation.alert)
                    )}
                  </div>
                </div>
              </>
            ) : (
              <p style={{color: 'var(--text-secondary)', fontSize: '0.875rem'}}>
                {isPlaying ? 'AI is monitoring trajectory...' : 'Awaiting orchestration engine execution.'}
              </p>
            )}
          </div>
          
          <div style={{marginTop: '1rem'}}>
            <button className="btn-primary" onClick={() => handleEvaluate(telemetry)} disabled={loading || isPlaying}>
              {loading ? <span className="loader"></span> : "Manual AI Evaluation"}
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;
