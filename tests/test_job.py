import io
import random
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "mapreduce"))

import local_run  # noqa: E402
import mapper  # noqa: E402


@pytest.fixture(scope="module")
def sample(tmp_path_factory):
    p = tmp_path_factory.mktemp("d") / "sample.csv"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_sample.py"), str(p), "--rows", "3000"], check=True, capture_output=True)
    return p


def as_frame(rows):
    df = pd.DataFrame([r.split("\t") for r in rows], columns=["task", "key", "flights", "avg", "min", "max"])
    df[["avg", "min", "max"]] = df[["avg", "min", "max"]].astype(float)
    df["flights"] = df["flights"].astype(int)
    return df.set_index(["task", "key"])


def test_matches_pandas(sample):
    lines = sample.read_text().splitlines(True)
    got = as_frame(local_run.run(lines, mappers=3, reducers=2))
    df = pd.read_csv(sample)
    exp = df.groupby("Airline")["Price"].agg(["count", "mean", "min", "max"])
    for airline, r in exp.iterrows():
        g = got.loc[("AIRLINE", airline)]
        assert g["flights"] == r["count"]
        assert g["avg"] == pytest.approx(r["mean"], abs=0.01)
        assert g["min"] == r["min"] and g["max"] == r["max"]
    month = pd.to_datetime(df["Date_of_Journey"], format="%d/%m/%Y").dt.strftime("%Y-%m")
    exp_m = df.groupby(month)["Price"].mean()
    for m, v in exp_m.items():
        assert got.loc[("MONTH", m), "avg"] == pytest.approx(v, abs=0.01)


def test_result_does_not_depend_on_cluster_layout_or_order(sample):
    lines = sample.read_text().splitlines(True)
    base = local_run.run(lines, mappers=1, reducers=1, combine=False)
    shuffled = [lines[0]] + random.Random(3).sample(lines[1:], len(lines) - 1)
    for m, r in [(4, 3), (7, 1), (2, 5)]:
        assert local_run.run(shuffled, mappers=m, reducers=r) == base


def test_both_date_formats_are_read():
    out = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = out
    try:
        mapper.main(io.StringIO("Airline,Date_of_Journey,Source,Destination,Price\nA,24/03/2019,X,Y,100\nA,24-03-2019,X,Y,200\n"))
    finally:
        sys.stdout = sys_stdout
    months = [ln for ln in out.getvalue().splitlines() if ln.startswith("MONTH|")]
    assert len(months) == 2 and all("2019-03" in m for m in months)


def test_bad_rows_are_skipped():
    out, err = io.StringIO(), io.StringIO()
    so, se = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        mapper.main(io.StringIO("Airline,Date_of_Journey,Source,Destination,Price\nA,24/03/2019,X,Y,abc\n,24/03/2019,X,Y,10\n"))
    finally:
        sys.stdout, sys.stderr = so, se
    assert out.getvalue() == ""
    assert err.getvalue().count("bad_row") == 2


def test_original_reducer_breaks_when_values_arrive_unsorted():
    """Documents the bug in the coursework version (see docs/coursework-review.md).

    Hadoop sorts on the key, which for the original mapper was only the task name. Lines for
    different airlines then arrive mixed, and the reducer prints a new partial average every
    time the airline changes.
    """
    lines = ["AveragePrice\tA\t100", "AveragePrice\tB\t300", "AveragePrice\tA\t200"]
    res = subprocess.run([sys.executable, str(ROOT / "original" / "reducer.py")], input="\n".join(lines) + "\n", text=True, capture_output=True)
    out = res.stdout.strip().splitlines()
    assert len(out) == 3  # three outputs for two airlines
    assert "Average Price for A: 100.00" in out  # A's true average is 150


def test_original_mapper_drops_dates_with_dashes():
    line = "IndiGo,24-03-2019,Banglore,New Delhi,BLR-DEL,22:20,01:10,2h 50m,non-stop,No info,3897\n"
    res = subprocess.run([sys.executable, str(ROOT / "original" / "mapper.py")], input=line, text=True, capture_output=True)
    assert "PriceDistribution" not in res.stdout
    assert "Error processing line" in res.stderr
