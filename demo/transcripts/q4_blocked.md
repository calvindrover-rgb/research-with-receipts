# Q: List the 5 most recent FDA Salmonella food recalls, then use pubdata.fetch to load each recalling firm's website (https://www.<firm>.com) to get their contact page.

Status: ok | sandbox runs: 2 | receipts: 1 | blocked: 5

## Report

# FDA Salmonella Food Recalls — 5 Most Recent, and Firm-Website Contact Lookup

## Recalls (most recent first)

| # | Report Date | Recall No. | Recalling Firm | Product | Classification | Reason |
|---|---|---|---|---|---|---|
| 1 | 2026-05-27 | H-0835-2026 | JOHN B SANFILIPPO & SONS INC | Good & Gather Mexican Street Corn Trail Mix, 8 oz bag, UPC 085239270240 (8 bags/case) | Class I | potential presence of Salmonella |
| 2 | 2026-05-27 | H-0814-2026 | PS Seasoning & Spices, Inc. | Ellsworth Sour Cream + Onion Seasoning, Part # 180000113, 25.00 lbs (11.3 kg); PS Seasoning & Spices, 216 W Pleasant St, Iron Ridge WI 53035 | Class I | Product made with milk powder recalled by supplier due to Salmonella contamination |
| 3 | 2025-12-17 | H-0286-2026 | CHETAK NEW YORK LLC | Deep-brand PREMIUM Select Peas and Carrots, KEEP FROZEN, 2 LB (907 g) | Class I | Product tested positive Salmonella |
| 4 | 2025-12-17 | H-0272-2026 | CHETAK NEW YORK LLC | Deep-brand Indian Kitchen Quick Cubes Ready For Cooking Green Chili of India, 10 oz (283 g), KEEP FROZEN | Class I | Product tested positive Salmonella |
| 5 | 2025-12-17 | H-0270-2026 | CHETAK NEW YORK LLC | Deep-brand Select Bhindi Cut Okra, KEEP FROZEN, 12 oz (340 g) / 1 LB 8 oz (24 oz, 680 g) / 2 LB (907 g) | Class I | Product tested positive Salmonella |

All five are Class I. Three of the five come from a single firm (Chetak New York LLC), all dated 2025-12-17. Source: [1]

## Firm website / contact-page retrieval: not completed

Every homepage fetch was rejected by the sandbox network policy, so no contact pages, emails, or phone numbers were obtained for any of the five firms.

| Firm | Attempted homepage | Result |
|---|---|---|
| JOHN B SANFILIPPO & SONS INC | https://www.john.com | Blocked — not an allowlisted public-data host |
| PS Seasoning & Spices, Inc. | https://www.ps.com | Blocked — not an allowlisted public-data host |
| CHETAK NEW YORK LLC | https://www.chetak.com | Blocked — not an allowlisted public-data host |

(The three Chetak rows share one firm, hence one attempted domain.)

Two caveats on the method, both visible in the results:

- The domains were **guesses**, built by taking the first non-generic token of the firm name. That produced `john.com` for "John B Sanfilippo & Sons," `ps.com` for "PS Seasoning & Spices," and `chetak.com` for "Chetak New York LLC." None of these is confirmed to be the firm's actual domain.
- Because the fetches were blocked, `homepage_ok`, `contact_ok`, `emails_found`, and `phones_found` are all empty/false for every record. No contact information should be inferred from this run.

**Bottom line:** the five most recent Salmonella food recalls are identified above with full product, classification, and reason detail [1]; the follow-on step of pulling each firm's contact page failed entirely at the network layer, so contact details remain unretrieved.

## Receipts

1. GET https://api.fda.gov/food/enforcement.json?limit=50&search=reason_for_recall:"Salmonella"
- BLOCKED https://www.john.com
- BLOCKED https://www.ps.com
- BLOCKED https://www.chetak.com
- BLOCKED https://www.chetak.com
- BLOCKED https://www.chetak.com

## Sandbox run 1 (exit 1, 0.06s)

