# V2 技术栈覆盖核验

本版本对应简历中的“基于多模态融合的温室黄瓜灌水决策智能体研究 / 多 Agent 协作灌溉系统”工程实现。核验范围为当前源码目录：

`G:\AI_TRAVEL\cucumber-irrigation-linux`

## 结论

当前工程已经覆盖简历技术栈中的核心工程能力：LangGraph 多 Agent 编排、YOLO11 分割感知、TSMixer 多模态时序预测、Agentic RAG、PostgreSQL/Redis/ChromaDB 接入、FastMCP 工具化、SSE 流式交互、Prometheus/Grafana 可观测、长短期记忆持久化，以及 PDF/图片知识库上传索引。

需要注意的是，论文/简历中的实验性指标，例如 3045 张标注图像、mAP50-95 提升 15.2%、93 天生长季与 2135 条日尺度记录，属于数据和实验结果口径，需要由论文数据、训练日志或实验报告继续背书；本工程负责把这些能力落到可运行系统链路中。

## 技术栈映射

| 简历技术点 | 工程覆盖情况 | 主要源码位置 |
| --- | --- | --- |
| LangGraph Router + Handoffs + Subagents | 已覆盖。主图、日决策子图、并行 Send 调度和 handoff 数据结构均在源码中实现。 | `backend/app/graph/builder_v2.py`, `backend/app/graph/subagent.py`, `backend/app/graph/state.py` |
| Phase1 YOLO ∥ RAG, Phase2 TSMixer ∥ RAG | 已覆盖。决策图按感知和预测两阶段并行调度，最终由主 Agent 汇总。 | `backend/app/graph/builder_v2.py` |
| GPT 统一模型配置 | 已覆盖。模型名从运行配置读取，前端也展示运行模型名。 | `backend/app/core/config.py`, `frontend/src/stores/chatStore.ts` |
| YOLO11 改进分割感知 | 已覆盖工程调用。提供 YOLO 服务、模型权重路径、图像感知输出和 fallback。 | `backend/app/services/yolo_service.py`, `models/yolo/yolo11_seg_best.pt` |
| TSMixer 多模态时序预测 | 已覆盖。提供模型加载、96 窗口构造、11 维特征组织和预测服务。 | `backend/app/services/tsmixer_service.py`, `backend/app/graph/feature_builder.py`, `models/tsmixer/` |
| Agentic RAG 4R 管道 | 已覆盖工程版本。实现查询改写、混合检索、精排/重排、读取引用，并支持 FAO56、历史记忆和用户上传文献。 | `backend/app/services/rag_service.py`, `src/cucumber_irrigation/rag/`, `backend/app/api/v1/knowledge.py` |
| PDF/TXT/MD 上传索引 | 已覆盖。支持文献上传、解析、chunk、图片抽取、索引入库与引用展示。 | `backend/app/api/v1/knowledge.py`, `backend/app/services/pdf_enhanced_parser.py`, `frontend/src/pages/Knowledge.tsx` |
| PDF 图片/表格增强解析 | 已覆盖工程接口。集成 DocLayout-YOLO / Table Transformer 风格的布局和表格抽取适配逻辑，并保留 PyMuPDF fallback。 | `backend/app/services/pdf_enhanced_parser.py` |
| PostgreSQL | 已覆盖接入。包含连接封装、checkpointer/状态持久化配置和 docker compose。 | `backend/app/infra/postgres.py`, `backend/app/graph/runtime.py`, `docker-compose.yml` |
| Redis | 已覆盖接入。用于缓存和 RAG 检索结果缓存。 | `backend/app/infra/redis_cache.py`, `backend/app/services/rag_service.py`, `docker-compose.yml` |
| ChromaDB | 已覆盖接入。支持向量存储、用户文献索引和 fallback。 | `backend/app/infra/chroma_store.py`, `backend/app/api/v1/knowledge.py`, `docker-compose.yml` |
| SSE 实时交互 | 已覆盖。后端 EventSourceResponse，前端 EventSource 流式渲染。 | `backend/app/api/v1/chat.py`, `frontend/src/stores/chatStore.ts` |
| Prometheus / Grafana | 已覆盖。提供 `/metrics`、指标注册、Prometheus 配置和 Grafana Dashboard。 | `backend/app/observability/metrics.py`, `backend/app/observability/instrumentation.py`, `ops/prometheus.yml`, `ops/grafana/` |
| FastMCP / MCP 工具 | 已覆盖。MCP client 与多个 MCP server 封装灌溉、知识、视觉、预测等能力。 | `backend/app/services/mcp_client.py`, `backend/mcp_servers/` |
| 长短期记忆三层持久化 | 已覆盖。包含 checkpointer、episode 日志、weekly summary，以及 LLM 调用前的记忆注入链路。 | `backend/app/graph/runtime.py`, `backend/app/services/memory_service.py`, `backend/app/api/v1/episodes.py`, `backend/app/api/v1/weekly.py` |
| Loguru 工程日志 | 已覆盖。 | `backend/app/core/logging.py` |

## V2 版本重点

1. 三个 SubAgent 均为 prompt-driven 结构：YOLOAgent、TSMixerAgent、RAGAgent。
2. 决策链路保留 Phase1/Phase2 并行调度。
3. 用户上传 PDF 可以进入知识库索引，并在问答输出中混排引用与抽取图片。
4. 引用支持上传 PDF 页码打开，FAO56 引用支持内容弹窗。
5. Prometheus/Grafana 已提供可观测入口，可用于查看请求、Agent 决策、RAG、LLM、上传解析等链路指标。

## 本地运行提示

完整工程链路建议同时启动：

```powershell
docker compose up -d postgres redis chroma prometheus grafana
E:\anaconda\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
npm --prefix frontend run dev
```

访问入口：

- 前端：`http://127.0.0.1:3003`
- 后端指标：`http://127.0.0.1:8000/metrics`
- Prometheus：`http://127.0.0.1:9090`
- Grafana：`http://127.0.0.1:3000`
