from __future__ import annotations

import json
import sys

import httpx

from app.core.config import get_settings
from app.infrastructure.external_apis.ollama_client import OllamaEmbeddingClient, OllamaLLMClient


def main() -> int:
    settings = get_settings()
    base_url = settings.ollama_base_url.rstrip("/")

    print("llm_provider=ollama (locked)")
    print(f"ollama_base_url={base_url}")
    print(f"chat_model={settings.ollama_chat_model}")
    print(f"fallback_models={settings.ollama_fallback_models}")
    print(f"embedding_model={settings.ollama_embedding_model}")
    print("-")

    try:
        tags_resp = httpx.get(f"{base_url}/api/tags", timeout=8.0)
        tags_resp.raise_for_status()
    except Exception as exc:
        print(f"[FAIL] cannot connect to Ollama tags endpoint: {exc}")
        return 1

    tags_data = tags_resp.json()
    model_names = [item.get("name", "") for item in tags_data.get("models", [])]
    print(f"[OK] connection: {base_url}/api/tags")
    print("available_models=")
    print(json.dumps(model_names, indent=2))

    llm = OllamaLLMClient(
        base_url=base_url,
        primary_model=settings.ollama_chat_model,
        fallback_models=[m.strip() for m in settings.ollama_fallback_models.split(",") if m.strip()],
    )
    emb = OllamaEmbeddingClient(
        base_url=base_url,
        embedding_model=settings.ollama_embedding_model,
    )

    prompt = (
        "You are a coding assistant. "
        "Reply with exactly 2 bullet points describing what you can do."
    )
    try:
        out = llm.generate(prompt=prompt)
    except Exception as exc:
        print(f"[FAIL] generate call failed: {exc}")
        return 2

    print("-")
    print("[OK] generate output:")
    print(out)

    try:
        vec = emb.embed("check embedding health")
    except Exception as exc:
        print(f"[FAIL] embeddings call failed: {exc}")
        return 3

    print("-")
    print(f"[OK] embedding dimensions={len(vec)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
