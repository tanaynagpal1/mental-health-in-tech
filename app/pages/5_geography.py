"""Act 5 - The map.

The brief asks whether mental health and attitudes vary by geography. They do.
But 46 countries answered this survey and 18 of them sent exactly one person,
so two of the six charts on this page exist to show what cannot be reported
rather than what can.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import charts, data, theme

view: pd.DataFrame = st.session_state["view"]
full: pd.DataFrame = st.session_state["full"]

theme.hero(
    "Act five · the map",
    "Who experiences what?",
    "Treatment-seeking runs from 33% in continental Europe to 55% in the US. "
    "Whether that is a real difference or a thin sample is the question this "
    "page keeps asking.",
)

charts.reading_panel()

# --------------------------------------------------------------------------
# Page-local controls
# --------------------------------------------------------------------------
c1, c2 = st.columns([1.6, 2.4])
with c1:
    level = st.segmented_control(
        "Geography", ["Country", "Region", "US state"],
        default="Country", key="geo_level")
with c2:
    min_n = st.slider(
        "Minimum respondents to report a figure", 5, 50,
        value=20, step=5, key="geo_min",
        help="The project rule is 20 for countries and 10 for US states. "
             "Move it and watch places appear and disappear.",
    )

level = level or "Country"
treated = view.treatment.eq("Yes")

# --------------------------------------------------------------------------
# 5.1 / 5.2  The map itself, at the chosen level
# --------------------------------------------------------------------------
if level == "Country":
    charts.section(
        "Treatment-seeking by country",
        f"Countries with at least {min_n} respondents. Everyone else is pooled "
        "into the chart below, not deleted.",
    )
    if data.guard(view, "the country comparison", 100):
        rows = charts.by_group(view, "country", treated)
        big = rows[rows.n >= min_n]
        if len(big) >= 2:
            charts.show(charts.dot_ci(
                big, baseline=treated.mean() * 100,
                baseline_label="All respondents in view",
            ))
            dropped = int(rows[rows.n < min_n].n.sum())
            charts.brief(
                what=f"The share who sought treatment in each country with at least "
                     f"{min_n} respondents, with 95% confidence intervals.",
                how="The dot is the estimate, the bar is the range the true value "
                    "plausibly sits in. Overlapping bars mean the two countries "
                    "cannot be told apart. The dotted line is the overall rate.",
                why="Dots with intervals, not bars. A bar chart would give a country "
                    "of 21 people the same solid, confident block as one of 746.",
                careful=f"{dropped} respondents in smaller countries are not shown "
                        "here. They are not missing from the dashboard - they are "
                        "pooled into regions and counted in every other chart.",
            )
        else:
            st.info(f"No country reaches {min_n} respondents under the current filters.")

elif level == "US state":
    charts.section(
        "Treatment-seeking by US state",
        f"States with at least {min_n} respondents. Uncoloured states did not "
        "send enough people to report a figure.",
    )
    us = view[view.country.eq("United States")]
    us = us[~us.state.isin(["Not applicable", "Not specified"])]
    if data.guard(us, "the state map", 100):
        rows = charts.by_group(us, "state", us.treatment.eq("Yes"))
        big = rows[rows.n >= min_n]
        if len(big) >= 3:
            charts.show(charts.choropleth(big))
            charts.brief(
                what=f"Treatment-seeking across US states with at least {min_n} "
                     f"respondents - {len(big)} states covering "
                     f"{int(big.n.sum()):,} of the {len(us):,} US respondents in view.",
                how="Darker is a higher rate. Hover a state for its figure, its "
                    "confidence interval and how many people it rests on. Grey "
                    "states are below the threshold.",
                why="Geography is the variable, so a map is the form. Leaving thin "
                    "states uncoloured rather than filling them keeps them off the "
                    "same scale as the ones we can actually report.",
                careful="Eleven US respondents gave no state at all (DQ-11) and are "
                        "excluded from this map while remaining in every other "
                        "figure. State was self-reported and never verified.",
            )
        else:
            st.info(f"Fewer than three states reach {min_n} respondents in this view.")

else:
    charts.section(
        "Five regions, three measures",
        "Regions exist so that nobody is dropped for living in a small country. "
        "Same scale on all three panels.",
    )
    if data.guard(view, "the regional comparison", 100):
        MEASURES = [
            ("Sought treatment", view.treatment.eq("Yes")),
            ("Would tell all coworkers", view.coworkers.eq("Yes")),
            ("Fears consequences", view.mental_health_consequence.eq("Yes")),
        ]
        panels = []
        for title, flag in MEASURES:
            r = charts.by_group(view, "region", flag)
            panels.append((title, r[r.n >= min_n]))
        top = max((p[1]["hi"].max() for p in panels if len(p[1])), default=100)
        cols = st.columns(3)
        for col, (title, rows) in zip(cols, panels):
            with col:
                st.markdown(f"**{title}**")
                if len(rows) >= 2:
                    charts.show(charts.dot_ci(rows, height=300,
                                              xmax=min(100, top * 1.3)))
                else:
                    st.caption("Too few respondents per region.")
        charts.brief(
            what="Three different questions, each broken down by the same five "
                 "regions, on one shared scale.",
            how="Read across the panels for one region, not down a single panel. "
                "Europe sits lowest on treatment and highest on openness - the two "
                "do not move together.",
            why="Small multiples. Putting three measures on one chart would need "
                "either three colours competing for the same rows or - far worse - "
                "a second axis.",
            careful="Regions were built for coverage, not homogeneity. \"Rest of "
                    "world\" is 38 people from dozens of countries and means very "
                    "little as a category.",
        )

# --------------------------------------------------------------------------
# 5.3  Sample size against certainty
# --------------------------------------------------------------------------
charts.section(
    "Why some places cannot be reported",
    "Every country with at least eight respondents, plotted by how many people "
    "it has and how wide its confidence interval is.",
)

if data.guard(view, "the precision plot", 100):
    rows = charts.by_group(view, "country", treated)
    rows = rows[rows.n >= 8]
    if len(rows) >= 4:
        charts.show(charts.precision(rows))
        charts.brief(
            what="Treatment-seeking against sample size, one point per country, with "
                 "the 95% interval drawn as a vertical bar.",
            how="Left is a small sample, right is a large one. The bar through each "
                "point is how uncertain that estimate is. Clay points sit below the "
                "reporting threshold; teal points clear it.",
            why="A log x-axis because sample sizes run from 8 to 746. Drawing the "
                "interval vertically turns the caveat into something you look at "
                "instead of something you read underneath.",
            careful="A wide bar does not mean a country is unusual - it means we "
                    "cannot tell. India's ten respondents give an interval roughly "
                    "50 points wide, which is why no India figure appears anywhere.",
        )

# --------------------------------------------------------------------------
# 5.4  Who is in the sample
# --------------------------------------------------------------------------
charts.section(
    "Who this survey actually reached",
    "Treatment-seeking by age band and gender. Cells below the reporting "
    "threshold are left blank rather than estimated.",
)

if data.guard(view, "the demographic grid", 150):
    ct = pd.crosstab(view.age_group, view.gender_clean)
    rate = pd.crosstab(view.age_group, view.gender_clean,
                       values=treated, aggfunc="mean") * 100
    if rate.size >= 4 and (ct >= min_n).to_numpy().sum() >= 2:
        charts.show(charts.heat(rate, ct, minimum=min_n, height=320,
                                label="sought treatment",
                                xtitle="Gender", ytitle="Age group"))
        charts.brief(
            what="Treatment-seeking for every combination of age band and gender.",
            how="Darker is a higher rate; a dot means that cell is below the "
                "threshold. Read down a column to see age within one gender.",
            why="A grid, because two demographics against one measure is exactly "
                "what a grid is for - and it makes the empty cells visible, which "
                "a pair of bar charts would quietly hide.",
            careful="Most cells are blank, and that is the finding. Only 13 "
                    "gender-diverse respondents took this survey and the oldest "
                    "band has 68 people in total (DQ-27, DQ-28).",
        )

# --------------------------------------------------------------------------
# 5.5  What is not on the map
# --------------------------------------------------------------------------
charts.section(
    "What the map leaves out",
    "One square per respondent, coloured by whether their country is large "
    "enough to appear on the country chart at the current threshold.",
)

if data.guard(view, "the coverage chart", 100):
    counts = view.country.value_counts()
    reportable = set(counts[counts >= min_n].index)
    shown = int(view.country.isin(reportable).sum())
    hidden = len(view) - shown
    if shown and hidden:
        charts.show(charts.unit_chart(
            {f"In a country reported individually ({len(reportable)} countries)": shown,
             f"Pooled into regions ({int((counts < min_n).sum())} countries)": hidden},
            colours={f"In a country reported individually ({len(reportable)} countries)": theme.TEAL,
                     f"Pooled into regions ({int((counts < min_n).sum())} countries)": theme.SLATE},
            height=300, noun="respondents",
        ))
        charts.brief(
            what=f"How the {len(view):,} respondents in view split between countries "
                 f"big enough to chart on their own and countries that are not.",
            how="Each square is one person. The grey block is everybody whose country "
                "never appears by name on the first chart of this page.",
            why="An honesty chart. Every dashboard has a set of rows it quietly "
                "declines to show; this one draws them, so the reader can judge how "
                "much of the sample the map is actually describing.",
            careful=f"{hidden} people - {hidden / len(view) * 100:.1f}% of this view - "
                    "are invisible on the country chart. They are still counted in "
                    "the regional panels and in every non-geographic figure.",
        )
        st.caption(
            f"Move the threshold slider above and watch this split change. "
            f"At n = {min_n}, {len(reportable)} countries are reportable and "
            f"{int((counts < min_n).sum())} are not."
        )

st.caption(
    f"Showing {len(view):,} of {len(full):,} respondents · "
    f"{st.session_state.get('filter_text', 'No filters')}"
)