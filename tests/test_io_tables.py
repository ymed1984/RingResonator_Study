from dataclasses import dataclass
from pathlib import Path

import pytest

from ringresonator_study.io import write_csv_rows


@dataclass(frozen=True)
class Row:
    voltage: float
    power: float


def test_write_csv_rows_writes_dict_rows(tmp_path: Path):
    output_path = write_csv_rows(
        [
            {"voltage": 0.0, "power": 0.5},
            {"voltage": 1.0, "power": 0.7},
        ],
        tmp_path / "rows.csv",
    )

    assert output_path.read_text().splitlines() == [
        "voltage,power",
        "0.0,0.5",
        "1.0,0.7",
    ]


def test_write_csv_rows_writes_dataclass_rows(tmp_path: Path):
    output_path = write_csv_rows(
        [Row(voltage=0.0, power=0.5)],
        tmp_path / "rows.csv",
    )

    assert output_path.read_text().splitlines() == [
        "voltage,power",
        "0.0,0.5",
    ]


def test_write_csv_rows_accepts_fieldnames(tmp_path: Path):
    output_path = write_csv_rows(
        [{"voltage": 0.0, "power": 0.5, "phase": 0.1}],
        tmp_path / "rows.csv",
        fieldnames=["power", "voltage"],
    )

    assert output_path.read_text().splitlines() == [
        "power,voltage",
        "0.5,0.0",
    ]


def test_write_csv_rows_rejects_empty_rows(tmp_path: Path):
    with pytest.raises(ValueError):
        write_csv_rows([], tmp_path / "rows.csv")
