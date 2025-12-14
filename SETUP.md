# Setup & Integration Guide

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
# Navigate to cs194 folder
cd /path/to/mcu/cs194

# Create conda environment
conda create -n minecraft-benchmark python=3.10 -y
conda activate minecraft-benchmark

# Install Java (required for MineStudio)
conda install --channel=conda-forge openjdk=8 -y

# Install Python dependencies
pip install -r requirements.txt

# Install MineStudio
pip install minestudio
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

Add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Test Installation

```bash
# Show benchmark info
python main.py info

# List available tasks
python main.py list-tasks --difficulty simple

# Run a quick test (mock mode if MineStudio not fully configured)
python main.py launch --task-name collect_wood --difficulty simple
```

## Detailed Setup

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: Recommended for MineStudio (CUDA-capable)
- **Python**: 3.10 or higher
- **Java**: OpenJDK 8 (installed via conda)

### MineStudio Configuration

If you encounter display issues with MineStudio:

#### Option 1: Headless Mode (Linux servers)
```bash
# Install Xvfb for virtual display
sudo apt-get install xvfb

# Run with virtual display
xvfb-run -a python main.py launch --task-name collect_wood
```

#### Option 2: Docker (Recommended for production)
```bash
# Build Docker image (create Dockerfile first)
docker build -t minecraft-benchmark .

# Run container
docker run --gpus all -p 9001:9001 -p 9002:9002 minecraft-benchmark
```

#### Option 3: Local Display (macOS/Windows)
MineStudio should work out of the box on systems with displays.

### Agent Model Configuration

The white agent uses VPT (Video Pre-Training) models by default. To use different models:

#### Download VPT Models

```bash
# Create pretrained directory
mkdir -p pretrained

# Download foundation model (2x)
# Visit: https://huggingface.co/OpenDILabCommunity/VPT
# Download:
#   - foundation-model-2x.model
#   - foundation-model-2x.weights

# Place in pretrained/ folder
```

#### Use Custom Models

Edit `white_agent/agent.py`:
```python
# Around line 120, change model paths:
policy = load_vpt_policy(
    model_path="/path/to/your/model.model",
    weights_path="/path/to/your/weights.weights"
).to("cuda")
```

## AgentBeats Integration

### Registering Green Agent on AgentBeats

1. **Start your green agent locally:**
   ```bash
   python main.py green --host 0.0.0.0 --port 9001
   ```

2. **Make it publicly accessible** (choose one):

   **Option A: ngrok (Development)**
   ```bash
   # Install ngrok: https://ngrok.com/
   ngrok http 9001

   # Copy the public URL (e.g., https://abc123.ngrok.io)
   ```

   **Option B: Cloud Deployment (Production)**
   Deploy to AWS, GCP, or Azure with public IP.

