import json
from collections import Counter

FILES = [
    "data/results/final_research_100.json",
    "data/results/verified_research.json",
]

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    apps = data["applications"]
    print(f"\nProcessing {path}: {len(apps)} applications.")
    
    cli_apps = {"sherlock", "mermaid-cli"}
    web_only_apps = {"notebooklm", "consensus", "devin", "fanbasis"}
    
    for a in apps:
        aid = a["app_id"]
        auth = a["auth"]
        
        # 1. Integration Mode & Applicability
        if aid in cli_apps:
            auth["integration_mode"] = "CLI / LOCAL_PROCESS"
            auth["auth_applicability"] = "NOT_APPLICABLE"
            auth["primary_method"] = "NOT_APPLICABLE"
            auth["supported_methods"] = ["NOT_APPLICABLE"]
            auth["accessibility_notes"] = "Local CLI utility execution; runs locally without SaaS API authentication."
        elif aid in web_only_apps:
            auth["integration_mode"] = "WEB_ONLY"
            auth["auth_applicability"] = "NOT_APPLICABLE"
            auth["primary_method"] = "NOT_APPLICABLE"
            auth["supported_methods"] = ["NOT_APPLICABLE"]
            auth["accessibility_notes"] = "Consumer web interface; no public developer API or API authentication documented."
        else:
            auth["integration_mode"] = "API"
            auth["auth_applicability"] = "APPLICABLE"
            
            # Update specific SaaS APIs previously misclassified as OTHER
            if aid == "dealcloud":
                auth["primary_method"] = "UNKNOWN"
                auth["supported_methods"] = ["UNKNOWN"]
                auth["accessibility_notes"] = "Enterprise private CRM API; credentials and auth specifications require partner / sales contact."
            elif aid in ["slack", "hubspot", "ecwid", "xero"]:
                auth["primary_method"] = "OAUTH2"
                auth["supported_methods"] = ["OAUTH2", "BEARER_TOKEN"] if aid in ["slack", "hubspot"] else ["OAUTH2"]
                auth["accessibility_notes"] = f"OAuth 2.0 authorization framework ({aid})."
            elif aid in ["attio", "bigcommerce", "clickup", "copper", "freshdesk", "mongodb-atlas", "mrscraper", "reducto", "twenty", "twilio", "vonage", "zendesk"]:
                auth["primary_method"] = "API_KEY"
                auth["supported_methods"] = ["API_KEY"]
                auth["accessibility_notes"] = f"API Key / token credentials ({aid})."
            elif aid in ["front", "harvest", "sentry", "snowflake", "telegram"]:
                auth["primary_method"] = "TOKEN / PAT"
                auth["supported_methods"] = ["TOKEN / PAT", "BEARER_TOKEN"]
                auth["accessibility_notes"] = f"Access token / Personal Access Token credentials ({aid})."
            elif aid in ["dataforseo", "neo4j"]:
                auth["primary_method"] = "BASIC"
                auth["supported_methods"] = ["BASIC", "API_KEY"] if aid == "dataforseo" else ["BASIC"]
                auth["accessibility_notes"] = f"HTTP Basic Auth credentials ({aid})."
            elif aid in ["coda", "github"]:
                auth["primary_method"] = "TOKEN / PAT"
                auth["supported_methods"] = ["TOKEN / PAT", "OAUTH2"]
            elif auth["primary_method"] in ["PERSONAL_ACCESS_TOKEN", "BEARER_TOKEN"]:
                auth["primary_method"] = "TOKEN / PAT"
            # OAUTH2, API_KEY, UNKNOWN stay as they are
            
        # Update claims if primary_method claim exists
        for claim in a.get("claims", []):
            if claim.get("field_name") == "auth.primary_method":
                claim["extracted_value"] = auth["primary_method"]
                if auth["primary_method"] == "NOT_APPLICABLE":
                    claim["supporting_excerpt"] = auth["accessibility_notes"]
                    claim["polarity"] = "NEGATIVE"
                elif auth["primary_method"] != "UNKNOWN":
                    claim["supporting_excerpt"] = auth["accessibility_notes"]
                    claim["polarity"] = "POSITIVE"

    # Verify counts
    total = len(apps)
    mode_counts = Counter(a["auth"]["integration_mode"] for a in apps)
    app_counts = Counter(a["auth"]["auth_applicability"] for a in apps)
    auth_counts = Counter(a["auth"]["primary_method"] for a in apps)
    
    print("Integration Modes:", dict(mode_counts))
    print("Auth Applicability:", dict(app_counts))
    print("All Auth Methods:", dict(auth_counts))
    
    applicable_apps = [a for a in apps if a["auth"]["auth_applicability"] == "APPLICABLE"]
    known_auth = [a for a in applicable_apps if a["auth"]["primary_method"] not in ["UNKNOWN", "NOT_APPLICABLE"]]
    unknown_auth = [a for a in applicable_apps if a["auth"]["primary_method"] == "UNKNOWN"]
    not_applicable = [a for a in apps if a["auth"]["auth_applicability"] == "NOT_APPLICABLE"]
    
    print(f"\n--- STRICT METRICS ({path}) ---")
    print(f"Total applications: {total}")
    print(f"API-integratable applications: {mode_counts['API']} ({mode_counts['API']/total*100:.1f}%, {mode_counts['API']}/{total})")
    print(f"CLI / Local Process applications: {mode_counts['CLI / LOCAL_PROCESS']} ({mode_counts['CLI / LOCAL_PROCESS']/total*100:.1f}%, {mode_counts['CLI / LOCAL_PROCESS']}/{total})")
    print(f"Web-only applications: {mode_counts['WEB_ONLY']} ({mode_counts['WEB_ONLY']/total*100:.1f}%, {mode_counts['WEB_ONLY']}/{total})")
    print(f"Authentication-applicable applications: {len(applicable_apps)} ({len(applicable_apps)/total*100:.1f}%, {len(applicable_apps)}/{total})")
    print(f"Not-applicable records: {len(not_applicable)} ({len(not_applicable)/total*100:.1f}%, {len(not_applicable)}/{total})")
    print(f"Known authentication records: {len(known_auth)} ({len(known_auth)/len(applicable_apps)*100:.1f}% of applicable, {len(known_auth)}/{len(applicable_apps)})")
    print(f"Unknown authentication records: {len(unknown_auth)} ({len(unknown_auth)/len(applicable_apps)*100:.1f}% of applicable, {len(unknown_auth)}/{len(applicable_apps)})")
    
    known_methods = Counter(a["auth"]["primary_method"] for a in known_auth)
    print("\nDistribution of Known Authentication Methods (denominator = " + str(len(known_auth)) + "):")
    for m, c in known_methods.most_common():
        pct = c / len(known_auth) * 100
        print(f"  - {m}: {c} ({pct:.1f}%, {c}/{len(known_auth)})")
        
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {path} successfully.")

if __name__ == "__main__":
    for p in FILES:
        update_file(p)
