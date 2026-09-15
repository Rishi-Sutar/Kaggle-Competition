"""
Phase 0.6 — CORRECTED action format testing.
Now using the ACTUAL format from the environment spec:

Action format:
{
    "farmer": [op, ...args],         # ONE action for the farmer (list, not string!)
    "hands": [[op, ...args], ...],   # One action per hand (list of lists)
    "market": [[op, ...args], ...]   # Market orders (list of lists)
}

Movement: NORTH, SOUTH, EAST, WEST (NOT UP, DOWN, LEFT, RIGHT!)
Farmer ops: NORTH, SOUTH, EAST, WEST, PASS, PICKUP <item> [n],
            PLANT <crop>, WATER, HARVEST, FERTILIZE, BUILD_COOP,
            BUILD_PASTURE, DIG, PLACE <item> [n], FEED,
            COLLECT_FERTILIZER, CARE
Market ops: BUY_SEED <crop> <n>, BUY_PRODUCT <item> <n>,
            BUY_ANIMAL <animal> <n>, SELL <item> <n>, HIRE, BUY_LAND
"""
import sys, os
sys.path.insert(0, os.getcwd())
from kaggle_environments import make

def run_experiment(agent_fn, steps=48, seed=42):
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed}, debug=True)
    return env.run([agent_fn, lambda obs: {"farmer": ["PASS"], "hands": [], "market": []}])

def get_farm(obs):
    return obs["farms"][obs["player"]]

# ====================================================================
# 0.6a — MOVE (NORTH/SOUTH/EAST/WEST)
# ====================================================================
print("=" * 70)
print("0.6a — MOVE (corrected: NORTH/SOUTH/EAST/WEST)")
print("=" * 70)

move_log = []
def move_agent(obs):
    step = obs.get("step", 0)
    farm = get_farm(obs)
    pos = tuple(farm["farmer"])
    move_log.append({"step": step, "pos": pos})

    moves = {
        0: ["WEST"],   # Move west (col-1)
        1: ["WEST"],
        2: ["NORTH"],  # Move north (row-1)
        3: ["NORTH"],
        4: ["EAST"],   # Move east (col+1)
        5: ["SOUTH"],  # Move south (row+1)
    }
    action = moves.get(step, ["PASS"])
    return {"farmer": action, "hands": [], "market": []}

run_experiment(move_agent, steps=12)
print("  Movement sequence:")
for e in move_log:
    print(f"    Step {e['step']}: pos = {e['pos']}")

# ====================================================================
# 0.6b — BUY_SEED (market action, note: BUY_SEED not BUY_SEEDS)
# ====================================================================
print("\n" + "=" * 70)
print("0.6b — BUY_SEED (market action)")
print("=" * 70)

seed_log = []
def buy_seed_agent(obs):
    step = obs.get("step", 0)
    farm = get_farm(obs)
    seed_log.append({
        "step": step,
        "money": farm["money"],
        "seeds": dict(obs["private"]["seeds"]),
    })

    market = []
    if step == 0:
        market = [["BUY_SEED", "WHEAT", 5]]
    elif step == 1:
        market = [["BUY_SEED", "CARROT", 3]]
    elif step == 2:
        market = [["BUY_SEED", "TOMATO", 2]]
    elif step == 3:
        market = [["BUY_SEED", "STRAWBERRY", 2]]
    elif step == 4:
        market = [["BUY_SEED", "MELON", 1]]

    return {"farmer": ["PASS"], "hands": [], "market": market}

run_experiment(buy_seed_agent, steps=12)
print("  Buy seed sequence:")
for e in seed_log:
    print(f"    Step {e['step']}: money=${e['money']}, seeds={e['seeds']}")

# Calculate costs
print("\n  Seed costs:")
for i in range(1, min(6, len(seed_log))):
    cost = seed_log[i-1]["money"] - seed_log[i]["money"]
    if cost != 0:
        print(f"    Step {i}: cost ${cost}")

