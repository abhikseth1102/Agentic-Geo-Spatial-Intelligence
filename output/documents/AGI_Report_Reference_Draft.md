# Agentic Geo-Spatial Intelligence

Reference draft for study; follow your instructor’s AI policy.


## Agentic Geo-Spatial Intelligence

Technical reference draft for project review

| Team member | Name | Registration number |
| --- | --- | --- |
| 1 | ________________________ | ___________________ |
| 2 | ________________________ | ___________________ |
| 3 | ________________________ | ___________________ |

Abstract

Maritime data can support useful operational questions only when the observations, assumptions, and evaluation procedures are made explicit. This project develops a local research workspace for historical vessel analysis, short-horizon speed estimation, and explainable voyage scenarios. The implementation combines a React interface with a FastAPI service, a reproducible Python data pipeline, actual H3 spatial indexing, and SQLite experiment storage. Its objective is to make an end-to-end analytical process inspectable, rather than to claim autonomous navigation or verified arrival-delay prediction.

The source AIS file contains 9,306,345 messages from 28 August 2023. A Gulf of Mexico and Florida bounding box, deterministic vessel selection, validation, duplicate removal, and five-minute resampling produce 37,843 observations from 217 distinct vessel identifiers. Hurricane Idalia positions are aligned retrospectively using the local NHC HURDAT2 archive. The interface supports vessel search, cumulative hourly replay, trajectory inspection, distributions, correlations, missing-value analysis, and geographic density. An offline coastline provides geographic context without requiring API credentials.

The forecasting experiment estimates the next observed speed over intervals of 2–30 minutes. A vessel-disjoint split contains 27,264 training examples from 151 vessels and 9,985 test examples from 51 vessels. Persistence, a training-median baseline, ridge regression, random forest, and gradient boosting are evaluated with MAE, RMSE, and R². Persistence achieves the lowest MAE, 0.3498 knots; gradient boosting produces a slightly lower RMSE, 1.4886 knots compared with 1.5182 knots. These results show why a complex model should be judged against a strong operational baseline, not assumed to be superior.

A separate scenario workflow validates inputs, calculates a documented exposure index, compares three voyage assumptions, and records a human-review recommendation. Fuel and carbon estimates are illustrative calculations, not measured savings. The main contribution is an integrated and reproducible analytical workflow with explicit limits. Multi-day evaluation, validated operational weather inputs, and actual voyage outcomes are necessary before stronger predictive or operational claims can be made.

Keywords: automatic identification system; exploratory data analysis; maritime intelligence; geospatial analytics; vessel forecasting; explainable decisions; data quality.

The supplied report instructions prohibit AI tools. This reference material supports study and verification; the submitted report must be student-authored or explicitly permitted by the instructor.


## 1 Introduction

1.1 From vessel messages to useful evidence

A ship-position dataset appears straightforward: each row describes a vessel at a place and time. In practice, the analytical problem is more difficult. One vessel can transmit many thousands of messages, reporting intervals vary, and static fields may be incomplete. A dense cluster of points can therefore represent frequent reporting, repeated stationary observations, or many different vessels. These interpretations have different implications for an analysis of traffic. The project begins by treating message counts, distinct-vessel counts, and temporal coverage as separate quantities.

Automatic Identification System messages provide identity, position, speed over ground, course over ground, and other vessel information. Historical archives make it possible to study movement at a scale that would be difficult to observe manually. However, the broadcast record is not a complete inventory of maritime activity. Coverage depends on carriage requirements, reception, collection practices, and data quality. The NOAA MarineCadastre source is suitable for historical exploration, but the presence of an official source does not remove the need for validation or justify assumptions about unobserved vessels.

This project focuses on a historical Gulf of Mexico and Florida case study during the formation of Hurricane Idalia. The weather context makes it tempting to infer disruption from proximity alone. That inference would be premature. AIS speed is affected by port operations, vessel purpose, maneuvering, route choices, and reporting quality. The supplied files do not contain a verified delay outcome, an expected arrival schedule, or measured fuel consumption. Consequently, the implemented prediction task is limited to an outcome actually observable in the data: the next reported speed.

1.2 Why an integrated workspace is useful

Separate scripts can calculate statistics, train models, and draw maps, yet they often leave the reader to connect those results manually. An integrated workspace makes the relationship visible. A vessel selected from a directory can be inspected on the map; its speed history can be compared with a model estimate; the dataset audit explains which observations were retained; and the benchmark identifies how the estimate was evaluated. This reduces the gap between an attractive demonstration and an analysis that can be questioned and reproduced.

The interface deliberately separates three forms of evidence. Historical views display observations. The benchmark displays model estimates evaluated against held-out observations. The scenario lab displays calculations conditional on hypothetical inputs. Keeping these categories separate is a design requirement, because a numerical result can look authoritative even when it is only an assumption. The distinction is repeated in labels, source notes, model explanations, and the review guide.

1.3 Intended use

The intended user is a student or analyst exploring how maritime data, machine learning, and decision support fit together. The system is designed for local demonstration and research. It does not connect to a live AIS feed, issue navigation commands, or certify a route as safe. Its value lies in making a bounded investigation complete and inspectable: source data, preprocessing, exploratory questions, baseline comparisons, uncertainty, and limitations can all be examined in one workspace.


## 1 Introduction continued

1.4 Research questions and evaluation criteria

