# micro_agent/tools/wiki.py
"""get_wiki_summary — Wikipedia REST API 摘要。"""

import requests

UA = {"User-Agent": "MicroAgent/0.1.0"}


def get_wiki_summary(pageid_or_title: str, sentences: int = 5) -> str:
    try:
        pid = int(pageid_or_title)
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{pid}",
            headers=UA, timeout=10)
    except ValueError:
        r = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/",
            params={"title": pageid_or_title}, headers=UA, timeout=10)
    if r.status_code == 404:
        return f"Page not found: {pageid_or_title}"
    r.raise_for_status()
    d = r.json()
    s = ". ".join(d.get("extract","").split(". ")[:sentences])
    url = d.get("content_urls",{}).get("desktop",{}).get("page","")
    return f"{s}.\n- {url}" if url else s
