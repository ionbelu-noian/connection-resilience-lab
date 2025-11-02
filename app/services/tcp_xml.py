import asyncio
from typing import Set, Dict, Any
from ..logutil import log
from ..formats import build_xml_heartbeat, build_xml_track, sample_track

class XMLServer:
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.clients: Set[asyncio.StreamWriter] = set()
        self.source = "tcp_xml"

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle individual client connection"""
        peername = writer.get_extra_info('peername')
        log(self.source, f"new client connection from {peername}")
        self.clients.add(writer)
        
        try:
            while True:
                # Keep connection alive until client disconnects
                await reader.read(1)
                break
        except Exception:
            pass
        finally:
            self.clients.remove(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            log(self.source, f"client {peername} disconnected")

    async def broadcast(self, message: str) -> None:
        """Send message to all connected clients"""
        if not self.clients or not self.state["xml_running"]:
            return
        
        dead_clients = set()
        for writer in self.clients:
            try:
                writer.write(f"{message}\n".encode())
                await writer.drain()
            except Exception:
                dead_clients.add(writer)
        
        # Clean up dead clients
        for writer in dead_clients:
            self.clients.remove(writer)
            try:
                writer.close()
            except Exception:
                pass

    async def heartbeat_loop(self) -> None:
        """Send heartbeats periodically"""
        while True:
            if self.state["xml_running"] and not self.state["xml_paused"]:
                await self.broadcast(build_xml_heartbeat())
            await asyncio.sleep(self.state["heartbeat_interval"])

    async def data_loop(self) -> None:
        """Send data messages periodically"""
        while True:
            if self.state["xml_running"] and not self.state["xml_paused"]:
                track = sample_track()
                await self.broadcast(build_xml_track(track))
            await asyncio.sleep(self.state["message_interval"])

    async def start_server(self) -> None:
        """Start the TCP XML server"""
        server = await asyncio.start_server(
            self.handle_client, 
            '0.0.0.0', 
            self.state["tcp_xml_port"]
        )
        log(self.source, f"listening on :{self.state['tcp_xml_port']}")
        
        async with server:
            await server.serve_forever()

    def close_clients(self, graceful: bool = True) -> None:
        """Close all client connections"""
        for writer in self.clients.copy():
            try:
                if graceful:
                    writer.write_eof()
                writer.close()
            except Exception:
                pass
        self.clients.clear()

    async def start(self) -> None:
        """Start all server tasks"""
        self.state["xml_running"] = True
        self.state["xml_paused"] = False
        return await asyncio.gather(
            self.start_server(),
            self.heartbeat_loop(),
            self.data_loop()
        )

async def start_service(state: Dict[str, Any]) -> asyncio.Task:
    """Create and start the XML server service"""
    server = XMLServer(state)
    return asyncio.create_task(server.start())