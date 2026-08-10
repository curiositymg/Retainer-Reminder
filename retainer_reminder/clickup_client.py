"""Thin wrapper around ClickUp's public REST API v2.

Used by run_daily.py to gather retainer-hours data without a live MCP
session, so the daily report can run unattended (e.g. from a scheduled
GitHub Action) with a stored API token.

Note: ClickUp's public v2 API has no keyword/name-search endpoint, only
tag filtering. Client discovery here is tag-based only — see README.md
for why the small number of un-tagged clients need the tag added in
ClickUp rather than being name-matched here.
"""

import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

BASE_URL = "https://api.clickup.com/api/v2"
CHAT_BASE_URL = "https://api.clickup.com/api/v3"  # Chat lives under v3, not v2
REPORT_TIMEZONE = ZoneInfo("America/Chicago")  # CMG's timezone (CST/CDT)


class ClickUpClient:
    def __init__(self, api_token: str):
        self._session = requests.Session()
        self._session.headers["Authorization"] = api_token

    def _get(self, path: str, base: str = BASE_URL, **params):
        resp = self._session.get(f"{base}{path}", params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json_body: dict, base: str = BASE_URL):
        resp = self._session.post(f"{base}{path}", json=json_body, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def get_tasks_by_tag(self, team_id: str, tag: str) -> list[dict]:
        """All tasks in the workspace carrying the given tag, across pages."""
        tasks = []
        page = 0
        while True:
            data = self._get(
                f"/team/{team_id}/task",
                **{"tags[]": tag, "include_closed": "true", "page": page},
            )
            tasks.extend(data.get("tasks", []))
            if data.get("last_page", True):
                break
            page += 1
        return tasks

    def get_task_space_id(self, task_id: str) -> str | None:
        data = self._get(f"/task/{task_id}")
        return data.get("space", {}).get("id")

    def get_workspace_member_ids(self, team_id: str) -> list[str]:
        data = self._get("/team")
        for team in data.get("teams", []):
            if team.get("id") == team_id:
                return [str(m["user"]["id"]) for m in team.get("members", [])]
        return []

    def get_time_entries(
        self,
        team_id: str,
        start_date_ms: int,
        end_date_ms: int,
        assignee: str | None = None,
    ) -> list[dict]:
        """Time entries in [start_date_ms, end_date_ms].

        assignee=None means 'whatever the token's own permissions allow' —
        ClickUp returns only the token owner's entries unless that account
        can see others'. assignee="any" resolves to every workspace member's
        ID (ClickUp's API has no literal "all users" value — the caller
        still needs "see time tracked by others" permission for this to
        return anything beyond the token owner's own entries).
        """
        params = {"start_date": start_date_ms, "end_date": end_date_ms}
        if assignee == "any":
            params["assignee"] = ",".join(self.get_workspace_member_ids(team_id))
        elif assignee:
            params["assignee"] = assignee
        data = self._get(f"/team/{team_id}/time_entries", **params)
        return data.get("data", [])

    def send_chat_message(self, team_id: str, channel_id: str, content: str) -> dict:
        """Post a message to a ClickUp Chat channel (DM or group).

        Uses ClickUp's Chat API (api/v3, workspace-scoped) — a newer surface
        than the rest of this client's v2 calls. Verify against current
        ClickUp API docs before relying on this if it starts failing;
        endpoint details on newer APIs can change.
        """
        return self._post(
            f"/workspaces/{team_id}/channels/{channel_id}/messages",
            {"content": content, "content_format": "text/plain"},
            base=CHAT_BASE_URL,
        )


def month_start_ms(now: float | None = None) -> int:
    """Start of the current month in CMG's timezone (America/Chicago),
    as epoch ms. Using the CST/CDT calendar boundary — not UTC's — matters
    because a UTC month boundary is 5-6 hours off from what CMG considers
    "the 1st", which would misclassify hours logged near month-end."""
    now = now or time.time()
    local_now = datetime.fromtimestamp(now, tz=REPORT_TIMEZONE)
    month_start = local_now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    return int(month_start.timestamp() * 1000)
