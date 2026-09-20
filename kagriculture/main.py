"""
Main Agent for Kaggriculture — Phase 6: Predictive Planning
- Parses observation with WorldState
- Re-plans every morning using simulator.best_strategy()
- Generates tasks from active strategy
- Manages market trading driven by strategy
"""
from typing import Any, Dict, List, Optional
from world_state import parse_observation, WorldState
from pathfinding import manhattan_distance, next_move
from task_manager import generate_tasks, assign_tasks, execute_worker_task
import action_engine as ae
from market_model import MarketTracker
from animal_model import ANIMAL_TYPES
from strategy import Strategy, CANDIDATE_STRATEGIES
from simulator import best_strategy
from optimizer import optimize_assignments

tracker = MarketTracker()
active_strategy: Optional[Strategy] = None


def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Kaggle-compatible agent entry point."""
    global active_strategy
    
    world: WorldState = parse_observation(obs)
    my_farm = world.my_farm
    private = world.private
    market = world.market
    
    tracker.update(market.prices, market.inventory)
    
    # --- Re-plan every morning (hour 0 of each day) ---
    if world.hour == 0 or active_strategy is None:
        num_animals = len(my_farm.structure_tiles)
        active_strategy = best_strategy(
            current_day=world.day,
            current_money=my_farm.money,
            num_empty_tiles=len(my_farm.empty_tiles),
            num_animals=num_animals,
            market_prices=market.prices,
            wheat_in_shed=private.shed.get("WHEAT", 0),
        )
    
    is_endgame = active_strategy.sell_aggressively or world.day >= 28
    market_orders: List[List[Any]] = []
    
    # Determine crop from strategy (fallback to market tracker if BALANCED)
    if active_strategy.focus_crop:
        best_crop = active_strategy.focus_crop
    else:
        best_crop = tracker.best_crop_to_plant(market.prices, my_farm.money) or "WHEAT"
    
    tasks = generate_tasks(world, default_crop=best_crop)
    
    # Determine WHEAT retention for feeding animals
    num_animals = len(my_farm.structure_tiles) + sum(private.shed.get(a, 0) for a in ["GOOSE", "COW", "SHEEP"])
    wheat_reserve = num_animals * 3 if not is_endgame else 0
    
    # 1. Market Orders: Sell harvested produce from shed
    for good, count in private.shed.items():
        if count > 0 and good in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"):
            current_price = market.price_of(good)
            
            available_to_sell = count
            if good == "WHEAT":
                available_to_sell = max(0, count - wheat_reserve)
            
            if is_endgame:
                sell_qty = available_to_sell
            else:
                sell_qty = tracker.should_sell(good, available_to_sell, current_price)
                
            if sell_qty > 0:
                market_orders.append(ae.sell_order(good, sell_qty))
            
    # 2. Market Orders: Maintain seed supply
    if not is_endgame:
        target_seeds = private.seeds.get(best_crop, 0)
        if target_seeds < 5 and my_farm.money >= 100:
            buy_qty = 5 - target_seeds
            if buy_qty > 0:
                market_orders.append(ae.buy_seed_order(best_crop, buy_qty))
                
    # 3. Market Orders: Hire Workers (strategy-gated)
    if not is_endgame and active_strategy.hire_workers and my_farm.money >= 200:
        if len(tasks) > len(my_farm.all_workers) * 3:
            market_orders.append(ae.hire_order())
            
    # 4. Market Orders: Buy Animals (strategy-gated)
    if not is_endgame and active_strategy.buy_animals and my_farm.money >= 1500 and private.shed.get("WHEAT", 0) >= 5:
        unplaced = sum(private.shed.get(a, 0) for a in ["GOOSE", "COW", "SHEEP"])
        if unplaced == 0:
            market_orders.append(ae.buy_animal_order("SHEEP", 1))

    # 5. Worker Assignments (CP-SAT optimizer with greedy fallback)
    assignments = optimize_assignments(my_farm.all_workers, tasks, time_limit_ms=400)
    
    farmer_act = execute_worker_task(my_farm.farmer, assignments.get(0), world)
    
    hands_acts = []
    for hand in my_farm.hands:
        h_act = execute_worker_task(hand, assignments.get(hand.worker_id), world)
        hands_acts.append(h_act)
        
    return ae.make_action(
        farmer_action=farmer_act,
        hands_actions=hands_acts,
        market_orders=market_orders,
        expected_hands_count=len(my_farm.hands)
    )
