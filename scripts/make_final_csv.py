import gzip
import json
import csv
import re
import os

from wordfreq import top_n_list


KAIKKI_FILE = "../data/raw-wiktextract-data.jsonl.gz"
ETYMOLOGY_DB_FILE = "../data/etymology.csv.gz"

OUTPUT_FILE = "../output/a.csv"

TARGET_COUNT = 10000


# ============================================================
# 기본 함수
# ============================================================

def unique(items):
    result = []
    seen = set()

    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)

    return result


def add_unique(target_list, new_items, limit=None):
    existing = set(target_list)

    for item in new_items:
        if not item:
            continue

        if item not in existing:
            target_list.append(item)
            existing.add(item)

        if limit and len(target_list) >= limit:
            break


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

            if not isinstance(example, dict):
                continue

            text = example.get("text")

            if text:
                result.append(text)

    return result


def get_words(items):
    result = []

    for item in items or []:

        if not isinstance(item, dict):
            continue

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


# ============================================================
# 너무 긴 Kaikki 어원 설명 정리
# ============================================================

def compact_etymology(text):

    if not text:
        return ""

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    # Etymology tree가 길게 붙는 경우
    # 실제 설명 문장을 뒤에서부터 찾음
    if lines[0].lower() == "etymology tree":

        keywords = [
            "from ",
            "inherited from",
            "borrowed from",
            "by surface analysis",
            "equivalent to",
            "derived from"
        ]

        for line in reversed(lines):

            lower = line.lower()

            if any(
                keyword in lower
                for keyword in keywords
            ):
                return line[:1500]

        return lines[-1][:1500]

    # 일반 설명은 한 줄로 정리
    result = " ".join(lines)

    return result[:1500]


# ============================================================
# Kaikki 형태소 분석
# ============================================================

def parse_morpheme(value, extra_meaning=""):

    term = value.split("<")[0].strip()

    if term.lower() in {
        "en",
        "english"
    }:
        return None

    meaning = ""

    meaning_match = re.search(
        r"<t:(.*?)>",
        value
    )

    if meaning_match:
        meaning = meaning_match.group(1)

    if not meaning:

        id_match = re.search(
            r"<id:(.*?)>",
            value
        )

        if id_match:
            meaning = id_match.group(1)

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
        "meaning": meaning,
        "language": "English"
    }


def get_kaikki_morphemes(templates):

    # 신뢰도 순서
    for wanted_name in [
        "surf",
        "affix",
        "af"
    ]:

        for template in templates or []:

            if template.get("name") != wanted_name:
                continue

            args = template.get(
                "args",
                {}
            )

            if args.get("1") != "en":
                continue

            numeric_keys = []

            for key in args.keys():

                if (
                    key.isdigit()
                    and int(key) >= 2
                ):
                    numeric_keys.append(key)

            numeric_keys.sort(
                key=lambda x: int(x)
            )

            result = []

            for key in numeric_keys:

                value = args[key]

                pos_number = (
                    int(key) - 1
                )

                extra_meaning = args.get(
                    f"pos{pos_number}",
                    ""
                )

                morpheme = parse_morpheme(
                    value,
                    extra_meaning
                )

                if morpheme:
                    result.append(morpheme)

            # 형태소가 최소 2개는 있어야
            # 실제 분해라고 판단
            if len(result) >= 2:
                return result

    return []


def get_kaikki_origin(templates):

    result = []

    useful = {
        "inh",
        "inh+",
        "bor",
        "bor+",
        "der"
    }

    for template in templates or []:

        if template.get("name") not in useful:
            continue

        expansion = template.get(
            "expansion"
        )

        if expansion:
            result.append(expansion)

    return unique(result)[:8]


# ============================================================
# etymology-db 처리
# ============================================================

def safe_number(value):

    try:
        return int(value)

    except:
        return 999


