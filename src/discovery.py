import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential


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
    time.sleep(1)
    return response


def discover_ca_bills_by_enumeration(
    keyword,
    start_num=1,
    end_num=300,
    bill_types=None,
):
    """
    Generate candidate California bill URLs without seeding them manually.
    """
    session_prefix = "202520260"
    bill_types = bill_types or ["AB", "SB"]

    candidates = []

    for bill_type in bill_types:
        for number in range(start_num, end_num + 1):
            bill_id = f"{session_prefix}{bill_type}{number}"
            url = f"https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id={bill_id}"

            candidates.append({
                "state": "CA",
                "keyword": keyword,
                "source_type": "legislature site",
                "candidate_url": url,
                "candidate_title": f"{bill_type} {number}",
                "snippet": "Generated CA bill candidate",
            })

    print(
        f"Generated {len(candidates)} CA bill candidates for keyword: {keyword} "
        f"({', '.join(bill_types)} {start_num}-{end_num})"
    )
    return candidates


def discover_candidates(search_url, keyword, state):
    if state != "CA":
        return []

    # Change these chunk boundaries as needed
    return discover_ca_bills_by_enumeration(
        keyword=keyword,
        start_num=2300,
        end_num=2450,
        bill_types=["AB", "SB"],
    )