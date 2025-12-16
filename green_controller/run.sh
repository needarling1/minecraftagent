#!/bin/bash
# AgentBeats controller script for green agent (evaluator)

# Activate the minecraft-benchmark conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate minecraft-benchmark

# Navigate to project directory
cd ~/dev/minecraftagent

# Set virtual display for headless server (for OpenCV/video processing)
export DISPLAY=:99

# Set OpenAI API key for VLM evaluation (GPT-4V)
# TODO: Replace with your actual OpenAI API key
export OPENAI_API_KEY=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

# Start the green agent
# Earthshaker will set $HOST, $AGENT_PORT, and $AGENT_URL environment variables
python main.py green
