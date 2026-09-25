"""Declared-range epistemic uncertainty example used in the manuscript."""
from dataclasses import replace
import numpy as np
from iot_battery_life import BatteryDatabase, NodeProfile, service_life

rng = np.random.default_rng(20260925)
db = BatteryDatabase.default()
cell = db["Li-SOCl2"]
node = NodeProfile.default()

def run(events_per_day: int, n_samples: int = 20000):
    out = np.empty(n_samples)
    for i in range(n_samples):
        c = replace(
            cell,
            C=cell.C * rng.uniform(0.90, 1.10),
            sdr=cell.sdr * rng.uniform(0.50, 1.50),
            n=rng.uniform(1.05, 1.15),
            Ea_sd=cell.Ea_sd * rng.uniform(0.80, 1.20),
        )
        ev = rng.uniform(0.80, 1.20)
        nd = replace(
            node,
            converter_efficiency=rng.uniform(0.85, 0.95),
            sleep_current_mA=node.sleep_current_mA * rng.uniform(0.50, 2.00),
            sense_current_mA=node.sense_current_mA * ev,
            mcu_current_mA=node.mcu_current_mA * ev,
            tx_current_mA=node.tx_current_mA * ev,
        )
        out[i] = service_life(c, nd, 20.0, events_per_day).reported_life_years
    p5, med, p95 = np.percentile(out, [5,50,95])
    print(f"{events_per_day}/day: P5={p5:.2f}, median={med:.2f}, P95={p95:.2f} years")

if __name__ == "__main__":
    run(24)
    run(1440)
