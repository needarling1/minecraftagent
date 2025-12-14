"""Task configuration utilities for Minecraft benchmark."""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_task_config(config_path: str) -> Dict[str, Any]:
    """
    Load a task configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing task configuration with keys:
        - custom_init_commands: List of Minecraft commands to initialize the task
        - text: Task description
        - defaults: Optional list of default configs
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def get_task_name_from_path(config_path: str) -> str:
    """
    Extract task name from configuration file path.

    Args:
        config_path: Path to the configuration file

    Returns:
        Task name (filename without extension)
    """
    return Path(config_path).stem


def find_task_config(task_name: str, difficulty: str = "simple", task_configs_dir: str = None) -> Optional[str]:
    """
    Find the configuration file for a given task name and difficulty.

    Args:
        task_name: Name of the task
        difficulty: Task difficulty ('simple', 'hard', or 'compositional')
        task_configs_dir: Base directory containing task configurations

    Returns:
        Path to the configuration file if found, None otherwise
    """
    # Default to script directory if not provided
    if task_configs_dir is None:
        script_dir = Path(__file__).parent.parent.absolute()
        task_configs_dir = script_dir / "task_configs"

    config_path = Path(task_configs_dir) / difficulty / f"{task_name}.yaml"
    if config_path.exists():
        return str(config_path)
    return None


def list_available_tasks(difficulty: str = "simple", task_configs_dir: str = None) -> List[str]:
    """
    List all available tasks for a given difficulty.

    Args:
        difficulty: Task difficulty ('simple', 'hard', or 'compositional')
        task_configs_dir: Base directory containing task configurations

    Returns:
        List of task names
    """
    # Default to script directory if not provided
    if task_configs_dir is None:
        script_dir = Path(__file__).parent.parent.absolute()
        task_configs_dir = script_dir / "task_configs"

    config_dir = Path(task_configs_dir) / difficulty
    if not config_dir.exists():
        return []

    task_files = config_dir.glob("*.yaml")
    return [f.stem for f in task_files]
