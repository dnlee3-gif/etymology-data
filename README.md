# Etymology Data Pipeline

A data collection and preprocessing pipeline for an English etymology learning web service.

## Main Features

- Uses 10,000 frequently used English words
- Extracts dictionary data from Kaikki / Wiktionary
- Collects definitions, Korean translations, examples, synonyms, related words, and derived words
- Extracts structured morphemes when available
- Uses etymology-db as a fallback source
- Does not invent unsupported etymologies

Example:

transport
- trans-: beyond, across, through
- port: to carry

biology
- bio
- logy

predict
- Latin prae-
- Latin dīcō

## Data Sources

### Kaikki / Wiktionary
Primary source for:
- definitions
- translations
- examples
- synonyms
- related words
- derived words
- etymology

### etymology-db
Secondary source for additional etymological relationships and morpheme structures.

## Current Dataset

- Total words: 10,000
- Found in Kaikki: 9,586
- Structured morphemes from Kaikki: 1,016
- Additional morphemes from etymology-db: 1,744
- No structured morpheme data: 7,240

The final processed dataset is:

output/a.csv

## Main Scripts

- scripts/make_final_csv.py  
  Generates the final 10,000-word CSV.

- scripts/search_app.py  
  Allows users to search the generated dataset from the terminal.

## Generate Dataset

Run:

cd scripts
python make_final_csv.py

## Search Dataset

Run:

cd scripts
python search_app.py

Example:

Enter word: transport

The program displays:
- definitions
- Korean translations
- morphemes
- etymology
- synonyms
- related words
- derived words
- examples

Type `exit` to quit.

## Project Goal

The goal is to build an English-learning service where users can understand how words were formed instead of only memorizing definitions.

Key principle:

**Do not invent etymology. Use verified dictionary data first.**