import csv
import json

CSV_FILE = "../output/a.csv"


def parse_json_field(value):
    if not value:
        return []

    try:
        return json.loads(value)
    except:
        return []


print("Loading dictionary...")

dictionary = {}

with open(
    CSV_FILE,
    "r",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        dictionary[row["word"].lower()] = row


print(f"Loaded {len(dictionary):,} words.")
print()
print("Type a word to search.")
print("Type 'exit' to quit.")
print()


while True:

    query = input("Enter word: ").strip().lower()

    if query == "exit":
        print("Bye!")
        break

    if query not in dictionary:
        print()
        print("Word not found.")
        print()
        continue

    row = dictionary[query]

    parts_of_speech = parse_json_field(
        row["parts_of_speech"]
    )

    definitions_en = parse_json_field(
        row["definitions_en"]
    )

    definitions_ko = parse_json_field(
        row["definitions_ko"]
    )

    morphemes = parse_json_field(
        row["morphemes"]
    )

    origin = parse_json_field(
        row["origin"]
    )

    synonyms = parse_json_field(
        row["synonyms"]
    )

    related_words = parse_json_field(
        row["related_words"]
    )

    derived_words = parse_json_field(
        row["derived_words"]
    )

    examples = parse_json_field(
        row["examples"]
    )


    print()
    print("=" * 70)
    print("WORD:", row["word"])
    print("=" * 70)

    print(
        "Rank:",
        row["rank"]
    )

    print(
        "Part of speech:",
        ", ".join(parts_of_speech)
        if parts_of_speech
        else "N/A"
    )


    print()
    print("[English Definitions]")

    if definitions_en:

        for i, definition in enumerate(
            definitions_en,
            start=1
        ):
            print(
                f"{i}. {definition}"
            )

    else:
        print("N/A")


    print()
    print("[Korean Definitions]")

    if definitions_ko:

        for meaning in definitions_ko:
            print(
                "-",
                meaning
            )

    else:
        print("N/A")


    print()
    print("[Morphemes]")

    if morphemes:

        for morpheme in morphemes:

            text = morpheme.get(
                "text",
                ""
            )

            meaning = morpheme.get(
                "meaning",
                ""
            )

            language = morpheme.get(
                "language",
                ""
            )

            print(
                f"- {text}"
            )

            if meaning:
                print(
                    f"  Meaning: {meaning}"
                )

            if language:
                print(
                    f"  Language: {language}"
                )

    else:
        print("No structured morpheme data.")


    print(
        "Morpheme source:",
        row["morpheme_source"]
    )


    print()
    print("[Etymology Summary]")

    if row["etymology_summary"]:
        print(
            row["etymology_summary"]
        )
    else:
        print("N/A")


    print()
    print("[Origin]")

    if origin:

        for item in origin:
            print(
                "-",
                item
            )

    else:
        print("N/A")


    print()
    print("[Synonyms]")

    if synonyms:
        print(
            ", ".join(synonyms)
        )
    else:
        print("N/A")


    print()
    print("[Related Words]")

    if related_words:
        print(
            ", ".join(related_words)
        )
    else:
        print("N/A")


    print()
    print("[Derived Words]")

    if derived_words:
        print(
            ", ".join(derived_words)
        )
    else:
        print("N/A")


    print()
    print("[Examples]")

    if examples:

        for example in examples:
            print(
                "-",
                example
            )

    else:
        print("N/A")

    print()