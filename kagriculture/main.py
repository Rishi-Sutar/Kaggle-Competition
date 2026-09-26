"""
Main Agent for Kaggriculture — Phase 12: Expected Marginal Value (EMV) Engine.
"""
from typing import Any, Dict, List
from world_state import parse_observation, WorldState
from task_manager import generate_tasks, execute_worker_task, assign_tasks
from optimizer import optimize_assignments
import action_engine as ae
from market_model import MarketTracker
from emv_engine import get_best_investments, get_operational_buffer
from animal_model import ANIMAL_TYPES
from crop_model import CROP_TYPES

tracker = MarketTracker()

# We cache the best default crop to pass to the task manager
current_best_crop = "CARROT"

def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    global current_best_crop

    world: WorldState = parse_observation(obs)
    my_farm = world.my_farm
    private = world.private
    market = world.market

    tracker.update(world)
    market_orders: List[List[Any]] = []
    is_endgame = world.day >= 25

    # Calculate operational buffer for tomorrow
    op_buffer = get_operational_buffer(world, private.shed)
    projected_money = my_farm.money

    # ==========================================
    # 1. EMV ENGINE & PURCHASES (Hour 0)
    # ==========================================
    if world.hour == 0:
        # 1a. Hire Workers for today
        if not is_endgame:
            num_hires = 5 if my_farm.money >= 50 else (3 if my_farm.money >= 20 else 1)
            for _ in range(num_hires):
                market_orders.append(ae.hire_order())
                
        # 1b. EMV Investment Allocation
        if not is_endgame:
            investments = get_best_investments(world, tracker, private.shed)
            
            # Find the best crop from investments to set as our default
            best_crop = next((name for typ, name, roi in investments if typ == "CROP"), "CARROT")
            current_best_crop = best_crop

            empty_tiles = len(my_farm.empty_tiles)
            
            for inv_type, name, roi in investments:
                if projected_money <= op_buffer:
                    break # Stop if we hit the operational buffer
                    
                if inv_type == "ANIMAL":
                    cost = ANIMAL_TYPES[name].cost
                    if projected_money >= cost + op_buffer and empty_tiles > 0:
                        market_orders.append(ae.buy_animal_order(name, 1))
                        projected_money -= cost
                        empty_tiles -= 1
                        
                elif inv_type == "CROP":
                    cost = CROP_TYPES[name].seed_cost
                    seeds_owned = private.seeds.get(name, 0)
                    
                    if seeds_owned < empty_tiles and projected_money >= cost + op_buffer:
                        # Buy in small batches to save market orders, up to available money above buffer
                        buy_count = min(empty_tiles - seeds_owned, int((projected_money - op_buffer) // cost), 15)
                        if buy_count > 0:
                            market_orders.append(ae.buy_seed_order(name, buy_count))
                            projected_money -= buy_count * cost

            # Expand farm land if running out of space and we have plenty of cash
            if projected_money >= 1000 + op_buffer and len(my_farm.unlocked_quadrants) < 4:
                if len(my_farm.empty_tiles) < 5:
                    market_orders.append(ae.buy_land_order())
                    projected_money -= 1000

    # Count animals to calculate wheat feed reserve
    num_animals = len(my_farm.structure_tiles) + sum(
        private.shed.get(a, 0) for a in ["GOOSE", "COW", "SHEEP"]
    ) + sum(
        w.inventory.get(a, 0) for w in my_farm.all_workers for a in ["GOOSE", "COW", "SHEEP"]
    )
    wheat_reserve = num_animals * 3 if not is_endgame else 0
    wheat_in_shed = private.shed.get("WHEAT", 0)

    # Replenish wheat feed if running low (done every hour if needed)
    if not is_endgame and wheat_in_shed < wheat_reserve and projected_money >= 100:
        shortfall = wheat_reserve - wheat_in_shed
        buy_qty = min(shortfall, 5)
        if buy_qty > 0:
            market_orders.append(ae.buy_product_order("WHEAT", buy_qty))
            projected_money -= buy_qty * market.price_of("WHEAT")

    # ==========================================
    # 2. MARKET SELLING (Hour 23)
    # ==========================================
    if world.hour == 23 or is_endgame:
        total_shed_items = sum(private.shed.values())
        
        for good, count in private.shed.items():
            if count > 0 and good in (
                "MELON", "WOOL", "MILK", "EGG", "STRAWBERRY", "TOMATO", "CARROT", "FERTILIZER"
            ):
                price = market.price_of(good)
                sell_qty = tracker.should_sell(good, count, price, world.day, total_shed_items, is_endgame=is_endgame)
                if sell_qty > 0:
                    market_orders.append(ae.sell_order(good, sell_qty))

        # Sell surplus wheat beyond animal feed reserve
        available_wheat = wheat_in_shed if is_endgame else max(0, wheat_in_shed - wheat_reserve)
        if available_wheat > 0:
            sell_qty = tracker.should_sell("WHEAT", available_wheat, market.price_of("WHEAT"), world.day, total_shed_items, is_endgame=is_endgame)
            if sell_qty > 0:
                market_orders.append(ae.sell_order("WHEAT", sell_qty))

    # ==========================================
    # 3. TASK GENERATION & WORKER ASSIGNMENT
    # ==========================================
    tasks = generate_tasks(world, default_crop=current_best_crop)

    try:
        assignments = optimize_assignments(my_farm.all_workers, tasks, time_limit_ms=350)
    except Exception:
        assignments = assign_tasks(my_farm.all_workers, tasks)

    farmer_act = execute_worker_task(my_farm.farmer, assignments.get(0), world)
    hands_acts = []
    for hand in my_farm.hands:
        h_act = execute_worker_task(hand, assignments.get(hand.worker_id), world)
        hands_acts.append(h_act)

    return ae.make_action(
        farmer_action=farmer_act,
        hands_actions=hands_acts,
        market_orders=market_orders[:10],
        expected_hands_count=len(my_farm.hands),
    )
