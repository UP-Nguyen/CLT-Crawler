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