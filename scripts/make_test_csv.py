import gzip
import json
import csv
import re

INPUT_FILE = "../data/raw-wiktextract-data.jsonl.gz"
OUTPUT_FILE = "../output/a.csv"

TARGET_WORDS = {
    "transport",
    "important",
    "import",
    "export",
    "portable",
    "international",
    "impossible",
    "predict",
    "biology",
    "telephone"
}


def unique(items):
    result = []
    seen = set()

    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)

    return result


def get_definitions(senses):
    result = []

    for sense in senses or []:
        for gloss in sense.get("glosses", []):
            if gloss:
                result.append(gloss)

    return result


def get_examples(senses):
    result = []

    for sense in senses or []:
        for example in sense.get("examples", []):
            if isinstance(example, dict):
                text = example.get("text")

                if text:
                    result.append(text)

    return result


def get_words(items):
    result = []

    for item in items or []:
        if isinstance(item, dict):
            word = item.get("word")

            if word:
                result.append(word)

    return result


def get_korean_translations(data):
    result = []

    translations = []

    translations.extend(
        data.get("translations", [])
    )

    for sense in data.get("senses", []):
        translations.extend(
            sense.get("translations", [])
        )

    for item in translations:
        if not isinstance(item, dict):
            continue

        if item.get("lang_code") == "ko":
            word = item.get("word")

            if word:
                result.append(word)

    return result

def parse_morpheme(value, extra_meaning=""):
    term = value.split("<")[0].strip()

    # 가끔 언어 코드가 형태소처럼 들어가는 경우 제거
    if term.lower() in {"en", "english"}:
        return None

    meaning = ""

    # <t:...> 안의 뜻 찾기
    meaning_match = re.search(
        r"<t:(.*?)>",
        value
    )

    if meaning_match:
        meaning = meaning_match.group(1)

    # <t:...>가 없으면 <id:...> 사용
    if not meaning:
        id_match = re.search(
            r"<id:(.*?)>",
            value
        )

        if id_match:
            meaning = id_match.group(1)

    # telephone 같은 affix template의 pos1, pos2 정보 사용
    if not meaning and extra_meaning:
        meaning = extra_meaning

        quoted = re.search(
            r"meaning [‘'“\"](.+?)[’'”\"]",
            extra_meaning
        )

        if quoted:
            meaning = quoted.group(1)

    return {
        "text": term,
        "meaning": meaning
    }


def get_morphemes(templates):

    # 우선순위:
    # 1. surf
    # 2. affix
    # 3. af

    for wanted_name in [
        "surf",
        "affix",
        "af"
    ]:

        for template in templates or []:

            if template.get("name") != wanted_name:
                continue

            args = template.get("args", {})

            # 영어 단어 분석만 사용
            if args.get("1") != "en":
                continue

            result = []

            numeric_keys = []

            for key in args.keys():
                if key.isdigit() and int(key) >= 2:
                    numeric_keys.append(key)

            numeric_keys.sort(
                key=lambda x: int(x)
            )

            for key in numeric_keys:

                value = args[key]

                # affix template에서는
                # 2 → pos1
                # 3 → pos2
                pos_number = int(key) - 1

                extra_meaning = args.get(
                    f"pos{pos_number}",
                    ""
                )

                morpheme = parse_morpheme(
                    value,
                    extra_meaning
                )

                if morpheme is not None:
                    result.append(morpheme)

            if result:
                return result

    return []

def get_origin(templates):
    origins = []

    useful_templates = {
        "inh+",
        "inh",
        "bor+",
        "bor",
        "der"
    }

    for template in templates or []:

        if template.get("name") not in useful_templates:
            continue

        expansion = template.get("expansion")

        if expansion:
            origins.append(expansion)

    return unique(origins)[:5]


# 각 단어의 entry들을 여기에 저장
found_words = {
    word: []
    for word in TARGET_WORDS
}


print("Starting search...")


with gzip.open(
    INPUT_FILE,
    "rt",
    encoding="utf-8"
) as file:

    checked = 0

    for line in file:

        checked += 1

        if checked % 100000 == 0:
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

        found_words[word].append(data)


print("\nSearch finished!")


rows = []


for word in sorted(TARGET_WORDS):

    entries = found_words[word]

    parts_of_speech = []
    definitions = []
    definitions_ko = []
    synonyms = []
    related_words = []
    examples = []
    morphemes = []
    origin = []

    for data in entries:

        pos = data.get("pos")

        if pos:
            parts_of_speech.append(pos)

        definitions.extend(
            get_definitions(
                data.get("senses", [])
            )
        )

        definitions_ko.extend(
            get_korean_translations(data)
        )

        synonyms.extend(
            get_words(
                data.get("synonyms", [])
            )
        )

        related_words.extend(
            get_words(
                data.get("related", [])
            )
        )

        examples.extend(
            get_examples(
                data.get("senses", [])
            )
        )

        templates = data.get(
            "etymology_templates",
            []
        )

        if not morphemes:
            morphemes = get_morphemes(
                templates
            )

        origin.extend(
            get_origin(templates)
        )

    row = {
        "word": word,

        "parts_of_speech":
            json.dumps(
                unique(parts_of_speech),
                ensure_ascii=False
            ),

        "definitions_en":
            json.dumps(
                unique(definitions)[:5],
                ensure_ascii=False
            ),

        "definitions_ko":
            json.dumps(
                unique(definitions_ko)[:10],
                ensure_ascii=False
            ),

        "morphemes":
            json.dumps(
                morphemes,
                ensure_ascii=False
            ),

        "origin":
            json.dumps(
                unique(origin)[:5],
                ensure_ascii=False
            ),

        "synonyms":
            json.dumps(
                unique(synonyms)[:10],
                ensure_ascii=False
            ),

        "related_words":
            json.dumps(
                unique(related_words)[:15],
                ensure_ascii=False
            ),

        "examples":
            json.dumps(
                unique(examples)[:3],
                ensure_ascii=False
            ),

        "source":
            "Kaikki / Wiktionary"
    }

    rows.append(row)

    print(
        word,
        "entries:",
        len(entries),
        "| morphemes:",
        morphemes
    )


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=rows[0].keys()
    )

    writer.writeheader()
    writer.writerows(rows)


print("\nCSV CREATED!")
print("File:", OUTPUT_FILE)
print("Words:", len(rows))