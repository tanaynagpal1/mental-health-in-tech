"""Act 3 - The offer.

What does an employer actually put on the table, and does it change anything?
The page ends on the finding that reframes the rest of the dashboard: the
barrier is not the absence of support, it is not knowing whether you have any.

Runs on EMPLOYEES ONLY (DQ-14). The 141 self-employed respondents are their
own employer, so "does your employer provide X" has no answer for them.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import charts, data, theme

view: pd.DataFrame = st.session_state["view"]
full: pd.DataFrame = st.session_state["full"]

theme.hero(
    "Act three · the offer",
    "Workplace support",
    "More support does go with more treatment. But the largest single answer in "
    "this whole survey is not yes and it is not no - it is don't know.",
)

charts.reading_panel()

# --------------------------------------------------------------------------
# Page-local filters
# --------------------------------------------------------------------------
c1, c2, _ = st.columns([1.2, 1.2, 1.6])
with c1:
    f_tech = st.segmented_control(
        "Tech company", ["All", "Yes", "No"], default="All", key="sup_tech")
with c2:
    f_remote = st.segmented_control(
        "Works remotely", ["All", "Yes", "No"], default="All", key="sup_remote")

emp = view[view.employment_type.eq("Employee")]
if f_tech and f_tech != "All":
    emp = emp[emp.tech_company.eq(f_tech)]
if f_remote and f_remote != "All":
    emp = emp[emp.remote_work.eq(f_remote)]

st.caption(
    f"Employees only · {len(emp):,} of {len(view):,} respondents in view. "
    "The six employer-support questions do not apply to the self-employed (DQ-14)."
)

treated = emp.treatment.eq("Yes")

# --------------------------------------------------------------------------
# 3.1  What employers actually offer
# --------------------------------------------------------------------------
charts.section(
    "What employers actually offer",
    "Six questions about employer provision, centred on \"don't know\". Everything "
    "grey is an employee who could not say either way.",
)

SUPPORT_LABELS = {
    "benefits": "Employer provides mental health benefits",
    "care_options": "Knows what care options are covered",
    "wellness_program": "Mental health raised in a wellness programme",
    "seek_help": "Employer says where to seek help",
    "anonymity": "Anonymity is protected if you use it",
    "mental_vs_physical": "Employer takes it as seriously as physical health",
}

if data.guard(emp, "the support battery", 50):
    rows = {}
    for col, label in SUPPORT_LABELS.items():
        share = emp[col].value_counts(normalize=True) * 100
        rows[label] = {
            "No": float(share.get("No", 0.0)),
            # care_options asks "Not sure" where the others ask "Don't know".
            # Same gap in knowledge, different wording (DQ-22).
            "Don't know": float(share.get("Don't know", 0.0) + share.get("Not sure", 0.0)),
            "Yes": float(share.get("Yes", 0.0)),
        }
    table = pd.DataFrame(rows).T[["No", "Don't know", "Yes"]]
    table = table.sort_values("Don't know")

    charts.show(charts.likert(table, negative=["No"], neutral="Don't know",
                              positive=["Yes"], height=330))
    unsure = table["Don't know"].max()
    worst = table["Don't know"].idxmax()
    charts.brief(
        what=f"How {len(emp):,} employees answered six questions about what their "
             "employer provides.",
        how="Each bar is centred on \"don't know\", so the grey band straddles zero. "
            "Read left of zero for no, right for yes, and the width of the grey for "
            "how many people could not answer at all.",
        why="A diverging stacked bar is the standard form for an ordered answer scale. "
            "On a 100% stacked bar the middle category floats at a different start "
            "point on every row and the two ends cannot be compared by eye.",
        careful=f"\"{worst}\" reaches {unsure:.1f}% don't-know. That is not a missing "
                "value to be cleaned away - it is the answer, and the rest of this "
                "page is about what it costs.",
    )

# --------------------------------------------------------------------------
# 3.2  The support ladder
# --------------------------------------------------------------------------
charts.section(
    "More support, more treatment",
    "Treatment-seeking against the support score - a count of how many of the six "
    "provisions an employee actually has.",
)

scored = emp.dropna(subset=["support_score"])
if data.guard(scored, "the support ladder", 60):
    tagged = scored.assign(band=scored.support_score.astype(int).astype(str))
    rows = charts.by_group(tagged, "band", tagged.treatment.eq("Yes"))
    rows = rows[rows.n >= 20].sort_values("group")
    if len(rows) >= 3:
        charts.show(charts.ladder(rows, xtitle="Support score (0-6)"))
        charts.brief(
            what="The share who sought treatment at each level of employer support.",
            how="Left to right is more provision. The shaded band is the 95% interval "
                "and it widens as the groups get smaller - only a few dozen employees "
                "score 5 or 6.",
            why="An ordered score on the x-axis with its uncertainty drawn in. Bars "
                "would make the dip at the top look like a finding; the ribbon shows "
                "it is well inside the noise.",
            careful="Bands with fewer than 20 employees are dropped entirely. And the "
                    "direction is not settled: people who sought treatment are also "
                    "the people who went looking for what their employer offers.",
        )

# --------------------------------------------------------------------------
# 3.3  Benefits by company size
# --------------------------------------------------------------------------
charts.section(
    "Small companies offer least",
    "Share answering yes, no or don't know to \"does your employer provide mental "
    "health benefits\", by company size. Column width is the number of employees "
    "who answered.",
)

if data.guard(emp, "the company-size breakdown", 100):
    ct = pd.crosstab(emp.no_employees, emp.benefits)
    ct = ct.loc[ct.sum(axis=1) >= 20]
    for col in ["No", "Don't know", "Yes"]:
        if col not in ct.columns:
            ct[col] = 0
    ct = ct[["No", "Don't know", "Yes"]]
    if len(ct) >= 3:
        charts.show(charts.marimekko(
            ct,
            colours={"No": theme.CLAY, "Don't know": theme.SLATE, "Yes": theme.TEAL},
            xtitle="Company size (column width = number of employees)",
        ))
        charts.brief(
            what="Mental health benefits by company size, for every size band with at "
                 "least 20 employees in view.",
            how="Height is the share giving each answer. Width is how many people that "
                "band contains - so a narrow column is a small group and its "
                "percentages should be read with that in mind.",
            why="A Marimekko, not a stacked bar. Equal-width columns would give the "
                "smallest firms the same visual weight as the largest, and the 1-5 "
                "band has a fraction of the respondents of the 1000+ band.",
            careful="Company size was reported by the employee, and nine self-employed "
                    "respondents described a client's headcount rather than their own "
                    "(DQ-13). They are excluded here along with all self-employed.",
        )

# --------------------------------------------------------------------------
# 3.4  The uncertainty curve
# --------------------------------------------------------------------------
charts.section(
    "Not knowing is the barrier",
    "Treatment-seeking against the uncertainty score - how many of seven questions "
    "about employer support the respondent answered \"don't know\" or \"not sure\".",
)

if data.guard(view, "the uncertainty curve", 100):
    tagged = view.assign(band=view.uncertainty_score.astype(int).astype(str))
    rows = charts.by_group(tagged, "band", tagged.treatment.eq("Yes"))
    rows = rows[rows.n >= 20].sort_values("group")
    if len(rows) >= 3:
        charts.show(charts.ladder(rows, colour=theme.VIOLET, fill=True,
                                  xtitle="Uncertainty score (0-7)"))
        charts.brief(
            what="Treatment-seeking as knowledge about employer support falls away. "
                 "Runs on everyone in view, not just employees - uncertainty is a "
                 "state of the respondent, not a property of the employer.",
            how="Left is an employee who could answer every question; right is one who "
                "could answer none. The line falls the whole way.",
            why="An area under an ordered scale. The filled shape makes a monotone "
                "decline legible as a slide rather than eight separate readings.",
            careful="\"Maybe\" is deliberately excluded from this score (DQ-22). Saying "
                    "a disclosure might have consequences is a judgement about risk, "
                    "not a gap in knowledge, and mixing the two would blur the finding.",
        )

# --------------------------------------------------------------------------
# 3.5  Support against openness and fear
# --------------------------------------------------------------------------
charts.section(
    "Support buys openness, and buys down fear",
    "Two different questions plotted against the same support score. Both are "
    "percentages, so both sit on one axis.",
)

if data.guard(scored, "the openness comparison", 80):
    tagged = scored.assign(band=scored.support_score.astype(int).astype(str))
    keep = tagged.band.value_counts()
    keep = set(keep[keep >= 20].index)
    tagged = tagged[tagged.band.isin(keep)]
    if tagged.band.nunique() >= 3:
        openness = charts.by_group(tagged, "band", tagged.supervisor.eq("Yes"))
        fear = charts.by_group(tagged, "band",
                               tagged.mental_health_consequence.eq("Yes"))
        openness = openness.sort_values("group")
        fear = fear.sort_values("group")
        charts.show(charts.lines(
            {"Would tell their supervisor": openness,
             "Fears consequences at work": fear},
            colours={"Would tell their supervisor": theme.TEAL,
                     "Fears consequences at work": theme.CLAY},
            xtitle="Support score (0-6)",
        ))
        charts.brief(
            what="Two outcomes across the same support score: willingness to tell a "
                 "supervisor, and fear of consequences for disclosing.",
            how="The two lines move in opposite directions. Where they cross, an "
                "employee is more likely to speak up than to expect a penalty.",
            why="One axis, two series - both are percentages of the same people, so "
                "they belong on the same scale. A second y-axis would let the two "
                "lines be slid into any relationship you liked.",
            careful="Support, openness and low fear plausibly all come from the same "
                    "kind of employer. This shows they travel together; it does not "
                    "show that adding a benefit makes anyone braver.",
        )

# --------------------------------------------------------------------------
# 3.6  The leave paradox
# --------------------------------------------------------------------------
charts.section(
    "The chart that runs backwards",
    "Treatment-seeking by how hard the respondent thinks medical leave would be. "
    "This one is kept in the dashboard precisely because it does not behave.",
)

LEAVE_ORDER = ["Very difficult", "Somewhat difficult", "Somewhat easy",
               "Very easy", "Don't know"]

if data.guard(view, "the leave comparison", 100):
    rows = charts.by_group(view, "leave", view.treatment.eq("Yes"))
    rows = rows[rows.n >= 20]
    rows = rows.assign(_o=rows.group.map({v: i for i, v in enumerate(LEAVE_ORDER)}))
    rows = rows.sort_values("_o", ascending=False).drop(columns="_o")
    if len(rows) >= 3:
        charts.show(charts.dot_ci(
            rows, sort=False,
            highlight=["Very difficult", "Somewhat difficult"],
            baseline=view.treatment.eq("Yes").mean() * 100,
            baseline_label="Everyone in view",
        ))
        charts.brief(
            what="Treatment-seeking by perceived ease of taking medical leave, in the "
                 "survey's own order rather than sorted by rate.",
            how="The two highlighted rows are the ones who called leave difficult - and "
                "they are the most treated, not the least. The dotted line is the "
                "overall rate for comparison.",
            why="A dot plot in scale order, deliberately not sorted by value. Sorting "
                "would hide the reversal by putting the difficult answers where a "
                "reader expects them.",
            careful="This is selection, not causation. You find out how hard leave is "
                    "by trying to take it - so the people who know it is difficult are "
                    "disproportionately people who have already sought treatment. Read "
                    "it as evidence about who answers, not about what leave policy does.",
        )

st.caption(
    f"Showing {len(emp):,} employees of {len(full):,} respondents · "
    f"{st.session_state.get('filter_text', 'No filters')}"
)