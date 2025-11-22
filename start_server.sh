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

# Optional: Start Cloudflared tunnel for local testing
if command -v cloudflared &> /dev/null; then
    echo "Starting Cloudflared tunnel (optional, for local testing)..."
    cloudflared tunnel --url http://localhost:8000 > cloudflared.log 2>&1 &
    TUNNEL_PID=$!
    echo "Tunnel started with PID: $TUNNEL_PID"
    echo ""
    echo "Public URL will be shown in cloudflared.log"
else
    echo "Cloudflared not found. Skipping tunnel setup."
    echo "For production, deploy to Render.com (see DEPLOY_RENDER.md)"
    TUNNEL_PID=""
fi

echo ""
echo "=========================================="
echo "A2A Server is running!"
echo "=========================================="
echo "Server PID: $SERVER_PID"
if [ ! -z "$TUNNEL_PID" ]; then
    echo "Tunnel PID: $TUNNEL_PID"
fi
echo ""
echo "Local URL: http://localhost:8000"
echo ""
echo "To stop the server:"
if [ ! -z "$TUNNEL_PID" ]; then
    echo "  kill $SERVER_PID $TUNNEL_PID"
else
    echo "  kill $SERVER_PID"
fi
echo ""
echo "To view logs:"
echo "  tail -f server.log"
if [ ! -z "$TUNNEL_PID" ]; then
    echo "  tail -f cloudflared.log"
fi
echo ""
echo "For production deployment, see DEPLOY_RENDER.md"
echo "=========================================="