def get_db_morphemes(rows):

    # --------------------------------------------------------
    # 1. biology → bio + logy
    # --------------------------------------------------------

    confixes = []

    for row in rows:

        if (
            row.get("reltype") == "has_confix"
            and
            row.get("related_lang") == "English"
            and
            row.get("related_term")
        ):

            confixes.append({
                "text":
                    row.get("related_term"),

                "meaning":
                    "",

                "language":
                    "English",

                "_position":
                    safe_number(
                        row.get("position")
                    )
            })

    if len(confixes) >= 2:

        confixes.sort(
            key=lambda x:
            x["_position"]
        )

        for item in confixes:
            item.pop("_position", None)

        return confixes


    # --------------------------------------------------------
    # 2. 직접 prefix / suffix 관계
    # --------------------------------------------------------

    direct = []

    useful_direct = {
        "has_prefix",
        "has_suffix",
        "has_prefix_with_root",
        "has_suffix_with_root"
    }

    for row in rows:

        if (
            row.get("reltype")
            in useful_direct
            and
            row.get("related_term")
        ):

            direct.append({
                "text":
                    row.get("related_term"),

                "meaning":
                    "",

                "language":
                    row.get(
                        "related_lang",
                        ""
                    ),

                "_position":
                    safe_number(
                        row.get("position")
                    )
            })

    if len(direct) >= 2:

        direct.sort(
            key=lambda x:
            x["_position"]
        )

        for item in direct:
            item.pop("_position", None)

        return direct


    # --------------------------------------------------------
    # 3. group_affix_root
    # import → in + portō
    # predict → prae- + dīcō
    # --------------------------------------------------------

    group_tags = []

    for row in rows:

        if (
            row.get("reltype")
            == "group_affix_root"
        ):

            tag = row.get(
                "group_tag"
            )

            if tag:
                group_tags.append(tag)


    for tag in group_tags:

        children = []

        for row in rows:

            if row.get("parent_tag") != tag:
                continue

            related_term = row.get(
                "related_term"
            )

            if not related_term:
                continue

            children.append({
                "text":
                    related_term,

                "meaning":
                    "",

                "language":
                    row.get(
                        "related_lang",
                        ""
                    ),

                "_position":
                    safe_number(
                        row.get(
                            "parent_position"
                        )
                    )
            })

        if len(children) >= 2:

            children.sort(
                key=lambda x:
                x["_position"]
            )

            for item in children:
                item.pop(
                    "_position",
                    None
                )

            return children

    return []


def get_db_origin(rows):

    result = []

    useful = {
        "borrowed_from",
        "derived_from",
        "inherited_from"
    }

    for row in rows:

        if (
            row.get("reltype")
            not in useful
        ):
            continue

        lang = row.get(
            "related_lang",
            ""
        )

        term = row.get(
            "related_term",
            ""
        )

        if not term:
            continue

        if lang:
            result.append(
                f"{lang} {term}"
            )

        else:
            result.append(term)

    return unique(result)[:8]


# ============================================================
# 1. 자주 쓰이는 영어 단어 10,000개 생성
# ============================================================

print("=" * 70)
print("STEP 1/4")
print("Creating frequent English word list...")
print("=" * 70)

raw_words = top_n_list(
    "en",
    30000
)

target_words = []
seen = set()

for word in raw_words:

    word = word.lower().strip()

    # 영어 알파벳으로만 된 단어
    if not word.isascii():
        continue

    if not word.isalpha():
        continue

    if word in seen:
        continue

    seen.add(word)
    target_words.append(word)

    if len(target_words) == TARGET_COUNT:
        break


if len(target_words) < TARGET_COUNT:
    raise RuntimeError(
        "Could not collect 10,000 target words."
    )


target_set = set(target_words)

rank_map = {
    word: rank
    for rank, word
    in enumerate(
        target_words,
        start=1
    )
}


print(
    "Target words:",
    len(target_words)
)

print(
    "First 20:",
    target_words[:20]
)


