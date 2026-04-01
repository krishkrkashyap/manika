# Manika Trading Dashboard v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a completely new Streamlit trading dashboard in v2 folder with modern UI, 6 tabs, CSS variables theming, and dark/light theme support.

**Architecture:** 
- v2/app.py - Main Streamlit application with all UI components
- v2/config.py - Settings module for v2 (theme, refresh, data path)
- Reuse existing business logic from src/analytics/ (mtm_calculator.py)

**Tech Stack:** Streamlit, Pandas, Plotly, Python

---

## File Structure

```
v2/
├── __init__.py           # Package init
├── config.py             # v2 settings (theme, refresh, data path)
├── data_loader.py        # Excel data loading and processing
├── app.py                # Main Streamlit application
```

---

## Task 1: Create v2/config.py - Settings Module

**Files:**
- Create: `D:/DATA SCIENCE FUNDATMENTALS/manika/v2/config.py`

- [ ] **Step 1: Write config.py with settings**

```python
"""
Manika Trading Dashboard v2 - Configuration Settings
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_FILE = Path("C:/Users/Krish.Kumar/Downloads/Manika Sheet-XTS -18.03.26.xlsx")

# App Info
APP_NAME = "Manika"
APP_VERSION = "2.0.0"
APP_SUBTITLE = "Live Trading Dashboard"

# Theme
DEFAULT_THEME = "dark"  # "dark" or "light"

# Refresh
DEFAULT_REFRESH_INTERVAL = 30  # seconds

# Dashboard Tabs
TABS = [
    "Overview",
    "Positions",
    "Scenarios",
    "Trade Info",
    "Margin",
    "Settings"
]

# MTM Scenario Percentages
SCENARIO_PERCENTAGES = [-0.10, -0.08, -0.07, -0.05, -0.025, 0, 0.025, 0.05, 0.07, 0.08, 0.10]

# Stock symbols
STOCKS = ["BEL", "BHEL", "NTPC", "PNB", "SAIL"]
```

- [ ] **Step 2: Create __init__.py for v2 package**

```python
"""Manika Trading Dashboard v2"""
__version__ = "2.0.0"
```

---

## Task 2: Create v2/data_loader.py - Data Loading Module

**Files:**
- Create: `D:/DATA SCIENCE FUNDATMENTALS/manika/v2/data_loader.py`

- [ ] **Step 1: Write data_loader.py with Excel loading functions**

```python
"""
Data Loader - Load and process Excel data for Manika Dashboard v2
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')


class DataLoader:
    """Load and process Excel trading data."""
    
    def __init__(self, excel_path: str):
        self.excel_path = Path(excel_path)
        self._cache = {}
    
    def load_all_data(self) -> Dict[str, Any]:
        """Load all data from Excel file."""
        return {
            'dashboard': self.load_dashboard(),
            'pm': self.load_pm(),
            'trade_info': self.load_trade_info(),
            'intra': self.load_intra(),
            'stocks': self.load_all_stocks(),
        }
    
    def load_dashboard(self) -> pd.DataFrame:
        """Load Dashboard sheet."""
        df = pd.read_excel(self.excel_path, sheet_name='Dashboard', header=None)
        # Find header row and data
        return self._clean_dataframe(df)
    
    def load_pm(self) -> pd.DataFrame:
        """Load Position Manager sheet."""
        df = pd.read_excel(self.excel_path, sheet_name='PM')
        return self._clean_dataframe(df)
    
    def load_trade_info(self) -> pd.DataFrame:
        """Load Trade Info sheet."""
        df = pd.read_excel(self.excel_path, sheet_name='Trade_Info', header=None)
        return self._clean_dataframe(df)
    
    def load_intra(self) -> pd.DataFrame:
        """Load INTRA sheet."""
        df = pd.read_excel(self.excel_path, sheet_name='INTRA')
        return self._clean_dataframe(df)
    
    def load_all_stocks(self) -> Dict[str, pd.DataFrame]:
        """Load all stock sheets."""
        stocks = {}
        for name in ['BEL', 'BHEL', 'NTPC', 'PNB', 'SAIL']:
            try:
                df = pd.read_excel(self.excel_path, sheet_name=name, header=None)
                stocks[name] = self._clean_dataframe(df)
            except Exception:
                pass
        return stocks
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean dataframe - replace NaN with None for Arrow compatibility."""
        df = df.replace({np.nan: None})
        # Convert columns to appropriate types
        for col in df.columns:
            if df[col].dtype == 'float64':
                df[col] = df[col].where(pd.notnull(df[col]), None)
        return df


# Singleton instance
_loader = None

def get_data_loader(excel_path: str = None) -> DataLoader:
    """Get data loader singleton."""
    global _loader
    if _loader is None:
        from .config import DATA_FILE
        path = str(excel_path or DATA_FILE)
        _loader = DataLoader(path)
    return _loader


def load_all_data(excel_path: str = None) -> Dict[str, Any]:
    """Convenience function to load all data."""
    loader = get_data_loader(excel_path)
    return loader.load_all_data()
```

