# Two Schedulers, Each Sure It Was the Only One

*A duplicate post taught me the platform won't let you delete your way out of a mistake — and that the
real gap wasn't the bug, it was how long it sat there before anyone saw it.*

**Platform:** thequietai.com — canonical site article, "It Shipped Itself" format
(`DISPATCH-content-proof-format-2026-08-26.md`). Sep 7 hub piece.
**Source:** `~/.claude/projects/-Users-gabe-Desktop-the-quiet-ai/memory/scribe-hands-git-race-duplicate-post-2026-08-30.md`
and `~/.claude/projects/-Users-gabe-Desktop-the-quiet-ai/memory/scribe-hands-duplicate-post-autodelete-policy.md`
(the corrected 2026-08-30 version). No number, detail, or claim here is not traceable to those two files.
**Sibling cuts:** `two-schedulers-one-bug-linkedin.md` · `-facebook.md` · `-skool.md`.
**Never-blend:** no yoga identity, no year-count credential, no GabeYoga branding. No plumbing words.
**Refusal doctrine held:** the piece narrates every decision (merging the diverged records, disabling one
scheduler, building the alert instead of relying on an auto-delete) as something worked out and done by a
person; the automation only ever executes and reports.
**Scribe-hands framing note:** cited per `CLAUDE.md`'s 2026-08-30 scoped amendment — real, run scribe-hands
results are licensed as brand-level proof that "the same team-of-digital-workers method runs our own
channel," never as "the Suite includes this." No account handle, follower count, engagement number, or
account-history count (e.g. total days/posts) is stated — the source material's account-history figures
are deliberately omitted since none are needed for this story, and `CLAUDE.md` requires any such number be
pulled fresh from `STATS.md` at time of use, not reused from an August memory file.
**Image slots:** none exist yet — needs a separate design dispatch. Concept slots marked inline.

---

## Body

[IMAGE — HERO. Concept: two identical small icons, each labeled with a clock, sitting on opposite sides of
a thin broken line — the point being two systems, no longer connected, each still running.]

I'd already written once about moving my Instagram scheduler off my laptop and onto its own always-on
service, so it wouldn't care whether my laptop was open, closed, or on a plane. I said the local,
laptop-based version would stay on as a backup while I worked out a real fix for the cloud version. I meant
it as an honest "still open," not a loose end I expected to get hit.

It got hit.

My laptop was closed for a few hours one afternoon while I was traveling. When I checked back at the end of
the day, the scheduler itself had done its job — its own catch-up logic correctly noticed the one post it
had missed during the closed lid and fired it once things came back. That part worked exactly as designed.

What I found instead was two actual duplicate posts, live on the real account. Not a display glitch. Two
separate captions, each published twice.

## What actually happened

The cloud scheduler and the laptop backup share their sense of "what's already posted" through one common
record. That record had quietly stopped syncing cleanly between the two sometime around midday — a routine
step that keeps both copies in agreement had started failing without making any noise about it. From that
point on, each scheduler was working from its own, slightly different idea of what had already gone out,
with no way to see what the other had just done.

One post fired from the cloud side at 12:52. The laptop backup, unaware, fired the identical post again at
15:17. A second post fired from the laptop at 15:17, and the cloud side, equally unaware, fired that one
again at 18:12.

[IMAGE — Concept: a simple timeline strip showing four marks in sequence, two pairs, each pair labeled with
the same short tag — plain, diagrammatic, no screenshots.]

I didn't find this from my own logs, either — I found it by checking the account directly. The written
record actually under-reported what had happened: one scheduler's own confirmation step had reported itself
as failed, even though the post had gone out correctly, so its half of the story never made it into the
shared bookkeeping at all. The lesson I keep re-learning in different shapes: the log is
not the same thing as the account's real state. When something looks off, check the account, not the file
that's supposed to describe it.

## The fix, and the thing I tried that didn't work

The immediate fix was mechanical: reconcile the two divergent records back into one, and turn off one of
the two schedulers so exactly one is ever allowed to fire, until there's a sturdier design that doesn't
depend on two systems quietly agreeing with each other.

Cleaning up the two duplicate posts themselves was a different problem. I reached for the obvious tool —
the same script that publishes also has a delete function — and pointed it at one of them.

