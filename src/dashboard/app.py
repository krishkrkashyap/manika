"""
Manika - Live Trading Dashboard v2.2
Premium Streamlit Application with dark/light theme toggle,
consolidated positions, LAST/INTRA/EXP MTM, per-stock scenarios.

Fixed CSS issues with proper modern Streamlit selectors.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

from config.settings import (
    APP_NAME, APP_VERSION, APP_SUBTITLE,
    DEMO_MODE, REFRESH_INTERVAL_SECONDS, DASHBOARD_TABS
)
from src.data.position_manager import get_position_manager
from src.data.market_data import get_market_data_fetcher
from src.data.watchlist_manager import get_watchlist_manager
from src.analytics.mtm_calculator import get_mtm_calculator
from src.analytics.margin_calc import get_margin_calculator
from src.analytics.alerts import get_alert_system


# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=f"{APP_NAME} — {APP_SUBTITLE}",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ═══════════════════════════════════════════════════════════════
# THEME SYSTEM WITH CSS VARIABLES
# ═══════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "name": "dark",
        "bg_primary": "#0a0c10",
        "bg_secondary": "#12151f",
        "bg_tertiary": "#1a1e2e",
        "bg_card": "#1e2233",
        "bg_card_hover": "#252a3f",
        "border": "#2a2f44",
        "border_focus": "#3d4466",
        "text_primary": "#e8ecf4",
        "text_secondary": "#9ca3b5",
        "text_muted": "#6b7280",
        "accent": "#5b8def",
        "accent_hover": "#7094f8",
        "accent2": "#a78bfa",
        "green": "#22c55e",
        "green_bg": "rgba(34,197,94,0.12)",
        "red": "#ef4444",
        "red_bg": "rgba(239,68,68,0.12)",
        "orange": "#f59e0b",
        "orange_bg": "rgba(245,158,11,0.12)",
        "cyan": "#06b6d4",
        "chart_grid": "rgba(91,141,239,0.08)",
        "shadow": "rgba(0,0,0,0.4)",
    },
    "light": {
        "name": "light",
        "bg_primary": "#f8f9fc",
        "bg_secondary": "#ffffff",
        "bg_tertiary": "#f1f3f8",
        "bg_card": "#ffffff",
        "bg_card_hover": "#f5f7fb",
        "border": "#e2e5f0",
        "border_focus": "#c5cad9",
        "text_primary": "#1a1d2e",
        "text_secondary": "#4b5568",
        "text_muted": "#9ca3af",
        "accent": "#4f6df5",
        "accent_hover": "#6183f6",
        "accent2": "#7c5cfc",
        "green": "#16a34a",
        "green_bg": "rgba(22,163,74,0.12)",
        "red": "#dc2626",
        "red_bg": "rgba(220,38,38,0.12)",
        "orange": "#d97706",
        "orange_bg": "rgba(217,119,6,0.12)",
        "cyan": "#0891b2",
        "chart_grid": "rgba(79,109,245,0.08)",
        "shadow": "rgba(0,0,0,0.08)",
    },
}


def get_theme():
    """Get current theme colors."""
    mode = st.session_state.get("theme_mode", "dark")
    return THEMES.get(mode, THEMES["dark"])


def build_css(t):
    """Build robust CSS with proper selectors for Streamlit 1.35+."""
    return f"""
    <style>
    /* ═══════════════════════════════════════════════════════════
       CSS VARIABLES
       ═══════════════════════════════════════════════════════════ */
    :root {{
        --bg-primary: {t['bg_primary']};
        --bg-secondary: {t['bg_secondary']};
        --bg-tertiary: {t['bg_tertiary']};
        --bg-card: {t['bg_card']};
        --bg-card-hover: {t['bg_card_hover']};
        --border: {t['border']};
        --border-focus: {t['border_focus']};
        --text-primary: {t['text_primary']};
        --text-secondary: {t['text_secondary']};
        --text-muted: {t['text_muted']};
        --accent: {t['accent']};
        --accent-hover: {t['accent_hover']};
        --accent2: {t['accent2']};
        --green: {t['green']};
        --green-bg: {t['green_bg']};
        --red: {t['red']};
        --red-bg: {t['red_bg']};
        --orange: {t['orange']};
        --orange-bg: {t['orange_bg']};
        --cyan: {t['cyan']};
        --chart-grid: {t['chart_grid']};
        --shadow: {t['shadow']};
    }}

    /* ═══════════════════════════════════════════════════════════
       BASE RESET - No transparency
       ═══════════════════════════════════════════════════════════ */
    html, body, .stApp {{
        background-color: var(--bg-primary) !important;
        color: var(--text-secondary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }}
    
    /* Main container - solid background */
    .block-container {{
        background-color: var(--bg-primary) !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }}
    
    /* Fix header */
    header[data-testid="stHeader"] {{
        background-color: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--border) !important;
        height: 48px !important;
    }}
    
    /* Main content area */
    section[data-testid="stMain"] {{
        background-color: var(--bg-primary) !important;
    }}
    
    section[data-testid="stMain"] > div {{
        background-color: var(--bg-primary) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       SIDEBAR - Solid backgrounds
       ═══════════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"] {{
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }}
    
    section[data-testid="stSidebar"] > div {{
        background-color: var(--bg-secondary) !important;
    }}
    
    /* Sidebar text */
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {{
        color: var(--text-secondary) !important;
    }}
    
    /* Sidebar radio buttons */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
        color: var(--text-secondary) !important;
        background-color: var(--bg-secondary) !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        margin: 4px 0 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.15s ease !important;
    }}
    
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {{
        background-color: var(--bg-card-hover) !important;
    }}
    
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {{
        background-color: var(--bg-card) !important;
        color: var(--accent) !important;
    }}
    
    /* Sidebar divider */
    section[data-testid="stSidebar"] hr {{
        border-color: var(--border) !important;
        margin: 1rem 0 !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       TYPOGRAPHY
       ═══════════════════════════════════════════════════════════ */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}
    
    .stMarkdown p,
    .stMarkdown span,
    p, span, label {{
        color: var(--text-secondary) !important;
    }}
    
    /* Code */
    code {{
        background-color: var(--bg-tertiary) !important;
        color: var(--accent) !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       KPI CARDS - Modern card design
       ═══════════════════════════════════════════════════════════ */
    .kpi-card {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        margin-bottom: 8px;
        box-shadow: 0 2px 8px var(--shadow);
        transition: all 0.2s ease;
    }}
    
    .kpi-card:hover {{
        border-color: var(--accent) !important;
        transform: translateY(-1px);
    }}
    
    .kpi-label {{
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 6px;
    }}
    
    .kpi-value {{
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: -0.3px;
        line-height: 1.2;
    }}
    
    .kpi-value.positive {{ color: var(--green); }}
    .kpi-value.negative {{ color: var(--red); }}
    .kpi-value.neutral  {{ color: var(--accent); }}
    
    .kpi-delta {{
        font-size: 0.75rem;
        margin-top: 4px;
        font-weight: 500;
    }}
    
    .kpi-delta.positive {{ color: var(--green); }}
    .kpi-delta.negative {{ color: var(--red); }}

    /* ═══════════════════════════════════════════════════════════
       SECTION HEADERS
       ═══════════════════════════════════════════════════════════        */
    .sec-hdr {{
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-primary) !important;
        margin: 24px 0 12px 0;
        padding: 12px 0 10px 0;
        border-bottom: 2px solid var(--border);
        letter-spacing: 0.3px;
        background-color: var(--bg-primary) !important;
        display: block;
        width: 100%;
    }}

    /* ═══════════════════════════════════════════════════════════
       BADGES
       ═══════════════════════════════════════════════════════════ */
    .badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}
    
    .badge-demo {{
        background-color: rgba(167, 139, 250, 0.15);
        color: var(--accent2);
        border: 1px solid rgba(167, 139, 250, 0.3);
    }}
    
    .badge-live {{
        background-color: var(--green-bg);
        color: var(--green);
        border: 1px solid rgba(34, 197, 94, 0.3);
    }}

    /* ═══════════════════════════════════════════════════════════
       TABS - Modern styling
       ═══════════════════════════════════════════════════════════ */
    .stTabs {{
        background-color: var(--bg-primary) !important;
        gap: 0;
    }}
    
    div[data-testid="stTabbedContent"] {{
        background-color: var(--bg-card) !important;
        border-radius: 12px;
        border: 1px solid var(--border);
        overflow: hidden;
    }}
    
    div[data-testid="stTabbedContent"] > div:first-child {{
        background-color: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--border);
    }}
    
    /* Tab buttons */
    div[data-testid="stTabbedContent"] button[role="tab"] {{
        border-radius: 0 !important;
        padding: 14px 20px !important;
        color: var(--text-muted) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        background-color: var(--bg-secondary) !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.2s ease !important;
    }}
    
    div[data-testid="stTabbedContent"] button[role="tab"]:hover {{
        background-color: var(--bg-card-hover) !important;
        color: var(--text-primary) !important;
    }}
    
    div[data-testid="stTabbedContent"] button[role="tab"][aria-selected="true"],
    div[data-testid="stTabbedContent"] button[role="tab"][data-selected="true"] {{
        background-color: var(--bg-card) !important;
        color: var(--accent) !important;
        font-weight: 600 !important;
        border-bottom-color: var(--accent) !important;
    }}
    
    div[data-testid="stTabPanel"] {{
        background-color: var(--bg-card) !important;
        padding: 20px !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       DATAFRAMES - Solid backgrounds
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stDataFrame"] {{
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
        background-color: var(--bg-card) !important;
    }}
    
    div[data-testid="stDataFrame"] > div:first-child {{
        border-radius: 10px 10px 0 0 !important;
    }}
    
    /* DataFrame table */
    div[data-testid="stDataFrame"] table {{
        background-color: var(--bg-card) !important;
    }}
    
    div[data-testid="stDataFrame"] thead {{
        background-color: var(--bg-secondary) !important;
    }}
    
    div[data-testid="stDataFrame"] th {{
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        border-bottom: 1px solid var(--border) !important;
    }}
    
    div[data-testid="stDataFrame"] td {{
        color: var(--text-secondary) !important;
        border-bottom: 1px solid var(--border) !important;
    }}
    
    div[data-testid="stDataFrame"] tr:hover td {{
        background-color: var(--bg-card-hover) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       BUTTONS - Modern styling
       ═══════════════════════════════════════════════════════════ */
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-secondary"],
    div[data-testid="stButton"] > button {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 10px 16px !important;
        transition: all 0.15s ease !important;
    }}
    
    button[data-testid="stBaseButton-primary"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover,
    div[data-testid="stButton"] > button:hover {{
        border-color: var(--accent) !important;
        background-color: var(--bg-card-hover) !important;
    }}
    
    button[data-testid="stBaseButton-primary"] {{
        background-color: var(--accent) !important;
        border-color: var(--accent) !important;
        color: #ffffff !important;
    }}
    
    button[data-testid="stBaseButton-primary"]:hover {{
        background-color: var(--accent-hover) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       INPUTS - Solid backgrounds
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border-color: var(--border) !important;
        border-radius: 8px !important;
    }}
    
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(91,141,239,0.15) !important;
    }}
    
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSelectbox"] label {{
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       EXPANDERS
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stExpander"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }}
    
    div[data-testid="stExpander"] summary {{
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        padding: 14px 18px;
        border-radius: 10px 10px 0 0 !important;
    }}
    
    div[data-testid="stExpander"]:hover {{
        border-color: var(--accent) !important;
    }}
    
    div[data-testid="stExpander"] details {{
        background-color: var(--bg-secondary) !important;
        border-radius: 0 0 10px 10px;
    }}

    /* ═══════════════════════════════════════════════════════════
       METRICS
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}
    
    div[data-testid="stMetricLabel"] {{
        color: var(--text-muted) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       CHECKBOX
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stCheckbox"] label {{
        color: var(--text-secondary) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       FORMS
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stForm"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }}
    
    div[data-testid="stForm"] label {{
        color: var(--text-secondary) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       ALERTS - Info/Success/Warning/Error
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stAlert"] {{
        border-radius: 10px !important;
        border: none !important;
        padding: 14px 18px !important;
    }}
    
    div[data-testid="stAlert"].stInfo {{
        background-color: rgba(91,141,239,0.12) !important;
        color: var(--accent) !important;
    }}
    
    div[data-testid="stAlert"].stSuccess {{
        background-color: var(--green-bg) !important;
        color: var(--green) !important;
    }}
    
    div[data-testid="stAlert"].stWarning {{
        background-color: var(--orange-bg) !important;
        color: var(--orange) !important;
    }}
    
    div[data-testid="stAlert"].stError {{
        background-color: var(--red-bg) !important;
        color: var(--red) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       VERTICAL BLOCKS & CONTAINERS - Solid backgrounds
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalStack"],
    div[data-testid="stHorizontalBlock"] {{
        background-color: var(--bg-primary) !important;
    }}
    
    div[data-testid="column"] {{
        background-color: var(--bg-primary) !important;
    }}
    
    div[data-testid="stSpacer"] {{
        background-color: var(--bg-primary) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       SLIDER
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stSlider"] [data-testid="stThumbValue"] {{
        background-color: var(--accent) !important;
    }}
    
    div[data-testid="stSlider"] [data-testid="stThumb"] {{
        background-color: var(--accent) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       SELECTBOX DROPDOWN
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stSelectbox"] [data-testid="stPopover"] {{
        background-color: var(--bg-card) !important;
        border-color: var(--border) !important;
    }}
    
    div[data-testid="stSelectbox"] ul {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
    }}
    
    div[data-testid="stSelectbox"] li {{
        color: var(--text-secondary) !important;
    }}
    
    div[data-testid="stSelectbox"] li:hover {{
        background-color: var(--bg-card-hover) !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       MULTISELECT
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stMultiSelect"] {{
        background-color: var(--bg-card) !important;
    }}
    
    /* ═══════════════════════════════════════════════════════════
       SCROLLBAR
       ═══════════════════════════════════════════════════════════ */
    ::-webkit-scrollbar {{ 
        width: 6px; 
        height: 6px; 
    }}
    ::-webkit-scrollbar-track {{ 
        background: var(--bg-secondary); 
    }}
    ::-webkit-scrollbar-thumb {{ 
        background: var(--border); 
        border-radius: 3px; 
    }}
    ::-webkit-scrollbar-thumb:hover {{ 
        background: var(--accent); 
    }}

    /* ═══════════════════════════════════════════════════════════
       DIVIDER
       ═══════════════════════════════════════════════════════════ */
    hr {{
        border-color: var(--border) !important;
        margin: 1rem 0 !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       HIDE DEFAULT STREAMLIT BRANDING
       ═══════════════════════════════════════════════════════════ */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    
    /* ═══════════════════════════════════════════════════════════
       SPINNER
       ═══════════════════════════════════════════════════════════ */
    div[data-testid="stSpinner"] {{
        background-color: var(--bg-card) !important;
    }}
    
    /* ═══════════════════════════════════════════════════════════
       SELECTION & HIGHLIGHTS
       ═══════════════════════════════════════════════════════════ */
    ::selection {{
        background-color: rgba(91,141,239,0.3) !important;
        color: var(--text-primary) !important;
    }}
    </style>
    """


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def fmt(value, prefix="₹"):
    """Format value as compact currency."""
    if value is None:
        return f"{prefix}0"
    if abs(value) >= 1e7:
        return f"{prefix}{value/1e7:.2f} Cr"
    if abs(value) >= 1e5:
        return f"{prefix}{value/1e5:.2f} L"
    return f"{prefix}{value:,.0f}"


def color_class(value):
    if value > 0: return "positive"
    if value < 0: return "negative"
    return "neutral"


def kpi_html(label, value, fmt_value=None):
    cc = color_class(value)
    display = fmt_value or fmt(value)
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {cc}">{display}</div>
    </div>
    """


def get_plotly_layout(t, height=350, **kwargs):
    """Get Plotly layout dict for current theme."""
    base = dict(
        paper_bgcolor=t['bg_card'],
        plot_bgcolor=t['bg_card'],
        font=dict(family='Inter, sans-serif', color=t['text_secondary'], size=12),
        margin=dict(l=50, r=20, t=45, b=40),
        xaxis=dict(
            gridcolor=t['chart_grid'],
            zerolinecolor=t['border'],
            tickfont=dict(color=t['text_muted']),
            linecolor=t['border'],
        ),
        yaxis=dict(
            gridcolor=t['chart_grid'],
            zerolinecolor=t['border'],
            tickfont=dict(color=t['text_muted']),
            linecolor=t['border'],
        ),
        legend=dict(
            bgcolor=t['bg_card'],
            font=dict(color=t['text_secondary'], size=11),
        ),
        height=height,
        hoverlabel=dict(
            bgcolor=t['bg_card'],
            font_size=13,
            font_family='Inter, sans-serif',
            font_color=t['text_primary'],
            bordercolor=t['border'],
        ),
    )
    base.update(kwargs)
    return base


def style_mtm_val(val, t):
    """Return inline style for MTM value."""
    if isinstance(val, (int, float)) and val != 0:
        color = t['green'] if val > 0 else t['red']
        return f'color: {color}; font-weight: 600'
    return ''


def safe_numeric(val):
    """Convert value to numeric, returning None for invalid/empty values."""
    if val is None or val == '' or (isinstance(val, str) and val.strip() == ''):
        return None
    try:
        return float(val) if '.' in str(val) else int(val)
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════

def init_session():
    defaults = {
        'quotes': {},
        'last_update': None,
        'mtm_data': {},
        'auto_refresh': True,
        'theme_mode': 'dark',
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def refresh_data():
    pm = get_position_manager()
    mdf = get_market_data_fetcher()
    mc = get_mtm_calculator()
    symbols = pm.get_all_tradable_symbols()
    quotes = mdf.update_all_quotes(symbols)
    positions = pm.get_all_positions()
    mtm_result = mc.calculate_all_mtm(positions, quotes)
    st.session_state.quotes = quotes
    st.session_state.mtm_data = mtm_result
    st.session_state.last_update = datetime.now().strftime('%H:%M:%S')
    return quotes, mtm_result


# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════

def render_header(t):
    c1, c2, c3 = st.columns([3, 1, 1])
    badge_cls = 'badge-demo' if DEMO_MODE else 'badge-live'
    badge_txt = 'DEMO' if DEMO_MODE else 'LIVE'
    with c1:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:4px;">
            <span style="font-size:1.75rem;font-weight:800;color:{t['accent']};">{APP_NAME}</span>
            <span class="badge {badge_cls}">{badge_txt}</span>
        </div>
        <span style="color:{t['text_muted']};font-size:0.82rem;">{APP_SUBTITLE} v{APP_VERSION}</span>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="text-align:right;padding-top:8px;">
            <span style="color:{t['text_muted']};font-size:0.68rem;text-transform:uppercase;letter-spacing:1.2px;">Last Update</span><br>
            <span style="color:{t['text_primary']};font-size:1.1rem;font-weight:600;">{st.session_state.get('last_update', '--:--:--')}</span>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="text-align:right;padding-top:8px;">
            <span style="color:{t['text_muted']};font-size:0.68rem;text-transform:uppercase;letter-spacing:1.2px;">Date</span><br>
            <span style="color:{t['text_primary']};font-size:1.1rem;font-weight:600;">{datetime.now().strftime('%d %b %Y')}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown(f"<hr style='border:none;border-top:1px solid {t['border']};margin:12px 0 20px 0;'>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════

def render_overview(t):
    mtm = st.session_state.get('mtm_data', {})
    total_mtm = mtm.get('total_mtm', 0)
    last_total = mtm.get('last_total', 0)
    intra_total = mtm.get('intra_total', 0)
    exp_total = mtm.get('exp_total', 0)
    breakdown = mtm.get('breakdown', {})
    stock_totals = mtm.get('stock_totals', {})
    positions_mtm = mtm.get('positions_mtm', [])

    pm = get_position_manager()
    total_value = pm.get_total_position_value()
    active = sum(1 for p in positions_mtm if p.get('net_qty', 0) != 0)
    profitable = sum(1 for p in positions_mtm if p.get('mtm', 0) > 0)
    losing = sum(1 for p in positions_mtm if p.get('mtm', 0) < 0)

    # ── KPI Row ──
    cols = st.columns(6)
    kpis = [
        ("Total MTM", total_mtm, fmt(total_mtm)),
        ("LAST MTM", last_total, fmt(last_total)),
        ("Intraday MTM", intra_total, fmt(intra_total)),
        ("Expiry MTM", exp_total, fmt(exp_total)),
        ("Position Value", total_value, fmt(total_value)),
        ("Active Positions", active, str(active)),
    ]
    for col, (label, val, display) in zip(cols, kpis):
        with col:
            st.markdown(kpi_html(label, val, display), unsafe_allow_html=True)

    st.markdown("", unsafe_allow_html=True)

    # ── Charts Row ──
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f'<div class="sec-hdr">📊 MTM by Stock</div>', unsafe_allow_html=True)
        if stock_totals:
            stocks = list(stock_totals.keys())
            vals = [stock_totals[s]['total_mtm'] for s in stocks]
            colors = [t['green'] if v >= 0 else t['red'] for v in vals]

            fig = go.Figure(data=[go.Bar(
                x=stocks, y=vals,
                marker_color=colors,
                text=[fmt(v) for v in vals],
                textposition='outside',
                textfont=dict(size=11, color=t['text_secondary']),
                hovertemplate='<b>%{x}</b><br>MTM: ₹%{y:,.0f}<extra></extra>',
            )])
            fig.update_layout(**get_plotly_layout(t, height=360), showlegend=False,
                              yaxis_title="MTM (₹)")
            st.plotly_chart(fig, width='stretch', key="mtm_stock_bar")

    with c2:
        st.markdown(f'<div class="sec-hdr">📈 Futures vs Options</div>', unsafe_allow_html=True)
        if breakdown:
            labels = list(breakdown.keys())
            values = [abs(v) for v in breakdown.values()]
            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values,
                marker=dict(colors=[t['accent'], t['accent2']]),
                hole=0.5,
                textinfo='label+percent',
                textfont=dict(size=12, color=t['text_primary']),
                hovertemplate='<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>',
            )])
            layout = get_plotly_layout(t, height=360)
            layout['showlegend'] = True
            fig.update_layout(**layout)
            fig.add_annotation(
                text=f"<b>{fmt(total_mtm)}</b>",
                font=dict(size=16, color=t['green'] if total_mtm >= 0 else t['red']),
                showarrow=False, x=0.5, y=0.5,
            )
            st.plotly_chart(fig, width='stretch', key="mtm_pie")

    # ── Stock Breakdown Table ──
    st.markdown(f'<div class="sec-hdr">📋 Stock-wise MTM Breakdown</div>', unsafe_allow_html=True)
    if stock_totals:
        rows = []
        for stock, sv in stock_totals.items():
            rows.append({
                'Stock': stock,
                'LAST MTM': sv['last_mtm'],
                'Intraday MTM': sv['intra_mtm'],
                'Expiry MTM': sv['exp_mtm'],
                'Total MTM': sv['total_mtm'],
            })
        rows.append({
            'Stock': '🔸 GRAND TOTAL',
            'LAST MTM': last_total,
            'Intraday MTM': intra_total,
            'Expiry MTM': exp_total,
            'Total MTM': total_mtm,
        })
        df = pd.DataFrame(rows)
        styled = df.style.map(
            lambda v: style_mtm_val(v, t),
            subset=['LAST MTM', 'Intraday MTM', 'Expiry MTM', 'Total MTM']
        ).format({
            'LAST MTM': '₹{:,.0f}',
            'Intraday MTM': '₹{:,.0f}',
            'Expiry MTM': '₹{:,.0f}',
            'Total MTM': '₹{:,.0f}',
        })
        st.dataframe(styled, use_container_width=True, height=260)

    # ── Win/Loss ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(kpi_html("Profitable", profitable, f"{profitable} positions"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_html("Losing", -losing if losing > 0 else 0, f"{losing} positions"), unsafe_allow_html=True)
    with c3:
        ratio = f"{profitable}/{profitable + losing}" if (profitable + losing) > 0 else "0/0"
        st.markdown(kpi_html("Win Ratio", profitable - losing, ratio), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# TAB 2: POSITIONS
# ═══════════════════════════════════════════════════════════════

def render_positions(t):
    pm = get_position_manager()
    quotes = st.session_state.get('quotes', {})
    mtm_data = st.session_state.get('mtm_data', {})
    positions_mtm = mtm_data.get('positions_mtm', [])
    mtm_lookup = {p['symbol']: p for p in positions_mtm}
    consolidated = pm.get_consolidated_view(quotes)

    mtm_cols = ['LAST MTM', 'INTRA MTM', 'EXP MTM', 'TOTAL']

    def make_styled(df, cols):
        s = df.style.map(lambda v: style_mtm_val(v, t), subset=cols)
        fmt_dict = {}
        for c in df.columns:
            if c in cols:
                fmt_dict[c] = '₹{:,.0f}'
            elif c in ('Stk Price', 'Buy Avg', 'Sell Avg', 'Close', 'LTP'):
                fmt_dict[c] = lambda x: f'₹{x:,.2f}' if isinstance(x, (int, float)) and x else ''
            elif c in ('Net Qty', 'Lots'):
                fmt_dict[c] = lambda x: f'{x:,}' if isinstance(x, (int, float)) else ''
            elif c == 'Strike':
                fmt_dict[c] = lambda x: f'{x}' if x else ''
        s = s.format(fmt_dict)
        return s

    # ── Futures ──
    st.markdown(f'<div class="sec-hdr">📈 Futures Positions</div>', unsafe_allow_html=True)
    fut_rows = [r for r in consolidated if r['section'] == 'FUTURES']
    if fut_rows:
        data = []
        for r in fut_rows:
            m = mtm_lookup.get(r['symbol'], {})
            data.append({
                'Stock': r['stock'], 'Symbol': r['symbol'], 'Expiry': r['expiry'],
                'Stk Price': r['stk_prc'], 'Net Qty': r['net_qty'], 'Lots': r['net_lots'],
                'Buy Avg': r['buy_avg'], 'Sell Avg': r['sell_avg'],
                'Close': r['close'], 'LTP': r['ltp'],
                'LAST MTM': m.get('last_mtm', 0), 'INTRA MTM': m.get('intra_mtm', 0),
                'EXP MTM': m.get('exp_mtm', 0), 'TOTAL': m.get('mtm', 0),
            })
        data.append({
            'Stock': '🔸 TOTAL', 'Symbol': '', 'Expiry': '',
            'Stk Price': None, 'Net Qty': sum(d['Net Qty'] for d in data),
            'Lots': sum(d['Lots'] for d in data),
            'Buy Avg': None, 'Sell Avg': None, 'Close': None, 'LTP': None,
            'LAST MTM': sum(d['LAST MTM'] for d in data),
            'INTRA MTM': sum(d['INTRA MTM'] for d in data),
            'EXP MTM': sum(d['EXP MTM'] for d in data),
            'TOTAL': sum(d['TOTAL'] for d in data),
        })
        df = pd.DataFrame(data)
        st.dataframe(make_styled(df, mtm_cols), use_container_width=True, height=280)

    # ── PE Options ──
    st.markdown(f'<div class="sec-hdr">🔴 PUT Options (PE)</div>', unsafe_allow_html=True)
    pe_rows = [r for r in consolidated if r['section'] == 'PE']
    if pe_rows:
        data = []
        for r in pe_rows:
            m = mtm_lookup.get(r['symbol'], {})
            data.append({
                'Stock': r['stock'], 'Symbol': r['symbol'],
                'Strike': str(r['strike']), 'Expiry': r['expiry'],
                'Net Qty': r['net_qty'], 'Lots': r['net_lots'],
                'Sell Avg': r['sell_avg'], 'Buy Avg': r['buy_avg'],
                'Close': r['close'], 'LTP': r['ltp'],
                'LAST MTM': m.get('last_mtm', 0), 'INTRA MTM': m.get('intra_mtm', 0),
                'EXP MTM': m.get('exp_mtm', 0), 'TOTAL': m.get('mtm', 0),
            })
        data.append({
            'Stock': '🔸 TOTAL', 'Symbol': '', 'Strike': '', 'Expiry': '',
            'Net Qty': sum(d['Net Qty'] for d in data), 'Lots': sum(d['Lots'] for d in data),
            'Sell Avg': None, 'Buy Avg': None, 'Close': None, 'LTP': None,
            'LAST MTM': sum(d['LAST MTM'] for d in data),
            'INTRA MTM': sum(d['INTRA MTM'] for d in data),
            'EXP MTM': sum(d['EXP MTM'] for d in data),
            'TOTAL': sum(d['TOTAL'] for d in data),
        })
        df = pd.DataFrame(data)
        st.dataframe(make_styled(df, mtm_cols), use_container_width=True, height=360)

    # ── CE Options ──
    st.markdown(f'<div class="sec-hdr">🟢 CALL Options (CE)</div>', unsafe_allow_html=True)
    ce_rows = [r for r in consolidated if r['section'] == 'CE']
    active_ce = [r for r in ce_rows if r['net_qty'] != 0]
    if active_ce:
        data = []
        for r in active_ce:
            m = mtm_lookup.get(r['symbol'], {})
            data.append({
                'Stock': r['stock'], 'Symbol': r['symbol'],
                'Strike': str(r['strike']), 'Expiry': r['expiry'],
                'Net Qty': r['net_qty'], 'Lots': r['net_lots'],
                'Buy Avg': r['buy_avg'], 'Sell Avg': r['sell_avg'],
                'Close': r['close'], 'LTP': r['ltp'],
                'LAST MTM': m.get('last_mtm', 0), 'INTRA MTM': m.get('intra_mtm', 0),
                'EXP MTM': m.get('exp_mtm', 0), 'TOTAL': m.get('mtm', 0),
            })
        df = pd.DataFrame(data)
        st.dataframe(make_styled(df, mtm_cols), use_container_width=True, height=250)
    else:
        st.info("All CE options are squared off (net qty = 0)")

    squared_ce = [r for r in ce_rows if r['net_qty'] == 0]
    if squared_ce:
        with st.expander("Squared-off CE Options (reference)"):
            data = [{'Stock': r['stock'], 'Symbol': r['symbol'], 'Strike': str(r['strike']),
                     'Expiry': r['expiry'], 'Buy Avg': r['buy_avg'], 'Sell Avg': r['sell_avg'],
                     'LTP': r['ltp']} for r in squared_ce]
            st.dataframe(pd.DataFrame(data), use_container_width=True, height=200)

    # ── Grand Total KPIs ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_html("G.T. LAST MTM", mtm_data.get('last_total', 0),
                             fmt(mtm_data.get('last_total', 0))), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_html("G.T. Intraday", mtm_data.get('intra_total', 0),
                             fmt(mtm_data.get('intra_total', 0))), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_html("G.T. Expiry", mtm_data.get('exp_total', 0),
                             fmt(mtm_data.get('exp_total', 0))), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_html("Grand Total", mtm_data.get('total_mtm', 0),
                             fmt(mtm_data.get('total_mtm', 0))), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# TAB 3: SCENARIOS