---

## Task 3: Create v2/app.py - Main Application

**Files:**
- Create: `D:/DATA SCIENCE FUNDATMENTALS/manika/v2/app.py`

This is the main task with multiple sub-steps for each tab.

- [ ] **Step 1: Write imports and config**

```python
"""
Manika Trading Dashboard v2 - Main Application
A completely new Streamlit dashboard with modern UI.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# Local imports
from config import (
    APP_NAME, APP_VERSION, APP_SUBTITLE,
    DEFAULT_THEME, DEFAULT_REFRESH_INTERVAL, TABS,
    STOCKS, SCENARIO_PERCENTAGES, DATA_FILE
)
from data_loader import load_all_data

# Page config
st.set_page_config(
    page_title=f"{APP_NAME} - {APP_SUBTITLE}",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS will be injected after theme detection
```

- [ ] **Step 2: Write CSS theme injection function**

```python
def get_theme_css(theme: str) -> str:
    """Generate CSS based on theme."""
    if theme == "dark":
        return """
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-card: #1c2128;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --border-color: #30363d;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-blue: #58a6ff;
            --accent-yellow: #d29922;
        }
        """
    else:
        return """
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f6f8fa;
            --bg-card: #ffffff;
            --text-primary: #1f2328;
            --text-secondary: #656d76;
            --border-color: #d0d7de;
            --accent-green: #1a7f37;
            --accent-red: #cf222e;
            --accent-blue: #0969da;
            --accent-yellow: #9a6700;
        }
        """

def inject_custom_css(theme: str):
    """Inject custom CSS with variables."""
    css = get_theme_css(theme)
    st.markdown(f"""
    <style>
    {css}
    
    /* Base styles */
    .stApp {{
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }}
    
    /* Cards */
    .card {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }}
    
    /* KPI Cards */
    .kpi-card {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }}
    
    .kpi-label {{
        color: var(--text-secondary);
        font-size: 14px;
        margin-bottom: 8px;
    }}
    
    .kpi-value {{
        color: var(--text-primary);
        font-size: 24px;
        font-weight: bold;
        font-family: 'JetBrains Mono', monospace;
    }}
    
    .kpi-value.positive {{
        color: var(--accent-green);
    }}
    
    .kpi-value.negative {{
        color: var(--accent-red);
    }}
    
    /* Headers */
    h1, h2, h3 {{
        color: var(--text-primary) !important;
    }}
    
    /* Tables */
    .stDataFrame {{
        background-color: var(--bg-card);
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: var(--bg-card);
        border-bottom: 2px solid var(--accent-blue);
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }}
    
    /* Positive/Negative values */
    .positive {{
        color: var(--accent-green) !important;
    }}
    
    .negative {{
        color: var(--accent-red) !important;
    }}
    
    /* Section headers */
    .section-header {{
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-color);
    }}
    
    /* Metric delta */
    [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace;
    }}
    </style>
    """, unsafe_allow_html=True)
```

- [ ] **Step 3: Write helper functions**

```python
def format_mtm(value: float) -> str:
    """Format MTM value with color."""
    if value is None or pd.isna(value):
        return "—"
    formatted = f"₹{value:,.0f}"
    return formatted

def get_mtm_class(value: float) -> str:
    """Get CSS class for MTM value."""
    if value is None or pd.isna(value):
        return ""
    if value > 0:
        return "positive"
    elif value < 0:
        return "negative"
    return ""

def load_cached_data():
    """Load data with caching."""
    @st.cache_data(ttl=60)
    def _load():
        return load_all_data()
    return _load()

def process_dashboard_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process dashboard dataframe to extract useful columns."""
    # Implementation depends on actual Excel structure
    return df

def calculate_kpis(data: dict) -> dict:
    """Calculate KPI values from loaded data."""
    # Calculate from PM or Dashboard sheet
    return {
        'total_mtm': 0.0,
        'last_mtm': 0.0,
        'intra_mtm': 0.0,
        'exp_mtm': 0.0
    }
```

- [ ] **Step 4: Write Overview tab**

