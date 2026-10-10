import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_FILE = (
    BASE_DIR
    / "output"
    / "a_classified.csv"
)

TARGET_WORDS = {
    "algorithm",
    "beautiful",
    "enzyme",
    "inflation",
    "lawsuit",
    "photosynthesis",
    "quarterback",
    "transport"
}


with open(
    CSV_FILE,
    "r",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        word = row["word"].lower()

        if word not in TARGET_WORDS:
            continue

        print()
        print("=" * 70)
        print("WORD:", word)
        print("Classification:", row["classification"])
        print("Domains:", row["domains"])
        print("Raw topics:", row["raw_topics"])
        print("Domain source:", row["domain_source"])