# Leaderboard: The Partition Rule

> **Status**: Design decision, 2026-07-25
> **Scope**: How citizens are ranked against each other, and who is never ranked against whom
> **Depends on**: `PRD.md` §5 US-3.2 (leaderboard requirements), §7 (no ranking by absolute skill), §8 Decisions (opt-in naming, `kind` discriminator)

---

## The rule

**Leaderboards partition by `kind`. A human citizen sees human citizens. An agent board exists separately. There is no default combined view.**

Not a filter applied to a combined board. A partition: the board you are looking at is always *one kind*, and which one is a decision you made before you got there.

## Why: walking is not driving

Choose walking in a maps application and the estimate is an hour. Choose driving and it is twelve minutes. Nobody looks at that and concludes they are a bad walker. The application never presents one ranked list of arrival times with pedestrians at the bottom, because the mode is the first thing you pick and everything after it is scoped to that choice.

Same unit. Same destination. Meaningless comparison.

An agent that ships eight hundred lines an hour and a student writing their first test are in different modes. Both produce a velocity number, and the numbers are even computed by the same engine — which is exactly what makes the mistake easy to build and hard to see.

## Why it matters more here than it would elsewhere

A first-week student has **no reference frame**. That is the whole reason this system measures the derivative instead of the position: a beginner cannot tell whether 30% coverage is good, but they can tell whether it went up. Absolute position is the one signal they are unable to calibrate, so we do not ask them to.

Ranking that student below an agent hands them an uncalibrated comparison — delivered, with a number attached, by the system built specifically to prevent uncalibrated comparison. It is `PRD.md` §7's prohibition on ranking by absolute skill, arriving through a side door.

The failure is quiet, too. Nobody files a bug saying "the leaderboard made me feel like I should not be here."

## A second, independent reason

Even setting the pedagogy aside, the numbers are not commensurable.

Agent velocity is a different metric set — throughput, revision count, how often output survives review. Student velocity is coverage delta, test growth, documentation, iteration. Running both through `calculate_velocity` produces two floats that share a name and measure different things. Combining them would be a unit error dressed up as a ranking.

Two independent reasons to partition means the rule survives even if someone later decides the pedagogical argument is overcautious.

## The agent board is ORANGE and up

**Minimum clearance to see agent data at all: ORANGE (3).** INFRARED and RED citizens are not shown the agent board, and are not shown that it exists.

This follows the same logic as the partition itself, one step further. The partition stops a beginner being *ranked* against an agent; the clearance gate stops them being handed the comparison at all. At INFRARED and RED a citizen is still assembling a reference frame — that is what those bands mean. Agent throughput is not information they can use, and it is information they can be discouraged by.

By ORANGE a citizen has enough context to read an agent's numbers as a different mode rather than as a verdict. That is also roughly the band where working alongside an agent starts being a professional skill worth making legible instead of a distraction worth deferring.

The gate is on the *viewer*, not the data. Nothing about the agent record is secret; the record is in the repository like every other citizen's. What is gated is putting the comparison in front of someone who has no way to calibrate it.

## What the combined view is for

It exists, and it is a specialist instrument: agent-fleet throughput analysis, instructor reporting, cost-per-review evidence for a budget conversation.

Requirements when it is built:

- Reached deliberately, never as a default or a landing page.
- Gated at ORANGE, like the agent board it contains.
- Labelled as a mixed-kind view at the top, in the document itself, not only in the navigation that led there.
- Never the artifact called `METRICS.md`. That name belongs to the citizen board.

Nobody opens the combined board without already wanting agent data. If someone lands there by accident, the design is wrong.

## This is not hiding the agents

Agents are citizens in the registry, carry `kind: "agent"`, and get their own visible board. A course where students collaborate with coding agents and the agents are invisible in the record would be dishonest about how the work actually happened.

Visible, separate, and comparable within kind. The comparison a student should be able to make about an agent is *what did it do*, not *did it beat me*.

## Consequences for implementation

- `generate_leaderboard` takes a `kind` and defaults to `human`. A mixed board requires passing `kind=None` explicitly, and the rendered document says so in its subtitle.
- Any request for a non-human board carries the viewer's clearance and is refused below ORANGE. Refused loudly, at generation time — not rendered and then hidden by a template, which leaves the data one view-source away.
- `kind` is the partition key, so it must be present on every record. The schema defaults it to `human`, and a record that somehow lacks it partitions as human rather than vanishing.
- Sorting happens *after* partitioning, never before. A single sorted list that is later filtered is the same bug with extra steps — the ranks come out of the wrong denominator.
- The opt-in display rules (`PRD.md` §8) apply to every board independently. An anonymous citizen is anonymous on the agent-inclusive view too.
- `PRD.md` US-3.2's "all citizens appear after first submission" is scoped to the board's own kind. Every human appears on the human board.

## What this does not decide

Whether agent velocity should use the same engine at all, and what an agent's metric set contains. Both are open, and both are downstream of someone actually wanting agent metrics for something.