The platform sent back a flat rejection: deleting a published post through that interface isn't supported.
Not a permissions issue, not a bug on my end. The interface simply doesn't do that, full stop.

That mattered more than it sounds like it should, because a note I'd written earlier had claimed the
opposite — that this exact delete path had been "proven live and working." It hadn't. Nobody had actually
called it against a real post; the earlier note recorded an assumption as if it were a tested fact. I
corrected it out loud rather than let it quietly stand, because the whole point of writing any of this down
is that it's supposed to be checkable, and a false "proven working" note is worse than no note at all.

## What I built instead

Since I can't delete a duplicate automatically, I built something to catch one and tell me, fast. A check
now runs on its own, watching the account's real, live posts rather than any log file, grouping today's
posts by matching caption text. If it ever finds more than one copy of the same post, it still tries the
delete first — cheap to attempt, and the platform's own behavior here could change — but it now treats that
failure as the expected outcome, logs it plainly, and sends an alert naming the exact duplicate so a person
can remove it by hand, in the app, which is the only path that actually works.

## The gap that actually mattered

Both of those duplicates sat live on the account for about three hours before I saw them and deleted them
myself. That gap, not the missing auto-delete, was the real failure. The only alert that existed was a
notification on a laptop that was closed the entire time. A perfect detection system that only speaks to a
screen nobody's looking at isn't much of a system.

So I added a real alert that reaches a phone, not just a laptop — wired into the duplicate check, into the
scheduler's catch-up notice, and into a failed publish attempt, which used to fail completely silently
outside the log. I tested it against the real service and confirmed it arrives. I still need to finish
subscribing my own phone to it before I can call the loop actually closed — the code is proven; whether it
reaches me every time isn't confirmed yet, and I'd rather say that plainly than round it up to done.

More of this, honestly, at thequietai.com.

---

## Worker notes

- **Grounded entirely in `scribe-hands-git-race-duplicate-post-2026-08-30.md` and
  `scribe-hands-duplicate-post-autodelete-policy.md`** (both `~/.claude/projects/.../memory/`). The two
  schedulers, the diverged shared record, the two duplicate posts and their real times (12:52/15:17,
  15:17/18:12), the "proven live and working" claim that was never actually tested, the confirmed
  unsupported-operation response, the detect-and-alert redesign, the ~3-hour visibility gap, and the
  phone-push fix are all pulled directly from those two files. No detail invented.
- **Continuity note:** this piece opens by referencing "I'd already written once about moving my scheduler
  off my laptop" — a light callback to `the-automation-that-never-once-worked.md` (live), which ends on
  exactly this open thread ("a real fix... is still open. I'm leaving it open on purpose"). This piece
  stands alone and re-explains enough to be read independently, but the callback is intentional continuity,
  not an assumption the reader saw the earlier piece.
- **Numbers used are all sourced and non-account-history:** the specific post times per pair
  (12:52/15:17/18:12), "a few hours," "about three hours." **Deliberately omitted:** the source file's
  account-history figures (e.g., total days/post counts) — not needed for this story, and per `CLAUDE.md`'s
  standing rule any such count must be pulled fresh from `STATS.md` at time of use, not carried over from
  an August memory file that would be stale by September.
- **Platform/tool specifics kept concrete**, matching `the-automation-that-never-once-worked.md`'s
  precedent register: the delete-attempt, the platform-level rejection, and the account-vs-log distinction
  are all named plainly, without inventing technical jargon beyond what the source states.
- **The "I still need to finish subscribing my own phone" closing beat is a deliberate honesty-over-triumph
  choice**, matching `BRAND.md`'s "no triumph/redemption cash-out" rule — the source is explicit that
  delivery to a device is unconfirmed until the operator subscribes, and this piece states that plainly
  rather than rounding the fix up to fully done.
- **Refusal doctrine held throughout** — every decision (what to fix first, what to leave open, what to
  correct out loud) is attributed to the founder, never to the automation.
- ⛔ **NEVER-BLEND held.** No yoga identity, no GabeYoga branding, no year-count credential.
- **Needs a full honesty-gate pass before this is treated as cleared** — not self-certifying.
