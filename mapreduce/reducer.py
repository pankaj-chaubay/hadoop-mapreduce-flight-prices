#!/usr/bin/env python3
"""Combiner and reducer for the flight price job.

Input lines are "TASK|key <TAB> sum,count,min,max", sorted by key (Hadoop does
the sort). Lines with the same key are merged. Sum, count, min and max can be
merged in any order and in any number of steps, so the same script works as a
combiner on each mapper and as the final reducer.

    --final   write readable output: task, key, flights, average, min, max
    (default) write the merged sum,count,min,max again (combiner mode)
"""

import sys


def merge(a, b):
    return (a[0] + b[0], a[1] + b[1], min(a[2], b[2]), max(a[3], b[3]))


def write(key, acc, final, out):
    if final:
        task, name = key.split("|", 1)
        out.write(f"{task}\t{name}\t{acc[1]}\t{acc[0] / acc[1]:.2f}\t{acc[2]:.2f}\t{acc[3]:.2f}\n")
    else:
        out.write(f"{key}\t{acc[0]},{acc[1]},{acc[2]},{acc[3]}\n")


def main(stream=sys.stdin, out=sys.stdout, final=False) -> None:
    current, acc = None, None
    for line in stream:
        line = line.rstrip("\n")
        if not line:
            continue
        key, value = line.split("\t", 1)
        s, c, lo, hi = value.split(",")
        rec = (float(s), int(c), float(lo), float(hi))
        if key == current:
            acc = merge(acc, rec)
        else:
            if current is not None:
                write(current, acc, final, out)
            current, acc = key, rec
    if current is not None:
        write(current, acc, final, out)


if __name__ == "__main__":
    main(final="--final" in sys.argv[1:])
