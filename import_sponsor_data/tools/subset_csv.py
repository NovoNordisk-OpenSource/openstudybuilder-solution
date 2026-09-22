# A very simple script that crates a new csv by filtering out any row
# where the value in a given column is not present in another csv file.
import csv
import sys

fname1 = sys.argv[1]
fname2 = sys.argv[2]
colname1 = sys.argv[3]
colname2 = sys.argv[4]

values = []
with open(fname1, encoding="utf-8", errors="ignore") as textfile:
    rows = csv.reader(textfile, delimiter=",")
    headers = next(rows)
    idx = headers.index(colname1)
    for row in rows:
        values.append(row[idx])

with open(fname2, encoding="utf-8", errors="ignore") as infile:

    with open(fname2 + ".new.csv", "w") as outfile:
        writer = csv.writer(outfile)
        rows = csv.reader(infile, delimiter=",")
        headers = next(rows)
        writer.writerow(headers)
        idx = headers.index(colname2)
        for row in rows:
            val = row[idx]
            if val in values:
                writer.writerow(row)
