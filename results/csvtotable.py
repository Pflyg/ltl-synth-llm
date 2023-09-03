import csv
import os

import sys

# weird hack because the python module system is a mess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark import Benchmark


def crawlDir(path):
    filtered_files = []
    for root, subdirs, files in os.walk(path):
        for file in filter(lambda s: s.endswith(".csv"), files):
            filtered_files.append(file)
    return filtered_files


mappings = {
    "benchmark": "Benchmark",
    "strix": r"\STRIX",
    "bosy": r"\BOSY",
    "none": r"\NONE",
    "self": r"\SELF",
}


def transform(val, label=False):
    val = mappings.get(val, val)
    if val.isnumeric():
        return "$" + val + "$"
    if label:
        return val.replace("_", r"\_\allowbreak ")
    return "\\" + val.replace("_", "")


def transformCSV(path):
    with open(path, newline="") as csvfile:
        reader = csv.reader(csvfile, dialect=csv.unix_dialect)
        header = [transform(h, label=True) for h in next(reader)]
        rows = [
            [transform(val, label=(i == 0)) for i, val in enumerate(row)]
            for row in sorted(list(reader), key=lambda x: x[0])
        ]
    column_def = "@{} A|" + "B" * (len(header) - 1) + " @{}"
    header_def = " & ".join(header) + " \\\\\n"
    lastrow = rows.pop()  # to avoid trailing \\
    rows_def = "".join(
        [" & ".join(row) + " \\\\\n" for row in rows] + [" & ".join(lastrow)]
    )
    return f"""\\footnotesize\\begin{{tblr}}{{colsep=5pt,colspec={{{column_def}}},width=\\textwidth,rowspec={{Q[b]|}}}}
{header_def}
{rows_def}
\end{{tblr}}%
"""


def processBenchmarks(benchmarks, result_file):
    rows = [
        r"Benchmark & {Example Parameter Value 1} & {Example Parameter Value 2} & {Parameter Value to generate}\\",
    ]
    for bm in sorted(benchmarks, key=lambda x: x.name):
        # incidentally, all benchmarks ONLY use "n" as a parameter name
        row = (
            [transform(bm.name, label=True)]
            + [str(impl["params"]["n"]) for impl in bm.implementations]
            + [str(bm.generate_params["n"])]
        )
        rows.append(" & ".join(row) + r"\\")
    rows = "\n".join(rows)
    table = f"""\\begin{{tblr}}{{colsep=5pt,colspec={{@{{}} A|XXX @{{}}}},width=\\textwidth,rowspec={{Q[b]|}}}}
{(rows)}
\\end{{tblr}}"""
    with open(result_file, "w") as f:
        f.write(table)


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

processBenchmarks(
    Benchmark.load_from_json("../benchmarks.json", "../parametric_solutions"),
    "tex/benchmarks_human.tex",
)

processBenchmarks(
    Benchmark.load_from_json("../benchmarks_strix.json", "../syntcomp/tlsf"),
    "tex/benchmarks_strix.tex",
)

processBenchmarks(
    Benchmark.load_from_json("../benchmarks_bosy.json", "../syntcomp/tlsf"),
    "tex/benchmarks_bosy.tex",
)

# ,row{even}={bg=black!10}
