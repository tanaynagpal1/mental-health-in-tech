"""Reusable chart forms and the plumbing every page shares.

Pages describe *what* they want plotted; this module owns *how* it looks and
how uncertainty is drawn. Nothing here knows about the survey - pass it rows.

Three rules the whole dashboard inherits from here:

1.  A proportion is never drawn without its confidence interval. Wilson, not
    normal-approximation: at n = 13 (gender-diverse) the normal method puts
    the upper bound above 100%.
2.  One measure, one axis. There is no dual-axis helper and there never will
    be - two scales on one plot invent a correlation the data does not have.
3.  Colour follows the entity, not its rank. A filter that drops a series
    never repaints the survivors.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import theme

# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------
Z = 1.959963985  # 95%


def wilson(successes: int, n: int, z: float = Z) -> tuple[float, float]:
    """95% Wilson score interval for a proportion, returned as percentages.

    Wilson stays inside [0, 1] at small n and with proportions near 0 or 1,
    which is exactly where this dataset lives: 13 gender-diverse respondents,
    4.7% fearing physical-health consequences.
    """
    if n == 0:
        return 0.0, 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, (centre - half)) * 100, min(1.0, (centre + half)) * 100


def rate_ci(flags: pd.Series) -> tuple[float, float, float, int]:
    """(rate %, ci low %, ci high %, n) for a boolean Series."""
    flags = flags.dropna()
    n = len(flags)
    k = int(flags.sum())
    lo, hi = wilson(k, n)
    return (k / n * 100 if n else 0.0), lo, hi, n


def by_group(df: pd.DataFrame, group: str, flag: pd.Series) -> pd.DataFrame:
    """Rate + Wilson interval + n for every level of `group`.

    `flag` is a boolean Series aligned to df, e.g. df.treatment.eq("Yes").
    Levels come back in categorical order when the column is ordered.
    """
    work = pd.DataFrame({"g": df[group].astype(str), "flag": flag.to_numpy()})
    rows = []
    for level, part in work.groupby("g", sort=False):
        rate, lo, hi, n = rate_ci(part["flag"])
        rows.append({"group": level, "rate": rate, "lo": lo, "hi": hi, "n": n})
    out = pd.DataFrame(rows)
    if isinstance(df[group].dtype, pd.CategoricalDtype):
        order = [str(c) for c in df[group].cat.categories]
        out["_o"] = out["group"].map({g: i for i, g in enumerate(order)})
        out = out.sort_values("_o").drop(columns="_o")
    return out.reset_index(drop=True)


# --------------------------------------------------------------------------
# House style
# --------------------------------------------------------------------------
def style(fig: go.Figure, height: int = 380, xtitle: str = "", ytitle: str = "",
          legend: bool = False, margin_l: int = 10) -> go.Figure:
    """Apply the shared layout. automargin is what stops category labels clipping."""
    fig.update_layout(
        height=height,
        showlegend=legend,
        margin=dict(l=margin_l, r=16, t=10, b=40),
        xaxis_title=xtitle or None,
        yaxis_title=ytitle or None,
        hovermode="closest",
        dragmode=False,
    )
    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor=theme.LINE,
                     automargin=True)
    fig.update_yaxes(gridwidth=1, zeroline=False, automargin=True)
    return fig


def show(fig: go.Figure) -> None:
    """Render a figure. Toolbar off - the filters are the interaction model."""
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def pct_axis(fig: go.Figure, axis: str = "x", top: float = 100) -> go.Figure:
    upd = fig.update_xaxes if axis == "x" else fig.update_yaxes
    upd(range=[0, top], ticksuffix="%")
    return fig


# --------------------------------------------------------------------------
# The brief layer
# --------------------------------------------------------------------------
def brief(what: str, how: str, why: str, careful: str) -> None:
    """The four-field explainer that sits under every chart.

    Fixed fields, always in this order, so a reader who opens the second one
    already knows where to look.
    """
    with st.expander("How to read this"):
        st.markdown(
            f"""
            <div class="mt-brief">
              <p><b>What it shows</b><br>{what}</p>
              <p><b>How to read it</b><br>{how}</p>
              <p><b>Why this chart</b><br>{why}</p>
              <p class="care"><b>Careful</b><br>{careful}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def reading_panel() -> None:
    """The page-level panel. Identical on every analysis page, by design."""
    with st.expander("Reading this dashboard"):
        st.markdown(
            """
            **Two denominators.** Every figure runs on the **1,247** cleaned responses,
            except the six employer-support questions, which run on **employees only
            (1,088)** - the 141 self-employed people are their own employer, so asking
            what "your employer" provides has no answer for them. Any chart on that
            basis says so in its subtitle.

            **The sample badge** in the sidebar shows how many respondents survive your
            current filters, and the meter shows what share of the full survey that is.

            **When a chart disappears.** No figure is reported below **n = 20**
            (n = 10 for US states). Filter hard enough and charts are replaced by a
            guard card. That is the rule working, not a bug - a treatment rate from
            six people carries a margin of error wider than the number itself.

            **Colour means the same thing everywhere.** Teal = yes / has support.
            Clay = no. Violet and magenta are second and third series. Grey is never a
            real answer - it means "don't know", background context, or a cell below
            the reporting threshold.

            **Wording.** This survey never asked "do you have a condition?". It asked
            whether mental health interferes with work. So we say **treatment-seeking**
            and **self-reported condition**, never "prevalence of mental illness".
            """
        )


