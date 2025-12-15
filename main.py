"""CLI entry point for Minecraft Benchmark - cs194 project."""

import os
import typer
import asyncio
from pathlib import Path

from green_agent import start_green_agent
from white_agent import start_white_agent
from launcher import launch_evaluation, launch_batch_evaluation
from utils.task_utils import list_available_tasks

app = typer.Typer(
    help="Minecraft Agent Benchmark - Evaluate Minecraft agents using VLM-based assessment"
)


@app.command()
def green(
    host: str = typer.Option(None, help="Host to bind to (uses $HOST env var if set)"),
    port: int = typer.Option(None, help="Port to bind to (uses $AGENT_PORT env var if set)"),
):
    """Start the green agent (evaluator) server."""
    # Support AgentBeats controller environment variables
    host = host or os.getenv("HOST", "localhost")
    port = port or int(os.getenv("AGENT_PORT", "9001"))

    typer.echo(f"Starting green agent on {host}:{port}")
    start_green_agent(host=host, port=port)


@app.command()
def white(
    host: str = typer.Option(None, help="Host to bind to (uses $HOST env var if set)"),
    port: int = typer.Option(None, help="Port to bind to (uses $AGENT_PORT env var if set)"),
):
    """Start the white agent (task executor) server."""
    # Support AgentBeats controller environment variables
    host = host or os.getenv("HOST", "localhost")
    port = port or int(os.getenv("AGENT_PORT", "9002"))

    typer.echo(f"Starting white agent on {host}:{port}")
    start_white_agent(host=host, port=port)


@app.command()
def launch(
    task_name: str = typer.Option("collect_wood", help="Name of the task to evaluate"),
    difficulty: str = typer.Option("simple", help="Task difficulty (simple/hard/compositional)"),
    max_steps: int = typer.Option(12000, help="Maximum simulation steps"),
    green_host: str = typer.Option("localhost", help="Green agent host"),
    green_port: int = typer.Option(9001, help="Green agent port"),
    white_host: str = typer.Option("localhost", help="White agent host"),
    white_port: int = typer.Option(9002, help="White agent port"),
):
    """Launch complete evaluation workflow with both agents."""
    typer.echo(f"Launching evaluation for task: {task_name} ({difficulty})")
    asyncio.run(launch_evaluation(
        task_name=task_name,
        difficulty=difficulty,
        max_steps=max_steps,
        green_host=green_host,
        green_port=green_port,
        white_host=white_host,
        white_port=white_port
    ))


@app.command()
def batch(
    tasks_file: str = typer.Option(None, help="Path to file with task names (one per line)"),
    difficulty: str = typer.Option("simple", help="Task difficulty (simple/hard/compositional)"),
    max_steps: int = typer.Option(12000, help="Maximum simulation steps per task"),
    all_tasks: bool = typer.Option(False, help="Evaluate all available tasks"),
    green_host: str = typer.Option("localhost", help="Green agent host"),
    green_port: int = typer.Option(9001, help="Green agent port"),
    white_host: str = typer.Option("localhost", help="White agent host"),
    white_port: int = typer.Option(9002, help="White agent port"),
):
    """Run batch evaluation for multiple tasks."""
    if all_tasks:
        # Get all available tasks for the difficulty
        task_names = list_available_tasks(difficulty=difficulty)
        typer.echo(f"Found {len(task_names)} tasks for difficulty '{difficulty}'")
    elif tasks_file:
        # Read tasks from file
        with open(tasks_file, 'r') as f:
            task_names = [line.strip() for line in f if line.strip()]
        typer.echo(f"Loaded {len(task_names)} tasks from {tasks_file}")
    else:
        typer.echo("Error: Please specify either --tasks-file or --all-tasks")
        raise typer.Exit(1)

    if not task_names:
        typer.echo("No tasks to evaluate")
        raise typer.Exit(1)

    typer.echo(f"Starting batch evaluation...")
    asyncio.run(launch_batch_evaluation(
        task_names=task_names,
        difficulty=difficulty,
        max_steps=max_steps,
        green_host=green_host,
        green_port=green_port,
        white_host=white_host,
        white_port=white_port
    ))


@app.command()
def list_tasks(
    difficulty: str = typer.Option("simple", help="Task difficulty (simple/hard/compositional)"),
):
    """List all available tasks for a given difficulty."""
    task_names = list_available_tasks(difficulty=difficulty)

    if not task_names:
        typer.echo(f"No tasks found for difficulty '{difficulty}'")
        return

    typer.echo(f"\nAvailable tasks for difficulty '{difficulty}' ({len(task_names)} total):\n")
    for task in sorted(task_names):
        typer.echo(f"  - {task}")
    typer.echo("")


@app.command()
def info():
    """Display information about the Minecraft benchmark."""
    typer.echo("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    MINECRAFT AGENT BENCHMARK - CS194                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

This benchmark evaluates Minecraft agents using VLM-based video assessment.

📊 BENCHMARK STATISTICS:
   • 80+ atomic tasks across 10 categories
   • 20+ compositional tasks
   • 2 difficulty modes (Simple & Hard)
   • 6 evaluation dimensions

📁 TASK CATEGORIES:
   • ⚔️  Combat: Fighting mobs, hunting animals
   • 🛠️  Crafting: Creating tools, items, blocks
   • ⛏️  Mining: Extracting resources
   • 🏗️  Building: Constructing structures
   • 🧰 Tool Use: Using Minecraft tools effectively
   • 🧭 Exploration: Navigating the world
   • 🌀 Motion: Movement and positioning
   • 🖼️  Decoration: Aesthetic improvements
   • 🧲 Finding: Locating blocks/biomes/structures
   • 🪤 Trapping: Capturing entities

📈 EVALUATION CRITERIA:
   1. Task Progress - Completion of key steps
   2. Action Control - Precision and relevance
   3. Error Recognition & Correction - Self-debugging ability
   4. Creative Attempts - Innovative problem-solving
   5. Task Completion Efficiency - Speed and resource management
   6. Material Selection & Usage - Appropriate tool usage

🔧 ARCHITECTURE:
   • Green Agent: VLM-based evaluator using A2A protocol
   • White Agent: Task executor using MineStudio simulator
   • A2A Protocol: Agent-to-agent communication standard
   • AgentBeats: Platform integration ready

📖 USAGE EXAMPLES:
   # Start individual agents
   python main.py green --port 9001
   python main.py white --port 9002

   # Run single task evaluation
   python main.py launch --task-name collect_wood --difficulty simple

   # Run batch evaluation
   python main.py batch --all-tasks --difficulty simple

   # List available tasks
   python main.py list-tasks --difficulty simple

🌐 INTEGRATION:
   This benchmark is compatible with AgentBeats platform for standardized
   agent assessment. Both green and white agents implement the A2A protocol
   for seamless integration with the AgentBeats ecosystem.

For more information, visit: https://github.com/yourusername/minecraft-benchmark
""")


if __name__ == "__main__":
    app()