# ═══════════════════════════════════════════════════════════════

def render_scenarios(t):
    mc = get_mtm_calculator()
    pm = get_position_manager()
    quotes = st.session_state.get('quotes', {})
    positions = pm.get_all_positions()

    st.markdown(f'<div class="sec-hdr">📊 Overall Scenario Analysis (-10% to +10%)</div>', unsafe_allow_html=True)
    scenarios = mc.generate_scenario_table(positions, quotes)

    if scenarios:
        rows = []
        for s in scenarios:
            row = {'Scenario': s['percentage']}
            for stock in positions.keys():
                row[stock] = s['stocks'].get(stock, 0)
            row['TOTAL'] = s['total_mtm']
            rows.append(row)

        df = pd.DataFrame(rows)
        num_cols = [c for c in df.columns if c != 'Scenario']
        styled = df.style.map(
            lambda v: style_mtm_val(v, t), subset=num_cols
        ).format({c: '₹{:,.0f}' for c in num_cols})
        st.dataframe(styled, use_container_width=True, height=420)

        # Interactive line chart
        fig = go.Figure()
        stock_list = list(positions.keys())
        colors = [t['accent'], t['accent2'], t['green'], t['orange'], t['cyan'], t['red']]

        def hex_to_rgba(hex_color, alpha=0.04):
            """Convert hex color to rgba string."""
            h = hex_color.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f'rgba({r},{g},{b},{alpha})'

        for i, stock in enumerate(stock_list):
            y_vals = [s['stocks'].get(stock, 0) for s in scenarios]
            col = colors[i % len(colors)]
            fig.add_trace(go.Scatter(
                x=[s['percentage'] for s in scenarios], y=y_vals,
                name=stock, mode='lines+markers',
                line=dict(color=col, width=2.5),
                marker=dict(size=7),
                fill='tonexty' if i > 0 else 'tozeroy',
                fillcolor=hex_to_rgba(col, 0.04),
                hovertemplate=f'<b>{stock}</b><br>Scenario: %{{x}}<br>MTM: ₹%{{y:,.0f}}<extra></extra>',
            ))
        fig.add_trace(go.Scatter(
            x=[s['percentage'] for s in scenarios],
            y=[s['total_mtm'] for s in scenarios],
            name='TOTAL', mode='lines+markers',
            line=dict(color=t['text_primary'], width=3, dash='dot'),
            marker=dict(size=9, symbol='diamond'),
            hovertemplate='<b>TOTAL</b><br>Scenario: %{x}<br>MTM: ₹%{y:,.0f}<extra></extra>',
        ))
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color=t['text_muted'], line_width=1,
                      annotation_text="Break-even", annotation_position="bottom left",
                      annotation_font_color=t['text_muted'])
        fig.update_layout(**get_plotly_layout(t, height=420, title="Scenario Projection"),
                          yaxis_title="MTM (₹)")
        st.plotly_chart(fig, width='stretch', key="scenario_line")

    # ── Per-stock ──
    st.markdown(f'<div class="sec-hdr">📈 Per-Stock Scenario Breakdown</div>', unsafe_allow_html=True)
    stock_tabs = st.tabs(list(positions.keys()))

    colors = [t['accent'], t['accent2'], t['green'], t['orange'], t['cyan'], t['red']]

    for idx, (tab, (stock, data)) in enumerate(zip(stock_tabs, positions.items())):
        with tab:
            stock_scenarios = mc.generate_stock_scenario_table(stock, data, quotes)
            if stock_scenarios:
                rows = [{'Scenario': s['percentage'], 'Futures MTM': s['futures_mtm'],
                         'Options MTM': s['options_mtm'], 'Total MTM': s['total_mtm']}
                        for s in stock_scenarios]
                df = pd.DataFrame(rows)
                sc_cols = ['Futures MTM', 'Options MTM', 'Total MTM']
                styled = df.style.map(
                    lambda v: style_mtm_val(v, t), subset=sc_cols
                ).format({c: '₹{:,.0f}' for c in sc_cols})
                st.dataframe(styled, use_container_width=True, height=380)

                # Grouped bar + line
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[s['percentage'] for s in stock_scenarios],
                    y=[s['futures_mtm'] for s in stock_scenarios],
                    name='Futures', marker_color=t['accent'],
                    hovertemplate='Futures: ₹%{y:,.0f}<extra></extra>',
                ))
                fig.add_trace(go.Bar(
                    x=[s['percentage'] for s in stock_scenarios],
                    y=[s['options_mtm'] for s in stock_scenarios],
                    name='Options', marker_color=t['accent2'],
                    hovertemplate='Options: ₹%{y:,.0f}<extra></extra>',
                ))
                fig.add_trace(go.Scatter(
                    x=[s['percentage'] for s in stock_scenarios],
                    y=[s['total_mtm'] for s in stock_scenarios],
                    name='Total', mode='lines+markers',
                    line=dict(color=t['text_primary'], width=2.5),
                    marker=dict(size=7),
                    hovertemplate='Total: ₹%{y:,.0f}<extra></extra>',
                ))
                fig.add_hline(y=0, line_dash="dash", line_color=t['text_muted'], line_width=1)
                fig.update_layout(**get_plotly_layout(t, height=360, title=f"{stock} Scenarios"),
                                  barmode='group', yaxis_title="MTM (₹)")
                st.plotly_chart(fig, width='stretch', key=f"scenario_{stock}")


