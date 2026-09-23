# Kaggriculture — Step-by-Step Implementation Plan

> This plan is written to be followed **literally, one phase at a time**. Each phase has exact file names, exact function signatures, exact code, and explicit checkpoints. **Do not skip phases. Do not combine phases. Complete one, verify it, then move to the next.**

---

## Ground Truth Facts

| Fact | Value |
|------|-------|
| Game length | 720 turns (30 days × 24 turns/day) |
| Starting capital | $3,000 |
| Grid size | 10×10 (only NW 5×5 active initially) |
| Shed capacity | 100 non-seed items; overflow discarded at end of day |
| Players | 2 |
| Scoring | Terminal bank capital (money at game end) |
| Observations per step | 2 (one per player) |
| Competitor code | Not available |

---

## Project Structure (Final Target)

```text
kagriculture/
├── kagriculture.ipynb          # Experiment notebook
├── main.py                     # Kaggle submission entry point
├── world_state.py              # WorldState dataclasses
├── action_engine.py            # Action creation + validation
├── task_manager.py             # Task generation + worker assignment
├── pathfinding.py              # BFS movement
├── market_model.py             # Market price tracking + prediction
├── crop_model.py               # Crop profitability calculations
├── animal_model.py             # Animal management logic
├── strategy.py                 # Strategic planner (Approach B)
├── simulator.py                # Future simulator (Approach B)
└── optimizer.py                # OR-Tools scheduler (Approach C)
```

> **Do NOT create all these files upfront.** Create each file only when its phase arrives.

---

# PHASE 0 — Environment Reconnaissance

## Status: Experiments 0.1–0.3 DONE. Continue from 0.4.

---

## Phase 0.4 — Clock Analysis

### Goal
Determine the exact relationship between `step`, `day`, and `hour`.

### What to do in the notebook

Add a new cell with this exact heading:

```python
# ============================================================
# Phase 0.4 — Clock Analysis
# ============================================================
# Question: What is the exact relationship between step, day, hour?
# Setup: PASS/PASS for 96 steps (4 days)
```

Then run this experiment:

```python
# Step 1: Run a longer PASS/PASS game
history = []

def clock_agent(obs):
    history.append({
        "step": obs.get("step"),
        "day": obs.get("day"),
        "hour": obs.get("hour"),
    })
    return {"farmer": ["PASS"], "market": []}

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 96, "seed": 42},
    debug=True,
)
result = env.run([clock_agent, clock_agent])
```

```python
# Step 2: Deduplicate (we get 2 observations per step)
import pandas as pd

clock_df = pd.DataFrame(history)
clock_unique = clock_df.drop_duplicates(subset=["step"]).reset_index(drop=True)
print(clock_unique.to_string())
```

```python
# Step 3: Verify the formula
clock_unique["computed_day"] = clock_unique["step"] // 24
clock_unique["computed_hour"] = clock_unique["step"] % 24
clock_unique["day_match"] = clock_unique["day"] == clock_unique["computed_day"]
clock_unique["hour_match"] = clock_unique["hour"] == clock_unique["computed_hour"]

print("All days match:", clock_unique["day_match"].all())
print("All hours match:", clock_unique["hour_match"].all())
```

### Expected result
- `day = step // 24`
- `hour = step % 24`

### Checkpoint
Write a conclusion cell:

```python
# Conclusion 0.4:
# day = step // 24
# hour = step % 24
# Confirmed: [YES/NO]
```

> **STOP HERE. Verify the result. Only proceed to 0.5 if confirmed.**

---

## Phase 0.5 — Autonomous Market Behavior

### Goal
Determine exactly how market inventory and prices change when nobody acts.

### What to do in the notebook

```python
# ============================================================
# Phase 0.5 — Autonomous Market Behavior
# ============================================================
# Question: How do market inventory and prices change with no player actions?
```

```python
# Step 1: Run PASS/PASS for 720 steps (full game) and record market data
market_history = []

def market_probe_agent(obs):
    market_history.append({
        "step": obs.get("step"),
        "day": obs.get("day"),
        "hour": obs.get("hour"),
        "inventory": dict(obs["market"]["inventory"]),
        "prices": dict(obs["market"]["prices"]),
    })
    return {"farmer": ["PASS"], "market": []}

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720, "seed": 42},
    debug=True,
)
result = env.run([market_probe_agent, market_probe_agent])
print(f"Collected {len(market_history)} observations")
```

```python
# Step 2: Build a clean DataFrame (one row per step)
mdf = pd.DataFrame(market_history)
mdf = mdf.drop_duplicates(subset=["step"]).reset_index(drop=True)

# Expand inventory and prices into columns
inv_df = pd.DataFrame(mdf["inventory"].tolist())
inv_df.columns = [f"inv_{c}" for c in inv_df.columns]

price_df = pd.DataFrame(mdf["prices"].tolist())
price_df.columns = [f"price_{c}" for c in price_df.columns]

mdf = pd.concat([mdf[["step", "day", "hour"]], inv_df, price_df], axis=1)
print(mdf.head(10).to_string())
```

```python
# Step 3: Compute per-step inventory changes
inv_cols = [c for c in mdf.columns if c.startswith("inv_")]
for col in inv_cols:
    mdf[f"{col}_change"] = mdf[col].diff()

# Show when inventory changes happen
change_cols = [c for c in mdf.columns if c.endswith("_change")]
print("\nInventory changes per step (first 50 steps):")
print(mdf[["step", "day", "hour"] + change_cols].head(50).to_string())
```

```python
# Step 4: Check if changes happen at specific hours
print("\nInventory change by hour:")
for col in change_cols:
    changes = mdf[mdf[col].fillna(0) != 0]
    if len(changes) > 0:
        print(f"\n{col}:")
        print(changes.groupby("hour").size())
```

