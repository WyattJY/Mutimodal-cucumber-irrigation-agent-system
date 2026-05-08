# 温室黄瓜灌水决策智能体 AI_TRAVEL 技术栈覆盖说明

## 改造边界

本项目保持业务目标不变：**基于多模态融合的温室黄瓜灌水决策智能体研究**。`AI_TRAVEL` 在这里指复用其 Agent 工程技术栈与设计方法，不是把业务改成旅游规划。

源项目已从 `G:\master_tools\projects\cucumber-irrigation-linux` 复制到：

```text
G:\AI_TRAVEL\cucumber-irrigation-linux
```

复制后已清理 `.env`、`.git`、虚拟环境、运行缓存、旧 MongoDB 数据目录和我临时验证生成的 `.venv`。

## 核心架构

当前主图入口：

```text
backend/app/graph/builder_v2.py
```

执行链路：

```text
Router
  -> daily_decision_subgraph
      -> load_env
      -> perception_dispatch
          -> Send(yolo_agent) || Send(rag_perception_agent)
      -> perception_join
      -> prediction_dispatch
          -> Send(tsmixer_agent) || Send(rag_prediction_agent)
      -> prediction_join
      -> plan_agent
      -> finalize
```

可选 Handoff：

```text
collect_agent -> perception_dispatch
plan_agent -> plant_response/review or finalize
sanity_check -> reflection loop or finalize
```

## 简历覆盖矩阵

| 简历表述 | 当前代码落点 |
|---|---|
| Router + Handoffs + Subagents | `backend/app/graph/builder_v2.py`, `backend/app/graph/handoff.py`, `backend/app/graph/router.py` |
| 3 个 SubAgent 并行调度 | `yolo_agent`, `rag_agent`, `tsmixer_agent`；两阶段 `YOLO || RAG`、`TSMixer || RAG` 使用 LangGraph `Send` |
| YOLO11n-FCHL + 视觉表型 | `backend/app/graph/subagent.py`, `backend/app/services/yolo_service.py` |
| TSMixer 多模态时序预测 | `backend/app/graph/feature_builder.py`, `backend/app/services/tsmixer_service.py` |
| 11 维多模态特征，96 天窗口 | `feature_builder.py` 明确定义 `3 环境 + 7 YOLO + 1 历史灌水` 和 `WINDOW_SIZE=96` |
| Agentic RAG | `backend/app/services/rag_service.py`，支持 Redis cache、ChromaDB 查询和 keyword/BM25 fallback |
| PostgreSQL/Redis/ChromaDB | `backend/app/infra/postgres.py`, `redis_cache.py`, `chroma_store.py`, `docker-compose.yml` |
| FastAPI + SSE | `backend/app/api/v1/agent.py` 提供 `/api/agent/decision` 和 `/api/agent/decision/stream` |
| MCP 工具化 | `backend/app/services/mcp_client.py`, `backend/mcp_servers/*.py` |
| Prometheus/Grafana | `backend/app/observability/metrics.py`, `ops/prometheus.yml`, `ops/grafana/**`, `/metrics` |
| Qwen/OpenAI-compatible LLM | `.env.example`, `backend/app/core/config.py`, `backend/app/services/llm_service.py` |

## 新增可验证接口

```text
GET  /api/agent/stack
POST /api/agent/decision
POST /api/agent/decision/stream
GET  /api/health
GET  /metrics
```

示例请求：

```json
{
  "date": "2024-05-07",
  "user_input": "run irrigation decision",
  "env_data": {
    "temperature": 25,
    "humidity": 70,
    "light": 50000,
    "growth_stage": "fruiting"
  },
  "history_irrigation": [4.5, 5.0, 5.2],
  "options": {
    "save_episode": false,
    "save_response": false
  }
}
```

## 工程栈口径

目标生产栈：

```text
FastAPI + SSE
LangGraph + Checkpointer/Store
PostgreSQL
Redis
ChromaDB
FastMCP / MCP Client
Qwen/OpenAI-compatible API
Prometheus + Grafana + Loguru + optional LangSmith
React/Vite frontend
```

本地无外部服务时的降级：

```text
PostgreSQL -> LangGraph MemorySaver/InMemoryStore
Redis -> process memory cache
ChromaDB -> keyword/BM25-style local fallback
MCP adapters missing -> MCP health reports unavailable, graph still works
LLM key missing -> deterministic plan fallback
image missing -> YOLO mock visual metrics fallback
```

## 审核结论

原完整 MD 的设计方向可行，但之前最大问题是“目标架构高于代码证据”。本次改造已经把核心证据落到代码：主图可编译、Subagent 可并行、特征构造可测试、RAG/Redis/Chroma/PostgreSQL/MCP/SSE/Prometheus 都有明确代码入口和部署配置。

仍需谨慎的点：简历中的具体实验数字，例如 mAP 提升、万级 chunks、节水增产比例，需要继续保留原论文/实验脚本或数据证明；本次工程改造负责把系统架构和演示闭环补齐，不伪造实验指标。
