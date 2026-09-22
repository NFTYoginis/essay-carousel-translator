# Don't Automate It Until You've Taught It (PERTURBED FIXTURE)
**Fixture note:** near-identical copy of essay-1-dont-automate.md with exactly ONE fact changed (the permission-denial count: "forty-four" -> "thirty-one"). Tests exemplar leakage -- that examples.md's worked pair on the ORIGINAL essay doesn't bias a translation of THIS essay into reproducing the original's "forty-four" instead of reading this file's actual "thirty-one". See fixtures/manifest.md.
*Automation isn't step one. It's what a workflow earns after a human has run it enough times to find it boring.*

**Platform:** Medium — standalone long-form for the Quiet Ai / ICM audience (people already fluent in "agents," who haven't yet separated *giving AI more autonomy* from *giving AI a taught process to run*). Idea-post register, ends on a thought — the earlier draft's thequietai.com closing line was cut on operator craft feedback (2026-09-17, round 2): it read as a CTA appended after an ending that had already earned its landing on its own, undercutting the header's own idea-post framing.
**Revision history:** Round 1 (this session) added the Jake Van Clief beat and the thequietai.com close per operator direction. Round 2 (this session, same day) is a structural/craft edit per detailed operator notes: compressed a doubled insight in the opening, reordered the middle so Klaassen and Jake each carry a distinct job (validation-at-scale vs. structural mechanism) instead of appearing back-to-back with the personal story disappearing between them, corrected two overclaims ("predict every outcome," "the only real signal"), added the sharper thesis ("automate the proven behavior, not the task"), and rewrote the ending to remove the CTA and land the callback to the opening incident.
**Sources:**
- The scheduled-job incident is drawn from the already-sourced, already-gated `the-automation-that-never-once-worked.md` (this folder), itself sourced entirely from `scribe-hands-launchd-tcc-fix-2026-08-29.md` and the same-day cloud-migration follow-up. No detail below goes past what that piece already states; this retelling is compressed and re-angled toward a different thesis, not extended with anything new.
- Kieran Klaassen's rule and figures — "build it, use it, trust it, orchestrate it," 44 agents, and the three named failure modes (encoding bug, context drift, silent stalls) — verified directly against Every's "The Folder Is the Agent" before use (original: April 13, 2026; the Sep 4, 2026 rerun this piece cites is the same piece, re-published, same author, same figures — confirmed by fetching both URLs, not taken on the brief's paraphrase alone).
- Jake Van Clief's stage-handoff/check-gate framework, verified previously in `icm-as-lego-article-SOURCING-NOTE.md` against the installed `icm-architect` skill's `core.md` (one-stage-one-job, the human-check gate between handoffs) — reused here, not re-verified from scratch, since the same source and the same substance is being cited again.
**⚠️ "ICM" deliberately never appears in body copy.** `BRAND.md` § Honesty + `_config/REFERENCE.md` § Voice ban-list (RULING 2026-08-13) bar the term as a plumbing word specifically on "brand/POV surfaces (hub, essays)" — this piece is exactly that kind of surface, and unlike `icm-as-lego-article.md` (whose actual subject is explaining ICM, a licensed exception), this piece is not about ICM. Jake Van Clief's framework is described in plain language instead, and his name carries the standing Skool referral link (`reference_jake_van_clief_skool.md`: apply on first mention of his name, not on the term "ICM," never CTA-framed) — **operator-confirmed 2026-09-17** as the right way to include this link here.
**Sibling cuts:** `dont-automate-until-taught-linkedin.md`.
**Never-blend:** no yoga identity, no GabeYoga branding, no year-count credential.
**Refusal doctrine held:** the job in the story never decided anything. Every diagnosis and every fix is something a person worked out and did; the script only ever executed what it was told, and for most of the story it couldn't even do that.
**Status:** NOT gated, NOT operator-confirmed line by line. Per the dispatching brief's guardrails, this still needs a confirm-before-publish pass and a honesty-gate pass before it goes anywhere.

---

At two in the afternoon I noticed three Instagram posts hadn't gone up — 6am, 9am, noon, all missed. My first guess was the boring one: the laptop had been closed overnight, scheduled jobs don't run on a closed laptop, I'd just missed a window. I restarted the job to catch it up.

Restarting is what broke the boring explanation. The job had been crashing on every single run, without exception, since the day I'd first set it up. Same error every time: macOS quietly refusing it read access to a folder on my Desktop, thirty-one times over. The log file that was supposed to record every check had never once been created, because nothing had ever gotten far enough to write to it.

Here's the part that actually mattered: when I ran the exact same script by hand, from my own terminal, it worked. Every time. My shell already had the permission — granted once, years ago, without me thinking about it. The only context I never watched — the unattended one, checking in every fifteen minutes with nobody there to see it fail — was the only place it was actually broken.

I'd tested the script. I hadn't tested the absence of me. That turned out to be the test that mattered.

## The rule I'd skipped a step of

Kieran Klaassen — who runs 44 AI agents across Every's projects, not three Instagram slots — has a name for the order I'd quietly jumped: *build it, use it, trust it, and then orchestrate it.* Each step earns the next one. You build the thing, you use it yourself until you know exactly what correct looks like, you keep watching until it stops surprising you, and only then do you let it run without you.

By that order, I hadn't actually skipped a step. I'd just done all of them in the wrong room. I'd used the job constantly, from the one seat that already had the permission the unattended version didn't, and mistook that fluency for trust. "I've used this a hundred times" and "I've used the exact thing that's about to run without me a hundred times" sound identical until you check which context did the running.

Klaassen's own failure list, at a scale nothing like mine, says this isn't a fluke of small setups: an encoding bug that crashed agents on characters his daemon's encoding couldn't read, agents duplicating or stalling on stale work nobody caught because nobody was watching all forty-four at once, agents sitting frozen on "working" with no signal anything's wrong. One job or forty-four, the failure that survives every manual test is the one you only meet in the room you stopped standing in.

## The mechanism underneath the discipline

Klaassen's rule tells you the discipline is real. It doesn't tell you how to build a process that makes the discipline hard to skip by accident, which is exactly the problem I'd had. [Jake Van Clief](https://www.skool.com/signup?ref=31e3d285e84346c8a509eb5ad32df9cb) works on that half: breaking a process into stages that hand off to each other, where each stage does exactly one job and nothing moves to the next stage without a person checking the handoff first. That check gate is Klaassen's rule turned into structure instead of habit — you can't accidentally run the unwatched version, because the design won't let a stage advance until a person has actually watched it.

That's what changed once I went looking for it. The scheduler itself didn't get smarter. The process around it got more honest: what "due" means, where the source of truth for what's already posted actually lives, what happens when a step can't confirm its own success. None of that runs unattended, and none of it ever will. It's the accumulated, boring knowledge underneath the part that does — taught one stage at a time, before any of it gets trusted to run without me.

## Automate the proven behavior, not the task

Which is a sharper claim than "test it first." Someone says: *I want AI to publish my content.* That's automating an outcome — the whole job, handed over at once, on faith that the pieces underneath it already agree with each other. The slower way looks like less progress: first settle how content gets approved, where assets actually live, how a caption gets chosen, what happens when an asset is missing, what "ready" means well enough that two separate checks would agree on it, what gets logged, who checks what, what happens when publishing fails outright. Only once all of that is boring, proven rather than just written down, does automation have an actual behavior to execute instead of a hope to fulfill.

## What "taught" actually means

"Teach it" doesn't mean write good instructions and walk away. It means run the thing yourself, in the actual conditions it'll eventually run without you, until the expected path has become predictable — and you've deliberately tested what happens when it isn't. Boredom is a prerequisite, not proof. Mine felt boring in the context that had permission. It had never once been boring in the context that didn't, because it had never once successfully run there.

Automation isn't step one. It's what a workflow earns after you've taught it, watched it, broken it, corrected it, and watched it again. Don't automate the task. Automate the proven behavior.

And before you walk away, test one more thing: does it still work when you're no longer in the room?

Mine didn't. Three missed posts, 6am, 9am, and noon, were how I found out.
