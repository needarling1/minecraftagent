"""Green agent implementation - manages Minecraft benchmark assessment and evaluation."""

import uvicorn
import json
import time
import base64
import os
from pathlib import Path
from typing import Optional
import sys

# Handle tomllib for Python <3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "tomli is required for Python <3.11. Install with: pip install tomli"
        )

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from a2a.utils import new_agent_text_message, get_text_parts

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.a2a_utils import parse_tags, send_message
from utils.task_utils import find_task_config, load_task_config


def load_agent_card_toml(agent_name: str):
    """Load agent card configuration from TOML file."""
    current_dir = Path(__file__).parent
    toml_path = current_dir / f"{agent_name}.toml"
    with open(toml_path, "rb") as f:
        return tomllib.load(f)


async def request_white_agent_evaluation(
    white_agent_url: str,
    task_name: str,
    difficulty: str,
    task_config_path: str,
    max_steps: int = 12000
) -> dict:
    """
    Request white agent to perform a task and submit video artifact.

    Args:
        white_agent_url: URL of the white agent
        task_name: Name of the task
        difficulty: Task difficulty (simple/hard/compositional)
        task_config_path: Path to the task configuration YAML
        max_steps: Maximum simulation steps

    Returns:
        Dictionary with video_path and metadata
    """
    # Read task config to get description
    task_config = load_task_config(task_config_path)
    task_description = task_config.get('text', task_name)

    # Create message for white agent
    request_message = f"""
<task_request>
Please complete the following Minecraft task and submit the video recording.

Task Name: {task_name}
Difficulty: {difficulty}
Description: {task_description}
Max Steps: {max_steps}

Task Configuration Path: {task_config_path}

After completing the task, please respond with:
<video_artifact>
{{
  "video_path": "path/to/video.mp4",
  "video_base64": "base64_encoded_video_data",
  "task_name": "{task_name}",
  "difficulty": "{difficulty}",
  "steps_taken": number_of_steps,
  "completed": true/false
}}
</video_artifact>
</task_request>
"""

    print(f"Green Agent: Sending task request to white agent at {white_agent_url}")
    print(f"Task: {task_name} ({difficulty})")

    # Send request to white agent (with longer timeout for task execution)
    response = await send_message(white_agent_url, request_message, timeout=600.0)

    # Parse response
    res_root = response.root
    from a2a.types import SendMessageSuccessResponse, Message

    assert isinstance(res_root, SendMessageSuccessResponse)
    res_result = res_root.result
    assert isinstance(res_result, Message)

    text_parts = get_text_parts(res_result.parts)
    assert len(text_parts) == 1, "Expecting exactly one text part from white agent"

    white_response = text_parts[0]
    print(f"Green Agent: Received response from white agent")
    print(f"DEBUG: Response length: {len(white_response)}")
    print(f"DEBUG: First 500 chars:\n{white_response[:500]}")
    print(f"DEBUG: Last 500 chars:\n{white_response[-500:]}")

    # Parse video artifact
    tags = parse_tags(white_response)
    print(f"DEBUG: Tags found: {list(tags.keys())}")

    if 'video_artifact' not in tags:
        print(f"DEBUG: Full response:\n{white_response}")
        raise ValueError("White agent did not return video_artifact")

    artifact_data = json.loads(tags['video_artifact'])
    return artifact_data


def evaluate_video_with_vlm(
    task_name: str,
    video_path: str,
    criteria_file_path: str
) -> dict:
    """
    Evaluate a video using the existing VLM evaluation logic.

    Args:
        task_name: Name of the task
        video_path: Path to the video file
        criteria_file_path: Path to the criteria file

    Returns:
        Dictionary with evaluation scores
    """
    # Import the existing eval module
    sys.path.append(str(Path(__file__).parent.parent / "auto_eval"))
    from eval import process_video, assess_video

    # Process video to get frames
    frames = process_video(task_name, video_path)

    # Run assessment
    result = assess_video(task_name, frames, video_path, str(Path(criteria_file_path).parent))

    # Parse result to get scores
    import re
    scores = {}
    if result:
        lines = result.strip().split('\n')
        for line in lines:
            if line.startswith('- '):
                parts = line.split(': ')
                if len(parts) == 2:
                    key = parts[0].strip('- ')
                    value = parts[1].strip()
                    try:
                        scores[key] = int(value)
                    except ValueError:
                        pass

    return scores


