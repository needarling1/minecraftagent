#!/bin/bash
# AgentBeats controller script for white agent (executor)

# Activate the minecraft-benchmark conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate minecraft-benchmark

# Navigate to project directory
cd ~/dev/minecraftagent

# Start the white agent
# Earthshaker will set $HOST, $AGENT_PORT, and $AGENT_URL environment variables
python main.py white
