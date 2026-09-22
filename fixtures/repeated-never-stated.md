# A Week of Standups About the Same Flaky Test

**Fixture note:** synthetic, built to test that volume of discussion is never mistaken for a stated,
groundable claim. The topic below is discussed at length across four paragraphs, but the actual lesson is
never plainly stated anywhere in the text — verify.py must reject an output that claims otherwise. See
`fixtures/manifest.md`.

---

Monday's standup opened with the flaky checkout test again. It had failed twice overnight, passed on rerun
both times, and nobody had a theory yet beyond "probably just flaky." We agreed to keep an eye on it and
moved on to the rest of the board.

Tuesday it failed three more times. Someone suggested it might be a timing issue in the test setup, someone
else thought it could be a shared database fixture bleeding state between runs, and a third person wondered
out loud whether it was really the test's fault at all rather than something in the checkout service itself.
Nobody had time to dig in that day either.

Wednesday and Thursday looked the same: the test kept failing intermittently, standup kept opening with it,
and the running joke became that it had its own line item on the agenda now. We talked about adding a retry
wrapper around it, talked about whether retries would just hide a real bug instead of fixing anything,
talked about who had bandwidth to actually own it, and never quite landed on an answer either day.

By Friday the test had failed nine more times across the week, someone finally sat down with the full log
history side by side, and the standup ended the way it had all week: more discussion, no decision, same test
still red on Monday.
