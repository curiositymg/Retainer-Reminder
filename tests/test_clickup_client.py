import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from retainer_reminder.clickup_client import month_start_ms

CHICAGO = ZoneInfo("America/Chicago")


def test_month_start_uses_chicago_calendar_not_utc():
    # 2026-08-01 03:00 UTC = 2026-07-31 22:00 CDT (UTC-5) — still July in
    # Chicago, so the month boundary must be July 1, not August 1.
    now = datetime(2026, 8, 1, 3, 0, 0, tzinfo=ZoneInfo("UTC")).timestamp()
    expected = datetime(2026, 7, 1, tzinfo=CHICAGO).timestamp() * 1000
    assert month_start_ms(now) == expected


def test_month_start_handles_year_boundary():
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=CHICAGO).timestamp()
    expected = datetime(2026, 1, 1, tzinfo=CHICAGO).timestamp() * 1000
    assert month_start_ms(now) == expected


def test_month_start_handles_dst_transition():
    # December is CST (UTC-6); confirm it still resolves to Dec 1 00:00 CST.
    now = datetime(2026, 12, 15, 12, 0, 0, tzinfo=CHICAGO).timestamp()
    expected = datetime(2026, 12, 1, tzinfo=CHICAGO).timestamp() * 1000
    assert month_start_ms(now) == expected
