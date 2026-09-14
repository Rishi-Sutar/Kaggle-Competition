# Kaggriculture — Progress Tracker

> Update this file after completing each task. Mark items as they progress.
>
> `[ ]` = not started | `[/]` = in progress | `[x]` = done | `[!]` = blocked/issue

---

## PHASE 0 — Environment Reconnaissance

### 0.1 — Environment Startup
- [x] Kaggriculture environment installs and runs
- **Date completed**: ___

### 0.2 — Observation Inspection
- [x] Confirmed observation structure (player, farms, private, market, town, day, hour)
- **Date completed**: ___

### 0.3 — PASS/PASS Experiment
- [x] Ran PASS/PASS experiment
- [x] Confirmed market changes autonomously
- [x] Confirmed money stays unchanged with PASS
- **Date completed**: ___

### 0.4 — Clock Analysis
- [ ] Ran clock experiment (96 steps)
- [ ] Verified `day = step // 24`
- [ ] Verified `hour = step % 24`
- **Findings**: ___
- **Date completed**: ___

### 0.5 — Autonomous Market Behavior
- [ ] Ran full 720-step PASS/PASS game
- [ ] Recorded market inventory over time
- [ ] Recorded market prices over time
- [ ] Determined autonomous consumption rate
- [ ] Determined consumption timing (every step? every hour? every day?)
- [ ] Determined price-inventory relationship
- [ ] Plotted inventory and price charts
- **Findings**:
  - Consumption rate: ___
  - Consumption timing: ___
  - Price formula: ___
  - Goods consumed: ___
- **Date completed**: ___

### 0.6 — Action Mechanics Discovery
- [ ] 0.6a — MOVE: tested, preconditions/effects recorded
- [ ] 0.6b — BUY_SEEDS: tested, cost/location recorded
- [ ] 0.6c — PLANT: tested, preconditions/effects recorded
- [ ] 0.6d — WATER: tested, preconditions/effects recorded
- [ ] 0.6e — HARVEST: tested, preconditions/effects recorded
- [ ] 0.6f — SELL (market): tested, format/effects recorded
- [ ] 0.6g — HIRE: tested, cost/effects recorded
- [ ] 0.6h — BUY_ANIMAL: tested, cost/location recorded
- [ ] 0.6i — FEED: tested, preconditions/effects recorded
- [ ] 0.6j — CARE: tested, preconditions/effects recorded
- **Action Reference Table**:

| Action     | Precondition | Effect | Cost | Location Required |
|------------|-------------|--------|------|-------------------|
| MOVE       |             |        |      |                   |
| BUY_SEEDS  |             |        |      |                   |
| PLANT      |             |        |      |                   |
| WATER      |             |        |      |                   |
| HARVEST    |             |        |      |                   |
| SELL       |             |        |      |                   |
| HIRE       |             |        |      |                   |
| BUY_ANIMAL |             |        |      |                   |
| FEED       |             |        |      |                   |
| CARE       |             |        |      |                   |

- **Date completed**: ___

### 0.7 — Full Crop Lifecycle
- [ ] Executed complete WHEAT lifecycle (buy → plant → water → harvest → sell)
- [ ] Recorded growth timing
- [ ] Recorded yield
- [ ] Calculated net profit
- **Crop Data Discovered**:

| Crop       | Seed Cost | Growth Turns | Waterings | Yield | Fertilized Yield |
|------------|-----------|-------------|-----------|-------|-----------------|
| WHEAT      |           |             |           |       |                 |
| CARROT     |           |             |           |       |                 |
| TOMATO     |           |             |           |       |                 |
| STRAWBERRY |           |             |           |       |                 |
| MELON      |           |             |           |       |                 |

- **Date completed**: ___

### Phase 0 — COMPLETE?
- [ ] All sub-experiments done
- [ ] Environment model frozen
- **Date completed**: ___

---

## PHASE 1 — WorldState Parser

- [ ] Created `world_state.py`
- [ ] `TileState` dataclass defined
- [ ] `WorkerState` dataclass defined
- [ ] `FarmState` dataclass defined (with derived lists)
- [ ] `MarketState` dataclass defined
- [ ] `PrivateState` dataclass defined
- [ ] `TownState` dataclass defined
- [ ] `WorldState` dataclass defined
- [ ] `parse_observation()` function works
- [ ] Verified: parses every observation in a full game without errors
- [ ] Verified: all fields match raw observation values
- [ ] Verified: `empty_tiles`, `crop_tiles`, `ready_to_harvest` lists correct
- **Date completed**: ___

---

## PHASE 2 — Action Engine + Pathfinding

- [ ] Created `pathfinding.py`
- [ ] `bfs_path()` finds correct shortest paths
- [ ] `next_move()` returns correct single-step direction
- [ ] `manhattan_distance()` works correctly
- [ ] Created `action_engine.py`
- [ ] `make_action()` produces valid Kaggle format
- [ ] `pass_action()` produces correct PASS entries
- [ ] Verified: all functions tested in notebook
- **Date completed**: ___

