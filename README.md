# Minecraft Agent Benchmark - CS194

A comprehensive benchmark for evaluating Minecraft agents using VLM-based video assessment, implementing the A2A protocol for AgentBeats integration.

## Overview

This benchmark evaluates Minecraft agents across **80+ atomic tasks** and **20+ compositional tasks** spanning 10 categories. Each task is assessed using Vision-Language Models (VLMs) analyzing video recordings across 6 evaluation dimensions.

### Features

- **🟢 Green Agent (Evaluator)**: VLM-based assessment using GPT-4V for video analysis
- **⚪ White Agent (Task Executor)**: MineStudio-based Minecraft task execution
- **🔄 A2A Protocol**: Standardized agent-to-agent communication
- **🌐 AgentBeats Ready**: Full integration with AgentBeats platform
- **📊 Comprehensive Evaluation**: 6-dimensional scoring across diverse tasks
- **🎯 Dual Difficulty**: Simple and Hard modes for each task

## Project Structure

```
cs194/
├── green_agent/                # Green agent (evaluator)
│   ├── agent.py               # A2A server implementation
│   ├── minecraft_green_agent.toml  # Agent card
│   └── __init__.py
├── white_agent/               # White agent (task executor)
│   ├── agent.py              # MineStudio integration
│   ├── minecraft_white_agent.toml  # Agent card
│   └── __init__.py
├── auto_eval/                 # Evaluation module
│   ├── criteria_files/       # Task criteria (82 files)
│   ├── prompt/               # VLM prompts
│   ├── eval.py              # Core evaluation logic
│   └── vlm_rating_res/      # Evaluation results
├── task_configs/             # Task configurations
│   ├── simple/              # Simple difficulty (82 tasks)
│   ├── hard/                # Hard difficulty (82 tasks)
│   └── compositional/       # Compositional tasks (18 tasks)
├── utils/                    # Utility modules
│   ├── a2a_utils.py        # A2A protocol utilities
│   └── task_utils.py       # Task configuration utilities
├── output/                   # Video outputs (generated)
├── launcher.py              # Orchestration logic
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
└── .env.example            # Environment variables template
```

## Installation

### Prerequisites

1. **Python 3.10+**
2. **Conda** (for MineStudio dependencies)
3. **OpenAI API Key** (for VLM evaluation)

### Setup Instructions

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/mcu/cs194
   ```

2. **Create conda environment:**
   ```bash
   conda create -n minecraft-benchmark python=3.10 -y
   conda activate minecraft-benchmark
   conda install --channel=conda-forge openjdk=8 -y
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install MineStudio:**
   ```bash
   pip install minestudio
   ```

5. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Usage

### Quick Start

Run a single task evaluation:
```bash
python main.py launch --task-name collect_wood --difficulty simple
```

### CLI Commands

#### Start Agents Individually

```bash
# Start green agent (evaluator)
python main.py green --host localhost --port 9001

# In another terminal, start white agent (executor)
python main.py white --host localhost --port 9002
```

#### Launch Complete Evaluation

```bash
# Evaluate a specific task
python main.py launch \
  --task-name build_a_house \
  --difficulty simple \
  --max-steps 12000

# See all options
python main.py launch --help
```

#### Batch Evaluation

```bash
# Evaluate all tasks for a difficulty
python main.py batch --all-tasks --difficulty simple

# Evaluate tasks from a file (one task name per line)
python main.py batch --tasks-file tasks.txt --difficulty hard
```

#### List Available Tasks

```bash
# List tasks for a difficulty
python main.py list-tasks --difficulty simple
```

#### Show Benchmark Info

```bash
python main.py info
```

## Evaluation Criteria

Each task is evaluated across **6 dimensions**:

1. **Task Progress** (0-10): Completion of key task steps
2. **Action Control** (0-10): Precision and relevance of actions
3. **Error Recognition & Correction** (0-10): Ability to identify and fix mistakes
4. **Creative Attempts** (0-10): Innovative problem-solving approaches
5. **Task Completion Efficiency** (0-10): Speed and resource management
6. **Material Selection & Usage** (0-10): Appropriate tool and material usage

## Task Categories

The benchmark includes tasks across 10 categories:

- **⚔️ Combat**: Fighting mobs, hunting animals (9 tasks)
- **🛠️ Crafting**: Creating tools, items, blocks (10 tasks)
- **⛏️ Mining & Collecting**: Extracting resources (8 tasks)
- **🏗️ Building**: Constructing structures (13 tasks)
- **🧰 Tool Use**: Using Minecraft tools (10 tasks)
- **🧭 Exploration**: Navigating the world (5 tasks)
- **🌀 Motion**: Movement and positioning (4 tasks)
- **🖼️ Decoration**: Aesthetic improvements (6 tasks)
- **🧲 Finding**: Locating blocks/biomes/structures (9 tasks)
- **🪤 Trapping**: Capturing entities (4 tasks)

