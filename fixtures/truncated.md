# I Found Bugs in My Own Demo. I Posted It Anyway. — Skool cut (TRUNCATED FIXTURE)

**Fixture note:** the real essay `essay-3-demo-bugs.md`, deliberately cut off mid-paragraph after the
Reveal section, before Mechanism or Close exist. Tests that verify.py's `truncated_source` flag catches a
document cut off mid-thought, distinct from an essay that genuinely just has no material for a role. See
`fixtures/manifest.md`.

---

Something happened during a live demo of a tool I built, and I want to walk through the actual mechanics of
what I did with the recording afterward, because I think the process is more useful than the story.

I asked the tool for a five-second video. Nothing came back. Not slow — nothing. Then I found a second
problem sitting underneath the first one: the system hadn't logged what had gone wrong, so there wasn't even
a record to point at afterward. A third, smaller issue — a slow step further upstream — resolved on its own
while I was still recording.

Here's the part worth talking about: what to do with that footage.

I had it. Full recording, failure and all. And there's a real, tempting, three-step move available to
basically anyone in this situation:

1. Cut the dead air where nothing happened.
2. Reframe the intro so the "ask" and the eventual working result sit closer together.
3. Post it as a clean walkthrough. Nobody watching would ever know anything went sideways.

I want to be honest that I considered it. It's not a dramatic temptation — it's a boring, practical one. The
edited version is simply a better-looking piece of content. It holds attention better. It makes the tool look
more finished than it is.

I didn't do it. Here's the actual reasoning, not the inspirational version of the reasoning:

**A working demo proves the tool can work once, under conditions you controlled, with every rough edge
removed before anyone saw it.** That's a real thing to show people, but it's a weaker proof than it looks
like, because you as the viewer have no way to tell how much got trimmed.

**A broken demo, left broken, proves something you can't fake:** what the failure actually looks like, and
what the person showing it to you does next. That second part is the whole thing. Anyone can have a bug.
What you can't manufacture after the fact is an honest reaction to one, on camera, in real time.

So mechanically, what I did was: nothing. I didn't cut the silence. I didn't re-order anything to make the
timing look tighter than it was. I posted the take with the failure in it, in the order it happened, and
noted plainly which parts were still
