# Quick Start Guide

## Will it work with AgentBeats?

**Yes!** After following these steps, you can paste your URL into AgentBeats and it should work.

## Prerequisites Check

Before starting, make sure you have:

- [ ] Python 3.10+ installed
- [ ] OpenAI API key (for video evaluation)
- [ ] Java 8 installed (for MineStudio)
- [ ] Cloudflare account (for cloudflared tunnel)

## Step-by-Step Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 3. Start the Server

**Option A: Quick Start (using quick tunnel - no setup needed)**
```bash
# Terminal 1: Start the server
python a2a_server.py --host 0.0.0.0 --port 8000

# Terminal 2: Start cloudflared (get public URL)
cloudflared tunnel --url http://localhost:8000
```

**Option B: Using the startup script**
```bash
./start_server.sh
```

### 4. Get Your Public URL

After starting cloudflared, you'll see output like:
```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable): |
|  https://xxxx-xxxx-xxxx.trycloudflare.com                                                  |
+--------------------------------------------------------------------------------------------+
```

**Copy that URL** - this is what you'll paste into AgentBeats!

### 5. Verify It's Working

Test the server:
```bash
python test_server.py
```

Or manually test:
```bash
# Health check
curl https://your-url.trycloudflare.com/health

# Agent card (required by AgentBeats)
curl https://your-url.trycloudflare.com/.well-known/agent.json

# List tasks
curl https://your-url.trycloudflare.com/a2a/tasks
```

### 6. Register with AgentBeats

1. Go to https://v2.agentbeats.org/main
2. Login with GitHub
3. In the controller, paste your public URL (e.g., `https://xxxx-xxxx-xxxx.trycloudflare.com`)
4. AgentBeats will discover your agent via `/.well-known/agent.json`

## What AgentBeats Will Do

1. **Discover your agent** via `/.well-known/agent.json`
2. **Send white agents** to interact with your server:
   - Initialize tasks via `/a2a/task/init`
   - Execute actions via `/a2a/action`
   - Submit videos for evaluation via `/a2a/evaluate`
3. **Your green agent** will:
   - Provide MineStudio access to white agents
   - Evaluate their video submissions
   - Return scores and feedback

## Troubleshooting

### Server not accessible?
- Make sure cloudflared is running
- Check that port 8000 is not blocked
- Verify the URL in cloudflared output

### AgentBeats can't discover your agent?
- Test: `curl https://your-url/.well-known/agent.json`
- Should return JSON with agent metadata
- Check CORS settings (already enabled in code)

### Evaluation not working?
- Verify `OPENAI_API_KEY` is set: `echo $OPENAI_API_KEY`
- Check server logs for errors
- Ensure criteria files exist in `auto_eval/criteria_files/`

### MineStudio issues?
- Verify Java 8: `java -version`
- Check MineStudio installation: `pip show minestudio`
- Server will still work for evaluation even if MineStudio fails

## Expected Behavior

Once registered with AgentBeats:
- ✅ AgentBeats discovers your agent
- ✅ White agents can initialize Minecraft tasks
- ✅ White agents can execute actions
- ✅ Videos are automatically evaluated
- ✅ Scores are returned to AgentBeats

## Notes

- The server handles multiple concurrent white agents
- Each agent gets its own session (agent_id)
- Videos are evaluated using your existing green agent logic
- All evaluation happens server-side

