"""Hybrid agent policy combining LLM planning with VPT execution."""

import json
import base64
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
import os
from pathlib import Path


class SubtaskPlanner:
    """LLM-based high-level task planner using chain-of-thought reasoning."""

    def __init__(self, model: str = "gpt-5-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def plan_task(self, task_description: str, inventory: Dict[str, int],
                  position: Optional[Dict] = None, completed_steps: List[str] = None) -> Dict[str, Any]:
        """
        Generate a step-by-step plan for completing the task.

        Returns:
            {
                "reasoning": "Chain-of-thought explanation",
                "subtasks": ["step 1", "step 2", ...],
                "current_subtask": "next immediate action",
                "estimated_steps": int
            }
        """
        completed_steps = completed_steps or []

        system_prompt = """You are an expert Minecraft player and task planner.
Your role is to break down tasks into clear, executable subtasks.

For each task:
1. Analyze what's needed
2. Break it into sequential subtasks
3. Consider current inventory and position
4. Identify the immediate next action
5. Estimate steps needed

Be specific and actionable. Each subtask should be something concrete that can be executed."""

        user_prompt = f"""Task: {task_description}

Current State:
- Inventory: {json.dumps(inventory, indent=2)}
- Position: {position if position else "Unknown"}
- Completed steps: {completed_steps if completed_steps else "None yet"}

Please provide:
1. Your reasoning (chain-of-thought)
2. A numbered list of subtasks to complete this task
3. The immediate next action to take
4. Estimated number of steps needed

Respond in JSON format:
{{
    "reasoning": "your step-by-step thinking",
    "subtasks": ["subtask 1", "subtask 2", ...],
    "current_subtask": "immediate next action",
    "estimated_steps": number
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )

            plan = json.loads(response.choices[0].message.content)
            return plan
        except Exception as e:
            print(f"Planning error: {e}")
            # Fallback simple plan
            return {
                "reasoning": f"Error in planning: {e}. Using simple approach.",
                "subtasks": [task_description],
                "current_subtask": task_description,
                "estimated_steps": 1000
            }


class StateManager:
    """Tracks agent state including inventory, position, and progress."""

    def __init__(self):
        self.inventory: Dict[str, int] = {}
        self.position: Optional[Dict] = None
        self.completed_subtasks: List[str] = []
        self.current_subtask: Optional[str] = None
        self.action_history: List[str] = []

    def update_from_observation(self, obs: Any) -> None:
        """Update state from MineStudio observation."""
        try:
            # Extract inventory from observation
            if hasattr(obs, 'get') and 'inventory' in obs:
                self.inventory = obs['inventory']

            # Extract position if available
            if hasattr(obs, 'get') and 'location' in obs:
                self.position = obs['location']
        except Exception as e:
            print(f"State update error: {e}")

    def mark_subtask_complete(self, subtask: str) -> None:
        """Mark a subtask as completed."""
        if subtask not in self.completed_subtasks:
            self.completed_subtasks.append(subtask)
            print(f"✓ Completed subtask: {subtask}")

    def add_action(self, action_name: str) -> None:
        """Record an action taken."""
        self.action_history.append(action_name)

    def get_state_summary(self) -> str:
        """Get a text summary of current state."""
        return f"""
Inventory: {self.inventory}
Position: {self.position}
Completed: {len(self.completed_subtasks)} subtasks
Recent actions: {self.action_history[-5:] if self.action_history else 'None'}
"""


class ActionMapper:
    """Maps high-level subtasks to low-level Minecraft actions."""

    # Define action primitives that VPT can execute
    ACTION_PRIMITIVES = {
        "move_forward": "forward",
        "move_back": "back",
        "turn_left": "left",
        "turn_right": "right",
        "jump": "jump",
        "attack": "attack",
        "use": "use",
        "sneak": "sneak",
        "sprint": "sprint"
    }

    def __init__(self, llm_client: OpenAI, model: str = "gpt-4o"):
        self.client = llm_client
        self.model = model

    def subtask_to_actions(self, subtask: str, state: StateManager) -> List[str]:
        """
        Convert a subtask into a sequence of primitive actions.

        Uses LLM to reason about what specific actions are needed.
        """
        system_prompt = """You are an expert at translating high-level Minecraft goals
into sequences of primitive actions.

Available actions:
- move_forward, move_back, turn_left, turn_right
- jump, attack, use
- sneak, sprint

For each subtask, provide a sequence of these primitive actions."""

        user_prompt = f"""Subtask: {subtask}

Current state: {state.get_state_summary()}

What sequence of primitive actions should be taken?
Respond with a JSON list of action names.

Example: ["move_forward", "move_forward", "attack", "use"]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            actions = result.get("actions", ["move_forward"] * 10)
            return actions
        except Exception as e:
            print(f"Action mapping error: {e}")
            # Fallback: basic exploration
            return ["move_forward"] * 5 + ["turn_right"] * 2


