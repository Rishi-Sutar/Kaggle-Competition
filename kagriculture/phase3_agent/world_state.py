"""
WorldState Parser for Kaggriculture.
Parses raw Kaggle observation dictionary into structured, typed dataclasses
with convenient query helpers for agents.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

@dataclass
class TileState:
    x: int  # col
    y: int  # row
    is_locked: bool = False
    is_empty: bool = False
    is_weed: bool = False
    is_plant: bool = False
    is_structure: bool = False
    
    # Plant attributes
    crop: Optional[str] = None
    planted_day: int = -1
    watered_today: bool = False
    consecutive_unwatered: int = 0
    yield_units: int = 0
    max_lifespan_step: int = -1
    fertilized_until_day: int = -1
    
    # Animal structure attributes
    structure_kind: Optional[str] = None  # 'COOP' or 'PASTURE'
    animal: Optional[str] = None          # 'GOOSE', 'COW', 'SHEEP'
    placed_day: int = -1
    fed_today: bool = False
    consecutive_unfed: int = 0
    cared_today: bool = False
    fertilizer_available: bool = False
    pending_care_bonus: int = 0
    
    @property
    def pos(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    @property
    def ready_to_harvest(self) -> bool:
        return self.yield_units > 0
    
    @property
    def needs_water(self) -> bool:
        return self.is_plant and not self.watered_today
    
    @property
    def needs_feed(self) -> bool:
        return self.is_structure and self.animal is not None and not self.fed_today


@dataclass
class WorkerState:
    worker_id: int  # 0 = farmer, 1..N = hands
    x: int
    y: int
    inventory: Dict[str, int] = field(default_factory=dict)
    
    @property
    def pos(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    @property
    def is_farmer(self) -> bool:
        return self.worker_id == 0


@dataclass
class FarmState:
    money: float
    farmer: WorkerState
    hands: List[WorkerState] = field(default_factory=list)
    unlocked_quadrants: List[str] = field(default_factory=list)
    hires_today: int = 0
    grid: List[List[TileState]] = field(default_factory=list)  # grid[y][x]
    
    # Precomputed derived lists for fast agent decisions
    empty_tiles: List[TileState] = field(default_factory=list)
    plant_tiles: List[TileState] = field(default_factory=list)
    ready_to_harvest_tiles: List[TileState] = field(default_factory=list)
    unwatered_crop_tiles: List[TileState] = field(default_factory=list)
    weed_tiles: List[TileState] = field(default_factory=list)
    structure_tiles: List[TileState] = field(default_factory=list)
    empty_structures: List[TileState] = field(default_factory=list)
    unfed_animal_tiles: List[TileState] = field(default_factory=list)

    def get_tile(self, x: int, y: int) -> Optional[TileState]:
        if 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]):
            return self.grid[y][x]
        return None

    @property
    def all_workers(self) -> List[WorkerState]:
        return [self.farmer] + self.hands


@dataclass
class MarketState:
    inventory: Dict[str, int] = field(default_factory=dict)
    prices: Dict[str, int] = field(default_factory=dict)
    
    def price_of(self, item: str) -> int:
        return self.prices.get(item, 0)
    
    def inventory_of(self, item: str) -> int:
        return self.inventory.get(item, 0)


@dataclass
class PrivateState:
    shed: Dict[str, int] = field(default_factory=dict)
    seeds: Dict[str, int] = field(default_factory=dict)
    inventories: List[Dict[str, int]] = field(default_factory=list)
    
    @property
    def total_seeds(self) -> int:
        return sum(self.seeds.values())
    
    @property
    def shed_occupied(self) -> int:
        # Non-seed capacity is 100
        return sum(self.shed.values())


@dataclass
class TownState:
    unlocked_shops: List[str] = field(default_factory=list)


@dataclass
class WorldState:
    player_id: int
    opponent_id: int
    day: int
    hour: int
    step: int
    my_farm: FarmState
    opp_farm: FarmState
    market: MarketState
    private: PrivateState
    town: TownState

    @property
    def is_morning(self) -> bool:
        return self.hour == 0

    @property
    def is_end_of_day(self) -> bool:
        return self.hour == 23


def parse_tile(x: int, y: int, raw_tile: Any) -> TileState:
    tile = TileState(x=x, y=y)
    
    if raw_tile == "LOCKED":
        tile.is_locked = True
        return tile
    
    if raw_tile is None:
        tile.is_empty = True
        return tile
        
    if isinstance(raw_tile, dict):
        kind = raw_tile.get("kind")
        if kind == "WEED":
            tile.is_weed = True
        elif kind == "PLANT":
            tile.is_plant = True
            tile.crop = raw_tile.get("crop")
            tile.planted_day = raw_tile.get("planted_day", -1)
            tile.watered_today = raw_tile.get("watered_today", False)
            tile.consecutive_unwatered = raw_tile.get("consecutive_unwatered", 0)
            tile.yield_units = raw_tile.get("yield_units", 0)
            tile.max_lifespan_step = raw_tile.get("max_lifespan_step", -1)
            tile.fertilized_until_day = raw_tile.get("fertilized_until_day", -1)
        elif kind in ("COOP", "PASTURE"):
            tile.is_structure = True
            tile.structure_kind = kind
            tile.animal = raw_tile.get("animal")
            tile.placed_day = raw_tile.get("placed_day", -1)
            tile.yield_units = raw_tile.get("yield_units", 0)
            tile.fed_today = raw_tile.get("fed_today", False)
            tile.consecutive_unfed = raw_tile.get("consecutive_unfed", 0)
            tile.cared_today = raw_tile.get("cared_today", False)
            tile.fertilizer_available = raw_tile.get("fertilizer_available", False)
            tile.pending_care_bonus = raw_tile.get("pending_care_bonus", 0)
            
    return tile


def parse_farm(raw_farm: Dict[str, Any], raw_inventories: List[Dict[str, int]]) -> FarmState:
    fx, fy = raw_farm["farmer"]
    farmer_inv = raw_inventories[0] if raw_inventories else {}
    farmer = WorkerState(worker_id=0, x=fx, y=fy, inventory=farmer_inv)
    
    hands: List[WorkerState] = []
    raw_hands = raw_farm.get("hands", [])
    for idx, (hx, hy) in enumerate(raw_hands, start=1):
        hand_inv = raw_inventories[idx] if idx < len(raw_inventories) else {}
        hands.append(WorkerState(worker_id=idx, x=hx, y=hy, inventory=hand_inv))
        
    tiles_grid: List[List[TileState]] = []
    empty_tiles: List[TileState] = []
    plant_tiles: List[TileState] = []
    ready_to_harvest_tiles: List[TileState] = []
    unwatered_crop_tiles: List[TileState] = []
    weed_tiles: List[TileState] = []
    structure_tiles: List[TileState] = []
    empty_structures: List[TileState] = []
    unfed_animal_tiles: List[TileState] = []
    
    raw_tiles = raw_farm.get("tiles", [])
    for y, row in enumerate(raw_tiles):
        row_tiles: List[TileState] = []
        for x, raw_cell in enumerate(row):
            t = parse_tile(x, y, raw_cell)
            row_tiles.append(t)
            
            if t.is_empty:
                empty_tiles.append(t)
            elif t.is_weed:
                weed_tiles.append(t)
            elif t.is_plant:
                plant_tiles.append(t)
                if t.ready_to_harvest:
                    ready_to_harvest_tiles.append(t)
                if t.needs_water:
                    unwatered_crop_tiles.append(t)
            elif t.is_structure:
                structure_tiles.append(t)
                if t.animal is None:
                    empty_structures.append(t)
                elif t.ready_to_harvest:
                    ready_to_harvest_tiles.append(t)
                if t.needs_feed:
                    unfed_animal_tiles.append(t)
                    
        tiles_grid.append(row_tiles)
        
    return FarmState(
        money=float(raw_farm.get("money", 0.0)),
        farmer=farmer,
        hands=hands,
        unlocked_quadrants=list(raw_farm.get("unlocked_quadrants", [])),
        hires_today=int(raw_farm.get("hires_today", 0)),
        grid=tiles_grid,
        empty_tiles=empty_tiles,
        plant_tiles=plant_tiles,
        ready_to_harvest_tiles=ready_to_harvest_tiles,
        unwatered_crop_tiles=unwatered_crop_tiles,
        weed_tiles=weed_tiles,
        structure_tiles=structure_tiles,
        empty_structures=empty_structures,
        unfed_animal_tiles=unfed_animal_tiles,
    )


def parse_observation(obs: Dict[str, Any]) -> WorldState:
    """
    Main entry point: convert raw kaggle observation dictionary to WorldState.
    """
    player_id = obs["player"]
    opp_id = 1 - player_id
    
    step = obs.get("step", 0)
    day = obs.get("day", step // 24)
    hour = obs.get("hour", step % 24)
    
    private_raw = obs.get("private", {})
    inventories_raw = private_raw.get("inventories", [])
    
    my_raw_farm = obs["farms"][player_id]
    opp_raw_farm = obs["farms"][opp_id]
    
    my_farm = parse_farm(my_raw_farm, inventories_raw)
    # Opponent private inventories are hidden, pass empty list
    opp_farm = parse_farm(opp_raw_farm, [])
    
    market_raw = obs.get("market", {})
    market = MarketState(
        inventory=dict(market_raw.get("inventory", {})),
        prices=dict(market_raw.get("prices", {})),
    )
    
    private = PrivateState(
        shed=dict(private_raw.get("shed", {})),
        seeds=dict(private_raw.get("seeds", {})),
        inventories=list(inventories_raw),
    )
    
    town_raw = obs.get("town", {})
    town = TownState(
        unlocked_shops=list(town_raw.get("unlocked_shops", [])),
    )
    
    return WorldState(
        player_id=player_id,
        opponent_id=opp_id,
        day=day,
        hour=hour,
        step=step,
        my_farm=my_farm,
        opp_farm=opp_farm,
        market=market,
        private=private,
        town=town,
    )
