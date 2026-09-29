"""
Expected Marginal Value (EMV) Engine — Phase 13: Internal Supply Chain & Land Expansion
Dynamically calculates the absolute profit of every possible investment per tile.
"""
from typing import Dict, List, Tuple, Any
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
        private_state.get(a, 0) for a in ANIMAL_TYPES
    )
    
    # We need to feed them. Assume wheat cost is ~25.
    feed_cost = num_animals * WHEAT_FEED_COST
    
    # We need workers to feed/water. Assume we hire at least 3 workers (cost: 1+1+2 = 4)
    worker_cost = 4
    
    return float(feed_cost + worker_cost)


def calculate_crop_emv(crop_name: str, current_day: int, tracker: MarketTracker, town_model) -> float:
    """
    Calculates the total expected profit of planting a crop today until Day 30.
    Assumes FERTILIZER is used, which doubles one-time yield rate or doubles ongoing yields.
    """
    info = CROP_TYPES.get(crop_name)
    if not info:
        return -9999.0
        
    days_left = 30 - current_day
    if days_left <= info.first_yield_day:
        return -9999.0 # Won't even reach first harvest
        
    predicted_price = tracker.predict_price_at_maturity(crop_name, town_model)
    
    if info.nature == "ONE-TIME":
        if days_left <= info.max_yield_day:
            if days_left <= info.first_yield_day: return -9999.0
            yield_amount = 1
        else:
            # Assume fertilizer is used -> yields hit absolute max cap
            yield_amount = info.peak_fertilized_yield
            
        revenue = predicted_price * yield_amount
        revenue = predicted_price * yield_amount
        profit = revenue - info.seed_cost
        
    else: # ONGOING (Tomato, Strawberry)
        yields_possible = 0
        day_pointer = info.first_yield_day
        interval = 2 if crop_name == "STRAWBERRY" else 1
        
        while day_pointer < days_left and yields_possible < info.peak_unfertilized_yield:
            yields_possible += 1
            day_pointer += interval
            
        # Fertilizer DOUBLES ongoing yields!
        revenue = predicted_price * (yields_possible * 2)
        profit = revenue - info.seed_cost
        
    return profit


def calculate_animal_emv(animal_name: str, current_day: int, tracker: MarketTracker, town_model) -> float:
    """
    Calculates the total expected profit of buying an animal today until Day 30.
    Assumes CARE is applied daily, which banks +1 yield per day.
    """
    info = ANIMAL_TYPES.get(animal_name)
    if not info:
        return -9999.0
        
    days_left = 30 - current_day
    if days_left <= info.first_yield_day:
        return -9999.0 # Won't even reach first yield
        
    predicted_price = tracker.predict_price_at_maturity(info.product, town_model)
    
    # Calculate total yields before day 30
    yield_ticks = max(0, (days_left - info.first_yield_day) // info.yield_interval + 1)
    
    # With daily CARE, the animal produces (1 base + yield_interval banked days) per tick
    # Example: Cow (interval 2) produces 1 base + 2 banked = 3 milk per tick
    yield_per_tick = 1 + info.yield_interval
    total_products = yield_ticks * yield_per_tick
    
    revenue = predicted_price * total_products
    
    feed_cost = WHEAT_FEED_COST * days_left
    profit = revenue - info.cost - feed_cost
    return profit


def calculate_land_emv(current_day: int, tracker: MarketTracker, town_model) -> float:
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
    # We evaluate all animals to find the most profitable one to fill the new tiles
    best_animal_emv = 0.0
    for animal_name in ANIMAL_TYPES:
        emv = calculate_animal_emv(animal_name, current_day, tracker, town_model)
        if emv > best_animal_emv:
            best_animal_emv = emv

    # Assume we can profitably fill ~60% of the quadrant (structure build time + movement)
    effective_tiles = QUADRANT_TILES * 0.60
    projected_profit = best_animal_emv * effective_tiles

    # Deduct land cost
    return projected_profit - LAND_COST


def get_target_portfolio(world: WorldState, tracker: MarketTracker, private: Any, town_model) -> List[Tuple[str, str, float]]:
    """
    Calculates the absolute best items to buy RIGHT NOW.
    Accounts for market glut by artificially lowering the EMV of items we already have
    or items that are highly sensitive to market crashes.
    Returns a sorted list of (Type, Name, Adjusted_EMV).
    """
    options = []
    days_left = 30 - world.day
    
    # 1. Land Expansion
    if len(world.my_farm.unlocked_quadrants) < 4:
        land_emv = calculate_land_emv(world.day, tracker, town_model)
        if land_emv > 0:
            options.append(("LAND", "QUADRANT", land_emv))
            
    # Calculate our current exposure to each product
    current_exposure = {}
    for tile in world.my_farm.plant_tiles:
        if tile.crop:
            current_exposure[tile.crop] = current_exposure.get(tile.crop, 0) + 1
    for tile in world.my_farm.structure_tiles:
        if tile.animal:
            prod = ANIMAL_TYPES[tile.animal].product
            current_exposure[prod] = current_exposure.get(prod, 0) + 1
            
    # 2. Crops
    for crop_name, info in CROP_TYPES.items():
        base_emv = calculate_crop_emv(crop_name, world.day, tracker, town_model)
        if base_emv > 0:
            # Glut penalty: Reduce EMV based on how many we already have vs market tolerance (T)
            # Highly sensitive crops (Strawberry T=100) lose EMV much faster than Wheat (T=400)
            T_VALUES = {"WHEAT": 250, "CARROT": 150, "MELON": 250, "STRAWBERRY": 100, "TOMATO": 150, "EGG": 250, "MILK": 100, "WOOL": 150}
            exposure = current_exposure.get(crop_name, 0)
            glut_penalty = 1.0 - (exposure / max(1, T_VALUES.get(crop_name, 100)))
            adjusted_emv = base_emv * max(0.1, glut_penalty)
            
            # Artificial boost for WHEAT if we have animals
            if crop_name == "WHEAT":
                num_animals = len(world.my_farm.structure_tiles) + sum(private.shed.get(a, 0) for a in ANIMAL_TYPES)
                if exposure < (num_animals // 2) + 1 and num_animals > 0:
                    adjusted_emv = 99999.0
                    
            options.append(("CROP", crop_name, adjusted_emv))
            
    # 3. Animals
    for animal_name, info in ANIMAL_TYPES.items():
        base_emv = calculate_animal_emv(animal_name, world.day, tracker, town_model)
        if base_emv > 0:
            T_VALUES = {"WHEAT": 250, "CARROT": 150, "MELON": 250, "STRAWBERRY": 100, "TOMATO": 150, "EGG": 250, "MILK": 100, "WOOL": 150}
            exposure = current_exposure.get(info.product, 0)
            glut_penalty = 1.0 - (exposure / max(1, T_VALUES.get(info.product, 100)))
            adjusted_emv = base_emv * max(0.1, glut_penalty)
            options.append(("ANIMAL", animal_name, adjusted_emv))
            
    options.sort(key=lambda x: x[2], reverse=True)
    return options
