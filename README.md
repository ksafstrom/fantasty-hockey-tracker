# Fantasy Hockey Live Tracker

Automated NHL fantasy tracker for a custom league:

- Skaters: 1 point per goal + 1 point per assist + 0.1 point per shot on goal
- Goalies: 1 point per win + 2 additional points per shutout

The tracker pulls current statistics from the NHL web API and writes the results to Google Sheets. It is designed to run locally or automatically daily with GitHub Actions.

## 1. Create the Google Sheet

Create a blank Google Sheet. Copy its ID from the URL:

`https://docs.google.com/spreadsheets/d/GOOGLE_SHEET_ID/edit`

You will share this sheet with a Google service account in the next step.

## 2. Create a Google service account

In Google Cloud:

1. Create/select a project.
2. Enable the Google Sheets API.
3. Create a service account.
4. Create a JSON key for the service account and download it as `service-account.json`.
5. Copy the service account's email address.
6. Share your Google Sheet with that email address as **Editor**.

Keep `service-account.json` private. It is already excluded by `.gitignore`.

## 3. Local setup

Python 3.10+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set your variables.

macOS/Linux:

```bash
export GOOGLE_SHEET_ID="your_sheet_id"
export GOOGLE_SERVICE_ACCOUNT_FILE="service-account.json"
python main.py
```

Windows PowerShell:

```powershell
$env:GOOGLE_SHEET_ID="your_sheet_id"
$env:GOOGLE_SERVICE_ACCOUNT_FILE="service-account.json"
python main.py
```

The script creates/updates three tabs:

- `Summary`
- `Skaters`
- `Goalies`

## 4. GitHub Actions automation

Create two GitHub repository secrets:

- `GOOGLE_SHEET_ID` = your spreadsheet ID
- `GOOGLE_SERVICE_ACCOUNT_JSON` = the entire contents of `service-account.json`

Push the repository to GitHub. The workflow runs every 30 minutes and can also be started manually from the Actions tab.

## 5. Change your player list

Edit `players.json`.

The current season is configured as `20262027`.

## Notes

The NHL API's current leader endpoints are used for goals, assists, shots, wins and shutouts. The tracker intentionally calculates your league's custom fantasy score instead of using NHL/Yahoo/ESPN fantasy scoring.

If the NHL API temporarily fails, the script retries three times and exits rather than overwriting the Sheet with bad data.
