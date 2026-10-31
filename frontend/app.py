import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        from app.core import orjson_shim
        sys.modules["orjson"] = orjson_shim
        from app.core import ormsgpack_shim
        sys.modules["ormsgpack"] = ormsgpack_shim
        sys.modules["xarray"] = None
        sys.modules["statsmodels"] = None
    except Exception:
        pass

import streamlit as st
import plotly.io as pio
pio.json.config.default_engine = "json"

st.set_page_config(
    page_title="University Ranking Analytics — Multi-System Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

from frontend.components.theme import apply_custom_css
from frontend.components.api_client import is_backend_online

from frontend.views.overview import render_overview
from frontend.views.comparison import render_comparison
from frontend.views.country_analysis import render_country_analysis
from frontend.views.trends import render_trends
from frontend.views.criteria_analysis import render_criteria_analysis
from frontend.views.demographics import render_demographics
from frontend.views.ai_copilot import render_ai_copilot

apply_custom_css()

# Sidebar Branding
with st.sidebar:
    st.markdown("## 🎓 University Analytics")
    st.caption("Cross-System Longitudinal Intelligence & GenAI Platform")
    
    # System Status Pill
    api_online = is_backend_online()
    if api_online:
        st.success("🟢 FastAPI Backend: Online")
    else:
        st.info("🔷 Engine: Direct Analytics Service (Zero Latency)")
        
    st.markdown("---")

# Navigation Definition
pages = {
    "Analytical Dashboards": [
        st.Page(render_overview, title="Executive Overview", icon="🏛️", default=True),
        st.Page(render_comparison, title="University Comparison", icon="⚖️"),
        st.Page(render_country_analysis, title="Country Intelligence", icon="🌍"),
        st.Page(render_trends, title="Historical Trends", icon="📈"),
        st.Page(render_criteria_analysis, title="Criteria & Trade-offs", icon="🔬"),
        st.Page(render_demographics, title="Student Demographics", icon="👥"),
    ],
    "GenAI Intelligence": [
        st.Page(render_ai_copilot, title="AI Analytics Assistant", icon="✨"),
    ]
}

pg = st.navigation(pages)
pg.run()
