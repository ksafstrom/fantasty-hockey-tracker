from __future__ import annotations

import json
import os
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_client() -> gspread.Client:
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json")
        with open(path, "r", encoding="utf-8") as f:
            info = json.load(f)
    else:
        info = json.loads(raw)
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(credentials)


def update_sheet(spreadsheet_id: str, skaters: list[dict[str, Any]], goalies: list[dict[str, Any]]) -> None:
    client = get_client()
    spreadsheet = client.open_by_key(spreadsheet_id)

    def write_tab(title: str, rows: list[dict[str, Any]], headers: list[str]):
        try:
            ws = spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=title, rows=max(len(rows) + 5, 20), cols=len(headers))
        values = [headers] + [[r.get(h, "") for h in headers] for r in rows]
        ws.clear()
        ws.update(values, "A1")
        ws.freeze(rows=1)
        ws.format("A1:Z1", {"textFormat": {"bold": True}})

    skater_headers = ["Player", "Position", "Team", "GP", "G", "A", "SOG", "Fantasy Points", "Fantasy Pts/GP", "Status", "Updated UTC"]
    goalie_headers = ["Player", "Position", "Team", "GP", "W", "SO", "Fantasy Points", "Fantasy Pts/GP", "Status", "Updated UTC"]
    write_tab("Skaters", skaters, skater_headers)
    write_tab("Goalies", goalies, goalie_headers)

    try:
        summary = spreadsheet.worksheet("Summary")
    except gspread.WorksheetNotFound:
        summary = spreadsheet.add_worksheet(title="Summary", rows=20, cols=6)
    summary.clear()
    summary_values = [
        ["Fantasy Hockey Tracker", ""],
        ["Season", "2026-27"],
        ["Skater scoring", "1 G + 1 A + 0.1 SOG"],
        ["Goalie scoring", "1 W + 2 SO"],
        ["Last updated (UTC)", skaters[0].get("Updated UTC", "") if skaters else ""],
        ["", ""],
        ["Skaters", ""],
        ["Player", "Fantasy Points"],
    ]
    summary_values.extend([[r["Player"], r["Fantasy Points"]] for r in skaters])
    summary_values += [["", ""], ["Goalies", ""], ["Player", "Fantasy Points"]]
    summary_values.extend([[r["Player"], r["Fantasy Points"]] for r in goalies])
    summary.update(summary_values, "A1")
    summary.format("A1:B1", {"textFormat": {"bold": True, "fontSize": 14}})
    summary.format("A7:B8", {"textFormat": {"bold": True}})
    summary.freeze(rows=1)
