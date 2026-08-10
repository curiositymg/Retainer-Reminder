import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from retainer_reminder.run_daily import client_name_from_task, extract_cap


def test_client_name_strips_suffix():
    assert client_name_from_task({"name": "Sunglass World | Retainer Hours"}) == "Sunglass World"


def test_client_name_no_separator():
    assert client_name_from_task({"name": "Watson Spence"}) == "Watson Spence"


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
