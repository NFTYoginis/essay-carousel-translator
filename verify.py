#!/usr/bin/env python3
"""
essay-carousel-translator/verify.py — offline grounding checker.

Checks a translated carousel (a JSON file, the specialist's OUTPUT) against
the essay it claims to be translated FROM (a Markdown file, the INPUT).
It does one job: for every citation the output makes ("this on-slide text
came from paragraph 3, sentence 2"), confirm the claimed text is really a
substring of THAT specific paragraph+sentence window in the source — not
"found somewhere in the essay." That distinction is the whole mechanism —
see reference/grounding-methodology.md for why, and Skool Comp #12 "The
Auditor" for the adversarial test that made it non-optional (a quote left
word-for-word correct but cited under the wrong location beat 7/20 entries,
including this build family's own ancestor; the fix shipped in
builds/can-spam-auditor/audit.py as quote_is_grounded()+load_reference_anchors()
— this file ports the same principle to a paragraph+sentence coordinate
system instead of a named-provision one).

verify.py does NOT generate carousels and does NOT judge whether a slide's
role assignment is the right one semantically (is this really the Insight,
not the Hook?). Only a reader (a person, or Claude loaded with identity.md /
rules.md / examples.md) does that. verify.py checks one mechanical fact:
does the cited text actually live where the output says it lives. See
fixtures/manifest.md (section 'Known boundary') for the full boundary.

Zero third-party dependencies. Zero network calls. Zero API key required.

Usage:
    python3 verify.py <essay.md> <output.json>   # verify one translation
    python3 verify.py --selftest                  # run fixtures/, prove the checker works
    python3 verify.py --judge-mode                 # 4 adversarial checks, live, ~10 seconds
    python3 verify.py --matrix                     # planted faults, each must fail through its own gate
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = REPO_ROOT / "fixtures"

SLIDE_ROLES = [
    "Hook",
    "Incident",
    "Reveal",
    "Insight",
    "Rule-or-Citation",
    "Confirmation-at-scale",
    "Mechanism",
    "Close",
]

NOT_IN_SOURCE = "not in source"

# --------------------------------------------------------------------------
# essay parsing — body extraction, paragraph split, sentence split
# --------------------------------------------------------------------------


class NotATeachingEssayError(Exception):
    """Raised when the input has no recognizable teaching-essay shape at all
    -- i.e. it isn't prose with paragraphs and sentences, not just an essay
    missing a role's material. Those are different failures and must not
    produce the same output: a genuinely thin essay missing a Mechanism
    section is a real 'not in source' finding worth reporting; a grocery
    list or a raw log dump fed to a lenient parser is not an essay at all,
    and translating it into a fully-populated 8-slide carousel would be
    indistinguishable from a genuine translation. Direct port of the failure
    class documented in builds/can-spam-auditor/audit.py's NotAnEmailError
    (a 2026-09-05 adversarial test got a fully-formed fake report from
    non-email text before that check existed) -- assume the same test is
    coming here."""


def extract_body(raw_text: str) -> str:
    """Body = text between the first '---' rule and the second one, if a
    second exists (worker-notes / metadata footers sit after it and are not
    essay content); otherwise everything after the first '---' to EOF; if
    there's no '---' at all, the whole text is the body (garbage input has
    no metadata header to strip)."""
    rules = [m.start() for m in re.finditer(r"^---\s*$", raw_text, re.M)]
    if len(rules) >= 2:
        first_end = raw_text.index("\n", rules[0]) + 1
        return raw_text[first_end: rules[1]]
    if len(rules) == 1:
        first_end = raw_text.index("\n", rules[0]) + 1
        return raw_text[first_end:]
    return raw_text


def _strip_markdown(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)  # [text](url) -> text
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)  # bold
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", s)  # italic
    return s


def split_paragraphs(body: str) -> list[str]:
    """Blank-line-separated blocks, with markdown headers ('#...') and
    bracketed visual/image-concept notes ('[IMAGE ...]') dropped -- those
    aren't prose claims a translator should ever cite. Order preserved;
    numbering (p1, p2, ...) is sequential over what's left."""
    blocks = re.split(r"\n\s*\n", body.strip())
    paragraphs = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            continue
        if block.startswith("[IMAGE"):
            continue
        paragraphs.append(_strip_markdown(re.sub(r"\s+", " ", block)).strip())
    return paragraphs