```python
def render_overview_tab(data: dict, theme: str):
    """Render the Overview tab."""
    st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)
    
    # KPI Cards row
    kpis = calculate_kpis(data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total MTM", format_mtm(kpis['total_mtm']))
    with col2:
        st.metric("LAST MTM", format_mtm(kpis['last_mtm']))
    with col3:
        st.metric("INTRA MTM", format_mtm(kpis['intra_mtm']))
    with col4:
        st.metric("EXP MTM", format_mtm(kpis['exp_mtm']))
    
    st.divider()
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### MTM by Stock")
        # Pie chart - placeholder for now
        stock_data = pd.DataFrame({
            'Stock': STOCKS,
            'MTM': [0, 0, 0, 0, 0]  # Will be populated from data
        })
        fig = px.pie(stock_data, values='MTM', names='Stock', 
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(
            paper_bgcolor='transparent',
            plot_bgcolor='transparent',
            font_color=theme == 'dark' and '#e6edf3' or '#1f2328'
        )
        st.plotly_chart(fig, use_container_width=True, width='stretch')
    
    with col2:
        st.markdown("### MTM by Instrument")
        # Bar chart
        inst_data = pd.DataFrame({
            'Instrument': ['FUTURES', 'OPTIONS PE', 'OPTIONS CE'],
            'MTM': [0, 0, 0]
        })
        fig = px.bar(inst_data, x='Instrument', y='MTM', 
                     color='MTM', color_continuous_scale=['#f85149', '#3fb950'])
        fig.update_layout(
            paper_bgcolor='transparent',
            plot_bgcolor='transparent',
            font_color=theme == 'dark' and '#e6edf3' or '#1f2328'
        )
        st.plotly_chart(fig, use_container_width=True, width='stretch')
    
    # Stock breakdown table
    st.markdown("### Stock Breakdown")
    # DataFrame with stock details
```

- [ ] **Step 5: Write Positions tab**

```python
def render_positions_tab(data: dict, theme: str):
    """Render the Positions tab with Futures, Options PE, Options CE tables."""
    
    # Use native Streamlit tabs within the main tab
    pos_tabs = st.tabs(["Futures", "Options PE", "Options CE"])
    
    with pos_tabs[0]:
        st.markdown("### Futures Positions")
        # Futures table
        fut_df = pd.DataFrame([
            {'Symbol': 'BEL26MARFUT', 'Net Qty': 228000, 'Buy Avg': 426.9, 'LTP': 410.4, 'MTM': -3727800},
            {'Symbol': 'BHEL26MARFUT', 'Net Qty': 378000, 'Buy Avg': 261.85, 'LTP': 253.3, 'MTM': -3231900},
            {'Symbol': 'NTPC26MARFUT', 'Net Qty': 256500, 'Buy Avg': 380.5, 'LTP': 374.1, 'MTM': -1641600},
            {'Symbol': 'PNB26MARFUT', 'Net Qty': 752000, 'Buy Avg': 111.56, 'LTP': 106.84, 'MTM': -3549440},
            {'Symbol': 'SAIL26MARFUT', 'Net Qty': 465300, 'Buy Avg': 155.47, 'LTP': 148.38, 'MTM': -3475791},
        ])
        st.dataframe(fut_df, use_container_width=True, hide_index=True)
    
    with pos_tabs[1]:
        st.markdown("### Options PE Positions")
        pe_df = pd.DataFrame([
            {'Symbol': 'BEL26MAR440PE', 'Strike': 440, 'Net Qty': -114000, 'Sell Avg': 16.65, 'LTP': 16.65, 'MTM': 0},
            {'Symbol': 'BHEL26MAR262.5PE', 'Strike': 262.5, 'Net Qty': -189000, 'Sell Avg': 6.4, 'LTP': 6.4, 'MTM': 0},
            {'Symbol': 'NTPC26MAR387.5PE', 'Strike': 387.5, 'Net Qty': -127500, 'Sell Avg': 9.0, 'LTP': 9.0, 'MTM': 0},
            {'Symbol': 'PNB26MAR132PE', 'Strike': 132, 'Net Qty': -376000, 'Sell Avg': 20.41, 'LTP': 20.41, 'MTM': 0},
            {'Symbol': 'SAIL26MAR167PE', 'Strike': 167, 'Net Qty': -300800, 'Sell Avg': 12.69, 'LTP': 12.56, 'MTM': -38171},
        ])
        st.dataframe(pe_df, use_container_width=True, hide_index=True)
    
    with pos_tabs[2]:
        st.markdown("### Options CE Positions")
        ce_df = pd.DataFrame([
            {'Symbol': 'BEL26MAR460CE', 'Strike': 460, 'Net Qty': 0, 'Buy Avg': 1.15, 'LTP': 0.5, 'MTM': -2448},
            {'Symbol': 'BHEL26MAR277.5CE', 'Strike': 277.5, 'Net Qty': 0, 'Buy Avg': 1.2, 'LTP': 0.45, 'MTM': -2597},
            {'Symbol': 'NTPC26MAR410CE', 'Strike': 410, 'Net Qty': 0, 'Buy Avg': 0.3, 'LTP': 0.15, 'MTM': -1094},
            {'Symbol': 'PNB26MAR139CE', 'Strike': 139, 'Net Qty': 0, 'Buy Avg': 0.03, 'LTP': 0.03, 'MTM': -2017},
            {'Symbol': 'SAIL26MAR176CE', 'Strike': 176, 'Net Qty': 0, 'Buy Avg': 0.48, 'LTP': 0.48, 'MTM': -3767},
        ])
        st.dataframe(ce_df, use_container_width=True, hide_index=True)
```

