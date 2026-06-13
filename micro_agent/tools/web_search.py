# micro_agent/tools/web_search.py
"""web_search — DuckDuckGo HTML lite 搜索。"""

import re, requests, html

UA = {"User-Agent": "Mozilla/5.0 Windows NT 10.0; Win64; x64 MicroAgent/0.2"}


def _decode_html(value: str) -> str:
    return value.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ").replace("&#x27;", "'").replace("&quot;", "\"")


def web_search(query: str) -> str:
    try:
        r = requests.get("https://lite.duckduckgo.com/lite/",
            params={"q": query}, headers=UA, timeout=12)
        if r.status_code != 200:
            return f"Search error: HTTP {r.status_code}"

        # Parse DDGo lite HTML results
        results = []
        for m in re.finditer(r'<a\b[^>]*class="[^"]*result-link[^"]*"[^>]*href="([^"]*)"[^>]*>([\s\S]*?)</a>', r.text):
            href = m.group(1)
            title = _decode_html(re.sub(r'<[^>]+>', ' ', m.group(2)).strip())
            if title and href:
                results.append(f"[{len(results)+1}] {title}\n    {href}")
            if len(results) >= 5:
                break

        return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {e}"
