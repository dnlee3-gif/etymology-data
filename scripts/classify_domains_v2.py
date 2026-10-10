import csv
import gzip
import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

KAIKKI_FILE = (
    BASE_DIR
    / "data"
    / "raw-wiktextract-data.jsonl.gz"
)

INPUT_CSV = (
    BASE_DIR
    / "output"
    / "a.csv"
)

OUTPUT_CSV = (
    BASE_DIR
    / "output"
    / "a_classified_v2.csv"
)


# ============================================================
# Kaikki topic/category용 분야 키워드
# ============================================================

DOMAIN_KEYWORDS = {

    "computer_science": [
        "computer",
        "computing",
        "programming",
        "software",
        "hardware",
        "internet",
        "social-media",
        "social media",
        "artificial-intelligence",
        "machine-learning",
        "data-science"
    ],

    "mathematics": [
        "mathematics",
        "math",
        "algebra",
        "geometry",
        "calculus",
        "statistics",
        "probability"
    ],

    "biology": [
        "biology",
        "biochemistry",
        "microbiology",
        "genetics",
        "botany",
        "zoology",
        "ecology",
        "anatomy"
    ],

    "medicine": [
        "medicine",
        "medical",
        "pathology",
        "pharmacology",
        "surgery",
        "psychiatry"
    ],

    "chemistry": [
        "chemistry",
        "biochemistry",
        "organic-chemistry",
        "inorganic-chemistry"
    ],

    "physics": [
        "physics",
        "mechanics",
        "thermodynamics",
        "optics",
        "quantum"
    ],

    "economics": [
        "economics",
        "finance",
        "banking",
        "accounting"
    ],

    "business": [
        "business",
        "commerce",
        "marketing",
        "management"
    ],

    "law": [
        "law",
        "legal",
        "jurisprudence"
    ],

    "politics": [
        "politics",
        "government",
        "elections"
    ],

    "sports": [
        "sports",
        "football",
        "baseball",
        "basketball",
        "soccer",
        "rugby",
        "tennis",
        "hockey",
        "athletics",
        "ball-games"
    ],

    "astronomy": [
        "astronomy",
        "cosmology",
        "astrophysics"
    ],

    "engineering": [
        "engineering",
        "electronics",
        "electrical-engineering",
        "mechanical-engineering",
        "civil-engineering"
    ],

    "religion": [
        "religion",
        "christianity",
        "islam",
        "judaism",
        "buddhism",
        "hinduism",
        "theology"
    ],

    "linguistics": [
        "linguistics",
        "grammar",
        "phonetics",
        "phonology"
    ],

    "music": [
        "music",
        "musical"
    ],

    "arts": [
        "art",
        "arts",
        "literature",
        "theatre",
        "theater",
        "film",
        "photography"
    ],

    "food": [
        "food",
        "cooking",
        "culinary",
        "cuisine"
    ],

    "military": [
        "military",
        "warfare",
        "army",
        "navy"
    ],

    "education": [
        "education",
        "school",
        "academic"
    ],

    "geography": [
        "geography",
        "geology",
        "meteorology"
    ]
}


# ============================================================
# 첫 번째 뜻에서 topic이 비어 있을 때 사용할
# 보수적인 정의(gloss) 키워드
# ============================================================

GLOSS_KEYWORDS = {

    "computer_science": [
        "computer",
        "computational",
        "algorithm",
        "programming",
        "software"
    ],

    "mathematics": [
        "mathematical",
        "mathematics",
        "algebra",
        "geometry",
        "calculus"
    ],

    "biology": [
        "biological",
        "biomolecule",
        "protein",
        "dna",
        "rna"
    ],

    "chemistry": [
        "chemical reaction",
        "chemical compound"
    ],

    "medicine": [
        "medical",
        "patient",
        "disease",
        "clinical"
    ],

    "law": [
        "civil law",
        "criminal law",
        "court of law",
        "legal proceeding"
    ],

    "sports": [
        "football",
        "baseball",
        "basketball",
        "rugby",
        "quarterback"
    ]
}


IGNORE_TAGS = {
    "obsolete",
    "historical",
    "archaic"
}


def normalize(text):

    return (
        text
        .lower()
        .strip()
        .replace("_", "-")
    )


def detect_label_domains(labels):

    domains = set()

    for label in labels:

        cleaned = normalize(label)

        if cleaned.startswith("en:"):
            cleaned = cleaned[3:]

        for domain, keywords in DOMAIN_KEYWORDS.items():

            for keyword in keywords:

                if keyword in cleaned:
                    domains.add(domain)
                    break

    return domains


def detect_gloss_domains(glosses):

    text = " ".join(
        glosses
    ).lower()

    domains = set()

    for domain, keywords in GLOSS_KEYWORDS.items():

        for keyword in keywords:

            pattern = (
                r"(?<![a-z])"
                + re.escape(keyword)
                + r"(?![a-z])"
            )

            if re.search(pattern, text):
                domains.add(domain)
                break

    return domains


