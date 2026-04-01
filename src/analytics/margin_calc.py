"""
Margin Calculator - Calculate margin requirements for positions.
"""
from typing import Dict, List


class MarginCalculator:
    """Calculate margin requirements for trading positions."""
    
    MARGIN_RATES = {
        'FUTURES': {
            'NSECM': 0.12,
            'NSEFO': 0.12,
            'BSECM': 0.12,
            'BSEFO': 0.12,
        },
        'OPTIONS': {
            'NSECM': 0.15,
            'NSEFO': 0.15,
            'BSECM': 0.15,
            'BSEFO': 0.15,
        }
    }
    
    def __init__(self):
        pass
    
    def calculate_futures_margin(self, position: Dict, current_price: float) -> float:
        """Calculate margin requirement for futures position.
        
        Args:
            position: Position dict with 'net_qty', 'lot_size'
            current_price: Current LTP
            
        Returns:
            Margin required
        """
        net_qty = abs(position.get('net_qty', 0))
        lot_size = position.get('lot_size', 1500)
        exchange = position.get('exchange', 'NSEFO')
        
        if net_qty == 0:
            return 0.0
        
        margin_rate = self.MARGIN_RATES['FUTURES'].get(exchange, 0.12)
        
        lots = net_qty / lot_size if lot_size > 0 else net_qty
        margin = lots * lot_size * current_price * margin_rate
        
        return round(margin, 2)
    
    def calculate_options_margin(self, position: Dict, current_price: float) -> float:
        """Calculate margin requirement for options position.
        
        Args:
            position: Position dict with 'net_qty', 'lot_size'
            current_price: Current LTP
            
        Returns:
            Margin required
        """
        net_qty = abs(position.get('net_qty', 0))
        lot_size = position.get('lot_size', 1500)
        exchange = position.get('exchange', 'NSEFO')
        
        if net_qty == 0:
            return 0.0
        
        margin_rate = self.MARGIN_RATES['OPTIONS'].get(exchange, 0.15)
        
        premium = current_price * net_qty
        margin = premium * margin_rate
        
        return round(margin, 2)
    
    def calculate_total_margin(self, positions: Dict, quotes: Dict) -> Dict:
        """Calculate total margin requirement for all positions.
        
        Returns:
            Dict with total_margin, futures_margin, options_margin, breakdown
        """
        futures_margin = 0.0
        options_margin = 0.0
        breakdown = []
        
        for stock, data in positions.items():
            stock_fut_margin = 0.0
            stock_opt_margin = 0.0
            
            fut = data.get('futures', {})
            if fut.get('net_qty', 0) != 0:
                symbol = fut.get('symbol')
                ltp = quotes.get(symbol, {}).get('ltp', fut.get('buy_avg', 0))
                margin = self.calculate_futures_margin(fut, ltp)
                stock_fut_margin = margin
                futures_margin += margin
            
            for opt in data.get('options', []):
                if opt.get('net_qty', 0) != 0:
                    symbol = opt.get('symbol')
                    ltp = quotes.get(symbol, {}).get('ltp', opt.get('sell_avg', 0))
                    margin = self.calculate_options_margin(opt, ltp)
                    stock_opt_margin += margin
                    options_margin += margin
            
            if stock_fut_margin > 0 or stock_opt_margin > 0:
                breakdown.append({
                    'stock': stock,
                    'futures_margin': stock_fut_margin,
                    'options_margin': stock_opt_margin,
                    'total_margin': stock_fut_margin + stock_opt_margin
                })
        
        total_margin = futures_margin + options_margin
        
        return {
            'total_margin': round(total_margin, 2),
            'futures_margin': round(futures_margin, 2),
            'options_margin': round(options_margin, 2),
            'breakdown': breakdown
        }
    
    def calculate_order_margin(self, symbol: str, quantity: int, price: float, 
                               product_type: str = 'MIS', exchange: str = 'NSEFO') -> Dict:
        """Calculate margin for a new order.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            product_type: MIS, NRML, CNC, CO, BO
            exchange: Exchange segment
            
        Returns:
            Margin details
        """
        if product_type in ['CNC', 'NRML']:
            margin = 0.0
        elif product_type == 'MIS':
            margin_rate = self.MARGIN_RATES['FUTURES'].get(exchange, 0.12)
            margin = quantity * price * margin_rate
        elif product_type in ['CO', 'BO']:
            margin_rate = self.MARGIN_RATES['FUTURES'].get(exchange, 0.12)
            margin = quantity * price * margin_rate * 1.5
        else:
            margin = 0.0
        
        return {
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'product_type': product_type,
            'exchange': exchange,
            'required_margin': round(margin, 2),
            'leverage': round((quantity * price) / margin, 2) if margin > 0 else 0
        }


_margin_calculator = None


def get_margin_calculator() -> MarginCalculator:
    """Get singleton margin calculator instance."""
    global _margin_calculator
    if _margin_calculator is None:
        _margin_calculator = MarginCalculator()
    return _margin_calculator
