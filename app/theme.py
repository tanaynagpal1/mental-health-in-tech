"""Single source of visual truth for the MIND//TECH dashboard.

Colours, CSS and the Plotly template live here and nowhere else, so a design
change is one edit. Pages import from this module; they never hard-code a hex.
"""

import time

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --------------------------------------------------------------------------
# Tokens (from the MIND//TECH spec)
# --------------------------------------------------------------------------
BG         = "#F7F8F5"
SURFACE    = "#FFFFFF"
SURFACE_2  = "#F0F3EF"
INK        = "#17201D"
MUTED      = "#69736F"
LINE       = "#DFE5DF"

# Interface accents - pastels, atmosphere only
MINT       = "#86D8B2"
MINT_LIGHT = "#CCEFE0"
LAVENDER   = "#AAA0EB"
PEACH      = "#F3B39F"

# Data colours - deeper steps of the same hues.
# Validated all-pairs (not just adjacent, because the scatter, bubble and
# choropleth need every pair separable):
#   CVD deltaE 9.0 worst pair · normal-vision 17.5 · contrast all >= 3:1 on white.
# The pastels above FAIL those checks, which is why charts never use them.
TEAL       = "#00909E"
VIOLET     = "#5B4BD6"
CLAY       = "#C85A34"
MAGENTA    = "#B5006E"

# SLATE is NOT a series colour - it is below the chroma floor and reads as grey.
# That is exactly what we want it to mean: don't-know, context, below threshold.
SLATE      = "#7A8783"
DEEMPH     = SLATE

# Ordinal ramp for ordered scales (Never -> Often). One hue, light to dark.
# Validated: lightness monotone, adjacent dL >= 0.06, light end 2.24:1 on white.
TEAL_RAMP = ["#5FB8C2", "#2A9CA8", "#007B87", "#00555E"]

SERIES = [TEAL, VIOLET, CLAY, MAGENTA]
C_YES, C_NO, C_UNSURE = TEAL, CLAY, SLATE          # fixed meanings across the app

RADIUS_L, RADIUS_M, RADIUS_S = 24, 20, 12


# --------------------------------------------------------------------------
# Plotly template
# --------------------------------------------------------------------------
def register_plotly_template() -> None:
    """One template every chart inherits: transparent surface, soft grid."""
    pio.templates["mindtech"] = go.layout.Template(
        layout=go.Layout(
            colorway=SERIES,
            font=dict(family="Inter, system-ui, sans-serif", size=13, color=INK),
            title=dict(font=dict(family="Manrope, Inter, sans-serif", size=17), x=0, xanchor="left"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=48, b=10),
            xaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE,
                       title_font=dict(size=12, color=MUTED), tickfont=dict(color=MUTED)),
            yaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE,
                       title_font=dict(size=12, color=MUTED), tickfont=dict(color=MUTED)),
            hoverlabel=dict(bgcolor=SURFACE, bordercolor=LINE,
                            font=dict(family="Inter, sans-serif", size=12, color=INK)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                        font=dict(size=12, color=MUTED)),
            transition=dict(duration=450, easing="cubic-in-out"),
        )
    )
    pio.templates.default = "mindtech"


# --------------------------------------------------------------------------
# CSS
# --------------------------------------------------------------------------
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', system-ui, sans-serif; }}
h1, h2, h3 {{ font-family: 'Manrope', 'Inter', sans-serif; letter-spacing: -0.03em; }}

/* ---------------- Hero: ambient light field ---------------- */
.mt-hero {{
  position: relative; overflow: hidden; isolation: isolate;
  border: 1px solid {LINE}; border-radius: {RADIUS_L}px;
  background: {SURFACE_2}; padding: 34px 30px; margin-bottom: 18px;
}}
.mt-blob {{
  position: absolute; border-radius: 50%; will-change: transform, opacity;
  animation: mt-drift var(--dur,16s) ease-in-out infinite alternate,
             mt-glow  var(--gdur,9s) ease-in-out infinite;
}}
.mt-b1 {{ width:300px; height:300px; right:-60px; top:-110px; --dur:19s; --gdur:8s;
          background: radial-gradient(circle at 35% 35%, {MINT}, transparent 68%); }}
