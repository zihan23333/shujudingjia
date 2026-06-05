"""Utilities for parsing JSON returned by LLMs."""

from __future__ import annotations

import json
import re
from json import JSONDecodeError


CODE_FENCE_PATTERN = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```",
    flags=re.IGNORECASE | re.DOTALL,
)


def safe_parse_json(text: str) -> dict:
    """Parse the first JSON object from model output.

    The parser tolerates Markdown code fences and leading/trailing prose.
    It raises a ValueError with a clear message when parsing fails.
    """
    if text is None:
        raise ValueError("Cannot parse JSON from None response text.")

    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("Cannot parse JSON from empty response text.")

    fence_match = CODE_FENCE_PATTERN.search(cleaned_text)
    candidate_text = fence_match.group(1).strip() if fence_match else cleaned_text

    decoder = json.JSONDecoder()
    search_positions = [0]
    search_positions.extend(
        index for index, char in enumerate(candidate_text) if char == "{"
    )

    last_error: Exception | None = None
    seen_positions: set[int] = set()

    for start_index in search_positions:
        if start_index in seen_positions:
            continue
        seen_positions.add(start_index)
        snippet = candidate_text[start_index:].lstrip()
        if not snippet.startswith("{"):
            continue
        try:
            parsed_object, _ = decoder.raw_decode(snippet)
            if not isinstance(parsed_object, dict):
                raise ValueError("Parsed JSON is not an object.")
            return parsed_object
        except (JSONDecodeError, ValueError) as exc:
            last_error = exc

    raise ValueError(
        "Failed to parse a JSON object from model output."
        + (f" Last parser error: {last_error}" if last_error else "")
    )