---

## PHASE 3 — Baseline Heuristic Agent (Approach A)

- [ ] Created `task_manager.py`
- [ ] `Task` dataclass defined
- [ ] `generate_tasks()` produces planting, watering, harvesting tasks
- [ ] `assign_tasks()` assigns workers greedily by distance
- [ ] Updated `main.py` with heuristic agent
- [ ] Agent runs full 720-turn game without errors
- [ ] Agent earns more than starting capital ($3,000)
- [ ] Agent beats `random` opponent
- [ ] Win rate vs random (20 games): ___ / 20 = ___%
- [ ] **FIRST KAGGLE SUBMISSION DONE?** [ ]
- **Average final money**: ___
- **Date completed**: ___

---

## PHASE 4 — Market Intelligence (Approach A+)

- [ ] Created `market_model.py`
- [ ] `MarketTracker` records price and inventory history
- [ ] `get_price_trend()` computes price direction
- [ ] `should_sell()` returns smart sell quantities
- [ ] `best_crop_to_plant()` selects based on price/profitability
- [ ] Created `crop_model.py`
- [ ] `CropInfo` dataclass with real values from Phase 0.7
- [ ] `crop_profitability()` calculates ROI per turn
- [ ] Updated `main.py` to use MarketTracker
- [ ] Sells in batches (not all at once)
- [ ] Dynamically selects crops based on profitability
- [ ] **Comparison vs Phase 3 baseline**:
  - Phase 3 avg final money: ___
  - Phase 4 avg final money: ___
  - Improvement: ___%
- [ ] Win rate vs random (20 games): ___ / 20 = ___%
- **Date completed**: ___

---

## PHASE 5 — Animal Management + Worker Hiring

- [ ] Created `animal_model.py`
- [ ] `AnimalInfo` dataclass with real values from experiments
- [ ] Added animal tasks to `generate_tasks()` (feed, care, harvest)
- [ ] Added `should_hire()` worker hiring logic to `main.py`
- [ ] Animals are fed and produce items
- [ ] Animal products are sold
- [ ] Workers hired only when justified by workload
- [ ] End-game liquidation working (last 2 days)
- [ ] **Comparison vs Phase 4 baseline**:
  - Phase 4 avg final money: ___
  - Phase 5 avg final money: ___
  - Improvement: ___%
- [ ] Win rate vs random (20 games): ___ / 20 = ___%
- **Date completed**: ___

---

## PHASE 6 — Predictive Planning (Approach B)

- [ ] Created `strategy.py`
- [ ] `Strategy` dataclass defined
- [ ] `generate_strategies()` produces 3–5 candidates
- [ ] Created `simulator.py`
- [ ] `simulate_strategy()` estimates projected money
- [ ] `rank_strategies()` ranks by projected outcome
- [ ] Updated `main.py` to re-plan every 24 turns
- [ ] Agent behavior changes based on selected strategy
- [ ] **Comparison vs Phase 5 baseline**:
  - Phase 5 avg final money: ___
  - Phase 6 avg final money: ___
  - Improvement: ___%
- [ ] Win rate vs random (20 games): ___ / 20 = ___%
- **Date completed**: ___

---

## PHASE 7 — Optimization (Approach C — Optional)

- [ ] Prerequisites met (Phase 3–6 working, >90% vs random)
- [ ] Created `optimizer.py`
- [ ] OR-Tools CP-SAT worker scheduling
- [ ] Solver runs within 1 second
- [ ] Schedule is valid (no conflicts)
- [ ] **Comparison vs Phase 6 baseline**:
  - Phase 6 avg final money: ___
  - Phase 7 avg final money: ___
  - Improvement: ___%
- **Date completed**: ___

---

## KAGGLE SUBMISSIONS

| # | Date | Phase | Win Rate vs Random | Leaderboard Score | Notes |
|---|------|-------|--------------------|-------------------|-------|
| 1 |      |       |                    |                   |       |
| 2 |      |       |                    |                   |       |
| 3 |      |       |                    |                   |       |
| 4 |      |       |                    |                   |       |
| 5 |      |       |                    |                   |       |

---

## EXPERIMENT LOG

Record significant experiments and their outcomes here.

| Date | Experiment | Question | Result | Impact |
|------|-----------|----------|--------|--------|
|      |           |          |        |        |
|      |           |          |        |        |
|      |           |          |        |        |

---

## BUGS & ISSUES

| # | Date Found | Description | Status | Date Fixed |
|---|-----------|-------------|--------|-----------|
|   |           |             |        |           |

---

## KEY DECISIONS

Record important design decisions and why they were made.

| Date | Decision | Reason |
|------|----------|--------|
|      |          |        |