```python
# Step 5: Plot inventory over time for key items
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 1, figsize=(14, 8))

for col in ["inv_WHEAT", "inv_CARROT", "inv_TOMATO"]:
    if col in mdf.columns:
        axes[0].plot(mdf["step"], mdf[col], label=col)
axes[0].set_title("Market Inventory Over Time (PASS/PASS)")
axes[0].set_xlabel("Step")
axes[0].set_ylabel("Inventory")
axes[0].legend()

for col in ["price_WHEAT", "price_CARROT", "price_TOMATO"]:
    if col in mdf.columns:
        axes[1].plot(mdf["step"], mdf[col], label=col)
axes[1].set_title("Market Prices Over Time (PASS/PASS)")
axes[1].set_xlabel("Step")
axes[1].set_ylabel("Price")
axes[1].legend()

plt.tight_layout()
plt.show()
```

### What to look for
1. **Consumption rate**: How many units per step does the market lose autonomously?
2. **Consumption timing**: Does it happen every step? Every hour 0? Every day?
3. **Price formula**: Is price = f(inventory)? If inventory drops by 1, how much does price increase?
4. **Which goods are consumed**: Are all goods consumed equally?

### Checkpoint

```python
# Conclusion 0.5:
# Autonomous consumption rate: ___ units per ___ for each good
# Consumption timing: every ___
# Price-inventory relationship: ___
# Goods consumed: [list]
```

> **STOP HERE. Record findings. Proceed to 0.6 only after.**

---

## Phase 0.6 — Action Mechanics Discovery

### Goal
Test individual actions and observe their effects.

### What to do in the notebook

Test each action **one at a time** in separate experiments. For each action:
1. Run a short episode
2. Have the agent perform ONLY that action
3. Record what changes

#### 0.6a — MOVE action

```python
# ============================================================
# Phase 0.6a — MOVE Action
# ============================================================

move_history = []

def move_agent(obs):
    step = obs.get("step", 0)
    move_history.append({
        "step": step,
        "farmer_pos": tuple(obs["farms"][obs["player"]]["farmer"]),
        "money": obs["farms"][obs["player"]]["money"],
    })

    # Try moving right on step 0, down on step 1, etc.
    directions = ["RIGHT", "DOWN", "LEFT", "UP"]
    direction = directions[step % 4] if step < 8 else "PASS"

    return {"farmer": [direction], "market": []}

env = make("kaggriculture", configuration={"episodeSteps": 24, "seed": 42}, debug=True)
result = env.run([move_agent, "random"])

move_df = pd.DataFrame(move_history)
print(move_df.to_string())
```

#### 0.6b — BUY_SEEDS action

```python
# ============================================================
# Phase 0.6b — BUY_SEEDS
# ============================================================
# Question: How do we buy seeds? Where? What does it cost?

buy_history = []

def buy_seeds_agent(obs):
    step = obs.get("step", 0)
    player = obs["player"]
    farm = obs["farms"][player]

    buy_history.append({
        "step": step,
        "money": farm["money"],
        "farmer_pos": tuple(farm["farmer"]),
        "seeds": obs["private"].get("seeds", {}),
    })

    # Try buying wheat seeds
    if step == 0:
        return {"farmer": ["BUY_SEEDS WHEAT"], "market": []}
    return {"farmer": ["PASS"], "market": []}

env = make("kaggriculture", configuration={"episodeSteps": 24, "seed": 42}, debug=True)
result = env.run([buy_seeds_agent, "random"])

buy_df = pd.DataFrame(buy_history)
print(buy_df.to_string())
```

#### 0.6c — PLANT action

```python
# ============================================================
# Phase 0.6c — PLANT
# ============================================================
# Test the full cycle: buy seeds → move to tile → plant
# Record tile state before and after
```

#### 0.6d — WATER action

#### 0.6e — HARVEST action

#### 0.6f — SELL action (market)

#### 0.6g — HIRE action

#### 0.6h — BUY_ANIMAL action

#### 0.6i — FEED action

#### 0.6j — CARE action

### Pattern for each action test

For every action, record:

```python
{
    "action_name": "...",
    "preconditions": "what must be true before this action works",
    "effect": "what changes after the action",
    "cost": "money spent",
    "location_requirement": "where must the farmer/worker be",
    "failure_behavior": "what happens if preconditions are not met",
}
```

### Checkpoint

```python
# Conclusion 0.6:
# Complete action reference table:
# | Action     | Precondition              | Effect                  | Cost    | Location |
# |------------|---------------------------|-------------------------|---------|----------|
# | MOVE       | ...                       | ...                     | ...     | ...      |
# | BUY_SEEDS  | ...                       | ...                     | ...     | ...      |
# | PLANT      | ...                       | ...                     | ...     | ...      |
# | WATER      | ...                       | ...                     | ...     | ...      |
# | HARVEST    | ...                       | ...                     | ...     | ...      |
# | SELL       | ...                       | ...                     | ...     | ...      |
# | HIRE       | ...                       | ...                     | ...     | ...      |
# | BUY_ANIMAL | ...                       | ...                     | ...     | ...      |
# | FEED       | ...                       | ...                     | ...     | ...      |
# | CARE       | ...                       | ...                     | ...     | ...      |
```

> **STOP HERE. This table is the foundation for everything else.**

---

## Phase 0.7 — Full Crop Lifecycle Experiment

### Goal
Execute one complete crop lifecycle: buy seeds → plant → water → grow → harvest → sell.

### What to do in the notebook

```python
# ============================================================
# Phase 0.7 — Full Crop Lifecycle
# ============================================================
# Execute: BUY_SEEDS → PLANT → WATER (repeat) → HARVEST → SELL

lifecycle_history = []

def lifecycle_agent(obs):
    step = obs.get("step", 0)
    player = obs["player"]
    farm = obs["farms"][player]

    lifecycle_history.append({
        "step": step,
        "day": obs.get("day"),
        "hour": obs.get("hour"),
        "money": farm["money"],
        "farmer_pos": tuple(farm["farmer"]),
        "seeds": dict(obs["private"].get("seeds", {})),
        "shed": dict(obs["private"].get("shed", {})),
        "tiles": obs["farms"][player]["tiles"],  # record full tile state
    })

    # Hard-coded action sequence for one wheat lifecycle
    # ADJUST THESE BASED ON PHASE 0.6 FINDINGS
    action_sequence = [
        "BUY_SEEDS WHEAT",   # step 0: buy seeds
        "PASS",               # step 1: (adjust if needed)
        # ... fill in based on movement needed, planting, watering, etc.
    ]

    if step < len(action_sequence):
        action = action_sequence[step]
    else:
        action = "PASS"

    return {"farmer": [action], "market": []}
```