# ============================================================
# 각 단어 저장 공간
# ============================================================

word_data = {}

for word in target_words:

    word_data[word] = {
        "parts_of_speech": [],
        "definitions_en": [],
        "definitions_ko": [],
        "etymology_summary": "",
        "kaikki_morphemes": [],
        "kaikki_origin": [],
        "synonyms": [],
        "related_words": [],
        "derived_words": [],
        "examples": [],
        "kaikki_found": False
    }


# ============================================================
# 2. Kaikki 읽기
# ============================================================

print()
print("=" * 70)
print("STEP 2/4")
print("Scanning Kaikki...")
print("=" * 70)


with gzip.open(
    KAIKKI_FILE,
    "rt",
    encoding="utf-8"
) as file:

    checked = 0
    matched = 0

    for line in file:

        checked += 1

        if checked % 500000 == 0:

            print(
                f"Kaikki: "
                f"{checked:,} entries checked"
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

        if word not in target_set:
            continue

        # 고유명사 항목은 제외
        if data.get("pos") == "name":
            continue

        record = word_data[word]

        if not record["kaikki_found"]:
            matched += 1

        record["kaikki_found"] = True

        pos = data.get("pos")

        if pos:
            add_unique(
                record["parts_of_speech"],
                [pos]
            )

        add_unique(
            record["definitions_en"],
            get_definitions(
                data.get(
                    "senses",
                    []
                )
            ),
            limit=8
        )

        add_unique(
            record["definitions_ko"],
            get_korean_translations(data),
            limit=10
        )

        add_unique(
            record["synonyms"],
            get_words(
                data.get(
                    "synonyms",
                    []
                )
            ),
            limit=10
        )

        add_unique(
            record["related_words"],
            get_words(
                data.get(
                    "related",
                    []
                )
            ),
            limit=15
        )

        add_unique(
            record["derived_words"],
            get_words(
                data.get(
                    "derived",
                    []
                )
            ),
            limit=15
        )

        add_unique(
            record["examples"],
            get_examples(
                data.get(
                    "senses",
                    []
                )
            ),
            limit=3
        )


        # 어원 설명
        if not record["etymology_summary"]:

            ety = compact_etymology(
                data.get(
                    "etymology_text",
                    ""
                )
            )

            if ety:
                record[
                    "etymology_summary"
                ] = ety


        templates = data.get(
            "etymology_templates",
            []
        )


        # 형태소
        if not record["kaikki_morphemes"]:

            morphemes = (
                get_kaikki_morphemes(
                    templates
                )
            )

            if morphemes:

                record[
                    "kaikki_morphemes"
                ] = morphemes


        # origin
        add_unique(
            record["kaikki_origin"],
            get_kaikki_origin(
                templates
            ),
            limit=8
        )


print()
print(
    "Kaikki words found:",
    matched,
    "/",
    TARGET_COUNT
)


# ============================================================
# 3. etymology-db 읽기
# ============================================================

print()
print("=" * 70)
print("STEP 3/4")
print("Scanning etymology-db...")
print("=" * 70)


db_entries = {
    word: []
    for word in target_words
}


with gzip.open(
    ETYMOLOGY_DB_FILE,
    "rt",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    checked = 0

    for row in reader:

        checked += 1

        if checked % 500000 == 0:

            print(
                f"etymology-db: "
                f"{checked:,} rows checked"
            )

        if row.get("lang") != "English":
            continue

        word = row.get(
            "term",
            ""
        ).lower()

        if word not in target_set:
            continue

        # 필요한 정보만 저장
        db_entries[word].append({
            "reltype":
                row.get("reltype", ""),

            "related_lang":
                row.get(
                    "related_lang",
                    ""
                ),

            "related_term":
                row.get(
                    "related_term",
                    ""
                ),

            "position":
                row.get(
                    "position",
                    ""
                ),

            "group_tag":
                row.get(
                    "group_tag",
                    ""
                ),

            "parent_tag":
                row.get(
                    "parent_tag",
                    ""
                ),

            "parent_position":
                row.get(
                    "parent_position",
                    ""
                )
        })


# ============================================================
# 4. 최종 CSV 생성
# ============================================================

print()
print("=" * 70)
print("STEP 4/4")
print("Creating final CSV...")
print("=" * 70)


rows_to_save = []

kaikki_morpheme_count = 0
db_morpheme_count = 0
missing_morpheme_count = 0
missing_kaikki_count = 0


for word in target_words:

    record = word_data[word]

    db_rows = db_entries[word]


    # etymology-db 형태소
    db_morphemes = (
        get_db_morphemes(
            db_rows
        )
    )


    # Kaikki 우선
    if record["kaikki_morphemes"]:

        final_morphemes = (
            record[
                "kaikki_morphemes"
            ]
        )

        morpheme_source = "Kaikki"

        kaikki_morpheme_count += 1


    elif db_morphemes:

        final_morphemes = (
            db_morphemes
        )

        morpheme_source = (
            "etymology-db"
        )

        db_morpheme_count += 1


    else:

        final_morphemes = []

        morpheme_source = "none"

        missing_morpheme_count += 1


    final_origin = unique(
        record["kaikki_origin"]
        +
        get_db_origin(
            db_rows
        )
    )[:8]


    has_etymology = bool(
        final_morphemes
        or final_origin
        or record["etymology_summary"]
    )


    if not record["kaikki_found"]:
        missing_kaikki_count += 1


    row = {

        "rank":
            rank_map[word],

        "word":
            word,

        "parts_of_speech":
            json.dumps(
                record[
                    "parts_of_speech"
                ],
                ensure_ascii=False
            ),

        "definitions_en":
            json.dumps(
                record[
                    "definitions_en"
                ][:5],
                ensure_ascii=False
            ),

        "definitions_ko":
            json.dumps(
                record[
                    "definitions_ko"
                ][:10],
                ensure_ascii=False
            ),

        "etymology_summary":
            record[
                "etymology_summary"
            ],

        "morphemes":
            json.dumps(
                final_morphemes,
                ensure_ascii=False
            ),

        "morpheme_source":
            morpheme_source,

        "origin":
            json.dumps(
                final_origin,
                ensure_ascii=False
            ),

        "synonyms":
            json.dumps(
                record[
                    "synonyms"
                ][:10],
                ensure_ascii=False
            ),

        "related_words":
            json.dumps(
                record[
                    "related_words"
                ][:15],
                ensure_ascii=False
            ),

        "derived_words":
            json.dumps(
                record[
                    "derived_words"
                ][:15],
                ensure_ascii=False
            ),

        "examples":
            json.dumps(
                record[
                    "examples"
                ][:3],
                ensure_ascii=False
            ),

        "has_etymology":
            has_etymology,

        "kaikki_found":
            record[
                "kaikki_found"
            ],

        "source":
            "Kaikki / Wiktionary + etymology-db"
    }


    rows_to_save.append(row)


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=
            rows_to_save[0].keys()
    )

    writer.writeheader()

    writer.writerows(
        rows_to_save
    )


# ============================================================
# 결과 통계
# ============================================================

file_size_mb = (
    os.path.getsize(
        OUTPUT_FILE
    )
    /
    1024
    /
    1024
)


print()
print("=" * 70)
print("FINISHED!")
print("=" * 70)

print(
    "Total words:",
    len(rows_to_save)
)

print(
    "Kaikki morphemes:",
    kaikki_morpheme_count
)

print(
    "etymology-db fallback:",
    db_morpheme_count
)

print(
    "No structured morphemes:",
    missing_morpheme_count
)

print(
    "Not found in Kaikki:",
    missing_kaikki_count
)

print(
    f"CSV size: "
    f"{file_size_mb:.2f} MB"
)

print(
    "Output:",
    OUTPUT_FILE
)

print("=" * 70)