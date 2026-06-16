# Outlook MCP Server

An [MCP](https://modelcontextprotocol.io) server that connects Claude (or any MCP
client) to **Outlook / Microsoft 365** through the Microsoft Graph API — read,
send, and organize mail, manage calendar and contacts, and run a daily
inbox-automation loop.

Built in Python with MSAL device-code auth: log in once, the refresh token is
cached and silently renewed so scheduled runs stay unattended.

## Features

- **Mail** — list/read inbox, send, draft + send replies
- **Organize** — categorize, flag, move between folders, mark read/unread
- **Calendar** — list today's events, query a date range, create events
- **Contacts** — list contacts
- **Triage rules** — deterministic, user-editable inbox classifier (`rules.py`)
- **Daily loop** — organize inbox, build a daily brief, draft (and optionally send) replies, on a schedule

## Architecture

```
MCP client (Claude Code)
        │  stdio / JSON-RPC
        ▼
   server.py            15 MCP tools (FastMCP)
        │
        ▼
   graph.py             thin Microsoft Graph REST client
        │  Bearer token
        ▼
   auth.py              MSAL device-code flow + on-disk token cache (auto-refresh)
        │
        ▼
   Microsoft Graph API
```

`rules.py` is called by the loop to triage each message before the LLM decides.

## Tools

| Tool | Purpose |
|------|---------|
| `list_inbox` | List inbox messages (unread filter, limit) |
| `read_message` | Full body + recipients of one message |
| `send_mail` | Send a new message |
| `draft_reply` | Create a reply draft (not sent) |
| `send_draft` | Send a previously created draft |
| `list_folders` | List mail folders (ids for moves) |
| `move_message` | Move a message to a folder |
| `categorize` | Set category tags |
| `flag` | Flag for follow-up |
| `mark_read` | Mark read/unread |
| `classify` | Deterministic triage hint (`rules.py`) |
| `today_events` | Events from now to end of today |
| `list_events` | Events in an ISO8601 window |
| `create_event` | Create a calendar event |
| `list_contacts` | List contacts |

## Quick start

### 1. Install
```powershell
git clone https://github.com/arshsyee/outlook-mcp outlook-mcp
cd outlook-mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Register an Azure app (one time)
You need an Entra ID app registration to get a client ID. In
[portal.azure.com](https://portal.azure.com) → **Entra ID → App registrations → New registration**:

1. Name `outlook-mcp`, single-tenant, no redirect URI → **Register**.
2. Copy **Application (client) ID** and **Directory (tenant) ID**.
3. **Authentication → Allow public client flows → Yes** (required for device-code).
4. **API permissions → Microsoft Graph → Delegated** → add:
   `Mail.ReadWrite`, `Mail.Send`, `Calendars.ReadWrite`, `Contacts.Read`,
   `MailboxSettings.Read`, `offline_access`.

> No admin rights needed for personal/most tenants — you consent for your own
> mailbox at first login. See [Design notes](#design-notes-tenant-constraints) if
> your organization restricts this.

### 3. Configure credentials
```powershell
setx OUTLOOK_CLIENT_ID "<client id>"
setx OUTLOOK_TENANT_ID "<tenant id>"
```

### 4. First login (one time)
```powershell
python auth.py
```
Open the printed URL, enter the code, sign in, approve scopes. On success a
`.token_cache.bin` is written and reused/refreshed automatically afterward.

### 5. Register with Claude Code
```powershell
claude mcp add outlook -- python <absolute-path-to-repo>\server.py
```
Verify with `claude mcp list` — `outlook` should appear with its tools.

## Daily automation loop

The server is designed to run on a schedule: organize new mail, produce a daily
brief (unread + today's calendar), draft replies, and — under a conservative
send policy — send simple replies automatically. The loop prompt, send policy,
and a Windows Task Scheduler example are in [`daily_loop.md`](daily_loop.md).

Triage logic lives in [`rules.py`](rules.py) and is meant to be edited to match
your own inbox (professors, coursework, newsletters, deadlines, etc.).

## Security

- `.token_cache.bin` grants live access to your mailbox — it is **gitignored** and
  must never be committed.
- Scopes are **delegated** and limited to **your own mailbox**.
- No secrets are stored in code; the client/tenant IDs come from environment vars.
- Revoke access anytime at
  [myaccount.microsoft.com](https://myaccount.microsoft.com) → Apps & services.

## Design notes: tenant constraints

This project was first targeted at a university Microsoft 365 account, which
surfaced a real-world constraint worth documenting:

- **Many organization tenants disable student/user app registration.** On the
  tenant this was built against, the Azure **App registrations** page returns
  *"You do not have access to this page,"* so the custom-app path (step 2 above)
  cannot be completed there.
- The server code itself is provider-agnostic and works unchanged against any
  account that permits app registration — a personal `outlook.com` account, or an
  org account where IT registers the app for you.
- For locked-down tenants, [`FALLBACK.md`](FALLBACK.md) documents a no-portal
  alternative using a pre-approved published MCP server, and the escalation paths
  (request IT consent, use a personal account, or forward mail to one) when even
  third-party user consent is disabled.

The takeaway: the auth design (delegated device-code) is the right call for a
personal automation tool; the blocker is organizational policy, not the code.

## License

MIT — see [LICENSE](LICENSE).
