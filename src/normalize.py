from datetime import date
import hashlib


def infer_confidence(raw_text, keywords_matched):
    text = (raw_text or "").lower()

    if "community land trust" in text or "community land trusts" in text:
        return "High"
    if any(k.lower() in text for k in keywords_matched):
        return "Medium"
    return "Low"


def make_content_hash(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def map_record_category(discovery_row, extracted_row):
    """
    Smarter Airtable category mapping using source type + title + snippet + keyword.
    """
    keyword = (discovery_row.get("keyword") or "").lower()
    source_type = (discovery_row.get("source_type") or "").lower()
    title = (extracted_row.get("title") or "").lower()
    identifier = (extracted_row.get("identifier") or "").lower()
    snippet = (extracted_row.get("summary_snippet") or "").lower()
    source_url = (extracted_row.get("source_url") or "").lower()

    combined = " ".join([keyword, source_type, title, identifier, snippet, source_url])

    # 1. Tax / assessment / exemption / credit
    if any(term in combined for term in [
        "welfare exemption",
        "property tax",
        "tax credit",
        "taxation",
        "assessment",
        "assessor",
        "32 v.s.a.",
        "revenue and taxation",
    ]):
        return "Standards for Tax Assessments/Guidance"

    # 2. Surplus land / land banking
    if any(term in combined for term in [
        "surplus land",
        "surplus lands",
        "public land",
        "land bank",
        "land banking",
        "disposition of land",
    ]):
        return "Surplus Land/Land Banking"

    # 3. TOPA / COPA
    if any(term in combined for term in [
        "tenant opportunity to purchase",
        "topa",
        "copa",
        "purchase act",
    ]):
        return "TOPA/COPA"

    # 4. ADUs
    if any(term in combined for term in [
        "accessory dwelling unit",
        "adus",
        "adu",
    ]):
        return "ADUs"

    # 5. Funding
    if any(term in combined for term in [
        "housing trust fund",
        "allocation of funding",
        "appropriation",
        "grant program",
        "funding",
        "subsidy",
    ]):
        return "Special Allocation of Funding"

    # 6. Affordability / covenants / resale restrictions
    if any(term in combined for term in [
        "affordability",
        "affordable housing",
        "permanently affordable",
        "permanent affordability",
        "resale restriction",
        "resale restrictions",
        "covenant",
        "covenants",
        "restrictions preserving affordability",
        "ground lease",
        "shared appreciation",
        "shared equity",
        "shared-equity",
        "24 v.s.a. § 4303",
        "24 v.s.a.",
    ]):
        return "Affordability Covenants"

    # 7. Direct CLT / enabling / definition
    if any(term in combined for term in [
        "community land trust",
        "community land trusts",
        "clt",
        "10 v.s.a. § 321",
        "demonstration program",
        "definition of community land trust",
    ]):
        return "Definition of CLT"

    return "Uncategorized"


def normalize_record(discovery_row, extracted_row):
    keywords = [discovery_row["keyword"]]
    api_payload = discovery_row.get("api_payload") or {}
    match_reason = discovery_row.get("match_reason", "")
    match_terms = discovery_row.get("match_terms", "")

    normalized = {
        "state": discovery_row["state"],
        "source_type": discovery_row.get("source_type", "unknown"),
        "source_url": extracted_row["source_url"],
        "title": extracted_row.get("title", ""),
        "identifier": extracted_row.get("identifier", ""),
        "status": extracted_row.get("status", "Unknown"),
        "last_seen_date": str(date.today()),
        "summary_snippet": extracted_row.get("summary_snippet", ""),
        "keywords_matched": "; ".join(keywords),
        "confidence": infer_confidence(extracted_row.get("raw_text", ""), keywords),
        "notes": "",
        "airtable_category": map_record_category(discovery_row, extracted_row),
        "content_hash": make_content_hash(extracted_row.get("raw_text", "")),
        "session": api_payload.get("session", ""),
        "match_reason": match_reason,
        "match_terms": match_terms,
    }

    return normalized