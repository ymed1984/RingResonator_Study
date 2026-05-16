RingResonator Study
===================

This repository contains small Python models for ring resonator studies.

## Directory layout

```text
ringresonator_study/
  components.py          Couplerなどの再利用できる光部品
  phase.py               波長・実効屈折率・周回長から位相を計算
  responses.py           複素振幅からpower/phaseを明示する応答型
  models/
    add_drop.py          add-drop型リング共振器の伝達関数
    ring_modulator.py    電圧依存の単一リング変調器
    series_coupled.py    Ansys型CROW/series-coupled ringの伝達関数
    vernier.py           2リングVernier filterの長さ合成と応答
  modulation/
    voltage_models.py    bias voltageからn_eff/loss/alphaを計算
    metrics.py           ER/IL/OMAなどの変調指標
  plotting/
    add_drop.py          add-drop応答のグラフ化
    modulator.py         バイアス依存スペクトルのグラフ化

examples/
  add_drop_console.py    数値を標準出力する実行例
  plot_add_drop.py       パワーと位相のグラフを生成する実行例
  plot_ring_modulator_bias.py
                          波長掃引と複数バイアスの変調依存グラフ

tests/
  test_add_drop.py       add-dropモデルの最小検証
```

## Relationship

```text
Coupler(t, kappa)
        |
        v
AddDropRing(input_coupler, output_coupler, alpha)
        |
        |  phi = 2*pi*n_eff*length/wavelength
        v
AddDropResponse
  |                 |
  v                 v
through           drop
PortResponse      PortResponse
  |                 |
  +--> amplitude    +--> amplitude
  +--> power        +--> power
  +--> phase        +--> phase

plot_add_drop_response(...)
        ^
        |
      spectrum(...)
```

`t` and `kappa` are field-amplitude coefficients. The model keeps
complex amplitudes as the primary result, then derives power and phase from them:

- `power = abs(amplitude) ** 2`
- `phase = arg(amplitude)` in radians

## Add-drop ring

The first implemented model is a simple add-drop ring resonator:

```python
from ringresonator_study import AddDropRing, Coupler

ring = AddDropRing(
    input_coupler=Coupler.lossless_from_t(0.95),
    output_coupler=Coupler.lossless_from_t(0.95),
    alpha=0.98,
)

response = ring.response(phi=0.0)
print(response.through.amplitude, response.through.power, response.through.phase)
print(response.drop.amplitude, response.drop.power, response.drop.phase)
```

Definitions:

- `t`: through/self-coupling field-amplitude coefficient.
- `kappa`: cross-coupling field-amplitude coefficient.
- `alpha`: round-trip field transmission of the ring.
- `phi`: round-trip phase in radians.
- `power`: `abs(amplitude) ** 2`.
- `phase`: principal optical phase in radians.

For an ideal lossless coupler, `abs(t)**2 + abs(kappa)**2 == 1`.

Run tests with:

```sh
uv run pytest
```

Generate a graph with:

```sh
uv run python examples/plot_add_drop.py
uv run python examples/plot_series_coupled.py
uv run python examples/plot_vernier.py
uv run python examples/plot_ring_modulator_bias.py
uv run python examples/plot_ring_modulator_transfer.py
```

The graphs are written under `output/`.

## Ring modulator

`RingModulator` keeps `AddDropRing` as the passive optical core and applies a
voltage-dependent optical state from `VoltageOpticalModel`. The first available
model is `LinearVoltageOpticalModel`, which maps bias voltage to `n_eff` and
round-trip field transmission `alpha` through a propagation-loss value.

```python
from pathlib import Path

from ringresonator_study import AddDropRing, Coupler, RingModulator
from ringresonator_study.modulation import LinearVoltageOpticalModel
from ringresonator_study.plotting import plot_bias_spectra

modulator = RingModulator(
    ring=AddDropRing(
        input_coupler=Coupler.lossless_from_t(0.95),
        output_coupler=Coupler.lossless_from_t(0.95),
        alpha=1.0,
    ),
    length_um=30.0,
    voltage_model=LinearVoltageOpticalModel(
        n_eff0=2.4,
        dn_eff_dv=-1e-4,
        loss_db_per_cm0=2.0,
        dloss_db_per_cm_dv=0.5,
    ),
)

rows = modulator.bias_spectrum(
    wavelengths_um=[1.54, 1.55, 1.56],
    voltages=[0.0, 0.5, 1.0, 1.5],
)

plot_bias_spectra(
    rows,
    port="through",
    y_axis="db",
    output_path=Path("output/ring_modulator_bias_spectrum.png"),
)
```