The central forecasting question is whether a small supervised model can estimate the next observed vessel speed more accurately than carrying the current speed forward. This question is deliberately narrower than arrival prediction or autonomous routing. It has a measurable target in the available files, can be tested without fabricating labels, and exposes the importance of a meaningful baseline. The experiment also asks whether the answer changes when error is measured by average absolute deviation or by squared-error sensitivity to large mistakes.

| Question | Evidence in the implementation |
| --- | --- |
| What remains after cleaning and sampling? | Manifest counts, missingness audit, fingerprint, deterministic extraction rules. |
| How does movement vary across the cohort? | Speed histogram, hourly counts, vessel classes, trajectories, H3 density. |
| Does a learned model improve next-speed estimates? | Five approaches evaluated on the same held-out vessel cohort. |
| What information drives model behavior? | Permutation importance on held-out observations and subgroup error tables. |
| How do voyage assumptions change outcomes? | Scenario contribution chart, time/fuel/CO₂ comparison, persistent experiment history. |

The system is evaluated on both analytical and software criteria. Analytical criteria include a defined target, separation of train and test vessels, comparable metrics, and a clear account of the dataset boundaries. Software criteria include input validation, consistent filtering, correct units, reproducible execution, persistent scenario history, and a usable interface. A chart is considered successful only when the underlying API values and selected filters agree.

1.5 Scope and exclusions

The source contains one day of U.S. AIS reports. The analytical cohort restricts latitude to 20–35 degrees north and longitude to 90–75 degrees west. A deterministic modulo rule retains a subset of MMSIs, and a five-minute bin keeps the first valid report per vessel. This choice makes a laptop demonstration manageable while retaining trajectories. It does not create a balanced sample across ship types, ports, or activity levels. Results should therefore be described as properties of the extracted cohort.

No ground-truth hazard labels are supplied. The anomaly layer identifies unusual feature combinations and must be interpreted as a screening tool. Likewise, the scenario lab does not solve a constrained sea-route optimization problem. It compares a baseline voyage, a lower-speed voyage, and a hypothetical longer corridor with reduced exposure. Bathymetry, land avoidance, vessel draft limits, traffic separation schemes, and navigational regulations are outside the implemented model.

The word agentic refers to an inspectable sequence of bounded decision stages. The current stages are deterministic and do not call a language model. This design keeps the prototype reproducible and removes dependency on external AI credentials. A future language-model explanation layer would need to cite the same structured calculations rather than invent additional numerical claims.


## 1 Introduction continued

1.6 System contribution and architecture

Figure 1. Data preparation, retrospective context, model evaluation, and the user workspace form one inspectable workflow.

The implementation contributes a coherent research artifact rather than a new forecasting algorithm. Its analytical contribution is the alignment of a real dataset, a defensible target, reproducible preprocessing, and baseline-aware evaluation. Its engineering contribution is the connection of those elements to a usable frontend with local persistence and transparent scenario traces. These contributions can be demonstrated directly and do not depend on claims of state-of-the-art accuracy.

The data preparation script scans the raw CSV in chunks to avoid loading the entire source file at once. It writes a compact observation table and a manifest. The model script consumes that derived table, generates a vessel-disjoint experiment, and records results in a machine-readable benchmark file. The API loads these artifacts at startup. The React client requests summaries, filtered vessel lists, trajectories, and scenario evaluations through documented endpoints.

The map uses a bundled Natural Earth coastline by default, allowing the main geographic view to work without tile-service credentials. Optional OpenStreetMap tiles provide finer visual context when a network connection is available. H3 cells are computed from observed coordinates, not randomly drawn. Selecting a vessel changes the displayed trajectory, while the hourly control restricts the cumulative historical window. Each marker is the latest available report for its vessel, not a claim that all ships were observed at one simultaneous instant.

1.7 Reproducibility as a design choice

The repository retains the derived cohort, preprocessing description, fixed random seed, model configuration, software versions, and a SHA-256 fingerprint. Large raw archives and local scenario history are excluded from version control. A new environment can train the benchmark from the compact data without re-downloading the raw archive. Recreating the exact extraction requires the original AIS and HURDAT2 files, which are already present in the local project folder.

The report proceeds from prior research to the implemented methodology and then to measured results. Published papers motivate design choices and future directions; their published metrics are not placed beside the local metrics as if they were directly comparable. The local comparison uses one dataset, one target, and one held-out split for every implemented approach. That common experimental setting is essential for a meaningful results table.


## 2 Related work and literature survey

2.1 Prediction from AIS sequences

Bao et al. (2022) describe a trajectory-prediction architecture combining multi-head attention with a bidirectional recurrent unit. Park et al. (2021) combine trajectory clustering with a bidirectional LSTM. Their publisher abstracts motivate the use of historical sequences and movement patterns, whereas the current project intentionally starts with a compact single-observation feature set. These are different tasks and model capacities; no performance equivalence is implied.

Sequence methods are a plausible next step when a sufficiently long and carefully split trajectory dataset is available. They also introduce decisions about sequence length, interpolation, padding, observation gaps, and vessel identity. A larger architecture does not remove these data-design choices. The current benchmark establishes a transparent baseline before introducing that additional complexity. The observed strength of persistence makes this baseline especially important.

The records for Zhu et al. (2025) and Wang et al. (2024) identify hybrid AIS predictors, including explicit attention to uncertainty in the latter title. Their bibliographic metadata were verified, but full experimental details were not available in the retrieved records. They are included as targeted reading for future model development. Their results are not summarized numerically or treated as evidence that a hybrid model would improve this project’s cohort.

