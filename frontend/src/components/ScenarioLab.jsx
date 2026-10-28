import { useEffect, useState } from "react";
import {
  FlaskConical,
  RefreshCw,
  Compass,
  Save,
  Check,
  Trash2,
} from "lucide-react";
import { api, fmt } from "../lib/api";
import { Panel } from "./Shared";
const initial = {
  name: "Gulf transit assessment",
  distance_nm: 300,
  speed: 14,
  wind: 25,
  waves: 2,
  congestion: 35,
  storm_distance_nm: 160,
  fuel_tons_day: 24,
  fuel_price: 650,
  carbon_factor: 3.114,
};
export default function ScenarioLab() {
  const [form, setForm] = useState(initial),
    [result, setResult] = useState(null),
    [saved, setSaved] = useState([]),
    [pending, setPending] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  useEffect(() => {
    api("/scenarios")
      .then(setSaved)
      .catch((e) => setError(e.message));
  }, []);
  async function run(save = false) {
    setPending(true);
    setError("");
    setMessage("");
    try {
      const r = await api(save ? "/scenarios" : "/scenarios/evaluate", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setResult(save ? r.result : r);
      if (save) {
        setSaved(await api("/scenarios"));
        setMessage("Scenario saved to your local experiment history.");
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setPending(false);
    }
  }
  function change(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
    setResult(null);
    setMessage("");
  }
  const sliders = [
    ["distance_nm", "Voyage distance", 50, 1000, 10, "nm"],
    ["speed", "Cruising speed", 5, 25, 0.5, "kn"],
    ["wind", "Wind speed", 0, 100, 1, "kn"],
    ["waves", "Significant wave height", 0, 12, 0.2, "m"],
    ["congestion", "Traffic assumption", 0, 100, 1, "/100"],
    ["storm_distance_nm", "Distance to storm", 0, 600, 10, "nm"],
  ];
  return (
    <>
      <div className="lab-banner">
        <FlaskConical size={22} />
        <div>
          <strong>A controlled what-if environment</strong>
          <p>
            Scenario inputs are hypothetical. Results are estimates, not live
            weather or navigational instructions.
          </p>
        </div>
        <span className="badge">SIMULATION</span>
      </div>
      <div className="lab-grid">
        <Panel
          title="Define your scenario"
          subtitle="Change one input at a time to understand its effect."
        >
          <div className="form-body">
            <label className="field">
              Scenario name
              <input
                value={form.name}
                maxLength={80}
                onChange={(e) => change("name", e.target.value)}
              />
            </label>
            <div className="presets">
              {[
                [
                  "Calm transit",
                  {
                    wind: 10,
                    waves: 0.8,
                    congestion: 15,
                    storm_distance_nm: 400,
                  },
                ],
                [
                  "Busy corridor",
                  {
                    wind: 25,
                    waves: 2.5,
                    congestion: 85,
                    storm_distance_nm: 150,
                  },
                ],
                [
                  "Severe weather",
                  { wind: 75, waves: 7, congestion: 70, storm_distance_nm: 40 },
                ],
              ].map(([n, v]) => (
                <button
                  key={n}
                  onClick={() => {
                    setForm({ ...form, ...v, name: n });
                    setResult(null);
                  }}
                >
                  {n}
                </button>
              ))}
            </div>
            {sliders.map(([k, label, min, max, step, unit]) => (
              <label className="slider" key={k}>
                <span>
                  {label}
                  <strong>
                    {form[k]} <small>{unit}</small>
                  </strong>
                </span>
                <input
                  type="range"
                  min={min}
                  max={max}
                  step={step}
                  value={form[k]}
                  onChange={(e) => change(k, +e.target.value)}
                />
                <span className="range-ends">
                  <small>
                    {min} {unit}
                  </small>
                  <small>
                    {max} {unit}
                  </small>
                </span>
              </label>
            ))}
            <details>
              <summary>Fuel & emissions assumptions</summary>
              <div className="assumption-fields">
                {[
                  ["fuel_tons_day", "Fuel tonnes/day at 14 kn", 1, 500, 0.1],
                  ["fuel_price", "Fuel price USD/tonne", 1, 3000, 1],
                  ["carbon_factor", "CO₂ factor t/t fuel", 2, 4, 0.001],
                ].map(([k, l, min, max, step]) => (
                  <label className="field" key={k}>
                    {l}
                    <input
                      type="number"
                      min={min}
                      max={max}
                      step={step}
                      value={form[k]}
                      onChange={(e) => change(k, +e.target.value)}
                    />
                  </label>
                ))}
              </div>
            </details>
            <button
              className="button primary full"
              disabled={pending || !form.name.trim()}
              onClick={() => run()}
            >
              {pending ? (
                <RefreshCw className="spin" size={16} />
              ) : (
                <Compass size={16} />
              )}
              Evaluate scenario
            </button>
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
          </div>
        </Panel>
        <div>
          {result ? (
            <>
              <ScenarioSummary form={form} result={result} />
              <Panel
                title="Decision briefing"
                subtitle="A traceable recommendation for human review"
                action={
                  <span
                    className={`status ${result.level === "High" ? "review" : ""}`}
                  >
                    {result.level} exposure
                  </span>
                }
              >
                <div className="briefing">
                  <div
                    className="score"
                    style={{ "--score": `${result.score}%` }}
                  >
                    <strong>
                      {result.score}
                      <small>/100</small>
                    </strong>
                  </div>
                  <div>
                    <span className="eyebrow">PROPOSED OPTION</span>
                    <h2>{result.recommendation}</h2>
                    <p>{result.explanation}</p>
                  </div>
                </div>
                <div className="contributions">
                  {result.components.map((c) => (
                    <div key={c.factor}>
                      <span>{c.factor}</span>
                      <div>
                        <i style={{ width: `${(c.points / 30) * 100}%` }} />
                      </div>
                      <strong>{c.points}</strong>
                    </div>
                  ))}
                </div>
              </Panel>
              <Panel
                title="Compare the trade-offs"
                subtitle="Each alternative uses the same input assumptions"
              >
                <div className="table-wrap">
                  <table className="comparison">
                    <thead>
                      <tr>
                        <th>OPTION</th>
                        <th>HOURS</th>
                        <th>FUEL t</th>
                        <th>CO₂ t</th>
                        <th>COST $</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.alternatives.map((a) => (
                        <tr
                          key={a.name}
                          className={
                            a.name === result.recommendation
                              ? "selected-row"
                              : ""
                          }
                        >
                          <td>
                            <strong>{a.name}</strong>
                            <small>
                              {a.speed} kn · {a.distance_nm} nm
                            </small>
                          </td>
                          <td>{a.hours}</td>
                          <td>{a.fuel_tons}</td>
                          <td>{a.co2_tons}</td>
                          <td>{fmt(a.fuel_cost)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="panel-pad">
                  <button
                    className="button secondary"
                    disabled={pending}
                    onClick={() => run(true)}
                  >
                    <Save size={15} />
                    Save experiment
                  </button>
                  {message && (
                    <p className="success" role="status">
                      <Check size={14} />
                      {message}
                    </p>
                  )}
                </div>
              </Panel>
              <Panel
                title="Agent execution trace"
                subtitle="Deterministic stages · no external AI service"
              >
                <div className="agent-trace">
                  {result.trace.map((t, i) => (
                    <div key={t.agent}>
                      <span>{i + 1}</span>
                      <div>
                        <h4>{t.agent}</h4>
                        <p>{t.finding}</p>
                      </div>
                      <Check size={16} />
                    </div>
                  ))}
                </div>
                <details className="panel-pad">
                  <summary>Read all assumptions</summary>
                  <ul className="assumptions">
                    {result.assumptions.map((a) => (
                      <li key={a}>{a}</li>
                    ))}
                  </ul>
                </details>
              </Panel>
            </>
          ) : (
            <div className="lab-empty">
              <div className="orb">
                <Compass size={48} />
              </div>
              <span className="eyebrow">YOUR NEXT EXPERIMENT STARTS HERE</span>
              <h2>
                What changes when
                <br />
                the conditions change?
              </h2>
              <p>
                Set your assumptions, evaluate the scenario, and compare voyage
                time, fuel, emissions, and exposure side by side.
              </p>
              <div>
                <span>
                  <Check size={14} />
                  Explainable factors
                </span>
                <span>
                  <Check size={14} />
                  Persistent history
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
      <Panel
        title="Experiment history"
        subtitle="Saved locally in SQLite · up to 100 most recent runs"
      >
        <div className="history-list">
          {saved.length === 0 ? (
            <p className="muted">
              No saved experiments yet. Evaluate a scenario and save its
              results.
            </p>
          ) : (
            saved.map((s) => (
              <div key={s.id}>
                <FlaskConical size={18} />
                <div>
                  <strong>{s.name}</strong>
                  <small>
                    {new Date(s.created).toLocaleString()} · {s.result.score}
                    /100 exposure
                  </small>
                </div>
                <button
                  className="button secondary"
                  onClick={() => {
                    setForm(s.payload);
                    setResult(s.result);
                    setMessage("Loaded saved experiment.");
                  }}
                >
                  Load
                </button>
                <button
                  className="icon-btn"
                  aria-label={`Delete ${s.name}`}
                  onClick={async () => {
                    try {
                      await api(`/scenarios/${s.id}`, { method: "DELETE" });
                      setSaved(saved.filter((x) => x.id !== s.id));
                    } catch (e) {
                      setError(e.message);
                    }
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </Panel>
    </>
  );
}


function ScenarioSummary({ form, result }) {
  const baseline = result.alternatives[0];
  const selected = result.alternatives.find(a => a.name === result.recommendation) || baseline;
  const calmHours = form.distance_nm / form.speed;
  const extra = baseline.hours - calmHours;
  const difference = selected.hours - baseline.hours;
  const alerts = [];
  if (form.wind >= 34) alerts.push(`High wind input: ${form.wind} kn`);
  if (form.waves >= 4) alerts.push(`High wave input: ${form.waves} m`);
  if (form.storm_distance_nm <= 100) alerts.push(`Nearby storm / cyclone scenario: ${form.storm_distance_nm} nm`);
  return <section className="scenario-summary" aria-label="Weather alerts and voyage time">
    <div className={`scenario-alerts ${alerts.length ? 'has-alerts' : ''}`}>
      <strong>{alerts.length ? 'Weather scenario warnings' : 'No scenario warning thresholds reached'}</strong>
      {alerts.length > 0 && <ul>{alerts.map(a => <li key={a}>{a}</li>)}</ul>}
      <p>Hypothetical inputs, not live warnings. Project screening rules: wind ≥34 kn, waves ≥4 m, storm distance ≤100 nm. These are not vessel-specific safety limits.</p>
    </div>
    <div className="voyage-time-cards">
      <div><span>Estimated voyage time</span><strong>{selected.hours.toFixed(2)} <small>h</small></strong><p>{selected.name}</p></div>
      <div><span>Weather & traffic time added</span><strong>{extra.toFixed(2)} <small>h</small></strong><p>Maintain course versus {calmHours.toFixed(2)} h with no wave or traffic penalty</p></div>
      <div><span>{Math.abs(difference) < 0.005 ? 'No time change' : difference < 0 ? 'Time saved' : 'Additional travel time'}</span><strong>{Math.abs(difference).toFixed(2)} <small>h</small></strong><p>Recommended option versus maintain course</p></div>
    </div>
    <p className="time-assumption">Illustrative travel estimates, not measured arrival delays. A lower-exposure detour can take longer; wind and storm distance affect the exposure score, while waves and traffic affect modeled travel time.</p>
  </section>;
}
