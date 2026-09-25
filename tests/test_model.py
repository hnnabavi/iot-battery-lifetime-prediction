import math

from iot_battery_life import BatteryDatabase, NodeProfile, harvest_break_even_mA, service_life


def test_event_charge_units():
    node = NodeProfile.default()
    assert math.isclose(node.event_charge_mAh, 0.00044444444444444447, rel_tol=0, abs_tol=1e-12)


def test_li_socl2_24_per_day_retention_limited():
    db = BatteryDatabase.default(); node = NodeProfile.default()
    r = service_life(db["Li-SOCl2"], node, 20, 24)
    assert r.status == "ok"
    assert r.limiting_mechanism == "retention"
    assert math.isclose(r.reported_life_years, 22.29, rel_tol=0.002)


def test_li_socl2_1440_per_day_capacity_limited():
    db = BatteryDatabase.default(); node = NodeProfile.default()
    r = service_life(db["Li-SOCl2"], node, 20, 1440)
    assert r.limiting_mechanism == "capacity_and_load"
    assert math.isclose(r.reported_life_years, 10.59, rel_tol=0.01)


def test_lfp_harvest_break_even():
    db = BatteryDatabase.default(); node = NodeProfile.default()
    uA = 1000 * harvest_break_even_mA(db["LFP"], node, 20, 24)
    assert math.isclose(uA, 89.6, rel_tol=0.01)


def test_out_of_spec_temperature():
    db = BatteryDatabase.default(); node = NodeProfile.default()
    r = service_life(db["NMC"], node, -30, 24)
    assert r.status == "out_of_spec"
    assert r.reported_life_years is None
