"""WebSocket client for real-time game data streaming."""

import asyncio
import json
import logging
from typing import Optional

from ..models.factory_state import FactoryState

logger = logging.getLogger(__name__)


class RealTimeStream:
    """WebSocket client for real-time game data streaming."""

    def __init__(self, host: str = "localhost", port: int = 8470) -> None:
        self.uri = f"ws://{host}:{port}"
        self.websocket: Optional[object] = None  # websockets.WebSocketClientProtocol
        self.latest_state: Optional[FactoryState] = None
        self._receive_task: Optional[asyncio.Task[None]] = None
        self._connected = False

    async def connect(self) -> bool:
        """Establish WebSocket connection to game plugin."""
        try:
            import websockets

            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=10,
                ping_timeout=5,
            )
            self._receive_task = asyncio.create_task(self._receive_loop())
            self._connected = True
            logger.info(f"Connected to game at {self.uri}")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to game: {e}")
            self._connected = False
            return False

    async def _receive_loop(self) -> None:
        """Continuously receive and process game data."""
        try:
            import websockets

            async for message in self.websocket:  # type: ignore
                data = json.loads(message)
                self.latest_state = FactoryState.from_realtime_data(data)
                logger.debug(f"Received state update: {len(message)} bytes")
        except Exception as e:
            logger.info(f"WebSocket connection closed: {e}")
            self._connected = False

    def is_connected(self) -> bool:
        """Check if WebSocket connection is active."""
        return self._connected and self.latest_state is not None

    async def get_current_state(self) -> FactoryState:
        """Get most recent factory state from stream."""
        if not self.is_connected():
            if not await self.connect():
                raise ConnectionError("Cannot connect to game")

        # Wait for at least one state update
        timeout = 5.0
        elapsed = 0.0
        while self.latest_state is None and elapsed < timeout:
            await asyncio.sleep(0.1)
            elapsed += 0.1

        if self.latest_state is None:
            raise TimeoutError("No data received from game")

        return self.latest_state

    async def close(self) -> None:
        """Close WebSocket connection."""
        if self._receive_task:
            self._receive_task.cancel()
        if self.websocket:
            await self.websocket.close()  # type: ignore
        self._connected = False
