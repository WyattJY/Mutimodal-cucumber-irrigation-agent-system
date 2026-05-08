"""
Conditional edge functions for the irrigation pipeline graph.

4 conditional edges (matching AI_TRAVEL pattern):
1. route_after_load_env — cold start detection → skip or proceed
2. route_after_anomaly — severe anomaly → emergency or continue
3. route_after_sanity — reflection loop → retry or finalize (max 3 iterations)
4. route_after_rag — RAG recall sufficiency → proceed or back to collect

Each function takes the current state and returns the name of the next node.
"""
from __future__ import annotations


def route_after_load_env(state: dict) -> str:
    """
    Conditional Edge 1: After load_env node.

    - Cold start with no image → skip YOLO/TSMixer, go to RAG
    - Otherwise → normal YOLO path (parallel sub-agents)
    """
    options = state.get("options", {}) or {}
    if options.get("require_collect_agent"):
        return "collect_agent"
    return "perception_dispatch"  # Dispatch YOLO + RAG sub-agents, with mock fallback if no image.


def route_after_anomaly(state: dict) -> str:
    """
    Conditional Edge 2: After anomaly detection.

    - Severe anomaly → emergency finalization (skip sanity check)
    - Otherwise → normal sanity check
    """
    severity = state.get("anomaly_severity", "none")

    if severity == "severe":
        return "finalize_emergency"
    return "sanity_check"


def route_after_sanity(state: dict) -> str:
    """
    Conditional Edge 3: After sanity check (reflection loop).

    - Passed → finalize
    - Failed and iteration_count < 3 → retry plant_response (reflection)
    - Failed and iteration_count >= 3 → finalize anyway (with warning)

    Max iterations: 3 (matching AI_TRAVEL)
    """
    if state.get("sanity_passed", True):
        return "finalize"

    iteration_count = state.get("iteration_count", 0)
    if iteration_count < 3:
        return "plant_response"  # Reflection: re-evaluate

    return "finalize"  # Max iterations reached, force finalize


def route_after_rag(state: dict) -> str:
    """
    Conditional Edge 4: After RAG retrieval (recall sufficiency check).

    - Recall sufficient (>= 3 documents) → proceed to plan_agent
    - Recall insufficient → back to collect_agent for clarification

    This is the 4th conditional edge, matching AI_TRAVEL's pattern
    of routing back to collect when retrieval fails.
    """
    rag_results = state.get("rag_results", [])
    rag_recall_sufficient = state.get("rag_recall_sufficient", True)

    # Check if RAG recall is sufficient
    options = state.get("options", {}) or {}
    if (not rag_recall_sufficient or len(rag_results) < 3) and options.get("ask_clarification_on_low_recall"):
        return "collect_agent"  # Back to collect for clarification

    return "plan_agent"  # Proceed to plan generation
