# Kaggriculture Competition — Project Context & Development Plan

## 1. Purpose of This Document

This document provides the complete context for developing our solution for the Kaggle **Kaggriculture** competition.

The goal is to build a highly competitive agent through a **step-by-step, experiment-driven development process**.

The most important development principle is:

> **Do not jump directly into optimization, reinforcement learning, OR-Tools, MCTS, or hard-coded strategies. First understand and model the environment accurately, then build the system incrementally and validate every layer.**

We are using:

- **VS Code** as the development environment.
- A **Jupyter notebook** for experiments, investigation, visualization, debugging, and environment analysis.
- `main.py` as the actual Kaggle agent entry point.

Current project setup:

```text
kagriculture/
│
├── kagriculture.ipynb    # Experimental laboratory
└── main.py               # Actual agent
```

We want to keep this simple initially and grow the architecture only when necessary.

---

# 2. Competition Understanding

Kaggriculture is a two-player farm/economic strategy simulation.

The game lasts:

```text
720 turns
30 days
24 turns/day
```

Players compete to finish with more money / better competitive outcome.

The environment contains:

- Farm land
- Crops
- Animals
- Workers
- Seeds
- Fertilizer
- Market
- Town shops
- Dynamic prices
- Production
- Inventory
- Land expansion
- Worker hiring
- Opponent interaction

The environment is not a simple static supervised ML problem.

It is fundamentally a:

- Sequential decision problem
- Resource allocation problem
- Scheduling problem
- Dynamic economic optimization problem
- Two-player competitive game
- Partially observable environment

The agent observes the environment, chooses actions, receives a new observation, and repeats.

Conceptually:

```text
State(t)
   +
Action(t)
   ↓
Environment
   ↓
State(t+1)
   +
Reward / outcome
```

Our eventual agent should exploit this sequential nature.

---

# 3. Important Strategic Principle

Do NOT build an agent around rules such as:

```python
if day < 10:
    plant melon

if day > 20:
    plant wheat
```

Those may be useful baseline heuristics, but they should not be the foundation of our final solution.

The target architecture is:

```text
Current State
     ↓
Understand current world
     ↓
Predict future consequences
     ↓
Generate candidate strategies
     ↓
Simulate possible futures
     ↓
Evaluate strategies
     ↓
Choose strategy
     ↓
Generate concrete tasks
     ↓
Schedule workers/actions
     ↓
Execute
     ↓
Observe new state
     ↓
Re-plan
```

The agent should be **predictive and adaptive**, not merely reactive.

---

# 4. Our High-Level Architecture

The proposed end-to-end architecture is:

```text
                         KAGGRICULTURE ENVIRONMENT
                                   │
                                   │ Observation
                                   ▼
                         ┌─────────────────────┐
                         │ ENVIRONMENT ADAPTER │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    STATE ENGINE     │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
        OUR FARM                MARKET                 OPPONENT
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     WORLD MODEL     │
                         │                     │
                         │ Farm                │
                         │ Crops               │
                         │ Animals             │
                         │ Market              │
                         │ Town                │
                         │ Production          │
                         │ Opponent            │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  STRATEGIC PLANNER  │
                         └──────────┬──────────┘
                                    │
                             Candidate plans
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  FUTURE SIMULATOR   │
                         │                     │
                         │ What happens if...? │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  STRATEGY SCORER    │
                         └──────────┬──────────┘
                                    │
                             Selected strategy
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ TACTICAL SCHEDULER  │
                         │                     │
                         │ Tasks               │
                         │ Workers             │
                         │ Dependencies        │
                         │ Movement            │
                         │ Timing              │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  ACTION EXECUTOR    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                              ENVIRONMENT
                                    │
                                    └────────── LOOP
```

---

# 5. Two Major Decision Layers

A critical architectural separation is:

## Strategic Layer

Answers:

> What should we accomplish?

Examples:

```text
Produce wheat.
Buy sheep.
Expand land.
Save cash.
Hold wool.
Sell tomatoes later.
Hire two workers.
```

## Tactical Layer

Answers:

> How do we accomplish it?

Examples:

```text
Worker 1 → move → plant wheat
Worker 2 → feed sheep
Worker 3 → harvest tomato
Worker 4 → collect fertilizer
```

The strategic layer should not care about exact movement.

The tactical layer should not independently decide the overall economic strategy.

---

# 6. Environment Adapter

