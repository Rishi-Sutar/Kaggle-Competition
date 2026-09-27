"""
Expected Marginal Value (EMV) Engine — Phase 13: Internal Supply Chain & Land Expansion
Dynamically calculates the absolute profit of every possible investment per tile.
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
WHEAT_FEED_COST = 2.5 # Internal supply chain cost (10 seed / 4 yield)

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


def calculate_land_emv(current_day: int, tracker: MarketTracker) -> float:
    """
    Calculates the EMV of buying one new quadrant (25 tiles at $1000 cost).
    The logic: each new tile can be filled with the best available investment.
    We approximate by multiplying the top-ranked animal EMV by 25 tiles,
    discounted to account for the time it takes to build structures and place animals.
    If days left are too few to recoup the $1000, returns negative.
    """
    LAND_COST = 1000
    QUADRANT_TILES = 25
    days_left = 30 - current_day

    # Not worth buying land if we can't populate and recoup in time
    if days_left < 10:
        return -9999.0

    # What's the best per-tile EMV available right now?
    # We use Cow EMV as a proxy since cows are the primary animal we'd fill tiles with
    best_cow_emv = calculate_animal_emv("COW", current_day, tracker)
    best_sheep_emv = calculate_animal_emv("SHEEP", current_day, tracker)
    best_animal_emv = max(best_cow_emv, best_sheep_emv, 0)

    # Assume we can profitably fill ~60% of the quadrant (structure build time + movement)
    effective_tiles = QUADRANT_TILES * 0.60
    projected_profit = best_animal_emv * effective_tiles

    # Deduct land cost
    return projected_profit - LAND_COST


def get_best_investments(world: WorldState, tracker: MarketTracker, private_state: dict) -> List[Tuple[str, str, float]]:
    """
    Evaluates all options and returns a list of (Type, Name, EMV) sorted by absolute EMV descending.
    Type is 'CROP', 'ANIMAL', or 'LAND'.
    """
    options = []

    # Evaluate Land Expansion first (it unlocks all future tile options)
    if len(world.my_farm.unlocked_quadrants) < 4:
        land_emv = calculate_land_emv(world.day, tracker)
        if land_emv > 0:
            options.append(("LAND", "QUADRANT", land_emv))
    
    # Evaluate Crops
    for crop_name, info in CROP_TYPES.items():
        emv = calculate_crop_emv(crop_name, world.day, tracker)
        if emv > 0:
            options.append(("CROP", crop_name, emv))
            
    # Evaluate Animals
    for animal_name, info in ANIMAL_TYPES.items():
        emv = calculate_animal_emv(animal_name, world.day, tracker)
        if emv > 0:
            options.append(("ANIMAL", animal_name, emv))
            
    # Sort by Absolute EMV descending
    options.sort(key=lambda x: x[2], reverse=True)
    return options