2.2 Sampling and trajectory representation

Zaman et al. (2023) discuss the irregular timing of AIS reports and study interpolation for waypoint inference. That issue directly affects the definition of a prediction horizon. This project retains observed reports after five-minute binning and predicts the next available speed only when the interval lies between 2 and 30 minutes. It does not silently convert irregular observations into a fixed 15-minute target.

Trajectory simplification is another relevant preprocessing topic, represented by Wei et al. (2020). The present pipeline uses an explicitly documented binning rule rather than claiming behavior-preserving simplification. Binning reduces repeated reports and computation, but can suppress brief maneuvers. The first valid report in a bin is retained; the rule therefore changes the observational resolution and must be reported alongside model results.

| Research direction | Relation to this project | Boundary |
| --- | --- | --- |
| Recurrent and attention-based prediction | Motivates future sequence features | Not implemented or benchmarked locally. |
| Hybrid predictors and uncertainty | Useful follow-up literature | Metadata verified; no imported performance claims. |
| Sparse-track interpolation | Clarifies variable observation horizons | No imputed speed targets are created. |
| Trajectory simplification | Highlights sampling trade-offs | Five-minute binning is not behavior-preserving by proof. |

The literature therefore supports a staged development strategy: first make the data and baseline defensible, then evaluate richer temporal models on an unchanged or carefully redesigned protocol. A future comparison should retain vessel-disjoint testing and add later-date evaluation. Without those controls, additional model complexity could improve apparent accuracy while leaving deployment performance uncertain.


## 2 Related work continued

2.3 Anomaly detection and the meaning of unusual

Wolsing et al. (2022) survey 44 approaches to anomalies in maritime AIS tracks. Their abstract emphasizes the variety of anomaly types and the limitations of existing approaches. Stach et al. (2023) place anomaly detection in the setting of vessel traffic services and decision-support tools. Together these sources motivate separating a statistical alert from an operational conclusion.

An unusual movement can reflect legitimate vessel function, environmental conditions, a reporting error, or genuinely concerning behavior. A speed that is ordinary for a passenger ship may be unusual in a cohort dominated by slowly moving pleasure craft. Position-based features also make rarity dependent on the region represented in training. The project therefore labels anomaly results as review suggestions. It does not assign legal, safety, or security meaning to an Isolation Forest flag.

The wider reading set includes the review by Ribeiro et al. (2023), an unsupervised situational-awareness study by Liang et al. (2024), and kinematic anomaly classification by Liu et al. (2024). Skat-Rørdam et al. (2025) identify a self-explainable autoencoder approach. The latter records were verified bibliographically; detailed methods and performance are not reconstructed from their titles. They define useful categories for a fuller student-led literature review: reconstruction error, unsupervised scoring, kinematic features, and explanation.

2.4 Spatial patterns and traffic networks

Filipiak et al. (2020) describe a network-extraction process using maneuvering points, waypoint discovery, and edge construction. This provides a useful distinction between a traffic-density map and a route graph. The H3 layer in the current application aggregates observed vessel presence within cells. It does not infer a graph of navigable connections or solve routing over those connections.

Young et al. (2022) use MarineCadastre data to investigate a network of U.S. ports and regional connectivity. Their work supports the broader relevance of vessel movement to transport-system analysis. The present case study is more local and descriptive: it does not build a port network, calculate resilience, or attribute observed movement to disruption. Those analyses would require explicit port definitions and additional temporal evidence.

The reading list also includes maritime-network evolution (Carlini et al. (2022)), maneuvering hot zones (Wei et al. (2022)), and traffic-safety analytics (Ma et al. (2024)). These are relevant extensions, but the implementation does not claim to reproduce them. H3 density is presented as cumulative distinct-vessel presence, with resolution and time window visible to the user.

2.5 Practical implication

The common lesson is that the analytical unit must match the question. A message, a vessel, a trajectory, a port call, and a network edge are different objects. Counting messages may be useful for data-volume planning; counting vessels is more appropriate for describing observed fleet composition. Similarly, a statistical outlier score answers a different question from a labeled anomaly classifier. The dashboard preserves these distinctions so that the demonstration can be explained without overstating its capabilities.


## 2 Related work continued

2.6 Fuel models require fuel observations

Kim et al. (2021) study fuel-consumption models using in-service data from a container ship. Yang et al. (2024) combine voyage and meteorological information when comparing fuel-prediction models. Their abstracts establish an important requirement: a validated fuel predictor depends on relevant operational measurements, not just coordinates and an assumed relationship.

Melo et al. (2024) examine machine-learning approaches for vessel fuel consumption in the Amazon region. Chen et al. (2025) examine time-series architectures for the same broader prediction problem. Luo et al. (2025) identify transfer learning as another approach. These studies define possible future work when measured fuel use and vessel characteristics become available. Their published accuracy values are not transferable to the AIS-only cohort used here.

Ribeiro da Silva et al. (2024) describe an AIS-based emission-assessment methodology that uses vessel technical and operational characteristics. The present scenario model is much simpler. It converts an assumed fuel amount into CO₂ using a configurable carbon factor, with 3.114 tonnes of CO₂ per tonne of residual fuel as the default. This is a conditional engineering calculation. It does not estimate a validated regional emission inventory or measured environmental savings.

2.7 Coverage and context