### What to record
1. How many steps from plant to harvest-ready?
2. How many waterings needed?
3. What is the yield (how many items in shed after harvest)?
4. What is the sell revenue vs seed cost?

### Checkpoint

```python
# Conclusion 0.7:
# WHEAT lifecycle:
#   Seed cost: ___
#   Steps to harvest: ___
#   Waterings needed: ___
#   Yield: ___
#   Sell price (at step ___): ___
#   Net profit: ___
```

> **STOP. Phase 0 is complete after this. Proceed to Phase 1.**

---

# PHASE 1 — WorldState Parser

## Goal
Create `world_state.py` — a clean parser that converts raw observations into structured Python objects.

## File: `world_state.py`

### Exact code structure to create

```python
"""
WorldState — Structured representation of the game state.
Created in Phase 1.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class TileState:
    """State of a single farm tile."""
    row: int
    col: int
    content: str          # e.g., "EMPTY", "WHEAT", "CARROT", "SHEEP", etc.
    growth_stage: int     # 0 = just planted, max = ready to harvest
    watered: bool
    fertilized: bool


@dataclass
class WorkerState:
    """State of a worker (farmer or hired hand)."""
    position: Tuple[int, int]
    carrying: Optional[str]  # what the worker is carrying, if anything


@dataclass
class FarmState:
    """State of one player's farm."""
    money: float
    farmer: WorkerState
    hands: List[WorkerState]
    tiles: List[TileState]
    unlocked_quadrants: List[str]
    hires_today: int

    # Derived (computed after parsing)
    empty_tiles: List[TileState] = field(default_factory=list)
    crop_tiles: List[TileState] = field(default_factory=list)
    animal_tiles: List[TileState] = field(default_factory=list)
    ready_to_harvest: List[TileState] = field(default_factory=list)


@dataclass
class MarketState:
    """State of the market."""
    inventory: Dict[str, int]
    prices: Dict[str, float]


@dataclass
class PrivateState:
    """Player's private state (only visible to that player)."""
    shed: Dict[str, int]       # items in shed
    seeds: Dict[str, int]      # seeds available
    inventories: Dict[str, int]  # other inventories


@dataclass
class TownState:
    """State of the town."""
    unlocked_shops: List[str]


@dataclass
class WorldState:
    """Complete world state for one observation."""
    step: int
    day: int
    hour: int
    player: int              # which player we are (0 or 1)

    my_farm: FarmState
    opponent_farm: FarmState
    market: MarketState
    private: PrivateState
    town: TownState


def parse_observation(obs: dict) -> WorldState:
    """
    Convert a raw Kaggle observation dict into a WorldState.

    This is the ONLY function that should touch the raw observation format.
    Everything else in the codebase uses WorldState.

    Args:
        obs: Raw observation dict from Kaggle environment

    Returns:
        WorldState object
    """
    player = obs["player"]
    opponent = 1 - player

    # Parse time
    step = obs.get("step", 0)
    day = obs.get("day", step // 24)
    hour = obs.get("hour", step % 24)

    # Parse tiles for a farm
    def parse_tiles(farm_data) -> List[TileState]:
        tiles = []
        # ADJUST THIS based on Phase 0.6 findings about tile structure
        raw_tiles = farm_data.get("tiles", [])
        for row_idx, row in enumerate(raw_tiles):
            for col_idx, cell in enumerate(row):
                # Parse cell based on actual structure discovered in Phase 0
                tiles.append(TileState(
                    row=row_idx,
                    col=col_idx,
                    content=str(cell) if cell else "EMPTY",
                    growth_stage=0,   # ADJUST based on actual data
                    watered=False,    # ADJUST based on actual data
                    fertilized=False, # ADJUST based on actual data
                ))
        return tiles

    # Parse workers
    def parse_workers(farm_data) -> List[WorkerState]:
        workers = []
        for hand in farm_data.get("hands", []):
            workers.append(WorkerState(
                position=tuple(hand) if isinstance(hand, list) else (0, 0),
                carrying=None,  # ADJUST based on actual data
            ))
        return workers

    # Parse farms
    my_farm_data = obs["farms"][player]
    opp_farm_data = obs["farms"][opponent]

    my_farm = FarmState(
        money=my_farm_data["money"],
        farmer=WorkerState(
            position=tuple(my_farm_data["farmer"]),
            carrying=None,
        ),
        hands=parse_workers(my_farm_data),
        tiles=parse_tiles(my_farm_data),
        unlocked_quadrants=my_farm_data.get("unlocked_quadrants", []),
        hires_today=my_farm_data.get("hires_today", 0),
    )

    opp_farm = FarmState(
        money=opp_farm_data["money"],
        farmer=WorkerState(
            position=tuple(opp_farm_data["farmer"]),
            carrying=None,
        ),
        hands=parse_workers(opp_farm_data),
        tiles=parse_tiles(opp_farm_data),
        unlocked_quadrants=opp_farm_data.get("unlocked_quadrants", []),
        hires_today=opp_farm_data.get("hires_today", 0),
    )

    # Compute derived tile lists
    for farm in [my_farm, opp_farm]:
        farm.empty_tiles = [t for t in farm.tiles if t.content == "EMPTY"]
        farm.crop_tiles = [t for t in farm.tiles if t.content not in ("EMPTY", "WEED")]
        # ADJUST: add animal detection based on Phase 0.6 findings

    # Parse market
    market = MarketState(
        inventory=dict(obs["market"]["inventory"]),
        prices=dict(obs["market"]["prices"]),
    )

    # Parse private
    private = PrivateState(
        shed=dict(obs["private"].get("shed", {})),
        seeds=dict(obs["private"].get("seeds", {})),
        inventories=dict(obs["private"].get("inventories", {})),
    )

    # Parse town
    town = TownState(
        unlocked_shops=list(obs["town"].get("unlocked_shops", [])),
    )

    return WorldState(
        step=step,
        day=day,
        hour=hour,
        player=player,
        my_farm=my_farm,
        opponent_farm=opp_farm,
        market=market,
        private=private,
        town=town,
    )
```

