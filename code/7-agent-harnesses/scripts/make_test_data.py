"""Generate test_data/sensor_readings.csv — 1M rows of synthetic sensor data.

Sized to clear the cuDF 100K-row gate so Exercise 4 shows real GPU work.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROWS = 1_000_000
OUT = Path(__file__).parent.parent / "test_data" / "sensor_readings.csv"

rng = np.random.default_rng(42)
df = pd.DataFrame(
    {
        "device_id": rng.integers(0, 500, ROWS),
        "timestamp": pd.Timestamp("2026-01-01")
        + pd.to_timedelta(rng.integers(0, 90 * 24 * 3600, ROWS), unit="s"),
        "sensor_type": rng.choice(["temp", "humidity", "pressure", "vibration"], ROWS),
        "reading": np.round(rng.normal(50, 15, ROWS), 3),
        "battery_pct": rng.integers(1, 101, ROWS),
    }
)

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Wrote {ROWS:,} rows to {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
