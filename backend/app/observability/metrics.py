"""Central Prometheus metric definitions for AgriAgent."""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, Info


# HTTP/API
HTTP_REQUESTS = Counter(
    "agri_http_requests_total",
    "Total HTTP requests served by the FastAPI backend",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION = Histogram(
    "agri_http_request_duration_seconds",
    "HTTP request latency by route",
    ["method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30],
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "agri_http_requests_in_progress",
    "In-flight HTTP requests",
    ["method", "path"],
)
HTTP_EXCEPTIONS = Counter(
    "agri_http_exceptions_total",
    "Unhandled HTTP request exceptions",
    ["method", "path", "error_type"],
)


# Pipeline/graph
PIPELINE_RUNS = Counter(
    "agri_pipeline_runs_total",
    "Total graph pipeline executions",
    ["version", "status"],
)
PIPELINE_DURATION = Histogram(
    "agri_pipeline_duration_seconds",
    "End-to-end graph pipeline latency",
    ["version"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)
NODE_DURATION = Histogram(
    "agri_node_duration_seconds",
    "Per-node execution latency",
    ["node_name", "status"],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60],
)
ACTIVE_GRAPH_RUNS = Gauge(
    "agri_active_graph_runs",
    "Currently executing graph runs",
)
AGENT_INTENT_ROUTES = Counter(
    "agri_agent_intent_routes_total",
    "Intent routes selected by the LangGraph router",
    ["intent"],
)
SUBAGENT_RUNS = Counter(
    "agri_subagent_runs_total",
    "Prompt-driven subagent executions",
    ["agent_name", "phase", "status"],
)


# LLM
LLM_CALLS = Counter(
    "agri_llm_calls_total",
    "Total OpenAI-compatible LLM calls",
    ["model", "purpose"],
)
LLM_LATENCY = Histogram(
    "agri_llm_latency_seconds",
    "LLM call latency",
    ["model", "purpose"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60],
)
LLM_TOKENS = Counter(
    "agri_llm_tokens_total",
    "Total tokens consumed",
    ["model", "direction"],
)
LLM_ERRORS = Counter(
    "agri_llm_errors_total",
    "LLM call errors",
    ["model", "purpose", "error_type"],
)


# RAG
RAG_QUERIES = Counter(
    "agri_rag_queries_total",
    "Total RAG queries",
    ["stage"],
)
RAG_CACHE_HITS = Counter(
    "agri_rag_cache_hits_total",
    "RAG cache hits",
)
RAG_CACHE_MISSES = Counter(
    "agri_rag_cache_misses_total",
    "RAG cache misses",
)
RAG_LATENCY = Histogram(
    "agri_rag_latency_seconds",
    "RAG retrieval latency",
    ["stage"],
    buckets=[0.05, 0.1, 0.5, 1, 5, 10],
)
RAG_RESULTS_COUNT = Histogram(
    "agri_rag_results_count",
    "Number of RAG results returned",
    buckets=[0, 1, 3, 5, 10, 20],
)


# YOLO/TSMixer
YOLO_INFERENCE = Histogram(
    "agri_yolo_inference_seconds",
    "YOLO inference latency",
    buckets=[0.5, 1, 2, 5, 10, 30],
)
YOLO_DETECTIONS = Histogram(
    "agri_yolo_detections_count",
    "Number of YOLO detections per image",
    ["class_name"],
    buckets=[0, 1, 5, 10, 20, 50],
)
TSMIXER_INFERENCE = Histogram(
    "agri_tsmixer_inference_seconds",
    "TSMixer inference latency",
    buckets=[0.01, 0.05, 0.1, 0.5, 1],
)
TSMIXER_PREDICTION = Histogram(
    "agri_tsmixer_prediction_value",
    "TSMixer predicted irrigation amount in L per square meter",
    buckets=[0.5, 1, 2, 3, 5, 7, 10, 15],
)


# MCP
MCP_TOOL_CALLS = Counter(
    "agri_mcp_tool_calls_total",
    "MCP tool calls",
    ["tool_name", "status"],
)
MCP_TOOL_LATENCY = Histogram(
    "agri_mcp_tool_latency_seconds",
    "MCP tool call latency",
    ["tool_name", "status"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 30],
)
MCP_TOOLS_AVAILABLE = Gauge(
    "agri_mcp_tools_available",
    "Number of tools exposed through MultiServerMCPClient",
)


# Knowledge upload/indexing
KNOWLEDGE_UPLOADS = Counter(
    "agri_knowledge_uploads_total",
    "Uploaded knowledge documents",
    ["file_type", "status"],
)
KNOWLEDGE_CHUNKS_INDEXED = Counter(
    "agri_knowledge_chunks_indexed_total",
    "Knowledge chunks indexed by backend",
    ["backend"],
)
KNOWLEDGE_ASSETS_INDEXED = Counter(
    "agri_knowledge_assets_indexed_total",
    "PDF-derived image assets indexed by backend",
    ["backend"],
)
KNOWLEDGE_INDEX_DURATION = Histogram(
    "agri_knowledge_index_duration_seconds",
    "Knowledge upload extraction and indexing latency",
    ["status"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120],
)


# SSE
SSE_EVENTS = Counter(
    "agri_sse_events_total",
    "SSE events emitted by the Agent API",
    ["event_type", "status"],
)


# Runtime/system
MEMORY_EPISODES = Gauge(
    "agri_memory_episodes_count",
    "Number of stored episodes",
)
COMPONENT_UP = Gauge(
    "agri_component_up",
    "Runtime component health status, where 1 means connected/up",
    ["component", "backend"],
)
COMPONENT_ERROR = Gauge(
    "agri_component_error",
    "Runtime component error status, where 1 means an error is present",
    ["component", "backend"],
)
SYSTEM_INFO = Info(
    "agri_system",
    "System information",
)
SERVICE_INFO = Info(
    "agri_service",
    "AgriAgent service runtime metadata",
)
