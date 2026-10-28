"""Create the project reference pack from measured results and verified metadata."""

from pathlib import Path
import json, re, html, csv
from xml.sax.saxutils import escape
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/documents"
OUT.mkdir(parents=True, exist_ok=True)
REFS = json.loads((ROOT / "docs/research/references.json").read_text(encoding="utf-8"))
M = json.loads((ROOT / "data/atlas/manifest.json").read_text())
B = json.loads((ROOT / "data/atlas/benchmark.json").read_text())
for name, file in [
    ("TimesLocal", "times.ttf"),
    ("TimesLocal-Bold", "timesbd.ttf"),
    ("TimesLocal-Italic", "timesi.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, "C:/Windows/Fonts/" + file))
pdfmetrics.registerFontFamily(
    "TimesLocal",
    normal="TimesLocal",
    bold="TimesLocal-Bold",
    italic="TimesLocal-Italic",
    boldItalic="TimesLocal-Bold",
)
INK = colors.HexColor("#243b46")
TEAL = colors.HexColor("#218773")
LIGHT = colors.HexColor("#eef5f2")
styles = {
    "body": ParagraphStyle(
        "body",
        fontName="TimesLocal",
        fontSize=11,
        leading=13,
        spaceAfter=9,
        alignment=TA_JUSTIFY,
        textColor=INK,
    ),
    "h1": ParagraphStyle(
        "h1",
        fontName="TimesLocal-Bold",
        fontSize=20,
        leading=24,
        spaceAfter=18,
        textColor=INK,
    ),
    "h2": ParagraphStyle(
        "h2",
        fontName="TimesLocal-Bold",
        fontSize=12.5,
        leading=16,
        spaceBefore=11,
        spaceAfter=8,
        textColor=INK,
    ),
    "caption": ParagraphStyle(
        "caption",
        fontName="TimesLocal-Italic",
        fontSize=9,
        leading=11,
        spaceBefore=6,
        spaceAfter=13,
        textColor=colors.HexColor("#667c80"),
    ),
    "small": ParagraphStyle(
        "small",
        fontName="TimesLocal",
        fontSize=9,
        leading=11,
        spaceAfter=7,
        textColor=INK,
    ),
    "ref": ParagraphStyle(
        "ref",
        fontName="TimesLocal",
        fontSize=10,
        leading=12,
        spaceAfter=14,
        leftIndent=18,
        firstLineIndent=-18,
        textColor=INK,
    ),
    "handbook": ParagraphStyle(
        "handbook",
        fontName="TimesLocal",
        fontSize=10.5,
        leading=12.5,
        spaceAfter=7,
        alignment=TA_JUSTIFY,
        textColor=INK,
    ),
    "cell": ParagraphStyle(
        "cell", fontName="TimesLocal", fontSize=9, leading=11, textColor=INK
    ),
}


def p(text, style="body"):
    return Paragraph(text, styles[style])


def year(r):
    return r.get("published-print", r.get("published", r.get("issued")))["date-parts"][
        0
    ][0]


def cite(i):
    r = REFS[i - 1]
    a = r["author"]
    names = [x.get("family", x.get("name", "Unknown")) for x in a]
    name = names[0] + " et al." if len(names) > 2 else " and ".join(names)
    return escape(f"{name} ({year(r)})")


def authors(r):
    arr = []
    for a in r["author"][:20]:
        initials = " ".join(
            w[0] + "." for w in re.split(r"[\s-]+", a.get("given", "")) if w
        )
        arr.append(
            a.get("family", a.get("name", "")) + (", " + initials if initials else "")
        )
    return ", ".join(arr[:-1]) + ", & " + arr[-1] if len(arr) > 1 else arr[0]


def sentence_case(s):
    protected = [
        "AIS",
        "MHA-BiGRU",
        "Bi-LSTM",
        "SEAuAIS",
        "United States",
        "Scotland",
        "Amazon",
    ]
    result = s.lower()
    for term in protected:
        result = re.sub(re.escape(term.lower()), term, result)
    result = result[0].upper() + result[1:]
    result = re.sub(r"(:\s+)([a-z])", lambda m: m[1] + m[2].upper(), result)
    return result


def apa(r):
    journal = html.unescape(r["container-title"][0])
    title = sentence_case(html.unescape(r["title"][0]))
    volume = r.get("volume", "")
    issue = "(" + r["issue"] + ")" if r.get("issue") else ""
    pages = r.get("page", r.get("article-number", ""))
    tail = f", {pages}" if pages else ""
    return (
        escape(f"{authors(r)} ({year(r)}). {title}. ")
        + f'<i>{escape(journal)}, {escape(volume)}</i>{escape(issue+tail)}. <link href="https://doi.org/{r["DOI"]}" color="#218773">https://doi.org/{escape(r["DOI"])}</link>'
    )


def table(headers, rows, widths=None):
    data = [[p(escape(str(x)), "cell") for x in headers]] + [
        [p(escape(str(x)), "cell") for x in row] for row in rows
    ]
    t = Table(
        data,
        colWidths=widths or [475 / len(headers)] * len(headers),
        repeatRows=1,
        hAlign="LEFT",
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#cdded8")),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#e5ece9")),
            ]
        )
    )
    return t


pages = []


def page(title, *content):
    pages.append((title, list(content)))


def text(s):
    return p(s)


def heading(s):
    return p(s, "h2")


def flow_diagram():
    d = Drawing(475, 180)
    nodes = [
        ("Historical AIS", 0, 115),
        ("Quality audit", 165, 115),
        ("Derived cohort", 330, 115),
        ("HURDAT2 track", 0, 25),
        ("Models and EDA", 165, 25),
        ("React workspace", 330, 25),
    ]
    for label, x, y in nodes:
        d.add(
            Rect(
                x,
                y,
                145,
                45,
                fillColor=LIGHT,
                strokeColor=colors.HexColor("#bbd3c9"),
                radius=5,
            )
        )
        d.add(
            String(
                x + 72.5,
                y + 19,
                label,
                textAnchor="middle",
                fontName="TimesLocal-Bold",
                fontSize=11,
                fillColor=INK,
            )
        )
    for x1, y1, x2, y2 in [
        (145, 137, 165, 137),
        (310, 137, 330, 137),
        (72, 70, 180, 115),
        (402, 115, 237, 70),
        (310, 47, 330, 47),
    ]:
        d.add(Line(x1, y1, x2, y2, strokeColor=TEAL, strokeWidth=1.4))
    return d


