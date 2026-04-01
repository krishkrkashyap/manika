"""
Watchlist Manager - Manage watchlist with price alerts.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from config.settings import DATA_DIR
from .demo_data import DEMO_WATCHLIST


class WatchlistManager:
    """Manages watchlist and price alerts."""
    
    def __init__(self):
        self.watchlist_file = DATA_DIR / "watchlist.json"
        self.alerts_history_file = DATA_DIR / "alerts_history.json"
        self._watchlist = []
        self._alerts_history = []
        self._load_data()
    
    def _load_data(self):
        """Load watchlist and alerts from files or demo data."""
        if self.watchlist_file.exists():
            with open(self.watchlist_file, 'r') as f:
                self._watchlist = json.load(f)
        else:
            self._watchlist = DEMO_WATCHLIST
        
        if self.alerts_history_file.exists():
            with open(self.alerts_history_file, 'r') as f:
                self._alerts_history = json.load(f)
    
    def save_watchlist(self):
        """Save watchlist to file."""
        with open(self.watchlist_file, 'w') as f:
            json.dump(self._watchlist, f, indent=2)
    
    def save_alerts_history(self):
        """Save alerts history to file."""
        with open(self.alerts_history_file, 'w') as f:
            json.dump(self._alerts_history, f, indent=2, default=str)
    
    def get_watchlist(self) -> List[Dict]:
        """Get current watchlist."""
        return self._watchlist
    
    def add_to_watchlist(self, symbol: str, exchange: str, target_price: float, alert_type: str) -> bool:
        """Add symbol to watchlist."""
        for item in self._watchlist:
            if item['symbol'] == symbol:
                return False
        
        self._watchlist.append({
            'symbol': symbol,
            'exchange': exchange,
            'target_price': target_price,
            'alert_type': alert_type,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.save_watchlist()
        return True
    
    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove symbol from watchlist."""
        for i, item in enumerate(self._watchlist):
            if item['symbol'] == symbol:
                self._watchlist.pop(i)
                self.save_watchlist()
                return True
        return False
    
    def update_watchlist_item(self, symbol: str, target_price: float = None, alert_type: str = None) -> bool:
        """Update watchlist item."""
        for item in self._watchlist:
            if item['symbol'] == symbol:
                if target_price is not None:
                    item['target_price'] = target_price
                if alert_type is not None:
                    item['alert_type'] = alert_type
                self.save_watchlist()
                return True
        return False
    
    def check_alerts(self, quotes: Dict) -> List[Dict]:
        """Check for price alerts triggered."""
        triggered_alerts = []
        
        for item in self._watchlist:
            symbol = item['symbol']
            target_price = item['target_price']
            alert_type = item['alert_type']
            
            if symbol in quotes:
                current_price = quotes[symbol].get('ltp')
                if current_price is None:
                    continue
                
                triggered = False
                if alert_type == 'cross_above' and current_price >= target_price:
                    triggered = True
                elif alert_type == 'cross_below' and current_price <= target_price:
                    triggered = True
                
                if triggered:
                    alert = {
                        'symbol': symbol,
                        'target_price': target_price,
                        'current_price': current_price,
                        'alert_type': alert_type,
                        'triggered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    triggered_alerts.append(alert)
                    self._alerts_history.append(alert)
        
        if triggered_alerts:
            self.save_alerts_history()
        
        return triggered_alerts
    
    def get_alerts_history(self) -> List[Dict]:
        """Get alerts history."""
        return self._alerts_history
    
    def clear_alerts_history(self):
        """Clear alerts history."""
        self._alerts_history = []
        self.save_alerts_history()


_watchlist_manager = None


def get_watchlist_manager() -> WatchlistManager:
    """Get singleton watchlist manager instance."""
    global _watchlist_manager
    if _watchlist_manager is None:
        _watchlist_manager = WatchlistManager()
    return _watchlist_manager
