"""
Test suite for world_state.py
Verifies parsing against live Kaggle environments steps.
"""
import sys, os
sys.path.insert(0, os.getcwd())
from kaggle_environments import make
from world_state import parse_observation, WorldState, TileState, WorkerState

def test_world_state_parser():
    print("Testing world_state.py on live game...")
    env = make("kaggriculture", configuration={"episodeSteps": 48, "seed": 42}, debug=True)
    
    parsed_states = []
    
    def test_agent(obs):
        ws = parse_observation(obs)
        parsed_states.append(ws)
        
        # Verify basic types and properties
        assert isinstance(ws, WorldState)
        assert ws.player_id in (0, 1)
        assert ws.opponent_id == 1 - ws.player_id
        assert ws.step == obs.get("step", 0)
        assert ws.day == obs.get("day", 0)
        assert ws.hour == obs.get("hour", 0)
        assert ws.my_farm.money == obs["farms"][obs["player"]]["money"]
        assert ws.my_farm.farmer.x == obs["farms"][obs["player"]]["farmer"][0]
        assert ws.my_farm.farmer.y == obs["farms"][obs["player"]]["farmer"][1]
        
        # Verify grid dimensions
        assert len(ws.my_farm.grid) == 10
        assert len(ws.my_farm.grid[0]) == 10
        
        # Verify tile parsing
        raw_tiles = obs["farms"][obs["player"]]["tiles"]
        total_tiles_counted = (
            len(ws.my_farm.empty_tiles) +
            len(ws.my_farm.plant_tiles) +
            len(ws.my_farm.weed_tiles) +
            len(ws.my_farm.structure_tiles) +
            sum(1 for row in ws.my_farm.grid for t in row if t.is_locked)
        )
        assert total_tiles_counted == 100, f"Expected 100 tiles total, got {total_tiles_counted}"
        
        # Test get_tile
        assert ws.my_farm.get_tile(4, 4) is not None
        assert ws.my_farm.get_tile(99, 99) is None
        
        # Market and private checks
        assert ws.market.price_of("WHEAT") == obs["market"]["prices"]["WHEAT"]
        assert ws.private.seeds == obs["private"]["seeds"]
        assert ws.private.shed == obs["private"]["shed"]
        
        # Take some actions to create variety of tiles:
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 2]]}
        elif step == 1:
            return {"farmer": ["WEST"], "hands": [], "market": []}
        elif step == 2:
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
        elif step == 3:
            return {"farmer": ["WATER"], "hands": [], "market": []}
        
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env.run([test_agent, "random"])
    
    print(f"Successfully verified {len(parsed_states)} steps without any errors!")
    
    # Check that planting was parsed properly in later steps
    last_ws = parsed_states[-1]
    print(f"Final state: step={last_ws.step}, day={last_ws.day}, hour={last_ws.hour}")
    print(f"  Empty tiles: {len(last_ws.my_farm.empty_tiles)}")
    print(f"  Plant tiles: {len(last_ws.my_farm.plant_tiles)}")
    print(f"  Unwatered crop tiles: {len(last_ws.my_farm.unwatered_crop_tiles)}")
    print(f"  Ready to harvest tiles: {len(last_ws.my_farm.ready_to_harvest_tiles)}")
    print(f"  Weed tiles: {len(last_ws.my_farm.weed_tiles)}")
    print(f"  Farmer pos: {last_ws.my_farm.farmer.pos}")
    print(f"  Shed occupied: {last_ws.private.shed_occupied}")
    print(f"  Total seeds: {last_ws.private.total_seeds}")
    print(f"  Unlocked shops: {last_ws.town.unlocked_shops}")
    
    assert len(last_ws.my_farm.plant_tiles) >= 1, "Expected at least 1 plant tile parsed!"
    print("ALL CHECKS PASSED! Phase 1 is fully functional.")

if __name__ == "__main__":
    test_world_state_parser()
