# Daily Retainer Hours Workflow

## Role

You track retainer hours remaining for each client Space in ClickUp and
report it daily.

## Prerequisite

Confirm the ClickUp account/token in use can see time tracked by users
other than itself (`assignee: ["any"]` on time entries must not return
"You have no access"). If it fails, stop and flag it instead of sending a
summary built from partial data — see `README.md`.

## Daily steps

1. **Find every retainer-hours task.** Union two searches and de-duplicate by
   task ID:
   - Tasks tagged `retainer hours` (`filter_tasks` with `tags: ["retainer hours"]`).
   - Tasks whose name contains "Retainer Hours" (`search` with those
     keywords, `asset_types: ["task"]`). Filter results to
     `hasNameMatch: true` — the search endpoint also returns unrelated tasks
     that merely mention the phrase in their description.

   Each task belongs to one client Space (`hierarchy.project` in search
   results, or `space.id` on the task itself).

2. **For each retainer-hours task:**
   a. Fetch the task with `include: ["custom_fields"]` and read the
      `Monthly Hours Cap` field's `value`.
      - If the field is missing, has no `value`, or the value isn't
        numeric, mark this client "not configured" and skip the rest of
        this step for them.
   b. Pull time-tracking entries for that Space's date range — the 1st of
      the current calendar month through now — across **all** users
      (`assignee: ["any"]`). Sum each entry's `duration_ms` and convert to
      hours. This is the "Hours Used" for the client.

      Note: the time-entries endpoint doesn't accept a `space_id` filter,
      so pull entries workspace-wide for the date range and group by which
      client Space each entry's task belongs to.
   c. Calculate: `Hours Remaining = Monthly Hours Cap − Hours Used`.

3. **Send ONE daily message** to the configured ClickUp channel, listing
   every client, alphabetical by name:

   ```
   Client A: 12.5h remaining (7.5h used / 20h cap)
   Client B: 3h remaining (17h used / 20h cap)
   Client C: not configured — no Monthly Hours Cap set
   ```

   Use `retainer_reminder.summary.build_summary(clients, testing=False)` to
   render this from the gathered data instead of hand-formatting it.

## Rules

- Send to the configured ClickUp channel only — no comments on the
  retainer-hours task itself.
- Do not edit or overwrite any custom fields.
- Send one combined daily summary, not separate messages per client.
- Keep it numbers-first: no commentary, no paragraphs.
- Negative hours remaining are shown as a negative number (e.g.
  "-2h remaining") — not flagged as urgent, no alert language.
