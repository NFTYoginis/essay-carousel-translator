# essay-carousel-translator

**Built for Skool Weekly Comp #13, "The Translator."** A folder-based AI translator: same shape in, same
shape out, every time. Not a summarizer. Not a writer. A converter with a contract.

**Converts:** one incident-driven teaching essay (a real event → first guess → what it turned out to be →
the lesson → sometimes a citation, sometimes scale-evidence, sometimes a mechanism → a closing thought) into
a fixed 8-slide teaching carousel. See `reference/genre-notes.md` for the exact genre and who does this
conversion by hand today.

## Press one button

```
$ python3 verify.py --judge-mode
essay-carousel-translator --judge-mode
Four adversarial checks. Each one encodes a named failure this build was built to resist.

-- neighbor-swap-decoy.md --
   Skool Comp #12 'The Auditor' lesson, ported...
   [PASS] caught: "...nineteen retries..." NOT found in the source window at p1s2 (...)

-- misspelled-name.md --
   the brief's own named disqualifying-invention example...
   [PASS] caught: "A colleague, Alex Petrosian, mentioned it..." NOT found...

-- garbage-input.txt --
   the can-spam-auditor 2026-09-05 incident, ported...
   [PASS] refused to parse (NotATeachingEssayError)

-- repeated-never-stated.md --
   volume of discussion is not the same as a stated, groundable claim...
   [PASS] caught: "The real problem was that nobody owned the flaky test" NOT found...

JUDGE-MODE PASSED -- all four confirmed live, right now
```

Under a second, nothing to install beyond Python 3. Each check is a real, named failure mode this build was
built against — not a hypothetical. Full reasoning for each in `fixtures/manifest.md`.

## Full test suite

```
$ python3 verify.py --selftest
```

Runs all 10 fixture pairs (3 real essays, 7 synthetic attacks) plus the garbage-input refusal — 65
individual grounding checks in total. `SELFTEST PASSED` on a clean run.

## The contract, in one sentence

Every translation produces exactly 8 slide roles, in fixed order, every run — populated ones cite the exact
paragraph+sentence they came from, empty ones say `not in source`, and nothing ships until `verify.py`
confirms every citation is a real substring of the location it claims. See `reference/schema.md`.

## Two ways to use this

**Run the offline checker yourself (30 seconds, the real deterministic part):**

1. Clone this repo. Python 3.9+, nothing else — no `pip install`.
2. `python3 verify.py --selftest` — confirm the checker works on your machine.
3. `python3 verify.py fixtures/essay-1-dont-automate.md fixtures/essay-1-dont-automate.output.json` — verify
   one real translation by hand.

**Drop the folder into a Claude Project (or a code-execution-enabled chat) to translate a new essay:**

Add this repo to a Claude Project (or paste `identity.md` / `rules.md` / `examples.md` / `reference/` into
its instructions), paste in a new essay matching the genre in `reference/genre-notes.md`, and ask for a
translation. The specialist extracts the 8 roles, cites every fact, and — with code execution enabled —
runs `verify.py` against its own output before calling it final. **Without code execution, it can still do
the extraction by hand-checking citations against the essay text, and is instructed to say plainly that
`verify.py` wasn't run mechanically, rather than imply it was.** See `identity.md` § What you need to do the
job.

## What it checks (and what it honestly doesn't)

`verify.py` mechanically checks **grounding** — is a cited fact a real substring of the specific
paragraph+sentence window it claims, narrow enough that a real-but-wrong-location value still fails (see
`fixtures/neighbor-swap-decoy.md`, the ported Skool Comp #12 lesson). It does **not** and cannot check
whether a slide's role assignment is the semantically right one, or which of two self-corrected values is
the final one (`fixtures/contradicted-correction.md`) — those are the specialist's job, taught in
`rules.md`/`examples.md`. Full boundary in `fixtures/manifest.md` § Known boundary.

## Usage

```
python3 verify.py <essay.md> <output.json>   # verify one translation, Markdown-style report, exit 0/1/2
python3 verify.py --selftest                  # run all fixtures, prove the checker works
python3 verify.py --judge-mode                # the 4 adversarial checks above, live, ~10 seconds
```

Exit `0` if every citation grounds; `1` if any citation fails grounding; `2` on a malformed/non-essay
input or an invalid output shape.

## What this is not

Not a general summarizer, and not a multi-genre or multi-platform tool. One essay genre in, one carousel
schema out — see `reference/genre-notes.md` § Scope discipline. Not a generator: `verify.py` verifies a
given translation against a given essay; it doesn't produce one. The actual extraction — reading the essay,
deciding what's Hook vs. Incident vs. Insight — is done by whoever (or whatever) is loaded with
`identity.md`/`rules.md`/`examples.md`, same as every other specialist this worker builds.

## Repo layout

```
verify.py                        ← the whole grounding engine, stdlib only
fixtures/
  essay-{1,2,3}-*.md             ← 3 real essays (operator's own published writing)
  essay-{1,2,3}-*.output.json    ← correct, fully-grounded translations of each
  neighbor-swap-decoy.md · misspelled-name.md · one-word-perturbed.md ·
  truncated.md · buried-fact.md · repeated-never-stated.md ·
  contradicted-correction.md     ← synthetic attack fixtures, one per named trick
  garbage-input.txt              ← non-essay input, must refuse to parse
  manifest.md                    ← what each fixture proves, PASS/FAIL table
reference/
  schema.md                      ← the 8-role contract + output JSON format
  grounding-methodology.md       ← the citation coordinate system, ported from can-spam-auditor
  genre-notes.md                 ← the essay genre this targets, and who does this by hand today
identity.md / rules.md / examples.md   ← the ICM specialist layer
docs/index.html                  ← this repo's own landing page (GitHub Pages)
```

## Sources

The three real essays in `fixtures/` are the operator's own published/pre-publication writing, from
`~/Desktop/the-quiet-ai/writing/` — see `LICENSE` for their reproduction terms (not MIT-covered). The
grounding methodology is ported from this worker's own `builds/can-spam-auditor/audit.py`; see
`reference/grounding-methodology.md` for the full lineage.

## License

MIT for the code — see `LICENSE` (fixture essays are separately licensed, same file).
