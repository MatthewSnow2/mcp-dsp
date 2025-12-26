"""Data models for factory state representation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ItemMetrics:
    """Production metrics for a specific item."""

    item_name: str
    production_rate: float  # items/min
    consumption_rate: float  # items/min
    current_storage: int
    net_rate: float = field(init=False)

    def __post_init__(self) -> None:
        self.net_rate = self.production_rate - self.consumption_rate


@dataclass
class AssemblerMetrics:
    """Metrics for individual assembler/smelter."""

    assembler_id: int
    recipe_id: int
    production_rate: float
    theoretical_max: float
    input_starved: bool = False
    output_blocked: bool = False
    efficiency: float = field(init=False)

    def __post_init__(self) -> None:
        self.efficiency = (
            (self.production_rate / self.theoretical_max * 100)
            if self.theoretical_max > 0
            else 0
        )


@dataclass
class PowerMetrics:
    """Power grid metrics for a planet."""

    generation_mw: float
    consumption_mw: float
    accumulator_charge_percent: float = 0.0
    surplus_mw: float = field(init=False)

    def __post_init__(self) -> None:
        self.surplus_mw = self.generation_mw - self.consumption_mw


@dataclass
class BeltMetrics:
    """Belt throughput metrics."""

    belt_id: int
    item_type: str
    throughput: float  # items/sec
    max_throughput: float  # items/sec (based on tier)
    saturation_percent: float = field(init=False)

    def __post_init__(self) -> None:
        self.saturation_percent = (
            (self.throughput / self.max_throughput * 100) if self.max_throughput > 0 else 0
        )


@dataclass
class PlanetState:
    """Complete state for a single planet."""

    planet_id: int
    planet_name: str = ""
    production: Dict[str, ItemMetrics] = field(default_factory=dict)
    assemblers: List[AssemblerMetrics] = field(default_factory=list)
    power: Optional[PowerMetrics] = None
    belts: List[BeltMetrics] = field(default_factory=list)


@dataclass
class FactoryState:
    """Complete factory state across all planets."""

    timestamp: datetime
    planets: Dict[int, PlanetState] = field(default_factory=dict)

    @classmethod
    def from_realtime_data(cls, data: dict) -> "FactoryState":
        """Construct FactoryState from real-time plugin data."""
        planets: Dict[int, PlanetState] = {}

        for planet_id_str, planet_data in data.get("Planets", {}).items():
            planet_id = int(planet_id_str)
            planet_state = PlanetState(planet_id=planet_id)

            # Parse power metrics
            if "Power" in planet_data:
                power_data = planet_data["Power"]
                planet_state.power = PowerMetrics(
                    generation_mw=power_data.get("GenerationMW", 0),
                    consumption_mw=power_data.get("ConsumptionMW", 0),
                    accumulator_charge_percent=power_data.get("AccumulatorPercent", 0),
                )

            # Parse production metrics
            for prod in planet_data.get("Production", []):
                item_name = prod.get("ItemName", "unknown")
                planet_state.production[item_name] = ItemMetrics(
                    item_name=item_name,
                    production_rate=prod.get("ProductionRate", 0),
                    consumption_rate=prod.get("ConsumptionRate", 0),
                    current_storage=prod.get("Storage", 0),
                )

            planets[planet_id] = planet_state

        return cls(
            timestamp=datetime.fromtimestamp(data.get("Timestamp", 0)),
            planets=planets,
        )

    @classmethod
    def from_save_data(cls, save_data: dict) -> "FactoryState":
        """Construct FactoryState from parsed save file."""
        # TODO: Transform qhgz2013 parser output to FactoryState
        # This will be implemented in Phase 1A
        return cls(timestamp=datetime.now(), planets={})
