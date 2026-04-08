"""
Alert System - Monitor price movements and trigger alerts
"""

from typing import Dict, List


class AlertSystem:
    """Monitor price movements and trigger alerts"""

    def __init__(self):
        self.alerts: List[Dict] = []

    def add_alert(self, stock: str, alert_type: str, threshold: float) -> Dict:
        """Add an alert

        Args:
            stock: Stock symbol
            alert_type: 'price_drop' or 'price_rise'
            threshold: Percentage threshold
        """
        alert = {
            "id": len(self.alerts) + 1,
            "stock": stock,
            "type": alert_type,
            "threshold": threshold,
            "triggered": False,
        }
        self.alerts.append(alert)
        return alert

    def remove_alert(self, alert_id: int) -> bool:
        """Remove an alert by ID"""
        self.alerts = [a for a in self.alerts if a["id"] != alert_id]
        return True

    def check_alerts(self, positions: List[Dict]) -> List[Dict]:
        """Check if any alerts are triggered"""
        triggered = []

        for alert in self.alerts:
            stock = alert["stock"]
            threshold = alert["threshold"]

            # Find position for this stock
            stock_positions = [
                p for p in positions if p.get("stock", "").upper() == stock.upper()
            ]

            for pos in stock_positions:
                ltp = pos.get("ltp", 0)
                buy_avg = pos.get("buy_avg", 0)
                sell_avg = pos.get("sell_avg", 0)

                if buy_avg > 0:
                    change_pct = ((ltp - buy_avg) / buy_avg) * 100
                elif sell_avg > 0:
                    change_pct = ((sell_avg - ltp) / sell_avg) * 100
                else:
                    continue

                if alert["type"] == "price_drop" and change_pct <= -abs(threshold):
                    alert["triggered"] = True
                    triggered.append({**alert, "current_change": round(change_pct, 2)})
                elif alert["type"] == "price_rise" and change_pct >= abs(threshold):
                    alert["triggered"] = True
                    triggered.append({**alert, "current_change": round(change_pct, 2)})

        return triggered

    def get_all_alerts(self) -> List[Dict]:
        """Get all alerts"""
        return self.alerts


_alert_system = None


def get_alert_system() -> AlertSystem:
    """Get singleton alert system instance"""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
    return _alert_system
