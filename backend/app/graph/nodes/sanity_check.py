"""
LLM SanityCheck node — validates TSMixer prediction against PlantResponse.

Wraps: llm_service.sanity_check
"""
from __future__ import annotations

from loguru import logger

from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.observability.decorators import traced_node


@traced_node("sanity_check")
async def run(state: dict) -> dict:
    """Validate TSMixer prediction consistency with PlantResponse."""
    tsmixer_prediction = state.get("tsmixer_prediction", 5.0)
    plant_response = state.get("plant_response")
    env_data = state.get("env_data", {})
    rag_advice = state.get("rag_advice")
    run_check = state.get("options", {}).get("run_sanity_check", True)
    iteration_count = state.get("iteration_count", 0)

    if not run_check or not plant_response:
        logger.info("[sanity_check] 跳过 SanityCheck")
        return {
            "sanity_check": None,
            "sanity_passed": True,
            "node_trace": [{"node": "sanity_check", "status": "skipped"}],
        }

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

        return {
            "sanity_check": result_dict,
            "sanity_passed": is_consistent,
            "iteration_count": iteration_count + 1,
            "node_trace": [{
                "node": "sanity_check",
                "status": "ok",
                "consistent": is_consistent,
                "adjusted_value": round(result.adjusted_value, 2),
                "iteration": iteration_count,
            }],
        }

    except Exception as e:
        logger.error(f"[sanity_check] 失败: {e}")
        return {
            "sanity_check": None,
            "sanity_passed": True,
            "warnings": [f"SanityCheck 执行失败: {e}，默认通过"],
            "node_trace": [{"node": "sanity_check", "status": "error", "detail": str(e)}],
        }
