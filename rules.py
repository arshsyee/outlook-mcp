"""Your inbox triage rules. Deterministic, fast, free (no LLM call).

The daily loop calls classify_message() on each new mail to get a hint:
where to file it, what category tag, whether to flag, whether it likely
needs a reply. The loop combines this with its own judgment.

TODO (you): tune the rules below to YOUR college inbox.
Think about the senders/subjects you actually get:
  - professors / course staff  -> flag, category "Academic", needs_reply often True
  - LMS/Canvas/Blackboard auto-mail -> category "Coursework", folder "Courses"
  - clubs / events / newsletters -> category "FYI", move out of inbox, no reply
  - deadlines ("due", "assignment", "exam") -> flag urgent
  - billing / registrar / financial aid -> flag, never auto-reply

Return dict keys (all optional except 'category'):
  category   : str   label to tag the mail
  folder     : str|None  displayName of folder to move to (None = leave in inbox)
  flag       : bool  flag for follow-up
  needs_reply: bool  candidate for draft_reply
"""


# Edit these to match real senders/keywords in your mailbox.
ACADEMIC_DOMAINS = ("edu",)                       # e.g. add your uni domain "@xyz.edu"
PROFESSOR_HINTS = ("professor", "dr.", "prof")     # sender display-name hints
URGENT_WORDS = ("due", "deadline", "exam", "assignment", "grade", "urgent")
NEWSLETTER_WORDS = ("newsletter", "unsubscribe", "event", "club", "weekly digest")
ADMIN_SENDERS = ("registrar", "financial", "billing", "no-reply", "noreply")


def classify_message(subject: str, sender: str, preview: str) -> dict:
    s = f"{subject} {preview}".lower()
    snd = sender.lower()

    # Admin / financial: important, never auto-reply.
    if any(w in snd for w in ADMIN_SENDERS):
        return {"category": "Admin", "folder": None, "flag": True, "needs_reply": False}

    # Urgent academic keywords.
    if any(w in s for w in URGENT_WORDS):
        return {"category": "Urgent", "folder": None, "flag": True, "needs_reply": True}

    # Likely a person from the university (professor / staff).
    if any(h in snd for h in PROFESSOR_HINTS) or snd.endswith(ACADEMIC_DOMAINS):
        return {"category": "Academic", "folder": None, "flag": True, "needs_reply": True}

    # Bulk / newsletters: file away, no reply.
    if any(w in s for w in NEWSLETTER_WORDS):
        return {"category": "FYI", "folder": "Newsletters", "flag": False, "needs_reply": False}

    # Default: leave it, let the loop's LLM decide.
    return {"category": "Unsorted", "folder": None, "flag": False, "needs_reply": False}
