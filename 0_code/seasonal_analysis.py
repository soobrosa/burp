#!/usr/bin/env python3
"""Seasonal and temporal analysis of Hungarian menu dishes.

Computes monthly frequency distributions, seasonality indices, and
identifies seasonal patterns in dish appearances.

Usage:
    python 0_code/seasonal_analysis.py \
        --menus daily_menus.csv \
        --dishes dishes_resolved.csv \
        --output-monthly dish_monthly_counts.csv \
        --output-summary dish_seasonal_summary.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

SEASONS = {
    "tél": [12, 1, 2],
    "tavasz": [3, 4, 5],
    "nyár": [6, 7, 8],
    "ősz": [9, 10, 11],
}

MONTH_TO_SEASON = {}
for season, months in SEASONS.items():
    for m in months:
        MONTH_TO_SEASON[m] = season


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--menus", type=Path, default=Path("daily_menus.csv"),
    )
    parser.add_argument(
        "--dishes", type=Path, default=Path("dishes_resolved.csv"),
        help="Resolved dishes CSV with canonical_name column.",
    )
    parser.add_argument(
        "--output-monthly", type=Path, default=Path("dish_monthly_counts.csv"),
    )
    parser.add_argument(
        "--output-summary", type=Path, default=Path("dish_seasonal_summary.csv"),
    )
    parser.add_argument(
        "--output-json", type=Path, default=Path("seasonal_dishes.json"),
    )
    parser.add_argument(
        "--min-count", type=int, default=10,
        help="Minimum total appearances to include in analysis (default: 10).",
    )
    return parser.parse_args()


def build_canonical_map(dishes_path: Path) -> dict[str, str]:
    """Build dish_name -> canonical_name mapping from resolved dishes."""
    mapping: dict[str, str] = {}
    with dishes_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            name = row.get("dish_name", "")
            canonical = row.get("canonical_name", name)
            if name:
                mapping[name] = canonical
    return mapping


def main() -> None:
    args = parse_args()
    for p in [args.menus, args.dishes]:
        if not p.exists():
            raise SystemExit(f"File not found: {p}")

    print("=" * 60, file=sys.stderr)
    print("Seasonal / Temporal Analysis", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Load canonical name mapping — only dishes present in cleaned set
    canonical_map = build_canonical_map(args.dishes)
    known_dishes = set(canonical_map.keys())
    print(f"  Loaded {len(canonical_map):,} dish->canonical mappings", file=sys.stderr)

    # Read menus and aggregate by month
    # monthly_counts[canonical][month] = count
    monthly_counts: dict[str, Counter[int]] = defaultdict(Counter)
    first_seen: dict[str, str] = {}
    last_seen: dict[str, str] = {}
    total_counts: Counter[str] = Counter()
    bad_dates = 0
    unmatched = 0

    with args.menus.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            date_str = row.get("date", "")
            dish = row.get("dish_name", "").strip()
            if not dish or not date_str:
                continue

            # Skip dishes not in the cleaned set
            if dish not in known_dishes:
                unmatched += 1
                continue

            # Parse month from YYYY-MM-DD
            parts = date_str.split("-")
            if len(parts) < 2:
                bad_dates += 1
                continue
            try:
                month = int(parts[1])
            except ValueError:
                bad_dates += 1
                continue

            # Resolve to canonical name
            canonical = canonical_map.get(dish, dish)

            monthly_counts[canonical][month] += 1
            total_counts[canonical] += 1

            if canonical not in first_seen or date_str < first_seen[canonical]:
                first_seen[canonical] = date_str
            if canonical not in last_seen or date_str > last_seen[canonical]:
                last_seen[canonical] = date_str

    print(f"  Processed menus ({bad_dates} bad dates, {unmatched:,} unmatched skipped)", file=sys.stderr)
    print(f"  Unique canonical dishes: {len(monthly_counts):,}", file=sys.stderr)

    # Filter by min count
    filtered = {
        dish: counts
        for dish, counts in monthly_counts.items()
        if total_counts[dish] >= args.min_count
    }
    print(f"  After min_count={args.min_count} filter: {len(filtered):,} dishes", file=sys.stderr)

    # Write monthly counts
    month_cols = [f"month_{m:02d}" for m in range(1, 13)]
    with args.output_monthly.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["canonical_name", "total"] + month_cols)
        for dish in sorted(filtered, key=lambda d: -total_counts[d]):
            counts = filtered[dish]
            row = [dish, total_counts[dish]]
            row += [counts.get(m, 0) for m in range(1, 13)]
            writer.writerow(row)

    # Compute seasonality index (coefficient of variation across months)
    summaries = []
    for dish in sorted(filtered, key=lambda d: -total_counts[d]):
        counts = filtered[dish]
        month_vals = [counts.get(m, 0) for m in range(1, 13)]
        total = sum(month_vals)
        mean = total / 12
        if mean > 0:
            variance = sum((v - mean) ** 2 for v in month_vals) / 12
            std = variance ** 0.5
            cv = std / mean
        else:
            cv = 0.0

        # Peak month and season
        peak_month = max(range(1, 13), key=lambda m: counts.get(m, 0))
        peak_season = MONTH_TO_SEASON[peak_month]

        # Season totals
        season_totals = {}
        for season, months in SEASONS.items():
            season_totals[season] = sum(counts.get(m, 0) for m in months)

        summaries.append({
            "canonical_name": dish,
            "total_count": total_counts[dish],
            "peak_month": peak_month,
            "peak_season": peak_season,
            "seasonality_index": round(cv, 3),
            "first_seen": first_seen.get(dish, ""),
            "last_seen": last_seen.get(dish, ""),
            "tél": season_totals["tél"],
            "tavasz": season_totals["tavasz"],
            "nyár": season_totals["nyár"],
            "ősz": season_totals["ősz"],
        })

    # Write summary
    summary_fields = [
        "canonical_name", "total_count", "peak_month", "peak_season",
        "seasonality_index", "first_seen", "last_seen",
        "tél", "tavasz", "nyár", "ősz",
    ]
    with args.output_summary.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=summary_fields)
        writer.writeheader()
        writer.writerows(summaries)

    # Top seasonal dishes JSON
    seasonal_top: dict[str, list[dict]] = {}
    for season in SEASONS:
        by_season = sorted(summaries, key=lambda s: -s[season])
        seasonal_top[season] = [
            {"dish": s["canonical_name"], "count": s[season], "seasonality": s["seasonality_index"]}
            for s in by_season[:20]
        ]

    # Most seasonal dishes (highest CV, appearing enough)
    most_seasonal = sorted(
        [s for s in summaries if s["total_count"] >= args.min_count * 2],
        key=lambda s: -s["seasonality_index"],
    )[:30]

    json_out = {
        "top_per_season": seasonal_top,
        "most_seasonal": [
            {
                "dish": s["canonical_name"],
                "peak_season": s["peak_season"],
                "peak_month": s["peak_month"],
                "seasonality_index": s["seasonality_index"],
                "total": s["total_count"],
            }
            for s in most_seasonal
        ],
    }
    with args.output_json.open("w", encoding="utf-8") as fh:
        json.dump(json_out, fh, ensure_ascii=False, indent=2)

    # Print highlights
    print(f"\n  Most seasonal dishes (highest CV):", file=sys.stderr)
    for s in most_seasonal[:10]:
        print(
            f"    {s['canonical_name']:40s} CV={s['seasonality_index']:.2f}  "
            f"peak={s['peak_season']} (month {s['peak_month']})",
            file=sys.stderr,
        )

    print(f"\n  Wrote {args.output_monthly}", file=sys.stderr)
    print(f"  Wrote {args.output_summary}", file=sys.stderr)
    print(f"  Wrote {args.output_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
