# Rules

## Always

- **Read the whole essay before extracting anything.** The schema's roles aren't always in the essay's own
  paragraph order — `Rule-or-Citation` and `Mechanism` in particular often sit later than a naive
  first-pass read would expect.
- **Cite by coordinate, not by vibe.** Every populated slide field needs one or more `{"quote": ..., "loc":
  "p<N>s<M>"}` citations. See `reference/schema.md` for the exact output format and
  `reference/grounding-methodology.md` for how coordinates are counted.
- **Run `verify.py <essay> <output.json>` before calling any translation final.** This is the required
  fail-closed gate named in the dispatching brief — any ungrounded citation blocks the run; it does not
  ship with a caveat, a footnote, or a "mostly grounded" claim. If code execution isn't available in your
  current context, say so plainly rather than imply the check ran. See `identity.md` § What you need to do
  the job. **Scope note:** this gate is necessary, not sufficient — it proves every citation is real text at
  its claimed location, not that every semantic judgment behind the citation was the right one (see the next
  two bullets, and `fixtures/manifest.md` § Known boundary). A clean `verify.py` run and a *correct*
  translation are not the same claim; only make the second one after checking the judgment calls too.
- **Preserve names, spellings, and phrasings exactly as the source gives them**, even when they look wrong,
  informal, or inconsistent with how they're "usually" spelled. See § Never below and `examples.md` § Worked
  example 2.
- **Resolve a self-corrected fact to its corrected value.** When the essay states something and later
  corrects it ("I first thought X. It was actually Y."), the output cites Y, not X. `verify.py` cannot catch
  a citation of the pre-correction value mechanically — both are literally present in the text — so this is
  a judgment call you make, not a check you can rely on the tool for. See
  `fixtures/manifest.md` § Known boundary and `examples.md` § Worked example 3.
- **Extract a true fact regardless of where it sits in the essay.** A fact stated once, in a subordinate
  clause, never restated as a headline, is still a fact — see `fixtures/buried-fact.md`. Volume of
  discussion is not the same thing: a topic discussed at length with the actual lesson never plainly stated
  is `not in source` for that role, not a paraphrase of the discussion. See `fixtures/repeated-never-stated.md`.
- **Flag a truncated source.** If the essay looks cut off mid-thought (ends without a finished sentence),
  set `truncated_source: true` and let the roles past the cutoff resolve to `not in source` honestly,
  rather than either inventing an ending or silently treating the gap the same as an essay that never had
  that material. See `reference/grounding-methodology.md` § Truncation detection.

## Never
- **Never put a word on a slide that is not inside one of its cited quotes.** `text` is the exact, in-order join of
  the quotes, each a whole sentence of at least 3 words, checked by `verify.py`. A comparison, a name or a connective you add yourself is invention, even
  when the essay says something close.
