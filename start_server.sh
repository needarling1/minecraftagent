#!/bin/bash

# Start script for A2A server with Cloudflared
# This script starts both the FastAPI server and Cloudflared tunnel

set -e

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY environment variable is not set"
    echo "Video evaluation will not work without it"
fi

# Start FastAPI server in background
echo "Starting FastAPI server on port 8000..."
python a2a_server.py --host 0.0.0.0 --port 8000 > server.log 2>&1 &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait a moment for server to start
sleep 2

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: Server failed to start. Check server.log for details."
    exit 1
fi

# Start Cloudflared tunnel
echo "Starting Cloudflared tunnel..."
cloudflared tunnel run mcu-green-agent > cloudflared.log 2>&1 &
TUNNEL_PID=$!
echo "Tunnel started with PID: $TUNNEL_PID"

echo ""
echo "=========================================="
echo "A2A Server is running!"
echo "=========================================="
echo "Server PID: $SERVER_PID"
echo "Tunnel PID: $TUNNEL_PID"
echo ""
echo "To stop the server:"
echo "  kill $SERVER_PID $TUNNEL_PID"
echo ""
echo "To view logs:"
echo "  tail -f server.log"
echo "  tail -f cloudflared.log"
echo ""
echo "Server URL will be shown in cloudflared.log"
echo "=========================================="