# ═══════════════════════════════════════════════════════════════
# TAB 4: TRADE INFO
# ═══════════════════════════════════════════════════════════════

def render_trade_info(t):
    pm = get_position_manager()
    quotes = st.session_state.get('quotes', {})
    trade_info = pm.get_trade_info(quotes)

    st.markdown(f'<div class="sec-hdr">📑 Opening Positions / Trade Info</div>', unsafe_allow_html=True)

    total_buy_amt, total_sell_amt, total_gross_mtm, total_closing_mtm = 0, 0, 0, 0

    if trade_info:
        data = []
        for ti in trade_info:
            # Fix Arrow serialization: use None instead of empty strings for numeric columns
            buy_qty = ti['buy_qty']
            sell_qty = ti['sell_qty']
            
            # Ensure numeric values are proper Python types, not empty strings
            if buy_qty == '' or buy_qty is None:
                buy_qty = None
            if sell_qty == '' or sell_qty is None:
                sell_qty = None
                
            data.append({
                'Stock': ti['stock'], 'Scrip': ti['scrip_name'], 'Type': ti['instrument_type'],
                'Buy Qty': buy_qty, 'Buy Avg': ti['buy_avg_prc'],
                'Buy Amt': ti['buy_amt'],
                'Sell Qty': sell_qty, 'Sell Avg': ti['sell_avg_prc'],
                'Sell Amt': ti['sell_amt'],
                'Net Qty': ti['net_qty'], 'Close': ti['closing_price'],
                'LTP': ti['ltp'],
                'Gross MTM': ti['gross_mtm'], 'Closing MTM': ti['closing_mtm'],
            })
            total_buy_amt += ti['buy_amt'] or 0
            total_sell_amt += ti['sell_amt'] or 0
            total_gross_mtm += ti['gross_mtm'] or 0
            total_closing_mtm += ti['closing_mtm'] or 0

        data.append({
            'Stock': '🔸 TOTAL', 'Scrip': '', 'Type': '',
            'Buy Qty': None, 'Buy Avg': None, 'Buy Amt': total_buy_amt,
            'Sell Qty': None, 'Sell Avg': None, 'Sell Amt': total_sell_amt,
            'Net Qty': None, 'Close': None, 'LTP': None,
            'Gross MTM': total_gross_mtm, 'Closing MTM': total_closing_mtm,
        })

        df = pd.DataFrame(data)
        
        # Format function that handles None values properly
        def fmt_price(x):
            if x is None or (isinstance(x, str) and x == ''):
                return ''
            if isinstance(x, (int, float)) and x:
                return f'₹{x:,.2f}'
            return ''
        
        def fmt_amt(x):
            if x is None or (isinstance(x, str) and x == ''):
                return ''
            if isinstance(x, (int, float)):
                return f'₹{x:,.0f}'
            return ''
        
        def fmt_mtm(x):
            if x is None or (isinstance(x, str) and x == ''):
                return '₹0'
            if isinstance(x, (int, float)):
                return f'₹{x:,.0f}'
            return '₹0'
        
        styled = df.style.map(
            lambda v: style_mtm_val(v, t), subset=['Gross MTM', 'Closing MTM']
        ).format({
            'Buy Avg': fmt_price,
            'Buy Amt': fmt_amt,
            'Sell Avg': fmt_price,
            'Sell Amt': fmt_amt,
            'Close': fmt_price,
            'LTP': fmt_price,
            'Gross MTM': fmt_mtm,
            'Closing MTM': fmt_mtm,
        })
        st.dataframe(styled, use_container_width=True, height=500)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_html("Total Buy Value", total_buy_amt, fmt(total_buy_amt)), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_html("Total Sell Value", total_sell_amt, fmt(total_sell_amt)), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_html("Gross MTM", total_gross_mtm, fmt(total_gross_mtm)), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_html("Closing MTM", total_closing_mtm, fmt(total_closing_mtm)), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# TAB 5: WATCHLIST