.mt-b2 {{ width:260px; height:260px; right:130px; bottom:-150px; --dur:23s; --gdur:11s;
          animation-delay:-5s,-3s;
          background: radial-gradient(circle at 40% 40%, {LAVENDER}, transparent 68%); }}
.mt-b3 {{ width:220px; height:220px; right:-30px; bottom:-90px; --dur:17s; --gdur:13s;
          animation-delay:-9s,-6s;
          background: radial-gradient(circle at 45% 45%, {PEACH}, transparent 68%); }}
.mt-b4 {{ width:200px; height:200px; right:250px; top:-90px; --dur:27s; --gdur:10s;
          animation-delay:-13s,-8s;
          background: radial-gradient(circle at 50% 50%, {MINT_LIGHT}, transparent 70%); }}
.mt-b5 {{ width:150px; height:150px; right:60px; top:40%; --dur:21s; --gdur:7s;
          animation-delay:-4s,-2s;
          background: radial-gradient(circle at 50% 50%, {LAVENDER}, transparent 70%); }}
@keyframes mt-drift {{
  0%   {{ transform: translate3d(0,0,0) scale(1); }}
  50%  {{ transform: translate3d(-26px,22px,0) scale(1.08); }}
  100% {{ transform: translate3d(14px,-18px,0) scale(.94); }}
}}
@keyframes mt-glow {{ 0%,100% {{ opacity:.30; }} 50% {{ opacity:.72; }} }}
.mt-hero::after {{
  content:""; position:absolute; inset:-40%; pointer-events:none;
  background: radial-gradient(38% 50% at 50% 50%, rgba(255,255,255,.55), transparent 70%);
  animation: mt-sweep 24s linear infinite;
}}
@keyframes mt-sweep {{ 0% {{ transform: translate3d(-45%,10%,0); }}
                       100% {{ transform: translate3d(55%,-10%,0); }} }}
@media (prefers-reduced-motion: reduce) {{
  .mt-blob {{ animation: none; opacity: .5; }}
  .mt-hero::after {{ animation: none; }}
}}
.mt-hero-inner {{ position: relative; max-width: 34rem; }}
.mt-eyebrow {{ font-size: 10.5px; letter-spacing: .16em; text-transform: uppercase;
               color: {MUTED}; font-weight: 700; }}
.mt-hero h1 {{ font-size: clamp(26px, 4vw, 40px); font-weight: 800; line-height: 1.05;
               margin: 10px 0 8px; color: {INK}; }}
.mt-hero p {{ color: {MUTED}; margin: 0; font-size: 14.5px; }}

/* ---------------- Cards, KPIs, small pieces ---------------- */
.mt-card {{ background: {SURFACE}; border: 1px solid {LINE};
            border-radius: {RADIUS_M}px; padding: 16px 18px; }}
.mt-kpi {{ background: {SURFACE}; border: 1px solid {LINE};
           border-radius: {RADIUS_M}px; padding: 14px 16px; height: 100%; }}
.mt-kpi.accent {{ background: linear-gradient(180deg, {MINT_LIGHT}, {SURFACE});
                  border-color: {MINT}; }}

/* Clickable KPI cards: a transparent button sits over the whole card. */
[class*="st-key-mtkpi-"] {{ position: relative; }}
[class*="st-key-mtkpi-"] [data-testid="stButton"] {{
  position: absolute; inset: 0; margin: 0; z-index: 3;
}}
[class*="st-key-mtkpi-"] [data-testid="stButton"] button {{
  width: 100%; height: 100%; opacity: 0; border: none;
  background: transparent; cursor: pointer;
}}
[class*="st-key-mtkpi-"] .mt-kpi {{
  transition: border-color .18s ease, transform .18s ease, box-shadow .18s ease;
}}
[class*="st-key-mtkpi-"]:hover .mt-kpi {{
  border-color: {MINT}; transform: translateY(-2px);
  box-shadow: 0 6px 16px -10px rgba(23,32,29,.35);
}}
.mt-kpi-note {{ margin: 10px 2px 0; font-size: 13px; color: {MUTED}; }}
.mt-answer {{ margin: 18px 0 2px; }}
.mt-answer .q {{ font-family: 'Manrope', sans-serif; font-weight: 800;
                 font-size: 17px; letter-spacing: -.02em; color: {INK};
                 padding-left: 12px; border-left: 3px solid {TEAL}; }}
