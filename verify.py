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
_ABBREVIATION_END = re.compile(
    r"(?:^|[\s(\"'])(?:Dr|Mr|Mrs|Ms|Prof|Sr|Jr|St|Mt|vs|etc|Inc|Ltd|Co|Corp|Gen|Gov|Sen|Rep|Rev|Hon|Fig|No|approx|e\.g|i\.e|U\.S|U\.K)\.[\"')]?$"
)
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
        if _ABBREVIATION_END.search(text[:end]):
            continue  # "Dr. Vance", "vs. the", "e.g. a": not a sentence end (Comp #13 re-gate: a stub cut at "Dr." dropped a retraction)
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

_LOC_RE = re.compile(r"^p([0-9]+)s([0-9]+)$", re.ASCII)


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


def resolve_quote(quote: str, loc: str, paragraphs: list[list[str]]):
    """The real (paragraph, sentence) a quote is, found by matching it against the whole sentences of the cited
    window (cited sentence +/-1, same paragraph). A quote must BE a sentence, not a piece of one: Comp #13
    re-gate showed every clause-level cut can change meaning ('Critics argue: automation is free, but it never
    is' -> 'automation is free'; a dropped 'No,'; '0.5' -> '0.'). Returns (p, s), 1-indexed, or None."""
    p_idx, s_idx = parse_loc(loc)
    if p_idx < 1 or p_idx > len(paragraphs):
        return None
    sentences = paragraphs[p_idx - 1]
    nq = normalize(quote)
    for k in range(max(0, s_idx - 2), min(len(sentences), s_idx + 1)):
        if normalize(sentences[k]) == nq:
            return (p_idx, k + 1)
    return None


def quote_ground_status(quote: str, loc: str, paragraphs: list[list[str]]) -> str:
    """'ok' (a whole sentence of the window), 'cut' (inside the window but only part of a sentence) or 'absent'."""
    window = window_for_loc(paragraphs, loc)
    if window is None:
        return "absent"
    nq = normalize(quote)
    if not nq or nq not in normalize(window):
        return "absent"
    return "ok" if resolve_quote(quote, loc, paragraphs) else "cut"


def quote_is_grounded(quote: str, loc: str, paragraphs: list[list[str]]) -> bool:
    return quote_ground_status(quote, loc, paragraphs) == "ok"


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
    extra = set(output) - {"source", "truncated_source", "left_out", "slides"}
    if extra:
        raise ShapeError(f"unexpected top-level key(s) {sorted(extra)}: the contract has source, truncated_source, left_out, slides")
    for slide in output["slides"]:
        bad = set(slide) - {"role", "text", "citations"}
        if bad:
            raise ShapeError(f"{slide.get('role')}: unexpected key(s) {sorted(bad)} -- only role, text, citations are allowed")
        for c in slide.get("citations", []) if isinstance(slide.get("citations"), list) else []:
            if not isinstance(c, dict) or set(c) - {"quote", "loc"}:
                raise ShapeError(f"{slide.get('role')}: a citation may carry only quote and loc")
    left_out = output.get("left_out", [])
    if not isinstance(left_out, list) or any(
        not isinstance(x, dict) or not {"loc", "role", "why"} <= set(x) for x in left_out
    ):
        raise ShapeError("left_out must be a list of {loc, role, why} objects")
    for x in left_out:
        if x["role"] not in SLIDE_ROLES or not isinstance(x["why"], str) or len(x["why"]) > 240 or set(x) - {"loc", "role", "why"}:
            raise ShapeError(f"left_out role must be one of the 8 roles and why a one-line string (<=240 chars): {x!r}")
    got_roles = [s.get("role") for s in slides]
    if got_roles != SLIDE_ROLES:
        raise ShapeError(f"slide roles must appear in fixed order {SLIDE_ROLES}, got {got_roles}")
    if slides[0].get("text", "").strip() == NOT_IN_SOURCE:
        raise ShapeError("Hook is 'not in source': every essay opens somewhere, so Hook is always populated")
    if slides[-1].get("text", "").strip() == NOT_IN_SOURCE and not output.get("truncated_source"):
        raise ShapeError("Close is 'not in source' on an essay not marked truncated: every finished essay ends somewhere")
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



MIN_QUOTE_WORDS = 3


