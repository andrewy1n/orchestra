/**
 * orchestra hook adapter for OpenCode.
 *
 * View injection is an optimization, not a correctness requirement: the
 * orchestra skills call `adaptive-artifacts hook-start` themselves when views
 * were not injected. This plugin makes that automatic on OpenCode.
 *
 * It is optional. Delete this file (or install on a host without plugin
 * support) and the skills still work; `adaptive-artifacts hook-stop` just
 * runs later or from the skill.
 */

import { spawn } from "node:child_process"
import { Plugin } from "@opencode/plugin"

function runHook(command, cwd) {
  return new Promise((resolve) => {
    const child = spawn("adaptive-artifacts", [command], {
      cwd,
      stdio: "ignore",
    })
    child.on("error", resolve)
    child.on("close", resolve)
  })
}

export default Plugin.define({
  id: "orchestra-hooks",
  setup(ctx) {
    const controller = new AbortController()
    let started = false

    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({
          signal: controller.signal,
        })) {
          if (event.type === "session.created" && !started) {
            started = true
            await runHook("hook-start", ctx.location.directory)
            continue
          }
          if (event.type === "session.idle" || event.type === "session.deleted") {
            started = false
            await runHook("hook-stop", ctx.location.directory)
          }
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error("orchestra: hook event stream failed", error)
        }
      }
    })()

    return () => controller.abort()
  },
})
