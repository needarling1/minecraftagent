#!/bin/bash
# AgentBeats controller script for white agent (executor)

# Activate the minecraft-benchmark conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate minecraft-benchmark

# Navigate to project directory
cd ~/dev/minecraftagent

# Set the public URL for the agent card
export PUBLIC_URL="https://white.mcubenchmark.org"

# Start the white agent
# The controller will set $HOST and $AGENT_PORT environment variables
python main.py white
