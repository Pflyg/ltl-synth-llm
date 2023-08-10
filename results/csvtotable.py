import csv
import os


def crawlDir(path):
    filtered_files = []
    for root, subdirs, files in os.walk(path):
        for file in filter(lambda s: s.endswith(".csv"), files):
            filtered_files.append(file)
    return filtered_files


csv_files = crawlDir(".")

mappings = {"benchmark": "Benchmark"}


def transform(val):
    val = mappings.get(val, val)
    return val.replace("_", "\_")


def transformCSV(path):
    with open(path, newline="") as csvfile:
        reader = csv.reader(csvfile, dialect=csv.unix_dialect)
        header = [transform(h) for h in next(reader)]
        rows = [[transform(val) for val in row] for row in list(reader)]
        print(header, rows)
    column_def = " |" + "|".join(["A"] + ["B"] * (len(header) - 1)) + "| "
    header_def = " & ".join(header) + " \\\\\n"
    rows_def = "".join([" & ".join(row) + " \\\\\n" for row in rows])
    return f"""\\begin{{tabular}}{{{column_def}}}
\\hline
{header_def}\\hline
{rows_def}\\hline
\end{{tabular}}    
"""


print(transformCSV(csv_files[0]))
