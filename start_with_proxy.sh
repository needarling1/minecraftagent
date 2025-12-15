#!/bin/bash
# Start agents with AgentBeats-style proxy routing
# This creates /to_agent/{id}/ URL structure without requiring earthshaker (Python 3.13+)

echo "Starting Minecraft agents with proxy wrapper..."
echo "==============================================="
echo ""

# Start green agent on port 9001 (internal)
echo "[1/4] Starting green agent on port 9001..."
python main.py green --host 127.0.0.1 --port 9001 &
GREEN_PID=$!
sleep 3

# Start white agent on port 9002 (internal)
echo "[2/4] Starting white agent on port 9002..."
python main.py white --host 127.0.0.1 --port 9002 &
WHITE_PID=$!
sleep 3

# Start proxy for green agent on port 8001 (public)
echo "[3/4] Starting proxy for green agent on port 8001..."
python proxy_wrapper.py --agent-url http://localhost:9001 --port 8001 &
GREEN_PROXY_PID=$!
sleep 2

# Start proxy for white agent on port 8002 (public)
echo "[4/4] Starting proxy for white agent on port 8002..."
python proxy_wrapper.py --agent-url http://localhost:9002 --port 8002 &
WHITE_PROXY_PID=$!
sleep 2

echo ""
echo "==============================================="
echo "All services started!"
echo ""
echo "Green Agent (with proxy):"
echo "  Proxy URL: http://localhost:8001"
echo "  Visit: http://localhost:8001/ to see agent ID"
echo "  Agent card: http://localhost:8001/to_agent/{ID}/.well-known/agent-card.json"
echo ""
echo "White Agent (with proxy):"
echo "  Proxy URL: http://localhost:8002"
echo "  Visit: http://localhost:8002/ to see agent ID"
echo "  Agent card: http://localhost:8002/to_agent/{ID}/.well-known/agent-card.json"
echo ""
echo "Next steps:"
echo "1. Expose ports 8001 and 8002 with localtunnel:"
echo "   lt --port 8001  # For green agent"
echo "   lt --port 8002  # For white agent"
echo "2. Get the agent IDs from http://localhost:8001/ and http://localhost:8002/"
echo "3. Register on AgentBeats using URLs like:"
echo "   https://your-tunnel.loca.lt/to_agent/{agent_id}/"
echo ""
echo "Press Ctrl+C to stop all services"
echo "==============================================="

# Wait for Ctrl+C
wait

# Cleanup on exit
echo ""
echo "Stopping all services..."
kill $GREEN_PID $WHITE_PID $GREEN_PROXY_PID $WHITE_PROXY_PID 2>/dev/null
echo "Done!"