class MinecraftGreenAgentExecutor(AgentExecutor):
    """Green agent executor for Minecraft benchmark assessments."""

    def __init__(self, task_configs_dir: str = None, criteria_dir: str = None):
        # Get the directory where the script is located
        script_dir = Path(__file__).parent.parent.absolute()

        # Use absolute paths relative to script location
        if task_configs_dir is None:
            task_configs_dir = script_dir / "task_configs"
        if criteria_dir is None:
            criteria_dir = script_dir / "auto_eval" / "criteria_files"

        self.task_configs_dir = Path(task_configs_dir)
        self.criteria_dir = Path(criteria_dir)

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute assessment request from AgentBeats or other orchestrator."""
        print("Green Agent: Received assessment request")

        # Parse the request
        user_input = context.get_user_input()
        tags = parse_tags(user_input)

        # Extract parameters
        white_agent_url = tags.get('white_agent_url')
        task_name = tags.get('task_name')
        difficulty = tags.get('difficulty', 'simple')
        max_steps = int(tags.get('max_steps', '12000'))

        if not white_agent_url or not task_name:
            await event_queue.enqueue_event(
                new_agent_text_message("Error: Missing white_agent_url or task_name in request")
            )
            return

        print(f"Green Agent: Assessment parameters:")
        print(f"  White Agent URL: {white_agent_url}")
        print(f"  Task: {task_name}")
        print(f"  Difficulty: {difficulty}")
        print(f"  Max Steps: {max_steps}")

        # Find task config
        task_config_path = find_task_config(task_name, difficulty, str(self.task_configs_dir))
        if not task_config_path:
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: Task config not found for {task_name} ({difficulty})")
            )
            return

        # Find criteria file
        criteria_file = self.criteria_dir / f"{task_name}.txt"
        if not criteria_file.exists():
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: Criteria file not found for {task_name}")
            )
            return

        try:
            # Request white agent to perform task
            await event_queue.enqueue_event(
                new_agent_text_message(f"Requesting white agent to perform task: {task_name}...")
            )

            artifact_data = await request_white_agent_evaluation(
                white_agent_url,
                task_name,
                difficulty,
                task_config_path,
                max_steps
            )

            # Save video if base64 encoded
            video_path = artifact_data.get('video_path')
            if 'video_base64' in artifact_data:
                # Decode and save video
                script_dir = Path(__file__).parent.parent.absolute()
                output_dir = script_dir / "output" / task_name
                output_dir.mkdir(parents=True, exist_ok=True)
                video_path = str(output_dir / f"episode_{int(time.time())}.mp4")

                video_data = base64.b64decode(artifact_data['video_base64'])
                with open(video_path, 'wb') as f:
                    f.write(video_data)

                print(f"Green Agent: Saved video to {video_path}")

            # Evaluate video
            await event_queue.enqueue_event(
                new_agent_text_message(f"Evaluating video with VLM...")
            )

            scores = evaluate_video_with_vlm(
                task_name,
                video_path,
                str(criteria_file)
            )

            # Prepare results
            result_data = {
                "task_name": task_name,
                "difficulty": difficulty,
                "white_agent_url": white_agent_url,
                "video_path": video_path,
                "steps_taken": artifact_data.get('steps_taken', 'unknown'),
                "task_completed": artifact_data.get('completed', False),
                "evaluation_scores": scores,
                "timestamp": time.time()
            }

            # Send results back
            result_message = f"""
Assessment Complete!

Task: {task_name} ({difficulty})
Task Completed: {result_data['task_completed']}
Steps Taken: {result_data['steps_taken']}

Evaluation Scores:
{json.dumps(scores, indent=2)}

Full Results:
{json.dumps(result_data, indent=2)}
"""

            await event_queue.enqueue_event(
                new_agent_text_message(result_message)
            )

            print("Green Agent: Assessment complete")

        except Exception as e:
            error_msg = f"Error during assessment: {str(e)}"
            print(f"Green Agent: {error_msg}")
            import traceback
            traceback.print_exc()
            await event_queue.enqueue_event(
                new_agent_text_message(error_msg)
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel ongoing assessment."""
        raise NotImplementedError("Cancellation not supported")


def start_green_agent(
    agent_name: str = "minecraft_green_agent",
    host: str = "localhost",
    port: int = 9001,
    task_configs_dir: str = None,
    criteria_dir: str = None
):
    """
    Start the green agent A2A server.

    Args:
        agent_name: Name of the agent (must match TOML filename)
        host: Host to bind to
        port: Port to bind to
        task_configs_dir: Directory containing task configurations
        criteria_dir: Directory containing criteria files
    """
    print(f"Starting Minecraft Green Agent on {host}:{port}...")

    # Load agent card
    agent_card_dict = load_agent_card_toml(agent_name)

    # Use AGENT_URL from earthshaker if available, otherwise localhost
    agent_url = os.getenv("AGENT_URL")
    if agent_url:
        url = agent_url
        print(f"Using agent URL from earthshaker: {url}")
    else:
        url = f"http://{host}:{port}"
        print(f"Using local URL for testing: {url}")
    agent_card_dict["url"] = url

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=MinecraftGreenAgentExecutor(
            task_configs_dir=task_configs_dir,
            criteria_dir=criteria_dir
        ),
        task_store=InMemoryTaskStore(),
    )

    # Create A2A application
    app = A2AStarletteApplication(
        agent_card=AgentCard(**agent_card_dict),
        http_handler=request_handler,
    )

    print("Green Agent ready to accept assessment requests")
    uvicorn.run(app.build(), host=host, port=port)
