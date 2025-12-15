"""
Simple proxy wrapper to add /to_agent/{id}/ routing pattern.
Compatible with Python 3.10+, doesn't require earthshaker.
"""

import uuid
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx
import argparse

app = FastAPI()

# Configuration
AGENT_URL = None
AGENT_ID = str(uuid.uuid4().hex[:32])  # Generate a unique agent ID


@app.api_route("/to_agent/{agent_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_agent(agent_id: str, path: str, request: Request):
    """Proxy all requests to /to_agent/{id}/* to the actual agent."""

    # Forward request to actual agent
    target_url = f"{AGENT_URL}/{path}"

    # Copy headers
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header

    # Get request body
    body = await request.body()

    # Forward request
    async with httpx.AsyncClient(timeout=600.0) as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params
        )

    # Return response
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@app.get("/")
async def root():
    """Root endpoint showing agent info."""
    return {
        "message": "AgentBeats Proxy Wrapper",
        "agent_id": AGENT_ID,
        "agent_url": f"/to_agent/{AGENT_ID}/.well-known/agent-card.json"
    }


def main():
    global AGENT_URL, AGENT_ID

    parser = argparse.ArgumentParser(description="Proxy wrapper for AgentBeats-style routing")
    parser.add_argument("--agent-url", required=True, help="URL of the agent to proxy (e.g., http://localhost:9001)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, required=True, help="Port to bind to")
    parser.add_argument("--agent-id", default=None, help="Custom agent ID (optional, auto-generated if not provided)")

    args = parser.parse_args()

    AGENT_URL = args.agent_url.rstrip("/")
    if args.agent_id:
        AGENT_ID = args.agent_id

    print(f"Starting proxy wrapper on {args.host}:{args.port}")
    print(f"Agent ID: {AGENT_ID}")
    print(f"Proxying to: {AGENT_URL}")
    print(f"Agent accessible at: http://{args.host}:{args.port}/to_agent/{AGENT_ID}/")
    print(f"Agent card: http://{args.host}:{args.port}/to_agent/{AGENT_ID}/.well-known/agent-card.json")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