The Environment Adapter is the boundary between Kaggle and our code.

Responsibilities:

- Receive observations.
- Parse Kaggle-specific structures.
- Convert internal actions into Kaggle action format.
- Handle environment lifecycle.
- Keep Kaggle-specific implementation details isolated.

It should NOT contain strategic logic.

Conceptually:

```text
Kaggle Observation
       ↓
Environment Adapter
       ↓
Internal WorldState
```

And:

```text
Internal Action
       ↓
Environment Adapter
       ↓
Kaggle Action
```

---

# 7. State Engine

The State Engine is our canonical representation of the current world.

Raw Kaggle observations should not be passed throughout the system.

Instead:

```text
Raw Observation
       ↓
State Builder
       ↓
WorldState
```

The target conceptual structure is:

```python
WorldState(
    time=...,

    self=FarmState(...),

    opponent=OpponentState(...),

    market=MarketState(...),

    town=TownState(...),

    history=...
)
```

---

# 8. Expected WorldState

The exact schema will be determined from experiments.

The intended conceptual structure is:

```text
WorldState
│
├── Time
│   ├── step
│   ├── day
│   └── hour
│
├── Self
│   ├── money
│   ├── farm
│   ├── farmer
│   ├── hands
│   ├── unlocked_quadrants
│   └── hires_today
│
├── Opponent
│   ├── money
│   ├── farm
│   ├── farmer
│   ├── hands
│   └── unlocked_quadrants
│
├── Private
│   ├── shed
│   ├── seeds
│   └── inventories
│
├── Market
│   ├── inventory
│   └── prices
│
└── Town
    └── unlocked_shops
```

Do not implement this blindly.

The exact schema should be frozen only after Phase 0 experiments verify the observation structure.

---

# 9. State History

The current observation is not enough.

We need historical information.

For example:

```text
Day 10    Wheat price = 40
Day 11    Wheat price = 42
Day 12    Wheat price = 39
Day 13    Wheat price = 35
```

This allows us to derive:

- Price trends
- Price volatility
- Market inventory trends
- Opponent production trends
- Town consumption trends
- Our own production trends
- Strategy performance

Eventually:

```python
StateHistory(
    market_history=...,
    opponent_history=...,
    production_history=...,
    actions=...
)
```

---

# 10. World Models

The World Model predicts what happens in the future.

It should initially be deterministic wherever the environment is deterministic.

Major models:

```text
Farm Model
Crop Model
Animal Model
Production Model
Market Model
Town Model
Opponent Model
```

---

# 11. Farm Model

The Farm Model tracks:

- Land
- Tiles
- Crops
- Animals
- Buildings
- Workers
- Seeds
- Fertilizer
- Inventory
- Positions

It should answer questions such as:

```text
How many usable tiles do I have?

How many empty tiles exist?

How many workers exist?

What crops are currently growing?

Which crops are ready?

Which animals are active?

What resources are available?
```

---

# 12. Crop Model

The Crop Model should represent crop lifecycle.

Conceptually:

```text
Plant
  ↓
Water
  ↓
Grow
  ↓
Potential fertilizer
  ↓
Harvest
  ↓
Inventory
  ↓
Sell
```

It should calculate:

```text
expected yield
harvest time
required actions
watering requirements
fertilizer effects
labor requirement
expected revenue
```

Do not hard-code economic conclusions into the crop model.

The crop model describes mechanics.

The planner decides whether the crop is worthwhile.

---

# 13. Animal Model

Animals are recurring production systems.

Conceptually:

```text
Purchase
   ↓
Housing
   ↓
Feed
   ↓
Care
   ↓
Production
   ↓
Harvest
   ↓
Sell
```

The model should calculate:

```text
animal cost
feed requirement
production frequency
production quantity
care effects
labor requirement
expected revenue
```

The economic planner then determines whether the animal is worth owning.

---

# 14. Market Model

The market is one of the most important components.

The price is dynamic.

The value of selling a quantity is not necessarily:

```text
current_price × quantity
```

because selling itself can affect the market.

We therefore need:

```text
Revenue(quantity)
```

rather than assuming constant price.

The Market Model should eventually consider:

```text
Current market inventory
+
Town consumption
+
Our future production
+
Opponent future production
+
Player sales
+
Player purchases
```

and predict:

```text
future prices
```

The planner should be able to ask:

