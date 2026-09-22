# The Launch Date We Said Twice

**Fixture note:** synthetic, built to test that a self-corrected fact resolves to the CORRECTED value, not
the first-stated one. Both values are literally present in the text — this is not something `verify.py`'s
mechanical substring check can catch on its own (both citations would ground successfully; the wrong one
just cites the superseded value). This is a judgment call taught in `rules.md` and demonstrated in
`examples.md`, not a `--selftest` assertion. See `fixtures/manifest.md` § Known boundary.

---

We told the team the migration would ship on March 3rd. That date went into the release notes. It went into
the customer email draft too, and into two internal Slack channels, before anyone double-checked it against
the actual project plan.

It was wrong. The project plan had always said March 10th. The 3rd was a typo from an earlier draft, one
that got copied forward without anyone catching it. By the time someone noticed, three separate documents
already had the wrong date baked in.

We corrected all three the same afternoon. The migration did in fact ship on March 10th, on schedule once
you're counting from the date that was actually right the whole time.
