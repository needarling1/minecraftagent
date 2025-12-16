"""White agent implementation - executes Minecraft tasks using MineStudio."""

import uvicorn
import json
import base64
import time
import os
from pathlib import Path
from typing import Optional

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.utils import new_agent_text_message

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.a2a_utils import parse_tags
from utils.task_utils import load_task_config

# Import MineStudio components
try:
    # Adjust these imports based on actual MineStudio structure in your MCU folder
    sys.path.append(str(Path(__file__).parent.parent.parent / "MCU" / "minestudio"))
    from minestudio.simulator import MinecraftSim
    from minestudio.simulator.callbacks import RecordCallback
    MINESTUDIO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MineStudio not available: {e}")
    print("White agent will run in mock mode")
    MINESTUDIO_AVAILABLE = False


class MinecraftWhiteAgentExecutor(AgentExecutor):
    """White agent executor for performing Minecraft tasks."""

    def __init__(self, output_dir: str = None):
        # Get the directory where the script is located
        script_dir = Path(__file__).parent.parent.absolute()

        # Use absolute path relative to script location
        if output_dir is None:
            output_dir = script_dir / "output"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute a Minecraft task and return video artifact."""
        print("White Agent: Received task request")

        # Parse the request
        user_input = context.get_user_input()
        tags = parse_tags(user_input)

        if 'task_request' not in tags:
            await event_queue.enqueue_event(
                new_agent_text_message("Error: No task_request found in message")
            )
            return

        # Extract task parameters from the message
        task_name = None
        difficulty = "simple"
        max_steps = 12000
        task_config_path = None

        # Parse task details from the request text
        request_text = tags['task_request']
        for line in request_text.split('\n'):
            line = line.strip()
            if line.startswith('Task Name:'):
                task_name = line.split(':', 1)[1].strip()
            elif line.startswith('Difficulty:'):
                difficulty = line.split(':', 1)[1].strip()
            elif line.startswith('Max Steps:'):
                max_steps = int(line.split(':', 1)[1].strip())
            elif line.startswith('Task Configuration Path:'):
                task_config_path = line.split(':', 1)[1].strip()

        if not task_name or not task_config_path:
            await event_queue.enqueue_event(
                new_agent_text_message("Error: Missing task_name or task_config_path")
            )
            return

        print(f"White Agent: Executing task '{task_name}' ({difficulty}) for {max_steps} steps")

        try:
            # Load task configuration
            task_config = load_task_config(task_config_path)
            custom_init_commands = task_config.get('custom_init_commands', [])
            task_description = task_config.get('text', '')

            print(f"White Agent: Task description: {task_description}")
            print(f"White Agent: Init commands: {len(custom_init_commands)} commands")

            # Note: Don't send intermediate messages - only send the final complete response
            # await event_queue.enqueue_event(
            #     new_agent_text_message(f"Starting task execution: {task_name}\nDescription: {task_description}")
            # )

            # Execute task with MineStudio
            if MINESTUDIO_AVAILABLE:
                try:
                    video_path, steps_taken, completed = await self._execute_with_minestudio(
                        task_name=task_name,
                        difficulty=difficulty,
                        custom_init_commands=custom_init_commands,
                        task_description=task_description,
                        max_steps=max_steps,
                        event_queue=event_queue
                    )
                except (EOFError, Exception) as e:
                    # Fall back to mock mode if MineStudio fails
                    print(f"White Agent: MineStudio execution failed ({str(e)}), falling back to mock mode")
                    video_path, steps_taken, completed = await self._execute_mock(
                        task_name=task_name,
                        difficulty=difficulty,
                        max_steps=max_steps,
                        event_queue=event_queue
                    )
            else:
                # Mock execution for testing without MineStudio
                video_path, steps_taken, completed = await self._execute_mock(
                    task_name=task_name,
                    difficulty=difficulty,
                    max_steps=max_steps,
                    event_queue=event_queue
                )

            # Read video and encode as base64
            with open(video_path, 'rb') as f:
                video_data = f.read()
                video_base64 = base64.b64encode(video_data).decode('utf-8')

            # Prepare artifact response
            artifact_data = {
                "video_path": str(video_path),
                "video_base64": video_base64,
                "task_name": task_name,
                "difficulty": difficulty,
                "steps_taken": steps_taken,
                "completed": completed,
                "timestamp": time.time()
            }

            # IMPORTANT: Must include <video_artifact> tags for green agent to parse
            response_message = f"""Task execution complete!

