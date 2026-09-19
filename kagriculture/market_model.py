"""
Market Model for Kaggriculture.
Tracks price history, calculates trends, and provides intelligence on when to sell.
"""
from typing import Dict, List, Optional
from crop_model import CROP_TYPES, crop_profitability

class MarketTracker:
    def __init__(self):
        # Maps item name -> list of prices over the steps observed
        self.price_history: Dict[str, List[int]] = {}
        # Maps item name -> list of inventory counts over the steps observed
        self.inventory_history: Dict[str, List[int]] = {}
        
    def update(self, current_prices: Dict[str, int], current_inventory: Dict[str, int]) -> None:
        """
        Called every step with the latest market state.
        """
        for item, price in current_prices.items():
            if item not in self.price_history:
                self.price_history[item] = []
            self.price_history[item].append(price)
            
        for item, inv in current_inventory.items():
            if item not in self.inventory_history:
                self.inventory_history[item] = []
            self.inventory_history[item].append(inv)
            
    def get_price_trend(self, item: str, window: int = 5) -> float:
        """
        Returns the average change in price over the last `window` steps.
        Positive = price is rising, Negative = price is dropping.
        """
        history = self.price_history.get(item, [])
        if len(history) < 2:
            return 0.0
            
        actual_window = min(window, len(history))
        recent_prices = history[-actual_window:]
        
        # Simple slope calculation (End - Start) / Length
        diff = recent_prices[-1] - recent_prices[0]
        return diff / (actual_window - 1) if actual_window > 1 else 0.0

    def should_sell(self, item: str, amount_held: int, current_price: int) -> int:
        """
        Determines how many units to sell this turn.
        Avoids crashing the market if we hold a large quantity.
        """
        if amount_held == 0:
            return 0
            
        trend = self.get_price_trend(item, window=10)
        
        # If price is at or near the floor ($1), HODL unless we need money
        if current_price <= 5:
            # We could sell 1 to see if we can push it up, or just hold
            return 0
            
        # If price is rapidly dropping, panic sell a larger chunk!
        if trend < -2.0:
            return min(amount_held, 5)
            
        # If price is rising, hold or sell slowly
        if trend > 0.5:
            return 1
            
        # Steady market: sell in moderate batches
        return min(amount_held, 3)

    def best_crop_to_plant(self, current_prices: Dict[str, int], money: float) -> Optional[str]:
        """
        Calculates the best crop to plant based on current market profitability.
        """
        best_crop = None
        best_roi = -999.0
        
        for crop_name, info in CROP_TYPES.items():
            # Only consider crops we can afford the seeds for
            if money >= info.seed_cost:
                price = current_prices.get(crop_name, info.base_sell_price)
                roi = crop_profitability(crop_name, price)
                
                if roi > best_roi:
                    best_roi = roi
                    best_crop = crop_name
                    
        return best_crop
