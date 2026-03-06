"""Demo WeeklyPipeline calling LLM to generate key_insights

Run:
    cd cucumber-irrigation
    uv run python scripts/demo_weekly_llm.py

Make sure LLM_API_KEY is set in .env file
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cucumber_irrigation.pipelines import WeeklyPipeline, WeeklyPipelineConfig
from cucumber_irrigation.memory import EpisodeStore, WeeklySummaryStore
from cucumber_irrigation.services import LLMService
from cucumber_irrigation.models import Episode, EpisodePredictions, FinalDecision

# ========== API Key ==========
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")

if not API_KEY:
    print("Please set LLM_API_KEY in .env file")
    sys.exit(1)


def create_sample_episodes(storage_path: str) -> EpisodeStore:
    """Create sample week of Episode data"""
    episode_store = EpisodeStore(json_path=f"{storage_path}/episodes.json")

    base_date = datetime(2025, 3, 10)
    trends = ["better", "better", "same", "worse", "better", "same", "better"]
    irrigations = [5.2, 5.5, 5.3, 4.8, 5.8, 5.5, 6.0]

    for i in range(7):
        date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")

        ep = Episode(
            date=date_str,
            predictions=EpisodePredictions(
                tsmixer_raw=irrigations[i],
                growth_stage="flowering",
                plant_response={"trend": trends[i]}
            ),
            final_decision=FinalDecision(
                value=irrigations[i],
                source="tsmixer"
            )
        )
        episode_store.save(ep)
        print(f"  Episode: {date_str}, irrigation: {irrigations[i]:.1f} L/m2, trend: {trends[i]}")

    return episode_store


def main():
    print("=" * 60)
    print("WeeklyPipeline LLM Demo")
    print("=" * 60)

    storage_path = "data/demo_storage"
    Path(storage_path).mkdir(parents=True, exist_ok=True)

    print("\n[1] Creating sample Episode data...")
    episode_store = create_sample_episodes(storage_path)

    print("\n[2] Initializing LLM Service...")
    print(f"    API: https://yunwu.ai/v1")
    print(f"    Model: gpt-5.2")

    llm_service = LLMService(
        api_key=API_KEY,
        base_url="https://yunwu.ai/v1",
        model="gpt-5.2"
    )

    print("\n[3] Initializing WeeklyPipeline (enable_llm_insights=True)...")
    weekly_store = WeeklySummaryStore(json_path=f"{storage_path}/weekly.json")

    config = WeeklyPipelineConfig(
        enable_rag=False,
        enable_llm_insights=True  # Enable LLM!
    )

    pipeline = WeeklyPipeline(
        episode_store=episode_store,
        weekly_store=weekly_store,
        llm_service=llm_service,  # Pass LLM service!
        config=config
    )

    print("\n[4] Running weekly summary (calling LLM for key_insights)...")
    print("-" * 40)

    result = pipeline.run(week_end_date="2025-03-16", season="spring")

    print("-" * 40)
    print("\n[5] Result:")
    print(f"    Period: {result.week_start} ~ {result.week_end}")
    print(f"    Trend: better={result.summary.trend_stats.better_days} / same={result.summary.trend_stats.same_days} / worse={result.summary.trend_stats.worse_days}")
    print(f"    Avg irrigation: {result.summary.irrigation_stats.daily_avg:.2f} L/m2")
    print(f"    prompt_block tokens: {result.prompt_block_tokens}")

    print("\n    === LLM Generated key_insights ===")
    for i, insight in enumerate(result.summary.key_insights, 1):
        print(f"    [{i}] {insight}")

    print("\n" + "=" * 60)
    print("Demo complete! LLM was called successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