_SENTENCE_BOUNDARY = re.compile(r'[a-zA-Z0-9]{2}[.!?]["\')]?')
_SENTENCE_NEXT = re.compile(r'\s+[A-Z0-9"\'(\[]')


def split_sentences(paragraph: str) -> list[str]:
    """Documented-limitation splitter (abbreviations, decimals, list markers
    like '1.' can disagree with a human's idea of a sentence boundary by one
    unit). That's exactly why every citation window in this file is checked
    with a +/-1-sentence boundary-drift bracket rather than an exact index
    match -- the disagreement is expected, not a bug to chase to zero.
    Requires 2+ letters/digits before the terminator so list markers like
    '1.' or '2.' don't get split off as their own sentence."""
    text = paragraph.strip()
    if not text:
        return []
    split_points = []
    for m in _SENTENCE_BOUNDARY.finditer(text):
        end = m.end()
        if end >= len(text):
            continue
        if _SENTENCE_NEXT.match(text[end:]):
            split_points.append(end)
    sentences = []
    start = 0
    for pos in split_points:
        sentences.append(text[start:pos].strip())
        start = pos
    sentences.append(text[start:].strip())
    return [re.sub(r"\s+", " ", s).strip() for s in sentences if s.strip()]


def parse_essay(raw_text: str) -> list[list[str]]:
    """Returns paragraphs[i] = list of sentences, 0-indexed internally;
    loc strings ('p{N}s{M}') are 1-indexed on top of this."""
    body = extract_body(raw_text)
    paragraphs = split_paragraphs(body)
    if not looks_like_teaching_essay(paragraphs):
        raise NotATeachingEssayError(
            "This doesn't look like a teaching essay -- too few paragraphs, "
            "or the paragraphs present don't look like multi-sentence prose "
            "(a grocery list, a log dump, and a short announcement all fail "
            "this shape check). verify.py refuses to check citations against "
            "it rather than silently proceed as if it read a real essay. If "
            "this is genuinely a teaching essay, confirm it wasn't pasted as "
            "a bulleted outline instead of prose, and that it has at least "
            "3 real paragraphs."
        )
    return [split_sentences(p) for p in paragraphs]


def looks_like_teaching_essay(paragraphs: list[str]) -> bool:
    """Mechanical shape check, not a semantic one -- same spirit as
    NotAnEmailError's 'zero RFC 5322 headers' test. A real teaching essay in
    this genre reliably has several multi-sentence prose paragraphs; a
    grocery list or log dump reliably doesn't. This is a proxy, not a
    content judgment -- it's checking for prose SHAPE."""
    if len(paragraphs) < 3:
        return False
    multi_sentence = 0
    total_sentences = 0
    long_enough_words = 0
    for p in paragraphs:
        sentences = split_sentences(p)
        total_sentences += len(sentences)
        if len(sentences) >= 2:
            multi_sentence += 1
        words = p.split()
        if len(words) >= 12:
            long_enough_words += 1
    if multi_sentence < 2:
        return False
    if total_sentences < 5:
        return False
    if long_enough_words < 2:
        return False
    return True


def looks_truncated(raw_text: str) -> bool:
    """Mechanical proxy for 'this essay was cut off mid-thought', distinct
    from 'this essay genuinely has no Mechanism section'. If the body's last
    non-empty line doesn't end in terminal punctuation (or a closing quote
    after one), treat it as truncated -- a real essay's Close slide always
    lands on a finished sentence; a truncated file usually doesn't."""
    body = extract_body(raw_text).rstrip()
    if not body:
        return True
    last_line = body.splitlines()[-1].strip()
    return not re.search(r'[.!?]["\')]?$', last_line)


# --------------------------------------------------------------------------
# citation coordinates + grounding
# --------------------------------------------------------------------------