.mt-kpi-note b {{ color: {INK}; }}
.mt-kpi .lab {{ font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
                color: {MUTED}; font-weight: 700; }}
.mt-kpi .val {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 29px;
                letter-spacing: -.045em; margin-top: 6px; font-variant-numeric: tabular-nums;
                color: {INK}; }}
.mt-kpi .sub {{ font-size: 12px; color: {MUTED}; }}
.mt-pill {{ display:inline-block; background:{MINT_LIGHT}; color:#0C5B45;
            border-radius:999px; padding:3px 10px; font-size:11px; font-weight:700; }}
.mt-guard {{ border:1px solid {PEACH}; background:#FDF3EF; border-radius:{RADIUS_M}px;
             padding:14px 16px; }}
.mt-finding {{ border:1px solid {LINE}; border-radius:{RADIUS_M}px; padding:16px;
               background:{SURFACE}; height:100%; }}
.mt-finding .stat {{ font-family:'Manrope',sans-serif; font-weight:800; font-size:26px;
                     letter-spacing:-.04em; color:{TEAL}; }}
.mt-finding p {{ margin:6px 0 0; color:{MUTED}; font-size:13px; }}

/* ---------------- Sidebar ---------------- */
section[data-testid="stSidebar"] {{ background: {SURFACE_2}; border-right: 1px solid {LINE};
                                    min-width: 320px !important; }}

/* Collapsing must actually give the space back.
   Streamlit collapses by sliding the sidebar out AND shrinking it to zero
   width so the main area reflows. Our min-width above is !important, so it
   wins over the shrink and the sidebar sits off-screen still occupying
   320px - leaving a dead margin. Release it while collapsed. */
section[data-testid="stSidebar"][aria-expanded="false"] {{
  min-width: 0 !important;
  width: 0 !important;
  overflow: hidden !important;
}}

/* Filter block */
.mt-side-h {{ font-size: 10.5px; letter-spacing: .14em; text-transform: uppercase;
              color: {MUTED}; font-weight: 700; margin: 16px 0 4px; }}
.mt-chips {{ display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }}
.mt-chip {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: 999px;
            padding: 2px 9px; font-size: 11px; color: {INK}; }}
.mt-chip.none {{ color: {MUTED}; }}
.mt-meter {{ height: 6px; border-radius: 999px; background: {LINE};
             overflow: hidden; margin-top: 8px; }}
.mt-meter > span {{ display: block; height: 100%; border-radius: 999px;
                    background: linear-gradient(90deg, {TEAL}, {VIOLET});
                    transition: width .45s cubic-bezier(.4,0,.2,1); }}

/* ---------------- Chart section headings & the brief layer ---------------- */
.mt-sec {{ margin: 26px 0 6px; }}
.mt-sec h3 {{ font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 19px;
              letter-spacing: -.03em; color: {INK}; margin: 0; }}
.mt-sec p {{ margin: 4px 0 0; color: {MUTED}; font-size: 13.5px; max-width: 58rem; }}

.mt-brief p {{ margin: 0 0 10px; font-size: 13.5px; color: {INK}; line-height: 1.55; }}
.mt-brief p b {{ font-size: 11px; letter-spacing: .1em; text-transform: uppercase;
                 color: {MUTED}; }}
.mt-brief p.care {{ margin-bottom: 0; padding-left: 12px;
                    border-left: 3px solid {PEACH}; }}
.mt-brief p.care b {{ color: {CLAY}; }}

section[data-testid="stSidebar"] ~ * [data-testid="stExpander"] details {{
  border: 1px solid {LINE}; border-radius: {RADIUS_M}px; background: {SURFACE};
}}
section[data-testid="stSidebar"] ~ * [data-testid="stExpander"] summary {{
  font-size: 13px; color: {MUTED}; font-weight: 600;
}}

