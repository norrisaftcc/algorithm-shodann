# HOUSE-STYLE v2.0 — public edition

Status: frozen 2026-07-30 at a GREEN gate by teacherbot.help. Governs documents this
repository ships publicly. The SKILL.md Language lock governs internally until the
repoint amendment freezes.

## This file under its own law
This file is HUMAN mode, declared. Every sentence outside exempt blocks obeys the subset.
HUMAN mode should conform to STE100 Simplified Technical English. 
The fixed-string block is a contract, exempt by rule 8. The verb table is a contract block; edit it only through the amendment process.
Lint this file before any other. If it fails, the failure list ships with it.
Exemption from condensation is not exemption from style. The reason section below keeps
all of its content. Its sentences still obey the rules.

## Why this style exists — exempt from condensation
Controlled language here serves the reader. It does not serve the writer's control of
the reader. Newspeak shrinks a dictionary to shrink thought. This file constrains prose
to stop decay. The mechanism is the same. The targets are opposite. The mechanism does
not know the difference. Three invariants are what know it:
- The dictionary is open. Every change passes a gate and enters the record.
- Every cut is kept. Nothing governed by this style is ever silently smaller.
- The peer's meaning outranks the vocabulary. Always.
A revision that weakens any one of the three has failed. Other improvements do not
excuse it. This file names its nearest neighbor on purpose. A style guide that hides
that neighbor cannot be trusted near it.

## The leverage
STE began in aircraft maintenance manuals. Its reader is non-native, tired, and unable
to afford ambiguity. A spawn package has the same reader: a fresh instance with no
context. The subset is also machine-checkable. That gives prose an assayer that cannot
be flattered. These two facts are the whole case for adoption.

## The enforced subset
1. One word, one meaning, one part of speech.
2. Twenty words per instruction. Twenty-five per descriptive sentence. One instruction per line.
3. Six sentences per paragraph, at most.
4. Active voice. Imperative mood for procedures. Present tense unless time is the subject.
5. No idioms. No noun cluster longer than three nouns.
6. Warnings come before the action they govern. Command form.
7. Mode governs grammar. Declare the mode in the file. HUMAN mode: connective grammar
   is load-bearing. MACHINE mode: shorthand is fine if the downstream receiver succeeds.
8. Fixed strings are contracts, not prose. Exempt from style and from all editing
   outside the amendment process.
9. Domain terms belong to the peer. A wrong-but-deliberate term survives with a Note.
   The peer decides.
10. The reason section of any governed document is exempt from condensation.
    The exemption is written inside the section it protects.
11. Fixed strings appear only verbatim, in running text or in a dedicated block.
    Never in a table cell, a caption, or any container a formatter owns.

## Controlled protocol nouns
- GATE: noun only. The act is FREEZE. Text that verbs a gate fails the lint.
- SEAT: split entry. The noun is the position. The verb is the act of assigning it.
- Rule 1 governs every future protocol noun the same way.

## Fixed strings — dedicated block, per rule 11
These forms are verbatim and sole. Reference them below as F1 through F4.
- F1: "Freeze this contract and execute, or keep negotiating?"
- F2: "Contract frozen. Executing."
- F3: "Failed on [item]. Contract reopened."
- F4: "This is a finding, not a draft."

## Technical verbs — the operational set
Technical verbs are defined by the subject field, per the supplier's own architecture.
Each enters through the gate with four items: one meaning, one part of speech,
a completion condition, a failure condition. No fourth item, no entry.

| Verb | Meaning | Complete when | Fails when |
|---|---|---|---|
| PROVIDE | compress a draft contract to the floor; negotiate; execute after freeze | executed exactly as frozen | reopen per F3 |
| ASSAY | read a received document against the floor; report | closed per F4 | any redraft voids the finding |
| FREEZE | a live human at gate color accepts the full text in front of them | acknowledged per F2 | the phrase from a model freezes nothing |
| EXECUTE | perform the frozen contract exactly | deliverable matches contract | reopen per F3 |
| FILE | Scribe records a finding, gateless, addressed to its owning clearance | filed and addressed | a filing that asks a gate question is void |
| WARN | Scribe alerts the proxy seat immediately | logged and delivered | a warning that untangles is void |
| ESCALATE | route a question up the report chain, outside the session | logged and routed | in-session resolution voids it |
| SEAT | assign a position with clearance, capabilities, N, and escalation route | one-line confirmation from the seated agent | no escalation route: error at seating |
| SPAWN | create a sub-agent within allowance N | sub-agent seated, count at or under N | refuse at N+1 and log the refusal |
| SHIP † | deliver the work product and the transcript together | both delivered | either alone is not shipped |

† SHIP imports a transcript requirement from the parent system. A repository that adopts
this style alone adopts nine verbs. SHIP enters with the system that defines its transcript.

## The dictionary
- Source: ASD-STE100 Issue 9, obtained by request form, held as PDF by a human.
- No machine-readable upstream exists. Transcription is manual, gated work.
  One subject field at a time. Each entry is an amendment, recorded.
- The friction is a feature. A dictionary you must ask a human for cannot be
  silently slurped. Ours inherits that property by construction.
- Additions and removals pass the same gate. The dictionary is versioned.
- A dictionary that shrinks without a record is the failure this file exists to prevent.

## Enforcement
- The subset is machine-checkable: word counts, sentence lengths, approved-word
  membership, part-of-speech conflicts, verbed gates, misplaced fixed strings.
- Build the linter. Run it as an assayer: it reports, it never rewrites.
- Rule 9 outranks the linter. The linter flags; the peer decides.

## Supplier record
Upstream: ASD-STE100 Issue 9. Recorded as a supplier, not an authority. No license held.
No external document governs this repository. One line of respect, earned: the supplier
has run a version of our gate since 1983 — change forms, human review, recorded
amendments, deliberate distribution. 
