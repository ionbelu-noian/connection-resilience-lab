import asyncio
import os
import signal
import sys
from typing import Dict, Any

from .logutil import log
from .menu import Menu
from .services import tcp_xml, tcp_json, ws_json, udp_unicast

def get_env_int(name: str, default: int) -> int:
    """Get integer from environment variable with default"""
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default

def get_env_float(name: str, default: float) -> float:
    """Get float from environment variable with default"""
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default

def init_state() -> Dict[str, Any]:
    """Initialize application state"""
    return {
        # Service ports
        "tcp_xml_port": get_env_int("TCP_XML_PORT", 9001),
        "tcp_json_port": get_env_int("TCP_JSON_PORT", 9002),
        "ws_json_port": get_env_int("WS_JSON_PORT", 9003),
        
        # UDP configuration
        "udp_dest_ip": os.getenv("UDP_DEST_IP", "127.0.0.1"),
        "udp_dest_port": get_env_int("UDP_DEST_PORT", 9004),
        
        # Timing intervals
        "heartbeat_interval": get_env_float("HEARTBEAT_SEC", 10.0),
        "message_interval": get_env_float("MESSAGE_SEC", 15.0),
        
        # Service status flags
        "xml_running": False,
        "json_running": False,
        "ws_running": False,
        "udp_running": False,
        
        "xml_paused": False,
        "json_paused": False,
        "ws_paused": False,
        "udp_paused": False,
        
        # Command flags
        "xml_close_type": None,
        "json_close_type": None,
        "ws_close_type": None,
        "udp_dest_update": None,
    }

async def main() -> None:
    """Main application entry point"""
    # Initialize shared state
    state = init_state()
    
    # Create menu
    menu = Menu(state)
    
    # Start all services
    log("main", "starting services")
    tasks = []
    
    try:
        # Start TCP XML server
        xml_task = await tcp_xml.start_service(state)
        tasks.append(xml_task)
        
        # Start TCP JSON server
        json_task = await tcp_json.start_service(state)
        tasks.append(json_task)
        
        # Start WebSocket server
        ws_task = await ws_json.start_service(state)
        tasks.append(ws_task)
        
        # Start UDP sender
        udp_task = await udp_unicast.start_service(state)
        tasks.append(udp_task)
        
        # Start menu if running with TTY
        if sys.stdin.isatty():
            menu_task = asyncio.create_task(menu.run())
            tasks.append(menu_task)
        
        # Wait for all tasks or interruption
        await asyncio.gather(*tasks)
        
    except asyncio.CancelledError:
        log("main", "shutdown requested")
    except Exception as e:
        log("main", f"error: {str(e)}")
    finally:
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        log("main", "shutdown complete")

def run() -> None:
    """Run the application"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Handle signals
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: loop.stop())
    
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

if __name__ == "__main__":
    run()