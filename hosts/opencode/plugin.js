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
export const OrchestraHooks = async ({ $, directory }) => {
  let started = false

  return {
    event: async ({ event }) => {
      if (event.type === "session.created" && !started) {
        started = true
        await $`adaptive-artifacts hook-start`.cwd(directory).catch(() => {})
        return
      }
      if (event.type === "session.idle" || event.type === "session.deleted") {
        started = false
        await $`adaptive-artifacts hook-stop`.cwd(directory).catch(() => {})
      }
    },
  }
}
