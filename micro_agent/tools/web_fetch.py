# micro_agent/tools/web_fetch.py
"""web_fetch — 抓取网页，提取可读文本。"""

import re, requests, html

UA = {"User-Agent": "Mozilla/5.0 Windows NT 10.0; Win64; x64 MicroAgent/0.2"}


def _decode_html(value: str) -> str:
    return value.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ").replace("&#x27;", "'").replace("&quot;", "\"")


def web_fetch(url: str) -> str:
    try:
        r = requests.get(url, headers=UA, timeout=12, allow_redirects=True)
        if r.status_code >= 400:
            return f"HTTP {r.status_code}: {url}"

        text = r.text
        # Remove scripts, styles, nav, footer
        for tag in ["script", "style", "nav", "footer", "header", "noscript"]:
            text = re.sub(rf"<{tag}[^>]*>[\s\S]*?</{tag}>", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        # Extract title
        title_match = re.search(r"<title[^>]*>([\s\S]*?)</title>", r.text, re.IGNORECASE)
        title = _decode_html(title_match.group(1).strip()) if title_match else ""

        return f"URL: {r.url}\nTITLE: {title}\n\n{text[:8000]}"
    except Exception as e:
        return f"Fetch error: {e}"
