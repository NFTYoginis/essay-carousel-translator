# The 8-slide schema — the contract

This is the whole contract. Every translation produces exactly these 8 roles, in exactly this order, every
run, regardless of what the input essay contains. Short input → output still has every field, marked empty
where there was nothing to fill it. This is what makes it a translator and not a summarizer — see
`identity.md` § Three properties that make this a translator, not a summarizer.

| # | Role | What it is |
| - | --- | --- |
| 1 | **Hook** | the essay's own opening tension/contradiction |
| 2 | **Incident** | the concrete event that happened |
| 3 | **Reveal** | what turned out to be true, contradicting the first guess |
| 4 | **Insight** | the compressed, quotable lesson |
| 5 | **Rule-or-Citation** | a named external source/rule, if the essay cites one |
| 6 | **Confirmation-at-scale** | evidence the pattern isn't a one-off, if the essay includes any |
| 7 | **Mechanism** | the underlying structural fix, if the essay describes one |
| 8 | **Close** | the essay's own final thought — no CTA, no link |

**Slide order is rhetorical, not strictly chronological.** `reference/genre-notes.md`'s shared arc narrates
the story in the order it actually happened (incident → what it first looked like → what it turned out to
be). The schema's role order is not a re-narration of that timeline — Hook and Incident often draw from the
*same* opening material, because most essays in this genre open in medias res: the concrete event and the
narrator's first (wrong) read of it arrive in the opening paragraphs. `Hook` is whichever part of that opening
carries the tension/contradiction; `Incident` is whichever part states the concrete event; on many essays
these cite adjacent or even overlapping sentences (see `fixtures/essay-1-dont-automate.output.json`, where
Hook cites p1s1 and Incident cites p2s2-s3 — the same opening scene, split by which specific fact each role
needs). Two roles may cite the same sentence; `left_out` is only for a sentence that lost every role it competed for. `Reveal` always comes after both, regardless of where the essay's own reveal paragraph sits,
because a role's position in the carousel is about the role it plays, not the sentence order it was written
in.

**No scored or subjective field anywhere in this schema.** No sentiment score, no engagement rating, no
priority rank. The dispatching brief names sentiment-scoring as its own worked example of a disqualifying
fabrication — the fix isn't a defensible version of it, it's not having the field. If a future request asks
for one, `rules.md` § Never names the exact refusal.

## Output format

```json
{
  "source": "<essay filename>",
  "truncated_source": false,
  "left_out": [],
  "slides": [
    {
      "role": "Hook",
      "text": "the plain join of this slide's citation quotes, nothing else",
      "citations": [
        {"quote": "exact substring expected in the source", "loc": "p3s2"}
      ]
    },
    ...
    { "role": "Rule-or-Citation", "text": "not in source", "citations": [] }
  ]
}
```

**`left_out`** is a list (empty when nothing competed) of `{"loc": "pNsM", "role": "<role it competed for>",
"why": "<one line>"}`: the sentences the essay clearly leans on that lost a role to another sentence. Each `loc`
must exist in the essay; `verify.py` checks it. See `rules.md` § Never.

**Every populated field cites at least one location.** `citations[].quote` is checked as a literal
substring of its own `loc`'s window — see `reference/grounding-methodology.md`. `text` is **the plain join of its
citation quotes, separated by single spaces, and nothing else**. `verify.py` removes every cited quote from `text`
(ignoring case) and fails the slide if any word is left; punctuation between quotes is ignored, a word is not (Comp #13: a checker that proves the quote exists is half a gate; this is the other half). No
bridging, no paraphrase, no connective the essay does not contain. If a slide needs more context, cite more
of the essay.

## The "not in source" rule

If a role has no material in the essay, its `text` field is the literal string `not in source` and its
`citations` list is empty. Never omit the slot. Never invent content to fill it. This is not a fallback for
error cases — it's an expected, correct output for a large share of real short-form essays (see
`essay-2-two-schedulers.md` and `essay-3-demo-bugs.md` in `fixtures/`, both of which correctly resolve
`Rule-or-Citation` and/or `Confirmation-at-scale` to `not in source`, on real, unedited input).

`verify.py`'s `check_shape()` enforces this mechanically: a populated `text` with empty `citations` is a
shape error, and so is `text` equal to `not in source` with a non-empty `citations` list. The two states
are mutually exclusive on purpose — there's no way to half-say "not in source."

## `truncated_source`

A truncated essay is not the same failure as an essay that genuinely has no material for a role, and the
output must say which one happened (see `reference/grounding-methodology.md` § Truncation detection). Set
`truncated_source: true` at the top level when the source essay looks cut off mid-thought. `verify.py`
checks this mechanically (last line of the body has no terminal punctuation) and fails the run if the flag
disagrees with what it finds.
