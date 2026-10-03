# Worked examples

Full essay text and full output JSON for all of these live in `fixtures/` — this file shows the reasoning,
not a duplicate copy. Run `python3 verify.py fixtures/<essay> fixtures/<output>.json` to see any of these
checked live.

## Worked example 1 — the happy path, and why this output isn't the human carousel's phrasing

**Input:** `fixtures/essay-1-dont-automate.md` — "Don't Automate It Until You've Taught It." All 8 roles
have material, including a named citation (Kieran Klaassen) and a described mechanism (Jake Van Clief's
stage-handoff framework).

**Output:** `fixtures/essay-1-dont-automate.output.json`. Two slides, abbreviated. On every slide `text` is exactly the join of its cited quotes; the Rule-or-Citation slide below cites the whole sentence so the attribution to Klaassen is a checked quote, not words added beside one:

```json
{"role": "Insight", "text": "I'd tested the script. I hadn't tested the absence of me.",
 "citations": [
   {"quote": "I'd tested the script.", "loc": "p4s1"},
   {"quote": "I hadn't tested the absence of me.", "loc": "p4s2"}
 ]}
```

```json
{"role": "Rule-or-Citation",
 "text": "Kieran Klaassen — who runs 44 AI agents across Every's projects, not three Instagram slots — has a name for the order I'd quietly jumped: build it, use it, trust it, and then orchestrate it.",
 "citations": [{"quote": "Kieran Klaassen — who runs 44 AI agents across Every's projects, not three Instagram slots — has a name for the order I'd quietly jumped: build it, use it, trust it, and then orchestrate it.", "loc": "p5s1"}]}
```

**Why this diverges from the essay's own real, hand-authored carousel** (`dont-automate-until-taught-
carousel.md`, in the same source tree as the essay — see `reference/genre-notes.md`): that carousel's slide
1 is "Every test I ran passed. The one test I never ran was the only one that mattered." — a skilled
editorial paraphrase, not a literal quote from any single sentence in the essay. A human copywriter is
licensed to compress like that. This translator isn't — every fact in its output has to be a checked
substring of a specific location, so its Hook slide instead quotes the essay's actual opening sentence
directly. The teaching content converges; the phrasing doesn't, on purpose. That's the whole difference
between a translator and a rewrite.

## Worked example 2 — "not in source," and preserving a name exactly as given

**Input:** `fixtures/essay-3-demo-bugs.md` — "I Found Bugs in My Own Demo. I Posted It Anyway." No named
external authority, no evidence-at-scale claim.

**Output:** `fixtures/essay-3-demo-bugs.output.json`:

```json
{"role": "Rule-or-Citation", "text": "not in source", "citations": []}
{"role": "Confirmation-at-scale", "text": "not in source", "citations": []}
```

This is the correct, complete output for those two roles on this essay — not a partial result. The essay
genuinely doesn't name an external authority or offer scale evidence; inventing either to fill the slot
would be exactly the disqualifying failure the dispatching brief names.

**Name preservation:** `fixtures/misspelled-name.md` is the sharper version of this same discipline — a
person's name appears once, informally self-typed as "Aleksei Petrosian," different from an earlier
third-person mention "Aleks Petrosyan." A correct translation cites whichever spelling actually appears at
the cited location, never a normalized or "corrected" version. `fixtures/misspelled-name.bad-output.json`
is the wrong move made concrete — a citation using a tidied third spelling ("Alex Petrosian") that appears
nowhere in the source, and `verify.py` fails it accordingly. See `rules.md` § Never.

## Worked example 3 — a self-correction resolves to the corrected value

**Input:** `fixtures/contradicted-correction.md` — a team states a launch date (March 3rd), then corrects it
(March 10th) in the next paragraph.

**Output:** `fixtures/contradicted-correction.output.json` cites the corrected value for the Reveal and
Close roles (Reveal shown):

```json
{"role": "Reveal", "text": "It was wrong. The project plan had always said March 10th.",
 "citations": [
   {"quote": "It was wrong.", "loc": "p2s1"},
   {"quote": "The project plan had always said March 10th.", "loc": "p2s2"}
 ]}
```

**Why this needs a rule, not just a checker:** both "March 3rd" and "March 10th" are literally present in
the source. A citation of the pre-correction "March 3rd" as if it were the final date would ground just as
cleanly as this one does — `verify.py` checks that cited text exists at its claimed location, not which of
two real, located facts is the one that still holds. Getting this right is `rules.md`'s job
("resolve a self-corrected fact to its corrected value"), demonstrated here, not something the offline
checker enforces on its own. See `fixtures/manifest.md` § Known boundary.
