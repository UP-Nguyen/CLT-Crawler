from datetime import date
import hashlib


def infer_confidence(raw_text, keywords_matched):
    text = raw_text.lower()

    if "community land trust" in text:
        return "High"
    if any(k.lower() in text for k in keywords_matched):
        return "Medium"
    return "Low"

def map_keyword_category(keyword):
    keyword = keyword.lower()
    if "community land trust" in keyword or "shared equity" in keyword:
        return "Definition of CLT"
    if "property tax" in keyword:
        return "Standards for Tax Assessments/Guidance"
    if "copa" in keyword or "tenant opportunity to purchase" in keyword:
        return "TOPA/COPA"
    if "accessory dwelling unit" in keyword or "adus" in keyword:
        return "ADUs"
    if "housing trust fund" in keyword:
        return "Special Allocation of Funding"
    if "surplus land" in keyword or "land bank" in keyword:
        return "Surplus Land/Land Banking"
    if "permanently affordable" in keyword or "ground lease" in keyword:
        return "Affordability Covenants"
    return "Uncategorized"

def normalize_record(discovery_row, extracted_row):
    keywords = [discovery_row["keyword"]]

    normalized = {
        "state": discovery_row["state"],
        "source_type": "legislature site",
        "source_url": extracted_row["source_url"],
        "title": extracted_row.get("title", ""),
        "identifier": extracted_row.get("identifier", ""),
        "status": extracted_row.get("status", "Unknown"),
        "last_seen_date": str(date.today()),
        "summary_snippet": extracted_row.get("summary_snippet", ""),
        "keywords_matched": "; ".join(keywords),
        "confidence": infer_confidence(extracted_row.get("raw_text", ""), keywords),
        "notes": "",
        "airtable_category": map_keyword_category(discovery_row["keyword"]),
        "content_hash": make_content_hash(extracted_row.get("raw_text", "")),
    }

    return normalized

def make_content_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