The record for Hague et al. (2025) explicitly concerns AIS underrepresentation around coastal Scotland. Its geographic finding should not be copied as a numerical correction for the Gulf cohort. Instead, it highlights a question that this study must acknowledge: which vessels and activities are missing from a broadcast-derived dataset? Ramos et al. (2025) use AIS in a coastal tourism setting, illustrating that the meaning of vessel activity depends on the application and vessel population.

In the current cohort, pleasure vessels form a large share of distinct identifiers, and many observations have low speed. Neither fact can be generalized to all Gulf shipping from this deterministic subset. Missing draft, width, and navigation-status fields further limit analyses requiring technical vessel properties. This motivates retaining missing values visibly rather than filling them with plausible-looking numbers.

2.8 Gap addressed by the project

The project addresses an educational and engineering gap between isolated analytical methods and an inspectable research demonstration. It combines data lineage, exploratory views, a common benchmark, explicit scenario assumptions, and a usable interface. It does not fill the broader research gaps of navigation-grade routing, validated delay forecasting, or fuel prediction from operational measurements. Those remain future tasks requiring different data and validation.

The bibliography contains 25 journal records published from 2020 onward, exceeding the required minimum of 15 recent papers. Metadata were retrieved from Crossref; publisher abstracts were reviewed when present. Entries without accessible abstracts are marked in the reading matrix as metadata-only. Before writing the final student-authored literature review, the team should read the selected full papers, verify their experimental setups, and revise the synthesis accordingly. A verified reference is not a substitute for reading a paper.


## 3 Proposed methodology

3.1 Source extraction and auditable cleaning

The source file is streamed in 250,000-row chunks. The pipeline selects a geographic region, keeps vessel identifiers satisfying MMSI modulo 13 equals zero, validates observations, removes duplicate identifier–timestamp pairs, and retains the first valid report per five-minute vessel bin. The modulo rule is deterministic and simple to reproduce. It is not a random probability sample or an attempt to balance classes.

| Stage | Count | Interpretation |
| --- | --- | --- |
| Entire raw file | 9,306,345 | All messages scanned. |
| Geographic subset | 1,538,134 | Messages within the Gulf/Florida box. |
| Vessel cohort | 122,629 | Messages from selected identifiers. |
| Invalid observations removed | 25,113 | Time, speed, course, or identity invalid. |
| Duplicate pairs removed | 6 | Repeated vessel and timestamp. |
| Removed by five-minute binning | 59,667 | Repeated valid reports within bins. |
| Retained observations | 37,843 | Final analytical table. |
| Distinct vessels | 217 | Unique MMSIs in retained data. |

The validation range accepts speeds from 0 to 60 knots and courses from 0 inclusive to 360 exclusive. Unknown or invalid courses are removed, which can disproportionately exclude stationary or poorly reported vessels. Missing names receive an explicit unnamed-vessel label. Missing vessel-type codes are assigned to the Other category. Missing technical dimensions are retained as missing, because silently estimating them would introduce information not present in the source.

3.2 Provenance and retrospective weather

The local HURDAT2 archive is parsed for storm AL102023, Idalia. Each retained observation is aligned to a linearly interpolated storm latitude and longitude at its timestamp. Great-circle distance is computed using a spherical Earth radius of 3,440.065 nautical miles. This distance is a retrospective descriptive feature. The storm location on 28 August is not replaced with its later Florida landfall position.

The manifest records source filename, source byte size, stage counts, missing-field counts, sampling rules, time range, and a SHA-256 fingerprint of the derived observation file. The fingerprint is updated after anomaly columns are added. It verifies consistency of the derived artifact; it is not a cryptographic certification of the historical source archive. The source and the transformation rules must still be retained for full reproducibility.

Reproduction commands: scripts/build_dataset.py followed by scripts/train_benchmark.py. The latter can run independently using the included compact cohort.


## 3 Proposed methodology continued

3.3 Features and target construction

Within each vessel, observations are ordered by timestamp. The next reported speed becomes the target only when the interval to that observation lies between 2 and 30 minutes. Last observations and pairs outside that interval remain useful for exploration but do not enter the supervised benchmark. The resulting forecast is a variable-horizon estimate. It must not be described as a fixed five-minute or fifteen-minute prediction.

| Feature | Representation | Reason or limitation |
| --- | --- | --- |
| Current speed | Knots | Strong persistence signal; observed at prediction time. |
| Course | Sine and cosine of bearing | Preserves proximity across the 0/360-degree boundary. |
| Latitude and longitude | Decimal degrees | Geographic context; may not generalize to new regions. |
| Vessel type | Numeric AIS code | Available category cue; ordinal coding limits the linear model. |
| Storm proximity | EDA only | Retrospective best track excluded from predictive features. |

3.4 Training and held-out evaluation

A single GroupShuffleSplit with test size 0.25 and random state 42 partitions vessel identifiers. All eligible observations for one vessel remain in the same partition. The split produces 151 training vessels and 51 test vessels, with no overlap. Some of the 217 observed vessels do not have eligible target pairs, which explains why the supervised vessel counts sum to 202 rather than 217.

The training-median baseline predicts the median target speed from the training set. Persistence predicts the current speed. Ridge regression is placed in a pipeline with a scaler fitted only on training data. Random forest uses 100 trees, maximum depth 14, and minimum leaf size 8. Histogram gradient boosting uses 140 iterations, at most 20 leaf nodes, and L2 regularization of 2. These configurations are fixed; no hyperparameter search or test-based model selection is performed.

All methods are scored on the same held-out observations using MAE, RMSE, and R². The gradient-boosting model is retained for the application as a prespecified demonstration model, not because it wins every metric. Its MAE interval is estimated with 500 vessel-cluster bootstrap samples. Resampling whole vessels respects dependence among their repeated observations more closely than treating every ping as an independent sample.