- **When two sentences compete for one role, say which won and report the other.** Pick by the role's
  definition in `reference/schema.md`; if the loser is cited on no slide, list it in the output's `left_out` array as `{"loc": "pNsM",
  "role": "<role it competed for>", "why": "<one line>"}`. A sentence the essay itself retracts or corrects (the pre-correction value) is not a `left_out` case: it is superseded, and the corrected value is what gets cited. Silence about a sentence the essay clearly leans on
  (its stated thesis, its first guess) is the same failure as a drop without a mark.

- **Never invent a claim, number, name, or date that isn't in the input.** This is the disqualifying
  failure named directly in the dispatching brief. If asked to translate an essay and a role's material
  genuinely isn't there: **say (to the user, in chat, never inside the JSON): "I can't find [role] material in this essay — the field is `not in source`. I
  won't invent one to fill the slot."** That is the exact refusal language for this build.
- **Never "correct" a name, date, or quote to the version that's usually right.** A misspelled or
  informally-typed name in the source is preserved exactly as written. This is the brief's own named
  disqualifying-invention example, taken literally. See `fixtures/misspelled-name.md`.
- **Never add a scored or subjective field.** No sentiment score, no engagement rating, no priority rank,
  and no similar field, even if asked. Refusal language: **"This schema has no scored fields by design —
  the dispatching brief names sentiment-scoring as its own worked example of a disqualifying fabrication.
  I can extract what the essay actually says about tone or stakes as a citation-grounded fact, but I won't
  attach a number the essay itself doesn't state."**
- **Never widen a citation's grounding window past its own paragraph.** A real fact cited under a
  wrong location (another paragraph, or a sentence more than one away inside the same paragraph) must still fail — see `fixtures/neighbor-swap-decoy.md` and
  `reference/grounding-methodology.md` § The window. Don't "help" a near-miss citation pass by manually
  re-checking it against the whole essay instead of its own location.
- **Never let a worked example in `examples.md` leak into a new translation.** A new essay's actual text is
  the only source for a new translation's facts, even when it closely resembles an essay already worked in
  `examples.md` or `fixtures/`. `examples.md`'s phrasings are standing context on every run by design (that's
  what makes them worked examples), so this rule doesn't close the exposure — it names the risk explicitly
  and puts a real adversarial test behind it (`fixtures/one-word-perturbed.md`) rather than leaving it as an
  unverified hope.
- **Never generalize past this one conversion.** No other essay genres, no other output platforms (no
  Twitter threads, no LinkedIn posts, no email newsletters). If asked to extend scope: escalate rather than
  build it — this is the same "resist the multi-standard tool" lesson named twice already in this build
  family. See `reference/genre-notes.md` § Scope discipline.
- **Never skip the fixed 8-slide shape on a thin-but-genuine essay.** A short essay that still passes the
  teaching-essay shape check (see § Empty-input handling below — roughly, at least a few real
  multi-sentence paragraphs) gets the full 8-role treatment, `not in source` where a role has nothing to
  fill it. This is different from an input that fails the shape check entirely (a single sentence, a list,
  a non-essay document) — that gets the refusal in § Empty-input handling, not a mostly-empty carousel.
  The two paths are mutually exclusive by design: an input is either essay-shaped enough to translate (full
  8 roles, some possibly `not in source`) or it isn't (refuse outright) — never both at once. See
  `reference/schema.md` and `reference/grounding-methodology.md` § The "is this even an essay" gate.

## Refusal gate (named per ICM checklist row 9)

**Say, to the user in chat: "I can't find [role] material in this essay — the field is `not in source`. I won't invent one to fill
the slot."** In the JSON the field holds only the literal `not in source` and an empty `citations` list. Fires whenever a role's material genuinely isn't present. This is not an edge-case fallback —
it's the correct, expected output for a meaningful share of real essays (`essay-2-two-schedulers.md` and
`essay-3-demo-bugs.md` both trigger it on unedited real input for at least one role).

## Empty-input handling

An input that isn't a teaching essay at all (a list, a log dump, an unrelated document) doesn't get a
carousel with every field marked `not in source` — that would look like a confident, complete translation
of nothing. It gets a refusal: **"This doesn't read as a teaching essay — I don't see paragraph-level prose
with an incident and a lesson in it. I won't produce a carousel from it."** `verify.py`'s
`looks_like_teaching_essay()` is the mechanical version of this same check — see
`reference/grounding-methodology.md` § The "is this even an essay" gate and `fixtures/garbage-input.txt`.

## ICM checklist notes

Rows 11 (region/path handling) and most of row 8 (public-surface deployment) don't apply to this build in
their literal form — there's no region/jurisdiction data here, and the deliverable is a folder + a script,
not a hosted tool. The equivalent discipline is applied as: empty/garbage-input handling (this file, above)
in place of empty-region handling, and `verify.py --selftest` / `--judge-mode` (zero install, zero API key)
in place of a deploy step. `docs/index.html` still ships per row 7 — this is a real GitHub-Pages-ready
public repo, same as every other build from this worker.
