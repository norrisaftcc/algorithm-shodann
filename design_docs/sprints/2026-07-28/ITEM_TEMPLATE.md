# Candidate item template

Every survey finding fills this and nothing else. The template carries the rigor;
the surveyor carries the labour. A surveyor does not need to know why the fields
exist, and deliberately is not told.

```
ID:               S1-NN
Tag:              hygiene | ledger
What:             one sentence, plain
Where:            path:line
Why now:          one sentence
Depends on:       item IDs, or "none"
Effort:           S | M | L
Risk if skipped:  one sentence
Confidence:       high | low
```

## Field notes

**Tag** — `hygiene` is a one-off fix confined to this repo. `ledger` touches
`.shodann/` citizen state, its schema, or anything a live record depends on;
those carry blast radius across every existing citizen file. The two do not
share units, and keeping them distinguishable is the point.

**Effort — S/M/L, never minutes.** A mixed human/agent team cannot share a clock:
one side does not experience wall time, the other does not count tool calls.
Ordinal buckets are the one unit both can read, and calibration on buckets is
still calibration — did the S items stay S?

**Depends on** — the field exists so ordering constraints get recorded whether or
not anyone is thinking about them. A ranking that ignores dependencies is wrong
regardless of which method produced it.

**Confidence** — `low` is a valid and useful answer. An item nobody is sure about
is data; an item everyone pretends to be sure about is not.
