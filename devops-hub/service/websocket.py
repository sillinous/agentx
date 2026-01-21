"""
WebSocket support for real-time event streaming.

Provides WebSocket endpoint for clients to receive events from the MessageBus in real-time.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from starlette.websockets import WebSocketState

from service.message_bus import get_message_bus, Event

logger = logging.getLogger(__name__)

# WebSocket router
router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for real-time event streaming.

    Features:
    - Multiple concurrent client connections
    - Per-connection event type filtering
    - Automatic cleanup on disconnect
    - Heartbeat/ping-pong for connection health
    """

    def __init__(self):
        self._connections: Dict[str, "ClientConnection"] = {}
        self._lock = asyncio.Lock()
        self._subscription_id: Optional[str] = None
        self._heartbeat_interval: int = 30  # seconds

    async def connect(
        self,
        websocket: WebSocket,
        event_types: Optional[List[str]] = None,
        source_filter: Optional[str] = None,
    ) -> str:
        """
        Accept a new WebSocket connection and register it.

        Args:
            websocket: The WebSocket connection
            event_types: List of event types to filter (None = all events)
            source_filter: Filter events by source

        Returns:
            Connection ID
        """
        await websocket.accept()

        connection_id = str(uuid4())
        connection = ClientConnection(
            id=connection_id,
            websocket=websocket,
            event_types=set(event_types) if event_types else None,
            source_filter=source_filter,
        )

        async with self._lock:
            self._connections[connection_id] = connection

            # Subscribe to message bus if this is the first connection
            if self._subscription_id is None:
                bus = get_message_bus()
                self._subscription_id = bus.subscribe(
                    event_type="*",
                    handler=self._broadcast_event,
                )
                logger.info("WebSocket manager subscribed to message bus")

        logger.info(f"WebSocket client connected: {connection_id}")

        # Send connection confirmation
        await self._send_message(connection, {
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat(),
            "filters": {
                "event_types": list(event_types) if event_types else None,
                "source": source_filter,
            },
        })

        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """Remove a connection and clean up resources."""
        async with self._lock:
            if connection_id in self._connections:
                connection = self._connections.pop(connection_id)
                logger.info(f"WebSocket client disconnected: {connection_id}")

                # Close the websocket if still open
                if connection.websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await connection.websocket.close()
                    except Exception:
                        pass

                # Unsubscribe from message bus if no more connections
                if not self._connections and self._subscription_id:
                    bus = get_message_bus()
                    bus.unsubscribe(self._subscription_id)
                    self._subscription_id = None
                    logger.info("WebSocket manager unsubscribed from message bus")

    async def _broadcast_event(self, event: Event) -> None:
        """Broadcast an event to all matching connections."""
        event_data = {
            "type": "event",
            "event": event.to_dict(),
        }

        # Get snapshot of connections
        async with self._lock:
            connections = list(self._connections.values())

        # Send to each matching connection
        disconnected = []
        for connection in connections:
            if connection.matches_event(event):
                try:
                    await self._send_message(connection, event_data)
                except Exception as e:
                    logger.warning(f"Failed to send to {connection.id}: {e}")
                    disconnected.append(connection.id)

        # Clean up disconnected clients
        for conn_id in disconnected:
            await self.disconnect(conn_id)

    async def _send_message(self, connection: "ClientConnection", data: dict) -> None:
        """Send a JSON message to a connection."""
        if connection.websocket.client_state == WebSocketState.CONNECTED:
            await connection.websocket.send_json(data)

    async def send_heartbeat(self, connection_id: str) -> bool:
        """Send a heartbeat ping to a connection. Returns True if successful."""
        async with self._lock:
            connection = self._connections.get(connection_id)

        if not connection:
            return False

        try:
            await self._send_message(connection, {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat(),
            })
            return True
        except Exception:
            return False

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    def get_connection_info(self) -> List[dict]:
        """Get information about all active connections."""
        return [
            {
                "id": conn.id,
                "connected_at": conn.connected_at.isoformat(),
                "event_types": list(conn.event_types) if conn.event_types else None,
                "source_filter": conn.source_filter,
            }
            for conn in self._connections.values()
        ]


