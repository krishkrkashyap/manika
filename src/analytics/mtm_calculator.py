"""
MTM Calculator - Calculate Mark to Market profits/losses.
Supports LAST (yesterday close vs today close), INTRA (today open vs LTP),
and EXP (entry price vs LTP) MTM calculations matching the Excel sheet.
"""
from typing import Dict, List
from config.settings import MTM_SCENARIO_PERCENTAGES


class MTMCalculator:
    """Calculate MTM (Mark to Market) for positions."""
    
    def __init__(self):
        self.scenario_percentages = MTM_SCENARIO_PERCENTAGES
    
    def calculate_position_mtm(self, position: Dict, current_price: float) -> Dict:
        """Calculate MTM for a single position (entry-based / TOTAL MTM).
        
        Args:
            position: Position dict with 'net_qty', 'buy_avg', 'sell_avg'
            current_price: Current LTP
            
        Returns:
            Dict with mtm, mtm_pct
        """
        net_qty = position.get('net_qty', 0)
        buy_avg = position.get('buy_avg', 0)
        sell_avg = position.get('sell_avg', 0)
        
        if net_qty > 0:
            avg_price = buy_avg if buy_avg > 0 else sell_avg
            mtm = (current_price - avg_price) * net_qty
        elif net_qty < 0:
            avg_price = sell_avg if sell_avg > 0 else buy_avg
            mtm = (avg_price - current_price) * abs(net_qty)
        else:
            mtm = 0.0
        
        avg_price = buy_avg if net_qty > 0 else sell_avg
        if avg_price > 0:
            mtm_pct = ((current_price - avg_price) / avg_price) * 100 if net_qty > 0 else ((avg_price - current_price) / avg_price) * 100
        else:
            mtm_pct = 0.0
        
        return {
            'mtm': round(mtm, 2),
            'mtm_pct': round(mtm_pct, 2),
            'current_price': current_price
        }
    
    def calculate_last_mtm(self, position: Dict, current_close: float, yesterday_close: float) -> float:
        """Calculate LAST MTM: (today's close - yesterday's close) * qty.
        This represents the day-over-day change.
        
        Args:
            position: Position dict with 'net_qty'
            current_close: Today's closing price (or LTP during market hours)
            yesterday_close: Yesterday's closing price
        
        Returns:
            LAST MTM value
        """
        net_qty = position.get('net_qty', 0)
        if net_qty == 0 or yesterday_close <= 0:
            return 0.0
        
        if net_qty > 0:
            mtm = (current_close - yesterday_close) * net_qty
        else:
            mtm = (yesterday_close - current_close) * abs(net_qty)
        
        return round(mtm, 2)
    
    def calculate_intra_mtm(self, position: Dict, ltp: float, today_open: float) -> float:
        """Calculate INTRA MTM: (LTP - today's open) * qty.
        This represents the intraday change from market open.
        
        Args:
            position: Position dict with 'net_qty'
            ltp: Last traded price
            today_open: Today's opening price
        
        Returns:
            INTRA MTM value
        """
        net_qty = position.get('net_qty', 0)
        if net_qty == 0 or today_open <= 0:
            return 0.0
        
        if net_qty > 0:
            mtm = (ltp - today_open) * net_qty
        else:
            mtm = (today_open - ltp) * abs(net_qty)
        
        return round(mtm, 2)
    
    def calculate_exp_mtm(self, position: Dict, ltp: float) -> float:
        """Calculate EXP MTM: (LTP - entry avg) * qty.
        This represents total P&L from entry to current (expiry view).
        Same as total MTM.
        
        Args:
            position: Position dict with 'net_qty', 'buy_avg', 'sell_avg'
            ltp: Last traded price
        
        Returns:
            EXP MTM value
        """
        result = self.calculate_position_mtm(position, ltp)
        return result['mtm']
    
    def calculate_all_mtm(self, positions: Dict, quotes: Dict) -> Dict:
        """Calculate MTM for all positions with LAST/INTRA/EXP breakdown.
        
        Args:
            positions: Dict of all positions
            quotes: Dict of current quotes
            
        Returns:
            Dict with total_mtm, positions_mtm, breakdown, last_total, intra_total, exp_total
        """
        total_mtm = 0.0
        last_total = 0.0
        intra_total = 0.0
        exp_total = 0.0
        positions_mtm = []
        breakdown = {'FUTURES': 0.0, 'OPTIONS': 0.0}
        stock_totals = {}
        
        for stock, data in positions.items():
            stock_mtm = 0.0
            stock_last = 0.0
            stock_intra = 0.0
            stock_exp = 0.0
            
            # Futures
            fut = data.get('futures', {})
            if fut.get('net_qty', 0) != 0:
                symbol = fut.get('symbol')
                quote = quotes.get(symbol, {})
                ltp = quote.get('ltp', fut.get('buy_avg', 0))
                close = quote.get('close', fut.get('yesterday_close', 0))
                yesterday_close = quote.get('yesterday_close', close)
                today_open = quote.get('open', close)
                
                mtm_data = self.calculate_position_mtm(fut, ltp)
                fut_mtm = mtm_data['mtm']
                last_mtm = self.calculate_last_mtm(fut, ltp, yesterday_close)
                intra_mtm = self.calculate_intra_mtm(fut, ltp, today_open)
                exp_mtm = self.calculate_exp_mtm(fut, ltp)
                
                stock_mtm += fut_mtm
                stock_last += last_mtm
                stock_intra += intra_mtm
                stock_exp += exp_mtm
                breakdown['FUTURES'] += fut_mtm
                
                positions_mtm.append({
                    'stock': stock,
                    'symbol': symbol,
                    'type': 'FUTURES',
                    'net_qty': fut.get('net_qty'),
                    'ltp': ltp,
                    'mtm': fut_mtm,
                    'mtm_pct': mtm_data['mtm_pct'],
                    'last_mtm': last_mtm,
                    'intra_mtm': intra_mtm,
                    'exp_mtm': exp_mtm,
                })
            
            # Options
            for opt in data.get('options', []):
                if opt.get('net_qty', 0) != 0:
                    symbol = opt.get('symbol')
                    quote = quotes.get(symbol, {})
                    ltp = quote.get('ltp', opt.get('sell_avg', 0))
                    close = quote.get('close', opt.get('yesterday_close', 0))
                    yesterday_close = quote.get('yesterday_close', close)
                    today_open = quote.get('open', close)
                    
                    mtm_data = self.calculate_position_mtm(opt, ltp)
                    opt_mtm = mtm_data['mtm']
                    last_mtm = self.calculate_last_mtm(opt, ltp, yesterday_close)
                    intra_mtm = self.calculate_intra_mtm(opt, ltp, today_open)
                    exp_mtm = self.calculate_exp_mtm(opt, ltp)
                    
                    stock_mtm += opt_mtm
                    stock_last += last_mtm
                    stock_intra += intra_mtm
                    stock_exp += exp_mtm
                    breakdown['OPTIONS'] += opt_mtm
                    
                    positions_mtm.append({
                        'stock': stock,
                        'symbol': symbol,
                        'type': 'OPTIONS',
                        'strike': opt.get('strike'),
                        'option_type': opt.get('option_type'),
                        'net_qty': opt.get('net_qty'),
                        'ltp': ltp,
                        'mtm': opt_mtm,
                        'mtm_pct': mtm_data['mtm_pct'],
                        'last_mtm': last_mtm,
                        'intra_mtm': intra_mtm,
                        'exp_mtm': exp_mtm,
                    })
            
            total_mtm += stock_mtm
            last_total += stock_last
            intra_total += stock_intra
            exp_total += stock_exp
            
            stock_totals[stock] = {
                'total_mtm': round(stock_mtm, 2),
                'last_mtm': round(stock_last, 2),
                'intra_mtm': round(stock_intra, 2),
                'exp_mtm': round(stock_exp, 2),
            }
        
        return {
            'total_mtm': round(total_mtm, 2),
            'last_total': round(last_total, 2),
            'intra_total': round(intra_total, 2),
            'exp_total': round(exp_total, 2),
            'positions_mtm': positions_mtm,
            'breakdown': breakdown,
            'stock_totals': stock_totals,
        }
    
    def calculate_scenario_mtm(self, position: Dict, base_price: float, percentage: float) -> float:
        """Calculate MTM for a scenario percentage change."""
        scenario_price = base_price * (1 + percentage)
        mtm_data = self.calculate_position_mtm(position, scenario_price)
        return mtm_data['mtm']
    
    def generate_scenario_table(self, positions: Dict, quotes: Dict) -> List[Dict]:
        """Generate MTM scenario table like in Excel (-10% to +10%).
        Returns per-stock breakdown for each scenario.
        """
        scenarios = []
        
        for pct in self.scenario_percentages:
            scenario = {
                'percentage': f"{pct*100:+.1f}%",
                'pct_value': pct,
                'total_mtm': 0.0,
                'stocks': {}
            }
            
            for stock, data in positions.items():
                stock_mtm = 0.0
                
                fut = data.get('futures', {})
                if fut.get('net_qty', 0) != 0:
                    close = quotes.get(fut.get('symbol'), {}).get('close', fut.get('buy_avg', 0))
                    if close > 0:
                        mtm = self.calculate_scenario_mtm(fut, close, pct)
                        stock_mtm += mtm
                
                for opt in data.get('options', []):
                    if opt.get('net_qty', 0) != 0:
                        close = quotes.get(opt.get('symbol'), {}).get('close', opt.get('sell_avg', 0))
                        if close > 0:
                            mtm = self.calculate_scenario_mtm(opt, close, pct)
                            stock_mtm += mtm
                
                scenario['stocks'][stock] = round(stock_mtm, 2)
                scenario['total_mtm'] += stock_mtm
            
            scenario['total_mtm'] = round(scenario['total_mtm'], 2)
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_stock_scenario_table(self, stock: str, data: Dict, quotes: Dict) -> List[Dict]:
        """Generate per-stock scenario table matching the Excel stock sheets."""
        scenarios = []
        
        for pct in self.scenario_percentages:
            row = {
                'percentage': f"{pct*100:+.1f}%",
                'pct_value': pct,
                'futures_mtm': 0.0,
                'options_mtm': 0.0,
                'total_mtm': 0.0,
            }
            
            fut = data.get('futures', {})
            if fut.get('net_qty', 0) != 0:
                close = quotes.get(fut.get('symbol'), {}).get('close', fut.get('buy_avg', 0))
                if close > 0:
                    row['futures_mtm'] = round(self.calculate_scenario_mtm(fut, close, pct), 2)
            
            for opt in data.get('options', []):
                if opt.get('net_qty', 0) != 0:
                    close = quotes.get(opt.get('symbol'), {}).get('close', opt.get('sell_avg', 0))
                    if close > 0:
                        row['options_mtm'] += self.calculate_scenario_mtm(opt, close, pct)
            
            row['options_mtm'] = round(row['options_mtm'], 2)
            row['total_mtm'] = round(row['futures_mtm'] + row['options_mtm'], 2)
            scenarios.append(row)
        
        return scenarios


_mtm_calculator = None


def get_mtm_calculator() -> MTMCalculator:
    """Get singleton MTM calculator instance."""
    global _mtm_calculator
    if _mtm_calculator is None:
        _mtm_calculator = MTMCalculator()
    return _mtm_calculator