```text
What happens if I sell 5?

What happens if I sell 20?

What happens if I sell 50?

What happens if I hold until tomorrow?
```

---

# 15. Town Model

Town shops affect demand.

The model should track:

- Unlocked shops
- Consumption
- Resource requirements
- Timing
- Demand changes

Eventually we want:

```text
Town
  ↓
Expected consumption
  ↓
Market inventory
  ↓
Future prices
  ↓
Production decisions
```

---

# 16. Opponent Model

This is a major area where we want to improve over simple heuristic solutions.

The opponent has publicly observable information but also hidden/private information.

We should track:

```text
Observed opponent state
        ↓
Historical behavior
        ↓
Production estimate
        ↓
Future supply estimate
```

Initially this can be heuristic.

Later we can experiment with:

```text
Opponent Model v1
Rule-based

Opponent Model v2
Statistical

Opponent Model v3
Machine learning
```

Do not introduce ML until the simpler model has been tested.

---

# 17. Strategic Planner

The Strategic Planner determines what we should pursue.

It receives:

```text
WorldState
+
World Models
+
Historical State
```

and generates candidate strategies.

Example:

### Strategy A

```text
Aggressive crop production
Expand land
Hire workers
Sell frequently
```

### Strategy B

```text
Animal-heavy strategy
Increase sheep
Exploit wool demand
```

### Strategy C

```text
Conservative strategy
Preserve cash
High-value crops
Minimal expansion
```

### Strategy D

```text
Market timing
Hold inventory
Sell in controlled batches
```

The planner should eventually compare these rather than assume one is always optimal.

---

# 18. Planning Horizon

Do NOT attempt to solve all 720 turns every time.

Use a receding-horizon approach.

Conceptually:

```text
Current State
     ↓
Plan next N turns
     ↓
Execute some/all of plan
     ↓
Observe new state
     ↓
Re-plan
```

For example:

```text
Day 8
  ↓
Plan days 8–11
  ↓
Execute
  ↓
New observation
  ↓
Re-plan
```

This gives the agent adaptability.

---

# 19. Future Simulator

The Future Simulator is one of the most important components.

It answers:

> What happens if we follow this plan?

For example:

```text
Strategy A
    ↓
Simulate
    ↓
Projected final wealth = 7,800

Strategy B
    ↓
Simulate
    ↓
Projected final wealth = 8,200

Strategy C
    ↓
Simulate
    ↓
Projected final wealth = 6,900
```

Then the Strategy Scorer selects among them.

---

# 20. Simulator Architecture

The long-term target is:

```text
                 CURRENT WORLD STATE
                         │
                         ▼
                  Candidate Plan
                         │
                         ▼
                 ┌───────────────┐
                 │   Simulator   │
                 └───────┬───────┘
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
         Future t+1   Future t+2   Future t+N
             │           │           │
             └───────────┼───────────┘
                         ▼
                    Final state
                         │
                         ▼
                       Score
```

Eventually this simulator should model:

- Farm
- Crops
- Animals
- Market
- Town
- Opponent
- Workers
- Movement
- Inventory
- Time
- Actions

---

# 21. Strategy Scorer

The scorer should reflect the actual competition objective.

We should not blindly optimize:

```text
total production
```

or:

```text
inventory value
```

The final competitive outcome matters.

The exact scoring function should be verified from the competition environment before being frozen.

Potential internal metrics include:

```text
Expected final money
Probability of winning
Expected margin
Risk
Cash availability
Resource utilization
```

---

# 22. Tactical Planner

Once the strategic planner chooses:

```text
Produce 10 wheat
Maintain 4 sheep
Harvest by turn X
Sell when price reaches threshold
```

the Tactical Planner converts that into concrete tasks.

Example:

```text
Plant wheat
Water wheat
Feed sheep
Care sheep
Harvest tomato
Collect fertilizer
Sell wheat
```

The Tactical Planner handles:

- Dependencies
- Timing
- Worker assignment
- Task conflicts
- Movement
- Deadlines

---

# 23. OR-Tools

OR-Tools should NOT be the architecture.

It should be a tool inside the architecture.

Potential placement:

```text
Strategic/Tactical Planning
          │
          ▼
   Candidate constraints
          │
          ▼
      OR-Tools
          │
          ▼
    Feasible schedule
```

Potential uses:

- Integer optimization
- CP-SAT
- Scheduling
- Worker assignment
- Resource allocation
- Land allocation
- Production planning

