import json
import os
import urllib.parse
import urllib.request

USER = "xGabou"

def get_json(url: str, headers: dict | None = None) -> object:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "xGabou-downloads-badge",
            **(headers or {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def patch_gist(gist_id: str, token: str, content: str) -> None:
    url = f"https://api.github.com/gists/{gist_id}"
    payload = {"files": {"mod-downloads-total.json": {"content": content}}}
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="PATCH",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "xGabou-downloads-badge",
        },
    )
    urllib.request.urlopen(req, timeout=30).read()

def get_modrinth_downloads_owner_only(username: str) -> int:
    projects = get_json(f"https://api.modrinth.com/v2/user/{username}/projects")

    total = 0
    for p in projects:
        team_id = p.get("team")
        if not team_id:
            continue

        members = get_json(f"https://api.modrinth.com/v2/team/{team_id}/members")

        is_owner = False
        for m in members:
            u = (m or {}).get("user") or {}
            if u.get("username") == username and (m.get("role") == "Owner"):
                is_owner = True
                break

        if is_owner:
            total += int(p.get("downloads", 0))

    return total

def get_curseforge_downloads(author_id: int, api_key: str) -> int:
    # CurseForge REST API base
    base = "https://api.curseforge.com/v1/mods/search"

    # Minecraft gameId = 432
    # classId = 6 (Mods)
    params = {
        "gameId": 432,
        "classId": 6,
        "authorId": author_id,
        "pageSize": 50,
        "index": 0,
    }

    headers = {"x-api-key": api_key}

    total = 0
    while True:
        url = base + "?" + urllib.parse.urlencode(params)
        data = get_json(url, headers=headers)

        items = (data or {}).get("data") or []
        if not items:
            break

        for mod in items:
            total += int(mod.get("downloadCount", 0))

        # Pagination
        if len(items) < params["pageSize"]:
            break
        params["index"] += params["pageSize"]

    return total

if __name__ == "__main__":
    gist_id = os.environ["GIST_ID"]
    gist_token = os.environ["GIST_TOKEN"]

    # Modrinth
    modrinth_total = get_modrinth_downloads_owner_only(USER)

    # CurseForge
    # Tu dois fournir ton authorId CurseForge et ta clé API
    curseforge_author_id = int(os.environ["CURSEFORGE_AUTHOR_ID"])
    curseforge_api_key = os.environ["CURSEFORGE_API_KEY"]
    curseforge_total = get_curseforge_downloads(curseforge_author_id, curseforge_api_key)

    badge = {
        "schemaVersion": 1,
        "label": "Downloads",
        "message": f"CF {curseforge_total:,} | MR {modrinth_total:,}",
        "color": "blue",
    }

    patch_gist(gist_id, gist_token, json.dumps(badge))
