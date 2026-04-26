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
    series_coupled.py    2段series-coupled ringの伝達関数
    vernier.py           2リングVernier filterの長さ合成と応答
  plotting/
    add_drop.py          add-drop応答のグラフ化

examples/
  add_drop_console.py    数値を標準出力する実行例
  plot_add_drop.py       パワーと位相のグラフを生成する実行例

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
uv run python -m unittest discover -s tests -p 'test_*.py'
```

Generate a graph with:

```sh
uv run python examples/plot_add_drop.py
uv run python examples/plot_series_coupled.py
uv run python examples/plot_vernier.py
```

The graphs are written under `output/`.

## Series-coupled rings

`SeriesCoupledRings` is currently implemented for two rings. The constructor
already takes ring couplers and losses as sequences so the model can grow toward
N-stage transfer matrices later.

```python
from ringresonator_study import Coupler, SeriesCoupledRings

model = SeriesCoupledRings.two_ring(
    input_coupler=Coupler.lossless_from_t(0.95),
    ring_coupler=Coupler.lossless_from_t(0.90),
    output_coupler=Coupler.lossless_from_t(0.95),
    alpha_1=0.98,
    alpha_2=0.98,
)

response = model.response_for_wavelength(
    1.55,
    n_effs=(2.4, 2.4),
    lengths=(30.0, 31.0),
)
print(response.drop.power, response.drop.phase)
```

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
