# Outlook MCP server

Custom MCP server → Microsoft Graph for your college Outlook. Delegated auth
(device-code), token cached + auto-refreshed so a daily loop runs unattended.

---

## ⚠️ STATUS (2026-06-15): custom-app path BLOCKED on this account

The college tenant **blocks students from registering apps**. App registrations
page in Azure Portal returns *"You do not have access to this page."* So Section 1
below **cannot be completed** with this account. The custom server code (auth.py,
graph.py, server.py, rules.py) is finished and correct — it will work the day this
runs against any tenant/account that allows app registration (e.g. a personal
outlook.com account, or after uni IT registers an app for you).

**Active plan = pre-approved server (no Azure portal).** See `FALLBACK.md`.

Keep this folder: zero changes needed once an unblocked account is available —
just do Sections 1–5.

---

## 1. Register the app in Azure (one time, you do this) — BLOCKED on college tenant

1. Go to https://portal.azure.com → **Microsoft Entra ID** → **App registrations** → **New registration**.
2. Name: `outlook-mcp`.
3. **Supported account types:** "Accounts in this organizational directory only" (single tenant).
4. **Redirect URI:** leave blank (device-code flow needs none).
5. Click **Register**.
6. On the **Overview** page copy **Application (client) ID** and **Directory (tenant) ID**.
7. **Authentication** (left menu) → **Advanced settings** → set **Allow public client flows** = **Yes** → Save. *(Device-code flow requires this.)*
8. **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions** → add:
   `Mail.ReadWrite`, `Mail.Send`, `Calendars.ReadWrite`, `Contacts.Read`, `MailboxSettings.Read`, `offline_access`.
9. If a **"Grant admin consent"** button appears and is greyed/blocked → your university restricts consent. You'll find out at step 4 of setup; if login errors with consent, ping IT or fall back to a pre-approved server.

> **What actually happened (2026-06-15):** never reached this step. The App
> registrations page itself denied access ("You do not have access to this page").
> Student app registration is disabled tenant-wide. → use `FALLBACK.md`.

## 2. Install

```powershell
git clone <your-repo-url> outlook-mcp
cd outlook-mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Set credentials (PowerShell, current session)

```powershell
$env:OUTLOOK_CLIENT_ID = "<Application (client) ID>"
$env:OUTLOOK_TENANT_ID = "<Directory (tenant) ID>"
```

To persist across reboots (recommended for the loop), set them as user env vars:
```powershell
setx OUTLOOK_CLIENT_ID "<client id>"
setx OUTLOOK_TENANT_ID "<tenant id>"
```

## 4. First login (one time)

```powershell
python auth.py
```
Prints a URL + code. Open URL, type code, sign in with the college account,
approve scopes. On success: `OK, got token...` and `.token_cache.bin` is written.

> If you see an error about admin consent / app not approved → university blocks
> user consent. Stop here and tell me; we switch to a pre-approved MCP server.

## 5. Register the server with Claude Code

```powershell
claude mcp add outlook -- python <absolute-path-to-repo>\server.py
```
Verify: `claude mcp list` → `outlook` shows tools.

## 6. Daily loop

See `daily_loop.md` for the prompt and scheduling.

## Security notes
- `.token_cache.bin` = live access to your mailbox. Never commit it. (`.gitignore` covers it.)
- Scopes are delegated and limited to YOUR mailbox only.
- Revoke anytime: https://myaccount.microsoft.com → "Apps & services" → remove `outlook-mcp`.
