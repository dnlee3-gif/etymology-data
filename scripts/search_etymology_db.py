import gzip
import csv

FILE_PATH = "../data/etymology.csv.gz"

TARGET_WORDS = {
    "biology",
    "export",
    "import",
    "predict",
    "telephone",
    "transport"
}

results = {
    word: []
    for word in TARGET_WORDS
}

print("Searching etymology-db...")

with gzip.open(
    FILE_PATH,
    "rt",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    checked = 0

    for row in reader:
        checked += 1

        if checked % 100000 == 0:
            print(
                f"Searching... {checked:,} rows checked"
            )

        lang = row.get("lang", "")
        term = row.get("term", "").lower()

        # 영어 단어만
        if lang != "English":
            continue

        if term not in TARGET_WORDS:
            continue

        results[term].append(row)


print("\nSEARCH FINISHED!")


for word in sorted(TARGET_WORDS):

    rows = results[word]

    print("\n")
    print("=" * 70)
    print("WORD:", word)
    print("ROWS FOUND:", len(rows))
    print("=" * 70)

    if not rows:
        print("NO DATA")
        continue

    for row in rows:

        print(
            "reltype:",
            row.get("reltype")
        )

        print(
            "related_lang:",
            row.get("related_lang")
        )

        print(
            "related_term:",
            row.get("related_term")
        )

        print(
            "position:",
            row.get("position")
        )

        print(
            "group_tag:",
            row.get("group_tag")
        )

        print(
            "parent_tag:",
            row.get("parent_tag")
        )

        print(
            "parent_position:",
            row.get("parent_position")
        )

        print("-" * 50)