# --------------------------------------------------------------------------
# Form 1 - dot plot with confidence intervals
# --------------------------------------------------------------------------
def dot_ci(rows: pd.DataFrame, highlight: list[str] | None = None,
           baseline: float | None = None, baseline_label: str = "All respondents",
           height: int | None = None, sort: bool = True,
           xmax: float | None = None) -> go.Figure:
    """Horizontal dots with CI whiskers - the default for comparing rates.

    Bars would imply a precision these proportions do not have; the whisker is
    the honest mark. `highlight` names the groups that carry the accent colour,
    everything else recedes to grey.
    """
    d = rows.sort_values("rate") if sort else rows.iloc[::-1]
    hi = set(highlight or d["group"])
    colours = [theme.TEAL if g in hi else theme.SLATE for g in d["group"]]

    fig = go.Figure()
    if baseline is not None:
        fig.add_vline(x=baseline, line_width=1, line_dash="dot", line_color=theme.MUTED,
                      annotation_text=baseline_label, annotation_position="top",
                      annotation_yshift=8,
                      annotation_font_size=11, annotation_font_color=theme.MUTED)

    for (_, r), colour in zip(d.iterrows(), colours):
        fig.add_trace(go.Scatter(
            x=[r.lo, r.hi], y=[r.group, r.group], mode="lines",
            line=dict(color=colour, width=2), opacity=0.35,
            hoverinfo="skip", showlegend=False,
        ))
    fig.add_trace(go.Scatter(
        x=d["rate"], y=d["group"], mode="markers",
        marker=dict(size=11, color=colours, line=dict(width=2, color=theme.SURFACE)),
        customdata=d[["n", "lo", "hi"]],
        hovertemplate="<b>%{y}</b><br>%{x:.1f}%  (95% CI %{customdata[1]:.1f}-%{customdata[2]:.1f})"
                      "<br>n = %{customdata[0]}<extra></extra>",
        showlegend=False,
    ))
    # Value sits past the end of the whisker, never on top of it.
    fig.add_trace(go.Scatter(
        x=d["hi"], y=d["group"], mode="text",
        text=[f"{v:.1f}%" for v in d["rate"]], textposition="middle right",
        textfont=dict(size=11.5, color=theme.INK),
        hoverinfo="skip", showlegend=False, cliponaxis=False,
    ))
    fig = style(fig, height=height or max(240, 34 * len(d) + 96), margin_l=8)
    fig.update_layout(margin_t=28 if baseline is not None else 10)
    # xmax lets a row of small multiples share one scale; without it each
    # panel autoscales and the panels stop being comparable.
    fig.update_xaxes(range=[0, xmax or min(100, d["hi"].max() * 1.26)],
                     ticksuffix="%", showgrid=True)
    fig.update_yaxes(showline=False)
    return fig


# --------------------------------------------------------------------------
# Form 2 - dumbbell
# --------------------------------------------------------------------------
def dumbbell(labels: list[str], left: list[float], right: list[float],
             left_name: str, right_name: str,
             left_colour: str | None = None, right_colour: str | None = None,
             height: int | None = None, suffix: str = "%",
             gap_suffix: str | None = None,
             left_detail: list[str] | None = None,
             right_detail: list[str] | None = None) -> go.Figure:
    """Two paired values per row. The distance between the dots is the subject.

    `left_detail` / `right_detail` name the group behind each dot when the two
    ends mean something different on every row (e.g. a ranking of contrasts).
    They appear in the hover, so the chart stays uncluttered.
    """
    lc = left_colour or theme.SLATE
    rc = right_colour or theme.TEAL
    # A difference between two percentages is percentage points, not percent.
    gsuf = gap_suffix if gap_suffix is not None else ("pp" if suffix == "%" else suffix)

    fig = go.Figure()
    for lab, a, b in zip(labels, left, right):
        fig.add_trace(go.Scatter(
            x=[a, b], y=[lab, lab], mode="lines",
            line=dict(color=theme.LINE, width=3),
            hoverinfo="skip", showlegend=False,
        ))
    for name, vals, colour, detail in ((left_name, left, lc, left_detail),
                                       (right_name, right, rc, right_detail)):
        tmpl = ("<b>%{y}</b><br>%{customdata}: %{x:.1f}" + suffix
                if detail else "<b>%{y}</b><br>" + name + ": %{x:.1f}" + suffix)
        fig.add_trace(go.Scatter(
            x=vals, y=labels, mode="markers", name=name,
            marker=dict(size=13, color=colour, line=dict(width=2, color=theme.SURFACE)),
            customdata=detail,
            hovertemplate=tmpl + "<extra></extra>",
        ))
