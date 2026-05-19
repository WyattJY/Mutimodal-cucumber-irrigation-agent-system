#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_BASE="${API_BASE:-http://127.0.0.1:8000/api}"
IMAGE_PATH="${IMAGE_PATH:-$PROJECT_ROOT/demo_cases/images/cucumber_monitor_original_0420.jpg}"
RAG_DOC="$PROJECT_ROOT/demo_cases/knowledge/agriagent_rag_demo.md"
AGENT_TIMEOUT_SECONDS="${AGENT_TIMEOUT_SECONDS:-360}"

print_title() {
  printf '\n\033[1;34m%s\033[0m\n' "== $1 =="
}

print_json_summary() {
  local label="${1:-response}"
  local tmp_file
  tmp_file="$(mktemp)"
  cat > "$tmp_file"
  python3 - "$label" "$tmp_file" <<'PY'
import json
import sys
from pathlib import Path

label = sys.argv[1] if len(sys.argv) > 1 else "response"
raw = Path(sys.argv[2]).read_text(encoding="utf-8", errors="ignore")
try:
    data = json.loads(raw)
except Exception:
    print(raw[:1200])
    raise SystemExit(0)

print(f"{label}: success={data.get('success', data.get('status', 'n/a'))}")
payload = data.get("data", data)
if isinstance(payload, dict):
    interesting = [
        "status", "message", "rag_available", "chunk_count", "uploaded_documents",
        "uploaded_chunks", "total_images", "total_processed", "model_loaded",
        "irrigation_amount", "final_irrigation", "confidence", "prediction_source",
        "fallback", "fallback_reason",
    ]
    for key in interesting:
        if key in payload:
            print(f"  {key}: {payload[key]}")
    if "answer" in payload:
        print("  answer:", str(payload["answer"]).replace("\n", " ")[:360])
    if "content" in payload:
        print("  content:", str(payload["content"]).replace("\n", " ")[:360])
    if "references" in payload:
        print("  references:", len(payload["references"] or []))
    if "metrics" in payload and isinstance(payload["metrics"], dict):
        metrics = payload["metrics"]
        keys = ["leaf_instance_count", "flower_instance_count", "fruit_instance_count", "total_instances", "is_mock"]
        print("  metrics:", {k: metrics.get(k) for k in keys if k in metrics})
    if "prediction" in payload:
        print("  prediction:", payload["prediction"])
else:
    print(str(payload)[:1200])
PY
  rm -f "$tmp_file"
}

require_file() {
  if [ ! -f "$1" ]; then
    echo "Missing file: $1" >&2
    exit 1
  fi
}

require_file "$RAG_DOC"
require_file "$IMAGE_PATH"

print_title "Health"
curl -fsS "$API_BASE/health" | print_json_summary "health"

print_title "RAG status before upload"
curl -fsS "$API_BASE/chat/rag-status" | print_json_summary "rag-status"

print_title "Upload demo RAG document"
curl -fsS -X POST "$API_BASE/knowledge/upload" \
  -F "file=@$RAG_DOC" \
  -F "title=AgriAgent RAG 演示知识库" \
  -F "category=demo" | print_json_summary "knowledge-upload"

print_title "Knowledge search"
curl -fsS --get "$API_BASE/knowledge/search" \
  --data-urlencode "q=温室黄瓜 结果期 高温低湿 灌水 YOLO mask" \
  --data-urlencode "top_k=5" | print_json_summary "knowledge-search"

print_title "RAG answer generation"
curl -fsS -X POST "$API_BASE/knowledge/query" \
  -H "Content-Type: application/json" \
  --data-binary "@$PROJECT_ROOT/demo_cases/payloads/knowledge_query.json" | print_json_summary "knowledge-query"

print_title "Chat RAG reply"
curl -fsS -X POST "$API_BASE/chat/" \
  -H "Content-Type: application/json" \
  --data-binary "@$PROJECT_ROOT/demo_cases/payloads/chat_rag.json" | print_json_summary "chat"

print_title "Vision status"
curl -fsS "$API_BASE/vision/status" | print_json_summary "vision-status"

print_title "Available image dates"
curl -fsS "$API_BASE/vision/available-dates" | print_json_summary "available-dates"

print_title "Vision analyze image"
curl -fsS -X POST "$API_BASE/vision/analyze?conf_threshold=0.25" \
  -F "file=@$IMAGE_PATH" | print_json_summary "vision-analyze"

print_title "Predict from structured features"
curl -fsS -X POST "$API_BASE/predict/" \
  -H "Content-Type: application/json" \
  --data-binary "@$PROJECT_ROOT/demo_cases/payloads/predict_default.json" | print_json_summary "predict"

print_title "Predict with image"
curl -fsS -X POST "$API_BASE/predict/with-image" \
  -F "file=@$IMAGE_PATH" \
  -F "temperature=29.2" \
  -F "humidity=58" \
  -F "light=62000" \
  -F "date=2026-05-17" | print_json_summary "predict-with-image"

print_title "Agent stack"
curl -fsS "$API_BASE/agent/stack" | print_json_summary "agent-stack"

print_title "Agent decision"
curl -fsS --max-time "$AGENT_TIMEOUT_SECONDS" -X POST "$API_BASE/agent/decision" \
  -H "Content-Type: application/json" \
  --data-binary "@$PROJECT_ROOT/demo_cases/payloads/agent_decision.json" | print_json_summary "agent-decision"

print_title "Done"
echo "Demo smoke test finished."
