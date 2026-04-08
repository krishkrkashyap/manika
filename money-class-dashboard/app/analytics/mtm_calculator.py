"""
MTM Calculator - Calculate Mark to Market profits/losses
"""

from typing import Dict, List
from app.core import config


class MTMCalculator:
    """Calculate MTM for positions."""

    def __init__(self):
        self.scenario_percentages = config.MTM_SCENARIO_PERCENTAGES

    def calculate_last_mtm(
        self, position: Dict, current_close: float, yesterday_close: float
    ) -> float:
        """LAST MTM: (today's close - yesterday's close) * qty"""
        net_qty = position.get("net_qty", 0)
        if net_qty == 0:
            return 0.0
        if net_qty > 0:
            return (current_close - yesterday_close) * net_qty
        else:
            return (yesterday_close - current_close) * abs(net_qty)

    def calculate_intra_mtm(
        self, position: Dict, ltp: float, today_open: float
    ) -> float:
        """INTRA MTM: (ltp - today_open) * qty"""
        net_qty = position.get("net_qty", 0)
        if net_qty == 0:
            return 0.0
        if net_qty > 0:
            return (ltp - today_open) * net_qty
        else:
            return (today_open - ltp) * abs(net_qty)

    def calculate_exp_mtm(self, position: Dict, ltp: float) -> float:
        """EXP MTM: (ltp - entry_price) * qty (uses entry price, NOT last close)"""
        net_qty = position.get("net_qty", 0)
        buy_avg = position.get("buy_avg", 0)
        sell_avg = position.get("sell_avg", 0)
        if net_qty == 0:
            return 0.0
        if net_qty > 0:
            entry = buy_avg if buy_avg > 0 else sell_avg
            return (ltp - entry) * net_qty
        else:
            entry = sell_avg if sell_avg > 0 else buy_avg
            return (entry - ltp) * abs(net_qty)

    def calculate_position_mtm(self, position: Dict, current_price: float) -> Dict:
        """Calculate MTM for a single position."""
        net_qty = position.get("net_qty", 0)
        buy_avg = position.get("buy_avg", 0)
        sell_avg = position.get("sell_avg", 0)

        if net_qty > 0:
            avg_price = buy_avg if buy_avg > 0 else sell_avg
            mtm = (current_price - avg_price) * net_qty
        elif net_qty < 0:
            avg_price = sell_avg if sell_avg > 0 else buy_avg
            mtm = (avg_price - current_price) * abs(net_qty)
        else:
            mtm = 0.0

        return {"mtm": round(mtm, 2), "current_price": current_price}

    def calculate_all_mtm(self, positions: List[Dict], quotes: Dict) -> Dict:
        """Return all MTM types: LAST, INTRA, EXP"""
        last_total = 0.0
        intra_total = 0.0
        exp_total = 0.0
        positions_mtm = []

        for pos in positions:
            # Get prices - use entry price for EXP
            ltp = pos.get("ltp", 0)
            yesterday_close = pos.get("yesterday_close", ltp)
            today_open = pos.get("open", ltp)

            # For demo data: use buy_avg/sell_avg as entry price
            buy_avg = pos.get("buy_avg", 0)
            sell_avg = pos.get("sell_avg", 0)

            # Calculate all MTM types
            last_mtm = self.calculate_last_mtm(pos, ltp, yesterday_close)
            intra_mtm = self.calculate_intra_mtm(pos, ltp, today_open)
            exp_mtm = self.calculate_exp_mtm(pos, ltp)

            positions_mtm.append(
                {
                    "stock": pos.get("stock", ""),
                    "symbol": pos.get("symbol", ""),
                    "type": pos.get("type", ""),
                    "net_qty": pos.get("net_qty", 0),
                    "ltp": ltp,
                    "last_mtm": round(last_mtm, 2),
                    "intra_mtm": round(intra_mtm, 2),
                    "exp_mtm": round(exp_mtm, 2),
                }
            )

            last_total += last_mtm
            intra_total += intra_mtm
            exp_total += exp_mtm

        return {
            "last_total": round(last_total, 2),
            "intra_total": round(intra_total, 2),
            "exp_total": round(exp_total, 2),
            "positions": positions_mtm,
        }

    def generate_scenario_table(
        self, positions: List[Dict], quotes: Dict
    ) -> List[Dict]:
        """Generate MTM scenario table."""
        scenarios = []

        for pct in self.scenario_percentages:
            scenario_total = 0.0

            for pos in positions:
                symbol = pos.get("symbol", "")
                close = pos.get("close", pos.get("buy_avg", 100))
                quote = quotes.get(symbol, {})
                if quote:
                    close = quote.get("close", close)

                if close > 0:
                    scenario_price = close * (1 + pct)
                    mtm_data = self.calculate_position_mtm(pos, scenario_price)
                    scenario_total += mtm_data["mtm"]

            scenarios.append(
                {
                    "percentage": f"{pct * 100:.1f}%",
                    "pct_value": pct,
                    "total_mtm": round(scenario_total, 2),
                }
            )

        return scenarios

    def generate_stock_scenario_table(
        self, stock: str, data: Dict, quotes: Dict
    ) -> List[Dict]:
        """Generate per-stock scenario with futures, options, total breakdown"""
        scenarios = []

        for pct in self.scenario_percentages:
            row = {
                "percentage": f"{pct * 100:+.1f}%",
                "pct_value": pct,
                "futures_mtm": 0.0,
                "options_mtm": 0.0,
                "total_mtm": 0.0,
            }

            # Get the position for this stock
            fut = data.get("futures", {})
            options = data.get("options", [])

            # Futures scenario
            if fut.get("net_qty", 0) != 0:
                close = quotes.get(fut.get("symbol"), {}).get(
                    "close", fut.get("buy_avg", 0)
                )
                if close > 0:
                    scenario_price = close * (1 + pct)
                    mtm_data = self.calculate_position_mtm(fut, scenario_price)
                    row["futures_mtm"] = mtm_data["mtm"]

            # Options scenario - combine PE and CE
            for opt in options:
                if opt.get("net_qty", 0) != 0:
                    close = quotes.get(opt.get("symbol"), {}).get(
                        "close", opt.get("sell_avg", 0)
                    )
                    if close > 0:
                        scenario_price = close * (1 + pct)
                        mtm_data = self.calculate_position_mtm(opt, scenario_price)
                        row["options_mtm"] += mtm_data["mtm"]

            row["total_mtm"] = round(row["futures_mtm"] + row["options_mtm"], 2)
            scenarios.append(row)

        return scenarios

    def generate_all_stock_scenarios(self, positions: Dict, quotes: Dict) -> Dict:
        """Generate scenarios for all stocks with per-stock breakdown"""
        stock_scenarios = {}

        for stock, data in positions.items():
            stock_scenarios[stock] = self.generate_stock_scenario_table(
                stock, data, quotes
            )

        return stock_scenarios


def calculate_all_mtm(positions: List[Dict], quotes: Dict) -> Dict:
    """Convenience function."""
    calc = MTMCalculator()
    return calc.calculate_all_mtm(positions, quotes)


def generate_scenario_table(positions: List[Dict], quotes: Dict) -> List[Dict]:
    """Convenience function."""
    calc = MTMCalculator()
    return calc.generate_scenario_table(positions, quotes)


def generate_all_stock_scenarios(positions: Dict, quotes: Dict) -> Dict:
    """Convenience function for per-stock scenarios."""
    calc = MTMCalculator()
    return calc.generate_all_stock_scenarios(positions, quotes)
