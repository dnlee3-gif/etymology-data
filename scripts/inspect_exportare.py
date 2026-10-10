import gzip
import csv

FILE_PATH = "../data/etymology.csv.gz"

TARGET_LANG = "Latin"
TARGET_TERM = "exportare"

print("Searching for Latin exportare...")

with gzip.open(
    FILE_PATH,
    "rt",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    found = 0

    for row in reader:

        if row.get("lang") != TARGET_LANG:
            continue

        if row.get("term") != TARGET_TERM:
            continue

        found += 1

        print("\n" + "=" * 70)
        print("ROW:", found)

        print("term:", row.get("term"))
        print("reltype:", row.get("reltype"))
        print("related_lang:", row.get("related_lang"))
        print("related_term:", row.get("related_term"))
        print("position:", row.get("position"))
        print("group_tag:", row.get("group_tag"))
        print("parent_tag:", row.get("parent_tag"))
        print("parent_position:", row.get("parent_position"))


print("\nFINISHED")
print("ROWS FOUND:", found)