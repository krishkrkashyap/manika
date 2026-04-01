"""
XTS API Client - Wrapper for XTS Market Data and Trading APIs.

Fixed to match the official XTS API v2 documentation:
- Trading API uses separate login flow with HostLookup → Login (secretKey + appKey + uniqueKey + accessToken)
- Market Data API uses direct login (secretKey + appKey)
- Both APIs produce their own independent tokens
- Correct endpoint paths for all operations
"""
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

from config.settings import XTS_CONFIG, DEMO_MODE, EXCHANGE_SEGMENTS


class XTSClient:
    """XTS API Client for Market Data and Trading."""
    
    def __init__(self, app_key: str = None, secret_key: str = None, user_id: str = None):
        self.app_key = app_key or XTS_CONFIG.get('app_key')
        self.secret_key = secret_key or XTS_CONFIG.get('secret_key')
        self.user_id = user_id or XTS_CONFIG.get('user_id')
        
        self.market_data_url = XTS_CONFIG.get('market_data_url')
        self.trading_url = XTS_CONFIG.get('trading_url')
        self.host_lookup_url = XTS_CONFIG.get('host_lookup_url')
        
        # Separate tokens for each API service
        self.market_data_token = None
        self.trading_token = None
        self.unique_key = None
        self.connection_string = None
        
        self.is_connected = False
    
    # ═══════════════════════════════════════════════════════
    # HOST LOOKUP (Required before Trading API login)
    # ═══════════════════════════════════════════════════════
    
    def host_lookup(self) -> Dict:
        """Perform HostLookup to obtain UniqueKey and connectionString.
        
        Must be called before trading login.
        Docs: POST https://developers.symphonyfintech.in/hostlookup
        """
        if DEMO_MODE:
            return {'success': True, 'unique_key': 'demo_key', 'connection_string': 'demo'}
        
        url = self.host_lookup_url
        payload = {
            "accesspassword": "2021HostLookUpAccess",
            "version": "interactive_1.0.2"
        }
        
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            data = response.json()
            
            if data.get('type') == 'success':
                result = data.get('result', {})
                self.unique_key = result.get('UniqueKey')
                self.connection_string = result.get('connectionString')
                return {
                    'success': True,
                    'unique_key': self.unique_key,
                    'connection_string': self.connection_string
                }
            else:
                return {'success': False, 'error': data.get('description', 'HostLookup failed')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ═══════════════════════════════════════════════════════
    # MARKET DATA API - Login/Logout
    # Docs: POST /auth/login  (appKey + secretKey)
    # ═══════════════════════════════════════════════════════
    
    def login_market_data(self) -> Dict:
        """Login to Market Data API and obtain market data token.
        
        Docs: POST {market_data_url}/auth/login
        Payload: { "secretKey": "...", "appKey": "..." }
        """
        if DEMO_MODE or not self.app_key or not self.secret_key:
            self.market_data_token = 'demo_token'
            return {
                'success': True,
                'token': 'demo_token',
                'user_id': 'DEMO_USER',
                'message': 'Demo mode active'
            }
        
        url = f"{self.market_data_url}/auth/login"
        payload = {
            "appKey": self.app_key,
            "secretKey": self.secret_key
        }
        
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            data = response.json()
            
            # Market Data API returns list or dict
            result = data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}
            
            if result.get('type') == 'success':
                self.market_data_token = result['result']['token']
                return {
                    'success': True,
                    'token': self.market_data_token,
                    'user_id': result['result'].get('userID')
                }
            else:
                return {'success': False, 'error': result.get('description', 'Market data login failed')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ═══════════════════════════════════════════════════════
    # TRADING (INTERACTIVE) API - Login/Logout
    # Docs: POST /user/session  (secretKey + appKey + uniqueKey + accessToken)
    # NOTE: Requires HostLookup first to get uniqueKey
    # ═══════════════════════════════════════════════════════
    
    def login_trading(self, access_token: str = None) -> Dict:
        """Login to Trading (Interactive) API.
        
        Docs: POST {trading_url}/user/session
        Payload: { "secretKey", "appKey", "uniqueKey", "accessToken" }
        
        Args:
            access_token: OAuth access token from the login flow
        """
        if DEMO_MODE or not self.app_key or not self.secret_key:
            self.trading_token = 'demo_token'
            self.is_connected = True
            return {
                'success': True,
                'token': 'demo_token',
                'user_id': 'DEMO_USER',
                'message': 'Demo mode active'
            }
        
        # Ensure HostLookup was done first
        if not self.unique_key:
            lookup = self.host_lookup()
            if not lookup.get('success'):
                return {'success': False, 'error': f"HostLookup failed: {lookup.get('error')}"}
        
        url = f"{self.trading_url}/user/session"
        payload = {
            "secretKey": self.secret_key,
            "appKey": self.app_key,
            "uniqueKey": self.unique_key,
            "accessToken": access_token or ""
        }
        
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            data = response.json()
            
            if data.get('type') == 'success':
                self.trading_token = data['result']['token']
                self.is_connected = True
                return {
                    'success': True,
                    'token': self.trading_token,
                    'user_id': data['result'].get('userID'),
                    'enums': data['result'].get('enums', {})
                }
            else:
                return {'success': False, 'error': data.get('description', 'Trading login failed')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def login(self, access_token: str = None) -> Dict:
        """Convenience: login to both APIs.
        
        Returns combined result.
        """
        # Market Data login
        md_result = self.login_market_data()
        if not md_result.get('success'):
            return md_result
        
        # Trading login
        tr_result = self.login_trading(access_token)
        if not tr_result.get('success'):
            return tr_result
        
        return {
            'success': True,
            'market_data_token': self.market_data_token,
            'trading_token': self.trading_token,
            'user_id': tr_result.get('user_id'),
            'message': 'Both APIs connected'
        }
    
    def logout(self) -> Dict:
        """Logout from both APIs."""
        results = {}
        
        # Logout Market Data
        if self.market_data_token and not DEMO_MODE:
            try:
                url = f"{self.market_data_url}/auth/logout"
                headers = {'Authorization': self.market_data_token}
                requests.delete(url, headers=headers)
            except Exception:
                pass
            self.market_data_token = None
        
        # Logout Trading
        if self.trading_token and not DEMO_MODE:
            try:
                url = f"{self.trading_url}/user/session"
                headers = {'Authorization': self.trading_token}
                requests.delete(url, headers=headers)
            except Exception:
                pass
            self.trading_token = None
        
        self.is_connected = False
        return {'success': True}
    
    # ═══════════════════════════════════════════════════════
    # MARKET DATA API ENDPOINTS
    # All use market_data_token
    # ═══════════════════════════════════════════════════════
    
    def get_quote(self, instruments: List[Dict], xts_message_code: int = 1501,
                  publish_format: str = "JSON") -> Dict:
        """Get quote for instruments.
        
        Docs: POST {market_data_url}/instruments/quotes
        Payload: {
            "instruments": [{"exchangeSegment": 1, "exchangeInstrumentID": 22}],
            "xtsMessageCode": 1501,
            "publishFormat": "JSON"
        }
        
        xtsMessageCode:
            1501 = Touchline (best bid/ask + LTP)
            1502 = Market Depth (order book)
            1505 = Candle Data (OHLCV)
            1510 = Open Interest
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.market_data_url}/instruments/quotes"
        headers = {
            'Authorization': self.market_data_token,
            'Content-Type': 'application/json'
        }
        payload = {
            'instruments': instruments,
            'xtsMessageCode': xts_message_code,
            'publishFormat': publish_format
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_instruments_by_id(self, instruments: List[Dict]) -> Dict:
        """Search instruments by exchange segment + instrument ID.
        
        Docs: POST {market_data_url}/search/instrumentsbyid
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.market_data_url}/search/instrumentsbyid"
        headers = {
            'Authorization': self.market_data_token,
            'Content-Type': 'application/json'
        }
        payload = {'instruments': instruments}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_instruments_by_string(self, search_string: str, exchange_segment: int = 1) -> Dict:
        """Search instruments by string (e.g. symbol name).
        
        Docs: GET {market_data_url}/search/instruments?searchString={}&source={}&exchangeSegment={}
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.market_data_url}/search/instruments"
        headers = {'Authorization': self.market_data_token}
        params = {
            'searchString': search_string,
            'source': 'WebAPI',
            'exchangeSegment': exchange_segment
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_master(self, exchange_segment_list: List[str]) -> Dict:
        """Get instrument master data (full instrument dump).
        
        Docs: POST {market_data_url}/instruments/master
        Payload: { "exchangeSegmentList": ["NSECM", "NSEFO"] }
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.market_data_url}/instruments/master"
        headers = {
            'Authorization': self.market_data_token,
            'Content-Type': 'application/json'
        }
        payload = {'exchangeSegmentList': exchange_segment_list}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_ohlc(self, exchange_segment: str, exchange_instrument_id: int,
                 start_time: str, end_time: str, compression_value: int = 60) -> Dict:
        """Get intraday OHLC candle data.
        
        Docs: GET {market_data_url}/instruments/ohlc
        Params: exchangeSegment, exchangeInstrumentID, startTime, endTime, compressionValue
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.market_data_url}/instruments/ohlc"
        headers = {'Authorization': self.market_data_token}
        params = {
            'exchangeSegment': exchange_segment,
            'exchangeInstrumentID': exchange_instrument_id,
            'startTime': start_time,
            'endTime': end_time,
            'compressionValue': compression_value
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def subscribe(self, instruments: List[Dict], xts_message_code: int = 1501) -> Dict:
        """Subscribe to real-time market data via WebSocket.
        
        Docs: POST {market_data_url}/instruments/subscription
        Payload: {
            "instruments": [{"exchangeSegment": 1, "exchangeInstrumentID": 22}],
            "xtsMessageCode": 1501
        }
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.market_data_url}/instruments/subscription"
        headers = {
            'Authorization': self.market_data_token,
            'Content-Type': 'application/json'
        }
        payload = {
            'instruments': instruments,
            'xtsMessageCode': xts_message_code
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def unsubscribe(self, instruments: List[Dict], xts_message_code: int = 1501) -> Dict:
        """Unsubscribe from real-time market data.
        
        Docs: PUT {market_data_url}/instruments/subscription
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.market_data_url}/instruments/subscription"
        headers = {
            'Authorization': self.market_data_token,
            'Content-Type': 'application/json'
        }
        payload = {
            'instruments': instruments,
            'xtsMessageCode': xts_message_code
        }
        
        try:
            response = requests.put(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ═══════════════════════════════════════════════════════
    # TRADING (INTERACTIVE) API ENDPOINTS
    # All use trading_token
    # ═══════════════════════════════════════════════════════
    
    def get_positions(self, day_or_net: str = "DayWise") -> Dict:
        """Get open positions from trading API.
        
        Docs: GET {trading_url}/portfolio/positions?dayOrNet=DayWise
        Required param: dayOrNet = "DayWise" or "NetWise"
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/portfolio/positions"
        headers = {'Authorization': self.trading_token}
        params = {'dayOrNet': day_or_net}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_holdings(self) -> Dict:
        """Get holdings from trading API.
        
        Docs: GET {trading_url}/portfolio/holdings
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/portfolio/holdings"
        headers = {'Authorization': self.trading_token}
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_orderbook(self) -> Dict:
        """Get orderbook from trading API.
        
        Docs: GET {trading_url}/orders
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/orders"
        headers = {'Authorization': self.trading_token}
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_tradebook(self) -> Dict:
        """Get tradebook (executed trades) from trading API.
        
        Docs: GET {trading_url}/orders/trades
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/orders/trades"
        headers = {'Authorization': self.trading_token}
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_order_history(self, app_order_id: int) -> Dict:
        """Get order history trail for a specific order.
        
        Docs: GET {trading_url}/orders?appOrderID={id}
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/orders"
        headers = {'Authorization': self.trading_token}
        params = {'appOrderID': app_order_id}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_balance(self) -> Dict:
        """Get account balance / RMS limits.
        
        Docs: GET {trading_url}/user/balance
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/user/balance"
        headers = {'Authorization': self.trading_token}
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_profile(self, client_id: str = None) -> Dict:
        """Get user profile.
        
        Docs: GET {trading_url}/user/profile?clientID={id}
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/user/profile"
        headers = {'Authorization': self.trading_token}
        params = {}
        if client_id:
            params['clientID'] = client_id
        
        try:
            response = requests.get(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def place_order(self, order_params: Dict) -> Dict:
        """Place a new order.
        
        Docs: POST {trading_url}/orders
        Payload: {
            "exchangeSegment": "NSEFO",
            "exchangeInstrumentID": 37054,
            "productType": "NRML",
            "orderType": "LIMIT",
            "orderSide": "BUY",
            "timeInForce": "DAY",
            "disclosedQuantity": 0,
            "orderQuantity": 75,
            "limitPrice": 25000,
            "stopPrice": 0,
            "orderUniqueIdentifier": "test123"
        }
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True, 'message': 'Demo mode - order not placed'}
        
        url = f"{self.trading_url}/orders"
        headers = {
            'Authorization': self.trading_token,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=order_params, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def modify_order(self, order_params: Dict) -> Dict:
        """Modify an existing order.
        
        Docs: PUT {trading_url}/orders
        Payload: {
            "appOrderID": 2190766863,
            "modifiedProductType": "NRML",
            "modifiedOrderType": "LIMIT",
            "modifiedOrderQuantity": 25,
            "modifiedDisclosedQuantity": 0,
            "modifiedLimitPrice": 255.65,
            "modifiedStopPrice": 0,
            "modifiedTimeInForce": "DAY",
            "orderUniqueIdentifier": "123abc"
        }
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/orders"
        headers = {
            'Authorization': self.trading_token,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.put(url, json=order_params, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, app_order_id: int) -> Dict:
        """Cancel an open order.
        
        Docs: DELETE {trading_url}/orders?appOrderID={id}
        Note: appOrderID is a QUERY PARAMETER, not in the body.
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/orders"
        headers = {'Authorization': self.trading_token}
        params = {'appOrderID': app_order_id}
        
        try:
            response = requests.delete(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cancel_all_orders(self, exchange_segment: str, exchange_instrument_id: int = 0) -> Dict:
        """Cancel all open orders for a segment or instrument.
        
        Docs: POST {trading_url}/orders/cancelall
        Pass exchangeInstrumentID=0 to cancel ALL orders in that segment.
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/orders/cancelall"
        headers = {
            'Authorization': self.trading_token,
            'Content-Type': 'application/json'
        }
        payload = {
            'exchangeSegment': exchange_segment,
            'exchangeInstrumentID': exchange_instrument_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def position_convert(self, exchange_segment: str, exchange_instrument_id: int,
                         target_qty: int, is_day_wise: bool, old_product_type: str,
                         new_product_type: str) -> Dict:
        """Convert position from one product type to another.
        
        Docs: PUT {trading_url}/portfolio/positions/convert
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/portfolio/positions/convert"
        headers = {
            'Authorization': self.trading_token,
            'Content-Type': 'application/json'
        }
        payload = {
            'exchangeSegment': exchange_segment,
            'exchangeInstrumentID': exchange_instrument_id,
            'targetQty': target_qty,
            'isDayWise': is_day_wise,
            'oldProductType': old_product_type,
            'newProductType': new_product_type,
            'statisticsLevel': '0',
            'isInterOpPosition': False
        }
        
        try:
            response = requests.put(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_brokerage(self, client_id: str, orders: List[Dict]) -> Dict:
        """Calculate brokerage for orders.
        
        Docs: POST {trading_url}/user/calculatebrokerage
        Payload: {
            "clientID": "SYMP",
            "brokerageOrderInformation": [
                { "exchangeSegment": 2, "exchangeInstrumentID": 37054,
                  "productType": "NRML", "orderSide": "BUY",
                  "orderQty": 75, "orderPrice": 25000 }
            ]
        }
        """
        if DEMO_MODE:
            return {'success': True, 'demo': True}
        
        url = f"{self.trading_url}/user/calculatebrokerage"
        headers = {
            'Authorization': self.trading_token,
            'Content-Type': 'application/json'
        }
        payload = {
            'clientID': client_id,
            'brokerageOrderInformation': orders
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}


_xts_client = None


def get_xts_client() -> XTSClient:
    """Get singleton XTS client instance."""
    global _xts_client
    if _xts_client is None:
        _xts_client = XTSClient()
    return _xts_client