[data-testid="stMetricValue"] {{ font-family: 'Manrope', sans-serif; }}
footer, #MainMenu {{ visibility: hidden; }}
/* Brand - change max-width to resize the wordmark, nothing else */
.mt-brand {{ max-width: 320px; margin: -26px 0 10px 2px; }}
[data-testid="stSidebarHeader"] {{ padding-top: 0 !important; padding-bottom: 0 !important;
                                   min-height: 0 !important; }}
section[data-testid="stSidebar"] > div:first-child {{ padding-top: 0 !important; }}
.mt-brand svg {{ display: block; width: 100%; height: auto; }}

/* Our own nav links (st.page_link) */
section[data-testid="stSidebar"] [data-testid="stPageLink"] a,
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
  border-radius: {RADIUS_S}px !important;
  padding: 7px 12px !important;
  margin: 3px 0 !important;
  position: relative;
  overflow: visible;
  transition: background .18s ease, transform .18s ease, box-shadow .18s ease;
}}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
  background: {SURFACE}; transform: translateX(3px);
  box-shadow: 0 1px 2px rgba(23,32,29,.06);
}}

section[data-testid="stSidebar"] [data-testid="stPageLink"] a p,
section[data-testid="stSidebar"] [data-testid="stPageLink"] a span {{
  font-size: 16px !important; font-weight: 600 !important; line-height: 1.3 !important;
}}
section[data-testid="stSidebar"] [data-testid="stPageLink"] [data-testid="stIconMaterial"] {{
  font-size: 20px !important; margin-right: 8px;
}}
</style>
"""


def apply_theme() -> None:
    """Inject the CSS and register the Plotly template. Called once per rerun."""
    st.markdown(CSS, unsafe_allow_html=True)
    register_plotly_template()


def hero(eyebrow: str, title: str, subtitle: str) -> None:
    """The animated hero panel: five drifting lights plus a slow sheen."""
    st.markdown(
        f"""
        <div class="mt-hero">
          <div class="mt-blob mt-b1"></div><div class="mt-blob mt-b2"></div>
          <div class="mt-blob mt-b3"></div><div class="mt-blob mt-b4"></div>
          <div class="mt-blob mt-b5"></div>
          <div class="mt-hero-inner">
            <div class="mt-eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi(label: str, value: str, sub: str = "", accent: bool = False) -> None:
    """One KPI tile."""
    st.markdown(
        f"""<div class="mt-kpi{' accent' if accent else ''}">
              <div class="lab">{label}</div>
              <div class="val">{value}</div>
              <div class="sub">{sub}</div>
            </div>""",
        unsafe_allow_html=True,
    )

def kpi_row(tiles: list[dict], state_key: str = "kpi_focus", default: int = 3) -> int:
    """A row of KPI tiles where clicking one moves the accent to it.

    `tiles` is a list of dicts with keys: label, value, sub, note.

    Each tile is a plain HTML card with a transparent Streamlit button laid
    over it, so the whole card is the click target while the card itself stays
    ours to style. The button carries a zero-width label because Streamlit
    buttons take text, not markup.

    Returns the focused index, so a page can react to it if it wants to.
    """
    focus = st.session_state.get(state_key)
    if focus is None:
        # No explicit click: rotate. The seed is set once per browser session,
        # so a reload starts somewhere different; page_visit then advances it
        # on every navigation back to this page.
        seed = st.session_state.setdefault("kpi_seed",
                                           int(time.time()) % len(tiles))
        focus = (seed + st.session_state.get("page_visit", 0)) % len(tiles)
    focus = min(focus, len(tiles) - 1)

    cols = st.columns(len(tiles))
    for i, (col, t) in enumerate(zip(cols, tiles)):
        with col:
            with st.container(key=f"mtkpi-{i}"):
                st.markdown(
                    f'<div class="mt-kpi{" accent" if i == focus else ""}">'
                    f'<div class="lab">{t["label"]}</div>'
                    f'<div class="val">{t["value"]}</div>'
                    f'<div class="sub">{t.get("sub", "")}</div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("\u200b", key=f"mtkpi_btn_{i}",
                             help=t.get("label", ""), width="stretch"):
                    st.session_state[state_key] = i
                    # The cards above were already drawn with the old focus,
                    # so redraw rather than showing a stale highlight.
                    st.rerun()

    note = tiles[focus].get("note", "")
    if note:
        st.markdown(
            f'<div class="mt-kpi-note"><b>{tiles[focus]["label"]}</b> — {note}</div>',
            unsafe_allow_html=True,
        )
    return focus

