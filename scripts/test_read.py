import gzip
import json

file_path = "../data/raw-wiktextract-data.jsonl.gz"

with gzip.open(file_path, "rt", encoding="utf-8") as file:
    line = file.readline()
    data = json.loads(line)

print("WORD:", data.get("word"))
print("LANGUAGE:", data.get("lang"))
print("LANG CODE:", data.get("lang_code"))
print("PART OF SPEECH:", data.get("pos"))

print("\nAVAILABLE DATA:")
for key in data.keys():
    print("-", key)