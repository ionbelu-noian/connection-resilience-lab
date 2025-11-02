# Connection Resilience Lab

A multi-service Python application that demonstrates various network protocols and connection handling patterns.

## Services

1. TCP server sending XML messages (port 9001)
2. TCP server sending JSON messages (port 9002)
3. WebSocket server sending JSON messages (port 9003)
4. UDP unicast sender transmitting Protobuf messages (destination configurable, default port 9004)

## Features

- Heartbeat messages every 10 seconds
- Data messages every 15 seconds
- Runtime-configurable intervals
- Interactive menu for controlling services
- Graceful shutdown handling
- Clean logging format

## Building

```bash
docker build -t connection-resilience-lab .
```

## Running

```bash
docker run -it --rm \
  -p 9001:9001 \
  -p 9002:9002 \
  -p 9003:9003 \
  connection-resilience-lab
```

### Environment Variables

- `TCP_XML_PORT=9001`
- `TCP_JSON_PORT=9002`
- `WS_JSON_PORT=9003`
- `UDP_DEST_IP=127.0.0.1`
- `UDP_DEST_PORT=9004`
- `HEARTBEAT_SEC=10`
- `MESSAGE_SEC=15`

## Interactive Menu Commands

```
help                           - show command help
status                         - show services status
pause xml|json|ws|udp         - pause a service
resume xml|json|ws|udp        - resume a service
graceful-close xml|json|ws    - close connections gracefully
hard-close xml|json|ws        - force close connections
half-close xml|json           - shutdown write side only
burst xml|json|ws N           - send N data messages
intervals <svc> hb <sec> msg <sec>  - change intervals
udp-dest <ip> <port>          - change UDP destination
quit                          - exit the application
```

## Testing Connections

### TCP XML Server (port 9001)
```bash
nc localhost 9001
```

### TCP JSON Server (port 9002)
```bash
nc localhost 9002
```

### WebSocket Server (port 9003)
```bash
# Using websocat
websocat ws://localhost:9003/
```

### UDP Messages (port 9004)
```bash
# Using netcat in UDP mode
nc -lu 9004
```