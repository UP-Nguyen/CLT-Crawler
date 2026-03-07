import pandas as pd
from discovery import discover_candidates
from extraction import extract_page_fields, looks_like_real_ca_bill, matches_keyword
from normalize import normalize_record
from storage import save_csv, save_sqlite


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

            print(f"\nRunning discovery for {state} | {keyword}")

            try:
                candidates = discover_candidates(search_url, keyword, state)
                print(f"Candidates generated: {len(candidates)}")
            except Exception as e:
                print(f"Discovery failed for {state} | {keyword}: {e}")
                continue

            for candidate in candidates:
                try:
                    extracted = extract_page_fields(
                        candidate["candidate_url"],
                        source_type=candidate.get("source_type", source_type)
                    )

                    raw_text = extracted.get("raw_text", "")

                    print("CHECKING:", candidate["candidate_url"])
                    print("TITLE:", extracted.get("title"))
                    print("IDENTIFIER:", extracted.get("identifier"))
                    print("STATUS:", extracted.get("status"))
                    print("REAL BILL?", looks_like_real_ca_bill(raw_text))
                    print("MATCHES KEYWORD?", matches_keyword(raw_text, keyword))
                    print("-" * 80)

                    if not looks_like_real_ca_bill(raw_text):
                        continue

                    if not matches_keyword(raw_text, keyword):
                        continue

                    normalized = normalize_record(candidate, extracted)
                    all_normalized.append(normalized)

                    print(f"MATCH: {normalized['identifier']} -> {normalized['source_url']}")

                except Exception as e:
                    print(f"Extraction failed for {candidate['candidate_url']}: {e}")

    if all_normalized:
        df = pd.DataFrame(all_normalized).drop_duplicates(
            subset=["state", "source_url", "identifier", "airtable_category"]
        )
        records = df.to_dict(orient="records")

        save_csv(records, "data/exports/findings_export.csv")
        save_sqlite(records)
        print(f"\nSaved {len(records)} matching records.")
    else:
        print("\nNo matching records found.")


if __name__ == "__main__":
    run_pipeline()