import time
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from urllib.parse import urljoin


# Safe HTTP requests - retry if a request fails, exponential wait, and polite throttling

HEADERS = {
    "User-Agent": "CLT-Legislation-Prototype/0.1 (academic research project)"
}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_page(url, params=None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=20)
    response.raise_for_status()
    time.sleep(2)  # polite rate limiting
    return response


#TODO: customize per site, depending on how search results are returned

def discover_candidates(search_url, keyword, state):
    params = {"q": keyword}
    response = fetch_page(search_url, params=params)
    soup = BeautifulSoup(response.text, "lxml")

    candidates = []

    for result in soup.select("div.search-result, li.search-result, tr"):
        link = result.select_one("a")
        if not link:
            continue

        href = link.get("href")
        title = link.get_text(" ", strip=True)
        snippet_el = result.select_one(".snippet, .summary, p")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        if not href or not title:
            continue

        full_url = urljoin(search_url, href)

        candidates.append({
            "state": state,
            "keyword": keyword,
            "candidate_url": full_url,
            "candidate_title": title,
            "snippet": snippet,
        })

    return candidates