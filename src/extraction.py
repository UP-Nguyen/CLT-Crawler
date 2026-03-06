import re
from bs4 import BeautifulSoup
from discovery import fetch_page

def clean_text(text):
    return " ".join(text.split()) if text else ""


""" What is the page title?
Does the page mention a bill number/citation?
Can I infer the status?
Can I pull a short excerpt for review? """

def extract_identifier(text):
    """
    Try to detect bill numbers or statute-like identifiers.
    """
    patterns = [
        r"\b(HB|SB|AB|S\.B\.|H\.B\.)\s*\d+\b",
        r"\b[A-Z]\.\s*\d+\b",
        r"\bChapter\s+\d+\b",
        r"\bc\.\s*\d+\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

def extract_status(text):
    text_lower = text.lower()
    if "introduced" in text_lower:
        return "Introduced"
    if "in committee" in text_lower:
        return "In committee"
    if "passed" in text_lower:
        return "Passed"
    if "enacted" in text_lower or "current law" in text_lower:
        return "Enacted / Current law"
    return "Unknown"

def extract_page_fields(url):
    response = fetch_page(url)
    soup = BeautifulSoup(response.text, "lxml")

    title = ""
    if soup.title:
        title = clean_text(soup.title.get_text())

    # Try common page areas
    main_text = clean_text(soup.get_text(" ", strip=True))
    identifier = extract_identifier(main_text)
    status = extract_status(main_text)

    # crude summary: first 300 chars
    summary_snippet = main_text[:300]

    return {
        "source_url": url,
        "title": title,
        "identifier": identifier,
        "status": status,
        "summary_snippet": summary_snippet,
        "raw_text": main_text,
    }

def extract_bill_detail_page(soup):
    title_el = soup.select_one("h1, .bill-title, .page-title")
    title = clean_text(title_el.get_text()) if title_el else ""

    status_el = soup.select_one(".status, .bill-status")
    status = clean_text(status_el.get_text()) if status_el else "Unknown"

    summary_el = soup.select_one(".summary, .bill-summary, .description")
    summary = clean_text(summary_el.get_text()) if summary_el else ""

    return {
        "title": title,
        "status": status,
        "summary_snippet": summary[:300]
    }

def extract_page_fields(url, source_type="legislature"):
    response = fetch_page(url)
    soup = BeautifulSoup(response.text, "lxml")

    if source_type == "legislature":
        fields = extract_bill_detail_page(soup)
    else:
        fields = {
            "title": clean_text(soup.title.get_text()) if soup.title else "",
            "status": "Unknown",
            "summary_snippet": clean_text(soup.get_text(" ", strip=True))[:300],
        }

    text = clean_text(soup.get_text(" ", strip=True))

    fields["source_url"] = url
    fields["identifier"] = extract_identifier(text)
    fields["raw_text"] = text

    if not fields.get("status"):
        fields["status"] = extract_status(text)

    return fields