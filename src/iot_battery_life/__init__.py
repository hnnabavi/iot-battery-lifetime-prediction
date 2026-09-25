"""IoT Battery Life package."""
from .core import (
    CellParameters,
    LifeResult,
    NodeProfile,
    calendar_age_factor,
    harvest_break_even_mA,
    rate_factor,
    retention_life_years,
    self_discharge_mAh_day,
    service_life,
    temperature_factor,
)
from .parameters import BatteryDatabase

__all__ = [
    "BatteryDatabase", "CellParameters", "LifeResult", "NodeProfile",
    "service_life", "harvest_break_even_mA", "temperature_factor",
    "rate_factor", "self_discharge_mAh_day", "retention_life_years",
    "calendar_age_factor",
]

__version__ = "0.1.0"
