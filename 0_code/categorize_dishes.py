#!/usr/bin/env python3
"""Categorize Hungarian dishes by course type, protein, and cooking method.

Uses rule-based keyword matching on both original dish names and lemmatized
forms to assign multi-label categories.

Usage:
    python 0_code/categorize_dishes.py \
        --input dishes_with_lemmas.csv \
        --output categorized_dishes.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Keyword dictionaries – matched against lowercased dish_name + lemmas
# ---------------------------------------------------------------------------

COURSE_KEYWORDS: dict[str, list[str]] = {
    "leves": [
        "leves", "krémleves", "gulyásleves", "raguleves", "bableves",
        "csontleves", "gyümölcsleves", "húsleves", "zöldségleves",
        "paradicsomleves", "tojásleves", "lebbencsleves", "tarhonyaleves",
        "palócleves", "brokkoli krémleves", "gombaleves", "babgulyás",
        "erőleves", "meggyleves", "meggy leves", "almaleves",
        "grízgaluskaleves", "lebbencs", "karfiol leves", "karfiolleves",
        "babgulyás", "borsóleves", "lencsegulyás", "burgonyaleves",
        "kukoricakrémleves", "pacalleves",
    ],
    "desszert": [
        "sütemény", "torta", "palacsinta", "rétes", "máglyarakás",
        "gombóc", "bukta", "kalács", "krémes", "fagylalt", "tiramisu",
        "brownie", "mousse", "puding", "strudel",
    ],
    "saláta": [
        "saláta tál", "salátás tál", "saláta tálak",
    ],
    "főzelék": [
        "főzelék",
    ],
    "köret": [
        # standalone sides – only matched when no protein is found
    ],
}

PROTEIN_KEYWORDS: dict[str, list[str]] = {
    "csirke": [
        "csirkemell", "csirkecomb", "csirkeszárny", "csirkemáj", "csirke",
        "pulykamell", "pulyka", "jérce", "jércemell", "csibe",
        "szárny", "baromfi",
    ],
    "sertés": [
        "sertés", "sertésszelet", "sertéskaraj", "karaj", "oldalas",
        "sertésborda", "sertésmáj", "malac", "tarja", "dagadó",
        "csülök", "sonka", "szalonna", "kolbász", "virsli", "hurka",
        "disznó", "disznótoros", "bacon",
    ],
    "marha": [
        "marha", "marhahús", "borjú", "gulyás",
    ],
    "hal": [
        "halfilé", "hal ", "pangasius", "lazac", "hekk", "harcsa",
        "ponty", "tőkehal", "halászlé", "busatörzs",
    ],
}

COOKING_METHOD_KEYWORDS: dict[str, list[str]] = {
    "rántott": ["rántott", "rántva"],
    "sült": ["sült", "sütve", "kisütött"],
    "párolt": ["párolt"],
    "töltött": ["töltött"],
    "grillezett": ["grillezett", "grill", "roston"],
    "rakott": ["rakott"],
    "főtt": ["főtt", "főzött"],
    "pirított": ["pirított"],
    "pörkölt": ["pörkölt"],
    "tepsis": ["tepsis"],
    "bundás": ["bundás"],
    "fasírozott": ["fasírozott", "fasírt"],
    "párizsi": ["párizsi"],
    "bécsi": ["bécsi"],
    "milánói": ["milánói"],
}

SIDE_KEYWORDS: list[str] = [
    "burgonya", "rizs", "rizibizi", "galuska", "krokett",
    "hasábburgonya", "sültburgonya", "törtburgonya", "burgonyapüré",
    "krumplipüré", "steak burgonya", "bulgur", "tarhonya",
    "petrezselymes burgonya", "héjában sült burgonya",
]


def _match(text: str, keywords: list[str]) -> bool:
    """Check if any keyword appears in text (case-insensitive)."""
    low = text.lower()
    return any(kw in low for kw in keywords)


def categorize_course(dish: str, lemmas: str) -> str:
    """Return course type for a dish."""
    combined = f"{dish} {lemmas}".lower()
    for course, kws in COURSE_KEYWORDS.items():
        if _match(combined, kws):
            return course
    # Default: if it has protein or cooking method, it's a main course
    return "főétel"


def categorize_protein(dish: str, lemmas: str) -> str:
    """Return protein type(s), comma-separated."""
    combined = f"{dish} {lemmas}".lower()
    found = [p for p, kws in PROTEIN_KEYWORDS.items() if _match(combined, kws)]
    if found:
        return ",".join(found)
    # Check for vegetarian indicators
    veg_kws = [
        "sajt", "gomba", "túró", "tojás", "zöldség", "karfiol",
        "brokkoli", "padlizsán", "cukkini", "lecsó", "bab ",
        "lencse", "krumpli", "tök",
    ]
    if _match(combined, veg_kws):
        return "vegetáriánus"
    return ""


def categorize_method(dish: str, lemmas: str) -> str:
    """Return cooking method(s), comma-separated."""
    combined = f"{dish} {lemmas}".lower()
    found = [m for m, kws in COOKING_METHOD_KEYWORDS.items() if _match(combined, kws)]
    return ",".join(found) if found else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("dishes_with_lemmas.csv"),
        help="Input CSV with dish_name, score, lemmas columns.",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("categorized_dishes.csv"),
        help="Output CSV with added category columns.",
    )
    parser.add_argument(
        "--stats", type=Path, default=Path("category_stats.json"),
        help="Output JSON with category distribution stats.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    print("=" * 60, file=sys.stderr)
    print("Categorizing dishes", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    rows_out: list[dict] = []
    skipped = 0

    with args.input.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            dish = row.get("dish_name", "")
            lemmas = row.get("lemmas", "")
            score = row.get("score", "0")
            # skip duplicate header row
            if dish == "dish_name":
                continue
            if not dish.strip():
                skipped += 1
                continue

            course = categorize_course(dish, lemmas)
            protein = categorize_protein(dish, lemmas)
            method = categorize_method(dish, lemmas)

            rows_out.append({
                "dish_name": dish,
                "count": score,
                "lemmas": lemmas,
                "course": course,
                "protein": protein,
                "cooking_method": method,
            })

    # Write output
    fieldnames = ["dish_name", "count", "lemmas", "course", "protein", "cooking_method"]
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"  Categorized {len(rows_out):,} dishes (skipped {skipped})", file=sys.stderr)

    # Compute stats
    from collections import Counter
    course_counts = Counter(r["course"] for r in rows_out)
    protein_counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()
    for r in rows_out:
        for p in r["protein"].split(","):
            if p:
                protein_counts[p] += 1
        for m in r["cooking_method"].split(","):
            if m:
                method_counts[m] += 1

    stats = {
        "total_dishes": len(rows_out),
        "course_distribution": dict(course_counts.most_common()),
        "protein_distribution": dict(protein_counts.most_common()),
        "cooking_method_distribution": dict(method_counts.most_common()),
    }
    with args.stats.open("w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)

    print(f"\n  Course types:", file=sys.stderr)
    for c, n in course_counts.most_common():
        print(f"    {c:15s} {n:,}", file=sys.stderr)
    print(f"\n  Proteins:", file=sys.stderr)
    for p, n in protein_counts.most_common():
        print(f"    {p:15s} {n:,}", file=sys.stderr)
    print(f"\n  Cooking methods:", file=sys.stderr)
    for m, n in method_counts.most_common():
        print(f"    {m:15s} {n:,}", file=sys.stderr)

    print(f"\n  Wrote {args.output} and {args.stats}", file=sys.stderr)


if __name__ == "__main__":
    main()
