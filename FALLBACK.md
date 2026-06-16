# Fallback: pre-approved MCP server (no Azure portal)

Why: college tenant blocks student app registration (see README STATUS).
This path uses a **published MCP server that ships its own Azure app ID**, so you
register nothing. You only sign in via device-code and approve consent.

Server: `ms-365-mcp-server` (Softeria) — Microsoft 365 / Graph, MIT licensed.
Requires Node (you have v24 ✅).

## The one remaining unknown
First login shows a Microsoft consent screen. Two outcomes:
- **Consent screen → you click Accept → works.** (User consent allowed.)
- **"Need admin approval" / can't accept → blocked.** Your uni also disables
  user consent to third-party apps. Then only uni IT can unblock. No client-side fix.

We only learn which by trying the login below.

## Setup

1. Smoke-test the package (no install):
   ```powershell
   npx -y @softeria/ms-365-mcp-server --help
   ```
2. Register it with Claude Code:
   ```powershell
   claude mcp add ms365 -- npx -y @softeria/ms-365-mcp-server
   ```
3. Trigger login. In Claude Code, ask it to use the ms365 `login` tool, OR run the
   server's login flow directly:
   ```powershell
   npx -y @softeria/ms-365-mcp-server login
   ```
   Follow the printed URL + device code. Sign in with the **college account**.
4. Watch the consent screen:
   - Accept available → approve → done.
   - "Need admin approval" → STOP, this account is fully locked; go to "If blocked".

5. Verify: `claude mcp list` → `ms365` lists tools. Ask Claude to list your inbox.

## If blocked (admin approval required)
Options, best → worst:
1. **Email uni IT helpdesk:** ask them to "grant tenant admin consent for the
   `ms-365-mcp-server` app" or to allow user consent for Graph delegated scopes
   (Mail, Calendars, Contacts). Include the app's client ID from the consent URL.
2. **Use a personal Outlook account** (outlook.com) instead — no tenant
   restrictions; the original custom `outlook-mcp` server works there immediately.
3. **Forwarding rule:** forward college mail → a personal Outlook, run automation
   on the personal account. (Loses send-as-college, but unblocks read/organize.)

## Daily loop
Same as `daily_loop.md`, but point the loop prompt at the `ms365` tool names
(check `claude mcp list` for exact names; differ from our custom server's).

## Note on the custom server
`outlook-mcp` code stays valid. The moment you have an unblocked account
(personal outlook.com, or IT registers an app), follow README Sections 1–5 and it
runs — richer, since `rules.py` holds YOUR triage logic the generic server lacks.