# Direct-label the gap itself - the one number the reader came for.

    for lab, a, b in zip(labels, left, right):
        fig.add_annotation(x=max(a, b), y=lab, text=f"{abs(b - a):.1f}{gsuf} gap",
                           showarrow=False, xanchor="left", xshift=12,
                           font=dict(size=11, color=theme.MUTED))

    fig = style(fig, height=height or max(200, 46 * len(labels) + 86), legend=True)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    fig.update_xaxes(ticksuffix=suffix, showgrid=True,
                     range=[0, max(max(left), max(right)) * 1.30])
    fig.update_yaxes(showline=False)
    return fig

    # Direct-label the gap itself - the one number the reader came for.
    for lab, a, b in zip(labels, left, right):
        fig.add_annotation(x=max(a, b), y=lab, text=f"{abs(b - a):.1f}{suffix} gap",
                           showarrow=False, xanchor="left", xshift=12,
                           font=dict(size=11, color=theme.MUTED))

    fig = style(fig, height=height or max(200, 46 * len(labels) + 86), legend=True)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    fig.update_xaxes(ticksuffix=suffix, showgrid=True,
                     range=[0, max(max(left), max(right)) * 1.42])
    fig.update_yaxes(showline=False)
    return fig


# --------------------------------------------------------------------------
# Form 3 - diverging stacked Likert
# --------------------------------------------------------------------------
def likert(rows: pd.DataFrame, negative: list[str], neutral: str, positive: list[str],
           colours: dict[str, str] | None = None, height: int | None = None) -> go.Figure:
    """Ordered-scale shares centred on the neutral answer.

    `rows` is indexed by question label, one column per answer, values are
    percentages. The neutral band straddles zero so the eye compares the
    positive and negative wings independently - and so "Don't know" reads as
    the mass it is, not as a slice buried in the middle of a 100% bar.
    """
    palette = colours or {}
    default = {**{a: theme.CLAY for a in negative},
               neutral: theme.SLATE,
               **{a: theme.TEAL for a in positive}}
    shades = {**default, **palette}

    labels = list(rows.index)
    offset = rows[negative].sum(axis=1) + rows[neutral] / 2

    fig = go.Figure()
    order = list(negative) + [neutral] + list(positive)
    for i, ans in enumerate(order):
        if ans not in rows.columns:
            continue
        base = rows[order[:i]].sum(axis=1) if i else 0
        fig.add_trace(go.Bar(
            y=labels, x=rows[ans], base=(base - offset) if i else -offset,
            orientation="h", name=ans,
            marker=dict(color=shades.get(ans, theme.SLATE),
                        line=dict(width=2, color=theme.SURFACE)),
            hovertemplate="<b>%{y}</b><br>" + ans + ": %{x:.1f}%<extra></extra>",
        ))

    fig = style(fig, height=height or max(240, 46 * len(labels) + 110), legend=True)
    fig.update_layout(barmode="relative",
                      bargap=0.42 if len(labels) > 2 else 0.70,
                      legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0))
    fig.add_vline(x=0, line_width=1, line_color=theme.LINE)
    fig.update_xaxes(showgrid=True,
                     tickvals=[-75, -50, -25, 0, 25, 50, 75],
                     ticktext=["75%", "50%", "25%", "0", "25%", "50%", "75%"])
    fig.update_yaxes(showline=False)
    return fig


