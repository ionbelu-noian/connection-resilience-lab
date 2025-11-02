import asyncio
import json
from typing import Set, Dict, Any
import websockets
from websockets.server import WebSocketServerProtocol
from ..logutil import log
from ..formats import build_json_heartbeat, build_json_track, sample_track

class WebSocketServer:
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.clients: Set[WebSocketServerProtocol] = set()
        self.source = "ws"

    async def handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handle individual WebSocket client connection"""
        try:
            log(self.source, f"new client connection from {websocket.remote_address}")
            self.clients.add(websocket)
            await websocket.wait_closed()
        except Exception:
            pass
        finally:
            self.clients.remove(websocket)
            log(self.source, f"client {websocket.remote_address} disconnected")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Send message to all connected clients"""
        if not self.clients or not self.state["ws_running"]:
            return

        json_str = json.dumps(message)
        dead_clients = set()

        for websocket in self.clients:
            try:
                await websocket.send(json_str)
            except Exception:
                dead_clients.add(websocket)

        # Clean up dead clients
        self.clients.difference_update(dead_clients)

    async def heartbeat_loop(self) -> None:
        """Send heartbeats periodically"""
        while True:
            if self.state["ws_running"] and not self.state["ws_paused"]:
                await self.broadcast(build_json_heartbeat())
            await asyncio.sleep(self.state["heartbeat_interval"])

    async def data_loop(self) -> None:
        """Send data messages periodically"""
        while True:
            if self.state["ws_running"] and not self.state["ws_paused"]:
                track = sample_track()
                await self.broadcast(build_json_track(track))
            await asyncio.sleep(self.state["message_interval"])

    def close_clients(self, graceful: bool = True) -> None:
        """Close all client connections"""
        if self.clients:
            asyncio.create_task(self._close_clients(graceful))

    async def _close_clients(self, graceful: bool) -> None:
        """Asynchronously close all client connections"""
        for websocket in self.clients.copy():
            try:
                if graceful:
                    await websocket.close()
                else:
                    websocket.transport.close()
            except Exception:
                pass
        self.clients.clear()

    async def start(self) -> None:
        """Start the WebSocket server and message loops"""
        self.state["ws_running"] = True
        self.state["ws_paused"] = False
        
        async with websockets.serve(
            self.handle_client,
            "0.0.0.0",
            self.state["ws_json_port"]
        ) as server:
            log(self.source, f"listening on :{self.state['ws_json_port']}")
            await asyncio.gather(
                self.heartbeat_loop(),
                self.data_loop(),
                server.wait_closed()
            )

async def start_service(state: Dict[str, Any]) -> asyncio.Task:
    """Create and start the WebSocket server service"""
    server = WebSocketServer(state)
    return asyncio.create_task(server.start())