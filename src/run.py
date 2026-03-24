import pandas as pd
from datetime import datetime
from discovery import discover_candidates
from extraction import extract_page_fields, looks_like_real_bill, get_match_details
from normalize import normalize_record
from storage import save_csv, save_sqlite
from pathlib import Path


DEBUG_STATES = ["MA"]
DEBUG_KEYWORDS = ["community land trust"]
SAVE_SQLITE = False

def run_pipeline():
    states_df = pd.read_csv("config/states.csv")
    keywords_df = pd.read_csv("config/keywords.csv")

    if DEBUG_STATES:
        states_df = states_df[states_df["state"].isin(DEBUG_STATES)]

    if DEBUG_KEYWORDS:
        keywords_df = keywords_df[keywords_df["keyword"].isin(DEBUG_KEYWORDS)]

    all_normalized = []
    crawl_log = []

    for _, state_row in states_df.iterrows():
        state = state_row["state"]
        search_url = state_row["search_url"]
        default_source_type = state_row["source_type"]

        for _, keyword_row in keywords_df.iterrows():
            keyword = keyword_row["keyword"]

            print(f"\nRunning discovery for {state} | {keyword}")

            try:
                candidates = discover_candidates(search_url, keyword, state)
                print(f"Candidates generated: {len(candidates)}")
            except Exception as e:
                print(f"Discovery failed for {state} | {keyword}: {e}")
                continue

            for i, candidate in enumerate(candidates, start=1):
                try:
                    extracted = extract_page_fields(
                        candidate["candidate_url"],
                        source_type=candidate.get("source_type", default_source_type)
                    )

                    raw_text = extracted.get("raw_text", "")
                    is_real_bill = looks_like_real_bill(raw_text)
                    match_details = get_match_details(raw_text, keyword)
                    keyword_hit = match_details["matched"]
                    match_reason = match_details["match_reason"]
                    match_terms = "; ".join(match_details["match_terms"])

                    crawl_log.append({
                        "state": candidate.get("state", state),
                        "keyword": keyword,
                        "candidate_title": candidate.get("candidate_title", ""),
                        "candidate_url": candidate.get("candidate_url", ""),
                        "extracted_title": extracted.get("title", ""),
                        "identifier": extracted.get("identifier", ""),
                        "status": extracted.get("status", ""),
                        "is_real_bill": is_real_bill,
                        "matches_keyword": keyword_hit,
                        "match_reason": match_reason,
                        "match_terms": match_terms,
                    })

                    if i % 10 == 0:
                        print(f"Checked {i} candidates for {state} | {keyword}")

                    if not is_real_bill:
                        continue

                    if not keyword_hit:
                        continue


                    candidate["match_reason"] = match_reason
                    candidate["match_terms"] = match_terms

                    normalized = normalize_record(candidate, extracted)
                    all_normalized.append(normalized)

                    print(f"MATCH: {normalized['state']} | {normalized['identifier']} -> {normalized['source_url']}")

                except Exception as e:
                    crawl_log.append({
                        "state": candidate.get("state", state),
                        "keyword": keyword,
                        "candidate_title": candidate.get("candidate_title", ""),
                        "candidate_url": candidate.get("candidate_url", ""),
                        "extracted_title": "",
                        "identifier": "",
                        "status": "",
                        "is_real_bill": False,
                        "matches_keyword": False,
                        "error": str(e),
                    })
                    print(f"Extraction failed for {candidate['candidate_url']}: {e}")

            subset = pd.DataFrame(crawl_log)
            subset = subset[(subset["state"] == state) & (subset["keyword"] == keyword)]
            if not subset.empty:
                print(f"{state} | {keyword} total checked: {len(subset)}")
                print(f"{state} | {keyword} real bills/statutes: {int(subset['is_real_bill'].fillna(False).sum())}")
                print(f"{state} | {keyword} keyword hits: {int(subset['matches_keyword'].fillna(False).sum())}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


    exports_dir = Path("data/exports")
    archive_crawl_dir = exports_dir / "archive" / "crawl_log"
    archive_findings_dir = exports_dir / "archive" / "findings_export"

    archive_crawl_dir.mkdir(parents=True, exist_ok=True)
    archive_findings_dir.mkdir(parents=True, exist_ok=True)

    crawl_log_df = pd.DataFrame(crawl_log)
    save_csv(crawl_log_df.to_dict(orient="records"), str(exports_dir / "crawl_log.csv"))
    save_csv(
        crawl_log_df.to_dict(orient="records"),
        str(archive_crawl_dir / f"crawl_log_{timestamp}.csv")
    )

    if all_normalized:
        findings_df = pd.DataFrame(all_normalized).drop_duplicates(
            subset=["state", "source_url", "identifier", "airtable_category"]
        )
        findings_records = findings_df.to_dict(orient="records")

        save_csv(findings_records, str(exports_dir / "findings_export.csv"))
        save_csv(
            findings_records,
            str(archive_findings_dir / f"findings_export_{timestamp}.csv")
        )

        if SAVE_SQLITE:
            save_sqlite(findings_records)

        print(f"\nSaved {len(findings_records)} matching records.")
        print("\nMatches by state:")
        print(findings_df["state"].value_counts())
    else:
        print("\nNo matching records found.")


if __name__ == "__main__":
    run_pipeline()