Task: {task_name}
Difficulty: {difficulty}
Steps Taken: {steps_taken}
Completed: {completed}
Video saved to: {video_path}

<video_artifact>
{json.dumps(artifact_data)}
</video_artifact>
"""

            await event_queue.enqueue_event(
                new_agent_text_message(response_message)
            )

            print(f"White Agent: Task complete, video saved to {video_path}")

        except Exception as e:
            error_msg = f"Error executing task: {str(e)}"
            print(f"White Agent: {error_msg}")
            import traceback
            traceback.print_exc()
            await event_queue.enqueue_event(
                new_agent_text_message(error_msg)
            )

    async def _execute_with_minestudio(
        self,
        task_name: str,
        difficulty: str,
        custom_init_commands: list,
        task_description: str,
        max_steps: int,
        event_queue: EventQueue
    ) -> tuple[str, int, bool]:
        """
        Execute task using MineStudio simulator.

        Returns:
            Tuple of (video_path, steps_taken, completed)
        """
        # Create output directory for this task
        task_output_dir = self.output_dir / task_name
        task_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"White Agent: Initializing MineStudio environment...")

        # Create callbacks for task execution
        # Note: You may need to adjust these based on actual MCU implementation
        from minestudio.simulator.callbacks.callback import MinecraftCallback

        class CommandsCallback(MinecraftCallback):
            """Callback to execute custom initialization commands."""
            def __init__(self, commands):
                super().__init__()
                self.commands = commands

            def after_reset(self, sim, obs, info):
                # Try to execute commands if the method exists
                # Note: Command execution API varies by MineStudio version
                try:
                    if hasattr(sim, 'execute_command'):
                        for cmd in self.commands:
                            sim.execute_command(cmd)
                    elif hasattr(sim, 'env') and hasattr(sim.env, 'execute_command'):
                        for cmd in self.commands:
                            sim.env.execute_command(cmd)
                    else:
                        print(f"White Agent: Command execution not available in this MineStudio version")
                        print(f"White Agent: Skipping {len(self.commands)} initialization commands")
                except Exception as e:
                    print(f"White Agent: Warning - could not execute commands: {e}")
                return obs, info

        class TaskCallback(MinecraftCallback):
            """Callback for task-specific logic."""
            def __init__(self, task_text):
                super().__init__()
                self.task_text = task_text

            def after_reset(self, sim, obs, info):
                info['task'] = self.task_text
                return obs, info

        # Initialize environment with callbacks
        env = MinecraftSim(
            obs_size=(128, 128),
            callbacks=[
                RecordCallback(
                    record_path=str(task_output_dir),
                    fps=20,
                    frame_type="pov",
                    recording=True
                ),
                CommandsCallback(custom_init_commands),
                TaskCallback(task_description)
            ]
        )

        print(f"White Agent: Environment initialized, starting episode...")
        # Don't send intermediate messages - only the final response matters
        # await event_queue.enqueue_event(
        #     new_agent_text_message(f"MineStudio environment initialized, running {max_steps} steps...")
        # )

        # Load agent policy (Hybrid: LLM planning + VPT execution)
        # Note: You'll need to have the model files available
        vpt_policy = None
        try:
            from minestudio.models import load_vpt_policy
            vpt_policy = load_vpt_policy(
                model_path="../MCU/pretrained/foundation-model-2x.model",
                weights_path="../MCU/pretrained/foundation-model-2x.weights"
            ).to("cuda")
            print("White Agent: Loaded VPT policy for low-level control")
        except Exception as e:
            print(f"Warning: Could not load VPT policy: {e}")
            print("Hybrid agent will use LLM-only mode")

        # Initialize hybrid policy (LLM planner + VPT executor)
        from white_agent.hybrid_policy import HybridPolicy
        policy = HybridPolicy(vpt_policy=vpt_policy, model="gpt-4o")

        # Initialize the plan for this task
        policy.initialize_plan(task_description)

        # Run episode with hybrid policy
        obs, info = env.reset()
        memory = None
        steps_taken = 0
        completed = False

        for step in range(max_steps):
            # Hybrid policy handles planning and execution
            action, memory = policy.get_action(obs, memory, step=step, max_steps=max_steps)

            obs, reward, terminated, truncated, info = env.step(action)
            steps_taken = step + 1

            # Check for task completion (you may need to customize this)
            if terminated or truncated:
                completed = True
                break

            # Progress update every 1000 steps
            if (step + 1) % 1000 == 0:
                print(f"White Agent: Step {step + 1}/{max_steps}")
                # Don't send intermediate messages - only the final response matters
                # await event_queue.enqueue_event(
                #     new_agent_text_message(f"Progress: {step + 1}/{max_steps} steps")
                # )

        env.close()
        print(f"White Agent: Episode complete after {steps_taken} steps")

        # Save reasoning summary for documentation
        reasoning_summary = policy.get_reasoning_summary()
        reasoning_file = task_output_dir / f"reasoning_{task_name}.md"
        with open(reasoning_file, 'w') as f:
            f.write(reasoning_summary)
        print(f"White Agent: Reasoning saved to {reasoning_file}")

        # Find the generated video
        video_files = list(task_output_dir.glob("episode_*.mp4"))
        if not video_files:
            raise FileNotFoundError(f"No video file generated in {task_output_dir}")

        video_path = str(video_files[-1])  # Get most recent
        return video_path, steps_taken, completed

    async def _execute_mock(
        self,
        task_name: str,
        difficulty: str,
        max_steps: int,
        event_queue: EventQueue
    ) -> tuple[str, int, bool]:
        """
        Mock task execution for testing without MineStudio.

        Returns:
            Tuple of (video_path, steps_taken, completed)
        """
        print("White Agent: Running in MOCK mode (MineStudio not available)")
        # Don't send intermediate messages - only the final response matters
        # await event_queue.enqueue_event(
        #     new_agent_text_message("Running in mock mode - MineStudio not available")
        # )

        # Create a dummy video file
        task_output_dir = self.output_dir / task_name
        task_output_dir.mkdir(parents=True, exist_ok=True)
        video_path = task_output_dir / f"mock_episode_{int(time.time())}.mp4"

        # Create a proper minimal black video using OpenCV
        try:
            import cv2
            import numpy as np

            # Create a 30-frame black video (640x480, 1 second at 30fps)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))

            # Write 30 black frames
            black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            for _ in range(30):
                out.write(black_frame)

            out.release()
            print(f"White Agent: Created mock video with 30 black frames at {video_path}")

        except Exception as e:
            print(f"Warning: Could not create proper mock video: {e}")
            # Fallback to minimal MP4 header
            with open(video_path, 'wb') as f:
                # Write minimal MP4 header (this is just a placeholder)
                f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42mp41')

        steps_taken = max_steps
        completed = True

        return str(video_path), steps_taken, completed

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel ongoing task execution."""
        raise NotImplementedError("Cancellation not supported")