3.5 Interpretation and outlier screening

Permutation importance shuffles one feature at a time in a deterministic sample of up to 2,000 held-out rows, repeating the procedure five times. The increase in MAE describes reliance of this fitted model on that feature. Correlated predictors and sampling variation can complicate interpretation; the measure is not causal and is not SHAP. Isolation Forest is separately fitted on training-cohort speed, position, and circular course features with contamination 0.03. Its flags are review cues, not verified anomaly labels.


## 3 Proposed methodology continued

3.6 Deterministic decision stages

The scenario workflow accepts a voyage distance, cruising speed, wind, significant wave height, traffic assumption, storm distance, reference fuel rate, fuel price, and carbon conversion factor. Pydantic validates ranges, disallows non-finite numbers, and rejects unknown fields. Four stages produce a structured execution trace: input validation, exposure analysis, voyage estimation, and a recommendation policy.

Exposure is the sum of four capped contributions. Wind contributes up to 30 points, waves up to 25, the traffic assumption up to 20, and proximity up to 25. The score is transparent by construction, but its weights are illustrative. No observed delay or hazard labels were used to calibrate them. A value such as 70 means 70 points on this index, not a 70 percent probability of delay.

| Quantity | Implemented expression |
| --- | --- |
| Exposure E | 30 min(wind/64, 1) + 25 min(waves/8, 1) + 0.2 traffic + 25 max(0, 1 - storm_nm/300) |
| Voyage duration H | (distance × distance_factor / speed) × (1 + 0.025 waves × weather_factor + 0.001 traffic) |
| Fuel F | (H/24) × reference_tonnes_per_day × (speed/14)³ × (1 + 0.04 waves × weather_factor) |
| CO₂ and fuel cost | CO₂ = F × carbon_factor; cost = F × fuel_price |

Maintain course uses the supplied speed and distance. Economy speed uses 80 percent of the supplied speed. The illustrative detour uses 120 percent of the distance and a weather factor of 0.55. The decision policy favors the detour at exposure of at least 60, economy speed below 35, and the baseline otherwise. These thresholds make the workflow easy to inspect; they are not learned optimal thresholds.

3.7 Persistence, interface, and defensive behavior

A saved experiment stores its validated input and complete output in SQLite together with a generated identifier and a UTC timestamp. Loading the experiment restores the recorded scenario. Database operations use parameterized queries. The CSV export respects the selected cohort filters and prefixes strings beginning with spreadsheet formula characters. React renders vessel names and analysis text as text rather than directly inserting untrusted HTML.

The API binds to the local machine in the standard launch script. The frontend uses same-origin requests in a production build and a development proxy during editing. API documentation is exposed through FastAPI. A public multi-user deployment would require authentication, authorization, rate limiting, and a persistence design beyond the current local workspace. The container and CI files prepare reproducible execution but are not evidence that a public service has been deployed.


## 4 Experimental analysis

4.1 Experimental protocol and comparison

Every method is evaluated against the same 9,985 held-out target observations from 51 unseen vessels. Training uses 27,264 examples from 151 other vessels. The test cohort is not used for scaling, fitting, or tuning. Results compare implementations under a common local protocol; they do not compare numerical claims taken from papers that used different data, target definitions, and forecasting horizons.

| Approach | MAE kn | RMSE kn | R² | Training s |
| --- | --- | --- | --- | --- |
| Persistence baseline | 0.3498 | 1.5182 | 0.8990 | 0 |
| Training median | 2.3362 | 5.3171 | -0.2392 | 0 |
| Ridge regression | 0.4368 | 1.4974 | 0.9017 | 0.015 |
| Random forest | 0.5385 | 1.5008 | 0.9013 | 1.839 |
| Gradient boosting | 0.4878 | 1.4886 | 0.9029 | 0.103 |

Table 1. Measured benchmark results. Training times are from one local execution and are not hardware-independent performance guarantees.

Persistence gives the lowest MAE at 0.3498 knots. Gradient boosting yields an MAE of 0.4878 knots, approximately 39.5 percent higher, while its RMSE is about 1.95 percent lower than persistence. Ridge regression and random forest also show slightly lower RMSE than persistence but higher MAE. The training-median baseline performs poorly, indicating that the current observation carries substantially more predictive information than a fleet-wide constant.

4.2 Why the metrics disagree

MAE assigns a linear penalty to each error. RMSE squares the errors before averaging and therefore emphasizes occasional large mistakes. A model can improve a few large misses while introducing many small deviations from otherwise stable speeds. The observed rankings are consistent with that possibility, but this aggregate table alone does not prove the detailed mechanism. Inspecting individual residuals and activity subgroups is necessary before drawing a stronger conclusion.

R² expresses squared-error improvement relative to a constant based on the test-target mean. It is not a percentage of correct predictions, and a high R² does not imply a small operational error in every case. The median baseline has negative R² because it is a poor predictor for this test distribution. The project reports all three metrics to prevent a single attractive number from becoming the whole result.

4.3 Main finding

The experiment does not support a blanket statement that machine learning improves short-horizon speed prediction. It supports a narrower conclusion: persistence is a strong average-error baseline in this cohort, and the learned methods alter the distribution of errors. For a user prioritizing MAE, persistence is the better measured option. For a user particularly concerned with large errors, the small RMSE difference motivates further evaluation, including paired uncertainty analysis and additional dates.


