"""
Action Engine for Kaggriculture.
Constructs and validates the exact action dictionary expected by the Kaggle environment:
{
    "farmer": [op, ...args],
    "hands": [[op, ...args], ...],
    "market": [[op, ...args], ...]
}
"""
from typing import Any, Dict, List, Optional, Union

MAX_MARKET_ORDERS = 10

def move_action(direction: str) -> List[str]:
    """NORTH, SOUTH, EAST, WEST"""
    return [direction]

def plant_action(crop: str) -> List[str]:
    return ["PLANT", crop]

def water_action() -> List[str]:
    return ["WATER"]

def harvest_action() -> List[str]:
    return ["HARVEST"]

def fertilize_action() -> List[str]:
    return ["FERTILIZE"]

def dig_action() -> List[str]:
    return ["DIG"]

def build_coop_action() -> List[str]:
    return ["BUILD_COOP"]

def build_pasture_action() -> List[str]:
    return ["BUILD_PASTURE"]

def place_action(item: str, n: int = 1) -> List[Any]:
    if n == 1:
        return ["PLACE", item]
    return ["PLACE", item, n]

def feed_action() -> List[str]:
    return ["FEED"]

def care_action() -> List[str]:
    return ["CARE"]

def collect_fertilizer_action() -> List[str]:
    return ["COLLECT_FERTILIZER"]

def pickup_action(item: str, n: int = 1) -> List[Any]:
    return ["PICKUP", item, n]

def drop_action() -> List[str]:
    return ["DROP"]

def pass_worker_action() -> List[str]:
    return ["PASS"]

# Market orders
def buy_seed_order(crop: str, n: int = 1) -> List[Any]:
    return ["BUY_SEED", crop, int(n)]

def sell_order(item: str, n: int = 1) -> List[Any]:
    return ["SELL", item, int(n)]

def buy_product_order(item: str, n: int = 1) -> List[Any]:
    return ["BUY_PRODUCT", item, int(n)]

def buy_animal_order(animal: str, n: int = 1) -> List[Any]:
    return ["BUY_ANIMAL", animal, int(n)]

def hire_order() -> List[str]:
    return ["HIRE"]

def buy_land_order() -> List[str]:
    return ["BUY_LAND"]

def pass_action(hands_count: int = 0) -> Dict[str, Any]:
    """Returns a full no-op action structure."""
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in range(hands_count)],
        "market": [],
    }

def make_action(
    farmer_action: Optional[List[Any]] = None,
    hands_actions: Optional[List[List[Any]]] = None,
    market_orders: Optional[List[List[Any]]] = None,
    expected_hands_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Constructs a well-formed action dictionary.
    - Caps market orders at MAX_MARKET_ORDERS (10).
    - Ensures hands list matches expected hands count if provided.
    - Default farmer action is ['PASS'].
    """
    farmer = farmer_action if farmer_action else ["PASS"]
    
    hands = list(hands_actions) if hands_actions else []
    if expected_hands_count is not None:
        while len(hands) < expected_hands_count:
            hands.append(["PASS"])
        if len(hands) > expected_hands_count:
            hands = hands[:expected_hands_count]
            
    market = list(market_orders) if market_orders else []
    if len(market) > MAX_MARKET_ORDERS:
        market = market[:MAX_MARKET_ORDERS]
        
    return {
        "farmer": farmer,
        "hands": hands,
        "market": market,
    }