### Verification in notebook

```python
# ============================================================
# Phase 1 — WorldState Verification
# ============================================================

from world_state import parse_observation

# Use an observation from a previous experiment
test_obs = result[0]  # first observation from any prior experiment

state = parse_observation(test_obs)

print(f"Step: {state.step}, Day: {state.day}, Hour: {state.hour}")
print(f"Player: {state.player}")
print(f"My money: {state.my_farm.money}")
print(f"My farmer at: {state.my_farm.farmer.position}")
print(f"Workers: {len(state.my_farm.hands)}")
print(f"Empty tiles: {len(state.my_farm.empty_tiles)}")
print(f"Market WHEAT price: {state.market.prices.get('WHEAT')}")
print(f"Seeds: {state.private.seeds}")
print(f"Shed: {state.private.shed}")
```

### Checkpoint
- [ ] `parse_observation()` runs without errors on every observation in a full game
- [ ] All fields are populated correctly (cross-check with raw observation)
- [ ] `empty_tiles`, `crop_tiles` lists are correct

> **STOP. Verify. Then proceed to Phase 2.**

---

# PHASE 2 — Action Engine + Pathfinding

## Goal
Create `action_engine.py` (action creation) and `pathfinding.py` (BFS movement).

## File: `pathfinding.py`

```python
"""
BFS pathfinding on the farm grid.
Created in Phase 2.
"""
from collections import deque
from typing import List, Tuple, Optional


def bfs_path(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    grid_size: int = 10,
    blocked: set = None,
) -> List[str]:
    """
    Find shortest path from start to goal using BFS.

    Args:
        start: (row, col) starting position
        goal: (row, col) target position
        grid_size: size of the grid (default 10x10)
        blocked: set of (row, col) positions that cannot be entered

    Returns:
        List of direction strings: ["RIGHT", "DOWN", ...] 
        Empty list if start == goal.
        None if no path found.
    """
    if start == goal:
        return []

    if blocked is None:
        blocked = set()

    # Directions: (delta_row, delta_col, direction_name)
    directions = [
        (-1, 0, "UP"),
        (1, 0, "DOWN"),
        (0, -1, "LEFT"),
        (0, 1, "RIGHT"),
    ]

    queue = deque()
    queue.append((start, []))
    visited = {start}

    while queue:
        (row, col), path = queue.popleft()

        for dr, dc, direction in directions:
            nr, nc = row + dr, col + dc

            if 0 <= nr < grid_size and 0 <= nc < grid_size:
                if (nr, nc) not in visited and (nr, nc) not in blocked:
                    new_path = path + [direction]

                    if (nr, nc) == goal:
                        return new_path

                    visited.add((nr, nc))
                    queue.append(((nr, nc), new_path))

    return None  # No path found


def next_move(start: Tuple[int, int], goal: Tuple[int, int], grid_size: int = 10) -> str:
    """
    Get the next single move direction to go from start toward goal.

    Returns:
        Direction string ("UP", "DOWN", "LEFT", "RIGHT") or "PASS" if already at goal.
    """
    path = bfs_path(start, goal, grid_size)
    if path is None or len(path) == 0:
        return "PASS"
    return path[0]


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Manhattan distance between two positions."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
```

## File: `action_engine.py`

```python
"""
Action Engine — Creates valid Kaggle actions from internal commands.
Created in Phase 2.

IMPORTANT: The exact action format strings must match what the Kaggle
environment expects. Verify each one against Phase 0.6 findings.
"""
from typing import List, Dict


def make_action(farmer_actions: List[str], market_actions: List[str] = None) -> Dict:
    """
    Create a Kaggle-format action dict.

    Args:
        farmer_actions: List of action strings for farmer + workers.
                        First element is farmer's action.
                        Subsequent elements are for hired hands (in order).
        market_actions: List of market action strings.

    Returns:
        Dict in Kaggle action format: {"farmer": [...], "market": [...]}
    """
    if market_actions is None:
        market_actions = []

    return {
        "farmer": farmer_actions,
        "market": market_actions,
    }


def pass_action(num_workers: int = 0) -> Dict:
    """Create a PASS action for farmer and all workers."""
    actions = ["PASS"] * (1 + num_workers)  # 1 farmer + N workers
    return make_action(actions)
```

### Verification in notebook

```python
# ============================================================
# Phase 2 — Pathfinding + Action Engine Verification
# ============================================================

from pathfinding import bfs_path, next_move, manhattan_distance
from action_engine import make_action, pass_action

# Test BFS
path = bfs_path((4, 4), (0, 0))
print(f"Path from (4,4) to (0,0): {path}")
print(f"Length: {len(path)}")
print(f"Manhattan distance: {manhattan_distance((4, 4), (0, 0))}")

# Test next_move
move = next_move((4, 4), (4, 6))
print(f"Next move from (4,4) toward (4,6): {move}")

# Test action creation
action = make_action(["RIGHT", "PASS"], ["SELL WHEAT 5"])
print(f"Action dict: {action}")

# Test pass action
print(f"Pass with 2 workers: {pass_action(2)}")
```

### Checkpoint
- [ ] BFS finds correct shortest paths
- [ ] `manhattan_distance` matches path lengths (no obstacles)
- [ ] `make_action` produces valid Kaggle format
- [ ] `pass_action` produces correct number of PASS entries

> **STOP. Verify. Proceed to Phase 3.**

---

# PHASE 3 — Baseline Heuristic Agent (Approach A)

## Goal
Build a simple but working agent that plants crops, harvests, sells, and manages workers.

## File: `task_manager.py`

