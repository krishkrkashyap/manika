"""
Market Data Fetcher - Fetch live quotes from demo or XTS API.
"""
import random
import time
from typing import Dict, Optional
from datetime import datetime

from config.settings import DEMO_MODE
from .demo_data import DEMO_QUOTES


class MarketDataFetcher:
    """Fetches market data from demo mode or XTS API."""
    
    def __init__(self):
        self._quotes = DEMO_QUOTES.copy()
        self._price_cache = {}
        self._last_update = None
        self._instrument_map = {}  # symbol → {exchange_segment, exchange_instrument_id}
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote for a single symbol."""
        if DEMO_MODE:
            return self._get_demo_quote(symbol)
        else:
            return self._fetch_from_xts(symbol)
    
    def get_quotes_batch(self, symbols: list) -> Dict:
        """Get quotes for multiple symbols."""
        quotes = {}
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        return quotes
    
    def _get_demo_quote(self, symbol: str) -> Optional[Dict]:
        """Get simulated quote with slight price fluctuations."""
        base_quote = DEMO_QUOTES.get(symbol)
        if not base_quote:
            return None
        
        ltp = base_quote.get('ltp', base_quote.get('close', 100))
        
        variation = random.uniform(-0.02, 0.02)
        new_ltp = round(ltp * (1 + variation), 2)
        
        change = round(new_ltp - base_quote['close'], 2)
        change_pct = round((change / base_quote['close']) * 100, 2)
        
        return {
            'symbol': symbol,
            'ltp': new_ltp,
            'close': base_quote['close'],
            'open': base_quote['open'],
            'high': base_quote['high'],
            'low': base_quote['low'],
            'volume': base_quote['volume'],
            'change': change,
            'change_pct': change_pct,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    
    def _fetch_from_xts(self, symbol: str) -> Optional[Dict]:
        """Fetch real quote from XTS API.
        
        Uses: POST {market_data_url}/instruments/quotes
        with xtsMessageCode 1501 (Touchline) for best bid/ask + LTP.
        
        Requires the instrument to be mapped to (exchangeSegment, exchangeInstrumentID).
        """
        try:
            from ..api.xts_client import get_xts_client
            client = get_xts_client()
            
            # Look up instrument mapping from positions/config
            instrument_info = self._get_instrument_info(symbol)
            if not instrument_info:
                return None
            
            instruments = [{
                'exchangeSegment': instrument_info['exchange_segment'],
                'exchangeInstrumentID': instrument_info['exchange_instrument_id']
            }]
            
            result = client.get_quote(instruments, xts_message_code=1501, publish_format="JSON")
            
            # Parse XTS response
            if isinstance(result, list):
                result = result[0] if result else {}
            
            if result.get('type') != 'success':
                return None
            
            # Extract touchline data from response
            list_quotes = result.get('result', {}).get('listQuotes', {})
            if isinstance(list_quotes, str):
                import json
                list_quotes = json.loads(list_quotes)
            
            touchline = list_quotes.get('Touchline', list_quotes) if isinstance(list_quotes, dict) else {}
            
            ltp = touchline.get('LastTradedPrice', 0)
            close = touchline.get('Close', 0)
            change = round(ltp - close, 2) if close else 0
            change_pct = round((change / close) * 100, 2) if close else 0
            
            return {
                'symbol': symbol,
                'ltp': ltp,
                'close': close,
                'open': touchline.get('Open', 0),
                'high': touchline.get('High', 0),
                'low': touchline.get('Low', 0),
                'volume': touchline.get('TotalTradedQuantity', 0),
                'change': change,
                'change_pct': change_pct,
                'bid_price': touchline.get('BidInfo', {}).get('Price', 0),
                'ask_price': touchline.get('AskInfo', {}).get('Price', 0),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
        except Exception as e:
            print(f"XTS quote fetch error for {symbol}: {e}")
            return None
    
    def _get_instrument_info(self, symbol: str) -> Optional[Dict]:
        """Look up exchange segment + instrument ID for a symbol.
        
        In production, this would query a cached instrument master
        or a pre-built mapping from the POST /instruments/master API.
        """
        # Check if we have a cached mapping
        return self._instrument_map.get(symbol)
    
    def set_instrument_map(self, mapping: Dict[str, Dict]):
        """Set the symbol → instrument mapping.
        
        Args:
            mapping: { "BEL26MARFUT": {"exchange_segment": 2, "exchange_instrument_id": 37054}, ... }
        """
        self._instrument_map = mapping
    
    def update_all_quotes(self, symbols: list) -> Dict:
        """Update and return quotes for all symbols."""
        quotes = {}
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        
        self._last_update = datetime.now()
        return quotes
    
    def get_last_update(self) -> Optional[datetime]:
        """Get last update timestamp."""
        return self._last_update
    
    def simulate_market_movement(self):
        """Simulate market movement for demo mode."""
        for symbol in DEMO_QUOTES:
            self.get_quote(symbol)


_market_data_fetcher = None


def get_market_data_fetcher() -> MarketDataFetcher:
    """Get singleton market data fetcher instance."""
    global _market_data_fetcher
    if _market_data_fetcher is None:
        _market_data_fetcher = MarketDataFetcher()
    return _market_data_fetcher