# --------------------------------------------------------------------------
# Form 4 - ladder (ordered scale with a CI ribbon)
# --------------------------------------------------------------------------
def ladder(rows: pd.DataFrame, colour: str | None = None, fill: bool = False,
           height: int = 340, xtitle: str = "", annotate_ends: bool = True) -> go.Figure:
    """A rate across an ordered score, with its confidence band.

    The ribbon is the point: support score 6 has 49 people, so its interval is
    twice as wide as score 0's. A bare line would hide that completely.
    """
    c = colour or theme.TEAL
    x = rows["group"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        # mode is explicit: plotly draws markers by default on short traces,
        # which would stud the confidence band with stray dots.
        x=x + x[::-1], y=rows["hi"].tolist() + rows["lo"].tolist()[::-1],
        mode="lines", fill="toself", fillcolor="rgba(0,144,158,.12)",
        line=dict(width=0), hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=x, y=rows["rate"], mode="lines+markers",
        line=dict(color=c, width=2.5, shape="spline", smoothing=0.5),
        marker=dict(size=9, color=c, line=dict(width=2, color=theme.SURFACE)),
        fill="tozeroy" if fill else None,
        fillcolor="rgba(0,144,158,.07)" if fill else None,
        customdata=rows[["n", "lo", "hi"]],
        hovertemplate="%{x}<br><b>%{y:.1f}%</b>  (95% CI %{customdata[1]:.1f}-%{customdata[2]:.1f})"
                      "<br>n = %{customdata[0]}<extra></extra>",
        showlegend=False,
    ))
    if annotate_ends and len(rows) > 1:
        for idx, pos in ((0, "bottom"), (len(rows) - 1, "top")):
            r = rows.iloc[idx]
            fig.add_annotation(x=r["group"], y=r["rate"], text=f"{r['rate']:.1f}%",
                               showarrow=False, yshift=16 if pos == "top" else -16,
                               font=dict(size=12, color=theme.INK))

    fig = style(fig, height=height, xtitle=xtitle)
    # Headroom so the end label is not clipped by the plot edge.
    fig.update_yaxes(ticksuffix="%", range=[0, min(100, rows["hi"].max() * 1.14)])
    return fig


# --------------------------------------------------------------------------
# Form 5 - heatmap
# --------------------------------------------------------------------------
def heat(matrix: pd.DataFrame, counts: pd.DataFrame | None = None,
         minimum: int = 20, height: int = 380, suffix: str = "%",
         label: str = "rate", xtitle: str = "", ytitle: str = "") -> go.Figure:
    """Two categorical dimensions against one measure.

    Cells whose own n is below `minimum` are blanked rather than coloured -
    the same threshold rule the rest of the app follows, applied per cell.
    """
    z = matrix.copy().astype(float)
    text = matrix.map(lambda v: f"{v:.0f}{suffix}" if pd.notna(v) else "")

    if counts is not None:
        thin = counts < minimum
        z = z.mask(thin)
        text = text.mask(thin, "\u00b7")

    hover = "<b>%{y}</b> x <b>%{x}</b><br>" + label + ": %{z:.1f}" + suffix
    customdata = None
    if counts is not None:
        customdata = counts.to_numpy()
        hover += "<br>n = %{customdata}"

    fig = go.Figure(go.Heatmap(
        z=z.to_numpy(), x=[str(c) for c in matrix.columns], y=[str(i) for i in matrix.index],
        customdata=customdata,
        colorscale=[[0, theme.SURFACE], [0.5, theme.MINT_LIGHT], [1, theme.TEAL]],
        hovertemplate=hover + "<extra></extra>",
        xgap=2, ygap=2,
        colorbar=dict(ticksuffix=suffix, thickness=10, outlinewidth=0, len=0.8),
    ))

    # Cell labels as annotations, not texttemplate: plotly picks label colour
    # per cell by its own luminance rule and gets the mid-tones inconsistent.
    # One explicit threshold keeps every label legible.
    vmax = float(z.max().max()) if z.notna().to_numpy().any() else 1.0
    vmin = float(z.min().min()) if z.notna().to_numpy().any() else 0.0
    cut = vmin + (vmax - vmin) * 0.62
    for yi, idx in enumerate(matrix.index):
        for xi, col in enumerate(matrix.columns):
            txt = text.iloc[yi, xi]
            if not txt:
                continue
            val = z.iloc[yi, xi]
            colour = (theme.MUTED if txt == "\u00b7"
                      else theme.SURFACE if pd.notna(val) and val >= cut
                      else theme.INK)
            fig.add_annotation(x=str(col), y=str(idx), text=txt, showarrow=False,
                               font=dict(size=12, color=colour))
    # Axis titles matter here more than on most forms: both axes of a
    # cross-tab often carry the same answer labels, and without titles there
    # is nothing on screen saying which question is which.
    fig = style(fig, height=height, xtitle=xtitle, ytitle=ytitle)
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showline=False, autorange="reversed")
    return fig


