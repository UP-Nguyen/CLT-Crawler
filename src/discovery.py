import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from tenacity import retry, stop_after_attempt, wait_exponential


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
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
    time.sleep(0.5)
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
    time.sleep(0.5)
    return response.json()


def discover_ca_bills_by_enumeration(
    keyword,
    start_num=2395,
    end_num=2405,
    bill_types=None,
):
    session_prefix = "202520260"
    bill_types = bill_types or ["AB"]

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


def discover_ny_bills_via_api(keyword, session_years=None, limit=10):
    api_key = os.getenv("NY_OPENLEG_KEY")
    if not api_key:
        raise ValueError("Missing NY_OPENLEG_KEY environment variable.")

    session_years = session_years or ["2025", "2024", "2023"]
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


def discover_vt_bills_by_enumeration(keyword, sessions=None, start_num=1, end_num=25, bill_types=None):
    sessions = sessions or ["2026"]
    bill_types = bill_types or ["H"]

    candidates = []

    for session in sessions:
        for bill_type in bill_types:
            for number in range(start_num, end_num + 1):
                url = f"https://legislature.vermont.gov/bill/status/{session}/{bill_type}.{number}"
                candidates.append({
                    "state": "VT",
                    "keyword": keyword,
                    "source_type": "legislature site",
                    "candidate_url": url,
                    "candidate_title": f"{bill_type}.{number}",
                    "snippet": f"Generated VT {session} bill candidate",
                    "api_payload": {"session": session},
                })

    print(
        f"Generated {len(candidates)} VT bill candidates for keyword: {keyword} "
        f"({', '.join(sessions)} | {', '.join(bill_types)} {start_num}-{end_num})"
    )
    return candidates


def discover_ma_bills_by_enumeration(keyword, general_court="194", start_num=1, end_num=100, bill_types=None):
    bill_types = bill_types or ["H", "S"]
    candidates = []

    for bill_type in bill_types:
        for number in range(start_num, end_num + 1):
            url = f"https://malegislature.gov/Bills/{general_court}/{bill_type}{number}"
            candidates.append({
                "state": "MA",
                "keyword": keyword,
                "source_type": "legislature site",
                "candidate_url": url,
                "candidate_title": f"{bill_type}{number}",
                "snippet": f"Generated MA bill candidate for General Court {general_court}",
                "api_payload": {"session": general_court},
            })

    print(
        f"Generated {len(candidates)} MA bill candidates for keyword: {keyword} "
        f"({general_court} | {', '.join(bill_types)} {start_num}-{end_num})"
    )
    return candidates


def discover_al_statute_seeds(keyword):
    return [
        {
            "state": "AL",
            "keyword": keyword,
            "source_type": "code site",
            "candidate_url": "https://alison.legislature.state.al.us/code-of-alabama?section=24-10-1",
            "candidate_title": "Ala. Code § 24-10-1",
            "snippet": "Alabama Affordable Housing Act - short title",
            "api_payload": None,
        },
        {
            "state": "AL",
            "keyword": keyword,
            "source_type": "code site",
            "candidate_url": "https://alison.legislature.state.al.us/code-of-alabama?section=24-10-4",
            "candidate_title": "Ala. Code § 24-10-4",
            "snippet": "Alabama Affordable Housing Trust Fund",
            "api_payload": None,
        },
        {
            "state": "AL",
            "keyword": keyword,
            "source_type": "code site",
            "candidate_url": "https://alison.legislature.state.al.us/code-of-alabama?section=24-10-6",
            "candidate_title": "Ala. Code § 24-10-6",
            "snippet": "Affordable housing purposes",
            "api_payload": None,
        },
        {
            "state": "AL",
            "keyword": keyword,
            "source_type": "code site",
            "candidate_url": "https://alison.legislature.state.al.us/code-of-alabama?section=24-10-7",
            "candidate_title": "Ala. Code § 24-10-7",
            "snippet": "Affordable housing goals and priorities",
            "api_payload": None,
        },
        {
            "state": "AL",
            "keyword": keyword,
            "source_type": "code site",
            "candidate_url": "https://alison.legislature.state.al.us/code-of-alabama?section=24-1-40.1",
            "candidate_title": "Ala. Code § 24-1-40.1",
            "snippet": "Tax exemption for municipal housing authorities",
            "api_payload": None,
        },
    ]


