# Manika - Live Trading Dashboard

A production-grade dashboard for monitoring open positions with real-time MTM calculations, price alerts, and margin tracking. Built with Streamlit.

## Features

- **Live Position Monitoring**: Real-time display of all open positions
- **MTM Calculator**: Intraday & Expiry MTM with scenario analysis (-10% to +10%)
- **Price Alerts**: Monitor watchlist and get alerts when targets are crossed
- **Margin Calculator**: Calculate margin requirements for positions
- **Watchlist**: Track symbols with custom price targets
- **P&L Charts**: Visual breakdown of profits/losses by position

## Demo Mode

The dashboard currently runs in **Demo Mode** with simulated data based on your Manika Sheet-XTS (18.03.26). To switch to live trading:

1. Get XTS API credentials (appKey, secretKey)
2. Update `config/settings.py` with your credentials
3. Set `DEMO_MODE = False`

## Project Structure

```
manika/
├── config/
│   └── settings.py          # App configuration
├── src/
│   ├── api/
│   │   ├── xts_client.py    # XTS API wrapper
│   │   └── websocket_manager.py  # Real-time streaming
│   ├── data/
│   │   ├── demo_data.py     # Demo positions data
│   │   ├── position_manager.py  # Position management
│   │   ├── market_data.py   # Market data fetching
│   │   └── watchlist_manager.py # Watchlist management
│   ├── analytics/
│   │   ├── mtm_calculator.py   # MTM calculations
│   │   ├── margin_calc.py   # Margin calculator
│   │   └── alerts.py        # Alert system
│   └── dashboard/
│       └── app.py           # Streamlit dashboard
├── data/                    # Data storage
├── requirements.txt
└── README.md
```

## Installation

```bash
cd D:/DATA SCIENCE FUNDATMENTALS/manika
pip install -r requirements.txt
```

## Running the Dashboard

```bash
streamlit run src/dashboard/app.py
```

Or use the run script:

```bash
python run.py
```

## Dashboard Tabs

1. **Dashboard**: Overview with positions and quick stats
2. **Positions**: Detailed position table with MTM
3. **MTM Scenarios**: Scenario analysis table (-10% to +10%)
4. **Watchlist**: Price monitoring with alerts
5. **Margin**: Margin requirements calculator
6. **Settings**: Configuration and refresh settings

## Configuration

Edit `config/settings.py` to customize:
- `DEMO_MODE`: Toggle demo/live mode
- `REFRESH_INTERVAL_SECONDS`: Auto-refresh rate (default: 1 second)
- XTS API credentials

## Requirements

- Python 3.8+
- streamlit
- pandas
- numpy
- requests
- plotly
- websocket-client
- python-dotenv

## Author

Krish Kumar

## License

Proprietary - For personal use only
