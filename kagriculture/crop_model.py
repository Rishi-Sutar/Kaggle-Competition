"""
Crop Model for Kaggriculture.
Contains the hardcoded static values and profitability models for all crops.
"""
from dataclasses import dataclass
from typing import Dict

@dataclass
class CropInfo:
    name: str
    nature: str                 # "ONE-TIME" or "ONGOING"
    seed_cost: int
    base_sell_price: int
    first_yield_day: int        # When the first yield happens (if watered)
    max_yield_day: int          # For one-time crops, the day when yield peaks. For ongoing, when the schedule ends.
    peak_unfertilized_yield: int
    peak_fertilized_yield: int
    
    @property
    def growth_time(self) -> int:
        return self.first_yield_day


# Hardcoded values obtained from environment rules and Phase 0 experiments
CROP_TYPES: Dict[str, CropInfo] = {
    "WHEAT": CropInfo(
        name="WHEAT",
        nature="ONE-TIME",
        seed_cost=10,
        base_sell_price=25,
        first_yield_day=2,
        max_yield_day=4,
        peak_unfertilized_yield=4,
        peak_fertilized_yield=6
    ),
    "CARROT": CropInfo(
        name="CARROT",
        nature="ONE-TIME",
        seed_cost=20,
        base_sell_price=35,
        first_yield_day=2,
        max_yield_day=3,
        peak_unfertilized_yield=3,
        peak_fertilized_yield=4
    ),
    "TOMATO": CropInfo(
        name="TOMATO",
        nature="ONGOING",
        seed_cost=50,
        base_sell_price=60,
        first_yield_day=8,
        max_yield_day=11,
        peak_unfertilized_yield=4,  # Cap over multiple days
        peak_fertilized_yield=4     # Same cap
    ),
    "STRAWBERRY": CropInfo(
        name="STRAWBERRY",
        nature="ONGOING",
        seed_cost=100,
        base_sell_price=120,
        first_yield_day=10,
        max_yield_day=16,
        peak_unfertilized_yield=4,  # Cap over multiple days
        peak_fertilized_yield=4     # Same cap
    ),
    "MELON": CropInfo(
        name="MELON",
        nature="ONE-TIME",
        seed_cost=80,
        base_sell_price=250,
        first_yield_day=10,
        max_yield_day=10,
        peak_unfertilized_yield=6,
        peak_fertilized_yield=6
    )
}

def crop_profitability(crop: str, current_price: int) -> float:
    """
    Calculates estimated Return on Investment (ROI) per turn.
    Assuming peak unfertilized yield.
    ROI = (Revenue - Cost) / (Growth Days * Turns Per Day)
    """
    info = CROP_TYPES.get(crop)
    if not info:
        return 0.0
        
    revenue = current_price * info.peak_unfertilized_yield
    profit = revenue - info.seed_cost
    
    # We use max_yield_day for the expected timeframe of holding the plant to max yield
    timeframe_turns = info.max_yield_day * 24
    
    # Avoid division by zero
    if timeframe_turns == 0:
        timeframe_turns = 24
        
    return profit / timeframe_turns
