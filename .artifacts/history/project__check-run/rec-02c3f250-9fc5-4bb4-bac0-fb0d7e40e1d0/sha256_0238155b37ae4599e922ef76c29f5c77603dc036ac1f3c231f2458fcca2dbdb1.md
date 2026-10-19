---
{
  "base_kind": "event",
  "id": "rec-02c3f250-9fc5-4bb4-bac0-fb0d7e40e1d0",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-fa93899c-8721-4377-99f1-a99a14cbf1a2",
    "duration_s": 0.41963,
    "effort": "packaging",
    "exit_code": 1,
    "method": "tdd",
    "output_sha256": "3f8b71ecf7ab12c5fb0ee1308713bbe10a32958528582ca9b2c1d8c696366cc4",
    "requirement": "R2",
    "result": "fail",
    "revision": "e7604b05f15bedb13b9392681a2e950d415ebb4e",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "rename-package-cli"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-15T08:07:31+00:00",
  "relationships": {
    "informed_by": [
      "rec-fa93899c-8721-4377-99f1-a99a14cbf1a2"
    ]
  },
  "revision": "sha256:0238155b37ae4599e922ef76c29f5c77603dc036ac1f3c231f2458fcca2dbdb1",
  "subject": "rename-package-cli",
  "time": {
    "observed": "2026-10-15T08:07:31+00:00",
    "recorded": "2026-10-15T08:07:31+00:00"
  }
}
---

tests/test_aa_resolve.py::test_bin_env_wins
tests/test_aa_resolve.py::test_root_env_uses_tools_py
tests/test_aa_resolve.py::test_plugin_root_sibling_before_path
tests/test_aa_resolve.py::test_path_used_when_no_plugin_root
tests/test_aa_resolve.py::test_home_checkout_not_quiet_fallback
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import affidavit, affidavit.cli; assert not __import__('importlib.util').find_spec('se_workflow')
                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'importlib' has no attribute 'find_spec'
