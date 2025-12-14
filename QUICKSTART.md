# Quick Start Guide - 5 Minutes to First Evaluation

## Prerequisites

- Python 3.10+
- Conda installed
- OpenAI API key

## Setup (2 minutes)

```bash
# 1. Navigate to cs194
cd /path/to/mcu/cs194

# 2. Create environment
conda create -n minecraft-benchmark python=3.10 -y
conda activate minecraft-benchmark
conda install --channel=conda-forge openjdk=8 -y

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure OpenAI API key
cp .env.example .env
echo "OPENAI_API_KEY=your-key-here" > .env
```

## First Test (3 minutes)

```bash
# Run single task evaluation
python main.py launch --task-name collect_wood --difficulty simple
```

**Expected Output:**
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
{
  "Task Progress": 8,
  "Action Control": 7,
  ...
}
```

## What Just Happened?

1. **Green agent** started (evaluator)
2. **White agent** started (task executor)
3. White agent executed Minecraft task
4. Video was recorded and saved
5. Green agent evaluated video with GPT-4V
6. Scores returned across 6 dimensions

## Next Steps

### List All Tasks
```bash
python main.py list-tasks --difficulty simple
```

### Run Different Task
```bash
python main.py launch --task-name build_a_house --difficulty simple
```

### Batch Evaluation
```bash
python main.py batch --all-tasks --difficulty simple
```

### Get Help
```bash
python main.py --help
python main.py info
```

## Common Issues

### "MineStudio not available"
**Solution:** Running in mock mode is normal for first test. For full functionality:
```bash
pip install minestudio
```

### "OpenAI API error"
**Solution:** Check your API key in `.env`:
```bash
cat .env  # Should show: OPENAI_API_KEY=sk-...
```

### "Port already in use"
**Solution:** Use different ports:
```bash
python main.py launch --green-port 9003 --white-port 9004
```

## Full Documentation

- **README.md**: Complete project documentation
- **SETUP.md**: Detailed setup and deployment
- **IMPLEMENTATION_SUMMARY.md**: Technical overview

## AgentBeats Integration

Once local testing works:

1. Expose agents publicly (ngrok or cloud)
2. Register at https://v2.agentbeats.org/main
3. Participate in AgentX-AgentBeats competition

See **SETUP.md** for complete integration guide.

---

**You're ready to go! 🚀**

Run your first evaluation now:
```bash
python main.py launch --task-name collect_wood --difficulty simple
```