The bias spectrum output is tabular, so it can also be passed to pandas or
exported for comparison with future Lumerical FDE and Sentaurus Device results.

Tabular voltage models can be used when voltage-dependent optical parameters
come from simulation or measurement:

```python
from ringresonator_study.modulation import TableVoltageOpticalModel

voltage_model = TableVoltageOpticalModel(
    rows=[
        {"voltage": 0.0, "n_eff": 2.4000, "loss_db_per_cm": 2.0},
        {"voltage": 0.5, "n_eff": 2.3998, "loss_db_per_cm": 2.2},
        {"voltage": 1.0, "n_eff": 2.3995, "loss_db_per_cm": 2.5},
    ],
)
```

The same model can be loaded from CSV:

```python
voltage_model = TableVoltageOpticalModel.from_csv("data/modulator_bias_table.csv")
```

Expected CSV columns:

```csv
voltage,n_eff,loss_db_per_cm,n_group,capacitance_f
0.0,2.4000,2.0,4.2,3.5e-14
0.5,2.3998,2.2,4.2,3.3e-14
1.0,2.3995,2.5,4.2,3.1e-14
```

Resonance tracking and fixed-wavelength transfer curves are also available:

```python
from ringresonator_study.modulation import track_resonance
from ringresonator_study.plotting import plot_transfer_curve

resonances = track_resonance(rows, port="through", mode="min")
operating_wavelength = resonances[0]["resonance_wavelength"]

transfer_rows = modulator.transfer_curve(
    voltages=[0.0, 0.25, 0.5, 0.75, 1.0],
    wavelength_um=operating_wavelength,
)

plot_transfer_curve(
    transfer_rows,
    port="through",
    y_axis="db",
    output_path=Path("output/ring_modulator_transfer.png"),
)
```

Operating-point search can rank wavelength and bias candidates by static
modulation metrics:

```python
from ringresonator_study.modulation import find_best_operating_point

best = find_best_operating_point(
    modulator,
    wavelengths_um=[1.545, 1.550, 1.555],
    bias_voltages=[0.25, 0.50, 0.75],
    drive_voltage=0.5,
    port="through",
    max_insertion_loss_db=6.0,
)

print(best.wavelength, best.bias_voltage)
print(best.extinction_ratio_db, best.insertion_loss_db)
```

Wavelength shifts can also be converted to frequency-domain units:

```python
from ringresonator_study.units import wavelength_shift_to_frequency_shift_ghz

shift_ghz = wavelength_shift_to_frequency_shift_ghz(
    center_wavelength_um=1.55,
    delta_wavelength_um=0.001,
)
```

## Series-coupled rings

`SeriesCoupledRings` follows the Ansys/Lumerical Tunable CROW Filter structure:
identical rings are coupled in series, the edge rings couple to bus waveguides by
`kappa1`, and adjacent rings couple by `kappa2`. The nominal constructor uses
the example values `kappa1^2 = 0.13`, `kappa2^2 = 0.0047`, `n_eff = 2.566`,
`n_g = 3.893`, and `FSR = 79.5 GHz`.

```python
from ringresonator_study import SeriesCoupledRings

model = SeriesCoupledRings.ansys_nominal_two_ring(tuning_voltage=0.95)

print(model.design)
response = model.response_for_wavelength(1.55)
print(response.drop.power, response.drop.phase)
```

Reference note: `info/oe-19-18-17653.pdf` is Liu and Yariv, "Synthesis of
high-order bandpass filters based on coupled-resonator optical waveguides
(CROWs)". It is useful for the next step beyond the nominal Ansys CROW model:
deriving non-uniform coupling coefficients for higher-order Butterworth or Bessel
CROW filters.

## Vernier ring

`VernierRing` follows the compact behavior of the Luceda Academy Vernier sample:
two add-drop rings named `Ring1` and `Ring2` have different FSRs and are cascaded.
The useful transmission is the product of the two drop responses.

```python
from ringresonator_study import VernierRing

vernier = VernierRing.from_design(
    center_wavelength=1.55,
    ring1_fsr=0.001,
    target_vernier_factor=25.0,
    n_eff_ring1=2.4,
    n_eff_ring2=2.4,
    n_group=4.5,
    alpha=0.98,
)

print(vernier.design)
print(vernier.response_for_wavelength(1.55).transmission.power)
```
