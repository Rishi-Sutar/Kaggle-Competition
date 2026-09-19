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

def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Kaggle-compatible agent entry point."""
    world: WorldState = parse_observation(obs)
    my_farm = world.my_farm
    private = world.private
    market = world.market
    
    market_orders: List[List[Any]] = []
    
    # 1. Market Orders: Sell harvested produce from shed
    for good, count in private.shed.items():
        if count > 0 and good in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"):
            market_orders.append(ae.sell_order(good, count))
            
    # 2. Market Orders: Maintain seed supply
    wheat_seeds = private.seeds.get("WHEAT", 0)
    # If seeds are low and we have funds, buy wheat seeds
    if wheat_seeds < 5 and my_farm.money >= 50:
        buy_qty = min(5, int(my_farm.money // 10))
        if buy_qty > 0:
            market_orders.append(ae.buy_seed_order("WHEAT", buy_qty))
            
    # 3. Tasks & Worker Assignments
    tasks = generate_tasks(world, default_crop="WHEAT")
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
