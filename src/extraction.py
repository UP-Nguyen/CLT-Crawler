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
    if "introduced" in text_lower:
        return "Introduced"
    if "in committee" in text_lower:
        return "In committee"
    if "passed" in text_lower:
        return "Passed"
    if "enacted" in text_lower or "current law" in text_lower:
        return "Enacted / Current law"
    return "Unknown"


def extract_page_fields(url, source_type="legislature"):
    # crude PDF handling for now
    if url.lower().endswith(".pdf"):
        title = url.split("/")[-1]
        return {
            "source_url": url,
            "title": title,
            "identifier": extract_identifier(url, title, ""),
            "status": "Unknown",
            "summary_snippet": "PDF source - manual review needed",
            "raw_text": "",
        }

    response = fetch_page(url)
    soup = BeautifulSoup(response.text, "xml")

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