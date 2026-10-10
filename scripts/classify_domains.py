import csv
import gzip
import json
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
    / "a_classified.csv"
)


# ============================================================
# 분야 분류 규칙
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
        "data-science",
        "cyber",
        "digital"
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
        "psychiatry",
        "disease"
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

    "mathematics": [
        "mathematics",
        "math",
        "algebra",
        "geometry",
        "calculus",
        "statistics",
        "probability"
    ],

    "economics": [
        "economics",
        "finance",
        "banking",
        "accounting",
        "economic"
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
        "political",
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
        "phonology",
        "language"
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
        "navy",
        "weapon"
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
# 보조 함수
# ============================================================

def normalize(text):

    return (
        text
        .lower()
        .strip()
        .replace("_", "-")
    )


def detect_domains(labels):

    domains = set()

    for label in labels:

        cleaned = normalize(label)

        # category의 "en:" 제거
        if cleaned.startswith("en:"):
            cleaned = cleaned[3:]

        for domain, keywords in (
            DOMAIN_KEYWORDS.items()
        ):

            for keyword in keywords:

                if keyword in cleaned:
                    domains.add(domain)
                    break

    return sorted(domains)


# ============================================================
# 현재 a.csv 단어 읽기
# ============================================================

print("=" * 70)
print("STEP 1/3")
print("Loading current CSV...")
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
    "Words loaded:",
    len(target_words)
)


# ============================================================
# Kaikki에서 topics/categories 수집
# ============================================================

print()
print("=" * 70)
print("STEP 2/3")
print("Scanning Kaikki for domain information...")
print("=" * 70)


domain_data = {

    word: {
        "topics": set(),
        "categories": set(),
        "found": False
    }

    for word in target_words
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


        if data.get("lang_code") != "en":
            continue


        word = data.get(
            "word",
            ""
        ).lower()


        if word not in target_words:
            continue


        # 고유명사 제외
        if data.get("pos") == "name":
            continue


        info = domain_data[word]

        info["found"] = True


        # 각 sense 확인
        for sense in data.get(
            "senses",
            []
        ):

            for topic in sense.get(
                "topics",
                []
            ):

                if topic:
                    info["topics"].add(
                        topic
                    )


            for category in sense.get(
                "categories",
                []
            ):

                # en:으로 시작하는
                # 의미 기반 category만 사용
                if (
                    category
                    and
                    category.lower().startswith(
                        "en:"
                    )
                ):

                    info[
                        "categories"
                    ].add(category)


print("Kaikki scan finished.")


# ============================================================
# 분류 + CSV 생성
# ============================================================

print()
print("=" * 70)
print("STEP 3/3")
print("Classifying words...")
print("=" * 70)


classification_counts = {
    "general": 0,
    "domain": 0,
    "unknown": 0
}

domain_counts = {}


for row in rows:

    word = row["word"].lower()

    info = domain_data[word]

    topics = sorted(
        info["topics"]
    )

    categories = sorted(
        info["categories"]
    )


    labels = (
        topics
        +
        categories
    )


    domains = detect_domains(
        labels
    )


    # -----------------------------------------
    # 최종 분류
    # -----------------------------------------

    if not info["found"]:

        classification = "unknown"

        domain_source = "none"


    elif domains:

        classification = "domain"

        if topics and categories:

            domain_source = (
                "topics+categories"
            )

        elif topics:

            domain_source = "topics"

        else:

            domain_source = (
                "categories"
            )


    else:

        classification = "general"

        domain_source = "none"


    classification_counts[
        classification
    ] += 1


    for domain in domains:

        domain_counts[domain] = (
            domain_counts.get(
                domain,
                0
            )
            + 1
        )


    # 새 컬럼
    row[
        "classification"
    ] = classification

    row[
        "domains"
    ] = json.dumps(
        domains,
        ensure_ascii=False
    )

    row[
        "raw_topics"
    ] = json.dumps(
        topics,
        ensure_ascii=False
    )

    row[
        "domain_source"
    ] = domain_source


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


# ============================================================
# 결과
# ============================================================

print()
print("=" * 70)
print("FINISHED!")
print("=" * 70)

print(
    "General:",
    classification_counts[
        "general"
    ]
)

print(
    "Domain:",
    classification_counts[
        "domain"
    ]
)

print(
    "Unknown:",
    classification_counts[
        "unknown"
    ]
)


print()
print("DOMAIN COUNTS:")

for domain, count in sorted(
    domain_counts.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(
        f"{domain}: {count}"
    )


print()
print(
    "Output:",
    OUTPUT_CSV
)

print("=" * 70)