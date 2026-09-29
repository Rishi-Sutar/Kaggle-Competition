from typing import Dict, List
from world_state import WorldState

SHOPS = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

TOWN_CENTER_PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]

class TownModel:
    def __init__(self):
        self.daily_demand: Dict[str, int] = {}
        self.shop_interval = 4  # hours
        self.center_interval = 24 # hours

    def update(self, world: WorldState):
        """
        Calculates exact daily autonomous demand based on currently unlocked shops and town center.
        """
        demand = {item: 0 for item in TOWN_CENTER_PRODUCTS}
        
        # Town center consumes 1 unit per day (at hour 0)
        for item in TOWN_CENTER_PRODUCTS:
            demand[item] += 1
            
        # Shops consume every 4 hours (6 times a day)
        shops = world.town.unlocked_shops
        times_per_day = self.center_interval // self.shop_interval
        
        for shop_name in shops:
            if shop_name not in SHOPS:
                continue
            products = SHOPS[shop_name]
            multiplier = 2 if len(products) == 1 else 1
            
            for item in products:
                if item in demand:
                    demand[item] += multiplier * times_per_day
                    
        self.daily_demand = demand

    def get_daily_demand(self, product: str) -> int:
        """Returns the total number of units of this product consumed by the town per day."""
        return self.daily_demand.get(product, 0)

    def get_demand_forecast(self, product: str, days_ahead: int) -> int:
        """
        Returns the total expected consumption over the next `days_ahead`.
        Does not try to predict future shop unlocks, just extrapolates current demand.
        """
        return self.get_daily_demand(product) * days_ahead
