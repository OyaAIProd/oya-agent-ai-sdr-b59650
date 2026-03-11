import os
import json
import httpx

BASE = "https://api.instantly.ai/api/v2"


def _headers(key):
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def api(key, method, path, body=None, params=None, timeout=15):
    with httpx.Client(timeout=timeout) as c:
        url = f"{BASE}/{path}" if not path.startswith("http") else path
        r = c.request(method, url, json=body, params=params, headers=_headers(key))
        if r.status_code >= 400:
            try:
                err_body = r.json()
            except Exception:
                err_body = r.text
            raise Exception(f"Instantly API {r.status_code} on {path}: {json.dumps(err_body) if isinstance(err_body, dict) else err_body}")
        return r.json()


def _int(val, default):
    try:
        v = int(val)
        return v if v >= 1 else default
    except (TypeError, ValueError):
        return default


def do_list_campaigns(key, inp):
    params = {"limit": min(_int(inp.get("limit"), 10), 50)}
    if inp.get("search"):
        params["search"] = inp["search"]
    if inp.get("status"):
        params["status"] = inp["status"].upper()

    data = api(key, "GET", "campaigns", params=params)
    items = data if isinstance(data, list) else data.get("items", data.get("data", []))
    return {
        "campaigns": [
            {
                "id": c.get("id", ""),
                "name": c.get("name", ""),
                "status": c.get("status", ""),
                "created_at": c.get("timestamp_created", c.get("created_at", "")),
            }
            for c in (items if isinstance(items, list) else [])
        ],
    }


def do_get_campaign(key, inp):
    cid = inp.get("campaign_id", "")
    if not cid:
        return {"error": "Provide campaign_id"}

    data = api(key, "GET", f"campaigns/{cid}")
    return {
        "id": data.get("id", ""),
        "name": data.get("name", ""),
        "status": data.get("status", ""),
        "created_at": data.get("timestamp_created", data.get("created_at", "")),
    }


def do_add_lead(key, inp):
    cid = inp.get("campaign_id", "")
    email = inp.get("email", "")
    if not cid:
        return {"error": "Provide campaign_id"}
    if not email:
        return {"error": "Provide email"}

    body = {
        "campaign_id": cid,
        "email": email,
        "skip_if_in_workspace": False,
        "skip_if_in_campaign": True,
    }
    if inp.get("first_name"):
        body["first_name"] = inp["first_name"]
    if inp.get("last_name"):
        body["last_name"] = inp["last_name"]
    if inp.get("company_name"):
        body["company_name"] = inp["company_name"]
    if inp.get("website"):
        body["website"] = inp["website"]
    if inp.get("personalization"):
        body["personalization"] = inp["personalization"]

    # Custom variables
    if inp.get("custom_variables"):
        try:
            cv = json.loads(inp["custom_variables"]) if isinstance(inp["custom_variables"], str) else inp["custom_variables"]
            if isinstance(cv, dict):
                body["custom_variables"] = cv
        except (json.JSONDecodeError, TypeError):
            pass

    data = api(key, "POST", "leads", body)
    return {"status": "added", "email": email, "campaign_id": cid, "detail": data}


def do_add_leads_bulk(key, inp):
    cid = inp.get("campaign_id", "")
    leads_raw = inp.get("leads_json", "")
    if not cid:
        return {"error": "Provide campaign_id"}
    if not leads_raw:
        return {"error": "Provide leads_json (JSON array of lead objects)"}

    try:
        leads = json.loads(leads_raw) if isinstance(leads_raw, str) else leads_raw
    except (json.JSONDecodeError, TypeError):
        return {"error": "leads_json must be valid JSON array"}

    if not isinstance(leads, list) or not leads:
        return {"error": "leads_json must be a non-empty array"}

    # Format each lead
    formatted = []
    for lead in leads:
        entry = {"email": lead.get("email", "")}
        if not entry["email"]:
            continue
        for field in ("first_name", "last_name", "company_name", "website", "personalization"):
            if lead.get(field):
                entry[field] = lead[field]
        if lead.get("custom_variables"):
            cv = lead["custom_variables"]
            if isinstance(cv, str):
                try:
                    cv = json.loads(cv)
                except Exception:
                    pass
            if isinstance(cv, dict):
                entry["custom_variables"] = cv
        formatted.append(entry)

    if not formatted:
        return {"error": "No valid leads with email addresses found"}

    body = {
        "campaign_id": cid,
        "leads": formatted,
        "skip_if_in_workspace": False,
        "skip_if_in_campaign": True,
    }

    data = api(key, "POST", "leads", body)
    return {"status": "added", "count": len(formatted), "campaign_id": cid, "detail": data}


