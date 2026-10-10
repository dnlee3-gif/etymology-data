import gzip
import json

FILE_PATH = "../data/raw-wiktextract-data.jsonl.gz"

TARGET_WORDS = {
    "algorithm",
    "enzyme",
    "inflation",
    "lawsuit",
    "photosynthesis",
    "quarterback",
    "transport",
    "beautiful"
}

results = {
    word: []
    for word in TARGET_WORDS
}

print("Searching domain information...")

with gzip.open(
    FILE_PATH,
    "rt",
    encoding="utf-8"
) as file:

    checked = 0

    for line in file:

        checked += 1

        if checked % 500000 == 0:
            print(
                f"Searching... {checked:,} entries checked"
            )

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        if data.get("lang_code") != "en":
            continue

        word = data.get(
            "word",
            ""
        ).lower()

        if word not in TARGET_WORDS:
            continue

        entry = {
            "pos": data.get("pos"),
            "categories": data.get(
                "categories",
                []
            ),
            "senses": []
        }

        for sense in data.get(
            "senses",
            []
        ):

            entry["senses"].append({
                "glosses": sense.get(
                    "glosses",
                    []
                ),
                "topics": sense.get(
                    "topics",
                    []
                ),
                "tags": sense.get(
                    "tags",
                    []
                ),
                "categories": sense.get(
                    "categories",
                    []
                )
            })

        results[word].append(entry)


print("\nSEARCH FINISHED!")


for word in sorted(TARGET_WORDS):

    print("\n")
    print("=" * 70)
    print("WORD:", word)
    print("=" * 70)

    entries = results[word]

    print(
        "ENTRIES:",
        len(entries)
    )

    for entry in entries:

        print()
        print(
            "POS:",
            entry["pos"]
        )

        print(
            "TOP-LEVEL CATEGORIES:",
            entry["categories"][:20]
        )

        for i, sense in enumerate(
            entry["senses"],
            start=1
        ):

            print(
                f"\n  SENSE {i}"
            )

            print(
                "  Gloss:",
                sense["glosses"][:1]
            )

            print(
                "  Topics:",
                sense["topics"]
            )

            print(
                "  Tags:",
                sense["tags"]
            )

            print(
                "  Categories:",
                sense["categories"][:10]
            )