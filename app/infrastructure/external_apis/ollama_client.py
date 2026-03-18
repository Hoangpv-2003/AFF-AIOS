"""Ollama generation and embedding clients for local LLM integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx


@dataclass
class OllamaLLMClient:
    base_url: str
    primary_model: str
    fallback_models: List[str]
    timeout_seconds: float = 30.0
    last_debug: Optional[Dict[str, object]] = None

    def _models_in_order(
        self,
        override_model: Optional[str] = None,
    ) -> List[str]:
        if override_model:
            return [override_model]
        models = [self.primary_model]
        for model in self.fallback_models:
            if model and model not in models:
                models.append(model)
        return models

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        final_prompt = (
            prompt if not system_prompt else f"{system_prompt}\n\n{prompt}"
        )
        last_error: Optional[Exception] = None
        attempts: List[Dict[str, object]] = []
        for candidate in self._models_in_order(override_model=model):
            try:
                response = httpx.post(
                    f"{self.base_url.rstrip('/')}/api/generate",
                    json={
                        "model": candidate,
                        "prompt": final_prompt,
                        "stream": False,
                    },
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                data = response.json()
                text = str(data.get("response", "")).strip()
                attempts.append(
                    {
                        "model": candidate,
                        "ok": bool(text),
                        "status_code": response.status_code,
                        "response_chars": len(text),
                    }
                )
                if text:
                    self.last_debug = {
                        "used_model": candidate,
                        "attempts": attempts,
                        "error": None,
                    }
                    return text
            except Exception as exc:  # pragma: no cover
                attempts.append(
                    {
                        "model": candidate,
                        "ok": False,
                        "error": str(exc),
                    }
                )
                last_error = exc
                continue

        self.last_debug = {
            "used_model": None,
            "attempts": attempts,
            "error": (
                str(last_error)
                if last_error is not None
                else "no response"
            ),
        }
        if last_error is not None:
            raise RuntimeError(
                f"Ollama generate failed: {last_error}"
            ) from last_error
        raise RuntimeError("Ollama generate failed: no response")

    def get_last_debug(self) -> Dict[str, object]:
        return dict(self.last_debug or {})


@dataclass
class OllamaEmbeddingClient:
    base_url: str
    embedding_model: str
    timeout_seconds: float = 30.0

    def embed(self, text: str) -> List[float]:
        response = httpx.post(
            f"{self.base_url.rstrip('/')}/api/embeddings",
            json={"model": self.embedding_model, "prompt": text},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        embedding = data.get("embedding") or []
        return [float(value) for value in embedding]
