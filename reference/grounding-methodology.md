# Grounding methodology — the citation coordinate system

**Ported from `builds/can-spam-auditor/audit.py`'s `quote_is_grounded()` + `load_reference_anchors()`**
(this worker's own prior build). That checker verifies a regulatory citation is a real substring of the
*specific provision* it's cited under, never the whole corpus — the fix for the defect class that beat 7 of
20 entries (including this build family's own ancestor) in Skool Comp #12 "The Auditor": a quote left
word-for-word correct, but cited under the wrong provision. This file ports the same principle to a
paragraph+sentence coordinate system instead of a named-provision one, because essays don't have provisions
— they have paragraphs and sentences.

## Why "found somewhere in the essay" isn't enough

A citation that's checked against the whole document, rather than the specific location it claims, will
pass a **neighbor swap**: a real fact, true and present in the essay, cited under the wrong paragraph. See
`fixtures/neighbor-swap-decoy.md` — two similar numbers ("twelve retries," "nineteen retries") sit one
paragraph apart; a wrong-but-plausible citation of the real "nineteen" value at the "twelve" location must
fail, and it only fails if the check is scoped to that specific window.

## The coordinate: `p<N>s<M>`

- **Body extraction.** The essay's body is the text between the first `---` rule and the second one, if a
  second exists (a metadata/worker-notes footer sits after it and isn't essay content); otherwise everything
  after the first `---` to EOF. Markdown headers (`## ...`) and bracketed visual notes (`[IMAGE ...]`) are
  dropped — they're structure and design intent, not prose claims.
- **Paragraphs (`p<N>`)** are blank-line-separated blocks of the remaining body, numbered sequentially from 1.
- **Sentences (`s<M>`)** are split within each paragraph by a regex requiring 2+ letters/digits before a
  terminal `.`/`!`/`?`, so list markers like "1." don't get split off as their own sentence. This is a
  documented-limitation splitter, not a linguistic parser — see § Boundary drift below for why that's fine.

## The window: cited sentence ± 1, same paragraph only

`verify.py` doesn't check a citation against its exact sentence alone — it checks against that sentence plus
one sentence before and one after, **within the same paragraph only**. Two things this buys:

1. **Boundary-drift tolerance.** Sentence-splitting disagrees with a human reader by exactly one unit often
   enough to matter — an abbreviation, a colon before a quoted line, an em-dash mid-thought. A ±1 bracket
   absorbs that disagreement without the check becoming meaningless.
2. **Still narrow enough to catch a real attack.** The bracket does not cross into a neighboring paragraph.
   Widening it that far would make `neighbor-swap-decoy.md`'s attack pass — the exact defect this file
   exists to prevent. Narrow on purpose; see `fixtures/manifest.md`.

## Normalization

Before the substring check, both the citation's `quote` and the source window are normalized: markdown
link/bold/italic syntax stripped to plain text (`[text](url)` → `text`), curly quotes and em/en-dashes
folded to their ASCII equivalents, and whitespace collapsed. This matches what a slide's on-slide text
actually looks like — a reader never sees `[Jake Van Clief](https://...)`, they see "Jake Van Clief." The
substring check has to compare like with like.

## Truncation detection

Distinguishing "this essay genuinely has no Mechanism section" from "this document looks incomplete" is one
of the brief's own named failure modes (`fixtures/truncated.md`). The mechanical proxy: if the body's last
non-empty line doesn't end in terminal punctuation (optionally followed by a closing quote/paren), the essay
is flagged truncated. A finished essay's closing thought always lands on a complete sentence; a file cut off
mid-paragraph usually doesn't. This is a shape check, not a content judgment — same spirit as
`looks_like_teaching_essay()` below.

## The "is this even an essay" gate

`looks_like_teaching_essay()` is the direct port of `can-spam-auditor`'s `NotAnEmailError` — a mechanical
shape check that runs before any citation logic, refusing to proceed on input that doesn't have the right
*shape*, not input that fails a content judgment. A grocery list, a log dump, or a short announcement all
fail on shape (too few multi-sentence paragraphs) — see `fixtures/garbage-input.txt` and
`fixtures/manifest.md`. This is deliberately a proxy, not a semantic essay-detector: it can be fooled by
sufficiently long, sufficiently sentence-structured non-essay prose, and it can reject a genuinely terse
real essay. Both failure directions are named here rather than left implicit.

## What this file's mechanism does NOT check

See `fixtures/manifest.md` § Known boundary and `identity.md` § What you need to do the job. Grounding
(is the text really there, at that specific location) is fully mechanical. Extraction (which text deserves
to be the Insight; which of two self-corrected values is the final one) is not — it's the specialist's job,
taught here and in `rules.md`/`examples.md`, checked by a human reader, not by `verify.py`.
