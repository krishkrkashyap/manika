"""
Money Class Dashboard - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.api import routes, websocket
from app.core import config


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Real-time Trading Dashboard with XTS API Integration",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(routes.router, prefix="/api")
# app.include_router(websocket.router, prefix="/ws")


# Dashboard UI
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page."""
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "demo_mode": config.DEMO_MODE,
    }


if __name__ == "__main__":
    import uvicorn
    import sys

    # Check if running via thread mode
    if len(sys.argv) > 1 and sys.argv[1] == "--thread":
        import threading
        import time

        def run():
            uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        time.sleep(2)
        print(f"Server running on http://127.0.0.1:8000")
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
