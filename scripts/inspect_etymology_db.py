import gzip
import csv

FILE_PATH = "../data/etymology.csv.gz"

with gzip.open(
    FILE_PATH,
    "rt",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    print("COLUMNS:")
    print(reader.fieldnames)

    print("\nFIRST 5 ROWS:\n")

    for i, row in enumerate(reader):

        print("=" * 60)
        print("ROW", i + 1)

        for key, value in row.items():
            print(f"{key}: {value}")

        if i == 4:
            break