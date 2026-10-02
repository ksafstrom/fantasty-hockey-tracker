
def update_sheet(
    spreadsheet_id: str,
    skaters: list[dict[str, Any]],
    goalies: list[dict[str, Any]]
) -> None:

    client = get_client()
    spreadsheet = client.open_by_key(spreadsheet_id)

    def write_tab(title, rows, headers):
        try:
            ws = spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(
                title=title,
                rows=max(len(rows) + 5, 20),
                cols=len(headers)
            )

        values = [headers] + [
            [r.get(h, "") for h in headers]
            for r in rows
        ]

        ws.clear()
        ws.update(values, "A1")
        ws.freeze(rows=1)
        ws.format(
            "A1:Z1",
            {"textFormat": {"bold": True}}
        )

    skater_headers = [
        "Player", "Position", "Team", "GP",
        "G", "A", "SOG", "Fantasy Points",
        "Fantasy Pts/GP", "Status", "Updated UTC"
    ]

    goalie_headers = [
        "Player", "Position", "Team", "GP",
        "W", "SO", "Fantasy Points",
        "Fantasy Pts/GP", "Status", "Updated UTC"
    ]

    write_tab("Skaters", skaters, skater_headers)
    write_tab("Goalies", goalies, goalie_headers)

    # ----------------------------------
    # SUMMARY TAB
    # ----------------------------------

    try:
        summary = spreadsheet.worksheet("Summary")
    except gspread.WorksheetNotFound:
        summary = spreadsheet.add_worksheet(
            title="Summary",
            rows=50,
            cols=6
        )

    summary.clear()

    summary_values = [
        ["Fantasy Hockey Tracker", ""],
        ["Season", "2026-27"],
        ["Skater scoring", "1 G + 1 A + 0.1 SOG"],
        ["Goalie scoring", "1 W + 2 SO"],
        [
            "Last updated (UTC)",
            skaters[0].get("Updated UTC", "") if skaters else ""
        ],
        ["", ""],
        ["Skaters", ""],
        ["Player", "Fantasy Points"],
    ]

    # Skater rows start at row 9
    skater_start = len(summary_values) + 1

    summary_values.extend([
        [r["Player"], r["Fantasy Points"]]
        for r in skaters
    ])

    skater_end = len(summary_values)

    # Add goalie section
    summary_values += [
        ["", ""],
        ["Goalies", ""],
        ["Player", "Fantasy Points"]
    ]

    goalie_start = len(summary_values) + 1

    summary_values.extend([
        [r["Player"], r["Fantasy Points"]]
        for r in goalies
    ])

    goalie_end = len(summary_values)

    # ----------------------------------
    # TOTAL FANTASY POINTS
    # ----------------------------------

    total_row = len(summary_values) + 2

    total_formula = (
        f"=SUM(B{skater_start}:B{skater_end})"
        f"+SUM(B{goalie_start}:B{goalie_end})"
    )

    summary_values.extend([
        ["", ""],
        ["TOTAL FANTASY POINTS", total_formula]
    ])

    # Write summary to Google Sheets
    summary.update(
        summary_values,
        "A1",
        value_input_option="USER_ENTERED"
    )

    # ----------------------------------
    # FORMATTING
    # ----------------------------------

    summary.format(
        "A1:B1",
        {
            "textFormat": {
                "bold": True,
                "fontSize": 14
            }
        }
    )

    summary.format(
        "A7:B8",
        {"textFormat": {"bold": True}}
    )

    # Format goalie section headers
    goalie_header_row = skater_end + 2

    summary.format(
        f"A{goalie_header_row}:B{goalie_header_row + 1}",
        {"textFormat": {"bold": True}}
    )

    # Highlight total row
    summary.format(
        f"A{total_row}:B{total_row}",
        {
            "textFormat": {
                "bold": True,
                "fontSize": 12
            },
            "backgroundColor": {
                "red": 0.88,
                "green": 0.94,
                "blue": 1.0
            }
        }
    )

    summary.freeze(rows=1)
