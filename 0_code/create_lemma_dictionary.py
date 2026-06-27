#!/usr/bin/env python3
"""Create a dictionary/vocabulary from lemmatized dish names.

Extracts all unique lemmas from the processed CSV and creates a dictionary
with frequency counts and statistics.

Usage:
    python 0_code/create_lemma_dictionary.py \
        --input dishes_with_lemmas.csv \
        --output lemma_dictionary.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import string
import sys
from collections import Counter
from pathlib import Path


def is_punctuation_only(token: str) -> bool:
    """Check if token contains only punctuation."""
    return all(c in string.punctuation or c.isspace() for c in token)


def read_lemmas(csv_path: Path, filter_punctuation: bool = False) -> list[str]:
    """Read lemmas from CSV file."""
    print(f"Reading lemmas from: {csv_path.name}...", file=sys.stderr)
    lemmas_list: list[str] = []
    filtered_count = 0
    
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            lemmas_str = row.get("lemmas", "")
            if lemmas_str and lemmas_str != "dish_name":  # Skip header row
                # Split by spaces and filter empty strings
                lemmas = [lemma.strip() for lemma in lemmas_str.split() if lemma.strip()]
                
                # Filter punctuation if requested
                if filter_punctuation:
                    original_len = len(lemmas)
                    lemmas = [lemma for lemma in lemmas if not is_punctuation_only(lemma)]
                    filtered_count += original_len - len(lemmas)
                
                lemmas_list.extend(lemmas)
    
    print(f"  ✓ Extracted {len(lemmas_list):,} total lemmas", file=sys.stderr)
    if filter_punctuation and filtered_count > 0:
        print(f"  ✓ Filtered out {filtered_count:,} punctuation-only tokens", file=sys.stderr)
    return lemmas_list


def create_dictionary(lemmas_list: list[str]) -> dict[str, int]:
    """Create frequency dictionary from lemmas."""
    print(f"\nCreating lemma dictionary...", file=sys.stderr)
    counter = Counter(lemmas_list)
    dictionary = dict(counter.most_common())
    
    print(f"  ✓ Found {len(dictionary):,} unique lemmas", file=sys.stderr)
    print(f"  ✓ Most common: {list(dictionary.items())[:5]}", file=sys.stderr)
    
    return dictionary


def write_csv_dictionary(dictionary: dict[str, int], output_path: Path) -> None:
    """Write dictionary to CSV file."""
    print(f"\nWriting CSV dictionary to: {output_path.name}...", file=sys.stderr)
    
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["lemma", "frequency", "rank"])
        
        for rank, (lemma, frequency) in enumerate(dictionary.items(), 1):
            writer.writerow([lemma, frequency, rank])
    
    print(f"  ✓ Saved {len(dictionary):,} entries to {output_path}", file=sys.stderr)


def write_json_dictionary(dictionary: dict[str, int], output_path: Path) -> None:
    """Write dictionary to JSON file."""
    print(f"\nWriting JSON dictionary to: {output_path.name}...", file=sys.stderr)
    
    # Create a more structured format
    json_data = {
        "total_unique_lemmas": len(dictionary),
        "total_occurrences": sum(dictionary.values()),
        "dictionary": dictionary,
        "sorted_by_frequency": [
            {"lemma": lemma, "frequency": freq}
            for lemma, freq in dictionary.items()
        ]
    }
    
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(json_data, handle, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Saved dictionary to {output_path}", file=sys.stderr)


def print_statistics(dictionary: dict[str, int]) -> None:
    """Print statistics about the dictionary."""
    total_occurrences = sum(dictionary.values())
    frequencies = list(dictionary.values())
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("Dictionary Statistics:", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"  Total unique lemmas: {len(dictionary):,}", file=sys.stderr)
    print(f"  Total occurrences: {total_occurrences:,}", file=sys.stderr)
    print(f"  Average frequency: {total_occurrences / len(dictionary):.2f}", file=sys.stderr)
    print(f"  Most frequent lemma: {list(dictionary.items())[0]}", file=sys.stderr)
    print(f"  Least frequent lemma: {list(dictionary.items())[-1]}", file=sys.stderr)
    
    # Frequency distribution
    single_occurrence = sum(1 for f in frequencies if f == 1)
    print(f"  Lemmas appearing once: {single_occurrence:,} ({single_occurrence/len(dictionary)*100:.1f}%)", file=sys.stderr)
    
    # Top 10
    print(f"\n  Top 10 most frequent lemmas:", file=sys.stderr)
    for idx, (lemma, freq) in enumerate(list(dictionary.items())[:10], 1):
        print(f"    {idx:2d}. {lemma:20s} ({freq:,}x)", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("dishes_with_lemmas.csv"),
        help="Input CSV file with lemmas (default: dishes_with_lemmas.csv).",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        help="Output CSV file for dictionary (default: lemma_dictionary.csv).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Output JSON file for dictionary (optional).",
    )
    parser.add_argument(
        "--min-frequency",
        type=int,
        default=1,
        help="Minimum frequency threshold for including lemmas (default: 1).",
    )
    parser.add_argument(
        "--filter-punctuation",
        action="store_true",
        help="Filter out punctuation-only tokens from dictionary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    print("=" * 60, file=sys.stderr)
    print("Creating Lemma Dictionary", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Read lemmas
    lemmas_list = read_lemmas(args.input, filter_punctuation=args.filter_punctuation)

    if not lemmas_list:
        raise SystemExit("No lemmas found in input file")

    # Create dictionary
    dictionary = create_dictionary(lemmas_list)

    # Filter by minimum frequency if specified
    if args.min_frequency > 1:
        print(f"\nFiltering lemmas with frequency >= {args.min_frequency}...", file=sys.stderr)
        dictionary = {lemma: freq for lemma, freq in dictionary.items() if freq >= args.min_frequency}
        print(f"  ✓ Filtered to {len(dictionary):,} lemmas", file=sys.stderr)

    # Print statistics
    print_statistics(dictionary)

    # Write outputs
    if args.output_csv:
        write_csv_dictionary(dictionary, args.output_csv)
    else:
        default_csv = Path("lemma_dictionary.csv")
        write_csv_dictionary(dictionary, default_csv)

    if args.output_json:
        write_json_dictionary(dictionary, args.output_json)

    print("\n" + "=" * 60, file=sys.stderr)
    print("✓ Dictionary creation complete!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()