# --------------------------------------------------------------------------
# Form 6 - Sankey
# --------------------------------------------------------------------------
def sankey(labels: list[str], colours: list[str],
           source: list[int], target: list[int], value: list[int],
           link_colours: list[str] | None = None, height: int = 400) -> go.Figure:
    """Flow between categorical states. Use only when the *path* is the story."""
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=labels, color=colours, pad=22, thickness=16,
                  line=dict(width=0),
                  hovertemplate="%{label}<br>%{value} people<extra></extra>"),
        link=dict(source=source, target=target, value=value,
                  color=link_colours or "rgba(122,135,131,.22)",
                  hovertemplate="%{source.label} -> %{target.label}"
                                "<br>%{value} people<extra></extra>"),
    ))
    fig.update_layout(height=height,
                      margin=dict(l=6, r=6, t=10, b=10),
                      font=dict(size=12.5, color=theme.INK))
    return fig

# --------------------------------------------------------------------------
# Form 7 - forest plot (odds ratios on a log axis)
# --------------------------------------------------------------------------
def forest(rows: pd.DataFrame, height: int | None = None,
           ref: float = 1.0, xtitle: str = "Odds ratio (log scale)") -> go.Figure:
    """Model effects with their intervals, against a reference line at 1.

    Columns: term, or, lo, hi. A term whose interval crosses 1 is drawn grey -
    the model cannot tell its direction apart from no effect, and the chart
    should say so rather than leaving the reader to compare numbers.

    The axis is log because an odds ratio of 0.5 and one of 2.0 are the same
    size of effect in opposite directions; on a linear axis 0.5 looks tiny.
    """
    d = rows.copy()
    d["sig"] = (d["lo"] > ref) | (d["hi"] < ref)
    d["mag"] = (d["or"] / ref).apply(lambda v: abs(math.log(v)))
    d = d.sort_values("mag")

    colours = [theme.TEAL if s and o > ref else theme.CLAY if s else theme.SLATE
               for s, o in zip(d["sig"], d["or"])]

    fig = go.Figure()
    fig.add_vline(x=ref, line_width=1, line_color=theme.MUTED, line_dash="dot")
    fig.add_annotation(x=math.log10(ref) if ref > 0 else 0, xref="x",
                       y=1.0, yref="paper", yshift=14,
                       text="no effect", showarrow=False,
                       font=dict(size=11, color=theme.MUTED))
    for (_, r), colour in zip(d.iterrows(), colours):
        fig.add_trace(go.Scatter(
            x=[r.lo, r.hi], y=[r.term, r.term], mode="lines",
            line=dict(color=colour, width=2), opacity=0.4,
            hoverinfo="skip", showlegend=False,
        ))
    fig.add_trace(go.Scatter(
        x=d["or"], y=d["term"], mode="markers",
        marker=dict(size=11, color=colours, line=dict(width=2, color=theme.SURFACE)),
        customdata=d[["lo", "hi"]],
        hovertemplate="<b>%{y}</b><br>odds ratio %{x:.2f}"
                      "<br>95% CI %{customdata[0]:.2f}-%{customdata[1]:.2f}<extra></extra>",
        showlegend=False,
    ))
    fig = style(fig, height=height or max(260, 30 * len(d) + 110), xtitle=xtitle)
    fig.update_layout(margin_t=30)
    # Explicit padded range - autorange on a log axis clips the widest interval.
    lo_edge = min(d["lo"].min(), ref) / 1.35
    hi_edge = max(d["hi"].max(), ref) * 1.35
    fig.update_xaxes(type="log", showgrid=True,
                     range=[math.log10(lo_edge), math.log10(hi_edge)],
                     tickvals=[0.25, 0.5, 1, 2, 4, 8, 16],
                     ticktext=["0.25", "0.5", "1", "2", "4", "8", "16"])
    fig.update_yaxes(showline=False)
    return fig

