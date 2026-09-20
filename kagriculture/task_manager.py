"""
Task Manager for Kaggriculture.
Generates farming tasks (WATER, HARVEST, PLANT, DIG) from WorldState
and assigns them to available workers.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
from world_state import WorldState, TileState, WorkerState
from pathfinding import manhattan_distance, next_move
import action_engine as ae

TASK_PRIORITIES = {
    "FEED": 11,      # Crucial for animal survival and production
    "WATER": 10,     # Prevent weeds & boost yield
    "HARVEST": 9,    # Harvest mature crops before decay
    "HARVEST_ANIMAL": 9, # Harvest animal products
    "CARE": 8,       # Care for animals
    "PLACE_ANIMAL": 7, # Place animals in structures
    "BUILD_STRUCTURE": 6, # Build pastures and coops
    "PLANT": 5,      # Keep farm occupied
    "DIG": 2,        # Clear weeds
    "IDLE": 0,
}

@dataclass
class Task:
    task_type: str        # 'WATER', 'HARVEST', 'PLANT', 'DIG', 'IDLE'
    target_pos: Tuple[int, int]  # (x, y)
    priority: int
    crop: Optional[str] = None   # For PLANT tasks
    worker_id: Optional[int] = None

    def __lt__(self, other: "Task") -> bool:
        return self.priority > other.priority  # Higher priority first


def generate_tasks(world: WorldState, default_crop: str = "WHEAT") -> List[Task]:
    """
    Generates all active tasks needed on the farm this turn.
    """
    tasks: List[Task] = []
    farm = world.my_farm
    
    # 1. WATER tasks for all unwatered crops
    for tile in farm.unwatered_crop_tiles:
        tasks.append(Task(
            task_type="WATER",
            target_pos=tile.pos,
            priority=TASK_PRIORITIES["WATER"]
        ))
        
    # 2. HARVEST tasks for all harvestable crops
    for tile in farm.ready_to_harvest_tiles:
        # If crop is ready to harvest, prioritize it
        tasks.append(Task(
            task_type="HARVEST",
            target_pos=tile.pos,
            priority=TASK_PRIORITIES["HARVEST"],
            crop=tile.crop
        ))
        
    # 3. PLANT tasks: only for empty unlocked tiles if we have seeds
    seeds_available = dict(world.private.seeds)
    if seeds_available.get(default_crop, 0) > 0:
        available_seeds = seeds_available[default_crop]
        # Sort empty tiles by distance to shed (4, 4) for tighter farming clusters
        sorted_empty = sorted(
            farm.empty_tiles,
            key=lambda t: manhattan_distance(t.pos, (4, 4))
        )
        for tile in sorted_empty[:available_seeds]:
            tasks.append(Task(
                task_type="PLANT",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["PLANT"],
                crop=default_crop
            ))
            
    # 4. DIG tasks for weeds
    for tile in farm.weed_tiles:
        tasks.append(Task(
            task_type="DIG",
            target_pos=tile.pos,
            priority=TASK_PRIORITIES["DIG"]
        ))
        
    # 5. Animal tasks: FEED, HARVEST_ANIMAL, CARE
    # Assumes WHEAT is used for feed. We check private.shed.
    wheat_in_shed = world.private.shed.get("WHEAT", 0)
    for tile in farm.structure_tiles:
        if tile.ready_to_harvest:
            tasks.append(Task(
                task_type="HARVEST_ANIMAL",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["HARVEST_ANIMAL"]
            ))
        if tile.needs_feed and wheat_in_shed > 0:
            tasks.append(Task(
                task_type="FEED",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["FEED"]
            ))
            wheat_in_shed -= 1 # Prevent over-queueing if we lack wheat
            
    # 6. PLACE_ANIMAL tasks for empty structures
    unplaced_animals = []
    for animal in ["GOOSE", "COW", "SHEEP"]:
        for _ in range(world.private.shed.get(animal, 0)):
            unplaced_animals.append(animal)
            
    for tile in farm.empty_structures:
        if not unplaced_animals:
            break
            
        animal_to_place = None
        for a in unplaced_animals:
            if tile.structure_kind == "COOP" and a == "GOOSE":
                animal_to_place = a
                break
            elif tile.structure_kind == "PASTURE" and a in ("COW", "SHEEP"):
                animal_to_place = a
                break
                
        if animal_to_place:
            unplaced_animals.remove(animal_to_place)
            tasks.append(Task(
                task_type="PLACE_ANIMAL",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["PLACE_ANIMAL"],
                crop=animal_to_place # We reuse crop field for item
            ))
            
    # 7. BUILD_STRUCTURE tasks if we still have unplaced animals
    coops_needed = unplaced_animals.count("GOOSE")
    pastures_needed = sum(1 for a in unplaced_animals if a in ("COW", "SHEEP"))
    
    # We use empty tiles that are furthest from the shed (4, 4) for structures
    # so crops stay closer to the shed
    if coops_needed > 0 or pastures_needed > 0:
        sorted_empty_rev = sorted(
            farm.empty_tiles,
            key=lambda t: manhattan_distance(t.pos, (4, 4)),
            reverse=True
        )
        for tile in sorted_empty_rev:
            if coops_needed > 0:
                tasks.append(Task(
                    task_type="BUILD_STRUCTURE",
                    target_pos=tile.pos,
                    priority=TASK_PRIORITIES["BUILD_STRUCTURE"],
                    crop="COOP"
                ))
                coops_needed -= 1
            elif pastures_needed > 0:
                tasks.append(Task(
                    task_type="BUILD_STRUCTURE",
                    target_pos=tile.pos,
                    priority=TASK_PRIORITIES["BUILD_STRUCTURE"],
                    crop="PASTURE"
                ))
                pastures_needed -= 1
            else:
                break
                
    return tasks


def assign_tasks(
    workers: List[WorkerState],
    tasks: List[Task]
) -> Dict[int, Optional[Task]]:
    """
    Greedy assignment of tasks to workers:
    Workers pick the highest priority / nearest task available.
    """
    assignments: Dict[int, Optional[Task]] = {w.worker_id: None for w in workers}
    if not tasks:
        return assignments
        
    remaining_tasks = list(tasks)
    # Sort tasks by priority descending
    remaining_tasks.sort(key=lambda t: t.priority, reverse=True)
    
    assigned_targets: Set[Tuple[int, int]] = set()
    
    for worker in workers:
        best_task = None
        best_score = -999999
        best_idx = -1
        
        for idx, task in enumerate(remaining_tasks):
            if task.target_pos in assigned_targets:
                continue
                
            dist = manhattan_distance(worker.pos, task.target_pos)
            # Score balances priority (weight 10) vs distance penalty
            score = (task.priority * 10) - dist
            
            if score > best_score:
                best_score = score
                best_task = task
                best_idx = idx
                
        if best_task is not None:
            assignments[worker.worker_id] = best_task
            assigned_targets.add(best_task.target_pos)
            remaining_tasks.pop(best_idx)
            
    return assignments


def execute_worker_task(worker: WorkerState, task: Optional[Task], world: WorldState) -> List[str]:
    """
    Translates a task assignment into an action for that worker:
    - If at target: perform action
    - If not at target: move towards target
    - If no task: move towards shed (4, 4) or PASS
    """
    if task is None:
        if worker.pos != (4, 4):
            mv = next_move(worker.pos, (4, 4))
            if mv:
                return ae.move_action(mv)
        return ae.pass_worker_action()
        
    # Check if worker is already on the target tile
    if worker.pos == task.target_pos:
        if task.task_type == "WATER":
            return ae.water_action()
        elif task.task_type == "HARVEST":
            return ae.harvest_action()
        elif task.task_type == "HARVEST_ANIMAL":
            return ae.harvest_action()
        elif task.task_type == "FEED":
            return ae.feed_action()
        elif task.task_type == "CARE":
            return ae.care_action()
        elif task.task_type == "PLACE_ANIMAL":
            animal = task.crop
            if animal:
                return ae.place_action(animal, 1)
        elif task.task_type == "BUILD_STRUCTURE":
            struct_type = task.crop
            if struct_type == "COOP":
                return ae.build_coop_action()
            elif struct_type == "PASTURE":
                return ae.build_pasture_action()
        elif task.task_type == "PLANT":
            crop = task.crop or "WHEAT"
            return ae.plant_action(crop)
        elif task.task_type == "DIG":
            return ae.dig_action()
            
    # Worker is not at target -> move towards it
    mv = next_move(worker.pos, task.target_pos)
    if mv:
        return ae.move_action(mv)
        
    return ae.pass_worker_action()
