# Phase end

Parent-only. Run after the closing verification task is `done`, when
no same-focus `planned`/`in_progress` work-items remain (or the
incidental task is closed). Order:

last implementation wave → closing verification → analyze → suite (per
`[suite]` in `orchestra.toml`) → reviewer → integration-report from
reviewer `integration` → phase gate → phase close.

After the last implementation wave's execution-reports, return to
execute step 3 for the closing verification task. Do **not**
write an integration-report before verification.

Skip reviewer / review check-run / integration-report / suite when
incidental. An empty task list is not proof the phase is done — check
the gate below before closing.
