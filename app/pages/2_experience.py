"""Act 2 - The weight.

Who carries a mental health condition, and how does it show up at work? The
page moves from the 1,247 as people, to how often the condition interferes,
to the one factor that outweighs every workplace variable: family history.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import charts, data, theme

view: pd.DataFrame = st.session_state["view"]
full: pd.DataFrame = st.session_state["full"]

theme.hero(
    "Act two · the weight",
    "Mental health & work",
    "Four in five respondents report a condition. This page is about what that "
    "condition does to a working week - and who is carrying it.",
)

charts.reading_panel()

# --------------------------------------------------------------------------
# Page-local filters - one row, above everything they scope
# --------------------------------------------------------------------------
c1, c2, _ = st.columns([1.1, 1.1, 1.8])
with c1:
    f_cond = st.segmented_control(
        "Reports a condition", ["All", "Yes", "No"], default="All", key="exp_cond")
with c2:
    f_hist = st.segmented_control(
        "Family history", ["All", "Yes", "No"], default="All", key="exp_hist")

page = view
if f_cond and f_cond != "All":
    page = page[page.has_condition.eq(f_cond)]
if f_hist and f_hist != "All":
    page = page[page.family_history.eq(f_hist)]

if len(page) != len(view):
    st.caption(f"Page filters active · {len(page):,} of {len(view):,} respondents in view")

treated = page.treatment.eq("Yes")

# --------------------------------------------------------------------------
# 2.1  The unit chart
# --------------------------------------------------------------------------
charts.section(
    f"The {len(page):,}, one square each",
    "Every respondent is one square, grouped by whether they report a condition "
    "and whether they ever sought treatment. The clay block is the group this "
    "dashboard is about.",
)

if data.guard(page, "the unit chart", 100):
    cond = page.has_condition.eq("Yes")
    blocks = {
        "Condition · treated": int((cond & treated).sum()),
        "Condition · never treated": int((cond & ~treated).sum()),
        "No condition · treated": int((~cond & treated).sum()),
        "No condition · no treatment": int((~cond & ~treated).sum()),
    }
    charts.show(charts.unit_chart(
        {k: v for k, v in blocks.items() if v},
        colours={"Condition · treated": theme.TEAL,
                 "Condition · never treated": theme.CLAY,
                 "No condition · treated": theme.VIOLET,
                 "No condition · no treatment": theme.SLATE},
        noun="respondents",
    ))
    charts.brief(
        what=f"All {len(page):,} respondents in view, one square each, in four groups.",
        how="Count blocks, not percentages. Each square is a person; hover any block "
            "for its size and share.",
        why="A pie or a stacked bar would give the same four proportions. Only a unit "
            "chart makes the untreated group a countable quantity rather than an "
            "abstraction - which is the difference between 28.9% and 360 people.",
        careful="The tiny violet block is real: a handful of people sought treatment "
                "but skipped the interference question, so they read as 'no condition'. "
                "That is the DQ-12 group, kept deliberately rather than overridden.",
    )

# --------------------------------------------------------------------------
# 2.2  How often it interferes
# --------------------------------------------------------------------------
charts.section(
    "How often it gets in the way",
    "Asked only of people who report a condition. Centred on 'Rarely', so the "
    "heavier side of the scale is visible at a glance.",
)

with_cond = page[page.has_condition.eq("Yes")]
if data.guard(with_cond, "the interference scale", 50):
    share = (with_cond.work_interfere.value_counts(normalize=True) * 100)
    rows = pd.DataFrame(
        [[share.get(a, 0.0) for a in ["Never", "Rarely", "Sometimes", "Often"]]],
        index=["Interferes with work"],
        columns=["Never", "Rarely", "Sometimes", "Often"],
    )
    charts.show(charts.likert(
        rows, negative=["Never"], neutral="Rarely", positive=["Sometimes", "Often"],
        colours=dict(zip(["Never", "Rarely", "Sometimes", "Often"], theme.TEAL_RAMP)),
        height=180,
    ))
    charts.brief(
        what=f"How the {len(with_cond):,} people reporting a condition answered "
             "\"does it interfere with your work?\"",
        how="The bar is centred on 'Rarely'. Everything right of zero is a condition "
            "that interferes at least sometimes; everything left is one that does not.",
        why="A diverging bar is the standard form for an ordered scale. On a 100% "
            "stacked bar the middle category floats and the two wings can't be "
            "compared by eye.",
        careful="'Never' here means the condition exists but does not affect work - "
                "not that there is no condition. Those two answers are different and "
                "the next chart is about why that matters.",
    )

# --------------------------------------------------------------------------
# 2.3  The "never interferes" cliff
# --------------------------------------------------------------------------
charts.section(
    "The cliff between 'never' and 'rarely'",
    "Treatment-seeking against how often the condition interferes with work.",
)

if data.guard(with_cond, "the interference ladder", 50):
    rows = charts.by_group(with_cond, "work_interfere", with_cond.treatment.eq("Yes"))
    rows = rows[rows.group.isin(["Never", "Rarely", "Sometimes", "Often"])]
    order = {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3}
    rows = rows.assign(_o=rows.group.map(order)).sort_values("_o").drop(columns="_o")
    if len(rows) >= 2:
        charts.show(charts.ladder(rows, xtitle="How often it interferes with work"))
        charts.brief(
            what="The share who sought treatment, at each level of work interference.",
            how="The shaded band is the 95% confidence interval - wider where fewer "
                "people gave that answer. Read the step between the first two points.",
            why="An ordered scale on the x-axis with a confidence ribbon. Separate bars "
                "would show the same heights but hide how much of the difference is "
                "sampling noise - here, almost none of it.",
            careful="This is the clearest case of reverse causation in the dataset. "
                    "Treatment plausibly reduces interference, so the low rate among "
                    "'never' is partly people whose condition is managed, and partly "
                    "people who never needed help.",
        )

# --------------------------------------------------------------------------
# 2.4  Family history
# --------------------------------------------------------------------------
charts.section(
    "The factor that outweighs the workplace",
    "Treatment-seeking with and without a family history of mental illness, "
    "within each demographic group. Groups need 20 respondents on both sides.",
)

FACETS = [("Gender", "gender_clean", ["Female", "Male", "Gender-diverse"]),
          ("Age", "age_group", ["18-24", "25-34", "35-44", "45+"])]

if f_hist == "All" and data.guard(page, "the family-history comparison", 100):
    labels, no_hist, with_hist, dn, dy = [], [], [], [], []
    for family, col, levels in FACETS:
        for lv in levels:
            sub = page[page[col].astype(str).eq(lv)]
            a, b = sub[sub.family_history.eq("No")], sub[sub.family_history.eq("Yes")]
            if len(a) >= 20 and len(b) >= 20:
                # Prefix the facet name: without it "Male" and "25-34" sit in
                # one column with nothing saying they come from two questions.
                labels.append(f"{family} · {lv}")
                no_hist.append(a.treatment.eq("Yes").mean() * 100)
                with_hist.append(b.treatment.eq("Yes").mean() * 100)
                dn.append(f"No family history (n={len(a)})")
                dy.append(f"Family history (n={len(b)})")
    if len(labels) >= 2:
        charts.show(charts.dumbbell(
            labels[::-1], no_hist[::-1], with_hist[::-1],
            left_name="No family history", right_name="Family history",
            left_detail=dn[::-1], right_detail=dy[::-1],
        ))
        charts.brief(
            what="Treatment-seeking split by family history, shown separately for each "
                 "gender and age band so the comparison is like-for-like.",
            how="Each row is one demographic group. The grey dot is that group without "
                "a family history, the teal dot is the same group with one. The bar "
                "between them is the effect.",
            why="Small multiples inside one dumbbell: if the gap survives in every "
                "subgroup, it is not an artefact of who happens to be in the sample. "
                "Here it survives in all of them.",
            careful="A family history is also a reason to recognise symptoms earlier "
                    "and know where to go. Part of this gap is exposure to illness, "
                    "part is literacy about it - the survey cannot separate the two.",
        )
    else:
        st.info("Not enough respondents on both sides of family history in any group.")
elif f_hist != "All":
    st.info("This chart compares family history against itself - set the "
            "**Family history** filter above back to *All* to see it.")

# --------------------------------------------------------------------------
# 2.5  Age
# --------------------------------------------------------------------------
charts.section(
    "Treatment-seeking rises with age",
    "And the confidence band widens with it, because the oldest band is the "
    "smallest one in the survey.",
)

if data.guard(page, "the age ladder", 80):
    rows = charts.by_group(page, "age_group", treated)
    if len(rows) >= 2:
        charts.show(charts.ladder(rows, xtitle="Age group", fill=True))
        charts.brief(
            what="The share who sought treatment in each age band.",
            how="Follow the line for the trend; read the width of the band for how "
                "much to trust each point. The 45+ band is visibly less certain.",
            why="An ordered axis with its uncertainty drawn in. Four bars would imply "
                "all four estimates are equally solid - they are not.",
            careful="Age bands were closed at 45+ precisely because only 68 people are "
                    "older than that and just 6 are over 60 (DQ-28). This is not a "
                    "life-course trend; it is four snapshots of different people.",
        )

# --------------------------------------------------------------------------
# 2.6  Severity against access
# --------------------------------------------------------------------------
charts.section(
    "Severity against access",
    "Treatment-seeking in every combination of work interference and how hard "
    "medical leave is to take. Cells with fewer than 10 people are left blank.",
)

if data.guard(page, "the severity grid", 150):
    # "No condition" is not a severity level - the grid is about people who
    # have one, so that row is dropped rather than drawn as a near-zero band.
    grid = page[page.work_interfere.astype(str).ne("No condition")]
    ct = pd.crosstab(grid.work_interfere, grid.leave)
    rate = pd.crosstab(grid.work_interfere, grid.leave,
                       values=grid.treatment.eq("Yes"), aggfunc="mean") * 100
    ct = ct.loc[ct.sum(axis=1) > 0]
    rate = rate.reindex(ct.index)
    if rate.size and rate.notna().to_numpy().sum() > 4:
        charts.show(charts.heat(rate, ct, minimum=10, height=360,
                                label="sought treatment"))
        charts.brief(
            what="Treatment-seeking for each pairing of interference level (rows) and "
                 "perceived ease of taking medical leave (columns).",
            how="Darker is a higher rate. A dot means that combination has fewer than "
                "10 respondents and is not reported. Hover any cell for its exact "
                "rate and count.",
            why="Two categorical dimensions against one measure is what a grid is for. "
                "Grouped bars would need 25 bars and five legend entries to say the "
                "same thing.",
            careful="Read down the columns, not across the rows: the 'Don't know' "
                    "column is the largest in the survey and is a statement about "
                    "knowledge, not about difficulty.",
        )

st.caption(
    f"Showing {len(page):,} of {len(full):,} respondents · "
    f"{st.session_state.get('filter_text', 'No filters')}"
)