# ═══════════════════════════════════════════════════════════════

def render_watchlist(t):
    wm = get_watchlist_manager()
    quotes = st.session_state.get('quotes', {})

    c1, c2 = st.columns([3, 1])

    with c1:
        st.markdown(f'<div class="sec-hdr">🔔 Watchlist</div>', unsafe_allow_html=True)
        watchlist = wm.get_watchlist()
        if watchlist:
            data = []
            for item in watchlist:
                symbol = item['symbol']
                target = item['target_price']
                current = quotes.get(symbol, {}).get('ltp', 0)
                change_pct = quotes.get(symbol, {}).get('change_pct', 0)
                alert_type = item['alert_type']
                triggered = (alert_type == 'cross_above' and current >= target) or \
                            (alert_type == 'cross_below' and current <= target)
                distance = ((target - current) / current * 100) if current > 0 else 0

                data.append({
                    'Symbol': symbol, 'Exchange': item['exchange'],
                    'Current': current, 'Target': target,
                    'Distance': f"{distance:+.2f}%",
                    'Alert': alert_type.replace('_', ' ').title(),
                    'Change %': f"{change_pct:+.2f}%",
                    'Status': '🔴 TRIGGERED' if triggered else '🟢 Watching',
                })
            df = pd.DataFrame(data)
            st.dataframe(df.style.format({'Current': '₹{:,.2f}', 'Target': '₹{:,.2f}'}),
                         use_container_width=True, height=350)
        else:
            st.info("Watchlist is empty. Add symbols →")

    with c2:
        st.markdown(f'<div class="sec-hdr">➕ Add Symbol</div>', unsafe_allow_html=True)
        with st.form("add_watchlist", clear_on_submit=True):
            symbol = st.text_input("Symbol")
            exchange = st.selectbox("Exchange", ["NSECM", "NSEFO", "BSECM", "BSEFO"])
            target_price = st.number_input("Target Price", min_value=0.0, step=1.0)
            alert_type = st.selectbox("Alert Type", ["cross_above", "cross_below"])
            if st.form_submit_button("Add to Watchlist"):
                if symbol and target_price > 0:
                    if wm.add_to_watchlist(symbol, exchange, target_price, alert_type):
                        st.success(f"Added {symbol}")
                        st.rerun()
                    else:
                        st.error("Already in watchlist")


