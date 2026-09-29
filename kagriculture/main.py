"""
Main Agent for Kaggriculture — Phase 12: Expected Marginal Value (EMV) Engine.
"""
from typing import Any, Dict, List
from world_state import parse_observation, WorldState
from task_manager import generate_tasks, execute_worker_task, assign_tasks
from optimizer import optimize_assignments
import action_engine as ae
from market_model import MarketTracker
from town_model import TownModel
from emv_engine import get_target_portfolio, get_operational_buffer
from animal_model import ANIMAL_TYPES
from crop_model import CROP_TYPES

tracker = MarketTracker()
town_tracker = TownModel()

# We cache the best default crop to pass to the task manager
current_best_crop = "CARROT"

def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    global current_best_crop

    world: WorldState = parse_observation(obs)
    my_farm = world.my_farm
    private = world.private
    market = world.market

    tracker.update(world)
    town_tracker.update(world)
    market_orders: List[List[Any]] = []
    is_endgame = world.day >= 27

    # Calculate operational buffer for tomorrow
    op_buffer = get_operational_buffer(world, private.shed)
    projected_money = my_farm.money

    # ==========================================
    # 1. EMV ENGINE & PURCHASES (Hour 0)
    # ==========================================
    if world.hour == 0:
        if not is_endgame:
            # Calculate precise steps required for today's tasks, prioritized by survival
            import math
            from task_manager import TASK_PRIORITIES, SHED_POS
            from pathfinding import manhattan_distance
            
            proxy_tasks = [] # List of (priority, exact_steps)
            
            # Animals
            for tile in my_farm.structure_tiles:
                if tile.animal:
                    dist = manhattan_distance(tile.pos, SHED_POS)
                    proxy_tasks.append((TASK_PRIORITIES["FEED"], dist + 2))
                    proxy_tasks.append((TASK_PRIORITIES["CARE"], dist + 1))
                    if tile.fertilizer_available:
                        proxy_tasks.append((TASK_PRIORITIES["COLLECT_FERTILIZER"], dist + 2))
                    if tile.yield_units > 0:
                        proxy_tasks.append((TASK_PRIORITIES["HARVEST_ANIMAL"], dist + 2))
                        
            # Crops
            for tile in my_farm.plant_tiles:
                if tile.crop:
                    dist_to_shed = manhattan_distance(tile.pos, SHED_POS)
                    
                    if not tile.watered_today:
                        proxy_tasks.append((TASK_PRIORITIES["WATER"], dist_to_shed + 1)) # No well trip needed, just walk and water
                    if tile.yield_units > 0:
                        proxy_tasks.append((TASK_PRIORITIES["HARVEST"], dist_to_shed + 2))
                        
            # Empty Tiles (assume they will be planted)
            for tile in my_farm.empty_tiles:
                dist = manhattan_distance(tile.pos, SHED_POS)
                proxy_tasks.append((TASK_PRIORITIES["PLANT"], dist + 2))
                
            # Sort tasks by Priority (Highest first)
            proxy_tasks.sort(key=lambda x: x[0], reverse=True)
            
            # Determine exactly how many workers we need, respecting priority and budget
            from animal_model import ANIMAL_TYPES
            num_animals = len(my_farm.structure_tiles) + sum(private.shed.get(a, 0) for a in ANIMAL_TYPES)
            affordable_budget = my_farm.money - (num_animals * 5) # Feed buffer
            
            accumulated_steps = 0
            ideal_workers_total = 1 # Farmer is free
            fib = [1, 1, 2, 3, 5, 8, 13, 21, 34]
            
            for priority, steps in proxy_tasks:
                accumulated_steps += steps
                required_total = math.ceil(accumulated_steps / 24.0)
                
                if required_total > ideal_workers_total:
                    hands_needed = required_total - 1
                    if hands_needed > 8: 
                        break # Farm capacity maxed out
                    
                    wage_cost = sum(fib[:hands_needed])
                    if wage_cost <= affordable_budget:
                        ideal_workers_total = required_total
                    else:
                        break # Cannot afford to staff lower priority tasks, stop hiring
                        
            # Phase 17: Cap at 4 hands so we reserve at least 6 slots for market investments (limit is 10)
            num_hands = min(ideal_workers_total - 1, 4)
            
            # Hire the calculated number of workers
            for _ in range(num_hands):
                market_orders.append(ae.hire_order())
                
            # Get the optimal portfolio given current market glut
            target_portfolio = get_target_portfolio(world, tracker, private, town_tracker)
            
            best_crop = next((name for typ, name, roi in target_portfolio if typ == "CROP" and name != "WHEAT"), "CARROT")
            global current_best_crop
            current_best_crop = best_crop
            
            empty_tiles = len(my_farm.empty_tiles)
            
            # Execute purchases
            for item_type, name, emv in target_portfolio:
                if len(market_orders) >= 10: break # Market slot cap
                if projected_money <= op_buffer: break
                
                if item_type == "LAND":
                    if projected_money >= 1000 + op_buffer:
                        market_orders.append(ae.buy_land_order())
                        projected_money -= 1000
                        empty_tiles += 25
                elif item_type == "ANIMAL":
                    cost = ANIMAL_TYPES[name].cost
                    if projected_money >= cost + op_buffer and empty_tiles > 0:
                        market_orders.append(ae.buy_animal_order(name, 1))
                        projected_money -= cost
                        empty_tiles -= 1
                elif item_type == "CROP":
                    cost = CROP_TYPES[name].seed_cost
                    seeds_owned = private.seeds.get(name, 0)
                    if seeds_owned < empty_tiles and projected_money >= cost + op_buffer:
                        buy_count = min(empty_tiles - seeds_owned, int((projected_money - op_buffer) // cost), 10 - len(market_orders))
                        if buy_count > 0:
                            market_orders.append(ae.buy_seed_order(name, buy_count))
                            projected_money -= buy_count * cost

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
        
        # Sort by current price descending so high-value items (MILK, WOOL) sell first
        sellable_goods = [
            (good, count, market.price_of(good))
            for good, count in private.shed.items()
            if count > 0 and good in (
                "MELON", "WOOL", "MILK", "EGG", "STRAWBERRY", "TOMATO",
                "CARROT", "FERTILIZER"
            )
        ]
        sellable_goods.sort(key=lambda x: x[2], reverse=True)
        
        for good, count, price in sellable_goods:
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