def brand() -> None:
    """Wordmark drawn inline, so its size is entirely ours to set."""
    st.markdown(
        f"""
        <div class="mt-brand">
          <svg viewBox="0 0 260 60" width="100%" role="img" aria-label="MIND//TECH">
            <text x="0" y="30" font-family="Manrope, Inter, sans-serif" font-size="30"
                  font-weight="800" letter-spacing="-1.4" fill="{INK}">MIND<tspan
                  fill="{TEAL}">//</tspan>TECH</text>
            <text x="1" y="50" font-family="Inter, sans-serif" font-size="9.5"
                  letter-spacing="1.7" fill="{MUTED}">MENTAL HEALTH IN TECH - 2014</text>
          </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nav_highlight(url_path: str) -> None:
    """Mark the active nav link.

    This Streamlit build sets no ``aria-current`` on page links, so there is
    nothing in the markup that says which row is current. What it does set is
    ``href``, equal to the page's ``url_path`` ("" for the default page). We
    know the active path in Python, so we write an exact selector for it each
    rerun. No dependency on Streamlit's internal class names.
    """
    st.markdown(
        f"""
        <style>
        /* every row: reserve the border, let the halo escape the box */
        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
          overflow: visible !important;
          border: 1px solid transparent !important;
          background: transparent !important;
        }}

        /* ---- the active row ---- */
        section[data-testid="stSidebar"] a[href="{url_path}"] {{
          background: linear-gradient(90deg, {MINT_LIGHT} 0%, {SURFACE} 84%) !important;
          border: 1px solid {MINT} !important;
          border-radius: {RADIUS_S}px !important;
          box-shadow: 0 0 0 3px rgba(134,216,178,.30),
                      0 8px 20px -8px rgba(0,144,158,.45) !important;
          animation: mt-ring 2.8s ease-in-out infinite;
        }}
        /* teal to violet bar down the left edge */
        section[data-testid="stSidebar"] a[href="{url_path}"]::before {{
          content: ""; position: absolute; left: -1px; top: 8px; bottom: 8px;
          width: 4px; border-radius: 4px;
          background: linear-gradient(180deg, {TEAL}, {VIOLET});
        }}
        /* pulsing dot on the right */
        section[data-testid="stSidebar"] a[href="{url_path}"]::after {{
          content: ""; position: absolute; right: 12px; top: 50%; margin-top: -3px;
          width: 6px; height: 6px; border-radius: 50%; background: {TEAL};
          animation: mt-pulse 2.4s ease-in-out infinite;
        }}
        section[data-testid="stSidebar"] a[href="{url_path}"] p {{
          font-weight: 700 !important; color: {INK} !important;
        }}
        section[data-testid="stSidebar"] a[href="{url_path}"] span[data-testid="stIconMaterial"] {{
          color: {TEAL} !important;
        }}

        /* mt-ring, not mt-glow: mt-glow belongs to the hero blobs */
        @keyframes mt-ring {{
          0%, 100% {{ box-shadow: 0 0 0 3px rgba(134,216,178,.22),
                                  0 8px 20px -8px rgba(0,144,158,.35); }}
          50%      {{ box-shadow: 0 0 0 5px rgba(134,216,178,.45),
                                  0 10px 26px -8px rgba(0,144,158,.55); }}
        }}
        @keyframes mt-pulse {{
          0%, 100% {{ transform: scale(1);   opacity: 1;   }}
          50%      {{ transform: scale(1.5); opacity: .45; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
          section[data-testid="stSidebar"] a[href="{url_path}"],
          section[data-testid="stSidebar"] a[href="{url_path}"]::after {{
            animation: none !important;
          }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )