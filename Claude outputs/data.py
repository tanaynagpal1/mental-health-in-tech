"""Data access for the dashboard: one cached load, one filter function, one guard.

Filter state note: widget keys carry a version number (f_region_0, f_region_1, ...).
Resetting or applying a preset bumps the version, so Streamlit builds fresh widgets
with new defaults. Nothing ever writes to an existing widget's key, which is what
raises StreamlitWidgetAlreadyInstantiatedError.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import config as cfg

MIN_N = cfg.MIN_N_COUNTRY          # 20 - the reporting threshold from DQ-24


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Read the cleaned file once per session and restore the ordered dtypes."""
    df = pd.read_csv(cfg.DATA_CLEAN, encoding=cfg.ENCODING)
    for col, cats in [
        ("no_employees", cfg.SIZE_ORDER),
        ("leave", cfg.LEAVE_ORDER),
        ("work_interfere", cfg.INTERFERE_ORDER),
        ("age_group", cfg.AGE_LABELS),
    ]:
        df[col] = pd.Categorical(df[col], categories=cats, ordered=True)
    df["treated"] = df.treatment.eq("Yes")
    return df


# --------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------
FILTERS = {
    "region":          "Region",
    "gender_clean":    "Gender",
    "age_group":       "Age group",
    "no_employees":    "Company size",
    "employment_type": "Employment",
}

PRESETS = {
    "Employees only": {"employment_type": ["Employee"]},
    "United States":  {"region": ["United States"]},
    "Large firms":    {"no_employees": ["500-1000", "More than 1000"]},
    "Under 35":       {"age_group": ["18-24", "25-34"]},
}


def _options(df: pd.DataFrame, col: str) -> list[str]:
    """Option list for one filter, in a meaningful order."""
    present = {str(v) for v in df[col].dropna().unique()}
    if isinstance(df[col].dtype, pd.CategoricalDtype):
        return [str(c) for c in df[col].cat.categories if str(c) in present]
    return sorted(present)


def _bump(preset_values: dict[str, list[str]]) -> None:
    """Switch every filter widget to a new key so new defaults take effect."""
    st.session_state["preset_values"] = preset_values
    st.session_state["filter_version"] = st.session_state.get("filter_version", 0) + 1


def sidebar_filters(df: pd.DataFrame) -> dict[str, list[str]]:
    """Quick-view buttons, pills for short lists, dropdowns for long ones."""
    version = st.session_state.setdefault("filter_version", 0)
    defaults = st.session_state.get("preset_values", {})

    st.sidebar.markdown('<div class="mt-side-h">Quick views</div>', unsafe_allow_html=True)
    cols = st.sidebar.columns(2)
    for i, (name, values) in enumerate(PRESETS.items()):
        if cols[i % 2].button(name, use_container_width=True, key=f"preset_{i}_{version}"):
            _bump(values)
            st.rerun()

    st.sidebar.markdown('<div class="mt-side-h">Filters</div>', unsafe_allow_html=True)
    selection: dict[str, list[str]] = {}

    for col in ("gender_clean", "employment_type"):
        options = _options(df, col)
        preset = [v for v in defaults.get(col, []) if v in options]
        selection[col] = st.sidebar.pills(
            FILTERS[col], options, selection_mode="multi",
            default=preset or None, key=f"f_{col}_{version}",
        ) or []

    for col in ("region", "age_group", "no_employees"):
        options = _options(df, col)
        preset = [v for v in defaults.get(col, []) if v in options]
        selection[col] = st.sidebar.multiselect(
            FILTERS[col], options, default=preset, key=f"f_{col}_{version}",
        )

    chips = [f'<span class="mt-chip">{v}</span>' for vals in selection.values() for v in vals]
    st.sidebar.markdown(
        '<div class="mt-chips">'
        + ("".join(chips) if chips else '<span class="mt-chip none">All respondents</span>')
        + "</div>",
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Reset", use_container_width=True, key=f"reset_{version}"):
        _bump({})
        st.rerun()

    return selection


def apply_filters(df: pd.DataFrame, selection: dict[str, list[str]]) -> pd.DataFrame:
    """Apply the selection. An empty list means 'all', never 'none'."""
    mask = pd.Series(True, index=df.index)
    for col, chosen in selection.items():
        if chosen:
            mask &= df[col].astype(str).isin(chosen)
    return df[mask]


def active_filter_text(selection: dict[str, list[str]]) -> str:
    """One readable line describing what is currently filtered."""
    parts = [f"{FILTERS[c]}: {', '.join(v)}" for c, v in selection.items() if v]
    return " - ".join(parts) if parts else "No filters - all respondents"


# --------------------------------------------------------------------------
# The n-guard (DQ-24)
# --------------------------------------------------------------------------
def sample_badge(view: pd.DataFrame, full: pd.DataFrame) -> None:
    """Respondents in view, with a meter showing what share of the sample that is."""
    n, total = len(view), len(full)
    pct = (n / total * 100) if total else 0
    st.sidebar.markdown(
        f"""<div style="border:1px solid #DFE5DF;background:#FFFFFF;border-radius:12px;
                    padding:12px;margin-top:10px">
              <div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;
                          letter-spacing:-.03em">{n:,}</div>
              <div style="color:#69736F;font-size:11.5px">of {total:,} respondents - {pct:.0f}%</div>
              <div class="mt-meter"><span style="width:{pct:.1f}%"></span></div>
            </div>""",
        unsafe_allow_html=True,
    )
    if n < MIN_N:
        st.sidebar.warning(f"Below the n = {MIN_N} reporting threshold.")


def enough(view: pd.DataFrame, minimum: int = MIN_N) -> bool:
    return len(view) >= minimum


def guard(view: pd.DataFrame, what: str = "this view", minimum: int = MIN_N) -> bool:
    """Render the refusal panel and return False when the sample is too small."""
    if enough(view, minimum):
        return True
    st.markdown(
        f"""<div class="mt-guard">
              <b>Too few responses for {what}.</b>
              <p style="margin:6px 0 0;color:#69736F">Only {len(view)} respondents match the
              current filters. No figure is reported below n = {minimum} - a rule carried over
              from the cleaning decisions (DQ-24).</p>
            </div>""",
        unsafe_allow_html=True,
    )
    return False


def big_enough_groups(df: pd.DataFrame, column: str, minimum: int = MIN_N) -> list[str]:
    counts = df[column].value_counts()
    return counts[counts >= minimum].index.tolist()
