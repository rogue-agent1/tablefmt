#!/usr/bin/env python3
"""tablefmt - Format data as tables (markdown, CSV, TSV, ASCII, HTML).

Single-file, zero-dependency CLI. Reads CSV/TSV/JSON from stdin or file.
"""

import sys
import argparse
import csv
import json
import io


def read_data(args):
    """Read input data into list of dicts."""
    if args.file:
        with open(args.file) as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        return [], []

    fmt = args.input_format
    if fmt == "auto":
        if text.strip().startswith("[") or text.strip().startswith("{"):
            fmt = "json"
        elif "\t" in text.split("\n")[0]:
            fmt = "tsv"
        else:
            fmt = "csv"

    if fmt == "json":
        data = json.loads(text)
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                headers = list(data[0].keys())
                rows = [[str(r.get(h, "")) for h in headers] for r in data]
                return headers, rows
            else:
                return [], [list(map(str, r)) for r in data]
        return [], []

    sep = "\t" if fmt == "tsv" else ","
    reader = csv.reader(io.StringIO(text), delimiter=sep)
    all_rows = list(reader)
    if not all_rows:
        return [], []
    return all_rows[0], all_rows[1:]


def fmt_markdown(headers, rows):
    if not headers:
        headers = [f"Col{i}" for i in range(len(rows[0]))] if rows else []
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))
    header = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    sep = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    lines = [header, sep]
    for row in rows:
        cells = [(row[i] if i < len(row) else "").ljust(widths[i]) for i in range(len(headers))]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def fmt_csv(headers, rows, sep=","):
    out = io.StringIO()
    w = csv.writer(out, delimiter=sep)
    if headers:
        w.writerow(headers)
    w.writerows(rows)
    return out.getvalue().rstrip()


def fmt_ascii(headers, rows):
    if not headers:
        headers = [f"Col{i}" for i in range(len(rows[0]))] if rows else []
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))
    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    lines = [border, header, border]
    for row in rows:
        cells = [(row[i] if i < len(row) else "").ljust(widths[i]) for i in range(len(headers))]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append(border)
    return "\n".join(lines)


def fmt_html(headers, rows):
    lines = ["<table>"]
    if headers:
        lines.append("  <thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>")
    lines.append("  <tbody>")
    for row in rows:
        lines.append("    <tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    lines.append("  </tbody>")
    lines.append("</table>")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(prog="tablefmt", description="Format data as tables")
    p.add_argument("-f", "--file", help="Input file")
    p.add_argument("-i", "--input-format", default="auto", choices=["auto", "csv", "tsv", "json"])
    p.add_argument("-o", "--output-format", default="markdown", choices=["markdown", "csv", "tsv", "ascii", "html"])
    args = p.parse_args()

    headers, rows = read_data(args)
    if not rows and not headers:
        print("No data", file=sys.stderr)
        return 1

    formatters = {
        "markdown": fmt_markdown,
        "csv": lambda h, r: fmt_csv(h, r, ","),
        "tsv": lambda h, r: fmt_csv(h, r, "\t"),
        "ascii": fmt_ascii,
        "html": fmt_html,
    }
    print(formatters[args.output_format](headers, rows))


if __name__ == "__main__":
    sys.exit(main())
