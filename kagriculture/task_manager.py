"""
Task Manager for Kaggriculture — Phase 9: Coordinated Multi-Worker Pipeline.
Generates farming tasks (FEED, CARE, WATER, HARVEST, PLACE_ANIMAL, BUILD_STRUCTURE, DROP_OFF, PLANT, DIG)
and manages multi-step worker execution including shed pickups and drops.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
from world_state import WorldState, TileState, WorkerState
from pathfinding import manhattan_distance, next_move
import action_engine as ae

SHED_POS = (4, 4)
PRODUCE_ITEMS = {"MILK", "WOOL", "EGG", "MELON", "CARROT", "TOMATO", "STRAWBERRY", "FERTILIZER"}

TASK_PRIORITIES = {
    "FEED": 15,               # CRITICAL: unfed animals escape after 2 days — always first
    "CARE": 14,               # Phase 17: Care for animals to compound yield bonus (highest after feed)
    "WATER": 13,              # CRITICAL: unwatered crops weed after 2 days — second
    "COLLECT_FERTILIZER": 12, # Free fertilizer from animals — do after survival needs met
    "HARVEST_ANIMAL": 11,     # Collect high-value animal products before cap
    "HARVEST": 11,            # Harvest mature crops before decay
    "FERTILIZE": 9,           # Apply fertilizer to crops
    "DROP_OFF": 8,            # Deposit harvested goods into shed for market sale
    "PLACE_ANIMAL": 7,        # Place purchased animals in structures
    "BUILD_STRUCTURE": 6,     # Build pastures and coops for unplaced animals
    "PLANT": 5,               # Keep tiles productive
    "DIG": 2,                 # Clear weeds
    "IDLE": 0,
}

@dataclass
class Task:
    task_type: str        # 'FEED', 'WATER', 'HARVEST', 'PLACE_ANIMAL', 'BUILD_STRUCTURE', 'DROP_OFF', 'PLANT', 'CARE', 'DIG'
    target_pos: Tuple[int, int]  # (x, y)
    priority: int
    crop: Optional[str] = None   # For PLANT/BUILD/PLACE tasks (holds crop name or animal/structure type)
    worker_id: Optional[int] = None

    def __lt__(self, other: "Task") -> bool:
        return self.priority > other.priority


def effective_distance(worker: WorkerState, task: Task) -> int:
    """Computes realistic travel distance considering required shed trips."""
    if task.task_type == "PLACE_ANIMAL":
        animal = task.crop
        if worker.inventory.get(animal, 0) > 0:
            return manhattan_distance(worker.pos, task.target_pos)
        return manhattan_distance(worker.pos, SHED_POS) + manhattan_distance(SHED_POS, task.target_pos)
    elif task.task_type == "FEED":
        if worker.inventory.get("WHEAT", 0) > 0:
            return manhattan_distance(worker.pos, task.target_pos)
        return manhattan_distance(worker.pos, SHED_POS) + manhattan_distance(SHED_POS, task.target_pos)
    elif task.task_type == "DROP_OFF":
        return manhattan_distance(worker.pos, SHED_POS)
    return manhattan_distance(worker.pos, task.target_pos)


def generate_tasks(world: WorldState, default_crop: str = "MELON") -> List[Task]:
    """
    Generates all active tasks needed on the farm this turn.
    """
    tasks: List[Task] = []
    farm = world.my_farm
    private = world.private

    # 1. DROP_OFF tasks for workers carrying produce
    for worker in farm.all_workers:
        if any(worker.inventory.get(p, 0) > 0 for p in PRODUCE_ITEMS):
            tasks.append(Task(
                task_type="DROP_OFF",
                target_pos=SHED_POS,
                priority=TASK_PRIORITIES["DROP_OFF"],
                worker_id=worker.worker_id,
            ))

    # 2. COLLECT_FERTILIZER — free from every animal daily
    for tile in farm.structure_tiles:
        if tile.animal is not None and tile.fertilizer_available:
            tasks.append(Task(
                task_type="COLLECT_FERTILIZER",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["COLLECT_FERTILIZER"],
            ))

    # 3. FEED, CARE tasks for animals
    total_wheat = private.shed.get("WHEAT", 0) + sum(w.inventory.get("WHEAT", 0) for w in farm.all_workers)
    for tile in farm.structure_tiles:
        if tile.ready_to_harvest:
            tasks.append(Task(
                task_type="HARVEST_ANIMAL",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["HARVEST_ANIMAL"],
            ))
        if tile.needs_feed and total_wheat > 0:
            tasks.append(Task(
                task_type="FEED",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["FEED"],
            ))
            total_wheat -= 1
        elif tile.animal is not None and tile.fed_today and not tile.cared_today:
            tasks.append(Task(
                task_type="CARE",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["CARE"],
            ))

    # 4. WATER tasks for all unwatered crops
    for tile in farm.unwatered_crop_tiles:
        tasks.append(Task(
            task_type="WATER",
            target_pos=tile.pos,
            priority=TASK_PRIORITIES["WATER"],
        ))

    # 5. HARVEST tasks for mature crops
    for tile in farm.ready_to_harvest_tiles:
        tasks.append(Task(
            task_type="HARVEST",
            target_pos=tile.pos,
            priority=TASK_PRIORITIES["HARVEST"],
            crop=tile.crop,
        ))

    # 6. Unplaced animals -> PLACE_ANIMAL and BUILD_STRUCTURE

    # 6a. FERTILIZE tasks — apply fertilizer from shed to highest-value crop tiles
    fertilizer_in_shed = private.shed.get("FERTILIZER", 0) + sum(
        w.inventory.get("FERTILIZER", 0) for w in farm.all_workers
    )
    if fertilizer_in_shed > 0:
        # Prioritize ongoing crops (strawberry, tomato) and melon for fertilization
        FERTILIZE_PRIORITY = ["STRAWBERRY", "MELON", "TOMATO", "CARROT", "WHEAT"]
        fertilizable = [
            t for t in farm.plant_tiles
            if t.crop in FERTILIZE_PRIORITY and t.fertilized_until_day == -1
        ]
        fertilizable.sort(key=lambda t: FERTILIZE_PRIORITY.index(t.crop))
        for tile in fertilizable[:fertilizer_in_shed]:
            tasks.append(Task(
                task_type="FERTILIZE",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["FERTILIZE"],
            ))

    # 6b. Unplaced animals
    unplaced_animals: List[str] = []
    from animal_model import ANIMAL_TYPES
    for animal in ANIMAL_TYPES:
        count = private.shed.get(animal, 0) + sum(w.inventory.get(animal, 0) for w in farm.all_workers)
        for _ in range(count):
            unplaced_animals.append(animal)

    # Empty structures ready for placement
    available_animals = list(unplaced_animals)
    for tile in farm.empty_structures:
        if not available_animals:
            break
        chosen_animal = None
        for a in available_animals:
            if tile.structure_kind == ANIMAL_TYPES[a].structure:
                chosen_animal = a
                break
        if chosen_animal:
            available_animals.remove(chosen_animal)
            tasks.append(Task(
                task_type="PLACE_ANIMAL",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["PLACE_ANIMAL"],
                crop=chosen_animal,
            ))

    # Structure building if we have unplaced animals exceeding empty structures
    structs_needed = {}
    for a in unplaced_animals:
        s = ANIMAL_TYPES[a].structure
        structs_needed[s] = structs_needed.get(s, 0) + 1
        
    empty_structs = {}
    for t in farm.empty_structures:
        empty_structs[t.structure_kind] = empty_structs.get(t.structure_kind, 0) + 1
        
    for s_needed in structs_needed:
        missing = max(0, structs_needed[s_needed] - empty_structs.get(s_needed, 0))
        structs_needed[s_needed] = missing
        
    if sum(structs_needed.values()) > 0:
        # Build structures at empty tiles furthest from shed (leave center for crops)
        sorted_empty_rev = sorted(
            farm.empty_tiles,
            key=lambda t: manhattan_distance(t.pos, SHED_POS),
            reverse=True,
        )
        for s_needed, count in structs_needed.items():
            for _ in range(count):
                if not sorted_empty_rev: break
                tile = sorted_empty_rev.pop()
                tasks.append(Task(
                    task_type="BUILD_STRUCTURE",
                    target_pos=tile.pos,
                    priority=TASK_PRIORITIES["BUILD_STRUCTURE"],
                    crop=s_needed,
                ))

    # 7. PLANT tasks for empty tiles if we have seeds
    seeds_available = dict(private.seeds)
    # Check default crop first, then any other crop seeds
    crop_to_plant = default_crop if seeds_available.get(default_crop, 0) > 0 else None
    if not crop_to_plant:
        for c, count in seeds_available.items():
            if count > 0:
                crop_to_plant = c
                break

    if crop_to_plant and seeds_available.get(crop_to_plant, 0) > 0:
        available_seeds = seeds_available[crop_to_plant]
        # Sort empty tiles by proximity to shed for tight farming clusters
        sorted_empty = sorted(
            [t for t in farm.empty_tiles if not any(tk.target_pos == t.pos for tk in tasks)],
            key=lambda t: manhattan_distance(t.pos, SHED_POS),
        )
        for tile in sorted_empty[:available_seeds]:
            tasks.append(Task(
                task_type="PLANT",
                target_pos=tile.pos,
                priority=TASK_PRIORITIES["PLANT"],
                crop=crop_to_plant,
            ))

    # 8. DIG weeds
    for tile in farm.weed_tiles:
        tasks.append(Task(
            task_type="DIG",
            target_pos=tile.pos,
            priority=TASK_PRIORITIES["DIG"],
        ))

    return tasks


def assign_tasks(
    workers: List[WorkerState],
    tasks: List[Task],
) -> Dict[int, Optional[Task]]:
    """
    Greedy assignment of tasks to workers considering realistic effective distance.
    """
    assignments: Dict[int, Optional[Task]] = {w.worker_id: None for w in workers}
    if not tasks:
        return assignments

    # Handle worker-pinned tasks (e.g. DROP_OFF) first
    unassigned_workers = list(workers)
    remaining_tasks: List[Task] = []
    for task in tasks:
        if task.worker_id is not None:
            w = next((wk for wk in unassigned_workers if wk.worker_id == task.worker_id), None)
            if w:
                assignments[w.worker_id] = task
                unassigned_workers.remove(w)
                continue
        remaining_tasks.append(task)

    remaining_tasks.sort(key=lambda t: t.priority, reverse=True)
    assigned_targets: Set[Tuple[int, int]] = {t.target_pos for t in assignments.values() if t is not None and t.task_type != "DROP_OFF"}

    for worker in unassigned_workers:
        best_task = None
        best_score = -999999
        best_idx = -1

        for idx, task in enumerate(remaining_tasks):
            if task.target_pos in assigned_targets and task.task_type != "DROP_OFF":
                continue

            dist = effective_distance(worker, task)
            score = (task.priority * 15) - dist

            if score > best_score:
                best_score = score
                best_task = task
                best_idx = idx

        if best_task is not None:
            assignments[worker.worker_id] = best_task
            if best_task.task_type != "DROP_OFF":
                assigned_targets.add(best_task.target_pos)
            remaining_tasks.pop(best_idx)

    return assignments


def execute_worker_task(worker: WorkerState, task: Optional[Task], world: WorldState) -> List[str]:
    """
    Translates a task assignment into an action for that worker:
    - Multi-step PLACE_ANIMAL: pickups from shed (4,4) before placing at structure
    - Multi-step FEED: pickups wheat from shed (4,4) before feeding at structure
    - DROP_OFF: drops harvested goods at shed (4,4)
    - Standard farming actions when at target
    """
    has_produce = any(worker.inventory.get(p, 0) > 0 for p in PRODUCE_ITEMS)

    # If no task assigned
    if task is None:
        if has_produce:
            if worker.pos == SHED_POS:
                return ae.drop_action()
            mv = next_move(worker.pos, SHED_POS)
            return ae.move_action(mv) if mv else ae.pass_worker_action()
        # Idle workers gather near shed
        if worker.pos != SHED_POS:
            mv = next_move(worker.pos, SHED_POS)
            if mv:
                return ae.move_action(mv)
        return ae.pass_worker_action()

    # Task: DROP_OFF
    if task.task_type == "DROP_OFF":
        if worker.pos == SHED_POS:
            return ae.drop_action()
        mv = next_move(worker.pos, SHED_POS)
        return ae.move_action(mv) if mv else ae.pass_worker_action()

    # Task: PLACE_ANIMAL
    if task.task_type == "PLACE_ANIMAL":
        animal = task.crop or "SHEEP"
        if worker.inventory.get(animal, 0) > 0:
            if worker.pos == task.target_pos:
                return ae.place_action(animal)
            mv = next_move(worker.pos, task.target_pos)
            return ae.move_action(mv) if mv else ae.pass_worker_action()
        else:
            # Must pick up from shed first
            if worker.pos == SHED_POS:
                return ae.pickup_action(animal, 1)
            mv = next_move(worker.pos, SHED_POS)
            return ae.move_action(mv) if mv else ae.pass_worker_action()

    # Task: FEED
    if task.task_type == "FEED":
        if worker.inventory.get("WHEAT", 0) > 0:
            if worker.pos == task.target_pos:
                return ae.feed_action()
            mv = next_move(worker.pos, task.target_pos)
            return ae.move_action(mv) if mv else ae.pass_worker_action()
        else:
            # Must pick up wheat from shed first
            if worker.pos == SHED_POS:
                shed_wheat = world.private.shed.get("WHEAT", 0)
                qty = min(3, max(1, shed_wheat))
                return ae.pickup_action("WHEAT", qty)
            mv = next_move(worker.pos, SHED_POS)
            return ae.move_action(mv) if mv else ae.pass_worker_action()

    # Task: COLLECT_FERTILIZER
    if task.task_type == "COLLECT_FERTILIZER":
        if worker.pos == task.target_pos:
            return ae.collect_fertilizer_action()
        mv = next_move(worker.pos, task.target_pos)
        return ae.move_action(mv) if mv else ae.pass_worker_action()

    # Task: FERTILIZE
    if task.task_type == "FERTILIZE":
        # Need fertilizer in hand first
        if worker.inventory.get("FERTILIZER", 0) > 0:
            if worker.pos == task.target_pos:
                return ae.fertilize_action()
            mv = next_move(worker.pos, task.target_pos)
            return ae.move_action(mv) if mv else ae.pass_worker_action()
        else:
            if worker.pos == SHED_POS:
                shed_fert = world.private.shed.get("FERTILIZER", 0)
                qty = min(3, max(1, shed_fert))
                return ae.pickup_action("FERTILIZER", qty)
            mv = next_move(worker.pos, SHED_POS)
            return ae.move_action(mv) if mv else ae.pass_worker_action()

    # Standard actions: must be on target tile
    if worker.pos == task.target_pos:
        if task.task_type == "WATER":
            return ae.water_action()
        elif task.task_type in ("HARVEST", "HARVEST_ANIMAL"):
            return ae.harvest_action()
        elif task.task_type == "CARE":
            return ae.care_action()
        elif task.task_type == "BUILD_STRUCTURE":
            struct_type = task.crop
            if struct_type == "COOP":
                return ae.build_coop_action()
            return ae.build_pasture_action()
        elif task.task_type == "PLANT":
            crop = task.crop or "MELON"
            return ae.plant_action(crop)
        elif task.task_type == "DIG":
            return ae.dig_action()

    # Move towards target tile
    mv = next_move(worker.pos, task.target_pos)
    if mv:
        return ae.move_action(mv)

    return ae.pass_worker_action()
