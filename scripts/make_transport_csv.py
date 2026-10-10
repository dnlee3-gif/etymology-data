import gzip
import json
import csv
import re

INPUT_FILE = "../data/raw-wiktextract-data.jsonl.gz"
OUTPUT_FILE = "../output/a.csv"

TARGET_WORD = "transport"


# 중복을 제거하는 함수
def unique(items):
    result = []
    seen = set()

    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)

    return result


# definition 추출
def get_definitions(senses):
    definitions = []

    for sense in senses or []:
        for gloss in sense.get("glosses", []):
            if gloss:
                definitions.append(gloss)

    return definitions


# example sentence 추출
def get_examples(senses):
    examples = []

    for sense in senses or []:
        for example in sense.get("examples", []):
            if isinstance(example, dict):
                text = example.get("text")

                if text:
                    examples.append(text)

    return examples


# synonym / related / derived 같은 단어 목록 추출
def get_words(items):
    words = []

    for item in items or []:
        if isinstance(item, dict):
            word = item.get("word")

            if word:
                words.append(word)

    return words


# transport → trans + port 같은 구조 추출
def get_morphemes(etymology_templates):
    morphemes = []

    for template in etymology_templates or []:

        # 우리가 원하는 "surface analysis" 데이터
        if template.get("name") != "surf":
            continue

        args = template.get("args", {})

        # 2, 3, 4... 번째 요소가 형태소
        for key in sorted(args.keys()):
            if not key.isdigit():
                continue

            if int(key) < 2:
                continue

            value = args[key]

            # 예:
            # trans-<id:across, beyond><t:beyond, across, through>

            term = value.split("<")[0]

            meaning_match = re.search(
                r"<t:(.*?)>",
                value
            )

            meaning = ""

            if meaning_match:
                meaning = meaning_match.group(1)

            morphemes.append({
                "text": term,
                "meaning": meaning
            })

    return morphemes


# --------------------------------------------------
# 실제 데이터 읽기
# --------------------------------------------------

entries = []

print("Searching for:", TARGET_WORD)

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

        # 영어 entry만
        if data.get("lang_code") != "en":
            continue

        # transport만
        if data.get("word", "").lower() != TARGET_WORD:
            continue

        entries.append(data)


print()
print("Found entries:", len(entries))


# --------------------------------------------------
# 여러 품사 데이터를 하나로 합치기
# --------------------------------------------------

parts_of_speech = []
definitions = []
synonyms = []
related_words = []
derived_words = []
examples = []

etymology_text = ""
morphemes = []


for data in entries:

    pos = data.get("pos")

    if pos:
        parts_of_speech.append(pos)

    definitions.extend(
        get_definitions(
            data.get("senses", [])
        )
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

    derived_words.extend(
        get_words(
            data.get("derived", [])
        )
    )

    examples.extend(
        get_examples(
            data.get("senses", [])
        )
    )

    # 첫 번째 어원 설명만 저장
    if not etymology_text:
        etymology_text = data.get(
            "etymology_text",
            ""
        )

    # trans + port 정보 찾기
    if not morphemes:
        morphemes = get_morphemes(
            data.get(
                "etymology_templates",
                []
            )
        )


# 중복 제거
parts_of_speech = unique(parts_of_speech)
definitions = unique(definitions)
synonyms = unique(synonyms)
related_words = unique(related_words)
derived_words = unique(derived_words)
examples = unique(examples)


# 너무 많은 데이터는 잘라냄
definitions = definitions[:10]
synonyms = synonyms[:10]
related_words = related_words[:15]
derived_words = derived_words[:15]
examples = examples[:5]


# --------------------------------------------------
# CSV 저장
# --------------------------------------------------

row = {
    "word": TARGET_WORD,

    "parts_of_speech":
        json.dumps(
            parts_of_speech,
            ensure_ascii=False
        ),

    "definitions":
        json.dumps(
            definitions,
            ensure_ascii=False
        ),

    "etymology_text":
        etymology_text,

    "morphemes":
        json.dumps(
            morphemes,
            ensure_ascii=False
        ),

    "synonyms":
        json.dumps(
            synonyms,
            ensure_ascii=False
        ),

    "related_words":
        json.dumps(
            related_words,
            ensure_ascii=False
        ),

    "derived_words":
        json.dumps(
            derived_words,
            ensure_ascii=False
        ),

    "examples":
        json.dumps(
            examples,
            ensure_ascii=False
        ),

    "source":
        "Kaikki / Wiktionary"
}


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=row.keys()
    )

    writer.writeheader()
    writer.writerow(row)


print()
print("CSV CREATED!")
print("File:", OUTPUT_FILE)

print()
print("MORPHEMES:")
print(morphemes)