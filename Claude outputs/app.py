"""MIND//TECH - Mental Health in Tech Survey dashboard.

Entry point. The sidebar is built by hand (brand, nav links, filters) so the
brand sits above navigation and both are fully under our own CSS.

Run:  streamlit run app.py
"""

import streamlit as st

from app import data, theme

st.set_page_config(
    page_title="MIND//TECH",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

theme.apply_theme()

PAGES = [
    st.Page("app/pages/1_overview.py",     title="Overview",              icon=":material/insights:", default=True),
    st.Page("app/pages/2_experience.py",   title="Mental health & work",  icon=":material/psychology:"),
    st.Page("app/pages/3_support.py",      title="Workplace support",     icon=":material/health_and_safety:"),
    st.Page("app/pages/4_conversation.py", title="Can we talk?",          icon=":material/forum:"),
    st.Page("app/pages/5_geography.py",    title="Who experiences what?", icon=":material/public:"),
    st.Page("app/pages/6_ask.py",          title="Ask MIND//TECH",        icon=":material/chat:"),
    st.Page("app/pages/7_methodology.py",  title="About the data",        icon=":material/description:"),
]

# position="hidden" -> Streamlit draws no navigation; we draw it ourselves below.
nav = st.navigation(PAGES, position="hidden")

with st.sidebar:
    theme.brand()
    for page in PAGES:
        st.page_link(page)

_df = data.load_data()
_selection = data.sidebar_filters(_df)
_view = data.apply_filters(_df, _selection)
data.sample_badge(_view, _df)

st.session_state["view"] = _view
st.session_state["full"] = _df
st.session_state["filter_text"] = data.active_filter_text(_selection)

nav.run()
