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
# IMPORTANT: Set your OpenAI API key before running
# Option 1: Set in your shell environment before running this script:
#   export OPENAI_API_KEY=sk-your-key-here
# Option 2: Create a .env file in the project root with:
#   OPENAI_API_KEY=sk-your-key-here
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable is not set"
    echo "Please set your OpenAI API key before running this script"
    exit 1
fi
export OPENAI_API_KEY

# Start the white agent
# Earthshaker will set $HOST, $AGENT_PORT, and $AGENT_URL environment variables
python main.py white
