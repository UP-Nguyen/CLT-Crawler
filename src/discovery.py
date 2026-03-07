import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from bs4 import BeautifulSoup
from urllib.parse import urljoin



HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_page(url, params=None):
    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=20,
        allow_redirects=True,
    )

    print(f"FETCHING: {response.url}")
    print(f"STATUS: {response.status_code}")

    response.raise_for_status()
    time.sleep(2)
    return response

# manual seed list approach.
# discovery is still simple, but now it can return actual candidate pages
# fetch_page is reusable
# discover is clearly separated from extraction
# can add actual seed URLs state by state

""" def discover_candidates(search_url, keyword, state):
    manual_candidates = {
        "CA": [
            {
                "title": "California Legislative Information Home",
                "url": "https://leginfo.legislature.ca.gov/faces/home.xhtml",
                "snippet": "General California legislative information page"
            }
        ]
    }

    state_candidates = manual_candidates.get(state, [])

    return [
        {
            "state": state,
            "keyword": keyword,
            "candidate_url": item["url"],
            "candidate_title": item["title"],
            "snippet": item["snippet"],
        }
        for item in state_candidates
    ] """

from bs4 import BeautifulSoup
from urllib.parse import urljoin

""" def discover_candidates(search_url, keyword, state):
    response = fetch_page(search_url)
    soup = BeautifulSoup(response.text, "xml")

    candidates = []
    seen_urls = set()

    for link in soup.find_all("a", href=True):
        title = " ".join(link.get_text(" ", strip=True).split())
        href = link["href"]
        full_url = urljoin(search_url, href)

        # only keep actual CA bill detail pages
        if "billTextClient.xhtml?bill_id=" not in full_url:
            continue

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        candidates.append({
            "state": state,
            "keyword": keyword,
            "candidate_url": full_url,
            "candidate_title": title if title else full_url,
            "snippet": "",
        })

    print("Filtered candidates:")
    for c in candidates[:10]:
        print(c["candidate_title"], "->", c["candidate_url"])

    return candidates """

def discover_candidates(search_url, keyword, state):
    manual_candidates = [
        {
            "state": "CA",
            "keyword": keyword,
            "candidate_url": "https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260AB2399",
            "candidate_title": "AB 2399 Real property tax: welfare exemption: community land trusts.",
            "snippet": "Seeded real bill page"
        }
    ]

    print("Filtered candidates:")
    for c in manual_candidates:
        print(c["candidate_title"], "->", c["candidate_url"])

    return manual_candidates