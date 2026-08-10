# Retainer Reminder

Tracks retainer hours remaining per client Space in ClickUp and reports a daily
summary via ClickUp chat.

## Two ways to run this

1. **Live agent turn (MCP).** Read `WORKFLOW.md` as the prompt for a Claude
   session with the ClickUp MCP connector attached — it defines how to find
   retainer-hours tasks, read the hours cap, pull time tracked, and format
   the summary. Whichever ClickUp account the connector is authorized as
   determines what it can see (and who messages appear to come from).
2. **Unattended script (direct API).** `retainer_reminder/run_daily.py` talks
   to ClickUp's REST API directly with a stored token — no live session
   needed, so it can run on a schedule (see
   `.github/workflows/daily-retainer-report.yml`). Requires three secrets:
   `CLICKUP_API_TOKEN`, `CLICKUP_TEAM_ID`, `CLICKUP_CHANNEL_ID`. Test locally
   first with `python -m retainer_reminder.run_daily --dry-run` (prints
   instead of sending).

Both paths share the same calculation/formatting logic and the same
permission constraint below — switching from MCP to a direct API call does
**not** by itself fix visibility into other people's tracked time; that's
still governed by whatever ClickUp account the token/connection belongs to.

## What lives where

- `WORKFLOW.md` — the daily role and step-by-step instructions for the MCP
  agent-turn path.
- `retainer_reminder/clickup_client.py` — thin ClickUp REST API v2 wrapper
  used by the direct-API path. Tag-based task discovery only (see "Client
  discovery" below). Chat sends go through ClickUp's api/v3 Chat API
  (`/workspaces/{team_id}/chat/channels/{channel_id}/messages`), confirmed
  working against production with retry-on-5xx (that API is documented as
  experimental, so re-verify the path if it starts failing).
- `retainer_reminder/run_daily.py` — orchestrates the direct-API path:
  gather clients → compute → send (or `--dry-run` to just print).
- `retainer_reminder/summary.py` — pure, ClickUp-independent calculation and
  formatting logic: given each client's Monthly Hours Cap and a list of
  tracked time-entry durations, it computes Hours Used, Hours Remaining, and
  renders the exact DM format from the spec (including the "not configured"
  and negative-remaining cases). No network calls, fully unit tested.
- `tests/` — unit tests for the above (13 tests, no network required).

## Workspace-wide time entries

The daily workflow requires summing time tracked by **everyone** on a client
Space this month. ClickUp's time-entries API only returns the *authenticated
user's own* entries unless the caller has "see time tracked by others"
permission and passes `assignee: any` (or explicit other users' IDs).

**Resolved for the direct-API path**: `CLICKUP_API_TOKEN` is set to a
ClickUp account (CMG's project manager) that has this permission, confirmed
against production. `assignee: "any"` resolves to every workspace member's
ID (`get_workspace_member_ids`) since ClickUp's real API has no literal
"all users" value.

**Still limited for the MCP path** (`WORKFLOW.md`): the MCP connector used
in a live agent session is a separate authorization from the API token
above, tied to whatever account it's connected as. If that's not an account
with the same permission, `assignee: ["any"]` will still fail there with
`"You have no access"` even though the direct-API path works — check which
path (and which account) is actually running before trusting either one's
output.

## Client discovery

The spec says "named or tagged 'retainer hours'." In practice these are two
different capabilities:

- **MCP path (`WORKFLOW.md`):** can do both — tag filter, plus a name-match
  keyword search that catches tasks where the tag was never applied.
  Confirmed in this workspace: Budo's Mystical Forest, Dynamic Landscape &
  Coastal Bloome, JVC, NaJu Pets, PD | Brightridge, and PD | Garden Guru were
  name-matches only, no tag — the union of both is what finds all 34 clients.
- **Direct-API path (`run_daily.py`):** tag-only. ClickUp's public v2 API has
  no keyword/name-search endpoint, so it can't reproduce the name-match
  fallback. **Fix this by adding the `retainer hours` tag to those six tasks
  in ClickUp** (the tag is what their own task description already asks for)
  rather than trying to work around the missing API — that also makes the
  MCP path's name-match fallback unnecessary going forward.

Each retainer-hours task's `Monthly Hours Cap` custom field comes back
already included in the tag-filtered task list — no extra per-task fetch
needed for the direct-API path.

## Testing

```
python3 -m pytest tests/
```
