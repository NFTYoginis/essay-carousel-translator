# fixtures/ manifest

Every essay in this folder ships with either an `.output.json` (a correct, fully-grounded translation —
proves the shape works) or a `.bad-output.json` (a deliberately wrong translation, hand-authored to encode
one specific attack — proves `verify.py` catches it). `verify.py --selftest` runs every pair below and
checks the outcome matches this table. `verify.py --judge-mode` runs the four marked ★ live.

| Fixture | Pair | What it proves | 
| --- | --- | --- |
| `essay-1-dont-automate.md` | `.output.json` — PASS | shape holds on a real essay (the canonical "Don't Automate It Until You've Taught It," ground-truth carousel in the same source tree) |
| `essay-2-two-schedulers.md` | `.output.json` — PASS | shape holds on a genuinely different real essay; `Rule-or-Citation` and `Confirmation-at-scale` correctly resolve to `not in source` (this essay names no external authority and gives no scale-evidence) |
| `essay-3-demo-bugs.md` | `.output.json` — PASS | shape holds on a third real essay, deliberately the shortest/simplest, no named citation — proves the "not in source" path on real (not synthetic) material, per the dispatching brief |
| ★ `neighbor-swap-decoy.md` | `.bad-output.json` — FAIL | Skool Comp #12 "The Auditor" lesson, ported: a real value cited under the wrong-but-nearby location. Two similar numbers (12 retries / 19 retries) sit one paragraph apart; the bad output cites the true "19 retries" claim at the "12 retries" location. Must FAIL — the words exist in the essay, just not there. |
| ★ `misspelled-name.md` | `.bad-output.json` — FAIL | the brief's own named disqualifying-invention example: "a name spelled the way it usually is instead of the way it appeared." The source gives an informal, misspelled self-typed name; the bad output "corrects" it to a tidy spelling that appears nowhere in the text. Must FAIL. |
| `one-word-perturbed.md` | `.bad-output.json` — FAIL | exemplar-leakage: a near-identical copy of `essay-1-dont-automate.md` with exactly one fact changed ("forty-four" → "thirty-one"). The bad output reuses the ORIGINAL example's "forty-four" instead of reading this file's actual value. Must FAIL. |
| `garbage-input.txt` | (no output — refusal) | ★ the can-spam-auditor 2026-09-05 incident, ported: a grocery list fed to a lenient checker once produced a fluent fake report. `parse_essay()` must raise `NotATeachingEssayError` before any citation check runs. |
| `truncated.md` | `.output.json` — PASS, `truncated_source: true` | a real essay (`essay-3-demo-bugs.md`) cut off mid-paragraph. Must set `truncated_source: true` and resolve `Mechanism`/`Close` to `not in source` — distinct from an essay that genuinely never had those sections (`looks_truncated()` is a mechanical last-line-punctuation check, not a length heuristic). |
| `buried-fact.md` | `.output.json` — PASS | the Insight is stated exactly once, in a subordinate clause inside a 72-word sentence, never restated. Must still be extracted and correctly cited — proves the translator doesn't only catch headline-positioned claims. |
| ★ `repeated-never-stated.md` | `.bad-output.json` — FAIL | a topic (a flaky test) discussed at length across 4 paragraphs; the "lesson" is never plainly stated anywhere. The bad output invents a tidy-sounding lesson and cites a paragraph that merely discusses the topic. Must FAIL — volume of discussion isn't a stated claim. |
| `contradicted-correction.md` | `.output.json` — PASS | the essay states a fact (March 3rd) then corrects it (March 10th). The correct output cites the corrected value. **Known boundary:** both values are literally present in the source, so a bad output citing the PRE-correction value would also ground successfully — `verify.py`'s substring check cannot catch this class of error by itself. Which value is "final" is a semantic judgment, taught in `rules.md` and demonstrated in `examples.md`, not mechanically enforced. This fixture documents that boundary rather than papering over it. |

## Known boundary — what `verify.py` checks vs. what only a reader's judgment provides

Same two-track honesty as `builds/can-spam-auditor/audit.py`'s `AUTOMATED` / `AI-ASSISTED` split, applied
here: `verify.py` mechanically checks **grounding** — is the cited text really a substring of the specific
paragraph+sentence window it claims. It does **not** and cannot check:

- Whether a slide's role assignment is the semantically right one (is this really the Insight, not the Hook).
- Which of two literally-present, self-corrected values is the "final" one (`contradicted-correction.md`).
- (closed in v2) `text` is the exact join of its quotes, so there is no paraphrase left to judge.
- **Still a reader's job (found by the independent re-gate, 2026-10-03):**
  - Two whole sentences from neighbouring paragraphs, in source order, can read as a claim the essay does not make (cause and effect flipped), and a sentence can mislead when quoted alone. The checker bounds the stitching (whole sentences, source order judged on real positions, same or adjacent paragraph) but cannot judge meaning.
  - `left_out[].why` is free text; only its `loc` and `role` are checked.
  - An all-`not in source` middle (Incident through Mechanism) is accepted: absence cannot be proven mechanically. Hook and Close are required.
  - Parser limits, inherited and unchanged: a heading directly followed by a paragraph with no blank line drops that paragraph; a fixed list of common abbreviations (Dr., Mr., vs., e.g., etc., U.S.) no longer splits a sentence, but any other abbreviation still can and puts a human-counted loc one sentence off; a `---` scene break inside the body ends the body. A quote must carry its sentence's final punctuation and any list marker ("2. Post it as a clean walkthrough."), and two sentences are cited as two quotes; that strictness is deliberate.
  - A sentence can be a strawman or a setup that the essay then rejects. Quoted alone it passes, because it is a whole real sentence. Only a reader tells.

Those are the specialist's job — taught in `identity.md` / `rules.md`, demonstrated in `examples.md`, and
checkable by a human reader opening the essay next to the output. `verify.py` is the fail-closed gate for
the one thing that's fully mechanical: a citation either points at real text, or it doesn't, and the slide says nothing the citations do not.

## `contradicted-correction.md` and `one-word-perturbed.md` are not in `--judge-mode`

`--judge-mode` runs the 4 checks the dispatching brief named explicitly. The other 6 fixtures (including
these two) are real, run every time in `--selftest`, just not narrated live in the 10-second version —
`--selftest`'s full 10-pair run is one command away for anyone who wants the complete picture.
