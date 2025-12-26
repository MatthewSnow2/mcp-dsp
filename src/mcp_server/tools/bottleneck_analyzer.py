"""Production bottleneck detection and analysis."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..models.factory_state import FactoryState

logger = logging.getLogger(__name__)


@dataclass
class Bottleneck:
    """Represents a detected production bottleneck."""

    item_name: str
    bottleneck_type: str  # "input_starvation", "output_blocked", "power_limited"
    severity: float  # 0-100, higher = more severe
    affected_throughput: float  # items/min lost
    root_cause: str
    recommendation: str


class BottleneckAnalyzer:
    """Analyze factory state to identify production bottlenecks."""

    async def analyze(
        self,
        factory_state: FactoryState,
        planet_id: Optional[int] = None,
        target_item: Optional[str] = None,
        time_window: int = 60,
        include_downstream: bool = True,
    ) -> Dict[str, Any]:
        """
        Identify production chain bottlenecks.

        Args:
            factory_state: Current factory state
            planet_id: Specific planet to analyze (None = all)
            target_item: Focus on specific product
            time_window: Analysis window in seconds
            include_downstream: Trace impact to final products

        Returns:
            Analysis results with bottlenecks and recommendations
        """
        logger.info(f"Analyzing bottlenecks: planet={planet_id}, item={target_item}")

        bottlenecks: List[Bottleneck] = []
        planets_analyzed = 0

        for pid, planet in factory_state.planets.items():
            if planet_id is not None and pid != planet_id:
                continue

            planets_analyzed += 1

            # Analyze each assembler for bottleneck indicators
            for assembler in planet.assemblers:
                if assembler.efficiency < 90:  # Less than 90% efficiency
                    bottleneck = self._analyze_assembler(assembler, planet, target_item)
                    if bottleneck:
                        bottlenecks.append(bottleneck)

        # Sort by severity
        bottlenecks.sort(key=lambda b: b.severity, reverse=True)

        return {
            "timestamp": factory_state.timestamp.isoformat(),
            "planets_analyzed": planets_analyzed,
            "bottlenecks_found": len(bottlenecks),
            "bottlenecks": [
                {
                    "item": b.item_name,
                    "type": b.bottleneck_type,
                    "severity": b.severity,
                    "throughput_loss": b.affected_throughput,
                    "root_cause": b.root_cause,
                    "recommendation": b.recommendation,
                }
                for b in bottlenecks[:10]  # Top 10 bottlenecks
            ],
            "critical_path": self._build_critical_path(bottlenecks) if include_downstream else [],
        }

    def _analyze_assembler(
        self,
        assembler: Any,
        planet: Any,
        target_item: Optional[str],
    ) -> Optional[Bottleneck]:
        """Analyze a single assembler for bottleneck conditions."""
        # TODO: Implement detailed analysis
        # This is a placeholder for the full algorithm

        if assembler.input_starved:
            return Bottleneck(
                item_name="unknown",  # TODO: Get from recipe database
                bottleneck_type="input_starvation",
                severity=100 - assembler.efficiency,
                affected_throughput=assembler.theoretical_max - assembler.production_rate,
                root_cause="Insufficient input materials",
                recommendation="Increase upstream production or add more input belts",
            )

        if assembler.output_blocked:
            return Bottleneck(
                item_name="unknown",
                bottleneck_type="output_blocked",
                severity=100 - assembler.efficiency,
                affected_throughput=assembler.theoretical_max - assembler.production_rate,
                root_cause="Output buffer full, downstream consumption insufficient",
                recommendation="Add more output belts or increase downstream consumption",
            )

        return None

    def _build_critical_path(self, bottlenecks: List[Bottleneck]) -> List[str]:
        """Build critical path through dependency graph."""
        # TODO: Implement dependency graph traversal
        return [b.item_name for b in bottlenecks[:5]]
