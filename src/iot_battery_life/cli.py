from __future__ import annotations

import argparse
import csv
import json
import math
import numpy as np

from .core import NodeProfile, harvest_break_even_mA, service_life
from .parameters import BatteryDatabase
from .plots import plot_reporting_curve


def _result_dict(r):
    return {
        "chemistry": r.chemistry,
        "temperature_c": r.temperature_c,
        "events_per_day": r.events_per_day,
        "status": r.status,
        "q_load_mAh_day": r.q_load_mAh_day,
        "q_battery_mAh_day": r.q_battery_mAh_day,
        "q_self_discharge_mAh_day": r.q_self_discharge_mAh_day,
        "k_rate": r.k_rate,
        "k_temperature": r.k_temperature,
        "effective_capacity_mAh": r.effective_capacity_mAh,
        "capacity_life_years": r.capacity_life_years,
        "retention_life_years": r.retention_life_years,
        "reported_life_years": r.reported_life_years,
        "limiting_mechanism": r.limiting_mechanism,
    }


def build_parser():
    p = argparse.ArgumentParser(prog="iot-battery-life", description="Battery lifetime model for low-power IoT")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List bundled chemistries")

    e = sub.add_parser("estimate")
    e.add_argument("--chemistry", required=True)
    e.add_argument("--temperature", type=float, required=True)
    e.add_argument("--events", type=float, required=True)
    e.add_argument("--harvest-mA", type=float, default=0.0)

    c = sub.add_parser("curve")
    c.add_argument("--chemistry", required=True, nargs="+")
    c.add_argument("--temperature", type=float, default=20.0)
    c.add_argument("--min-events", type=float, default=1.0)
    c.add_argument("--max-events", type=float, default=1440.0)
    c.add_argument("--points", type=int, default=60)
    c.add_argument("--output", default="battery_curve.png")

    comp = sub.add_parser("compare")
    comp.add_argument("--temperature", type=float, required=True)
    comp.add_argument("--events", type=float, required=True)
    comp.add_argument("--output", default="comparison.csv")

    h = sub.add_parser("harvest")
    h.add_argument("--temperature", type=float, required=True)
    h.add_argument("--events", type=float, nargs="+", required=True)
    h.add_argument("--output", default="harvest_break_even.csv")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    db = BatteryDatabase.default()
    node = NodeProfile.default()

    if args.command == "list":
        for cell in db:
            print(f"{cell.id:10s} {cell.family:9s} {cell.V:g} V {cell.C:g} Ah {cell.srctype}")
        return

    if args.command == "estimate":
        r = service_life(db[args.chemistry], node, args.temperature, args.events, args.harvest_mA)
        print(json.dumps(_result_dict(r), indent=2, allow_nan=True))
        return

    if args.command == "curve":
        xs = np.geomspace(args.min_events, args.max_events, args.points)
        plot_reporting_curve([db[x] for x in args.chemistry], node, args.temperature, xs, args.output)
        print(f"Wrote {args.output}")
        return

    if args.command == "compare":
        rows = [_result_dict(service_life(cell, node, args.temperature, args.events)) for cell in db]
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"Wrote {args.output}")
        return

    if args.command == "harvest":
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["chemistry","temperature_c","events_per_day","break_even_mA","break_even_uA"])
            for cell in [c for c in db if c.family == "secondary"]:
                for events in args.events:
                    mA = harvest_break_even_mA(cell, node, args.temperature, events)
                    w.writerow([cell.id,args.temperature,events,mA,mA*1000 if not math.isnan(mA) else math.nan])
        print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
