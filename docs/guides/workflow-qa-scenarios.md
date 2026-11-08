# Workflow discussion walkthroughs

Use these scenarios for one grouped human review of the spec and design
skills. Text checks confirm instruction boundaries. They do not prove
conversation quality.

## Intent and clarification: R30, R31, R32, R33, R34

**Prompt:** “Make phase setup easier.” The phase, existing tools, and users
are already in the store.

**Expected:** The assistant reads the phase and current tools. It reflects the
likely outcome and asks one open question about the largest missing behavior.
It explains the consequence when the answer changes scope. It does not offer
implementation choices while user intent remains unclear. Once intent is
clear, it asks only questions the existing records do not answer.

**Review:** Check context use, one-question pacing, consequence, and whether
the assistant avoids repeating supplied facts.

## Behavioral examples: R35

**Prompt:** Specify a tool that saves a user draft and can lose connectivity.

**Expected:** The assistant tests a normal save and a relevant failure or
retry example. It asks whether the observed behavior matches the intended
contract. It keeps transport, storage, and retry design for the design step.

**Review:** Check that examples clarify observable behavior without choosing
technical components.

## Technical walkthroughs: R36, R37, R38, R39, R40

**Prompt:** Design a workflow with stored progress, resumable work, and
upstream changes.

**Expected:** The assistant inspects current records and code before it asks
for preferences. It traces normal operation, relevant recovery, upstream
change, and proof. It states uncertain technical facts and researches them
before comparing options. It does not claim that an untested assumption is a
fact.

**Review:** Check that each walkthrough applies to a real risk and each option
satisfies the agreed specification.

## Depth and final review: R41, R42

**Prompt:** Compare a local text change with a change to shared recovery and
interfaces.

**Expected:** The assistant keeps the local change concise. It investigates
the shared change's recovery and interface effects in more depth. It ends
each discussion with one consolidated specification or design and asks for
review. It stops asking questions when no consequential gap remains.

**Review:** Check depth against consequence, complete output, and a clear
approval request.

## Approval boundary

For each walkthrough, answer the final review with either an explicit
approval or an explicit delegation. Then check that the matching workflow
review records the artifact and authority. A request to continue or a
completed Q&A alone does not establish readiness.
