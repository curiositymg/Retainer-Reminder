import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from retainer_reminder.summary import (
    ClientRetainer,
    build_summary,
    evaluate_client,
    format_hours,
)


def test_format_hours_whole_number():
    assert format_hours(12.0) == "12h"


def test_format_hours_fraction():
    assert format_hours(12.5) == "12.5h"


def test_format_hours_negative():
    assert format_hours(-2.0) == "-2h"


def test_evaluate_client_not_configured():
    client = ClientRetainer(name="Client C", monthly_hours_cap=None)
    result = evaluate_client(client)
    assert result.configured is False
    assert result.hours_remaining is None


def test_evaluate_client_computes_remaining():
    # 27,000,000 ms = 7.5 hours
    client = ClientRetainer(
        name="Client A", monthly_hours_cap=20, time_entry_durations_ms=[27_000_000]
    )
    result = evaluate_client(client)
    assert result.hours_used == 7.5
    assert result.hours_remaining == 12.5


def test_evaluate_client_negative_remaining():
    # 61,200,000 ms = 17 hours against a 15h cap
    client = ClientRetainer(
        name="Client B", monthly_hours_cap=15, time_entry_durations_ms=[61_200_000]
    )
    result = evaluate_client(client)
    assert result.hours_remaining == -2


def test_build_summary_matches_spec_format():
    clients = [
        ClientRetainer(name="Client A", monthly_hours_cap=20, time_entry_durations_ms=[27_000_000]),
        ClientRetainer(name="Client B", monthly_hours_cap=20, time_entry_durations_ms=[61_200_000]),
        ClientRetainer(name="Client C", monthly_hours_cap=None),
    ]
    summary = build_summary(clients, testing=True)

    assert "Client A: 12.5h remaining (7.5h used / 20h cap)" in summary
    assert "Client B: 3h remaining (17h used / 20h cap)" in summary
    assert "Client C: not configured — no Monthly Hours Cap set" in summary
    assert "TESTING MODE" in summary


def test_build_summary_sorts_alphabetically():
    clients = [
        ClientRetainer(name="Zebra Co", monthly_hours_cap=10),
        ClientRetainer(name="apple Inc", monthly_hours_cap=10),
        ClientRetainer(name="Mango LLC", monthly_hours_cap=10),
    ]
    summary = build_summary(clients, testing=False)
    lines = [line for line in summary.splitlines() if line]

    assert lines == [
        "apple Inc: 10h remaining (0h used / 10h cap)",
        "Mango LLC: 10h remaining (0h used / 10h cap)",
        "Zebra Co: 10h remaining (0h used / 10h cap)",
    ]
