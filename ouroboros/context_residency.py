"""Task-class residency classifiers for self-body context documents.

Leaf module (no dependencies beyond the task-contract helpers): owns the
class-aware residency decisions for ARCHITECTURE.md (v6.115.0) and
DEVELOPMENT.md (v6.116.0) in owner-max context mode. Extracted from
ouroboros/context.py to keep the context builder below the giant-file
threshold; context.py re-imports these names so call sites are unchanged.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from ouroboros.contracts.task_contract import normalize_bool


def _task_requires_development_context(task: Dict[str, Any]) -> bool:
    """Return whether low mode should inline the engineering handbook.

    Web chat tasks are direct-chat but still may ask for code/self-modification.
    Err toward preserving engineering competence unless a structured caller
    explicitly declares that this task does not need DEVELOPMENT.md.
    """
    explicit = task.get("context_requires_development")
    if explicit is not None:
        return normalize_bool(explicit)
    return str(task.get("type") or "") == "task" or not bool(task.get("_is_direct_chat"))


def _explicit_self_body_docs_flag(task: Dict[str, Any]) -> Optional[bool]:
    """Explicit context_requires_self_body_docs from the task or its contract;
    None when neither declares it."""
    explicit = task.get("context_requires_self_body_docs")
    if explicit is not None:
        return normalize_bool(explicit)
    contract = task.get("task_contract") if isinstance(task.get("task_contract"), dict) else {}
    explicit = contract.get("context_requires_self_body_docs") if isinstance(contract, dict) else None
    if explicit is not None:
        return normalize_bool(explicit)
    return None


def _task_requires_self_body_docs(task: Dict[str, Any]) -> bool:
    """Return True when the task is structurally about Ouroboros itself."""

    explicit = _explicit_self_body_docs_flag(task)
    if explicit is not None:
        return explicit
    contract = task.get("task_contract") if isinstance(task.get("task_contract"), dict) else {}
    task_type = str(task.get("type") or contract.get("task_type") or "").strip().lower()
    return task_type in {"evolution", "deep_self_review", "review"}


def _task_uses_external_context(task: Dict[str, Any]) -> bool:
    """Return True for structured headless/workspace/delegated task surfaces."""

    metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
    source = str(metadata.get("source") or task.get("source") or "").strip().lower()
    actor = str(task.get("actor_id") or metadata.get("actor_id") or "").strip().lower()
    delegation_role = str(task.get("delegation_role") or metadata.get("delegation_role") or "").strip().lower()
    if str(task.get("workspace_root") or metadata.get("workspace_root") or "").strip():
        return True
    if delegation_role == "subagent":
        return True
    if source in {"api_task", "cli", "scheduled_task", "skill_scheduled_task"}:
        return True
    if actor in {"cli", "scheduler"}:
        return True
    return False


def _task_architecture_full_resident(task: Dict[str, Any]) -> bool:
    """v6.115.0 (owner decision): does THIS task class keep ARCHITECTURE.md
    full-resident in owner-max?

    Exhaustive precedence table — every task dict resolves to exactly one
    class, and unknown/malformed shapes default to FULL (the conservative
    direction: today's behavior for anything the enumerated signals do not
    cover):

      1. explicit ``context_requires_self_body_docs`` (task or task_contract)
         wins in BOTH directions;
      2. externally-bound surfaces (``_task_uses_external_context``: a bound
         workspace — including a project task's auto-provisioned genesis tree —
         a subagent, or an external api/cli/scheduled surface) → navigation map;
      3. direct-chat turns (``_is_direct_chat``, owner-confirmed nav class) →
         navigation map;
      4. otherwise (default-lane pooled tasks, evolution, deep self-review,
         review, unknown shapes) → FULL.
    """
    explicit = _explicit_self_body_docs_flag(task)
    if explicit is not None:
        return explicit
    if _task_uses_external_context(task):
        return False
    if bool(task.get("_is_direct_chat")):
        return False
    return True


def _task_development_full_resident(task: Dict[str, Any]) -> bool:
    """v6.116.0 (owner decision): does THIS task class keep DEVELOPMENT.md
    full-resident in owner-max?

    Same precedence skeleton as ``_task_architecture_full_resident`` (the
    owner-approved mirror, lever №1 of the context campaign):

      1. explicit ``context_requires_self_body_docs`` wins in BOTH directions;
      2. direct-chat turns → navigation map + on-demand pointer (owner-confirmed
         nav class for the handbook too);
      3. externally-bound surfaces → True here, but harmless: the D-DEV block
         keeps that class pointer-only via ``include_development=False``; a bare
         pointer is the implemented external posture (no nav map added);
      4. otherwise (pooled, evolution, review, unknown shapes) → FULL.

    Only the rendered form of ``include_development=True`` branches depends on
    this flag; an explicit ``context_requires_development=False`` still takes
    the pointer-only path regardless.
    """
    explicit = _explicit_self_body_docs_flag(task)
    if explicit is not None:
        return explicit
    if bool(task.get("_is_direct_chat")):
        return False
    return True
