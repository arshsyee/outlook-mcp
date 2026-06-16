"""Delegated auth for Microsoft Graph via MSAL device-code flow.

First run: prints a code + URL, you log in once with the college account.
After that: refresh token is cached to disk and silently renewed every call,
so the daily loop runs unattended until a Conditional Access policy forces
an interactive re-login.
"""

import os
import sys
import atexit
import msal

# --- Config: filled from environment (see .env.example / README) -------------
CLIENT_ID = os.environ.get("OUTLOOK_CLIENT_ID", "")
TENANT_ID = os.environ.get("OUTLOOK_TENANT_ID", "common")  # your university tenant GUID
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Delegated scopes (your mailbox only). offline_access => refresh token.
SCOPES = [
    "Mail.ReadWrite",
    "Mail.Send",
    "Calendars.ReadWrite",
    "Contacts.Read",
    "MailboxSettings.Read",
]

# Token cache lives next to this file. Treat it like a password.
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".token_cache.bin")


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as fh:
            cache.deserialize(fh.read())
    # Persist on exit only if something changed.
    atexit.register(
        lambda: open(CACHE_PATH, "w", encoding="utf-8").write(cache.serialize())
        if cache.has_state_changed
        else None
    )
    return cache


def _app() -> msal.PublicClientApplication:
    if not CLIENT_ID:
        raise RuntimeError(
            "OUTLOOK_CLIENT_ID not set. Register the app in Azure Portal first (see README)."
        )
    return msal.PublicClientApplication(
        CLIENT_ID, authority=AUTHORITY, token_cache=_load_cache()
    )


def get_token() -> str:
    """Return a valid access token. Silent if cached, device-code if first run."""
    app = _app()

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    # No usable cached token -> interactive device-code flow (first run only).
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Device flow failed: {flow.get('error_description', flow)}")

    # message tells you exactly where to go and what code to type.
    print(flow["message"], file=sys.stderr, flush=True)

    result = app.acquire_token_by_device_flow(flow)  # blocks until you finish login
    if "access_token" not in result:
        raise RuntimeError(
            f"Auth failed: {result.get('error_description', result)}\n"
            "If you see a consent/admin error, your university blocks user consent "
            "for custom apps — fall back to a pre-approved MCP server."
        )
    return result["access_token"]


if __name__ == "__main__":
    # `python auth.py` -> do the one-time login and confirm it works.
    tok = get_token()
    print("OK, got token (len %d). Cache written to %s" % (len(tok), CACHE_PATH))