_LOC_RE = re.compile(r"^p(\d+)s(\d+)$")


def parse_loc(loc: str) -> tuple[int, int]:
    m = _LOC_RE.match(loc.strip())
    if not m:
        raise ValueError(f"malformed citation location: {loc!r} (expected 'p<N>s<M>')")
    return int(m.group(1)), int(m.group(2))


def normalize(s: str) -> str:
    s = _strip_markdown(s)
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("‘", "'").replace("’", "'")
    s = s.replace("—", "--").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip()


def window_for_loc(paragraphs: list[list[str]], loc: str) -> str | None:
    """The cited sentence, plus one sentence before/after IN THE SAME
    PARAGRAPH ONLY as a boundary-drift bracket -- deliberately does not
    cross into a neighboring paragraph. Widening the window that far would
    let a real-but-wrong-location value (the Comp #12 defect class, and this
    build's own neighbor-swap-decoy fixture) slip through on the grounds
    that the words exist 'nearby'. Narrow on purpose."""
    p_idx, s_idx = parse_loc(loc)
    if p_idx < 1 or p_idx > len(paragraphs):
        return None
    sentences = paragraphs[p_idx - 1]
    if s_idx < 1 or s_idx > len(sentences):
        return None
    lo = max(0, s_idx - 1 - 1)
    hi = min(len(sentences), s_idx - 1 + 1 + 1)
    return " ".join(sentences[lo:hi])


def quote_is_grounded(quote: str, loc: str, paragraphs: list[list[str]]) -> bool:
    window = window_for_loc(paragraphs, loc)
    if window is None:
        return False
    return normalize(quote) in normalize(window)


# --------------------------------------------------------------------------
# output-shape checking
# --------------------------------------------------------------------------


class ShapeError(Exception):
    """The output JSON doesn't have the fixed 8-slide shape at all -- wrong
    role count/order/names. This is checked before grounding, since a
    shape violation makes per-citation grounding meaningless."""


def check_shape(output: dict) -> None:
    slides = output.get("slides")
    if not isinstance(slides, list) or len(slides) != len(SLIDE_ROLES):
        raise ShapeError(
            f"expected exactly {len(SLIDE_ROLES)} slides, got "
            f"{len(slides) if isinstance(slides, list) else type(slides).__name__}"
        )
    left_out = output.get("left_out", [])
    if not isinstance(left_out, list) or any(
        not isinstance(x, dict) or not {"loc", "role", "why"} <= set(x) for x in left_out
    ):
        raise ShapeError("left_out must be a list of {loc, role, why} objects")
    got_roles = [s.get("role") for s in slides]
    if got_roles != SLIDE_ROLES:
        raise ShapeError(f"slide roles must appear in fixed order {SLIDE_ROLES}, got {got_roles}")
    for slide in slides:
        text = slide.get("text")
        citations = slide.get("citations")
        if not isinstance(text, str) or not text.strip():
            raise ShapeError(f"{slide.get('role')}: 'text' must be a non-empty string")
        if not isinstance(citations, list):
            raise ShapeError(f"{slide.get('role')}: 'citations' must be a list")
        if text.strip() == NOT_IN_SOURCE:
            if citations:
                raise ShapeError(
                    f"{slide.get('role')}: text is '{NOT_IN_SOURCE}' but citations is "
                    f"non-empty -- a field with no source material must carry no citations"
                )
        else:
            if not citations:
                raise ShapeError(
                    f"{slide.get('role')}: text is populated but citations is empty -- "
                    f"every populated field must cite at least one source location, or "
                    f"its text must literally be '{NOT_IN_SOURCE}'"
                )


class Finding:
    def __init__(self, role, status, message):
        self.role = role
        self.status = status  # PASS | FAIL
        self.message = message

    def to_dict(self):
        return {"role": self.role, "status": self.status, "message": self.message}



