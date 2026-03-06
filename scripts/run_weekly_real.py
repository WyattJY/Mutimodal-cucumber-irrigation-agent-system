"""使用真实数据运行 WeeklyPipeline

读取 output/responses/ 中的真实 PlantResponse 数据
生成周度总结，调用 LLM 生成 key_insights

Run:
    cd cucumber-irrigation
    uv run python scripts/run_weekly_real.py

Make sure LLM_API_KEY is set in .env file
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cucumber_irrigation.pipelines import WeeklyPipeline, WeeklyPipelineConfig
from cucumber_irrigation.memory import EpisodeStore, WeeklySummaryStore
from cucumber_irrigation.services import LLMService, LocalRAGService, DBService, RAGService
from cucumber_irrigation.models import Episode, EpisodePredictions, FinalDecision, EpisodeAnomalies
from cucumber_irrigation.rag.json_store import JsonKnowledgeStore
from cucumber_irrigation.memory.knowledge_retriever import RetrievalConfig

# ========== API Key ==========
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")


def load_response_file(file_path: Path) -> dict:
    """加载单个 response 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_to_episode(response_data: dict) -> Episode:
    """将 response 数据转换为 Episode"""
    date = response_data["date"]
    resp = response_data.get("response", {})
    env = response_data.get("env_today", {})

    # 提取异常信息
    abnormalities = resp.get("abnormalities", {})
    has_anomaly = any([
        abnormalities.get("wilting", "none") != "none",
        abnormalities.get("yellowing", "none") != "none",
        abnormalities.get("pest_damage", "none") != "none"
    ])

    # 模拟灌溉量 (基于环境数据)
    irrigation = (env.get("temperature", 20) * 0.2 +
                  env.get("light", 5000) / 2000 +
                  (100 - env.get("humidity", 60)) * 0.03)

    episode = Episode(
        date=date,
        predictions=EpisodePredictions(
            tsmixer_raw=irrigation,
            growth_stage=resp.get("growth_stage", "unknown"),
            plant_response={
                "trend": resp.get("trend", "same"),
                "confidence": resp.get("confidence", 0.5),
                "evidence": resp.get("evidence", {}),
                "comparison": resp.get("comparison", {})
            }
        ),
        final_decision=FinalDecision(
            value=irrigation,
            source="tsmixer"
        ),
        anomalies=EpisodeAnomalies(
            out_of_range=False,
            trend_conflict=has_anomaly,
            trend_conflict_severity="minor" if has_anomaly else None,
            env_anomaly=False,
            env_anomaly_type=None
        )
    )

    return episode


def load_episodes_for_week(responses_dir: Path, week_end_date: str) -> list[Episode]:
    """加载指定周的 Episodes"""
    end_date = datetime.strptime(week_end_date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=6)

    episodes = []
    current = start_date

    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        file_path = responses_dir / f"{date_str}.json"

        if file_path.exists():
            try:
                response_data = load_response_file(file_path)
                episode = convert_to_episode(response_data)
                episodes.append(episode)
            except Exception as e:
                print(f"  ⚠ 加载失败 {date_str}: {e}")
        else:
            print(f"  ⚠ 文件不存在: {date_str}")

        current += timedelta(days=1)

    return episodes


