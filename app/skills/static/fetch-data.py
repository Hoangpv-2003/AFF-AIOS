from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx


def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    payload = dict(input_data or {})
    topic = str(payload.get("topic") or payload.get("query") or "").strip()
    if not topic:
        return {
            "status": "error",
            "summary": "Thiếu chủ đề tìm kiếm.",
            "error_reason": "Missing required key: topic",
            "results": [],
            "source_urls": [],
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return {
            "status": "error",
            "summary": "Thiếu cấu hình TAVILY_API_KEY.",
            "error_reason": "missing_tavily_api_key",
            "results": [],
            "source_urls": [],
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": topic,
                    "search_depth": "advanced",
                    "max_results": 8,
                    "include_answer": True,
                },
            )
            response.raise_for_status()
            data = response.json() if response.content else {}

        results = data.get("results") if isinstance(data, dict) else []
        if not isinstance(results, list):
            results = []
        source_urls = [
            str(item.get("url", "")).strip()
            for item in results
            if isinstance(item, dict) and str(item.get("url", "")).strip()
        ]

        return {
            "status": "success",
            "summary": f"Đã truy xuất {len(results)} nguồn dữ liệu.",
            "results": results,
            "source_urls": source_urls,
            "answer": data.get("answer", "") if isinstance(data, dict) else "",
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        return {
            "status": "error",
            "summary": "Không thể lấy dữ liệu realtime.",
            "error_reason": str(exc),
            "results": [],
            "source_urls": [],
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    import json
    import sys
    # Read input from stdin if piped, else argv[1]
    input_str = sys.argv[1] if len(sys.argv) > 1 else "{}"
    try:
        input_data = json.loads(input_str)
    except:
        input_data = {}
    
    result = run(input_data)
    print(json.dumps(result, ensure_ascii=False))