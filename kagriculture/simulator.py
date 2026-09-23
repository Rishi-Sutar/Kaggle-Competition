"""
Simulator Module for Kaggriculture.
Projects future money for each candidate strategy and ranks them.
Uses MarketTracker for predictive pricing.
"""
from typing import Dict, List, Optional
from strategy import Strategy, CANDIDATE_STRATEGIES
from crop_model import CROP_TYPES, crop_profitability
from animal_model import ANIMAL_TYPES
from market_model import MarketTracker

TOTAL_GAME_DAYS = 30
TURNS_PER_DAY = 24


def simulate_strategy(
    strategy: Strategy,
    current_day: int,
    current_money: float,
    num_empty_tiles: int,
    num_animals: int,
    tracker: MarketTracker,
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
            # Predict price at maturity using MarketTracker
            predicted_price = tracker.predict_price_at_maturity(focus)
            roi_per_turn = crop_profitability(focus, predicted_price)
            # Approximate daily income: ROI * 24 turns * tiles we can plant
            tiles_planted = min(farmable_tiles, max(1, int(money // crop_info.seed_cost)))
            cost_this_day = tiles_planted * crop_info.seed_cost
            if money >= cost_this_day:
                money -= cost_this_day
                crop_daily_income = roi_per_turn * TURNS_PER_DAY * tiles_planted
    
    # --- Estimate animal income per day ---
    animal_daily_income = 0.0
    
    # Simple compounding simulation for animals:
    # If strategy buys animals, assume we spend all excess money > $800 on SHEEP/COW.
    simulated_days = days_remaining
    simulated_money = money
    simulated_animals = animals
    
    # Sheep info
    sheep_info = ANIMAL_TYPES["SHEEP"]
    sheep_price = tracker.price_history.get("WOOL", [200])[-1] # fallback to current price
    sheep_daily_income = sheep_price / 3.0
    
    # Wheat cost
    wheat_price = tracker.price_history.get("WHEAT", [25])[-1]
    
    for day in range(simulated_days):
        # Income for this day
        daily_income = crop_daily_income + (simulated_animals * sheep_daily_income)
        daily_cost = simulated_animals * wheat_price
        
        simulated_money += (daily_income - daily_cost)
        
        # Reinvest in animals if strategy allows
        if strategy.buy_animals and simulated_money >= sheep_info.cost + 500: # Keep 500 buffer
            # How many can we buy?
            buy_count = int((simulated_money - 500) // sheep_info.cost)
            simulated_animals += buy_count
            simulated_money -= buy_count * sheep_info.cost

    return simulated_money


def rank_strategies(
    current_day: int,
    current_money: float,
    num_empty_tiles: int,
    num_animals: int,
    tracker: MarketTracker,
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
            tracker=tracker,
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
    tracker: MarketTracker,
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
        tracker=tracker,
        wheat_in_shed=wheat_in_shed,
    )
    
    if ranked:
        return ranked[0]
    
    # Fallback: BALANCED
    return next((s for s in CANDIDATE_STRATEGIES if s.name == "BALANCED"), CANDIDATE_STRATEGIES[0])
