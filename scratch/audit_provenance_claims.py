import json

with open("data/results/final_research_100.json", "r", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]

total_claims = 0
live_fetched_claims = []
generated_live_claims = []

# Typical generated conclusion phrases
generated_phrases = [
    "no verified official mcp server",
    "no server discovered",
    "no saas api authentication",
    "application does not expose api authentication",
    "no public developer api",
    "open source codebase available without credential gating",
    "open source cli codebase available without credential gating",
    "native composio toolkit available",
    "primary authentication method is oauth",
    "local cli utility execution",
    "consumer web interface",
]

for a in apps:
    for c in a.get("claims", []):
        total_claims += 1
        if c.get("provenance") == "LIVE_FETCHED":
            live_fetched_claims.append((a["app_id"], c))
            excerpt = (c.get("supporting_excerpt") or "").lower()
            if any(p in excerpt for p in generated_phrases) or not c.get("source_url"):
                generated_live_claims.append((a["app_id"], c))

print(f"Total claims: {total_claims}")
print(f"Total LIVE_FETCHED claims: {len(live_fetched_claims)}")
print(f"Suspicious/Generated LIVE_FETCHED claims: {len(generated_live_claims)}")

print("\nSample of suspicious LIVE_FETCHED claims:")
for aid, c in generated_live_claims[:15]:
    print(f"[{aid}] {c['field_name']} = {c['extracted_value']}")
    print(f"   Excerpt: {c.get('supporting_excerpt')}")
    print(f"   URL: {c.get('source_url')}")
