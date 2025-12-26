"""Logistics and belt saturation analysis."""

import logging
from typing import Any, Dict, List, Optional

from ..models.factory_state import FactoryState

logger = logging.getLogger(__name__)


# Belt tier maximum throughput (items/sec)
BELT_TIERS = {
    "mk1": 6,   # Blue belt: 6/sec = 360/min
    "mk2": 12,  # Green belt: 12/sec = 720/min
    "mk3": 30,  # Yellow belt: 30/sec = 1800/min
}


class LogisticsAnalyzer:
    """Analyze belt and logistics station efficiency."""

    async def analyze(
        self,
        factory_state: FactoryState,
        planet_id: Optional[int] = None,
        item_filter: Optional[List[str]] = None,
        saturation_threshold: float = 95.0,
    ) -> Dict[str, Any]:
        """
        Detect belt and logistics bottlenecks.

        Args:
            factory_state: Current factory state
            planet_id: Specific planet to analyze (None = all)
            item_filter: Only analyze belts carrying these items
            saturation_threshold: % of max throughput to flag

        Returns:
            Saturated belts and logistics issues
        """
        logger.info(f"Analyzing logistics: threshold={saturation_threshold}%")

        saturated_belts: List[Dict[str, Any]] = []
        near_saturation: List[Dict[str, Any]] = []

        for pid, planet in factory_state.planets.items():
            if planet_id is not None and pid != planet_id:
                continue

            for belt in planet.belts:
                # Apply item filter if specified
                if item_filter and belt.item_type not in item_filter:
                    continue

                belt_data = {
                    "planet_id": pid,
                    "belt_id": belt.belt_id,
                    "item": belt.item_type,
                    "throughput": round(belt.throughput, 2),
                    "max_throughput": belt.max_throughput,
                    "saturation": round(belt.saturation_percent, 1),
                }

                if belt.saturation_percent >= saturation_threshold:
                    belt_data["status"] = "saturated"
                    belt_data["recommendation"] = self._upgrade_recommendation(belt)
                    saturated_belts.append(belt_data)
                elif belt.saturation_percent >= saturation_threshold - 10:
                    belt_data["status"] = "near_saturation"
                    near_saturation.append(belt_data)

        # Sort by saturation level
        saturated_belts.sort(key=lambda b: b["saturation"], reverse=True)
        near_saturation.sort(key=lambda b: b["saturation"], reverse=True)

        return {
            "timestamp": factory_state.timestamp.isoformat(),
            "threshold": saturation_threshold,
            "summary": {
                "saturated_count": len(saturated_belts),
                "near_saturation_count": len(near_saturation),
            },
            "saturated_belts": saturated_belts[:20],  # Top 20
            "near_saturation": near_saturation[:10],  # Top 10
            "recommendations": self._global_recommendations(saturated_belts),
        }

    def _upgrade_recommendation(self, belt: Any) -> str:
        """Generate upgrade recommendation for a belt."""
        current_tier = self._detect_tier(belt.max_throughput)

        if current_tier == "mk1":
            return "Upgrade to Mk2 (green) belt for 2x throughput"
        elif current_tier == "mk2":
            return "Upgrade to Mk3 (yellow) belt for 2.5x throughput"
        else:
            return "At max tier - consider parallel belt lines"

    def _detect_tier(self, max_throughput: float) -> str:
        """Detect belt tier from max throughput."""
        if max_throughput <= 6:
            return "mk1"
        elif max_throughput <= 12:
            return "mk2"
        else:
            return "mk3"

    def _global_recommendations(
        self, saturated_belts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate global logistics recommendations."""
        recommendations: List[str] = []

        if len(saturated_belts) == 0:
            recommendations.append("No saturated belts detected - logistics healthy")
        elif len(saturated_belts) < 5:
            recommendations.append(
                f"{len(saturated_belts)} saturated belts - targeted upgrades recommended"
            )
        else:
            recommendations.append(
                f"{len(saturated_belts)} saturated belts - consider systematic belt upgrade"
            )

            # Find most common saturated item
            item_counts: Dict[str, int] = {}
            for belt in saturated_belts:
                item = belt["item"]
                item_counts[item] = item_counts.get(item, 0) + 1

            if item_counts:
                worst_item = max(item_counts, key=item_counts.get)  # type: ignore
                recommendations.append(
                    f"Most congested item: {worst_item} ({item_counts[worst_item]} belts)"
                )

        return recommendations