page(
    "Agentic Geo-Spatial Intelligence",
    p("Technical reference draft for project review", "caption"),
    table(
        ["Team member", "Name", "Registration number"],
        [
            ["1", "________________________", "___________________"],
            ["2", "________________________", "___________________"],
            ["3", "________________________", "___________________"],
        ],
        [65, 230, 180],
    ),
    Spacer(1, 13),
    heading("Abstract"),
    text(
        "Maritime data can support useful operational questions only when the observations, assumptions, and evaluation procedures are made explicit. This project develops a local research workspace for historical vessel analysis, short-horizon speed estimation, and explainable voyage scenarios. The implementation combines a React interface with a FastAPI service, a reproducible Python data pipeline, actual H3 spatial indexing, and SQLite experiment storage. Its objective is to make an end-to-end analytical process inspectable, rather than to claim autonomous navigation or verified arrival-delay prediction."
    ),
    text(
        "The source AIS file contains 9,306,345 messages from 28 August 2023. A Gulf of Mexico and Florida bounding box, deterministic vessel selection, validation, duplicate removal, and five-minute resampling produce 37,843 observations from 217 distinct vessel identifiers. Hurricane Idalia positions are aligned retrospectively using the local NHC HURDAT2 archive. The interface supports vessel search, cumulative hourly replay, trajectory inspection, distributions, correlations, missing-value analysis, and geographic density. An offline coastline provides geographic context without requiring API credentials."
    ),
    text(
        "The forecasting experiment estimates the next observed speed over intervals of 2–30 minutes. A vessel-disjoint split contains 27,264 training examples from 151 vessels and 9,985 test examples from 51 vessels. Persistence, a training-median baseline, ridge regression, random forest, and gradient boosting are evaluated with MAE, RMSE, and R². Persistence achieves the lowest MAE, 0.3498 knots; gradient boosting produces a slightly lower RMSE, 1.4886 knots compared with 1.5182 knots. These results show why a complex model should be judged against a strong operational baseline, not assumed to be superior."
    ),
    text(
        "A separate scenario workflow validates inputs, calculates a documented exposure index, compares three voyage assumptions, and records a human-review recommendation. Fuel and carbon estimates are illustrative calculations, not measured savings. The main contribution is an integrated and reproducible analytical workflow with explicit limits. Multi-day evaluation, validated operational weather inputs, and actual voyage outcomes are necessary before stronger predictive or operational claims can be made."
    ),
    text(
        "<b>Keywords:</b> automatic identification system; exploratory data analysis; maritime intelligence; geospatial analytics; vessel forecasting; explainable decisions; data quality."
    ),
    p(
        "The supplied report instructions prohibit AI tools. This reference material supports study and verification; the submitted report must be student-authored or explicitly permitted by the instructor.",
        "small",
    ),
)

page(
    "1 Introduction",
    heading("1.1 From vessel messages to useful evidence"),
    text(
        "A ship-position dataset appears straightforward: each row describes a vessel at a place and time. In practice, the analytical problem is more difficult. One vessel can transmit many thousands of messages, reporting intervals vary, and static fields may be incomplete. A dense cluster of points can therefore represent frequent reporting, repeated stationary observations, or many different vessels. These interpretations have different implications for an analysis of traffic. The project begins by treating message counts, distinct-vessel counts, and temporal coverage as separate quantities."
    ),
    text(
        "Automatic Identification System messages provide identity, position, speed over ground, course over ground, and other vessel information. Historical archives make it possible to study movement at a scale that would be difficult to observe manually. However, the broadcast record is not a complete inventory of maritime activity. Coverage depends on carriage requirements, reception, collection practices, and data quality. The NOAA MarineCadastre source is suitable for historical exploration, but the presence of an official source does not remove the need for validation or justify assumptions about unobserved vessels."
    ),
    text(
        "This project focuses on a historical Gulf of Mexico and Florida case study during the formation of Hurricane Idalia. The weather context makes it tempting to infer disruption from proximity alone. That inference would be premature. AIS speed is affected by port operations, vessel purpose, maneuvering, route choices, and reporting quality. The supplied files do not contain a verified delay outcome, an expected arrival schedule, or measured fuel consumption. Consequently, the implemented prediction task is limited to an outcome actually observable in the data: the next reported speed."
    ),
    heading("1.2 Why an integrated workspace is useful"),
    text(
        "Separate scripts can calculate statistics, train models, and draw maps, yet they often leave the reader to connect those results manually. An integrated workspace makes the relationship visible. A vessel selected from a directory can be inspected on the map; its speed history can be compared with a model estimate; the dataset audit explains which observations were retained; and the benchmark identifies how the estimate was evaluated. This reduces the gap between an attractive demonstration and an analysis that can be questioned and reproduced."
    ),
    text(
        "The interface deliberately separates three forms of evidence. Historical views display observations. The benchmark displays model estimates evaluated against held-out observations. The scenario lab displays calculations conditional on hypothetical inputs. Keeping these categories separate is a design requirement, because a numerical result can look authoritative even when it is only an assumption. The distinction is repeated in labels, source notes, model explanations, and the review guide."
    ),
    heading("1.3 Intended use"),
    text(
        "The intended user is a student or analyst exploring how maritime data, machine learning, and decision support fit together. The system is designed for local demonstration and research. It does not connect to a live AIS feed, issue navigation commands, or certify a route as safe. Its value lies in making a bounded investigation complete and inspectable: source data, preprocessing, exploratory questions, baseline comparisons, uncertainty, and limitations can all be examined in one workspace."
    ),
)

page(
    "1 Introduction continued",
    heading("1.4 Research questions and evaluation criteria"),
    text(
        "The central forecasting question is whether a small supervised model can estimate the next observed vessel speed more accurately than carrying the current speed forward. This question is deliberately narrower than arrival prediction or autonomous routing. It has a measurable target in the available files, can be tested without fabricating labels, and exposes the importance of a meaningful baseline. The experiment also asks whether the answer changes when error is measured by average absolute deviation or by squared-error sensitivity to large mistakes."
    ),
    table(
        ["Question", "Evidence in the implementation"],
        [
            (
                "What remains after cleaning and sampling?",
                "Manifest counts, missingness audit, fingerprint, deterministic extraction rules.",
            ),
            (
                "How does movement vary across the cohort?",
                "Speed histogram, hourly counts, vessel classes, trajectories, H3 density.",
            ),
            (
                "Does a learned model improve next-speed estimates?",
                "Five approaches evaluated on the same held-out vessel cohort.",
            ),
            (
                "What information drives model behavior?",
                "Permutation importance on held-out observations and subgroup error tables.",
            ),
            (
                "How do voyage assumptions change outcomes?",
                "Scenario contribution chart, time/fuel/CO₂ comparison, persistent experiment history.",
            ),
        ],
        [200, 275],
    ),
    Spacer(1, 12),
    text(
        "The system is evaluated on both analytical and software criteria. Analytical criteria include a defined target, separation of train and test vessels, comparable metrics, and a clear account of the dataset boundaries. Software criteria include input validation, consistent filtering, correct units, reproducible execution, persistent scenario history, and a usable interface. A chart is considered successful only when the underlying API values and selected filters agree."
    ),
    heading("1.5 Scope and exclusions"),
    text(
        "The source contains one day of U.S. AIS reports. The analytical cohort restricts latitude to 20–35 degrees north and longitude to 90–75 degrees west. A deterministic modulo rule retains a subset of MMSIs, and a five-minute bin keeps the first valid report per vessel. This choice makes a laptop demonstration manageable while retaining trajectories. It does not create a balanced sample across ship types, ports, or activity levels. Results should therefore be described as properties of the extracted cohort."
    ),
    text(
        "No ground-truth hazard labels are supplied. The anomaly layer identifies unusual feature combinations and must be interpreted as a screening tool. Likewise, the scenario lab does not solve a constrained sea-route optimization problem. It compares a baseline voyage, a lower-speed voyage, and a hypothetical longer corridor with reduced exposure. Bathymetry, land avoidance, vessel draft limits, traffic separation schemes, and navigational regulations are outside the implemented model."
    ),
    text(
        "The word agentic refers to an inspectable sequence of bounded decision stages. The current stages are deterministic and do not call a language model. This design keeps the prototype reproducible and removes dependency on external AI credentials. A future language-model explanation layer would need to cite the same structured calculations rather than invent additional numerical claims."
    ),
)

