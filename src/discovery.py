import os
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
        timeout=30,
        allow_redirects=True,
    )

    print(f"FETCHING: {response.url}")
    print(f"STATUS: {response.status_code}")

    response.raise_for_status()
    time.sleep(1)
    return response


def fetch_json(url, params=None):
    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=30,
        allow_redirects=True,
    )

    print(f"FETCHING JSON: {response.url}")
    print(f"STATUS: {response.status_code}")

    if response.status_code == 401:
        raise ValueError("NY Open Legislation API rejected the key. Check or replace NY_OPENLEG_KEY.")

    response.raise_for_status()
    time.sleep(1)
    return response.json()


def discover_ca_bills_by_enumeration(
    keyword,
    start_num=1,
    end_num=300,
    bill_types=None,
):
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
                "api_payload": None,
            })

    print(
        f"Generated {len(candidates)} CA bill candidates for keyword: {keyword} "
        f"({', '.join(bill_types)} {start_num}-{end_num})"
    )
    return candidates


def discover_ny_bills_via_api(keyword, session_years=None, limit=25):
    api_key = os.getenv("NY_OPENLEG_KEY")
    if not api_key:
        raise ValueError("Missing NY_OPENLEG_KEY environment variable.")

    session_years = session_years or ["2025", "2023"]
    candidates = []

    for session_year in session_years:
        url = f"https://legislation.nysenate.gov/api/3/bills/{session_year}/search"
        params = {
            "key": api_key,
            "term": keyword,
            "limit": limit,
        }

        data = fetch_json(url, params=params)
        items = data.get("result", {}).get("items", [])

        for item in items:
            result = item.get("result", {})
            base_print_no = result.get("basePrintNo", "")
            title = result.get("title", "")
            summary = result.get("summary", "")
            status_desc = result.get("status", {}).get("statusDesc", "")

            if not base_print_no:
                continue

            bill_url = f"https://legislation.nysenate.gov/api/3/bills/{session_year}/{base_print_no}"

            candidates.append({
                "state": "NY",
                "keyword": keyword,
                "source_type": "legislature api",
                "candidate_url": bill_url,
                "candidate_title": f"{base_print_no} {title}".strip(),
                "snippet": summary,
                "api_payload": {
                    "session": session_year,
                    "basePrintNo": base_print_no,
                    "title": title,
                    "summary": summary,
                    "statusDesc": status_desc,
                    "raw_search_result": result,
                },
            })

    print(f"Generated {len(candidates)} NY API candidates for keyword: {keyword}")
    return candidates


def discover_candidates(search_url, keyword, state):
    if state == "CA":
        return discover_ca_bills_by_enumeration(
            keyword=keyword,
            start_num=2300,
            end_num=2450,
            bill_types=["AB", "SB"],
        )

    if state == "NY":
        return discover_ny_bills_via_api(
            keyword=keyword,
            session_years=["2025","2024", "2023"],
            limit=50,
        )

    return []