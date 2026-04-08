"""
Configuration Settings for Money Class Dashboard
"""

import os
from pathlib import Path

# Path Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# App Configuration
APP_NAME = "Money Class Dashboard"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Live Trading Dashboard"

# Demo Mode - Set to False when XTS credentials are ready
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# XTS API Configuration
XTS_CONFIG = {
    # Trading (Interactive) API credentials
    "trading_app_key": os.getenv("XTS_TRADING_APP_KEY", "0daeeb05bfd840e59a1116"),
    "trading_secret_key": os.getenv("XTS_TRADING_SECRET_KEY", "Kftw578#@G"),
    # Market Data API credentials
    "market_data_app_key": os.getenv(
        "XTS_MARKET_DATA_APP_KEY", "ddc9ca260dee67556bd436"
    ),
    "market_data_secret_key": os.getenv("XTS_MARKET_DATA_SECRET_KEY", "Fixs437#W1"),
    # User ID
    "user_id": os.getenv("XTS_USER_ID", "X51039H"),
    # API URLs (Broker provided)
    "market_data_url": "http://xts.achintya.net.in:3000/apimarketdata",
    "trading_url": "http://xts.achintya.net.in:3000/interactive",
    "source": "WEBAPI",
}

# Exchange Segments
EXCHANGE_SEGMENTS = {
    "NSECM": 1,
    "NSEFO": 2,
    "NSECD": 3,
    "BSECM": 11,
    "BSEFO": 12,
    "BSECD": 13,
    "MCXFO": 51,
    "NCDEX": 52,
}

# Instrument Types
INSTRUMENT_TYPES = {
    "FUTURES": 1,
    "OPTIONS": 2,
    "EQUITY": 8,
}

# Refresh Settings
WEBSOCKET_REFRESH_INTERVAL = 5  # seconds
AUTO_REFRESH_ENABLED = True

# MTM Scenario Percentages
MTM_SCENARIO_PERCENTAGES = [
    -0.10,
    -0.08,
    -0.07,
    -0.05,
    -0.025,
    0,
    0.025,
    0.05,
    0.07,
    0.08,
    0.10,
]

# Alert Thresholds
DEFAULT_ALERT_THRESHOLDS = {
    "price_drop_2_5_percent": -2.5,
    "price_drop_5_percent": -5.0,
    "price_drop_10_percent": -10.0,
    "price_rise_2_5_percent": 2.5,
    "price_rise_5_percent": 5.0,
    "price_rise_10_percent": 10.0,
}