Plus 20+ compositional tasks combining multiple categories.

## A2A Protocol & AgentBeats Integration

Both green and white agents implement the **A2A (Agent-to-Agent) Protocol**, making them compatible with the **AgentBeats platform**.

### Green Agent Card

- **Name**: `minecraft_green_agent`
- **Skill**: `minecraft_assessment`
- **Capabilities**: VLM-based video evaluation across 80+ tasks
- **Port**: 9001 (default)

### White Agent Card

- **Name**: `minecraft_white_agent`
- **Skill**: `minecraft_task_execution`
- **Capabilities**: MineStudio-based task execution with video recording
- **Port**: 9002 (default)

### Integration Example

```python
# Green agent receives assessment request from AgentBeats
assessment_request = """
<white_agent_url>http://localhost:9002/</white_agent_url>
<task_name>build_a_house</task_name>
<difficulty>simple</difficulty>
<max_steps>12000</max_steps>
"""

# Green agent coordinates with white agent via A2A
# White agent executes task, returns video
# Green agent evaluates video, returns scores
```

## Architecture

### Option A: Artifact Submission (Implemented)

1. **Green Agent** receives assessment_request from AgentBeats
2. **Green Agent** → **White Agent**: "Execute task X"
3. **White Agent**: Runs MineStudio, generates video, encodes as base64
4. **White Agent** → **Green Agent**: Returns video artifact
5. **Green Agent**: Evaluates video with VLM, returns JSON scores

### Benefits

- Clean separation of concerns
- Easier debugging and testing
- Better resource allocation
- Simulator-agnostic green agent

## Development

### Project Dependencies

- **a2a-sdk**: A2A protocol implementation
- **uvicorn**: ASGI server for agents
- **openai**: GPT-4V for video evaluation
- **opencv-python**: Video processing
- **minestudio**: Minecraft simulation environment
- **typer**: CLI framework

### Extending the Benchmark

#### Add New Tasks

1. Create task YAML in `task_configs/simple/` or `task_configs/hard/`:
   ```yaml
   custom_init_commands:
   - /give @s minecraft:diamond_pickaxe 1
   text: Mine 10 diamond ore blocks
   ```

2. Create criteria file in `auto_eval/criteria_files/`:
   ```
   **Task Progress: the key factors/steps for completing the task**
   - whether the agent locates diamond ore
   - whether the agent successfully mines the ore
   ...
   ```

#### Customize Evaluation

Modify `auto_eval/eval.py` to adjust:
- Scoring criteria
- VLM prompts
- Frame sampling rate
- Evaluation metrics

## Troubleshooting

### Common Issues

1. **MineStudio not found**
   - Ensure you've installed with: `pip install minestudio`
   - Check that Java 8 is installed: `java -version`

2. **OpenAI API errors**
   - Verify `.env` has valid `OPENAI_API_KEY`
   - Check API quota and billing

3. **Agent connection timeout**
   - Ensure ports 9001 and 9002 are available
   - Check firewall settings
   - Increase timeout in `launcher.py`

4. **Video generation fails**
   - Check MineStudio dependencies (OpenJDK, display)
   - Review white agent logs for errors
   - Verify task config is valid YAML

## Results & Outputs

### Video Recordings

Generated videos are saved to:
```
output/
└── {task_name}/
    └── episode_{timestamp}.mp4
```

### Evaluation Results

VLM evaluation results saved to:
```
vlm_rating_res/
└── {task_name}.json
```

Example result:
```json
{
  "Task Progress": 8,
  "Action Control": 7,
  "Error Recognition and Correction": 6,
  "Creative Attempts": 5,
  "Task Completion Efficiency": 7,
  "Material Selection and Usage": 9,
  "video_path": "./output/build_a_house/episode_123456.mp4",
  "task_name": "build_a_house"
}
```

## Citation

If you use this benchmark, please cite:

```bibtex
@misc{minecraft-benchmark-cs194,
  title={Minecraft Agent Benchmark with A2A Integration},
  author={CS194 Project},
  year={2025},
  note={AgentBeats-compatible evaluation framework}
}
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear description

## Support

For issues or questions:
- Open an issue on GitHub
- Check AgentBeats documentation: https://docs.agentbeats.org/
- Review A2A protocol docs: https://a2a-protocol.org/

---

Built for the CS194 Agentic AI course at UC Berkeley
