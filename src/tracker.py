from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nhl_api import current_goalie_category, current_skater_category
from scoring import goalie_fantasy_points, skater_fantasy_points

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "players.json").read_text())
SEASON = CONFIG["season"]


def normalize_name(row: dict[str, Any]) -> str:
    if row.get("name"):
        return str(row["name"]).strip()
    first = row.get("firstName", "")
    last = row.get("lastName", "")
    if isinstance(first, dict):
        first = first.get("default", "")
    if isinstance(last, dict):
        last = last.get("default", "")
    return f"{first} {last}".strip()


def numeric(row: dict[str, Any], *keys: str) -> float:
    for key in keys:
        value = row.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    return 0.0


def merge_categories(rows_by_category: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for category, rows in rows_by_category.items():
        for row in rows:
            name = normalize_name(row)
            if not name:
                continue
            key = name.casefold()
            merged.setdefault(key, {"name": name}).update(row)
            merged[key][category] = numeric(row, category)
    return merged


def find_player(merged: dict[str, dict[str, Any]], requested: str) -> dict[str, Any] | None:
    exact = merged.get(requested.casefold())
    if exact:
        return exact
    # Handle minor API naming differences while keeping the configured name.
    candidates = [v for k, v in merged.items() if k.endswith(requested.casefold()) or requested.casefold() in k]
    return candidates[0] if len(candidates) == 1 else None


def build_tracker() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    skater_categories = {
        "goals": current_skater_category("goals"),
        "assists": current_skater_category("assists"),
        "shots": current_skater_category("shots"),
    }
    goalie_categories = {
        "wins": current_goalie_category("wins"),
        "shutouts": current_goalie_category("shutouts"),
    }

    skaters = merge_categories(skater_categories)
    goalies = merge_categories(goalie_categories)
    updated = datetime.now(timezone.utc).isoformat(timespec="seconds")

    skater_rows = []
    for requested in CONFIG["skaters"]:
        row = find_player(skaters, requested)
        if row is None:
            skater_rows.append({
                "Player": requested, "Position": "Skater", "GP": "", "G": "", "A": "", "SOG": "",
                "Fantasy Points": "", "Fantasy Pts/GP": "", "Status": "NOT FOUND", "Updated UTC": updated,
            })
            continue
        gp = numeric(row, "gamesPlayed", "gp")
        goals = numeric(row, "goals")
        assists = numeric(row, "assists")
        shots = numeric(row, "shots")
        fp = skater_fantasy_points(goals, assists, shots)
        skater_rows.append({
            "Player": requested,
            "Position": row.get("position", "Skater"),
            "Team": row.get("teamAbbrev", row.get("team", "")),
            "GP": int(gp) if gp.is_integer() else gp,
            "G": int(goals) if goals.is_integer() else goals,
            "A": int(assists) if assists.is_integer() else assists,
            "SOG": int(shots) if shots.is_integer() else shots,
            "Fantasy Points": fp,
            "Fantasy Pts/GP": round(fp / gp, 2) if gp else "",
            "Status": "OK",
            "Updated UTC": updated,
        })

    goalie_rows = []
    for requested in CONFIG["goalies"]:
        row = find_player(goalies, requested)
        if row is None:
            goalie_rows.append({
                "Player": requested, "Position": "G", "GP": "", "W": "", "SO": "",
                "Fantasy Points": "", "Fantasy Pts/GP": "", "Status": "NOT FOUND", "Updated UTC": updated,
            })
            continue
        gp = numeric(row, "gamesPlayed", "gp")
        wins = numeric(row, "wins")
        shutouts = numeric(row, "shutouts")
        fp = goalie_fantasy_points(wins, shutouts)
        goalie_rows.append({
            "Player": requested,
            "Position": "G",
            "Team": row.get("teamAbbrev", row.get("team", "")),
            "GP": int(gp) if gp.is_integer() else gp,
            "W": int(wins) if wins.is_integer() else wins,
            "SO": int(shutouts) if shutouts.is_integer() else shutouts,
            "Fantasy Points": fp,
            "Fantasy Pts/GP": round(fp / gp, 2) if gp else "",
            "Status": "OK",
            "Updated UTC": updated,
        })

    skater_rows.sort(key=lambda r: float(r["Fantasy Points"]) if r["Fantasy Points"] != "" else -1, reverse=True)
    goalie_rows.sort(key=lambda r: float(r["Fantasy Points"]) if r["Fantasy Points"] != "" else -1, reverse=True)
    return skater_rows, goalie_rows
