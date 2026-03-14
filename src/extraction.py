import re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from discovery import fetch_page, fetch_json


def clean_text(text):
    return " ".join(text.split()) if text else ""


def extract_identifier_from_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    bill_id_vals = query.get("bill_id", [])

    if bill_id_vals:
        bill_id = bill_id_vals[0]
        match = re.search(r"(AB|SB|ACA|SCA|AJR|SJR)(\d+)$", bill_id, re.IGNORECASE)
        if match:
            return f"{match.group(1).upper()} {match.group(2)}"

    ny_match = re.search(r"/api/3/bills/\d{4}/([SA]\d+)", url, re.IGNORECASE)
    if ny_match:
        return ny_match.group(1).upper()

    vt_bill_match = re.search(r"/bill/status/\d{4}/([HS]\.\d+)", url, re.IGNORECASE)
    if vt_bill_match:
        return vt_bill_match.group(1).upper()

    # Vermont statute URLs like /statutes/section/24/117/04303
    vt_statute_match = re.search(r"/statutes/section/(\d+)/(\d+)/(\d+)", url, re.IGNORECASE)
    if vt_statute_match:
        title_num = vt_statute_match.group(1)
        section_num = str(int(vt_statute_match.group(3)))  # 04303 -> 4303
        return f"{title_num} V.S.A. § {section_num}"

    return None


def extract_identifier_from_title(title):
    if not title:
        return None

    ca_match = re.search(r"\b(AB|SB|ACA|SCA|AJR|SJR)[-\s]*(\d+)\b", title, re.IGNORECASE)
    if ca_match:
        return f"{ca_match.group(1).upper()} {ca_match.group(2)}"

    ny_match = re.search(r"\b([SA])(\d+)\b", title, re.IGNORECASE)
    if ny_match:
        return f"{ny_match.group(1).upper()}{ny_match.group(2)}"

    vt_match = re.search(r"\b([HS])\.(\d+)\b", title, re.IGNORECASE)
    if vt_match:
        return f"{vt_match.group(1).upper()}.{vt_match.group(2)}"

    return None


def extract_identifier_from_text(text):
    patterns = [
        ("ca_bill", r"\b(AB|SB|ACA|SCA|AJR|SJR)[-\s]*(\d+)\b"),
        ("ny_bill", r"\b([SA])(\d+)\b"),
        ("vt_bill", r"\b([HS])\.(\d+)\b"),
        ("generic_bill", r"\b(HB|SB)[-\s]*(\d+)\b"),
        ("chapter", r"\bChapter\s+(\d+)\b"),
        ("citation", r"\bc\.\s*(\d+)\b"),
    ]

    for pattern_type, pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue

        if pattern_type == "vt_bill":
            return f"{match.group(1).upper()}.{match.group(2)}"

        if pattern_type in {"ca_bill", "ny_bill", "generic_bill"}:
            g1 = match.group(1).upper()
            g2 = match.group(2)
            if pattern_type == "ny_bill":
                return f"{g1}{g2}"
            return f"{g1} {g2}"

        if pattern_type == "chapter":
            return f"Chapter {match.group(1)}"

        if pattern_type == "citation":
            return f"c. {match.group(1)}"

    return None


def extract_identifier(url, title, text):
    return (
        extract_identifier_from_url(url)
        or extract_identifier_from_title(title)
        or extract_identifier_from_text(text)
    )


def extract_status(text):
    text_lower = text.lower()

    if "approved by governor" in text_lower or "chaptered" in text_lower:
        return "Enacted / Current law"
    if "amended" in text_lower:
        return "Amended"
    if "passed the assembly" in text_lower or "passed the senate" in text_lower:
        return "Passed"
    if "in committee" in text_lower or "referred to committee" in text_lower:
        return "In committee"
    if "introduced by" in text_lower or "introduced" in text_lower:
        return "Introduced"

    return "Unknown"


