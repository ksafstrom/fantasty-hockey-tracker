
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nhl_api import (
    resolve_player,
    player_game_log,
    goalie_season_stats,
)

from scoring import (
    goalie_fantasy_points,
    skater_fantasy_points,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "players.json").read_text())
SEASON = CONFIG["season"]


def calculate_skater_stats(games):
    goals = sum(g.get("goals", 0) or 0 for g in games)
    assists = sum(g.get("assists", 0) or 0 for g in games)
    shots = sum(g.get("shots", 0) or 0 for g in games)

    return {
        "gp": len(games),
        "goals": goals,
        "assists": assists,
        "shots": shots,
    }


def build_tracker() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]]
]:
    updated = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    skater_rows = []
    goalie_rows = []
    errors = []

    # ----------------------------------
    # SKATERS
    # ----------------------------------

    for requested in dict.fromkeys(CONFIG["skaters"]):

        try:
            player = resolve_player(requested)
            player_id = player["playerId"]

            data = player_game_log(player_id, SEASON)
            games = data.get("gameLog", [])

            stats = calculate_skater_stats(games)

            gp = stats["gp"]
            goals = stats["goals"]
            assists = stats["assists"]
            shots = stats["shots"]

            fp = skater_fantasy_points(
                goals,
                assists,
                shots
            )

            skater_rows.append({
                "Player": requested,
                "Position": player.get(
                    "positionCode", "Skater"
                ),
                "Team": player.get("teamAbbrev", ""),
                "GP": gp,
                "G": goals,
                "A": assists,
                "SOG": shots,
                "Fantasy Points": fp,
                "Fantasy Pts/GP": round(fp / gp, 2) if gp else 0,
                "Status": "OK" if gp else "NO GAMES",
                "Updated UTC": updated,
            })

        except Exception as exc:
            errors.append(f"{requested}: {exc}")

            skater_rows.append({
                "Player": requested,
                "Position": "Skater",
                "Team": "",
                "GP": "",
                "G": "",
                "A": "",
                "SOG": "",
                "Fantasy Points": "",
                "Fantasy Pts/GP": "",
                "Status": "ERROR",
                "Updated UTC": updated,
            })

    # ----------------------------------
    # GOALTENDERS
    # ----------------------------------

    for requested in dict.fromkeys(CONFIG["goalies"]):

        try:
            player = resolve_player(requested)
            player_id = player["playerId"]

            stats = goalie_season_stats(
                player_id,
                SEASON
            )

            gp = stats["gp"]
            wins = stats["wins"]
            shutouts = stats["shutouts"]

            fp = goalie_fantasy_points(
                wins,
                shutouts
            )

            goalie_rows.append({
                "Player": requested,
                "Position": "G",
                "Team": player.get("teamAbbrev", ""),
                "GP": gp,
                "W": wins,
                "SO": shutouts,
                "Fantasy Points": fp,
                "Fantasy Pts/GP": round(fp / gp, 2) if gp else 0,
                "Status": "OK" if gp else "NO GAMES",
                "Updated UTC": updated,
            })

        except Exception as exc:
            errors.append(f"{requested}: {exc}")

            goalie_rows.append({
                "Player": requested,
                "Position": "G",
                "Team": "",
                "GP": "",
                "W": "",
                "SO": "",
                "Fantasy Points": "",
                "Fantasy Pts/GP": "",
                "Status": "ERROR",
                "Updated UTC": updated,
            })

    # ----------------------------------
    # SORTING
    # ----------------------------------

    def sort_points(row):
        value = row["Fantasy Points"]
        return float(value) if value != "" else -1

    skater_rows.sort(
        key=sort_points,
        reverse=True
    )

    goalie_rows.sort(
        key=sort_points,
        reverse=True
    )

    # Do not publish an incomplete tracker.
    if errors:
        raise RuntimeError(
            "Tracker update aborted due to NHL API errors:\n"
            + "\n".join(errors)
        )

    return skater_rows, goalie_rows