3. **Register on AgentBeats:**
   - Visit: https://v2.agentbeats.org/main
   - Click "Register Agent"
   - Provide your public URL (e.g., https://abc123.ngrok.io)
   - AgentBeats will fetch your agent card automatically

### Registering White Agent

Similar process as green agent:
```bash
# Start white agent
python main.py white --host 0.0.0.0 --port 9002

# Expose with ngrok or cloud
ngrok http 9002

# Register on AgentBeats
```

### Assessment Request Format

When integrated with AgentBeats, your green agent will receive requests like:

```xml
<white_agent_url>
https://your-white-agent.ngrok.io/
</white_agent_url>
<task_name>
build_a_house
</task_name>
<difficulty>
simple
</difficulty>
<max_steps>
12000
</max_steps>
```

The green agent automatically:
1. Parses the request
2. Finds the task config and criteria
3. Sends task to white agent
4. Receives video artifact
5. Evaluates with VLM
6. Returns scores to AgentBeats

## Testing & Validation

### Test Green Agent Independently

```bash
# Terminal 1: Start green agent
python main.py green

# Terminal 2: Test with curl
curl -X POST http://localhost:9001/card
# Should return agent card JSON
```

### Test White Agent Independently

```bash
# Terminal 1: Start white agent
python main.py white

# Terminal 2: Test with curl
curl -X POST http://localhost:9002/card
# Should return agent card JSON
```

### Test Complete Integration

```bash
# Run full evaluation (starts both agents)
python main.py launch --task-name collect_wood --difficulty simple
```

Expected output:
```
================================================================================
MINECRAFT BENCHMARK EVALUATION LAUNCHER
================================================================================

[1/4] Launching green agent at localhost:9001...
Green agent is ready!

[2/4] Launching white agent at localhost:9002...
White agent is ready!

[3/4] Sending assessment request to green agent...
Task: collect_wood
Difficulty: simple
Max Steps: 12000

[4/4] Assessment Complete!
================================================================================
RESULTS:
================================================================================
Assessment Complete!

Task: collect_wood (simple)
Task Completed: True
Steps Taken: 12000

Evaluation Scores:
{
  "Task Progress": 8,
  "Action Control": 7,
  ...
}
```

## Troubleshooting

### Issue: "MineStudio not available"

**Solution:**
```bash
# Reinstall MineStudio
pip uninstall minestudio
pip install minestudio

# Verify Java
java -version  # Should show Java 8

# Check display
echo $DISPLAY  # Should show :0 or similar
```

### Issue: "OpenAI API rate limit"

**Solution:**
```bash
# Edit auto_eval/eval.py to add delays
# Around line 22-30, add:
import time
time.sleep(1)  # Wait 1 second between API calls
```

### Issue: "Port already in use"

**Solution:**
```bash
# Find process using port
lsof -i :9001  # or :9002

# Kill process
kill -9 <PID>

# Or use different ports
python main.py green --port 9003
python main.py white --port 9004
```

### Issue: "Task config not found"

**Solution:**
```bash
# Verify task exists
python main.py list-tasks --difficulty simple

# Check task_configs directory structure
ls task_configs/simple/
ls task_configs/hard/

# Ensure task name matches exactly (case-sensitive)
```

### Issue: "Criteria file not found"

**Solution:**
```bash
# List available criteria files
ls auto_eval/criteria_files/

# Task name must match criteria filename
# e.g., task "build_a_house" needs "build_a_house.txt"
```

## Advanced Configuration

### Custom Evaluation Prompts

Edit `auto_eval/prompt/single_rating_prompt.txt` to customize:
- Scoring guidelines
- Output format
- Evaluation focus areas

### Batch Processing

Create a task list file:
```bash
# tasks.txt
collect_wood
build_a_house
craft_ladder
mine_diamond_ore
```

Run batch:
```bash
python main.py batch --tasks-file tasks.txt --difficulty simple
```

### Multi-GPU Setup

For parallel white agents:

```python
# launcher.py - modify to spawn multiple white agents
# Each on different GPU
white_agents = [
    ("cuda:0", 9002),
    ("cuda:1", 9003),
    ("cuda:2", 9004),
]
```

## Production Deployment

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 python3-pip openjdk-8-jdk xvfb

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 9001 9002

CMD ["python3", "main.py", "launch"]
```

Build and run:
```bash
docker build -t minecraft-benchmark .
docker run --gpus all -p 9001:9001 -p 9002:9002 minecraft-benchmark
```

### Kubernetes Deployment

Create deployment YAML for green and white agents with proper resource allocation.

### Monitoring & Logging

Add logging configuration:
```python
# Add to main.py
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('benchmark.log'),
        logging.StreamHandler()
    ]
)
```

## Next Steps

1. ✅ Complete setup following this guide
2. ✅ Test with a single task locally
3. ✅ Run batch evaluation on your task set
4. ✅ Deploy agents with public URLs
5. ✅ Register on AgentBeats platform
6. ✅ Participate in AgentX-AgentBeats competition!

## Support Resources

- **AgentBeats Docs**: https://docs.agentbeats.org/
- **A2A Protocol**: https://a2a-protocol.org/
- **MineStudio**: https://craftjarvis.github.io/MineStudio/
- **OpenAI API**: https://platform.openai.com/docs

For project-specific issues, check the main README.md or open an issue.
