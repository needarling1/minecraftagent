"""Launcher module - initiates and coordinates the evaluation process."""

import multiprocessing
import asyncio
from pathlib import Path

from green_agent.agent import start_green_agent
from white_agent.agent import start_white_agent
from utils.a2a_utils import wait_agent_ready, send_message


async def launch_evaluation(
    task_name: str = "collect_wood",
    difficulty: str = "simple",
    max_steps: int = 12000,
    green_host: str = "localhost",
    green_port: int = 9001,
    white_host: str = "localhost",
    white_port: int = 9002
):
    """
    Launch complete evaluation workflow with green and white agents.

    Args:
        task_name: Name of the Minecraft task to evaluate
        difficulty: Task difficulty ('simple', 'hard', or 'compositional')
        max_steps: Maximum simulation steps
        green_host: Host for green agent
        green_port: Port for green agent
        white_host: Host for white agent
        white_port: Port for white agent
    """
    print("=" * 80)
    print("MINECRAFT BENCHMARK EVALUATION LAUNCHER")
    print("=" * 80)

    # Start green agent
    print(f"\n[1/4] Launching green agent at {green_host}:{green_port}...")
    green_url = f"http://{green_host}:{green_port}"
    p_green = multiprocessing.Process(
        target=start_green_agent,
        args=("minecraft_green_agent", green_host, green_port)
    )
    p_green.start()

    # Wait for green agent to be ready
    print("Waiting for green agent to initialize...")
    if not await wait_agent_ready(green_url, timeout=30):
        print("ERROR: Green agent failed to start")
        p_green.terminate()
        return

    print("Green agent is ready!")

    # Start white agent
    print(f"\n[2/4] Launching white agent at {white_host}:{white_port}...")
    white_url = f"http://{white_host}:{white_port}"
    p_white = multiprocessing.Process(
        target=start_white_agent,
        args=("minecraft_white_agent", white_host, white_port)
    )
    p_white.start()

    # Wait for white agent to be ready
    print("Waiting for white agent to initialize...")
    if not await wait_agent_ready(white_url, timeout=30):
        print("ERROR: White agent failed to start")
        p_green.terminate()
        p_white.terminate()
        return

    print("White agent is ready!")

    # Send assessment request to green agent
    print(f"\n[3/4] Sending assessment request to green agent...")
    print(f"  Task: {task_name}")
    print(f"  Difficulty: {difficulty}")
    print(f"  Max Steps: {max_steps}")

    assessment_request = f"""
Your task is to assess the Minecraft agent at:
<white_agent_url>
{white_url}
</white_agent_url>

Please evaluate the following task:
<task_name>
{task_name}
</task_name>
<difficulty>
{difficulty}
</difficulty>
<max_steps>
{max_steps}
</max_steps>
"""

    print("\nSending request...")
    try:
        response = await send_message(green_url, assessment_request, timeout=2400.0)  # 15 min timeout

        # Parse response
        from a2a.types import SendMessageSuccessResponse, Message
        from a2a.utils import get_text_parts

        res_root = response.root
        assert isinstance(res_root, SendMessageSuccessResponse)
        res_result = res_root.result
        assert isinstance(res_result, Message)

        text_parts = get_text_parts(res_result.parts)
        result_text = "\n".join(text_parts)

        print("\n[4/4] Assessment Complete!")
        print("=" * 80)
        print("RESULTS:")
        print("=" * 80)
        print(result_text)
        print("=" * 80)

    except Exception as e:
        print(f"\nERROR during assessment: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\nShutting down agents...")
        p_green.terminate()
        p_green.join()
        p_white.terminate()
        p_white.join()
        print("Agents terminated. Evaluation complete.")


async def launch_batch_evaluation(
    task_names: list[str],
    difficulty: str = "simple",
    max_steps: int = 12000,
    green_host: str = "localhost",
    green_port: int = 9001,
    white_host: str = "localhost",
    white_port: int = 9002
):
    """
    Launch batch evaluation for multiple tasks.

    Args:
        task_names: List of task names to evaluate
        difficulty: Task difficulty
        max_steps: Maximum simulation steps per task
        green_host: Host for green agent
        green_port: Port for green agent
        white_host: Host for white agent
        white_port: Port for white agent
    """
    print("=" * 80)
    print(f"BATCH EVALUATION: {len(task_names)} tasks")
    print("=" * 80)

    for i, task_name in enumerate(task_names, 1):
        print(f"\n{'='*80}")
        print(f"TASK {i}/{len(task_names)}: {task_name}")
        print(f"{'='*80}\n")

        await launch_evaluation(
            task_name=task_name,
            difficulty=difficulty,
            max_steps=max_steps,
            green_host=green_host,
            green_port=green_port,
            white_host=white_host,
            white_port=white_port
        )

        # Small delay between tasks
        if i < len(task_names):
            print(f"\nWaiting 5 seconds before next task...")
            await asyncio.sleep(5)

    print(f"\n{'='*80}")
    print(f"BATCH EVALUATION COMPLETE: {len(task_names)} tasks finished")
    print(f"{'='*80}")


if __name__ == "__main__":
    # Example: run a single task evaluation
    asyncio.run(launch_evaluation(
        task_name="collect_wood",
        difficulty="simple",
        max_steps=12000
    ))
