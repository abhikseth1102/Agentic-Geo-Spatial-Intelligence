import { chartGrid, axis } from "./ChartConfig";
import { Database, FlaskConical, ShieldCheck } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ScatterChart,
  Scatter,
  ReferenceLine,
} from "recharts";
import { fmt } from "../lib/api";
import { Panel, Chart, Notice, Stat } from "./Shared";
export default function Benchmark({ report: r }) {
  const best = Math.min(...r.results.map((x) => x.mae));
  return (
    <>
      <div className="stats three">
        <Stat
          label="Training observations"
          value={fmt(r.train_rows)}
          icon={Database}
          note={`${r.train_vessels} distinct vessels`}
        />
        <Stat
          label="Held-out observations"
          value={fmt(r.test_rows)}
          icon={FlaskConical}
          note={`${r.test_vessels} unseen vessels`}
        />
        <Stat
          label="Vessel overlap"
          value={r.overlapping_vessels}
          icon={ShieldCheck}
          note="No shared vessels across the split"
        />
      </div>
      <Notice>
        The target is <strong>{r.task}</strong>. The gradient-boosting model was
        specified before evaluation. A simple baseline can win—and reporting
        that honestly is a valid experimental result.
      </Notice>
      <Panel
        title="Experimental comparison"
        subtitle="Lower MAE and RMSE are better · errors in knots"
        action={<span className="badge">SEED {r.seed}</span>}
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>APPROACH</th>
                <th>MAE ↓</th>
                <th>RMSE ↓</th>
                <th>R² ↑</th>
                <th>TRAIN TIME</th>
              </tr>
            </thead>
            <tbody>
              {r.results.map((x) => (
                <tr key={x.model}>
                  <td>
                    <strong>{x.model}</strong>
                    {x.mae === best && <span className="best">Lowest MAE</span>}
                  </td>
                  <td>{x.mae.toFixed(4)}</td>
                  <td>{x.rmse.toFixed(4)}</td>
                  <td>{x.r2.toFixed(4)}</td>
                  <td>{x.train_seconds}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      <div className="chart-grid">
        <Panel
          title="What the model relies on"
          subtitle="Permutation importance · increase in held-out MAE"
        >
          <Chart>
            <BarChart
              data={r.feature_importance}
              layout="vertical"
              margin={{ left: 18, right: 20 }}
            >
              {chartGrid}
              <XAxis type="number" {...axis} />
              <YAxis dataKey="feature" type="category" width={90} {...axis} />
              <Tooltip />
              <Bar
                dataKey="increase_mae"
                fill="#18a88b"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </Chart>
          <Notice>
            Shuffling one feature measures how much performance degrades. This
            is permutation importance, not SHAP or a causal effect.
          </Notice>
        </Panel>
        <Panel
          title="Predicted vs observed speed"
          subtitle="300 held-out observations · both axes in knots"
        >
          <Chart>
            <ScatterChart>
              {chartGrid}
              <XAxis dataKey="actual" name="Observed" type="number" {...axis} />
              <YAxis
                dataKey="predicted"
                name="Predicted"
                type="number"
                {...axis}
              />
              <Tooltip />
              <ReferenceLine
                segment={[
                  { x: 0, y: 0 },
                  { x: 30, y: 30 },
                ]}
                stroke="#a8b4c1"
                strokeDasharray="4 4"
              />
              <Scatter data={r.scatter} fill="#5689db" fillOpacity={0.55} />
            </ScatterChart>
          </Chart>
        </Panel>
      </div>
      {r.subgroups && (
        <Panel
          title="Where the errors occur"
          subtitle="Held-out activity and horizon subgroups · MAE in knots"
        >
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>SUBGROUP</th>
                  <th>OBSERVATIONS</th>
                  <th>PERSISTENCE</th>
                  <th>BOOSTING</th>
                </tr>
              </thead>
              <tbody>
                {r.subgroups.map((s) => (
                  <tr key={s.group}>
                    <td>{s.group}</td>
                    <td>{fmt(s.n)}</td>
                    <td>{s.persistence_mae}</td>
                    <td>{s.boosting_mae}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="panel-pad">
            <p>
              Activity and horizon groups overlap. Different vessel compositions
              mean these rows do not isolate the causal effect of forecast
              duration.
            </p>
          </div>
        </Panel>
      )}
      <Panel title="Reproducibility & uncertainty" subtitle={r.split}>
        <div className="panel-pad">
          <p>
            Gradient boosting MAE:{" "}
            <strong>{r.mae_cluster_bootstrap_95ci.join("–")} kn</strong> (95%
            percentile interval, 500 vessel-cluster bootstrap samples). This
            interval measures sampling uncertainty within the held-out cohort,
            not global accuracy.
          </p>
          <ul className="assumptions">
            {r.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
          <code>
            python scripts/build_dataset.py → python scripts/train_benchmark.py
          </code>
        </div>
      </Panel>
    </>
  );
}
