#!/usr/bin/env python3
"""
sql2csv.py

Download a Travian map.sql file from a URL, extract the x_world INSERT data,
and write it out as a CSV.
"""

import argparse
import csv
import re
import sys

import requests

# The exact headers you specified:
HEADERS = [
    "Field ID", "X", "Y", "Tribe", "Village ID", "Village name",
    "Player ID", "Player name", "Alliance ID", "Alliance Tag",
    "Population", "Region", "Capital", "City", "Harbor", "Victory points"
]

INSERT_PATTERN = re.compile(r"INSERT INTO `x_world` VALUES\s*\((.*?)\);", re.IGNORECASE)


def fetch_sql(url: str, timeout: float = 10.0) -> str:
    """Download the SQL file from the given URL and return its text."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_value_strings(sql_text: str) -> list[str]:
    """
    Find all the INSERT lines and return a list of the
    comma‑delimited value strings inside the parentheses.
    """
    return INSERT_PATTERN.findall(sql_text)


def parse_record(record_str: str, expected_cols: int) -> list[str]:
    """
    Given the inside‑parentheses string of values (e.g.
    "1,-200,200,2,31688,'006',..." etc), parse it into a list of fields,
    respecting single-quoted strings, using the csv module.
    """
    # Use a CSV reader with single-quote quoting
    reader = csv.reader([record_str], delimiter=",", quotechar="'")
    fields = next(reader)
    # Some records may have more or fewer fields—truncate or pad as needed:
    if len(fields) > expected_cols:
        return fields[:expected_cols]
    elif len(fields) < expected_cols:
        return fields + [""] * (expected_cols - len(fields))
    return fields


def write_csv(records: list[list[str]], headers: list[str], output_path: str) -> None:
    """Write all parsed records to a CSV file with the given headers."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(records)


def main():
    URL = "https://ts21.x2.international.travian.com/map.sql"
    output_file = "map.csv"
    from_file = False # Change to False to fetch from URL

    try:
        if from_file:
            print("Reading SQL from map.sql…", file=sys.stderr)
            with open("map.sql", "r", encoding="utf-8") as f:
                sql_text = f.read()
        else:
            print(f"Fetching SQL from {URL}…", file=sys.stderr)
            sql_text = fetch_sql(URL)
            print(f"Saving fetched SQL to map.sql…", file=sys.stderr)
            with open("map.sql", "w", encoding="utf-8") as f:
                f.write(sql_text)

        print("Extracting INSERT records…", file=sys.stderr)
        raw_records = extract_value_strings(sql_text)
        if not raw_records:
            print("No `x_world` INSERTs found in the SQL!", file=sys.stderr)
            sys.exit(1)

        print(f"Parsing {len(raw_records)} records…", file=sys.stderr)
        parsed = [
            parse_record(rec, expected_cols=len(HEADERS))
            for rec in raw_records
        ]

        print(f"Writing CSV to {output_file}…", file=sys.stderr)
        write_csv(parsed, HEADERS, output_file)

        print("Done!", file=sys.stderr)

    except requests.RequestException as e:
        print(f"Error fetching SQL: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