# ====================================================================
# 0.6c — PLANT (farmer action, must be on empty tile with seeds)
# ====================================================================
print("\n" + "=" * 70)
print("0.6c — PLANT + WATER + HARVEST lifecycle")
print("=" * 70)

life_log = []
def lifecycle_agent(obs):
    step = obs.get("step", 0)
    farm = get_farm(obs)
    pos = tuple(farm["farmer"])
    tile_here = farm["tiles"][pos[0]][pos[1]]
    shed = dict(obs["private"]["shed"])
    seeds = dict(obs["private"]["seeds"])

    life_log.append({
        "step": step,
        "day": obs.get("day"),
        "hour": obs.get("hour"),
        "money": farm["money"],
        "pos": pos,
        "tile_here": tile_here,
        "seeds": seeds,
        "shed_wheat": shed.get("WHEAT", 0),
    })

    # Step 0: Buy wheat seeds
    if step == 0:
        return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 5]]}
    # Steps 1-4: Move to (0,0) from (4,4)
    if step == 1: return {"farmer": ["NORTH"], "hands": [], "market": []}
    if step == 2: return {"farmer": ["NORTH"], "hands": [], "market": []}
    if step == 3: return {"farmer": ["NORTH"], "hands": [], "market": []}
    if step == 4: return {"farmer": ["NORTH"], "hands": [], "market": []}
    # Steps 5-8: Move west
    if step == 5: return {"farmer": ["WEST"], "hands": [], "market": []}
    if step == 6: return {"farmer": ["WEST"], "hands": [], "market": []}
    if step == 7: return {"farmer": ["WEST"], "hands": [], "market": []}
    if step == 8: return {"farmer": ["WEST"], "hands": [], "market": []}
    # Step 9: Plant wheat
    if step == 9:
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
    # Steps 10+: Water every step, try harvest when ready
    if step >= 10:
        if isinstance(tile_here, dict):
            # Check if harvestable
            gs = tile_here.get("growth_stage", 0)
            mg = tile_here.get("max_growth", 999)
            if gs >= mg:
                return {"farmer": ["HARVEST"], "hands": [], "market": []}
        return {"farmer": ["WATER"], "hands": [], "market": []}

    return {"farmer": ["PASS"], "hands": [], "market": []}

run_experiment(lifecycle_agent, steps=200)

print("  Crop lifecycle:")
prev_tile = None
for e in life_log:
    tile = e["tile_here"]
    if tile != prev_tile or e["step"] <= 10 or e["step"] % 24 == 0 or e["shed_wheat"] > 0:
        print(f"    Step {e['step']:3d} (d{e['day']}h{e['hour']:02d}): pos={e['pos']}, tile={tile}, seeds={e['seeds']}, shed_wheat={e['shed_wheat']}")
        prev_tile = tile

# ====================================================================
# 0.6d — HIRE (market action)
# ====================================================================
print("\n" + "=" * 70)
print("0.6d — HIRE")
print("=" * 70)

hire_log = []
def hire_agent(obs):
    step = obs.get("step", 0)
    farm = get_farm(obs)
    hire_log.append({
        "step": step,
        "money": farm["money"],
        "hands": len(farm["hands"]),
        "hires_today": farm["hires_today"],
        "hand_positions": [tuple(h) for h in farm["hands"]] if farm["hands"] else [],
    })

    market = []
    if step == 0:
        market = [["HIRE"]]
    elif step == 1:
        market = [["HIRE"]]
    elif step == 2:
        market = [["HIRE"]]

    hands_actions = [["PASS"] for _ in farm["hands"]]
    return {"farmer": ["PASS"], "hands": hands_actions, "market": market}

run_experiment(hire_agent, steps=12)
print("  Hire sequence:")
for e in hire_log:
    print(f"    Step {e['step']}: money=${e['money']}, hands={e['hands']}, hires_today={e['hires_today']}, positions={e['hand_positions']}")

