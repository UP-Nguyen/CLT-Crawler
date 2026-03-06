import pandas as pd
from discovery import discover_candidates
from extraction import extract_page_fields
from normalize import normalize_record
from storage import save_csv, save_sqlite, deduplicate_records

def run_pipeline():
    states_df = pd.read_csv("config/states.csv")
    keywords_df = pd.read_csv("config/keywords.csv")

    all_normalized = []

    for _, state_row in states_df.iterrows():
        state = state_row["state"]
        search_url = state_row["search_url"]
        source_type = state_row["source_type"]

        for _, keyword_row in keywords_df.iterrows():
            keyword = keyword_row["keyword"]

            print(f"Running discovery for {state} | {keyword}")
            try:
                candidates = discover_candidates(search_url, keyword, state)
            except Exception as e:
                print(f"Discovery failed for {state} | {keyword}: {e}")
                continue

            for candidate in candidates[:10]:  # limit during testing
                try:
                    extracted = extract_page_fields(candidate["candidate_url"], source_type=source_type)
                    normalized = normalize_record(candidate, extracted)
                    all_normalized.append(normalized)
                except Exception as e:
                    print(f"Extraction failed for {candidate['candidate_url']}: {e}")

    if all_normalized:
        all_normalized = deduplicate_records(all_normalized)
        save_csv(all_normalized, "data/exports/findings_export.csv")
        save_sqlite(all_normalized)
        print(f"Saved {len(all_normalized)} records.")
    else:
        print("No records found.")

if __name__ == "__main__":
    run_pipeline()