## 4 Experimental analysis continued

4.4 Activity and horizon subgroups

| Held-out subgroup | Rows | Persistence MAE | Boosting MAE |
| --- | --- | --- | --- |
| Stationary or slow (<0.5 kn) | 7194 | 0.0918 | 0.155 |
| Moving (>=0.5 kn) | 2791 | 1.0148 | 1.3456 |
| Short horizon (2–10 min) | 9747 | 0.356 | 0.4963 |
| Longer horizon (>10–30 min) | 238 | 0.0958 | 0.1399 |

Table 2. Subgroup errors in knots. Subgroups overlap across the activity and horizon definitions; their counts must not be added across all four rows.

Of the held-out examples, 7,194 have current speed below 0.5 knots and 2,791 are moving at or above that threshold. Persistence MAE is 0.0918 knots for the first group and 1.0148 knots for the second. The corresponding boosting values are 0.1550 and 1.3456 knots. The much larger error among moving observations indicates that the aggregate score is strongly influenced by the prevalence of stationary or slow reports.

Most targets occur within ten minutes: 9,747 examples fall in that horizon group, compared with 238 in the longer group. The longer-horizon subgroup happens to have smaller measured errors in this cohort. This is not evidence that longer-range prediction is easier. The groups contain different vessels and activity patterns, and the smaller group is especially sensitive to composition. A fixed-horizon evaluation with matched populations would be needed to isolate the effect of forecast duration.

4.5 Sampling uncertainty

For the prespecified gradient-boosting model, the 95 percent percentile interval for MAE is 0.2710–0.7543 knots across 500 vessel-cluster bootstrap samples. The interval is wider than a naive row-level analysis might suggest because many observations belong to the same vessel. Repeated reports share movement patterns and cannot safely be treated as thousands of unrelated experiments.

This interval is conditional on the chosen test cohort, observation day, target definition, and training procedure. It is not a prediction interval for an individual ship, and it does not estimate uncertainty for an entirely different season or region. The project does not claim that the slight RMSE improvement is statistically significant. A paired comparison over multiple held-out dates and vessel cohorts would be a more appropriate next experiment.

4.6 What should change next

The most informative next step is to collect more days and define an evaluation protocol before adding architecture complexity. Candidate extensions include fixed-horizon targets, short historical windows, acceleration features, and vessel-category encoding. Each extension should be compared against persistence on unchanged held-out partitions. The team should also report performance for moving vessels separately, because an excellent aggregate score on mostly stationary data can conceal the more difficult operational cases.


## 4 Experimental analysis continued

4.7 Model inspection

| Feature shuffled | Mean increase in MAE | Repeat standard deviation |
| --- | --- | --- |
| speed | 3.4249 | 0.0257 |
| course_sin | 0.0285 | 0.0033 |
| course_cos | 0.0124 | 0.0032 |
| lat | -0.0088 | 0.0016 |
| lon | 0.039 | 0.0082 |
| type_code | 0.0016 | 0.0037 |

Table 3. Held-out permutation importance for gradient boosting. Positive values indicate that shuffling worsened performance; a small negative value is possible.

Current speed dominates the measured importance, with a mean MAE increase of 3.4249 knots after shuffling. Course and longitude have much smaller positive contributions. Latitude has a slightly negative mean importance in this sampled test set. This does not establish that latitude is intrinsically harmful or that the other variables cause speed changes. Importance depends on the fitted model, correlated features, and the evaluation sample.

4.8 Exploratory findings and quality limits

The complete analytical cohort has a mean observed speed of about 2.25 knots. The dashboard separates this observation-weighted mean from distinct-vessel counts. Missing technical fields are substantial: draft is absent in 77,034 of the 122,629 selected-cohort messages before validation and resampling, while width is absent in 25,172. These gaps explain why the project does not train a fuel-consumption model or estimate vessel-specific resistance from dimensions.

A notable cleaning effect is the removal of 25,113 invalid observations before duplicate elimination. The accepted course range excludes the unknown-course sentinel and other invalid values. This improves the reliability of circular course features but changes which observations remain. Missingness and validity are therefore not merely housekeeping statistics; they affect the population on which results are reported.

The H3 layer counts distinct MMSIs in each cell across the selected cumulative window. One vessel can contribute to several cells as it moves. Summing unique-vessel counts over cells would double-count such vessels, whereas summing observation counts over cells recovers the selected message total. The automated tests check the latter conservation property. This distinction provides a useful example of why geospatial aggregation requires a clear definition of the unit being counted.

4.9 Storm context

The scatterplot links observed speed with retrospective distance to Idalia. It is an exploratory view, not a causal model of weather disruption. At this date, the storm center was near Cuba rather than at its eventual Florida landfall. Port location, vessel class, route, and activity can confound the relationship. The predictive benchmark excludes storm distance to avoid presenting retrospective best-track knowledge as if it had been an operational forecast.


## 4 Experimental analysis continued

4.10 Working demonstration and scenario evidence

The implemented workspace provides five functional views: fleet overview, EDA, scenario lab, model benchmark, and data/methodology. The browser checks exercised vessel inspection, view changes, severe-weather evaluation, experiment persistence and deletion, and mobile rendering. Backend tests cover filtering, target and split consistency, input rejection, scenario calculations, persistence, CSV export, storm alignment, and artifact fingerprint consistency.

