from pathlib import Path
import csv
import json
import streamlit as st


# --------------------------------------------------
# 파일 위치
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_FILE = BASE_DIR / "output" / "a.csv"


# --------------------------------------------------
# Streamlit 설정
# --------------------------------------------------

st.set_page_config(
    page_title="Etymology Explorer",
    page_icon="📚",
    layout="centered"
)


# --------------------------------------------------
# JSON 형태 CSV 값 읽기
# --------------------------------------------------

def parse_json_field(value):
    if not value:
        return []

    try:
        return json.loads(value)
    except:
        return []


# --------------------------------------------------
# CSV 불러오기
# --------------------------------------------------

@st.cache_data
def load_dictionary():

    dictionary = {}

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            dictionary[
                row["word"].lower()
            ] = row

    return dictionary


dictionary = load_dictionary()


# --------------------------------------------------
# 화면
# --------------------------------------------------

st.title("📚 Etymology Explorer")

st.write(
    "영어 단어의 뜻, 어원, 형태소와 관련 단어를 확인하세요."
)

st.caption(
    f"{len(dictionary):,} words available"
)


query = st.text_input(
    "Search a word",
    placeholder="transport",
).strip().lower()


# --------------------------------------------------
# 검색 결과
# --------------------------------------------------

if query:

    row = dictionary.get(query)

    if not row:

        st.warning(
            f'"{query}" is not in the current dataset.'
        )

    else:

        st.divider()

        st.header(row["word"])


        # ------------------------------------------
        # 기본 정보
        # ------------------------------------------

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Frequency Rank",
                row["rank"]
            )

        with col2:

            parts = parse_json_field(
                row["parts_of_speech"]
            )

            st.write("**Part of Speech**")

            if parts:
                st.write(", ".join(parts))
            else:
                st.write("N/A")


        # ------------------------------------------
        # 일반어 / 전문어 분류
        # ------------------------------------------

        classification = row.get(
            "classification",
            ""
        )

        domains = parse_json_field(
            row.get(
                "domains",
                "[]"
            )
        )

        primary_domains = parse_json_field(
            row.get(
                "primary_domains",
                "[]"
            )
        )

        secondary_domains = parse_json_field(
            row.get(
                "secondary_domains",
                "[]"
            )
        )


        st.subheader("🏷️ Classification")


        if classification == "general":

            st.success(
                "General Word"
            )


        elif classification == "domain":

            st.warning(
                "Domain / Specialized Word"
            )


        elif classification == "mixed":

            st.info(
                "Mixed: General + Specialized Meanings"
            )


        elif classification == "unknown":

            st.write(
                "Unknown"
            )


        else:

            st.write(
                "Classification not available."
            )


        if domains:

            st.write(
                "**Domains:** "
                + ", ".join(domains)
            )


        if primary_domains:

            st.write(
                "**Primary Domains:** "
                + ", ".join(
                    primary_domains
                )
            )


        if secondary_domains:

            st.write(
                "**Secondary Domains:** "
                + ", ".join(
                    secondary_domains
                )
            )


        # ------------------------------------------
        # 한국어 뜻
        # ------------------------------------------

        korean = parse_json_field(
            row["definitions_ko"]
        )

        st.subheader("🇰🇷 Korean Meaning")

        if korean:

            for meaning in korean:
                st.write(
                    f"• {meaning}"
                )

        else:
            st.write(
                "Korean definition not available."
            )


        # ------------------------------------------
        # 영어 정의
        # ------------------------------------------

        english = parse_json_field(
            row["definitions_en"]
        )

        st.subheader("📖 English Definitions")

        if english:

            for i, definition in enumerate(
                english,
                start=1
            ):

                st.write(
                    f"{i}. {definition}"
                )

        else:
            st.write("N/A")


        # ------------------------------------------
        # 형태소
        # ------------------------------------------

        st.subheader("🧩 Word Structure")

        morphemes = parse_json_field(
            row["morphemes"]
        )

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

                st.markdown(
                    f"### {text}"
                )

                if meaning:

                    st.write(
                        f"**Meaning:** {meaning}"
                    )

                else:

                    st.write(
                        "**Meaning:** Not available"
                    )

                if language:

                    st.caption(
                        f"Language: {language}"
                    )

            st.caption(
                "Morpheme source: "
                + row["morpheme_source"]
            )

        else:

            st.info(
                "No verified structured "
                "morpheme data available."
            )


        # ------------------------------------------
        # 어원
        # ------------------------------------------

        st.subheader("🏛️ Etymology")

        etymology = row[
            "etymology_summary"
        ]

        if etymology:
            st.write(etymology)
        else:
            st.write("N/A")


        origins = parse_json_field(
            row["origin"]
        )

        if origins:

            with st.expander(
                "View origin details"
            ):

                for origin in origins:
                    st.write(
                        f"• {origin}"
                    )


        # ------------------------------------------
        # 관련 단어
        # ------------------------------------------

        related = parse_json_field(
            row["related_words"]
        )

        synonyms = parse_json_field(
            row["synonyms"]
        )

        derived = parse_json_field(
            row["derived_words"]
        )


        if related:

            st.subheader(
                "🔗 Related Words"
            )

            st.write(
                ", ".join(related)
            )


        if synonyms:

            st.subheader(
                "🔄 Synonyms"
            )

            st.write(
                ", ".join(synonyms)
            )


        if derived:

            with st.expander(
                "Derived Words"
            ):

                for word in derived:
                    st.write(
                        f"• {word}"
                    )


        # ------------------------------------------
        # 예문
        # ------------------------------------------

        examples = parse_json_field(
            row["examples"]
        )

        st.subheader("✏️ Examples")

        if examples:

            for example in examples:

                st.info(example)

        else:
            st.write(
                "No examples available."
            )


        st.divider()

        st.caption(
            "Sources: "
            + row["source"]
        )