# --------------------------------------------------------------------------
# Form 8 - unit chart (one mark per person)
# --------------------------------------------------------------------------
def unit_chart(counts: "dict[str, int]", colours: "dict[str, str]",
               per_row: int | None = None, height: int = 360,
               noun: str = "people") -> go.Figure:
    """One square per respondent, grouped into blocks by category.

    A percentage is an abstraction; a block of 360 squares is a number you can
    look at. Used once, at the top of the page, to put a human unit on the
    headline before the rest of the page goes back to rates.

    `counts` is ordered - the blocks appear in the order given.
    """
    total = sum(counts.values())
    if total == 0:
        return style(go.Figure(), height=height)
    cols = per_row or max(20, int(math.ceil(math.sqrt(total * 2.4))))

    fig = go.Figure()
    i = 0
    for label, count in counts.items():
        xs, ys = [], []
        for _ in range(int(count)):
            xs.append(i % cols)
            ys.append(i // cols)
            i += 1
        share = count / total * 100
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers",
            name=f"{label} · {count:,}",
            marker=dict(symbol="square", size=9, color=colours.get(label, theme.SLATE),
                        line=dict(width=0)),
            hovertemplate=f"<b>{label}</b><br>{count:,} {noun} "
                          f"({share:.1f}%)<extra></extra>",
        ))

    fig = style(fig, height=height, legend=True)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=6, r=6, t=10, b=6),
    )
    fig.update_xaxes(visible=False, showgrid=False, showline=False,
                     range=[-1, cols])
    fig.update_yaxes(visible=False, showgrid=False, showline=False,
                     autorange="reversed", scaleanchor="x", scaleratio=1)
    return fig

# --------------------------------------------------------------------------
# Form 9 - Marimekko (width carries the group size)
# --------------------------------------------------------------------------
def marimekko(counts: pd.DataFrame, colours: "dict[str, str]",
              height: int = 400, xtitle: str = "") -> go.Figure:
    """A 100% stacked bar per group, with bar WIDTH set by that group's n.

    An ordinary stacked bar gives six equal columns, so a band of 62 people
    looks exactly as substantial as one of 276. Here the 62 is a sliver, which
    is the honest picture - the reader sees the share and the weight at once.

    `counts` is a crosstab: index = groups (left to right), columns = answers.
    """
    totals = counts.sum(axis=1)
    grand = totals.sum()
    if grand == 0:
        return style(go.Figure(), height=height)

    widths = (totals / grand * 100).to_numpy()
    centres, edge = [], 0.0
    for w in widths:
        centres.append(edge + w / 2)
        edge += w

    shares = counts.div(totals, axis=0) * 100

    fig = go.Figure()
    base = pd.Series(0.0, index=counts.index)
    for answer in counts.columns:
        fig.add_trace(go.Bar(
            x=centres, y=shares[answer], width=widths, base=base,
            name=str(answer),
            marker=dict(color=colours.get(str(answer), theme.SLATE),
                        line=dict(width=2, color=theme.SURFACE)),
            customdata=np.stack([counts[answer].to_numpy(),
                                 totals.to_numpy(),
                                 [str(i) for i in counts.index]], axis=-1),
            hovertemplate="<b>%{customdata[2]}</b><br>" + str(answer) +
                          ": %{y:.1f}%<br>%{customdata[0]} of %{customdata[1]}"
                          "<extra></extra>",
        ))
        base = base + shares[answer]

    fig = style(fig, height=height, legend=True, xtitle=xtitle)
    fig.update_layout(barmode="stack", bargap=0,
                      legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0))
    fig.update_xaxes(
        tickmode="array", tickvals=centres,
        ticktext=[f"{i}<br><span style='font-size:10px'>n={int(t)}</span>"
                  for i, t in zip(counts.index, totals)],
        range=[0, 100], showgrid=False,
    )
    fig.update_yaxes(ticksuffix="%", range=[0, 100])
    return fig


# --------------------------------------------------------------------------
# Form 10 - several rate series on one axis
# --------------------------------------------------------------------------
def lines(series: "dict[str, pd.DataFrame]", colours: "dict[str, str]",
          height: int = 360, xtitle: str = "", ribbon: bool = True) -> go.Figure:
    """Two or more rates across the same ordered x, on ONE axis.

    Both series must be the same unit - here, percentages - because there is
    no second y-axis and never will be. Two scales on one plot invent a
    relationship the data has not got.

    Each value is a DataFrame from by_group(): group, rate, lo, hi, n.
    """
    fig = go.Figure()
    for name, rows in series.items():
        colour = colours.get(name, theme.TEAL)
        x = rows["group"].tolist()
        if ribbon:
            fig.add_trace(go.Scatter(
                x=x + x[::-1], y=rows["hi"].tolist() + rows["lo"].tolist()[::-1],
                mode="lines", fill="toself", fillcolor=_fade(colour, 0.10),
                line=dict(width=0), hoverinfo="skip", showlegend=False,
            ))
        fig.add_trace(go.Scatter(
            x=x, y=rows["rate"], mode="lines+markers", name=name,
            line=dict(color=colour, width=2.5, shape="spline", smoothing=0.5),
            marker=dict(size=9, color=colour, line=dict(width=2, color=theme.SURFACE)),
            customdata=rows[["n", "lo", "hi"]],
            hovertemplate="%{x}<br><b>" + name + ": %{y:.1f}%</b>"
                          "  (95% CI %{customdata[1]:.1f}-%{customdata[2]:.1f})"
                          "<br>n = %{customdata[0]}<extra></extra>",
        ))

    fig = style(fig, height=height, xtitle=xtitle, legend=True)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    top = max(r["hi"].max() for r in series.values())
    fig.update_yaxes(ticksuffix="%", range=[0, min(100, top * 1.12)])
    return fig


