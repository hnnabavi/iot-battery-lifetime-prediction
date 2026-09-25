"""Clone -> install -> run this file to reproduce reference outputs."""
from pathlib import Path
import csv

from iot_battery_life import BatteryDatabase, NodeProfile, harvest_break_even_mA, service_life
from iot_battery_life.plots import plot_reporting_curve

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output_example"
OUT.mkdir(exist_ok=True)

db = BatteryDatabase.default()
node = NodeProfile.default()

plot_reporting_curve(
    cells=[db["Li-SOCl2"], db["Li-FeS2"], db["Li-MnO2"], db["Li-CFx"], db["LFP"]],
    node=node,
    temperature_c=20,
    events_per_day=[1,2,6,12,24,48,96,144,288,576,1440],
    output=OUT / "battery_lifetime_curve.png",
)

with (OUT / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["chemistry","status","reported_life_years","limiting_mechanism","srctype"])
    for cell in db:
        r = service_life(cell, node, 20, 24)
        w.writerow([cell.id,r.status,r.reported_life_years,r.limiting_mechanism,cell.srctype])

print("Reference event charge:", node.event_charge_mAh * 1000, "uAh/event")
print("Li-SOCl2 @20 C, 24/day:", service_life(db["Li-SOCl2"], node, 20, 24).reported_life_years, "years")
print("LFP harvest break-even @20 C, 24/day:", 1000*harvest_break_even_mA(db["LFP"], node, 20, 24), "uA")