page(
    "1 Introduction continued",
    heading("1.6 System contribution and architecture"),
    flow_diagram(),
    p(
        "Figure 1. Data preparation, retrospective context, model evaluation, and the user workspace form one inspectable workflow.",
        "caption",
    ),
    text(
        "The implementation contributes a coherent research artifact rather than a new forecasting algorithm. Its analytical contribution is the alignment of a real dataset, a defensible target, reproducible preprocessing, and baseline-aware evaluation. Its engineering contribution is the connection of those elements to a usable frontend with local persistence and transparent scenario traces. These contributions can be demonstrated directly and do not depend on claims of state-of-the-art accuracy."
    ),
    text(
        "The data preparation script scans the raw CSV in chunks to avoid loading the entire source file at once. It writes a compact observation table and a manifest. The model script consumes that derived table, generates a vessel-disjoint experiment, and records results in a machine-readable benchmark file. The API loads these artifacts at startup. The React client requests summaries, filtered vessel lists, trajectories, and scenario evaluations through documented endpoints."
    ),
    text(
        "The map uses a bundled Natural Earth coastline by default, allowing the main geographic view to work without tile-service credentials. Optional OpenStreetMap tiles provide finer visual context when a network connection is available. H3 cells are computed from observed coordinates, not randomly drawn. Selecting a vessel changes the displayed trajectory, while the hourly control restricts the cumulative historical window. Each marker is the latest available report for its vessel, not a claim that all ships were observed at one simultaneous instant."
    ),
    heading("1.7 Reproducibility as a design choice"),
    text(
        "The repository retains the derived cohort, preprocessing description, fixed random seed, model configuration, software versions, and a SHA-256 fingerprint. Large raw archives and local scenario history are excluded from version control. A new environment can train the benchmark from the compact data without re-downloading the raw archive. Recreating the exact extraction requires the original AIS and HURDAT2 files, which are already present in the local project folder."
    ),
    text(
        "The report proceeds from prior research to the implemented methodology and then to measured results. Published papers motivate design choices and future directions; their published metrics are not placed beside the local metrics as if they were directly comparable. The local comparison uses one dataset, one target, and one held-out split for every implemented approach. That common experimental setting is essential for a meaningful results table."
    ),
)

page(
    "2 Related work and literature survey",
    heading("2.1 Prediction from AIS sequences"),
    text(
        f"{cite(2)} describe a trajectory-prediction architecture combining multi-head attention with a bidirectional recurrent unit. {cite(3)} combine trajectory clustering with a bidirectional LSTM. Their publisher abstracts motivate the use of historical sequences and movement patterns, whereas the current project intentionally starts with a compact single-observation feature set. These are different tasks and model capacities; no performance equivalence is implied."
    ),
    text(
        "Sequence methods are a plausible next step when a sufficiently long and carefully split trajectory dataset is available. They also introduce decisions about sequence length, interpolation, padding, observation gaps, and vessel identity. A larger architecture does not remove these data-design choices. The current benchmark establishes a transparent baseline before introducing that additional complexity. The observed strength of persistence makes this baseline especially important."
    ),
    text(
        f"The records for {cite(1)} and {cite(5)} identify hybrid AIS predictors, including explicit attention to uncertainty in the latter title. Their bibliographic metadata were verified, but full experimental details were not available in the retrieved records. They are included as targeted reading for future model development. Their results are not summarized numerically or treated as evidence that a hybrid model would improve this project’s cohort."
    ),
    heading("2.2 Sampling and trajectory representation"),
    text(
        f"{cite(24)} discuss the irregular timing of AIS reports and study interpolation for waypoint inference. That issue directly affects the definition of a prediction horizon. This project retains observed reports after five-minute binning and predicts the next available speed only when the interval lies between 2 and 30 minutes. It does not silently convert irregular observations into a fixed 15-minute target."
    ),
    text(
        f"Trajectory simplification is another relevant preprocessing topic, represented by {cite(4)}. The present pipeline uses an explicitly documented binning rule rather than claiming behavior-preserving simplification. Binning reduces repeated reports and computation, but can suppress brief maneuvers. The first valid report in a bin is retained; the rule therefore changes the observational resolution and must be reported alongside model results."
    ),
    table(
        ["Research direction", "Relation to this project", "Boundary"],
        [
            (
                "Recurrent and attention-based prediction",
                "Motivates future sequence features",
                "Not implemented or benchmarked locally.",
            ),
            (
                "Hybrid predictors and uncertainty",
                "Useful follow-up literature",
                "Metadata verified; no imported performance claims.",
            ),
            (
                "Sparse-track interpolation",
                "Clarifies variable observation horizons",
                "No imputed speed targets are created.",
            ),
            (
                "Trajectory simplification",
                "Highlights sampling trade-offs",
                "Five-minute binning is not behavior-preserving by proof.",
            ),
        ],
        [130, 175, 170],
    ),
    Spacer(1, 12),
    text(
        "The literature therefore supports a staged development strategy: first make the data and baseline defensible, then evaluate richer temporal models on an unchanged or carefully redesigned protocol. A future comparison should retain vessel-disjoint testing and add later-date evaluation. Without those controls, additional model complexity could improve apparent accuracy while leaving deployment performance uncertain."
    ),
)

page(
    "2 Related work continued",
    heading("2.3 Anomaly detection and the meaning of unusual"),
    text(
        f"{cite(8)} survey 44 approaches to anomalies in maritime AIS tracks. Their abstract emphasizes the variety of anomaly types and the limitations of existing approaches. {cite(25)} place anomaly detection in the setting of vessel traffic services and decision-support tools. Together these sources motivate separating a statistical alert from an operational conclusion."
    ),
    text(
        "An unusual movement can reflect legitimate vessel function, environmental conditions, a reporting error, or genuinely concerning behavior. A speed that is ordinary for a passenger ship may be unusual in a cohort dominated by slowly moving pleasure craft. Position-based features also make rarity dependent on the region represented in training. The project therefore labels anomaly results as review suggestions. It does not assign legal, safety, or security meaning to an Isolation Forest flag."
    ),
    text(
        f"The wider reading set includes the review by {cite(6)}, an unsupervised situational-awareness study by {cite(9)}, and kinematic anomaly classification by {cite(10)}. {cite(7)} identify a self-explainable autoencoder approach. The latter records were verified bibliographically; detailed methods and performance are not reconstructed from their titles. They define useful categories for a fuller student-led literature review: reconstruction error, unsupervised scoring, kinematic features, and explanation."
    ),
    heading("2.4 Spatial patterns and traffic networks"),
    text(
        f"{cite(22)} describe a network-extraction process using maneuvering points, waypoint discovery, and edge construction. This provides a useful distinction between a traffic-density map and a route graph. The H3 layer in the current application aggregates observed vessel presence within cells. It does not infer a graph of navigable connections or solve routing over those connections."
    ),
    text(
        f"{cite(13)} use MarineCadastre data to investigate a network of U.S. ports and regional connectivity. Their work supports the broader relevance of vessel movement to transport-system analysis. The present case study is more local and descriptive: it does not build a port network, calculate resilience, or attribute observed movement to disruption. Those analyses would require explicit port definitions and additional temporal evidence."
    ),
    text(
        f"The reading list also includes maritime-network evolution ({cite(11)}), maneuvering hot zones ({cite(23)}), and traffic-safety analytics ({cite(15)}). These are relevant extensions, but the implementation does not claim to reproduce them. H3 density is presented as cumulative distinct-vessel presence, with resolution and time window visible to the user."
    ),
    heading("2.5 Practical implication"),
    text(
        "The common lesson is that the analytical unit must match the question. A message, a vessel, a trajectory, a port call, and a network edge are different objects. Counting messages may be useful for data-volume planning; counting vessels is more appropriate for describing observed fleet composition. Similarly, a statistical outlier score answers a different question from a labeled anomaly classifier. The dashboard preserves these distinctions so that the demonstration can be explained without overstating its capabilities."
    ),
)

