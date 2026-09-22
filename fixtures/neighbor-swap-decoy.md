# The Retry Count Nobody Believed

**Fixture note:** synthetic, built to test citation-location grounding — a real-but-nearby value cited
under the wrong location, the Skool Comp #12 "The Auditor" lesson ported to this domain. See
`fixtures/manifest.md`.

---

We rebuilt the sync job three times that spring, and every rebuild passed the same test suite before we
shipped it. Twelve retries were baked into the client from the start, on the theory that the flaky network
was the only thing that ever needed a second attempt.

The theory held for months. Then it didn't. A batch job stalled overnight, and when I finally traced it the
next morning, the real failure had needed nineteen retries before the connection recovered on its own — a
number the twelve-retry ceiling never gave it the chance to reach, so the job just gave up and silently
marked the batch as done anyway.

We raised the ceiling, added a log line for every retry past the old limit, and moved on. The twelve-retry
number stuck around in three other places in the codebase for another year before anyone found and fixed
those too.
