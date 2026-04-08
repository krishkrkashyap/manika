"""
Margin Calculator - Match Excel formula exactly:
Excel Formula: =IF(RIGHT(I2,1)="E", BE*12000/10000000, BE*1500/10000000)
Where BE = trade amount (buy_amt + sell_amt)

For our positions (net_qty, buy_avg, sell_avg):
- Long (net_qty > 0): amount = net_qty * buy_avg
- Short (net_qty < 0): amount = abs(net_qty) * sell_avg
"""

from typing import Dict, List
from app.core import config


class MarginCalculator:
    """Calculate margin requirements matching Excel formula."""

    # Excel formula constants
    FUTURE_MARGIN_RATE = 12000 / 10000000  # 0.0012 (0.12%)
    OPTION_MARGIN_RATE = 1500 / 10000000  # 0.00015 (0.015%)

    def calculate_trade_amount(self, pos: Dict) -> float:
        """Calculate trade amount for a position.

        Excel BE column = Buy Amount + Sell Amount
        For our data:
        - Long position (net_qty > 0): amount = net_qty * buy_avg
        - Short position (net_qty < 0): amount = abs(net_qty) * sell_avg
        """
        net_qty = pos.get("net_qty", 0)
        buy_avg = pos.get("buy_avg", 0)
        sell_avg = pos.get("sell_avg", 0)

        if net_qty > 0:
            # Long - use buy average
            return net_qty * buy_avg
        elif net_qty < 0:
            # Short - use sell average
            return abs(net_qty) * sell_avg
        return 0.0

    def calculate_position_margin(self, pos: Dict) -> float:
        """Calculate margin for a position using Excel formula.

        Formula: IF(symbol ends with "E", trade_amount * 0.0012, trade_amount * 0.00015)
        """
        symbol = pos.get("symbol", "")
        amount = self.calculate_trade_amount(pos)

        if amount <= 0:
            return 0.0

        # Check if futures (symbol ends with 'E')
        is_futures = symbol.upper().endswith("E") if symbol else False

        if is_futures:
            return amount * self.FUTURE_MARGIN_RATE
        else:
            return amount * self.OPTION_MARGIN_RATE

    def calculate_total_margin(self, positions: List[Dict], quotes: Dict) -> Dict:
        """Calculate total margin for all positions matching Excel."""
        futures_margin = 0.0
        options_margin = 0.0
        breakdown = []

        for pos in positions:
            symbol = pos.get("symbol", "")
            net_qty = pos.get("net_qty", 0)

            # Calculate trade amount
            amount = self.calculate_trade_amount(pos)
            margin = self.calculate_position_margin(pos)

            is_futures = symbol.upper().endswith("E") if symbol else False

            if is_futures:
                futures_margin += margin
            else:
                options_margin += margin

            breakdown.append(
                {
                    "stock": pos.get("stock", ""),
                    "symbol": symbol,
                    "type": "FUT" if is_futures else "OPT",
                    "net_qty": net_qty,
                    "trade_amount": round(amount, 2),
                    "margin": round(margin, 2),
                }
            )

        return {
            "total_margin": round(futures_margin + options_margin, 2),
            "futures_margin": round(futures_margin, 2),
            "options_margin": round(options_margin, 2),
            "breakdown": breakdown,
        }

    def calculate_order_margin(
        self,
        symbol: str,
        quantity: int,
        price: float,
        product_type: str = "MIS",
        exchange: str = "NSEFO",
    ) -> Dict:
        """Calculate margin for a new order using Excel formula."""
        if quantity == 0:
            return {
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "product_type": product_type,
                "required_margin": 0,
                "leverage": 0,
            }

        # Calculate trade amount
        trade_amount = abs(quantity) * price

        # Check instrument type
        is_futures = symbol.upper().endswith("E") if symbol else False

        if is_futures:
            margin = trade_amount * self.FUTURE_MARGIN_RATE
        else:
            margin = trade_amount * self.OPTION_MARGIN_RATE

        return {
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "product_type": product_type,
            "exchange": exchange,
            "trade_amount": round(trade_amount, 2),
            "required_margin": round(margin, 2),
            "leverage": round(trade_amount / margin, 2) if margin > 0 else 0,
        }


def calculate_total_margin(positions: List[Dict], quotes: Dict) -> Dict:
    """Convenience function."""
    calc = MarginCalculator()
    return calc.calculate_total_margin(positions, quotes)
