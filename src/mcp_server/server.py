"""Dyson-MCP: MCP server for Dyson Sphere Program factory optimization."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .data_sources.realtime_stream import RealTimeStream
from .data_sources.save_parser import SaveFileParser
from .tools.bottleneck_analyzer import BottleneckAnalyzer
from .tools.power_analyzer import PowerAnalyzer
from .tools.logistics_analyzer import LogisticsAnalyzer
from .models.factory_state import FactoryState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Dyson Sphere Program Optimizer")

# Initialize data sources
realtime_stream = RealTimeStream(host="localhost", port=8470)
save_parser = SaveFileParser()

# Initialize analyzers
bottleneck_analyzer = BottleneckAnalyzer()
power_analyzer = PowerAnalyzer()
logistics_analyzer = LogisticsAnalyzer()


async def _get_factory_state() -> FactoryState:
    """Helper to get factory state from best available source."""
    if realtime_stream.is_connected():
        logger.info("Using real-time game data")
        return await realtime_stream.get_current_state()
    else:
        logger.info("Using save file data (game not running)")
        return await save_parser.get_latest_state()


@mcp.tool()
async def analyze_production_bottlenecks(
    planet_id: Optional[int] = None,
    target_item: Optional[str] = None,
    time_window: int = 60,
    include_downstream: bool = True,
) -> Dict[str, Any]:
    """
    Identify production chain bottlenecks causing throughput limitations.

    Args:
        planet_id: Specific planet to analyze (None = all planets)
        target_item: Focus analysis on specific product (e.g., "green-circuit")
        time_window: Analysis window in seconds for real-time mode
        include_downstream: Trace impact to final products

    Returns:
        Bottleneck analysis with root causes and recommendations
    """
    logger.info(f"Analyzing bottlenecks: planet={planet_id}, item={target_item}")

    try:
        factory_state = await _get_factory_state()
        result = await bottleneck_analyzer.analyze(
            factory_state=factory_state,
            planet_id=planet_id,
            target_item=target_item,
            time_window=time_window,
            include_downstream=include_downstream,
        )
        return result
    except ConnectionError as e:
        logger.error(f"Game connection failed: {e}")
        return {
            "error": "game_not_running",
            "message": "Could not connect to game. Ensure DSP is running with DysonMCP plugin.",
            "fallback": "Try load_save_analysis with a save file path instead.",
        }
    except Exception as e:
        logger.exception("Unexpected error in bottleneck analysis")
        return {"error": "analysis_failed", "message": str(e)}


@mcp.tool()
async def analyze_power_grid(
    planet_id: Optional[int] = None,
    include_accumulator_cycles: bool = True,
) -> Dict[str, Any]:
    """
    Evaluate power generation, consumption, and distribution efficiency.

    Args:
        planet_id: Specific planet to analyze (None = all planets)
        include_accumulator_cycles: Include charge/discharge pattern analysis

    Returns:
        Power grid analysis with deficit warnings and recommendations
    """
    logger.info(f"Analyzing power grid: planet={planet_id}")

    try:
        factory_state = await _get_factory_state()
        result = await power_analyzer.analyze(
            factory_state=factory_state,
            planet_id=planet_id,
            include_accumulator_cycles=include_accumulator_cycles,
        )
        return result
    except Exception as e:
        logger.exception("Error in power analysis")
        return {"error": "analysis_failed", "message": str(e)}


@mcp.tool()
async def analyze_logistics_saturation(
    planet_id: Optional[int] = None,
    item_filter: Optional[List[str]] = None,
    saturation_threshold: float = 95.0,
) -> Dict[str, Any]:
    """
    Detect belt/logistics bottlenecks and flow inefficiencies.

    Args:
        planet_id: Specific planet to analyze
        item_filter: Only analyze belts carrying these items
        saturation_threshold: % of max throughput to flag (default 95%)

    Returns:
        Saturated belts and logistics station bottlenecks
    """
    logger.info(f"Analyzing logistics: planet={planet_id}, threshold={saturation_threshold}%")

    try:
        factory_state = await _get_factory_state()
        result = await logistics_analyzer.analyze(
            factory_state=factory_state,
            planet_id=planet_id,
            item_filter=item_filter,
            saturation_threshold=saturation_threshold,
        )
        return result
    except Exception as e:
        logger.exception("Error in logistics analysis")
        return {"error": "analysis_failed", "message": str(e)}


@mcp.tool()
async def get_factory_snapshot(
    planet_id: Optional[int] = None,
    item_filter: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Retrieve current production state for all items.

    Args:
        planet_id: Specific planet (None = all planets)
        item_filter: Only return data for these items

    Returns:
        Production, consumption, and storage for each item
    """
    logger.info(f"Getting factory snapshot: planet={planet_id}")

    try:
        factory_state = await _get_factory_state()

        # Filter and format data
        snapshot: Dict[str, Any] = {
            "timestamp": factory_state.timestamp.isoformat(),
            "planets": {},
        }

        for pid, planet in factory_state.planets.items():
            if planet_id is None or pid == planet_id:
                planet_data: Dict[str, Any] = {
                    "planet_name": planet.planet_name,
                    "items": [],
                }

                for item_name, metrics in planet.production.items():
                    if item_filter is None or item_name in item_filter:
                        planet_data["items"].append({
                            "name": item_name,
                            "production": metrics.production_rate,
                            "consumption": metrics.consumption_rate,
                            "net": metrics.net_rate,
                            "storage": metrics.current_storage,
                        })

                if planet.power:
                    planet_data["power"] = {
                        "generation_mw": planet.power.generation_mw,
                        "consumption_mw": planet.power.consumption_mw,
                        "surplus_mw": planet.power.surplus_mw,
                    }

                snapshot["planets"][pid] = planet_data

        return snapshot
    except Exception as e:
        logger.exception("Error getting factory snapshot")
        return {"error": "snapshot_failed", "message": str(e)}


@mcp.tool()
async def load_save_analysis(
    save_file_path: str,
    analysis_type: str = "full",
) -> Dict[str, Any]:
    """
    Parse .dsv save file and extract factory state for offline analysis.

    Args:
        save_file_path: Path to .dsv save file
        analysis_type: Type of analysis (production|power|logistics|full)

    Returns:
        Comprehensive save state or focused analysis
    """
    logger.info(f"Loading save file: {save_file_path}, type={analysis_type}")

    try:
        factory_state = await save_parser.parse_file(save_file_path)

        if analysis_type == "production":
            return await bottleneck_analyzer.analyze(factory_state)
        elif analysis_type == "power":
            return await power_analyzer.analyze(factory_state)
        elif analysis_type == "logistics":
            return await logistics_analyzer.analyze(factory_state)
        else:  # full
            return {
                "production": await bottleneck_analyzer.analyze(factory_state),
                "power": await power_analyzer.analyze(factory_state),
                "logistics": await logistics_analyzer.analyze(factory_state),
            }
    except FileNotFoundError as e:
        return {"error": "file_not_found", "message": str(e)}
    except Exception as e:
        logger.exception("Error loading save file")
        return {"error": "parse_failed", "message": str(e)}


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
