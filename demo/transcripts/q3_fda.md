# Q: Recent FDA food recalls for undeclared allergens

Status: ok | sandbox runs: 1 | receipts: 1 | blocked: 0

## Report

# Recent FDA Food Recalls for Undeclared Allergens

## Overview

A search of FDA food enforcement records for "undeclared allergen" returned a batch of recent recalls, all reported on **2026-10-28** and all issued by a single firm, **El Ruisenor De Mexico, Inc.** [1]. The recalls cover a wide range of products — flours, snacks, dried fruits, nuts, seeds, drink mixes, and candy — each flagged for one or more undeclared allergens or color additives.

## Recalls by classification

Of the 21 records returned, 3 are **Class I**, 8 are **Class II**, and 9 are **Class III** (one record's reason text was truncated in the returned data) [1].

### Class I (most serious)

| Product | Undeclared allergen(s) |
|---|---|
| Special Red Almond Mole Powder (1 lb, 5 lb, 11 lb) | Sesame, peanuts, wheat, soy, almonds, walnuts, Yellow #5, Yellow #6, Red #40, Blue #2 |
| Fritura Rueda Papa / Potato Wheel Snack (1 lb, 5 lb, 33 lb) | Wheat |
| Horchata Drink Mix (1 lb, 5 lb, 50 lb) | Milk |

### Class II

- Jovy Gummy Worms Neon (UPC 712199083411) — Red #40, Yellow #5, Yellow #6, Blue #1
- Jovy Gummy Bears Regular (UPC 712199085156) — Red #40, Yellow #5, Yellow #6, Blue #1
- Milk Chocolate Covered Raisins (1 lb, 5 lb, 20 lb) — milk, soy
- Fritura mixed dry fruit (1 lb, 5 lb, 25 lb) — wheat, Yellow #5, Yellow #6
- All-Purpose Flour (1 lb, 5 lb, 50 lb) — wheat
- Churro Mix (1 lb, 5 lb, 50 lb) — egg, wheat
- Dried Pears (1 lb, 5 lb, 25 lb) — sulfites
- Dried Diced Pineapple (1 lb, 5 lb, 44 lb) — sulfites

### Class III

- Whole wheat flour (1 lb, 5 lb, 50 lb) — wheat
- Black Sesame Seeds (1 lb, 5 lb, 50 lb) — sesame
- 10X10 Wheat Snack (2 lb, 5 lb, 33 lb) — wheat
- Textured Soy Protein (1 lb, 5 lb, 33 lb) — soy
- Soybeans (1 lb, 5 lb, 50 lb) — soy
- Almonds in Shell (1 lb, 5 lb, 50 lb) — almond
- 4X6 and 4X8 Wheat Snack (1 lb, 5 lb, 33 lb) — wheat
- Wheat Bran (1 lb, 5 lb, 50 lb) — wheat
- Butter Toffee Peanuts (1 lb, 5 lb, 50 lb) — peanuts, milk

An additional Class III item, **Fritura Lagrimita / Teardrop Wheat Snack** (1 lb, 5 lb, 44 lb), lists wheat among its undeclared allergens, though the full reason text was cut off in the returned record [1].

## Notable patterns

- **Wheat** is the most frequently cited undeclared allergen, appearing in flours, wheat snacks, bran, churro mix, and the mole powder [1].
- **Soy, milk, sesame, peanuts, tree nuts (almond, walnut), egg, and sulfites** also appear across the recalls [1].
- Several products were flagged for undeclared **color additives** (Red #40, Yellow #5, Yellow #6, Blue #1, Blue #2) rather than classic allergens [1].
- Most products are packaged in bulk clear plastic units (1 lb up to 50 lb) with **no UPC**, suggesting a wholesale/ingredient distribution channel [1].

## Source

[1] https://api.fda.gov/food/enforcement.json?limit=25&search=reason_for_recall:"undeclared%20allergen"&sort=report_date:desc

## Receipts

1. GET https://api.fda.gov/food/enforcement.json?limit=25&search=reason_for_recall:"undeclared%20allergen"&sort=report_date:desc

## Sandbox run 1 (exit 0, 0.92s)

```python
import pubdata

recalls = pubdata.fda_recalls(category='food', keyword='undeclared allergen', limit=25)

if not recalls:
    recalls = pubdata.fda_recalls(category='food', keyword='allergen', limit=25)

result = []
for r in recalls:
    result.append({
        'recalling_firm': r.get('recalling_firm'),
        'product_description': r.get('product_description'),
        'reason_for_recall': r.get('reason_for_recall'),
        'classification': r.get('classification'),
        'report_date': r.get('report_date'),
    })

pubdata.emit(result)
```