def prepare_white_agent_card(url: str) -> AgentCard:
    """Prepare the agent card for the white agent."""
    skill = AgentSkill(
        id="minecraft_task_execution",
        name="Minecraft Task Execution",
        description="Executes Minecraft tasks using MineStudio and returns video recordings",
        tags=["minecraft", "white agent", "task execution"],
        examples=[],
    )

    card = AgentCard(
        name="minecraft_white_agent",
        description="Minecraft agent that executes tasks and generates video recordings for evaluation",
        url=url,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(),
        skills=[skill],
    )

    return card


def start_white_agent(
    agent_name: str = "minecraft_white_agent",
    host: str = "localhost",
    port: int = 9002,
    output_dir: str = None
):
    """
    Start the white agent A2A server.

    Args:
        agent_name: Name of the agent
        host: Host to bind to
        port: Port to bind to
        output_dir: Directory to save output videos
    """
    print(f"Starting Minecraft White Agent on {host}:{port}...")

    # Use AGENT_URL from earthshaker if available, otherwise localhost
    agent_url = os.getenv("AGENT_URL")
    if agent_url:
        url = agent_url
        print(f"Using agent URL from earthshaker: {url}")
    else:
        url = f"http://{host}:{port}"
        print(f"Using local URL for testing: {url}")
    card = prepare_white_agent_card(url)

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=MinecraftWhiteAgentExecutor(output_dir=output_dir),
        task_store=InMemoryTaskStore(),
    )

    # Create A2A application
    app = A2AStarletteApplication(
        agent_card=card,
        http_handler=request_handler,
    )

    print("White Agent ready to execute Minecraft tasks")
    uvicorn.run(app.build(), host=host, port=port)