page(
    "2 Related work continued",
    heading("2.6 Fuel models require fuel observations"),
    text(
        f"{cite(19)} study fuel-consumption models using in-service data from a container ship. {cite(20)} combine voyage and meteorological information when comparing fuel-prediction models. Their abstracts establish an important requirement: a validated fuel predictor depends on relevant operational measurements, not just coordinates and an assumed relationship."
    ),
    text(
        f"{cite(16)} examine machine-learning approaches for vessel fuel consumption in the Amazon region. {cite(17)} examine time-series architectures for the same broader prediction problem. {cite(18)} identify transfer learning as another approach. These studies define possible future work when measured fuel use and vessel characteristics become available. Their published accuracy values are not transferable to the AIS-only cohort used here."
    ),
    text(
        f"{cite(12)} describe an AIS-based emission-assessment methodology that uses vessel technical and operational characteristics. The present scenario model is much simpler. It converts an assumed fuel amount into CO₂ using a configurable carbon factor, with 3.114 tonnes of CO₂ per tonne of residual fuel as the default. This is a conditional engineering calculation. It does not estimate a validated regional emission inventory or measured environmental savings."
    ),
    heading("2.7 Coverage and context"),
    text(
        f"The record for {cite(21)} explicitly concerns AIS underrepresentation around coastal Scotland. Its geographic finding should not be copied as a numerical correction for the Gulf cohort. Instead, it highlights a question that this study must acknowledge: which vessels and activities are missing from a broadcast-derived dataset? {cite(14)} use AIS in a coastal tourism setting, illustrating that the meaning of vessel activity depends on the application and vessel population."
    ),
    text(
        "In the current cohort, pleasure vessels form a large share of distinct identifiers, and many observations have low speed. Neither fact can be generalized to all Gulf shipping from this deterministic subset. Missing draft, width, and navigation-status fields further limit analyses requiring technical vessel properties. This motivates retaining missing values visibly rather than filling them with plausible-looking numbers."
    ),
    heading("2.8 Gap addressed by the project"),
    text(
        "The project addresses an educational and engineering gap between isolated analytical methods and an inspectable research demonstration. It combines data lineage, exploratory views, a common benchmark, explicit scenario assumptions, and a usable interface. It does not fill the broader research gaps of navigation-grade routing, validated delay forecasting, or fuel prediction from operational measurements. Those remain future tasks requiring different data and validation."
    ),
    text(
        "The bibliography contains 25 journal records published from 2020 onward, exceeding the required minimum of 15 recent papers. Metadata were retrieved from Crossref; publisher abstracts were reviewed when present. Entries without accessible abstracts are marked in the reading matrix as metadata-only. Before writing the final student-authored literature review, the team should read the selected full papers, verify their experimental setups, and revise the synthesis accordingly. A verified reference is not a substitute for reading a paper."
    ),
)

page(
    "3 Proposed methodology",
    heading("3.1 Source extraction and auditable cleaning"),
    text(
        "The source file is streamed in 250,000-row chunks. The pipeline selects a geographic region, keeps vessel identifiers satisfying MMSI modulo 13 equals zero, validates observations, removes duplicate identifier–timestamp pairs, and retains the first valid report per five-minute vessel bin. The modulo rule is deterministic and simple to reproduce. It is not a random probability sample or an attempt to balance classes."
    ),
    table(
        ["Stage", "Count", "Interpretation"],
        [
            ("Entire raw file", f'{M["raw_rows"]:,}', "All messages scanned."),
            (
                "Geographic subset",
                f'{M["region_rows"]:,}',
                "Messages within the Gulf/Florida box.",
            ),
            (
                "Vessel cohort",
                f'{M["cohort_rows"]:,}',
                "Messages from selected identifiers.",
            ),
            (
                "Invalid observations removed",
                f'{M["invalid_rows"]:,}',
                "Time, speed, course, or identity invalid.",
            ),
            (
                "Duplicate pairs removed",
                str(M["duplicate_rows"]),
                "Repeated vessel and timestamp.",
            ),
            (
                "Removed by five-minute binning",
                f'{M["resampled_rows_removed"]:,}',
                "Repeated valid reports within bins.",
            ),
            (
                "Retained observations",
                f'{M["observations"]:,}',
                "Final analytical table.",
            ),
            ("Distinct vessels", str(M["vessels"]), "Unique MMSIs in retained data."),
        ],
        [175, 80, 220],
    ),
    Spacer(1, 12),
    text(
        "The validation range accepts speeds from 0 to 60 knots and courses from 0 inclusive to 360 exclusive. Unknown or invalid courses are removed, which can disproportionately exclude stationary or poorly reported vessels. Missing names receive an explicit unnamed-vessel label. Missing vessel-type codes are assigned to the Other category. Missing technical dimensions are retained as missing, because silently estimating them would introduce information not present in the source."
    ),
    heading("3.2 Provenance and retrospective weather"),
    text(
        "The local HURDAT2 archive is parsed for storm AL102023, Idalia. Each retained observation is aligned to a linearly interpolated storm latitude and longitude at its timestamp. Great-circle distance is computed using a spherical Earth radius of 3,440.065 nautical miles. This distance is a retrospective descriptive feature. The storm location on 28 August is not replaced with its later Florida landfall position."
    ),
    text(
        "The manifest records source filename, source byte size, stage counts, missing-field counts, sampling rules, time range, and a SHA-256 fingerprint of the derived observation file. The fingerprint is updated after anomaly columns are added. It verifies consistency of the derived artifact; it is not a cryptographic certification of the historical source archive. The source and the transformation rules must still be retained for full reproducibility."
    ),
    p(
        "Reproduction commands: scripts/build_dataset.py followed by scripts/train_benchmark.py. The latter can run independently using the included compact cohort.",
        "caption",
    ),
)

