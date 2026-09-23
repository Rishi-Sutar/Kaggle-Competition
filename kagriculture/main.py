"""
Main Agent for Kaggriculture — Phase 10: Predictive Dynamic Strategy.
- Removes static Days heuristics
- Predicts market prices
- Tracks opponent behavior
- Chooses strategy via simulation
- Dynamically scales the animal economy
"""
from typing import Any, Dict, List, Optional
from world_state import parse_observation, WorldState
from task_manager import generate_tasks, execute_worker_task, assign_tasks
from optimizer import optimize_assignments
import action_engine as ae
from market_model import MarketTracker
from simulator import best_strategy
from strategy import CANDIDATE_STRATEGIES
from animal_model import ANIMAL_TYPES
from crop_model import CROP_TYPES

tracker = MarketTracker()
current_strategy = CANDIDATE_STRATEGIES[0]

def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Kaggle submission entry point."""
    global current_strategy

    world: WorldState = parse_observation(obs)
    my_farm = world.my_farm
    opp_farm = world.opp_farm
    private = world.private
    market = world.market

    tracker.update(world)
    market_orders: List[List[Any]] = []

    is_endgame = world.day >= 25

    # ==========================================
    # 1. DAILY STRATEGY RE-EVALUATION (Hour 0)
    # ==========================================
    if world.hour == 0:
        num_animals = sum(private.shed.get(a, 0) for a in ["GOOSE", "COW", "SHEEP"]) + len(my_farm.structure_tiles)
        wheat_in_shed = private.shed.get("WHEAT", 0)
        
        current_strategy = best_strategy(
            current_day=world.day,
            current_money=my_farm.money,
            num_empty_tiles=len(my_farm.empty_tiles),
            num_animals=num_animals,
            tracker=tracker,
            wheat_in_shed=wheat_in_shed,
        )

        # Hired hands expire at end of each day; re-hire them
        if not is_endgame and current_strategy.hire_workers:
            num_hires = 5 if my_farm.money >= 50 else (3 if my_farm.money >= 20 else 1)
            for _ in range(num_hires):
                market_orders.append(ae.hire_order())

    # Count animals to calculate wheat feed reserve
    num_animals = len(my_farm.structure_tiles) + sum(
        private.shed.get(a, 0) for a in ["GOOSE", "COW", "SHEEP"]
    ) + sum(
        w.inventory.get(a, 0) for w in my_farm.all_workers for a in ["GOOSE", "COW", "SHEEP"]
    )
    wheat_reserve = num_animals * 3 if not is_endgame else 0
    wheat_in_shed = private.shed.get("WHEAT", 0)

    # ==========================================
    # 2. MARKET SELLING (Sell produce from shed)
    # ==========================================
    for good, count in private.shed.items():
        if count > 0 and good in (
            "MELON", "WOOL", "MILK", "EGG", "STRAWBERRY", "TOMATO", "CARROT", "FERTILIZER"
        ):
            price = market.price_of(good)
            sell_qty = tracker.should_sell(good, count, price, is_endgame=is_endgame)
            if sell_qty > 0:
                market_orders.append(ae.sell_order(good, sell_qty))

    # Sell surplus wheat beyond animal feed reserve
    available_wheat = wheat_in_shed if is_endgame else max(0, wheat_in_shed - wheat_reserve)
    if available_wheat > 0:
        sell_qty = tracker.should_sell("WHEAT", available_wheat, market.price_of("WHEAT"), is_endgame=is_endgame)
        if sell_qty > 0:
            market_orders.append(ae.sell_order("WHEAT", sell_qty))

    # ==========================================
    # 3. MARKET PURCHASES (Feed, Seeds, Animals, Land)
    # ==========================================
    if not is_endgame:
        projected_money = my_farm.money
        
        # Replenish wheat feed if running low
        if wheat_in_shed < wheat_reserve and projected_money >= 100:
            shortfall = wheat_reserve - wheat_in_shed
            buy_qty = min(shortfall, 5)
            if buy_qty > 0:
                market_orders.append(ae.buy_product_order("WHEAT", buy_qty))
                projected_money -= buy_qty * market.price_of("WHEAT")

        # Dynamic Animal Purchasing
        if current_strategy.buy_animals:
            sheep_cost = ANIMAL_TYPES["SHEEP"].cost
            cow_cost = ANIMAL_TYPES["COW"].cost
            if projected_money >= cow_cost + 500:
                market_orders.append(ae.buy_animal_order("COW", 1))
                projected_money -= cow_cost
            elif projected_money >= sheep_cost + 500:
                market_orders.append(ae.buy_animal_order("SHEEP", 1))
                projected_money -= sheep_cost

        # Expand farm land when running out of space
        if projected_money >= 1000 + 500 and len(my_farm.unlocked_quadrants) < 4:
            if len(my_farm.empty_tiles) < 5:
                market_orders.append(ae.buy_land_order())
                projected_money -= 1000

        # Replenish seeds
        focus_crop = current_strategy.focus_crop
        if not focus_crop:
            focus_crop = tracker.best_crop_to_plant(projected_money)

        if focus_crop:
            crop_info = CROP_TYPES.get(focus_crop)
            if crop_info:
                seeds_owned = private.seeds.get(focus_crop, 0)
                empty_count = len(my_farm.empty_tiles)
                target_seeds = min(max(6, empty_count), 15)
                if seeds_owned < target_seeds and projected_money >= crop_info.seed_cost:
                    buy_count = min(target_seeds - seeds_owned, int(projected_money // crop_info.seed_cost))
                    if buy_count > 0:
                        market_orders.append(ae.buy_seed_order(focus_crop, buy_count))
                        projected_money -= buy_count * crop_info.seed_cost

    # ==========================================
    # 4. TASK GENERATION & WORKER ASSIGNMENT
    # ==========================================
    default_crop = current_strategy.focus_crop or tracker.best_crop_to_plant(my_farm.money) or "WHEAT"
    tasks = generate_tasks(world, default_crop=default_crop)

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
        # Ensure we don't exceed the 10 market order limit
        market_orders=market_orders[:10],
        expected_hands_count=len(my_farm.hands),
    )
