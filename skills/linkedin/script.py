import os
import json
import httpx

REST_BASE = "https://api.linkedin.com/rest"
API_VERSION = "202402"


def get_access_token():
    return os.environ.get("LINKEDIN_ACCESS_TOKEN", "")


def _rest_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "LinkedIn-Version": API_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
    }


def api_get(headers, path, params=None, timeout=15):
    with httpx.Client(timeout=timeout) as c:
        r = c.get(f"{REST_BASE}/{path}", headers=headers, params=params)
        r.raise_for_status()
        return r.json()


def api_post(headers, path, body, timeout=15):
    with httpx.Client(timeout=timeout) as c:
        r = c.post(f"{REST_BASE}/{path}", headers=headers, json=body)
        r.raise_for_status()
        return r.json() if r.content else {}


def api_delete(headers, path, timeout=15):
    with httpx.Client(timeout=timeout) as c:
        r = c.delete(f"{REST_BASE}/{path}", headers=headers)
        r.raise_for_status()
        return None


# --- Actions ---


def do_get_profile(headers):
    with httpx.Client(timeout=15) as c:
        r = c.get("https://api.linkedin.com/v2/userinfo", headers={
            "Authorization": headers["Authorization"],
            "Accept": "application/json",
        })
        r.raise_for_status()
        data = r.json()
    return {
        "sub": data.get("sub", ""),
        "name": data.get("name", ""),
        "given_name": data.get("given_name", ""),
        "family_name": data.get("family_name", ""),
        "email": data.get("email", ""),
        "picture": data.get("picture", ""),
    }


def _get_person_urn(headers):
    """Get the authenticated user's person URN."""
    with httpx.Client(timeout=15) as c:
        r = c.get("https://api.linkedin.com/v2/userinfo", headers={
            "Authorization": headers["Authorization"],
            "Accept": "application/json",
        })
        r.raise_for_status()
        data = r.json()
    sub = data.get("sub", "")
    if not sub:
        raise ValueError("Could not determine LinkedIn user ID")
    return f"urn:li:person:{sub}"


def do_create_post(headers, person_urn, text, visibility="PUBLIC"):
    if not text or not text.strip():
        return {"error": "text is required for create_post"}
    body = {
        "author": person_urn,
        "commentary": text.strip(),
        "visibility": visibility.upper(),
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
    }
    data = api_post(headers, "posts", body)
    # REST API returns post URN in x-restli-id header or in response
    post_urn = data.get("id", "") or data.get("urn", "")
    return {
        "post_urn": post_urn,
        "created": True,
    }


def do_share_url(headers, person_urn, url, title="", text="", visibility="PUBLIC"):
    if not url or not url.strip():
        return {"error": "url is required for share_url"}
    article = {
        "source": url.strip(),
    }
    if title and title.strip():
        article["title"] = title.strip()

    body = {
        "author": person_urn,
        "commentary": text.strip() if text else "",
        "visibility": visibility.upper(),
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {
            "article": article,
        },
        "lifecycleState": "PUBLISHED",
    }
    data = api_post(headers, "posts", body)
    return {
        "post_urn": data.get("id", "") or data.get("urn", ""),
        "created": True,
    }


def do_delete_post(headers, post_urn):
    if not post_urn or not post_urn.strip():
        return {"error": "post_urn is required for delete_post"}
    urn = post_urn.strip()
    from urllib.parse import quote
    encoded = quote(urn, safe="")
    api_delete(headers, f"posts/{encoded}")
    return {"post_urn": urn, "deleted": True}


def do_get_company(headers, organization_id):
    if not organization_id or not organization_id.strip():
        return {"error": "organization_id is required for get_company"}
    org_id = organization_id.strip()
    data = api_get(headers, f"organizations/{org_id}", params={
        "projection": "(id,localizedName,vanityName,logoV2,description,staffCountRange)"
    })
    return {
        "id": data.get("id", ""),
        "name": data.get("localizedName", ""),
        "vanity_name": data.get("vanityName", ""),
        "description": (data.get("description", {}) or {}).get("localized", {}).get("en_US", ""),
        "staff_count_range": data.get("staffCountRange", ""),
    }


def do_create_company_post(headers, organization_id, text, visibility="PUBLIC"):
    if not organization_id or not organization_id.strip():
        return {"error": "organization_id is required for create_company_post"}
    if not text or not text.strip():
        return {"error": "text is required for create_company_post"}
    org_urn = f"urn:li:organization:{organization_id.strip()}"
    body = {
        "author": org_urn,
        "commentary": text.strip(),
        "visibility": visibility.upper(),
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
    }
    data = api_post(headers, "posts", body)
    return {
        "post_urn": data.get("id", "") or data.get("urn", ""),
        "organization_id": organization_id.strip(),
        "created": True,
    }


