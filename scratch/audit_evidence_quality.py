"""Audit evidence quality, citations vs claims, and excerpts."""

import json
from collections import Counter, defaultdict

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]

total_citations = sum(len(a.get("evidence", [])) for a in apps)
total_claims = sum(len(a.get("claims", [])) for a in apps)

print(f"Total Applications: {len(apps)}")
print(f"Total Evidence Citations: {total_citations}")
print(f"Total Evaluated Claims: {total_claims}")

# Check citations
citation_domains = Counter()
citation_urls = set()
duplicate_citations = 0

for a in apps:
    seen_urls_in_app = set()
    for e in a.get("evidence", []):
        u = e.get("url")
        if u in seen_urls_in_app:
            duplicate_citations += 1
        seen_urls_in_app.add(u)
        citation_urls.add(u)
        from urllib.parse import urlparse
        domain = urlparse(u).netloc
        citation_domains[domain] += 1

print(f"Distinct Citation URLs: {len(citation_urls)}")
print(f"Intra-app duplicate citation instances: {duplicate_citations}")
print("\nTop Citation Domains:")
for d, cnt in citation_domains.most_common(10):
    print(f"  {d}: {cnt}")

# Check claims
live_fetched_claims = 0
inferred_claims = 0
unknown_claims = 0
claims_with_excerpt = 0
claims_without_excerpt = 0

for a in apps:
    for c in a.get("claims", []):
        prov = c.get("provenance")
        excerpt = c.get("supporting_excerpt")
        if prov == "LIVE_FETCHED":
            live_fetched_claims += 1
            assert c.get("source_url") is not None, f"Live fetched claim without URL in {a['app_id']}"
            assert excerpt is not None and len(excerpt) > 0, f"Live fetched claim without excerpt in {a['app_id']}"
            claims_with_excerpt += 1
        elif prov == "INFERRED":
            inferred_claims += 1
            if excerpt:
                claims_with_excerpt += 1
            else:
                claims_without_excerpt += 1
        elif prov == "UNKNOWN":
            unknown_claims += 1
            claims_without_excerpt += 1

print("\nClaims Breakdown:")
print(f"  LIVE_FETCHED claims (directly backed by live HTTP text): {live_fetched_claims} ({live_fetched_claims/total_claims*100:.1f}%)")
print(f"  INFERRED claims (deterministic algorithmic logic): {inferred_claims} ({inferred_claims/total_claims*100:.1f}%)")
print(f"  UNKNOWN claims (missing evidence preserved): {unknown_claims} ({unknown_claims/total_claims*100:.1f}%)")
print(f"  Claims with verbatim supporting excerpts: {claims_with_excerpt}")
print(f"  Claims without excerpts (inferred or unknown): {claims_without_excerpt}")

# Verification status: explain that 65 passed automated checks, NOT "independently verified"
verif_counts = Counter(a.get("verification_status") for a in apps)
print("\nVerification Status Distribution:")
for s, cnt in verif_counts.most_common():
    print(f"  {s}: {cnt}")
