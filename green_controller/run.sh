#!/bin/bash
# AgentBeats controller script for green agent (evaluator)

# Activate the minecraft-benchmark conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate minecraft-benchmark

# Navigate to project directory
cd ~/dev/minecraftagent

# Set the public URL for the agent card
export PUBLIC_URL="https://green.mcubenchmark.org"

# Start the green agent
# The controller will set $HOST and $AGENT_PORT environment variables
python main.py green
