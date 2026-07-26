# Agents

Two kinds of file live here, and mixing them up will waste your time.

## SHODANN-tuned (maintained)

| Agent | Role | Exercised on |
|---|---|---|
| `citizen-zero` | The reader. Takes one review as a beginner would - with no repository access at all - and reports what they understood, what they would do next, and what they were left believing. Testimony, not critique. | The first REDUCED ALLOCATION review a citizen would receive. Reported "What I would do next: I don't have one", and caught a contradiction no checker could: the review promised readings "measured, not interpreted" and then opened with "The Algorithm is deeply pleased". Both fixed in the same PR. |
| `oracle-warden` | Mechanical gate. Runs the frozen toolchain, verifies oracle fixtures and engine guards are intact, reports pass/fail tables with evidence. Never repairs. | The velocity engine port (`c98c497`). Returned `GATE FAIL` on its first run and was right: `pyproject.toml` declared `ruff>=0.16`, an open bound, while `PRD.md` and `CLAUDE.md` both promised a pin. A routine reinstall would have moved the `C901` numbers that feed the velocity score. Fixed in the same PR that added the agent. |
| `clive-prompt-warden` | Cross-document consistency. Reads every file and checks that what one claims, another has. Reports; never repairs. | Prompt assembly. Caught `_PSEUDO_SYNTAX` failing to match `{{ EXAMPLES }}`, and 20 emoji names present in the templates with no entry in the map — both silent, both would have reached a citizen. |

## Inherited from CSC-134 (unmaintained, do not run as-is)

The rest of this directory was copied from the CSC-134 course-build repository. They were general-purpose agents once, but they drifted hard toward their host: PRISM clearance bands, LPAA beats, module numbering M0–M8, `g++ -std=c++17`, dungeon-canon theme rules.

Run against SHODANN work they import assumptions that do not hold here — a compile gate that shells out to a C++ compiler in a Python repository, a repo warden citing a course spine that does not exist in this tree.

`linx-voice-readability-editor`, `kevin-repo-warden`, `program-advisor` and `spine-owner` have SHODANN analogues worth retargeting, in that order. `cadence-master`, `module-builder` and `liza-theme-skinner` have none — leave them, and delete them if they are still unused once the fleet has been exercised.

**One vocabulary collision to watch.** CSC-134 uses PRISM bands and SHODANN uses INFRARED → BLUE+ for a superficially similar concept. They are not the same ladder and they do not map onto each other. Do not let one leak into the other.

## The three positions

The fleet is not three checkers of the same thing. Each occupies an epistemic
position the others structurally cannot reach:

| Agent | Asks | Sees |
|---|---|---|
| `oracle-warden` | Does it run? | The commands and their output |
| `clive-prompt-warden` | Does it comply? | Every file, cross-referenced |
| `citizen-zero` | Does it teach? | **Only the review** |

The third is the one that cannot cheat. A reader who has seen the submission
will unconsciously supply context the review failed to give, and will report
that the review was clear. Citizen Zero's tool list is empty on purpose -
the constraint is structural rather than a promise.

## Rules for retargeting

1. Rewrite one agent, then **run it on live work in this repository** before starting the next. An agent is done when it has produced a usable result, not when its prompt reads well.
2. No CSC-134 vocabulary survives: no PRISM, no LPAA, no module numbering, no C++ toolchain.
3. A verification agent gets read and run tools only. It reports; the implementer repairs. Enforce that with the `tools:` frontmatter, not with a sentence in the prompt.
4. Record what it was exercised on in the table above.
