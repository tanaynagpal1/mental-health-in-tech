"""About the data.

The receipts. Where the numbers came from, what was changed, what was thrown
away and why, and what this survey cannot tell you however hard you filter it.

Nothing on this page is analysis. It exists so the other six pages can be
checked rather than believed.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from app import charts, data, theme
from src import config as cfg

full: pd.DataFrame = st.session_state["full"]

theme.hero(
    "The receipts",
    "About the data",
    "One public survey, 1,259 raw responses, 29 documented decisions and a "
    "reproducible pipeline. Every figure in this dashboard traces back to here.",
)

# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------
charts.section("Where this comes from")

p1, p2, p3 = st.columns(3)
with p1:
    theme.kpi("Source", "OSMI 2014",
              "Open Sourcing Mental Illness, Mental Health in Tech Survey")
with p2:
    theme.kpi("Raw responses", f"{cfg.EXPECTED_ROWS_RAW:,}",
              "as published, before any cleaning")
with p3:
    theme.kpi("Analysed", f"{len(full):,}",
              f"{full.shape[1]} columns after 13 were derived")

st.markdown(
    "The survey was run by [Open Sourcing Mental Illness](https://osmihelp.org) "
    "in 2014 and released publicly. It asked 26 questions about mental health, "
    "what an employer provides, and what a respondent would be willing to say "
    "out loud at work. Everyone answered voluntarily."
)

# --------------------------------------------------------------------------
# What was removed
# --------------------------------------------------------------------------
charts.section(
    "How 1,259 became 1,247",
    "Twelve rows were removed, in two groups, for two documented reasons. "
    "Nothing else was deleted at any point.",
)

charts.show(charts.waterfall(
    labels=["Raw responses", "Impossible ages", "Duplicate submissions",
            "Analysed"],
    values=[cfg.EXPECTED_ROWS_RAW, -8, -4, 0],
    measures=["absolute", "relative", "relative", "total"],
))
charts.brief(
    what="The row count from the published file to the one every chart runs on.",
    how="Grey bars are totals, clay bars are removals. The steps add up to the "
        "final figure, so you can check it rather than take it on trust.",
    why="A waterfall shows a derivation. Two numbers with a sentence between "
        "them asks the reader to believe the arithmetic.",
    careful="0.95% of rows were removed. The headline treatment rate moved from "
            "50.6% to 50.5% - the cleaning changed the data's integrity, not "
            "its conclusions.",
)

d1, d2 = st.columns(2)
with d1:
    st.markdown(
        "**The 8 impossible ages** (DQ-01)\n\n"
        "Reported ages included -1726, -29, -1, 5, 8, 11, 329 and 99999999999. "
        "The raw mean age was 79 million. An age that cannot be true casts "
        "doubt on the rest of that response, so the whole row went."
    )
with d2:
    st.markdown(
        "**The 4 duplicate submissions** (DQ-16)\n\n"
        "Four pairs were identical across all 26 answer columns, submitted "
        "between 12 seconds and 5 minutes apart. The first submission of each "
        "pair was kept, the second dropped."
    )

# --------------------------------------------------------------------------
# The 29 decisions
# --------------------------------------------------------------------------
charts.section(
    "29 decisions, grouped by what they actually did",
    "Every data-quality issue found in Phase 2, and the action taken. Hover "
    "any square for the decision.",
)

DECISIONS = [
    # Rows dropped
    ("DQ-01", "Rows dropped", "8 impossible ages removed"),
    ("DQ-16", "Rows dropped", "4 duplicate resubmissions removed"),
    # Column derived
    ("DQ-02", "Column derived", "gender_clean from 44 free-text spellings"),
    ("DQ-05", "Column derived", "has_condition from the blank interference question"),
    ("DQ-08", "Column derived", "has_comment, because commenters are unrepresentative"),
    ("DQ-14", "Column derived", "employment_type, to hold the self-employed out"),
    ("DQ-18", "Column derived", "survey_wave, main vs late responses"),
    ("DQ-20", "Column derived", "ordered categoricals plus size, leave and interference scores"),
    ("DQ-21", "Column derived", "uncertainty_score across 7 questions"),
    ("DQ-24", "Column derived", "region, so small countries are not dropped"),
    ("DQ-28", "Column derived", "age_group with an open-ended 45+ band"),
    # Rule documented
    ("DQ-03", "Rule documented", "strip whitespace before any matching"),
    ("DQ-04", "Rule documented", "lowercase before matching"),
    ("DQ-06", "Rule documented", "blank state labelled by cause, not filled"),
    ("DQ-09", "Rule documented", 'load with na_values=["NA","-",""]'),
    ("DQ-10", "Rule documented", "3 non-US rows: clear the state, keep the country"),
    ("DQ-11", "Rule documented", "only US rows may hold a state"),
    ("DQ-19", "Rule documented", "parse the timestamp with an explicit format"),
    ("DQ-22", "Rule documented", '"Maybe" excluded from the uncertainty score'),
    ("DQ-25", "Rule documented", "say treatment-seeking, never prevalence"),
    ("DQ-26", "Rule documented", "3 leaky features banned from the model"),
    ("DQ-27", "Rule documented", "state the sample skew, never weight it"),
    # No change needed
    ("DQ-07", "No change needed", "18 blank self_employed left blank; imputation failed a test"),
    ("DQ-12", "No change needed", "4 treated-but-no-interference rows left as answered"),
    ("DQ-13", "No change needed", "9 self-employed with a large headcount: ambiguous, not wrong"),
    ("DQ-15", "No change needed", "no benefits but knows the options is a valid pair"),
    ("DQ-17", "No change needed", "13 shared timestamps kept; the answers differ"),
    ("DQ-23", "No change needed", 'the comma in "Bahamas, The" is properly quoted'),
    ("DQ-29", "No change needed", "2 straight-lined rows already removed by DQ-01"),
]

OUTCOME_COLOUR = {
    "Rows dropped": theme.CLAY,
    "Column derived": theme.TEAL,
    "Rule documented": theme.VIOLET,
    "No change needed": theme.SLATE,
}

charts.show(charts.decision_matrix(
    [{"id": i, "outcome": o, "title": t} for i, o, t in DECISIONS],
    colours=OUTCOME_COLOUR, per_row=11, height=330,
))
charts.brief(
    what="All 29 documented data-quality decisions, grouped by their effect on "
         "the dataset rather than by the kind of problem they solved.",
    how="Each square is one decision, numbered. Hover for what it was. The row "
        "labels show how many decisions had each kind of effect.",
    why="Grouping by outcome rather than by problem type answers the question a "
        "sceptical reader actually has: how much of this data was changed?",
    careful="Only 2 of 29 decisions removed any rows, and 7 concluded that "
            "nothing needed doing. That is the point - most of the work was "
            "deciding what a blank meant, not editing values.",
)

# --------------------------------------------------------------------------
# Derived columns
# --------------------------------------------------------------------------
charts.section(
    "The 13 derived columns",
    "Nothing here was invented. Each one is a label for a meaning the original "
    "answer already carried.",
)

DERIVED = [
    ("has_condition", "Yes / No", "Does the interference question have an answer? (DQ-05)"),
    ("gender_clean", "3 groups", "44 free-text spellings resolved (DQ-02)"),
    ("employment_type", "3 groups", "Employee, self-employed or unknown (DQ-14)"),
    ("age_group", "4 bands", "18-24, 25-34, 35-44, 45+ (DQ-28)"),
    ("region", "5 regions", "So a country of 3 people is still counted (DQ-24)"),
    ("size_rank", "1-6", "Company size as a number, in the right order (DQ-20)"),
    ("leave_score", "1-4", "Ease of medical leave as a number (DQ-20)"),
    ("interfere_score", "1-4", "How often it interferes, as a number (DQ-20)"),
    ("knows_leave_policy", "Yes / No", "Did they answer the leave question at all"),
    ("has_comment", "Yes / No", "Commenters differ from non-commenters (DQ-08)"),
    ("survey_wave", "Main / Late", "76 responses arrived months later (DQ-18)"),
    ("uncertainty_score", "0-7", "How many support questions they could not answer (DQ-21)"),
    ("support_score", "0-6", "How many of six provisions they actually have"),
]

st.dataframe(
    pd.DataFrame(DERIVED, columns=["Column", "Values", "What it means"]),
    width="stretch", hide_index=True,
)
st.caption(
    "The last two are the dashboard's backbone: **support_score** is what the "
    "employer provides, **uncertainty_score** is whether the employee knows it."
)

# --------------------------------------------------------------------------
# Limitations
# --------------------------------------------------------------------------
charts.section(
    "What this survey cannot tell you",
    "Read this before quoting any figure from the other six pages.",
)

male = full.gender_clean.eq("Male").mean() * 100
tech = full.tech_company.eq("Yes").mean() * 100
us = full.country.eq("United States").mean() * 100

l1, l2 = st.columns(2)
with l1:
    st.markdown(
        f"""
        **It is not a representative sample.** {male:.0f}% of respondents are
        male, {tech:.0f}% work at a tech company and {us:.0f}% are in the
        United States. Everyone volunteered. No weighting was applied, because
        there is no population benchmark to weight against (DQ-27).

        So every figure is **"X% of respondents"**, never "X% of tech workers".

        **It never asked for a diagnosis.** There is no question "do you have a
        mental health condition?". `has_condition` is inferred from whether the
        work-interference question was answered, and `treatment` records
        treatment-seeking. Neither is prevalence (DQ-25).
        """
    )
with l2:
    st.markdown(
        f"""
        **It is one moment in 2014.** {int(full.survey_wave.eq('Late').sum())} of
        the {len(full):,} responses arrived months after the rest, and they
        differ - 63.2% treatment against 49.7%. That gap is composition, not
        change over time, and nothing here should be read as a trend (DQ-18).

        **Association, never cause.** Two findings almost certainly run
        backwards: people who call medical leave difficult are the most treated,
        and people whose condition "never interferes" are the least. You learn
        those things by needing them.

        **Nothing is reported below n = 20** (n = 10 for US states). Filter hard
        enough and charts refuse rather than mislead (DQ-24).
        """
    )

# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------
charts.section(
    "Reproducing this",
    "Three commands take the published CSV to the file behind every chart.",
)

st.code(
    "python -m src.clean          # survey.csv  ->  survey_clean.csv\n"
    "python -m src.validate       # 19 assertions, all must pass\n"
    "streamlit run app.py         # this dashboard",
    language="powershell",
)
st.markdown(
    "`src/validate.py` re-checks every decision on this page: the row count, "
    "the 13 derived columns, the category orders, the two denominators and the "
    "n thresholds. If a cleaning rule is ever changed, that script fails before "
    "a chart can quietly report a different number."
)

# --------------------------------------------------------------------------
# The documents
# --------------------------------------------------------------------------
charts.section(
    "The full decision log",
    "Evidence, options considered, decision and verification for every issue.",
)

DOCS = [
    ("cleaning_decision_log.md", "Cleaning decision log",
     "The full record: evidence, the options weighed, what was chosen and how "
     "it was verified."),
    ("all_29_decisions.md", "All 29 decisions",
     "One page: the problem and the fix for each issue."),
    ("data_dictionary.md", "Data dictionary",
     "All 27 original columns, grouped into six families."),
]

docs_dir = Path(cfg.PROJECT_ROOT) / "docs"
for filename, title, blurb in DOCS:
    path = docs_dir / filename
    with st.expander(f"{title} — {blurb}"):
        if path.exists():
            text = path.read_text(encoding=cfg.ENCODING)
            st.caption(f"`docs/{filename}` · {len(text.splitlines()):,} lines")
            st.markdown(text)
        else:
            st.warning(f"`docs/{filename}` was not found in the repository.")

st.caption(
    f"{len(full):,} rows · {full.shape[1]} columns · 29 documented decisions · "
    "19 automated checks"
)