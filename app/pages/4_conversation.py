"""Act 4 - The silence.

Act three said support goes with treatment. This page says why the support
often goes unused: the same people, at the same employer, treat a mental
health condition and a physical one as two completely different things to
admit to.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import charts, data, theme

view: pd.DataFrame = st.session_state["view"]
full: pd.DataFrame = st.session_state["full"]

theme.hero(
    "Act four · the silence",
    "Can we talk?",
    "One in five fears consequences for disclosing a mental health condition. "
    "One in twenty fears the same for a physical one. Same people, same employer, "
    "same question asked twice.",
)

charts.reading_panel()

# --------------------------------------------------------------------------
# Page-local filter
# --------------------------------------------------------------------------
c1, _ = st.columns([1.5, 2.5])
with c1:
    f_fear = st.segmented_control(
        "Fears consequences at work", ["All", "Yes", "Maybe", "No"],
        default="All", key="talk_fear")

page = view
if f_fear and f_fear != "All":
    page = page[page.mental_health_consequence.eq(f_fear)]

if len(page) != len(view):
    st.caption(f"Page filter active · {len(page):,} of {len(view):,} respondents in view")

# --------------------------------------------------------------------------
# 4.1  Mental against physical
# --------------------------------------------------------------------------
charts.section(
    "The same question, asked twice",
    "The survey asked each of these two questions once about mental health and "
    "once about physical health. The distance between the dots is the stigma.",
)

PAIRS = [
    ("Fears negative consequences at work",
     "mental_health_consequence", "phys_health_consequence"),
    ("Would raise it in a job interview",
     "mental_health_interview", "phys_health_interview"),
]

if data.guard(page, "the mental-versus-physical comparison", 100):
    labels, phys, ment = [], [], []
    for label, m_col, p_col in PAIRS:
        labels.append(label)
        phys.append(page[p_col].eq("Yes").mean() * 100)
        ment.append(page[m_col].eq("Yes").mean() * 100)
    charts.show(charts.dumbbell(
        labels, phys, ment,
        left_name="About physical health", right_name="About mental health",
        left_colour=theme.SLATE, right_colour=theme.CLAY,
    ))
    charts.brief(
        what="The share answering \"yes\" to two questions, asked separately about "
             "mental and physical health.",
        how="Each row is one question. The grey dot is the physical-health version, "
            "the clay dot the mental-health version. The gap is the whole point - "
            "and note that the two rows run in opposite directions.",
        why="A dumbbell puts the comparison itself on screen. Four separate bars "
            "would make the reader hold two numbers in their head and subtract.",
        careful="These are the same respondents answering both versions, so the gap "
                "is not a sampling artefact. It is still a statement about what "
                "people expect, not about what employers actually do.",
    )

# --------------------------------------------------------------------------
# 4.2  Who do you tell?
# --------------------------------------------------------------------------
charts.section(
    "Who do you tell?",
    "Willingness to discuss a mental health condition with coworkers, against "
    "willingness to discuss it with a direct supervisor.",
)

if data.guard(page, "the disclosure matrix", 100):
    ct = pd.crosstab(page.coworkers, page.supervisor)
    if ct.size >= 4:
        charts.show(charts.heat(ct, ct, minimum=1, height=340,
                                suffix="", label="respondents",
                                xtitle="Would tell their supervisor",
                                ytitle="Would tell coworkers"))
        charts.brief(
            what="Every combination of the two disclosure questions, with the number "
                 "of respondents in each cell.",
            how="Rows are coworkers, columns are the supervisor. The top-left cell is "
                "people who would tell nobody; the bottom-right is people who would "
                "tell everyone. Darker means more people.",
            why="A cross-tabulation is what a grid is for. Two separate bar charts "
                "would show the margins and lose the interesting part - the "
                "combinations, especially the off-diagonal ones.",
            careful="This is willingness, not behaviour. Nobody was asked whether they "
                    "actually told anyone, only whether they would.",
        )
        # Spelled out rather than assembled from the raw answer values -
        # "would tell yes to their supervisor" is not a sentence.
        CW = {"Yes": "all of their coworkers",
              "Some of them": "some of their coworkers",
              "No": "none of their coworkers"}
        SV = {"Yes": "would tell their supervisor",
              "Some of them": "would tell some supervisors",
              "No": "would not tell their supervisor"}
        top = ct.stack().idxmax()
        st.caption(
            f"Largest single group — **{int(ct.stack().max()):,} people**: they would "
            f"tell {CW.get(top[0], top[0])}, and {SV.get(top[1], top[1])}."
        )

# --------------------------------------------------------------------------
# 4.3  Openness against fear
# --------------------------------------------------------------------------
charts.section(
    "Openness does not cancel fear",
    "How the three disclosure groups divide on whether they expect consequences "
    "at work.",
)

if data.guard(page, "the disclosure flow", 100):
    flow = pd.crosstab(page.coworkers, page.mental_health_consequence)
    for col in ["No", "Maybe", "Yes"]:
        if col not in flow.columns:
            flow[col] = 0
    flow = flow[["No", "Maybe", "Yes"]]
    left = [f"Tells {i.lower()} coworkers · {int(flow.loc[i].sum()):,}"
            if i != "No" else f"Tells no coworkers · {int(flow.loc[i].sum()):,}"
            for i in flow.index]
    right = [f"No fear · {int(flow['No'].sum()):,}",
             f"Maybe · {int(flow['Maybe'].sum()):,}",
             f"Fears consequences · {int(flow['Yes'].sum()):,}"]

    src, tgt, val, lcol = [], [], [], []
    tint = {0: "rgba(0,144,158,.22)", 1: "rgba(122,135,131,.18)",
            2: "rgba(200,90,52,.26)"}
    for i in range(len(flow.index)):
        for j in range(3):
            v = int(flow.iloc[i, j])
            if v:
                src.append(i); tgt.append(len(left) + j); val.append(v)
                lcol.append(tint[j])

    charts.show(charts.sankey(
        labels=left + right,
        colours=[theme.SLATE] * len(left) + [theme.TEAL, theme.SLATE, theme.CLAY],
        source=src, target=tgt, value=val, link_colours=lcol, height=380,
    ))
    charts.brief(
        what="Where each disclosure group lands on fear of consequences.",
        how="Left is who they would tell, right is what they expect to happen. "
            "Ribbon thickness is people. Follow the band out of any left-hand node.",
        why="A flow, because the question is how one answer distributes across "
            "another. A grouped bar would give the same numbers without showing "
            "that the middle group is where almost everyone is.",
        careful="Direction is unknowable here. Fear may keep people quiet, or being "
                "open may have taught them what the consequences are. The survey "
                "asked both questions at the same moment.",
    )

# --------------------------------------------------------------------------
# 4.4  Seeing it happen to someone else
# --------------------------------------------------------------------------
charts.section(
    "What witnessing a penalty does",
    "Respondents who have seen a colleague suffer consequences for a mental "
    "health condition, against those who have not.",
)

OUTCOMES = [
    ("Sought treatment", "treatment", "Yes"),
    ("Would tell their supervisor", "supervisor", "Yes"),
    ("Fears consequences at work", "mental_health_consequence", "Yes"),
]

seen = page[page.obs_consequence.eq("Yes")]
unseen = page[page.obs_consequence.eq("No")]

if len(seen) >= 20 and len(unseen) >= 20:
    labels, a_vals, b_vals = [], [], []
    for label, col, val in OUTCOMES:
        labels.append(label)
        a_vals.append(unseen[col].eq(val).mean() * 100)
        b_vals.append(seen[col].eq(val).mean() * 100)
    charts.show(charts.dumbbell(
        labels, a_vals, b_vals,
        left_name=f"Has not seen it happen (n={len(unseen):,})",
        right_name=f"Has seen it happen (n={len(seen):,})",
        left_colour=theme.SLATE, right_colour=theme.VIOLET,
    ))
    charts.brief(
        what="Three different outcomes, each split by whether the respondent has "
             "witnessed a colleague penalised for a mental health condition.",
        how="Grey has not seen it, violet has. Read the direction of each row "
            "separately - they do not all move the same way.",
        why="One dumbbell across three outcomes, so the pattern is visible as a "
            "shape. Three separate charts would make the reader assemble it.",
        careful="Witnessing is self-reported and unverifiable, and the people most "
                "attuned to these consequences may also be the most likely to "
                "notice them. Treat it as association.",
    )
    st.caption(
        "Worth pausing on: witnessing a penalty goes with **more** treatment-seeking "
        "and **less** willingness to tell a supervisor. People do not stop dealing "
        "with it — they stop talking about it at work."
    )
else:
    st.info("Too few respondents on one side of the witnessing question in this view.")

# --------------------------------------------------------------------------
# 4.5  The full answer, not just the yes
# --------------------------------------------------------------------------
charts.section(
    "The mass in the middle",
    "The same four questions as the first chart, but showing every answer. "
    "Centred on \"maybe\", which is where most people actually sit.",
)

ROWS = {
    "Consequences · mental health": "mental_health_consequence",
    "Consequences · physical health": "phys_health_consequence",
    "Interview · mental health": "mental_health_interview",
    "Interview · physical health": "phys_health_interview",
}

if data.guard(page, "the full answer breakdown", 100):
    table = {}
    for label, col in ROWS.items():
        share = page[col].value_counts(normalize=True) * 100
        table[label] = {"No": float(share.get("No", 0.0)),
                        "Maybe": float(share.get("Maybe", 0.0)),
                        "Yes": float(share.get("Yes", 0.0))}
    frame = pd.DataFrame(table).T[["No", "Maybe", "Yes"]]
    charts.show(charts.likert(frame, negative=["No"], neutral="Maybe",
                              positive=["Yes"], height=280))
    charts.brief(
        what="Full answer distributions for the two consequence questions and the "
             "two interview questions.",
        how="Bars are centred on \"maybe\". Left of zero is no, right is yes, and "
            "the grey band across the middle is everyone who would not commit.",
        why="The first chart on this page showed only the \"yes\" share, which hides "
            "that 38% answered \"maybe\" to the mental-health consequence question. "
            "A diverging stacked bar shows the whole scale.",
        careful="\"Maybe\" is deliberately not counted as uncertainty anywhere in this "
                "dashboard (DQ-22). It is a judgement about risk, not a gap in "
                "knowledge, and it does not enter the uncertainty score.",
    )

# --------------------------------------------------------------------------
# 4.6  Does telling anyone go with getting help?
# --------------------------------------------------------------------------
charts.section(
    "Disclosure against treatment",
    "Treatment-seeking in every combination of the two disclosure questions. "
    "Cells with fewer than 20 respondents are left blank.",
)

if data.guard(page, "the disclosure-treatment grid", 150):
    ct = pd.crosstab(page.coworkers, page.supervisor)
    rate = pd.crosstab(page.coworkers, page.supervisor,
                       values=page.treatment.eq("Yes"), aggfunc="mean") * 100
    if rate.size >= 4 and rate.notna().to_numpy().sum() >= 4:
        charts.show(charts.heat(rate, ct, minimum=20, height=340,
                                label="sought treatment",
                                xtitle="Would tell their supervisor",
                                ytitle="Would tell coworkers"))
        charts.brief(
            what="The same grid as above, but coloured by the share who sought "
                 "treatment rather than by how many people are in each cell.",
            how="Darker is a higher treatment rate. A dot means that combination has "
                "fewer than 20 respondents, so no figure is reported for it.",
            why="Reusing one grid for two measures lets the reader carry the shape of "
                "the first chart into the second and see where the two disagree.",
            careful="Compare this with the count grid above before drawing anything "
                    "from it: the darkest cells here are not the busiest cells there, "
                    "and several combinations are too small to report at all.",
        )

st.caption(
    f"Showing {len(page):,} of {len(full):,} respondents · "
    f"{st.session_state.get('filter_text', 'No filters')}"
)