def do_react_to_post(headers, person_urn, post_urn, reaction_type="LIKE"):
    if not post_urn or not post_urn.strip():
        return {"error": "post_urn is required for react_to_post"}
    valid_reactions = ["LIKE", "PRAISE", "EMPATHY", "INTEREST", "APPRECIATION", "ENTERTAINMENT", "MAYBE"]
    reaction_type = reaction_type.upper() if reaction_type else "LIKE"
    if reaction_type not in valid_reactions:
        return {"error": f"Invalid reaction_type. Must be one of: {', '.join(valid_reactions)}"}

    urn = post_urn.strip()
    from urllib.parse import quote
    encoded_urn = quote(urn, safe="")

    body = {
        "root": urn,
        "reactionType": reaction_type,
    }
    with httpx.Client(timeout=15) as c:
        r = c.post(
            f"{REST_BASE}/reactions",
            headers=headers,
            json=body,
        )
        r.raise_for_status()

    return {
        "post_urn": urn,
        "reaction_type": reaction_type,
        "reacted": True,
    }


def do_create_comment(headers, person_urn, post_urn, comment_text):
    if not post_urn or not post_urn.strip():
        return {"error": "post_urn is required for create_comment"}
    if not comment_text or not comment_text.strip():
        return {"error": "comment text is required for create_comment"}
    urn = post_urn.strip()
    from urllib.parse import quote
    encoded_urn = quote(urn, safe="")

    body = {
        "actor": person_urn,
        "object": urn,
        "message": {"text": comment_text.strip()},
    }
    with httpx.Client(timeout=15) as c:
        r = c.post(
            f"{REST_BASE}/socialActions/{encoded_urn}/comments",
            headers=headers,
            json=body,
        )
        r.raise_for_status()

    return {
        "post_urn": urn,
        "commented": True,
    }


def do_get_connections_count(headers):
    # Use the me endpoint with network sizes
    data = api_get(headers, "networkSizes/urn:li:fsd_profile:me", params={
        "edgeType": "COMPANYFOLLOWER",
    })
    return {
        "count": data.get("firstDegreeSize", 0),
    }


# --- Main ---

try:
    access_token = get_access_token()
    if not access_token:
        raise ValueError("No LinkedIn access token available. Please reconnect the LinkedIn gateway.")
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    action = inp.get("action", "")

    headers = _rest_headers(access_token)

    if action == "get_profile":
        result = do_get_profile(headers)
    elif action == "create_post":
        person_urn = _get_person_urn(headers)
        visibility = inp.get("visibility", "PUBLIC")
        result = do_create_post(headers, person_urn, inp.get("text", ""), visibility)
    elif action == "share_url":
        person_urn = _get_person_urn(headers)
        visibility = inp.get("visibility", "PUBLIC")
        result = do_share_url(headers, person_urn, inp.get("url", ""), inp.get("title", ""), inp.get("text", ""), visibility)
    elif action == "delete_post":
        result = do_delete_post(headers, inp.get("post_urn", ""))
    elif action == "get_company":
        result = do_get_company(headers, inp.get("organization_id", ""))
    elif action == "create_company_post":
        visibility = inp.get("visibility", "PUBLIC")
        result = do_create_company_post(headers, inp.get("organization_id", ""), inp.get("text", ""), visibility)
    elif action == "react_to_post":
        person_urn = _get_person_urn(headers)
        result = do_react_to_post(headers, person_urn, inp.get("post_urn", ""), inp.get("reaction_type", "LIKE"))
    elif action == "create_comment":
        person_urn = _get_person_urn(headers)
        result = do_create_comment(headers, person_urn, inp.get("post_urn", ""), inp.get("comment", ""))
    elif action == "get_connections_count":
        result = do_get_connections_count(headers)
    else:
        result = {"error": f"Unknown action: {action}. Available: get_profile, create_post, share_url, delete_post, get_company, create_company_post, react_to_post, create_comment, get_connections_count"}

    print(json.dumps(result))

except httpx.HTTPStatusError as e:
    status = e.response.status_code
    detail = ""
    try:
        detail = e.response.json().get("message", "") or str(e.response.json())
    except Exception:
        detail = e.response.text[:200]
    print(json.dumps({"error": f"LinkedIn API error {status}: {detail}" if detail else f"LinkedIn API error {status}"}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
