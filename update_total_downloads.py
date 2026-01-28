import json
import os
import urllib.request

USER = "xGabou"

def get(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "xGabou-downloads-badge"})
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

if __name__ == "__main__":
    gist_id = os.environ["GIST_ID"]
    gist_token = os.environ["GIST_TOKEN"]

    projects = get(f"https://api.modrinth.com/v2/user/{USER}/projects")
    total = sum(int(p.get("downloads", 0)) for p in projects)

    badge = {
        "schemaVersion": 1,
        "label": "Modrinth downloads",
        "message": f"{total:,}",
        "color": "blue",
    }

    patch_gist(gist_id, gist_token, json.dumps(badge))
