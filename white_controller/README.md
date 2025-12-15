# White Agent Controller Directory

This directory is used to run the AgentBeats controller for the **white agent** (executor).

## Usage

```bash
# Activate the controller environment
conda activate agentbeats-controller

# Navigate to this directory
cd ~/dev/minecraftagent/white_controller

# Start the controller
agentbeats run_ctrl
```

The controller will:
- Read `run.sh` to launch the white agent
- Create the `/to_agent/{id}/` URL structure
- Provide a management UI
- Automatically set $HOST and $AGENT_PORT environment variables

The white agent will run in the `minecraft-benchmark` environment (Python 3.10).
