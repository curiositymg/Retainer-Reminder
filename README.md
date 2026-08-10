# Retainer Reminder

Tracks retainer hours remaining per client Space in ClickUp and reports a daily
summary via ClickUp DM.

## Role

Read `WORKFLOW.md` for the full daily role/instructions. That file is written
to be usable verbatim as the prompt for a scheduled agent run (e.g. a daily
Routine): it defines how to find retainer-hours tasks, read the hours cap,
pull time tracked, and format the summary.

## What lives where

- `WORKFLOW.md` — the daily role and step-by-step instructions for the agent
  turn that talks to ClickUp. This is the only place ClickUp API calls happen
  (via MCP tools), because the calculation needs live workspace data.
- `retainer_reminder/summary.py` — pure, ClickUp-independent calculation and
  formatting logic: given each client's Monthly Hours Cap and a list of
  tracked time-entry durations, it computes Hours Used, Hours Remaining, and
  renders the exact DM format from the spec (including the "not configured"
  and negative-remaining cases). No network calls, fully unit tested.
- `tests/test_summary.py` — unit tests for the above.

The split exists because the ClickUp-querying part can only run inside an
agent turn with MCP tool access, while the arithmetic/formatting is ordinary
code that's easy to test and reuse.

## Known blocker: workspace-wide time entries

The daily workflow requires summing time tracked by **everyone** on a client
Space this month. ClickUp's time-entries API only returns the *authenticated
user's own* entries unless the caller has "see time tracked by others"
permission and passes `assignee: any` (or explicit other users' IDs).

As of this writing, the connected ClickUp integration is authenticated as a
single team member and does **not** have that permission — requests for any
other user's time (or `any`) fail with `"You have no access"`. Until a
workspace admin/owner either:

1. grants the connected integration "see time tracked by others", or
2. reauthorizes the connection under an account that already has it,

...the workflow can only see one person's tracked time, which understates
Hours Used for every client with more than one contributor. Do not send the
daily summary to the real "CMG Crew" channel (or treat it as authoritative)
until this is resolved and verified.

## Client discovery

Retainer-hours tasks are found two ways (per the spec: "named or tagged"):

- Tag filter: tasks tagged `retainer hours`.
- Name match: tasks whose name contains "Retainer Hours" (catches a handful
  of clients where the tag was never applied).

Both need to be unioned and de-duplicated by task ID — relying on the tag
alone misses real clients (confirmed in this workspace: Budo's Mystical
Forest, Dynamic Landscape & Coastal Bloome, JVC, NaJu Pets, PD | Brightridge,
and PD | Garden Guru were name-matches only, no tag).

Each retainer-hours task's `Monthly Hours Cap` custom field is read via the
task detail endpoint (`custom_fields`) — the value lives on the task, not at
the list/space level.

## Testing

```
python3 -m pytest tests/
```