page(
    "3 Proposed methodology continued",
    heading("3.3 Features and target construction"),
    text(
        "Within each vessel, observations are ordered by timestamp. The next reported speed becomes the target only when the interval to that observation lies between 2 and 30 minutes. Last observations and pairs outside that interval remain useful for exploration but do not enter the supervised benchmark. The resulting forecast is a variable-horizon estimate. It must not be described as a fixed five-minute or fifteen-minute prediction."
    ),
    table(
        ["Feature", "Representation", "Reason or limitation"],
        [
            (
                "Current speed",
                "Knots",
                "Strong persistence signal; observed at prediction time.",
            ),
            (
                "Course",
                "Sine and cosine of bearing",
                "Preserves proximity across the 0/360-degree boundary.",
            ),
            (
                "Latitude and longitude",
                "Decimal degrees",
                "Geographic context; may not generalize to new regions.",
            ),
            (
                "Vessel type",
                "Numeric AIS code",
                "Available category cue; ordinal coding limits the linear model.",
            ),
            (
                "Storm proximity",
                "EDA only",
                "Retrospective best track excluded from predictive features.",
            ),
        ],
        [110, 155, 210],
    ),
    Spacer(1, 12),
    heading("3.4 Training and held-out evaluation"),
    text(
        "A single GroupShuffleSplit with test size 0.25 and random state 42 partitions vessel identifiers. All eligible observations for one vessel remain in the same partition. The split produces 151 training vessels and 51 test vessels, with no overlap. Some of the 217 observed vessels do not have eligible target pairs, which explains why the supervised vessel counts sum to 202 rather than 217."
    ),
    text(
        "The training-median baseline predicts the median target speed from the training set. Persistence predicts the current speed. Ridge regression is placed in a pipeline with a scaler fitted only on training data. Random forest uses 100 trees, maximum depth 14, and minimum leaf size 8. Histogram gradient boosting uses 140 iterations, at most 20 leaf nodes, and L2 regularization of 2. These configurations are fixed; no hyperparameter search or test-based model selection is performed."
    ),
    text(
        "All methods are scored on the same held-out observations using MAE, RMSE, and R². The gradient-boosting model is retained for the application as a prespecified demonstration model, not because it wins every metric. Its MAE interval is estimated with 500 vessel-cluster bootstrap samples. Resampling whole vessels respects dependence among their repeated observations more closely than treating every ping as an independent sample."
    ),
    heading("3.5 Interpretation and outlier screening"),
    text(
        "Permutation importance shuffles one feature at a time in a deterministic sample of up to 2,000 held-out rows, repeating the procedure five times. The increase in MAE describes reliance of this fitted model on that feature. Correlated predictors and sampling variation can complicate interpretation; the measure is not causal and is not SHAP. Isolation Forest is separately fitted on training-cohort speed, position, and circular course features with contamination 0.03. Its flags are review cues, not verified anomaly labels."
    ),
)

page(
    "3 Proposed methodology continued",
    heading("3.6 Deterministic decision stages"),
    text(
        "The scenario workflow accepts a voyage distance, cruising speed, wind, significant wave height, traffic assumption, storm distance, reference fuel rate, fuel price, and carbon conversion factor. Pydantic validates ranges, disallows non-finite numbers, and rejects unknown fields. Four stages produce a structured execution trace: input validation, exposure analysis, voyage estimation, and a recommendation policy."
    ),
    text(
        "Exposure is the sum of four capped contributions. Wind contributes up to 30 points, waves up to 25, the traffic assumption up to 20, and proximity up to 25. The score is transparent by construction, but its weights are illustrative. No observed delay or hazard labels were used to calibrate them. A value such as 70 means 70 points on this index, not a 70 percent probability of delay."
    ),
    table(
        ["Quantity", "Implemented expression"],
        [
            (
                "Exposure E",
                "30 min(wind/64, 1) + 25 min(waves/8, 1) + 0.2 traffic + 25 max(0, 1 - storm_nm/300)",
            ),
            (
                "Voyage duration H",
                "(distance × distance_factor / speed) × (1 + 0.025 waves × weather_factor + 0.001 traffic)",
            ),
            (
                "Fuel F",
                "(H/24) × reference_tonnes_per_day × (speed/14)³ × (1 + 0.04 waves × weather_factor)",
            ),
            ("CO₂ and fuel cost", "CO₂ = F × carbon_factor; cost = F × fuel_price"),
        ],
        [115, 360],
    ),
    Spacer(1, 12),
    text(
        "Maintain course uses the supplied speed and distance. Economy speed uses 80 percent of the supplied speed. The illustrative detour uses 120 percent of the distance and a weather factor of 0.55. The decision policy favors the detour at exposure of at least 60, economy speed below 35, and the baseline otherwise. These thresholds make the workflow easy to inspect; they are not learned optimal thresholds."
    ),
    heading("3.7 Persistence, interface, and defensive behavior"),
    text(
        "A saved experiment stores its validated input and complete output in SQLite together with a generated identifier and a UTC timestamp. Loading the experiment restores the recorded scenario. Database operations use parameterized queries. The CSV export respects the selected cohort filters and prefixes strings beginning with spreadsheet formula characters. React renders vessel names and analysis text as text rather than directly inserting untrusted HTML."
    ),
    text(
        "The API binds to the local machine in the standard launch script. The frontend uses same-origin requests in a production build and a development proxy during editing. API documentation is exposed through FastAPI. A public multi-user deployment would require authentication, authorization, rate limiting, and a persistence design beyond the current local workspace. The container and CI files prepare reproducible execution but are not evidence that a public service has been deployed."
    ),
)

page(
    "4 Experimental analysis",
    heading("4.1 Experimental protocol and comparison"),
    text(
        "Every method is evaluated against the same 9,985 held-out target observations from 51 unseen vessels. Training uses 27,264 examples from 151 other vessels. The test cohort is not used for scaling, fitting, or tuning. Results compare implementations under a common local protocol; they do not compare numerical claims taken from papers that used different data, target definitions, and forecasting horizons."
    ),
    table(
        ["Approach", "MAE kn", "RMSE kn", "R²", "Training s"],
        [
            [
                r["model"],
                f'{r["mae"]:.4f}',
                f'{r["rmse"]:.4f}',
                f'{r["r2"]:.4f}',
                r["train_seconds"],
            ]
            for r in B["results"]
        ],
        [155, 75, 80, 70, 95],
    ),
    p(
        "Table 1. Measured benchmark results. Training times are from one local execution and are not hardware-independent performance guarantees.",
        "caption",
    ),
    text(
        "Persistence gives the lowest MAE at 0.3498 knots. Gradient boosting yields an MAE of 0.4878 knots, approximately 39.5 percent higher, while its RMSE is about 1.95 percent lower than persistence. Ridge regression and random forest also show slightly lower RMSE than persistence but higher MAE. The training-median baseline performs poorly, indicating that the current observation carries substantially more predictive information than a fleet-wide constant."
    ),
    heading("4.2 Why the metrics disagree"),
    text(
        "MAE assigns a linear penalty to each error. RMSE squares the errors before averaging and therefore emphasizes occasional large mistakes. A model can improve a few large misses while introducing many small deviations from otherwise stable speeds. The observed rankings are consistent with that possibility, but this aggregate table alone does not prove the detailed mechanism. Inspecting individual residuals and activity subgroups is necessary before drawing a stronger conclusion."
    ),
    text(
        "R² expresses squared-error improvement relative to a constant based on the test-target mean. It is not a percentage of correct predictions, and a high R² does not imply a small operational error in every case. The median baseline has negative R² because it is a poor predictor for this test distribution. The project reports all three metrics to prevent a single attractive number from becoming the whole result."
    ),
    heading("4.3 Main finding"),
    text(
        "The experiment does not support a blanket statement that machine learning improves short-horizon speed prediction. It supports a narrower conclusion: persistence is a strong average-error baseline in this cohort, and the learned methods alter the distribution of errors. For a user prioritizing MAE, persistence is the better measured option. For a user particularly concerned with large errors, the small RMSE difference motivates further evaluation, including paired uncertainty analysis and additional dates."
    ),
)

