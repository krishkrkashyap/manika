"""
Streamlit Cloud Entry Point
============================
Thin shim that runs src/dashboard/app.py as the Streamlit app.
"""
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Set __file__ for app.py so its Path(__file__) based sys.path logic works
_app_file = os.path.join(_ROOT, "src", "dashboard", "app.py")

# Compile and exec in our own globals so Streamlit sees everything
# as belonging to the entry-point module
with open(_app_file, "r", encoding="utf-8") as _f:
    _code = compile(_f.read(), _app_file, "exec")
    exec(_code, {**globals(), "__file__": _app_file})
