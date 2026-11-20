"""Run the job without Hadoop, following the same steps Hadoop Streaming takes.

1. Split the input into N chunks (one per mapper).
2. Map each chunk, then run the combiner on each mapper's sorted output.
3. Partition by key hash into R reducers, sort each partition, reduce.

Useful for testing: the result must not change with the number of mappers or
reducers, or with the order of the input.

    python scripts/local_run.py data/flight_prices.csv --mappers 4 --reducers 3 --out results/output.tsv
"""

from __future__ import annotations

import argparse
import io
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mapreduce"))

import mapper  # noqa: E402
import reducer  # noqa: E402


def run(lines: list[str], mappers: int = 1, reducers: int = 1, combine: bool = True) -> list[str]:
    header, body = (lines[0], lines[1:]) if lines and "Airline" in lines[0] else (None, lines)
    size = max(1, -(-len(body) // mappers))
    partitions: list[list[str]] = [[] for _ in range(reducers)]
    for i in range(0, max(len(body), 1), size):
        chunk = ([header] if header else []) + body[i : i + size]
        mapped = sorted(_capture(lambda: mapper.main(io.StringIO("".join(chunk)))).splitlines(True))
        if combine:
            buf = io.StringIO()
            reducer.main(io.StringIO("".join(mapped)), buf, final=False)
            mapped = buf.getvalue().splitlines(True)
        for line in mapped:
            key = line.split("\t", 1)[0]
            partitions[zlib.crc32(key.encode()) % reducers].append(line)
    result = []
    for part in partitions:
        buf = io.StringIO()
        reducer.main(io.StringIO("".join(sorted(part))), buf, final=True)
        result += buf.getvalue().splitlines()
    return sorted(result)


def _capture(fn) -> str:
    out, err = io.StringIO(), io.StringIO()
    _o, _e = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        fn()
    finally:
        sys.stdout, sys.stderr = _o, _e
    return out.getvalue()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--mappers", type=int, default=4)
    p.add_argument("--reducers", type=int, default=2)
    p.add_argument("--out", default="results/output.tsv")
    a = p.parse_args()
    lines = Path(a.input).read_text(encoding="utf-8-sig", errors="replace").splitlines(True)
    rows = run(lines, a.mappers, a.reducers)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("task\tkey\tflights\tavg_price\tmin_price\tmax_price\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"{len(rows)} result rows written to {a.out}")


if __name__ == "__main__":
    main()