But we should first determine what optimization problem actually exists.

Do not introduce OR-Tools before we have a validated model.

---

# 24. Execution Layer

The execution layer should be deliberately simple.

```text
Tactical Plan
     ↓
Task Queue
     ↓
Worker Assignment
     ↓
Pathfinding
     ↓
One-turn action
     ↓
Environment
```

It should:

- Validate actions
- Execute actions
- Handle movement
- Track task progress
- Report failures
- Avoid making strategic decisions

---

# 25. Pathfinding

The board is small.

A simple deterministic pathfinding algorithm such as BFS is likely sufficient.

We do not need ML for movement unless experiments prove otherwise.

The competitor's solution uses BFS-style movement and task assignment, which is a good idea to retain conceptually.

---

# 26. Offline Simulation and Evaluation

A major objective is to build a local simulation environment.

Once the environment model is reliable, we want:

```text
                 LOCAL SIMULATOR
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     Agent A        Agent B        Agent C
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                  Evaluation
```

We should eventually be able to run thousands of simulated episodes.

Metrics:

```text
Win rate
Loss rate
Tie rate

Final money
Final inventory

Land acquired
Crop production
Animal production

Worker utilization
Market impact

Average performance
Variance
```

---

# 27. Experiment-Driven Development

Every major change must be evaluated experimentally.

Example:

```text
Experiment
-----------
Baseline heuristic

Variant
-----------
Dynamic crop planner

Runs
-----------
1000 games

Results
-----------
Baseline win rate = 52.1%
Variant win rate  = 58.7%
```

Only keep changes that improve performance or provide some other demonstrated advantage.

Do not assume that a more sophisticated architecture is automatically better.

---

# 28. Competitor Solution We Found

We found a solution/code from another Kaggle participant.

This is **not the official competition specification**.

It should be treated as competitive intelligence.

The competitor built a sophisticated heuristic/task-dispatch system.

Conceptually:

```text
Observation
    ↓
Parse Farm State
    ↓
Animal Census
    ↓
Market Strategy
    ↓
Workforce Calculation
    ↓
Task Generation
    ↓
Task Assignment
    ↓
BFS Movement
    ↓
Actions
```

The competitor's implementation has several strong ideas.

---

# 29. What We Should Learn From the Competitor

## State abstraction

They transform raw board state into useful derived structures.

Examples:

```text
animals
empty_pastures
plants
weeds
empty_tiles
```

This is good and should influence our State Engine.

---

## Animal census

They account for animals across different locations, including:

```text
Field
Shed
Worker-held
```

This is good resource accounting.

---

## Task abstraction

They represent work as tasks with properties such as:

```text
Task
    priority
    position
    action
    requirements
```

This is a good execution architecture.

---

## Worker assignment

They assign workers based on:

```text
priority
+
distance
+
task requirements
```

This is a good baseline.

---

## BFS movement

The board is small, so BFS is a sensible pathfinding solution.

---

## Workforce estimation

They estimate required workers based on workload rather than blindly hiring.

This is a good idea.

---

## Demand awareness

They inspect town shops and modify production targets accordingly.

Again, this is directionally correct.

---

## End-game liquidation

They recognize that the game ends with money rather than simply maximizing inventory.

This is important.

---

# 30. Competitor Weaknesses

The competitor solution is primarily a **reactive heuristic system**.

Its basic pattern is:

```text
Current state
    ↓
Hard-coded rules
    ↓
Tasks
    ↓
Actions
```

Examples of hard-coded decisions include:

```text
Specific crop choices based on day
Specific animal targets
Specific land purchase days
Manually chosen workforce coefficients
Manual fertilizer rules
Immediate selling behavior
```

These are reasonable heuristics, but they are not a general predictive planning system.

---

# 31. Our Intended Advantage

Our target architecture is:

```text
Current State
     ↓
World Model
     ↓
Candidate Strategies
     ↓
Future Simulation
     ↓
Strategy Evaluation
     ↓
Optimization/Search
     ↓
Tactical Scheduling
     ↓
Action
```

The important distinction is:

### Competitor

```text
State
 ↓
Rules
 ↓
Action
```

### Our target

```text
State
 ↓
Prediction
 ↓
Possible futures
 ↓
Evaluation
 ↓
Best strategy
 ↓
Action
```

This does not mean our solution is automatically better.

The competitor has a working implementation.

Our architecture is currently only a design.

