from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
import types
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


try:
    import loguru  # noqa: F401
except Exception:
    class _Logger:
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass

    sys.modules["loguru"] = types.SimpleNamespace(logger=_Logger())


def test_calculate_irrigation_prefers_saved_final_decision():
    from app.services.episode_service import calculate_irrigation

    episode = {
        "date": "2025-03-10",
        "env_today": {},
        "final_decision": {"value": 5.2, "source": "tsmixer"},
    }

    assert calculate_irrigation(episode) == 5.2


def test_weekly_api_uses_local_weekly_storage(monkeypatch, tmp_path):
    from app.api.v1 import weekly

    weekly_file = tmp_path / "weekly.json"
    weekly_file.write_text(
        json.dumps(
            [
                {
                    "week_start": "2024-04-01",
                    "week_end": "2024-04-07",
                    "created_at": "2026-01-01T00:00:00",
                    "key_insights": ["真实周总结"],
                    "trend_stats": {"better_days": 3, "same_days": 4, "worse_days": 0},
                    "irrigation_stats": {"total": 51.1, "daily_avg": 7.3},
                    "override_summary": {"count": 0},
                    "knowledge_references": [{"doc_id": "ref-1", "source": "Fao56.pdf"}],
                    "prompt_block": "真实 prompt block",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    missing_file = tmp_path / "missing.json"
    monkeypatch.setattr(weekly, "WEEKLY_STORAGE_FILE", weekly_file, raising=False)
    monkeypatch.setattr(weekly, "MEMORY_WEEKLY_FILE", missing_file, raising=False)

    response = asyncio.run(weekly.get_all())

    assert response["success"] is True
    assert response["data"]["total"] == 1
    item = response["data"]["items"][0]
    assert item["week_start"] == "2024-04-01"
    assert item["insights"] == ["真实周总结"]
    assert item["stats"]["avg_irrigation"] == 7.3
    assert item["injected_prompt"] == "真实 prompt block"


def test_override_api_persists_and_overlays_episode(monkeypatch, tmp_path):
    from app.api.v1 import override
    from app.services import episode_service

    responses_dir = tmp_path / "responses"
    storage_dir = tmp_path / "storage"
    responses_dir.mkdir()
    storage_dir.mkdir()

    date = "2024-06-14"
    (responses_dir / f"{date}.json").write_text(
        json.dumps(
            {
                "date": date,
                "env_today": {"temperature": 25, "humidity": 70, "light": 5000},
                "response": {"trend": "same", "abnormalities": {}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    overrides_file = storage_dir / "overrides.json"
    overrides_db = storage_dir / "irrigation_overrides.sqlite3"
    monkeypatch.setattr(episode_service, "RESPONSES_DIR", responses_dir)
    monkeypatch.setattr(episode_service, "MEMORY_EPISODES_FILE", storage_dir / "episodes.json")
    monkeypatch.setattr(episode_service, "MEMORY_WEEKLY_FILE", storage_dir / "weekly_summaries.json")
    monkeypatch.setattr(episode_service, "OVERRIDES_DB", overrides_db, raising=False)
    monkeypatch.setattr(episode_service, "OVERRIDES_FILE", overrides_file, raising=False)

    request = override.OverrideRequest(
        date=date,
        original_value=4.0,
        replaced_value=6.7,
        reason="现场复核发现基质含水率偏低，需要临时增加灌水量",
        confirmation_answers={"soil": "low"},
    )

    response = asyncio.run(override.submit_override(request))
    reloaded = episode_service.get_episode_by_date(date)
    trend_data = episode_service.get_trend_data(7)
    saved = json.loads(overrides_file.read_text(encoding="utf-8"))
    with sqlite3.connect(str(overrides_db)) as conn:
        row = conn.execute(
            "SELECT replaced_value, reason FROM irrigation_overrides WHERE date = ?",
            (date,),
        ).fetchone()

    assert response["success"] is True
    assert reloaded["irrigation_amount"] == 6.7
    assert reloaded["decision_source"] == "Override"
    assert reloaded["override_reason"] == request.reason
    assert saved[date]["replaced_value"] == 6.7
    assert saved[date]["confirmation_answers"] == {"soil": "low"}
    assert row == (6.7, request.reason)
    assert trend_data["sources"] == ["Override"]
