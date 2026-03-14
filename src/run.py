import pandas as pd
from discovery import discover_candidates
from extraction import extract_page_fields, looks_like_real_bill, matches_keyword
from normalize import normalize_record
from storage import save_csv, save_sqlite
from datetime import datetime


def run_pipeline():
    states_df = pd.read_csv("config/states.csv")
    keywords_df = pd.read_csv("config/keywords.csv")

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
                    keyword_hit = matches_keyword(raw_text, keyword)

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
                    })

                    if i % 25 == 0:
                        print(f"Checked {i} candidates for {state} | {keyword}")

                    if not is_real_bill:
                        continue

                    if not keyword_hit:
                        continue

                    normalized = normalize_record(candidate, extracted)
                    all_normalized.append(normalized)

                    print(f"MATCH: {normalized['identifier']} -> {normalized['source_url']}")

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

    findings_df = pd.DataFrame(all_normalized)

    if not findings_df.empty:
        print("\nMatches by state:")
        print(findings_df["state"].value_counts())

    if all_normalized:
        findings_df = pd.DataFrame(all_normalized).drop_duplicates(
            subset=["state", "source_url", "identifier", "airtable_category"]
        )
        print("\nMatches by state:")
        print(findings_df["state"].value_counts())

    # Always save crawl log
    crawl_log_df = pd.DataFrame(crawl_log)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save matched findings
    if all_normalized:
        findings_df = pd.DataFrame(all_normalized).drop_duplicates(
            subset=["state", "source_url", "identifier", "airtable_category"]
        )
        findings_records = findings_df.to_dict(orient="records")

        save_csv(findings_records, "data/exports/findings_export.csv")
        save_csv(findings_records, f"data/exports/findings_export_{timestamp}.csv")
        save_sqlite(findings_records)
        print(f"\nSaved {len(findings_records)} matching records.")
    else:
        print("\nNo matching records found.")


if __name__ == "__main__":
    run_pipeline()