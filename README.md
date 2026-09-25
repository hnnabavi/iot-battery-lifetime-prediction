# Battery Lifetime Prediction for Low-Power IoT Devices

Open-source Python reference implementation for the uncertainty-aware, cross-chemistry battery lifetime framework developed for low-power IoT and wireless sensor nodes.

## Features

- energy-normalized IoT duty-cycle modelling
- bounded Peukert-type rate correction
- temperature-dependent deliverable capacity
- Arrhenius-scaled self-discharge
- 80% retention bound for primary cells
- calendar ageing for rechargeable cells
- harvester break-even current
- provenance-tagged parameters for 12 lithium chemistries
- reproducibility tests and examples

> This is a transparent engineering screening model, not an electrochemical cell simulator. Chemistry-class defaults should be replaced with product-specific data before design decisions are made.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .

iot-battery-life estimate --chemistry Li-SOCl2 --temperature 20 --events 24
pytest -q
```

Reference-node event charge: **0.000444 mAh = 0.444 µAh/event**.

Baseline checks with the bundled parameters:

- Li-SOCl2, 20 °C, 24 events/day: ≈ **22.29 years**, retention-limited
- Li-SOCl2, 20 °C, 1440 events/day: ≈ **10.59 years**, load/capacity-limited
- LFP, 20 °C, 24 events/day: harvest break-even ≈ **89.6 µA**

## Python API

```python
from iot_battery_life import BatteryDatabase, NodeProfile, service_life

db = BatteryDatabase.default()
node = NodeProfile.default()

r = service_life(
    db["Li-SOCl2"],
    node,
    temperature_c=20,
    events_per_day=24,
)

print(r.reported_life_years)
print(r.limiting_mechanism)
```

## Repository and paper

Repository: https://github.com/hnnabavi/iot-battery-lifetime-prediction

Accompanying manuscript:

**Battery Lifetime Prediction for Low-Power IoT Devices: An Uncertainty-Aware Cross-Chemistry Framework**

After the first release is archived in Zenodo, the software DOI will be added here and to `CITATION.cff`.

## Licence

- Code: MIT
- Bundled parameter dataset: CC BY 4.0

Third-party datasets and datasheets retain their original licences and citation requirements.
