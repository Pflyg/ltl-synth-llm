import csv
import os


def crawlDir(path):
    filtered_files = []
    for root, subdirs, files in os.walk(path):
        for file in filter(lambda s: s.endswith(".csv"), files):
            filtered_files.append(file)
    return filtered_files


mappings = {"benchmark": "Benchmark"}


def transform(val, label=False):
    val = mappings.get(val, val)
    if label:
        return val.replace("_", r"\_\allowbreak ")
    return "\\" + val.replace("_", "")


def transformCSV(path):
    with open(path, newline="") as csvfile:
        reader = csv.reader(csvfile, dialect=csv.unix_dialect)
        header = [transform(h, label=True) for h in next(reader)]
        rows = [
            [transform(val, label=(i == 0)) for i, val in enumerate(row)]
            for row in list(reader)
        ]
        # print(header, rows)
    column_def = " A|" + "B" * (len(header) - 1) + " "
    header_def = " & ".join(header) + " \\\\\n"
    lastrow = rows.pop()  # to avoid trailing \\
    rows_def = "".join(
        [" & ".join(row) + " \\\\\n" for row in rows] + [" & ".join(lastrow)]
    )
    return f"""\\begin{{tabular}}{{{column_def}}}
{header_def}\\hline
{rows_def}
\end{{tabular}}%
"""


csv_files = crawlDir(".")
os.makedirs("./tex/", mode=0o777, exist_ok=True)
for file in csv_files:
    name = os.path.basename(file).split(".")[0]
    try:
        transformed = transformCSV(file)
        with open("./tex/" + name + ".tex", "w") as f:
            f.write(transformed)
    except StopIteration:
        print("Fail: " + file)
