"""Daily retainer-hours report: gather live ClickUp data and send the summary.

Reads config from environment variables:
  CLICKUP_API_TOKEN   - required. Token for the account this report runs as.
                         That account's ClickUp permissions determine whether
                         Hours Used reflects everyone's tracked time or just
                         this account's own (see README.md).
  CLICKUP_TEAM_ID      - required. Workspace ID.
  CLICKUP_CHANNEL_ID   - required unless --dry-run. DM/group channel to post to.

Usage:
  python -m retainer_reminder.run_daily --dry-run   # print, don't send
  python -m retainer_reminder.run_daily             # send for real
"""

import argparse
import os
import sys
import time

import requests

from retainer_reminder.clickup_client import ClickUpClient, month_start_ms
from retainer_reminder.summary import ClientRetainer, build_summary

RETAINER_TAG = "retainer hours"
CAP_FIELD_NAME = "Monthly Hours Cap"


def client_name_from_task(task: dict) -> str:
    name = task["name"]
    return name.split("|")[0].strip() if "|" in name else name


def extract_cap(task: dict) -> float | None:
    """ClickUp's tag-filtered task list already includes each task's
    custom_fields, so no extra per-task fetch is needed to read the cap."""
    for field in task.get("custom_fields", []):
        if field.get("name") == CAP_FIELD_NAME:
            raw = field.get("value")
            try:
                return float(raw) if raw is not None else None
            except (TypeError, ValueError):
                return None
    return None


def gather_clients(client: ClickUpClient, team_id: str) -> list[ClientRetainer]:
    tasks = client.get_tasks_by_tag(team_id, RETAINER_TAG)

    start_ms = month_start_ms()
    end_ms = int(time.time() * 1000)
    entries = client.get_time_entries(team_id, start_ms, end_ms, assignee="any")

    # Time entries carry task.id but not the task's space, so resolve each
    # distinct task touched this month to its space and bucket durations there.
    durations_by_space: dict[str, list[int]] = {}
    space_id_cache: dict[str, str] = {}
    for entry in entries:
        task_id = entry.get("task", {}).get("id")
        if not task_id:
            continue
        if task_id not in space_id_cache:
            try:
                space_id_cache[task_id] = client.get_task_space_id(task_id)
            except requests.exceptions.HTTPError as exc:
                # A time entry can reference a task that's since been
                # deleted or is otherwise unreachable — skip attributing
                # that entry rather than failing the whole report.
                print(f"warning: skipping task {task_id}: {exc}", file=sys.stderr)
                space_id_cache[task_id] = None
        space_id = space_id_cache[task_id]
        if space_id:
            durations_by_space.setdefault(space_id, []).append(int(entry["duration"]))

    clients = []
    for task in tasks:
        space_id = task["space"]["id"]
        clients.append(
            ClientRetainer(
                name=client_name_from_task(task),
                monthly_hours_cap=extract_cap(task),
                time_entry_durations_ms=durations_by_space.get(space_id, []),
            )
        )
    return clients


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print instead of sending")
    args = parser.parse_args()

    token = os.environ["CLICKUP_API_TOKEN"]
    team_id = os.environ["CLICKUP_TEAM_ID"]

    client = ClickUpClient(token)
    clients = gather_clients(client, team_id)
    message = build_summary(clients, testing=True)

    if args.dry_run:
        print(message)
        return

    channel_id = os.environ["CLICKUP_CHANNEL_ID"].strip()
    client.send_chat_message(team_id, channel_id, message)


if __name__ == "__main__":
    main()
