import gzip
import json
import csv
import re

KAIKKI_FILE = "../data/raw-wiktextract-data.jsonl.gz"
ETYMOLOGY_DB_FILE = "../data/etymology.csv.gz"

OUTPUT_FILE = "../output/a_combined_test.csv"

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


# --------------------------------------------------
# Kaikki 형태소 분석
# --------------------------------------------------

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

    # 우선순위
    # surf → affix → af

    for wanted_name in [
        "surf",
        "affix",
        "af"
    ]:

        for template in templates or []:

            if template.get("name") != wanted_name:
                continue

            args = template.get("args", {})

            if args.get("1") != "en":
                continue

            result = []

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

            if len(result) >= 2:
                return result

    return []


# --------------------------------------------------
# Kaikki origin
# --------------------------------------------------

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

    return unique(result)[:5]


# --------------------------------------------------
# etymology-db 형태소 분석
# --------------------------------------------------

def safe_number(value):

    try:
        return int(value)

    except:
        return 999


def get_db_morphemes(rows):

    # ----------------------------------------------
    # 방법 1:
    # biology 같은 영어 confix
    # ----------------------------------------------

    confixes = []

    for row in rows:

        if (
            row.get("reltype")
            == "has_confix"
            and
            row.get("related_lang")
            == "English"
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


    # ----------------------------------------------
    # 방법 2:
    # 직접적인 prefix / suffix 관계
    # ----------------------------------------------

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


    # ----------------------------------------------
    # 방법 3:
    # group_affix_root
    #
    # import → in + portō
    # predict → prae- + dīcō
    # telephone → τῆλε + φωνή
    # transport → trans + porto
    # ----------------------------------------------

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

            if (
                row.get("parent_tag")
                != tag
            ):
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


# --------------------------------------------------
# etymology-db origin
# --------------------------------------------------

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

        if term:

            if lang:
                result.append(
                    f"{lang} {term}"
                )

            else:
                result.append(term)

    return unique(result)[:5]


# ==================================================
# STEP 1
# Kaikki 검색
# ==================================================

print("STEP 1/2")
print("Searching Kaikki...")

kaikki_entries = {
    word: []
    for word in TARGET_WORDS
}


with gzip.open(
    KAIKKI_FILE,
    "rt",
    encoding="utf-8"
) as file:

    checked = 0

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

        if (
            data.get("lang_code")
            != "en"
        ):
            continue

        word = data.get(
            "word",
            ""
        ).lower()

        if word in TARGET_WORDS:
            kaikki_entries[word].append(
                data
            )


print("Kaikki finished!")


# ==================================================
# STEP 2
# etymology-db 검색
# ==================================================

print()
print("STEP 2/2")
print("Searching etymology-db...")


db_entries = {
    word: []
    for word in TARGET_WORDS
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

        if (
            row.get("lang")
            != "English"
        ):
            continue

        word = row.get(
            "term",
            ""
        ).lower()

        if word in TARGET_WORDS:
            db_entries[word].append(row)


print("etymology-db finished!")


# ==================================================
# 데이터 합치기
# ==================================================

rows_to_save = []


print()
print("=" * 70)
print("FINAL RESULTS")
print("=" * 70)


for word in sorted(TARGET_WORDS):

    entries = kaikki_entries[word]

    parts_of_speech = []
    definitions_en = []
    definitions_ko = []
    synonyms = []
    related_words = []
    examples = []

    kaikki_morphemes = []
    kaikki_origin = []


    for data in entries:

        pos = data.get("pos")

        if pos:
            parts_of_speech.append(pos)

        definitions_en.extend(
            get_definitions(
                data.get(
                    "senses",
                    []
                )
            )
        )

        definitions_ko.extend(
            get_korean_translations(
                data
            )
        )

        synonyms.extend(
            get_words(
                data.get(
                    "synonyms",
                    []
                )
            )
        )

        related_words.extend(
            get_words(
                data.get(
                    "related",
                    []
                )
            )
        )

        examples.extend(
            get_examples(
                data.get(
                    "senses",
                    []
                )
            )
        )

        templates = data.get(
            "etymology_templates",
            []
        )

        if not kaikki_morphemes:

            kaikki_morphemes = (
                get_kaikki_morphemes(
                    templates
                )
            )

        kaikki_origin.extend(
            get_kaikki_origin(
                templates
            )
        )


    # etymology-db fallback

    db_rows = db_entries[word]

    db_morphemes = (
        get_db_morphemes(
            db_rows
        )
    )

    db_origin = (
        get_db_origin(
            db_rows
        )
    )


    # Kaikki 우선
    if kaikki_morphemes:

        final_morphemes = (
            kaikki_morphemes
        )

        morpheme_source = "Kaikki"

    elif db_morphemes:

        final_morphemes = (
            db_morphemes
        )

        morpheme_source = (
            "etymology-db"
        )

    else:

        final_morphemes = []

        morpheme_source = "none"


    final_origin = unique(
        kaikki_origin
        + db_origin
    )[:8]


    row = {

        "word":
            word,

        "parts_of_speech":
            json.dumps(
                unique(
                    parts_of_speech
                ),
                ensure_ascii=False
            ),

        "definitions_en":
            json.dumps(
                unique(
                    definitions_en
                )[:5],
                ensure_ascii=False
            ),

        "definitions_ko":
            json.dumps(
                unique(
                    definitions_ko
                )[:10],
                ensure_ascii=False
            ),

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
                unique(
                    synonyms
                )[:10],
                ensure_ascii=False
            ),

        "related_words":
            json.dumps(
                unique(
                    related_words
                )[:15],
                ensure_ascii=False
            ),

        "examples":
            json.dumps(
                unique(
                    examples
                )[:3],
                ensure_ascii=False
            ),

        "source":
            "Kaikki / Wiktionary + etymology-db"
    }


    rows_to_save.append(row)


    print()
    print(word)

    print(
        "  morpheme source:",
        morpheme_source
    )

    print(
        "  morphemes:",
        final_morphemes
    )


# ==================================================
# CSV 저장
# ==================================================

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


print()
print("=" * 70)
print("CSV CREATED!")
print("File:", OUTPUT_FILE)
print(
    "Words:",
    len(rows_to_save)
)
print("=" * 70)