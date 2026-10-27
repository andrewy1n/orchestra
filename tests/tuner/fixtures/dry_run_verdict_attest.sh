#!/usr/bin/env bash
# Local stand-in for the tuner-verdict Actions job (throwaway key).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
FIXTURE="$ROOT/tests/tuner/fixtures/verdict-repo"

bash "$ROOT/tests/tuner/fixtures/build_verdict_repo.sh"
BASE=$(git -C "$FIXTURE" rev-parse HEAD~1)
SHA=$(git -C "$FIXTURE" rev-parse HEAD)

python3 "$ROOT/bin/orchestra" verify verdict --cwd "$FIXTURE" --base "$BASE" --at "$SHA" claim-widget \
  | tee /tmp/vf-verdict.json
python3 -c 'import json; assert json.load(open("/tmp/vf-verdict.json"))["result"]=="pass"'

# Enrich verdict JSON with bind fields for attest emit
python3 - <<PY
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, "$ROOT")
from orchestra.tuner.manifest import load_manifest, resolve_commit, runner_digest

fixture = Path("$FIXTURE")
sha = "$SHA"
verdict = json.load(open("/tmp/vf-verdict.json"))
manifest_blob = Path(fixture / ".tuner/manifest.json").read_bytes()
# Prefer blob at commit
import subprocess
blob = subprocess.check_output(["git", "-C", str(fixture), "show", f"{sha}:.tuner/manifest.json"])
manifest_hash = "sha256:" + hashlib.sha256(blob).hexdigest()
manifest = load_manifest(fixture, sha)
body = {
    "commit": resolve_commit(fixture, sha),
    "manifest_hash": manifest_hash,
    "runner_digest": runner_digest(manifest.runner),
    "claims": verdict["claims"],
}
json.dump(body, open("/tmp/vf-attest-body.json", "w"))
print(json.dumps({"commit": body["commit"], "manifest_hash": manifest_hash}, indent=2))
PY

KEYDIR=$(mktemp -d)
ssh-keygen -t ed25519 -N "" -f "$KEYDIR/key" -q
PUB=$(ssh-keygen -y -f "$KEYDIR/key")
BLOB=$(echo "$PUB" | awk '{print $1" "$2}')
printf '%s\n' "ci namespaces=\"tuner-verdict\" $BLOB" > "$KEYDIR/allowed"

python3 "$ROOT/bin/orchestra" verify attest emit --key "$KEYDIR/key" --input /tmp/vf-attest-body.json \
  | tee /tmp/vf-attestation.json >/dev/null
# re-print for humans
cat /tmp/vf-attestation.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print("signed claims", d.get("claims"))'

MH=$(python3 -c 'import json; print(json.load(open("/tmp/vf-attest-body.json"))["manifest_hash"])')
python3 "$ROOT/bin/orchestra" verify attest verify \
  --allowlist "$KEYDIR/allowed" \
  --commit "$SHA" \
  --manifest-hash "$MH" \
  --input /tmp/vf-attestation.json

echo "dry_run_verdict_attest: ok"
