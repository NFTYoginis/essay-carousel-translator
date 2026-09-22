# The Migration That Took a Weekend Longer Than Planned

**Fixture note:** synthetic, built to test that the Insight isn't missed when it's stated once, in a
subordinate clause, and never restated headline-style — the brief's own named CRM-note failure example,
ported to this domain. See `fixtures/manifest.md`.

---

We scheduled the database migration for a Friday night, expecting it to run over the weekend and be done by
Monday standup. It wasn't. By Sunday afternoon, barely a third of the rows had moved, and the whole team was
back online trying to figure out why.

The dashboard we'd built to watch progress was reporting a healthy, steady rate the entire time — which,
once we actually sat down and compared the dashboard's numbers against the database's own row counts, a
comparison nobody had thought to run until Sunday, turned out to be counting retried rows as new progress
each time they retried, so a single stuck batch could inflate the on-screen percentage indefinitely while
genuinely doing nothing.

We rewrote the progress query to count distinct row IDs instead of retry attempts, and the real number
dropped from "94% done" to "31% done" the instant we deployed the fix. The migration itself finished the
following Wednesday, three days late, with no further surprises once the numbers finally meant what everyone
assumed they meant.
