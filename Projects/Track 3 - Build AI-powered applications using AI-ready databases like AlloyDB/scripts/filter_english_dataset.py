#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Filter IT support dataset to English-only rows")
    parser.add_argument("--source", required=True, help="Path to source CSV")
    parser.add_argument("--target", required=True, help="Path to target CSV")
    args = parser.parse_args()

    src = Path(args.source)
    dst = Path(args.target)

    if not src.exists():
        raise FileNotFoundError(f"Source dataset not found: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)

    with src.open("r", encoding="utf-8", newline="") as fsrc:
        reader = csv.DictReader(fsrc)
        fieldnames = reader.fieldnames or []

        with dst.open("w", encoding="utf-8", newline="") as fdst:
            writer = csv.DictWriter(fdst, fieldnames=fieldnames)
            writer.writeheader()

            count = 0
            for row in reader:
                if (row.get("language") or "").strip().lower() == "en":
                    writer.writerow(row)
                    count += 1

    print(f"Wrote cleaned dataset: {dst}")
    print(f"English rows: {count}")


if __name__ == "__main__":
    main()