Every proposed improvement must be validated.

---

# 32. Things We Should NOT Copy Directly

Avoid making these the foundation:

```text
Hard-coded crop calendar
Hard-coded animal targets
Hard-coded land purchase days
Hard-coded workforce coefficients
Immediate selling as the default
Static market assumptions
No meaningful opponent prediction
No future-state evaluation
```

These can be useful as baselines, but should not become immutable rules.

---

# 33. Things We Should Reuse Conceptually

Strong competitor ideas:

```text
State abstraction
Animal census
Task abstraction
Worker assignment
BFS movement
Market action separation
Workload-based hiring
Demand awareness
End-game liquidation
```

These belong primarily in our:

```text
State Engine
+
Tactical Planner
+
Execution Layer
```

Our predictive intelligence should sit above them.

---

# 34. Development Philosophy

The project must be developed incrementally.

Use:

```text
Experiment
   ↓
Observation
   ↓
Hypothesis
   ↓
Implementation
   ↓
Measurement
   ↓
Decision
```

Do NOT do:

```text
Idea
 ↓
Huge implementation
 ↓
Hope it works
```

Every phase needs a measurable checkpoint.

---

# 35. Phase Roadmap

## Phase 0 — Environment Reconnaissance

Goal:

> Understand the real environment.

Tasks:

```text
0.1 Environment startup
0.2 Observation structure
0.3 PASS/PASS transition
0.4 Clock behavior
0.5 Autonomous market behavior
0.6 Action transitions
0.7 Freeze environment model
```

---

## Phase 1 — WorldState

Build:

```text
WorldState
FarmState
TileState
PlantState
AnimalState
MarketState
TownState
PlayerState
```

Input:

```text
Raw observation
```

Output:

```text
Clean internal state
```

Checkpoint:

> We can reconstruct the important environment state from every observation.

---

## Phase 2 — Action Engine

Represent actions internally.

Examples:

```text
MOVE
PLANT
WATER
HARVEST
FEED
CARE
BUY
SELL
HIRE
BUILD
FERTILIZE
```

Checkpoint:

> Internal actions can be translated safely into Kaggle actions.

---

## Phase 3 — Environment Transition Model

Build a deterministic model for environment mechanics.

Goal:

```text
State(t) + Action
        ↓
Predicted State(t+1)
```

Checkpoint:

> Predicted state matches actual environment behavior.

---

## Phase 4 — Baseline Agent

Build a very simple reliable agent.

Potentially:

```text
Competitor-inspired heuristics
```

Purpose:

> Establish a measurable baseline.

Checkpoint:

```text
Baseline win rate
Average final money
```

---

## Phase 5 — Evaluation Framework

Build:

```text
Episode runner
Tournament runner
Metrics
Experiment tracking
```

Checkpoint:

> We can compare two agents statistically.

---

## Phase 6 — World Models

Implement:

```text
Crop Model
Animal Model
Production Model
Market Model
Town Model
Opponent Model
```

Checkpoint:

> Given a state and plan, we can predict future consequences reasonably accurately.

---

## Phase 7 — Strategic Planner

Generate candidate strategies.

Checkpoint:

> Planner can produce multiple feasible economic strategies.

---

## Phase 8 — Future Simulator

Simulate candidate strategies.

Checkpoint:

> Simulator can rank strategies based on projected outcomes.

---

## Phase 9 — Tactical Scheduler

Convert strategies into executable tasks.

Potential tools:

```text
Heuristics
OR-Tools
CP-SAT
Search
```

Checkpoint:

> Strategy can be converted into legal, efficient actions.

---

## Phase 10 — Opponent Model

Predict:

```text
Opponent production
Opponent expansion
Opponent strategy
Market impact
```

Checkpoint:

> Agent adapts to opponent behavior.

---

## Phase 11 — Optimization / Search

Evaluate:

```text
CP-SAT
MIP
Beam Search
MCTS
Dynamic Programming
Other approaches
```

Do not assume one method is best.

Experiment.

---

## Phase 12 — Learning

Only after the simulator and baseline system are strong should we investigate:

```text
Reinforcement Learning
Self-play
Policy networks
Value networks
Evolutionary methods
Learned opponent models
```

The simulator is what makes these approaches practical.

---

## Phase 13 — Kaggle Submission

Integrate the final validated agent into:

```text
main.py
```

Then test:

