"""
Main Agent for Kaggriculture.
Baseline Heuristic Agent (Approach A):
- Parses observation with WorldState
- Generates and prioritizes tasks (WATER, HARVEST, PLANT, DIG)
- Assigns tasks greedily to workers
- Manages market trading: sells harvested shed produce, buys seeds to maintain farming cycle
"""
from typing import Any, Dict, List
from world_state import parse_observation, WorldState
from pathfinding import manhattan_distance, next_move
from task_manager import generate_tasks, assign_tasks, execute_worker_task
import action_engine as ae
from market_model import MarketTracker

from animal_model import ANIMAL_TYPES

tracker = MarketTracker()

def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Kaggle-compatible agent entry point."""
    world: WorldState = parse_observation(obs)
    my_farm = world.my_farm
    private = world.private
    market = world.market
    
    is_endgame = world.day >= 28
    market_orders: List[List[Any]] = []
    
    tracker.update(market.prices, market.inventory)
    
    # Pre-calculate best crop and tasks to inform market decisions
    best_crop = tracker.best_crop_to_plant(market.prices, my_farm.money) or "WHEAT"
    tasks = generate_tasks(world, default_crop=best_crop)
    
    # Determine WHEAT retention for feeding animals
    num_animals = len(my_farm.structure_tiles) + sum(private.shed.get(a, 0) for a in ["GOOSE", "COW", "SHEEP"])
    wheat_reserve = num_animals * 3 if not is_endgame else 0
    
    # 1. Market Orders: Sell harvested produce from shed dynamically
    for good, count in private.shed.items():
        if count > 0 and good in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"):
            current_price = market.price_of(good)
            
            # For WHEAT, reserve some for animal feed
            available_to_sell = count
            if good == "WHEAT":
                available_to_sell = max(0, count - wheat_reserve)
                
            sell_qty = tracker.should_sell(good, available_to_sell, current_price)
            # In endgame, liquidate everything!
            if is_endgame:
                sell_qty = count
                
            if sell_qty > 0:
                market_orders.append(ae.sell_order(good, sell_qty))
            
    # 2. Market Orders: Maintain seed supply
    if not is_endgame:
        target_seeds = private.seeds.get(best_crop, 0)
        # If seeds are low and we have funds, buy the best seeds
        if target_seeds < 5 and my_farm.money >= 100:
            buy_qty = 5 - target_seeds
            if buy_qty > 0:
                market_orders.append(ae.buy_seed_order(best_crop, buy_qty))
                
    # 3. Market Orders: Hire Workers
    if not is_endgame and my_farm.money >= 200:
        # If we have more than 3 tasks per worker, hire another hand
        if len(tasks) > len(my_farm.all_workers) * 3:
            market_orders.append(ae.hire_order())
            
    # 4. Market Orders: Buy Animals
    # Only buy animals if we have good cash reserves and some wheat ready to feed them
    if not is_endgame and my_farm.money >= 1500 and private.shed.get("WHEAT", 0) >= 5:
        unplaced = sum(private.shed.get(a, 0) for a in ["GOOSE", "COW", "SHEEP"])
        if unplaced == 0:
            # Let's buy a SHEEP (most profitable)
            market_orders.append(ae.buy_animal_order("SHEEP", 1))

    # 5. Worker Assignments
    assignments = assign_tasks(my_farm.all_workers, tasks)
    
    # Execute farmer task
    farmer_act = execute_worker_task(my_farm.farmer, assignments.get(0), world)
    
    # Execute hands tasks
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