```python
"""
Task Manager — Generates and assigns tasks to workers.
Created in Phase 3.
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional
from pathfinding import manhattan_distance


@dataclass
class Task:
    """A single task for a worker to perform."""
    name: str                          # e.g., "plant_wheat", "harvest", "water"
    priority: int                      # lower = higher priority
    target_position: Tuple[int, int]   # where the worker needs to be
    action: str                        # the Kaggle action string to execute
    assigned_worker: Optional[int] = None  # worker index (None = unassigned)


def generate_tasks(world_state) -> List[Task]:
    """
    Generate tasks based on current world state.

    IMPORTANT: This function should be updated incrementally.
    Start with just crop tasks. Add animal tasks later.

    Args:
        world_state: WorldState object from world_state.py

    Returns:
        List of Task objects, sorted by priority
    """
    tasks = []
    farm = world_state.my_farm

    # --- PLANTING TASKS ---
    # If we have seeds and empty tiles, generate plant tasks
    for seed_type, count in world_state.private.seeds.items():
        if count > 0:
            for tile in farm.empty_tiles[:count]:  # one per seed
                tasks.append(Task(
                    name=f"plant_{seed_type.lower()}",
                    priority=20,
                    target_position=(tile.row, tile.col),
                    action=f"PLANT {seed_type}",
                ))

    # --- WATERING TASKS ---
    # Water crops that need watering
    for tile in farm.crop_tiles:
        if not tile.watered:
            tasks.append(Task(
                name=f"water_{tile.content.lower()}",
                priority=10,  # higher priority than planting
                target_position=(tile.row, tile.col),
                action="WATER",
            ))

    # --- HARVEST TASKS ---
    # Harvest crops that are ready
    for tile in farm.ready_to_harvest:
        tasks.append(Task(
            name=f"harvest_{tile.content.lower()}",
            priority=5,  # highest priority
            target_position=(tile.row, tile.col),
            action="HARVEST",
        ))

    # --- BUYING SEEDS ---
    # If no seeds and money available
    if not world_state.private.seeds and farm.money >= 100:
        # ADJUST: position of seed shop based on Phase 0.6
        tasks.append(Task(
            name="buy_seeds",
            priority=15,
            target_position=(0, 0),  # ADJUST: actual shop position
            action="BUY_SEEDS WHEAT",  # ADJUST: best crop choice
        ))

    # Sort by priority (lower number = higher priority)
    tasks.sort(key=lambda t: t.priority)
    return tasks


def assign_tasks(
    tasks: List[Task],
    worker_positions: List[Tuple[int, int]],
) -> List[Task]:
    """
    Assign tasks to workers using greedy nearest-worker strategy.

    Args:
        tasks: List of unassigned tasks (sorted by priority)
        worker_positions: List of (row, col) for each worker
                          Index 0 = farmer, 1+ = hired hands

    Returns:
        List of tasks with assigned_worker set
    """
    available_workers = set(range(len(worker_positions)))
    assigned_tasks = []

    for task in tasks:
        if not available_workers:
            break

        # Find closest available worker
        best_worker = None
        best_distance = float("inf")

        for worker_idx in available_workers:
            dist = manhattan_distance(
                worker_positions[worker_idx],
                task.target_position,
            )
            if dist < best_distance:
                best_distance = dist
                best_worker = worker_idx

        if best_worker is not None:
            task.assigned_worker = best_worker
            available_workers.remove(best_worker)
            assigned_tasks.append(task)

    return assigned_tasks
```

## Update `main.py` — Heuristic Agent

```python
"""
Kaggriculture Agent — main.py
Phase 3: Baseline Heuristic Agent

This is the Kaggle submission entry point.
"""
from world_state import parse_observation, WorldState
from action_engine import make_action, pass_action
from pathfinding import next_move
from task_manager import generate_tasks, assign_tasks


# Persistent state across turns
state_history = []


def agent(obs):
    """
    Main agent function called by Kaggle each turn.

    Args:
        obs: Raw observation dict from Kaggle

    Returns:
        Action dict: {"farmer": [...], "market": [...]}
    """
    # Step 1: Parse observation into WorldState
    world = parse_observation(obs)
    state_history.append(world)

    # Step 2: Count workers (farmer + hands)
    num_workers = 1 + len(world.my_farm.hands)
    worker_positions = [world.my_farm.farmer.position]
    for hand in world.my_farm.hands:
        worker_positions.append(hand.position)

    # Step 3: Generate tasks
    tasks = generate_tasks(world)

    # Step 4: Assign tasks to workers
    assigned = assign_tasks(tasks, worker_positions)

    # Step 5: Convert assigned tasks to actions
    farmer_actions = ["PASS"] * num_workers  # default all to PASS

    for task in assigned:
        worker_idx = task.assigned_worker
        worker_pos = worker_positions[worker_idx]

        if worker_pos == task.target_position:
            # Worker is at the target — perform the action
            farmer_actions[worker_idx] = task.action
        else:
            # Worker needs to move — take one step toward target
            move = next_move(worker_pos, task.target_position)
            farmer_actions[worker_idx] = move

    # Step 6: Market actions
    market_actions = []

    # SELL logic: sell everything in shed
    # ADJUST: add batch selling logic later
    for item, count in world.private.shed.items():
        if count > 0:
            market_actions.append(f"SELL {item} {count}")

    # Step 7: End-game liquidation (last 2 days)
    if world.day >= 28:
        # Sell everything, don't invest
        for item, count in world.private.shed.items():
            if count > 0 and f"SELL {item}" not in str(market_actions):
                market_actions.append(f"SELL {item} {count}")

    return make_action(farmer_actions, market_actions)
```

### Verification in notebook

```python
# ============================================================
# Phase 3 — Baseline Agent Verification
# ============================================================
import importlib
import main
importlib.reload(main)

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720, "seed": 42},
    debug=True,
)

result = env.run([main.agent, "random"])

# Check result
final_obs = result[-1][0]["observation"]
my_money = final_obs["farms"][0]["money"]
opp_money = final_obs["farms"][1]["money"]

print(f"My final money:       ${my_money}")
print(f"Opponent final money: ${opp_money}")
print(f"Winner: {'ME' if my_money > opp_money else 'OPPONENT'}")
```

