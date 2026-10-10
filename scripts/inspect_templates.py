import gzip
import json

INPUT_FILE = "../data/raw-wiktextract-data.jsonl.gz"

TARGET_WORDS = {
    "biology",
    "export",
    "import",
    "important",
    "impossible",
    "international",
    "portable",
    "predict",
    "telephone",
    "transport"
}


with gzip.open(
    INPUT_FILE,
    "rt",
    encoding="utf-8"
) as file:

    for line in file:

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        if data.get("lang_code") != "en":
            continue

        word = data.get("word", "").lower()

        if word not in TARGET_WORDS:
            continue

        print("\n")
        print("=" * 70)
        print("WORD:", word)
        print("POS:", data.get("pos"))
        print("=" * 70)

        print("\nETYMOLOGY TEXT:")
        print(data.get("etymology_text", "NONE"))

        print("\nTEMPLATES:")

        templates = data.get(
            "etymology_templates",
            []
        )

        if not templates:
            print("NO TEMPLATES")

        for template in templates:

            print("\nTemplate name:")
            print(template.get("name"))

            print("Arguments:")
            print(template.get("args"))

            print("Expansion:")
            print(template.get("expansion"))