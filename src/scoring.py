from __future__ import annotations


def skater_fantasy_points(goals: float, assists: float, shots: float) -> float:
    return round(goals + assists + (shots * 0.1), 1)


def goalie_fantasy_points(wins: float, shutouts: float) -> float:
    return round(wins + (shutouts * 2), 1)
