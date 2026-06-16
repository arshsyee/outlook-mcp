# Daily loop

## What it does
1. Organize new inbox mail (categorize/flag/move) using `classify` + judgment.
2. Build a daily summary (unread mail + today's events).
3. Draft replies to mail that needs one.
4. Send replies — **only** after they pass `rules` + your send policy.

## The loop prompt
Save as `loop_prompt.txt` or paste into the scheduler. Uses the `outlook` MCP tools.

```
You are my Outlook assistant. Using the outlook MCP tools, do this in order:

1. list_inbox(unread_only=true, limit=30).
2. For each message: call classify(subject, sender, preview). Then:
   - categorize() with the returned category.
   - if folder is set, find its id via list_folders() and move_message().
   - if flag is true, flag().
3. Build a "Daily Brief": bullet list of unread senders+subjects grouped by category,
   plus today_events(). Print it.
4. For each message where classify says needs_reply=true AND it is a genuine
   personal/academic message (not automated): draft_reply() with a short, polite,
   accurate reply. Print each draft for the record.
5. SEND policy — send a draft with send_draft() ONLY if ALL true:
   - it is a reply to a real person (has a from address, not no-reply/automated),
   - the reply is a simple acknowledgement/scheduling/confirmation (no commitments,
     no attachments, no sensitive info),
   - classify category is not "Admin".
   Otherwise leave it as a draft for me to review. Never send to no-reply addresses.
6. End with a one-line report: counts of organized / drafted / sent / left-for-review.
```

> Tune step 5 to taste. Start STRICT (draft only, send nothing) for the first week,
> watch what it would send, then loosen. Auto-send from a college account can email
> a professor — be conservative.

## Schedule it (Windows Task Scheduler)
Run headless once a day at 08:00:

```powershell
$cmd = 'claude -p "$(Get-Content <absolute-path-to-repo>\loop_prompt.txt -Raw)" --dangerously-skip-permissions'
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -Command $cmd"
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00am
Register-ScheduledTask -TaskName "outlook-daily" -Action $action -Trigger $trigger -Description "Daily Outlook organize+brief"
```

> `--dangerously-skip-permissions` lets it run unattended (no approval prompts).
> Only safe because the MCP server's scopes are limited to your mailbox. Review
> the send policy before enabling auto-send.

## Alternative: Claude Code /loop or /schedule
- `/schedule` — managed cloud cron agent (no local PC needed, but needs the MCP
  server reachable; local stdio server won't work in cloud — use Task Scheduler for
  the local server).
- `/loop 24h <prompt>` — keeps an interactive session looping while your PC is on.
For a local stdio MCP server, **Task Scheduler above is the right fit.**
```
