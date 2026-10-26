---
{
  "id": "rec-ff6595e5-3e4e-4dcd-80ac-9efcba034eb0",
  "lifecycle_state": "active",
  "payload": {
    "effort": "library-boundary",
    "method": "check",
    "phase": "library-e2e",
    "requirement": "R1",
    "verify_command": "python3 -c 'import importlib.util,tempfile; from pathlib import Path; s=importlib.util.spec_from_file_location(\"e2e\",\"tests/test_library_e2e.py\"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); repo,_=m._repository(Path(tempfile.mkdtemp())); assert (repo/\".git\").is_dir()'"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-21T12:10:41+00:00",
  "relationships": {},
  "revision": "sha256:3fb62a86935599b741776730d6efb912b36c1742ad534e0390304df4dc3fad25",
  "subject": "library-fixture",
  "time": {
    "as_of": "2026-10-21T11:55:21+00:00"
  }
}
---

