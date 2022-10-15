# This file cleans a fresh export from LNM by removing th last four columns

import csv

rows = []
with open("data/msfs_pois.csv", newline="") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) >= 10:
            row = row[0:-4]
        rows.append(row)

with open("data/msfs_pois.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(rows)
