import os
import pandas as pd
import sqlite3

def deduplicate_records(records):
    seen = set()
    unique = []

    for record in records:
        key = (
            record["state"],
            record["source_url"],
            record["identifier"],
            record["airtable_category"],
        )
        if key not in seen:
            seen.add(key)
            unique.append(record)

    return unique

def save_csv(records, filepath):
    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    return df

def save_sqlite(records, db_path="data/processed/clt_crawler.db", table_name="findings"):
    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="append", index=False)
    conn.close()