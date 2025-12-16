# Minecraft Agent Benchmark - CS194

A comprehensive benchmark for evaluating Minecraft agents using VLM-based video assessment with A2A protocol integration for AgentBeats.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Deployment](#deployment)
- [Task Categories](#task-categories)
- [Evaluation Criteria](#evaluation-criteria)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

## Overview

This benchmark evaluates Minecraft agents across **80+ atomic tasks** and **20+ compositional tasks** spanning 10 categories. Each task is assessed using Vision-Language Models (VLMs) analyzing video recordings across 6 evaluation dimensions.

### Key Components

- **🟢 Green Agent (Evaluator)**: VLM-based assessment using GPT-4V/GPT-5-mini for video analysis
- **⚪ White Agent (Task Executor)**: Hybrid agent combining LLM planning with VPT execution
- **🔄 A2A Protocol**: Standardized agent-to-agent communication
- **🌐 AgentBeats Ready**: Full integration with AgentBeats platform

## Quick Start

### Prerequisites

- Python 3.10+
- Conda installed
- OpenAI API key

### 5-Minute Setup

```bash
# 1. Navigate to project directory
cd /path/to/mcu/cs194

# 2. Create conda environment
conda create -n minecraft-benchmark python=3.10 -y
conda activate minecraft-benchmark
conda install --channel=conda-forge openjdk=8 -y

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Run your first evaluation
python main.py launch --task-name collect_wood --difficulty simple
```

### What Just Happened?

1. **Green agent** (evaluator) started
2. **White agent** (task executor) started
3. White agent executed Minecraft task with hybrid LLM+VPT policy
4. Video was recorded and saved
5. Green agent evaluated video with GPT-4V
6. Scores returned across 6 dimensions

## Features

### Green Agent (Evaluator)
- VLM-based video evaluation using GPT-4V
- 6-dimensional scoring framework
- Support for 80+ tasks across 10 categories
- A2A protocol for agent communication
- Flexible video input (MP4, base64-encoded)

### White Agent (Task Executor)
- **Hybrid Architecture**: LLM planning + VPT execution
- MineStudio-based Minecraft simulation
- Video recording with frame capture
- Custom initialization commands
- Mock mode for testing without simulator

### Hybrid Agent Architecture

The white agent uses a **hybrid approach** combining the strengths of both LLMs and VPT:

#### Architecture Components

1. **LLM Planner (GPT-4)**: High-level task decomposition
   - Analyzes task requirements
   - Creates step-by-step plans with reasoning
   - Monitors progress and adapts strategy
   - Provides interpretable decision-making

2. **State Manager**: Tracks agent progress
   - Inventory tracking
   - Position monitoring
   - Subtask completion status
   - Action history

3. **Action Mapper**: Translates plans to actions
   - Converts subtasks to primitive actions
   - Maps high-level goals to Minecraft commands

4. **VPT Executor**: Low-level control
   - Executes primitive actions in Minecraft
   - Handles pixel-to-action mapping
   - Provides smooth, natural gameplay

#### Why Hybrid?

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| **LLM-only** | Interpretable, flexible, good at planning | Expensive, slow, struggles with low-level control |
| **VPT-only** | Fast, efficient, smooth gameplay | Black box, no reasoning, hard to debug |
| **Hybrid (Ours)** | Best of both: interpretable planning + efficient execution | More complex implementation |

#### Example Workflow

For task "Collect 10 wood blocks":

```
1. LLM Planning:
   └─> Reasoning: "Need to find trees, then mine them with correct tool"
   └─> Subtasks: ["Locate forest", "Approach tree", "Mine wood", "Collect items"]

2. Execution Loop:
   For each subtask:
     ├─> LLM: Decompose subtask into actions
     ├─> VPT: Execute actions in Minecraft
     └─> State Manager: Track progress

3. Results:
   └─> Reasoning log saved for documentation
   └─> Video recorded for evaluation
```

## Architecture

### System Overview

```
┌─────────────┐
│ AgentBeats  │
│  Platform   │
└──────┬──────┘
       │ Assessment Request
       ↓
┌────────────────────────────────────────┐
│  Green Agent (Evaluator)               │
│  - Receives assessment requests        │
│  - Coordinates with white agent        │
│  - Evaluates videos with VLM           │
└──────┬─────────────────────────────────┘
       │ Task Request (A2A)
       ↓
┌────────────────────────────────────────┐
│  White Agent (Task Executor)           │
│  ┌──────────────────────────────────┐  │
│  │  Hybrid Policy Architecture      │  │
│  │  ┌────────────┐  ┌─────────────┐ │  │
│  │  │ LLM Planner│→ │ VPT Executor│ │  │
│  │  └────────────┘  └─────────────┘ │  │
│  │        ↓              ↓           │  │
│  │  ┌─────────────────────────────┐ │  │
│  │  │    State Manager            │ │  │
│  │  └─────────────────────────────┘ │  │
│  └──────────────────────────────────┘  │
│           ↓                             │
│  ┌──────────────────────────────────┐  │
│  │      MineStudio Simulator        │  │
│  └──────────────────────────────────┘  │
│           ↓                             │
│     Video Recording (MP4)               │
└──────┬─────────────────────────────────┘
       │ Video Artifact
       ↓
┌────────────────────────────────────────┐
│  VLM Evaluation (GPT-4V)               │
│  - Analyzes video frames               │
│  - Scores across 6 dimensions          │
│  - Returns JSON results                │
└────────────────────────────────────────┘
```

### A2A Protocol Flow

```
AgentBeats → Green Agent:
<white_agent_url>https://white-agent.example.com/</white_agent_url>
<task_name>collect_wood</task_name>
<difficulty>simple</difficulty>
<max_steps>12000</max_steps>

Green Agent → White Agent:
<task_request>
Task Name: collect_wood
Difficulty: simple
Description: Collect 10 wood blocks
Max Steps: 12000
Task Configuration Path: /path/to/config.yaml
</task_request>

White Agent → Green Agent:
<video_artifact>
{
  "video_path": "/path/to/video.mp4",
  "video_base64": "...",
  "task_name": "collect_wood",
  "steps_taken": 8543,
  "completed": true
}
</video_artifact>

Green Agent → AgentBeats:
{
  "task_name": "collect_wood",
  "evaluation_scores": {
    "Task Progress": 8,
    "Action Control": 7,
    ...
  },
  "timestamp": 1234567890.123
}
```

## Installation

### Standard Setup

```bash
# 1. Create environment
conda create -n minecraft-benchmark python=3.10 -y
conda activate minecraft-benchmark

# 2. Install Java for Minecraft
conda install --channel=conda-forge openjdk=8 -y

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install MineStudio (optional, for full functionality)
pip install minestudio

# 5. Configure environment
cp .env.example .env
# Edit .env and add:
# OPENAI_API_KEY=sk-your-key-here
```

### For AgentBeats Deployment

When deploying with AgentBeats earthshaker controllers:

```bash
# 1. Set up controller environment
conda create -n agentbeats-controller python=3.10 -y
conda activate agentbeats-controller
pip install agentbeats

# 2. Set up agent environment
conda create -n minecraft-benchmark python=3.10 -y
conda activate minecraft-benchmark
pip install -r requirements.txt

# 3. Configure controller run.sh scripts
# Set OPENAI_API_KEY environment variable before running
export OPENAI_API_KEY=sk-your-key-here

# 4. Start controllers
cd green_controller && agentbeats run_ctrl
cd white_controller && agentbeats run_ctrl
```

**IMPORTANT**: The controller `run.sh` scripts require `OPENAI_API_KEY` to be set in your environment before running. Never commit API keys to the repository.

### For Headless Servers

```bash
# Install virtual display for video processing
sudo apt-get install xvfb

# Set display in run.sh or before running
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
```

## Usage

### CLI Commands

#### Single Task Evaluation

```bash
python main.py launch \
  --task-name collect_wood \
  --difficulty simple \
  --max-steps 12000
```

#### Batch Evaluation

```bash
# Evaluate all tasks
python main.py batch --all-tasks --difficulty simple

# Evaluate from file (one task name per line)
python main.py batch --tasks-file tasks.txt --difficulty hard
```

#### List Available Tasks

```bash
python main.py list-tasks --difficulty simple
```

#### Start Agents Individually

```bash
# Terminal 1: Start green agent
python main.py green --host localhost --port 9001

# Terminal 2: Start white agent
python main.py white --host localhost --port 9002
```

#### Show Benchmark Info

```bash
python main.py info
```

## Deployment

### Option 1: Local Testing

Use the CLI commands above for local development and testing.

### Option 2: AgentBeats with Earthshaker Controllers

```bash
# 1. Activate controller environment
conda activate agentbeats-controller

# 2. Set your API key
export OPENAI_API_KEY=sk-your-key-here

# 3. Start green agent controller
cd green_controller
agentbeats run_ctrl

# 4. Start white agent controller (in another terminal)
cd white_controller
agentbeats run_ctrl
```

The earthshaker controller will:
- Read `run.sh` to launch the agent
- Set `$HOST`, `$AGENT_PORT`, and `$AGENT_URL` automatically
- Create the `/to_agent/{id}/` routing structure
- Provide a management UI

### Option 3: Tailscale Funnel (Cloudflare Alternative)

For deployments requiring longer timeouts (>100s), use Tailscale Funnel:

```bash
# 1. Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Authenticate
sudo tailscale up

# 3. Start agents locally
python main.py green --host localhost --port 8010
python main.py white --host localhost --port 8011

# 4. Expose via Tailscale Funnel
sudo tailscale serve --bg http://localhost:8010
sudo tailscale serve --bg --set-path=/white http://localhost:8011
sudo tailscale funnel --bg 443

# Your agents are now publicly accessible:
# Green: https://your-machine.tail4a0ed7.ts.net/
# White: https://your-machine.tail4a0ed7.ts.net/white
```

**Benefits of Tailscale Funnel:**
- No timeout limits (unlike Cloudflare's 100s)
- Free for personal use
- Automatic HTTPS
- No DNS configuration needed

### AgentBeats Registration

Once your agents are publicly accessible:

1. Visit https://v2.agentbeats.org/main
2. Click "Register Agent"
3. Provide your agent URLs:
   - Green: `https://your-domain/` (or Tailscale URL)
   - White: `https://your-domain/white` (or Tailscale URL)
4. AgentBeats fetches agent cards automatically
5. Your benchmark is now live!

## Task Categories

The benchmark includes **80+ atomic tasks** and **20+ compositional tasks** across 10 categories:

### Categories

- **⚔️ Combat** (9 tasks): Fighting mobs, hunting animals
  - Examples: `attack_cow`, `kill_zombie`, `hunt_spider`

- **🛠️ Crafting** (10 tasks): Creating tools, items, blocks
  - Examples: `craft_pickaxe`, `craft_sword`, `craft_chest`

- **⛏️ Mining & Collecting** (8 tasks): Extracting resources
  - Examples: `collect_wood`, `mine_stone`, `mine_diamond`

- **🏗️ Building** (13 tasks): Constructing structures
  - Examples: `build_house`, `build_bridge`, `build_tower`

- **🧰 Tool Use** (10 tasks): Using Minecraft tools
  - Examples: `use_crafting_table`, `use_furnace`, `use_axe`

- **🧭 Exploration** (5 tasks): Navigating the world
  - Examples: `find_village`, `explore_cave`, `locate_biome`

- **🌀 Motion** (4 tasks): Movement and positioning
  - Examples: `jump_gap`, `climb_ladder`, `swim_underwater`

- **🖼️ Decoration** (6 tasks): Aesthetic improvements
  - Examples: `place_torch`, `arrange_furniture`, `decorate_room`

- **🧲 Finding** (9 tasks): Locating blocks/biomes/structures
  - Examples: `find_diamond`, `find_village`, `find_nether_fortress`

- **🪤 Trapping** (4 tasks): Capturing entities
  - Examples: `trap_animal`, `build_trap`, `capture_mob`

### Difficulty Levels

Each task comes in multiple difficulties:

- **Simple**: Basic version with helpful initialization commands
- **Hard**: More challenging with fewer resources
- **Compositional**: Multi-step tasks combining multiple categories

## Evaluation Criteria

Each task is evaluated across **6 dimensions** (0-10 scale):

1. **Task Progress**: Completion of key task steps
   - Did the agent make measurable progress?
   - Were critical milestones reached?

2. **Action Control**: Precision and relevance of actions
   - Were actions appropriate for the task?
   - Was control smooth and accurate?

3. **Error Recognition & Correction**: Ability to identify and fix mistakes
   - Did the agent detect errors?
   - Were corrective actions taken?

4. **Creative Attempts**: Innovative problem-solving approaches
   - Did the agent try novel strategies?
   - Were creative solutions explored?

5. **Task Completion Efficiency**: Speed and resource management
   - Was the task completed quickly?
   - Were resources used efficiently?

6. **Material Selection & Usage**: Appropriate tool and material usage
   - Were correct tools selected?
   - Were materials used properly?

### Example Evaluation Output

```json
{
  "task_name": "build_a_house",
  "difficulty": "simple",
  "task_completed": true,
  "steps_taken": 8543,
  "evaluation_scores": {
    "Task Progress": 8,
    "Action Control": 7,
    "Error Recognition and Correction": 6,
    "Creative Attempts": 5,
    "Task Completion Efficiency": 7,
    "Material Selection and Usage": 9
  },
  "video_path": "./output/build_a_house/episode_123456.mp4",
  "timestamp": 1234567890.123
}
```

## Troubleshooting

### Common Issues

#### "MineStudio not available" / Running in Mock Mode

**Normal for first test.** The white agent will generate a placeholder video.

**For full functionality:**
```bash
pip install minestudio
```

#### "OpenAI API error" / "OPENAI_API_KEY not set"

**Solution 1 - Environment variable:**
```bash
export OPENAI_API_KEY=sk-your-key-here
```

**Solution 2 - .env file:**
```bash
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

**Solution 3 - Check configuration:**
```bash
cat .env  # Should show: OPENAI_API_KEY=sk-...
```

#### "Port already in use"

**Solution: Use different ports**
```bash
python main.py launch --green-port 9003 --white-port 9004
```

#### "Task config not found"

**Solution: Verify task name and difficulty**
```bash
# List available tasks
python main.py list-tasks --difficulty simple

# Check task configs directory
ls task_configs/simple/
```

#### "Agent connection timeout"

**Possible causes:**
- Firewall blocking ports
- Agents not started
- Wrong URLs

**Solution:**
```bash
# Check if agents are running
curl http://localhost:9001/card  # Green agent
curl http://localhost:9002/card  # White agent

# Check firewall
sudo ufw status
```

#### "Video generation fails"

**Requirements for video generation:**
- MineStudio installed
- Java 8 installed: `java -version`
- Display available (use Xvfb for headless)

**Solution:**
```bash
# For headless servers
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
```

#### Cloudflare 524 Timeout Errors

**Problem:** Tasks taking >100 seconds hit Cloudflare proxy timeout

**Solution:** Use Tailscale Funnel (see Deployment section) or disable Cloudflare proxy (gray cloud in DNS)

## Project Structure

```
cs194/
├── green_agent/                # Green agent (evaluator)
│   ├── agent.py               # A2A server implementation
│   ├── minecraft_green_agent.toml  # Agent card
│   └── __init__.py
│
├── white_agent/               # White agent (task executor)
│   ├── agent.py              # Hybrid agent + MineStudio
│   ├── hybrid_policy.py      # Hybrid LLM+VPT policy
│   ├── minecraft_white_agent.toml  # Agent card
│   └── __init__.py
│
├── utils/                     # Utility modules
│   ├── a2a_utils.py          # A2A protocol helpers
│   ├── task_utils.py         # Task configuration helpers
│   └── __init__.py
│
├── auto_eval/                 # Evaluation module
│   ├── criteria_files/       # Task criteria (82 files)
│   │   ├── collect_wood.txt
│   │   ├── build_house.txt
│   │   └── ...
│   ├── prompt/               # VLM prompts
│   │   └── single_rating_prompt.txt
│   ├── eval.py              # Core VLM evaluation logic
│   └── vlm_rating_res/      # Evaluation results (generated)
│
├── task_configs/             # Task configurations (182 files)
│   ├── simple/              # 82 simple tasks (YAML)
│   ├── hard/                # 82 hard tasks (YAML)
│   └── compositional/       # 18 compositional tasks (YAML)
│
├── output/                   # Video outputs (generated)
│   └── {task_name}/
│       └── episode_{timestamp}.mp4
│
├── green_controller/         # AgentBeats controller for green agent
│   ├── run.sh               # Controller launch script
│   └── README.md            # Controller instructions
│
├── white_controller/         # AgentBeats controller for white agent
│   ├── run.sh               # Controller launch script
│   └── README.md            # Controller instructions
│
├── launcher.py              # Orchestration logic
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git configuration
├── run_green.sh            # Standalone green agent script
├── run_white.sh            # Standalone white agent script
└── README.md               # This file
```

### Key Files

- **main.py**: CLI interface for all operations
- **launcher.py**: Orchestrates multi-agent evaluation
- **green_agent/agent.py**: VLM-based evaluator with A2A
- **white_agent/agent.py**: Hybrid agent with MineStudio integration
- **white_agent/hybrid_policy.py**: LLM planner + VPT executor
- **utils/a2a_utils.py**: A2A communication helpers
- **auto_eval/eval.py**: Core VLM evaluation logic

## Dependencies

### Python Packages

```
a2a-sdk[http-server]>=0.3.8   # A2A protocol
uvicorn>=0.37.0                # ASGI web server
typer>=0.19.2                  # CLI framework
openai>=1.0.0                  # VLM API (GPT-4V/GPT-5-mini)
opencv-python>=4.8.0           # Video processing
pyyaml>=6.0                    # YAML parsing
httpx>=0.25.0                  # HTTP client
minestudio (optional)          # Minecraft simulation
```

### System Dependencies

```
openjdk-8                      # Java for Minecraft
xvfb (optional)                # Virtual display for headless
cuda (optional)                # GPU acceleration for VPT
```

## Performance Notes

### Resource Requirements

**Green Agent:**
- CPU: Low (mainly API calls)
- RAM: ~500MB
- GPU: Not required
- Network: OpenAI API access

**White Agent:**
- CPU: Medium (video encoding)
- RAM: ~4GB (MineStudio + VPT)
- GPU: Recommended for VPT execution
- Disk: ~100MB per video

### Timing Estimates

- **Task Execution**: 2-10 minutes (varies by task complexity)
- **Video Encoding**: 10-30 seconds
- **VLM Evaluation**: 30-60 seconds (API latency)
- **Total per Task**: ~3-12 minutes

**Batch Processing:**
- 10 tasks: ~30-120 minutes
- 82 tasks (full benchmark): ~4-16 hours

## Citation

If you use this benchmark in your research, please cite:

```bibtex
@misc{minecraft-benchmark-cs194,
  title={Minecraft Agent Benchmark with Hybrid Architecture and A2A Integration},
  author={CS194 Project},
  year={2025},
  note={AgentBeats-compatible evaluation framework with LLM+VPT hybrid agents}
}
```

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Check this README first
- Review controller README files in `green_controller/` and `white_controller/`
- AgentBeats documentation: https://docs.agentbeats.org/
- A2A protocol docs: https://a2a-protocol.org/

---

**Built for the CS194 Agentic AI course at UC Berkeley**

**Status**: Ready for deployment ✅