| Verification area | Observed result |
| --- | --- |
| Backend behavioral suite | 17 tests passed in the recorded local verification. |
| Frontend build and lint | Production build and lint completed successfully. |
| Browser interactions | Seven view screenshots captured; no page errors in the scripted flow. |
| Mobile layout | 390-pixel viewport checked; no document-level horizontal overflow. |
| Dependency audit | npm audit reported zero vulnerabilities after dependency updates. |
| Offline geographic context | Bundled Natural Earth land polygons; optional online street basemap. |

These checks establish that the recorded workflow works in the tested local environment. They do not constitute a penetration test, a cross-browser certification, or a navigation safety validation. Container and CI configuration are included but are not described as executed remote infrastructure. The repository is prepared for a normal authenticated GitHub upload, with secrets and large raw files excluded.

4.11 A severe-weather scenario

The severe-weather preset uses 300 nautical miles, 14 knots, 75-knot wind, 7-metre waves, traffic assumption 70, and storm distance 40 nautical miles. With the default fuel assumptions, the exposure index is 87.55 out of 100. The policy proposes the illustrative detour. The baseline estimate is 26.68 hours and 34.15 tonnes of fuel; economy speed is 33.35 hours and 21.86 tonnes; the detour is 29.98 hours and 34.61 tonnes.

The detour therefore uses slightly more estimated fuel than the baseline in this scenario. This is an important result: lower assumed exposure does not automatically mean lower fuel consumption. The recommendation reflects the documented exposure policy, not an optimization that simultaneously minimizes time, fuel, emissions, and risk. A reviewer can inspect each contribution, compare the alternatives, and challenge the assumed distance or weather reduction.

4.12 Overall interpretation

The project is strongest when assessed as an integrated analytical workflow. Its interface makes the dataset and assumptions accessible, its benchmark demonstrates why baseline selection matters, and its scenario trace makes conditional reasoning explicit. The evidence does not support claims of verified delay avoidance, autonomous rerouting, measured fuel savings, or global forecasting performance. Keeping those claims out of the demonstration improves both technical credibility and the quality of the discussion.


## 5 Conclusion and future work

Agentic Geo-Spatial Intelligence turns a large historical AIS file into a usable and auditable maritime research workspace. The completed implementation connects real vessel exploration, geospatial aggregation, data-quality reporting, a reproducible forecasting benchmark, and transparent voyage scenarios. Its main contribution is the integration of these parts with traceable definitions and a working local interface.

The experiment demonstrates the importance of a strong baseline. Persistence achieves lower MAE than the learned models on the held-out vessel cohort, while gradient boosting has slightly lower RMSE. The difference in rankings is informative rather than inconvenient: it shows that model choice depends on the error objective and the distribution of vessel activity. The reported uncertainty interval, subgroup results, and feature inspection help explain the limits of an aggregate score.

Future work should begin with multi-day, multi-region evaluation and operationally available weather forecasts. Fixed-horizon targets and short movement histories can then be tested without changing the held-out protocol opportunistically. Verified port calls, schedules, and actual arrival outcomes are needed for delay prediction. Measured fuel use and vessel characteristics are needed for validated fuel models. Navigation-grade routing would additionally require charts, bathymetry, vessel constraints, and expert review.

The scenario workflow can be extended with sensitivity analysis, constrained optimization, and a richer audit trail. Any language-model component should explain structured evidence rather than generate unsupported numerical conclusions. For public deployment, authentication, authorization, rate limiting, and controlled persistence would be necessary. These are concrete next steps beyond the present local research scope.

The project is ready to demonstrate as a bounded research prototype. A defensible presentation should emphasize what was measured, what was assumed, and what remains unvalidated. That distinction is central to the project’s technical value.

Submission preparation: add the three team members and institutional details, read the primary papers, reproduce the results, and write the final report in accordance with the instructor’s stated AI policy.


## References

Bao, K., Bi, J., Gao, M., Sun, Y., Zhang, X., & Zhang, W. (2022). An improved ship trajectory prediction based on AIS data using MHA-BiGRU. Journal of Marine Science and Engineering, 10(6), 804. https://doi.org/10.3390/jmse10060804

Carlini, E., de Lira, V. M., Soares, A., Etemad, M., Brandoli, B., & Matwin, S. (2022). Understanding evolution of maritime networks from automatic identification system data. GeoInformatica, 26(3), 479-503. https://doi.org/10.1007/s10707-021-00451-0

Chen, X., Liu, X., Luo, Y., & Zeng, X. (2025). Exploring time-series deep learning models for ship fuel consumption prediction. Journal of Marine Science and Engineering, 13(11), 2102. https://doi.org/10.3390/jmse13112102

Filipiak, D., Węcel, K., Stróżyna, M., Michalak, M., & Abramowicz, W. (2020). Extracting maritime traffic networks from AIS data using evolutionary algorithm. Business & Information Systems Engineering, 62(5), 435-450. https://doi.org/10.1007/s12599-020-00661-0

Hague, E., Walters, A., Moscrop, A., Steel, E., Dyke, K., Hartny-Mills, L., Lomax, A., Dudley, R., Garrard, P., Hampson, J., Gorvett, S., Lightley, H., Mackie, C., Lehmann, J., Olias, S., Hilgenfeld, C., Cole, D., MacDonald-Taylor, S., Davis, C., & Siddle, B. (2025). AIS data underrepresents vessel traffic around coastal Scotland. Marine Policy, 178, 106719. https://doi.org/10.1016/j.marpol.2025.106719

