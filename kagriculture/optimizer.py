"""
Optimizer for Kaggriculture — Phase 7.
Uses OR-Tools CP-SAT to optimally assign workers to tasks,
minimizing total travel distance and maximizing task coverage.

Falls back to greedy assignment if OR-Tools is unavailable or times out.
"""
from typing import Dict, List, Optional, Tuple
from task_manager import Task
from world_state import WorkerState
from pathfinding import manhattan_distance

# Try importing OR-Tools; fall back gracefully if not available
try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


def _greedy_assign(
    workers: List[WorkerState],
    tasks: List[Task]
) -> Dict[int, Optional[Task]]:
    """Greedy fallback assignment."""
    from task_manager import assign_tasks
    return assign_tasks(workers, tasks)


def optimize_assignments(
    workers: List[WorkerState],
    tasks: List[Task],
    time_limit_ms: int = 500
) -> Dict[int, Optional[Task]]:
    """
    Assign tasks to workers using OR-Tools CP-SAT.
    Maximizes weighted priority coverage while minimizing total travel distance.

    Falls back to greedy assignment if:
      - OR-Tools is not installed
      - Problem is trivially small (< 2 workers or < 2 tasks)
      - Solver times out without a feasible solution
    """
    if not ORTOOLS_AVAILABLE or len(workers) < 2 or len(tasks) < 2:
        return _greedy_assign(workers, tasks)

    model = cp_model.CpModel()
    W = len(workers)
    T = len(tasks)

    # Decision variables: x[w][t] = 1 if worker w is assigned to task t
    x = [[model.NewBoolVar(f"x_w{w}_t{t}") for t in range(T)] for w in range(W)]

    # Constraint: each task assigned to at most one worker
    for t in range(T):
        model.Add(sum(x[w][t] for w in range(W)) <= 1)

    # Constraint: each worker assigned to at most one task
    for w in range(W):
        model.Add(sum(x[w][t] for t in range(T)) <= 1)

    # Objective: maximize sum of (priority * 100 - distance) for all assigned pairs
    MAX_DIST = 20  # Max possible manhattan distance on a 10x10 grid
    objective_terms = []
    for w, worker in enumerate(workers):
        for t, task in enumerate(tasks):
            dist = manhattan_distance(worker.pos, task.target_pos)
            # Scale priority up so it dominates the distance penalty
            weight = (task.priority * MAX_DIST) - dist
            # Shift to ensure positive weights (CP-SAT requires non-negative for maximize)
            weight_shifted = weight + (MAX_DIST * 15)  # offset so always positive
            objective_terms.append(weight_shifted * x[w][t])

    model.Maximize(sum(objective_terms))

    # Solve with time limit
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_ms / 1000.0
    solver.parameters.log_search_progress = False
    status = solver.Solve(model)

    # Build result
    assignments: Dict[int, Optional[Task]] = {w.worker_id: None for w in workers}

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for w, worker in enumerate(workers):
            for t, task in enumerate(tasks):
                if solver.Value(x[w][t]) == 1:
                    assignments[worker.worker_id] = task
                    break
    else:
        # Fallback if solver couldn't find feasible solution in time
        return _greedy_assign(workers, tasks)

    return assignments
