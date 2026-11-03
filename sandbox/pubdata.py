"""pubdata: the ONLY data library available inside the sandbox.
Every HTTP call is logged as a receipt (citation). Only allowlisted public-data hosts are reachable."""
import json, urllib.request, urllib.parse, os
ALLOW = {"api.fda.gov", "api.nhtsa.gov", "efts.sec.gov", "data.sec.gov", "api.usaspending.gov",
         "www.federalregister.gov", "geocoding.geo.census.gov", "data-api.ecb.europa.eu"}
RECEIPTS = []
UA = "PublicRecordsAgent/0.1 research@example.org"

def _req(url, data=None):
    host = urllib.parse.urlparse(url).hostname
    if host not in ALLOW:
        raise PermissionError(f"BLOCKED by sandbox policy: {host} is not an allowlisted public-data host")
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers={"User-Agent": UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=20) as resp:
        out = json.loads(resp.read().decode())
    RECEIPTS.append({"url": url, "method": "POST" if body else "GET"})
    return out

def fda_recalls(firm=None, keyword=None, category="food", limit=50):
    q = []
    if firm: q.append(f'recalling_firm:"{firm}"')
    if keyword: q.append(f'reason_for_recall:"{keyword}"')
    s = ("&search=" + urllib.parse.quote("+AND+".join(q), safe='+:"')) if q else ""
    try: return _req(f"https://api.fda.gov/{category}/enforcement.json?limit={limit}{s}").get("results", [])
    except urllib.error.HTTPError as e:
        if e.code == 404: return []
        raise

def nhtsa_recalls(make, model, year):
    return _req(f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={urllib.parse.quote(make)}&model={urllib.parse.quote(model)}&modelYear={year}").get("results", [])

def usaspending_awards(recipient=None, keyword=None, limit=25, start="2020-01-01", end="2026-12-31"):
    f = {"time_period": [{"start_date": start, "end_date": end}], "award_type_codes": ["A", "B", "C", "D"]}
    if recipient: f["recipient_search_text"] = [recipient]
    if keyword: f["keywords"] = [keyword]
    body = {"filters": f, "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency", "Start Date"],
            "limit": limit, "sort": "Award Amount", "order": "desc"}
    return _req("https://api.usaspending.gov/api/v2/search/spending_by_award/", body).get("results", [])

def sec_search(q, forms="10-K"):
    return _req(f"https://efts.sec.gov/LATEST/search-index?q={urllib.parse.quote(q)}&forms={forms}").get("hits", {}).get("hits", [])

def sec_facts(cik):
    return _req(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json")

def federal_register(term, limit=20):
    return _req(f"https://www.federalregister.gov/api/v1/documents.json?per_page={limit}&conditions[term]={urllib.parse.quote(term)}").get("results", [])

def fetch(url):
    """Generic fetch — still subject to the allowlist."""
    return _req(url)

def emit(result):
    """Call once at the end: prints result + receipts as JSON for the control plane."""
    print("@@RESULT@@" + json.dumps({"result": result, "receipts": RECEIPTS}, default=str))
