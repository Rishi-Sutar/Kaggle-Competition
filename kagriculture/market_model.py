"""
Market Model for Kaggriculture.
Tracks price history, calculates trends, and provides intelligence on when to sell.
"""
from crop_model import CROP_TYPES
from animal_model import ANIMAL_TYPES
from world_state import WorldState
import math

MARKET_I0 = 10000
PRICE_FLOOR = 1
HINGE_GAIN = 8.0

MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "I0": MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base":  35, "I0": MARKET_I0, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base":  60, "I0": MARKET_I0, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base":  50, "I0": MARKET_I0, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

def _shape(func: str, x: float, T: float = None) -> float:
    x = max(0.0, x)
    if func == "linear": return x
    if func == "sq":     return x * x
    if func == "sqrt":   return math.sqrt(x)
    if func == "log":    return math.log(1.0 + x)
    if func == "log10":  return math.log10(1.0 + x)
    if func == "hinge":
        if not T or T <= 0:
            return x
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x

def get_exact_price(item: str, inventory: int) -> int:
    """Exact pricing logic from the environment."""
    if item not in MARKET_PARAMS:
        return PRICE_FLOOR
    p = MARKET_PARAMS[item]
    base = p["base"]
    I0 = p["I0"]
    T = p["T"]
    if inventory < I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, T, T)
        price = base + amp * _shape(f, I0 - inventory, T)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, T, T)
        price = base - amp * _shape(f, inventory - I0, T)
    return max(PRICE_FLOOR, int(round(price)))

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
        self.opp_maturing_soon = {}
        self.opp_mature_now = {}
        
        if world.opp_farm and world.opp_farm.plant_tiles:
            for tile in world.opp_farm.plant_tiles:
                if tile.crop:
                    self.opp_crop_counts[tile.crop] = self.opp_crop_counts.get(tile.crop, 0) + 1
                    
                    info = CROP_TYPES.get(tile.crop)
                    if info:
                        days_planted = world.day - tile.planted_day
                        days_until_mature = info.first_yield_day - days_planted
                        
                        if tile.ready_to_harvest:
                            self.opp_mature_now[tile.crop] = self.opp_mature_now.get(tile.crop, 0) + 1
                        elif 0 < days_until_mature <= 2:
                            self.opp_maturing_soon[tile.crop] = self.opp_maturing_soon.get(tile.crop, 0) + 1

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

    def predict_price_at_maturity(self, crop: str, town_model) -> int:
        """
        Predicts the market price of a crop when it reaches maturity.
        Considers current inventory, exact town consumption, and opponent's impending harvests.
        """
        info = CROP_TYPES.get(crop)
        if not info:
            return 0
            
        current_inv = self.inventory_history.get(crop, [10000])[-1]
        
        # Exact autonomous consumption based on currently unlocked shops
        # We assume daily_demand units per day is consumed until maturity.
        days_to_mature = info.first_yield_day
        daily_demand = town_model.get_daily_demand(crop)
        consumption = days_to_mature * daily_demand
        
        # Add opponent's impending harvest to future inventory
        opp_harvest_estimate = self.opp_crop_counts.get(crop, 0) * info.peak_unfertilized_yield
        
        projected_inv = current_inv - consumption + opp_harvest_estimate
        
        # Use exact price equation
        return get_exact_price(crop, projected_inv)

    def should_sell(self, item: str, amount_held: int, current_price: int, current_day: int, total_shed_items: int, is_endgame: bool = False) -> int:
        """
        Smart sell rule (Phase 9/11): Predatory Dumping.
        Hoards items as the price rises from autonomous town demand.
        Dumps items massively right before or right as the opponent's crops mature to crash their profits.
        """
        if amount_held == 0:
            return 0
            
        if is_endgame:
            return amount_held

        if current_price <= 5:
            return 0
            
        trend = self.get_price_trend(item, window=10)
        
        # Check opponent sabotage logic for crops
        if item in CROP_TYPES:
            mature_now = self.opp_mature_now.get(item, 0)
            maturing_soon = self.opp_maturing_soon.get(item, 0)
            
            # If they have a large batch maturing soon, HOLD to let price rise further
            if maturing_soon >= 3 and mature_now == 0 and total_shed_items < 80:
                return 0
                
            # If their large batch just reached maturity, DUMP EVERYTHING NOW to beat them to the market
            if mature_now >= 3:
                return amount_held
        
        # Default behavior: If trend is highly positive, HOLD to wait for peak unless shed is full
        if trend > 2.0 and total_shed_items < 80:
            return 0
            
        # Otherwise, sell immediately to lock in profits
        return amount_held
