"""
Manager Agent for Krystal AI Core.

Acts as the 'HR/Manager' overseeing Worker agents. Provides:
- Project monitoring and status summaries
- Error auditing with technical root-cause analysis
- Iron Guard principles applied to oversight reporting
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import orchestrator components
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


_orchestrator = _load_sibling_module("krystal_manager._orchestrator", "orchestrator.py")

TaskMemory = _orchestrator.TaskMemory
StepStatus = _orchestrator.StepStatus
RetryStage = _orchestrator.RetryStage
ExecutionState = _orchestrator.ExecutionState

MEMORY_FILE = Path("agent_memory.json")


@dataclass
class ErrorReport:
    """Structured error report with technical root-cause analysis."""
    error_type: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    technical_summary: str
    probable_cause: str
    recommended_action: str
    affected_step: Optional[int] = None
    task_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ProjectSummary:
    """Human-readable summary of project execution status."""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    in_progress_tasks: int
    awaiting_confirmation: int
    total_steps: int
    completed_steps: int
    failed_steps: int
    total_retries: int
    summary_text: str
    active_tasks: List[Dict[str, Any]] = field(default_factory=list)
    recent_failures: List[ErrorReport] = field(default_factory=list)


class ManagerAgent:
    """
    HR/Manager Agent overseeing Worker agent execution.

    Monitors agent_memory.json and execution logs, providing:
    - Real-time project status summaries
    - Technical error audits with root-cause analysis
    - Iron Guard-style risk reporting
    """

    # Error classification patterns with technical precision
    ERROR_PATTERNS = {
        "API_TIMEOUT": {
            "patterns": [r"timeout", r"timed out", r"connection.*refused", r"network.*error"],
            "severity": "HIGH",
            "category": "Infrastructure Failure",
        },
        "RATE_LIMIT": {
            "patterns": [r"rate limit", r"429", r"too many requests", r"quota exceeded"],
            "severity": "MEDIUM",
            "category": "API Rate Limiting",
        },
        "AUTH_FAILURE": {
            "patterns": [r"authentication", r"unauthorized", r"401", r"api.*key.*invalid"],
            "severity": "CRITICAL",
            "category": "Authentication Failure",
        },
        "JSON_PARSE_ERROR": {
            "patterns": [r"json.*decode", r"json.*parse", r"invalid.*json", r"expecting.*delimiter"],
            "severity": "MEDIUM",
            "category": "Data Format Error",
        },
        "VALIDATION_ERROR": {
            "patterns": [r"validation", r"invalid.*input", r"schema.*error", r"type.*error"],
            "severity": "MEDIUM",
            "category": "Input Validation Failure",
        },
        "LLM_CONFIG_ERROR": {
            "patterns": [r"no.*api.*key", r"not.*configured", r"groq.*error", r"llm.*error"],
            "severity": "CRITICAL",
            "category": "LLM Configuration Failure",
        },
        "EXECUTION_ERROR": {
            "patterns": [r"exception", r"runtime.*error", r"execution.*failed"],
            "severity": "HIGH",
            "category": "Runtime Execution Failure",
        },
    }

    def __init__(self, memory_file: Optional[Union[str, Path]] = None) -> None:
        self._memory_file = Path(memory_file) if memory_file else MEMORY_FILE
        self._memory = TaskMemory(self._memory_file)
        self._error_history: List[ErrorReport] = []

    def get_project_summary(self) -> ProjectSummary:
        """
        Generate a human-readable summary of all tasks.

        Returns:
            ProjectSummary with complete execution overview
        """
        task_ids = self._memory.list_tasks()

        total_tasks = len(task_ids)
        completed_tasks = 0
        failed_tasks = 0
        in_progress_tasks = 0
        awaiting_confirmation = 0

        total_steps = 0
        completed_steps = 0
        failed_steps = 0
        total_retries = 0

        active_tasks: List[Dict[str, Any]] = []
        recent_failures: List[ErrorReport] = []

        for task_id in task_ids:
            plan = self._memory.get_plan(task_id)
            if not plan:
                continue

            steps = plan.get("steps", [])
            execution_state = plan.get("execution_state", ExecutionState.IDLE.value)
            status = plan.get("status", StepStatus.PENDING.value)
            requires_confirmation = plan.get("requires_confirmation", False)

            total_steps += len(steps)
            total_retries += plan.get("total_retries", 0)

            # Task status categorization
            if status == StepStatus.COMPLETED.value:
                completed_tasks += 1
            elif status == StepStatus.FAILED.value:
                failed_tasks += 1
            elif execution_state == ExecutionState.RUNNING.value:
                in_progress_tasks += 1
                active_tasks.append({
                    "task_id": task_id,
                    "current_step": plan.get("current_step_index", 0),
                    "total_steps": len(steps),
                    "progress_percent": round(
                        (plan.get("current_step_index", 0) / len(steps)) * 100, 1
                    ) if steps else 0,
                    "status": "RUNNING",
                })
            elif requires_confirmation:
                awaiting_confirmation += 1
                active_tasks.append({
                    "task_id": task_id,
                    "current_step": plan.get("current_step_index", 0),
                    "total_steps": len(steps),
                    "progress_percent": round(
                        (plan.get("current_step_index", 0) / len(steps)) * 100, 1
                    ) if steps else 0,
                    "status": "AWAITING_CONFIRMATION",
                    "confirmation_prompt": plan.get("confirmation_prompt"),
                })

            # Step-level analysis
            for step in steps:
                if step["status"] == StepStatus.COMPLETED.value:
                    completed_steps += 1
                elif step["status"] == StepStatus.FAILED.value:
                    failed_steps += 1
                    # Capture recent failures for report
                    last_error = step.get("last_error")
                    if last_error:
                        error_report = self._analyze_error(
                            last_error,
                            affected_step=step.get("index"),
                            task_id=task_id,
                        )
                        recent_failures.append(error_report)

        # Generate human-readable summary text
        summary_text = self._generate_summary_text(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            in_progress_tasks=in_progress_tasks,
            awaiting_confirmation=awaiting_confirmation,
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            total_retries=total_retries,
        )

        # Limit recent failures to most significant
        recent_failures.sort(key=lambda x: self._severity_rank(x.severity), reverse=True)
        recent_failures = recent_failures[:5]

        return ProjectSummary(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            in_progress_tasks=in_progress_tasks,
            awaiting_confirmation=awaiting_confirmation,
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            total_retries=total_retries,
            summary_text=summary_text,
            active_tasks=active_tasks,
            recent_failures=recent_failures,
        )

    def audit_error(self, error_message: str, task_id: Optional[str] = None, step_index: Optional[int] = None) -> ErrorReport:
        """
        Perform technical error audit with root-cause analysis.

        Args:
            error_message: The raw error message
            task_id: Optional task identifier
            step_index: Optional step index

        Returns:
            ErrorReport with technical analysis
        """
        return self._analyze_error(error_message, task_id, step_index)

    def _analyze_error(
        self,
        error_message: str,
        task_id: Optional[str] = None,
        affected_step: Optional[int] = None,
    ) -> ErrorReport:
        """
        Analyze error message and classify with technical precision.

        Args:
            error_message: Raw error text
            task_id: Associated task
            affected_step: Step index if applicable

        Returns:
            Structured ErrorReport
        """
        error_lower = error_message.lower()

        # Match against known patterns
        matched_category = "UNKNOWN_ERROR"
        severity = "MEDIUM"

        for category, config in self.ERROR_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, error_lower):
                    matched_category = config["category"]
                    severity = config["severity"]
                    break
            if matched_category != "UNKNOWN_ERROR":
                break

        # Generate technical summary based on category
        technical_summary = self._generate_technical_summary(
            matched_category, error_message
        )

        # Determine probable cause
        probable_cause = self._determine_probable_cause(matched_category, error_message)

        # Recommend action
        recommended_action = self._recommend_action(matched_category, severity)

        report = ErrorReport(
            error_type=matched_category,
            severity=severity,
            technical_summary=technical_summary,
            probable_cause=probable_cause,
            recommended_action=recommended_action,
            affected_step=affected_step,
            task_id=task_id,
        )

        # Store in history
        self._error_history.append(report)

        return report

    def _generate_technical_summary(self, category: str, error_message: str) -> str:
        """Generate precise technical summary for error category."""
        summaries = {
            "API Timeout": (
                f"Network-layer timeout occurred during API request. "
                f"Error: {error_message[:100]}..."
            ),
            "API Rate Limiting": (
                f"HTTP 429 / Rate limit exceeded. Service throttling active. "
                f"Error: {error_message[:100]}..."
            ),
            "Authentication Failure": (
                f"Credential validation failed. API key invalid or expired. "
                f"Error: {error_message[:100]}..."
            ),
            "Data Format Error": (
                f"JSON parsing failed. LLM returned malformed/invalid JSON structure. "
                f"Error: {error_message[:100]}..."
            ),
            "Input Validation Failure": (
                f"Schema validation failed on input data. Type mismatch or missing field. "
                f"Error: {error_message[:100]}..."
            ),
            "LLM Configuration Failure": (
                f"LLM processor initialization failed. Missing or invalid API credentials. "
                f"Error: {error_message[:100]}..."
            ),
            "Runtime Execution Failure": (
                f"Unhandled exception during step execution. Runtime error in business logic. "
                f"Error: {error_message[:100]}..."
            ),
        }
        return summaries.get(category, f"Unclassified error: {error_message[:100]}...")

    def _determine_probable_cause(self, category: str, error_message: str) -> str:
        """Determine technical root cause based on error category."""
        causes = {
            "API Timeout": (
                "Network instability, server-side latency spike, or request payload too large. "
                "Could also indicate DNS resolution failure or firewall blocking."
            ),
            "API Rate Limiting": (
                "Exceeded API provider's requests-per-minute quota. "
                "Multiple keys exhausted simultaneously or burst traffic detected."
            ),
            "Authentication Failure": (
                "API key revoked, expired, or incorrectly configured in environment. "
                "May also indicate key rotation without system restart."
            ),
            "Data Format Error": (
                "LLM response contained conversational text, markdown formatting, or partial JSON. "
                "System prompt may need reinforcement or model temperature too high."
            ),
            "Input Validation Failure": (
                "Type mismatch in function parameters or missing required field in data structure. "
                "Schema drift between expected and actual data format."
            ),
            "LLM Configuration Failure": (
                "Environment variables not loaded, GROQ_KEY_* entries missing from .env, "
                "or KeyManager failed to initialize."
            ),
            "Runtime Execution Failure": (
                "Unanticipated edge case in business logic, null pointer dereference, "
                "or external dependency failure."
            ),
        }
        return causes.get(
            category,
            "Unknown root cause. Requires manual investigation of stack trace."
        )

    def _recommend_action(self, category: str, severity: str) -> str:
        """Recommend corrective action based on category and severity."""
        if severity == "CRITICAL":
            return (
                "IMMEDIATE ACTION REQUIRED: Check API credentials, verify .env configuration, "
                "and restart service. Escalate to system administrator."
            )

        actions = {
            "API Timeout": (
                "Implement exponential backoff with jitter. Check network connectivity. "
                "Consider increasing timeout thresholds or switching provider."
            ),
            "API Rate Limiting": (
                "Activate circuit breaker pattern. Switch to fallback provider. "
                "Reduce request frequency or implement request queue."
            ),
            "Authentication Failure": (
                "Verify GROQ_KEY_* environment variables. Regenerate API keys if necessary. "
                "Check key permissions and expiration dates."
            ),
            "Data Format Error": (
                "Strengthen system prompt with explicit JSON formatting instructions. "
                "Add output validation and retry with temperature=0. Consider model swap."
            ),
            "Input Validation Failure": (
                "Add input sanitization. Update schema validation. "
                "Add type checking before function calls."
            ),
            "LLM Configuration Failure": (
                "Verify .env file exists and is loaded. Check GROQ_KEY_1 through GROQ_KEY_N. "
                "Ensure KeyManager properly initialized."
            ),
            "Runtime Execution Failure": (
                "Add defensive null checks. Implement try/catch blocks. "
                "Add logging for debugging. Review recent code changes."
            ),
        }
        return actions.get(
            category,
            "Manual investigation required. Capture full stack trace and logs."
        )

    def _generate_summary_text(
        self,
        total_tasks: int,
        completed_tasks: int,
        failed_tasks: int,
        in_progress_tasks: int,
        awaiting_confirmation: int,
        total_steps: int,
        completed_steps: int,
        failed_steps: int,
        total_retries: int,
    ) -> str:
        """Generate human-readable summary text."""
        lines = []

        # Executive summary
        if total_tasks == 0:
            lines.append("No active tasks in the system.")
        else:
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            lines.append(
                f"PROJECT STATUS: {completed_tasks}/{total_tasks} tasks completed "
                f"({completion_rate:.1f}% completion rate)"
            )

            # Progress breakdown
            if in_progress_tasks > 0:
                lines.append(f"  - {in_progress_tasks} task(s) currently executing")
            if awaiting_confirmation > 0:
                lines.append(f"  - {awaiting_confirmation} task(s) awaiting user confirmation")
            if failed_tasks > 0:
                lines.append(f"  - {failed_tasks} task(s) failed (requires attention)")

            # Step-level detail
            step_completion = (completed_steps / total_steps * 100) if total_steps > 0 else 0
            lines.append(
                f"\nSTEP BREAKDOWN: {completed_steps}/{total_steps} steps completed "
                f"({step_completion:.1f}%)"
            )

            if failed_steps > 0:
                lines.append(f"  - {failed_steps} step(s) failed across all tasks")
            if total_retries > 0:
                lines.append(f"  - {total_retries} total retry attempts (resilience active)")

            # Iron Guard-style risk assessment
            risk_level = self._calculate_risk_level(
                failed_tasks, total_tasks, failed_steps, total_steps
            )
            lines.append(f"\nRISK ASSESSMENT: {risk_level}")

            if risk_level == "CRITICAL":
                lines.append(
                    "  ALERT: Multiple task failures detected. "
                    "Immediate manager review required."
                )
            elif risk_level == "HIGH":
                lines.append(
                    "  WARNING: Elevated failure rate. "
                    "Monitor closely and prepare rollback procedures."
                )
            elif risk_level == "MEDIUM":
                lines.append(
                    "  CAUTION: Some failures detected. "
                    "Review error audit for corrective action."
                )
            else:
                lines.append("  NOMINAL: System operating within normal parameters.")

        return "\n".join(lines)

    def _calculate_risk_level(
        self,
        failed_tasks: int,
        total_tasks: int,
        failed_steps: int,
        total_steps: int,
    ) -> str:
        """Calculate risk level using Iron Guard principles."""
        if total_tasks == 0:
            return "NOMINAL"

        task_failure_rate = failed_tasks / total_tasks if total_tasks > 0 else 0
        step_failure_rate = failed_steps / total_steps if total_steps > 0 else 0

        # Iron Guard thresholds
        if task_failure_rate >= 0.25 or failed_tasks >= 3:
            return "CRITICAL"
        elif task_failure_rate >= 0.15 or step_failure_rate >= 0.20:
            return "HIGH"
        elif task_failure_rate >= 0.05 or step_failure_rate >= 0.10:
            return "MEDIUM"
        else:
            return "LOW"

    def _severity_rank(self, severity: str) -> int:
        """Convert severity to numeric rank for sorting."""
        ranks = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return ranks.get(severity, 0)

    def get_error_history(self) -> List[ErrorReport]:
        """Get all audited errors from this session."""
        return self._error_history.copy()

    def clear_error_history(self) -> None:
        """Clear the error history."""
        self._error_history = []

    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed view of a specific task."""
        plan = self._memory.get_plan(task_id)
        if not plan:
            return None

        # Enrich with error audits
        steps = plan.get("steps", [])
        enriched_steps = []

        for step in steps:
            enriched_step = step.copy()
            if step.get("last_error"):
                error_report = self._analyze_error(
                    step["last_error"],
                    task_id=task_id,
                    affected_step=step.get("index"),
                )
                enriched_step["error_audit"] = {
                    "type": error_report.error_type,
                    "severity": error_report.severity,
                    "summary": error_report.technical_summary,
                    "probable_cause": error_report.probable_cause,
                    "recommended_action": error_report.recommended_action,
                }
            enriched_steps.append(enriched_step)

        return {
            "task_id": task_id,
            "created_at": plan.get("created_at"),
            "updated_at": plan.get("updated_at"),
            "status": plan.get("status"),
            "execution_state": plan.get("execution_state"),
            "requires_confirmation": plan.get("requires_confirmation", False),
            "confirmation_prompt": plan.get("confirmation_prompt"),
            "current_step_index": plan.get("current_step_index"),
            "total_retries": plan.get("total_retries", 0),
            "steps": enriched_steps,
        }


# Convenience factory function
def create_manager_agent(memory_file: Optional[str] = None) -> ManagerAgent:
    """Factory function to create a ManagerAgent instance."""
    return ManagerAgent(memory_file)


def get_project_summary() -> ProjectSummary:
    """One-shot function to get project summary."""
    agent = ManagerAgent()
    return agent.get_project_summary()


def audit_error(error_message: str, task_id: Optional[str] = None, step_index: Optional[int] = None) -> ErrorReport:
    """One-shot function to audit an error."""
    agent = ManagerAgent()
    return agent.audit_error(error_message, task_id, step_index)
