from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from tracker import build_tracker  # noqa: E402
from sheets import update_sheet  # noqa: E402


def main() -> None:
    skaters, goalies = build_tracker()

    print("\nSKATERS")
    for r in skaters:
        print(f"{r['Player']}: {r['Fantasy Points']} FP ({r['G']} G, {r['A']} A, {r['SOG']} SOG)")

    print("\nGOALIES")
    for r in goalies:
        print(f"{r['Player']}: {r['Fantasy Points']} FP ({r['W']} W, {r['SO']} SO)")

    spreadsheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if spreadsheet_id:
        update_sheet(spreadsheet_id, skaters, goalies)
        print(f"\nGoogle Sheet updated: {spreadsheet_id}")
    else:
        print("\nGOOGLE_SHEET_ID not set; local stats-only run completed.")


if __name__ == "__main__":
    main()
