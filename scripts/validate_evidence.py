"""Validate snapshot schema/provenance, optionally checking public source URLs."""
import argparse, json, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STORE = Path(__file__).parent.parent / "data" / "verified_listings.json"
DOMAINS = {"aws.amazon.com", "azuremarketplace.microsoft.com"}
REQUIRED = {"id","provider","vendor","title","url","description","categories","delivery","verified_at"}

def validate(check_urls=False):
    payload=json.loads(STORE.read_text()); errors=[]; ids=set(); urls=set()
    for item in payload.get("listings", []):
        missing=REQUIRED-set(item)
        if missing: errors.append(f"{item.get('id','unknown')}: missing {sorted(missing)}"); continue
        if item["id"] in ids: errors.append(f"duplicate id: {item['id']}")
        if item["url"] in urls: errors.append(f"duplicate url: {item['url']}")
        ids.add(item["id"]); urls.add(item["url"])
        if urlparse(item["url"]).hostname not in DOMAINS: errors.append(f"unapproved domain: {item['url']}")
        if date.fromisoformat(item["verified_at"]) > date.today(): errors.append(f"future verification date: {item['id']}")
        if check_urls:
            try:
                request=Request(item["url"], headers={"User-Agent":"CloudMatch-evidence-validator/1.0"})
                with urlopen(request, timeout=15) as response:
                    if response.status >= 400: errors.append(f"HTTP {response.status}: {item['url']}")
            except Exception as error: errors.append(f"URL failed {item['id']}: {error}")
    return {"valid":not errors,"records":len(ids),"snapshot_verified_at":payload.get("verified_at"),"errors":errors}

if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--check-urls", action="store_true"); args=parser.parse_args()
    result=validate(args.check_urls); print(json.dumps(result, indent=2)); sys.exit(0 if result["valid"] else 1)
