from dataclasses import dataclass

import pytest

from ringresonator_study import AddDropRing, Coupler, RingModulator
from ringresonator_study.modulation import (
    LinearVoltageOpticalModel,
    TableVoltageOpticalModel,
    analyze_operating_points,
    find_best_operating_point,
    rank_operating_points,
)


def build_modulator() -> RingModulator:
    return RingModulator(
        ring=AddDropRing(
            input_coupler=Coupler.lossless_from_t(0.95),
            output_coupler=Coupler.lossless_from_t(0.95),
            alpha=1.0,
        ),
        length_um=30.0,
        voltage_model=LinearVoltageOpticalModel(
            n_eff0=2.4,
            dn_eff_dv=-1e-3,
            loss_db_per_cm0=2.0,
            dloss_db_per_cm_dv=0.5,
        ),
    )


def test_analyze_operating_points_evaluates_all_candidates():
    points = analyze_operating_points(
        build_modulator(),
        wavelengths_um=[1.54, 1.55],
        bias_voltages=[0.5, 1.0, 1.5],
        drive_voltage=0.4,
    )

    assert len(points) == 6
    assert points[0].voltage_low == pytest.approx(0.3)
    assert points[0].voltage_high == pytest.approx(0.7)
    assert points[0].score == pytest.approx(
        points[0].extinction_ratio_db - points[0].insertion_loss_db
    )


def test_rank_operating_points_filters_and_limits_results():
    points = analyze_operating_points(
        build_modulator(),
        wavelengths_um=[1.54, 1.55],
        bias_voltages=[0.5, 1.0],
        drive_voltage=0.4,
    )

    ranked = rank_operating_points(
        points,
        max_insertion_loss_db=max(point.insertion_loss_db for point in points),
        min_extinction_ratio_db=min(point.extinction_ratio_db for point in points),
        limit=1,
    )

    assert len(ranked) == 1
    assert ranked[0].score == max(point.score for point in points)


def test_find_best_operating_point_returns_highest_score():
    points = analyze_operating_points(
        build_modulator(),
        wavelengths_um=[1.54, 1.55],
        bias_voltages=[0.5, 1.0],
        drive_voltage=0.4,
    )

    best = find_best_operating_point(
        build_modulator(),
        wavelengths_um=[1.54, 1.55],
        bias_voltages=[0.5, 1.0],
        drive_voltage=0.4,
    )

    assert best.score == max(point.score for point in points)


def test_find_best_operating_point_rejects_unsatisfied_constraints():
    with pytest.raises(ValueError):
        find_best_operating_point(
            build_modulator(),
            wavelengths_um=[1.55],
            bias_voltages=[0.5],
            drive_voltage=0.4,
            min_extinction_ratio_db=1e9,
        )


def test_analyze_operating_points_skips_invalid_table_voltage_candidates():
    modulator = RingModulator(
        ring=AddDropRing(
            input_coupler=Coupler.lossless_from_t(0.95),
            output_coupler=Coupler.lossless_from_t(0.95),
            alpha=1.0,
        ),
        length_um=30.0,
        voltage_model=TableVoltageOpticalModel(
            rows=[
                {"voltage": 0.0, "n_eff": 2.4, "loss_db_per_cm": 2.0},
                {"voltage": 1.0, "n_eff": 2.399, "loss_db_per_cm": 3.0},
            ]
        ),
    )

    points = analyze_operating_points(
        modulator,
        wavelengths_um=[1.55],
        bias_voltages=[0.1, 0.5, 0.9],
        drive_voltage=0.4,
    )

    assert [point.bias_voltage for point in points] == [0.5]


def test_analyze_operating_points_can_raise_invalid_table_voltage_candidates():
    modulator = RingModulator(
        ring=AddDropRing(
            input_coupler=Coupler.lossless_from_t(0.95),
            output_coupler=Coupler.lossless_from_t(0.95),
            alpha=1.0,
        ),
        length_um=30.0,
        voltage_model=TableVoltageOpticalModel(
            rows=[
                {"voltage": 0.0, "n_eff": 2.4, "loss_db_per_cm": 2.0},
                {"voltage": 1.0, "n_eff": 2.399, "loss_db_per_cm": 3.0},
            ]
        ),
    )

    with pytest.raises(ValueError):
        analyze_operating_points(
            modulator,
            wavelengths_um=[1.55],
            bias_voltages=[0.1],
            drive_voltage=0.4,
            skip_invalid=False,
        )


def test_analyze_operating_points_rejects_invalid_inputs():
    modulator = build_modulator()

    with pytest.raises(ValueError):
        analyze_operating_points(
            modulator,
            wavelengths_um=[1.55],
            bias_voltages=[0.5],
            drive_voltage=0.0,
        )

    with pytest.raises(ValueError):
        analyze_operating_points(
            modulator,
            wavelengths_um=[1.55],
            bias_voltages=[0.5],
            drive_voltage=0.4,
            port="monitor",
        )


def test_rank_operating_points_rejects_invalid_limit():
    with pytest.raises(ValueError):
        rank_operating_points([], limit=0)


@dataclass(frozen=True)
class AlwaysInvalidModulator:
    def metrics(self, **_kwargs):
        raise ValueError("invalid")


def test_analyze_operating_points_rejects_when_all_candidates_are_skipped():
    with pytest.raises(ValueError):
        analyze_operating_points(
            AlwaysInvalidModulator(),
            wavelengths_um=[1.55],
            bias_voltages=[0.5],
            drive_voltage=0.4,
        )
