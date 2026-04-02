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
        
    al_match = re.search(r"[?&]section=(\d+-\d+-\d+(?:\.\d+)?)", url, re.IGNORECASE)
    if al_match:
        return f"Ala. Code § {al_match.group(1)}"  

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
    
    ma_bill_match = re.search(r"/Bills/(\d+)/([HS]\d+)$", url, re.IGNORECASE)
    if ma_bill_match:
        return ma_bill_match.group(2).upper()

    ma_statute_match = re.search(
        r"/Laws/GeneralLaws/Part([IVX]+)/Title([IVX]+)/Chapter(\d+[A-Z]?)/Section(\d+[A-Z]?)",
        url,
        re.IGNORECASE,
    )
    if ma_statute_match:
        chapter_num = ma_statute_match.group(3)
        section_num = ma_statute_match.group(4)
        return f"MGL c.{chapter_num} §{section_num}"    

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
        "act relating to",
        "bill as introduced",
        "bill information",
        "view text",
        "print preview",
        "download pdf",
        "general court",
        "petition (accompanied by bill",
    ]

    statute_signals = [
        "v.s.a.",
        "statutes",
        "section",
        "general laws",
        "mgl c.",
        "code of alabama",
        "ala. code",
        "affordable housing act",
        "affordable housing trust fund",
        "housing authority",
        "tax exemption",
    ]

    return any(signal in text_lower for signal in bill_signals) or any(signal in text_lower for signal in statute_signals)


def get_match_details(text, keyword, state=None):
    text_lower = (text or "").lower()
    state = (state or "").upper()

    exact_phrase_map = {
        "community land trust": [
            "community land trust",
            "community land trusts",
        ],
        "shared equity": [
            "shared equity",
            "shared-equity",
        ],
        "surplus land": [
            "surplus land",
            "surplus lands",
        ],
    }

    concept_map = {
        "community land trust": [
            "community land trust",
            "community land trusts",
            "shared appreciation",
            "shared equity",
            "shared-equity",
            "permanently affordable",
            "permanent affordability",
            "resale restriction",
            "resale restrictions",
            "ground lease",
            "affordable housing development",
            "affordable housing",
            "covenants or restrictions",
            "workforce housing",
            "housing tax increment financing",
            "housing authority",
            "tax exemption",
        ],
        "shared equity": [
            "shared equity",
            "shared-equity",
            "shared appreciation",
            "resale restriction",
            "resale restrictions",
            "ground lease",
            "permanent affordability",
        ],
        "surplus land": [
            "surplus land",
            "surplus lands",
            "public land",
            "land bank",
            "land banking",
            "disposition of land",
        ],
    }

    exact_phrases = exact_phrase_map.get(keyword.lower(), [keyword.lower()])
    concepts = concept_map.get(keyword.lower(), [keyword.lower()])

    exact_hits = [p for p in exact_phrases if p in text_lower]

    seen = set()
    concept_hits = []
    for c in concepts:
        if c in text_lower and c not in seen:
            concept_hits.append(c)
            seen.add(c)

    if exact_hits:
        return {
            "matched": True,
            "match_reason": f"exact_phrase:{exact_hits[0]}",
            "match_terms": concept_hits,
        }

    if state == "AL":
        al_terms = [
            "affordable housing",
            "affordable housing act",
            "affordable housing trust fund",
            "housing trust fund",
            "housing authority",
            "tax exemption",
        ]
        al_hits = [term for term in al_terms if term in text_lower]

        if len(al_hits) >= 1:
            return {
                "matched": True,
                "match_reason": f"state_fallback_al:{al_hits[0]}",
                "match_terms": al_hits,
            }

    if state == "MA":
        ma_terms = [
            "affordable housing",
            "affordable housing development",
            "permanent affordability",
            "permanently affordable",
            "resale restriction",
            "resale restrictions",
            "ground lease",
            "shared equity",
            "shared-equity",
            "workforce housing",
            "housing tax increment financing",
        ]
        ma_hits = [term for term in ma_terms if term in text_lower]

        if len(ma_hits) >= 1:
            return {
                "matched": False,
                "match_reason": "",
                "match_terms": ma_hits,
            }

    if len(concept_hits) >= 2:
        return {
            "matched": True,
            "match_reason": f"concept_combo:{', '.join(concept_hits[:2])}",
            "match_terms": concept_hits,
        }

    return {
        "matched": False,
        "match_reason": "",
        "match_terms": concept_hits,
    }


def matches_keyword(text, keyword, state=None):
    return get_match_details(text, keyword, state=state)["matched"]


def is_ma_review_candidate(text):
    text_lower = (text or "").lower()

    ma_review_terms = [
        "affordable housing",
        "workforce housing",
        "permanent affordability",
        "permanently affordable",
        "resale restriction",
        "resale restrictions",
        "shared equity",
        "shared-equity",
        "ground lease",
        "covenants or restrictions",
    ]

    hits = [term for term in ma_review_terms if term in text_lower]
    return len(hits) >= 1, hits

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

    # Remove obvious page chrome
    for tag in soup.select("nav, header, footer, script, style, noscript, form"):
        tag.decompose()

    # Try to target the main content first
    main_selectors = [
        "main",
        "#main-content",
        ".main-content",
        ".bill-content",
        ".content",
        ".container",
    ]

    main_text = ""
    for selector in main_selectors:
        el = soup.select_one(selector)
        if el:
            candidate_text = clean_text(el.get_text(" ", strip=True))
            if len(candidate_text) > len(main_text):
                main_text = candidate_text

    # fallback to full page if needed
    full_text = clean_text(soup.get_text(" ", strip=True))
    text = main_text if len(main_text) > 200 else full_text

    # Clean out common MA page chrome phrases
    junk_phrases = [
        "skip to content",
        "mylegislature",
        "sign in with mylegislature account",
        "the 194th general court of the commonwealth of massachusetts",
        "email* password*",
        "march 23, 2026",
    ]
    text_lower = text.lower()
    for phrase in junk_phrases:
        text_lower = text_lower.replace(phrase, " ")
    text = clean_text(text_lower)

    title_el = soup.select_one("h1, h2, .bill-title, .page-title, title")
    title = clean_text(title_el.get_text()) if title_el else ""

    identifier = extract_identifier(url, title, text)
    status = extract_status(text)
    summary_snippet = text[:300] if text else ""

    # Vermont statute cleanup
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