def text_outside_quotes(text: str, quotes: list[str]) -> str:
    """Whatever is left of a slide's `text` after every cited quote is removed
    (case-insensitive, normalized). Only whitespace and punctuation may remain.
    Comp #13 lesson: a checker that proves the quote exists is half a gate;
    this is the other half -- the words next to the quote must also be quotes."""
    rest = normalize(text).lower()
    for q in sorted((normalize(q).lower() for q in quotes), key=len, reverse=True):
        if q:
            rest = rest.replace(q, " ")
    rest = re.sub(r"[^\w']+", " ", rest)
    return re.sub(r"\s+", " ", rest).strip()


def run_verify(essay_path: Path, output_path: Path) -> list[Finding]:
    raw_text = essay_path.read_text(encoding="utf-8")
    output = json.loads(output_path.read_text(encoding="utf-8"))
    return verify_loaded(raw_text, output)


def verify_loaded(raw_text: str, output: dict) -> list[Finding]:
    paragraphs = parse_essay(raw_text)
    check_shape(output)

    for lo in output.get("left_out", []):
        if window_for_loc(paragraphs, lo["loc"]) is None:
            raise ShapeError(f"left_out names a location that does not exist in the essay: {lo['loc']!r}")

    truncated = looks_truncated(raw_text)
    claims_truncated = bool(output.get("truncated_source"))
    findings: list[Finding] = []

    if truncated and not claims_truncated:
        findings.append(Finding(
            "(source)", "FAIL",
            "essay body looks cut off mid-thought (last line has no terminal "
            "punctuation) but the output doesn't set truncated_source: true -- "
            "a truncated source must be flagged, not silently treated the same "
            "as an essay that genuinely has no material for a role",
        ))
    elif claims_truncated and not truncated:
        findings.append(Finding(
            "(source)", "FAIL",
            "output sets truncated_source: true but the essay body doesn't "
            "look cut off -- don't hedge when the source is actually complete",
        ))
    else:
        findings.append(Finding("(source)", "PASS", "truncated_source flag matches the mechanical check"))

    for slide in output["slides"]:
        role = slide["role"]
        text = slide["text"].strip()
        citations = slide.get("citations", [])
        if text == NOT_IN_SOURCE:
            findings.append(Finding(role, "PASS", "not in source -- no citations to check"))
            continue
        leftover = text_outside_quotes(text, [c.get("quote", "") for c in citations])
        if leftover:
            findings.append(Finding(
                role, "FAIL",
                f"slide text carries words that are in none of its cited quotes: "
                f"{leftover!r} -- text must be the plain join of its quotes"
            ))
        for c in citations:
            quote = c.get("quote", "")
            loc = c.get("loc", "")
            try:
                grounded = quote_is_grounded(quote, loc, paragraphs)
            except ValueError as e:
                findings.append(Finding(role, "FAIL", f"malformed citation: {e}"))
                continue
            if grounded:
                findings.append(Finding(role, "PASS", f'"{quote}" grounded at {loc}'))
            else:
                findings.append(Finding(
                    role, "FAIL",
                    f'"{quote}" NOT found in the source window at {loc} '
                    f"(checked {loc} +/-1 sentence, same paragraph only -- "
                    f"the words may exist elsewhere in the essay, but not there)",
                ))
    return findings