page(
    "4 Experimental analysis continued",
    heading("4.4 Activity and horizon subgroups"),
    table(
        ["Held-out subgroup", "Rows", "Persistence MAE", "Boosting MAE"],
        [
            [x["group"], x["n"], x["persistence_mae"], x["boosting_mae"]]
            for x in B["subgroups"]
        ],
        [200, 65, 105, 105],
    ),
    p(
        "Table 2. Subgroup errors in knots. Subgroups overlap across the activity and horizon definitions; their counts must not be added across all four rows.",
        "caption",
    ),
    text(
        "Of the held-out examples, 7,194 have current speed below 0.5 knots and 2,791 are moving at or above that threshold. Persistence MAE is 0.0918 knots for the first group and 1.0148 knots for the second. The corresponding boosting values are 0.1550 and 1.3456 knots. The much larger error among moving observations indicates that the aggregate score is strongly influenced by the prevalence of stationary or slow reports."
    ),
    text(
        "Most targets occur within ten minutes: 9,747 examples fall in that horizon group, compared with 238 in the longer group. The longer-horizon subgroup happens to have smaller measured errors in this cohort. This is not evidence that longer-range prediction is easier. The groups contain different vessels and activity patterns, and the smaller group is especially sensitive to composition. A fixed-horizon evaluation with matched populations would be needed to isolate the effect of forecast duration."
    ),
    heading("4.5 Sampling uncertainty"),
    text(
        "For the prespecified gradient-boosting model, the 95 percent percentile interval for MAE is 0.2710–0.7543 knots across 500 vessel-cluster bootstrap samples. The interval is wider than a naive row-level analysis might suggest because many observations belong to the same vessel. Repeated reports share movement patterns and cannot safely be treated as thousands of unrelated experiments."
    ),
    text(
        "This interval is conditional on the chosen test cohort, observation day, target definition, and training procedure. It is not a prediction interval for an individual ship, and it does not estimate uncertainty for an entirely different season or region. The project does not claim that the slight RMSE improvement is statistically significant. A paired comparison over multiple held-out dates and vessel cohorts would be a more appropriate next experiment."
    ),
    heading("4.6 What should change next"),
    text(
        "The most informative next step is to collect more days and define an evaluation protocol before adding architecture complexity. Candidate extensions include fixed-horizon targets, short historical windows, acceleration features, and vessel-category encoding. Each extension should be compared against persistence on unchanged held-out partitions. The team should also report performance for moving vessels separately, because an excellent aggregate score on mostly stationary data can conceal the more difficult operational cases."
    ),
)

page(
    "4 Experimental analysis continued",
    heading("4.7 Model inspection"),
    table(
        ["Feature shuffled", "Mean increase in MAE", "Repeat standard deviation"],
        [[x["feature"], x["increase_mae"], x["std"]] for x in B["feature_importance"]],
        [180, 150, 145],
    ),
    p(
        "Table 3. Held-out permutation importance for gradient boosting. Positive values indicate that shuffling worsened performance; a small negative value is possible.",
        "caption",
    ),
    text(
        "Current speed dominates the measured importance, with a mean MAE increase of 3.4249 knots after shuffling. Course and longitude have much smaller positive contributions. Latitude has a slightly negative mean importance in this sampled test set. This does not establish that latitude is intrinsically harmful or that the other variables cause speed changes. Importance depends on the fitted model, correlated features, and the evaluation sample."
    ),
    heading("4.8 Exploratory findings and quality limits"),
    text(
        "The complete analytical cohort has a mean observed speed of about 2.25 knots. The dashboard separates this observation-weighted mean from distinct-vessel counts. Missing technical fields are substantial: draft is absent in 77,034 of the 122,629 selected-cohort messages before validation and resampling, while width is absent in 25,172. These gaps explain why the project does not train a fuel-consumption model or estimate vessel-specific resistance from dimensions."
    ),
    text(
        "A notable cleaning effect is the removal of 25,113 invalid observations before duplicate elimination. The accepted course range excludes the unknown-course sentinel and other invalid values. This improves the reliability of circular course features but changes which observations remain. Missingness and validity are therefore not merely housekeeping statistics; they affect the population on which results are reported."
    ),
    text(
        "The H3 layer counts distinct MMSIs in each cell across the selected cumulative window. One vessel can contribute to several cells as it moves. Summing unique-vessel counts over cells would double-count such vessels, whereas summing observation counts over cells recovers the selected message total. The automated tests check the latter conservation property. This distinction provides a useful example of why geospatial aggregation requires a clear definition of the unit being counted."
    ),
    heading("4.9 Storm context"),
    text(
        "The scatterplot links observed speed with retrospective distance to Idalia. It is an exploratory view, not a causal model of weather disruption. At this date, the storm center was near Cuba rather than at its eventual Florida landfall. Port location, vessel class, route, and activity can confound the relationship. The predictive benchmark excludes storm distance to avoid presenting retrospective best-track knowledge as if it had been an operational forecast."
    ),
)

page(
    "4 Experimental analysis continued",
    heading("4.10 Working demonstration and scenario evidence"),
    text(
        "The implemented workspace provides five functional views: fleet overview, EDA, scenario lab, model benchmark, and data/methodology. The browser checks exercised vessel inspection, view changes, severe-weather evaluation, experiment persistence and deletion, and mobile rendering. Backend tests cover filtering, target and split consistency, input rejection, scenario calculations, persistence, CSV export, storm alignment, and artifact fingerprint consistency."
    ),
    table(
        ["Verification area", "Observed result"],
        [
            (
                "Backend behavioral suite",
                "17 tests passed in the recorded local verification.",
            ),
            (
                "Frontend build and lint",
                "Production build and lint completed successfully.",
            ),
            (
                "Browser interactions",
                "Seven view screenshots captured; no page errors in the scripted flow.",
            ),
            (
                "Mobile layout",
                "390-pixel viewport checked; no document-level horizontal overflow.",
            ),
            (
                "Dependency audit",
                "npm audit reported zero vulnerabilities after dependency updates.",
            ),
            (
                "Offline geographic context",
                "Bundled Natural Earth land polygons; optional online street basemap.",
            ),
        ],
        [180, 295],
    ),
    Spacer(1, 12),
    text(
        "These checks establish that the recorded workflow works in the tested local environment. They do not constitute a penetration test, a cross-browser certification, or a navigation safety validation. Container and CI configuration are included but are not described as executed remote infrastructure. The repository is prepared for a normal authenticated GitHub upload, with secrets and large raw files excluded."
    ),
    heading("4.11 A severe-weather scenario"),
    text(
        "The severe-weather preset uses 300 nautical miles, 14 knots, 75-knot wind, 7-metre waves, traffic assumption 70, and storm distance 40 nautical miles. With the default fuel assumptions, the exposure index is 87.55 out of 100. The policy proposes the illustrative detour. The baseline estimate is 26.68 hours and 34.15 tonnes of fuel; economy speed is 33.35 hours and 21.86 tonnes; the detour is 29.98 hours and 34.61 tonnes."
    ),
    text(
        "The detour therefore uses slightly more estimated fuel than the baseline in this scenario. This is an important result: lower assumed exposure does not automatically mean lower fuel consumption. The recommendation reflects the documented exposure policy, not an optimization that simultaneously minimizes time, fuel, emissions, and risk. A reviewer can inspect each contribution, compare the alternatives, and challenge the assumed distance or weather reduction."
    ),
    heading("4.12 Overall interpretation"),
    text(
        "The project is strongest when assessed as an integrated analytical workflow. Its interface makes the dataset and assumptions accessible, its benchmark demonstrates why baseline selection matters, and its scenario trace makes conditional reasoning explicit. The evidence does not support claims of verified delay avoidance, autonomous rerouting, measured fuel savings, or global forecasting performance. Keeping those claims out of the demonstration improves both technical credibility and the quality of the discussion."
    ),
)

