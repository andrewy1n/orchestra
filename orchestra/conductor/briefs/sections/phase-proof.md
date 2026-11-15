## Proof packet

When the gate holds, assemble a **proof packet** before phase close
or "phase done" language (skip only when no code/claim change).
Incidental / no-Landing still get a packet when code or claims
changed. Read `## Proof` on the phase for `kind` (default `claims`).
`base` = Landing base (or merge-base with main); `revision` =
phase-head. Machine = pointers only. With
`.tuner/manifest.json`, also `orchestra verify trail` and
`orchestra verify audit --base <base> --head <revision> --require-trail`
into Machine/Attention.

```bash
canon create --type conductor:proof-packet \
  --subject "{phase}" \
  --payload '{"phase":"{phase}","effort":"{effort}","revision":"<phase-head-sha>","base":"<base-sha>","kind":"<demo|commands|claims|audit-triage|mixed>"}' \
  --body-file "<proof-packet-body.md>"
```

Body: `## Look`, `## Machine`, `## Attention`, `## Diff`
(`git diff --stat <base>..<revision>` or `no tree change`). Print Look
and Attention in chat. Refuse "phase complete" without a packet at
this phase-head. Head moves after fixes → new packet.
