import './observatory.css';
import { chartGrid, axis } from "./components/ChartConfig";
import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ScatterChart,
  Scatter,
  LineChart,
  Line,
} from "recharts";
import {
  Anchor,
  ArrowUpRight,
  ArrowRight,
  Activity,
  BarChart3,
  Box,
  ChevronLeft,
  ChevronRight,
  Compass,
  Database,
  Download,
  FlaskConical,
  Pause,
  Play,
  Search,
  ShieldCheck,
  Ship,
  SlidersHorizontal,
  X,
  BookOpen,
  RefreshCw,
} from "lucide-react";
import { API, api, fmt } from "./lib/api";
import { Panel, Chart, Notice, Stat } from "./components/Shared";
import FleetMap from "./components/FleetMap";
import ScenarioLab from "./components/ScenarioLab";
import Benchmark from "./components/Benchmark";
import Methodology from "./components/Methodology";
import "leaflet/dist/leaflet.css";
import "./index.css";
const colors = [
  "#18a88b",
  "#5689db",
  "#ae7ae0",
  "#e6ac50",
  "#f07f6d",
  "#7398aa",
  "#838e9e",
  "#9db85e",
];
const tabs = [
  ["Fleet overview", Compass],
  ["Explore the data", BarChart3],
  ["Scenario lab", SlidersHorizontal],
  ["Model benchmark", FlaskConical],
  ["Data & methodology", Database],
];
function App() {
  const [tab, setTab] = useState(0),
    [data, setData] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(true);
  const [type, setType] = useState("All"),
    [hour, setHour] = useState(23),
    [playing, setPlaying] = useState(false),
    [refresh, setRefresh] = useState(0);
  const [query, setQuery] = useState(""),
    [page, setPage] = useState(1),
    [fleet, setFleet] = useState(null),
    [detail, setDetail] = useState(null),
    [selected, setSelected] = useState(null),
    [flagged, setFlagged] = useState(false);
  const [guide, setGuide] = useState(false),
    [benchmark, setBenchmark] = useState(null);
  useEffect(() => {
    let active = true;
    setBusy(true);
    setError("");
    api(`/overview?vessel_type=${encodeURIComponent(type)}&hour=${hour}`)
      .then((d) => {
        if (active) setData(d);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [type, hour, refresh]);
  useEffect(() => {
    let active = true;
    const timer = setTimeout(
      () =>
        api(
          `/vessels?q=${encodeURIComponent(query)}&vessel_type=${encodeURIComponent(type)}&hour=${hour}&page=${page}&flagged=${flagged}`,
        )
          .then((d) => {
            if (active) setFleet(d);
          })
          .catch((e) => {
            if (active) setError(e.message);
          }),
      180,
    );
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [query, type, hour, page, flagged, refresh]);
  useEffect(() => {
    let active = true;
    if (!selected) {
      setDetail(null);
      return;
    }
    api(`/vessels/${selected}?hour=${hour}`)
      .then((d) => {
        if (active) setDetail(d);
      })
      .catch(() => {
        if (active) setDetail(null);
      });
    return () => {
      active = false;
    };
  }, [selected, hour]);
  useEffect(() => {
    if (!playing) return;
    const t = setInterval(
      () =>
        setHour((h) => {
          if (h >= 23) {
            setPlaying(false);
            return 23;
          }
          return h + 1;
        }),
      1600,
    );
    return () => clearInterval(t);
  }, [playing]);
  useEffect(() => {
    api("/benchmark")
      .then(setBenchmark)
      .catch((e) => setError(e.message));
  }, [refresh]);
  function changeType(v) {
    setType(v);
    setPage(1);
    setSelected(null);
  }
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [tab]);
  useEffect(() => {
    if (!guide) return;
    const previous = document.activeElement;
    const handler = (e) => {
      if (e.key === "Escape") setGuide(false);
      if (e.key === "Tab") {
        const items = [...document.querySelectorAll(".guide-modal button")];
        if (e.shiftKey && document.activeElement === items[0]) {
          e.preventDefault();
          items.at(-1)?.focus();
        } else if (!e.shiftKey && document.activeElement === items.at(-1)) {
          e.preventDefault();
          items[0]?.focus();
        }
      }
    };
    document.addEventListener("keydown", handler);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
      previous?.focus();
    };
  }, [guide]);
  const m = data?.metrics;
  return (
    <div className="app">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setTab(0);
          }}
        >
          <span className="brand-symbol">
            <Anchor size={24} />
          </span>
          <div>
            AGI<span>MARITIME INTELLIGENCE</span>
          </div>
        </a>
        <div className="workspace">
          <span className="workspace-icon">
            <Box size={18} />
          </span>
          <div>
            Research workspace<small>Project / 2026</small>
          </div>
          <span className="workspace-tag">V2</span>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          {tabs.map(([name, Icon], i) => (
            <button
              key={name}
              className={tab === i ? "active" : ""}
              onClick={() => {
                setTab(i);
                setPlaying(false);
              }}
            >
              <Icon size={18} />
              {name}
              {i === 0 && (
                <span className="nav-count">{m?.vessels ?? "—"}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="research-card">
            <Compass size={21} />
            <h4>Field notes & methodology.</h4>
            <p>
              Data sources, experimental design, and the project review guide.
            </p>
            <button onClick={() => setGuide(true)}>
              Project walkthrough <ArrowUpRight size={15} />
            </button>
          </div>
          <div className="local-status">
            <span className="dot" />
            {error
              ? "Connection needs attention"
              : "Local research environment"}
            <small>Historical data · 28 Aug 2023</small>
          </div>
        </div>
      </aside>
      <div className="workspace-main">
        <header className="topbar">
          <div>
            Workspace <ChevronRight size={13} />
            <strong>{tabs[tab][0]}</strong>
          </div>
          <div className="top-actions">
            <span className="pill">
              <span className="dot" />
              HISTORICAL / 2023
            </span>
            <button
              className="icon-btn"
              aria-label="Open project walkthrough"
              onClick={() => setGuide(true)}
            >
              <BookOpen size={18} />
            </button>
            <span className="avatar">AG</span>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">AGENTIC GEO-SPATIAL INTELLIGENCE</div>
              <h1>
                {
                  [
                    "The fleet, in perspective.",
                    "Exploratory analysis.",
                    "Voyage scenarios.",
                    "Forecast evaluation.",
                    "Data provenance.",
                  ][tab]
                }
              </h1>
              <p>
                {
                  [
                    "Gulf of Mexico · 28 August 2023 · Historical vessel observatory",
                    "A closer look at vessel behavior across the selected historical window.",
                    "Transparent assumptions. Explainable decisions. A human in control.",
                    "Five approaches. One held-out cohort. Reproducible results.",
                    "Trace the journey from raw AIS messages to analytical insight.",
                  ][tab]
                }
              </p>
            </div>
            <a
              className="button secondary export"
              href={`${API}/api/export?vessel_type=${encodeURIComponent(type)}&hour=${hour}`}
            >
              <Download size={15} />
              Export data
            </a>
          </div>
          {error && (
            <div className="error" role="alert">
              {error}
              <button onClick={() => setRefresh((r) => r + 1)}>
                <RefreshCw size={14} />
                Retry
              </button>
            </div>
          )}
          {!data ? (
            <div className="empty">
              <RefreshCw className={busy ? "spin" : ""} />
              <h3>
                {busy
                  ? "Reading the research dataset…"
                  : "The dataset is not available."}
              </h3>
              <p>
                Start the backend and build the dataset using the README
                instructions.
              </p>
            </div>
          ) : (
            <>
              {(tab === 0 || tab === 1) && (
                <>
                  <div className="filter-row">
                    <div className="filter-controls">
                      <span className="filter-caption">
                        <SlidersHorizontal size={15} />
                        View
                      </span>
                      <select
                        aria-label="Vessel type"
                        value={type}
                        onChange={(e) => changeType(e.target.value)}
                      >
                        {[
                          "All",
                          "Cargo",
                          "Tanker",
                          "Passenger",
                          "Fishing",
                          "Tug",
                          "Sailing",
                          "Pleasure",
                          "Other",
                        ].map((t) => (
                          <option key={t} value={t}>
                            {t === "All" ? "All vessel types" : t}
                          </option>
                        ))}
                      </select>
                      <span className="date-filter">
                        28 Aug 2023 <span>·</span> 00:00–
                        {String(hour).padStart(2, "0")}:59 UTC
                      </span>
                    </div>
                    <span className="muted small">
                      {busy ? "Updating…" : "Historical snapshot"}
                      <span className={`dot ${busy ? "amber" : ""}`} />
                    </span>
                  </div>
                  <div className="stats">
                    <Stat
                      label="Vessels observed"
                      value={fmt(m.vessels)}
                      icon={Ship}
                      note="Distinct MMSI identifiers"
                    />
                    <Stat
                      label="AIS observations"
                      value={fmt(m.observations)}
                      icon={Activity}
                      note="Cleaned & sampled messages"
                    />
                    <Stat
                      label="Mean observed speed"
                      value={m.mean_speed}
                      unit="kn"
                      icon={Compass}
                      note="Across the selected observations"
                    />
                    <Stat
                      label="Outlier vessels"
                      value={fmt(m.flagged)}
                      icon={ShieldCheck}
                      note="Latest reports · review suggested"
                      tone="amber-text"
                    />
                  </div>
                </>
              )}
              {tab === 0 && (
                <>
                  <div className="overview-grid">
                    <Panel
                      title="Fleet activity"
                      subtitle="Gulf of Mexico & Florida coast"
                      action={<span className="badge">H3 RESOLUTION 5</span>}
                    >
                      <FleetMap
                        data={data}
                        detail={detail}
                        onSelect={setSelected}
                      />
                      <div className="timeline">
                        <button
                          className="icon-btn"
                          aria-label={
                            playing ? "Pause replay" : "Play historical replay"
                          }
                          onClick={() => {
                            if (hour === 23) setHour(0);
                            setPlaying(!playing);
                          }}
                        >
                          {playing ? <Pause size={17} /> : <Play size={17} />}
                        </button>
                        <span>HISTORICAL REPLAY</span>
                        <input
                          aria-label="Replay hour UTC"
                          type="range"
                          min="0"
                          max="23"
                          value={hour}
                          onChange={(e) => {
                            setHour(+e.target.value);
                            setPage(1);
                            setPlaying(false);
                          }}
                        />
                        <strong>{String(hour).padStart(2, "0")}:59</strong>
                        <span>UTC</span>
                      </div>
                    </Panel>
                    <div className="insight-column">
                      <Panel
                        title="Fleet composition"
                        subtitle="Distinct vessels by type"
                      >
                        <div className="composition-total">
                          {fmt(m.vessels)}
                          <span>vessels in this window</span>
                        </div>
                        <div className="stacked-bar">
                          {[...data.types]
                            .sort((a, b) => b.vessels - a.vessels)
                            .map((t, i) => (
                              <div
                                key={t.vessel_type}
                                style={{
                                  width: `${(t.vessels / Math.max(1, m.vessels)) * 100}%`,
                                  background: colors[i % colors.length],
                                }}
                                title={`${t.vessel_type}: ${t.vessels}`}
                              />
                            ))}
                        </div>
                        <div className="composition-list">
                          {[...data.types]
                            .sort((a, b) => b.vessels - a.vessels)
                            .map((t, i) => (
                              <div key={t.vessel_type}>
                                <span>
                                  <i style={{ background: colors[i] }} />
                                  {t.vessel_type}
                                </span>
                                <strong>
                                  {t.vessels}
                                  <small>
                                    {Math.round(
                                      (t.vessels / Math.max(1, m.vessels)) *
                                        100,
                                    )}
                                    %
                                  </small>
                                </strong>
                              </div>
                            ))}
                        </div>
                      </Panel>
                      <div className="insight-card">
                        <span className="eyebrow">
                          <Compass size={14} /> RESEARCH NOTE
                        </span>
                        <h3>Reading the density layer.</h3>
                        <p>
                          Density counts unique vessels in each hexagon.
                          Frequent transmitters do not automatically become the
                          busiest locations.
                        </p>
                        <button onClick={() => setTab(4)}>
                          Explore the methodology <ArrowRight size={15} />
                        </button>
                      </div>
                    </div>
                  </div>
                  <Panel
                    title="Vessel directory"
                    subtitle="Select a vessel to inspect its recorded trajectory and speed estimate."
                    action={
                      <div className="table-actions">
                        <label className="check-label">
                          <input
                            type="checkbox"
                            checked={flagged}
                            onChange={(e) => {
                              setFlagged(e.target.checked);
                              setPage(1);
                            }}
                          />
                          Outliers only
                        </label>
                        <div className="search">
                          <Search size={15} />
                          <input
                            aria-label="Search vessels"
                            placeholder="Search name or MMSI"
                            value={query}
                            onChange={(e) => {
                              setQuery(e.target.value);
                              setPage(1);
                            }}
                          />
                        </div>
                      </div>
                    }
                  >
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>VESSEL / MMSI</th>
                            <th>TYPE</th>
                            <th>SPEED</th>
                            <th>LAST REPORT · UTC</th>
                            <th>SCREENING</th>
                            <th />
                          </tr>
                        </thead>
                        <tbody>
                          {fleet?.items.map((v) => (
                            <tr
                              key={v.mmsi}
                              className={
                                selected === v.mmsi ? "selected-row" : ""
                              }
                              onClick={() => setSelected(v.mmsi)}
                            >
                              <td>
                                <div className="vessel-cell">
                                  <span className="ship-icon">
                                    <Ship size={17} />
                                  </span>
                                  <div>
                                    <strong>{v.name}</strong>
                                    <small>{v.mmsi}</small>
                                  </div>
                                </div>
                              </td>
                              <td>{v.vessel_type}</td>
                              <td className="numeric">
                                {v.speed.toFixed(1)}{" "}
                                <span className="muted">kn</span>
                              </td>
                              <td>{v.timestamp.slice(11)}</td>
                              <td>
                                <span
                                  className={`status ${v.anomaly ? "review" : ""}`}
                                >
                                  <span className="dot" />
                                  {v.anomaly
                                    ? "Review suggested"
                                    : "Typical pattern"}
                                </span>
                              </td>
                              <td>
                                <button
                                  aria-label={`Inspect ${v.name}`}
                                  className="icon-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelected(v.mmsi);
                                  }}
                                >
                                  <ArrowUpRight size={16} />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {fleet?.total === 0 && (
                        <div className="empty">
                          No vessels match these filters.
                        </div>
                      )}
                    </div>
                    <div className="pagination">
                      <span>
                        {fmt(fleet?.total)} vessels · page {page} of{" "}
                        {Math.max(1, Math.ceil((fleet?.total || 0) / 12))}
                      </span>
                      <div>
                        <button
                          aria-label="Previous page"
                          disabled={page === 1}
                          onClick={() => setPage((p) => p - 1)}
                        >
                          <ChevronLeft size={16} />
                        </button>
                        <button
                          aria-label="Next page"
                          disabled={page * 12 >= (fleet?.total || 0)}
                          onClick={() => setPage((p) => p + 1)}
                        >
                          <ChevronRight size={16} />
                        </button>
                      </div>
                    </div>
                  </Panel>
                  {detail && (
                    <Panel
                      className="detail-panel"
                      title={detail.vessel.name}
                      subtitle={`${detail.vessel.mmsi} · ${detail.track.length} observations in selected window`}
                      action={
                        <button
                          className="icon-btn"
                          aria-label="Close vessel detail"
                          onClick={() => setSelected(null)}
                        >
                          <X size={18} />
                        </button>
                      }
                    >
                      <div className="detail-grid">
                        <Chart>
                          <LineChart data={detail.track}>
                            {chartGrid}
                            <XAxis
                              dataKey="timestamp"
                              tickFormatter={(s) => s.slice(11, 16)}
                              {...axis}
                            />
                            <YAxis {...axis} unit=" kn" />
                            <Tooltip />
                            <Line
                              type="monotone"
                              dataKey="speed"
                              stroke="#189e8b"
                              dot={false}
                            />
                          </LineChart>
                        </Chart>
                        <div className="prediction">
                          <span className="eyebrow">
                            NEXT OBSERVED SPEED ESTIMATE
                          </span>
                          <strong>
                            {detail.predicted_next_speed ?? "—"}{" "}
                            <small>kn</small>
                          </strong>
                          <p>{detail.prediction_note}</p>
                        </div>
                      </div>
                    </Panel>
                  )}
                </>
              )}
              {tab === 1 && (
                <>
                  <div className="chart-grid">
                    <Panel
                      title="Activity over the day"
                      subtitle="Observation counts per UTC hour"
                    >
                      <Chart>
                        <AreaChart data={data.hourly}>
                          {chartGrid}
                          <XAxis dataKey="hour" {...axis} />
                          <YAxis {...axis} />
                          <Tooltip />
                          <Area
                            type="monotone"
                            dataKey="observations"
                            stroke="#179e8a"
                            fill="#e2f3ee"
                            strokeWidth={2}
                          />
                        </AreaChart>
                      </Chart>
                    </Panel>
                    <Panel
                      title="Speed distribution"
                      subtitle="Knots · zero-speed reports are retained"
                    >
                      <Chart>
                        <BarChart data={data.histogram}>
                          {chartGrid}
                          <XAxis dataKey="bin" {...axis} />
                          <YAxis {...axis} />
                          <Tooltip />
                          <Bar
                            dataKey="count"
                            fill="#5689db"
                            radius={[4, 4, 0, 0]}
                          />
                        </BarChart>
                      </Chart>
                    </Panel>
                    <Panel
                      title="Weather proximity & speed"
                      subtitle="Deterministic sample of up to 400 observations"
                    >
                      <Chart>
                        <ScatterChart>
                          {chartGrid}
                          <XAxis
                            dataKey="storm_distance_nm"
                            name="Storm distance"
                            unit=" nm"
                            type="number"
                            {...axis}
                          />
                          <YAxis
                            dataKey="speed"
                            name="Speed"
                            unit=" kn"
                            type="number"
                            {...axis}
                          />
                          <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                          <Scatter
                            data={data.scatter}
                            fill="#26a48f"
                            fillOpacity={0.55}
                          />
                        </ScatterChart>
                      </Chart>
                      <Notice>
                        Association is not causation. Best-track storm distance
                        describes historical proximity; it does not prove
                        weather caused a speed change.
                      </Notice>
                    </Panel>
                    <Panel
                      title="Feature correlations"
                      subtitle="Pearson correlation · pairwise complete observations"
                    >
                      <div className="correlation">
                        <table>
                          <thead>
                            <tr>
                              <th />
                              {data.correlation.columns.map((c) => (
                                <th key={c}>
                                  {c.replace("storm_distance_nm", "storm nm")}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {data.correlation.values.map((row, i) => (
                              <tr key={i}>
                                <th>
                                  {data.correlation.columns[i].replace(
                                    "storm_distance_nm",
                                    "storm nm",
                                  )}
                                </th>
                                {row.map((v, j) => (
                                  <td
                                    key={j}
                                    style={{
                                      background:
                                        v === null
                                          ? "#f5f6f8"
                                          : v >= 0
                                            ? `rgba(24,168,139,${Math.abs(v) * 0.6 + 0.03})`
                                            : `rgba(86,137,219,${Math.abs(v) * 0.6 + 0.03})`,
                                    }}
                                  >
                                    {v === null ? "N/A" : v.toFixed(2)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </Panel>
                  </div>
                  <Notice>
                    Use these plots to form hypotheses, then test them on
                    independent data. The cohort is a reproducible subset of one
                    day, not a representative sample of global shipping.
                  </Notice>
                </>
              )}
              {tab === 2 && <ScenarioLab />}
              {tab === 3 && benchmark && <Benchmark report={benchmark} />}
              {tab === 4 && (
                <Methodology data={data} onGuide={() => setGuide(true)} />
              )}
            </>
          )}
          <footer>
            <span>
              <Anchor size={13} /> Agentic Geo-Spatial Intelligence
            </span>
            <span>NOAA AIS / NHC HURDAT2 · Historical research workspace</span>
          </footer>
        </main>
      </div>
      {guide && (
        <div className="modal-backdrop" onClick={() => setGuide(false)}>
          <section
            className="guide-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Project walkthrough"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              autoFocus
              className="icon-btn close"
              aria-label="Close walkthrough"
              onClick={() => setGuide(false)}
            >
              <X />
            </button>
            <span className="eyebrow">YOUR FIVE-MINUTE PROJECT REVIEW</span>
            <h2>
              From a ship’s signal
              <br />
              to an explainable decision.
            </h2>
            {[
              [
                "01",
                "Start with the evidence",
                "AIS is a ship’s broadcast identity, position, speed, and course. We clean a real NOAA file and keep a reproducible vessel cohort.",
              ],
              [
                "02",
                "Explore before predicting",
                "Inspect distributions, missing values, geographic density, and individual trajectories. A map is useful only when its source and time window are clear.",
              ],
              [
                "03",
                "Test a measurable question",
                "Can a model estimate the next reported speed better than simply carrying the current speed forward? Vessels in the test set never appear in training.",
              ],
              [
                "04",
                "Explain the decision",
                "The scenario lab compares explicit weather, speed, distance, fuel, and emissions assumptions. Its agents are deterministic stages, not an LLM or an autonomous navigation system.",
              ],
              [
                "05",
                "Discuss the limits",
                "One day, variable forecast intervals, retrospective weather, and no verified delay outcomes. These define exactly what future research must address.",
              ],
            ].map(([n, t, p]) => (
              <div className="guide-step" key={n}>
                <span>{n}</span>
                <div>
                  <h3>{t}</h3>
                  <p>{p}</p>
                </div>
              </div>
            ))}
            <button className="button primary" onClick={() => setGuide(false)}>
              Let’s explore <ArrowRight size={16} />
            </button>
          </section>
        </div>
      )}
    </div>
  );
}

export default App;
