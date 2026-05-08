"""
LLM SanityCheck node (v2) — with Command-based Handoff.

Key improvement: Uses Command() for atomic state update + routing,
instead of returning state dict and relying on conditional edges.

This enables:
1. Atomic state update (no intermediate checkpoint between sanity_check and next node)
2. Direct routing via Command(goto=...) without conditional edge evaluation
3. Cleaner reflection loop control
"""
from __future__ import annotations

from loguru import logger
from langgraph.types import Command

from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.observability.decorators import traced_node
from app.graph.handoff import (
    command_handoff_to_reflect,
    command_handoff_to_finalize,
)


@traced_node("sanity_check")
async def run(state: dict) -> Command:
    """
    Validate TSMixer prediction consistency with PlantResponse.

    Returns Command object for atomic state update + routing:
    - Command(goto="finalize", update={...}) if consistent or max iterations
    - Command(goto="plant_response", update={...}) if inconsistent (reflection)
    """
    tsmixer_prediction = state.get("tsmixer_prediction", 5.0)
    plant_response = state.get("plant_response")
    env_data = state.get("env_data", {})
    rag_advice = state.get("rag_advice")
    run_check = state.get("options", {}).get("run_sanity_check", True)
    iteration_count = state.get("iteration_count", 0)

    # Skip check if disabled or no plant_response
    if not run_check or not plant_response:
        logger.info("[sanity_check] 跳过 SanityCheck")
        return command_handoff_to_finalize(
            sanity_result=None,
            iteration_count=iteration_count,
        )

    try:
        weekly_context = await memory_service.get_weekly_prompt_block()

        result = await llm_service.sanity_check(
            tsmixer_prediction=tsmixer_prediction,
            plant_response=plant_response,
            env_data=env_data,
            weekly_context=weekly_context,
            rag_advice=rag_advice,
        )

        result_dict = result.model_dump()
        is_consistent = result.is_consistent

        logger.info(
            f"[sanity_check] consistent={is_consistent}, "
            f"adjusted={result.adjusted_value:.2f}, iteration={iteration_count}"
        )

        # ── Handoff decision ────────────────────────────
        if is_consistent or iteration_count >= 3:
            # Consistent OR max iterations reached → finalize
            if iteration_count >= 3 and not is_consistent:
                logger.warning(
                    f"[sanity_check] 达到最大反思次数({iteration_count})，强制放行"
                )
            return command_handoff_to_finalize(
                sanity_result=result_dict,
                iteration_count=iteration_count + 1,
            )
        else:
            # Inconsistent → reflection loop back to plant_response
            logger.info(
                f"[sanity_check] 不一致，反思循环第{iteration_count+1}轮"
            )
            return command_handoff_to_reflect(
                sanity_result=result_dict,
                adjusted_value=result.adjusted_value,
                iteration_count=iteration_count,
            )

    except Exception as e:
        logger.error(f"[sanity_check] 失败: {e}")
        # On error → finalize with warning
        return command_handoff_to_finalize(
            sanity_result=None,
            iteration_count=iteration_count,
        )
