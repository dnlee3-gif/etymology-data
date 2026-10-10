import gzip
import json

FILE_PATH = "../data/raw-wiktextract-data.jsonl.gz"

TARGET_WORD = "transport"


def get_words(items):
    result = []

    for item in items or []:
        if isinstance(item, dict):
            word = item.get("word")

            if word:
                result.append(word)

    return result


def get_definitions(senses):
    definitions = []

    for sense in senses or []:
        for gloss in sense.get("glosses", []):
            if gloss:
                definitions.append(gloss)

    return definitions


def get_examples(senses):
    examples = []

    for sense in senses or []:
        for example in sense.get("examples", []):
            if isinstance(example, dict):
                text = example.get("text")

                if text:
                    examples.append(text)

    return examples


found = 0
checked = 0

with gzip.open(
    FILE_PATH,
    "rt",
    encoding="utf-8"
) as file:

    for line in file:
        checked += 1

        if checked % 100000 == 0:
            print(f"Searching... {checked:,} entries checked")

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        if data.get("lang_code") != "en":
            continue

        if data.get("word", "").lower() != TARGET_WORD.lower():
            continue

        found += 1

        print("\n" + "=" * 60)
        print("FOUND:", TARGET_WORD)
        print("=" * 60)

        print("\nWORD:")
        print(data.get("word"))

        print("\nPART OF SPEECH:")
        print(data.get("pos"))

        print("\nDEFINITIONS:")
        for definition in get_definitions(data.get("senses", []))[:5]:
            print("-", definition)

        print("\nETYMOLOGY:")
        print(
            data.get("etymology_text")
            or "No etymology information"
        )

        print("\nSYNONYMS:")
        print(get_words(data.get("synonyms"))[:10])

        print("\nRELATED WORDS:")
        print(get_words(data.get("related"))[:10])

        print("\nDERIVED WORDS:")
        print(get_words(data.get("derived"))[:10])

        print("\nEXAMPLES:")
        for example in get_examples(data.get("senses", []))[:3]:
            print("-", example)

        print("\nETYMOLOGY LINKS:")
        print(data.get("etymology_links", []))

        print("\nETYMOLOGY TEMPLATES:")
        for template in data.get("etymology_templates", []):
            print(template)


print("\nSearch finished.")
print("Number of matching entries:", found)