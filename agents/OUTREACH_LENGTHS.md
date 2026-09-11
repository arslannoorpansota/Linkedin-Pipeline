# OUTREACH_LENGTHS.md — Message length rules

> **Standing rule, set by Faizan 2026-09-12. Applies to EVERY outreach message from now on.**

---

## The rule

| Asset | Length | Notes |
|---|---|---|
| **Note** | **300 characters** | The default. This is what Faizan means by "note". |
| **Connection request note** | **200 characters** | Only when it must go out as a LinkedIn *connection request* — LinkedIn hard-caps these at 200 chars on a free account. |
| **InMail** | under 150 words | Unchanged (see `CLAUDE.md` §9). |

**Default to 300 characters.** Write the 200-character version only when the message
is going out attached to a connection request, or when Faizan asks for it.

---

## Why there are two numbers

LinkedIn enforces a **200-character hard limit** on the note attached to a connection
request. Anything longer is silently truncated or rejected.

A **300-character message** cannot be a connection-request note. It has to go out as
an InMail or as a DM after the person accepts. That is fine, and 300 characters is the
better length when the channel allows it, because it fits four things that 200 cannot:

1. the specific observation (the hook)
2. the OpenAI video-model credential
3. what we actually do
4. one ask

At 200 characters, something in that list gets cut — usually the credential or the
reassurance, which are the two parts that answer the reader's unspoken objection.

---

## What to do in practice

- Faizan says **"note"** → write **300 characters**.
- The message must ride on a **connection request** → write **200 characters**, and say
  explicitly which one is which when handing both over.
- When both are drafted, **log both in the sheet** and record which one was sent.

Never pad to reach the limit. 300 is a ceiling, not a target — if the message says
everything it needs in 240, leave it at 240.

---

## Standing content rules that still apply at any length

- Run every message through the **humanizer** skill before showing it (see
  `humanize-outreach-messages` memory). No em dashes or en dashes, no rule-of-three,
  no promotional adjectives, no negative parallelism, no filler.
- **One ask only**, at the end.
- Lead with the observation about **them**, never the pitch.
- The hook must be **verifiable** — something they can go and look at.
- Write as Arslan (CTO), first person singular.

---

Relates to `CLAUDE.md` §9 (Tone Rules), `agents/LIST_LOGGING.md` (channel by profile
rating), and the memory notes `humanize-outreach-messages`, `outreach-channel-by-rating`.
