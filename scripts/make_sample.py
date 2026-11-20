"""Generate a flight price file with the same columns as the Kaggle data.

The assignment asked for at least 1 GB in HDFS. This script can write a file of
any size for testing the cluster, without copying or inflating real data.

    python scripts/make_sample.py data/sample.csv --rows 20000
    python scripts/make_sample.py data/big.csv --megabytes 1100
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

AIRLINES = {"IndiGo": 0.9, "Air India": 1.15, "Jet Airways": 1.3, "SpiceJet": 0.85, "Vistara": 1.2, "GoAir": 0.88, "Air Asia": 0.8}
ROUTES = [("Banglore", "New Delhi", "BLR"), ("Delhi", "Cochin", "DEL"), ("Kolkata", "Banglore", "CCU"), ("Mumbai", "Hyderabad", "BOM"), ("Chennai", "Kolkata", "MAA")]
STOPS = ["non-stop", "1 stop", "2 stops"]
HEADER = "Airline,Date_of_Journey,Source,Destination,Route,Dep_Time,Arrival_Time,Duration,Total_Stops,Additional_Info,Price\n"


def row(rng: random.Random) -> str:
    airline = rng.choice(list(AIRLINES))
    src, dst, code = rng.choice(ROUTES)
    day = date(2019, 3, 1) + timedelta(days=rng.randrange(0, 120))
    stops = rng.choices(STOPS, weights=[4, 5, 1])[0]
    season = 1.25 if day.month in (5, 6) else 1.0
    price = int(rng.gauss(5500, 900) * AIRLINES[airline] * season * (1 + 0.35 * STOPS.index(stops)))
    dep = f"{rng.randrange(0, 24):02d}:{rng.choice([0, 15, 30, 45]):02d}"
    return f"{airline},{day.strftime('%d/%m/%Y')},{src},{dst},{code}-{dst[:3].upper()},{dep},{dep},2h 30m,{stops},No info,{max(price, 1500)}\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("out")
    p.add_argument("--rows", type=int, default=20000)
    p.add_argument("--megabytes", type=float, default=None)
    p.add_argument("--seed", type=int, default=1)
    a = p.parse_args()
    rng = random.Random(a.seed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    limit = a.megabytes * 1024 * 1024 if a.megabytes else None
    written = 0
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(HEADER)
        n = 0
        while (limit and written < limit) or (not limit and n < a.rows):
            line = row(rng)
            f.write(line)
            written += len(line)
            n += 1
    print(f"{n} rows, {written / 1024 / 1024:.1f} MB written to {a.out}")


if __name__ == "__main__":
    main()
