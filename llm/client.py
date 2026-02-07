#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import socket
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class LLMError(Exception):
    pass


def get_api_key(provider: str) -> Optional[str]:
    p = (provider or "").strip().lower()
    if p == "anthropic":
        return (os.environ.get("ANTHROPIC_API_KEY") or "").strip() or None
    if p == "openai":
        return (os.environ.get("OPENAI_API_KEY") or "").strip() or None
    return None


def default_model(provider: str) -> str:
    p = (provider or "").strip().lower()
    if p == "anthropic":
        return (os.environ.get("ANTHROPIC_MODEL") or "").strip() or "claude-3-5-sonnet-latest"
    if p == "openai":
        return (os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"
    return ""


def enhance_copy(
    *,
    provider: str,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int = 900,
    temperature: float = 0.6,
    timeout_s: int = 30,
) -> str:
    p = (provider or "").strip().lower()
    if not api_key:
        raise LLMError("Missing API key")
    if not model:
        raise LLMError("Missing model")
    if not prompt:
        raise LLMError("Missing prompt")

    if p == "anthropic":
        return _anthropic_messages(
            api_key=api_key,
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
        )
    if p == "openai":
        return _openai_chat_completions(
            api_key=api_key,
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
        )

    raise LLMError(f"Unsupported provider: {provider}")


def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout_s: int) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in (headers or {}).items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        raise LLMError(f"HTTP {e.code}: {err_body}".strip())
    except (urllib.error.URLError, socket.timeout) as e:
        raise LLMError(str(e))

    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise LLMError(f"Invalid JSON response: {e}")


def _anthropic_messages(
    *,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    timeout_s: int,
) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "messages": [{"role": "user", "content": prompt}],
    }
    data = _post_json(url, headers, payload, timeout_s)
    content = data.get("content")
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(str(block.get("text", "")))
        return "".join(texts).strip()
    if isinstance(content, str):
        return content.strip()
    return str(data).strip()


def _openai_chat_completions(
    *,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    timeout_s: int,
) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "messages": [{"role": "user", "content": prompt}],
    }
    data = _post_json(url, headers, payload, timeout_s)
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        msg = (choices[0] or {}).get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            return content.strip()
    return str(data).strip()
