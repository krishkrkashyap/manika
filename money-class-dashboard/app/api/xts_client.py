"""
XTS API Client for Market Data and Trading
Based on official XTS Python SDK: https://github.com/symphonyfintech/xts-pythonclient-api-sdk

Verification: Login uses JSON body (json=), matching official SDK format exactly
"""

import json
import requests
from typing import Dict, List, Optional
from app.core import config


class XTSClient:
    """XTS API Client for Market Data and Trading APIs."""

    # Exchange segment constants (from SDK)
    EXCHANGE_NSECM = 1
    EXCHANGE_NSEFO = 2
    EXCHANGE_NSECD = 3
    EXCHANGE_BSECM = 11
    EXCHANGE_BSEFO = 12
    EXCHANGE_MCXFO = 51

    # Message codes (from SDK)
    MSG_TOUCHLINE = 1501
    MSG_MARKET_DEPTH = 1502
    MSG_CANDLE = 1505
    MSG_OPEN_INTEREST = 1510

    def __init__(self):
        self.trading_app_key = config.XTS_CONFIG.get("trading_app_key", "")
        self.trading_secret_key = config.XTS_CONFIG.get("trading_secret_key", "")
        self.market_data_app_key = config.XTS_CONFIG.get("market_data_app_key", "")
        self.market_data_secret_key = config.XTS_CONFIG.get(
            "market_data_secret_key", ""
        )
        self.source = config.XTS_CONFIG.get("source", "WEBAPI")

        self.market_data_url = config.XTS_CONFIG.get("market_data_url")
        self.trading_url = config.XTS_CONFIG.get("trading_url")

        self.market_data_token: Optional[str] = None
        self.trading_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.is_investor_client: bool = True

        self.is_connected = False

    # ═══════════════════════════════════════════════════════════
    # LOGIN
    # ═══════════════════════════════════════════════════════════

    def login_market_data(self) -> Dict:
        """Login to Market Data API.

        Official SDK format: JSON body POST to /auth/login
        """
        if config.DEMO_MODE:
            self.market_data_token = "demo_token"
            return {"success": True, "token": "demo_token", "message": "Demo mode"}

        if not self.market_data_app_key or not self.market_data_secret_key:
            return {"success": False, "error": "Missing credentials"}

        try:
            # SDK uses json= (JSON body), NOT data= (form-encoded)
            response = requests.post(
                f"{self.market_data_url}/auth/login",
                json={
                    "appKey": self.market_data_app_key,
                    "secretKey": self.market_data_secret_key,
                    "source": self.source,
                },
                verify=False,
            )
            data = response.json()

            if isinstance(data, list):
                data = data[0] if data else {}

            if data.get("type") == "success":
                self.market_data_token = data["result"]["token"]
                self.user_id = data["result"].get("userID", "")
                return {
                    "success": True,
                    "token": self.market_data_token,
                    "userID": self.user_id,
                }
            return {
                "success": False,
                "error": data.get("description", "Login failed"),
                "code": data.get("code", ""),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def login_trading(self) -> Dict:
        """Login to Trading (Interactive) API.

        Official SDK format: JSON body POST to /user/session
        """
        if config.DEMO_MODE:
            self.trading_token = "demo_token"
            self.is_connected = True
            return {"success": True, "token": "demo_token", "message": "Demo mode"}

        if not self.trading_app_key or not self.trading_secret_key:
            return {"success": False, "error": "Missing credentials"}

        try:
            # SDK uses json= (JSON body), NOT data= (form-encoded)
            response = requests.post(
                f"{self.trading_url}/user/session",
                json={
                    "appKey": self.trading_app_key,
                    "secretKey": self.trading_secret_key,
                    "source": self.source,
                },
                verify=False,
            )
            data = response.json()

            if data.get("type") == "success":
                self.trading_token = data["result"]["token"]
                self.user_id = data["result"].get("userID", "")
                self.is_investor_client = data["result"].get("isInvestorClient", True)
                self.is_connected = True
                return {
                    "success": True,
                    "token": self.trading_token,
                    "userID": self.user_id,
                }
            return {
                "success": False,
                "error": data.get("description", "Login failed"),
                "code": data.get("code", ""),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def login(self) -> Dict:
        """Login to both APIs."""
        md_result = self.login_market_data()
        if not md_result.get("success"):
            return md_result

        tr_result = self.login_trading()
        if not tr_result.get("success"):
            return tr_result

        return {
            "success": True,
            "market_data_token": self.market_data_token,
            "trading_token": self.trading_token,
            "message": "Both APIs connected",
        }

    def logout(self) -> Dict:
        """Logout from both APIs."""
        results = {}

        if self.market_data_token:
            try:
                r = requests.delete(
                    f"{self.market_data_url}/auth/logout",
                    headers={"Authorization": self.market_data_token},
                    verify=False,
                )
                results["market_data"] = r.json()
                self.market_data_token = None
            except Exception as e:
                results["market_data"] = {"error": str(e)}

        if self.trading_token:
            try:
                r = requests.delete(
                    f"{self.trading_url}/user/session",
                    headers={"Authorization": self.trading_token},
                    verify=False,
                )
                results["trading"] = r.json()
                self.trading_token = None
            except Exception as e:
                results["trading"] = {"error": str(e)}

        self.is_connected = False
        return results

    # ═══════════════════════════════════════════════════════════
    # POSITIONS
    # ═══════════════════════════════════════════════════════════

    def get_positions(self, day_or_net: str = "DayWise") -> Dict:
        """Get positions from Trading API."""
        if config.DEMO_MODE:
            return self._get_demo_positions()

        if not self.trading_token:
            return {"success": False, "error": "Not logged in"}

        try:
            params = {"dayOrNet": day_or_net}
            if not self.is_investor_client:
                params["clientID"] = self.user_id

            response = requests.get(
                f"{self.trading_url}/portfolio/positions",
                headers={
                    "Authorization": self.trading_token,
                    "Content-Type": "application/json",
                },
                params=params,
                verify=False,
            )
            data = response.json()

            if data.get("type") == "success":
                positions = data.get("result", {}).get("listPositions", [])
                return {
                    "success": True,
                    "positions": self._transform_positions(positions),
                }
            return {
                "success": False,
                "error": data.get("description", "Failed to get positions"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _transform_positions(self, raw_positions: List[Dict]) -> List[Dict]:
        """Transform XTS API positions to our dashboard format.

        XTS returns:
        - buyAvgPrice, sellAvgPrice
        - buyQty, sellQty, netQty
        - unrealisedMTM, realisedMTM
        - exchangeSegment, exchangeInstrumentID
        """
        transformed = []

        for pos in raw_positions:
            symbol = pos.get("tradingSymbol", pos.get("symbolName", ""))
            stock = symbol[:4] if symbol else ""

            # Determine type
            if "FUT" in symbol.upper():
                pos_type = "FUT"
            elif "PE" in symbol.upper():
                pos_type = "PE"
            elif "CE" in symbol.upper():
                pos_type = "CE"
            else:
                pos_type = "EQ"

            buy_avg = float(pos.get("buyAvgPrice", 0))
            sell_avg = float(pos.get("sellAvgPrice", 0))
            buy_qty = int(pos.get("buyQty", 0))
            sell_qty = int(pos.get("sellQty", 0))
            net_qty = int(pos.get("netQty", 0))

            # MTM
            unrealised = float(pos.get("unrealisedMTM", 0))
            realised = float(pos.get("realisedMTM", 0))
            total_mtm = unrealised + realised

            # LTP from position data
            ltp = float(pos.get("ltp", pos.get("closePrice", 0)))

            transformed.append(
                {
                    "stock": stock,
                    "symbol": symbol,
                    "type": pos_type,
                    "net_qty": net_qty,
                    "buy_qty": buy_qty,
                    "sell_qty": sell_qty,
                    "buy_avg": buy_avg,
                    "sell_avg": sell_avg,
                    "ltp": ltp,
                    "m2m": total_mtm,
                    "unrealised_mtm": unrealised,
                    "realised_mtm": realised,
                    "exchange_segment": pos.get("exchangeSegment", ""),
                    "product_type": pos.get("productType", ""),
                }
            )

        return transformed

    # ═══════════════════════════════════════════════════════════
    # TRADES
    # ═══════════════════════════════════════════════════════════

    def get_trades(self) -> Dict:
        """Get trade history from Trading API."""
        if config.DEMO_MODE:
            return self._get_demo_trades()

        if not self.trading_token:
            return {"success": False, "error": "Not logged in"}

        try:
            params = {}
            if not self.is_investor_client:
                params["clientID"] = self.user_id

            response = requests.get(
                f"{self.trading_url}/orders/trades",
                headers={
                    "Authorization": self.trading_token,
                    "Content-Type": "application/json",
                },
                params=params,
                verify=False,
            )
            data = response.json()

            if data.get("type") == "success":
                trades = data.get("result", [])
                return {"success": True, "trades": self._transform_trades(trades)}
            return {
                "success": False,
                "error": data.get("description", "Failed to get trades"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _transform_trades(self, raw_trades: List[Dict]) -> List[Dict]:
        """Transform XTS API trades to our dashboard format."""
        transformed = []

        for trade in raw_trades:
            transformed.append(
                {
                    "time": trade.get(
                        "exchangeTradeTime", trade.get("orderDateTime", "")
                    ),
                    "symbol": trade.get("tradingSymbol", ""),
                    "type": trade.get("orderSide", ""),
                    "qty": int(trade.get("tradeQuantity", 0)),
                    "price": float(trade.get("tradePrice", 0)),
                    "value": float(trade.get("tradeValue", 0)),
                    "order_id": trade.get("appOrderID", ""),
                    "exchange_order_id": trade.get("exchangeOrderID", ""),
                }
            )

        return transformed

    # ═══════════════════════════════════════════════════════════
    # QUOTES & MARKET DATA
    # ═══════════════════════════════════════════════════════════

    def get_quote(self, instruments: List[Dict]) -> Dict:
        """Get quote for instruments from Market Data API.

        instruments: [{"exchangeSegment": 2, "exchangeInstrumentID": 52687}]
        xtsMessageCode: 1501 (touchline), 1502 (market depth)
        """
        if config.DEMO_MODE:
            return self._get_demo_quotes(instruments)

        if not self.market_data_token:
            return {"success": False, "error": "Not logged in"}

        try:
            response = requests.post(
                f"{self.market_data_url}/instruments/quotes",
                json={
                    "instruments": instruments,
                    "xtsMessageCode": self.MSG_TOUCHLINE,
                    "publishFormat": "JSON",
                },
                headers={
                    "Authorization": self.market_data_token,
                    "Content-Type": "application/json",
                },
                verify=False,
            )
            data = response.json()

            if isinstance(data, list):
                data = data[0] if data else {}

            if data.get("type") == "success":
                return {"success": True, "quotes": data.get("result", {})}
            return {
                "success": False,
                "error": data.get("description", "Failed to get quotes"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def subscribe_instruments(
        self, instruments: List[Dict], message_code: int = 1501
    ) -> Dict:
        """Subscribe to real-time instrument data."""
        if not self.market_data_token:
            return {"success": False, "error": "Not logged in"}

        try:
            response = requests.post(
                f"{self.market_data_url}/instruments/subscription",
                json={
                    "instruments": instruments,
                    "xtsMessageCode": message_code,
                },
                headers={
                    "Authorization": self.market_data_token,
                    "Content-Type": "application/json",
                },
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def unsubscribe_instruments(
        self, instruments: List[Dict], message_code: int = 1501
    ) -> Dict:
        """Unsubscribe from instrument data."""
        if not self.market_data_token:
            return {"success": False, "error": "Not logged in"}

        try:
            response = requests.put(
                f"{self.market_data_url}/instruments/subscription",
                json={
                    "instruments": instruments,
                    "xtsMessageCode": message_code,
                },
                headers={
                    "Authorization": self.market_data_token,
                    "Content-Type": "application/json",
                },
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_ohlc(
        self,
        exchange_segment: int,
        instrument_id: int,
        start_time: str,
        end_time: str,
        compression: str,
    ) -> Dict:
        """Get OHLC candle data."""
        if not self.market_data_token:
            return {"success": False, "error": "Not logged in"}

        try:
            response = requests.get(
                f"{self.market_data_url}/instruments/ohlc",
                params={
                    "exchangeSegment": exchange_segment,
                    "exchangeInstrumentID": instrument_id,
                    "startTime": start_time,
                    "endTime": end_time,
                    "compressionValue": compression,
                },
                headers={
                    "Authorization": self.market_data_token,
                    "Content-Type": "application/json",
                },
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_instruments(self, instruments: List[Dict]) -> Dict:
        """Search instruments by ID."""
        if not self.market_data_token:
            return {"success": False, "error": "Not logged in"}

        try:
            response = requests.post(
                f"{self.market_data_url}/search/instrumentsbyid",
                json={
                    "source": self.source,
                    "instruments": instruments,
                },
                headers={
                    "Authorization": self.market_data_token,
                    "Content-Type": "application/json",
                },
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_by_name(self, search_string: str) -> Dict:
        """Search instruments by name."""
        if not self.market_data_token:
            return {"success": False, "error": "Not logged in"}

        try:
            response = requests.get(
                f"{self.market_data_url}/search/instruments",
                params={"searchString": search_string},
                headers={
                    "Authorization": self.market_data_token,
                    "Content-Type": "application/json",
                },
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════
    # ORDERS
    # ═══════════════════════════════════════════════════════════

    def get_orders(self) -> Dict:
        """Get order book."""
        if not self.trading_token:
            return {"success": False, "error": "Not logged in"}

        try:
            params = {}
            if not self.is_investor_client:
                params["clientID"] = self.user_id

            response = requests.get(
                f"{self.trading_url}/orders",
                headers={
                    "Authorization": self.trading_token,
                    "Content-Type": "application/json",
                },
                params=params,
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def place_order(
        self,
        exchange_segment: int,
        instrument_id: int,
        product_type: str,
        order_type: str,
        order_side: str,
        quantity: int,
        price: float = 0,
        stop_price: float = 0,
        order_unique_id: str = "",
    ) -> Dict:
        """Place an order."""
        if not self.trading_token:
            return {"success": False, "error": "Not logged in"}

        try:
            payload = {
                "exchangeSegment": exchange_segment,
                "exchangeInstrumentID": instrument_id,
                "productType": product_type,
                "orderType": order_type,
                "orderSide": order_side,
                "timeInForce": "DAY",
                "disclosedQuantity": 0,
                "orderQuantity": quantity,
                "limitPrice": price,
                "stopPrice": stop_price,
                "orderUniqueIdentifier": order_unique_id or f"ORDER_{instrument_id}",
            }

            if not self.is_investor_client:
                payload["clientID"] = self.user_id

            response = requests.post(
                f"{self.trading_url}/orders",
                json=payload,
                headers={
                    "Authorization": self.trading_token,
                    "Content-Type": "application/json",
                },
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cancel_order(self, app_order_id: int) -> Dict:
        """Cancel an order."""
        if not self.trading_token:
            return {"success": False, "error": "Not logged in"}

        try:
            params = {"appOrderID": app_order_id}
            if not self.is_investor_client:
                params["clientID"] = self.user_id

            response = requests.delete(
                f"{self.trading_url}/orders",
                headers={
                    "Authorization": self.trading_token,
                    "Content-Type": "application/json",
                },
                params=params,
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_holdings(self) -> Dict:
        """Get portfolio holdings."""
        if not self.trading_token:
            return {"success": False, "error": "Not logged in"}

        try:
            params = {}
            if not self.is_investor_client:
                params["clientID"] = self.user_id

            response = requests.get(
                f"{self.trading_url}/portfolio/holdings",
                headers={
                    "Authorization": self.trading_token,
                    "Content-Type": "application/json",
                },
                params=params,
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_profile(self) -> Dict:
        """Get user profile."""
        if not self.trading_token:
            return {"success": False, "error": "Not logged in"}

        try:
            params = {}
            if not self.is_investor_client:
                params["clientID"] = self.user_id

            response = requests.get(
                f"{self.trading_url}/user/profile",
                headers={
                    "Authorization": self.trading_token,
                    "Content-Type": "application/json",
                },
                params=params,
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_balance(self) -> Dict:
        """Get account balance/limits."""
        if not self.trading_token:
            return {"success": False, "error": "Not logged in"}

        try:
            params = {}
            if not self.is_investor_client:
                params["clientID"] = self.user_id

            response = requests.get(
                f"{self.trading_url}/user/balance",
                headers={
                    "Authorization": self.trading_token,
                    "Content-Type": "application/json",
                },
                params=params,
                verify=False,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════
    # DEMO DATA
    # ═══════════════════════════════════════════════════════════

    def _get_demo_positions(self) -> Dict:
        """Return demo positions."""
        return {
            "success": True,
            "demo": True,
            "positions": [
                {
                    "stock": "BEL",
                    "type": "FUT",
                    "symbol": "BEL26MARFUT",
                    "net_qty": 228000,
                    "buy_qty": 228000,
                    "sell_qty": 0,
                    "buy_avg": 426.90,
                    "sell_avg": 0,
                    "ltp": 410.40,
                    "yesterday_close": 412.60,
                    "open": 408.00,
                    "m2m": -3763200,
                },
                {
                    "stock": "BEL",
                    "type": "PE",
                    "symbol": "BEL26MAR440PE",
                    "net_qty": -114000,
                    "buy_qty": 0,
                    "sell_qty": 114000,
                    "buy_avg": 0,
                    "sell_avg": 16.65,
                    "ltp": 7.45,
                    "yesterday_close": 8.20,
                    "open": 7.80,
                    "m2m": -1049400,
                },
                {
                    "stock": "BHEL",
                    "type": "FUT",
                    "symbol": "BHEL26MARFUT",
                    "net_qty": 378000,
                    "buy_qty": 378000,
                    "sell_qty": 0,
                    "buy_avg": 261.85,
                    "sell_avg": 0,
                    "ltp": 253.40,
                    "yesterday_close": 255.80,
                    "open": 250.00,
                    "m2m": -3194100,
                },
                {
                    "stock": "BHEL",
                    "type": "PE",
                    "symbol": "BHEL26MAR262.5PE",
                    "net_qty": -189000,
                    "buy_qty": 0,
                    "sell_qty": 189000,
                    "buy_avg": 0,
                    "sell_avg": 6.40,
                    "ltp": 8.94,
                    "yesterday_close": 7.50,
                    "open": 8.20,
                    "m2m": 480600,
                },
                {
                    "stock": "NTPC",
                    "type": "FUT",
                    "symbol": "NTPC26MARFUT",
                    "net_qty": 256500,
                    "buy_qty": 256500,
                    "sell_qty": 0,
                    "buy_avg": 380.50,
                    "sell_avg": 0,
                    "ltp": 373.85,
                    "yesterday_close": 376.20,
                    "open": 370.00,
                    "m2m": -1704750,
                },
                {
                    "stock": "PNB",
                    "type": "FUT",
                    "symbol": "PNB26MARFUT",
                    "net_qty": 752000,
                    "buy_qty": 752000,
                    "sell_qty": 0,
                    "buy_avg": 111.56,
                    "sell_avg": 0,
                    "ltp": 106.99,
                    "yesterday_close": 108.50,
                    "open": 105.00,
                    "m2m": -3436544,
                },
                {
                    "stock": "SAIL",
                    "type": "FUT",
                    "symbol": "SAIL26MARFUT",
                    "net_qty": 465300,
                    "buy_qty": 465300,
                    "sell_qty": 0,
                    "buy_avg": 155.47,
                    "sell_avg": 0,
                    "ltp": 148.38,
                    "yesterday_close": 150.25,
                    "open": 145.00,
                    "m2m": -3297741,
                },
            ],
        }

    def _get_demo_trades(self) -> Dict:
        """Return demo trade data."""
        return {
            "success": True,
            "demo": True,
            "trades": [
                {
                    "time": "09:15:30",
                    "symbol": "BEL26MARFUT",
                    "type": "BUY",
                    "qty": 76000,
                    "price": 426.90,
                    "value": 32444400,
                },
                {
                    "time": "09:30:15",
                    "symbol": "BHEL26MARFUT",
                    "type": "BUY",
                    "qty": 126000,
                    "price": 261.85,
                    "value": 32993100,
                },
                {
                    "time": "10:00:00",
                    "symbol": "NTPC26MARFUT",
                    "type": "BUY",
                    "qty": 85500,
                    "price": 380.50,
                    "value": 32532750,
                },
                {
                    "time": "10:15:45",
                    "symbol": "PNB26MARFUT",
                    "type": "BUY",
                    "qty": 250666,
                    "price": 111.56,
                    "value": 27964306,
                },
                {
                    "time": "10:30:00",
                    "symbol": "SAIL26MARFUT",
                    "type": "BUY",
                    "qty": 155100,
                    "price": 155.47,
                    "value": 24113397,
                },
                {
                    "time": "11:00:00",
                    "symbol": "BEL26MAR440PE",
                    "type": "SELL",
                    "qty": 57000,
                    "price": 16.65,
                    "value": 949050,
                },
                {
                    "time": "11:15:00",
                    "symbol": "BHEL26MAR262.5PE",
                    "type": "SELL",
                    "qty": 94500,
                    "price": 6.40,
                    "value": 604800,
                },
                {
                    "time": "11:30:00",
                    "symbol": "NTPC26MAR387.5PE",
                    "type": "SELL",
                    "qty": 42500,
                    "price": 9.00,
                    "value": 382500,
                },
            ],
        }

    def _get_demo_quotes(self, instruments: List[Dict]) -> Dict:
        """Return demo quotes."""
        import random

        quotes = {}
        for inst in instruments:
            symbol = inst.get("symbol", "")
            base_prices = {
                "BEL26MARFUT": 410.40,
                "BEL26MAR440PE": 7.45,
                "BEL26MAR460CE": 0.50,
                "BHEL26MARFUT": 253.40,
                "BHEL26MAR262.5PE": 8.94,
                "BHEL26MAR277.5CE": 0.45,
                "NTPC26MARFUT": 373.85,
                "NTPC26MAR387.5PE": 11.20,
                "NTPC26MAR410CE": 0.15,
                "PNB26MARFUT": 106.99,
                "PNB26MAR132PE": 18.50,
                "PNB26MAR139CE": 0.03,
                "SAIL26MARFUT": 148.38,
                "SAIL26MAR167PE": 12.56,
                "SAIL26MAR176CE": 0.48,
            }
            base = base_prices.get(symbol, 100.0)
            variation = random.uniform(-0.01, 0.01)
            ltp = round(base * (1 + variation), 2)
            quotes[symbol] = {"ltp": ltp, "close": base, "change": round(ltp - base, 2)}
        return {"success": True, "quotes": quotes}


_xts_client: Optional[XTSClient] = None


def get_xts_client() -> XTSClient:
    """Get singleton XTS client."""
    global _xts_client
    if _xts_client is None:
        _xts_client = XTSClient()
    return _xts_client
