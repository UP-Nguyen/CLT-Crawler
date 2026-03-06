# CLT-Crawler

# Discover > Extract > Normalize and Store
# The point of the web crawler is change detection, 

# (state + keyword) > Discovery > candidate URLs > Extraction > raw fields > Normalization > clean findings table > CSV, SQLite Airtable review

# Implementation:
# each page gets a content hash, each time we crawl, we compare the new hash to the old one, if changed, flag

# TODO:
# store the prior crawl in SQLite and compare by source_url.
# For now, just save the hash

