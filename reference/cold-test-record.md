# Cold-test record — 2026-09-22

Per the dispatching brief's "after the build" step: a fresh Claude session, with no prior context on this
build and no answer key, was asked to read only the instruction/reference layer — `identity.md`,
`rules.md`, `examples.md`, `reference/schema.md`, `reference/grounding-methodology.md`,
`reference/genre-notes.md` — and find contradictions between them. It was explicitly told not to read
`verify.py`, `README.md`, or `fixtures/`, since the point was checking whether the *instruction* files agree
with each other, not whether the code matches the instructions.

## Findings (verbatim from the agent's report)

**1. Broken cross-reference.** `reference/schema.md` pointed to a section in `identity.md`
("§ Three properties") that didn't exist.

**2. Genre arc order didn't match the schema's role order.** `identity.md` and `genre-notes.md` both
narrate the story in the order it happened (incident → first impression → reveal). The schema's role order
puts the tension/contradiction (Hook) before the concrete event (Incident) — the two files never reconciled
why the sequence flips, or where the "first impression" beat actually lands.

**3. "verify.py is the fail-closed final gate" sat uneasily against its own documented blind spot.**
`identity.md`/`rules.md` described a clean `verify.py` run as "final, no caveat," while `rules.md`'s own
self-correction rule and `grounding-methodology.md`'s closing section state plainly that `verify.py` cannot
catch a citation of a pre-correction value mechanically. A clean run is necessary but not sufficient for
correctness — the "no caveat" language didn't scope that precisely.

**4. "One-paragraph input" vs. the essay-shape gate left an unresolved edge case.** `rules.md` said never
skip the 8-slide shape "even on a one-paragraph input," while the shape gate (`looks_like_teaching_essay()`)
requires several real paragraphs before it will proceed at all — the two rules could point opposite ways on
the same short input.

**5. (Minor) Example-leakage rule vs. example-reading requirement.** The rule against letting `examples.md`
leak into a new translation sits against the fact that `examples.md` is standing context on every run by
design. Named as a real but inherent tension, not a bug — the build's own answer is a real adversarial test
(`fixtures/one-word-perturbed.md`), not a rule that closes the exposure outright.

No contradictions were found in the citation-window definition, the refusal-language wording, or the
"not in source" mutual-exclusivity rule — all consistent across every file that states them.

## Fixes applied

1. Added a "Three properties that make this a translator, not a summarizer" section to `identity.md`;
   corrected `reference/schema.md`'s cross-reference to point at it.
2. Added a "Slide order is rhetorical, not strictly chronological" note to `reference/schema.md`, explaining
   that Hook and Incident often draw from the same in-medias-res opening material, and pointing at the real
   example (`fixtures/essay-1-dont-automate.output.json`: Hook cites p1s1, Incident cites p2s2-s3 — same
   opening scene, split by role).
3. Scoped the "no caveat" language in `identity.md` and `rules.md` specifically to grounding, added an
   explicit "necessary, not sufficient" scope note, and pointed both at `fixtures/manifest.md` § Known
   boundary.
4. Rewrote the "never skip the 8-slide shape" rule in `rules.md` to state the two paths as mutually
   exclusive by design: an input either passes the essay-shape gate (full 8 roles, some possibly
   `not in source`) or it doesn't (refuse outright) — never both, and never a literal "one-paragraph input"
   getting the full-shape treatment if it can't clear the gate.
5. Added one clarifying sentence to the example-leakage rule in `rules.md`, naming plainly that the rule
   doesn't close the exposure, only names it and tests it.

## Independent verification (research-claude honesty-gate, 2026-09-22)

research-claude re-ran `verify.py --selftest` and `--judge-mode` live, read the grounding logic against the
`can-spam-auditor` lineage it claims, and independently confirmed all 4 fixes above are genuinely present in
the current `identity.md`/`rules.md`/`reference/schema.md` text, not just claimed in a commit message.
**Result: PASS.** This file is the artifact that closes the one non-blocking gap the gate noted — the
cold-test record living only in a commit message rather than a checkable file.
