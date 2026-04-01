"""
Alerts System - Price alerts and notifications.
"""
from typing import Dict, List, Optional
from datetime import datetime
from config.settings import DEFAULT_ALERT_THRESHOLDS


class AlertSystem:
    """System for managing price alerts and notifications."""
    
    def __init__(self):
        self.thresholds = DEFAULT_ALERT_THRESHOLDS.copy()
        self.active_alerts = []
        self.triggered_today = []
    
    def check_price_alert(self, symbol: str, current_price: float, 
                         target_price: float, alert_type: str) -> Optional[Dict]:
        """Check if price alert is triggered.
        
        Args:
            symbol: Trading symbol
            current_price: Current LTP
            target_price: Target price to trigger alert
            alert_type: 'cross_above' or 'cross_below'
            
        Returns:
            Alert dict if triggered, None otherwise
        """
        triggered = False
        
        if alert_type == 'cross_above' and current_price >= target_price:
            triggered = True
        elif alert_type == 'cross_below' and current_price <= target_price:
            triggered = True
        
        if triggered:
            alert = {
                'symbol': symbol,
                'current_price': current_price,
                'target_price': target_price,
                'alert_type': alert_type,
                'triggered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'PRICE_ALERT'
            }
            self.triggered_today.append(alert)
            return alert
        
        return None
    
    def check_percentage_alert(self, symbol: str, current_price: float, 
                              close_price: float) -> List[Dict]:
        """Check for percentage-based alerts (like in Excel -2.5%, -5%, etc).
        
        Args:
            symbol: Trading symbol
            current_price: Current LTP
            close_price: Previous close price
            
        Returns:
            List of triggered alerts
        """
        if close_price <= 0:
            return []
        
        change_pct = ((current_price - close_price) / close_price) * 100
        alerts = []
        
        threshold_map = {
            'price_drop_2_5_percent': -2.5,
            'price_drop_5_percent': -5.0,
            'price_drop_10_percent': -10.0,
            'price_rise_2_5_percent': 2.5,
            'price_rise_5_percent': 5.0,
            'price_rise_10_percent': 10.0,
        }
        
        for name, threshold in threshold_map.items():
            if threshold < 0 and change_pct <= threshold:
                alert = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'close_price': close_price,
                    'change_pct': round(change_pct, 2),
                    'threshold': threshold,
                    'alert_name': name,
                    'triggered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'PERCENTAGE_ALERT'
                }
                alerts.append(alert)
                self.triggered_today.append(alert)
            elif threshold > 0 and change_pct >= threshold:
                alert = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'close_price': close_price,
                    'change_pct': round(change_pct, 2),
                    'threshold': threshold,
                    'alert_name': name,
                    'triggered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'PERCENTAGE_ALERT'
                }
                alerts.append(alert)
                self.triggered_today.append(alert)
        
        return alerts
    
    def check_all_positions_alerts(self, positions: Dict, quotes: Dict) -> List[Dict]:
        """Check alerts for all positions.
        
        Args:
            positions: Dict of all positions
            quotes: Dict of current quotes
            
        Returns:
            List of all triggered alerts
        """
        all_alerts = []
        
        for stock, data in positions.items():
            fut = data.get('futures', {})
            if fut.get('net_qty', 0) != 0:
                symbol = fut.get('symbol')
                if symbol in quotes:
                    quote = quotes[symbol]
                    alerts = self.check_percentage_alert(
                        symbol, 
                        quote.get('ltp', 0),
                        quote.get('close', 0)
                    )
                    all_alerts.extend(alerts)
            
            for opt in data.get('options', []):
                if opt.get('net_qty', 0) != 0:
                    symbol = opt.get('symbol')
                    if symbol in quotes:
                        quote = quotes[symbol]
                        alerts = self.check_percentage_alert(
                            symbol,
                            quote.get('ltp', 0),
                            quote.get('close', 0)
                        )
                        all_alerts.extend(alerts)
        
        return all_alerts
    
    def get_triggered_alerts(self) -> List[Dict]:
        """Get all triggered alerts for today."""
        return self.triggered_today
    
    def clear_triggered_alerts(self):
        """Clear triggered alerts list."""
        self.triggered_today = []
    
    def set_threshold(self, name: str, value: float):
        """Update alert threshold."""
        self.thresholds[name] = value
    
    def get_thresholds(self) -> Dict:
        """Get current thresholds."""
        return self.thresholds.copy()


_alert_system = None


def get_alert_system() -> AlertSystem:
    """Get singleton alert system instance."""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
    return _alert_system
