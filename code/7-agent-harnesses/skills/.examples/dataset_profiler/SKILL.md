---
name: dataset_profiler
description: Systematic procedure for profiling, summarizing, or exploring an unfamiliar CSV file or DataFrame
---

# Dataset Profiler Skill

You are profiling an unfamiliar dataset. Follow this procedure in order and
report findings in the output format below. Prefer running small scripts over
guessing; never describe data you have not inspected.

## Procedure

1. **Shape & size** — row count, column count, file size on disk.
2. **Schema** — every column with its dtype; flag columns whose dtype looks
   wrong for the name (e.g. numeric IDs parsed as float, dates as object).
3. **Nulls** — per-column null counts; call out any column over 5% null.
4. **Duplicates** — count of fully duplicated rows.
5. **Numeric distributions** — min / max / mean / std for numeric columns;
   flag impossible values (negative ages, future dates, sentinel -999s).
6. **Cardinality** — unique-value counts for object columns; identify likely
   categorical columns (low cardinality) vs identifiers (cardinality ≈ rows).
7. **Three surprising facts** — the three most decision-relevant things a
   human should know before using this data.

## Output format

```
## Dataset Profile: <path>
- Shape: <rows> x <cols> (<size>)
- Schema: <table or list>
- Quality: <nulls, duplicates, suspicious values>
- Highlights:
  1. ...
  2. ...
  3. ...
```

## Notes

- For datasets over 100,000 rows on GPU-equipped machines, prefer
  GPU-accelerated profiling (e.g. `cudf.pandas`) and keep intermediate
  results on the GPU.
- If the file fails to parse, report the first malformed line rather than
  silently switching parsers.
