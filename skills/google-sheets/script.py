import os
import json
import httpx

try:
    from google.oauth2 import credentials, service_account
    from google.auth.transport.requests import Request as AuthRequest
except ImportError:
    print(json.dumps({"error": "google-auth not installed. pip install google-auth"}))
    raise SystemExit(1)

SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
DRIVE_API = "https://www.googleapis.com/drive/v3/files"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"]


def get_creds(creds_json):
    if creds_json.get("type") == "authorized_user":
        creds = credentials.Credentials.from_authorized_user_info(creds_json, scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    creds.refresh(AuthRequest())
    return creds


def headers(creds):
    return {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}


def do_list_spreadsheets(creds, query, limit):
    q = "mimeType='application/vnd.google-apps.spreadsheet'"
    if query:
        q += f" and name contains '{query}'"
    params = {"q": q, "pageSize": min(limit, 50), "fields": "files(id,name,modifiedTime,webViewLink)"}
    with httpx.Client(timeout=15) as c:
        r = c.get(DRIVE_API, headers=headers(creds), params=params)
        r.raise_for_status()
        data = r.json()
    files = data.get("files", [])
    return {
        "spreadsheets": [
            {"id": f["id"], "name": f["name"], "modified": f.get("modifiedTime", ""), "url": f.get("webViewLink", "")}
            for f in files
        ],
        "count": len(files),
    }


def do_get_sheet_info(creds, spreadsheet_id):
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{SHEETS_API}/{spreadsheet_id}", headers=headers(creds),
                   params={"fields": "spreadsheetId,properties.title,sheets.properties"})
        r.raise_for_status()
        data = r.json()
    sheets = data.get("sheets", [])
    return {
        "spreadsheet_id": data.get("spreadsheetId", ""),
        "title": data.get("properties", {}).get("title", ""),
        "sheets": [
            {
                "name": s["properties"]["title"],
                "index": s["properties"]["index"],
                "row_count": s["properties"].get("gridProperties", {}).get("rowCount", 0),
                "column_count": s["properties"].get("gridProperties", {}).get("columnCount", 0),
            }
            for s in sheets
        ],
    }


def do_read_sheet(creds, spreadsheet_id, range_str):
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{SHEETS_API}/{spreadsheet_id}/values/{range_str}", headers=headers(creds))
        r.raise_for_status()
        data = r.json()
    values = data.get("values", [])
    return {"range": data.get("range", ""), "values": values, "rows": len(values)}


def do_write_cells(creds, spreadsheet_id, range_str, values):
    if isinstance(values, str):
        values = json.loads(values)
    body = {"range": range_str, "majorDimension": "ROWS", "values": values}
    with httpx.Client(timeout=15) as c:
        r = c.put(
            f"{SHEETS_API}/{spreadsheet_id}/values/{range_str}",
            headers=headers(creds), json=body,
            params={"valueInputOption": "USER_ENTERED"},
        )
        r.raise_for_status()
        data = r.json()
    return {"updated_range": data.get("updatedRange", ""), "updated_cells": data.get("updatedCells", 0)}


def do_append_rows(creds, spreadsheet_id, range_str, values):
    if isinstance(values, str):
        values = json.loads(values)
    body = {"range": range_str, "majorDimension": "ROWS", "values": values}
    with httpx.Client(timeout=15) as c:
        r = c.post(
            f"{SHEETS_API}/{spreadsheet_id}/values/{range_str}:append",
            headers=headers(creds), json=body,
            params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
        )
        r.raise_for_status()
        data = r.json()
    updates = data.get("updates", {})
    return {"updated_range": updates.get("updatedRange", ""), "updated_rows": updates.get("updatedRows", 0)}


def do_create_spreadsheet(creds, title, sheet_names):
    body = {"properties": {"title": title}}
    if sheet_names:
        names = [n.strip() for n in sheet_names.split(",") if n.strip()]
        body["sheets"] = [{"properties": {"title": name}} for name in names]
    with httpx.Client(timeout=15) as c:
        r = c.post(SHEETS_API, headers=headers(creds), json=body)
        r.raise_for_status()
        data = r.json()
    return {
        "spreadsheet_id": data["spreadsheetId"],
        "title": data["properties"]["title"],
        "url": data.get("spreadsheetUrl", ""),
        "sheets": [s["properties"]["title"] for s in data.get("sheets", [])],
    }


try:
    creds_json = json.loads(os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"])
    creds = get_creds(creds_json)
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    action = inp.get("action", "")

    if action == "list_spreadsheets":
        result = do_list_spreadsheets(creds, inp.get("query", ""), inp.get("limit", 10))
    elif action == "get_sheet_info":
        result = do_get_sheet_info(creds, inp.get("spreadsheet_id", ""))
    elif action == "read_sheet":
        result = do_read_sheet(creds, inp.get("spreadsheet_id", ""), inp.get("range", "Sheet1"))
    elif action == "write_cells":
        result = do_write_cells(creds, inp.get("spreadsheet_id", ""), inp.get("range", "Sheet1"), inp.get("values", "[]"))
    elif action == "append_rows":
        result = do_append_rows(creds, inp.get("spreadsheet_id", ""), inp.get("range", "Sheet1"), inp.get("values", "[]"))
    elif action == "create_spreadsheet":
        result = do_create_spreadsheet(creds, inp.get("title", "Untitled"), inp.get("sheet_names", ""))
    else:
        result = {"error": f"Unknown action: {action}"}

    print(json.dumps(result))

except Exception as e:
    print(json.dumps({"error": str(e)}))
