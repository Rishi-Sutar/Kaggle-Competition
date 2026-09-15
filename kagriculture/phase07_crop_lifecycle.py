"""
Phase 0.7 — Full Crop Lifecycle Test.
Verifies:
1. Buy WHEAT seeds ($10/seed)
2. Plant on adjacent tile (e.g. 3, 4)
3. Move to crop tile each morning (since farmer respawns at (4,4) at hour 0)
4. Water daily for days 0, 1, 2, 3, 4
5. Observe yield_units grow to 4 (peak unfertilized yield)
6. Harvest at day 4 (yield goes into farmer's inventory)
7. Walk back to shed tile (4,4) and drop, or wait for end-of-day drop into shed
8. Sell WHEAT at market for dynamic price
9. Measure net profit
"""
import sys, os
sys.path.insert(0, os.getcwd())
from kaggle_environments import make

def get_farm(obs):
    return obs["farms"][obs["player"]]

def wheat_lifecycle_agent(obs):
    step = obs.get("step", 0)
    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    farm = get_farm(obs)
    fx, fy = farm["farmer"] # x is col, y is row
    money = farm["money"]
    private = obs["private"]
    seeds = private["seeds"]
    shed = private["shed"]
    inventories = private["inventories"]
    farmer_inv = inventories[0] if inventories else {}
    
    # We choose tile (3, 4) — x=3, y=4 (one step WEST from shed (4,4))
    crop_x, crop_y = 3, 4
    crop_tile = farm["tiles"][crop_y][crop_x]
    
    action = {"farmer": ["PASS"], "hands": [], "market": []}
    
    # Step 0: Buy 1 wheat seed ($10)
    if step == 0:
        action["market"] = [["BUY_SEED", "WHEAT", 1]]
        return action
        
    # Day 0, Hour 1: Move WEST to (3,4)
    if day == 0 and hour == 1:
        action["farmer"] = ["WEST"]
        return action
        
    # Day 0, Hour 2: Plant WHEAT
    if day == 0 and hour == 2:
        action["farmer"] = ["PLANT", "WHEAT"]
        return action
        
    # Day 0, Hour 3: Water WHEAT
    if day == 0 and hour == 3:
        action["farmer"] = ["WATER"]
        return action
        
    # For subsequent days:
    # At hour 0, farmer is at (4,4).
    # At hour 1, move WEST to (3,4).
    # At hour 2, WATER if not watered today.
    # At Day 4 (max yield day = 4), HARVEST!
    # At Day 4, Hour 3: Move EAST to (4,4) (shed adjacent) and DROP, then SELL!
    
    if hour == 0:
        # Farmer just respawned at (4,4). If we have wheat in shed, sell it!
        if shed.get("WHEAT", 0) > 0:
            action["market"] = [["SELL", "WHEAT", shed.get("WHEAT", 0)]]
        return action

    if hour == 1:
        if (fx, fy) != (crop_x, crop_y):
            action["farmer"] = ["WEST"]
            return action
            
    if (fx, fy) == (crop_x, crop_y):
        # We are on the crop tile
        if isinstance(crop_tile, dict) and crop_tile.get("kind") == "PLANT":
            # Check if Day >= 4 -> Peak harvest time!
            if day >= 4:
                action["farmer"] = ["HARVEST"]
                return action
            elif not crop_tile.get("watered_today"):
                action["farmer"] = ["WATER"]
                return action
        elif farmer_inv.get("WHEAT", 0) > 0:
            # We harvested! Move back to shed (4,4)
            action["farmer"] = ["EAST"]
            return action

    if (fx, fy) == (4, 4) and farmer_inv.get("WHEAT", 0) > 0:
        # We are at shed, drop inventory
        action["farmer"] = ["DROP"]
        return action

    if shed.get("WHEAT", 0) > 0:
        action["market"] = [["SELL", "WHEAT", shed.get("WHEAT", 0)]]
        return action

    return action

print("Running 125-step full wheat lifecycle experiment...")
env = make("kaggriculture", configuration={"episodeSteps": 125, "seed": 42}, debug=True)

steps_data = env.run([wheat_lifecycle_agent, "pass"])

print("Experiment completed. Analyzing timeline:")
for i, step_state in enumerate(steps_data):
    obs = step_state[0].observation
    farm = obs["farms"][0]
    fx, fy = farm["farmer"]
    crop_tile = farm["tiles"][4][3] # y=4, x=3
    priv = obs["private"]
    shed_wheat = priv["shed"].get("WHEAT", 0)
    farmer_wheat = priv["inventories"][0].get("WHEAT", 0) if priv["inventories"] else 0
    money = farm["money"]
    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    
    # Print key moments (hour 0, 1, 2, 3, 4)
    if hour in (0, 1, 2, 3, 4) and day in (0, 1, 2, 3, 4, 5):
        print(f"Step {i:3d} (d{day} h{hour:02d}) | Pos: ({fx},{fy}) | Money: ${money:.1f} | Tile(3,4): {crop_tile} | FarmerInv: {farmer_wheat} | Shed: {shed_wheat}")

print(f"\nFinal State at step {len(steps_data)-1}:")
final_farm = steps_data[-1][0].observation["farms"][0]
print(f"Final Money: ${final_farm['money']}")
print(f"Net Profit: ${final_farm['money'] - 3000:.2f}")
