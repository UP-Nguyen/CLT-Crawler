import re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from discovery import fetch_page


def clean_text(text):
    return " ".join(text.split()) if text else ""


def extract_identifier_from_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    bill_id_vals = query.get("bill_id", [])

    if not bill_id_vals:
        return None

    bill_id = bill_id_vals[0]
    match = re.search(r"(AB|SB|ACA|SCA|AJR|SJR)(\d+)$", bill_id, re.IGNORECASE)
    if match:
        return f"{match.group(1).upper()} {match.group(2)}"

    return None


def extract_identifier_from_title(title):
    if not title:
        return None

    match = re.search(r"\b(AB|SB|ACA|SCA|AJR|SJR)[-\s]*(\d+)\b", title, re.IGNORECASE)
    if match:
        return f"{match.group(1).upper()} {match.group(2)}"

    return None


def extract_identifier_from_text(text):
    patterns = [
        r"\b(AB|SB|ACA|SCA|AJR|SJR)[-\s]*(\d+)\b",
        r"\b(HB|SB)[-\s]*(\d+)\b",
        r"\bChapter\s+(\d+)\b",
        r"\bc\.\s*(\d+)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) >= 2:
                return f"{match.group(1).upper()} {match.group(2)}"
            return match.group(0)

    return None


def extract_identifier(url, title, text):
    return (
        extract_identifier_from_url(url)
        or extract_identifier_from_title(title)
        or extract_identifier_from_text(text)
    )


def extract_status(text):
    text_lower = text.lower()

    if "introduced by" in text_lower:
        return "Introduced"
    if "amended in" in text_lower:
        return "Amended"
    if "chaptered" in text_lower:
        return "Enacted / Current law"
    if "approved by governor" in text_lower:
        return "Enacted / Current law"
    if "passed the assembly" in text_lower or "passed the senate" in text_lower:
        return "Passed"
    if "in committee" in text_lower:
        return "In committee"
    if "introduced" in text_lower:
        return "Introduced"

    return "Unknown"


def looks_like_real_ca_bill(text):
    """
    Reject junk pages; keep actual bill pages.
    """
    text_lower = text.lower()

    bill_signals = [
        "legislative counsel's digest",
        "introduced by",
        "an act to",
        "assembly bill",
        "senate bill",
        "bill text",
    ]

    return any(signal in text_lower for signal in bill_signals)


def matches_keyword(text, keyword):
    text_lower = text.lower()

    keyword_map = {
        "community land trust": [
            "community land trust",
            "community land trusts",
        ],
        "surplus land": [
            "surplus land",
            "surplus lands",
        ],
    }

    phrases = keyword_map.get(keyword.lower(), [keyword.lower()])
    return any(phrase in text_lower for phrase in phrases)


def extract_page_fields(url, source_type="legislature"):
    response = fetch_page(url)
    soup = BeautifulSoup(response.text, "lxml")

    text = clean_text(soup.get_text(" ", strip=True))

    title_el = soup.select_one("h1, title, .bill-title, .page-title")
    title = clean_text(title_el.get_text()) if title_el else ""

    identifier = extract_identifier(url, title, text)
    status = extract_status(text)
    summary_snippet = text[:300] if text else ""

    return {
        "source_url": url,
        "title": title,
        "identifier": identifier,
        "status": status,
        "summary_snippet": summary_snippet,
        "raw_text": text,
    }