```python
# Run multiple games to get win rate
wins = 0
total = 20

for seed in range(total):
    importlib.reload(main)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
    result = env.run([main.agent, "random"])
    final = result[-1][0]["observation"]
    if final["farms"][0]["money"] > final["farms"][1]["money"]:
        wins += 1

print(f"Win rate vs random: {wins}/{total} = {wins/total*100:.1f}%")
```

### Checkpoint
- [ ] Agent runs a full 720-turn game without errors
- [ ] Agent earns more money than starting capital
- [ ] Agent beats `random` opponent > 70% of the time
- [ ] No invalid action errors in debug output

> **STOP. This is your first submittable agent. Test it. Then proceed to Phase 4.**

---

# PHASE 4 — Market Intelligence (Approach A+)

## Goal
Add smart selling (batch selling, price tracking) and dynamic crop selection.

## File: `market_model.py`

```python
"""
Market Model — Tracks prices, predicts trends, optimizes selling.
Created in Phase 4.
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class MarketTracker:
    """Tracks market history and provides selling recommendations."""

    price_history: Dict[str, List[float]] = field(default_factory=dict)
    inventory_history: Dict[str, List[int]] = field(default_factory=dict)

    def update(self, prices: Dict[str, float], inventory: Dict[str, int]):
        """Record current market state."""
        for item, price in prices.items():
            if item not in self.price_history:
                self.price_history[item] = []
            self.price_history[item].append(price)

        for item, inv in inventory.items():
            if item not in self.inventory_history:
                self.inventory_history[item] = []
            self.inventory_history[item].append(inv)

    def get_price_trend(self, item: str, lookback: int = 24) -> float:
        """
        Get price trend for an item.
        Returns positive number if price is rising, negative if falling.
        """
        if item not in self.price_history:
            return 0.0
        history = self.price_history[item]
        if len(history) < 2:
            return 0.0
        recent = history[-lookback:] if len(history) >= lookback else history
        return recent[-1] - recent[0]

    def should_sell(self, item: str, quantity: int, current_price: float) -> Tuple[bool, int]:
        """
        Decide whether to sell and how much.

        Strategy:
        - If price is rising, hold (sell only small amount)
        - If price is falling, sell more
        - Always sell at least 1 if we have shed pressure
        - Near end of game, sell everything

        Args:
            item: Item name
            quantity: How many we have
            current_price: Current market price

        Returns:
            (should_sell: bool, sell_quantity: int)
        """
        trend = self.get_price_trend(item)

        if trend > 0:
            # Price rising — sell in small batches
            sell_qty = max(1, quantity // 4)
            return True, sell_qty
        else:
            # Price falling or stable — sell more aggressively
            sell_qty = max(1, quantity // 2)
            return True, sell_qty

    def best_crop_to_plant(self, prices: Dict[str, float]) -> str:
        """
        Choose the best crop to plant based on current prices.

        Simple version: pick the crop with highest price.
        ADJUST: factor in growth time, seed cost, yield later.

        Returns:
            Crop name string (e.g., "WHEAT", "CARROT", "TOMATO")
        """
        # ADJUST: Add crop-specific data (growth time, seed cost, yield)
        # For now: simple price-based selection
        crop_prices = {k: v for k, v in prices.items()
                       if k in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")}
        if not crop_prices:
            return "WHEAT"
        return max(crop_prices, key=crop_prices.get)
```

## File: `crop_model.py`

```python
"""
Crop Model — Crop lifecycle data and profitability calculations.
Created in Phase 4.

IMPORTANT: Fill in the actual values from Phase 0.6 and 0.7 experiments.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class CropInfo:
    """Static information about a crop type."""
    name: str
    seed_cost: int
    growth_turns: int        # turns from plant to harvest-ready
    waterings_needed: int    # number of water actions required
    base_yield: int          # items produced per harvest
    fertilized_yield: int    # items with fertilizer
    labor_actions: int       # total actions: plant + water + harvest


# FILL THESE IN FROM PHASE 0.6 AND 0.7 EXPERIMENTS
CROP_DATA: Dict[str, CropInfo] = {
    "WHEAT": CropInfo(
        name="WHEAT",
        seed_cost=0,         # FILL IN
        growth_turns=0,      # FILL IN
        waterings_needed=0,  # FILL IN
        base_yield=0,        # FILL IN
        fertilized_yield=0,  # FILL IN
        labor_actions=0,     # FILL IN
    ),
    "CARROT": CropInfo(
        name="CARROT",
        seed_cost=0,         # FILL IN
        growth_turns=0,      # FILL IN
        waterings_needed=0,  # FILL IN
        base_yield=0,        # FILL IN
        fertilized_yield=0,  # FILL IN
        labor_actions=0,     # FILL IN
    ),
    # Add TOMATO, STRAWBERRY, MELON, etc.
}


def crop_profitability(
    crop_name: str,
    current_price: float,
    remaining_turns: int,
) -> float:
    """
    Calculate ROI per turn for a crop.

    Args:
        crop_name: Name of crop
        current_price: Current market price for this crop
        remaining_turns: Turns left in the game

    Returns:
        ROI per turn (higher = better)
        Returns -1.0 if crop cannot be harvested in remaining time
    """
    if crop_name not in CROP_DATA:
        return -1.0

    crop = CROP_DATA[crop_name]

    if crop.growth_turns > remaining_turns:
        return -1.0  # Can't harvest in time

    revenue = current_price * crop.base_yield
    cost = crop.seed_cost
    profit = revenue - cost
    roi_per_turn = profit / max(1, crop.growth_turns)

    return roi_per_turn
```

### Update `main.py` to use Market Model

Add the MarketTracker as persistent state and use it for sell decisions and crop selection. Replace the hard-coded "sell everything" and "always plant wheat" logic.

### Checkpoint
- [ ] MarketTracker correctly records price history over a full game
- [ ] `should_sell` returns reasonable quantities
- [ ] `best_crop_to_plant` selects higher-value crops when prices justify it
- [ ] Agent earns more money than Phase 3 baseline
- [ ] Win rate vs random improves

