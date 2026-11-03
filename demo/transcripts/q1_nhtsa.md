# Q: Which vehicle makes had the most NHTSA recalls in 2025?

Status: ok | sandbox runs: 1 | receipts: 1 | blocked: 0

## Report

# NHTSA Vehicle Recalls in 2025: Top Manufacturers

Ford Motor Company led all vehicle makes by a wide margin, with 146 recalls covering 12,914,776 potentially affected vehicles [1].

## Top 10 Manufacturers by Recall Count (2025)

| Rank | Manufacturer | Recalls | Potentially Affected |
|------|--------------|---------|----------------------|
| 1 | Ford Motor Company | 146 | 12,914,776 |
| 2 | Chrysler (FCA US, LLC) | 41 | 2,692,665 |
| 3 | Forest River, Inc. | 36 | 36,781 |
| 4 | General Motors, LLC | 28 | 1,079,437 |
| 5 | International Motors, LLC | 26 | 95,059 |
| 6 | Volkswagen Group of America, Inc. | 26 | 1,020,557 |
| 7 | BMW of North America, LLC | 23 | 509,190 |
| 8 | Honda (American Honda Motor Co.) | 23 | 1,158,632 |
| 9 | Mercedes-Benz USA, LLC | 21 | 142,359 |
| 10 | Hyundai Motor America | 20 | 1,076,874 |

## Key Observations

- **Ford** filed more than three times as many recalls as the next manufacturer (146 vs. 41) and accounted for the largest affected fleet by far [1].
- **Chrysler (FCA US)** ranked second in both recall count (41) and affected vehicles (2,692,665) [1].
- **Forest River** ranked third by count (36) but its affected volume was comparatively small (36,781), reflecting its recreational-vehicle focus [1].
- **International Motors** and **Volkswagen Group** tied at 26 recalls each, though Volkswagen's affected total (1,020,557) was roughly ten times larger [1].
- **BMW** and **Honda** also tied at 23 recalls each, with Honda's affected count (1,158,632) more than double BMW's (509,190) [1].

**Source:**
[1] NHTSA recall data (datahub.transportation.gov), vehicle recall campaigns received 2025-01-01 through 2025-12-31, grouped by manufacturer.

## Receipts

1. GET https://datahub.transportation.gov/resource/6axg-epim.json?%24select=manufacturer%2C+count%28%2A%29+as+recalls%2C+sum%28potentially_affected%29+as+potentially_affected&%24where=report_received_date+between+%272025-01-01T00%3A00%3A00%27+and+%272025-12-31T23%3A59%3A59%27+AND+recall_type%3D%27Vehicle%27&%24group=manufacturer&%24order=recalls+DESC&%24limit=10

## Sandbox run 1 (exit 0, 0.89s)

```python
import pubdata

result = pubdata.nhtsa_recall_counts_by_manufacturer(
    start='2025-01-01',
    end='2025-12-31',
    recall_type='Vehicle',
    top=10
)

pubdata.emit(result)
```
