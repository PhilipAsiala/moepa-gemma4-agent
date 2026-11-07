"""Praxeology LLM client backed by host Ollama on Arc Pro B70 (:11434)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class OllamaClient:
    """Chat client for local Gemma 4 via Ollama (Vulkan → B70).

    Larger Gemma 4 tags enable thinking by default; allow enough tokens so the
    final answer lands in ``message.content`` (not only ``thinking``).
    """

    def __init__(
        self,
        model: str = "gemma4:12b",
        base_url: str = "http://127.0.0.1:11434",
        timeout_sec: float = 600.0,
        num_predict: int = 2048,
        temperature: float = 0.2,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.num_predict = num_predict
        self.temperature = temperature

    def generate(self, prompt: str, *, system: Optional[str] = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": 4096,
                "num_predict": self.num_predict,
            },
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama chat failed for {self.model}: {e}") from e
        msg = body.get("message") or {}
        content = (msg.get("content") or "").strip()
        if content:
            return content
        # Fallback if the model spent the budget in thinking only.
        return (msg.get("thinking") or "").strip()
