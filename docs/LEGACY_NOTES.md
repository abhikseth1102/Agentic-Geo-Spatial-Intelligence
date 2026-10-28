# Changes from the original prototype

The old `Review_1_Notes.md` and `Dataset_Preview.md` describe the earlier prototype. Do not use them as the current project's technical evidence.

| Earlier claim or behavior | Current correction |
|---|---|
| 30,000 vessels | Counts distinguish messages from unique MMSI identifiers; actual derived cohort is 217 vessels |
| Synthetic weather-based labels described as actual delay risk | Prediction target is measured next-observed speed; scenarios explicitly hypothetical |
| Random hexagons | Actual H3 cells and observed unique-vessel counts |
| Feature importances called SHAP | Held-out permutation importance with its actual definition |
| Fixed Florida landfall location used for 28 August weather | Timestamp-aligned retrospective Idalia best track |
| A fabricated 80% fallback on prediction error | Explicit API error or unavailable estimate |
| Fixed 42% fuel savings and under-5% reroute risk | Transparent alternative calculations without guaranteed savings |
| Arbitrary rerouting through a different region | No navigation-grade route claim; hypothetical corridor trade-offs |
| Rendering alert HTML directly | React-rendered text and validated data |

Historical scripts remain for traceability. The current launch path is `backend.main` and `frontend/src/App.jsx`; build/train scripts are in `scripts/`.
