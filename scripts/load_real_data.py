"""从真实数据加载 Episodes

读取 output/responses/ 中的真实 PlantResponse 数据
将其转换为 Episode 格式存储
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cucumber_irrigation.models import Episode, EpisodePredictions, FinalDecision, EpisodeAnomalies
from cucumber_irrigation.memory import EpisodeStore


def load_response_file(file_path: Path) -> dict:
    """加载单个 response 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_to_episode(response_data: dict) -> Episode:
    """将 response 数据转换为 Episode"""
    date = response_data["date"]
    resp = response_data.get("response", {})
    env = response_data.get("env_today", {})
    yolo_today = response_data.get("yolo_today", {})

    # 提取异常信息
    abnormalities = resp.get("abnormalities", {})
    has_anomaly = any([
        abnormalities.get("wilting", "none") != "none",
        abnormalities.get("yellowing", "none") != "none",
        abnormalities.get("pest_damage", "none") != "none"
    ])

    # 构建 Episode
    episode = Episode(
        date=date,
        predictions=EpisodePredictions(
            tsmixer_raw=env.get("light", 0) / 1000,  # 使用光照作为模拟灌溉量
            growth_stage=resp.get("growth_stage", "unknown"),
            plant_response={
                "trend": resp.get("trend", "same"),
                "confidence": resp.get("confidence", 0.5),
                "evidence": resp.get("evidence", {}),
                "comparison": resp.get("comparison", {})
            }
        ),
        final_decision=FinalDecision(
            value=env.get("light", 0) / 1000,  # 模拟灌溉量
            source="tsmixer"
        ),
        anomalies=EpisodeAnomalies(
            out_of_range=False,
            trend_conflict=has_anomaly,
            trend_conflict_severity="minor" if has_anomaly else None,
            env_anomaly=abnormalities.get("wilting", "none") != "none",
            env_anomaly_type="wilting" if abnormalities.get("wilting", "none") != "none" else None
        )
    )

    return episode


def load_all_responses(responses_dir: str) -> list[Episode]:
    """加载所有 response 文件"""
    responses_path = Path(responses_dir)
    episodes = []

    if not responses_path.exists():
        print(f"目录不存在: {responses_path}")
        return episodes

    for json_file in sorted(responses_path.glob("*.json")):
        try:
            response_data = load_response_file(json_file)
            episode = convert_to_episode(response_data)
            episodes.append(episode)
        except Exception as e:
            print(f"加载失败 {json_file.name}: {e}")

    return episodes


def save_episodes_to_store(episodes: list[Episode], storage_path: str) -> EpisodeStore:
    """保存 Episodes 到存储"""
    Path(storage_path).mkdir(parents=True, exist_ok=True)
    store = EpisodeStore(json_path=f"{storage_path}/episodes.json")

    for ep in episodes:
        store.save(ep)

    return store


def main():
    print("=" * 60)
    print("加载真实 PlantResponse 数据")
    print("=" * 60)

    # 路径
    project_root = Path(__file__).parent.parent
    responses_dir = project_root / "output" / "responses"
    storage_path = project_root / "data" / "real_storage"

    print(f"\n数据源: {responses_dir}")
    print(f"存储路径: {storage_path}")

    # 加载数据
    print("\n[1] 加载 response 文件...")
    episodes = load_all_responses(str(responses_dir))
    print(f"    加载了 {len(episodes)} 个 Episodes")

    if not episodes:
        print("没有找到数据!")
        return

    # 保存到 EpisodeStore
    print("\n[2] 保存到 EpisodeStore...")
    store = save_episodes_to_store(episodes, str(storage_path))
    print(f"    保存完成: {storage_path}/episodes.json")

    # 统计信息
    print("\n[3] 数据统计:")
    trends = {"better": 0, "same": 0, "worse": 0}
    stages = {}

    for ep in episodes:
        trend = ep.predictions.plant_response.get("trend", "same")
        trends[trend] = trends.get(trend, 0) + 1

        stage = ep.predictions.growth_stage
        stages[stage] = stages.get(stage, 0) + 1

    print(f"    日期范围: {episodes[0].date} ~ {episodes[-1].date}")
    print(f"    趋势分布: better={trends['better']}, same={trends['same']}, worse={trends['worse']}")
    print(f"    生育期分布: {stages}")

    print("\n" + "=" * 60)
    print("数据加载完成!")
    print("=" * 60)

    return store


if __name__ == "__main__":
    main()
