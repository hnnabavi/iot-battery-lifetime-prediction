from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Iterator

import pandas as pd

from .core import CellParameters


def _optional_float(v):
    if pd.isna(v) or str(v).strip() == "":
        return None
    return float(v)


class BatteryDatabase:
    def __init__(self, cells: dict[str, CellParameters]):
        self._cells = cells
        self._aliases = {}
        for key, cell in cells.items():
            aliases = {
                key, cell.label, key.lower(), cell.label.lower(),
                key.replace("-", "").lower(), cell.label.replace("-", "").lower(),
            }
            for alias in aliases:
                self._aliases[alias] = key

    @classmethod
    def default(cls) -> "BatteryDatabase":
        path = files("iot_battery_life").joinpath("data/battery_parameters.csv")
        with path.open("r", encoding="utf-8") as f:
            df = pd.read_csv(f, skipinitialspace=True)
        return cls._from_dataframe(df)

    @classmethod
    def from_csv(cls, path: str | Path) -> "BatteryDatabase":
        return cls._from_dataframe(pd.read_csv(path, skipinitialspace=True))

    @classmethod
    def _from_dataframe(cls, df: pd.DataFrame) -> "BatteryDatabase":
        cells = {}
        for _, r in df.iterrows():
            cell = CellParameters(
                id=str(r["id"]), label=str(r["label"]), family=str(r["family"]), tf=str(r["tf"]),
                V=float(r["V"]), C=float(r["C"]), i_ref=float(r["i_ref"]), n=float(r["n"]),
                sdr=float(r["sdr"]), tmin=float(r["tmin"]), tmax=float(r["tmax"]), Ea_sd=float(r["Ea_sd"]),
                Ea_age=_optional_float(r.get("Ea_age")), fade1=_optional_float(r.get("fade1")),
                cycles=_optional_float(r.get("cycles")), ed=_optional_float(r.get("ed")),
                srctype=str(r.get("srctype", "")), source=str(r.get("source", "")),
            )
            cells[cell.id] = cell
        return cls(cells)

    def __getitem__(self, key: str) -> CellParameters:
        if key in self._cells:
            return self._cells[key]
        norm = key.lower()
        if norm in self._aliases:
            return self._cells[self._aliases[norm]]
        compact = key.replace("-", "").lower()
        if compact in self._aliases:
            return self._cells[self._aliases[compact]]
        raise KeyError(f"Unknown chemistry '{key}'. Available: {', '.join(self._cells)}")

    def __iter__(self) -> Iterator[CellParameters]:
        return iter(self._cells.values())

    def ids(self) -> list[str]:
        return list(self._cells.keys())
