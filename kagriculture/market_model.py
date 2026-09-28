"""
Market Model for Kaggriculture.
Tracks price history, calculates trends, and provides intelligence on when to sell.
"""
from crop_model import CROP_TYPES, crop_profitability
from animal_model import ANIMAL_TYPES
from world_state import WorldState

class MarketTracker:
    def __init__(self):
        # Maps item name -> list of prices over the steps observed
        self.price_history: Dict[str, List[int]] = {}
        # Maps item name -> list of inventory counts over the steps observed
        self.inventory_history: Dict[str, List[int]] = {}
        # Maps crop name -> number of planted tiles by opponent
        self.opp_crop_counts: Dict[str, int] = {}
        
    def update(self, world: WorldState) -> None:
        """
        Called every step with the latest market state and world state.
        """
        current_prices = world.market.prices
        current_inventory = world.market.inventory
        
        for item, price in current_prices.items():
            if item not in self.price_history:
                self.price_history[item] = []
            self.price_history[item].append(price)
            
        for item, inv in current_inventory.items():
            if item not in self.inventory_history:
                self.inventory_history[item] = []
            self.inventory_history[item].append(inv)
            
        # Track opponent crops
        self.opp_crop_counts = {}
        
        if world.opp_farm and world.opp_farm.plant_tiles:
            for tile in world.opp_farm.plant_tiles:
                if tile.crop:
                    self.opp_crop_counts[tile.crop] = self.opp_crop_counts.get(tile.crop, 0) + 1

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

    def predict_price_at_maturity(self, item_name: str) -> int:
        """
        Predicts the market price of an item when a newly bought one reaches maturity.
        """
        # If it's a crop
        info = CROP_TYPES.get(item_name)
        if info:
            base_price = info.base_sell_price
            days_to_mature = info.first_yield_day
            yield_est = info.peak_unfertilized_yield
            opp_harvest_estimate = self.opp_crop_counts.get(item_name, 0) * yield_est
        else:
            # Maybe it's an animal product (EGG, MILK, WOOL)
            # Find the animal that produces this
            animal_info = next((a for a in ANIMAL_TYPES.values() if a.product == item_name), None)
            if not animal_info:
                return 0
            base_price = animal_info.base_product_price
            days_to_mature = animal_info.first_yield_day
            opp_harvest_estimate = 0 # Animals produce steadily, less shock to market
            
        current_price = self.price_history.get(item_name, [base_price])[-1]
        current_inv = self.inventory_history.get(item_name, [10000])[-1]
        
        consumption = days_to_mature * 10 
        
        projected_inv = current_inv - consumption + opp_harvest_estimate
        
        baseline_inv = 10000
        inv_diff = projected_inv - baseline_inv
        price_modifier = 1.0 - (inv_diff / 10000.0) 
        price_modifier = max(0.1, min(price_modifier, 5.0)) 
        
        predicted = int(base_price * price_modifier)
        return max(5, predicted)
        
    def predict_price_tomorrow(self, item_name: str, opp_harvests_tomorrow: int = 0) -> int:
        """
        Predicts the price exactly for tomorrow, incorporating specific known opponent harvests.
        """
        info = CROP_TYPES.get(item_name)
        base_price = info.base_sell_price if info else 100
        
        # If it's an animal product
        if not info:
            animal_info = next((a for a in ANIMAL_TYPES.values() if a.product == item_name), None)
            if animal_info:
                base_price = animal_info.base_product_price
                
        current_inv = self.inventory_history.get(item_name, [10000])[-1]
        
        # Tomorrow means 1 day of consumption
        consumption = 10
        projected_inv = current_inv - consumption + opp_harvests_tomorrow
        
        baseline_inv = 10000
        inv_diff = projected_inv - baseline_inv
        price_modifier = 1.0 - (inv_diff / 10000.0) 
        price_modifier = max(0.1, min(price_modifier, 5.0)) 
        
        predicted = int(base_price * price_modifier)
        return max(5, predicted)

    def should_sell(self, item: str, amount_held: int, current_price: int, current_day: int, total_shed_items: int, is_endgame: bool = False) -> int:
        """
        Smart sell rule: Phase 12 removes hoarding to avoid crashing our own markets.
        We sell immediately at the end of the day unless price is surging rapidly.
        """
        if amount_held == 0:
            return 0
            
        if is_endgame:
            return amount_held

        if current_price <= 5:
            return 0
            
        trend = self.get_price_trend(item, window=10)
        
        # If trend is highly positive (price is surging), HOLD to wait for peak
        # unless shed is full
        if trend > 2.0 and total_shed_items < 80:
            return 0
            
        # Otherwise, sell immediately to lock in profits before the opponent crashes the market
        return amount_held
