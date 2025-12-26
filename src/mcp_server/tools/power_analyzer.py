"""Power grid analysis and optimization."""

import logging
from typing import Any, Dict, List, Optional

from ..models.factory_state import FactoryState

logger = logging.getLogger(__name__)


class PowerAnalyzer:
    """Analyze power grid efficiency and identify issues."""

    async def analyze(
        self,
        factory_state: FactoryState,
        planet_id: Optional[int] = None,
        include_accumulator_cycles: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluate power generation, consumption, and distribution.

        Args:
            factory_state: Current factory state
            planet_id: Specific planet to analyze (None = all)
            include_accumulator_cycles: Include charge/discharge analysis

        Returns:
            Power grid analysis with recommendations
        """
        logger.info(f"Analyzing power grid: planet={planet_id}")

        planets_data: List[Dict[str, Any]] = []
        total_generation = 0.0
        total_consumption = 0.0
        deficits_found = 0

        for pid, planet in factory_state.planets.items():
            if planet_id is not None and pid != planet_id:
                continue

            if planet.power is None:
                continue

            power = planet.power
            total_generation += power.generation_mw
            total_consumption += power.consumption_mw

            planet_data: Dict[str, Any] = {
                "planet_id": pid,
                "planet_name": planet.planet_name,
                "generation_mw": round(power.generation_mw, 2),
                "consumption_mw": round(power.consumption_mw, 2),
                "surplus_mw": round(power.surplus_mw, 2),
                "status": "surplus" if power.surplus_mw >= 0 else "deficit",
            }

            if power.surplus_mw < 0:
                deficits_found += 1
                planet_data["recommendation"] = self._generate_recommendation(power)

            if include_accumulator_cycles:
                planet_data["accumulator_charge"] = f"{power.accumulator_charge_percent:.1f}%"

            planets_data.append(planet_data)

        return {
            "timestamp": factory_state.timestamp.isoformat(),
            "summary": {
                "total_generation_mw": round(total_generation, 2),
                "total_consumption_mw": round(total_consumption, 2),
                "net_surplus_mw": round(total_generation - total_consumption, 2),
                "planets_with_deficit": deficits_found,
            },
            "planets": planets_data,
            "recommendations": self._global_recommendations(total_generation, total_consumption),
        }

    def _generate_recommendation(self, power: Any) -> str:
        """Generate power recommendation for a planet."""
        deficit = abs(power.surplus_mw)

        if deficit < 10:
            return f"Minor deficit of {deficit:.1f}MW - add 1 thermal plant"
        elif deficit < 50:
            plants_needed = int(deficit / 15) + 1  # Assuming ~15MW per fusion
            return f"Deficit of {deficit:.1f}MW - add {plants_needed} fusion plants"
        else:
            return f"Major deficit of {deficit:.1f}MW - consider artificial sun or ray receivers"

    def _global_recommendations(
        self, generation: float, consumption: float
    ) -> List[str]:
        """Generate global power recommendations."""
        recommendations: List[str] = []
        surplus = generation - consumption
        surplus_percent = (surplus / consumption * 100) if consumption > 0 else 100

        if surplus < 0:
            recommendations.append(
                f"CRITICAL: Global power deficit of {abs(surplus):.1f}MW"
            )
        elif surplus_percent < 10:
            recommendations.append(
                f"WARNING: Power surplus below 10% ({surplus_percent:.1f}%)"
            )
            recommendations.append("Consider adding generation capacity before expanding")
        elif surplus_percent > 50:
            recommendations.append(
                f"Healthy power surplus of {surplus_percent:.1f}%"
            )

        return recommendations
