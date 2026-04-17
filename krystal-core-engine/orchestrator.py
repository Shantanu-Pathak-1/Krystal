"""
Agentic Task Orchestrator for Krystal AI Core.

Provides task planning with LLM-driven step breakdown and persistent state management.
This module is independent of the API routing logic (engine.py/api.py) and uses
the existing LLMProcessor for text generation.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# Import existing engine components using same pattern as engine.py
import importlib.util
import sys

_ENGINE_DIR = Path(__file__).resolve().parent


def _load_sibling_module(unique_name: str, filename: str):
    """Load a sibling module from the same directory."""
    path = _ENGINE_DIR / filename
    spec = importlib.util.spec_from_file_location(unique_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = module
    spec.loader.exec_module(module)
    return module


# Load required engine modules
_api_router = _load_sibling_module("krystal_orchestrator._api_router", "api_router.py")
_llm_mod = _load_sibling_module("krystal_orchestrator._llm_processor", "llm_processor.py")

KeyManager = _api_router.KeyManager
LLMProcessor = _llm_mod.LLMProcessor

# Path for persistent task memory
MEMORY_FILE = Path("agent_memory.json")


class StepStatus(str, Enum):
    """Valid statuses for task steps."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RetryStage(str, Enum):
    """Stages of the 2-stage retry protocol."""
    NONE = "NONE"
    STAGE_1 = "STAGE_1"  # Silent retry in progress
    STAGE_2 = "STAGE_2"  # Awaiting user confirmation