```text
Local environment
       ↓
Kaggle submission
       ↓
Leaderboard
       ↓
Analyze
       ↓
Improve
```

---

# 36. Current Development Setup

Current files:

```text
kagriculture.ipynb
main.py
```

`main.py` currently contains a simple probe agent:

```python
printed = False

def probe_agent(obs):
    global printed

    if not printed:
        print("=" * 80)
        print("INITIAL OBSERVATION")
        print("=" * 80)

        from pprint import pprint
        pprint(obs)

        printed = True

    return {
        "farmer": ["PASS"],
        "market": [],
    }
```

This is intentionally not an intelligent agent yet.

It is an environment probe.

---

# 37. Notebook Role

The notebook is our experimental laboratory.

Use it for:

```text
Environment experiments
Observation analysis
State transition analysis
Market analysis
Visualizations
Statistical experiments
Simulator validation
Strategy experiments
Agent comparisons
```

The notebook should contain experiments with clear labels.

Example:

```text
# Phase 0.3 — PASS/PASS Transition

Question:
What changes when both players do nothing?

Setup:
seed = 42
episodeSteps = 48

Observation:
...

Conclusion:
...

Implementation consequence:
...
```

---

# 38. main.py Role

`main.py` is the production agent.

Do not dump experimental code into it.

Eventually:

```text
main.py
   ↓
agent(obs)
   ↓
Environment Adapter
   ↓
State Engine
   ↓
Planner
   ↓
Scheduler
   ↓
Executor
   ↓
Action
```

During early development, it can remain very small.

---

# 39. Experiments Completed

## Experiment 0.1 — Environment Startup

Status:

```text
PASSED
```

The Kaggriculture environment successfully executes.

---

## Experiment 0.2 — Observation Inspection

Status:

```text
PASSED
```

We confirmed that observations contain major components including:

```text
player
farms
private
market
town
day
hour
```

Farm state contains information about:

```text
money
tiles
farmer
hands
unlocked quadrants
hires_today
```

Private state contains information such as:

```text
shed
seeds
inventories
```

Market contains:

```text
inventory
prices
```

Town contains:

```text
unlocked_shops
```

---

# 40. Initial Observation

Our captured initial state showed approximately:

```text
day = 0
hour = 0

player 0 money = 2000
player 1 money = 2000

player 0 farmer = (4,4)
player 1 farmer = (4,4)

hands = 0

unlocked land = NW
```

The exact raw observation should remain the source of truth.

---

# 41. PASS/PASS Experiment

We ran both players with:

```python
{
    "farmer": ["PASS"],
    "market": []
}
```

for a short episode.

Observed:

```text
Money remains unchanged.
Farmer positions remain unchanged.
No workers appear.
Market inventory changes.
Market prices change.
Time advances.
```

This is an important result.

It means:

> `PASS` does not mean "the world remains unchanged."

It means the player does nothing, while the environment can still advance and perform autonomous processes.

---

# 42. Important Observation About Market

During PASS/PASS:

```text
WHEAT inventory
10000
   ↓
9999
   ↓
...
9992
```

even though neither player performed market actions.

Therefore the market must have autonomous dynamics, such as environmental/town consumption or another scheduled mechanism.

Do not assume:

```python
market_inventory -= player_purchase
```

is the complete market transition.

We need to experimentally determine the exact mechanism.

---

# 43. Important Observation About Time

The experiment showed that the relationship between:

```text
step
day
hour
```

must be carefully verified.

Do not blindly implement:

```python
day = step // 24
hour = step % 24
```

until the actual environment behavior confirms this.

This is why Phase 0 is experiment-driven.

---

# 44. Current Position

Current status:

```text
Phase 0
├── Environment startup       ✅
├── Observation discovery     ✅
├── PASS/PASS experiment      ✅
├── Clock analysis            ⬅ CURRENT
├── Market mechanics          ⬜
├── Action mechanics          ⬜
└── Environment model         ⬜

Phase 1
└── WorldState                ⬜
```

---

# 45. Immediate Next Step

The next task is **NOT** to build the agent.

The next task is:

> Determine the exact clock and environment transition behavior.

In the notebook, analyze:

```python
df[["step", "day", "hour"]].head(30)
```

and:

```python
df[["step", "day", "hour"]].drop_duplicates()
```

Also:

```python
df.groupby(["day", "hour"]).size().reset_index(name="observations")
```

Then analyze market inventory changes.

For example:

