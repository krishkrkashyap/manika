"""
Manika Trading Dashboard v2 - Run Script
Run: python run_v2.py
"""
import subprocess
import sys

def main():
    """Run the v2 Streamlit app."""
    print("Starting Manika Dashboard v2...")
    print("Open http://localhost:8501 in your browser")
    
    # Run streamlit
    result = subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "v2/app.py"],
        cwd="D:/DATA SCIENCE FUNDATMENTALS/manika"
    )
    return result.returncode

if __name__ == "__main__":
    main()