def looks_like_real_bill(text):
    text_lower = text.lower()

    bill_signals = [
        "legislative counsel",
        "introduced by",
        "an act to amend",
        "an act to add",
        "bill text",
        "digest",
        "vote:",
        "appropriation:",
        "fiscal committee:",
        "state-mandated local program:",
        "senate bill",
        "assembly bill",
        "legislative session",
        "sponsor memo",
        "summary of provisions",
        "as introduced",
        "house bill",
        "senate bill",
        "act relating to",
        "bill as introduced",
    ]

    statute_signals = [
        "v.s.a.",
        "statutes",
        "section",
        "community land trust",
        "tax credit",
        "affordability",
    ]

    return any(signal in text_lower for signal in bill_signals) or any(signal in text_lower for signal in statute_signals)


def matches_keyword(text, keyword):
    text_lower = text.lower()

    keyword_map = {
        "community land trust": [
            "community land trust",
            "community land trusts",
            "shared appreciation",
            "shared-equity",
            "shared equity",
            "permanently affordable",
            "permanent affordability",
            "resale restriction",
            "affordability",
            "affordable housing development",
            "covenants or restrictions",
        ],
        "surplus land": [
            "surplus land",
            "surplus lands",
            "public land",
            "land bank",
        ],
        "shared equity": [
            "shared equity",
            "shared-equity",
            "shared appreciation",
            "resale restriction",
            "permanent affordability",
        ],
    }

    phrases = keyword_map.get(keyword.lower(), [keyword.lower()])
    return any(phrase in text_lower for phrase in phrases)


def extract_ny_api_bill(url):
    from os import getenv

    api_key = getenv("NY_OPENLEG_KEY")
    data = fetch_json(url, params={"key": api_key})

    result = data.get("result", {})
    title = result.get("title", "") or ""
    summary = result.get("summary", "") or ""
    base_print_no = result.get("basePrintNo", "") or ""
    status_desc = result.get("status", {}).get("statusDesc", "") or ""

    amendments = result.get("amendments", {}).get("items", {})
    amendment_texts = []

    if isinstance(amendments, dict):
        for _, amendment in amendments.items():
            full_text = amendment.get("fullText") or ""
            memo = amendment.get("memo") or ""
            act_clause = amendment.get("actClause") or ""
            law_section = amendment.get("lawSection") or ""
            amendment_texts.extend([law_section, act_clause, memo, full_text])

    raw_text = clean_text(" ".join([title, summary, status_desc] + amendment_texts))
    identifier = base_print_no or extract_identifier(url, title, raw_text)

    return {
        "source_url": url,
        "title": title,
        "identifier": identifier,
        "status": status_desc if status_desc else extract_status(raw_text),
        "summary_snippet": summary[:300] if summary else raw_text[:300],
        "raw_text": raw_text,
    }


def extract_page_fields(url, source_type="legislature"):
    if source_type == "legislature api" and "legislation.nysenate.gov/api/3/bills/" in url:
        return extract_ny_api_bill(url)

    response = fetch_page(url)
    soup = BeautifulSoup(response.text, "lxml")

    text = clean_text(soup.get_text(" ", strip=True))

    # Default title extraction
    title_el = soup.select_one("h1, h2, title, .bill-title, .page-title")
    title = clean_text(title_el.get_text()) if title_el else ""

    identifier = extract_identifier(url, title, text)
    status = extract_status(text)
    summary_snippet = text[:300] if text else ""

    # Vermont statute cleanup:
    # if this is a statute page and the title is generic, use the identifier
    # plus any visible section heading if available.
    if "/statutes/section/" in url:
        heading_candidates = soup.select("h1, h2, h3, .section-title")
        heading_text = ""
        for el in heading_candidates:
            candidate = clean_text(el.get_text())
            if candidate and candidate.lower() not in {"vermont laws", "statutes"}:
                heading_text = candidate
                break

        if identifier and heading_text:
            title = f"{identifier} - {heading_text}"
        elif identifier:
            title = identifier

        status = "Current law"

    return {
        "source_url": url,
        "title": title,
        "identifier": identifier,
        "status": status,
        "summary_snippet": summary_snippet,
        "raw_text": text,
    }