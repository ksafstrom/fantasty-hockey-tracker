
from __future__ import annotations

import time
import unicodedata
from typing import Any

import requests

BASE_URL = "https://api-web.nhle.com/v1"
SEARCH_URL = "https://search.d3.nhle.com/api/v1/search/player"
STATS_URL = "https://api.nhle.com/stats/rest/en"

HEADERS = {"User-Agent": "fantasy-hockey-tracker/1.0"}


def get_url(url: str, params=None):
    last_error = None

    for attempt in range(3):
        try:
            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=20
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)

    raise RuntimeError(
        f"NHL API request failed: {url}: {last_error}"
    )


def get_json(path: str, params=None):
    return get_url(f"{BASE_URL}{path}", params)


def clean_name(value):
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        c for c in value if not unicodedata.combining(c)
    )
    return value.casefold().replace(".", "").strip()


def resolve_player(name: str):
    results = get_url(
        SEARCH_URL,
        {
            "culture": "en-us",
            "limit": 100,
            "q": name
        }
    )

    matches = [
        p for p in results
        if clean_name(p.get("name", "")) == clean_name(name)
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected one exact NHL match for {name}; "
            f"found {len(matches)}"
        )

    return matches[0]


def player_game_log(player_id, season="20262027"):
    return get_json(
        f"/player/{player_id}/game-log/{season}/2"
    )


def goalie_season_stats(player_id, season="20262027"):
    result = get_url(
        f"{STATS_URL}/goalie/summary",
        {
            "cayenneExp": (
                f"seasonId={season} and "
                f"gameTypeId=2 and playerId={player_id}"
            ),
            "limit": 100
        }
    )

    rows = result.get("data", [])

    return {
        "gp": sum(r.get("gamesPlayed", 0) for r in rows),
        "wins": sum(r.get("wins", 0) for r in rows),
        "shutouts": sum(r.get("shutouts", 0) for r in rows)
    }


def current_schedule():
    return get_json("/schedule/now")