# ═══════════════════════════════════════════════════════════════
# TAB 6: MARGIN
# ═══════════════════════════════════════════════════════════════

def render_margin(t):
    mcalc = get_margin_calculator()
    pm = get_position_manager()
    quotes = st.session_state.get('quotes', {})
    positions = pm.get_all_positions()
    margin_result = mcalc.calculate_total_margin(positions, quotes)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(kpi_html("Total Margin", margin_result['total_margin'],
                             fmt(margin_result['total_margin'])), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_html("Futures Margin", margin_result['futures_margin'],
                             fmt(margin_result['futures_margin'])), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_html("Options Margin", margin_result['options_margin'],
                             fmt(margin_result['options_margin'])), unsafe_allow_html=True)

    st.markdown(f'<div class="sec-hdr">💰 Margin Breakdown</div>', unsafe_allow_html=True)
    if margin_result['breakdown']:
        df = pd.DataFrame(margin_result['breakdown'])
        df.columns = ['Stock', 'Futures Margin', 'Options Margin', 'Total Margin']

        # Interactive horizontal bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df['Stock'], x=df['Futures Margin'], name='Futures',
            orientation='h', marker_color=t['accent'],
            hovertemplate='Futures: ₹%{x:,.0f}<extra></extra>',
        ))
        fig.add_trace(go.Bar(
            y=df['Stock'], x=df['Options Margin'], name='Options',
            orientation='h', marker_color=t['accent2'],
            hovertemplate='Options: ₹%{x:,.0f}<extra></extra>',
        ))
        fig.update_layout(**get_plotly_layout(t, height=300, title="Margin by Stock"),
                          barmode='stack', xaxis_title="Margin (₹)")
        st.plotly_chart(fig, width='stretch', key="margin_bar")

        styled = df.style.format({
            'Futures Margin': '₹{:,.0f}',
            'Options Margin': '₹{:,.0f}',
            'Total Margin': '₹{:,.0f}',
        })
        st.dataframe(styled, use_container_width=True, height=250)

    st.markdown(f'<div class="sec-hdr">🧮 Order Margin Calculator</div>', unsafe_allow_html=True)
    with st.form("order_margin"):
        c1, c2 = st.columns(2)
        with c1:
            symbol = st.text_input("Symbol")
            quantity = st.number_input("Quantity", min_value=1, step=1)
            price = st.number_input("Price", min_value=0.0, step=0.5)
        with c2:
            product_type = st.selectbox("Product Type", ["MIS", "NRML", "CNC", "CO", "BO"])
            exchange = st.selectbox("Exchange", ["NSEFO", "NSECM", "BSEFO", "BSECM"])
        if st.form_submit_button("Calculate Margin"):
            if symbol and quantity > 0 and price > 0:
                result = mcalc.calculate_order_margin(symbol, quantity, price, product_type, exchange)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(kpi_html("Margin Required", result['required_margin'],
                                         fmt(result['required_margin'])), unsafe_allow_html=True)
                with c2:
                    st.markdown(kpi_html("Leverage", result['leverage'],
                                         f"{result['leverage']}x"), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# TAB 7: SETTINGS
# ═══════════════════════════════════════════════════════════════

def render_settings(t):
    st.markdown(f'<div class="sec-hdr">⚙️ Dashboard Settings</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        mode = "badge-demo" if DEMO_MODE else "badge-live"
        mode_text = "Demo Mode Active" if DEMO_MODE else "Live Trading Active"
        st.markdown(f'<span class="badge {mode}">{mode_text}</span>', unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.caption(f"Refresh interval: {REFRESH_INTERVAL_SECONDS}s")
        st.caption(f"Theme & auto-refresh controls are in the sidebar ←")

    with c2:
        if st.button("🔄 Force Refresh Data"):
            refresh_data()
            st.rerun()
        if st.button("🗑️ Clear All Alerts"):
            get_alert_system().clear_triggered_alerts()
            st.success("Alerts cleared")
            st.rerun()

    st.markdown(f'<div class="sec-hdr">🔑 API Configuration</div>', unsafe_allow_html=True)
    st.info("Configure XTS credentials in `config/settings.py` for live trading.")

    if DEMO_MODE:
        st.markdown(f"""
        <div style="background-color:{t['bg_card']};border:1px solid {t['border']};
                    border-radius:10px;padding:18px 22px;margin-top:10px;">
            <p style="color:{t['accent2']};font-weight:600;margin-bottom:10px;">📋 Switch to Live Mode</p>
            <ol style="color:{t['text_secondary']};font-size:0.88rem;line-height:1.8;">
                <li>Get XTS API credentials (<code>appKey</code>, <code>secretKey</code>)</li>
                <li>Set in <code>config/settings.py</code> or environment variables</li>
                <li>Set <code>DEMO_MODE = False</code></li>
                <li>Restart the dashboard</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# SIDEBAR ALERTS
# ═══════════════════════════════════════════════════════════════

def render_sidebar_alerts():
    wm = get_watchlist_manager()
    quotes = st.session_state.get('quotes', {})
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔔 Alerts")
    
    triggered = wm.check_alerts(quotes)
    if triggered:
        st.sidebar.error(f"⚠️ {len(triggered)} Alert(s)!")
        for alert in triggered[:5]:
            st.sidebar.markdown(
                f"**{alert['symbol']}**: ₹{alert['current_price']:,.2f} "
                f"(Target: ₹{alert['target_price']:,.2f})"
            )
    else:
        st.sidebar.success("✅ No alerts triggered")


# ═══════════════════════════════════════════════════════════════
# PAGE WRAPPERS (for st.navigation — each runs in isolation)
# ═══════════════════════════════════════════════════════════════

def _page_setup():
    """Common setup for every page: session, theme, CSS, sidebar, data."""
    init_session()
    t = get_theme()
    st.markdown(build_css(t), unsafe_allow_html=True)

    # ── Sidebar: Theme & Refresh ──
    st.sidebar.markdown("---")
    current_theme = st.session_state.get('theme_mode', 'dark')
    new_theme = st.sidebar.selectbox(
        "🎨 Theme",
        ["dark", "light"],
        index=0 if current_theme == "dark" else 1,
        format_func=lambda x: "🌙 Dark" if x == "dark" else "☀️ Light",
    )
    if new_theme != current_theme:
        st.session_state.theme_mode = new_theme
        st.rerun()

    auto_ref = st.sidebar.checkbox("Auto Refresh", value=st.session_state.get('auto_refresh', True))
    st.session_state.auto_refresh = auto_ref

    render_sidebar_alerts()

    # Load data
    with st.spinner('Loading...'):
        refresh_data()

    render_header(t)
    return t


def page_overview():
    t = _page_setup()
    render_overview(t)
    if st.session_state.get('auto_refresh', True):
        time.sleep(REFRESH_INTERVAL_SECONDS)
        st.rerun()


def page_positions():
    t = _page_setup()
    render_positions(t)
    if st.session_state.get('auto_refresh', True):
        time.sleep(REFRESH_INTERVAL_SECONDS)
        st.rerun()


def page_scenarios():
    t = _page_setup()
    render_scenarios(t)
    if st.session_state.get('auto_refresh', True):
        time.sleep(REFRESH_INTERVAL_SECONDS)
        st.rerun()


def page_trade_info():
    t = _page_setup()
    render_trade_info(t)
    if st.session_state.get('auto_refresh', True):
        time.sleep(REFRESH_INTERVAL_SECONDS)
        st.rerun()


def page_watchlist():
    t = _page_setup()
    render_watchlist(t)
    if st.session_state.get('auto_refresh', True):
        time.sleep(REFRESH_INTERVAL_SECONDS)
        st.rerun()


def page_margin():
    t = _page_setup()
    render_margin(t)
    if st.session_state.get('auto_refresh', True):
        time.sleep(REFRESH_INTERVAL_SECONDS)
        st.rerun()


def page_settings():
    t = _page_setup()
    render_settings(t)
    if st.session_state.get('auto_refresh', True):
        time.sleep(REFRESH_INTERVAL_SECONDS)
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# MAIN — Native Multi-Page Navigation (no DOM leaking)
# ═══════════════════════════════════════════════════════════════

pages = st.navigation([
    st.Page(page_overview,   title="Overview",   icon="📊"),
    st.Page(page_positions,  title="Positions",  icon="📋"),
    st.Page(page_scenarios,  title="Scenarios",  icon="📈"),
    st.Page(page_trade_info, title="Trade Info",  icon="📑"),
    st.Page(page_watchlist,  title="Watchlist",  icon="🔔"),
    st.Page(page_margin,     title="Margin",     icon="💰"),
    st.Page(page_settings,   title="Settings",   icon="⚙️"),
])

pages.run()