> **STOP. Compare against Phase 3 baseline. Only proceed if this is better.**

---

# PHASE 5 — Animal Management + Worker Hiring

## Goal
Add animal management and intelligent worker hiring.

## File: `animal_model.py`

```python
"""
Animal Model — Animal management and profitability.
Created in Phase 5.

IMPORTANT: Fill in values from experiments.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class AnimalInfo:
    """Static information about an animal type."""
    name: str
    purchase_cost: int
    feed_item: str           # what to feed (e.g., "WHEAT")
    feed_quantity: int       # how much per feeding
    production_item: str     # what it produces (e.g., "WOOL", "MILK", "EGG")
    production_quantity: int # how much per production cycle
    production_frequency: int  # produce every N turns
    care_needed: bool        # does it need CARE action?


# FILL THESE IN FROM EXPERIMENTS
ANIMAL_DATA: Dict[str, AnimalInfo] = {
    "SHEEP": AnimalInfo(
        name="SHEEP",
        purchase_cost=0,         # FILL IN
        feed_item="WHEAT",       # VERIFY
        feed_quantity=0,         # FILL IN
        production_item="WOOL",
        production_quantity=0,   # FILL IN
        production_frequency=0,  # FILL IN
        care_needed=True,        # VERIFY
    ),
    "COW": AnimalInfo(
        name="COW",
        purchase_cost=0,         # FILL IN
        feed_item="WHEAT",       # VERIFY
        feed_quantity=0,         # FILL IN
        production_item="MILK",
        production_quantity=0,   # FILL IN
        production_frequency=0,  # FILL IN
        care_needed=True,        # VERIFY
    ),
    "CHICKEN": AnimalInfo(
        name="CHICKEN",
        purchase_cost=0,         # FILL IN
        feed_item="WHEAT",       # VERIFY
        feed_quantity=0,         # FILL IN
        production_item="EGG",
        production_quantity=0,   # FILL IN
        production_frequency=0,  # FILL IN
        care_needed=True,        # VERIFY
    ),
}
```

### What to add to `task_manager.py`

Add animal tasks to `generate_tasks()`:

```python
# --- ANIMAL FEED TASKS ---
# For each animal on the farm, generate a feed task if it hasn't been fed today
# Priority: 8 (higher than planting, lower than harvest)

# --- ANIMAL CARE TASKS ---
# For each animal that has been fed, generate a care task
# Priority: 9

# --- ANIMAL HARVEST TASKS ---
# For each animal with ready product, generate a harvest task
# Priority: 6 (almost as high as crop harvest)
```

### Worker Hiring Logic

Add to `main.py`:

```python
def should_hire(world: WorldState) -> bool:
    """
    Decide whether to hire a new worker.

    Rules:
    - Only hire if we have enough money (account for Fibonacci cost)
    - Only hire if workload exceeds current workforce
    - Don't hire in last 5 days (not enough time to recoup cost)
    """
    num_workers = 1 + len(world.my_farm.hands)
    remaining_days = 30 - world.day

    if remaining_days < 5:
        return False

    # Fibonacci-ish hiring costs (per day, cumulative)
    # VERIFY: exact cost from experiments
    hire_costs = [0, 10, 20, 30, 50, 80, 130, 210, 340]

    if num_workers >= len(hire_costs):
        return False

    daily_cost = hire_costs[num_workers]
    total_cost = daily_cost * remaining_days

    if world.my_farm.money < total_cost + 500:  # keep $500 buffer
        return False

    # Check if there's enough work for another worker
    pending_tasks = len(generate_tasks(world))
    if pending_tasks > num_workers * 1.5:
        return True

    return False
```

### Checkpoint
- [ ] Animals are fed and produce items
- [ ] Animal products are sold at market
- [ ] Worker hiring happens only when justified
- [ ] Agent earns more money than Phase 4

> **STOP. Compare. Then proceed to Phase 6.**

---

# PHASE 6 — Predictive Planning (Approach B)

## Goal
Add a simple future simulator and strategy comparison.

## File: `strategy.py`

```python
"""
Strategic Planner — Generates and evaluates candidate strategies.
Created in Phase 6.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Strategy:
    """A candidate strategy to evaluate."""
    name: str
    crop_focus: str           # primary crop to plant
    animal_target: int        # target number of animals
    sell_frequency: str       # "immediate", "daily", "batch"
    expand_land: bool         # whether to buy new land
    hire_workers: int         # target number of workers


def generate_strategies(world_state) -> List[Strategy]:
    """
    Generate 3-5 candidate strategies based on current game state.
    """
    remaining_days = 30 - world_state.day
    strategies = []

    # Strategy 1: Aggressive crops
    strategies.append(Strategy(
        name="aggressive_crops",
        crop_focus="TOMATO",  # ADJUST based on profitability
        animal_target=0,
        sell_frequency="daily",
        expand_land=remaining_days > 10,
        hire_workers=4,
    ))

    # Strategy 2: Animal-heavy
    strategies.append(Strategy(
        name="animal_heavy",
        crop_focus="WHEAT",  # wheat for animal feed
        animal_target=4,
        sell_frequency="batch",
        expand_land=remaining_days > 15,
        hire_workers=3,
    ))

    # Strategy 3: Conservative
    strategies.append(Strategy(
        name="conservative",
        crop_focus="WHEAT",
        animal_target=1,
        sell_frequency="immediate",
        expand_land=False,
        hire_workers=2,
    ))

    return strategies
```

## File: `simulator.py`

