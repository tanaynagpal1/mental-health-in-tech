"""Act 1 - The gap.

How many people are affected, and how many of them got help? Everything else
in the dashboard exists to explain the distance between those two numbers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app import charts, data, theme

view: pd.DataFrame = st.session_state["view"]
full: pd.DataFrame = st.session_state["full"]

theme.hero(
    "Human signals · workplace analytics",
    "What happens behind the screen?",
    "1,247 people working in technology answered 26 questions about mental health, "
    "what their employer offers, and what they dare say out loud.",
)

charts.reading_panel()

# --------------------------------------------------------------------------
# 1.1  KPI row
# --------------------------------------------------------------------------
n = len(view)
cond = view.has_condition.eq("Yes")
treated = view.treatment.eq("Yes")
untreated_with = int((cond & ~treated).sum())

theme.kpi_row([
    dict(label="Respondents", value=f"{n:,}",
         sub="of 1,247 after cleaning" if n == len(full) else f"of {len(full):,} in view",
         note="Responses left after the 8 impossible ages and 4 duplicate "
              "submissions were removed in Phase 2."),
    dict(label="Report a condition", value=f"{cond.mean() * 100:.1f}%",
         sub=f"{int(cond.sum()):,} people",
         note="Self-reported, and inferred from the work-interference question - "
              "the survey never asked for a diagnosis."),
    dict(label="Sought treatment", value=f"{treated.mean() * 100:.1f}%",
         sub=f"{int(treated.sum()):,} people",
         note="Treatment-seeking, not prevalence. Someone can have a condition "
              "and never have sought help - which is the point of the next tile."),
    dict(label="Condition, no treatment", value=f"{untreated_with:,}",
         sub=f"{untreated_with / n * 100:.1f}% of everyone here",
         note="The gap this dashboard exists to explain. Every page after this "
              "one is an attempt to account for these people."),
])

# --------------------------------------------------------------------------
# 1.2  Condition -> treatment flow
# --------------------------------------------------------------------------
charts.section(
    "Where the 1,247 go",
    "Every respondent splits twice: do they report a condition, and did they seek "
    "treatment. The thickest ribbon that ends in 'never sought help' is the subject "
    "of this dashboard.",
)

if data.guard(view, "the flow diagram", 100):
    ct = pd.crosstab(view.has_condition, view.treatment)
    yy = int(ct.loc["Yes", "Yes"]) if "Yes" in ct.index and "Yes" in ct.columns else 0
    yn = int(ct.loc["Yes", "No"]) if "Yes" in ct.index and "No" in ct.columns else 0
    ny = int(ct.loc["No", "Yes"]) if "No" in ct.index and "Yes" in ct.columns else 0
    nn = int(ct.loc["No", "No"]) if "No" in ct.index and "No" in ct.columns else 0

    fig = charts.sankey(
        labels=[f"All respondents · {yy + yn + ny + nn:,}",
                f"Reports a condition · {yy + yn:,}",
                f"No condition reported · {ny + nn:,}",
                f"Sought treatment · {yy + ny:,}",
                f"Never sought treatment · {yn + nn:,}"],
        colours=[theme.SLATE, theme.VIOLET, theme.SLATE, theme.TEAL, theme.CLAY],
        source=[0, 0, 1, 1, 2, 2],
        target=[1, 2, 3, 4, 3, 4],
        value=[yy + yn, ny + nn, yy, yn, ny, nn],
        link_colours=["rgba(91,75,214,.20)", "rgba(122,135,131,.16)",
                      "rgba(0,144,158,.26)", "rgba(200,90,52,.30)",
                      "rgba(0,144,158,.26)", "rgba(122,135,131,.16)"],
        height=420,
    )
    charts.show(fig)
    charts.brief(
        what=f"How the {n:,} respondents in view divide, first by whether they report a "
             "mental health condition, then by whether they ever sought treatment.",
        how="Ribbon thickness is people, not percent. Follow the violet band across to see "
            "how the group that reports a condition splits into treated and untreated. "
            "Hover any ribbon for its exact count.",
        why="A stacked bar would give the same four numbers but lose the path - and the "
            "path is the point. The untreated-with-condition group only exists as a "
            "branch of another group.",
        careful="\"Reports a condition\" is inferred from the work-interference question, "
                "which the survey only asked of people who have one. It is self-reported "
                "and not a diagnosis.",
    )

# --------------------------------------------------------------------------
# 1.3  What moves the needle
# --------------------------------------------------------------------------
charts.section(
    "What moves the needle",
    "For every factor, the two groups furthest apart on treatment-seeking. Sorted by "
    "the size of that gap. Only groups with at least 20 respondents are eligible.",
)

FACTORS = {
    "Family history of mental illness": "family_history",
    "Knows the care options": "care_options",
    "Employer offers benefits": "benefits",
    "Region": "region",
    "Gender": "gender_clean",
    "Ease of taking medical leave": "leave",
    "Has seen a colleague penalised": "obs_consequence",
    "Fears consequences at work": "mental_health_consequence",
    "Age group": "age_group",
    "Company size": "no_employees",
    "Would tell coworkers": "coworkers",
    "Works at a tech company": "tech_company",
    "Works remotely": "remote_work",
}


@st.cache_data(show_spinner=False)
def gap_table(frame: pd.DataFrame, minimum: int = 20) -> pd.DataFrame:
    """Widest within-factor contrast, one row per factor."""
    rows = []
    for label, col in FACTORS.items():
        if col not in frame.columns:
            continue
        g = frame.groupby(col, observed=True).agg(
            n=("treatment", "size"),
            rate=("treatment", lambda s: s.eq("Yes").mean() * 100),
        )
        g = g[g.n >= minimum]
        if len(g) < 2:
            continue
        lo_i, hi_i = g.rate.idxmin(), g.rate.idxmax()
        rows.append({
            "factor": label,
            "low": f"{lo_i} (n={int(g.n[lo_i])})", "low_rate": float(g.rate[lo_i]),
            "high": f"{hi_i} (n={int(g.n[hi_i])})", "high_rate": float(g.rate[hi_i]),
            "gap": float(g.rate[hi_i] - g.rate[lo_i]),
        })
    return pd.DataFrame(rows).sort_values("gap")


if data.guard(view, "the factor ranking", 100):
    gaps = gap_table(view)
    if len(gaps) < 3:
        st.info("Too few factors keep 20 respondents per group under these filters.")
    else:
        fig = charts.dumbbell(
            labels=gaps.factor.tolist(),
            left=gaps.low_rate.tolist(), right=gaps.high_rate.tolist(),
            left_name="Lowest group", right_name="Highest group",
            left_detail=gaps.low.tolist(), right_detail=gaps.high.tolist(),
        )
        charts.show(fig)
        top = gaps.iloc[-1]
        charts.brief(
            what="Each row is one survey question. The two dots are the answer groups with "
                 "the lowest and highest treatment-seeking rate within that question.",
            how="Read the length of the bar, not the position of the dots - the bar is the "
                "gap. Hover either dot to see which answer group it is and how many people "
                "gave that answer.",
            why="A dumbbell makes the comparison itself the visual object. Grouped bars "
                "would show 26 blocks and leave the reader to subtract.",
            careful=f"These are raw differences with nothing held constant. "
                    f"{top.factor} leads at {top.gap:.1f}pp, but factors overlap heavily - "
                    "the model below is what separates them.",
        )

# --------------------------------------------------------------------------
# 1.4  Odds of seeking treatment (the honest model)
# --------------------------------------------------------------------------
charts.section(
    "What still matters once everything else is held constant",
    "A logistic model of treatment-seeking. The three leaky columns - work interference, "
    "the derived condition flag and its score - are excluded by rule (DQ-26), because a "
    "model that sees them scores 90% and learns nothing.",
)

MODEL_FEATURES = [
    "family_history", "gender_clean", "age_group", "region", "no_employees",
    "remote_work", "tech_company", "benefits", "care_options", "seek_help",
    "anonymity", "leave", "obs_consequence", "mental_health_consequence",
    "coworkers", "supervisor",
]

PRETTY = {
    "family_history": "Family history", "gender_clean": "Gender",
    "age_group": "Age", "region": "Region", "no_employees": "Company size",
    "remote_work": "Remote work", "tech_company": "Tech company",
    "benefits": "Benefits", "care_options": "Care options",
    "seek_help": "Told where to seek help", "anonymity": "Anonymity protected",
    "leave": "Medical leave", "obs_consequence": "Saw a colleague penalised",
    "mental_health_consequence": "Fears consequences",
    "coworkers": "Would tell coworkers", "supervisor": "Would tell supervisor",
}


def _label(term: str) -> str:
    """'family_history_Yes' -> 'Family history: Yes'."""
    for col in sorted(MODEL_FEATURES, key=len, reverse=True):
        if term.startswith(col + "_"):
            return f"{PRETTY.get(col, col)}: {term[len(col) + 1:]}"
    return term


def _fit(frame: pd.DataFrame) -> pd.Series:
    X = frame[MODEL_FEATURES].astype(str)
    y = frame.treatment.eq("Yes").astype(int)
    pipe = Pipeline([
        ("enc", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore")),
        ("lr", LogisticRegression(max_iter=2000)),
    ])
    pipe.fit(X, y)
    names = pipe.named_steps["enc"].get_feature_names_out(MODEL_FEATURES)
    return pd.Series(pipe.named_steps["lr"].coef_[0], index=names)


@st.cache_data(show_spinner="Fitting the model and bootstrapping intervals...")
def odds_ratios(frame: pd.DataFrame, draws: int = 200, top: int = 12) -> pd.DataFrame:
    """Odds ratios with percentile-bootstrap 95% intervals.

    Bootstrap rather than a closed-form standard error: scikit-learn's
    LogisticRegression is regularised, so its Wald intervals would be wrong.
    Resampling makes no distributional assumption and costs ~3 seconds.
    """
    point = _fit(frame)
    rng = np.random.default_rng(7)
    draws_ = []
    for _ in range(draws):
        idx = rng.integers(0, len(frame), len(frame))
        try:
            draws_.append(_fit(frame.iloc[idx]))
        except ValueError:          # a resample lost a whole level
            continue
    boot = pd.DataFrame(draws_).reindex(columns=point.index)

    out = pd.DataFrame({
        "term": [_label(t) for t in point.index],
        "or": np.exp(point.to_numpy()),
        "lo": np.exp(boot.quantile(0.025).to_numpy()),
        "hi": np.exp(boot.quantile(0.975).to_numpy()),
    }).dropna()
    out["mag"] = np.abs(np.log(out["or"]))
    return out.nlargest(top, "mag").drop(columns="mag")


if data.guard(view, "the model", 200):
    table = odds_ratios(view)
    charts.show(charts.forest(table))
    charts.brief(
        what="The twelve largest effects on the odds of having sought treatment, with "
             "every other feature in the model held constant.",
        how="1.0 means no effect. A dot at 2.0 means those respondents had roughly twice "
            "the odds; at 0.5, half. The bar is the 95% interval - teal and clay bars "
            "clear 1.0, grey bars do not, and a grey result is a result: the model cannot "
            "separate it from nothing.",
        why="A forest plot shows effect size and uncertainty in one mark. A bar chart of "
            "coefficients would show only the point estimate, which is the half that "
            "misleads. The axis is log so that 0.5 and 2.0 look equally far from 1.0.",
        careful="This is association, not cause. The leave and coworker effects almost "
                "certainly run backwards - you learn how hard leave is by needing it. "
                "Intervals come from 200 bootstrap resamples of the current filtered view.",
    )

# --------------------------------------------------------------------------
# 1.5  Three findings
# --------------------------------------------------------------------------
charts.section("Three things the data says before you filter anything")

f1, f2, f3 = st.columns(3)
with f1:
    charts.finding("360", "people report a mental health condition and have never "
                          "sought treatment - 28.9% of everyone surveyed.")
with f2:
    charts.finding("61.8% → 26.9%", "treatment-seeking as uncertainty about employer "
                                    "support rises. Not knowing behaves like a barrier.")
with f3:
    charts.finding("22.9% vs 4.7%", "fear consequences for disclosing a mental health "
                                    "condition versus a physical one. Same people, "
                                    "same employer.")

st.caption(
    f"Showing {n:,} of {len(full):,} respondents · "
    f"{st.session_state.get('filter_text', 'No filters')}"
)