# ====================================================================
# 0.6e — BUY_ANIMAL + PLACE + FEED + CARE
# ====================================================================
print("\n" + "=" * 70)
print("0.6e — BUY_ANIMAL + PLACE + FEED + CARE")
print("=" * 70)

animal_log = []
def animal_agent(obs):
    step = obs.get("step", 0)
    farm = get_farm(obs)
    pos = tuple(farm["farmer"])
    shed = dict(obs["private"]["shed"])
    tile_here = farm["tiles"][pos[0]][pos[1]]

    animal_log.append({
        "step": step,
        "money": farm["money"],
        "pos": pos,
        "shed_sheep": shed.get("SHEEP", 0),
        "shed_wheat": shed.get("WHEAT", 0),
        "shed_wool": shed.get("WOOL", 0),
        "tile_here": tile_here,
    })

    # Buy sheep + wheat for feed
    if step == 0:
        return {"farmer": ["PASS"], "hands": [], "market": [["BUY_ANIMAL", "SHEEP", 1], ["BUY_SEED", "WHEAT", 5]]}
    # Move to (0,0)
    if step == 1: return {"farmer": ["NORTH"], "hands": [], "market": []}
    if step == 2: return {"farmer": ["NORTH"], "hands": [], "market": []}
    if step == 3: return {"farmer": ["NORTH"], "hands": [], "market": []}
    if step == 4: return {"farmer": ["NORTH"], "hands": [], "market": []}
    if step == 5: return {"farmer": ["WEST"], "hands": [], "market": []}
    if step == 6: return {"farmer": ["WEST"], "hands": [], "market": []}
    if step == 7: return {"farmer": ["WEST"], "hands": [], "market": []}
    if step == 8: return {"farmer": ["WEST"], "hands": [], "market": []}
    # Build pasture first, then place sheep
    if step == 9:
        return {"farmer": ["BUILD_PASTURE"], "hands": [], "market": []}
    if step == 10:
        return {"farmer": ["PLACE", "SHEEP"], "hands": [], "market": []}
    # Feed + care cycle
    if step == 11:
        return {"farmer": ["FEED"], "hands": [], "market": []}
    if step == 12:
        return {"farmer": ["CARE"], "hands": [], "market": []}
    # Keep feeding/caring
    if step >= 13 and step % 2 == 1:
        return {"farmer": ["FEED"], "hands": [], "market": []}
    if step >= 13 and step % 2 == 0:
        return {"farmer": ["CARE"], "hands": [], "market": []}

    return {"farmer": ["PASS"], "hands": [], "market": []}

run_experiment(animal_agent, steps=100)

print("  Animal sequence:")
prev_tile = None
for e in animal_log:
    tile = e["tile_here"]
    if tile != prev_tile or e["step"] <= 13 or e["shed_wool"] > 0 or e["step"] % 24 == 0:
        print(f"    Step {e['step']:3d}: money=${e['money']}, pos={e['pos']}, sheep={e['shed_sheep']}, wheat={e['shed_wheat']}, wool={e['shed_wool']}, tile={tile}")
        prev_tile = tile

# ====================================================================
# 0.6f — BUY_LAND + SELL
# ====================================================================
print("\n" + "=" * 70)
print("0.6f — BUY_LAND + SELL")
print("=" * 70)

land_log = []
def land_agent(obs):
    step = obs.get("step", 0)
    farm = get_farm(obs)
    land_log.append({
        "step": step,
        "money": farm["money"],
        "quadrants": list(farm["unlocked_quadrants"]),
    })

    if step == 0:
        return {"farmer": ["PASS"], "hands": [], "market": [["BUY_LAND"]]}
    return {"farmer": ["PASS"], "hands": [], "market": []}

run_experiment(land_agent, steps=6)
print("  BUY_LAND sequence:")
for e in land_log:
    print(f"    Step {e['step']}: money=${e['money']}, quadrants={e['quadrants']}")

print("\n" + "=" * 70)
print("PHASE 0.6 COMPLETE")
print("=" * 70)
