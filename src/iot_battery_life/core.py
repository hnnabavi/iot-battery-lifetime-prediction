"""Core equations for the IoT battery service-life model.

All charge quantities are in mAh unless explicitly noted. Temperature inputs
are degrees Celsius. Activation energies in the CSV are kJ/mol.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional

import numpy as np
from scipy.interpolate import PchipInterpolator

R_GAS = 8.31446261815324
DAYS_PER_YEAR = 365.25

PRIMARY_TEMP_C = np.array([-60, -40, -20, 0, 20, 40, 60, 85], dtype=float)
PRIMARY_KT = np.array([0.30, 0.55, 0.80, 0.92, 1.00, 1.02, 1.00, 0.95], dtype=float)
LIION_TEMP_C = np.array([-20, -10, 0, 10, 20, 40, 60], dtype=float)
LIION_KT = np.array([0.50, 0.70, 0.85, 0.95, 1.00, 1.00, 0.97], dtype=float)


@dataclass(frozen=True)
class NodeProfile:
    load_voltage_v: float = 3.3
    converter_efficiency: float = 0.90
    sleep_current_mA: float = 0.002
    sense_current_mA: float = 5.0
    sense_time_s: float = 0.020
    mcu_current_mA: float = 12.0
    mcu_time_s: float = 0.050
    tx_current_mA: float = 30.0
    tx_time_s: float = 0.030

    @classmethod
    def default(cls) -> "NodeProfile":
        return cls()

    @property
    def event_charge_mAh(self) -> float:
        return (
            self.sense_current_mA * self.sense_time_s
            + self.mcu_current_mA * self.mcu_time_s
            + self.tx_current_mA * self.tx_time_s
        ) / 3600.0

    def daily_load_charge_mAh(self, events_per_day: float) -> float:
        if events_per_day < 0:
            raise ValueError("events_per_day must be non-negative")
        return 24.0 * self.sleep_current_mA + events_per_day * self.event_charge_mAh

    def daily_battery_charge_mAh(self, events_per_day: float, battery_voltage_v: float) -> float:
        if not (0 < self.converter_efficiency <= 1):
            raise ValueError("converter_efficiency must be in (0, 1]")
        if battery_voltage_v <= 0:
            raise ValueError("battery_voltage_v must be positive")
        q_load = self.daily_load_charge_mAh(events_per_day)
        return q_load * self.load_voltage_v / (self.converter_efficiency * battery_voltage_v)


@dataclass(frozen=True)
class CellParameters:
    id: str
    label: str
    family: str
    tf: str
    V: float
    C: float
    i_ref: float
    n: float
    sdr: float
    tmin: float
    tmax: float
    Ea_sd: float
    Ea_age: Optional[float] = None
    fade1: Optional[float] = None
    cycles: Optional[float] = None
    ed: Optional[float] = None
    srctype: str = ""
    source: str = ""


@dataclass(frozen=True)
class LifeResult:
    chemistry: str
    temperature_c: float
    events_per_day: float
    status: str
    q_load_mAh_day: float
    q_battery_mAh_day: float
    q_self_discharge_mAh_day: float
    k_rate: float
    k_temperature: float
    effective_capacity_mAh: float
    capacity_life_years: Optional[float]
    retention_life_years: Optional[float]
    reported_life_years: Optional[float]
    limiting_mechanism: str


def _arrhenius_factor(temperature_c: float, reference_c: float, Ea_kJ_mol: float) -> float:
    t = temperature_c + 273.15
    tref = reference_c + 273.15
    if t <= 0 or tref <= 0:
        raise ValueError("temperature below absolute zero")
    Ea = Ea_kJ_mol * 1000.0
    return math.exp(-Ea / R_GAS * (1.0 / t - 1.0 / tref))


def temperature_factor(tf: str, temperature_c: float) -> float:
    if tf == "primary":
        x, y = PRIMARY_TEMP_C, PRIMARY_KT
    elif tf == "liion":
        x, y = LIION_TEMP_C, LIION_KT
    else:
        raise ValueError(f"unknown temperature-family key: {tf}")
    interp = PchipInterpolator(x, y, extrapolate=True)
    return float(np.clip(interp(float(temperature_c)), 0.0, 1.25))


def rate_factor(cell: CellParameters, average_external_current_mA: float) -> float:
    if average_external_current_mA <= 0:
        return 1.15
    raw = (cell.i_ref / average_external_current_mA) ** (cell.n - 1.0)
    return float(np.clip(raw, 0.50, 1.15))


def self_discharge_mAh_day(cell: CellParameters, temperature_c: float) -> float:
    base = cell.C * 1000.0 * (cell.sdr / 100.0) / 30.0
    return base * _arrhenius_factor(temperature_c, 20.0, cell.Ea_sd)


def retention_life_years(cell: CellParameters, temperature_c: float, retained_fraction: float = 0.80) -> float:
    if not (0 < retained_fraction < 1):
        raise ValueError("retained_fraction must be between 0 and 1")
    annual_fraction = 12.0 * cell.sdr / 100.0
    if annual_fraction <= 0:
        return math.inf
    if annual_fraction >= 1:
        raise ValueError("annualized self-discharge is >=100%; retention approximation invalid")
    k20 = -math.log(1.0 - annual_fraction)
    kT = k20 * _arrhenius_factor(temperature_c, 20.0, cell.Ea_sd)
    return -math.log(retained_fraction) / kT


def calendar_age_factor(cell: CellParameters, life_years: float, temperature_c: float) -> float:
    if cell.family != "secondary" or cell.fade1 is None or cell.Ea_age is None:
        return 1.0
    acceleration = _arrhenius_factor(temperature_c, 25.0, cell.Ea_age)
    factor = 1.0 - (cell.fade1 / 100.0) * math.sqrt(max(life_years, 0.0)) * acceleration
    return float(np.clip(factor, 0.0, 1.0))


def service_life(
    cell: CellParameters,
    node: NodeProfile,
    temperature_c: float,
    events_per_day: float,
    harvest_mA: float = 0.0,
    retention_fraction: float = 0.80,
) -> LifeResult:
    q_load = node.daily_load_charge_mAh(events_per_day)
    q_batt = node.daily_battery_charge_mAh(events_per_day, cell.V)

    if temperature_c < cell.tmin or temperature_c > cell.tmax:
        return LifeResult(
            cell.id, temperature_c, events_per_day, "out_of_spec",
            q_load, q_batt, math.nan, math.nan, math.nan, math.nan,
            None, None, None, "out_of_spec_temperature"
        )

    avg_external_current = q_batt / 24.0
    kr = rate_factor(cell, avg_external_current)
    kt = temperature_factor(cell.tf, temperature_c)
    cap_mAh = cell.C * 1000.0 * kr * kt
    q_sd = self_discharge_mAh_day(cell, temperature_c)
    net_daily = q_batt + q_sd - 24.0 * harvest_mA

    if net_daily <= 0:
        return LifeResult(
            cell.id, temperature_c, events_per_day, "energy_autonomous",
            q_load, q_batt, q_sd, kr, kt, cap_mAh,
            math.inf,
            retention_life_years(cell, temperature_c, retention_fraction) if cell.family == "primary" else None,
            math.inf, "harvest_exceeds_average_demand"
        )

    base_years = cap_mAh / net_daily / DAYS_PER_YEAR

    if cell.family == "primary":
        lret = retention_life_years(cell, temperature_c, retention_fraction)
        reported = min(base_years, lret)
        limiter = "retention" if lret <= base_years else "capacity_and_load"
        return LifeResult(
            cell.id, temperature_c, events_per_day, "ok",
            q_load, q_batt, q_sd, kr, kt, cap_mAh,
            base_years, lret, reported, limiter
        )

    life = base_years
    for _ in range(200):
        new_life = base_years * calendar_age_factor(cell, life, temperature_c)
        if abs(new_life - life) < 1e-10:
            life = new_life
            break
        life = new_life

    return LifeResult(
        cell.id, temperature_c, events_per_day, "ok",
        q_load, q_batt, q_sd, kr, kt, cap_mAh,
        base_years, None, life, "capacity_load_self_discharge_calendar_ageing"
    )


def harvest_break_even_mA(cell: CellParameters, node: NodeProfile, temperature_c: float, events_per_day: float) -> float:
    if temperature_c < cell.tmin or temperature_c > cell.tmax:
        return math.nan
    q_batt = node.daily_battery_charge_mAh(events_per_day, cell.V)
    q_sd = self_discharge_mAh_day(cell, temperature_c)
    return (q_batt + q_sd) / 24.0
