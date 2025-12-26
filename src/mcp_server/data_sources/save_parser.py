"""Parse DSP .dsv save files for offline analysis."""

import logging
from pathlib import Path
from typing import Optional

from ..models.factory_state import FactoryState

logger = logging.getLogger(__name__)


class SaveFileParser:
    """Parse DSP .dsv save files for offline analysis."""

    def __init__(self, auto_detect_path: bool = True) -> None:
        self.save_dir: Optional[Path] = None
        if auto_detect_path:
            self._detect_save_directory()

    def _detect_save_directory(self) -> None:
        """Auto-detect DSP save directory."""
        # Windows: %USERPROFILE%\Documents\Dyson Sphere Program\Save
        # Linux: ~/.config/unity3d/Youthcat Studio/Dyson Sphere Program/Save
        windows_path = Path.home() / "Documents" / "Dyson Sphere Program" / "Save"
        linux_path = (
            Path.home()
            / ".config"
            / "unity3d"
            / "Youthcat Studio"
            / "Dyson Sphere Program"
            / "Save"
        )

        if windows_path.exists():
            self.save_dir = windows_path
            logger.info(f"Found save directory: {windows_path}")
        elif linux_path.exists():
            self.save_dir = linux_path
            logger.info(f"Found save directory: {linux_path}")
        else:
            logger.warning("DSP save directory not found")

    async def parse_file(self, file_path: str) -> FactoryState:
        """Parse specific .dsv save file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Save file not found: {file_path}")

        if not path.suffix.lower() == ".dsv":
            raise ValueError(f"Invalid file type: {path.suffix} (expected .dsv)")

        try:
            # TODO: Integration with qhgz2013/dsp_save_parser
            # from dsp_save_parser import parse
            # save_data = parse(file_path)
            # return FactoryState.from_save_data(save_data)

            logger.warning("Save parser not yet implemented - returning empty state")
            return FactoryState.from_save_data({})
        except Exception as e:
            logger.error(f"Failed to parse save file: {e}")
            raise

    async def get_latest_state(self) -> FactoryState:
        """Parse most recent save file in save directory."""
        if not self.save_dir or not self.save_dir.exists():
            raise FileNotFoundError("DSP save directory not found")

        # Find most recent .dsv file
        save_files = list(self.save_dir.glob("*.dsv"))
        if not save_files:
            raise FileNotFoundError("No save files found")

        latest_save = max(save_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Loading latest save: {latest_save.name}")
        return await self.parse_file(str(latest_save))
