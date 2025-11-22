# MCU Green Agent - A2A Server for AgentBeats

This repository contains a green agent (evaluator) that provides A2A-compatible endpoints for evaluating white agents on Minecraft tasks through the AgentBeats platform.

## Overview

The green agent serves two main functions:
1. **MineStudio Access**: Provides white agents with access to Minecraft through MineStudio simulator
2. **Video Evaluation**: Evaluates video submissions from white agents using VLM-based scoring

## Architecture

```
White Agent (from AgentBeats) 
    ↓
A2A Server (FastAPI) - Green Agent
    ↓
├──→ Task Generation (LLM) - Generates tasks for white agents
├──→ MineStudio (Minecraft Simulator) - Provides Minecraft access
└──→ Video Evaluation (VLM) - Evaluates white agent performance
```

## Green Agent Workflow

The green agent can:

1. **Generate Tasks**: Use `/a2a/task/generate` to create new tasks using LLM
   - Atomic tasks (single objectives)
   - Compositional tasks (multiple objectives combined)
   - Simple or hard difficulty

2. **Assign Tasks**: Use `/a2a/task/assign` to give tasks to white agents
   - Can generate new tasks on-the-fly
   - Can use predefined tasks from `task_configs/`
   - Automatically initializes the Minecraft environment

3. **Evaluate Results**: Use `/a2a/evaluate` to assess white agent videos
   - Uses VLM (GPT-4 Vision) to analyze performance
   - Returns scores across 6 dimensions
   - Provides detailed feedback

## Prerequisites

- Python 3.10+
- OpenAI API key (for video evaluation and task generation)
- Java 8 (for MineStudio)
- Render.com account (for deployment) OR cloudflared (for local tunneling)

## Installation

1. **Clone the repository** (if not already done):
```bash
cd /path/to/cs194
```

2. **Create and activate virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Install Java 8** (required for MineStudio):
```bash
# macOS
brew install openjdk@8

# Linux
sudo apt-get install openjdk-8-jdk

# Or use conda
conda install --channel=conda-forge openjdk=8
```

5. **Set environment variables**:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## Deployment Options

### Option 1: Deploy to Render.com (Recommended)

