# micro_agent/tools/web.py
"""fetch_page — 抓取网页全文。"""

import re
import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "MicroAgent/0.1.0"}


def fetch_page(url: str) -> str:
    try:
        r = requests.get(url, timeout=10, headers=UA); r.raise_for_status()
        soup = BeautifulSoup(r.text,"html.parser")
        for t in soup(["script","style","nav","footer","header"]): t.decompose()
        text = re.sub(r"\n\s*\n","\n\n", soup.get_text(separator="\n")).strip()
        return text[:3000] if len(text)>3000 else text
    except Exception as e:
        return f"Fetch error: {e}"
