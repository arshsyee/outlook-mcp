"""Outlook MCP server. Exposes Graph operations as MCP tools.

Run: python server.py   (stdio transport, what Claude Code launches)
"""

from datetime import datetime, timezone, timedelta
from mcp.server.fastmcp import FastMCP

import graph
import rules

mcp = FastMCP("outlook")


# --- Mail read ---------------------------------------------------------------
@mcp.tool()
def list_inbox(unread_only: bool = True, limit: int = 25) -> list[dict]:
    """List inbox messages (id, subject, from, preview, read state, categories)."""
    return graph.list_messages("inbox", unread_only=unread_only, top=limit)


@mcp.tool()
def read_message(message_id: str) -> dict:
    """Full body + recipients of one message by id."""
    return graph.get_message(message_id)


# --- Mail send / reply -------------------------------------------------------
@mcp.tool()
def send_mail(to: list[str], subject: str, body: str, html: bool = False) -> str:
    """Send a new mail. `to` is a list of addresses."""
    graph.send_mail(to, subject, body, html=html)
    return "sent"


@mcp.tool()
def draft_reply(message_id: str, comment: str) -> dict:
    """Create a reply DRAFT (not sent). Returns draft with its own id for review/send."""
    d = graph.create_reply_draft(message_id, comment)
    return {"draft_id": d.get("id"), "subject": d.get("subject")}


@mcp.tool()
def send_draft(draft_id: str) -> str:
    """Send a draft created by draft_reply, by its draft_id."""
    graph.send_draft(draft_id)
    return "sent"


# --- Organize ----------------------------------------------------------------
@mcp.tool()
def list_folders() -> list[dict]:
    """List mail folders (id + displayName). Use ids for move_message."""
    return graph.list_folders()


@mcp.tool()
def move_message(message_id: str, destination_folder_id: str) -> str:
    """Move a message to a folder (by folder id)."""
    graph.move_message(message_id, destination_folder_id)
    return "moved"


@mcp.tool()
def categorize(message_id: str, categories: list[str]) -> str:
    """Set categories (color/label tags) on a message."""
    graph.categorize_message(message_id, categories)
    return "categorized"


@mcp.tool()
def flag(message_id: str, status: str = "flagged") -> str:
    """Flag a message. status: notFlagged | flagged | complete."""
    graph.flag_message(message_id, status)
    return status


@mcp.tool()
def mark_read(message_id: str, read: bool = True) -> str:
    """Mark a message read/unread."""
    graph.mark_read(message_id, read)
    return "ok"


@mcp.tool()
def classify(subject: str, sender: str, preview: str) -> dict:
    """Deterministic triage hint for one message (your rules in rules.py)."""
    return rules.classify_message(subject, sender, preview)


# --- Calendar ----------------------------------------------------------------
@mcp.tool()
def today_events() -> list[dict]:
    """Events from now through end of today (local-ish, UTC window)."""
    now = datetime.now(timezone.utc)
    end = now.replace(hour=23, minute=59, second=59)
    return graph.list_events(now.isoformat(), end.isoformat())


@mcp.tool()
def list_events(start_iso: str, end_iso: str) -> list[dict]:
    """Events in an arbitrary ISO8601 UTC window."""
    return graph.list_events(start_iso, end_iso)


@mcp.tool()
def create_event(subject: str, start_iso: str, end_iso: str, tz: str = "UTC",
                 attendees: list[str] | None = None, body: str = "") -> dict:
    """Create a calendar event. ISO8601 times."""
    ev = graph.create_event(subject, start_iso, end_iso, tz, attendees, body)
    return {"id": ev.get("id"), "subject": ev.get("subject")}


# --- Contacts ----------------------------------------------------------------
@mcp.tool()
def list_contacts(limit: int = 100) -> list[dict]:
    """List contacts (name, emails, phone)."""
    return graph.list_contacts(top=limit)


if __name__ == "__main__":
    mcp.run()