def _plain(s: str) -> str:
    """Case, punctuation and whitespace folded away; used to compare text with the in-order join of its quotes."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w']+", " ", normalize(s).lower())).strip()


def _plain_exact(s: str) -> str:
    """Whitespace-folded but case- and punctuation-preserving form, for comparing text with the exact join."""
    return re.sub(r"\s+", " ", normalize(s)).strip()


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

    cited_all: set = set()
    for slide in output["slides"]:
        role = slide["role"]
        text = slide["text"].strip()
        citations = slide.get("citations", [])
        if text == NOT_IN_SOURCE:
            findings.append(Finding(role, "PASS", "not in source -- no citations to check"))
            continue
        quotes = [c.get("quote", "") for c in citations]
        if _plain_exact(text) != _plain_exact(" ".join(quotes)) and not text_outside_quotes(text, quotes) and _plain(text) == _plain(" ".join(quotes)):
            findings.append(Finding(
                role, "FAIL",
                "slide text differs from the exact join of its quotes in case or punctuation -- text must equal the join of its quotes exactly"
            ))
        short = [q for q in quotes if len(normalize(q).split()) < MIN_QUOTE_WORDS]
        if short:
            findings.append(Finding(
                role, "FAIL",
                f"quote shorter than {MIN_QUOTE_WORDS} words ({short[0]!r}) -- fragments this small can be "
                f"stitched into a sentence the essay never wrote; cite the whole sentence"
            ))
        leftover = text_outside_quotes(text, quotes)
        if leftover:
            findings.append(Finding(
                role, "FAIL",
                f"slide text carries words that are in none of its cited quotes: "
                f"{leftover!r} -- text must be the plain join of its quotes"
            ))
        elif _plain(text) != _plain(" ".join(quotes)):
            findings.append(Finding(
                role, "FAIL",
                "slide text re-orders or repeats its cited quotes -- text must be the in-order join of its quotes"
            ))
        real = []
        for c in citations:
            try:
                real.append(resolve_quote(c.get("quote", ""), c.get("loc", ""), paragraphs))
            except ValueError:
                real.append(None)
        resolved = [r for r in real if r is not None]
        cited_all.update(resolved)
        if len(resolved) != len(set(resolved)):
            findings.append(Finding(role, "FAIL", "a quote appears twice in this slide's citations -- cite each passage once"))
        elif len(resolved) == len(real) and len(real) > 1:
            if real != sorted(real):
                findings.append(Finding(role, "FAIL", "citations are not in source order -- cite in the order the essay says them"))
            if max(r[0] for r in real) - min(r[0] for r in real) > 1:
                findings.append(Finding(role, "FAIL", "citations span more than two neighbouring paragraphs -- a slide cites one passage, not fragments from across the essay"))
        for c in citations:
            quote = c.get("quote", "")
            loc = c.get("loc", "")
            try:
                status = quote_ground_status(quote, loc, paragraphs)
            except ValueError as e:
                findings.append(Finding(role, "FAIL", f"malformed citation: {e}"))
                continue
            grounded = status == "ok"
            if status == "cut":
                findings.append(Finding(
                    role, "FAIL",
                    f'"{quote}" is in the source window at {loc} but is only part of a sentence '
                    f"-- cut at a bad edge: a quote must be a whole sentence"
                ))
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
    for lo in output.get("left_out", []):
        if parse_loc(lo["loc"]) in cited_all:
            findings.append(Finding("(left_out)", "FAIL", f"left_out lists {lo['loc']}, a sentence that is cited on a slide -- left_out is for sentences on no slide"))
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

    stub = split_sentences("The review concluded the drug is safe, according to Dr. Vance, who later retracted it. Nobody noticed.")
    if len(stub) == 2 and stub[0].endswith("retracted it."):
        print("[PASS] splitter keeps 'Dr. Vance' inside its sentence (no citable stub that drops the retraction)")
    else:
        ok = False
        print(f"[FAIL] splitter broke a sentence at an abbreviation: {stub}")

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
GATE_ORDER = "re-orders or repeats its cited quotes"
GATE_EXACT = "differs from the exact join of its quotes"
GATE_CUT = "only part of a sentence"
GATE_LODUP = "left_out lists"
GATE_SRCORDER = "not in source order"
GATE_SPAN = "span more than two neighbouring paragraphs"
GATE_KEYS = "unexpected"
GATE_DUP = "appears twice"
GATE_REQ = "always populated"
GATE_LEFTOUT = "left_out role must be one of the 8 roles"
GATE_MINQUOTE = "quote shorter than"
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
        # quotes reordered in text (needs two or more quotes)
        if len(slide["citations"]) >= 2:
            m = copy.deepcopy(output)
            m["slides"][i]["text"] = " ".join(reversed([c["quote"] for c in m["slides"][i]["citations"]]))
            yield (f"{role}: cited quotes reordered in text", GATE_ORDER, m)
        # a quote cut down to one word, text kept in step (stitching fragments)
        m = copy.deepcopy(output)
        m["slides"][i]["citations"][0]["quote"] = m["slides"][i]["citations"][0]["quote"].split()[0]
        m["slides"][i]["text"] = " ".join(c["quote"] for c in m["slides"][i]["citations"])
        yield (f"{role}: a quote cut to one word", GATE_MINQUOTE, m)
        # exact-join gates: case, terminal punctuation, injected symbols
        m = copy.deepcopy(output); m["slides"][i]["text"] = m["slides"][i]["text"].upper()
        yield (f"{role}: text set to ALL CAPS", GATE_EXACT, m)
        m = copy.deepcopy(output); m["slides"][i]["text"] += " !!!"
        yield (f"{role}: symbols appended to text", GATE_EXACT, m)
        m = copy.deepcopy(output); m["slides"][i]["text"] = "\U0001F6AB " + m["slides"][i]["text"]
        yield (f"{role}: symbol injected before text", GATE_EXACT, m)
        # quote cut at a bad edge: first word dropped (mid-clause), or first letter dropped (mid-word)
        qs = m0 = copy.deepcopy(output)
        q0 = qs["slides"][i]["citations"][0]["quote"]
        if len(q0.split()) >= 5:
            qs["slides"][i]["citations"][0]["quote"] = " ".join(q0.split()[1:])
            qs["slides"][i]["text"] = " ".join(c["quote"] for c in qs["slides"][i]["citations"])
            yield (f"{role}: first word of a quote dropped", GATE_CUT, qs)
        m = copy.deepcopy(output)
        qq = m["slides"][i]["citations"][0]["quote"]
        m["slides"][i]["citations"][0]["quote"] = qq[1:]
        m["slides"][i]["text"] = " ".join(c["quote"] for c in m["slides"][i]["citations"])
        yield (f"{role}: first letter of a quote dropped", GATE_CUT, m)
        # citations listed against source order
        if len(slide["citations"]) >= 2:
            m = copy.deepcopy(output)
            m["slides"][i]["citations"] = list(reversed(m["slides"][i]["citations"]))
            m["slides"][i]["text"] = " ".join(c["quote"] for c in m["slides"][i]["citations"])
            yield (f"{role}: citations listed against source order", GATE_SRCORDER, m)
        # the same passage cited twice
        m = copy.deepcopy(output)
        m["slides"][i]["citations"].append(copy.deepcopy(m["slides"][i]["citations"][0]))
        m["slides"][i]["text"] = " ".join(c["quote"] for c in m["slides"][i]["citations"])
        yield (f"{role}: first passage cited twice", GATE_DUP, m)
        # claimed locs kept ascending while the real sentence order is reversed (adjacent sentences)
        cs = slide["citations"]
        if len(cs) >= 2:
            (p1, s1), (p2, s2) = parse_loc(cs[0]["loc"]), parse_loc(cs[1]["loc"])
            if p1 == p2 and s2 - s1 == 1:
                m = copy.deepcopy(output)
                a, b = m["slides"][i]["citations"][0], m["slides"][i]["citations"][1]
                m["slides"][i]["citations"] = [{"quote": b["quote"], "loc": a["loc"]}, {"quote": a["quote"], "loc": b["loc"]}]
                m["slides"][i]["text"] = " ".join(c["quote"] for c in m["slides"][i]["citations"])
                yield (f"{role}: real order reversed under ascending claimed locs", GATE_SRCORDER, m)
        # left_out naming a sentence that is cited
        m = copy.deepcopy(output)
        m["left_out"] = [{"loc": slide["citations"][0]["loc"], "role": role, "why": "listed although cited"}]
        yield (f"{role}: left_out lists a cited sentence", GATE_LODUP, m)
        # extra key on the slide
        m = copy.deepcopy(output); m["slides"][i]["caption"] = "Revenue up 400%"
        yield (f"{role}: extra key on the slide", GATE_KEYS, m)
        # populated slide with its citations stripped
        m = copy.deepcopy(output)
        m["slides"][i]["citations"] = []
        yield (f"{role}: populated slide with no citation", GATE_SHAPE_CITE, m)
    m = copy.deepcopy(output)
    m["slides"] = m["slides"][:-1]
    yield ("last slide dropped (short output)", GATE_SHAPE_COUNT, m)
    m = copy.deepcopy(output); m["summary"] = "This post proves AI replaces teachers 100%"
    yield ("extra top-level key", GATE_KEYS, m)
    m = copy.deepcopy(output); m["slides"][0].update({"text": NOT_IN_SOURCE, "citations": []})
    yield ("Hook set to 'not in source'", GATE_REQ, m)
    if not output.get("truncated_source"):
        m = copy.deepcopy(output); m["slides"][-1].update({"text": NOT_IN_SOURCE, "citations": []})
        yield ("Close set to 'not in source' on a complete essay", "every finished essay ends somewhere", m)
    m = copy.deepcopy(output); m["left_out"] = [{"loc": "p1s1", "role": "Zzz", "why": "invented role"}]
    yield ("left_out entry with an invented role", GATE_LEFTOUT, m)
    # far stitching: borrow a quote from a slide two or more paragraphs away
    pop = [sl for sl in output["slides"] if sl["text"].strip() != NOT_IN_SOURCE]
    for a in pop:
        far = [b for b in pop if b is not a and abs(parse_loc(b["citations"][0]["loc"])[0] - parse_loc(a["citations"][-1]["loc"])[0]) >= 2
               and parse_loc(b["citations"][0]["loc"]) > parse_loc(a["citations"][-1]["loc"])]
        if far:
            m = copy.deepcopy(output)
            sl = next(x for x in m["slides"] if x["role"] == a["role"])
            sl["citations"].append(copy.deepcopy(far[0]["citations"][0]))
            sl["text"] = " ".join(c["quote"] for c in sl["citations"])
            yield (f"{a['role']}: quote from a distant paragraph stitched on", GATE_SPAN, m)
            break


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