page(
    "5 Conclusion and future work",
    text(
        "Agentic Geo-Spatial Intelligence turns a large historical AIS file into a usable and auditable maritime research workspace. The completed implementation connects real vessel exploration, geospatial aggregation, data-quality reporting, a reproducible forecasting benchmark, and transparent voyage scenarios. Its main contribution is the integration of these parts with traceable definitions and a working local interface."
    ),
    text(
        "The experiment demonstrates the importance of a strong baseline. Persistence achieves lower MAE than the learned models on the held-out vessel cohort, while gradient boosting has slightly lower RMSE. The difference in rankings is informative rather than inconvenient: it shows that model choice depends on the error objective and the distribution of vessel activity. The reported uncertainty interval, subgroup results, and feature inspection help explain the limits of an aggregate score."
    ),
    text(
        "Future work should begin with multi-day, multi-region evaluation and operationally available weather forecasts. Fixed-horizon targets and short movement histories can then be tested without changing the held-out protocol opportunistically. Verified port calls, schedules, and actual arrival outcomes are needed for delay prediction. Measured fuel use and vessel characteristics are needed for validated fuel models. Navigation-grade routing would additionally require charts, bathymetry, vessel constraints, and expert review."
    ),
    text(
        "The scenario workflow can be extended with sensitivity analysis, constrained optimization, and a richer audit trail. Any language-model component should explain structured evidence rather than generate unsupported numerical conclusions. For public deployment, authentication, authorization, rate limiting, and controlled persistence would be necessary. These are concrete next steps beyond the present local research scope."
    ),
    text(
        "The project is ready to demonstrate as a bounded research prototype. A defensible presentation should emphasize what was measured, what was assumed, and what remains unvalidated. That distinction is central to the project’s technical value."
    ),
    Spacer(1, 20),
    p(
        "Submission preparation: add the three team members and institutional details, read the primary papers, reproduce the results, and write the final report in accordance with the instructor’s stated AI policy.",
        "caption",
    ),
)

sorted_refs = sorted(REFS, key=lambda r: authors(r).lower())
for n, chunk in enumerate([sorted_refs[:9], sorted_refs[9:17], sorted_refs[17:]], 1):
    page(
        "References" + (" continued" if n > 1 else ""),
        *[p(apa(r), "ref") for r in chunk],
    )


def footer(canvas, doc):
    canvas.setFont("TimesLocal", 8)
    canvas.setFillColor(colors.HexColor("#879592"))
    canvas.drawString(60, 30, "Agentic Geo-Spatial Intelligence | Reference draft")
    canvas.drawRightString(A4[0] - 60, 30, str(doc.page))