def _fade(hex_colour: str, alpha: float) -> str:
    """'#00909E' -> 'rgba(0,144,158,0.10)'."""
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"

# --------------------------------------------------------------------------
# Form 11 - choropleth (US states)
# --------------------------------------------------------------------------
def choropleth(rows: pd.DataFrame, height: int = 440, suffix: str = "%",
               label: str = "sought treatment") -> go.Figure:
    """US states shaded by a rate. States not in `rows` are left uncoloured.

    Leaving a state blank is the honest treatment of "we do not have enough
    respondents here". Filling it with a neutral colour would put it on the
    same scale as the states we can actually report.

    `rows` needs: group (two-letter code), rate, lo, hi, n.
    """
    fig = go.Figure(go.Choropleth(
        locations=rows["group"], z=rows["rate"],
        locationmode="USA-states",
        colorscale=[[0, theme.SURFACE_2], [0.5, theme.MINT_LIGHT], [1, theme.TEAL]],
        marker=dict(line=dict(color=theme.SURFACE, width=1)),
        customdata=rows[["n", "lo", "hi"]],
        hovertemplate="<b>%{location}</b><br>" + label + ": %{z:.1f}" + suffix +
                      "<br>95% CI %{customdata[1]:.1f}-%{customdata[2]:.1f}"
                      "<br>n = %{customdata[0]}<extra></extra>",
        colorbar=dict(ticksuffix=suffix, thickness=10, outlinewidth=0, len=0.7),
    ))
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)",
                 lakecolor="rgba(0,0,0,0)",
                 landcolor=theme.SURFACE_2, showland=True,
                 subunitcolor=theme.SURFACE, showlakes=False, showframe=False),
    )
    return fig


# --------------------------------------------------------------------------
# Form 12 - precision plot (sample size against certainty)
# --------------------------------------------------------------------------
def precision(rows: pd.DataFrame, height: int = 420,
              xtitle: str = "Respondents (log scale)",
              ytitle: str = "") -> go.Figure:
    """Rate against sample size, with the confidence interval drawn vertically.

    The chart's job is to make "small sample, wide interval" a thing you can
    see rather than a footnote. A country with ten respondents gets a bar
    half the height of the plot, and no amount of labelling does that as well.

    x is log because sample sizes here span 10 to 746.
    """
    d = rows.sort_values("n")
    colours = [theme.TEAL if n >= 20 else theme.CLAY for n in d["n"]]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["n"], y=d["rate"], mode="markers+text",
        marker=dict(size=(d["n"] ** 0.42).clip(9, 34), color=colours,
                    opacity=0.85, line=dict(width=2, color=theme.SURFACE)),
        error_y=dict(type="data", symmetric=False,
                     array=(d["hi"] - d["rate"]), arrayminus=(d["rate"] - d["lo"]),
                     color=theme.LINE, thickness=2, width=0),
        text=d["group"], textposition="top center",
        textfont=dict(size=11, color=theme.MUTED),
        customdata=d[["n", "lo", "hi"]],
        hovertemplate="<b>%{text}</b><br>%{y:.1f}%"
                      "<br>95% CI %{customdata[1]:.1f}-%{customdata[2]:.1f}"
                      " (width %{customdata[2]:.0f}-%{customdata[1]:.0f})"
                      "<br>n = %{customdata[0]}<extra></extra>",
        showlegend=False, cliponaxis=False,
    ))
    fig.add_vline(x=20, line_width=1, line_dash="dot", line_color=theme.MUTED)
    fig.add_annotation(x=math.log10(20), xref="x", y=1.0, yref="paper", yshift=12,
                       text="reporting threshold, n = 20", showarrow=False,
                       font=dict(size=11, color=theme.MUTED))

    fig = style(fig, height=height, xtitle=xtitle, ytitle=ytitle)
    fig.update_layout(margin_t=32)
    # Explicit ticks: plotly's default log minor ticks read "8 9 10 2 3 4",
    # which looks like a broken axis rather than a decade scale.
    fig.update_xaxes(type="log", tickmode="array",
                     tickvals=[10, 20, 50, 100, 200, 500, 1000],
                     ticktext=["10", "20", "50", "100", "200", "500", "1,000"],
                     minor=dict(showgrid=False, ticks=""))
    fig.update_yaxes(ticksuffix="%", range=[0, 100])
    return fig

