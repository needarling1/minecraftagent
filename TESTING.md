# Testing Guide for A2A Server

## Setting Up Your OpenAI API Key

The server needs your OpenAI API key for:
- Task generation (LLM creates new tasks)
- Video evaluation (VLM evaluates white agent performance)

### Option 1: Export in Terminal (Recommended for Testing)

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

Then start the server:
```bash
python a2a_server.py
```

### Option 2: Set When Running Server

```bash
OPENAI_API_KEY="sk-your-api-key-here" python a2a_server.py
```

### Option 3: Create a `.env` File (Recommended for Production)

Create a file named `.env` in the project root:
```bash
echo 'OPENAI_API_KEY=sk-your-api-key-here' > .env
```

Then modify `a2a_server.py` to load it (or use python-dotenv):
```bash
pip install python-dotenv
```

And add to the top of `a2a_server.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Option 4: Use the Start Script

Edit `start_server.sh` and add before the server starts:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

## Quick Test

1. **Set your API key:**
   ```bash
   export OPENAI_API_KEY="sk-your-api-key-here"
   ```

2. **Start the server:**
   ```bash
   python a2a_server.py --host 0.0.0.0 --port 8000
   ```

3. **In another terminal, test it:**
   ```bash
   # Test health
   curl http://localhost:8000/health
   
   # Test agent card
   curl http://localhost:8000/.well-known/agent.json
   
   # Test task generation (requires API key)
   curl -X POST http://localhost:8000/a2a/task/generate \
     -H "Content-Type: application/json" \
     -d '{"task_type": "atomic", "difficulty": "simple"}'
   ```

## Testing Task Generation

### Test 1: Generate a Random Atomic Task

```bash
curl -X POST http://localhost:8000/a2a/task/generate \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "atomic",
    "difficulty": "simple"
  }'
```

Expected response:
```json
{
  "task_id": "uuid-here",
  "task_name": "combat_a_zombie",
  "task_description": "combat and kill a zombie",
  "difficulty": "simple",
  "task_type": "atomic",
  "thinking": "...",
  "custom_init_commands": ["/give @s ...", ...]
}
```

### Test 2: Generate a Specific Task

```bash
curl -X POST http://localhost:8000/a2a/task/generate \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "atomic",
    "difficulty": "simple",
    "task_name": "mine iron ore"
  }'
```

### Test 3: Generate Compositional Task

```bash
curl -X POST http://localhost:8000/a2a/task/generate \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "compositional",
    "difficulty": "simple",
    "num_tasks": 2
  }'
```

## Testing Task Assignment

### Assign a Generated Task to a White Agent

```bash
curl -X POST http://localhost:8000/a2a/task/assign \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "white_agent_1",
    "task_type": "atomic",
    "difficulty": "simple",
    "generate_new": true
  }'
```

This will:
1. Generate a new task
2. Initialize it in MineStudio
3. Return the initial observation

**Note:** This requires MineStudio to be installed and working.

## Testing Video Evaluation

### Test with a Video File

```bash
curl -X POST http://localhost:8000/a2a/evaluate \
  -F "task_name=mine_diamond_ore" \
  -F "video_file=@path/to/video.mp4"
```

### Test with Video URL

```bash
curl -X POST http://localhost:8000/a2a/evaluate \
  -F "task_name=mine_diamond_ore" \
  -F "video_url=https://example.com/video.mp4"
```

## Full Workflow Test

1. **Generate a task:**
   ```bash
   TASK_RESPONSE=$(curl -s -X POST http://localhost:8000/a2a/task/generate \
     -H "Content-Type: application/json" \
     -d '{"task_type": "atomic", "difficulty": "simple"}')
   
   echo $TASK_RESPONSE | jq .
   ```

2. **Assign to white agent (if MineStudio available):**
   ```bash
   curl -X POST http://localhost:8000/a2a/task/assign \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": "test_agent",
       "task_type": "atomic",
       "difficulty": "simple",
       "generate_new": true
     }'
   ```

3. **Evaluate a video:**
   ```bash
   curl -X POST http://localhost:8000/a2a/evaluate \
     -F "task_name=mine_diamond_ore" \
     -F "video_file=@output/collect_wood/episode_1.mp4"
   ```

## Using Python Test Script

Run the existing test script:
```bash
python test_server.py
```

This tests:
- Health check
- Task listing
- Agent listing
- Task initialization (if MineStudio available)

## Troubleshooting

### "OpenAI API key not configured"
- Make sure you exported the variable: `export OPENAI_API_KEY="sk-..."`
- Check it's set: `echo $OPENAI_API_KEY`
- Restart the server after setting it

### Task generation fails
- Check your OpenAI API key is valid
- Check you have API credits/quota
- Check the server logs for error messages

### MineStudio not working
- The server will still work for task generation and evaluation
- Task assignment requires MineStudio
- Check Java 8 is installed: `java -version`

## Testing with AgentBeats

Once your server is running and accessible:

1. **Get your public URL** (from cloudflared):
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

2. **Test the agent card:**
   ```bash
   curl https://your-url.trycloudflare.com/.well-known/agent.json
   ```

3. **Paste the URL into AgentBeats**

4. **AgentBeats will:**
   - Discover your agent
   - Generate/assign tasks to white agents
   - Submit videos for evaluation
   - Get scores back

