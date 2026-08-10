import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from retainer_reminder.clickup_client import ClickUpClient, month_start_ms

CHICAGO = ZoneInfo("America/Chicago")


def _response(status_code: int, json_body: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {}
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


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


@patch("time.sleep", return_value=None)
def test_send_chat_message_retries_on_500_then_succeeds(mock_sleep):
    client = ClickUpClient("fake-token")
    client._session.post = MagicMock(
        side_effect=[_response(500), _response(200, {"id": "msg-1"})]
    )

    result = client.send_chat_message("team-1", "chan-1", "hello")

    assert result == {"id": "msg-1"}
    assert client._session.post.call_count == 2


@patch("time.sleep", return_value=None)
def test_send_chat_message_gives_up_after_retries(mock_sleep):
    client = ClickUpClient("fake-token")
    client._session.post = MagicMock(return_value=_response(500))

    with pytest.raises(requests.exceptions.HTTPError):
        client.send_chat_message("team-1", "chan-1", "hello", retries=2)

    assert client._session.post.call_count == 3


def test_send_chat_message_does_not_retry_on_4xx():
    client = ClickUpClient("fake-token")
    client._session.post = MagicMock(return_value=_response(404))

    with pytest.raises(requests.exceptions.HTTPError):
        client.send_chat_message("team-1", "chan-1", "hello")

    assert client._session.post.call_count == 1