# --------------------------------------------------------------------------
# Form 13 - waterfall (how a count got from A to B)
# --------------------------------------------------------------------------
def waterfall(labels: list[str], values: list[float], measures: list[str],
              height: int = 320, suffix: str = "") -> go.Figure:
    """Running total with the steps that moved it.

    `measures` is one of "absolute", "relative" or "total" per bar - the same
    vocabulary plotly uses. Used once, to show row counts rather than assert
    them: a reader can add the steps up and get the answer.
    """
    # A "total" bar's height is computed by plotly from the steps before it,
    # so its own y value is ignored - label it with the running total, not
    # with the placeholder that was passed in.
    running, shown = 0.0, []
    for v, m in zip(values, measures):
        if m == "absolute":
            running = v
            shown.append(f"{running:,.0f}")
        elif m == "relative":
            running += v
            shown.append(f"{v:+,.0f}")
        else:
            shown.append(f"{running:,.0f}")

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures, x=labels, y=values,
        text=shown,
        textposition="outside",
        textfont=dict(size=12, color=theme.INK),
        connector=dict(line=dict(color=theme.LINE, width=1)),
        increasing=dict(marker=dict(color=theme.TEAL)),
        decreasing=dict(marker=dict(color=theme.CLAY)),
        totals=dict(marker=dict(color=theme.SLATE)),
        hovertemplate="<b>%{x}</b><br>%{y:,.0f}" + suffix + "<extra></extra>",
    ))
    fig = style(fig, height=height)
    fig.update_layout(margin_t=26)
    fig.update_yaxes(rangemode="tozero")
    return fig


# --------------------------------------------------------------------------
# Form 14 - decision matrix (one mark per documented decision)
# --------------------------------------------------------------------------
def decision_matrix(items: list[dict], colours: "dict[str, str]",
                    per_row: int = 10, height: int = 300) -> go.Figure:
    """One labelled square per decision, grouped by what the decision did.

    `items` are dicts with id, outcome, title. The point is auditability:
    29 squares you can hover, rather than a sentence claiming 29 decisions
    were made.
    """
    groups: dict[str, list[dict]] = {}
    for it in items:
        groups.setdefault(it["outcome"], []).append(it)

    fig = go.Figure()
    row = 0
    ticks, tick_text = [], []
    for outcome, members in groups.items():
        rows_used = (len(members) - 1) // per_row + 1
        ticks.append(row + (rows_used - 1) / 2)
        tick_text.append(f"{outcome}<br><span style='font-size:10px'>"
                         f"{len(members)} decisions</span>")
        xs, ys, text, ids = [], [], [], []
        for i, it in enumerate(members):
            xs.append(i % per_row)
            ys.append(row + i // per_row)
            text.append(f"<b>{it['id']}</b><br>{it['title']}")
            ids.append(it["id"].replace("DQ-", ""))
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers+text", name=outcome,
            marker=dict(symbol="square", size=30,
                        color=colours.get(outcome, theme.SLATE),
                        line=dict(width=3, color=theme.SURFACE)),
            text=ids, textfont=dict(size=10, color=theme.SURFACE),
            customdata=text,
            hovertemplate="%{customdata}<extra></extra>",
            showlegend=False,
        ))
        row += rows_used

    fig = style(fig, height=height)
    fig.update_layout(margin=dict(l=6, r=16, t=10, b=10))
    fig.update_xaxes(visible=False, range=[-0.7, per_row - 0.3])
    fig.update_yaxes(tickmode="array", tickvals=ticks, ticktext=tick_text,
                     autorange="reversed", showgrid=False, showline=False)
    return fig

# --------------------------------------------------------------------------
# Layout helpers
# --------------------------------------------------------------------------
def section(title: str, subtitle: str = "") -> None:
    """A chart heading. Kept out of the figure so it never collides with marks.

    Emitted as ONE line with no indentation. A multi-line f-string whose
    optional subtitle collapses to nothing leaves a whitespace-only line,
    which ends the HTML block - and Markdown then renders the indented
    closing tag as a code block.
    """
    body = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="mt-sec"><h3>{title}</h3>{body}</div>',
                unsafe_allow_html=True)


def finding(stat: str, text: str) -> None:
    st.markdown(
        f"""<div class="mt-finding"><div class="stat">{stat}</div><p>{text}</p></div>""",
        unsafe_allow_html=True,
    )