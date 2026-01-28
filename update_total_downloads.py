import json
import os
import re
import urllib.request

MODRINTH_USER = os.getenv("MODRINTH_USER", "Gaboouu")
CURSEFORGE_USER = os.getenv("CURSEFORGE_USER", "gaboouu")

def get_text(url: str, headers: dict | None = None) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "downloads-badge-updater", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def get_json(url: str, headers: dict | None = None) -> object:
    return json.loads(get_text(url, headers=headers))

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
            "User-Agent": "downloads-badge-updater",
        },
    )
    urllib.request.urlopen(req, timeout=30).read()

def parse_compact_number(s: str) -> int:
    t = s.strip().replace(",", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([KMB])?", t, flags=re.IGNORECASE)
    if not m:
        return int(float(t))
    val = float(m.group(1))
    suf = (m.group(2) or "").upper()
    mult = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[suf]
    return int(val * mult)

def get_modrinth_user_id(username_or_id: str) -> str:
    user = get_json(f"https://api.modrinth.com/v2/user/{username_or_id}")
    user_id = (user or {}).get("id")
    if not user_id:
        raise RuntimeError("Modrinth user id introuvable")
    return user_id

def get_modrinth_downloads(username_or_id: str) -> int:
    user_id = get_modrinth_user_id(username_or_id)
    projects = get_json(f"https://api.modrinth.com/v2/user/{user_id}/projects")
    return sum(int(p.get("downloads", 0)) for p in projects)

def get_curseforge_total_downloads_from_profile(username: str) -> int:
    html = get_text(f"https://www.curseforge.com/members/{username}/projects")
    m = re.search(r"(\d+(?:\.\d+)?)\s*([KMB])?\s*Downloads", html, flags=re.IGNORECASE)
    if not m:
        raise RuntimeError("Impossible de trouver le total Downloads sur la page CurseForge")
    return parse_compact_number(m.group(1) + (m.group(2) or ""))

if __name__ == "__main__":
    gist_id = os.environ["GIST_ID"]
    gist_token = os.environ["GIST_TOKEN"]

    modrinth_total = get_modrinth_downloads(MODRINTH_USER)
    curseforge_total = get_curseforge_total_downloads_from_profile(CURSEFORGE_USER)

    badge = {
        "schemaVersion": 1,
        "label": "Downloads",
        "message": f"CF {curseforge_total:,} | MR {modrinth_total:,}",
        "color": "blue",
    }

    patch_gist(gist_id, gist_token, json.dumps(badge))
