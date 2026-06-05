"""Shared OpenAI-compatible LLM client for ACT2 experiments."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from json_utils import safe_parse_json


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_TIMEOUT_SECONDS = 120


def _load_llm_config() -> dict[str, Any]:
    """Load LLM configuration from the repository root .env file."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    config = {
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
        "base_url": os.getenv("LLM_BASE_URL", "").strip(),
        "model": os.getenv("LLM_MODEL", "").strip(),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0") or 0),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "512") or 512),
    }

    missing_fields = [
        name
        for name, value in (
            ("LLM_API_KEY", config["api_key"]),
            ("LLM_BASE_URL", config["base_url"]),
            ("LLM_MODEL", config["model"]),
        )
        if not value
    ]
    if missing_fields:
        raise ValueError(
            "Missing required LLM configuration in .env: "
            + ", ".join(missing_fields)
        )

    return config


def _extract_message_content(response_json: dict[str, Any]) -> str:
    """Extract assistant message text from a chat-completions response."""
    choices = response_json.get("choices")
    if not choices:
        raise ValueError("LLM response does not contain any choices.")

    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        if text_parts:
            return "\n".join(text_parts)

    raise ValueError("LLM response does not contain string message content.")


def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 2,
) -> dict:
    """Call an OpenAI-compatible chat-completions API and parse JSON output.

    Returns parsed JSON fields together with raw_response, parse_failed, and error.
    """
    config = _load_llm_config()
    endpoint = config["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    last_raw_response = ""
    last_error = ""

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            response_json = response.json()
            raw_response = _extract_message_content(response_json)
            parsed_json = safe_parse_json(raw_response)
            parsed_json["raw_response"] = raw_response
            parsed_json["parse_failed"] = False
            parsed_json["error"] = ""
            return parsed_json
        except Exception as exc:
            last_error = f"Attempt {attempt + 1} failed: {exc}"
            try:
                last_raw_response = response.text  # type: ignore[name-defined]
            except Exception:
                pass
            if attempt >= max_retries:
                break

    return {
        "parse_failed": True,
        "raw_response": last_raw_response,
        "error": last_error or "Unknown LLM call error.",
    }
