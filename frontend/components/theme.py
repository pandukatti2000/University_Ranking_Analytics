import streamlit as st

PRIMARY_COLOR = "#6366F1"   # Indigo
SECONDARY_COLOR = "#0F172A" # Dark Slate
ACCENT_CYAN = "#06B6D4"     # Times Higher Education color
ACCENT_EMERALD = "#10B981"  # Shanghai color
ACCENT_PURPLE = "#8B5CF6"   # CWUR color
CARD_BG = "#1E293B"         # Slate-800
BORDER_COLOR = "#334155"    # Slate-700
TEXT_MUTED = "#94A3B8"      # Slate-400

CUSTOM_CSS = """
<style>
/* Modern Typography & Container Spacing */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Remove default top padding */
.block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 95%;
}

/* Custom Metric Cards */
.metric-container {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    transition: transform 0.2s ease, border-color 0.2s ease;
    margin-bottom: 0.75rem;
}

.metric-container:hover {
    transform: translateY(-2px);
    border-color: #6366F1;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.15);
}

.metric-title {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94A3B8;
    margin-bottom: 0.35rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.1;
}

.metric-subtitle {
    font-size: 0.78rem;
    color: #64748B;
    margin-top: 0.35rem;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.badge-the { background: rgba(6, 182, 212, 0.15); color: #22D3EE; border: 1px solid rgba(6, 182, 212, 0.3); }
.badge-arwu { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-cwur { background: rgba(139, 92, 246, 0.15); color: #A78BFA; border: 1px solid rgba(139, 92, 246, 0.3); }

/* Notice Callouts */
.callout-box {
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    margin: 1rem 0;
    font-size: 0.88rem;
    line-height: 1.45;
}
.callout-warning {
    background: rgba(245, 158, 11, 0.08);
    border-left: 4px solid #F59E0B;
    color: #FDE68A;
}
.callout-info {
    background: rgba(99, 102, 241, 0.08);
    border-left: 4px solid #6366F1;
    color: #C7D2FE;
}
.callout-danger {
    background: rgba(239, 68, 68, 0.08);
    border-left: 4px solid #EF4444;
    color: #FECACA;
}

/* Code & SQL inspection styling */
.sql-pill {
    background: #0B1120;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 0.8rem;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.82rem;
    color: #38BDF8;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #0B1120;
    border-right: 1px solid #1E293B;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 6px 16px;
    background-color: #1E293B;
    border: 1px solid #334155;
    color: #94A3B8;
}
.stTabs [aria-selected="true"] {
    background-color: #6366F1 !important;
    border-color: #6366F1 !important;
    color: #FFFFFF !important;
}
</style>
"""

def apply_custom_css():
    """Inject polished dark mode CSS stylesheet."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_metric_card(title: str, value: str, subtitle: str = "", icon: str = ""):
    """Render a modern dark-themed KPI metric card."""
    icon_html = f"<span>{icon}</span>" if icon else ""
    sub_html = f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ""
    html = f"""
    <div class="metric-container">
        <div class="metric-title">{icon_html} {title}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_scale_warning():
    """Render standard domain notice regarding scale isolation."""
    html = """
    <div class="callout-box callout-warning">
        ⚠️ <strong>Scale Isolation Notice:</strong> Ranking criteria use fundamentally different metrics.
        <strong>Times Higher Education</strong> and <strong>Shanghai (ARWU)</strong> report normalized scores (0–100, higher is better).
        In contrast, <strong>CWUR</strong> criteria 14–20 report <em>ordinal ranking positions</em> (1–1,000, lower is better).
        Scores and ranks cannot be aggregated across systems.
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_non_causal_notice():
    """Render correlation vs causation alert."""
    html = """
    <div class="callout-box callout-info">
        ℹ️ <strong>Associative Analysis Disclaimer:</strong> Demographic indicators (student counts, staff ratios,
        international and female percentages) reflect observable characteristics of institutions.
        Statistical correlations represent <strong>associations only</strong> and do not indicate causal impact on rankings.
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
