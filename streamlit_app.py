"""
Streamlit Cloud Entry Point
============================
This file is the main entry point for Streamlit Cloud deployment.
It simply imports and runs the dashboard from src/dashboard/app.py.

Set this as the "Main file path" in Streamlit Cloud:
    streamlit_app.py
"""
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import and run the actual app - this triggers all the Streamlit code
from src.dashboard.app import *
