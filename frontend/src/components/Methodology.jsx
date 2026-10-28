import {
  Database,
  Wind,
  Layers,
  ShieldCheck,
  ArrowUpRight,
} from "lucide-react";
import { fmt } from "../lib/api";
import { Panel, Notice } from "./Shared";
export default function Methodology({ data, onGuide }) {
  const m = data.manifest;
  return (
    <>
      <div className="lab-banner">
        <ShieldCheck size={24} />
        <div>
          <strong>Every number has a source.</strong>
          <p>
            Real AIS observations, retrospective hurricane data, and explicitly
            labeled hypothetical scenarios.
          </p>
        </div>
        <button className="button secondary" onClick={onGuide}>
          Review guide <ArrowUpRight size={15} />
        </button>
      </div>
      <div className="chart-grid">
        <Panel
          title="The data journey"
          subtitle="Reproducible extraction from the local NOAA source"
        >
          <div className="pipeline">
            {[
              ["Raw AIS messages", m.raw_rows, "Entire source file scanned"],
              ["Regional messages", m.region_rows, "20–35° N · 90–75° W"],
              ["Deterministic cohort", m.cohort_rows, "MMSI modulo 13 = 0"],
              [
                "Clean observations",
                m.observations,
                "First valid report per vessel per 5-minute bin",
              ],
              [
                "Distinct vessels",
                m.vessels,
                "Unique identifiers, not message counts",
              ],
            ].map(([label, count, note], i) => (
              <div key={label}>
                <span>{String(i + 1).padStart(2, "0")}</span>
                <div>
                  <strong>{label}</strong>
                  <small>{note}</small>
                </div>
                <b>{fmt(count)}</b>
              </div>
            ))}
          </div>
        </Panel>
        <Panel
          title="Data-quality audit"
          subtitle="Counts before five-minute resampling"
        >
          <div className="audit-summary">
            <div>
              <strong>{fmt(m.invalid_rows)}</strong>
              <span>Invalid time / speed / course / identity</span>
            </div>
            <div>
              <strong>{m.duplicate_rows}</strong>
              <span>Duplicate vessel–timestamp pairs</span>
            </div>
          </div>
          <div className="missing-list">
            {Object.entries(m.missing_fields)
              .filter(([, n]) => n > 0)
              .map(([k, n]) => (
                <div key={k}>
                  <span>{k}</span>
                  <div>
                    <i style={{ width: `${(n / m.cohort_rows) * 100}%` }} />
                  </div>
                  <strong>{((n / m.cohort_rows) * 100).toFixed(1)}%</strong>
                </div>
              ))}
          </div>
          <Notice>
            Missing dimensions are retained as missing. Vessel type is mapped to
            “Other” when unavailable. Unknown course values are excluded; this
            can bias the cohort toward better-reported tracks.
          </Notice>
        </Panel>
      </div>
      <Panel
        title="Sources, definitions & boundaries"
        subtitle="Use this section to explain the scope during your project review"
      >
        <div className="sources">
          <a
            href="https://coast.noaa.gov/digitalcoast/data/vesseltraffic.html"
            target="_blank"
            rel="noreferrer"
          >
            <Database />
            <div>
              <strong>NOAA / BOEM MarineCadastre</strong>
              <p>Historical AIS · 28 August 2023 · regional vessel cohort</p>
            </div>
            <ArrowUpRight />
          </a>
          <a
            href="https://www.nhc.noaa.gov/data/tcr/AL102023_Idalia.pdf"
            target="_blank"
            rel="noreferrer"
          >
            <Wind />
            <div>
              <strong>NHC Hurricane Idalia report & HURDAT2</strong>
              <p>Retrospective storm track · linear time alignment</p>
            </div>
            <ArrowUpRight />
          </a>
          <a href="https://h3geo.org/docs/" target="_blank" rel="noreferrer">
            <Layers />
            <div>
              <strong>H3 spatial indexing</strong>
              <p>
                Resolution 5 · distinct vessel density across the selected
                window
              </p>
            </div>
            <ArrowUpRight />
          </a>
        </div>
        <div className="panel-pad">
          <h4>Known limitations</h4>
          <ul className="assumptions">
            {m.caveats.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
          <h4>Dataset fingerprint</h4>
          <code className="hash">SHA-256 {m.sha256}</code>
          <p className="small muted">{m.sampling}</p>
        </div>
      </Panel>
    </>
  );
}
