# Explain your project with confidence

## A 30-second introduction

Agentic Geo-Spatial Intelligence is a maritime research dashboard. It processes real historical AIS messages into an auditable vessel dataset, lets us explore movements and data quality, and tests whether machine learning improves next-speed estimates. A separate scenario lab compares hypothetical voyage alternatives through transparent decision stages. Every result is labeled as observed data, a model estimate, or a scenario assumption.

Use this as study material. Explain the project in your own words during the review.

## A seven-minute live demonstration

1. **0:00–0:45 — Scope.** Open Fleet overview. Point to 217 vessels and 37,843 observations. Explain why these are different counts.
2. **0:45–1:45 — Exploration.** Choose Cargo, move the replay slider, search a vessel, inspect its track. Explain latest-available positions are not simultaneous positions and the hexagons count distinct vessels over the selected interval.
3. **1:45–2:45 — EDA.** Show speed distribution, hourly activity, and missing dimensions. Explain missingness and sampling bias before discussing models.
4. **2:45–4:00 — Experiment.** Open Model benchmark. Identify train/test vessels and zero overlap. Compare persistence with boosting using MAE and RMSE. State that persistence wins MAE; boosting has slightly lower RMSE. Do not claim statistical superiority.
5. **4:00–5:30 — Agentic decisions.** Choose Severe weather, evaluate, and inspect contributions and alternatives. Show the agent trace. Save, reload, and delete the experiment. Explain these are deterministic policy stages and that the detour is hypothetical.
6. **5:30–6:30 — Engineering.** Show sources, cleaning audit, SHA-256, API docs at /docs, and the passing test output. Mention the bundled offline map and no-key setup.
7. **6:30–7:00 — Limits and next steps.** Explain single-day scope, no arrival labels, no proven fuel savings, and the need for multi-day validation and operational weather forecasts.

## Questions you should be able to answer

**What is AIS?** A broadcast system carrying vessel identity and movement information. It is not a perfect ground-truth sensor: fields may be missing or wrong, and not every vessel is represented.

**What is EDA here?** Checking the data before modeling: distributions, missingness, outliers, correlations, geographic density, and trajectories. These checks determine which claims are possible.

**Why not randomly split rows?** The same vessel would probably occur in both training and test data. The model might benefit from vessel-specific patterns already seen in training. Our split holds whole vessels out.

**Why does persistence win?** Many observations have low or unchanged speed. Predicting the current speed is a strong short-horizon baseline. Boosting can reduce some large errors while adding small errors to stable observations, which makes RMSE and MAE disagree.

**What is a knot?** One nautical mile per hour. We use nautical miles throughout the new scenario equations. The original prototype mixed statute miles and nautical miles; the new implementation separates and labels units.

**Why encode course as sine and cosine?** Bearings wrap around: 359° is close to 1°, although their raw numeric difference is large. Circular features preserve that relationship. The raw vessel type remains a numeric code, a known limitation for the linear model.

**What does an anomaly mean?** Isolation Forest finds unusual combinations of speed, position, and course. It does not establish unsafe or unlawful behavior. Fast passenger ships can be unusual in a slow-moving cohort without being dangerous.

**What is H3?** A hierarchical spatial index that assigns locations to hexagonal cells. We use actual resolution-5 cells and count unique MMSIs per cell. Counts are cumulative, not a real-time congestion measure.

**Is the exposure score a probability?** No. It is a transparent sum of wind, wave, traffic, and storm-proximity contributions. We have no verified delay outcomes with which to calibrate a probability.

**What makes it agentic?** The decision workflow has separate validation, exposure, voyage-estimation, and recommendation stages with an execution trace. It is a bounded deterministic workflow, not a language-model agent or autonomous navigation controller.

**Why exclude hurricane distance from the speed model?** HURDAT2 is a retrospective best track. Using it as though it were an operational forecast would overstate what information was available at the time. It remains useful for retrospective EDA.

**Is fuel consumption predicted by machine learning?** No. It is a documented engineering scenario using a cubic speed relation and user-provided fuel rate. The dataset lacks measured fuel use, so a validated fuel model cannot be claimed.

**Is a detour always greener?** No. More distance can outweigh a lower weather penalty. The interface shows the resulting time, fuel, cost, and CO₂ values so the trade-off is visible.

**What does the confidence interval mean?** It is a percentile interval from resampling held-out vessels as clusters. It reflects uncertainty within this cohort; it does not guarantee accuracy in another season or geography.

**What is the main contribution?** An integrated, reproducible research workflow that connects audited real data, exploration, honest benchmarking, and explainable scenario decisions in a usable application. Do not describe it as a novel state-of-the-art forecasting algorithm.

## Suggested division for three members

| Member | Demonstration ownership | Concepts to prepare |
|---|---|---|
| Member 1 — name pending | Dataset, audit, EDA | Sampling, missing values, H3, AIS limitations |
| Member 2 — name pending | Models and experiments | Group split, baselines, metrics, bootstrap, importance |
| Member 3 — name pending | Frontend, API, scenario workflow | Validation, React state, SQLite, units, tests |

All members should understand the end-to-end data flow, not only their assigned section.

## Resume wording to adapt after you understand the work

- Built a React/FastAPI maritime analytics workspace from 9.3M historical AIS messages, with vessel exploration, H3 aggregation, data-quality auditing, and scenario experiment storage.
- Benchmarked five next-speed approaches on 51 held-out vessels with leakage-aware splits, error analysis, and permutation-based feature inspection.
- Implemented explainable voyage scenario comparisons, offline geographic context, validated APIs, and automated behavioral checks.

Only claim work and skills you can demonstrate. Keep team contributions accurate.