def make_report():
    story = []
    for i, (title, content) in enumerate(pages):
        story.append(p(title, "h1"))
        story.extend(content)
        if i < len(pages) - 1:
            story.append(PageBreak())
    SimpleDocTemplate(
        str(OUT / "AGI_Report_Reference_Draft.pdf"),
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=45,
        bottomMargin=48,
        title="Agentic Geo-Spatial Intelligence",
        author="Project team names pending",
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    make_markdown()


def make_markdown():
    def plain(value):
        if isinstance(value, (list, tuple)):
            return ' '.join(plain(x) for x in value)
        if isinstance(value, Paragraph):
            return html.unescape(re.sub('<[^>]+>', '', value.text))
        return str(value)

    md = [
        "# Agentic Geo-Spatial Intelligence\n\nReference draft for study; follow your instructor’s AI policy.\n"
    ]
    for title, content in pages:
        md.append("\n## " + title + "\n")
        for item in content:
            if isinstance(item, Paragraph):
                md.append(re.sub("<[^>]+>", "", html.unescape(item.text)) + "\n")
            elif isinstance(item, Table):
                for row_index, row in enumerate(item._cellvalues):
                    md.append(
                        "| "
                        + " | ".join(
                            plain(x)
                            for x in row
                        )
                        + " |"
                    )
                    if row_index == 0:
                        md.append('| ' + ' | '.join(['---'] * len(row)) + ' |')
                md.append("")
    (OUT / "AGI_Report_Reference_Draft.md").write_text("\n".join(md), encoding="utf-8")


def reading_matrix():
    lines = [
        "# Verified reading matrix",
        "",
        "Records verified through Crossref. Abstract-level summaries are not full-paper reviews. Read the primary papers before using them in your student-authored literature survey.",
        "",
    ]
    notes = {
        2: "Attention and recurrent sequence modeling motivate future historical-window predictors.",
        3: "Clustering and recurrent prediction motivate separating trajectory patterns before modeling.",
        8: "A review of varied anomaly definitions motivates cautious interpretation of statistical flags.",
        12: "Emission estimation requires technical and operational vessel assumptions.",
        13: "Port-network analysis is a different analytical unit from message density.",
        14: "Coastal activity analysis illustrates application-specific interpretation of vessel behavior.",
        16: "Fuel prediction studies need an observed fuel target absent from the project dataset.",
        17: "Temporal fuel modeling is a potential extension only with measured consumption data.",
        19: "In-service fuel measurements support a different task from AIS-only speed estimation.",
        20: "Meteorological and voyage features motivate future operational-data integration.",
        22: "Traffic-network extraction differs from the implemented hexagonal density aggregation.",
        24: "Irregular timing and interpolation affect the definition of forecast horizons.",
        25: "Vessel traffic services place anomaly flags within human decision support.",
    }
    rows = []
    for i, r in enumerate(REFS, 1):
        status = (
            "Publisher abstract reviewed"
            if r.get("abstract")
            else "Metadata verified; full text/abstract still to read"
        )
        note = notes.get(
            i,
            "Relevant reading identified by topic and verified metadata; no performance claim is imported.",
        )
        lines += [
            f'## {i}. {html.unescape(r["title"][0])}',
            f'{authors(r)} ({year(r)}). {html.unescape(r["container-title"][0])}.',
            f'https://doi.org/{r["DOI"]}',
            f"**Evidence level:** {status}",
            f"**Project relevance:** {note}",
            "",
        ]
        rows.append([i, html.unescape(r["title"][0]), year(r), r["DOI"], status, note])
    (ROOT / "docs/research/READING_MATRIX.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    with (ROOT / "docs/research/reading_matrix.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.writer(f)
        w.writerow(["id", "title", "year", "doi", "review_status", "project_relevance"])
        w.writerows(rows)
    (ROOT / "docs/research/REFERENCES_APA.md").write_text(
        "# APA reference list\n\n"
        + "\n\n".join(
            re.sub("<[^>]+>", "", html.unescape(apa(r))) for r in sorted_refs
        ),
        encoding="utf-8",
    )


def handbook():
    raw = (ROOT / "docs/REVIEW_GUIDE.md").read_text(encoding="utf-8")
    story = [
        p("Agentic Geo-Spatial Intelligence", "h1"),
        p("Project review handbook", "h2"),
    ]
    for line in raw.splitlines()[2:]:
        if not line.strip():
            continue
        if line.startswith("## "):
            story.append(p(escape(line[3:]), "h2"))
        elif line.startswith("| Member |"):
            story.append(
                table(
                    ["Member", "Ownership", "Preparation"],
                    [
                        [
                            "1 — name pending",
                            "Dataset, audit, EDA",
                            "Sampling, missingness, H3",
                        ],
                        [
                            "2 — name pending",
                            "Models and experiments",
                            "Splits, metrics, interpretation",
                        ],
                        [
                            "3 — name pending",
                            "Frontend, API, scenarios",
                            "Validation, persistence, units",
                        ],
                    ],
                    [100, 175, 200],
                )
            )
        elif line.startswith("|"):
            continue
        else:
            line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escape(line))
            story.append(p(line, "handbook"))
    SimpleDocTemplate(
        str(OUT / "AGI_Project_Review_Handbook.pdf"),
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=48,
        bottomMargin=48,
        title="Agentic Geo-Spatial Intelligence Review Handbook",
    ).build(story, onFirstPage=footer, onLaterPages=footer)


def notebook():
    cells = []

    def md(s):
        cells.append(dict(cell_type="markdown", metadata={}, source=s.splitlines(True)))

    def code(s):
        cells.append(
            dict(
                cell_type="code",
                metadata={},
                execution_count=None,
                outputs=[],
                source=s.splitlines(True),
            )
        )

    md(
        "# Agentic Geo-Spatial Intelligence\n## Reproducible exploratory analysis\nUse the project Python environment. This notebook reads the compact historical cohort; it does not manufacture delay labels. Figures require the optional matplotlib dependency."
    )
    code(
        "from pathlib import Path\nimport json\nimport pandas as pd\nimport numpy as np\nROOT = Path.cwd() if (Path.cwd()/'data/atlas').exists() else Path.cwd().parent\nDATA = ROOT/'data/atlas'\ndf = pd.read_csv(DATA/'observations.csv', dtype={'mmsi':str})\nmanifest = json.loads((DATA/'manifest.json').read_text())\nbenchmark = json.loads((DATA/'benchmark.json').read_text())\nprint(f'{len(df):,} observations; {df.mmsi.nunique()} vessels')\ndf.head()"
    )
    md(
        "## Audit and provenance\nThe missing-value counts in the manifest describe the sampled cohort before validation and binning. The table below describes the final derived observations; denominators differ."
    )
    code(
        "display(pd.Series(manifest))\ndisplay(df.isna().mean().sort_values(ascending=False).rename('missing_fraction'))\nassert len(df)==manifest['observations']\nassert not df.duplicated(['mmsi','timestamp']).any()"
    )
    md(
        "## Descriptive statistics\nA mean over observations weights vessels with more retained reports more heavily. Compare it with a mean of per-vessel means."
    )
    code(
        "display(df[['speed','storm_distance_nm','length','width','draft']].describe())\nprint('Observation-weighted mean:',df.speed.mean())\nprint('Vessel-weighted mean:',df.groupby('mmsi').speed.mean().mean())\ndisplay(df.groupby('vessel_type').agg(vessels=('mmsi','nunique'),observations=('mmsi','size'),mean_speed=('speed','mean')))"
    )
    md(
        "## Spatial and temporal exploration\nH3 cells count unique vessels over the day, not simultaneous congestion. Summing per-cell vessel counts double-counts moving vessels."
    )
    code(
        "display(df.groupby('h3').agg(vessels=('mmsi','nunique'),observations=('mmsi','size')).sort_values('vessels',ascending=False).head(10))\ndisplay(df.assign(hour=df.timestamp.str[11:13]).groupby('hour').agg(observations=('mmsi','size'),mean_speed=('speed','mean')))"
    )
    md(
        "## Charts\nOptional: install matplotlib into the same environment. The dashboard already provides interactive versions of these plots."
    )
    code(
        "import matplotlib.pyplot as plt\nfig,ax=plt.subplots(1,2,figsize=(12,4))\nax[0].hist(df.speed,bins=30,color='#189d88');ax[0].set(xlabel='Speed (knots)',ylabel='Observations')\nsample=df.sample(min(2000,len(df)),random_state=42)\nax[1].scatter(sample.storm_distance_nm,sample.speed,s=6,alpha=.3,color='#5689db');ax[1].set(xlabel='Retrospective storm distance (nm)',ylabel='Speed (knots)')\nplt.tight_layout()"
    )
    md(
        "## Correlation is not causation\nRetrospective storm distance is excluded from forecast features. Course has circular features because 359 degrees is close to 1 degree."
    )
    code("df[['speed','lat','lon','storm_distance_nm','length','draft']].corr()")
    md(
        "## Common held-out experiment\nThe benchmark uses whole-vessel separation. Persistence is the strongest MAE baseline in the recorded run. Do not select hyperparameters on these test scores."
    )
    code(
        "display(pd.DataFrame(benchmark['results']))\ndisplay(pd.DataFrame(benchmark['subgroups']))\ndisplay(pd.DataFrame(benchmark['feature_importance']))\nassert benchmark['overlapping_vessels']==0\nprint('Cluster bootstrap MAE interval:',benchmark['mae_cluster_bootstrap_95ci'])"
    )
    md(
        "## Questions for the team\n1. Why are there 217 observed vessels but only 202 with eligible prediction targets?\n2. How does dropping unknown course values change the cohort?\n3. Why do MAE and RMSE rank the methods differently?\n4. What additional data are required before predicting actual arrival delay or fuel consumption?"
    )
    target = ROOT / "notebooks"
    target.mkdir(exist_ok=True)
    (target / "01_maritime_eda.ipynb").write_text(
        json.dumps(
            dict(
                cells=cells,
                metadata=dict(
                    kernelspec=dict(
                        display_name="Python 3", language="python", name="python3"
                    ),
                    language_info=dict(name="python", version="3.12"),
                ),
                nbformat=4,
                nbformat_minor=5,
            ),
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    import sys

    if "--handbook-only" in sys.argv:
        handbook()
    elif "--markdown-only" in sys.argv:
        make_markdown()
    else:
        make_report()
        reading_matrix()
        handbook()
        notebook()
    print("Created requested research materials.")
