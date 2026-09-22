"""
Strategy Module for Kaggriculture.
Defines candidate strategies (FOCUS_CROP, FOCUS_ANIMAL, BALANCED, ENDGAME_LIQUIDATE)
that the agent selects from every morning using the simulator.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Strategy:
    name: str
    focus_crop: Optional[str]     # Which crop to plant (None = skip crops)
    buy_animals: bool             # Whether to invest in animals this day
    hire_workers: bool            # Whether to hire farm hands
    sell_aggressively: bool       # Sell everything regardless of price trend
    min_money_to_act: float       # Must have at least this to follow strategy
    description: str


# Candidate strategies evaluated each morning
CANDIDATE_STRATEGIES = [
    Strategy(
        name="FOCUS_CROP_WHEAT",
        focus_crop="WHEAT",
        buy_animals=False,
        hire_workers=True,
        sell_aggressively=False,
        min_money_to_act=100,
        description="Focus on Wheat farming with no animal investment"
    ),
    Strategy(
        name="FOCUS_CROP_CARROT",
        focus_crop="CARROT",
        buy_animals=False,
        hire_workers=True,
        sell_aggressively=False,
        min_money_to_act=120,
        description="Focus on Carrot farming with no animal investment"
    ),
    Strategy(
        name="FOCUS_CROP_MELON",
        focus_crop="MELON",
        buy_animals=False,
        hire_workers=True,
        sell_aggressively=False,
        min_money_to_act=500,
        description="Focus on Melon farming — high ROI, slow growth"
    ),
    Strategy(
        name="BALANCED",
        focus_crop=None,           # Use MarketTracker.best_crop_to_plant()
        buy_animals=True,
        hire_workers=True,
        sell_aggressively=False,
        min_money_to_act=500,
        description="Balanced: best crop + animals when affordable"
    ),
    Strategy(
        name="FOCUS_ANIMAL",
        focus_crop="WHEAT",        # Wheat for feeding animals
        buy_animals=True,
        hire_workers=True,
        sell_aggressively=False,
        min_money_to_act=800,
        description="Prioritize animal investment; grow wheat just for feed"
    ),
    Strategy(
        name="ENDGAME_LIQUIDATE",
        focus_crop=None,           # No more planting
        buy_animals=False,
        hire_workers=False,
        sell_aggressively=True,
        min_money_to_act=0,
        description="Endgame: harvest everything, sell aggressively, no new investment"
    ),
]
