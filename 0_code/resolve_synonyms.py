#!/usr/bin/env python3
"""Resolve synonym and variant dish names to canonical forms.

Combines a curated synonym map (JSON) with automated fuzzy grouping based
on Jaccard similarity of lemma sets.

Usage:
    python 0_code/resolve_synonyms.py \
        --input categorized_dishes.csv \
        --synonym-map 0_code/synonym_map.json \
        --output dishes_resolved.csv \
        --groups synonym_groups.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path


def strip_accents(s: str) -> str:
    """Remove Hungarian diacritics for fuzzy comparison."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def lemma_set(text: str) -> set[str]:
    """Extract a set of meaningful tokens from text."""
    stopwords = {"vagy", "és", "egy", "a", "az", "van", "volt", "meg", "is"}
    tokens = re.findall(r"[a-záéíóöőúüű]+", text.lower())
    return {t for t in tokens if t not in stopwords and len(t) > 1}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_synonym_map(path: Path) -> dict[str, str]:
    """Load curated synonym map. Returns {variant_lower: canonical}."""
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    mapping: dict[str, str] = {}
    for group in data["groups"]:
        canonical = group["canonical"]
        mapping[canonical.lower()] = canonical
        for variant in group["variants"]:
            mapping[variant.lower()] = canonical
    return mapping


def find_curated_match(dish: str, curated: dict[str, str]) -> str | None:
    """Check if dish matches a curated synonym (substring match)."""
    low = dish.lower()
    # Exact match first
    if low in curated:
        return curated[low]
    # Check if any variant is contained in the dish name
    for variant, canonical in curated.items():
        if variant in low:
            return canonical
    return None


def build_auto_groups(
    dishes: list[dict], threshold: float = 0.85
) -> dict[str, str]:
    """Group dishes by Jaccard similarity on lemma sets.

    Returns {dish_name: canonical_name} for auto-detected groups.
    Only groups dishes that don't already have a curated match.
    """
    # Build lemma sets
    items = []
    for d in dishes:
        ls = lemma_set(d.get("lemmas", "") or d["dish_name"])
        if ls:
            items.append((d["dish_name"], ls, int(d.get("count", 0) or 0)))

    # Sort by count descending so the most frequent becomes canonical
    items.sort(key=lambda x: -x[2])

    groups: dict[str, str] = {}  # dish_name -> canonical
    canonicals: list[tuple[str, set[str]]] = []

    for name, ls, _count in items:
        matched = False
        for canon_name, canon_ls in canonicals:
            if jaccard(ls, canon_ls) >= threshold:
                groups[name] = canon_name
                matched = True
                break
        if not matched:
            canonicals.append((name, ls))
            groups[name] = name  # self-canonical

    # Only return entries where canonical differs from dish name
    return {k: v for k, v in groups.items() if k != v}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("categorized_dishes.csv"),
    )
    parser.add_argument(
        "--synonym-map", type=Path, default=Path("0_code/synonym_map.json"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("dishes_resolved.csv"),
    )
    parser.add_argument(
        "--groups", type=Path, default=Path("synonym_groups.csv"),
    )
    parser.add_argument(
        "--threshold", type=float, default=0.85,
        help="Jaccard similarity threshold for auto-grouping (default: 0.85).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    print("=" * 60, file=sys.stderr)
    print("Resolving synonyms and variants", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Load curated map
    curated = load_synonym_map(args.synonym_map)
    print(f"  Loaded {len(curated)} curated mappings", file=sys.stderr)

    # Read input
    with args.input.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        dishes = list(reader)
    print(f"  Read {len(dishes):,} dishes", file=sys.stderr)

    # Phase 1: curated matches
    curated_matches: dict[str, str] = {}
    for d in dishes:
        match = find_curated_match(d["dish_name"], curated)
        if match:
            curated_matches[d["dish_name"]] = match

    print(f"  Curated matches: {len(curated_matches):,}", file=sys.stderr)

    # Phase 2: auto-group the rest
    unmatched = [d for d in dishes if d["dish_name"] not in curated_matches]
    auto_matches = build_auto_groups(unmatched, threshold=args.threshold)
    print(f"  Auto-grouped matches: {len(auto_matches):,}", file=sys.stderr)

    # Combine
    all_matches = {**auto_matches, **curated_matches}  # curated takes priority

    # Write resolved dishes
    fieldnames = list(dishes[0].keys()) + ["canonical_name"]
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for d in dishes:
            d["canonical_name"] = all_matches.get(d["dish_name"], d["dish_name"])
            writer.writerow(d)

    # Write synonym groups
    group_rows = []
    for variant, canonical in sorted(all_matches.items()):
        match_type = "curated" if variant in curated_matches else "auto"
        group_rows.append({
            "canonical_name": canonical,
            "variant_name": variant,
            "match_type": match_type,
        })
    with args.groups.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["canonical_name", "variant_name", "match_type"])
        writer.writeheader()
        writer.writerows(group_rows)

    total_resolved = len(all_matches)
    print(f"\n  Total resolved: {total_resolved:,} variants -> canonical forms", file=sys.stderr)
    print(f"  Wrote {args.output} and {args.groups}", file=sys.stderr)


if __name__ == "__main__":
    main()
