# micro_agent/tools/search.py
"""web_search — Wikipedia API + DuckDuckGo 搜索。"""

import re
import requests

UA = {"User-Agent": "MicroAgent/0.1.0"}


def web_search(query: str) -> str:
    parts = []
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php",
            params={"action":"query","list":"search","srsearch":query,
                    "format":"json","srlimit":3,"origin":"*"},
            headers=UA, timeout=10)
        for i, p in enumerate(r.json().get("query",{}).get("search",[])[:3]):
            s = re.sub(r"<[^>]+>", "", p["snippet"])
            parts.append(f"[{i+1}] {p['title']} (pageid:{p['pageid']})\n    {s[:250]}")
    except: pass
    try:
        r2 = requests.get("https://api.duckduckgo.com/",
            params={"q":query,"format":"json","no_html":1,"skip_disambig":1}, timeout=10)
        a = r2.json().get("Abstract","")
        if a: parts.append(f"[DDG] {a[:400]}")
    except: pass
    return "\n\n".join(parts) or f"No results for '{query}'."
