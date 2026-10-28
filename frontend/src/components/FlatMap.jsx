import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  Polyline,
  Polygon,
  GeoJSON,
  useMap,
} from "react-leaflet";
import { Layers, Wind, Map } from "lucide-react";
import coastline from "../assets/coastline.json";
import { fmt } from "../lib/api";
function FitTrack({ track }) {
  const map = useMap();
  useEffect(() => {
    if (track?.length)
      map.fitBounds(
        track.map((p) => [p.lat, p.lon]),
        { padding: [50, 50], maxZoom: 12 },
      );
  }, [track, map]);
  return null;
}
export default function FleetMap({ data, detail, onSelect }) {
  const [density, setDensity] = useState(true),
    [storm, setStorm] = useState(false),
    [tiles, setTiles] = useState(true);
  return (
    <div className="map-shell">
      <MapContainer center={[27.6, -83.4]} zoom={5} scrollWheelZoom={false}>
        {!tiles && <GeoJSON
          data={coastline}
          style={{
            color: "#b9c7d3",
            weight: 1,
            fillColor: "#f8fafc",
            fillOpacity: 1,
          }}
          attribution="Natural Earth · public domain · simplified coastline"
        />}
        {tiles && (
          <TileLayer
            attribution="© OpenStreetMap contributors"
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            eventHandlers={{ tileerror: () => setTiles(false) }}
          />
        )}
        {density &&
          data.cells.map((c) => (
            <Polygon
              key={c.h3}
              positions={c.boundary}
              pathOptions={{
                color: "#487fbd",
                weight: 1,
                fillOpacity: Math.min(0.4, 0.04 + c.vessels * 0.025),
              }}
            >
              <Popup>
                {c.vessels} distinct vessels · {fmt(c.observations)}{" "}
                observations
                <br />
                H3 resolution 5 · cumulative selected window
              </Popup>
            </Polygon>
          ))}
        {data.fleet.map((v) => (
          <CircleMarker
            key={v.mmsi}
            center={[v.lat, v.lon]}
            radius={v.mmsi === detail?.vessel.mmsi ? 8 : 4}
            pathOptions={{
              color: "#fff",
              weight: 1.3,
              fillColor: v.anomaly ? "#e8a444" : "#326bc0",
              fillOpacity: 0.95,
            }}
            eventHandlers={{ click: () => onSelect(v.mmsi) }}
          >
            <Popup>
              <strong>{v.name}</strong>
              <br />
              {v.speed} kn · {v.vessel_type}
              <br />
              Last report {v.timestamp.slice(11)} UTC
            </Popup>
          </CircleMarker>
        ))}
        {detail && (
          <>
            <Polyline
              positions={detail.track.map((p) => [p.lat, p.lon])}
              pathOptions={{ color: "#5486d7", weight: 3 }}
            />
            <FitTrack track={detail.track} />
          </>
        )}
        {storm && (
          <Polyline
            positions={data.storm.map((p) => [p.lat, p.lon])}
            pathOptions={{ color: "#d98a54", weight: 2, dashArray: "6 6" }}
          >
            <Popup>Idalia retrospective best track · full storm lifetime</Popup>
          </Polyline>
        )}
      </MapContainer>
      <div className="map-label">
        <span className="dot" /> GULF OF MEXICO <span>/</span> HISTORICAL AIS
      </div>
      <div className="map-tools">
        <button
          aria-pressed={density}
          className={density ? "selected" : ""}
          onClick={() => setDensity(!density)}
        >
          <Layers size={14} />
          Density
        </button>
        <button
          aria-pressed={storm}
          className={storm ? "selected" : ""}
          onClick={() => setStorm(!storm)}
        >
          <Wind size={14} />
          Idalia track
        </button>
        <button onClick={() => setTiles(!tiles)}>
          <Map size={14} />
          {tiles ? "Offline coastline" : "Street basemap"}
        </button>
      </div>
      <div className="map-legend">
        <span>
          <i style={{ background: "#326bc0" }} />
          Vessel
        </span>
        <span>
          <i style={{ background: "#e8a444" }} />
          Statistical outlier
        </span>
        <span className="map-note">
          Latest available position · not simultaneous
        </span>
      </div>
    </div>
  );
}
