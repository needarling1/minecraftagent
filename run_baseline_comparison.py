"""Run baseline comparisons for white agent evaluation."""

import asyncio
import json
from pathlib import Path
from launcher import MinecraftBenchmarkLauncher

# Tasks to evaluate
EVAL_TASKS = [
    {"name": "collect_wood", "difficulty": "simple"},
    {"name": "craft_wooden_pickaxe", "difficulty": "simple"},
    {"name": "build_a_house", "difficulty": "simple"},
    {"name": "hunt_a_cow", "difficulty": "simple"},
]


async def run_evaluation(task_name: str, difficulty: str, mode: str = "hybrid"):
    """
    Run a single evaluation.

    Args:
        task_name: Name of the task
        difficulty: Task difficulty
        mode: "hybrid", "vpt-only", or "random"
    """
    print(f"\n{'='*60}")
    print(f"Evaluating: {task_name} ({difficulty}) - Mode: {mode}")
    print(f"{'='*60}\n")

    # For baseline modes, you'd need to modify the white agent to use different policies
    # This is a simplified version - actual implementation would switch policies

    launcher = MinecraftBenchmarkLauncher()

    try:
        result = await launcher.launch_evaluation(
            task_name=task_name,
            difficulty=difficulty,
            max_steps=6000  # Shorter for quick evaluation
        )

        return {
            "task": task_name,
            "difficulty": difficulty,
            "mode": mode,
            "success": result.get("task_completed", False),
            "steps_taken": result.get("steps_taken", 0),
            "scores": result.get("evaluation_scores", {})
        }

    except Exception as e:
        print(f"Error in evaluation: {e}")
        return {
            "task": task_name,
            "difficulty": difficulty,
            "mode": mode,
            "success": False,
            "error": str(e)
        }


async def main():
    """Run all baseline comparisons."""
    results = []

    for task in EVAL_TASKS:
        result = await run_evaluation(
            task_name=task["name"],
            difficulty=task["difficulty"],
            mode="hybrid"
        )
        results.append(result)

        # Save intermediate results
        output_file = Path("baseline_results.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nCompleted {len(results)}/{len(EVAL_TASKS)} evaluations")

    print(f"\n{'='*60}")
    print("EVALUATION COMPLETE")
    print(f"{'='*60}\n")

    # Print summary
    print("Results Summary:")
    print(f"{'Task':<25} {'Success':<10} {'Steps':<10} {'Avg Score':<10}")
    print("-" * 60)

    for r in results:
        avg_score = sum(r.get("scores", {}).values()) / max(len(r.get("scores", {})), 1)
        print(f"{r['task']:<25} {str(r['success']):<10} {r.get('steps_taken', 0):<10} {avg_score:<10.1f}")

    print(f"\nFull results saved to: baseline_results.json")


if __name__ == "__main__":
    asyncio.run(main())