```python
"""
Future Simulator — Simulates forward from current state.
Created in Phase 6.

This is a SIMPLIFIED simulator. It does not model every detail.
It estimates projected money for each strategy.
"""
from world_state import WorldState
from crop_model import CROP_DATA
from market_model import MarketTracker


def simulate_strategy(
    world: WorldState,
    strategy,
    market_tracker: MarketTracker,
    horizon_days: int = 5,
) -> float:
    """
    Simulate a strategy forward and return projected final money.

    This is a rough estimation, NOT an exact simulation.

    Args:
        world: Current WorldState
        strategy: Strategy object
        market_tracker: MarketTracker with price history
        horizon_days: How many days to simulate forward

    Returns:
        Projected money at end of horizon
    """
    money = world.my_farm.money
    horizon_turns = horizon_days * 24
    num_workers = 1 + len(world.my_farm.hands)
    empty_tiles = len(world.my_farm.empty_tiles)

    # Estimate crop revenue
    if strategy.crop_focus in CROP_DATA:
        crop = CROP_DATA[strategy.crop_focus]
        if crop.growth_turns > 0:
            harvests_possible = horizon_turns // crop.growth_turns
            tiles_planted = min(empty_tiles, num_workers)
            revenue_per_harvest = (
                tiles_planted
                * crop.base_yield
                * world.market.prices.get(strategy.crop_focus, 0)
            )
            total_crop_revenue = revenue_per_harvest * harvests_possible
            total_seed_cost = tiles_planted * crop.seed_cost * harvests_possible
            money += total_crop_revenue - total_seed_cost

    # Estimate worker costs
    # ADJUST: use actual hiring cost formula
    worker_daily_cost = 10 * strategy.hire_workers  # rough estimate
    money -= worker_daily_cost * horizon_days

    # Estimate animal revenue
    # ADJUST: use actual animal data
    money += strategy.animal_target * 50 * horizon_days  # rough estimate

    return money


def rank_strategies(
    world: WorldState,
    strategies: list,
    market_tracker: MarketTracker,
) -> list:
    """
    Rank strategies by projected money.

    Returns:
        Strategies sorted best-first, with projected_money attribute added.
    """
    scored = []
    for strategy in strategies:
        projected = simulate_strategy(world, strategy, market_tracker)
        scored.append((projected, strategy))

    scored.sort(reverse=True, key=lambda x: x[0])

    print(f"Strategy rankings:")
    for money, s in scored:
        print(f"  {s.name}: projected ${money:.0f}")

    return [s for _, s in scored]
```

### Update `main.py` to use Strategy selection

Every N turns (e.g., every 24 turns = start of each day), call `generate_strategies()` → `rank_strategies()` → use the best strategy to configure the task generator.

### Checkpoint
- [ ] Strategies are generated and ranked each day
- [ ] Agent behavior changes based on selected strategy
- [ ] Agent beats Phase 5 baseline in win rate

> **STOP. Compare. Then proceed to Phase 7 if time permits.**

---

# PHASE 7 — Optimization (Approach C — Optional)

## Goal
Use OR-Tools for optimal worker scheduling (only if Phases 3–6 are solid).

### When to use OR-Tools

```text
ONLY add OR-Tools if:
  1. Phases 3–6 are fully working
  2. The agent beats random > 90%
  3. You have identified specific scheduling inefficiencies
  4. You have at least 3 days remaining before deadline
```

### What OR-Tools would optimize

```python
# Worker schedule optimization using CP-SAT
# Variables: worker[w] assigned to task[t] at time step[s]
# Constraints:
#   - Each worker does at most 1 task per step
#   - Tasks have location requirements (movement time)
#   - Tasks have dependencies (plant before water before harvest)
#   - Tasks have deadlines (harvest before crop dies)
# Objective: maximize completed tasks weighted by priority
```

### Checkpoint
- [ ] OR-Tools solver runs within 1 second
- [ ] Schedule is valid (no conflicts)
- [ ] Agent performance improves over greedy assignment

---

# Summary: Execution Order

| Step | Phase | What | Files Created/Modified | Days |
|------|-------|------|----------------------|------|
| 1 | 0.4 | Clock analysis | notebook only | 0.5 |
| 2 | 0.5 | Market behavior | notebook only | 0.5 |
| 3 | 0.6 | Action mechanics | notebook only | 1.5 |
| 4 | 0.7 | Crop lifecycle | notebook only | 0.5 |
| 5 | 1 | WorldState parser | `world_state.py` | 1 |
| 6 | 2 | Actions + BFS | `action_engine.py`, `pathfinding.py` | 0.5 |
| 7 | 3 | Baseline agent | `task_manager.py`, update `main.py` | 2 |
| 8 | 4 | Market intelligence | `market_model.py`, `crop_model.py` | 1.5 |
| 9 | 5 | Animals + hiring | `animal_model.py`, update `task_manager.py` | 1.5 |
| 10 | 6 | Strategy planning | `strategy.py`, `simulator.py` | 2 |
| 11 | 7 | Optimization | `optimizer.py` | 2 |

**Total: ~13.5 days (fits within 16-day deadline)**

---

# Rules For The Model

1. **Do ONE phase at a time.** Do not start Phase 3 before Phase 2 is verified.
2. **Run the checkpoint tests.** If a checkpoint fails, fix it before moving on.
3. **Fill in the `FILL IN` values** from actual experiment results, not from guesses.
4. **Every `# ADJUST` comment** marks something that depends on experiment results. Do not guess.
5. **Compare against the previous phase** before declaring the new phase done.
6. **Keep `main.py` clean.** No experiment code. No print statements (except debug mode).
7. **The notebook is for experiments.** The `.py` files are for production code.


---

# PHASE 10 — Predictive Dynamic Strategy (Score 2000+ Target)

## Goal
Transition the agent from static heuristics (Phase 9) to a fully dynamic, simulation-based strategy that predicts market prices, monitors the opponent, and reinvests capital aggressively into high-yield assets.

### Steps
1. **Enhance market_model.py**: Implement opponent tracking and predict_price_at_maturity().
2. **Enhance simulator.py**: Use predictive prices and include reinvestment compounding in simulations.
3. **Update main.py**: Remove static Day 0 Blitz. Implement daily Hour 0 strategy re-evaluation. Scale animals and land dynamically based on strategy.
4. **Dynamic Endgame**: Liquidate based on strategy (sell out on final days).

### Checkpoint
- [ ] Agent tracks opponent crops correctly
- [ ] Agent scales its animal herd to >10 animals in the mid-game
- [ ] Win rate vs Phase 3 remains 100%
- [ ] Terminal bank account reaches ,000+ consistently
