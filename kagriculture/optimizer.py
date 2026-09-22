"""
Optimizer for Kaggriculture — Phase 9.
Uses OR-Tools CP-SAT to optimally assign workers to tasks,
accounting for effective multi-step travel distance (shed pickups) and pinned tasks.

Falls back to assign_tasks if OR-Tools is unavailable or times out.
"""
from typing import Dict, List, Optional
from task_manager import Task, effective_distance, assign_tasks
from world_state import WorkerState

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


def optimize_assignments(
    workers: List[WorkerState],
    tasks: List[Task],
    time_limit_ms: int = 400
) -> Dict[int, Optional[Task]]:
    """
    Assign tasks to workers using OR-Tools CP-SAT.
    Maximizes weighted priority coverage while minimizing effective travel distance.
    """
    if not ORTOOLS_AVAILABLE or len(workers) < 2 or len(tasks) < 2:
        return assign_tasks(workers, tasks)

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

    # Constraint: pinned tasks (e.g. DROP_OFF pinned to a specific worker)
    for t, task in enumerate(tasks):
        if task.worker_id is not None:
            for w, worker in enumerate(workers):
                if worker.worker_id != task.worker_id:
                    model.Add(x[w][t] == 0)

    # Objective: maximize sum of (priority * 20 - effective_distance)
    MAX_DIST = 25
    objective_terms = []
    for w, worker in enumerate(workers):
        for t, task in enumerate(tasks):
            dist = effective_distance(worker, task)
            weight = (task.priority * MAX_DIST) - dist
            weight_shifted = weight + (MAX_DIST * 20)  # offset to ensure non-negative
            objective_terms.append(weight_shifted * x[w][t])

    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_ms / 1000.0
    solver.parameters.log_search_progress = False
    status = solver.Solve(model)

    assignments: Dict[int, Optional[Task]] = {w.worker_id: None for w in workers}

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for w, worker in enumerate(workers):
            for t, task in enumerate(tasks):
                if solver.Value(x[w][t]) == 1:
                    assignments[worker.worker_id] = task
                    break
    else:
        return assign_tasks(workers, tasks)

    return assignments
