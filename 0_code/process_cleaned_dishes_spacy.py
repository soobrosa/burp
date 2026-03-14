#!/usr/bin/env python3
"""Analyse dish names from `cleaned_dishes.csv` with a Hungarian spaCy model.

Usage:
    python 0_code/process_cleaned_dishes_spacy.py \
        --csv /Users/soobrosa/Documents/github/burp/cleaned_dishes.csv

Provide ``--output`` to write a CSV with lemmas instead of printing tokens.

Uses HuSpaCy (compatible with spaCy 3.x) for Hungarian language processing.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

try:
    import huspacy
    HUSPACY_AVAILABLE = True
except ImportError:
    HUSPACY_AVAILABLE = False

import spacy
from tqdm import tqdm


DEFAULT_MODEL = "huspacy"  # Use HuSpaCy by default


def load_pipeline(model: str) -> spacy.Language:
    print(f"Loading Hungarian NLP model...", file=sys.stderr)
    # Try HuSpaCy first if available and requested
    if model == "huspacy" or model == DEFAULT_MODEL:
        if HUSPACY_AVAILABLE:
            try:
                print("  → Loading HuSpaCy model (hu_core_news_lg)...", file=sys.stderr)
                nlp = huspacy.load()
                print(f"  ✓ Model loaded successfully: {nlp.meta.get('name', 'hu_core_news_lg')}", file=sys.stderr)
                return nlp
            except Exception as exc:
                print(
                    f"  ⚠ Warning: HuSpaCy model not downloaded. "
                    f"Run: python -c 'import huspacy; huspacy.download()'\n"
                    f"  → Falling back to blank Hungarian model.",
                    file=sys.stderr,
                )
                return spacy.blank("hu")
        else:
            print(
                "  ⚠ Warning: huspacy not installed. Install with: pip install huspacy\n"
                "  → Falling back to blank Hungarian model.",
                file=sys.stderr,
            )
            return spacy.blank("hu")
    
    # Try loading as a regular spaCy model
    try:
        print(f"  → Loading spaCy model: {model}...", file=sys.stderr)
        nlp = spacy.load(model)
        print(f"  ✓ Model loaded successfully", file=sys.stderr)
        return nlp
    except OSError as exc:
        # Try fallback to blank Hungarian model if the full model isn't available
        if "hu" in model.lower():
            try:
                print(
                    f"  ⚠ Warning: '{model}' not found, falling back to blank Hungarian model",
                    file=sys.stderr,
                )
                return spacy.blank("hu")
            except Exception:
                pass
        message = (
            f"spaCy model '{model}' is not installed. "
            "Install it once with: python -m spacy download "
            f"{model}\nOriginal error: {exc}"
        )
        raise SystemExit(message) from exc


def read_rows(csv_path: Path) -> list[tuple[str, str]]:
    print(f"Reading CSV file: {csv_path.name}...", file=sys.stderr)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = [(row[0], row[1]) for row in reader if row]
    print(f"  ✓ Loaded {len(rows):,} rows", file=sys.stderr)
    return rows


def analyse_rows(rows: list[tuple[str, str]], nlp: spacy.Language) -> list[dict[str, str]]:
    print(f"\nProcessing dish names with Hungarian NLP model...", file=sys.stderr)
    results: list[dict[str, str]] = []
    examples: list[tuple[str, str]] = []
    
    # Process with progress bar
    for idx, (dish_name, score) in enumerate(tqdm(rows, desc="  Processing", unit=" dishes", file=sys.stderr), 1):
        doc = nlp(dish_name)
        lemmas = " ".join(token.lemma_ for token in doc)
        results.append(
            {
                "dish_name": dish_name,
                "score": score,
                "lemmas": lemmas,
            }
        )
        
        # Collect first few examples
        if idx <= 3:
            examples.append((dish_name, lemmas))
    
    # Show examples after progress bar
    if examples:
        print("\n  Examples:", file=sys.stderr)
        for idx, (dish_name, lemmas) in enumerate(examples, 1):
            print(f"    {idx}. '{dish_name}' → '{lemmas}'", file=sys.stderr)
    
    print(f"\n  ✓ Processed {len(results):,} dish names", file=sys.stderr)
    return results


def write_output(results: list[dict[str, str]], output_path: Path) -> None:
    print(f"\nWriting results to: {output_path.name}...", file=sys.stderr)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dish_name", "score", "lemmas"])
        writer.writeheader()
        writer.writerows(results)
    print(f"  ✓ Saved {len(results):,} rows to {output_path}", file=sys.stderr)


def print_results(results: list[dict[str, str]]) -> None:
    for row in results:
        print(row["dish_name"])  # noqa: T201
        print(f"  score: {row['score']}")  # noqa: T201
        print(f"  lemmas: {row['lemmas']}")  # noqa: T201
        print()  # noqa: T201


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("cleaned_dishes.csv"),
        help="Path to the input CSV (default: cleaned_dishes.csv in repo root).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"spaCy pipeline to load (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write a CSV with lemmas added.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.csv.exists():
        raise SystemExit(f"Input CSV not found: {args.csv}")

    print("=" * 60, file=sys.stderr)
    print("Hungarian Dish Name NLP Processing", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    nlp = load_pipeline(args.model)
    print(file=sys.stderr)

    rows = read_rows(args.csv)
    if not rows:
        raise SystemExit(f"No rows read from {args.csv}")
    print(file=sys.stderr)

    analysed = analyse_rows(rows, nlp)

    if args.output:
        write_output(analysed, args.output)
        print("\n" + "=" * 60, file=sys.stderr)
        print("✓ Processing complete!", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
    else:
        print("\n" + "=" * 60, file=sys.stderr)
        print("Results:", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print_results(analysed)


if __name__ == "__main__":
    main()

