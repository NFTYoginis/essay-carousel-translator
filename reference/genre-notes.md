# The genre this translator targets

**Incident-driven teaching essay → platform teaching-carousel.** Not "any essay" — a specific, real,
recurring genre, confirmed by reading three real examples before committing to it (per the dispatching
brief; see `fixtures/essay-1-dont-automate.md`, `essay-2-two-schedulers.md`, `essay-3-demo-bugs.md`, all
sourced from `~/Desktop/the-quiet-ai/writing/`).

## The shared arc

A real incident happened → what it first looked like → what it turned out to actually be → the compressed
lesson → (sometimes) an external authority who names the same rule → (sometimes) evidence the pattern isn't
a one-off → (sometimes) the underlying structural fix → a closing thought, no CTA.

The schema in `schema.md` is this arc, fixed into 8 roles. The parenthetical "sometimes" roles
(`Rule-or-Citation`, `Confirmation-at-scale`, `Mechanism`) are exactly the roles most likely to resolve to
`not in source` on a real essay that doesn't happen to include them — see `essay-2-two-schedulers.md` and
`essay-3-demo-bugs.md`, both real, both missing at least one of these on their own terms, not because the
translator failed to find something.

## Who does this by hand today

This is a real, recurring conversion, already done by hand in this operator's own content pipeline — a
canonical essay gets dispatched manually to a content/design pass each time it needs platform "sibling
cuts" (LinkedIn / Facebook / Skool / carousel versions of the same piece). `essay-1-dont-automate.md` ships
with its own real, hand-authored 10-slide carousel in the same source tree
(`dont-automate-until-taught-carousel.md`) — the ground-truth schema source for this build, and worth
reading directly to see what a human editor's version of this conversion looks like.

**That hand-authored carousel is not reused verbatim as this translator's output for the same essay.** Its
slide 1 ("Every test I ran passed. The one test I never ran was the only one that mattered.") is a skilled
paraphrase, not a literal quote from any single location in the essay — exactly the kind of editorial
compression a human copywriter is licensed to do and this translator is not. `examples.md`'s worked example
on this essay grounds every slide in a literal citation instead, and is deliberately NOT a copy of the human
carousel's phrasing, even where the underlying content overlaps. See `examples.md` § Worked example 1 for
the full reasoning.

## Scope discipline

This translator does one conversion — this essay genre, into this carousel schema — proven deep with real
fixtures and a real offline verifier. It does not generalize to other essay genres or other output formats
(no "and it also does Twitter threads"). Per the dispatching brief, this is the same lesson from two earlier
entries in this build family: resisting the pull toward a multi-standard tool in favor of one conversion,
done well, with a real adversarial test suite behind it. See `rules.md` § Never.
