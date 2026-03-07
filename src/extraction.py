import re
from bs4 import BeautifulSoup
from discovery import fetch_page

""" What is the page title?
Does the page mention a bill number/citation?
Can I infer the status?
Can I pull a short excerpt for review? """


def clean_text(text):
    return " ".join(text.split()) if text else ""


def extract_identifier(text):
    patterns = [
        r"\b(AB|SB|ACA|SCA|AJR|SJR)\s*\d+\b",
        r"\b(HB|SB)\s*\d+\b",
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


def extract_page_fields(url, source_type="legislature"):
    response = fetch_page(url)
    soup = BeautifulSoup(response.text, "xml")

    text = clean_text(soup.get_text(" ", strip=True))

    title_el = soup.select_one("h1, title, .bill-title, .page-title")
    title = clean_text(title_el.get_text()) if title_el else ""

    identifier = extract_identifier(text)
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