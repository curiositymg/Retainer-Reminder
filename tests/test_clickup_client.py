import calendar
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from retainer_reminder.clickup_client import month_start_ms


def test_month_start_is_utc_regardless_of_local_timezone():
    # 2026-08-10 18:04:19 UTC, mid-August.
    now = calendar.timegm((2026, 8, 10, 18, 4, 19, 0, 0, 0))
    expected = calendar.timegm((2026, 8, 1, 0, 0, 0, 0, 0, 0)) * 1000
    assert month_start_ms(now) == expected


def test_month_start_handles_year_boundary():
    # 2026-01-15 UTC should resolve to 2026-01-01, not roll into 2025.
    now = calendar.timegm((2026, 1, 15, 12, 0, 0, 0, 0, 0))
    expected = calendar.timegm((2026, 1, 1, 0, 0, 0, 0, 0, 0)) * 1000
    assert month_start_ms(now) == expected