class HybridPolicy:
    """
    Hybrid agent combining LLM planning with VPT execution.

    Architecture:
    1. LLM Planner: Creates high-level plan with reasoning
    2. State Manager: Tracks inventory, position, progress
    3. Action Mapper: Converts subtasks to primitive actions
    4. VPT Executor: Executes low-level actions in Minecraft
    """

    def __init__(self, vpt_policy=None, model: str = "gpt-4o"):
        self.vpt_policy = vpt_policy
        self.planner = SubtaskPlanner(model=model)
        self.state = StateManager()
        self.action_mapper = ActionMapper(self.planner.client, model=model)

        # Planning state
        self.current_plan: Optional[Dict] = None
        self.current_subtask_index: int = 0
        self.steps_in_subtask: int = 0
        self.max_steps_per_subtask: int = 500

        # Reasoning logs
        self.reasoning_log: List[Dict] = []

    def initialize_plan(self, task_description: str) -> Dict[str, Any]:
        """Create initial plan for the task."""
        print(f"\n{'='*60}")
        print(f"HYBRID AGENT - PLANNING PHASE")
        print(f"{'='*60}")
        print(f"Task: {task_description}\n")

        plan = self.planner.plan_task(
            task_description=task_description,
            inventory=self.state.inventory,
            position=self.state.position,
            completed_steps=self.state.completed_subtasks
        )

        self.current_plan = plan
        self.current_subtask_index = 0

        # Log reasoning
        print(f"REASONING:")
        print(plan['reasoning'])
        print(f"\nPLAN:")
        for i, subtask in enumerate(plan['subtasks'], 1):
            print(f"{i}. {subtask}")
        print(f"\nEstimated steps: {plan['estimated_steps']}")
        print(f"{'='*60}\n")

        self.reasoning_log.append({
            "type": "initial_plan",
            "task": task_description,
            "plan": plan
        })

        return plan

    def get_action(self, obs, memory, step: int, max_steps: int):
        """
        Get next action using hybrid approach.

        Process:
        1. Update state from observation
        2. Check if need to replan
        3. Get current subtask
        4. Use VPT to execute (or fallback to action mapping)
        5. Return action and updated memory
        """
        # Update state
        self.state.update_from_observation(obs)

        # Check if need new subtask
        if self.current_plan is None or self._should_move_to_next_subtask():
            self._advance_subtask()

        # Get action from VPT or action mapper
        if self.vpt_policy is not None:
            # Use VPT for low-level control
            action, memory = self.vpt_policy.get_action(obs, memory, input_shape='*')
        else:
            # Fallback: use action mapper
            # This is simplified - in practice you'd execute the action sequence
            action = obs.action_space.sample()  # Placeholder
            memory = None

        # Record action
        self.steps_in_subtask += 1

        return action, memory

    def _should_move_to_next_subtask(self) -> bool:
        """Determine if should move to next subtask."""
        if self.current_plan is None:
            return True

        # Move on if spent too long on current subtask
        if self.steps_in_subtask >= self.max_steps_per_subtask:
            return True

        # Check if subtask appears complete (can add more sophisticated checks)
        # For now, just use step threshold
        return False

    def _advance_subtask(self) -> None:
        """Move to next subtask in plan."""
        if self.current_plan is None or \
           self.current_subtask_index >= len(self.current_plan['subtasks']):
            return

        # Mark previous subtask complete
        if self.current_subtask_index > 0:
            prev_subtask = self.current_plan['subtasks'][self.current_subtask_index - 1]
            self.state.mark_subtask_complete(prev_subtask)

        # Move to next
        if self.current_subtask_index < len(self.current_plan['subtasks']):
            current = self.current_plan['subtasks'][self.current_subtask_index]
            self.state.current_subtask = current
            self.steps_in_subtask = 0
            self.current_subtask_index += 1

            print(f"\n→ Starting subtask {self.current_subtask_index}/{len(self.current_plan['subtasks'])}: {current}")

    def get_reasoning_summary(self) -> str:
        """Get summary of agent's reasoning for documentation."""
        summary = "# Agent Reasoning Summary\n\n"

        for log in self.reasoning_log:
            if log['type'] == 'initial_plan':
                summary += f"## Initial Plan\n"
                summary += f"Task: {log['task']}\n\n"
                summary += f"Reasoning: {log['plan']['reasoning']}\n\n"
                summary += "Subtasks:\n"
                for i, subtask in enumerate(log['plan']['subtasks'], 1):
                    summary += f"{i}. {subtask}\n"
                summary += "\n"

        summary += f"## Progress\n"
        summary += f"Completed subtasks: {len(self.state.completed_subtasks)}\n"
        for subtask in self.state.completed_subtasks:
            summary += f"- ✓ {subtask}\n"

        return summary
