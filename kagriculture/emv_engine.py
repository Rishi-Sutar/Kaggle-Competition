"""
Expected Marginal Value (EMV) Engine
Dynamically calculates the ROI of every possible investment per tile.
"""
from typing import Dict, List, Tuple
from crop_model import CROP_TYPES
from animal_model import ANIMAL_TYPES
from market_model import MarketTracker
from world_state import WorldState

# Estimated average cost of a worker action (assuming ~5 workers hired for $12 total)
# 5 workers * 24 actions = 120 actions for $12. So $0.10 per action.
# Let's conservatively say $1 per daily maintenance action.
LABOR_COST_PER_DAY = 1.0
WHEAT_FEED_COST = 25.0 # Assuming market price for wheat

def get_operational_buffer(world: WorldState, private_state: dict) -> float:
    """
    Calculates the absolute minimum cash needed to survive tomorrow.
    Includes feed for all current animals and basic worker hiring.
    """
    # Count current animals
    num_animals = len(world.my_farm.structure_tiles) + sum(
        private_state.get(a, 0) for a in ["GOOSE", "COW", "SHEEP"]
    )
    
    # We need to feed them. Assume wheat cost is ~25.
    feed_cost = num_animals * WHEAT_FEED_COST
    
    # We need workers to feed/water. Assume we hire at least 3 workers (cost: 1+1+2 = 4)
    worker_cost = 4
    
    return float(feed_cost + worker_cost)


def calculate_crop_emv(crop_name: str, current_day: int, tracker: MarketTracker) -> float:
    """
    Calculates the total expected profit of planting a crop today until Day 30.
    """
    info = CROP_TYPES.get(crop_name)
    if not info:
        return -9999.0
        
    days_left = 30 - current_day
    if days_left <= info.first_yield_day:
        return -9999.0 # Won't even reach first harvest
        
    predicted_price = tracker.predict_price_at_maturity(crop_name)
    
    if info.nature == "ONE-TIME":
        # Check if we can reach peak yield
        if days_left <= info.max_yield_day:
            # We can harvest, but maybe not at peak. Assume base yield of 1-3.
            # We'll conservatively say it's not worth it if it doesn't reach peak.
            if days_left <= info.first_yield_day:
                return -9999.0
            yield_amount = 1
        else:
            yield_amount = info.peak_unfertilized_yield
            
        revenue = predicted_price * yield_amount
        labor_cost = LABOR_COST_PER_DAY * info.max_yield_day
        profit = revenue - info.seed_cost - labor_cost
        
    else: # ONGOING (Tomato, Strawberry)
        # Calculate how many yields we can get before Day 30
        yields_possible = 0
        day_pointer = info.first_yield_day
        interval = 2 if crop_name == "STRAWBERRY" else 1 # Strawberry every other day, Tomato every day
        
        while day_pointer < days_left and yields_possible < info.peak_unfertilized_yield:
            yields_possible += 1
            day_pointer += interval
            
        revenue = predicted_price * yields_possible
        labor_cost = LABOR_COST_PER_DAY * day_pointer
        profit = revenue - info.seed_cost - labor_cost
        
    return profit


def calculate_animal_emv(animal_name: str, current_day: int, tracker: MarketTracker) -> float:
    """
    Calculates the total expected profit of buying an animal today until Day 30.
    """
    info = ANIMAL_TYPES.get(animal_name)
    if not info:
        return -9999.0
        
    days_left = 30 - current_day
    if days_left <= info.first_yield_day:
        return -9999.0 # Won't even reach first yield
        
    predicted_price = tracker.predict_price_at_maturity(info.product)
    
    # Calculate total yields before day 30
    yields_possible = max(0, (days_left - info.first_yield_day) // info.yield_interval + 1)
    revenue = predicted_price * yields_possible
    
    feed_cost = WHEAT_FEED_COST * days_left
    labor_cost = LABOR_COST_PER_DAY * days_left
    
    profit = revenue - info.cost - feed_cost - labor_cost
    return profit


def get_best_investments(world: WorldState, tracker: MarketTracker, private_state: dict) -> List[Tuple[str, str, float]]:
    """
    Evaluates all options and returns a list of (Type, Name, ROI) sorted by ROI descending.
    Type is 'CROP' or 'ANIMAL'.
    ROI is expected_profit / investment_cost.
    """
    options = []
    
    # Evaluate Crops
    for crop_name, info in CROP_TYPES.items():
        emv = calculate_crop_emv(crop_name, world.day, tracker)
        if emv > 0:
            roi = emv / info.seed_cost
            options.append(("CROP", crop_name, roi))
            
    # Evaluate Animals
    for animal_name, info in ANIMAL_TYPES.items():
        emv = calculate_animal_emv(animal_name, world.day, tracker)
        if emv > 0:
            roi = emv / info.cost
            options.append(("ANIMAL", animal_name, roi))
            
    # Sort by ROI descending
    options.sort(key=lambda x: x[2], reverse=True)
    return options
