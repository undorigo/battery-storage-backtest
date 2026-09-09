# Recorded API responses

Real responses, saved verbatim, so the parser can be tested without the network and
without a token — and so a change in ENTSO-E's output shows up as a failing test rather
than as a quietly different number.

## `sample_A44_dayahead_price.xml`

Captured 9 September 2026, 11:43 UTC, during the platform's recovery from its
infrastructure migration.

```
documentType = A44                     day-ahead prices
in/out_Domain = 10Y1001A1001A82H       DE-LU
periodStart   = 202406010000
periodEnd     = 202406020000
```

**Why this one.** It happens to contain both traps the parser has to survive, which a
tidier response would not have shown:

1. **Two resolutions for the same hours.** The document carries four `TimeSeries`. Each
   period appears twice — once at `PT15M`, once at `PT60M` — even though this is June
   2024, well before quarter-hourly products went live in October 2025. The *only* field
   that tells them apart is
   `classificationSequence_AttributeInstanceComponent.position`: `1` is hourly, `2` is
   quarter-hourly. Domain, currency, business type, auction type and contract type are
   identical across all four. Selecting on anything else silently returns a different
   series.

2. **`curveType A03`, where an absent position is not missing data.** TimeSeries 3 holds
   95 points but its highest position is 96 — position 54 is simply absent. A03 means
   "variable-sized block": a gap repeats the previous value. Position 53 is `0` and
   position 55 is `-16.75`, so the correct value at 54 is `0`. Reindexing without a
   forward fill would put a NaN there and any later imputation would land near `-16.75`,
   which is a different price and, for a battery, a different decision.

`entsoe-py` handles both correctly (`parsers.py`, "Handle curveType A03: forward fill
missing positions"), and its hourly output for this window matched SMARD to 0.000000
EUR/MWh across all 49 overlapping hours. The fixture exists to keep that true.
