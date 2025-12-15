# Green Agent Controller Directory

This directory is used to run the AgentBeats controller for the **green agent** (evaluator).

## Usage

```bash
# Activate the controller environment
conda activate agentbeats-controller

# Navigate to this directory
cd ~/dev/minecraftagent/green_controller

# Start the controller
agentbeats run_ctrl
```

The controller will:
- Read `run.sh` to launch the green agent
- Create the `/to_agent/{id}/` URL structure
- Provide a management UI
- Automatically set $HOST and $AGENT_PORT environment variables

The green agent will run in the `minecraft-benchmark` environment (Python 3.10).
