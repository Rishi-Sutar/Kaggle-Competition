"""
Pathfinding and grid utilities for Kaggriculture.
Grid coordinates: x = col (0..9), y = row (0..9).
Moves:
  NORTH: y - 1
  SOUTH: y + 1
  WEST:  x - 1
  EAST:  x + 1
"""
from collections import deque
from typing import List, Optional, Set, Tuple

# Direction mappings: op -> (dx, dy)
DIRECTIONS = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "WEST": (-1, 0),
    "EAST": (1, 0),
}

DELTA_TO_DIR = {
    (0, -1): "NORTH",
    (0, 1): "SOUTH",
    (-1, 0): "WEST",
    (1, 0): "EAST",
}


def manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    """Computes Manhattan distance between (x1, y1) and (x2, y2)."""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def is_valid_coord(x: int, y: int, width: int = 10, height: int = 10) -> bool:
    return 0 <= x < width and 0 <= y < height


def next_move(current_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> Optional[str]:
    """
    Direct greedy single-step direction towards target_pos.
    Prioritizes the axis with larger distance.
    Returns 'NORTH', 'SOUTH', 'EAST', 'WEST', or None if already at target.
    """
    cx, cy = current_pos
    tx, ty = target_pos
    dx = tx - cx
    dy = ty - cy
    
    if dx == 0 and dy == 0:
        return None
        
    # Pick the axis with larger delta, breaking ties by x
    if abs(dx) >= abs(dy) and dx != 0:
        return "EAST" if dx > 0 else "WEST"
    elif dy != 0:
        return "SOUTH" if dy > 0 else "NORTH"
    elif dx != 0:
        return "EAST" if dx > 0 else "WEST"
        
    return None


def bfs_path(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    width: int = 10,
    height: int = 10,
    blocked: Optional[Set[Tuple[int, int]]] = None
) -> List[Tuple[int, int]]:
    """
    Finds shortest path from start to goal using BFS.
    Returns list of positions [start, p1, p2, ..., goal].
    If start == goal, returns [start].
    If no path exists, returns [].
    """
    if start == goal:
        return [start]
        
    blocked_set = blocked or set()
    queue = deque([start])
    came_from = {start: None}
    
    while queue:
        curr = queue.popleft()
        if curr == goal:
            break
            
        cx, cy = curr
        for dname, (dx, dy) in DIRECTIONS.items():
            nx, ny = cx + dx, cy + dy
            neighbor = (nx, ny)
            if is_valid_coord(nx, ny, width, height) and neighbor not in came_from:
                if neighbor not in blocked_set or neighbor == goal:
                    came_from[neighbor] = curr
                    queue.append(neighbor)
                    
    if goal not in came_from:
        return []
        
    # Reconstruct path
    curr = goal
    path = []
    while curr is not None:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    return path


def path_to_directions(path: List[Tuple[int, int]]) -> List[str]:
    """Converts a sequence of coordinate steps into direction strings."""
    dirs = []
    for i in range(len(path) - 1):
        c1 = path[i]
        c2 = path[i + 1]
        delta = (c2[0] - c1[0], c2[1] - c1[1])
        if delta in DELTA_TO_DIR:
            dirs.append(DELTA_TO_DIR[delta])
    return dirs
