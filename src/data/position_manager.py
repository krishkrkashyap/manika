"""
Position Manager - Load and manage positions from demo or XTS API.
Provides consolidated views matching the Excel MAIN sheet layout.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from config.settings import DATA_DIR, DEMO_MODE
from .demo_data import DEMO_POSITIONS, UNDERLYING_PRICES


class PositionManager:
    """Manages trading positions from demo data or XTS API."""
    
    def __init__(self):
        self.positions_file = DATA_DIR / "positions.json"
        self._positions = {}
        self._load_positions()
    
    def _load_positions(self):
        """Load positions from demo data or saved JSON."""
        if DEMO_MODE:
            self._positions = DEMO_POSITIONS
        else:
            self._load_from_file()
    
    def _load_from_file(self):
        """Load positions from JSON file."""
        if self.positions_file.exists():
            with open(self.positions_file, 'r') as f:
                self._positions = json.load(f)
        else:
            self._positions = DEMO_POSITIONS
    
    def save_positions(self):
        """Save positions to JSON file."""
        with open(self.positions_file, 'w') as f:
            json.dump(self._positions, f, indent=2, default=str)
    
    def get_all_positions(self) -> Dict:
        """Get all positions."""
        return self._positions
    
    def get_positions_by_stock(self, stock: str) -> Optional[Dict]:
        """Get position for a specific stock."""
        return self._positions.get(stock)
    
    def get_underlying_prices(self) -> Dict:
        """Get underlying spot prices for all stocks."""
        return UNDERLYING_PRICES
    
    def get_futures_positions(self) -> List[Dict]:
        """Get all futures positions."""
        futures = []
        for stock, data in self._positions.items():
            fut = data.get('futures', {})
            if fut.get('net_qty', 0) != 0:
                fut_copy = fut.copy()
                fut_copy['stock'] = stock
                fut_copy['type'] = 'FUTURES'
                futures.append(fut_copy)
        return futures
    
    def get_options_positions(self) -> List[Dict]:
        """Get all options positions."""
        options = []
        for stock, data in self._positions.items():
            for opt in data.get('options', []):
                if opt.get('net_qty', 0) != 0:
                    opt_copy = opt.copy()
                    opt_copy['stock'] = stock
                    opt_copy['type'] = 'OPTIONS'
                    options.append(opt_copy)
        return options
    
    def get_consolidated_view(self, quotes: Dict) -> List[Dict]:
        """Get consolidated position view matching Excel MAIN sheet.
        Returns rows grouped by stock with futures, PE, CE sections.
        
        Args:
            quotes: Current market quotes
            
        Returns:
            List of position rows with all fields for display
        """
        rows = []
        
        for stock, data in self._positions.items():
            underlying = UNDERLYING_PRICES.get(stock, {})
            stk_prc = underlying.get('spot_ltp', 0)
            
            # Futures row
            fut = data.get('futures', {})
            if fut.get('net_qty', 0) != 0:
                symbol = fut.get('symbol')
                quote = quotes.get(symbol, {})
                rows.append({
                    'stock': stock,
                    'name': data.get('name', stock),
                    'section': 'FUTURES',
                    'symbol': symbol,
                    'strike': '-',
                    'option_type': 'FUT',
                    'expiry': fut.get('expiry', ''),
                    'stk_prc': stk_prc,
                    'net_qty': fut.get('net_qty', 0),
                    'net_lots': fut.get('net_qty', 0) // fut.get('lot_size', 1),
                    'lot_size': fut.get('lot_size', 1500),
                    'buy_avg': fut.get('buy_avg', 0),
                    'sell_avg': fut.get('sell_avg', 0),
                    'close': quote.get('close', fut.get('yesterday_close', 0)),
                    'ltp': quote.get('ltp', 0),
                    'change_pct': quote.get('change_pct', 0),
                    'yesterday_close': quote.get('yesterday_close', fut.get('yesterday_close', 0)),
                    'today_open': quote.get('open', 0),
                })
            
            # PE Options
            pe_opts = [o for o in data.get('options', []) if o.get('option_type') == 'PE']
            for opt in pe_opts:
                symbol = opt.get('symbol')
                quote = quotes.get(symbol, {})
                rows.append({
                    'stock': stock,
                    'name': data.get('name', stock),
                    'section': 'PE',
                    'symbol': symbol,
                    'strike': opt.get('strike', 0),
                    'option_type': 'PE',
                    'expiry': opt.get('expiry', ''),
                    'stk_prc': stk_prc,
                    'net_qty': opt.get('net_qty', 0),
                    'net_lots': opt.get('net_qty', 0) // opt.get('lot_size', 1),
                    'lot_size': opt.get('lot_size', 1500),
                    'buy_avg': opt.get('buy_avg', 0),
                    'sell_avg': opt.get('sell_avg', 0),
                    'close': quote.get('close', opt.get('yesterday_close', 0)),
                    'ltp': quote.get('ltp', 0),
                    'change_pct': quote.get('change_pct', 0),
                    'yesterday_close': quote.get('yesterday_close', opt.get('yesterday_close', 0)),
                    'today_open': quote.get('open', 0),
                })
            
            # CE Options
            ce_opts = [o for o in data.get('options', []) if o.get('option_type') == 'CE']
            for opt in ce_opts:
                symbol = opt.get('symbol')
                quote = quotes.get(symbol, {})
                rows.append({
                    'stock': stock,
                    'name': data.get('name', stock),
                    'section': 'CE',
                    'symbol': symbol,
                    'strike': opt.get('strike', 0),
                    'option_type': 'CE',
                    'expiry': opt.get('expiry', ''),
                    'stk_prc': stk_prc,
                    'net_qty': opt.get('net_qty', 0),
                    'net_lots': opt.get('net_qty', 0) // opt.get('lot_size', 1),
                    'lot_size': opt.get('lot_size', 1500),
                    'buy_avg': opt.get('buy_avg', 0),
                    'sell_avg': opt.get('sell_avg', 0),
                    'close': quote.get('close', opt.get('yesterday_close', 0)),
                    'ltp': quote.get('ltp', 0),
                    'change_pct': quote.get('change_pct', 0),
                    'yesterday_close': quote.get('yesterday_close', opt.get('yesterday_close', 0)),
                    'today_open': quote.get('open', 0),
                })
        
        return rows
    
    def get_trade_info(self, quotes: Dict) -> List[Dict]:
        """Get trade info / opening positions matching Trade_Info Excel sheet.
        
        Returns:
            List of trade info rows with buy/sell details, closing price, MTM
        """
        rows = []
        
        for stock, data in self._positions.items():
            # Futures
            fut = data.get('futures', {})
            symbol = fut.get('symbol')
            quote = quotes.get(symbol, {})
            
            buy_qty = fut.get('quantity', 0)
            buy_avg = fut.get('buy_avg', 0)
            sell_avg = fut.get('sell_avg', 0)
            net_qty = fut.get('net_qty', 0)
            closing_price = quote.get('close', fut.get('yesterday_close', 0))
            ltp = quote.get('ltp', 0)
            
            buy_amt = buy_qty * buy_avg if buy_avg > 0 else 0
            sell_amt = (buy_qty - net_qty) * sell_avg if sell_avg > 0 else 0
            gross_mtm = (ltp - buy_avg) * net_qty if net_qty > 0 else 0
            closing_mtm = (closing_price - buy_avg) * net_qty if net_qty > 0 else 0
            
            rows.append({
                'stock': stock,
                'scrip_name': symbol,
                'instrument_type': 'FUTSTK',
                'buy_qty': buy_qty,
                'buy_avg_prc': buy_avg,
                'buy_amt': round(buy_amt, 2),
                'sell_qty': buy_qty - net_qty,
                'sell_avg_prc': sell_avg,
                'sell_amt': round(sell_amt, 2),
                'gross_mtm': round(gross_mtm, 2),
                'net_qty': net_qty,
                'closing_price': closing_price,
                'closing_mtm': round(closing_mtm, 2),
                'ltp': ltp,
            })
            
            # Options
            for opt in data.get('options', []):
                symbol = opt.get('symbol')
                quote = quotes.get(symbol, {})
                
                opt_qty = abs(opt.get('quantity', 0))
                buy_avg = opt.get('buy_avg', 0)
                sell_avg = opt.get('sell_avg', 0)
                net_qty = opt.get('net_qty', 0)
                closing_price = quote.get('close', opt.get('yesterday_close', 0))
                ltp = quote.get('ltp', 0)
                
                if net_qty < 0:  # Short option
                    gross_mtm = (sell_avg - ltp) * abs(net_qty)
                    closing_mtm = (sell_avg - closing_price) * abs(net_qty)
                elif net_qty > 0:  # Long option
                    gross_mtm = (ltp - buy_avg) * net_qty
                    closing_mtm = (closing_price - buy_avg) * net_qty
                else:
                    gross_mtm = 0
                    closing_mtm = 0
                
                rows.append({
                    'stock': stock,
                    'scrip_name': symbol,
                    'instrument_type': opt.get('instrument_type', 'OPTSTK'),
                    'buy_qty': opt_qty if buy_avg > 0 else 0,
                    'buy_avg_prc': buy_avg,
                    'buy_amt': round((opt_qty if buy_avg > 0 else 0) * buy_avg, 2),
                    'sell_qty': opt_qty if sell_avg > 0 else 0,
                    'sell_avg_prc': sell_avg,
                    'sell_amt': round((opt_qty if sell_avg > 0 else 0) * sell_avg, 2),
                    'gross_mtm': round(gross_mtm, 2),
                    'net_qty': net_qty,
                    'closing_price': closing_price,
                    'closing_mtm': round(closing_mtm, 2),
                    'ltp': ltp,
                })
        
        return rows
    
    def get_all_tradable_symbols(self) -> List[str]:
        """Get all tradable symbols from positions."""
        symbols = []
        for stock, data in self._positions.items():
            fut = data.get('futures', {})
            if fut.get('symbol'):
                symbols.append(fut['symbol'])
            for opt in data.get('options', []):
                if opt.get('symbol'):
                    symbols.append(opt['symbol'])
        return symbols
    
    def update_position_price(self, symbol: str, ltp: float):
        """Update LTP for a position symbol."""
        for stock, data in self._positions.items():
            if data.get('futures', {}).get('symbol') == symbol:
                data['futures']['ltp'] = ltp
                return
            for opt in data.get('options', []):
                if opt.get('symbol') == symbol:
                    opt['ltp'] = ltp
                    return
    
    def get_total_position_value(self) -> float:
        """Calculate total position value."""
        total = 0.0
        for stock, data in self._positions.items():
            fut = data.get('futures', {})
            if fut.get('net_qty', 0) != 0:
                ltp = fut.get('ltp', fut.get('buy_avg', 0))
                total += abs(fut['net_qty'] * ltp)
            for opt in data.get('options', []):
                if opt.get('net_qty', 0) != 0:
                    ltp = opt.get('ltp', opt.get('sell_avg', 0))
                    total += abs(opt['net_qty'] * ltp)
        return total
    
    def get_stock_names(self) -> Dict[str, str]:
        """Get mapping of stock tickers to full names."""
        return {stock: data.get('name', stock) for stock, data in self._positions.items()}


_position_manager = None


def get_position_manager() -> PositionManager:
    """Get singleton position manager instance."""
    global _position_manager
    if _position_manager is None:
        _position_manager = PositionManager()
    return _position_manager
