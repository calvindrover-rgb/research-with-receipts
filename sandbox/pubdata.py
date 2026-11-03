"""pubdata: the ONLY data library available inside the sandbox.
Every HTTP call is logged as a receipt (citation). Only allowlisted public-data hosts are reachable."""
import json, urllib.request, urllib.parse, os
ALLOW = {"api.fda.gov", "datahub.transportation.gov", "api.nhtsa.gov", "efts.sec.gov", "data.sec.gov", "api.usaspending.gov",
         "www.federalregister.gov", "geocoding.geo.census.gov", "data-api.ecb.europa.eu"}
RECEIPTS = []
BLOCKED = []  # egress attempts refused by policy (audit log, emitted with the result)
UA = "PublicRecordsAgent/0.1 research@example.org"

def _req(url, data=None):
    host = urllib.parse.urlparse(url).hostname
    if host not in ALLOW:
        BLOCKED.append({"url": url, "host": host})
        raise PermissionError(f"BLOCKED by sandbox policy: {host} is not an allowlisted public-data host")
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers={"User-Agent": UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as resp:
        out = json.loads(resp.read().decode())
    RECEIPTS.append({"url": url, "method": "POST" if body else "GET"})
    return out

def fda_recalls(firm=None, keyword=None, category="food", limit=50, sort="report_date:desc"):
    q = []
    if firm: q.append(f'recalling_firm:"{firm}"')
    if keyword: q.append(f'reason_for_recall:"{keyword}"')
    s = ("&search=" + urllib.parse.quote("+AND+".join(q), safe='+:"')) if q else ""
    srt = f"&sort={sort}" if sort else ""
    try: return _req(f"https://api.fda.gov/{category}/enforcement.json?limit={limit}{s}{srt}").get("results", [])
    except urllib.error.HTTPError as e:
        if e.code == 404: return []
        raise

def nhtsa_recalls(make, model, year):
    return _req(f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={urllib.parse.quote(make)}&model={urllib.parse.quote(model)}&modelYear={year}").get("results", [])

def nhtsa_recall_campaigns(start, end, manufacturer=None, limit=5000):
    """NHTSA recall campaigns filed between start and end (YYYY-MM-DD), from the official DOT open-data mirror."""
    w = f"report_received_date between '{start}T00:00:00' and '{end}T23:59:59'"
    if manufacturer: w += f" AND upper(manufacturer) like upper('%{manufacturer.replace(chr(39), '')}%')"
    qs = urllib.parse.urlencode({"$where": w, "$limit": limit, "$order": "report_received_date DESC",
          "$select": "nhtsa_id,report_received_date,manufacturer,subject,component,recall_type,potentially_affected"})
    return _req("https://datahub.transportation.gov/resource/6axg-epim.json?" + qs)

def nhtsa_recall_counts_by_manufacturer(start, end, recall_type="Vehicle", top=10):
    w = f"report_received_date between '{start}T00:00:00' and '{end}T23:59:59'"
    if recall_type: w += f" AND recall_type='{recall_type}'"
    qs = urllib.parse.urlencode({"$select": "manufacturer, count(*) as recalls, sum(potentially_affected) as potentially_affected",
          "$where": w, "$group": "manufacturer", "$order": "recalls DESC", "$limit": top})
    rows = _req("https://datahub.transportation.gov/resource/6axg-epim.json?" + qs)
    for r in rows:
        r["recalls"] = int(float(r.get("recalls", 0))); r["potentially_affected"] = int(float(r.get("potentially_affected") or 0))
    return rows

def usaspending_top_recipients(naics, fiscal_year, limit=10):
    fy = int(fiscal_year)
    body = {"filters": {"naics_codes": {"require": [str(naics)]}, "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [{"start_date": f"{fy-1}-10-01", "end_date": f"{fy}-09-30"}]}, "limit": limit}
    rows = _req("https://api.usaspending.gov/api/v2/search/spending_by_category/recipient/", body).get("results", [])
    return [{"name": r["name"], "amount": r["amount"], "uei": r.get("uei")} for r in rows]

def usaspending_awards(recipient=None, keyword=None, limit=25, start="2020-01-01", end="2026-12-31", naics=None):
    f = {"time_period": [{"start_date": start, "end_date": end}], "award_type_codes": ["A", "B", "C", "D"]}
    if naics: f["naics_codes"] = {"require": [str(naics)]}
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
    print("@@RESULT@@" + json.dumps({"result": result, "receipts": RECEIPTS, "blocked": BLOCKED}, default=str))
