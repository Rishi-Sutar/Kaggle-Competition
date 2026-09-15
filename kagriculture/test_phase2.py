"""
Test suite for Phase 2: pathfinding.py and action_engine.py
"""
import sys, os
sys.path.insert(0, os.getcwd())
from kaggle_environments import make
from pathfinding import manhattan_distance, next_move, bfs_path, path_to_directions
import action_engine as ae

def test_pathfinding():
    print("Testing pathfinding.py...")
    # Distance checks
    assert manhattan_distance((4, 4), (4, 4)) == 0
    assert manhattan_distance((4, 4), (5, 4)) == 1
    assert manhattan_distance((0, 0), (9, 9)) == 18
    
    # Next move checks
    assert next_move((4, 4), (3, 4)) == "WEST"
    assert next_move((4, 4), (5, 4)) == "EAST"
    assert next_move((4, 4), (4, 3)) == "NORTH"
    assert next_move((4, 4), (4, 5)) == "SOUTH"
    assert next_move((4, 4), (4, 4)) is None
    
    # BFS path checks
    path = bfs_path((0, 0), (2, 2))
    assert len(path) == 5
    assert path[0] == (0, 0)
    assert path[-1] == (2, 2)
    dirs = path_to_directions(path)
    assert len(dirs) == 4
    
    # BFS with blocked cells
    blocked = {(1, 0), (0, 1)}
    path_blocked = bfs_path((0, 0), (2, 2), blocked=blocked)
    # Since all neighbors of (0,0) are blocked, should return []
    assert path_blocked == []
    print("pathfinding.py checks passed!")

def test_action_engine():
    print("Testing action_engine.py...")
    # Helpers
    assert ae.move_action("NORTH") == ["NORTH"]
    assert ae.plant_action("WHEAT") == ["PLANT", "WHEAT"]
    assert ae.water_action() == ["WATER"]
    assert ae.harvest_action() == ["HARVEST"]
    assert ae.buy_seed_order("WHEAT", 5) == ["BUY_SEED", "WHEAT", 5]
    assert ae.sell_order("WHEAT", 3) == ["SELL", "WHEAT", 3]
    assert ae.hire_order() == ["HIRE"]
    assert ae.buy_land_order() == ["BUY_LAND"]
    
    # make_action
    act = ae.make_action(
        farmer_action=ae.water_action(),
        hands_actions=[ae.pass_worker_action()],
        market_orders=[ae.buy_seed_order("WHEAT", 1)] * 15,  # 15 orders
        expected_hands_count=2
    )
    assert act["farmer"] == ["WATER"]
    assert len(act["hands"]) == 2  # Padded to expected_hands_count
    assert len(act["market"]) == 10  # Capped at 10
    
    # pass_action
    pass_act = ae.pass_action(hands_count=3)
    assert pass_act["farmer"] == ["PASS"]
    assert len(pass_act["hands"]) == 3
    assert pass_act["market"] == []
    print("action_engine.py checks passed!")

def test_live_execution():
    print("Testing live execution in environment...")
    env = make("kaggriculture", configuration={"episodeSteps": 20, "seed": 42}, debug=True)
    
    target_route = [(4, 4), (4, 3), (3, 3), (2, 3), (2, 4)]
    
    def test_agent(obs):
        step = obs.get("step", 0)
        farm = obs["farms"][obs["player"]]
        curr_pos = tuple(farm["farmer"])
        
        market_orders = []
        if step == 0:
            market_orders.append(ae.buy_seed_order("CARROT", 2))
            
        target = target_route[min(step, len(target_route) - 1)]
        mv = next_move(curr_pos, target)
        farmer_act = ae.move_action(mv) if mv else ae.pass_worker_action()
        
        return ae.make_action(farmer_act, market_orders=market_orders, expected_hands_count=len(farm["hands"]))
        
    env.run([test_agent, "random"])
    print("Live execution completed successfully without any errors!")

if __name__ == "__main__":
    test_pathfinding()
    test_action_engine()
    test_live_execution()
    print("ALL PHASE 2 TESTS PASSED!")
