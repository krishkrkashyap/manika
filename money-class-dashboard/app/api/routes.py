"""
API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.api import xts_client as xts
from app.analytics import mtm_calculator, margin_calc
from app.analytics.alerts import get_alert_system
from app.core import config

router = APIRouter()


@router.get("/status")
async def get_status():
    """Get dashboard status."""
    return {
        "demo_mode": config.DEMO_MODE,
        "connected": True,
    }


@router.get("/positions")
async def get_positions(filter: str = "all"):
    """Get positions with optional filter: all, futures, pe, ce"""
    client = xts.get_xts_client()
    result = client.get_positions()

    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error", "Failed to get positions"),
        }

    positions = result.get(
        "positions", result.get("result", {}).get("listPositions", [])
    )

    # Apply filters
    if filter == "futures":
        positions = [p for p in positions if p.get("type", "").upper() == "FUT"]
    elif filter == "pe":
        positions = [p for p in positions if "PE" in p.get("symbol", "").upper()]
    elif filter == "ce":
        positions = [p for p in positions if "CE" in p.get("symbol", "").upper()]

    return {"success": True, "positions": positions}


@router.get("/quotes")
async def get_quotes(symbols: List[str] = None):
    """Get quotes for symbols."""
    client = xts.get_xts_client()

    if not symbols:
        # Default symbols
        symbols = [
            "BEL26MARFUT",
            "BEL26MAR440PE",
            "BHEL26MARFUT",
            "BHEL26MAR262.5PE",
            "NTPC26MARFUT",
            "PNB26MARFUT",
            "SAIL26MARFUT",
        ]

    instruments = [{"exchangeSegment": 2, "exchangeInstrumentID": s} for s in symbols]
    result = client.get_quote(instruments)

    return result


@router.get("/mtm")
async def get_mtm():
    """Get MTM calculations."""
    client = xts.get_xts_client()
    positions_result = client.get_positions()

    if not positions_result.get("success"):
        return {"success": False, "error": "Failed to get positions"}

    positions = positions_result.get("positions", [])
    quotes_result = client.get_quote([])
    quotes = quotes_result.get("quotes", {})

    mtm_data = mtm_calculator.calculate_all_mtm(positions, quotes)
    return {"success": True, "mtm": mtm_data}


@router.get("/margin")
async def get_margin():
    """Get margin calculations."""
    client = xts.get_xts_client()
    positions_result = client.get_positions()

    if not positions_result.get("success"):
        return {"success": False, "error": "Failed to get positions"}

    positions = positions_result.get("positions", [])
    quotes_result = client.get_quote([])
    quotes = quotes_result.get("quotes", {})

    margin_data = margin_calc.calculate_total_margin(positions, quotes)
    return {"success": True, "margin": margin_data}


@router.get("/scenarios")
async def get_scenarios():
    """Get MTM scenario analysis with per-stock breakdown."""
    client = xts.get_xts_client()
    positions_result = client.get_positions()

    if not positions_result.get("success"):
        return {"success": False, "error": "Failed to get positions"}

    positions = positions_result.get("positions", [])
    quotes_result = client.get_quote([])
    quotes = quotes_result.get("quotes", {})

    # Transform positions to dict keyed by stock for scenario analysis
    positions_dict = transform_positions_for_scenarios(positions)

    # Get total scenarios
    total_scenarios = mtm_calculator.generate_scenario_table(positions, quotes)

    # Get per-stock scenarios
    stock_scenarios = mtm_calculator.generate_all_stock_scenarios(
        positions_dict, quotes
    )

    return {
        "success": True,
        "scenarios": total_scenarios,
        "stock_scenarios": stock_scenarios,
        "stocks": list(positions_dict.keys()),
    }


def transform_positions_for_scenarios(positions: List[Dict]) -> Dict:
    """Transform flat positions list to dict grouped by stock"""
    result = {}
    for pos in positions:
        stock = pos.get("stock", "")
        if stock not in result:
            result[stock] = {"futures": {}, "options": []}

        symbol = pos.get("symbol", "")
        if "FUT" in symbol.upper():
            result[stock]["futures"] = pos
        else:
            result[stock]["options"].append(pos)

    return result


@router.post("/login")
async def login():
    """Login to XTS APIs."""
    client = xts.get_xts_client()
    result = client.login()
    return result


@router.post("/logout")
async def logout():
    """Logout from XTS APIs."""
    return {"success": True}


# ==================== Task 4: Trade Info Tab ====================


@router.get("/trades")
async def get_trades():
    """Get trade history"""
    client = xts.get_xts_client()
    result = client.get_trades()
    return result


# ==================== Task 5: Order Margin Calculator ====================


@router.post("/order_margin")
async def calculate_order_margin(request: dict):
    """Calculate margin for a new order"""
    symbol = request.get("symbol", "")
    quantity = request.get("quantity", 0)
    price = request.get("price", 0)
    product_type = request.get("product_type", "MIS")

    calc = margin_calc.MarginCalculator()
    result = calc.calculate_order_margin(symbol, quantity, price, product_type)
    return {"success": True, "margin": result}


# ==================== Task 6: Stock-wise Drilldown ====================


@router.get("/mtm/{stock}")
async def get_stock_mtm(stock: str):
    """Get detailed MTM for specific stock"""
    client = xts.get_xts_client()
    positions_result = client.get_positions()

    if not positions_result.get("success"):
        return {"success": False, "error": "Failed to get positions"}

    positions = positions_result.get("positions", [])
    stock_positions = [
        p for p in positions if p.get("stock", "").upper() == stock.upper()
    ]

    if not stock_positions:
        return {"success": False, "error": f"No positions found for {stock}"}

    # Calculate all MTM types for this stock
    mtm_data = mtm_calculator.calculate_all_mtm(stock_positions, {})

    return {"success": True, "stock": stock, "mtm": mtm_data}


# ==================== Task 7: Option-wise Drilldown ====================


@router.get("/options/{stock}")
async def get_stock_options(stock: str):
    """Get options breakdown for specific stock (PE + CE combined)"""
    client = xts.get_xts_client()
    positions_result = client.get_positions()

    if not positions_result.get("success"):
        return {"success": False, "error": "Failed to get positions"}

    positions = positions_result.get("positions", [])
    stock_positions = [
        p for p in positions if p.get("stock", "").upper() == stock.upper()
    ]

    # Separate PE and CE
    pe_positions = [p for p in stock_positions if "PE" in p.get("symbol", "").upper()]
    ce_positions = [p for p in stock_positions if "CE" in p.get("symbol", "").upper()]

    # Calculate MTM for each
    pe_mtm = mtm_calculator.calculate_all_mtm(pe_positions, {})
    ce_mtm = mtm_calculator.calculate_all_mtm(ce_positions, {})

    return {
        "success": True,
        "stock": stock,
        "pe": pe_mtm,
        "ce": ce_mtm,
        "total_exp": round(pe_mtm.get("exp_total", 0) + ce_mtm.get("exp_total", 0), 2),
    }


# ==================== Task 8: Alert System ====================


@router.get("/alerts")
async def get_alerts():
    """Get all alerts"""
    alert_system = get_alert_system()
    return {"success": True, "alerts": alert_system.get_all_alerts()}


@router.post("/alerts")
async def add_alert(request: dict):
    """Add a new alert"""
    stock = request.get("stock", "")
    alert_type = request.get("type", "price_drop")
    threshold = request.get("threshold", 5.0)

    alert_system = get_alert_system()
    alert = alert_system.add_alert(stock, alert_type, threshold)

    # Check if triggered immediately
    client = xts.get_xts_client()
    positions_result = client.get_positions()
    if positions_result.get("success"):
        positions = positions_result.get("positions", [])
        triggered = alert_system.check_alerts(positions)
        return {"success": True, "alert": alert, "triggered": triggered}

    return {"success": True, "alert": alert}


@router.delete("/alerts/{alert_id}")
async def remove_alert(alert_id: int):
    """Remove an alert"""
    alert_system = get_alert_system()
    alert_system.remove_alert(alert_id)
    return {"success": True}


@router.get("/alerts/check")
async def check_alerts():
    """Check all alerts against current positions"""
    alert_system = get_alert_system()
    client = xts.get_xts_client()
    positions_result = client.get_positions()

    if positions_result.get("success"):
        positions = positions_result.get("positions", [])
        triggered = alert_system.check_alerts(positions)
        return {"success": True, "triggered": triggered}

    return {"success": False, "error": "Failed to get positions"}
