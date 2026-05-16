import pytest

from ringresonator_study.modulation import resonance_shifts, track_resonance


def test_track_resonance_finds_through_dip_per_voltage():
    rows = [
        {"voltage": 0.0, "wavelength": 1.54, "through_power": 0.8},
        {"voltage": 0.0, "wavelength": 1.55, "through_power": 0.1},
        {"voltage": 1.0, "wavelength": 1.54, "through_power": 0.2},
        {"voltage": 1.0, "wavelength": 1.55, "through_power": 0.7},
    ]

    resonances = track_resonance(rows, port="through", mode="min")

    assert resonances == [
        {
            "voltage": 0.0,
            "resonance_wavelength": 1.55,
            "power": 0.1,
            "transmission_db": pytest.approx(-10.0),
        },
        {
            "voltage": 1.0,
            "resonance_wavelength": 1.54,
            "power": 0.2,
            "transmission_db": pytest.approx(-6.989700043360188),
        },
    ]


def test_track_resonance_finds_drop_peak_per_voltage():
    rows = [
        {"voltage": 0.0, "wavelength": 1.54, "drop_power": 0.1},
        {"voltage": 0.0, "wavelength": 1.55, "drop_power": 0.9},
        {"voltage": 1.0, "wavelength": 1.54, "drop_power": 0.8},
        {"voltage": 1.0, "wavelength": 1.55, "drop_power": 0.2},
    ]

    resonances = track_resonance(rows, port="drop", mode="max")

    assert [row["resonance_wavelength"] for row in resonances] == [1.55, 1.54]


def test_resonance_shifts_use_first_voltage_by_default():
    resonances = [
        {"voltage": 0.0, "resonance_wavelength": 1.5500},
        {"voltage": 1.0, "resonance_wavelength": 1.5505},
    ]

    shifts = resonance_shifts(resonances)

    assert shifts[0]["delta_wavelength_pm"] == pytest.approx(0.0)
    assert shifts[1]["delta_wavelength_pm"] == pytest.approx(500.0)


def test_resonance_shifts_can_use_reference_voltage():
    resonances = [
        {"voltage": 0.0, "resonance_wavelength": 1.5500},
        {"voltage": 1.0, "resonance_wavelength": 1.5505},
    ]

    shifts = resonance_shifts(resonances, reference_voltage=1.0)

    assert shifts[0]["delta_wavelength_pm"] == pytest.approx(-500.0)
    assert shifts[1]["delta_wavelength_pm"] == pytest.approx(0.0)


def test_track_resonance_rejects_empty_rows():
    with pytest.raises(ValueError):
        track_resonance([])


def test_track_resonance_rejects_unknown_mode():
    with pytest.raises(ValueError):
        track_resonance([], mode="center")
