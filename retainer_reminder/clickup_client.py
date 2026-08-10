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

import requests

BASE_URL = "https://api.clickup.com/api/v2"


class ClickUpClient:
    def __init__(self, api_token: str):
        self._session = requests.Session()
        self._session.headers["Authorization"] = api_token

    def _get(self, path: str, **params):
        resp = self._session.get(f"{BASE_URL}{path}", params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json_body: dict):
        resp = self._session.post(f"{BASE_URL}{path}", json=json_body, timeout=60)
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

    def get_time_entries(
        self,
        team_id: str,
        start_date_ms: int,
        end_date_ms: int,
        assignee: str | None = None,
    ) -> list[dict]:
        """Time entries in [start_date_ms, end_date_ms]. assignee=None means
        'whatever the token's own permissions allow' — ClickUp returns only
        the token owner's entries unless that account can see others'."""
        params = {"start_date": start_date_ms, "end_date": end_date_ms}
        if assignee:
            params["assignee"] = assignee
        data = self._get(f"/team/{team_id}/time_entries", **params)
        return data.get("data", [])

    def send_chat_message(self, channel_id: str, content: str) -> dict:
        """Post a message to a ClickUp Chat channel (DM or group).

        Uses ClickUp's Chat API. Verify against current ClickUp API docs
        before relying on this in production — Chat is a newer surface and
        endpoint details can change.
        """
        return self._post(
            f"/chat/v3/channels/{channel_id}/messages",
            {"content": content, "content_format": "text/plain"},
        )


def month_start_ms(now: float | None = None) -> int:
    now = now or time.time()
    struct = time.gmtime(now)
    month_start = time.struct_time(
        (struct.tm_year, struct.tm_mon, 1, 0, 0, 0, 0, 0, 0)
    )
    return int(time.mktime(month_start) * 1000)
