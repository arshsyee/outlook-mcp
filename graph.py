"""Thin Microsoft Graph client. One function per REST call the tools need.

Keeps HTTP details out of server.py. Every call attaches a fresh bearer token
from auth.get_token() (silently refreshed).
"""

import httpx
from auth import get_token

BASE = "https://graph.microsoft.com/v1.0"


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE,
        headers={"Authorization": f"Bearer {get_token()}"},
        timeout=30.0,
    )


def _raise(r: httpx.Response):
    if r.status_code >= 400:
        raise RuntimeError(f"Graph {r.status_code}: {r.text[:500]}")


# --- Mail --------------------------------------------------------------------
def list_messages(folder: str = "inbox", unread_only: bool = True, top: int = 25) -> list[dict]:
    params = {
        "$top": top,
        "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview,categories,flag",
        "$orderby": "receivedDateTime desc",
    }
    if unread_only:
        params["$filter"] = "isRead eq false"
    with _client() as c:
        r = c.get(f"/me/mailFolders/{folder}/messages", params=params)
    _raise(r)
    return r.json().get("value", [])


def get_message(message_id: str) -> dict:
    with _client() as c:
        r = c.get(
            f"/me/messages/{message_id}",
            params={"$select": "id,subject,from,toRecipients,receivedDateTime,body,categories"},
        )
    _raise(r)
    return r.json()


def send_mail(to: list[str], subject: str, body: str, html: bool = False) -> None:
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML" if html else "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": a}} for a in to],
        },
        "saveToSentItems": True,
    }
    with _client() as c:
        r = c.post("/me/sendMail", json=payload)
    _raise(r)


def create_reply_draft(message_id: str, comment: str) -> dict:
    """Make a reply draft (NOT sent). Returns the draft message (has its own id)."""
    with _client() as c:
        r = c.post(f"/me/messages/{message_id}/createReply", json={"comment": comment})
    _raise(r)
    return r.json()


def send_draft(draft_id: str) -> None:
    """Send a previously created draft by its id."""
    with _client() as c:
        r = c.post(f"/me/messages/{draft_id}/send")
    _raise(r)


# --- Organize ----------------------------------------------------------------
def list_folders() -> list[dict]:
    with _client() as c:
        r = c.get("/me/mailFolders", params={"$top": 100, "$select": "id,displayName"})
    _raise(r)
    return r.json().get("value", [])


def move_message(message_id: str, destination_folder_id: str) -> dict:
    with _client() as c:
        r = c.post(f"/me/messages/{message_id}/move", json={"destinationId": destination_folder_id})
    _raise(r)
    return r.json()


def categorize_message(message_id: str, categories: list[str]) -> None:
    with _client() as c:
        r = c.patch(f"/me/messages/{message_id}", json={"categories": categories})
    _raise(r)


def mark_read(message_id: str, read: bool = True) -> None:
    with _client() as c:
        r = c.patch(f"/me/messages/{message_id}", json={"isRead": read})
    _raise(r)


def flag_message(message_id: str, status: str = "flagged") -> None:
    # status: notFlagged | flagged | complete
    with _client() as c:
        r = c.patch(f"/me/messages/{message_id}", json={"flag": {"flagStatus": status}})
    _raise(r)


# --- Calendar ----------------------------------------------------------------
def list_events(start_iso: str, end_iso: str) -> list[dict]:
    with _client() as c:
        r = c.get(
            "/me/calendarView",
            params={
                "startDateTime": start_iso,
                "endDateTime": end_iso,
                "$select": "id,subject,start,end,location,organizer",
                "$orderby": "start/dateTime",
                "$top": 100,
            },
        )
    _raise(r)
    return r.json().get("value", [])


def create_event(subject: str, start_iso: str, end_iso: str, tz: str = "UTC",
                 attendees: list[str] | None = None, body: str = "") -> dict:
    payload = {
        "subject": subject,
        "start": {"dateTime": start_iso, "timeZone": tz},
        "end": {"dateTime": end_iso, "timeZone": tz},
        "body": {"contentType": "Text", "content": body},
    }
    if attendees:
        payload["attendees"] = [
            {"emailAddress": {"address": a}, "type": "required"} for a in attendees
        ]
    with _client() as c:
        r = c.post("/me/events", json=payload)
    _raise(r)
    return r.json()


# --- Contacts ----------------------------------------------------------------
def list_contacts(top: int = 100) -> list[dict]:
    with _client() as c:
        r = c.get(
            "/me/contacts",
            params={"$top": top, "$select": "id,displayName,emailAddresses,mobilePhone"},
        )
    _raise(r)
    return r.json().get("value", [])
