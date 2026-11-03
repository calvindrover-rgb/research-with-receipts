# Q: Top federal contractors for NAICS 541512 last fiscal year

Status: ok | sandbox runs: 1 | receipts: 1 | blocked: 0

## Report

## Top Federal Contractors — NAICS 541512, FY2026

Ranked by obligated contract dollars for the most recent completed federal fiscal year (FY2026):

| Rank | Contractor | Obligated Amount | UEI |
|---:|---|---:|---|
| 1 | ACCENTURE FEDERAL SERVICES LLC | $3,042,453,229.41 | C47BNA8GM833 |
| 2 | GENERAL DYNAMICS INFORMATION TECHNOLOGY, INC. | $2,127,558,535.61 | SMNWM6HN79X5 |
| 3 | ORACLE HEALTH GOVERNMENT SERVICES, INC. | $2,060,156,283.00 | DT2KS3HH5FP5 |
| 4 | BOOZ ALLEN HAMILTON INC | $1,782,568,945.49 | JCBMLGPE6Z71 |
| 5 | DELOITTE CONSULTING LLP | $1,450,897,650.27 | CKV2L9GZKJK3 |
| 6 | CACI, INC. - FEDERAL | $1,430,147,351.67 | N3PBJAVNKF61 |
| 7 | SCIENCE APPLICATIONS INTERNATIONAL CORPORATION | $1,344,840,790.89 | MMLKPW9JLX64 |
| 8 | SALIENT CRGT, INC. | $1,153,276,818.24 | Q5LJNF15T2R5 |
| 9 | PERATON INC. | $1,010,847,171.36 | ZBPQEJVECCT4 |
| 10 | LEIDOS, INC. | $762,406,209.06 | UE9QJD4KK1L6 |

Source: [1]

## Receipts

1. POST https://api.usaspending.gov/api/v2/search/spending_by_category/recipient/

## Sandbox run 1 (exit 0, 0.31s)

```python
import pubdata

result = pubdata.usaspending_top_recipients(
    naics="541512",
    fiscal_year=2026,
    limit=10
)

pubdata.emit(result)
```
