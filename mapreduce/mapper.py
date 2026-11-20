#!/usr/bin/env python3
"""Hadoop Streaming mapper for the flight price data.

Reads CSV lines from stdin and writes one line per analysis:

    TASK|key <TAB> sum,count,min,max

The task name is part of the key, so Hadoop sorts and partitions on the full
key. Every value has the same shape (sum, count, min, max), which means one
script can serve as both combiner and reducer.

Tasks
    AIRLINE   average, min and max price per airline
    ROUTE     number of flights per route (source -> destination)
    MONTH     price distribution per month of travel
    DATE      price distribution per travel date
    WEEKDAY   price distribution per day of the week

Bad rows are skipped and counted with Hadoop's reporter counters, so they show
up in the job summary instead of disappearing.
"""

import csv
import sys
from datetime import datetime

DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d")
REQUIRED = ("Airline", "Date_of_Journey", "Source", "Destination", "Price")


def counter(name: str) -> None:
    sys.stderr.write(f"reporter:counter:FlightPrices,{name},1\n")


def parse_date(text: str):
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def emit(task: str, key: str, price: float) -> None:
    print(f"{task}|{key}\t{price},1,{price},{price}")


def main(stream=sys.stdin) -> None:
    header = None
    for row in csv.reader(stream):
        if not row:
            continue
        row[0] = row[0].lstrip("﻿")
        if header is None and "Airline" in row:
            header = {name: i for i, name in enumerate(row)}
            continue
        if header is None:
            # no header line in this split: assume the column order of the Kaggle file
            header = {"Airline": 0, "Date_of_Journey": 1, "Source": 2, "Destination": 3, "Price": 10}
        try:
            airline = row[header["Airline"]].strip()
            source = row[header["Source"]].strip()
            destination = row[header["Destination"]].strip()
            price = float(row[header["Price"]])
        except (IndexError, ValueError):
            counter("bad_row")
            continue
        if not airline or price <= 0:
            counter("bad_row")
            continue
        counter("good_row")
        emit("AIRLINE", airline, price)
        emit("ROUTE", f"{source} -> {destination}", price)
        day = parse_date(row[header["Date_of_Journey"]])
        if day is None:
            counter("bad_date")
            continue
        emit("MONTH", day.strftime("%Y-%m"), price)
        emit("DATE", day.isoformat(), price)
        emit("WEEKDAY", f"{day.isoweekday()}-{day.strftime('%a')}", price)


if __name__ == "__main__":
    main()
