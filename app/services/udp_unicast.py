import asyncio
from typing import Dict, Any, Tuple
from ..logutil import log
from ..formats import build_protobuf_heartbeat, build_protobuf_track, sample_track

class UDPSender:
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.transport = None
        self.source = "udp"

    async def create_endpoint(self) -> None:
        """Create UDP endpoint"""
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            asyncio.DatagramProtocol,
            remote_addr=(self.state["udp_dest_ip"], self.state["udp_dest_port"])
        )
        self.transport = transport
        log(self.source, f"sending to {self.state['udp_dest_ip']}:{self.state['udp_dest_port']}")

    def send_message(self, message: bytes) -> None:
        """Send UDP message to configured destination"""
        if self.transport and self.state["udp_running"] and not self.state["udp_paused"]:
            try:
                self.transport.sendto(message)
            except Exception as e:
                log(self.source, f"failed to send: {str(e)}")

    async def update_destination(self, ip: str, port: int) -> None:
        """Update the UDP destination address"""
        old_transport = self.transport
        self.state["udp_dest_ip"] = ip
        self.state["udp_dest_port"] = port
        
        if old_transport:
            old_transport.close()
        
        await self.create_endpoint()
        log(self.source, f"destination changed to {ip}:{port}")

    async def heartbeat_loop(self) -> None:
        """Send heartbeats periodically"""
        while True:
            if self.state["udp_running"] and not self.state["udp_paused"]:
                self.send_message(build_protobuf_heartbeat())
            await asyncio.sleep(self.state["heartbeat_interval"])

    async def data_loop(self) -> None:
        """Send data messages periodically"""
        while True:
            if self.state["udp_running"] and not self.state["udp_paused"]:
                track = sample_track()
                self.send_message(build_protobuf_track(track))
            await asyncio.sleep(self.state["message_interval"])

    async def start(self) -> None:
        """Start the UDP sender service"""
        self.state["udp_running"] = True
        self.state["udp_paused"] = False
        await self.create_endpoint()
        
        await asyncio.gather(
            self.heartbeat_loop(),
            self.data_loop()
        )

    def stop(self) -> None:
        """Stop the UDP sender"""
        if self.transport:
            self.transport.close()
            self.transport = None

async def start_service(state: Dict[str, Any]) -> asyncio.Task:
    """Create and start the UDP sender service"""
    sender = UDPSender(state)
    return asyncio.create_task(sender.start())