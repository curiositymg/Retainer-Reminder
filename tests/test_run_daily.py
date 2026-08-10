import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from retainer_reminder.run_daily import client_name_from_task, extract_cap, gather_clients


def test_client_name_strips_suffix():
    assert client_name_from_task({"name": "Sunglass World | Retainer Hours"}) == "Sunglass World"


def test_client_name_no_separator():
    assert client_name_from_task({"name": "Watson Spence"}) == "Watson Spence"


def test_client_name_multiple_pipes_keeps_full_client_name():
    # Real case: tag was added to "PD | Brightridge | Retainer Hours" and
    # naively taking the first "|" segment produced just "PD".
    assert (
        client_name_from_task({"name": "PD | Brightridge | Retainer Hours"})
        == "PD | Brightridge"
    )


def test_client_name_monthly_retainer_hours_suffix():
    assert (
        client_name_from_task({"name": "Pro Tech | Monthly Retainer Hours"})
        == "Pro Tech"
    )


def test_extract_cap_present():
    task = {"custom_fields": [{"name": "Monthly Hours Cap", "value": "20"}]}
    assert extract_cap(task) == 20.0


def test_extract_cap_missing_field():
    task = {"custom_fields": [{"name": "Other Field", "value": "5"}]}
    assert extract_cap(task) is None


def test_extract_cap_no_value_set():
    task = {"custom_fields": [{"name": "Monthly Hours Cap"}]}
    assert extract_cap(task) is None


def test_extract_cap_non_numeric():
    task = {"custom_fields": [{"name": "Monthly Hours Cap", "value": "not a number"}]}
    assert extract_cap(task) is None


class FakeClient:
    """Minimal ClickUpClient stand-in: one task references a dead task_id
    that raises on space lookup; gather_clients should skip it, not crash."""

    def get_tasks_by_tag(self, team_id, tag):
        return [
            {
                "id": "task-1",
                "name": "Client A | Retainer Hours",
                "space": {"id": "space-1"},
                "custom_fields": [{"name": "Monthly Hours Cap", "value": "10"}],
            }
        ]

    def get_time_entries(self, team_id, start_ms, end_ms, assignee=None):
        return [
            {"task": {"id": "task-1"}, "duration": "3600000"},
            {"task": {"id": "dead-task"}, "duration": "1800000"},
        ]

    def get_task_space_id(self, task_id):
        if task_id == "dead-task":
            resp = requests.Response()
            resp.status_code = 500
            raise requests.exceptions.HTTPError(response=resp)
        return "space-1"


def test_gather_clients_skips_unreachable_task():
    clients = gather_clients(FakeClient(), "team-1")
    assert len(clients) == 1
    assert clients[0].time_entry_durations_ms == [3600000]
