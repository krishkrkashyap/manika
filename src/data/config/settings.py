"""
Application settings and configuration.
"""
import os
from pathlib import Path

# ═══════════════════════════════════════════════════════
# PATH CONFIGURATION
# ═══════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# ═══════════════════════════════════════════════════════
# APP CONFIGURATION
# ═══════════════════════════════════════════════════════
APP_NAME = "Manika's Dashboard"
APP_VERSION = "1.3.5"
APP_SUBTITLE = "Live Trading Dashboard"

# Demo mode - when True, uses simulated data
# Set to False when XTS credentials are available
DEMO_MODE = True

# Theme
THEME = "dark"  # "dark" or "light"

# ═══════════════════════════════════════════════════════
# XTS API CONFIGURATION (Set credentials when ready)
# ═══════════════════════════════════════════════════════
XTS_CONFIG = {
    "app_key": os.getenv("XTS_APP_KEY", ""),
    "secret_key": os.getenv("XTS_SECRET_KEY", ""),
    "user_id": os.getenv("XTS_USER_ID", ""),
    # Market Data API  (Binary Marketdata / REST + Socket.IO)
    "market_data_url": "https://developers.symphonyfintech.in/apimarketdata",
    # Interactive (Trading) API  (Orders / Positions / Balance)
    "trading_url": "https://developers.symphonyfintech.in/1interactive",
    # Host Lookup URL (for obtaining connectionString + UniqueKey)
    "host_lookup_url": "https://developers.symphonyfintech.in/hostlookup",
}

# ═══════════════════════════════════════════════════════
# REFRESH SETTINGS
# ═══════════════════════════════════════════════════════
REFRESH_INTERVAL_SECONDS = 5
WEBSOCKET_RECONNECT_DELAY = 5

# ═══════════════════════════════════════════════════════
# DASHBOARD TABS
# ═══════════════════════════════════════════════════════
DASHBOARD_TABS = [
    "📊 Overview",
    "📋 Positions",
    "📈 Scenarios",
    "📑 Trade Info",
    "🔔 Watchlist",
    "💰 Margin",
    "⚙️ Settings",
]

# ═══════════════════════════════════════════════════════
# EXCHANGE SEGMENTS (XTS Codes)
# ═══════════════════════════════════════════════════════
EXCHANGE_SEGMENTS = {
    "NSECM": 1,   # NSE Equity Cash
    "NSEFO": 2,   # NSE Futures & Options
    "NSECD": 3,   # NSE Currency Derivatives
    "BSECM": 11,  # BSE Equity Cash
    "BSEFO": 12,  # BSE Futures & Options
    "BSECD": 13,  # BSE Currency Derivatives
    "MCXFO": 51,  # MCX Commodity Derivatives
    "NCDEX": 52,  # NCDEX Agricultural Commodities
}

# ═══════════════════════════════════════════════════════
# INSTRUMENT TYPES
# ═══════════════════════════════════════════════════════
INSTRUMENT_TYPES = {
    "FUTURES": 1,
    "OPTIONS": 2,
    "EQUITY": 8,
}

# ═══════════════════════════════════════════════════════
# ALERT THRESHOLDS
# ═══════════════════════════════════════════════════════
DEFAULT_ALERT_THRESHOLDS = {
    "price_drop_2_5_percent": -2.5,
    "price_drop_5_percent": -5.0,
    "price_drop_10_percent": -10.0,
    "price_rise_2_5_percent": 2.5,
    "price_rise_5_percent": 5.0,
    "price_rise_10_percent": 10.0,
}

# ═══════════════════════════════════════════════════════
# MTM SCENARIO PERCENTAGES
# ═══════════════════════════════════════════════════════
MTM_SCENARIO_PERCENTAGES = [-0.10, -0.08, -0.07, -0.05, -0.025, 0, 0.025, 0.05, 0.07, 0.08, 0.10]
