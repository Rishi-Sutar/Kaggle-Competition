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
        Simple sell rule: sell everything if price is above floor ($5).
        Against competition agents, market prices rarely recover — holding is costly.
        """
        if amount_held == 0:
            return 0
        # At the price floor, hold and let the market recover naturally
        if current_price <= 5:
            return 0
        # Otherwise sell all of it — never hold against a competing agent
        return amount_held

    def best_crop_to_plant(self, current_prices: Dict[str, int], money: float, market_inventory: Dict[str, int] = None) -> Optional[str]:
        """
        Calculates the best crop to plant based on current market ROI and scarcity.
        Prefers crops with low market inventory (less flooded = better price sustainability).
        """
        best_crop = None
        best_score = -999.0
        
        for crop_name, info in CROP_TYPES.items():
            if money >= info.seed_cost:
                price = current_prices.get(crop_name, info.base_sell_price)
                roi = crop_profitability(crop_name, price)
                
                # Scarcity bonus: prefer crops with low market inventory
                scarcity_bonus = 0.0
                if market_inventory:
                    inv = market_inventory.get(crop_name, 10000)
                    # Penalize saturated crops (high inventory = low future price)
                    if inv > 5000:
                        scarcity_bonus = -0.5  # heavily penalize saturated market
                    elif inv < 1000:
                        scarcity_bonus = 0.3   # bonus for scarce crops
                
                score = roi + scarcity_bonus
                if score > best_score:
                    best_score = score
                    best_crop = crop_name
                    
        return best_crop
