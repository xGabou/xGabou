import json
import os
import urllib.request

MODRINTH_SLUGS = [
    "project-atmosphere",
    "identity-fix",
    "serene-seasons-plus",
    "oculus-for-simple-clouds",
    "atmospheric-shaders",
]

CURSEFORGE_IDS = [
    1258344,
    1238155,
    1288843,
    1386686,
    1387076,
]

def http_get_json(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def modrinth_total() -> int:
    total = 0
    for slug in MODRINTH_SLUGS:
        data = http_get_json(f"https://api.modrinth.com/v2/project/{slug}")
        total += int(data.get("downloads", 0))
    return total

def curseforge_total(api_key: str) -> int:
    total = 0
    headers = {"x-api-key": api_key}
    for mod_id in CURSEFORGE_IDS:
        data = http_get_json(f"https://api.curseforge.com/v1/mods/{mod_id}", headers=headers)
        total += int(data["data"].get("downloadCount", 0))
    return total

def patch_gist(gist_id: str, token: str, filename: str, content: str) -> None:
    url = f"https://api.github.com/gists/{gist_id}"
    payload = {"files": {filename: {"content": content}}}
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
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()

def main() -> None:
    gist_id = os.environ["GIST_ID"]
    gist_token = os.environ["GIST_TOKEN"]
    cf_key = os.environ["CURSEFORGE_API_KEY"]

    total = modrinth_total() + curseforge_total(cf_key)

    badge = {
        "schemaVersion": 1,
        "label": "Total downloads",
        "message": f"{total:,}",
        "color": "blue",
    }

    patch_gist(
        gist_id=gist_id,
        token=gist_token,
        filename="mod-downloads-total.json",
        content=json.dumps(badge, ensure_ascii=False),
    )

if __name__ == "__main__":
    main()