Kim, Y. R., Jung, M., & Park, J. B. (2021). Development of a fuel consumption prediction model based on machine learning using ship in-service data. Journal of Marine Science and Engineering, 9(2), 137. https://doi.org/10.3390/jmse9020137

Liang, M., Weng, L., Gao, R., Li, Y., & Du, L. (2024). Unsupervised maritime anomaly detection for intelligent situational awareness using AIS data. Knowledge-Based Systems, 284, 111313. https://doi.org/10.1016/j.knosys.2023.111313

Liu, J., Li, J., & Liu, C. (2024). AIS-based kinematic anomaly classification for maritime surveillance. Ocean Engineering, 305, 118026. https://doi.org/10.1016/j.oceaneng.2024.118026

Luo, X., Zhang, M., Han, Y., Yan, R., & Wang, S. (2025). Ship fuel consumption prediction based on transfer learning: Models and applications. Engineering Applications of Artificial Intelligence, 141, 109769. https://doi.org/10.1016/j.engappai.2024.109769


## References continued

Ma, Q., Tang, H., Liu, C., Zhang, M., Zhang, D., Liu, Z., & Zhang, L. (2024). A big data analytics method for the evaluation of maritime traffic safety using automatic identification system data. Ocean & Coastal Management, 251, 107077. https://doi.org/10.1016/j.ocecoaman.2024.107077

Melo, R. F., Figueiredo, N. M. d., Tobias, M. S. G., & Afonso, P. (2024). A machine learning predictive model for ship fuel consumption. Applied Sciences, 14(17), 7534. https://doi.org/10.3390/app14177534

Park, J., Jeong, J., & Park, Y. (2021). Ship trajectory prediction based on Bi-LSTM using spectral-clustered AIS data. Journal of Marine Science and Engineering, 9(9), 1037. https://doi.org/10.3390/jmse9091037

Ramos, J., Drakeford, B., Costa, J., Madiedo, A., & Leitão, F. (2025). Tracking tourism waves: Insights from automatic identification system (AIS) data on maritime–coastal activities. Tourism and Hospitality, 6(2), 99. https://doi.org/10.3390/tourhosp6020099

Ribeiro da Silva, J. N., Santos, T. A., & Teixeira, A. P. (2024). Methodology for predicting maritime traffic ship emissions using automatic identification system data. Journal of Marine Science and Engineering, 12(2), 320. https://doi.org/10.3390/jmse12020320

Ribeiro, C. V., Paes, A., & Oliveira, D. d. (2023). AIS-based maritime anomaly traffic detection: A review. Expert Systems with Applications, 231, 120561. https://doi.org/10.1016/j.eswa.2023.120561

Skat-Rørdam, H. V., Kjærsgaard, R. D., Hovad, E., & Clemmensen, L. K. (2025). SeauAIS: A self-explainable autoencoder with AIS-based maritime anomaly detection. Ocean Engineering, 341, 122656. https://doi.org/10.1016/j.oceaneng.2025.122656

Stach, T., Kinkel, Y., Constapel, M., & Burmeister, H. C. (2023). Maritime anomaly detection for vessel traffic services: A survey. Journal of Marine Science and Engineering, 11(6), 1174. https://doi.org/10.3390/jmse11061174


## References continued

Wang, C., Han, P., Zhu, M., Osen, O., Zhang, H., & Li, G. (2024). AIS data-based hybrid predictor for short-term ship trajectory prediction considering uncertainties. IEEE Transactions on Intelligent Transportation Systems, 25(12), 20268-20279. https://doi.org/10.1109/tits.2024.3461210

Wei, Z., Meng, X., Li, X., Zhang, X., & Gao, Y. (2022). Vessel manoeuvring hot zone recognition and traffic analysis with AIS data. Ocean Engineering, 266, 112858. https://doi.org/10.1016/j.oceaneng.2022.112858

Wei, Z., Xie, X., & Zhang, X. (2020). AIS trajectory simplification algorithm considering ship behaviours. Ocean Engineering, 216, 108086. https://doi.org/10.1016/j.oceaneng.2020.108086

Wolsing, K., Roepert, L., Bauer, J., & Wehrle, K. (2022). Anomaly detection in maritime AIS tracks: A review of recent approaches. Journal of Marine Science and Engineering, 10(1), 112. https://doi.org/10.3390/jmse10010112

Yang, H., Sun, Z., Han, P., & Ma, M. (2024). Data-driven prediction of ship fuel oil consumption based on machine learning models considering meteorological factors. Proceedings of the Institution of Mechanical Engineers, Part M: Journal of Engineering for the Maritime Environment, 238(3), 483-502. https://doi.org/10.1177/14750902231210047

Young, D. L., Scully, B. M., & Chambers, K. F. (2022). Resilience-focused analysis of the United States maritime transportation system using automatic identification system data. Transportation Research Record: Journal of the Transportation Research Board, 2676(7), 726-742. https://doi.org/10.1177/03611981221082561

Zaman, B., Marijan, D., & Kholodna, T. (2023). Interpolation-based inference of vessel trajectory waypoints from sparse AIS data in maritime. Journal of Marine Science and Engineering, 11(3), 615. https://doi.org/10.3390/jmse11030615

Zhu, M., Han, P., Wang, C., Skulstad, R., Zhang, H., & Li, G. (2025). An AIS data-driven hybrid approach to ship trajectory prediction. IEEE Transactions on Systems, Man, and Cybernetics: Systems, 55(1), 96-109. https://doi.org/10.1109/tsmc.2024.3458469