class ExecutionState(str, Enum):
    """Overall execution states for the orchestrator."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED_CONFIRMATION = "PAUSED_CONFIRMATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskMemory:
    """
    Persistent state manager for agentic task execution.
    Stores and retrieves task plans from local JSON file.
    """

    def __init__(self, memory_file: Optional[Union[str, Path]] = None) -> None:
        self._memory_file = Path(memory_file) if memory_file else MEMORY_FILE
        self._memory: Dict[str, Any] = {}
        self._load_memory()

    def _load_memory(self) -> None:
        """Load existing memory from disk or initialize empty."""
        try:
            if self._memory_file.exists():
                with open(self._memory_file, "r", encoding="utf-8") as f:
                    self._memory = json.load(f)
            else:
                self._memory = {}
        except (json.JSONDecodeError, IOError, PermissionError) as e:
            self._memory = {}
            print(f"[TaskMemory] Warning: Could not load memory file: {e}. Starting fresh.")

    def _save_memory(self) -> None:
        """Persist current memory state to disk."""
        try:
            with open(self._memory_file, "w", encoding="utf-8") as f:
                json.dump(self._memory, f, indent=2, ensure_ascii=False)
        except (IOError, PermissionError) as e:
            print(f"[TaskMemory] Error: Could not save memory file: {e}")

    def create_plan(
        self,
        task_id: str,
        steps_list: List[str],
        is_new_task: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new task plan with the given steps.

        Args:
            task_id: Unique identifier for the task
            steps_list: List of step descriptions (strings)
            is_new_task: If True, clears any existing state for this task_id

        Returns:
            The created task plan dictionary
        """
        if not isinstance(steps_list, list):
            raise ValueError("steps_list must be a list of strings")

        # Clear existing state if this is a new task (not a resume)
        if is_new_task and task_id in self._memory:
            del self._memory[task_id]
            print(f"[TaskMemory] Cleared existing state for new task: {task_id}")

        # Check if resuming an existing task
        if not is_new_task and task_id in self._memory:
            existing_plan = self._memory[task_id]
            print(f"[TaskMemory] Resuming existing task: {task_id}")
            return existing_plan

        steps = [
            {
                "index": idx,
                "description": str(step),
                "status": StepStatus.PENDING.value,
                "started_at": None,
                "completed_at": None,
                "retry_count": 0,
                "retry_stage": RetryStage.NONE.value,
                "last_error": None,
                "execution_context": {},
            }
            for idx, step in enumerate(steps_list)
        ]

        plan = {
            "task_id": task_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": StepStatus.PENDING.value,
            "execution_state": ExecutionState.IDLE.value,
            "steps": steps,
            "current_step_index": 0,
            "requires_confirmation": False,
            "confirmation_prompt": None,
            "total_retries": 0,
        }

        self._memory[task_id] = plan
        self._save_memory()
        return plan

    def is_task_active(self, task_id: str) -> bool:
        """Check if a task exists and has not completed or failed."""
        if task_id not in self._memory:
            return False
        plan = self._memory[task_id]
        return plan.get("status") not in (
            StepStatus.COMPLETED.value,
            StepStatus.FAILED.value
        )

    def clear_task_state(self, task_id: str) -> bool:
        """Clear state for a specific task. Returns True if cleared."""
        if task_id in self._memory:
            del self._memory[task_id]
            self._save_memory()
            print(f"[TaskMemory] Cleared state for task: {task_id}")
            return True
        return False

    def update_step_status(
        self,
        task_id: str,
        step_index: int,
        status: Union[str, StepStatus],
        error_message: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update the status of a specific step.

        Args:
            task_id: The task identifier
            step_index: Index of the step to update
            status: New status (PENDING, IN_PROGRESS, COMPLETED, FAILED)
            error_message: Optional error message for FAILED status

        Returns:
            Updated task plan or None if task not found
        """
        if task_id not in self._memory:
            return None

        status_str = status.value if isinstance(status, StepStatus) else status
        if status_str not in [s.value for s in StepStatus]:
            raise ValueError(f"Invalid status: {status_str}")

        plan = self._memory[task_id]
        steps = plan.get("steps", [])

        if step_index < 0 or step_index >= len(steps):
            raise IndexError(f"Step index {step_index} out of range")

        step = steps[step_index]
        step["status"] = status_str

        if error_message and status_str == StepStatus.FAILED.value:
            step["last_error"] = error_message

        now = datetime.now().isoformat()
        if status_str == StepStatus.IN_PROGRESS.value and step["started_at"] is None:
            step["started_at"] = now
        if status_str in (StepStatus.COMPLETED.value, StepStatus.FAILED.value):
            step["completed_at"] = now

        # Update current step index and overall plan status
        if status_str == StepStatus.IN_PROGRESS.value:
            plan["current_step_index"] = step_index
            plan["execution_state"] = ExecutionState.RUNNING.value
        elif status_str == StepStatus.COMPLETED.value:
            # Move to next step if all prior steps are completed
            pending_steps = [
                s for s in steps if s["status"] != StepStatus.COMPLETED.value
            ]
            if not pending_steps:
                plan["status"] = StepStatus.COMPLETED.value
                plan["execution_state"] = ExecutionState.COMPLETED.value
                plan["requires_confirmation"] = False
            else:
                next_pending = min(
                    s["index"] for s in pending_steps if s["status"] == StepStatus.PENDING.value
                ) if any(s["status"] == StepStatus.PENDING.value for s in pending_steps) else step_index + 1
                plan["current_step_index"] = next_pending
        elif status_str == StepStatus.FAILED.value:
            plan["status"] = StepStatus.FAILED.value

        plan["updated_at"] = now
        self._save_memory()
        return plan

    def update_step_retry(
        self,
        task_id: str,
        step_index: int,
        retry_stage: Union[str, RetryStage],
        increment_count: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Update retry state for a specific step.

        Args:
            task_id: The task identifier
            step_index: Index of the step
            retry_stage: Current retry stage
            increment_count: Whether to increment the retry counter

        Returns:
            Updated task plan or None if task not found
        """
        if task_id not in self._memory:
            return None

        plan = self._memory[task_id]
        steps = plan.get("steps", [])

        if step_index < 0 or step_index >= len(steps):
            raise IndexError(f"Step index {step_index} out of range")

        step = steps[step_index]
        stage_str = retry_stage.value if isinstance(retry_stage, RetryStage) else retry_stage
        step["retry_stage"] = stage_str

        if increment_count:
            step["retry_count"] = step.get("retry_count", 0) + 1
            plan["total_retries"] = plan.get("total_retries", 0) + 1

        # Update plan execution state based on retry stage
        if stage_str == RetryStage.STAGE_2.value:
            plan["execution_state"] = ExecutionState.PAUSED_CONFIRMATION.value
            plan["requires_confirmation"] = True
            step_description = step.get("description", "Unknown step")
            step["status"] = StepStatus.FAILED.value
            plan["confirmation_prompt"] = (
                f"Step [{step_index}] failed twice. Try again? "
                f"Description: {step_description[:50]}... "
                f"[Confirm/Cancel]"
            )

        plan["updated_at"] = datetime.now().isoformat()
        self._save_memory()
        return plan

    def confirm_step_retry(self, task_id: str, step_index: int, confirm: bool) -> Optional[Dict[str, Any]]:
        """
        Handle user confirmation for a retry decision.

        Args:
            task_id: The task identifier
            step_index: Index of the step to confirm/cancel
            confirm: True to retry, False to cancel

        Returns:
            Updated task plan or None if task not found
        """
        if task_id not in self._memory:
            return None

        plan = self._memory[task_id]
        steps = plan.get("steps", [])

        if step_index < 0 or step_index >= len(steps):
            raise IndexError(f"Step index {step_index} out of range")

        step = steps[step_index]

        if confirm:
            # Reset for retry
            step["status"] = StepStatus.PENDING.value
            step["retry_stage"] = RetryStage.NONE.value
            step["retry_count"] = 0
            plan["execution_state"] = ExecutionState.RUNNING.value
            plan["requires_confirmation"] = False
            plan["confirmation_prompt"] = None
        else:
            # Cancel - mark as failed
            step["status"] = StepStatus.FAILED.value
            plan["status"] = StepStatus.FAILED.value
            plan["execution_state"] = ExecutionState.FAILED.value
            plan["requires_confirmation"] = False
            plan["confirmation_prompt"] = None

        plan["updated_at"] = datetime.now().isoformat()
        self._save_memory()
        return plan

    def get_pending_step(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the first pending step for a task.

        Args:
            task_id: The task identifier

        Returns:
            The pending step dict or None if no pending steps or task not found
        """
        if task_id not in self._memory:
            return None

        plan = self._memory[task_id]
        steps = plan.get("steps", [])

        for step in steps:
            if step["status"] == StepStatus.PENDING.value:
                return step

        return None

    def get_plan(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the full plan for a task."""
        return self._memory.get(task_id)

    def delete_plan(self, task_id: str) -> bool:
        """Delete a task plan. Returns True if deleted, False if not found."""
        if task_id in self._memory:
            del self._memory[task_id]
            self._save_memory()
            return True
        return False

    def list_tasks(self) -> List[str]:
        """List all task IDs in memory."""
        return list(self._memory.keys())

    def reset_memory(self) -> None:
        """Clear all task memory."""
        self._memory = {}
        self._save_memory()


class TaskPlanner:
    """
    LLM-driven task planner that breaks user prompts into atomic steps.
    Uses existing LLMProcessor for API calls with rate limit handling.
    """

    SYSTEM_PROMPT = (
        "You are an autonomous task breakdown agent. "
        "Break the user's prompt into atomic, actionable steps. "
        "Return ONLY a valid JSON array of strings. "
        "No markdown, no conversational text."
    )

    FALLBACK_PROMPT_TEMPLATE = (
        "The previous request failed to return valid JSON. "
        "Return a valid JSON array containing exactly one string: "
        "the user's original prompt as a single step. "
        "Example: [\"User's original prompt here\"]"
    )

    def __init__(self) -> None:
        self._key_manager = KeyManager()
        self._llm = LLMProcessor(self._key_manager)

    def generate_plan(self, user_prompt: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a task plan from a user prompt using LLM.

        Args:
            user_prompt: The user's task description
            task_id: Optional task ID (generated if not provided)

        Returns:
            A task plan dictionary with generated steps
        """
        task_id = task_id or self._generate_task_id()

        try:
            steps = self._call_llm_for_plan(user_prompt)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[TaskPlanner] JSON parsing failed: {e}. Using fallback single-step plan.")
            steps = [user_prompt]
        except Exception as e:
            print(f"[TaskPlanner] LLM call failed: {e}. Using fallback single-step plan.")
            steps = [user_prompt]

        memory = TaskMemory()
        return memory.create_plan(task_id, steps)

    def _call_llm_for_plan(self, user_prompt: str) -> List[str]:
        """
        Call LLM to generate steps. Raises exception on failure.

        Args:
            user_prompt: User's task description

        Returns:
            List of step strings

        Raises:
            JSONDecodeError: If LLM returns invalid JSON
            ValueError: If parsed result is not a list of strings
            Exception: If LLM call fails entirely
        """
        response = self._llm.generate_response(
            user_text=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
        )

        # Check for error responses from LLMProcessor
        if response.startswith("[") and "error" in response.lower():
            raise Exception(f"LLM error: {response}")
        if "No Groq API keys configured" in response:
            raise Exception("LLM not configured: No API keys available")
        if "All configured Groq keys hit rate limits" in response:
            raise Exception("Rate limit: All API keys exhausted")

        # Clean up response - remove markdown code blocks if present
        cleaned = self._clean_json_response(response)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try once more with a more explicit prompt
            fallback_response = self._llm.generate_response(
                user_text=f"Convert this to valid JSON array: {cleaned}",
                system_prompt="Return ONLY a valid JSON array of strings. No markdown.",
            )
            cleaned = self._clean_json_response(fallback_response)
            parsed = json.loads(cleaned)

        if not isinstance(parsed, list):
            raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")

        # Ensure all items are strings
        steps = [str(item) for item in parsed if item is not None]

        if not steps:
            raise ValueError("Empty step list returned from LLM")

        return steps

    def _clean_json_response(self, response: str) -> str:
        """Extract JSON from markdown code blocks or clean the string."""
        response = response.strip()

        # Remove markdown code blocks
        if response.startswith("```"):
            lines = response.split("\n")
            # Find first and last code fence
            start_idx = 0
            end_idx = len(lines)

            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    if start_idx == 0 and i == 0:
                        start_idx = i + 1
                    else:
                        end_idx = i
                        break

            response = "\n".join(lines[start_idx:end_idx]).strip()

        # Remove any leading/trailing whitespace and common prefixes
        response = response.strip()
        if response.lower().startswith("json"):
            response = response[4:].strip()

        return response

    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        return f"task_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"


@dataclass
class StepResult:
    """Result of executing a single step."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    retry_stage: RetryStage = RetryStage.NONE


class TaskExecutor:
    """
    Executes task plans with 2-stage retry machine for robust error handling.

    Stage 1 (Silent Retry): Automatic retry with fresh context on first failure
    Stage 2 (Confirmation): Pause and wait for user confirmation after second failure
    """

    def __init__(self, memory: Optional[TaskMemory] = None) -> None:
        self._memory = memory or TaskMemory()
        self._key_manager = KeyManager()
        self._current_task_id: Optional[str] = None
        self._execution_log: List[Dict[str, Any]] = []

    def execute_task(
        self,
        task_id: str,
        step_executor: Callable[[str, int, Dict[str, Any]], StepResult],
    ) -> Dict[str, Any]:
        """
        Execute all pending steps of a task with retry logic.

        Args:
            task_id: The task to execute
            step_executor: Callable that executes a single step.
                           Signature: (task_id, step_index, step_data) -> StepResult

        Returns:
            Final task plan state
        """
        self._current_task_id = task_id
        self._execution_log = []

        plan = self._memory.get_plan(task_id)
        if not plan:
            raise ValueError(f"Task {task_id} not found")

        # Check if task requires confirmation (Stage 2 paused)
        if plan.get("requires_confirmation"):
            print(f"[TaskExecutor] Task {task_id} is awaiting confirmation")
            return plan

        steps = plan.get("steps", [])
        current_idx = plan.get("current_step_index", 0)

        # Mark task as running
        if plan.get("execution_state") == ExecutionState.IDLE.value:
            plan["execution_state"] = ExecutionState.RUNNING.value
            plan["started_at"] = datetime.now().isoformat()
            self._memory._save_memory()

        for idx in range(current_idx, len(steps)):
            step = steps[idx]
            if step["status"] == StepStatus.COMPLETED.value:
                continue

            result = self._execute_step_with_retry(
                task_id, idx, step, step_executor
            )

            # Check if we need to pause for confirmation (Stage 2)
            if result.retry_stage == RetryStage.STAGE_2:
                updated_plan = self._memory.get_plan(task_id)
                print(f"[TaskExecutor] Paused at step {idx} awaiting confirmation")
                return updated_plan

            if not result.success and result.retry_stage == RetryStage.NONE:
                # Step failed and user cancelled
                plan["execution_state"] = ExecutionState.FAILED.value
                self._memory._save_memory()
                return plan

        # All steps completed
        plan = self._memory.get_plan(task_id)
        if plan:
            plan["execution_state"] = ExecutionState.COMPLETED.value
            plan["completed_at"] = datetime.now().isoformat()
            self._memory._save_memory()

        return plan or {}

    def _execute_step_with_retry(
        self,
        task_id: str,
        step_index: int,
        step: Dict[str, Any],
        step_executor: Callable[[str, int, Dict[str, Any]], StepResult],
    ) -> StepResult:
        """
        Execute a single step with 2-stage retry protocol.

        Args:
            task_id: Task identifier
            step_index: Index of current step
            step: Step data dictionary
            step_executor: Function to execute the step

        Returns:
            StepResult with outcome and retry stage
        """
        step_desc = step.get("description", "Unknown step")
        retry_count = step.get("retry_count", 0)

        # Mark step as in progress
        self._memory.update_step_status(task_id, step_index, StepStatus.IN_PROGRESS)

        # Stage 0: First attempt
        print(f"[TaskExecutor] Executing step {step_index}: {step_desc[:50]}...")
        result = step_executor(task_id, step_index, step)

        if result.success:
            self._memory.update_step_status(task_id, step_index, StepStatus.COMPLETED)
            self._log_execution(task_id, step_index, "success", None)
            return result

        # Stage 1: Silent retry (first failure)
        error_msg = result.error or "Unknown error"
        print(f"[TaskExecutor] Step {step_index} failed: {error_msg}")
        print(f"[TaskExecutor] Stage 1: Silent retry with fresh context...")

        self._memory.update_step_status(
            task_id, step_index, StepStatus.FAILED, error_message=error_msg
        )
        self._memory.update_step_retry(
            task_id, step_index, RetryStage.STAGE_1, increment_count=True
        )

        # Force fresh key rotation for retry
        self._key_manager.get_next_groq_key()

        # Retry with fresh context
        result = step_executor(task_id, step_index, step)

        if result.success:
            print(f"[TaskExecutor] Step {step_index} succeeded on retry")
            self._memory.update_step_status(task_id, step_index, StepStatus.COMPLETED)
            self._log_execution(task_id, step_index, "retry_success", None)
            return result

        # Stage 2: Pause for confirmation
        error_msg = result.error or "Unknown error on retry"
        print(f"[TaskExecutor] Step {step_index} failed again: {error_msg}")
        print(f"[TaskExecutor] Stage 2: Pausing for user confirmation")

        self._memory.update_step_retry(
            task_id, step_index, RetryStage.STAGE_2, increment_count=False
        )
        self._memory.update_step_status(
            task_id, step_index, StepStatus.FAILED, error_message=error_msg
        )
        self._log_execution(task_id, step_index, "awaiting_confirmation", error_msg)

        return StepResult(
            success=False,
            error=error_msg,
            retry_stage=RetryStage.STAGE_2,
        )

    def _log_execution(
        self,
        task_id: str,
        step_index: int,
        outcome: str,
        error: Optional[str],
    ) -> None:
        """Log execution event for audit trail."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "step_index": step_index,
            "outcome": outcome,
            "error": error,
        }
        self._execution_log.append(log_entry)

    def confirm_retry(self, task_id: str, step_index: int, confirm: bool) -> Dict[str, Any]:
        """
        Handle user confirmation for a retry decision.

        Args:
            task_id: The task identifier
            step_index: Index of the step
            confirm: True to retry, False to cancel

        Returns:
            Updated task plan
        """
        if confirm:
            print(f"[TaskExecutor] User confirmed retry for step {step_index}")
            self._memory.confirm_step_retry(task_id, step_index, confirm=True)
        else:
            print(f"[TaskExecutor] User cancelled retry for step {step_index}")
            self._memory.confirm_step_retry(task_id, step_index, confirm=False)

        return self._memory.get_plan(task_id) or {}

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the execution log for the current session."""
        return self._execution_log.copy()

    def get_current_task_id(self) -> Optional[str]:
        """Get the currently executing task ID."""
        return self._current_task_id


# Convenience functions for direct usage
def create_task_planner() -> TaskPlanner:
    """Factory function to create a TaskPlanner instance."""
    return TaskPlanner()


def create_task_memory(memory_file: Optional[str] = None) -> TaskMemory:
    """Factory function to create a TaskMemory instance."""
    return TaskMemory(memory_file)


def create_task_executor(memory: Optional[TaskMemory] = None) -> TaskExecutor:
    """Factory function to create a TaskExecutor instance."""
    return TaskExecutor(memory)


def plan_and_store(
    user_prompt: str,
    task_id: Optional[str] = None,
    is_new_task: bool = True
) -> Dict[str, Any]:
    """
    One-shot function to plan and store a task.

    Args:
        user_prompt: User's task description
        task_id: Optional custom task ID
        is_new_task: If True, clears existing state for this task_id

    Returns:
        The created task plan
    """
    planner = TaskPlanner()
    task_id = task_id or planner._generate_task_id()

    memory = TaskMemory()

    # Check if resuming or creating new
    if not is_new_task and memory.is_task_active(task_id):
        return memory.get_plan(task_id) or {}

    try:
        steps = planner._call_llm_for_plan(user_prompt)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[plan_and_store] JSON parsing failed: {e}. Using fallback.")
        steps = [user_prompt]
    except Exception as e:
        print(f"[plan_and_store] LLM call failed: {e}. Using fallback.")
        steps = [user_prompt]

    return memory.create_plan(task_id, steps, is_new_task=is_new_task)
