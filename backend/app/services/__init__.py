"""Service package.

Services are intentionally not imported eagerly. YOLO and TSMixer load model
weights, so eager imports make API startup and tests unnecessarily heavy.
"""

__all__ = [
    "llm_service",
    "yolo_service",
    "tsmixer_service",
    "memory_service",
    "prediction_service",
    "weekly_summary_service",
    "rag_service",
]