def main():
    print("=" * 60)
    print("WeeklyPipeline 真实数据演示")
    print("=" * 60)

    # 检查 API Key
    if not API_KEY:
        print("\n⚠ 未设置 LLM_API_KEY，将使用简单规则生成洞察")
        llm_service = None
        enable_llm = False
    else:
        print(f"\n✓ API Key 已配置")
        print(f"  API: https://yunwu.ai/v1")
        print(f"  Model: gpt-5.2")
        llm_service = LLMService(
            api_key=API_KEY,
            base_url="https://yunwu.ai/v1",
            model="gpt-5.2"
        )
        enable_llm = True

    # 路径设置
    project_root = Path(__file__).parent.parent
    responses_dir = project_root / "output" / "responses"
    storage_path = project_root / "data" / "weekly_storage"
    storage_path.mkdir(parents=True, exist_ok=True)
    milvus_path = project_root / "data" / "index" / "milvus.db"
    bge_m3_path = Path("G:/Wyatt/Greenhouse_RAG/models/BAAI/bge-m3")

    # 检查 MongoDB
    print("\n[1] 检查 MongoDB 连接...")
    db_service = DBService()
    if db_service.is_connected():
        print(f"    ✓ MongoDB 已连接")
        mongo_client = db_service.client
        use_mongodb = True
    else:
        print("    ⚠ MongoDB 未连接，使用 JSON 文件存储")
        mongo_client = None
        use_mongodb = False

    # 检查 Milvus RAG
    print("\n[2] 检查 Milvus RAG...")
    rag_service = None
    enable_rag = False

    if use_mongodb and milvus_path.exists() and bge_m3_path.exists():
        try:
            print(f"    尝试初始化 Milvus RAG...")
            print(f"    Milvus: {milvus_path}")
            print(f"    BGE-M3: {bge_m3_path}")

            rag_service = RAGService(
                milvus_uri=str(milvus_path),
                mongo_client=mongo_client,
                config=RetrievalConfig(top_k=3, prefer_fao56=True),
                embedding_model_path=str(bge_m3_path)
            )
            # 测试一下能否检索
            test_results = rag_service.search("黄瓜灌溉", top_k=1)
            if test_results:
                print(f"    ✓ Milvus RAG 可用 (测试检索成功)")
                enable_rag = True
            else:
                print(f"    ⚠ Milvus RAG 初始化但检索无结果，使用本地RAG")
                rag_service = None
        except Exception as e:
            print(f"    ⚠ Milvus RAG 初始化失败: {e}")
            rag_service = None

    # 如果 Milvus 不可用，使用本地知识库
    if rag_service is None:
        print("\n[2.1] 使用本地知识库 (LocalRAG)...")
        knowledge_store = JsonKnowledgeStore()
        if knowledge_store.is_available:
            print(f"    ✓ 知识库可用: {knowledge_store.chunk_count} 个知识块")
            rag_service = LocalRAGService(knowledge_store=knowledge_store)
            enable_rag = True
        else:
            print("    ⚠ 知识库不可用")
            enable_rag = False

    # 选择要分析的周
    print("\n[3] 选择分析周次...")

    # 找出所有可用的周
    all_dates = sorted([f.stem for f in responses_dir.glob("*.json")])
    if not all_dates:
        print("    ✗ 没有找到响应数据!")
        return

    print(f"    数据范围: {all_dates[0]} ~ {all_dates[-1]}")

    # 选择几个代表性的周来分析
    sample_weeks = [
        "2024-03-21",  # 第一周 (苗期)
        "2024-04-07",  # 第四周 (营养生长期)
        "2024-05-05",  # 第八周 (开花期)
        "2024-06-09",  # 第十二周 (结果期)
    ]

    # 过滤出有数据的周
    available_weeks = [w for w in sample_weeks if w in all_dates]

    if not available_weeks:
        # 使用最后一周
        available_weeks = [all_dates[-1]]

    print(f"    分析周次: {available_weeks}")

    # 运行每周分析
    for week_end in available_weeks:
        print(f"\n{'='*60}")
        print(f"分析周次: {week_end}")
        print("=" * 60)

        # 加载该周的数据
        print("\n[4] 加载周数据...")
        episodes = load_episodes_for_week(responses_dir, week_end)
        print(f"    加载了 {len(episodes)} 天数据")

        if len(episodes) < 3:
            print("    ⚠ 数据不足，跳过该周")
            continue

        # 创建 EpisodeStore (优先使用 MongoDB)
        if use_mongodb:
            episode_store = EpisodeStore(mongo_client=mongo_client)
        else:
            episode_store = EpisodeStore(json_path=str(storage_path / "episodes_temp.json"))
        for ep in episodes:
            episode_store.save(ep)

        # 创建 WeeklySummaryStore (优先使用 MongoDB)
        if use_mongodb:
            weekly_store = WeeklySummaryStore(mongo_client=mongo_client)
        else:
            weekly_store = WeeklySummaryStore(json_path=str(storage_path / "weekly.json"))

        # 配置 Pipeline
        config = WeeklyPipelineConfig(
            enable_rag=enable_rag,  # 启用 RAG
            enable_llm_insights=enable_llm
        )

        # 创建 Pipeline
        pipeline = WeeklyPipeline(
            episode_store=episode_store,
            weekly_store=weekly_store,
            rag_service=rag_service,  # 传入 RAG 服务
            llm_service=llm_service,
            config=config
        )

        # 运行分析
        print("\n[5] 运行周度分析...")
        try:
            result = pipeline.run(week_end_date=week_end, season="spring")

            print(f"\n[6] 分析结果:")
            print(f"    周期: {result.week_start} ~ {result.week_end}")
            print(f"    趋势: better={result.summary.trend_stats.better_days} / "
                  f"same={result.summary.trend_stats.same_days} / "
                  f"worse={result.summary.trend_stats.worse_days}")
            print(f"    主导趋势: {result.summary.trend_stats.dominant_trend}")
            print(f"    日均灌溉: {result.summary.irrigation_stats.daily_avg:.2f} L/m²")
            print(f"    Prompt Block Tokens: {result.prompt_block_tokens}")

            print("\n    === Key Insights ===")
            for i, insight in enumerate(result.summary.key_insights, 1):
                print(f"    [{i}] {insight}")

            # 显示 RAG 知识引用
            if result.knowledge_references:
                print("\n    === RAG 知识引用 ===")
                for i, ref in enumerate(result.knowledge_references, 1):
                    print(f"    [{i}] {ref.get('source', 'unknown')}: {ref.get('doc_id', '')[:20]}...")

        except Exception as e:
            print(f"    ✗ 分析失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
