"""
Simulator Module for Kaggriculture.
Projects future money for each candidate strategy and ranks them.
This is a lightweight, fast heuristic simulation — not a full game replay.
"""
from typing import Dict, List, Optional
from strategy import Strategy, CANDIDATE_STRATEGIES
from crop_model import CROP_TYPES, crop_profitability
from animal_model import ANIMAL_TYPES


TOTAL_GAME_DAYS = 30
TURNS_PER_DAY = 24


def simulate_strategy(
    strategy: Strategy,
    current_day: int,
    current_money: float,
    num_empty_tiles: int,
    num_animals: int,
    market_prices: Dict[str, int],
    wheat_in_shed: int,
) -> float:
    """
    Projects final money for a given strategy from the current state until day 30.
    Uses fast heuristic forward modelling — no full game simulation.
    
    Returns: Projected final money
    """
    days_remaining = TOTAL_GAME_DAYS - current_day
    if days_remaining <= 0:
        return current_money
    
    money = current_money
    animals = num_animals
    wheat_reserve = wheat_in_shed
    farmable_tiles = max(0, num_empty_tiles)
    
    # --- Strategy: ENDGAME_LIQUIDATE ---
    if strategy.sell_aggressively:
        # No more investment — just estimate we'll earn ~0 new income
        return money

    # --- Estimate crop income per day ---
    crop_daily_income = 0.0
    focus = strategy.focus_crop
    
    if focus and farmable_tiles > 0:
        crop_info = CROP_TYPES.get(focus)
        if crop_info and money >= crop_info.seed_cost:
            price = market_prices.get(focus, crop_info.base_sell_price)
            roi_per_turn = crop_profitability(focus, price)
            # Approximate daily income: ROI * 24 turns * tiles we can plant
            tiles_planted = min(farmable_tiles, max(1, int(money // crop_info.seed_cost)))
            cost_this_day = tiles_planted * crop_info.seed_cost
            if money >= cost_this_day:
                money -= cost_this_day
                crop_daily_income = roi_per_turn * TURNS_PER_DAY * tiles_planted
    
    # --- Estimate animal income per day ---
    animal_daily_income = 0.0
    if strategy.buy_animals and money >= 800 and wheat_reserve >= 5:
        # Buy a sheep if we can afford it
        sheep_info = ANIMAL_TYPES["SHEEP"]
        if money >= sheep_info.cost:
            money -= sheep_info.cost
            animals += 1
    
    for _ in range(animals):
        # SHEEP: $200 WOOL every 3 days = ~$67/day (simplified)
        sheep_price = market_prices.get("WOOL", 200)
        animal_daily_income += sheep_price / 3.0
        
    # --- Daily feed cost for animals ---
    daily_feed_cost = animals * market_prices.get("WHEAT", 25)

    # --- Project income over remaining days ---
    net_daily = crop_daily_income + animal_daily_income - daily_feed_cost
    projected_money = money + (net_daily * days_remaining)
    
    return projected_money


def rank_strategies(
    current_day: int,
    current_money: float,
    num_empty_tiles: int,
    num_animals: int,
    market_prices: Dict[str, int],
    wheat_in_shed: int,
) -> List[Strategy]:
    """
    Scores all candidate strategies and returns them sorted best-first.
    """
    scored: List[tuple] = []
    
    for strategy in CANDIDATE_STRATEGIES:
        # Skip strategies we can't afford
        if current_money < strategy.min_money_to_act:
            continue
        
        projected = simulate_strategy(
            strategy=strategy,
            current_day=current_day,
            current_money=current_money,
            num_empty_tiles=num_empty_tiles,
            num_animals=num_animals,
            market_prices=market_prices,
            wheat_in_shed=wheat_in_shed,
        )
        scored.append((projected, strategy))
    
    # Sort by projected money descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored]


def best_strategy(
    current_day: int,
    current_money: float,
    num_empty_tiles: int,
    num_animals: int,
    market_prices: Dict[str, int],
    wheat_in_shed: int,
) -> Strategy:
    """
    Returns the single best strategy for the current state.
    Falls back to BALANCED if ranking fails.
    """
    from strategy import CANDIDATE_STRATEGIES
    
    # Always switch to ENDGAME_LIQUIDATE in final 5 days
    if current_day >= 25:
        endgame = next((s for s in CANDIDATE_STRATEGIES if s.name == "ENDGAME_LIQUIDATE"), None)
        if endgame:
            return endgame
    
    ranked = rank_strategies(
        current_day=current_day,
        current_money=current_money,
        num_empty_tiles=num_empty_tiles,
        num_animals=num_animals,
        market_prices=market_prices,
        wheat_in_shed=wheat_in_shed,
    )
    
    if ranked:
        return ranked[0]
    
    # Fallback: BALANCED
    return next((s for s in CANDIDATE_STRATEGIES if s.name == "BALANCED"), CANDIDATE_STRATEGIES[0])
