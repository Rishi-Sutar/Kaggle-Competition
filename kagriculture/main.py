"""
Main Agent for Kaggriculture — Phase 9: Coordinated Multi-Worker Pipeline.
Based on high-ELO replay insights and game engine rules:
- Day 0 Blitz: Spend starting capital on 5 workers, 2 Cows, 2 Sheep, Wheat feed, and Melon seeds
- Daily Morning Re-Hire: Every morning at hour 0, hire 5 workers ($12 total) to maintain 6-unit team
- Coordinated Multi-Step Tasks: Pickup animals/wheat at shed (4,4), place structures, feed, care, water, harvest, and drop off
- Scale & Reinvest: Sell high-value products (Milk, Wool, Melon), expand land with BUY_LAND, and maintain feed
"""
from typing import Any, Dict, List, Optional
from world_state import parse_observation, WorldState
from task_manager import generate_tasks, execute_worker_task, assign_tasks
from optimizer import optimize_assignments
import action_engine as ae
from market_model import MarketTracker

tracker = MarketTracker()
blitz_executed = False


def compute_blitz_orders(market_prices: Dict[str, int], money: float) -> List[List[Any]]:
    """
    Day 0 Blitz: Hire 5 workers, buy 2 Cows, 2 Sheep, 6 Wheat feed, and Melon seeds.
    Cost breakdown:
      - 5 Hires: 1 + 1 + 2 + 3 + 5 = $12
      - 2 Cows: $800
      - 2 Sheep: $1,000
      - 6 Wheat feed: $150
      - 8 Melon seeds: $640
      Total: ~$2,602 (within starting $3,000 budget)
    """
    orders = []
    # 1. 5 Hires
    for _ in range(5):
        orders.append(ae.hire_order())
    # 2. 2 Cows & 2 Sheep
    orders.append(ae.buy_animal_order("COW", 2))
    orders.append(ae.buy_animal_order("SHEEP", 2))
    # 3. 6 Wheat for animal feed
    orders.append(ae.buy_product_order("WHEAT", 6))
    # 4. Melon seeds (up to 8)
    orders.append(ae.buy_seed_order("MELON", 8))
    return orders[:10]


def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Kaggle submission entry point."""
    global blitz_executed

    world: WorldState = parse_observation(obs)
    my_farm = world.my_farm
    opp_farm = world.opp_farm
    private = world.private
    market = world.market

    tracker.update(market.prices, market.inventory)
    market_orders: List[List[Any]] = []

    # ==========================================
    # 1. DAY 0 BLITZ (First turn)
    # ==========================================
    if world.step == 0 and not blitz_executed:
        blitz_executed = True
        orders = compute_blitz_orders(market.prices, my_farm.money)
        return ae.make_action(
            farmer_action=["PASS"],
            hands_actions=[],
            market_orders=orders,
            expected_hands_count=0,
        )

    is_endgame = world.day >= 25

    # ==========================================
    # 2. DAILY MORNING WORKER RE-HIRE (Hour 0)
    # ==========================================
    # Hired hands expire at end of each day; cost resets to 1, 1, 2, 3, 5 ($12 total for 5)
    if world.hour == 0 and world.step > 0 and not is_endgame:
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

    # ==========================================
    # 3. MARKET SELLING (Sell produce from shed)
    # ==========================================
    for good, count in private.shed.items():
        if count > 0 and good in (
            "MELON", "WOOL", "MILK", "EGG", "STRAWBERRY", "TOMATO", "CARROT", "FERTILIZER"
        ):
            price = market.price_of(good)
            sell_qty = count if is_endgame else tracker.should_sell(good, count, price)
            if sell_qty > 0:
                market_orders.append(ae.sell_order(good, sell_qty))

    # Sell surplus wheat beyond animal feed reserve
    wheat_in_shed = private.shed.get("WHEAT", 0)
    available_wheat = wheat_in_shed if is_endgame else max(0, wheat_in_shed - wheat_reserve)
    if available_wheat > 0:
        sell_qty = available_wheat if is_endgame else tracker.should_sell("WHEAT", available_wheat, market.price_of("WHEAT"))
        if sell_qty > 0:
            market_orders.append(ae.sell_order("WHEAT", sell_qty))

    # ==========================================
    # 4. MARKET PURCHASES (Feed, Seeds, Land)
    # ==========================================
    if not is_endgame:
        # Replenish wheat feed if running low
        if wheat_in_shed < wheat_reserve and my_farm.money >= 100:
            shortfall = wheat_reserve - wheat_in_shed
            buy_qty = min(shortfall, 5)
            if buy_qty > 0:
                market_orders.append(ae.buy_product_order("WHEAT", buy_qty))

        # Expand farm land when wealthy
        if my_farm.money >= 2200 and len(my_farm.unlocked_quadrants) < 4:
            market_orders.append(ae.buy_land_order())

        # Replenish seeds based on harvest horizon:
        # Days 0-19: Melons (10 days to mature)
        # Days 20-26: Carrots or Wheat (2 days to mature)
        # Days 27+: Stop buying seeds, liquidate
        empty_count = len(my_farm.empty_tiles)
        if world.day <= 19:
            melon_seeds = private.seeds.get("MELON", 0)
            target_melons = min(max(6, empty_count), 12)
            if melon_seeds < target_melons and my_farm.money >= 300:
                buy_count = min(target_melons - melon_seeds, int((my_farm.money - 150) // 80))
                if buy_count > 0:
                    market_orders.append(ae.buy_seed_order("MELON", buy_count))
        elif world.day <= 26:
            carrot_seeds = private.seeds.get("CARROT", 0)
            target_carrots = min(empty_count, 10)
            if carrot_seeds < target_carrots and my_farm.money >= 100:
                buy_count = min(target_carrots - carrot_seeds, int(my_farm.money // 20))
                if buy_count > 0:
                    market_orders.append(ae.buy_seed_order("CARROT", buy_count))

    # ==========================================
    # 5. TASK GENERATION & WORKER ASSIGNMENT
    # ==========================================
    default_crop = "CARROT" if world.day >= 20 else "MELON"
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
        market_orders=market_orders[:10],
        expected_hands_count=len(my_farm.hands),
    )