See [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for detailed instructions.

Quick steps:
1. Push your code to GitHub
2. Connect repository to Render.com
3. Render will auto-detect `render.yaml`
4. Set `OPENAI_API_KEY` in Render dashboard
5. Deploy!

Your service will be available at: `https://your-service.onrender.com`

### Option 2: Local Development with Cloudflared

For local testing, you can use cloudflared:

```bash
# Quick tunnel (no setup)
cloudflared tunnel --url http://localhost:8000
```

Or set up a persistent tunnel:
```bash
./setup_cloudflared.sh
```

## Running the Server

### Local Development

1. **Set your OpenAI API key**:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

2. **Start the server**:
```bash
python a2a_server.py --host 0.0.0.0 --port 8000
```

The server will automatically:
- Use `PORT` environment variable if set (for Render.com)
- Fall back to port 8000 for local development
- Load `.env` file if present

### Using the Start Script (Local)

```bash
./start_server.sh
```

This will:
- Start the FastAPI server on port 8000
- Optionally start Cloudflared tunnel for local testing

## API Endpoints

### Health Check
- `GET /` - Server status
- `GET /health` - Health check

### Task Management

- `POST /a2a/task/generate` - Generate a new task using LLM (green agent uses this)
  ```json
  {
    "task_type": "atomic",  // "atomic" or "compositional"
    "difficulty": "simple",  // "simple" or "hard"
    "task_name": "optional-specific-task",  // Optional: specific task to generate
    "num_tasks": 2  // For compositional tasks
  }
  ```
  Returns a `task_id` that can be used to initialize the task.

- `POST /a2a/task/assign` - Assign a task to a white agent (green agent uses this)
  ```json
  {
    "agent_id": "agent_0",
    "task_type": "atomic",  // "atomic", "compositional", or "predefined"
    "difficulty": "simple",
    "task_name": "optional-task-name",  // For predefined tasks
    "generate_new": true  // Generate new task or use existing
  }
  ```
  This generates/selects a task and initializes it for the white agent.

- `POST /a2a/task/init` - Initialize a new Minecraft task (direct initialization)
  ```json
  {
    "task_name": "mine_diamond_ore",
    "difficulty": "simple",
    "agent_id": "optional-agent-id"
  }
  ```
  For predefined tasks. Use `/a2a/task/assign` for generated tasks.

- `POST /a2a/action` - Execute an action in Minecraft
  ```json
  {
    "agent_id": "agent_0",
    "action": {
      "forward": 1,
      "jump": 0,
      "attack": 0,
      "camera": [0, 0]
    }
  }
  ```

- `POST /a2a/task/reset` - Reset the task environment
  ```json
  {
    "agent_id": "agent_0"
  }
  ```

- `POST /a2a/task/close` - Close agent session
  ```json
  {
    "agent_id": "agent_0"
  }
  ```

### Evaluation
- `POST /a2a/evaluate` - Evaluate a video submission
  - Accepts `video_file` (multipart), `video_url`, or `video_base64`
  - Requires `task_name` form field
  - Returns evaluation scores and feedback

### Information
- `GET /a2a/tasks?difficulty=simple` - List available tasks
- `GET /a2a/agents` - List active agent sessions

## Integration with AgentBeats

1. **Get your public URL**:
   - **Render.com**: Your service URL (e.g., `https://mcu-green-agent.onrender.com`)
   - **Local with Cloudflared**: Check `cloudflared.log` or quick tunnel output

2. **Register with AgentBeats**:
   - Go to https://v2.agentbeats.org/main
   - Login with GitHub
   - Register your green agent with your public URL

3. **AgentBeats will**:
   - Discover your agent via `/.well-known/agent.json`
   - Generate/assign tasks to white agents
   - White agents will use `/a2a/task/init` and `/a2a/action` endpoints
   - Submit videos for evaluation via `/a2a/evaluate`

## Task Configuration

Tasks are defined in YAML files under `task_configs/`:
- `task_configs/simple/` - Simple difficulty tasks
- `task_configs/hard/` - Hard difficulty tasks
- `task_configs/compositional/` - Compositional tasks

Each task file contains:
- `custom_init_commands`: Minecraft commands to set up the environment
- `text`: Task description
- `defaults`: Base configuration

## Evaluation Criteria

Evaluation criteria files are in `auto_eval/criteria_files/`:
- Each task has a corresponding `.txt` file with grading rules
- Evaluation uses GPT-4 Vision to analyze video frames
- Scores are provided across 6 dimensions:
  - Task Progress
  - Action Control
  - Error Recognition and Correction
  - Creative Attempts
  - Task Completion Efficiency
  - Material Selection and Usage

## Important Notes

### MineStudio API Compatibility

The MineStudio API may vary between versions. If you encounter initialization errors, you may need to adjust the `init_task` function in `a2a_server.py`. Common variations:

- `MineStudio(callbacks=[...])` - Direct initialization
- `Simulator(callbacks=[...])` - Using Simulator class
- `MineStudio.create(callbacks=[...])` - Factory method

The code includes fallback logic, but you may need to modify it based on your specific MineStudio version. Check the [MCU repository](https://github.com/CraftJarvis/MCU) for examples of how MineStudio is used in that codebase.

## Troubleshooting

### Server won't start
- Check if port 8000 is available: `lsof -i :8000`
- Check Python version: `python --version` (should be 3.10+)
- Check dependencies: `pip list`

### MineStudio not working
- Verify Java 8 is installed: `java -version`
- Check MineStudio installation: `pip show minestudio`
- Review server logs for errors

### Deployment issues (Render.com)
- Check build logs in Render dashboard
- Verify `OPENAI_API_KEY` is set in environment variables
- Check service logs for runtime errors
- Ensure `render.yaml` is in your repository root

### Local tunneling issues (Cloudflared)
- Verify tunnel is running: `cloudflared tunnel list`
- Check tunnel status: `cloudflared tunnel info mcu-green-agent`
- Review cloudflared logs: `tail -f cloudflared.log`

### Evaluation not working
- Verify OPENAI_API_KEY is set: `echo $OPENAI_API_KEY`
- Check if criteria file exists for the task
- Review server logs for API errors

## Testing the Server

Run the test script to verify your setup:
```bash
python test_server.py
```

This will test:
- Health check endpoint
- Task listing
- Agent listing
- Task initialization (if MineStudio is available)

## Development

### Testing endpoints locally
```bash
# Health check
curl http://localhost:8000/health

# List tasks
curl http://localhost:8000/a2a/tasks

# Initialize task
curl -X POST http://localhost:8000/a2a/task/init \
  -H "Content-Type: application/json" \
  -d '{"task_name": "mine_diamond_ore", "difficulty": "simple"}'
```

### Adding new tasks
1. Create YAML file in `task_configs/simple/` or `task_configs/hard/`
2. Create corresponding criteria file in `auto_eval/criteria_files/`
3. Restart server

## File Structure

```
.
├── a2a_server.py              # Main FastAPI server
├── requirements.txt           # Python dependencies
├── cloudflared_config.yml     # Cloudflared tunnel config
├── setup_cloudflared.sh       # Cloudflared setup script
├── start_server.sh            # Server startup script
├── auto_eval/                 # Evaluation logic
│   ├── eval.py               # Video evaluation functions
│   ├── criteria_files/       # Task evaluation criteria
│   └── prompt/               # VLM prompts
├── task_configs/             # Task configurations
│   ├── simple/               # Simple difficulty tasks
│   ├── hard/                 # Hard difficulty tasks
│   └── compositional/        # Compositional tasks
└── utility/                   # Utility functions
    ├── task_call.py          # Task callback
    ├── record_call.py       # Video recording callback
    └── read_conf.py         # Config reader
```

## License

See the main repository license.

## Support

For issues related to:
- **MineStudio**: Check [MCU repository](https://github.com/CraftJarvis/MCU)
- **AgentBeats**: Check [AgentBeats platform](https://v2.agentbeats.org/main)
- **This server**: Open an issue in this repository

