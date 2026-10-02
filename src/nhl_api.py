from __future__ import annotations

import time
from typing import Any

import requests

BASE_URL = "https://api-web.nhle.com/v1"
HEADERS = {"User-Agent": "fantasy-hockey-tracker/1.0"}


def get_json(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    last_error = None
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"NHL API request failed: {url}: {last_error}")


def current_skater_category(category: str) -> list[dict[str, Any]]:
    data = get_json("/skater-stats-leaders/current", {"categories": category, "limit": -1})
    return data.get("skaterStats", []) or data.get("data", [])


def current_goalie_category(category: str) -> list[dict[str, Any]]:
    data = get_json("/goalie-stats-leaders/current", {"categories": category, "limit": -1})
    return data.get("goalieStats", []) or data.get("data", [])


def current_schedule() -> dict[str, Any]:
    return get_json("/schedule/now")
