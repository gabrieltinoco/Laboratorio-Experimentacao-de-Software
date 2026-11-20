import pandas as pd

from analysis.lab05.validate import validate
from analysis.lab05.power import simulate_power


def test_validate_flags_error():
    df = pd.DataFrame([{"error": "failed"}])
    assert any("erro" in item.lower() for item in validate(df, {}, "pilot"))


def test_validate_flags_hash_mismatch():
    df = pd.DataFrame([{"valid": False, "error": ""}])
    assert any("inválido" in item.lower() for item in validate(df, {}, "pilot"))


def test_validate_counts_timeouts():
    df = pd.DataFrame([{"timeout": True, "error": ""}])
    assert any("timeout" in item.lower() for item in validate(df, {}, "pilot"))


def test_power_identical_near_alpha():
    import numpy as np
    power = simulate_power(np.ones(10), np.ones(10), 10, n_sim=1000)
    assert 0.0 <= power <= 0.09


def test_power_shifted_high():
    import numpy as np
    power = simulate_power(np.zeros(20), np.arange(20) + 10, 10, n_sim=1000)
    assert power > 0.95
