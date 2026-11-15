## Analyze

After the closing verification is `done` and before the reviewer, run:

```bash
orchestra analyze {phase} --stage close
```

Refuse to start the reviewer while it exits 1. Fix each error finding
first, then run it again.
