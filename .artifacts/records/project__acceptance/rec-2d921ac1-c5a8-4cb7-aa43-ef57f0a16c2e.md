---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-2d921ac1-c5a8-4cb7-aa43-ef57f0a16c2e",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "effort": "library-boundary",
    "method": "check",
    "phase": "orchestra-callers",
    "requirement": "R8",
    "verify_command": "python3 -c 'import os,subprocess,sys,tempfile; from pathlib import Path; root=Path.cwd(); b=Path(tempfile.mkdtemp()); (b/\"sitecustomize.py\").write_text(\"import sys\\nclass Block:\\n def find_spec(self, name, path, target=None):\\n  if name==\\\"affidavit\\\" or name.startswith(\\\"affidavit.\\\"):\\n   raise ImportError(name)\\n  return None\\nsys.meta_path.insert(0, Block())\\n\"); env=os.environ.copy(); pp=env.get(\"PYTHONPATH\",\"\"); env[\"PYTHONPATH\"]=str(b)+os.pathsep+str(root)+(os.pathsep+pp if pp else \"\"); p=subprocess.run([sys.executable, str(root/\"bin\"/\"orchestra\"), \"--help\"], cwd=root, env=env); raise SystemExit(p.returncode)'"
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-21T11:14:56+00:00",
  "relationships": {},
  "revision": "sha256:88d7926f12a07e01d7bb833f352c5b8f7b52b5edd0e9d24e0447af5b287978ed",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "close-library-help",
  "time": {
    "as_of": "2026-10-21T10:29:18+00:00"
  }
}
---

