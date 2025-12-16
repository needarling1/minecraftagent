#!/bin/bash
# AgentBeats controller script for white agent (executor)

# Activate the minecraft-benchmark conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate minecraft-benchmark

# Navigate to project directory
cd ~/dev/minecraftagent

# Set virtual display for headless server (for MineStudio and video processing)
export DISPLAY=:99

# Set OpenAI API key for hybrid agent LLM planning
# TODO: Replace with your actual OpenAI API key
export OPENAI_API_KEY=sk-your-actual-key-here

# Start the white agent
# Earthshaker will set $HOST, $AGENT_PORT, and $AGENT_URL environment variables
python main.py white