def discover_ar_bills_from_listing(keyword, listing_urls=None):
    listing_urls = listing_urls or [
        "https://arkleg.state.ar.us/Bills/ViewBills?by=desc&ddBienniumSession=2025/2025R&sort=MeasureNo&type=HB",
        "https://arkleg.state.ar.us/Bills/ViewBills?by=desc&ddBienniumSession=2025/2025R&sort=MeasureNo&type=SB",
    ]

    candidates = []
    seen = set()

    for listing_url in listing_urls:
        response = fetch_page(listing_url)
        soup = BeautifulSoup(response.text, "lxml")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(listing_url, href)
            link_text = " ".join(link.get_text(" ", strip=True).split())

            if "/Bills/Detail" not in full_url:
                continue

            full_url = full_url.split("#")[0]

            if full_url.lower().endswith(".pdf") or "ftpdocument" in full_url.lower():
                continue

            if full_url in seen:
                continue
            seen.add(full_url)

            parent = link.find_parent("tr")
            row_text = " ".join(parent.get_text(" ", strip=True).split()) if parent else ""

            candidates.append({
                "state": "AR",
                "keyword": keyword,
                "source_type": "legislature site",
                "candidate_url": full_url,
                "candidate_title": link_text,
                "snippet": row_text[:300],
                "api_payload": None,
            })

    print(f"Generated {len(candidates)} AR bill candidates for keyword: {keyword}")
    return candidates

def discover_ar_manual_statute_candidates(keyword):
    return [
        {
            "state": "AR",
            "keyword": keyword,
            "source_type": "code site",
            "candidate_url": "https://arkleg.state.ar.us/Home/FTPDocument?path=%2FACTS%2F2009%2FPublic%2FACT661.pdf",
            "candidate_title": "Arkansas Housing Trust Fund Act of 2009",
            "snippet": "Creates the Arkansas Housing Trust Fund and adds Ark. Code Ann. §§ 15-5-1701 through 15-5-1706.",
            "api_payload": None,
        },
        {
            "state": "AR",
            "keyword": keyword,
            "source_type": "code site",
            "candidate_url": "https://arkleg.state.ar.us/Home/FTPDocument?path=%2FACTS%2F2023R%2FPublic%2FACT365.pdf",
            "candidate_title": "Act 365 of 2023",
            "snippet": "Amends Arkansas Housing Trust Fund provisions, including Ark. Code Ann. § 15-5-1705(c).",
            "api_payload": None,
        },
        {
            "state": "AR",
            "keyword": keyword,
            "source_type": "code site",
            "candidate_url": "https://arkleg.state.ar.us/Home/FTPDocument?path=%2FAssembly%2FMeeting+Attachments%2F040%2F4596%2FE.2.a+DOC+ADFA+2021+ADFA+Qualified+Allocation+Plan+Rules.pdf",
            "candidate_title": "ADFA Qualified Allocation Plan Rules",
            "snippet": "References the Affordable Neighborhood Housing Tax Credit Act of 1997 and Ark. Code Ann. § 15-5-1301 et seq.",
            "api_payload": None,
        },
    ]

def discover_wa_rcw_from_chapter_pages(keyword, chapter_pages=None):
    chapter_pages = chapter_pages or [
        "https://app.leg.wa.gov/rcw/default.aspx?cite=43.185A",
    ]

    candidates = []
    seen = set()

    for chapter_url in chapter_pages:
        response = fetch_page(chapter_url)
        soup = BeautifulSoup(response.text, "lxml")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(chapter_url, href)
            title = " ".join(link.get_text(" ", strip=True).split()).lower()

            if "default.aspx?cite=" not in full_url:
                continue

            if "pdf=true" in full_url.lower():
                continue

            if title == "pdf":
                continue

            parsed = urlparse(full_url)
            cite = parse_qs(parsed.query).get("cite", [""])[0]

            if not re.fullmatch(r"\d+\.\d+[A-Z]?\.\d+", cite):
                continue

            section_part = cite.split(".")[-1]
            if re.fullmatch(r"9\d\d", section_part):
                continue

            if full_url in seen:
                continue
            seen.add(full_url)

            candidates.append({
                "state": "WA",
                "keyword": keyword,
                "source_type": "code site",
                "candidate_url": full_url,
                "candidate_title": f"RCW {cite}",
                "snippet": "Discovered from WA RCW chapter page",
                "api_payload": {"chapter": ".".join(cite.split(".")[:-1])},
            })

    print(f"Generated {len(candidates)} WA RCW candidates for keyword: {keyword}")
    return candidates


def discover_candidates(search_url, keyword, state):
    if state == "AL":
        return discover_al_statute_seeds(keyword)

    if state == "AR":
        return discover_ar_manual_statute_candidates(keyword)

    if state == "CA":
        return discover_ca_bills_by_enumeration(
            keyword=keyword,
            start_num=2395,
            end_num=2405,
            bill_types=["AB"],
        )

    if state == "MA":
        return discover_ma_bills_by_enumeration(
            keyword=keyword,
            general_court="194",
            start_num=1,
            end_num=50,
            bill_types=["H", "S"],
        )

    if state == "NY":
        return discover_ny_bills_via_api(
            keyword=keyword,
            session_years=["2025", "2024", "2023"],
            limit=10,
        )

    if state == "VT":
        return discover_vt_bills_by_enumeration(
            keyword=keyword,
            sessions=["2026", "2024"],
            start_num=1,
            end_num=100,
            bill_types=["H", "S"],
        )

    if state == "WA":
        return discover_wa_rcw_from_chapter_pages(
            keyword,
            chapter_pages=[
                "https://app.leg.wa.gov/rcw/default.aspx?cite=43.185A",
            ],
        )

    return []