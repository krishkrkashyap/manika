"""
Manika Dashboard Runner
Run this script to start the Streamlit dashboard.
"""
import subprocess
import sys
import os

def main():
    """Run the Streamlit dashboard."""
    app_path = os.path.join(os.path.dirname(__file__), "src", "dashboard", "app.py")
    
    print("=" * 50)
    print("Manika - Live Trading Dashboard")
    print("=" * 50)
    print(f"Starting dashboard from: {app_path}")
    print()
    print("Open your browser at: http://localhost:8501")
    print("=" * 50)
    
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])

if __name__ == "__main__":
    main()
