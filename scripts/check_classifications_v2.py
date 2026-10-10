import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_FILE = (
    BASE_DIR
    / "output"
    / "a_classified_v2.csv"
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

        if row["word"].lower() not in TARGET_WORDS:
            continue

        print()
        print("=" * 70)

        print(
            "WORD:",
            row["word"]
        )

        print(
            "Classification:",
            row["classification"]
        )

        print(
            "Domains:",
            row["domains"]
        )

        print(
            "Primary domains:",
            row["primary_domains"]
        )

        print(
            "Secondary domains:",
            row["secondary_domains"]
        )