# ============================================================
# 기존 a.csv 읽기
# ============================================================

print("=" * 70)
print("STEP 1/3")
print("Loading a.csv...")
print("=" * 70)


rows = []

with open(
    INPUT_CSV,
    "r",
    encoding="utf-8-sig",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        rows.append(row)


target_words = {
    row["word"].lower()
    for row in rows
}


print(
    "Words:",
    len(target_words)
)


# ============================================================
# 단어별 sense 저장
# ============================================================

word_senses = {
    word: []
    for word in target_words
}

found_words = set()


# ============================================================
# Kaikki 읽기
# ============================================================

print()
print("=" * 70)
print("STEP 2/3")
print("Scanning Kaikki...")
print("=" * 70)


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


        if data.get("lang_code") != "en":
            continue


        word = data.get(
            "word",
            ""
        ).lower()


        if word not in target_words:
            continue


        if data.get("pos") == "name":
            continue


        found_words.add(word)


        for sense in data.get(
            "senses",
            []
        ):

            tags = set(
                sense.get(
                    "tags",
                    []
                )
            )


            # 오래되거나 역사적인 특수 의미는
            # 주 분류 판단에서 제외
            if tags & IGNORE_TAGS:
                continue


            topics = (
                sense.get(
                    "topics",
                    []
                )
            )

            categories = [
                category
                for category in sense.get(
                    "categories",
                    []
                )
                if (
                    category
                    and category
                    .lower()
                    .startswith("en:")
                )
            ]

            glosses = (
                sense.get(
                    "glosses",
                    []
                )
            )


            label_domains = (
                detect_label_domains(
                    topics
                    + categories
                )
            )


            gloss_domains = (
                detect_gloss_domains(
                    glosses
                )
            )


            domains = (
                label_domains
                | gloss_domains
            )


            word_senses[word].append({
                "domains": domains,
                "topics": topics,
                "categories": categories,
                "glosses": glosses
            })


print("Kaikki scan finished.")


# ============================================================
# 분류
# ============================================================

print()
print("=" * 70)
print("STEP 3/3")
print("Classifying...")
print("=" * 70)


counts = {
    "general": 0,
    "domain": 0,
    "mixed": 0,
    "unknown": 0
}


for row in rows:

    word = row[
        "word"
    ].lower()


    if word not in found_words:

        classification = "unknown"

        primary_domains = []

        secondary_domains = []


    else:

        senses = word_senses[word]


        if not senses:

            classification = "general"

            primary_domains = []

            secondary_domains = []


        else:

            # 첫 번째 일반적인 sense
            first_domains = set(
                senses[0][
                    "domains"
                ]
            )


            domain_frequency = {}

            for sense in senses:

                for domain in sense[
                    "domains"
                ]:

                    domain_frequency[
                        domain
                    ] = (
                        domain_frequency.get(
                            domain,
                            0
                        )
                        + 1
                    )


            later_domains = set()

            for sense in senses[1:]:

                later_domains.update(
                    sense[
                        "domains"
                    ]
                )


            if first_domains:

                classification = "domain"

                primary_domains = sorted(
                    first_domains
                )

                # 첫 뜻에는 없지만
                # 여러 sense에서 반복해서 등장하면
                # 보조 분야로 인정
                secondary_domains = sorted([
                    domain
                    for domain in later_domains
                    if (
                        domain
                        not in first_domains
                        and
                        domain_frequency.get(
                            domain,
                            0
                        ) >= 2
                    )
                ])


            elif later_domains:

                classification = "mixed"

                primary_domains = []

                secondary_domains = sorted(
                    later_domains
                )


            else:

                classification = "general"

                primary_domains = []

                secondary_domains = []


    all_domains = sorted(
        set(
            primary_domains
            + secondary_domains
        )
    )


    row[
        "classification"
    ] = classification


    row[
        "domains"
    ] = json.dumps(
        all_domains,
        ensure_ascii=False
    )


    row[
        "primary_domains"
    ] = json.dumps(
        primary_domains,
        ensure_ascii=False
    )


    row[
        "secondary_domains"
    ] = json.dumps(
        secondary_domains,
        ensure_ascii=False
    )


    counts[
        classification
    ] += 1


# ============================================================
# 저장
# ============================================================

fieldnames = list(
    rows[0].keys()
)


with open(
    OUTPUT_CSV,
    "w",
    encoding="utf-8-sig",
    newline=""
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(rows)


print()
print("=" * 70)
print("FINISHED!")
print("=" * 70)

print(
    "General:",
    counts["general"]
)

print(
    "Domain:",
    counts["domain"]
)

print(
    "Mixed:",
    counts["mixed"]
)

print(
    "Unknown:",
    counts["unknown"]
)

print()

print(
    "Output:",
    OUTPUT_CSV
)

print("=" * 70)