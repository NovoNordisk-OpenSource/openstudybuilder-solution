import csv
import sys

if len(sys.argv) < 4:
    print("Usage:")
    print("> python csvdiff.py old.csv new.csv key_column")
    print(
        "Optionally specify columns to skip, skips any columns with names starting with col_a or col_b:"
    )
    print('> python csvdiff.py old.csv new.csv key_column "col_a,col_b')
    print("Example")
    print(
        '> python csvdiff.py ucum.csv ucum2.csv UCUM_CODE "Row #,Previous UCUM version,Description of Change Made"'
    )
    sys.exit()
file1 = sys.argv[1]
file2 = sys.argv[2]
keyname = sys.argv[3]
if len(sys.argv) > 4:
    skip_columns = sys.argv[4].split(",")
else:
    skip_columns = []

rows1 = {}
with open(file1, newline="", errors="replace") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        rows1[row[keyname]] = row

rows2 = {}
with open(file2, newline="", errors="replace") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        rows2[row[keyname]] = row

_, first = next(iter(rows1.items()))
headers1 = first.keys()
_, first = next(iter(rows2.items()))
headers2 = first.keys()

excluded_headers = set()
for h in headers1:
    for s in skip_columns:
        if h.startswith(s):
            excluded_headers.add(h)
for h in headers2:
    for s in skip_columns:
        if h.startswith(s):
            excluded_headers.add(h)

# Compare headers
for h1 in headers1:
    if h1 not in excluded_headers and h1 not in headers2:
        print(f"Column {h1} only exists in first file!")
        sys.exit()
for h2 in headers2:
    if h2 not in excluded_headers and h2 not in headers1:
        print(f"Column {h2} only exists in second file!")
        sys.exit()

print(f"Ignoring columns:")
for h in excluded_headers:
    print(f"- {h}")
print("")

# Loop through 1
checked = []
for key, data in rows1.items():
    checked.append(key)
    different = []
    if key in rows2:
        for k, v in data.items():
            if k not in excluded_headers and v != rows2[key][k]:
                different.append([k, v, rows2[key][k]])
        if different:
            print(f"Changed: {key}")
            for diff in different:
                k, v1, v2 = diff
                print(f"    {k}:  '{v1}'  -->  '{v2}'")
    else:
        print(f"Removed: {key}")

# Loop through 2
for key in rows2.keys():
    if key not in checked:
        print(f"Added:   {key}")