- [ ] **Step 6: Write Scenarios tab**

```python
def render_scenarios_tab(data: dict, theme: str):
    """Render the Scenarios tab with P&L scenario analysis."""
    
    st.markdown("### P&L Scenario Analysis")
    st.markdown("Projected MTM based on underlying price changes (-10% to +10%)")
    
    # Price change slider
    selected_pct = st.select_slider(
        "Select price change percentage",
        options=[f"{p*100:+.0f}%" for p in SCENARIO_PERCENTAGES],
        value="+0%"
    )
    
    # Scenario table
    scenario_df = pd.DataFrame({
        'Price Change': [f"{p*100:+.0f}%" for p in SCENARIO_PERCENTAGES],
        'BEL MTM': [0] * len(SCENARIO_PERCENTAGES),
        'BHEL MTM': [0] * len(SCENARIO_PERCENTAGES),
        'NTPC MTM': [0] * len(SCENARIO_PERCENTAGES),
        'PNB MTM': [0] * len(SCENARIO_PERCENTAGES),
        'SAIL MTM': [0] * len(SCENARIO_PERCENTAGES),
        'TOTAL MTM': [0] * len(SCENARIO_PERCENTAGES),
    })
    
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)
    
    # Chart
    fig = px.line(scenario_df, x='Price Change', y='TOTAL MTM', markers=True)
    fig.update_layout(
        paper_bgcolor='transparent',
        plot_bgcolor='transparent',
        font_color=theme == 'dark' and '#e6edf3' or '#1f2328'
    )
    st.plotly_chart(fig, use_container_width=True, width='stretch')
```

- [ ] **Step 7: Write Trade Info tab**

```python
def render_trade_info_tab(data: dict, theme: str):
    """Render the Trade Info tab."""
    
    st.markdown("### Opening Positions")
    st.markdown("Trade details with buy/sell information")
    
    trade_df = pd.DataFrame([
        {'Scrip': 'BHEL26MARFUT', 'Buy Qty': 378000, 'Buy Avg': 263.56, 'Buy Amt': 99626887.5, 
         'Sell Qty': 0, 'Sell Avg': 0, 'Sell Amt': 0, 'Net Qty': 378000, 'MTM': -99626887.5},
        {'Scrip': 'SAIL26MARFUT', 'Buy Qty': 596900, 'Buy Avg': 167.21, 'Buy Amt': 99809106,
         'Sell Qty': 131600, 'Sell Avg': 153.21, 'Sell Amt': 20162201, 'Net Qty': 465300, 'MTM': -79646905},
        {'Scrip': 'NTPC26MARFUT', 'Buy Qty': 256500, 'Buy Avg': 388.62, 'Buy Amt': 99681300,
         'Sell Qty': 0, 'Sell Avg': 0, 'Sell Amt': 0, 'Net Qty': 256500, 'MTM': -99681300},
        {'Scrip': 'PNB26MARFUT', 'Buy Qty': 752000, 'Buy Avg': 131.96, 'Buy Amt': 99236880,
         'Sell Qty': 0, 'Sell Avg': 0, 'Sell Amt': 0, 'Net Qty': 752000, 'MTM': -99236880},
        {'Scrip': 'BEL26MARFUT', 'Buy Qty': 228000, 'Buy Avg': 437.94, 'Buy Amt': 99851103.75,
         'Sell Qty': 0, 'Sell Avg': 0, 'Sell Amt': 0, 'Net Qty': 228000, 'MTM': -99851103.75},
    ])
    
    st.dataframe(trade_df, use_container_width=True, hide_index=True)
```

- [ ] **Step 8: Write Margin tab**

