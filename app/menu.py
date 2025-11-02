import asyncio
import sys
from typing import Dict, Any, Optional, List
from .logutil import log

class Menu:
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.source = "menu"
        self.running = True

    def print_help(self) -> None:
        """Print available commands"""
        print("\nAvailable commands:")
        print("  help                           - show this help")
        print("  status                         - show services status")
        print("  pause xml|json|ws|udp         - pause a service")
        print("  resume xml|json|ws|udp        - resume a service")
        print("  graceful-close xml|json|ws    - close connections gracefully")
        print("  hard-close xml|json|ws        - force close connections")
        print("  half-close xml|json           - shutdown write side only")
        print("  burst xml|json|ws N           - send N data messages")
        print("  intervals <svc> hb <sec> msg <sec>  - change intervals")
        print("  udp-dest <ip> <port>          - change UDP destination")
        print("  quit                          - exit the application")

    def show_status(self) -> None:
        """Show current status of all services"""
        def format_service(name: str, running: bool, paused: bool, clients: int = 0) -> str:
            status = "running" if running else "stopped"
            if paused:
                status += " (paused)"
            if running:
                next_hb = round(self.state["heartbeat_interval"], 1)
                next_msg = round(self.state["message_interval"], 1)
                return f"{name:8} {status:15} clients: {clients:3} next_hb: {next_hb}s next_msg: {next_msg}s"
            return f"{name:8} {status}"

        print("\nService Status:")
        print(format_service("XML", self.state["xml_running"], self.state["xml_paused"], 
                           len(self.state.get("xml_clients", []))))
        print(format_service("JSON", self.state["json_running"], self.state["json_paused"],
                           len(self.state.get("json_clients", []))))
        print(format_service("WS", self.state["ws_running"], self.state["ws_paused"],
                           len(self.state.get("ws_clients", []))))
        print(format_service("UDP", self.state["udp_running"], self.state["udp_paused"]))
        print(f"UDP destination: {self.state['udp_dest_ip']}:{self.state['udp_dest_port']}")

    async def handle_command(self, cmd: str) -> None:
        """Process a command from user input"""
        parts = cmd.strip().split()
        if not parts:
            return

        cmd_name = parts[0].lower()

        if cmd_name == "help":
            self.print_help()
        
        elif cmd_name == "status":
            self.show_status()
            log(self.source, "status displayed")
        
        elif cmd_name == "quit":
            log(self.source, "quit requested")
            self.running = False
        
        elif cmd_name in ("pause", "resume"):
            if len(parts) != 2 or parts[1] not in ("xml", "json", "ws", "udp"):
                print("Usage: pause|resume xml|json|ws|udp")
                return
            
            service = parts[1]
            paused = cmd_name == "pause"
            self.state[f"{service}_paused"] = paused
            log(self.source, f"{cmd_name}d {service}")
        
        elif cmd_name in ("graceful-close", "hard-close", "half-close"):
            if len(parts) != 2 or parts[1] not in ("xml", "json", "ws"):
                valid_services = "xml|json|ws" if cmd_name != "half-close" else "xml|json"
                print(f"Usage: {cmd_name} {valid_services}")
                return
            
            service = parts[1]
            if cmd_name == "half-close" and service == "ws":
                log(self.source, "half-close not supported for WebSocket")
                return
                
            # This will be handled by the main loop to call appropriate service methods
            self.state[f"{service}_close_type"] = cmd_name
            log(self.source, f"{cmd_name} requested for {service}")
        
        elif cmd_name == "burst":
            if len(parts) != 3 or parts[1] not in ("xml", "json", "ws"):
                print("Usage: burst xml|json|ws N")
                return
            
            try:
                count = int(parts[2])
                if count <= 0:
                    raise ValueError
            except ValueError:
                print("Burst count must be a positive integer")
                return
            
            self.state[f"{parts[1]}_burst"] = count
            log(self.source, f"burst {count} messages requested for {parts[1]}")
        
        elif cmd_name == "intervals":
            if len(parts) != 6 or parts[2] != "hb" or parts[4] != "msg":
                print("Usage: intervals <svc> hb <sec> msg <sec>")
                return
            
            service = parts[1]
            if service not in ("xml", "json", "ws", "udp"):
                print("Invalid service. Use: xml, json, ws, or udp")
                return
            
            try:
                hb_interval = float(parts[3])
                msg_interval = float(parts[5])
                if hb_interval <= 0 or msg_interval <= 0:
                    raise ValueError
            except ValueError:
                print("Intervals must be positive numbers")
                return
            
            self.state["heartbeat_interval"] = hb_interval
            self.state["message_interval"] = msg_interval
            log(self.source, f"intervals updated for {service}: hb={hb_interval}s msg={msg_interval}s")
        
        elif cmd_name == "udp-dest":
            if len(parts) != 3:
                print("Usage: udp-dest <ip> <port>")
                return
            
            try:
                port = int(parts[2])
                if not (0 < port < 65536):
                    raise ValueError
            except ValueError:
                print("Port must be a number between 1 and 65535")
                return
            
            self.state["udp_dest_update"] = (parts[1], port)
            log(self.source, f"UDP destination update requested: {parts[1]}:{port}")
        
        else:
            print("Unknown command. Type 'help' for available commands.")

    async def run(self) -> None:
        """Run the interactive menu loop"""
        self.print_help()
        while self.running:
            try:
                if sys.stdin.isatty():
                    cmd = input("\n> ").strip()
                    await self.handle_command(cmd)
                else:
                    # No TTY available, just wait
                    await asyncio.sleep(1)
            except EOFError:
                break
            except KeyboardInterrupt:
                print()  # New line after ^C
                continue