# CLT-Crawler

# Discover > Extract > Normalize and Store
# The point of the web crawler is change detection, 

# (state + keyword) > Discovery > candidate URLs > Extraction > raw fields > Normalization > clean findings table > CSV, SQLite Airtable review

# Implementation:
# each page gets a content hash, each time we crawl, we compare the new hash to the old one, if changed, flag

# TODO:
# store the prior crawl in SQLite and compare by source_url.
# For now, just save the hash

# from main repo (CLT-Crawler):
# python src/run.py


# 3-5-26
# With just california, and community land trust,definition,high in keywords. 


# current flow
manual seed / source page
candidate links
extraction
normalized findings CSV
human review
Airtable

# maybe pivot
1. Load search page
2. Submit a real search
3. Get search results
4. Extract bill detail links from those results
5. Visit each bill detail page

Example: https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260AB2399


# 3/7/26 California prototype
seed files > discovery adapters > extraction > normalize > findings_export.csv ?

Phase 1
Generate many possible California bill URLs automatically.

Phase 2
Visit them and detect which are real.

Phase 3

Filter by  keywords.

seeded file processor > actual crawler 
Progression

FLOW
generate bill URLs
fetch page
check if it is a real bill
check if it matches your keyword
send to extraction/normalize
save findings_export.csv

# 3/13/2026
NY Open Legislation API
- search bills by keyword
- turn API results into candidates
- normalize directly

# 4/1

## Alabama
AL statutes by seeded title/chapter ranges
- official Code of Alabama section pages
- extract + match
- findings_export.csv

NOTE: working as a targeted legal-source retriever, not as a self-discovering crawler. 

seeded statute URLs
> fetch
> extract
> match
> export

TODO: add this to GH actions secrets
https://legislation.nysenate.gov/public

At the top of run.py

To compare states:
DEBUG_STATES = ["CA", "VT"]
SAVE_SQLITE = False            # keep False while prototyping


For a full run:
DEBUG_STATES = []
DEBUG_KEYWORDS = []
SAVE_SQLITE = True