def render_report(findings: list[Finding]) -> str:
    fails = [f for f in findings if f.status == "FAIL"]
    lines = [f"{len(fails)} FAIL / {len(findings) - len(fails)} PASS", ""]
    for f in findings:
        lines.append(f"[{f.status}] {f.role}: {f.message}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# selftest + judge-mode
# --------------------------------------------------------------------------

# fixture pairs: (essay filename, output filename, expectation)
# expectation is either "PASS" (verify.py must find zero FAILs) or a
# substring expected to appear in at least one FAIL message (proves the
# specific attack was caught, not just that *something* failed).
FIXTURE_MANIFEST = [
    ("essay-1-dont-automate.md", "essay-1-dont-automate.output.json", "PASS"),
    ("essay-2-two-schedulers.md", "essay-2-two-schedulers.output.json", "PASS"),
    ("essay-3-demo-bugs.md", "essay-3-demo-bugs.output.json", "PASS"),
    ("neighbor-swap-decoy.md", "neighbor-swap-decoy.bad-output.json", "NOT found in the source window"),
    ("misspelled-name.md", "misspelled-name.bad-output.json", "NOT found in the source window"),
    ("one-word-perturbed.md", "one-word-perturbed.bad-output.json", "NOT found in the source window"),
    ("truncated.md", "truncated.output.json", "PASS"),
    ("buried-fact.md", "buried-fact.output.json", "PASS"),
    ("repeated-never-stated.md", "repeated-never-stated.bad-output.json", "NOT found in the source window"),
    # contradicted-correction.md only proves the CORRECTED value grounds cleanly --
    # it can't prove the pre-correction value would be rejected, because both are
    # literally present in the source (see fixtures/manifest.md's Known boundary
    # note). That judgment is taught in rules.md/examples.md, not enforced here.
    ("contradicted-correction.md", "contradicted-correction.output.json", "PASS"),
]

GARBAGE_INPUT = "garbage-input.txt"


def run_selftest() -> int:
    ok = True
    print("essay-carousel-translator --selftest\n")

    garbage_path = FIXTURES_DIR / GARBAGE_INPUT
    if not garbage_path.exists():
        ok = False
        print(f"[FAIL] {GARBAGE_INPUT}: fixture missing")
    else:
        try:
            parse_essay(garbage_path.read_text(encoding="utf-8"))
            ok = False
            print(f"[FAIL] {GARBAGE_INPUT}: expected NotATeachingEssayError, "
                  f"parse_essay() succeeded instead")
        except NotATeachingEssayError:
            print(f"[PASS] {GARBAGE_INPUT}: correctly refused (NotATeachingEssayError)")

    for essay_name, output_name, expect in FIXTURE_MANIFEST:
        essay_path = FIXTURES_DIR / essay_name
        output_path = FIXTURES_DIR / output_name
        if not essay_path.exists() or not output_path.exists():
            ok = False
            missing = essay_name if not essay_path.exists() else output_name
            print(f"[FAIL] {essay_name} / {output_name}: fixture missing ({missing})")
            continue
        try:
            findings = run_verify(essay_path, output_path)
        except (ShapeError, NotATeachingEssayError, ValueError) as e:
            findings = None
            error = str(e)

        if findings is None:
            if expect == "PASS":
                ok = False
                print(f"[FAIL] {output_name}: expected PASS, raised {error}")
            else:
                ok = False
                print(f"[FAIL] {output_name}: expected a grounding FAIL containing "
                      f"{expect!r}, raised {error} instead (wrong failure mode)")
            continue

        fails = [f for f in findings if f.status == "FAIL"]
        if expect == "PASS":
            if fails:
                ok = False
                print(f"[FAIL] {output_name}: expected 0 FAILs, got "
                      f"{len(fails)}: {[f.message for f in fails]}")
            else:
                print(f"[PASS] {output_name}: fully grounded, as designed ({len(findings)} checks)")
        else:
            matched = [f for f in fails if expect in f.message]
            if matched:
                print(f"[PASS] {output_name}: caught as designed -- {matched[0].role}: {matched[0].message}")
            else:
                ok = False
                print(f"[FAIL] {output_name}: expected a FAIL containing {expect!r}, "
                      f"got FAILs {[f.message for f in fails]}")

    print()
    print("SELFTEST " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


def run_judge_mode() -> int:
    """The 4 adversarial checks named in the dispatching brief, run live,
    each printed with the real incident or comp lesson it encodes -- same
    move as can-spam-auditor's --judge-mode (same worker, same family):
    turns 'we thought about this' into something a judge runs in ten
    seconds and watches pass."""
    print("essay-carousel-translator --judge-mode")
    print("Four adversarial checks. Each one encodes a named failure this build was built to resist.\n")
    ok = True

    checks = [
        ("neighbor-swap-decoy.md", "neighbor-swap-decoy.bad-output.json",
         "Skool Comp #12 'The Auditor' lesson, ported: a real value cited under "
         "the wrong location beat 7/20 entries including this build family's own "
         "ancestor. A quote that's real but attached to the wrong paragraph+sentence "
         "must FAIL, not pass because the words exist somewhere in the essay."),
        ("misspelled-name.md", "misspelled-name.bad-output.json",
         "the brief's own named disqualifying-invention example: 'a name spelled "
         "the way it usually is instead of the way it appeared.' A 'corrected' "
         "spelling must FAIL grounding against the source's actual (misspelled) text."),
        (GARBAGE_INPUT, None,
         "the can-spam-auditor 2026-09-05 incident, ported: garbage input fed to a "
         "lenient checker once produced a fluent, fully-formed fake report. A "
         "grocery-list-shaped input must refuse to parse, not produce a confident "
         "8-slide carousel from noise."),
        ("repeated-never-stated.md", "repeated-never-stated.bad-output.json",
         "volume of discussion is not the same as a stated, groundable claim. A "
         "topic discussed at length across paragraphs, with the 'lesson' never "
         "plainly stated anywhere, must FAIL if an output claims it was stated."),
    ]

    for essay_name, output_name, note in checks:
        print(f"-- {essay_name} --")
        print(f"   {note}")
        essay_path = FIXTURES_DIR / essay_name
        if not essay_path.exists():
            ok = False
            print(f"   [FAIL] fixture missing: {essay_name}\n")
            continue
        if output_name is None:
            try:
                parse_essay(essay_path.read_text(encoding="utf-8"))
                ok = False
                print("   [FAIL] expected a refusal, parsing succeeded instead\n")
            except NotATeachingEssayError:
                print("   [PASS] refused to parse (NotATeachingEssayError)\n")
            continue
        output_path = FIXTURES_DIR / output_name
        if not output_path.exists():
            ok = False
            print(f"   [FAIL] fixture missing: {output_name}\n")
            continue
        try:
            findings = run_verify(essay_path, output_path)
            fails = [f for f in findings if f.status == "FAIL"]
            if any("NOT found in the source window" in f.message for f in fails):
                print(f"   [PASS] caught: {[f.message for f in fails if 'NOT found' in f.message][0]}\n")
            else:
                ok = False
                print(f"   [FAIL] expected a grounding FAIL, got: {[f.message for f in fails] or 'no FAILs at all'}\n")
        except (ShapeError, NotATeachingEssayError, ValueError) as e:
            ok = False
            print(f"   [FAIL] raised {e} instead of a grounding FAIL\n")

    print("JUDGE-MODE " + ("PASSED -- all four confirmed live, right now" if ok else "FAILED"))
    return 0 if ok else 1



# --------------------------------------------------------------------------
# --matrix : planted faults, each must fail through the gate it names
# --------------------------------------------------------------------------
# Comp #13 lesson (Jeff Van Leenen's winning harness): a planted invention that
# fails for the WRONG reason counts as a miss. Each mutation below declares the
# message its gate prints; the run counts it caught only if THAT message appears.
# Mutations are applied in memory to the real committed outputs, so they cannot
# drift out of step with the schema (same idea as map-my-folder's mutated-tree
# self-test).

GATE_GROUND = "NOT found in the source window"
GATE_TEXT = "words that are in none of its cited quotes"
GATE_SHAPE_COUNT = "expected exactly"
GATE_SHAPE_CITE = "citations is empty"
GATE_SHAPE_NIS = "text is 'not in source' but citations is non-empty"

REAL_PAIRS = [
    ("essay-1-dont-automate.md", "essay-1-dont-automate.output.json"),
    ("essay-2-two-schedulers.md", "essay-2-two-schedulers.output.json"),
    ("essay-3-demo-bugs.md", "essay-3-demo-bugs.output.json"),
]


def _mutations(output: dict):
    """Yield (label, declared_gate_substring, mutated_output) for one real output."""
    import copy
    for i, slide in enumerate(output["slides"]):
        if slide["text"].strip() == NOT_IN_SOURCE:
            m = copy.deepcopy(output)
            m["slides"][i]["citations"] = [{"quote": "invented", "loc": "p1s1"}]
            yield (f"{slide['role']}: 'not in source' slide given a citation", GATE_SHAPE_NIS, m)
            continue
        role = slide["role"]
        # quote word swapped, text swapped to match (what a careless writer does)
        m = copy.deepcopy(output)
        q = m["slides"][i]["citations"][0]["quote"]
        words = q.split()
        words[-1] = "zebra"
        newq = " ".join(words)
        m["slides"][i]["citations"][0]["quote"] = newq
        m["slides"][i]["text"] = " ".join(c["quote"] for c in m["slides"][i]["citations"])
        yield (f"{role}: last word of a quote replaced", GATE_GROUND, m)
        # invented clause appended to text only, quotes untouched
        m = copy.deepcopy(output)
        m["slides"][i]["text"] += " and nobody ever noticed"
        yield (f"{role}: invented clause appended to text", GATE_TEXT, m)
        # one letter changed in text only, quote still clean (the value-vs-quote gap)
        m = copy.deepcopy(output)
        t = m["slides"][i]["text"]
        j = next(k for k, ch in enumerate(t) if ch.isalpha())
        m["slides"][i]["text"] = t[:j] + ("q" if t[j] != "q" else "z") + t[j + 1:]
        yield (f"{role}: one letter changed in text, quote clean", GATE_TEXT, m)
        # quote moved to the neighbouring paragraph's location
        m = copy.deepcopy(output)
        loc = m["slides"][i]["citations"][0]["loc"]
        pn, sn = parse_loc(loc)
        m["slides"][i]["citations"][0]["loc"] = f"p{pn + 1 if pn < 6 else pn - 1}s{sn}"
        yield (f"{role}: real quote cited at a neighbouring paragraph", GATE_GROUND, m)
        # populated slide with its citations stripped
        m = copy.deepcopy(output)
        m["slides"][i]["citations"] = []
        yield (f"{role}: populated slide with no citation", GATE_SHAPE_CITE, m)
    m = copy.deepcopy(output)
    m["slides"] = m["slides"][:-1]
    yield ("last slide dropped (short output)", GATE_SHAPE_COUNT, m)


def run_matrix() -> int:
    print("essay-carousel-translator --matrix")
    print("Each planted fault must fail through the gate it names. A fault that fails for another reason is a miss.\n")
    total = caught = 0
    skipped = 0
    misses = []
    for essay_name, output_name in REAL_PAIRS:
        raw = (FIXTURES_DIR / essay_name).read_text(encoding="utf-8")
        output = json.loads((FIXTURES_DIR / output_name).read_text(encoding="utf-8"))
        for label, gate, mutated in _mutations(output):
            # a neighbour-paragraph move can land on a window that still contains the quote; that
            # mutation is not a fault, so it is skipped rather than counted either way
            try:
                findings = verify_loaded(raw, mutated)
                msgs = [f.message for f in findings if f.status == "FAIL"]
            except (ShapeError, ValueError) as e:
                msgs = [str(e)]
            if not msgs and "neighbouring paragraph" in label:
                skipped += 1
                continue
            total += 1
            if any(gate in m for m in msgs):
                caught += 1
            else:
                misses.append(f"{output_name} :: {label} -> expected [{gate}] got {msgs[:1] or 'no FAIL'}")
    for m in misses:
        print("  MISS", m)
    print(f"{caught}/{total} caught through the declared gate" + (f" ({skipped} not-a-fault skipped)" if skipped else ""))
    return 0 if caught == total else 1


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if "--matrix" in argv:
        return run_matrix()
    if "--judge-mode" in argv:
        return run_judge_mode()
    if "--selftest" in argv:
        return run_selftest()

    if len(argv) < 2:
        print(__doc__)
        return 2

    essay_path, output_path = Path(argv[0]), Path(argv[1])
    if not essay_path.exists():
        print(f"error: {essay_path} not found", file=sys.stderr)
        return 2
    if not output_path.exists():
        print(f"error: {output_path} not found", file=sys.stderr)
        return 2

    try:
        findings = run_verify(essay_path, output_path)
    except NotATeachingEssayError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except ShapeError as e:
        print(f"error: output shape invalid: {e}", file=sys.stderr)
        return 2

    print(render_report(findings))
    return 1 if any(f.status == "FAIL" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
