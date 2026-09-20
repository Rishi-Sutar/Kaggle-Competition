"""
Animal Model for Kaggriculture.
Contains the hardcoded static values for animals.
"""
from dataclasses import dataclass
from typing import Dict

@dataclass
class AnimalInfo:
    name: str
    structure: str              # 'COOP' or 'PASTURE'
    cost: int
    product: str                # EGG, MILK, WOOL
    base_product_price: int
    first_yield_day: int        # When the first yield happens
    yield_interval: int         # Days between yields after the first one
    feed_required: str          # Crop required to feed (usually WHEAT)
    feed_amount: int            # Amount of feed required per day
    max_yield_held: int         # Max products it can hold before it must be harvested

# Hardcoded values obtained from environment rules and Phase 0 experiments
ANIMAL_TYPES: Dict[str, AnimalInfo] = {
    "GOOSE": AnimalInfo(
        name="GOOSE",
        structure="COOP",
        cost=300,
        product="EGG",
        base_product_price=50,
        first_yield_day=4,
        yield_interval=1,       # 1 egg per day
        feed_required="WHEAT",
        feed_amount=1,
        max_yield_held=4
    ),
    "COW": AnimalInfo(
        name="COW",
        structure="PASTURE",
        cost=400,
        product="MILK",
        base_product_price=160,
        first_yield_day=8,
        yield_interval=2,       # 1 milk every 2 days
        feed_required="WHEAT",
        feed_amount=1,
        max_yield_held=6
    ),
    "SHEEP": AnimalInfo(
        name="SHEEP",
        structure="PASTURE",
        cost=500,
        product="WOOL",
        base_product_price=200,
        first_yield_day=6,
        yield_interval=3,       # 1 wool every 3 days
        feed_required="WHEAT",
        feed_amount=1,
        max_yield_held=6
    )
}
