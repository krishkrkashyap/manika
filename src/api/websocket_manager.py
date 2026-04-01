"""
WebSocket Manager - Handle real-time WebSocket streaming from XTS.

Fixed to match the official XTS Market Data API v2 docs:
- Socket.IO path: /apimarketdata/socketio
- Connection URL: {base}?token={token}&userID={userID}&publishFormat={fmt}&broadcastMode={mode}
- Listen on "xts-binary-packet" event for market data
- Subscribe via REST API first, then receive data on socket
"""
import threading
import time
import json
from typing import Dict, List, Callable, Optional

from config.settings import DEMO_MODE, XTS_CONFIG


class WebSocketManager:
    """Manage WebSocket connections for real-time data."""
    
    def __init__(self):
        self.is_connected = False
        self.is_subscribed = False
        self.subscribed_symbols = []
        self.callbacks = []
        self._thread = None
        self._running = False
        self._demo_prices = {}
        self._sio = None  # Socket.IO client
    
    def connect(self, token: str = None, user_id: str = None,
                publish_format: str = "JSON", broadcast_mode: str = "Full") -> bool:
        """Connect to WebSocket server.
        
        Docs: Socket.IO connection with query params:
            URL: {base_url}?token={token}&userID={userID}&publishFormat={fmt}&broadcastMode={mode}
            socketio_path: "/apimarketdata/socketio"
        
        Args:
            token: Market Data API token (from login response)
            user_id: User ID
            publish_format: "JSON" or "Binary"
            broadcast_mode: "Full" or "Partial"
        """
        if DEMO_MODE:
            self.is_connected = True
            return True
        
        try:
            import socketio
            
            base_url = XTS_CONFIG.get('market_data_url', '').replace('/apimarketdata', '')
            if not base_url:
                print("WebSocket: No market_data_url configured")
                return False
            
            self._sio = socketio.Client(logger=False)
            
            # Register event handlers
            @self._sio.on("connect")
            def on_connect():
                print("WebSocket: Connected")
                self.is_connected = True
            
            @self._sio.on("joined")
            def on_joined(data):
                print(f"WebSocket: Joined - {data}")
            
            @self._sio.on("error")
            def on_error(data):
                print(f"WebSocket: Error - {data}")
            
            @self._sio.on("disconnect")
            def on_disconnect():
                print("WebSocket: Disconnected")
                self.is_connected = False
            
            @self._sio.on("xts-binary-packet")
            def on_binary_data(data):
                """Handle incoming market data packets."""
                self._process_market_data(data)
            
            # Build connection URL with query params
            connection_string = (
                f"{base_url}?token={token}"
                f"&userID={user_id}"
                f"&publishFormat={publish_format}"
                f"&broadcastMode={broadcast_mode}"
            )
            
            # Connect with correct socketio_path
            self._sio.connect(
                connection_string,
                socketio_path="/apimarketdata/socketio",
                transports=['websocket']
            )
            
            self.is_connected = True
            return True
            
        except ImportError:
            print("WebSocket: python-socketio not installed. Run: pip install python-socketio[client]")
            return False
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from WebSocket server."""
        self._running = False
        self.is_connected = False
        self.is_subscribed = False
        
        if self._sio and not DEMO_MODE:
            try:
                self._sio.disconnect()
            except Exception:
                pass
            self._sio = None
        
        if self._thread:
            self._thread.join(timeout=2)
    
    def subscribe(self, symbols: List[str], callback: Callable = None):
        """Subscribe to symbols for real-time updates.
        
        Note: For XTS, actual subscription is done via the REST API
        (POST /instruments/subscription), not through socket events.
        The socket only receives data after REST subscription.
        
        Args:
            symbols: List of trading symbols
            callback: Function to call on updates
        """
        self.subscribed_symbols = symbols
        
        if callback:
            self.callbacks.append(callback)
        
        if DEMO_MODE:
            self.is_subscribed = True
            self._start_demo_streaming()
        else:
            self._subscribe_to_xts(symbols)
    
    def unsubscribe(self, symbols: List[str] = None):
        """Unsubscribe from symbols."""
        if symbols:
            for sym in symbols:
                if sym in self.subscribed_symbols:
                    self.subscribed_symbols.remove(sym)
        else:
            self.subscribed_symbols = []
        
        if DEMO_MODE:
            self.is_subscribed = len(self.subscribed_symbols) > 0
        else:
            self._unsubscribe_from_xts(symbols)
    
    def _subscribe_to_xts(self, symbols: List[str]):
        """Subscribe via XTS REST API (not socket).
        
        The REST subscription tells the server to stream data
        for these instruments to our socket connection.
        """
        from ..api.xts_client import get_xts_client
        client = get_xts_client()
        
        # Convert symbol names to instrument format
        # This would need proper instrument lookup in production
        instruments = []
        for symbol in symbols:
            # TODO: Map symbol → (exchangeSegment, exchangeInstrumentID)
            # For now, this is a placeholder
            pass
        
        if instruments:
            result = client.subscribe(instruments, xts_message_code=1501)
            if result.get('type') == 'success':
                self.is_subscribed = True
                print(f"WebSocket: Subscribed to {len(instruments)} instruments")
            else:
                print(f"WebSocket: Subscription failed - {result}")
    
    def _unsubscribe_from_xts(self, symbols: List[str]):
        """Unsubscribe via XTS REST API."""
        from ..api.xts_client import get_xts_client
        client = get_xts_client()
        
        instruments = []
        for symbol in symbols or []:
            pass  # TODO: Map symbol → instrument format
        
        if instruments:
            client.unsubscribe(instruments, xts_message_code=1501)
    
    def _process_market_data(self, data):
        """Process incoming market data from XTS socket.
        
        Data format depends on publishFormat:
        - JSON: parsed JSON dict with Touchline/MarketDepth fields
        - Binary: binary-encoded packet that needs deserialization
        """
        try:
            if isinstance(data, str):
                parsed = json.loads(data)
            elif isinstance(data, dict):
                parsed = data
            else:
                # Binary data — would need struct unpacking
                return
            
            # Extract key fields from Touchline (message code 1501)
            exchange_id = parsed.get('ExchangeInstrumentID')
            if exchange_id:
                touchline = parsed.get('Touchline', parsed)
                price_data = {
                    'exchange_instrument_id': exchange_id,
                    'ltp': touchline.get('LastTradedPrice', 0),
                    'open': touchline.get('Open', 0),
                    'high': touchline.get('High', 0),
                    'low': touchline.get('Low', 0),
                    'close': touchline.get('Close', 0),
                    'volume': touchline.get('TotalTradedQuantity', 0),
                    'change_pct': touchline.get('PercentChange', 0),
                    'timestamp': touchline.get('LastUpdateTime', '')
                }
                
                self._demo_prices[str(exchange_id)] = price_data
                
                for callback in self.callbacks:
                    try:
                        callback(price_data)
                    except Exception as e:
                        print(f"Callback error: {e}")
                        
        except Exception as e:
            print(f"Market data parse error: {e}")
    
    def _start_demo_streaming(self):
        """Start demo streaming with simulated prices."""
        self._running = True
        self._thread = threading.Thread(target=self._demo_stream_loop, daemon=True)
        self._thread.start()
    
    def _demo_stream_loop(self):
        """Demo streaming loop - simulates real-time updates."""
        import random
        from datetime import datetime
        
        while self._running:
            for symbol in self.subscribed_symbols:
                base_price = self._get_base_price(symbol)
                if base_price > 0:
                    variation = random.uniform(-0.005, 0.005)
                    new_price = round(base_price * (1 + variation), 2)
                    
                    self._demo_prices[symbol] = {
                        'symbol': symbol,
                        'ltp': new_price,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    for callback in self.callbacks:
                        try:
                            callback(self._demo_prices[symbol])
                        except Exception as e:
                            print(f"Callback error: {e}")
            
            time.sleep(1)
    
    def _get_base_price(self, symbol: str) -> float:
        """Get base price for demo symbol."""
        from ..data.demo_data import DEMO_QUOTES
        quote = DEMO_QUOTES.get(symbol, {})
        return quote.get('ltp', 100.0)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        if symbol in self._demo_prices:
            return self._demo_prices[symbol].get('ltp')
        return self._get_base_price(symbol)
    
    def get_all_prices(self) -> Dict:
        """Get all current prices."""
        return self._demo_prices.copy()


_websocket_manager = None


def get_websocket_manager() -> WebSocketManager:
    """Get singleton WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager
