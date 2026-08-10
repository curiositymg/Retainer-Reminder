"""Pure calculation/formatting logic for the daily retainer-hours summary.

This module has no ClickUp dependency. The caller (an agent turn with
ClickUp MCP tools, or any future integration) is responsible for gathering
each client's Monthly Hours Cap and time-tracking entries and handing them
to `build_summary`.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClientRetainer:
    """One client's retainer-hours inputs for the current month."""

    name: str
    monthly_hours_cap: Optional[float]  # None if the custom field is missing/non-numeric
    time_entry_durations_ms: list[int] = field(default_factory=list)


@dataclass
class ClientResult:
    name: str
    configured: bool
    hours_cap: Optional[float] = None
    hours_used: Optional[float] = None
    hours_remaining: Optional[float] = None


def hours_used(client: ClientRetainer) -> float:
    """Sum tracked time-entry durations (ms) into hours."""
    total_ms = sum(client.time_entry_durations_ms)
    return total_ms / 3_600_000


def evaluate_client(client: ClientRetainer) -> ClientResult:
    if client.monthly_hours_cap is None:
        return ClientResult(name=client.name, configured=False)

    used = hours_used(client)
    remaining = client.monthly_hours_cap - used
    return ClientResult(
        name=client.name,
        configured=True,
        hours_cap=client.monthly_hours_cap,
        hours_used=used,
        hours_remaining=remaining,
    )


def format_hours(value: float) -> str:
    """12.0 -> '12h', 12.5 -> '12.5h', -2.0 -> '-2h'."""
    rounded = round(value, 1)
    if rounded == int(rounded):
        return f"{int(rounded)}h"
    return f"{rounded}h"


def format_client_line(result: ClientResult) -> str:
    if not result.configured:
        return f"{result.name}: not configured — no Monthly Hours Cap set"

    return (
        f"{result.name}: {format_hours(result.hours_remaining)} remaining "
        f"({format_hours(result.hours_used)} used / {format_hours(result.hours_cap)} cap)"
    )


def build_summary(clients: list[ClientRetainer], testing: bool = True) -> str:
    """Build the full daily DM body: one line per client, numbers-first,
    alphabetical by client name."""
    ordered = sorted(clients, key=lambda c: c.name.lower())
    lines = [format_client_line(evaluate_client(c)) for c in ordered]

    if testing:
        lines.append("")
        lines.append(
            "[TESTING MODE — this is going to me only. Will switch to the "
            '"CMG Crew" channel once verified.]'
        )

    return "\n".join(lines)