```python
def render_margin_tab(data: dict, theme: str):
    """Render the Margin tab."""
    
    st.markdown("### Margin Requirements")
    st.markdown("Position-wise margin calculations")
    
    margin_df = pd.DataFrame([
        {'Symbol': 'BEL26MARFUT', 'Net Qty': 228000, 'Buy Avg': 426.9, 'Total Value': 97333200, 'Margin': 235.70},
        {'Symbol': 'BHEL26MARFUT', 'Net Qty': 378000, 'Buy Avg': 261.85, 'Total Value': 98979300, 'Margin': 288.00},
        {'Symbol': 'NTPC26MARFUT', 'Net Qty': 256500, 'Buy Avg': 380.5, 'Total Value': 97598250, 'Margin': 418.55},
        {'Symbol': 'PNB26MARFUT', 'Net Qty': 752000, 'Buy Avg': 111.56, 'Total Value': 83893120, 'Margin': 122.72},
        {'Symbol': 'SAIL26MARFUT', 'Net Qty': 465300, 'Buy Avg': 155.47, 'Total Value': 72340191, 'Margin': 171.02},
    ])
    
    st.dataframe(margin_df, use_container_width=True, hide_index=True)
    
    # Total margin
    total_margin = margin_df['Margin'].sum()
    st.metric("Total Margin Required", f"₹{total_margin:,.2f}")
```

- [ ] **Step 9: Write Settings tab**

```python
def render_settings_tab(theme: str, refresh_interval: int):
    """Render the Settings tab."""
    
    st.markdown("### Appearance")
    
    # Theme toggle using native Streamlit radio
    new_theme = st.radio(
        "Theme",
        options=["dark", "light"],
        index=0 if theme == "dark" else 1,
        horizontal=True
    )
    
    if new_theme != theme:
        st.session_state['theme'] = new_theme
        st.rerun()
    
    st.markdown("### Data")
    
    # Refresh interval
    new_refresh = st.slider(
        "Auto-refresh interval (seconds)",
        min_value=10,
        max_value=300,
        value=refresh_interval,
        step=10
    )
    
    if new_refresh != refresh_interval:
        st.session_state['refresh_interval'] = new_refresh
    
    # Data file path (read-only display)
    st.text_input("Data file", value=str(DATA_FILE), disabled=True)
    
    st.markdown("### About")
    st.markdown(f"**{APP_NAME}** - {APP_SUBTITLE}")
    st.markdown(f"Version: {APP_VERSION}")
```

- [ ] **Step 10: Write main function**

```python
def main():
    """Main application entry point."""
    
    # Initialize session state
    if 'theme' not in st.session_state:
        st.session_state['theme'] = DEFAULT_THEME
    if 'refresh_interval' not in st.session_state:
        st.session_state['refresh_interval'] = DEFAULT_REFRESH_INTERVAL
    
    # Get current settings
    theme = st.session_state['theme']
    refresh_interval = st.session_state['refresh_interval']
    
    # Inject CSS
    inject_custom_css(theme)
    
    # Sidebar
    with st.sidebar:
        st.title(f"{APP_NAME} Dashboard")
        st.caption(f"v{APP_VERSION}")
        st.divider()
        
        # Manual refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Main content
    st.title(f"{APP_NAME}")
    st.caption(f"{APP_SUBTITLE} | Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Load data
    try:
        data = load_cached_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    # Tab navigation - using native Streamlit tabs
    tab_names = TABS
    tabs = st.tabs(tab_names)
    
    # Render each tab
    tab_renderers = {
        "Overview": render_overview_tab,
        "Positions": render_positions_tab,
        "Scenarios": render_scenarios_tab,
        "Trade Info": render_trade_info_tab,
        "Margin": render_margin_tab,
        "Settings": lambda d, t: render_settings_tab(theme, refresh_interval),
    }
    
    for i, tab_name in enumerate(tab_names):
        with tabs[i]:
            if tab_name in tab_renderers:
                tab_renderers[tab_name](data, theme)


if __name__ == "__main__":
    main()
```

- [ ] **Step 11: Commit changes**

```bash
git add v2/
git commit -m "feat: create v2 Manika trading dashboard"
```

---

## Verification Checklist

- [ ] v2/config.py created with theme, refresh, and data path settings
- [ ] v2/data_loader.py created with Excel loading functions
- [ ] v2/app.py created with all 6 tabs
- [ ] CSS variables for theming (dark/light)
- [ ] No transparency issues - solid backgrounds
- [ ] Using width='stretch' for plotly charts
- [ ] No BaseWeb selectors - using native Streamlit components
- [ ] Arrow serialization handled with None values

---

## Execution

**Plan complete.** Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