```python
market_df = pd.DataFrame(df["market_inventory"].tolist())

market_df["step"] = df["step"]
market_df["day"] = df["day"]
market_df["hour"] = df["hour"]

market_df["WHEAT_change"] = market_df["WHEAT"].diff()

display(
    market_df[
        market_df["WHEAT_change"].fillna(0) != 0
    ][
        ["step", "day", "hour", "WHEAT", "WHEAT_change"]
    ]
)
```

Also inspect price changes.

---

# 46. Rules for Claude

When helping with this project, follow these rules.

## Rule 1 — Do not jump ahead

If we are in Phase 0, don't start designing the optimizer.

If we are validating the State Engine, don't start designing RL.

Stay on the current phase unless explicitly asked to move forward.

---

## Rule 2 — Experiments before assumptions

If something can be measured from the environment, prefer an experiment over guessing.

For example:

Bad:

```text
I assume two observations occur per turn.
```

Good:

```text
Let's run a controlled experiment and inspect step/day/hour.
```

---

## Rule 3 — Official environment is ground truth

Use the actual Kaggriculture environment as the final authority for runtime behavior.

Competition documentation provides intended behavior.

Experiments verify actual behavior.

---

## Rule 4 — Competitor code is not ground truth

The other Kaggle participant's solution is useful for:

- Ideas
- Architecture inspiration
- Baselines
- Competitive analysis
- Potential weaknesses

But don't assume their implementation is correct or optimal.

---

## Rule 5 — Don't over-engineer early

Avoid prematurely introducing:

```text
RL
Neural networks
MCTS
OR-Tools
Complex optimization
LLMs
```

First build:

```text
Reliable environment model
Reliable state model
Reliable action model
Reliable simulator
Reliable baseline
Reliable evaluation
```

---

## Rule 6 — Every new component must have a measurable purpose

Before implementing something, answer:

```text
What problem does this solve?
How will we measure whether it helps?
What baseline are we comparing against?
```

---

## Rule 7 — Preserve replaceability

Components should have clean interfaces.

For example:

```text
StrategyPlanner
    ↓
Strategy

TacticalPlanner
    ↓
ActionPlan

Executor
    ↓
KaggleAction
```

This allows us to replace:

```text
Heuristic Planner
```

with:

```text
OR-Tools Planner
```

or:

```text
MCTS Planner
```

without rewriting the entire system.

---

## Rule 8 — Prefer simple solutions where appropriate

For example:

```text
10×10 board
    ↓
BFS
```

is likely better than a neural pathfinder.

Use sophisticated methods only where the problem actually requires them.

---

# 47. Final Target

The final system should ideally operate like this:

```text
                   OBSERVATION
                        │
                        ▼
                 Update WorldState
                        │
                        ▼
                 Update History
                        │
                        ▼
                Predict World
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Market        Production    Opponent
       Forecast      Forecast      Forecast
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                Generate Strategies
                        │
                        ▼
                Simulate Futures
                        │
                        ▼
                Score Strategies
                        │
                        ▼
                 Select Strategy
                        │
                        ▼
                Generate Tasks
                        │
                        ▼
              Optimize Schedule
                        │
                        ▼
                 Assign Workers
                        │
                        ▼
                 Pathfinding
                        │
                        ▼
                    ACTION
                        │
                        ▼
                  ENVIRONMENT
                        │
                        ▼
                   OBSERVATION
                        │
                        └─────────────── LOOP
```

The long-term objective is:

> **Build an agent that continuously estimates the state of the game, predicts how the market/farm/opponent will evolve, evaluates alternative strategies through simulation, selects the best strategy, schedules the required actions efficiently, executes them, and then re-plans from the new state.**

But we reach that system **incrementally**, with experiments validating every layer.

---

# 48. Current Instruction

**Continue from the current notebook state.**

Do not restart the project.

Do not redesign the architecture.

Do not implement OR-Tools yet.

Do not implement RL yet.

Do not create the complete project structure yet.

First finish:

```text
Phase 0.4 — Clock analysis
```

Then:

```text
Phase 0.5 — Autonomous market behavior
```

Then:

```text
Phase 0.6 — Individual action transitions
```

Then freeze:

```text
Phase 0 — Environment Model
```

Only after that begin:

```text
Phase 1 — WorldState
```

The development philosophy is:

> **Measure → Understand → Model → Implement → Validate → Improve.**

Do not skip steps.