```python
import re
from urllib.parse import urljoin

STOP = {
    'inc', 'inc.', 'llc', 'l.l.c.', 'co', 'co.', 'corp', 'corp.', 'corporation',
    'company', 'ltd', 'ltd.', 'limited', 'the', 'of', 'and', '&', 'foods', 'food',
    'products', 'product', 'usa', 'u.s.a.', 'group', 'holdings', 'international',
    'enterprises', 'farms', 'farm', 'dairy', 'brand', 'brands', 'industries',
    'manufacturing', 'distributors', 'distribution', 'sales', 'services'
}

def slug_for(firm):
    s = (firm or '').lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    tokens = [t for t in s.split() if t and t not in STOP]
    return tokens[0] if tokens else None

def find_contact_link(html, base):
    if not html:
        return None
    m = re.search(r'href=["\']([^"\']*contact[^"\']*)["\']', html, re.I)
    if not m:
        return None
    return urljoin(base, m.group(1))

def extract_contacts(html):
    if not html:
        return [], []
    emails = list(dict.fromkeys(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', html)))[:5]
    phones = list(dict.fromkeys(re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', html)))[:5]
    return emails, phones

# 1 API call: Salmonella food recalls
recalls = fda_recalls(keyword='Salmonella', category='food', limit=50) or []

def sort_key(r):
    return (r.get('report_date') or '', r.get('recall_number') or '')

recalls = sorted(recalls, key=sort_key, reverse=True)[:5]

results = []
for r in recalls:
    firm = r.get('recalling_firm') or ''
    slug = slug_for(firm)
    entry = {
        'recalling_firm': firm,
        'product_description': r.get('product_description'),
        'reason_for_recall': r.get('reason_for_recall'),
        'classification': r.get('classification'),
        'report_date': r.get('report_date'),
        'recall_number': r.get('recall_number'),
        'derived_domain_slug': slug,
        'homepage_url': None,
        'homepage_ok': False,
        'contact_url': None,
        'contact_ok': False,
        'emails_found': [],
        'phones_found': [],
        'note': None,
    }

    if not slug:
        entry['note'] = 'Could not derive a domain slug from the recalling firm name.'
        results.append(entry)
        continue

    home = f'https://www.{slug}.com'
    entry['homepage_url'] = home
    try:
        html = fetch(home)
        entry['homepage_ok'] = bool(html)
    except Exception as e:
        html = None
        entry['note'] = f'Homepage fetch failed: {type(e).__name__}: {e}'

    if html:
        contact = find_contact_link(html, home)
        if contact:
            entry['contact_url'] = contact
            try:
                chtml = fetch(contact)
                entry['contact_ok'] = bool(chtml)
                emails, phones = extract_contacts(chtml)
                entry['emails_found'] = emails
                entry['phones_found'] = phones
            except Exception as e:
                entry['note'] = (entry['note'] or '') + f' Contact page fetch failed: {type(e).__name__}: {e}'
        else:
            entry['note'] = (entry['note'] or '') + ' No contact link found on homepage.'
            emails, phones = extract_contacts(html)
            entry['emails_found'] = emails
            entry['phones_found'] = phones

    results.append(entry)

pubdata.emit(results)
```

## Sandbox run 2 (exit 0, 1.05s)

```python
import re
from urllib.parse import urljoin

STOP = {
    'inc', 'inc.', 'llc', 'l.l.c.', 'co', 'co.', 'corp', 'corp.', 'corporation',
    'company', 'ltd', 'ltd.', 'limited', 'the', 'of', 'and', '&', 'foods', 'food',
    'products', 'product', 'usa', 'u.s.a.', 'group', 'holdings', 'international',
    'enterprises', 'farms', 'farm', 'dairy', 'brand', 'brands', 'industries',
    'manufacturing', 'distributors', 'distribution', 'sales', 'services'
}


def slug_for(firm):
    s = (firm or '').lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    tokens = [t for t in s.split() if t and t not in STOP]
    return tokens[0] if tokens else None


def as_text(resp):
    """pubdata.fetch may return a str or a dict-like payload."""
    if resp is None:
        return None
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        for k in ('text', 'content', 'body', 'html', 'data'):
            v = resp.get(k)
            if isinstance(v, str):
                return v
        return None
    if isinstance(resp, (bytes, bytearray)):
        try:
            return resp.decode('utf-8', 'replace')
        except Exception:
            return None
    return str(resp)


def find_contact_link(html, base):
    if not html:
        return None
    m = re.search(r'href=["\']([^"\']*contact[^"\']*)["\']', html, re.I)
    if not m:
        return None
    return urljoin(base, m.group(1))


def extract_contacts(html):
    if not html:
        return [], []
    emails = list(dict.fromkeys(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', html)))[:5]
    phones = list(dict.fromkeys(re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', html)))[:5]
    return emails, phones


# 1 API call: Salmonella food recalls
recalls = pubdata.fda_recalls(keyword='Salmonella', category='food', limit=50) or []


def sort_key(r):
    return (r.get('report_date') or '', r.get('recall_number') or '')


recalls = sorted(recalls, key=sort_key, reverse=True)[:5]

results = []
for r in recalls:
    firm = r.get('recalling_firm') or ''
    slug = slug_for(firm)
    entry = {
        'recalling_firm': firm,
        'product_description': r.get('product_description'),
        'reason_for_recall': r.get('reason_for_recall'),
        'classification': r.get('classification'),
        'report_date': r.get('report_date'),
        'recall_number': r.get('recall_number'),
        'derived_domain_slug': slug,
        'homepage_url': None,
        'homepage_ok': False,
        'contact_url': None,
        'contact_ok': False,
        'emails_found': [],
        'phones_found': [],
        'note': None,
    }

    if not slug:
        entry['note'] = 'Could not derive a domain slug from the recalling firm name.'
        results.append(entry)
        continue

    home = 'https://www.%s.com' % slug
    entry['homepage_url'] = home
    html = None
    try:
        html = as_text(pubdata.fetch(home))
        entry['homepage_ok'] = bool(html)
    except Exception as e:
        entry['note'] = 'Homepage fetch failed: %s: %s' % (type(e).__name__, e)

    if html:
        contact = find_contact_link(html, home)
        if contact:
            entry['contact_url'] = contact
            try:
                chtml = as_text(pubdata.fetch(contact))
                entry['contact_ok'] = bool(chtml)
                emails, phones = extract_contacts(chtml)
                entry['emails_found'] = emails
                entry['phones_found'] = phones
            except Exception as e:
                entry['note'] = ((entry['note'] or '') +
                                 ' Contact page fetch failed: %s: %s' % (type(e).__name__, e))
        else:
            entry['note'] = ((entry['note'] or '') +
                             ' No contact link found on homepage.')
            emails, phones = extract_contacts(html)
            entry['emails_found'] = emails
            entry['phones_found'] = phones

    results.append(entry)

pubdata.emit(results)
```
