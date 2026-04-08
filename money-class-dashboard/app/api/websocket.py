"""
WebSocket endpoint for real-time updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import json
from app.api import xts_client as xts
from app.analytics import mtm_calculator, margin_calc
from app.core import config

router = APIRouter()

# Connected WebSocket clients
connected_clients: Set[WebSocket] = set()


async def broadcast_update(data: dict):
    """Broadcast data to all connected clients."""
    for client in connected_clients:
        try:
            await client.send_json(data)
        except:
            pass


async def data_update_loop():
    """Background task to fetch and broadcast data."""
    while True:
        try:
            client = xts.get_xts_client()

            # Get positions
            positions_result = client.get_positions()
            positions = []
            if positions_result.get("success"):
                positions = positions_result.get("positions", [])

            # Get quotes
            symbols = [
                "BEL26MARFUT",
                "BEL26MAR440PE",
                "BHEL26MARFUT",
                "BHEL26MAR262.5PE",
                "NTPC26MARFUT",
                "PNB26MARFUT",
                "SAIL26MARFUT",
            ]
            instruments = [
                {"exchangeSegment": 2, "exchangeInstrumentID": s} for s in symbols
            ]
            quotes_result = client.get_quote(instruments)
            quotes = {}
            if quotes_result.get("success"):
                quotes = quotes_result.get("quotes", {})

            # Calculate MTM
            mtm_data = mtm_calculator.calculate_all_mtm(positions, quotes)

            # Calculate margin
            margin_data = margin_calc.calculate_total_margin(positions, quotes)

            # Broadcast
            await broadcast_update(
                {
                    "type": "update",
                    "positions": positions,
                    "quotes": quotes,
                    "mtm": mtm_data,
                    "margin": margin_data,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )

        except Exception as e:
            print(f"Data update error: {e}")

        await asyncio.sleep(config.WEBSOCKET_REFRESH_INTERVAL)


@router.websocket("/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket.accept()
    connected_clients.add(websocket)

    # Start background task if first client
    if len(connected_clients) == 1:
        asyncio.create_task(data_update_loop())

    try:
        while True:
            # Keep connection alive, handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "refresh":
                # Force immediate data refresh
                pass

    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)


async def start_websocket_manager():
    """Start websocket manager."""
    print("WebSocket manager started")


async def stop_websocket_manager():
    """Stop websocket manager."""
    connected_clients.clear()
    print("WebSocket manager stopped")