def do_list_leads(key, inp):
    cid = inp.get("campaign_id", "")
    if not cid:
        return {"error": "Provide campaign_id"}

    body = {
        "campaign_id": cid,
        "limit": min(_int(inp.get("limit"), 10), 100),
    }

    data = api(key, "POST", "leads/list", body)
    items = data if isinstance(data, list) else data.get("items", data.get("data", []))
    return {
        "leads": [
            {
                "email": l.get("email", ""),
                "first_name": l.get("first_name", ""),
                "last_name": l.get("last_name", ""),
                "company_name": l.get("company_name", ""),
                "status": l.get("lead_status", l.get("status", "")),
                "interest_status": l.get("interest_status", ""),
            }
            for l in (items if isinstance(items, list) else [])
        ],
        "total": data.get("total_count", len(items) if isinstance(items, list) else 0),
    }


def do_launch_campaign(key, inp):
    cid = inp.get("campaign_id", "")
    if not cid:
        return {"error": "Provide campaign_id"}

    data = api(key, "POST", f"campaigns/{cid}/launch")
    return {"status": "launched", "campaign_id": cid, "detail": data}


def do_pause_campaign(key, inp):
    cid = inp.get("campaign_id", "")
    if not cid:
        return {"error": "Provide campaign_id"}

    data = api(key, "POST", f"campaigns/{cid}/pause")
    return {"status": "paused", "campaign_id": cid, "detail": data}


def do_campaign_analytics(key, inp):
    cid = inp.get("campaign_id", "")
    params = {}
    if cid:
        params["id"] = cid

    data = api(key, "GET", "campaigns/analytics", params=params)

    # Handle both single campaign and overview responses
    if isinstance(data, list):
        results = data
    elif isinstance(data, dict) and "data" in data:
        results = data["data"] if isinstance(data["data"], list) else [data["data"]]
    else:
        results = [data]

    analytics = []
    for r in results:
        entry = {
            "campaign_id": r.get("campaign_id", r.get("id", cid)),
            "campaign_name": r.get("campaign_name", r.get("name", "")),
        }
        for field in ("total_leads", "leads_contacted", "contacted",
                       "emails_sent", "opens", "unique_opens",
                       "open_rate", "replies", "reply_rate",
                       "bounces", "bounce_rate", "unsubscribes",
                       "new_leads_contacted", "total_opportunities"):
            if field in r:
                entry[field] = r[field]
        analytics.append(entry)

    if len(analytics) == 1:
        return analytics[0]
    return {"campaigns": analytics}


def do_list_accounts(key, inp):
    params = {"limit": min(_int(inp.get("limit"), 25), 100)}
    data = api(key, "GET", "accounts", params=params)
    items = data if isinstance(data, list) else data.get("items", data.get("data", []))
    return {
        "accounts": [
            {
                "email": a.get("email", ""),
                "status": a.get("status", ""),
                "warmup_status": a.get("warmup_status", a.get("warmup", {}).get("status", "")),
                "daily_limit": a.get("daily_limit", a.get("sending_limit", "")),
            }
            for a in (items if isinstance(items, list) else [])
        ],
    }


try:
    key = os.environ["INSTANTLY_API_KEY"]
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    action = inp.get("action", "")

    actions = {
        "list_campaigns": do_list_campaigns,
        "get_campaign": do_get_campaign,
        "add_lead": do_add_lead,
        "add_leads_bulk": do_add_leads_bulk,
        "list_leads": do_list_leads,
        "launch_campaign": do_launch_campaign,
        "pause_campaign": do_pause_campaign,
        "campaign_analytics": do_campaign_analytics,
        "list_accounts": do_list_accounts,
    }

    handler = actions.get(action)
    if handler:
        result = handler(key, inp)
    else:
        result = {"error": f"Unknown action: {action}. Available: {', '.join(actions.keys())}"}

    print(json.dumps(result))

except Exception as e:
    print(json.dumps({"error": str(e)}))
