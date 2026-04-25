RingResonator Study
===================

This repository contains small Python models for ring resonator studies.

## Add-drop ring

The first implemented model is a simple add-drop ring resonator:

```python
from ringresonator_study import AddDropRing, Coupler

ring = AddDropRing(
    input_coupler=Coupler(t=0.95, kappa=1j * (1 - 0.95**2) ** 0.5),
    output_coupler=Coupler(t=0.95, kappa=1j * (1 - 0.95**2) ** 0.5),
    alpha=0.98,
)

response = ring.response(phi=0.0)
print(response["through"].amplitude, response["through"].power, response["through"].phase)
print(response["drop"].amplitude, response["drop"].power, response["drop"].phase)
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
uv run python plot_add_drop.py
```

The graph is written to `output/add_drop_response.png`.