class ClientConnection:
    """Represents a single WebSocket client connection."""

    def __init__(
        self,
        id: str,
        websocket: WebSocket,
        event_types: Optional[Set[str]] = None,
        source_filter: Optional[str] = None,
    ):
        self.id = id
        self.websocket = websocket
        self.event_types = event_types
        self.source_filter = source_filter
        self.connected_at = datetime.utcnow()

    def matches_event(self, event: Event) -> bool:
        """Check if this connection should receive the given event."""
        # Check event type filter
        if self.event_types and event.type not in self.event_types:
            return False

        # Check source filter
        if self.source_filter and event.source != self.source_filter:
            return False

        return True


# Global connection manager instance
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


@router.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
    event_types: Optional[str] = Query(None, description="Comma-separated list of event types to filter"),
    source: Optional[str] = Query(None, description="Filter events by source"),
):
    """
    WebSocket endpoint for real-time event streaming.

    Query Parameters:
        event_types: Comma-separated list of event types to subscribe to (e.g., "agent.started,task.completed")
        source: Filter events by source agent/service

    Messages:
        - Server sends 'connected' message on connection
        - Server sends 'event' messages for each matching event
        - Server sends 'ping' messages for heartbeat
        - Client can send 'pong' to respond to ping
        - Client can send 'subscribe' to update filters
        - Client can send 'unsubscribe' to clear filters
    """
    manager = get_connection_manager()

    # Parse event types filter
    event_type_list = None
    if event_types:
        event_type_list = [t.strip() for t in event_types.split(",") if t.strip()]

    # Accept connection
    connection_id = await manager.connect(
        websocket=websocket,
        event_types=event_type_list,
        source_filter=source,
    )

    try:
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(connection_id, manager)
        )

        try:
            # Main message loop
            while True:
                try:
                    # Wait for client messages with timeout for heartbeat
                    data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=60.0,
                    )
                    await _handle_client_message(connection_id, data, manager)
                except asyncio.TimeoutError:
                    # No message received, continue (heartbeat handles connection health)
                    continue
                except json.JSONDecodeError:
                    # Invalid JSON, send error and continue
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON",
                    })
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {connection_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        await manager.disconnect(connection_id)


async def _heartbeat_loop(connection_id: str, manager: ConnectionManager) -> None:
    """Send periodic heartbeat pings to keep the connection alive."""
    while True:
        await asyncio.sleep(30)
        if not await manager.send_heartbeat(connection_id):
            break


async def _handle_client_message(
    connection_id: str,
    data: dict,
    manager: ConnectionManager,
) -> None:
    """Handle incoming messages from WebSocket clients."""
    msg_type = data.get("type", "")

    if msg_type == "pong":
        # Client responded to ping, connection is healthy
        logger.debug(f"Received pong from {connection_id}")

    elif msg_type == "subscribe":
        # Client wants to update event type filters
        event_types = data.get("event_types", [])
        source = data.get("source")

        async with manager._lock:
            connection = manager._connections.get(connection_id)
            if connection:
                connection.event_types = set(event_types) if event_types else None
                connection.source_filter = source
                await connection.websocket.send_json({
                    "type": "subscribed",
                    "event_types": event_types,
                    "source": source,
                })

    elif msg_type == "unsubscribe":
        # Client wants to clear filters (receive all events)
        async with manager._lock:
            connection = manager._connections.get(connection_id)
            if connection:
                connection.event_types = None
                connection.source_filter = None
                await connection.websocket.send_json({
                    "type": "unsubscribed",
                })

    else:
        logger.debug(f"Unknown message type from {connection_id}: {msg_type}")


# REST endpoints for WebSocket management

@router.get("/ws/connections", tags=["WebSocket"])
async def get_connections():
    """Get information about active WebSocket connections."""
    manager = get_connection_manager()
    return {
        "count": manager.get_connection_count(),
        "connections": manager.get_connection_info(),
    }
