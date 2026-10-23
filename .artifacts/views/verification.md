# Project Verification

> Derived view — not authoritative. Edit underlying records, not this file.
> Store state: sha256:2d6a143f676e6d8c60c32801351f220b41b43248bed8d6fe43d5e503a919e6f6

## aa-installable-package

### Acceptance
- **aa-installable-package**: R1; check; packaging; test -f ~/adaptive-artifacts/pyproject.toml && grep -q adaptive-artifacts ~/adaptive-artifacts/pyproject.toml && grep -qE "scripts|entry.points|project.scripts" ~/adaptive-artifacts/pyproject.toml _(id: [rec-5926eafe-efb8-47ac-a314-50c1ff066f90](.artifacts/records/project__acceptance/rec-5926eafe-efb8-47ac-a314-50c1ff066f90.md))_

### Check
- **aa-installable-package**: rec-5926eafe-efb8-47ac-a314-50c1ff066f90; a086e27ca3eaff82960f6d5f4685a8dab4525a6b; pass; check _(id: [rec-49590822-0819-49cd-b0ed-056be7c098b7](.artifacts/records/project__check-run/rec-49590822-0819-49cd-b0ed-056be7c098b7.md))_

## aa-installable-package-plugin-bin

### Acceptance
- **aa-installable-package-plugin-bin**: R4; check; packaging; ~/adaptive-artifacts/bin/adaptive-artifacts --help >/dev/null _(id: [rec-de0125fd-b020-48fc-bd52-f66a04de6cbf](.artifacts/records/project__acceptance/rec-de0125fd-b020-48fc-bd52-f66a04de6cbf.md))_

### Check
- **aa-installable-package-plugin-bin**: rec-de0125fd-b020-48fc-bd52-f66a04de6cbf; a086e27ca3eaff82960f6d5f4685a8dab4525a6b; pass; check _(id: [rec-2fddaf05-bb48-4242-a78d-55585b11431d](.artifacts/records/project__check-run/rec-2fddaf05-bb48-4242-a78d-55585b11431d.md))_

## aa-installable-package-tools-shim

### Acceptance
- **aa-installable-package-tools-shim**: R5; check; packaging; python3 ~/adaptive-artifacts/tools/artifacts.py --help >/dev/null _(id: [rec-d7737207-7463-4fa3-828f-647c738784bf](.artifacts/records/project__acceptance/rec-d7737207-7463-4fa3-828f-647c738784bf.md))_

### Check
- **aa-installable-package-tools-shim**: rec-d7737207-7463-4fa3-828f-647c738784bf; a086e27ca3eaff82960f6d5f4685a8dab4525a6b; pass; check _(id: [rec-c3ecfc7f-1928-4e98-a7f7-55252996bb52](.artifacts/records/project__check-run/rec-c3ecfc7f-1928-4e98-a7f7-55252996bb52.md))_

## aa-library-review

### Check
- **aa-library-review**: aa-library-review; 206fcd0b22ed111d7a272c934bb1864271947591; fail; review _(id: [rec-016c0bd8-dc44-4247-97c8-da58c621e7c5](.artifacts/records/project__check-run/rec-016c0bd8-dc44-4247-97c8-da58c621e7c5.md))_
- **aa-library-review**: aa-library-review; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; review _(id: [rec-1654c2f3-ea33-4725-9d3e-9ac2b3ab7f25](.artifacts/records/project__check-run/rec-1654c2f3-ea33-4725-9d3e-9ac2b3ab7f25.md))_

## aa-packaging-amendment

### Acceptance
- **aa-packaging-amendment**: R8; manual; packaging _(id: [rec-f9dc41e0-3e64-4707-b78a-db7b4f48eeb4](.artifacts/records/project__acceptance/rec-f9dc41e0-3e64-4707-b78a-db7b4f48eeb4.md))_

### Check
- **aa-packaging-amendment**: rec-f9dc41e0-3e64-4707-b78a-db7b4f48eeb4; dirty; pass; manual; andrewyin _(id: [rec-f0ff3286-8d12-4ee7-be65-88e4d0b6948c](.artifacts/records/project__check-run/rec-f0ff3286-8d12-4ee7-be65-88e4d0b6948c.md))_

## aa-uv-tool-install-proof

### Acceptance
- **aa-uv-tool-install-proof**: R2; check; packaging; test -x ~/adaptive-artifacts/scripts/prove_uv_tool_install.sh && ~/adaptive-artifacts/scripts/prove_uv_tool_install.sh _(id: [rec-33598676-02a1-45b7-9d6f-379587854c4e](.artifacts/records/project__acceptance/rec-33598676-02a1-45b7-9d6f-379587854c4e.md))_

### Check
- **aa-uv-tool-install-proof**: rec-33598676-02a1-45b7-9d6f-379587854c4e; db2b7e9f447a6d63b61be244296fa998f1395205; pass; check _(id: [rec-b4bf3529-6490-42cd-81f1-a3fc4dbd3511](.artifacts/records/project__check-run/rec-b4bf3529-6490-42cd-81f1-a3fc4dbd3511.md))_

## aa-uv-tool-install-proof-store

### Acceptance
- **aa-uv-tool-install-proof-store**: R3; check; packaging; ~/adaptive-artifacts/scripts/prove_uv_tool_install.sh _(id: [rec-d9c4add2-b3a0-4106-8778-46d3711d3c7e](.artifacts/records/project__acceptance/rec-d9c4add2-b3a0-4106-8778-46d3711d3c7e.md))_

### Check
- **aa-uv-tool-install-proof-store**: rec-d9c4add2-b3a0-4106-8778-46d3711d3c7e; db2b7e9f447a6d63b61be244296fa998f1395205; pass; check _(id: [rec-ebcffda4-ba5f-4804-84eb-bd3398394ff2](.artifacts/records/project__check-run/rec-ebcffda4-ba5f-4804-84eb-bd3398394ff2.md))_

## activity-failures

### Acceptance
- **activity-failures**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k fail _(id: [rec-7d228e89-762a-4794-9c56-adfca651899a](.artifacts/records/project__acceptance/rec-7d228e89-762a-4794-9c56-adfca651899a.md))_

### Check
- **activity-failures**: rec-7d228e89-762a-4794-9c56-adfca651899a; 6c723d89c0a95f1c261cd940f48e51f9a731bfd1; pass; tdd _(id: [rec-2a089a7b-872b-465c-9b46-aaa8ae7f5812](.artifacts/records/project__check-run/rec-2a089a7b-872b-465c-9b46-aaa8ae7f5812.md))_

## add-dashboard-view

### Acceptance
- **add-dashboard-view**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-b6ae7140-2e58-4194-9294-6cc47d132fb4](.artifacts/records/project__acceptance/rec-b6ae7140-2e58-4194-9294-6cc47d132fb4.md))_

### Check
- **add-dashboard-view**: rec-1dceda28-8bfd-43df-b3ca-53d3a7740286; c993c1b8159c0a5a28827c63e588a86f40a0971b; pass; tdd _(id: [rec-31267407-87d0-4234-b4bb-761394266851](.artifacts/records/project__check-run/rec-31267407-87d0-4234-b4bb-761394266851.md))_
- **add-dashboard-view**: rec-b6ae7140-2e58-4194-9294-6cc47d132fb4; c993c1b8159c0a5a28827c63e588a86f40a0971b; pass; tdd _(id: [rec-c2cd5a62-cd01-4fe9-9a3d-83ce6a3b6abc](.artifacts/records/project__check-run/rec-c2cd5a62-cd01-4fe9-9a3d-83ce6a3b6abc.md))_

## add-dashboard-view-render

### Acceptance
- **add-dashboard-view-render**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q -k dashboard _(id: [rec-1dceda28-8bfd-43df-b3ca-53d3a7740286](.artifacts/records/project__acceptance/rec-1dceda28-8bfd-43df-b3ca-53d3a7740286.md))_

## advisory-suite-verification-policy

### Finding
- **advisory-suite-verification-policy**: advisory suite fail for verification-policy-suite; exit_code=1; failing journal pager tests under full suite; suite check-run passes at phase head, or human clears; none _(id: [rec-bc32b08c-6674-4bef-ac01-5f0442fae56c](.artifacts/records/project__finding/rec-bc32b08c-6674-4bef-ac01-5f0442fae56c.md))_

## affidavit-library-review

### Check
- **affidavit-library-review**: affidavit-library-review; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; review _(id: [rec-3bf4a5ae-ddad-495a-8331-77fdaf5ef7ca](.artifacts/records/project__check-run/rec-3bf4a5ae-ddad-495a-8331-77fdaf5ef7ca.md))_

## affidavit-readme-git-tool

### Acceptance
- **affidavit-readme-git-tool**: R6; check; packaging; grep -qiE 'uv tool install' README.md && grep -qiE 'git\+https://github.com/andrewy1n/adaptive-artifacts' README.md && grep -qiE 'PyPI.*(defer|later|not yet|wait)' README.md && ! test -f pyproject.toml _(id: [rec-7e5deb60-6cc8-4796-9c46-325a846307cb](.artifacts/records/project__acceptance/rec-7e5deb60-6cc8-4796-9c46-325a846307cb.md))_

### Check
- **affidavit-readme-git-tool**: rec-7e5deb60-6cc8-4796-9c46-325a846307cb; 5257818a25994a1b41742f10c48d12cb7e5d767c; pass; check _(id: [rec-884824d4-d802-4825-82df-dee9e34a297f](.artifacts/records/project__check-run/rec-884824d4-d802-4825-82df-dee9e34a297f.md))_

## affidavit-readme-git-tool-nopypi

### Acceptance
- **affidavit-readme-git-tool-nopypi**: R7; check; packaging; ! test -f pyproject.toml && ! grep -qiE 'twine upload|uv publish|pypi.org/project/adaptive-artifacts' README.md _(id: [rec-53c95333-c05e-4e8d-ad66-cd3d97bfc055](.artifacts/records/project__acceptance/rec-53c95333-c05e-4e8d-ad66-cd3d97bfc055.md))_

### Check
- **affidavit-readme-git-tool-nopypi**: rec-53c95333-c05e-4e8d-ad66-cd3d97bfc055; 5257818a25994a1b41742f10c48d12cb7e5d767c; pass; check _(id: [rec-b072bd28-67c5-4ab0-b11f-cd5a1b707720](.artifacts/records/project__check-run/rec-b072bd28-67c5-4ab0-b11f-cd5a1b707720.md))_

## ag-aggregate-cli

### Acceptance
- **ag-aggregate-cli**: tdd; session-analysis; python3 -m pytest -q tests/test_session_aggregate.py _(id: [rec-efaa257a-446d-4f97-a738-4d098747043f](.artifacts/records/project__acceptance/rec-efaa257a-446d-4f97-a738-4d098747043f.md))_

### Check
- **ag-aggregate-cli**: rec-efaa257a-446d-4f97-a738-4d098747043f; dirty; pass; tdd _(id: [rec-2d90d015-36ae-4873-a6d1-98bdecf0a0ec](.artifacts/records/project__check-run/rec-2d90d015-36ae-4873-a6d1-98bdecf0a0ec.md))_

## ag-effort-rollup

### Acceptance
- **ag-effort-rollup**: tdd; session-analysis; python3 -m pytest -q tests/test_effort_rollup.py _(id: [rec-d0cbaaf6-d767-45f6-aa4d-f32b9415b6bc](.artifacts/records/project__acceptance/rec-d0cbaaf6-d767-45f6-aa4d-f32b9415b6bc.md))_

### Check
- **ag-effort-rollup**: rec-d0cbaaf6-d767-45f6-aa4d-f32b9415b6bc; dirty; pass; tdd _(id: [rec-2a7118de-ad03-4568-9f13-c9f5b4c3be61](.artifacts/records/project__check-run/rec-2a7118de-ad03-4568-9f13-c9f5b4c3be61.md))_

## ag-outliers

### Acceptance
- **ag-outliers**: tdd; session-analysis; python3 -m pytest -q tests/test_session_outliers.py _(id: [rec-4b4378e7-5443-435e-86ab-02ad515ebb4d](.artifacts/records/project__acceptance/rec-4b4378e7-5443-435e-86ab-02ad515ebb4d.md))_

### Check
- **ag-outliers**: rec-4b4378e7-5443-435e-86ab-02ad515ebb4d; dirty; pass; tdd _(id: [rec-46e8a5f9-0acc-4f97-8a6e-c630b856a816](.artifacts/records/project__check-run/rec-46e8a5f9-0acc-4f97-8a6e-c630b856a816.md))_

## ag-tool-skill-rollup

### Acceptance
- **ag-tool-skill-rollup**: tdd; session-analysis; python3 -m pytest -q tests/test_tool_skill_rollup.py _(id: [rec-f283ff9c-78e6-439b-ae65-90ef88690304](.artifacts/records/project__acceptance/rec-f283ff9c-78e6-439b-ae65-90ef88690304.md))_

### Check
- **ag-tool-skill-rollup**: rec-f283ff9c-78e6-439b-ae65-90ef88690304; dirty; pass; tdd _(id: [rec-d83cb7ea-fdf5-43ff-963d-6a25570a2de5](.artifacts/records/project__check-run/rec-d83cb7ea-fdf5-43ff-963d-6a25570a2de5.md))_

## approval-confirm-ux

### Acceptance
- **approval-confirm-ux**: R1; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and (detail or confirm or cancel)' _(id: [rec-18701e87-22d6-4a86-add9-8b350996cbcf](.artifacts/records/project__acceptance/rec-18701e87-22d6-4a86-add9-8b350996cbcf.md))_

### Check
- **approval-confirm-ux**: rec-18701e87-22d6-4a86-add9-8b350996cbcf; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; tdd _(id: [rec-18a75883-bd92-4900-ba37-7f83f25bdb57](.artifacts/records/project__check-run/rec-18a75883-bd92-4900-ba37-7f83f25bdb57.md))_

## approval-confirm-ux-actions

### Acceptance
- **approval-confirm-ux-actions**: R3; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and (approve or reject or sign or accept)' _(id: [rec-cfce9c2b-44e5-4324-913a-5bb887a7aa33](.artifacts/records/project__acceptance/rec-cfce9c2b-44e5-4324-913a-5bb887a7aa33.md))_

### Check
- **approval-confirm-ux-actions**: rec-cfce9c2b-44e5-4324-913a-5bb887a7aa33; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; tdd _(id: [rec-c31a38af-f997-4e0f-aee3-c5a16df0102f](.artifacts/records/project__check-run/rec-c31a38af-f997-4e0f-aee3-c5a16df0102f.md))_

## approval-confirm-ux-readme

### Acceptance
- **approval-confirm-ux-readme**: R8; check; workflow-loop; grep -E 'Approve|Reject|Accept risk|Sign' README.md && grep -E 'Needs you|dismiss|confirm' README.md _(id: [rec-454294d0-2d0a-4652-92d3-ddfd22b795fd](.artifacts/records/project__acceptance/rec-454294d0-2d0a-4652-92d3-ddfd22b795fd.md))_

### Check
- **approval-confirm-ux-readme**: rec-454294d0-2d0a-4652-92d3-ddfd22b795fd; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; check _(id: [rec-bfbc3223-705a-45cc-b668-1664a79619e1](.artifacts/records/project__check-run/rec-bfbc3223-705a-45cc-b668-1664a79619e1.md))_

## approval-constraints

### Acceptance
- **approval-constraints**: R7; check; workflow-loop; /home/andrewyin/adaptive-artifacts/bin/adaptive-artifacts --store /home/andrewyin/se-workflow/.artifacts list --type project:constraint --state active | python3 -c "import sys,json; d=json.load(sys.stdin); stmts=[(r['subject'], (r.get('payload') or {}).get('statement') or '') for r in d['records']]; assert any(s=='dashboard-human-gate-writes' for s,_ in stmts); hg=[t for s,t in stmts if s=='dashboard-human-gate-writes']; assert hg and ('human Needs-you' in hg[0] or 'human-gate' in hg[0].lower()); old={'dashboard-read-only','dashboard-read-only-dashboard-bugfix','dashboard-read-only-dashboard-features'}; assert not any('never writes' in t.lower() for s,t in stmts if s in old); assert all('Retired' in t or 'dashboard-human-gate-writes' in t for s,t in stmts if s in old)" _(id: [rec-7927a6c7-eea1-4224-b9a1-9d4800dce4b0](.artifacts/records/project__acceptance/rec-7927a6c7-eea1-4224-b9a1-9d4800dce4b0.md))_

### Check
- **approval-constraints**: rec-7927a6c7-eea1-4224-b9a1-9d4800dce4b0; dirty; pass; check _(id: [rec-da95e0a2-c3d9-4062-99f0-7d1b309b6a40](.artifacts/records/project__check-run/rec-da95e0a2-c3d9-4062-99f0-7d1b309b6a40.md))_

## approval-contract

### Acceptance
- **approval-contract**: R8; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py -q -k approval_optional_payload_note_fields _(id: [rec-de3c1982-720c-4be7-90ef-54f23b74e65e](.artifacts/records/project__acceptance/rec-de3c1982-720c-4be7-90ef-54f23b74e65e.md))_

### Check
- **approval-contract**: rec-de3c1982-720c-4be7-90ef-54f23b74e65e; 74bd9a1d9af382217e652fb4eb3f7a23fb61a25d; pass; tdd _(id: [rec-03aaea29-4322-4cbd-a60e-77bed891d77c](.artifacts/records/project__check-run/rec-03aaea29-4322-4cbd-a60e-77bed891d77c.md))_
- **approval-contract**: rec-de3c1982-720c-4be7-90ef-54f23b74e65e; 99072b992cdbd1c45a11081d940de72e61022d3b; fail; tdd _(id: [rec-6e29f579-2087-4eb7-b762-3fb53abd21a4](.artifacts/records/project__check-run/rec-6e29f579-2087-4eb7-b762-3fb53abd21a4.md))_
- **approval-contract**: rec-de3c1982-720c-4be7-90ef-54f23b74e65e; 74bd9a1d9af382217e652fb4eb3f7a23fb61a25d; pass; tdd _(id: [rec-706b4c15-8743-4096-a7e7-23bdba2bd25d](.artifacts/records/project__check-run/rec-706b4c15-8743-4096-a7e7-23bdba2bd25d.md))_
- **approval-contract**: rec-de3c1982-720c-4be7-90ef-54f23b74e65e; 99072b992cdbd1c45a11081d940de72e61022d3b; pass; tdd _(id: [rec-970a0b83-b87f-4de8-a07c-dc081ef1c1e4](.artifacts/records/project__check-run/rec-970a0b83-b87f-4de8-a07c-dc081ef1c1e4.md))_

## approval-dismiss

### Acceptance
- **approval-dismiss**: R4; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k 'approval and (dismiss or revision or reject)' _(id: [rec-6709bf08-2353-479f-ae3d-993edd2c640c](.artifacts/records/project__acceptance/rec-6709bf08-2353-479f-ae3d-993edd2c640c.md))_

### Check
- **approval-dismiss**: rec-6709bf08-2353-479f-ae3d-993edd2c640c; 83a192e629165f9377c23943ea7088c2ce53e3e4; pass; tdd _(id: [rec-d5d8e1a2-38b3-41a6-ad24-a3547b8c4d9e](.artifacts/records/project__check-run/rec-d5d8e1a2-38b3-41a6-ad24-a3547b8c4d9e.md))_

## approval-dismiss-stale

### Acceptance
- **approval-dismiss-stale**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and stale' _(id: [rec-5acd72b1-7099-4efa-a8b1-ac7f5c99ebd1](.artifacts/records/project__acceptance/rec-5acd72b1-7099-4efa-a8b1-ac7f5c99ebd1.md))_

### Check
- **approval-dismiss-stale**: rec-5acd72b1-7099-4efa-a8b1-ac7f5c99ebd1; 83a192e629165f9377c23943ea7088c2ce53e3e4; pass; tdd _(id: [rec-9071df4e-a52b-459d-81c4-e36f196f16da](.artifacts/records/project__check-run/rec-9071df4e-a52b-459d-81c4-e36f196f16da.md))_

## as-cost-null

### Acceptance
- **as-cost-null**: tdd; session-analysis; python3 -m pytest -q tests/test_session_fields.py _(id: [rec-36001c1e-b274-4757-b5b3-44fd1a44e292](.artifacts/records/project__acceptance/rec-36001c1e-b274-4757-b5b3-44fd1a44e292.md))_

### Check
- **as-cost-null**: rec-36001c1e-b274-4757-b5b3-44fd1a44e292; dirty; pass; tdd _(id: [rec-cdcd7553-bfa6-4461-8cc7-fb0bce6b615c](.artifacts/records/project__check-run/rec-cdcd7553-bfa6-4461-8cc7-fb0bce6b615c.md))_

### Finding
- **as-cost-null**: Null cost_usd on 140 of 247 sessions is a data gap: those transcripts have no cost-state line, so cost totals are a lower bound over 107 sessions.; Streamed all 140 null transcripts: 0 cost-state lines and 0 cost-named keys. The 107 non-null sessions parse correctly.; Claude Code starts writing cost-state lines for more sessions, or a different cost field appears in transcripts.; none _(id: [rec-8aa9b9e5-9088-4e73-a8ec-facffa2d3833](.artifacts/records/project__finding/rec-8aa9b9e5-9088-4e73-a8ec-facffa2d3833.md))_

## as-dry-run

### Acceptance
- **as-dry-run**: manual; session-analysis _(id: [rec-2fa1b9d2-53f0-4a38-bc7f-ace90efeb566](.artifacts/records/project__acceptance/rec-2fa1b9d2-53f0-4a38-bc7f-ace90efeb566.md))_

### Check
- **as-dry-run**: rec-2fa1b9d2-53f0-4a38-bc7f-ace90efeb566; dirty; pass; manual _(id: [rec-23dbd684-3ad1-481e-ac44-afd9f4a53263](.artifacts/records/project__check-run/rec-23dbd684-3ad1-481e-ac44-afd9f4a53263.md))_
- **as-dry-run**: rec-2fa1b9d2-53f0-4a38-bc7f-ace90efeb566; dirty; pass; manual; Andrew Yin _(id: [rec-37f7dd93-e369-4875-9188-d90fef4007c4](.artifacts/records/project__check-run/rec-37f7dd93-e369-4875-9188-d90fef4007c4.md))_
- **as-dry-run**: rec-2fa1b9d2-53f0-4a38-bc7f-ace90efeb566; dirty; pass; manual; andrewyin _(id: [rec-e3de74ac-ae4b-4d14-8bd4-af486373d840](.artifacts/records/project__check-run/rec-e3de74ac-ae4b-4d14-8bd4-af486373d840.md))_

### Finding
- **as-dry-run**: The analyze-sessions skill yields 4 specific, metric-backed candidates on real data, but it lacks rules the agent had to guess: temp directory, pattern and noise, severity, and tool-level session ids.; Dry run over 243 sessions: 4 candidates each with a metric, session references and a target; 4 patterns dropped; 6 of 7 done-when criteria met (step 7 deferred to the caller). I re-checked the Bash, jira_create_issue and error-outlier numbers against a fresh run and they match.; SKILL.md defines the missing rules and a second dry run needs no manual report.jsonl lookups.; none _(id: [rec-1e84d081-a11f-4cf3-b588-672c9f99d52b](.artifacts/records/project__finding/rec-1e84d081-a11f-4cf3-b588-672c9f99d52b.md))_

## as-dry-run-rerun

### Finding
- **as-dry-run-rerun**: After the rules fix the skill needs no guessed rules for pattern, noise, severity or tool-level session references, but two gaps remain: project identity for worktree paths, and candidate edits that need a transcript read.; Second dry run over 243 sessions: 2 candidates with full session ids and targets, 2 patterns dropped, 1 noise session. The agent named remaining gaps: worktree project strings, double counting of slots across patterns, edits that cannot be named from metrics, cost outliers with empty efforts have no target, cross-repo fix locations.; SKILL.md and targets.md state the project-identity, double counting, evidence-needed and cross-repo rules and a third run needs no guesses.; none _(id: [rec-b393a226-8a19-4952-abff-ecfaf8532b8b](.artifacts/records/project__finding/rec-b393a226-8a19-4952-abff-ecfaf8532b8b.md))_

## as-skill

### Acceptance
- **as-skill**: tdd; session-analysis; python3 -m pytest -q tests/test_analyze_sessions_skill.py tests/test_skill_contract_consistency.py _(id: [rec-d186eb9e-852f-4f75-96aa-313e576c0f8b](.artifacts/records/project__acceptance/rec-d186eb9e-852f-4f75-96aa-313e576c0f8b.md))_

### Check
- **as-skill**: rec-d186eb9e-852f-4f75-96aa-313e576c0f8b; dirty; pass; tdd _(id: [rec-f0d0b94f-0628-4826-a559-1d534622f347](.artifacts/records/project__check-run/rec-f0d0b94f-0628-4826-a559-1d534622f347.md))_

## as-skill-rules

### Acceptance
- **as-skill-rules**: tdd; session-analysis; python3 -m pytest -q tests/test_analyze_sessions_skill.py tests/test_skill_contract_consistency.py _(id: [rec-f0c76da5-b91f-4660-bcc7-e221a00ac3e8](.artifacts/records/project__acceptance/rec-f0c76da5-b91f-4660-bcc7-e221a00ac3e8.md))_

### Check
- **as-skill-rules**: rec-f0c76da5-b91f-4660-bcc7-e221a00ac3e8; dirty; pass; tdd _(id: [rec-9b88c13a-abba-4c98-ba93-556c2280ccaa](.artifacts/records/project__check-run/rec-9b88c13a-abba-4c98-ba93-556c2280ccaa.md))_

## as-targets

### Acceptance
- **as-targets**: tdd; session-analysis; python3 -m pytest -q tests/test_analyze_sessions_targets.py _(id: [rec-9c15a1e4-c392-4ce0-8482-7bea7dd7f367](.artifacts/records/project__acceptance/rec-9c15a1e4-c392-4ce0-8482-7bea7dd7f367.md))_

### Check
- **as-targets**: rec-9c15a1e4-c392-4ce0-8482-7bea7dd7f367; dirty; pass; tdd _(id: [rec-aeb76e26-4633-45f2-8afb-47c8a383a79c](.artifacts/records/project__check-run/rec-aeb76e26-4633-45f2-8afb-47c8a383a79c.md))_

## assess-route

### Acceptance
- **assess-route**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_assess_routing.py -q _(id: [rec-fb7cdbf9-8de6-4066-a413-41f688ed3792](.artifacts/records/project__acceptance/rec-fb7cdbf9-8de6-4066-a413-41f688ed3792.md))_

### Check
- **assess-route**: rec-fb7cdbf9-8de6-4066-a413-41f688ed3792; dirty; pass; check _(id: [rec-41c4aff8-877d-449c-8d7d-a9f99470d5ac](.artifacts/records/project__check-run/rec-41c4aff8-877d-449c-8d7d-a9f99470d5ac.md))_

## atomic-claims-review

### Check
- **atomic-claims-review**: atomic-claims-review; 3b2f808f60f93b4db108543986be05d184226566; fail; review _(id: [rec-160ce198-ea6b-4418-9329-aefcbd6138a2](.artifacts/records/project__check-run/rec-160ce198-ea6b-4418-9329-aefcbd6138a2.md))_
- **atomic-claims-review**: atomic-claims-review; 50303893af61c747620551cd512239752b0528a1; pass; review _(id: [rec-281ddc89-16a9-41b9-83b4-3006a379573e](.artifacts/records/project__check-run/rec-281ddc89-16a9-41b9-83b4-3006a379573e.md))_
- **atomic-claims-review**: atomic-claims-review; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; review _(id: [rec-f8d76458-5ced-4219-bf3e-eb6c22207c04](.artifacts/records/project__check-run/rec-f8d76458-5ced-4219-bf3e-eb6c22207c04.md))_

## atomic-claims-suite

### Check
- **atomic-claims-suite**: atomic-claims-suite; 50303893af61c747620551cd512239752b0528a1; fail; check _(id: [rec-f6e34bd6-bdf4-4fa8-a9c6-bca44fcfa0ef](.artifacts/records/project__check-run/rec-f6e34bd6-bdf4-4fa8-a9c6-bca44fcfa0ef.md))_

## backlog-lifecycle

### Acceptance
- **backlog-lifecycle**: R3; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_backlog_item.py -q _(id: [rec-fc666597-85d7-42c1-a7e9-3f67d996e0c2](.artifacts/records/project__acceptance/rec-fc666597-85d7-42c1-a7e9-3f67d996e0c2.md))_

### Check
- **backlog-lifecycle**: rec-fc666597-85d7-42c1-a7e9-3f67d996e0c2; 0f7181ef59251f8135db5a71258471f92a972e7c; pass; tdd _(id: [rec-2dd9b20c-e93b-47b5-bd83-b464826e2221](.artifacts/records/project__check-run/rec-2dd9b20c-e93b-47b5-bd83-b464826e2221.md))_

## backlog-lifecycle-promote

### Acceptance
- **backlog-lifecycle-promote**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_backlog_item.py -q _(id: [rec-a19b9909-b798-4b7d-a0e1-c2eac876dc42](.artifacts/records/project__acceptance/rec-a19b9909-b798-4b7d-a0e1-c2eac876dc42.md))_

### Check
- **backlog-lifecycle-promote**: rec-a19b9909-b798-4b7d-a0e1-c2eac876dc42; 0f7181ef59251f8135db5a71258471f92a972e7c; pass; tdd _(id: [rec-9c7db177-6ef9-41d0-87e7-c2d124d1cd8d](.artifacts/records/project__check-run/rec-9c7db177-6ef9-41d0-87e7-c2d124d1cd8d.md))_

## backlog-lifecycle-status

### Acceptance
- **backlog-lifecycle-status**: R4; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_backlog_item.py -q _(id: [rec-f5bbe8ab-d0e6-4929-9293-f23518096569](.artifacts/records/project__acceptance/rec-f5bbe8ab-d0e6-4929-9293-f23518096569.md))_

### Check
- **backlog-lifecycle-status**: rec-f5bbe8ab-d0e6-4929-9293-f23518096569; 0f7181ef59251f8135db5a71258471f92a972e7c; pass; tdd _(id: [rec-a90020f0-ba81-4c5a-8b9a-ed62eb58e42d](.artifacts/records/project__check-run/rec-a90020f0-ba81-4c5a-8b9a-ed62eb58e42d.md))_

## budget-instructions

### Acceptance
- **budget-instructions**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py -q -k plan_phase_limits _(id: [rec-b147b60a-bac3-473f-bff5-6ea8db7fe2e9](.artifacts/records/project__acceptance/rec-b147b60a-bac3-473f-bff5-6ea8db7fe2e9.md))_

### Check
- **budget-instructions**: rec-b147b60a-bac3-473f-bff5-6ea8db7fe2e9; dirty; pass; tdd _(id: [rec-6d98b2c8-3812-46a3-9f47-2fc4de4481b3](.artifacts/records/project__check-run/rec-6d98b2c8-3812-46a3-9f47-2fc4de4481b3.md))_
- **budget-instructions**: rec-b147b60a-bac3-473f-bff5-6ea8db7fe2e9; dirty; pass; tdd _(id: [rec-9c88f0a0-58dd-430d-a412-71eb101b857a](.artifacts/records/project__check-run/rec-9c88f0a0-58dd-430d-a412-71eb101b857a.md))_
- **budget-instructions**: rec-b147b60a-bac3-473f-bff5-6ea8db7fe2e9; dirty; fail; tdd _(id: [rec-e1f51bc9-28f4-4b19-8688-95beb25889da](.artifacts/records/project__check-run/rec-e1f51bc9-28f4-4b19-8688-95beb25889da.md))_

## budget-instructions-close

### Acceptance
- **budget-instructions-close**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py -q -k close_instructions _(id: [rec-a12edd10-9c55-4760-b80f-7fc1177203da](.artifacts/records/project__acceptance/rec-a12edd10-9c55-4760-b80f-7fc1177203da.md))_

### Check
- **budget-instructions-close**: rec-a12edd10-9c55-4760-b80f-7fc1177203da; dirty; fail; tdd _(id: [rec-3159ba4a-f165-4735-af54-c4cdcfde42c7](.artifacts/records/project__check-run/rec-3159ba4a-f165-4735-af54-c4cdcfde42c7.md))_
- **budget-instructions-close**: rec-a12edd10-9c55-4760-b80f-7fc1177203da; dirty; pass; tdd _(id: [rec-c6f6deee-7dc9-4fc4-84fb-5eacb6fd6fe2](.artifacts/records/project__check-run/rec-c6f6deee-7dc9-4fc4-84fb-5eacb6fd6fe2.md))_

## budget-instructions-filter

### Acceptance
- **budget-instructions-filter**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py -q -k rejects_whole_suite _(id: [rec-61d66067-90f5-4d51-b24b-0afb76d408d1](.artifacts/records/project__acceptance/rec-61d66067-90f5-4d51-b24b-0afb76d408d1.md))_

### Check
- **budget-instructions-filter**: rec-61d66067-90f5-4d51-b24b-0afb76d408d1; dirty; fail; tdd _(id: [rec-8e14fedd-1a87-4a4e-be22-58e54814ed18](.artifacts/records/project__check-run/rec-8e14fedd-1a87-4a4e-be22-58e54814ed18.md))_
- **budget-instructions-filter**: rec-61d66067-90f5-4d51-b24b-0afb76d408d1; dirty; pass; tdd _(id: [rec-db43ba29-89a6-4655-b28b-22924b54d289](.artifacts/records/project__check-run/rec-db43ba29-89a6-4655-b28b-22924b54d289.md))_

## budget-instructions-stop

### Acceptance
- **budget-instructions-stop**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py -q -k verification_failure _(id: [rec-4c85a8d1-dde4-448b-bfe6-aee86654a15e](.artifacts/records/project__acceptance/rec-4c85a8d1-dde4-448b-bfe6-aee86654a15e.md))_

### Check
- **budget-instructions-stop**: rec-4c85a8d1-dde4-448b-bfe6-aee86654a15e; dirty; pass; tdd _(id: [rec-0c637640-3452-4958-b7df-c94c2c43ca43](.artifacts/records/project__check-run/rec-0c637640-3452-4958-b7df-c94c2c43ca43.md))_
- **budget-instructions-stop**: rec-4c85a8d1-dde4-448b-bfe6-aee86654a15e; dirty; pass; tdd _(id: [rec-5a6a0868-84bc-4a9f-bc50-5d2304feb0dd](.artifacts/records/project__check-run/rec-5a6a0868-84bc-4a9f-bc50-5d2304feb0dd.md))_
- **budget-instructions-stop**: rec-4c85a8d1-dde4-448b-bfe6-aee86654a15e; dirty; fail; tdd _(id: [rec-ef3f591d-b275-455e-b7eb-4b4e227cdbc1](.artifacts/records/project__check-run/rec-ef3f591d-b275-455e-b7eb-4b4e227cdbc1.md))_

## check-run-contract

### Acceptance
- **check-run-contract**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py tests/test_evidence_loop.py tests/test_assess_routing.py -q -k 'enum or result or method or contract' _(id: [rec-88363d0c-d058-4a0d-8c04-4a697bbe457d](.artifacts/records/project__acceptance/rec-88363d0c-d058-4a0d-8c04-4a697bbe457d.md))_

### Check
- **check-run-contract**: rec-88363d0c-d058-4a0d-8c04-4a697bbe457d; 16c24e78d806d5207ee2c37a9418e828521f8389; pass; tdd _(id: [rec-06babb10-72f2-4c7c-8ef8-285ebdef0f15](.artifacts/records/project__check-run/rec-06babb10-72f2-4c7c-8ef8-285ebdef0f15.md))_

## claim-clocks-review

### Check
- **claim-clocks-review**: claim-clocks-review; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; review _(id: [rec-bd6e09e1-0813-42ca-8542-437ccbf9a7ab](.artifacts/records/project__check-run/rec-bd6e09e1-0813-42ca-8542-437ccbf9a7ab.md))_

## claim-gate-clocks-both

### Acceptance
- **claim-gate-clocks-both**: R7; tdd; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_both_failures_name_both -q _(id: [rec-432334a4-f932-4592-9c38-06db287a2bc7](.artifacts/records/project__acceptance/rec-432334a4-f932-4592-9c38-06db287a2bc7.md))_

### Check
- **claim-gate-clocks-both**: rec-432334a4-f932-4592-9c38-06db287a2bc7; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; tdd _(id: [rec-150d0e8b-4c59-4bc5-95d5-2221c1cc6db5](.artifacts/records/project__check-run/rec-150d0e8b-4c59-4bc5-95d5-2221c1cc6db5.md))_
- **claim-gate-clocks-both**: rec-432334a4-f932-4592-9c38-06db287a2bc7; 0eeb43affeac04a97c98250569a39cac9ab779a8; pass; tdd _(id: [rec-30f8598f-01a9-4bcd-ae8a-b083d53b9790](.artifacts/records/project__check-run/rec-30f8598f-01a9-4bcd-ae8a-b083d53b9790.md))_
- **claim-gate-clocks-both**: rec-432334a4-f932-4592-9c38-06db287a2bc7; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; tdd _(id: [rec-eab80a8e-6688-4f4a-b531-b0471259edd5](.artifacts/records/project__check-run/rec-eab80a8e-6688-4f4a-b531-b0471259edd5.md))_
- **claim-gate-clocks-both**: rec-432334a4-f932-4592-9c38-06db287a2bc7; ee99dc40a59190f169f510bb16f2f44750f63f8b; fail; tdd _(id: [rec-f5070312-d379-441a-b6e6-ea6b2965d016](.artifacts/records/project__check-run/rec-f5070312-d379-441a-b6e6-ea6b2965d016.md))_

## claim-gate-clocks-recheck

### Acceptance
- **claim-gate-clocks-recheck**: R4; check; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_recheck_runs_for_claim -q _(id: [rec-8ab53d48-b718-4b23-8662-92a347813022](.artifacts/records/project__acceptance/rec-8ab53d48-b718-4b23-8662-92a347813022.md))_

### Check
- **claim-gate-clocks-recheck**: rec-8ab53d48-b718-4b23-8662-92a347813022; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-695f6ab1-eeaf-4745-8a1a-6c893431ae2e](.artifacts/records/project__check-run/rec-695f6ab1-eeaf-4745-8a1a-6c893431ae2e.md))_
- **claim-gate-clocks-recheck**: rec-8ab53d48-b718-4b23-8662-92a347813022; 0eeb43affeac04a97c98250569a39cac9ab779a8; pass; check _(id: [rec-7873e88f-844f-45ac-a258-d70f5a0b13fb](.artifacts/records/project__check-run/rec-7873e88f-844f-45ac-a258-d70f5a0b13fb.md))_
- **claim-gate-clocks-recheck**: rec-8ab53d48-b718-4b23-8662-92a347813022; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-9c640100-2f39-4158-b526-38a621e9b7e7](.artifacts/records/project__check-run/rec-9c640100-2f39-4158-b526-38a621e9b7e7.md))_

## claim-gate-clocks-recheck-only

### Acceptance
- **claim-gate-clocks-recheck-only**: R6; check; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_recheck_only_failure_names_recheck -q _(id: [rec-8bdcbaad-032e-4f37-a08c-716708bacad5](.artifacts/records/project__acceptance/rec-8bdcbaad-032e-4f37-a08c-716708bacad5.md))_

### Check
- **claim-gate-clocks-recheck-only**: rec-8bdcbaad-032e-4f37-a08c-716708bacad5; 0eeb43affeac04a97c98250569a39cac9ab779a8; pass; check _(id: [rec-22e7b3b8-e657-4a3a-ae74-910165fb98c0](.artifacts/records/project__check-run/rec-22e7b3b8-e657-4a3a-ae74-910165fb98c0.md))_
- **claim-gate-clocks-recheck-only**: rec-8bdcbaad-032e-4f37-a08c-716708bacad5; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-a5899bb4-9734-49fa-96c5-af70129da118](.artifacts/records/project__check-run/rec-a5899bb4-9734-49fa-96c5-af70129da118.md))_
- **claim-gate-clocks-recheck-only**: rec-8bdcbaad-032e-4f37-a08c-716708bacad5; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-da814626-5f89-47bd-b242-c74ae519aae2](.artifacts/records/project__check-run/rec-da814626-5f89-47bd-b242-c74ae519aae2.md))_

## claim-gate-clocks-verdict

### Acceptance
- **claim-gate-clocks-verdict**: R3; check; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_verdict_runs_at_green_revision -q _(id: [rec-e6afa1ae-62e4-404f-8881-cb486a1e0c59](.artifacts/records/project__acceptance/rec-e6afa1ae-62e4-404f-8881-cb486a1e0c59.md))_

### Check
- **claim-gate-clocks-verdict**: rec-e6afa1ae-62e4-404f-8881-cb486a1e0c59; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-8f5bed2a-9265-484b-929a-a9d822764a4b](.artifacts/records/project__check-run/rec-8f5bed2a-9265-484b-929a-a9d822764a4b.md))_
- **claim-gate-clocks-verdict**: rec-e6afa1ae-62e4-404f-8881-cb486a1e0c59; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-c2211206-5ec1-4909-8bd6-7a25cd47f5e8](.artifacts/records/project__check-run/rec-c2211206-5ec1-4909-8bd6-7a25cd47f5e8.md))_
- **claim-gate-clocks-verdict**: rec-e6afa1ae-62e4-404f-8881-cb486a1e0c59; 0eeb43affeac04a97c98250569a39cac9ab779a8; pass; check _(id: [rec-ed88270b-2b72-4556-8537-15701d2d6235](.artifacts/records/project__check-run/rec-ed88270b-2b72-4556-8537-15701d2d6235.md))_

## claim-gate-clocks-verdict-only

### Acceptance
- **claim-gate-clocks-verdict-only**: R5; check; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_verdict_only_failure_names_verdict -q _(id: [rec-4e6bb722-1c42-4e77-a12d-6af44ce9f400](.artifacts/records/project__acceptance/rec-4e6bb722-1c42-4e77-a12d-6af44ce9f400.md))_

### Check
- **claim-gate-clocks-verdict-only**: rec-4e6bb722-1c42-4e77-a12d-6af44ce9f400; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-297a01f2-c9af-4a4b-8bc7-8c293555c9c9](.artifacts/records/project__check-run/rec-297a01f2-c9af-4a4b-8bc7-8c293555c9c9.md))_
- **claim-gate-clocks-verdict-only**: rec-4e6bb722-1c42-4e77-a12d-6af44ce9f400; 0eeb43affeac04a97c98250569a39cac9ab779a8; pass; check _(id: [rec-604b3afa-7b7a-462d-a7d9-1c16a7c77166](.artifacts/records/project__check-run/rec-604b3afa-7b7a-462d-a7d9-1c16a7c77166.md))_
- **claim-gate-clocks-verdict-only**: rec-4e6bb722-1c42-4e77-a12d-6af44ce9f400; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-89198385-8565-41a1-bdaf-0e737665571d](.artifacts/records/project__check-run/rec-89198385-8565-41a1-bdaf-0e737665571d.md))_

## claim-gate-close

### Acceptance
- **claim-gate-close**: R5; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py::test_claim_gate_refuses_done_when_aff_verdict_nonzero -q _(id: [rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a](.artifacts/records/project__acceptance/rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a.md))_

### Check
- **claim-gate-close**: rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a; 61b77e4f1958556f05a740269859441df8726e10; fail; tdd _(id: [rec-0e7b2ecf-4181-4ddc-b346-0bc5da3e9e0d](.artifacts/records/project__check-run/rec-0e7b2ecf-4181-4ddc-b346-0bc5da3e9e0d.md))_
- **claim-gate-close**: rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a; 51cd740b7588ae41ef9a50360d992d6995d1e09d; fail; tdd _(id: [rec-17bd3720-c0c6-4f02-a813-1d3cba67b51e](.artifacts/records/project__check-run/rec-17bd3720-c0c6-4f02-a813-1d3cba67b51e.md))_
- **claim-gate-close**: rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a; dirty; fail; tdd _(id: [rec-1eebaf48-7b0a-4999-b4d5-825fa67b44ee](.artifacts/records/project__check-run/rec-1eebaf48-7b0a-4999-b4d5-825fa67b44ee.md))_
- **claim-gate-close**: rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-2d637fac-d590-44ed-a120-bc314030eb90](.artifacts/records/project__check-run/rec-2d637fac-d590-44ed-a120-bc314030eb90.md))_
- **claim-gate-close**: rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-4e2207ac-3d88-4ebb-becc-efc19a227045](.artifacts/records/project__check-run/rec-4e2207ac-3d88-4ebb-becc-efc19a227045.md))_
- **claim-gate-close**: rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-8c54c22a-c4e0-4258-b681-fb86cdc38463](.artifacts/records/project__check-run/rec-8c54c22a-c4e0-4258-b681-fb86cdc38463.md))_
- **claim-gate-close**: rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-c0d70dda-d892-41f2-940f-5f0dd427725e](.artifacts/records/project__check-run/rec-c0d70dda-d892-41f2-940f-5f0dd427725e.md))_

## claim-gate-close-recheck

### Acceptance
- **claim-gate-close-recheck**: R6; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py::test_claim_gate_refuses_done_when_aff_recheck_nonzero -q _(id: [rec-feea1426-6af8-4732-8e6b-431eb5331240](.artifacts/records/project__acceptance/rec-feea1426-6af8-4732-8e6b-431eb5331240.md))_

### Check
- **claim-gate-close-recheck**: rec-feea1426-6af8-4732-8e6b-431eb5331240; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-0cc1dadd-11ac-4718-9fce-9ae664beec94](.artifacts/records/project__check-run/rec-0cc1dadd-11ac-4718-9fce-9ae664beec94.md))_
- **claim-gate-close-recheck**: rec-feea1426-6af8-4732-8e6b-431eb5331240; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-15cb6665-0330-46cf-b741-967c4899e5fc](.artifacts/records/project__check-run/rec-15cb6665-0330-46cf-b741-967c4899e5fc.md))_
- **claim-gate-close-recheck**: rec-feea1426-6af8-4732-8e6b-431eb5331240; dirty; fail; tdd _(id: [rec-2a4009d4-1326-4b6f-8f08-56ae44e59ace](.artifacts/records/project__check-run/rec-2a4009d4-1326-4b6f-8f08-56ae44e59ace.md))_
- **claim-gate-close-recheck**: rec-feea1426-6af8-4732-8e6b-431eb5331240; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-6b760a48-7aba-4104-a2d3-8f75f05a263a](.artifacts/records/project__check-run/rec-6b760a48-7aba-4104-a2d3-8f75f05a263a.md))_
- **claim-gate-close-recheck**: rec-feea1426-6af8-4732-8e6b-431eb5331240; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-854e3225-e40a-492f-8281-432f746b650c](.artifacts/records/project__check-run/rec-854e3225-e40a-492f-8281-432f746b650c.md))_
- **claim-gate-close-recheck**: rec-feea1426-6af8-4732-8e6b-431eb5331240; 61b77e4f1958556f05a740269859441df8726e10; fail; tdd _(id: [rec-8878c64c-ee99-4dbd-8df7-f15580216198](.artifacts/records/project__check-run/rec-8878c64c-ee99-4dbd-8df7-f15580216198.md))_
- **claim-gate-close-recheck**: rec-feea1426-6af8-4732-8e6b-431eb5331240; 51cd740b7588ae41ef9a50360d992d6995d1e09d; fail; tdd _(id: [rec-fbfaf22d-0ff4-40aa-b0b4-04af91618d19](.artifacts/records/project__check-run/rec-fbfaf22d-0ff4-40aa-b0b4-04af91618d19.md))_

## claim-gate-source

### Acceptance
- **claim-gate-source**: R1; tdd; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_claim_id_read_only_from_payload_claim -q _(id: [rec-cc03c990-7e5c-4647-b54b-e1adedb8e479](.artifacts/records/project__acceptance/rec-cc03c990-7e5c-4647-b54b-e1adedb8e479.md))_

### Check
- **claim-gate-source**: rec-cc03c990-7e5c-4647-b54b-e1adedb8e479; ee99dc40a59190f169f510bb16f2f44750f63f8b; fail; tdd _(id: [rec-212f2086-7caf-4a08-8cdd-42c4eea1400a](.artifacts/records/project__check-run/rec-212f2086-7caf-4a08-8cdd-42c4eea1400a.md))_
- **claim-gate-source**: rec-cc03c990-7e5c-4647-b54b-e1adedb8e479; 6a284525302f6b39e634dee115e78e89d3aebf2a; pass; tdd _(id: [rec-6a056e9b-a304-45b6-a2af-74f847338d29](.artifacts/records/project__check-run/rec-6a056e9b-a304-45b6-a2af-74f847338d29.md))_
- **claim-gate-source**: rec-cc03c990-7e5c-4647-b54b-e1adedb8e479; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; tdd _(id: [rec-8bba5662-9a12-4483-8cb3-b82e67b42c20](.artifacts/records/project__check-run/rec-8bba5662-9a12-4483-8cb3-b82e67b42c20.md))_
- **claim-gate-source**: rec-cc03c990-7e5c-4647-b54b-e1adedb8e479; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; tdd _(id: [rec-943c22ca-3c87-49c5-a194-67935d251608](.artifacts/records/project__check-run/rec-943c22ca-3c87-49c5-a194-67935d251608.md))_

## claim-gate-source-empty

### Acceptance
- **claim-gate-source-empty**: R2; tdd; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_empty_claim_is_not_gated -q _(id: [rec-44d6f376-b9db-44a0-abf1-a069f90adbaf](.artifacts/records/project__acceptance/rec-44d6f376-b9db-44a0-abf1-a069f90adbaf.md))_

### Check
- **claim-gate-source-empty**: rec-44d6f376-b9db-44a0-abf1-a069f90adbaf; ee99dc40a59190f169f510bb16f2f44750f63f8b; fail; tdd _(id: [rec-26e0a527-3cd2-4856-970d-6221f288b877](.artifacts/records/project__check-run/rec-26e0a527-3cd2-4856-970d-6221f288b877.md))_
- **claim-gate-source-empty**: rec-44d6f376-b9db-44a0-abf1-a069f90adbaf; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; tdd _(id: [rec-37994da3-a534-4654-a1ee-7535740e1fa2](.artifacts/records/project__check-run/rec-37994da3-a534-4654-a1ee-7535740e1fa2.md))_
- **claim-gate-source-empty**: rec-44d6f376-b9db-44a0-abf1-a069f90adbaf; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; tdd _(id: [rec-404ff413-425b-4fbd-ac68-44a72dda2a18](.artifacts/records/project__check-run/rec-404ff413-425b-4fbd-ac68-44a72dda2a18.md))_
- **claim-gate-source-empty**: rec-44d6f376-b9db-44a0-abf1-a069f90adbaf; 6a284525302f6b39e634dee115e78e89d3aebf2a; pass; tdd _(id: [rec-8bc569ff-caed-4fce-a01e-6eb3a4e2cfa1](.artifacts/records/project__check-run/rec-8bc569ff-caed-4fce-a01e-6eb3a4e2cfa1.md))_

## claim-gate-source-missing

### Acceptance
- **claim-gate-source-missing**: R8; tdd; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_missing_acceptance_refuses -q _(id: [rec-d6885b67-904c-44af-96f1-d8a64c5fd613](.artifacts/records/project__acceptance/rec-d6885b67-904c-44af-96f1-d8a64c5fd613.md))_

### Check
- **claim-gate-source-missing**: rec-d6885b67-904c-44af-96f1-d8a64c5fd613; 6a284525302f6b39e634dee115e78e89d3aebf2a; pass; tdd _(id: [rec-4ffdebd0-890d-419b-a24f-ec77c8b50eab](.artifacts/records/project__check-run/rec-4ffdebd0-890d-419b-a24f-ec77c8b50eab.md))_
- **claim-gate-source-missing**: rec-d6885b67-904c-44af-96f1-d8a64c5fd613; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; tdd _(id: [rec-75283a6f-c4a8-4691-b79e-e9d7a4835e0b](.artifacts/records/project__check-run/rec-75283a6f-c4a8-4691-b79e-e9d7a4835e0b.md))_
- **claim-gate-source-missing**: rec-d6885b67-904c-44af-96f1-d8a64c5fd613; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; tdd _(id: [rec-76e38997-3f86-498f-9cd4-2938d7da2d9d](.artifacts/records/project__check-run/rec-76e38997-3f86-498f-9cd4-2938d7da2d9d.md))_
- **claim-gate-source-missing**: rec-d6885b67-904c-44af-96f1-d8a64c5fd613; ee99dc40a59190f169f510bb16f2f44750f63f8b; fail; tdd _(id: [rec-d9e5d9a1-a505-4a15-9c70-488bb13e15bf](.artifacts/records/project__check-run/rec-d9e5d9a1-a505-4a15-9c70-488bb13e15bf.md))_

## claim-gate-source-unknown

### Acceptance
- **claim-gate-source-unknown**: R9; tdd; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_unknown_claim_refuses -q _(id: [rec-0c3ee26a-b508-46c3-89b3-9fbbee3dd657](.artifacts/records/project__acceptance/rec-0c3ee26a-b508-46c3-89b3-9fbbee3dd657.md))_

### Check
- **claim-gate-source-unknown**: rec-0c3ee26a-b508-46c3-89b3-9fbbee3dd657; 6a284525302f6b39e634dee115e78e89d3aebf2a; pass; tdd _(id: [rec-2f31b85c-ad44-471c-8d9c-d14a8ee7d19c](.artifacts/records/project__check-run/rec-2f31b85c-ad44-471c-8d9c-d14a8ee7d19c.md))_
- **claim-gate-source-unknown**: rec-0c3ee26a-b508-46c3-89b3-9fbbee3dd657; ee99dc40a59190f169f510bb16f2f44750f63f8b; fail; tdd _(id: [rec-31c31d77-7d55-47a7-833a-cb41c5ea31fd](.artifacts/records/project__check-run/rec-31c31d77-7d55-47a7-833a-cb41c5ea31fd.md))_
- **claim-gate-source-unknown**: rec-0c3ee26a-b508-46c3-89b3-9fbbee3dd657; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; tdd _(id: [rec-64bb6c70-a482-4918-bc1e-708cce69e0b8](.artifacts/records/project__check-run/rec-64bb6c70-a482-4918-bc1e-708cce69e0b8.md))_
- **claim-gate-source-unknown**: rec-0c3ee26a-b508-46c3-89b3-9fbbee3dd657; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; tdd _(id: [rec-a46fd2f3-73c1-45fb-bdc5-25af4fc0ce9b](.artifacts/records/project__check-run/rec-a46fd2f3-73c1-45fb-bdc5-25af4fc0ce9b.md))_

## claim-witnesses-review

### Check
- **claim-witnesses-review**: claim-witnesses-review; d680521c3270c954d22b915c641c7e733595599f; pass; review _(id: [rec-86b5d648-38c1-458c-a821-a727cb4028e0](.artifacts/records/project__check-run/rec-86b5d648-38c1-458c-a821-a727cb4028e0.md))_

## claim-witnesses-suite

### Check
- **claim-witnesses-suite**: claim-witnesses-suite; d680521c3270c954d22b915c641c7e733595599f; fail; check _(id: [rec-988c5595-f0ea-4bef-b5c1-8bf881e4b72e](.artifacts/records/project__check-run/rec-988c5595-f0ea-4bef-b5c1-8bf881e4b72e.md))_

## claude-shared-marketplace

### Acceptance
- **claude-shared-marketplace**: R1; check; packaging; claude plugin validate . && python3 -c "import json;p=json.load(open('.claude-plugin/plugin.json'));d=p.get('dependencies',[]);assert 'adaptive-artifacts' in d or any(isinstance(x,dict) and x.get('name')=='adaptive-artifacts' for x in d);m=json.load(open('.claude-plugin/marketplace.json'));assert {x.get('name') for x in m['plugins']}>= {'se-workflow','adaptive-artifacts'}" _(id: [rec-a60c0f0a-abb6-4cfe-b569-657d0edb4722](.artifacts/records/project__acceptance/rec-a60c0f0a-abb6-4cfe-b569-657d0edb4722.md))_

### Check
- **claude-shared-marketplace**: rec-a60c0f0a-abb6-4cfe-b569-657d0edb4722; 40db2970236ac7ff04afd9eaf08292f072a912a2; pass; check _(id: [rec-133596a3-9698-4c2b-aeaa-ae7ab76e82f5](.artifacts/records/project__check-run/rec-133596a3-9698-4c2b-aeaa-ae7ab76e82f5.md))_

## claude-shared-marketplace-readme

### Acceptance
- **claude-shared-marketplace-readme**: R4; check; packaging; grep -q 'claude plugin marketplace add andrewy1n/se-workflow' README.md && grep -qi Cursor README.md && ! grep -qiE 'Cursor.*(auto-?install|plugin dependenc).*adaptive-artifacts' README.md _(id: [rec-49384b6f-6de8-4e22-b43c-f27f3e8f06ad](.artifacts/records/project__acceptance/rec-49384b6f-6de8-4e22-b43c-f27f3e8f06ad.md))_

### Check
- **claude-shared-marketplace-readme**: rec-49384b6f-6de8-4e22-b43c-f27f3e8f06ad; 40db2970236ac7ff04afd9eaf08292f072a912a2; pass; check _(id: [rec-afd46d92-057c-4b40-8961-34c19871e95d](.artifacts/records/project__check-run/rec-afd46d92-057c-4b40-8961-34c19871e95d.md))_

## cli-package

### Acceptance
- **cli-package**: R5; check; packaging; python3 -m pytest tests/test_cli_packaging.py -q -k path _(id: [rec-9ffe3fb9-03cc-47ac-a3a2-186887e34afd](.artifacts/records/project__acceptance/rec-9ffe3fb9-03cc-47ac-a3a2-186887e34afd.md))_

### Check
- **cli-package**: rec-9ffe3fb9-03cc-47ac-a3a2-186887e34afd; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-3c484689-8c21-4e0b-b41e-29bf0010584f](.artifacts/records/project__check-run/rec-3c484689-8c21-4e0b-b41e-29bf0010584f.md))_
- **cli-package**: rec-9ffe3fb9-03cc-47ac-a3a2-186887e34afd; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-84bcdf35-a0bf-46da-810e-8ddeafdbccae](.artifacts/records/project__check-run/rec-84bcdf35-a0bf-46da-810e-8ddeafdbccae.md))_
- **cli-package**: rec-9ffe3fb9-03cc-47ac-a3a2-186887e34afd; b4fc77a1a125f0526d9941a374d0c633886a6b96; pass; check _(id: [rec-9643824e-a156-43a9-9331-d53a008f2373](.artifacts/records/project__check-run/rec-9643824e-a156-43a9-9331-d53a008f2373.md))_

## cli-package-subcommands

### Acceptance
- **cli-package-subcommands**: R7; check; packaging; python3 -m pytest tests/test_cli_packaging.py -q -k subcommands _(id: [rec-813d0fb9-e4f2-4b91-8d62-c995948029de](.artifacts/records/project__acceptance/rec-813d0fb9-e4f2-4b91-8d62-c995948029de.md))_

### Check
- **cli-package-subcommands**: rec-813d0fb9-e4f2-4b91-8d62-c995948029de; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-29793863-33be-4d51-81c3-72db88466c12](.artifacts/records/project__check-run/rec-29793863-33be-4d51-81c3-72db88466c12.md))_
- **cli-package-subcommands**: rec-813d0fb9-e4f2-4b91-8d62-c995948029de; b4fc77a1a125f0526d9941a374d0c633886a6b96; pass; check _(id: [rec-4c93bf99-abc5-45f7-8a2d-6b2a680f1745](.artifacts/records/project__check-run/rec-4c93bf99-abc5-45f7-8a2d-6b2a680f1745.md))_
- **cli-package-subcommands**: rec-813d0fb9-e4f2-4b91-8d62-c995948029de; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-b97fed16-844d-4956-9877-6b2b65803558](.artifacts/records/project__check-run/rec-b97fed16-844d-4956-9877-6b2b65803558.md))_

## close-batch-cli

### Acceptance
- **close-batch-cli**: R3; tdd; packaging; uv run --with pytest python -m pytest tests/test_close_batch.py -q _(id: [rec-45b51bb0-0c79-4f85-9120-374742d1d297](.artifacts/records/project__acceptance/rec-45b51bb0-0c79-4f85-9120-374742d1d297.md))_

### Check
- **close-batch-cli**: rec-45b51bb0-0c79-4f85-9120-374742d1d297; dirty; fail; tdd _(id: [rec-644ce7a2-d954-465f-bb8c-f2899f253d92](.artifacts/records/project__check-run/rec-644ce7a2-d954-465f-bb8c-f2899f253d92.md))_
- **close-batch-cli**: rec-45b51bb0-0c79-4f85-9120-374742d1d297; 23c6f922d2a051135dc323f67924f2364b3788db; pass; tdd _(id: [rec-7637c340-cead-4240-9940-0a3c34093d3f](.artifacts/records/project__check-run/rec-7637c340-cead-4240-9940-0a3c34093d3f.md))_

## close-batch-store-verify

### Acceptance
- **close-batch-store-verify**: R1; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'store_authority or fabricated or mismatch' -q _(id: [rec-a4a45232-6634-47b1-bbaf-11633085234e](.artifacts/records/project__acceptance/rec-a4a45232-6634-47b1-bbaf-11633085234e.md))_

### Check
- **close-batch-store-verify**: rec-a4a45232-6634-47b1-bbaf-11633085234e; 947727b37d2e06a54a999103564c6a17b479f1de; fail; tdd _(id: [rec-0fe85e44-3f3b-41b7-b9d5-9eb11a1598a0](.artifacts/records/project__check-run/rec-0fe85e44-3f3b-41b7-b9d5-9eb11a1598a0.md))_
- **close-batch-store-verify**: rec-a4a45232-6634-47b1-bbaf-11633085234e; 947727b37d2e06a54a999103564c6a17b479f1de; fail; tdd _(id: [rec-2c0921e5-a03b-476c-bdad-808e6aa1869f](.artifacts/records/project__check-run/rec-2c0921e5-a03b-476c-bdad-808e6aa1869f.md))_
- **close-batch-store-verify**: rec-a4a45232-6634-47b1-bbaf-11633085234e; dirty; fail; tdd _(id: [rec-67d02bcd-6f63-46b9-ae30-afeddad6f3b6](.artifacts/records/project__check-run/rec-67d02bcd-6f63-46b9-ae30-afeddad6f3b6.md))_
- **close-batch-store-verify**: rec-a4a45232-6634-47b1-bbaf-11633085234e; dirty; fail; tdd _(id: [rec-bfe587a4-e52d-4223-8a38-5ef1c13060fa](.artifacts/records/project__check-run/rec-bfe587a4-e52d-4223-8a38-5ef1c13060fa.md))_
- **close-batch-store-verify**: rec-a4a45232-6634-47b1-bbaf-11633085234e; 1ca2b0676e8ba8febf2daf9cd8f98a4d2442a61f; pass; tdd _(id: [rec-d10d3440-6de3-435a-a886-2abdb2448572](.artifacts/records/project__check-run/rec-d10d3440-6de3-435a-a886-2abdb2448572.md))_
- **close-batch-store-verify**: rec-a4a45232-6634-47b1-bbaf-11633085234e; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-ff6c3257-ad8b-4494-8ca0-065d296b6043](.artifacts/records/project__check-run/rec-ff6c3257-ad8b-4494-8ca0-065d296b6043.md))_

## close-batch-store-verify-missing

### Acceptance
- **close-batch-store-verify-missing**: R4; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'missing_check_run_id or missing_result or result_optional' -q _(id: [rec-3c86fb99-228d-40b6-99f7-5d48aa05de37](.artifacts/records/project__acceptance/rec-3c86fb99-228d-40b6-99f7-5d48aa05de37.md))_

### Check
- **close-batch-store-verify-missing**: rec-3c86fb99-228d-40b6-99f7-5d48aa05de37; 947727b37d2e06a54a999103564c6a17b479f1de; fail; tdd _(id: [rec-7d02684a-510a-41ac-b74f-42e55e0cfad7](.artifacts/records/project__check-run/rec-7d02684a-510a-41ac-b74f-42e55e0cfad7.md))_
- **close-batch-store-verify-missing**: rec-3c86fb99-228d-40b6-99f7-5d48aa05de37; 1ca2b0676e8ba8febf2daf9cd8f98a4d2442a61f; pass; tdd _(id: [rec-7d60c2a8-e65e-4e13-b407-490841e3684e](.artifacts/records/project__check-run/rec-7d60c2a8-e65e-4e13-b407-490841e3684e.md))_
- **close-batch-store-verify-missing**: rec-3c86fb99-228d-40b6-99f7-5d48aa05de37; dirty; fail; tdd _(id: [rec-cd58fdd4-9eef-424d-a4c8-b1c42a9093cb](.artifacts/records/project__check-run/rec-cd58fdd4-9eef-424d-a4c8-b1c42a9093cb.md))_
- **close-batch-store-verify-missing**: rec-3c86fb99-228d-40b6-99f7-5d48aa05de37; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-d8450a84-74c8-4945-8e81-f3ecfb76f9e6](.artifacts/records/project__check-run/rec-d8450a84-74c8-4945-8e81-f3ecfb76f9e6.md))_
- **close-batch-store-verify-missing**: rec-3c86fb99-228d-40b6-99f7-5d48aa05de37; dirty; fail; tdd _(id: [rec-eee23a4f-f816-4909-ac37-daf7b52446a2](.artifacts/records/project__check-run/rec-eee23a4f-f816-4909-ac37-daf7b52446a2.md))_

## close-batch-store-verify-red

### Acceptance
- **close-batch-store-verify-red**: R2; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'red_store or dirty_green or missing_green_revision' -q _(id: [rec-3fd581e7-7b66-4e35-9f7d-174b45144862](.artifacts/records/project__acceptance/rec-3fd581e7-7b66-4e35-9f7d-174b45144862.md))_

### Check
- **close-batch-store-verify-red**: rec-3fd581e7-7b66-4e35-9f7d-174b45144862; 1ca2b0676e8ba8febf2daf9cd8f98a4d2442a61f; pass; tdd _(id: [rec-22edc17a-cab3-4029-83c1-74e2d635faf8](.artifacts/records/project__check-run/rec-22edc17a-cab3-4029-83c1-74e2d635faf8.md))_
- **close-batch-store-verify-red**: rec-3fd581e7-7b66-4e35-9f7d-174b45144862; 947727b37d2e06a54a999103564c6a17b479f1de; fail; tdd _(id: [rec-8ed56e4f-0c1e-4e58-b238-a37e1c6d74bb](.artifacts/records/project__check-run/rec-8ed56e4f-0c1e-4e58-b238-a37e1c6d74bb.md))_
- **close-batch-store-verify-red**: rec-3fd581e7-7b66-4e35-9f7d-174b45144862; dirty; fail; tdd _(id: [rec-96108f0c-a8d3-481a-90fe-16547ff56f95](.artifacts/records/project__check-run/rec-96108f0c-a8d3-481a-90fe-16547ff56f95.md))_
- **close-batch-store-verify-red**: rec-3fd581e7-7b66-4e35-9f7d-174b45144862; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-bdae3e95-4d02-4c59-9851-9445d5cdabe0](.artifacts/records/project__check-run/rec-bdae3e95-4d02-4c59-9851-9445d5cdabe0.md))_
- **close-batch-store-verify-red**: rec-3fd581e7-7b66-4e35-9f7d-174b45144862; dirty; fail; tdd _(id: [rec-ca809d75-2acd-4a1f-a96b-52a3dc63962a](.artifacts/records/project__check-run/rec-ca809d75-2acd-4a1f-a96b-52a3dc63962a.md))_

## close-batch-store-verify-revision

### Acceptance
- **close-batch-store-verify-revision**: R3; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'tdd_revision_without_red or revision_allowed_tdd' -q _(id: [rec-b97cbd55-140b-4868-8652-f4dda7f99ae8](.artifacts/records/project__acceptance/rec-b97cbd55-140b-4868-8652-f4dda7f99ae8.md))_

### Check
- **close-batch-store-verify-revision**: rec-b97cbd55-140b-4868-8652-f4dda7f99ae8; dirty; fail; tdd _(id: [rec-4d9f9cb3-23cb-41c9-8e01-3d6980298a12](.artifacts/records/project__check-run/rec-4d9f9cb3-23cb-41c9-8e01-3d6980298a12.md))_
- **close-batch-store-verify-revision**: rec-b97cbd55-140b-4868-8652-f4dda7f99ae8; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-8e91a2d8-5d02-4b3a-bfd0-36c34aca6957](.artifacts/records/project__check-run/rec-8e91a2d8-5d02-4b3a-bfd0-36c34aca6957.md))_
- **close-batch-store-verify-revision**: rec-b97cbd55-140b-4868-8652-f4dda7f99ae8; 947727b37d2e06a54a999103564c6a17b479f1de; fail; tdd _(id: [rec-b9153f80-684c-4145-bbda-6e104d1c8fe5](.artifacts/records/project__check-run/rec-b9153f80-684c-4145-bbda-6e104d1c8fe5.md))_
- **close-batch-store-verify-revision**: rec-b97cbd55-140b-4868-8652-f4dda7f99ae8; dirty; fail; tdd _(id: [rec-c6fdbea3-524c-4c2c-a3e8-5ac7b6a729f5](.artifacts/records/project__check-run/rec-c6fdbea3-524c-4c2c-a3e8-5ac7b6a729f5.md))_
- **close-batch-store-verify-revision**: rec-b97cbd55-140b-4868-8652-f4dda7f99ae8; 1ca2b0676e8ba8febf2daf9cd8f98a4d2442a61f; pass; tdd _(id: [rec-cc179d9e-1486-4c1e-92b2-7d80bf742243](.artifacts/records/project__check-run/rec-cc179d9e-1486-4c1e-92b2-7d80bf742243.md))_

## close-library

### Acceptance
- **close-library**: R5; tdd; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r5 -q _(id: [rec-8a58e738-d0bc-4b3c-b55d-88094659b4f4](.artifacts/records/project__acceptance/rec-8a58e738-d0bc-4b3c-b55d-88094659b4f4.md))_

### Check
- **close-library**: rec-8a58e738-d0bc-4b3c-b55d-88094659b4f4; cdcb9861c1b7f82caf097b00472d16f902d8d5b9; fail; tdd _(id: [rec-40c8a1c3-c8c1-46eb-ba0d-d408165bb205](.artifacts/records/project__check-run/rec-40c8a1c3-c8c1-46eb-ba0d-d408165bb205.md))_
- **close-library**: rec-8a58e738-d0bc-4b3c-b55d-88094659b4f4; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; tdd _(id: [rec-53f6559a-885a-45d8-934c-c02e40b6bf9f](.artifacts/records/project__check-run/rec-53f6559a-885a-45d8-934c-c02e40b6bf9f.md))_
- **close-library**: rec-8a58e738-d0bc-4b3c-b55d-88094659b4f4; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-93466c47-4a53-4680-92ad-1e147c468204](.artifacts/records/project__check-run/rec-93466c47-4a53-4680-92ad-1e147c468204.md))_

## close-library-help

### Acceptance
- **close-library-help**: R8; check; library-boundary; python3 -c 'import os,subprocess,sys,tempfile; from pathlib import Path; root=Path.cwd(); b=Path(tempfile.mkdtemp()); (b/"sitecustomize.py").write_text("import sys\nclass Block:\n def find_spec(self, name, path, target=None):\n  if name==\"affidavit\" or name.startswith(\"affidavit.\"):\n   raise ImportError(name)\n  return None\nsys.meta_path.insert(0, Block())\n"); env=os.environ.copy(); pp=env.get("PYTHONPATH",""); env["PYTHONPATH"]=str(b)+os.pathsep+str(root)+(os.pathsep+pp if pp else ""); p=subprocess.run([sys.executable, str(root/"bin"/"orchestra"), "--help"], cwd=root, env=env); raise SystemExit(p.returncode)' _(id: [rec-2d921ac1-c5a8-4cb7-aa43-ef57f0a16c2e](.artifacts/records/project__acceptance/rec-2d921ac1-c5a8-4cb7-aa43-ef57f0a16c2e.md))_

### Check
- **close-library-help**: rec-2d921ac1-c5a8-4cb7-aa43-ef57f0a16c2e; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; check _(id: [rec-03c37bec-03e7-451c-a539-9f22ee290f46](.artifacts/records/project__check-run/rec-03c37bec-03e7-451c-a539-9f22ee290f46.md))_
- **close-library-help**: rec-2d921ac1-c5a8-4cb7-aa43-ef57f0a16c2e; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; check _(id: [rec-04568437-14b3-4102-9702-3521e83d88f8](.artifacts/records/project__check-run/rec-04568437-14b3-4102-9702-3521e83d88f8.md))_

## close-library-missing

### Acceptance
- **close-library-missing**: R9; tdd; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r9 -q _(id: [rec-56c5cf71-8a5c-49c0-9331-a475932c2c42](.artifacts/records/project__acceptance/rec-56c5cf71-8a5c-49c0-9331-a475932c2c42.md))_

### Check
- **close-library-missing**: rec-56c5cf71-8a5c-49c0-9331-a475932c2c42; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-1f143775-78ef-495e-a31e-944aec984e9a](.artifacts/records/project__check-run/rec-1f143775-78ef-495e-a31e-944aec984e9a.md))_
- **close-library-missing**: rec-56c5cf71-8a5c-49c0-9331-a475932c2c42; cdcb9861c1b7f82caf097b00472d16f902d8d5b9; fail; tdd _(id: [rec-30122c21-ca22-454d-b9c7-f5890061c88a](.artifacts/records/project__check-run/rec-30122c21-ca22-454d-b9c7-f5890061c88a.md))_
- **close-library-missing**: rec-56c5cf71-8a5c-49c0-9331-a475932c2c42; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; tdd _(id: [rec-e861847a-7a1b-4a6f-94d2-19ed46907578](.artifacts/records/project__check-run/rec-e861847a-7a1b-4a6f-94d2-19ed46907578.md))_

## close-library-recheck

### Acceptance
- **close-library-recheck**: R7; tdd; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r7 -q _(id: [rec-60f10927-c3fc-4d5e-97b8-1533645d4081](.artifacts/records/project__acceptance/rec-60f10927-c3fc-4d5e-97b8-1533645d4081.md))_

### Check
- **close-library-recheck**: rec-60f10927-c3fc-4d5e-97b8-1533645d4081; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-08303457-af7d-4729-97bc-c0330b608842](.artifacts/records/project__check-run/rec-08303457-af7d-4729-97bc-c0330b608842.md))_
- **close-library-recheck**: rec-60f10927-c3fc-4d5e-97b8-1533645d4081; cdcb9861c1b7f82caf097b00472d16f902d8d5b9; fail; tdd _(id: [rec-138f801e-4b03-49d7-b302-7ecc46bfd35f](.artifacts/records/project__check-run/rec-138f801e-4b03-49d7-b302-7ecc46bfd35f.md))_
- **close-library-recheck**: rec-60f10927-c3fc-4d5e-97b8-1533645d4081; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; tdd _(id: [rec-b31937c2-5f5e-4401-9645-3d2530bd6d12](.artifacts/records/project__check-run/rec-b31937c2-5f5e-4401-9645-3d2530bd6d12.md))_

## close-library-verdict

### Acceptance
- **close-library-verdict**: R6; tdd; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r6 -q _(id: [rec-ffc3c0fc-0654-49b9-9849-52d3181c8673](.artifacts/records/project__acceptance/rec-ffc3c0fc-0654-49b9-9849-52d3181c8673.md))_

### Check
- **close-library-verdict**: rec-ffc3c0fc-0654-49b9-9849-52d3181c8673; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-0bcef520-0afe-4f8f-abf5-b114a7b8bef4](.artifacts/records/project__check-run/rec-0bcef520-0afe-4f8f-abf5-b114a7b8bef4.md))_
- **close-library-verdict**: rec-ffc3c0fc-0654-49b9-9849-52d3181c8673; cdcb9861c1b7f82caf097b00472d16f902d8d5b9; fail; tdd _(id: [rec-7f8b5bfb-98c9-4073-928c-f4101b15e989](.artifacts/records/project__check-run/rec-7f8b5bfb-98c9-4073-928c-f4101b15e989.md))_
- **close-library-verdict**: rec-ffc3c0fc-0654-49b9-9849-52d3181c8673; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; tdd _(id: [rec-e068d096-a6c4-41d5-8365-f47fb0c21284](.artifacts/records/project__check-run/rec-e068d096-a6c4-41d5-8365-f47fb0c21284.md))_

## close-red-first

### Acceptance
- **close-red-first**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first _(id: [rec-e7b02db3-cbf8-492f-8363-9844982d7753](.artifacts/records/project__acceptance/rec-e7b02db3-cbf8-492f-8363-9844982d7753.md))_

### Check
- **close-red-first**: rec-e7b02db3-cbf8-492f-8363-9844982d7753; b3159b685f2992638a84ad36d56a81f9ed8e8151; fail; tdd _(id: [rec-518b386e-aa2c-42c3-a539-a7d1220f7051](.artifacts/records/project__check-run/rec-518b386e-aa2c-42c3-a539-a7d1220f7051.md))_
- **close-red-first**: rec-e7b02db3-cbf8-492f-8363-9844982d7753; 54181564b74027f0ec23a402a44df7dc009d42d2; pass; tdd _(id: [rec-7f23ed3b-5645-4eb2-a0e0-5378ea9acb2d](.artifacts/records/project__check-run/rec-7f23ed3b-5645-4eb2-a0e0-5378ea9acb2d.md))_

## close-red-first-escape

### Acceptance
- **close-red-first-escape**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k 'red_first_escape or red_first_other_methods' _(id: [rec-c8b5c4cd-99a6-4906-a91c-7b4385187029](.artifacts/records/project__acceptance/rec-c8b5c4cd-99a6-4906-a91c-7b4385187029.md))_

### Check
- **close-red-first-escape**: rec-c8b5c4cd-99a6-4906-a91c-7b4385187029; 54181564b74027f0ec23a402a44df7dc009d42d2; pass; tdd _(id: [rec-33825f2d-fc44-4516-905b-51032ccb78e2](.artifacts/records/project__check-run/rec-33825f2d-fc44-4516-905b-51032ccb78e2.md))_
- **close-red-first-escape**: rec-c8b5c4cd-99a6-4906-a91c-7b4385187029; b3159b685f2992638a84ad36d56a81f9ed8e8151; fail; tdd _(id: [rec-eccd7ba2-0282-4e31-91bf-ef3c74080e73](.artifacts/records/project__check-run/rec-eccd7ba2-0282-4e31-91bf-ef3c74080e73.md))_

## close-red-first-methods

### Acceptance
- **close-red-first-methods**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_other_methods _(id: [rec-20f81a2f-2df9-4e5d-9eec-63da3defeec3](.artifacts/records/project__acceptance/rec-20f81a2f-2df9-4e5d-9eec-63da3defeec3.md))_

### Check
- **close-red-first-methods**: rec-20f81a2f-2df9-4e5d-9eec-63da3defeec3; 54181564b74027f0ec23a402a44df7dc009d42d2; pass; tdd _(id: [rec-7d303292-39e4-4fd7-b485-dc88c66ad0bb](.artifacts/records/project__check-run/rec-7d303292-39e4-4fd7-b485-dc88c66ad0bb.md))_
- **close-red-first-methods**: rec-20f81a2f-2df9-4e5d-9eec-63da3defeec3; b3159b685f2992638a84ad36d56a81f9ed8e8151; fail; tdd _(id: [rec-bc6eeb64-10b5-4bca-a8d0-6b0d84553830](.artifacts/records/project__check-run/rec-bc6eeb64-10b5-4bca-a8d0-6b0d84553830.md))_

## close-red-first-order

### Acceptance
- **close-red-first-order**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_order _(id: [rec-6e4d8f33-f843-4db1-a990-e3c5ea1abbd7](.artifacts/records/project__acceptance/rec-6e4d8f33-f843-4db1-a990-e3c5ea1abbd7.md))_

### Check
- **close-red-first-order**: rec-6e4d8f33-f843-4db1-a990-e3c5ea1abbd7; b3159b685f2992638a84ad36d56a81f9ed8e8151; fail; tdd _(id: [rec-22236a02-24dc-4d28-8d2c-c5fed9959b77](.artifacts/records/project__check-run/rec-22236a02-24dc-4d28-8d2c-c5fed9959b77.md))_
- **close-red-first-order**: rec-6e4d8f33-f843-4db1-a990-e3c5ea1abbd7; 54181564b74027f0ec23a402a44df7dc009d42d2; pass; tdd _(id: [rec-5e39adba-823f-401d-ba69-558b1eba100d](.artifacts/records/project__check-run/rec-5e39adba-823f-401d-ba69-558b1eba100d.md))_

## close-red-first-request

### Acceptance
- **close-red-first-request**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_request _(id: [rec-be6e5c30-7b5f-44e1-b497-7dcbccbea6ad](.artifacts/records/project__acceptance/rec-be6e5c30-7b5f-44e1-b497-7dcbccbea6ad.md))_

### Check
- **close-red-first-request**: rec-be6e5c30-7b5f-44e1-b497-7dcbccbea6ad; 54181564b74027f0ec23a402a44df7dc009d42d2; pass; tdd _(id: [rec-1ba03e59-6710-4afc-bafd-05f0555f3d77](.artifacts/records/project__check-run/rec-1ba03e59-6710-4afc-bafd-05f0555f3d77.md))_
- **close-red-first-request**: rec-be6e5c30-7b5f-44e1-b497-7dcbccbea6ad; b3159b685f2992638a84ad36d56a81f9ed8e8151; fail; tdd _(id: [rec-6c63bc4a-319f-4ba9-9412-c689022b6183](.artifacts/records/project__check-run/rec-6c63bc4a-319f-4ba9-9412-c689022b6183.md))_

## close-step-skill

### Acceptance
- **close-step-skill**: tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-8bcac210-20bd-42a8-b0ea-953bd412937a](.artifacts/records/project__acceptance/rec-8bcac210-20bd-42a8-b0ea-953bd412937a.md))_

### Check
- **close-step-skill**: rec-8bcac210-20bd-42a8-b0ea-953bd412937a; 8f1c9bbbb89ef3dc90f3fa36d00c83b924f2a721; pass; tdd _(id: [rec-624fc8c3-8603-42f5-b7bb-ab21d051cbc3](.artifacts/records/project__check-run/rec-624fc8c3-8603-42f5-b7bb-ab21d051cbc3.md))_

## column-resize

### Acceptance
- **column-resize**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k resize _(id: [rec-4b32e614-7d7e-4a55-be85-301c98fe6ef9](.artifacts/records/project__acceptance/rec-4b32e614-7d7e-4a55-be85-301c98fe6ef9.md))_

### Check
- **column-resize**: rec-4b32e614-7d7e-4a55-be85-301c98fe6ef9; b104980765db3920237082612a4d1aa5eda6a5b7; pass; tdd _(id: [rec-92efe161-3980-4dc2-b0ce-32eca9e0f501](.artifacts/records/project__check-run/rec-92efe161-3980-4dc2-b0ce-32eca9e0f501.md))_

### Observation
- **column-resize**: On resize, DashboardApp.on_resize runs before App.size updates, so paint() used the old width; EffortPane.on_resize replayed the stored stale width. Columns stayed wide until reload.; dashboard-bugfix _(id: [rec-c526251e-c035-426f-abf2-b9604030e7fa](.artifacts/records/project__investigation-observation/rec-c526251e-c035-426f-abf2-b9604030e7fa.md))_

## command-facade

### Acceptance
- **command-facade**: R20; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_command_facade.py::test_r20_create_without_store -q _(id: [rec-ff99f4c7-f4f4-43f3-8d09-afe55ef5d883](.artifacts/records/project__acceptance/rec-ff99f4c7-f4f4-43f3-8d09-afe55ef5d883.md))_

### Check
- **command-facade**: rec-ff99f4c7-f4f4-43f3-8d09-afe55ef5d883; dirty; fail; tdd _(id: [rec-27899b77-9be8-4dfc-95a3-3ee02f7f32ac](.artifacts/records/project__check-run/rec-27899b77-9be8-4dfc-95a3-3ee02f7f32ac.md))_
- **command-facade**: rec-ff99f4c7-f4f4-43f3-8d09-afe55ef5d883; 206fcd0b22ed111d7a272c934bb1864271947591; pass; tdd _(id: [rec-6f40d9f1-1109-4069-8322-8d23d2390058](.artifacts/records/project__check-run/rec-6f40d9f1-1109-4069-8322-8d23d2390058.md))_
- **command-facade**: rec-ff99f4c7-f4f4-43f3-8d09-afe55ef5d883; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-bfc494d4-ef31-457e-be75-26797480cd46](.artifacts/records/project__check-run/rec-bfc494d4-ef31-457e-be75-26797480cd46.md))_

## command-facade-get

### Acceptance
- **command-facade-get**: R21; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_command_facade.py::test_r21_get_without_store -q _(id: [rec-a4822eee-d1b1-4079-bf8d-3be6cf7babe4](.artifacts/records/project__acceptance/rec-a4822eee-d1b1-4079-bf8d-3be6cf7babe4.md))_

### Check
- **command-facade-get**: rec-a4822eee-d1b1-4079-bf8d-3be6cf7babe4; dirty; fail; tdd _(id: [rec-42721b07-0dfe-48d9-8627-6fde15b81aeb](.artifacts/records/project__check-run/rec-42721b07-0dfe-48d9-8627-6fde15b81aeb.md))_
- **command-facade-get**: rec-a4822eee-d1b1-4079-bf8d-3be6cf7babe4; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-77807359-056d-4ba9-a500-38cadb0c9b5c](.artifacts/records/project__check-run/rec-77807359-056d-4ba9-a500-38cadb0c9b5c.md))_
- **command-facade-get**: rec-a4822eee-d1b1-4079-bf8d-3be6cf7babe4; 206fcd0b22ed111d7a272c934bb1864271947591; pass; tdd _(id: [rec-e107b1b7-5df4-4eb1-b8e8-c253ae44cddb](.artifacts/records/project__check-run/rec-e107b1b7-5df4-4eb1-b8e8-c253ae44cddb.md))_

## command-facade-scan

### Acceptance
- **command-facade-scan**: R14; check; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_command_facade.py::test_r14_no_se_workflow_store -q _(id: [rec-9f9de8c6-9890-4dd5-b699-4469b9ddebb9](.artifacts/records/project__acceptance/rec-9f9de8c6-9890-4dd5-b699-4469b9ddebb9.md))_

### Check
- **command-facade-scan**: rec-9f9de8c6-9890-4dd5-b699-4469b9ddebb9; 206fcd0b22ed111d7a272c934bb1864271947591; pass; check _(id: [rec-e16eede4-d80f-4385-8056-7949fbbcce76](.artifacts/records/project__check-run/rec-e16eede4-d80f-4385-8056-7949fbbcce76.md))_
- **command-facade-scan**: rec-9f9de8c6-9890-4dd5-b699-4469b9ddebb9; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; check _(id: [rec-f697f97b-efb2-4320-b1e9-9bdad6657890](.artifacts/records/project__check-run/rec-f697f97b-efb2-4320-b1e9-9bdad6657890.md))_

## commit-stat-width

### Acceptance
- **commit-stat-width**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-de68bee3-9f99-4495-8545-8aa7b453e373](.artifacts/records/project__acceptance/rec-de68bee3-9f99-4495-8545-8aa7b453e373.md))_

### Check
- **commit-stat-width**: rec-de68bee3-9f99-4495-8545-8aa7b453e373; da2d120; pass; tdd _(id: [rec-b7acff16-1849-4e7f-a841-2a9bd821afd0](.artifacts/records/project__check-run/rec-b7acff16-1849-4e7f-a841-2a9bd821afd0.md))_

## contract-backlog

### Acceptance
- **contract-backlog**: R1; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-23b30985-3712-43f6-b1e4-f9240d9a632c](.artifacts/records/project__acceptance/rec-23b30985-3712-43f6-b1e4-f9240d9a632c.md))_

### Check
- **contract-backlog**: rec-23b30985-3712-43f6-b1e4-f9240d9a632c; 150d4cf3ea0e2c0d34718cc9645613ed33a8430b; pass; check _(id: [rec-131906fa-23a5-4e07-9669-db912f63c0e2](.artifacts/records/project__check-run/rec-131906fa-23a5-4e07-9669-db912f63c0e2.md))_

## contract-backlog-effort

### Acceptance
- **contract-backlog-effort**: R3; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-1686fb83-3253-4571-8f6d-9b927f916c77](.artifacts/records/project__acceptance/rec-1686fb83-3253-4571-8f6d-9b927f916c77.md))_

### Check
- **contract-backlog-effort**: rec-1686fb83-3253-4571-8f6d-9b927f916c77; 150d4cf3ea0e2c0d34718cc9645613ed33a8430b; pass; check _(id: [rec-3dd98e54-6a65-4576-8783-42412165c962](.artifacts/records/project__check-run/rec-3dd98e54-6a65-4576-8783-42412165c962.md))_

## contract-backlog-status

### Acceptance
- **contract-backlog-status**: R4; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-7f83aff0-87bd-4dfa-9d94-12920f3a46aa](.artifacts/records/project__acceptance/rec-7f83aff0-87bd-4dfa-9d94-12920f3a46aa.md))_

### Check
- **contract-backlog-status**: rec-7f83aff0-87bd-4dfa-9d94-12920f3a46aa; 150d4cf3ea0e2c0d34718cc9645613ed33a8430b; pass; check _(id: [rec-c6be4c30-1d8a-4ecb-968a-7572136c150f](.artifacts/records/project__check-run/rec-c6be4c30-1d8a-4ecb-968a-7572136c150f.md))_

## contract-loop

### Acceptance
- **contract-loop**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-6d715e64-501c-42c0-b057-42d81bbb01b8](.artifacts/records/project__acceptance/rec-6d715e64-501c-42c0-b057-42d81bbb01b8.md))_

### Check
- **contract-loop**: rec-6d715e64-501c-42c0-b057-42d81bbb01b8; dirty; pass; check _(id: [rec-bc6527c5-0217-413e-a69f-4a2272e61b1d](.artifacts/records/project__check-run/rec-bc6527c5-0217-413e-a69f-4a2272e61b1d.md))_

## contract-thin-criterion

### Acceptance
- **contract-thin-criterion**: R4; check; workflow-loop; python3 -c "import json; from pathlib import Path; d=json.loads(Path('contract/project-design.json').read_text()); acc=next(r for r in d['records'] if r['name']=='acceptance'); assert 'criterion' in acc['optional_payload']; assert 'criterion' not in (set(acc['payload'])-set(acc['optional_payload'])); views={v.get('name') or v.get('id'): v for v in (d['views'] if isinstance(d['views'], list) else list(d['views'].values()))}; bad=[n for n,v in views.items() for r in v.get('roles',[]) if (r.get('occupant')=='acceptance' or r.get('name')=='acceptance') and 'criterion' in r.get('requires_payload',[])]; assert not bad, bad" _(id: [rec-c79b18fc-3e2f-4a36-8417-9799d980ae1d](.artifacts/records/project__acceptance/rec-c79b18fc-3e2f-4a36-8417-9799d980ae1d.md))_

### Check
- **contract-thin-criterion**: rec-c79b18fc-3e2f-4a36-8417-9799d980ae1d; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; check _(id: [rec-32e0d94f-2f17-4818-98f0-37ed1b1b7ff9](.artifacts/records/project__check-run/rec-32e0d94f-2f17-4818-98f0-37ed1b1b7ff9.md))_
- **contract-thin-criterion**: rec-c79b18fc-3e2f-4a36-8417-9799d980ae1d; f9d7371db36180d569d1923814affd42a37d2e7c; pass; check _(id: [rec-954f2345-d0a9-4bb1-9209-fd755a230bca](.artifacts/records/project__check-run/rec-954f2345-d0a9-4bb1-9209-fd755a230bca.md))_
- **contract-thin-criterion**: rec-c79b18fc-3e2f-4a36-8417-9799d980ae1d; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-97dd5d85-a57a-4459-9142-0f743939654c](.artifacts/records/project__check-run/rec-97dd5d85-a57a-4459-9142-0f743939654c.md))_

## copy-and-commit-actions

### Acceptance
- **copy-and-commit-actions**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-b0782695-b6a8-443a-b1ed-fd39a65b5de8](.artifacts/records/project__acceptance/rec-b0782695-b6a8-443a-b1ed-fd39a65b5de8.md))_

### Check
- **copy-and-commit-actions**: rec-b0782695-b6a8-443a-b1ed-fd39a65b5de8; 9822923; pass; tdd _(id: [rec-fb98930f-0a3a-4841-95db-46f171e68f36](.artifacts/records/project__check-run/rec-fb98930f-0a3a-4841-95db-46f171e68f36.md))_

## cross-harness-install-review

### Check
- **cross-harness-install-review**: cross-harness-install-review; 48bcc343f9edcfd9338a6a497293aabd9cd52300; fail; review _(id: [rec-9eacddaf-278f-40f9-8075-a96dface5b29](.artifacts/records/project__check-run/rec-9eacddaf-278f-40f9-8075-a96dface5b29.md))_
- **cross-harness-install-review**: cross-harness-install-review; 483c621e1d813b9fe92d70b0c9c59a53d3080f79; fail; review _(id: [rec-a2572465-2fff-4cd9-8915-102116d3897b](.artifacts/records/project__check-run/rec-a2572465-2fff-4cd9-8915-102116d3897b.md))_
- **cross-harness-install-review**: cross-harness-install-review; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; review _(id: [rec-bb7b6bf8-c478-4f02-9770-e5ca349e9ef7](.artifacts/records/project__check-run/rec-bb7b6bf8-c478-4f02-9770-e5ca349e9ef7.md))_

## dashboard-app

### Acceptance
- **dashboard-app**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-607927c0-6e77-499d-ae1f-ee7a890cfd07](.artifacts/records/project__acceptance/rec-607927c0-6e77-499d-ae1f-ee7a890cfd07.md))_

### Check
- **dashboard-app**: rec-607927c0-6e77-499d-ae1f-ee7a890cfd07; f84a229; pass; tdd _(id: [rec-3b1bf0ad-45ab-4b9b-8c35-152bc2cd0bad](.artifacts/records/project__check-run/rec-3b1bf0ad-45ab-4b9b-8c35-152bc2cd0bad.md))_

## dashboard-approvals-review

### Check
- **dashboard-approvals-review**: dashboard-approvals-review; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; fail; review _(id: [rec-9b93df93-3d63-4d15-8eb1-f927c1beb724](.artifacts/records/project__check-run/rec-9b93df93-3d63-4d15-8eb1-f927c1beb724.md))_
- **dashboard-approvals-review**: dashboard-approvals-review; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; review _(id: [rec-a1ab248f-9e27-47ac-bce5-f732320cabba](.artifacts/records/project__check-run/rec-a1ab248f-9e27-47ac-bce5-f732320cabba.md))_

## dashboard-backlog

### Acceptance
- **dashboard-backlog**: R6; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k backlog _(id: [rec-00466274-876f-4c8b-a54e-a8db1e61fbda](.artifacts/records/project__acceptance/rec-00466274-876f-4c8b-a54e-a8db1e61fbda.md))_

### Check
- **dashboard-backlog**: rec-00466274-876f-4c8b-a54e-a8db1e61fbda; 2ba3f658a6c7a374ef157640f4dd4a3024588e90; pass; tdd _(id: [rec-0adb36e3-2686-4672-81d9-8173f848bb8d](.artifacts/records/project__check-run/rec-0adb36e3-2686-4672-81d9-8173f848bb8d.md))_

## dashboard-backlog-actions

### Acceptance
- **dashboard-backlog-actions**: R6; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k backlog _(id: [rec-644805a3-42e4-4437-8ffc-cd772a363cea](.artifacts/records/project__acceptance/rec-644805a3-42e4-4437-8ffc-cd772a363cea.md))_

### Check
- **dashboard-backlog-actions**: rec-644805a3-42e4-4437-8ffc-cd772a363cea; 2ba3f658a6c7a374ef157640f4dd4a3024588e90; pass; tdd _(id: [rec-4b35e98c-e1c7-4fd6-9afa-664703d80eab](.artifacts/records/project__check-run/rec-4b35e98c-e1c7-4fd6-9afa-664703d80eab.md))_

## dashboard-closed-goals

### Acceptance
- **dashboard-closed-goals**: tdd; workflow-loop; python3 -m pytest tests/test_dashboard_model.py -q _(id: [rec-f02ec3b2-3bd6-496f-933a-1506d3b4a877](.artifacts/records/project__acceptance/rec-f02ec3b2-3bd6-496f-933a-1506d3b4a877.md))_

### Check
- **dashboard-closed-goals**: rec-f02ec3b2-3bd6-496f-933a-1506d3b4a877; 8f1c9bbbb89ef3dc90f3fa36d00c83b924f2a721; pass; tdd _(id: [rec-d8041aec-d887-49ea-aa27-693636929bb6](.artifacts/records/project__check-run/rec-d8041aec-d887-49ea-aa27-693636929bb6.md))_

## dashboard-dismiss

### Acceptance
- **dashboard-dismiss**: R4; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k dismiss _(id: [rec-3399e692-0dd4-4842-9cb1-3ff2a3f95513](.artifacts/records/project__acceptance/rec-3399e692-0dd4-4842-9cb1-3ff2a3f95513.md))_

### Check
- **dashboard-dismiss**: rec-3399e692-0dd4-4842-9cb1-3ff2a3f95513; 8799ca930443a9a3144434eaf3b9e30e497adbce; pass; tdd _(id: [rec-1067db97-d173-4c6d-9703-51b875bfe369](.artifacts/records/project__check-run/rec-1067db97-d173-4c6d-9703-51b875bfe369.md))_

### Observation
- **dashboard-dismiss**: Needs you list/detail had no dismiss binding and never invoked adaptive-artifacts; workflow-loop _(id: [rec-ad0eb0da-1eac-4d9d-b81a-4b11e16bbe1b](.artifacts/records/project__investigation-observation/rec-ad0eb0da-1eac-4d9d-b81a-4b11e16bbe1b.md))_

### Finding
- **dashboard-dismiss**: Dashboard mirrored open human gates but never dismissed them via adaptive-artifacts CLI; pre-fix UI had no d-dismiss; pilots now pass for clear/refuse/CLI-fail; dismiss pilots fail or dashboard invents a local dismiss cache; none _(id: [rec-02f2b892-db35-4a29-8220-d89cbe33ab4c](.artifacts/records/project__finding/rec-02f2b892-db35-4a29-8220-d89cbe33ab4c.md))_

## dashboard-dismiss-refuse

### Acceptance
- **dashboard-dismiss-refuse**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'dismiss and (refuse or fail or error)' _(id: [rec-76204de3-ed47-4406-9096-db2caa3f9d68](.artifacts/records/project__acceptance/rec-76204de3-ed47-4406-9096-db2caa3f9d68.md))_

### Check
- **dashboard-dismiss-refuse**: rec-76204de3-ed47-4406-9096-db2caa3f9d68; 8799ca930443a9a3144434eaf3b9e30e497adbce; pass; tdd _(id: [rec-232c063c-895e-42a5-b91a-55d0d1a6cad0](.artifacts/records/project__check-run/rec-232c063c-895e-42a5-b91a-55d0d1a6cad0.md))_

## dashboard-launcher

### Acceptance
- **dashboard-launcher**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-e4e1b7a5-4c4b-45ce-8a02-bb12452e15ea](.artifacts/records/project__acceptance/rec-e4e1b7a5-4c4b-45ce-8a02-bb12452e15ea.md))_

### Check
- **dashboard-launcher**: rec-e4e1b7a5-4c4b-45ce-8a02-bb12452e15ea; f4cf9dc; pass; tdd _(id: [rec-c4dc7668-a282-42b6-bfa7-6669d2e8e89d](.artifacts/records/project__check-run/rec-c4dc7668-a282-42b6-bfa7-6669d2e8e89d.md))_

## dashboard-launcher-switch

### Acceptance
- **dashboard-launcher-switch**: tdd; dashboard; python3 -m pytest tests/test_dashboard_launcher.py tests/test_tmux_integration.py -q _(id: [rec-7fbf25bf-c639-424e-a4a2-66a5d640f23a](.artifacts/records/project__acceptance/rec-7fbf25bf-c639-424e-a4a2-66a5d640f23a.md))_

### Check
- **dashboard-launcher-switch**: rec-7fbf25bf-c639-424e-a4a2-66a5d640f23a; 3e52964; pass; tdd _(id: [rec-886e6cd6-162c-4c11-a70f-08b1d3cb20b9](.artifacts/records/project__check-run/rec-886e6cd6-162c-4c11-a70f-08b1d3cb20b9.md))_

## dashboard-snapshot

### Acceptance
- **dashboard-snapshot**: tdd; dashboard; python3 -m pytest tests/test_dashboard_model.py -q _(id: [rec-8f27fb0c-0113-4d37-9083-5f9767e2d6e6](.artifacts/records/project__acceptance/rec-8f27fb0c-0113-4d37-9083-5f9767e2d6e6.md))_

### Check
- **dashboard-snapshot**: rec-8f27fb0c-0113-4d37-9083-5f9767e2d6e6; 1e88c65; pass; tdd _(id: [rec-2bc92ccd-0454-477e-b1db-644874232b6c](.artifacts/records/project__check-run/rec-2bc92ccd-0454-477e-b1db-644874232b6c.md))_

## dashboard-status-segment

### Acceptance
- **dashboard-status-segment**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-e7e94ca1-9742-44b2-9fe1-7a014b58ef3d](.artifacts/records/project__acceptance/rec-e7e94ca1-9742-44b2-9fe1-7a014b58ef3d.md))_

### Check
- **dashboard-status-segment**: rec-e7e94ca1-9742-44b2-9fe1-7a014b58ef3d; 79fda7a; pass; tdd _(id: [rec-9b7aa254-a191-4196-a918-8e364893a451](.artifacts/records/project__check-run/rec-9b7aa254-a191-4196-a918-8e364893a451.md))_

## declared-install-review

### Check
- **declared-install-review**: declared-install-review; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; review _(id: [rec-c89aa1bb-fc48-4fe4-95e2-c3a326d79064](.artifacts/records/project__check-run/rec-c89aa1bb-fc48-4fe4-95e2-c3a326d79064.md))_

## deep-links-resolve

### Acceptance
- **deep-links-resolve**: R4; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/links.test.ts -t R4 _(id: [rec-d41c2986-ef5c-480a-971d-18377b39c1ad](.artifacts/records/project__acceptance/rec-d41c2986-ef5c-480a-971d-18377b39c1ad.md))_

### Check
- **deep-links-resolve**: rec-d41c2986-ef5c-480a-971d-18377b39c1ad; 3216e017c64e9e851f3a51efe273b26ba7450456; pass; check _(id: [rec-9e27f631-06b0-4612-848f-457c7f2e0611](.artifacts/records/project__check-run/rec-9e27f631-06b0-4612-848f-457c7f2e0611.md))_

## deep-links-resolve-r7

### Acceptance
- **deep-links-resolve-r7**: R7; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/links.test.ts -t R7 _(id: [rec-a3b4511b-eab7-48e1-b9f2-379030867ef0](.artifacts/records/project__acceptance/rec-a3b4511b-eab7-48e1-b9f2-379030867ef0.md))_

### Check
- **deep-links-resolve-r7**: rec-a3b4511b-eab7-48e1-b9f2-379030867ef0; 3216e017c64e9e851f3a51efe273b26ba7450456; pass; check _(id: [rec-9d12908b-fae7-4535-a444-4dfe1cd739ef](.artifacts/records/project__check-run/rec-9d12908b-fae7-4535-a444-4dfe1cd739ef.md))_

## deep-links-resolve-r8

### Acceptance
- **deep-links-resolve-r8**: R8; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/links.test.ts -t R8 _(id: [rec-28d4e052-e7a4-450a-9bd3-184e7c13b6fe](.artifacts/records/project__acceptance/rec-28d4e052-e7a4-450a-9bd3-184e7c13b6fe.md))_

### Check
- **deep-links-resolve-r8**: rec-28d4e052-e7a4-450a-9bd3-184e7c13b6fe; 3216e017c64e9e851f3a51efe273b26ba7450456; pass; check _(id: [rec-86c42115-690b-4b07-8f6e-2c9346721449](.artifacts/records/project__check-run/rec-86c42115-690b-4b07-8f6e-2c9346721449.md))_

## deep-links-review

### Check
- **deep-links-review**: 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; review _(id: [rec-b2518fc1-75e3-4270-a9b9-a0f4dbef72b6](.artifacts/records/project__check-run/rec-b2518fc1-75e3-4270-a9b9-a0f4dbef72b6.md))_

## deep-links-wire

### Acceptance
- **deep-links-wire**: R1; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/deepLinks.test.ts -t R1 _(id: [rec-1788deb2-bdc2-48db-aedb-3bf2a14a7a4a](.artifacts/records/project__acceptance/rec-1788deb2-bdc2-48db-aedb-3bf2a14a7a4a.md))_

### Check
- **deep-links-wire**: rec-1788deb2-bdc2-48db-aedb-3bf2a14a7a4a; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-8c93329e-11af-4de0-a823-5525701e49da](.artifacts/records/project__check-run/rec-8c93329e-11af-4de0-a823-5525701e49da.md))_
- **deep-links-wire**: rec-1788deb2-bdc2-48db-aedb-3bf2a14a7a4a; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-e8c5dd8a-61a2-425f-a8f0-b988e9d6817d](.artifacts/records/project__check-run/rec-e8c5dd8a-61a2-425f-a8f0-b988e9d6817d.md))_

## deep-links-wire-r2

### Acceptance
- **deep-links-wire-r2**: R2; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/deepLinks.test.ts -t R2 _(id: [rec-1ad98619-b61f-49c3-a0e2-2159185565b7](.artifacts/records/project__acceptance/rec-1ad98619-b61f-49c3-a0e2-2159185565b7.md))_

### Check
- **deep-links-wire-r2**: rec-1ad98619-b61f-49c3-a0e2-2159185565b7; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-10ab4da4-8328-4143-a83a-2c98aa58e50a](.artifacts/records/project__check-run/rec-10ab4da4-8328-4143-a83a-2c98aa58e50a.md))_
- **deep-links-wire-r2**: rec-1ad98619-b61f-49c3-a0e2-2159185565b7; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-a0c4c5ff-5493-4c9b-b5cb-78a2de13a360](.artifacts/records/project__check-run/rec-a0c4c5ff-5493-4c9b-b5cb-78a2de13a360.md))_

## deep-links-wire-r3

### Acceptance
- **deep-links-wire-r3**: R3; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/deepLinks.test.ts -t R3 _(id: [rec-b8ce4135-e40e-4ece-910a-781e5b30e30c](.artifacts/records/project__acceptance/rec-b8ce4135-e40e-4ece-910a-781e5b30e30c.md))_

### Check
- **deep-links-wire-r3**: rec-b8ce4135-e40e-4ece-910a-781e5b30e30c; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-35005cb7-feee-4b52-ad72-b3411ee6c7d6](.artifacts/records/project__check-run/rec-35005cb7-feee-4b52-ad72-b3411ee6c7d6.md))_
- **deep-links-wire-r3**: rec-b8ce4135-e40e-4ece-910a-781e5b30e30c; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-f8dfa5a5-dc1a-491e-b9ec-f4f749e43b78](.artifacts/records/project__check-run/rec-f8dfa5a5-dc1a-491e-b9ec-f4f749e43b78.md))_

## deep-links-wire-r5

### Acceptance
- **deep-links-wire-r5**: R5; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/deepLinks.test.ts -t R5 _(id: [rec-882aa357-a17d-41cc-a762-e75f493ea634](.artifacts/records/project__acceptance/rec-882aa357-a17d-41cc-a762-e75f493ea634.md))_

### Check
- **deep-links-wire-r5**: rec-882aa357-a17d-41cc-a762-e75f493ea634; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-0021c87c-c0c3-4fe1-ae7f-cfd27a5ce008](.artifacts/records/project__check-run/rec-0021c87c-c0c3-4fe1-ae7f-cfd27a5ce008.md))_
- **deep-links-wire-r5**: rec-882aa357-a17d-41cc-a762-e75f493ea634; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-40bc7ebe-fdd2-49c6-b2b8-fa00186ddbaa](.artifacts/records/project__check-run/rec-40bc7ebe-fdd2-49c6-b2b8-fa00186ddbaa.md))_

## deep-links-wire-r6

### Acceptance
- **deep-links-wire-r6**: R6; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/deepLinks.test.ts -t R6 _(id: [rec-a0481bf1-d92e-4f8c-a6b5-57be57e51c0d](.artifacts/records/project__acceptance/rec-a0481bf1-d92e-4f8c-a6b5-57be57e51c0d.md))_

### Check
- **deep-links-wire-r6**: rec-a0481bf1-d92e-4f8c-a6b5-57be57e51c0d; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-7688d828-996f-4ad3-a0ce-7a7c88b59c2b](.artifacts/records/project__check-run/rec-7688d828-996f-4ad3-a0ce-7a7c88b59c2b.md))_
- **deep-links-wire-r6**: rec-a0481bf1-d92e-4f8c-a6b5-57be57e51c0d; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-9239a964-00d9-44ff-acf0-b8060cd7d316](.artifacts/records/project__check-run/rec-9239a964-00d9-44ff-acf0-b8060cd7d316.md))_

## detail-redraw-race

### Acceptance
- **detail-redraw-race**: check; dashboard; for i in $(seq 30); do uv run --with textual --with pytest python -m pytest 'tests/test_dashboard_app.py::test_detail_screen_redraws_when_the_store_changes' -q || exit 1; done _(id: [rec-c4742568-196f-4b86-89ea-4a12a7490978](.artifacts/records/project__acceptance/rec-c4742568-196f-4b86-89ea-4a12a7490978.md))_

### Check
- **detail-redraw-race**: rec-c4742568-196f-4b86-89ea-4a12a7490978; 03d561c; pass; check _(id: [rec-83577b2a-8ec0-4648-b7d9-2d706b7959bd](.artifacts/records/project__check-run/rec-83577b2a-8ec0-4648-b7d9-2d706b7959bd.md))_

### Observation
- **detail-redraw-race**: test_detail_screen_redraws_when_the_store_changes[size1] failed with NoMatches: No nodes match '#related' on TaskDetailScreen(); 1 of 2 full runs, 1 of 4 isolated runs; earlier it timed out under load in two other full runs; dashboard-ui _(id: [rec-cf05a87a-e78b-48fb-ad15-132bd63bb053](.artifacts/records/project__investigation-observation/rec-cf05a87a-e78b-48fb-ad15-132bd63bb053.md))_

### Finding
- **detail-redraw-race**: The detail screen paint queried #related after awaits without re-checking that the screen was still attached, so a poll-triggered redraw racing teardown raised NoMatches; Traceback apply -> paint query_one(#related) in 5 of 25 loaded runs; 30/30 loaded and 30/30 alone after re-checking is_attached after the awaits; The test fails again with NoMatches after 03d561c; none _(id: [rec-5018f385-7ec4-40ba-9736-d651d7b2af88](.artifacts/records/project__finding/rec-5018f385-7ec4-40ba-9736-d651d7b2af88.md))_

## discuss-skill

### Acceptance
- **discuss-skill**: tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_discuss_skill.py -q _(id: [rec-29f17960-fd84-4c12-9d0b-9589e7b71980](.artifacts/records/project__acceptance/rec-29f17960-fd84-4c12-9d0b-9589e7b71980.md))_

### Check
- **discuss-skill**: rec-29f17960-fd84-4c12-9d0b-9589e7b71980; 8c697bc88db7147f17a058311b0323cd4a191fee; pass; tdd _(id: [rec-94e86670-ccc6-4d19-bc2f-38158169ceeb](.artifacts/records/project__check-run/rec-94e86670-ccc6-4d19-bc2f-38158169ceeb.md))_

## drop-row-waits-on

### Acceptance
- **drop-row-waits-on**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_tasks.py -q -k 'title_cell and waits' _(id: [rec-873b510b-7eeb-42da-a7e7-fc83684576e7](.artifacts/records/project__acceptance/rec-873b510b-7eeb-42da-a7e7-fc83684576e7.md))_

### Check
- **drop-row-waits-on**: rec-873b510b-7eeb-42da-a7e7-fc83684576e7; dirty; fail; tdd _(id: [rec-6d8ce709-787d-4d5d-8ecd-d092f017d26b](.artifacts/records/project__check-run/rec-6d8ce709-787d-4d5d-8ecd-d092f017d26b.md))_
- **drop-row-waits-on**: rec-873b510b-7eeb-42da-a7e7-fc83684576e7; 98bcbd8 dirty; pass; tdd _(id: [rec-c7ae8096-95aa-476a-9b82-1e919116029f](.artifacts/records/project__check-run/rec-c7ae8096-95aa-476a-9b82-1e919116029f.md))_

### Observation
- **drop-row-waits-on**: title_cell appended full unclipped waits on list; 8 long deps produced ~157-char title cell at widths 40/60/120; dashboard _(id: [rec-93f80c29-7ff5-4aa8-b53d-c92927d28a82](.artifacts/records/project__investigation-observation/rec-93f80c29-7ff5-4aa8-b53d-c92927d28a82.md))_

### Finding
- **drop-row-waits-on**: title_cell appended an unclipped waits-on dependency list that overflowed and wrapped task rows; code inspection of title_cell plus failing then passing TDD slice; title_cell again appends waits on text or detail loses Depends on links; none _(id: [rec-8a2bc307-f417-4d2f-a4b7-507724e2e977](.artifacts/records/project__finding/rec-8a2bc307-f417-4d2f-a4b7-507724e2e977.md))_

## drop-row-waits-on-detail

### Acceptance
- **drop-row-waits-on-detail**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'detail and (Depends or blocked or waiting)' _(id: [rec-d2f45e59-d643-45ff-97f9-72e4edd0debb](.artifacts/records/project__acceptance/rec-d2f45e59-d643-45ff-97f9-72e4edd0debb.md))_

### Check
- **drop-row-waits-on-detail**: rec-d2f45e59-d643-45ff-97f9-72e4edd0debb; dirty; fail; tdd _(id: [rec-59ffa822-2a79-460f-a77a-65666f6c920d](.artifacts/records/project__check-run/rec-59ffa822-2a79-460f-a77a-65666f6c920d.md))_
- **drop-row-waits-on-detail**: rec-d2f45e59-d643-45ff-97f9-72e4edd0debb; 98bcbd8 dirty; pass; tdd _(id: [rec-ab772415-e0aa-42a0-aa88-2a840c6d2471](.artifacts/records/project__check-run/rec-ab772415-e0aa-42a0-aa88-2a840c6d2471.md))_

## drop-row-waits-on-oneline

### Acceptance
- **drop-row-waits-on-oneline**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'waiting_row' _(id: [rec-171c0948-9d2c-48a5-8622-a063778e21bf](.artifacts/records/project__acceptance/rec-171c0948-9d2c-48a5-8622-a063778e21bf.md))_

### Check
- **drop-row-waits-on-oneline**: rec-171c0948-9d2c-48a5-8622-a063778e21bf; dirty; fail; tdd _(id: [rec-0b41479e-16e0-417c-b615-a9f37fcdc0e1](.artifacts/records/project__check-run/rec-0b41479e-16e0-417c-b615-a9f37fcdc0e1.md))_
- **drop-row-waits-on-oneline**: rec-171c0948-9d2c-48a5-8622-a063778e21bf; 98bcbd8 dirty; pass; tdd _(id: [rec-c9806692-e2a6-4d50-81aa-936e7d9fbaae](.artifacts/records/project__check-run/rec-c9806692-e2a6-4d50-81aa-936e7d9fbaae.md))_

## e2e-real-execute-run

### Acceptance
- **e2e-real-execute-run**: manual; dashboard _(id: [rec-70f9c43d-01d7-438e-8df6-ad97b7fd46ce](.artifacts/records/project__acceptance/rec-70f9c43d-01d7-438e-8df6-ad97b7fd46ce.md))_

### Check
- **e2e-real-execute-run**: rec-70f9c43d-01d7-438e-8df6-ad97b7fd46ce; dirty; pass; manual; ayin _(id: [rec-fd14f0b7-0adc-4394-8deb-14db551d0328](.artifacts/records/project__check-run/rec-fd14f0b7-0adc-4394-8deb-14db551d0328.md))_

## e2e-scripted-run

### Acceptance
- **e2e-scripted-run**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q -k e2e _(id: [rec-5f7f36da-ec22-4619-b31b-8ff7fb3b85ee](.artifacts/records/project__acceptance/rec-5f7f36da-ec22-4619-b31b-8ff7fb3b85ee.md))_

### Check
- **e2e-scripted-run**: rec-5f7f36da-ec22-4619-b31b-8ff7fb3b85ee; a3b4ee2; pass; tdd _(id: [rec-0bb17e22-8556-465f-b71b-26bf65439808](.artifacts/records/project__check-run/rec-0bb17e22-8556-465f-b71b-26bf65439808.md))_

### Observation
- **e2e-scripted-run**: One of ten full-suite runs failed on the e2e test before the status check became a poll; likely cause is the dashboard-status 2 s view timeout under load, which makes the status line print nothing; watch-dashboard _(id: [rec-a77f0052-dde9-486a-8cd7-d29c9576f5a4](.artifacts/records/project__investigation-observation/rec-a77f0052-dde9-486a-8cd7-d29c9576f5a4.md))_

## effort-switch-focus

### Acceptance
- **effort-switch-focus**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k switch _(id: [rec-768f3192-cdcf-45d9-9421-2282f78e8bef](.artifacts/records/project__acceptance/rec-768f3192-cdcf-45d9-9421-2282f78e8bef.md))_

### Check
- **effort-switch-focus**: rec-768f3192-cdcf-45d9-9421-2282f78e8bef; 9da847f3ed9909af06213792ab542bdd582422a3; pass; tdd _(id: [rec-f46731c5-7318-4e68-8d68-c07a955c4d00](.artifacts/records/project__check-run/rec-f46731c5-7318-4e68-8d68-c07a955c4d00.md))_

## estimate-chips

### Acceptance
- **estimate-chips**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_estimate.py -q -k estimate_view_chips _(id: [rec-9151bd53-c190-48d4-a538-e887e6f192bd](.artifacts/records/project__acceptance/rec-9151bd53-c190-48d4-a538-e887e6f192bd.md))_

### Check
- **estimate-chips**: rec-9151bd53-c190-48d4-a538-e887e6f192bd; dirty; pass; tdd _(id: [rec-74c63806-81fe-44f6-a287-e830459e7a99](.artifacts/records/project__check-run/rec-74c63806-81fe-44f6-a287-e830459e7a99.md))_
- **estimate-chips**: rec-9151bd53-c190-48d4-a538-e887e6f192bd; dirty; fail; tdd _(id: [rec-fd0dc3b1-bc13-48e3-b1d4-ed18aab7da50](.artifacts/records/project__check-run/rec-fd0dc3b1-bc13-48e3-b1d4-ed18aab7da50.md))_

## estimate-contract

### Acceptance
- **estimate-contract**: R1; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_contract.py -q -k size _(id: [rec-1f969ece-cd7e-42c2-944a-899e5ff0f266](.artifacts/records/project__acceptance/rec-1f969ece-cd7e-42c2-944a-899e5ff0f266.md))_

### Check
- **estimate-contract**: rec-1f969ece-cd7e-42c2-944a-899e5ff0f266; dirty; pass; tdd _(id: [rec-d8d55808-f9b0-4f46-9cf1-d924a88ec0d6](.artifacts/records/project__check-run/rec-d8d55808-f9b0-4f46-9cf1-d924a88ec0d6.md))_
- **estimate-contract**: rec-1f969ece-cd7e-42c2-944a-899e5ff0f266; dirty; fail; tdd _(id: [rec-fa2dfc43-1ec4-4d0e-bc55-80fc987bb32b](.artifacts/records/project__check-run/rec-fa2dfc43-1ec4-4d0e-bc55-80fc987bb32b.md))_

## estimate-contract-minutes

### Acceptance
- **estimate-contract-minutes**: R2; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_contract.py -q -k minutes _(id: [rec-5a0f9f85-407d-497d-b412-1e314d15e91d](.artifacts/records/project__acceptance/rec-5a0f9f85-407d-497d-b412-1e314d15e91d.md))_

### Check
- **estimate-contract-minutes**: rec-5a0f9f85-407d-497d-b412-1e314d15e91d; dirty; pass; tdd _(id: [rec-81470571-0061-44e4-8e84-2e21746a65bd](.artifacts/records/project__check-run/rec-81470571-0061-44e4-8e84-2e21746a65bd.md))_
- **estimate-contract-minutes**: rec-5a0f9f85-407d-497d-b412-1e314d15e91d; dirty; fail; tdd _(id: [rec-fb3ae873-822c-4528-87f2-c10c122aa0b0](.artifacts/records/project__check-run/rec-fb3ae873-822c-4528-87f2-c10c122aa0b0.md))_

## estimate-model

### Acceptance
- **estimate-model**: R1; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_sitting_phrase _(id: [rec-7eabd5f4-5519-4834-b2f5-2330ed0ff75e](.artifacts/records/project__acceptance/rec-7eabd5f4-5519-4834-b2f5-2330ed0ff75e.md))_

### Check
- **estimate-model**: rec-7eabd5f4-5519-4834-b2f5-2330ed0ff75e; dirty; pass; tdd _(id: [rec-4ff68584-f3f2-42d5-a170-df4ced720bcd](.artifacts/records/project__check-run/rec-4ff68584-f3f2-42d5-a170-df4ced720bcd.md))_
- **estimate-model**: rec-7eabd5f4-5519-4834-b2f5-2330ed0ff75e; dirty; fail; tdd _(id: [rec-e5b84812-c7d4-4ea5-bfb2-4a89b28fcadc](.artifacts/records/project__check-run/rec-e5b84812-c7d4-4ea5-bfb2-4a89b28fcadc.md))_

## estimate-model-blank

### Acceptance
- **estimate-model-blank**: R7; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_blank_executor _(id: [rec-910eed74-aa0f-4d5f-af8b-aa7323cf0f9a](.artifacts/records/project__acceptance/rec-910eed74-aa0f-4d5f-af8b-aa7323cf0f9a.md))_

### Check
- **estimate-model-blank**: rec-910eed74-aa0f-4d5f-af8b-aa7323cf0f9a; dirty; fail; tdd _(id: [rec-a401ce2e-b2b9-464b-a28c-dc6e140d68df](.artifacts/records/project__check-run/rec-a401ce2e-b2b9-464b-a28c-dc6e140d68df.md))_
- **estimate-model-blank**: rec-910eed74-aa0f-4d5f-af8b-aa7323cf0f9a; dirty; pass; tdd _(id: [rec-cb7813d1-d531-4b31-9efa-c3a57723f722](.artifacts/records/project__check-run/rec-cb7813d1-d531-4b31-9efa-c3a57723f722.md))_

## estimate-model-row

### Acceptance
- **estimate-model-row**: R4; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_row_fields _(id: [rec-18fd0fc9-9da2-4cc0-a5e1-a968d60dac73](.artifacts/records/project__acceptance/rec-18fd0fc9-9da2-4cc0-a5e1-a968d60dac73.md))_

### Check
- **estimate-model-row**: rec-18fd0fc9-9da2-4cc0-a5e1-a968d60dac73; dirty; pass; tdd _(id: [rec-88acb7c5-1acd-420f-b432-6a345415dbf4](.artifacts/records/project__check-run/rec-88acb7c5-1acd-420f-b432-6a345415dbf4.md))_
- **estimate-model-row**: rec-18fd0fc9-9da2-4cc0-a5e1-a968d60dac73; dirty; fail; tdd _(id: [rec-b532893c-2c49-4961-adfc-b72280078026](.artifacts/records/project__check-run/rec-b532893c-2c49-4961-adfc-b72280078026.md))_

## estimate-model-unset

### Acceptance
- **estimate-model-unset**: R3; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_unset_count _(id: [rec-12a895aa-399e-41fb-9955-825515f54673](.artifacts/records/project__acceptance/rec-12a895aa-399e-41fb-9955-825515f54673.md))_

### Check
- **estimate-model-unset**: rec-12a895aa-399e-41fb-9955-825515f54673; dirty; pass; tdd _(id: [rec-8b80532f-21ea-4fa2-bac4-31df00fba144](.artifacts/records/project__check-run/rec-8b80532f-21ea-4fa2-bac4-31df00fba144.md))_
- **estimate-model-unset**: rec-12a895aa-399e-41fb-9955-825515f54673; dirty; fail; tdd _(id: [rec-d8de5685-1a44-49b0-9e5b-eb7ac24eb638](.artifacts/records/project__check-run/rec-d8de5685-1a44-49b0-9e5b-eb7ac24eb638.md))_

## estimate-model-wave

### Acceptance
- **estimate-model-wave**: R2; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_wave_rule _(id: [rec-70638ad0-75c0-4b42-8827-77ec817e3cfd](.artifacts/records/project__acceptance/rec-70638ad0-75c0-4b42-8827-77ec817e3cfd.md))_

### Check
- **estimate-model-wave**: rec-70638ad0-75c0-4b42-8827-77ec817e3cfd; dirty; pass; tdd _(id: [rec-16df7a56-5f25-4f8a-9481-039de8e0b7fb](.artifacts/records/project__check-run/rec-16df7a56-5f25-4f8a-9481-039de8e0b7fb.md))_
- **estimate-model-wave**: rec-70638ad0-75c0-4b42-8827-77ec817e3cfd; dirty; fail; tdd _(id: [rec-aa113976-91b5-4222-9b1b-28736ee0c3d7](.artifacts/records/project__check-run/rec-aa113976-91b5-4222-9b1b-28736ee0c3d7.md))_

## estimate-skill

### Acceptance
- **estimate-skill**: R3; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_skill.py -q -k write _(id: [rec-0106101c-dc9b-4060-bef9-b1dd59a2bd68](.artifacts/records/project__acceptance/rec-0106101c-dc9b-4060-bef9-b1dd59a2bd68.md))_

### Check
- **estimate-skill**: rec-0106101c-dc9b-4060-bef9-b1dd59a2bd68; dirty; fail; tdd _(id: [rec-0a6a2d7f-dec7-444e-901a-677678bf9194](.artifacts/records/project__check-run/rec-0a6a2d7f-dec7-444e-901a-677678bf9194.md))_
- **estimate-skill**: rec-0106101c-dc9b-4060-bef9-b1dd59a2bd68; dirty; pass; tdd _(id: [rec-2b63e40c-65b3-4e1c-b831-27c8382140d7](.artifacts/records/project__check-run/rec-2b63e40c-65b3-4e1c-b831-27c8382140d7.md))_

## estimate-skill-rollup

### Acceptance
- **estimate-skill-rollup**: R4; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_skill.py -q -k rollup _(id: [rec-8ea82af0-405d-4dbb-bb7c-a73bdf063adf](.artifacts/records/project__acceptance/rec-8ea82af0-405d-4dbb-bb7c-a73bdf063adf.md))_

### Check
- **estimate-skill-rollup**: rec-8ea82af0-405d-4dbb-bb7c-a73bdf063adf; dirty; fail; tdd _(id: [rec-4ba11094-3b99-4c8c-b417-c795b942e238](.artifacts/records/project__check-run/rec-4ba11094-3b99-4c8c-b417-c795b942e238.md))_
- **estimate-skill-rollup**: rec-8ea82af0-405d-4dbb-bb7c-a73bdf063adf; dirty; pass; tdd _(id: [rec-ea82231e-3333-4c8a-882f-eb1bddf79085](.artifacts/records/project__check-run/rec-ea82231e-3333-4c8a-882f-eb1bddf79085.md))_

## estimate-skill-sitting

### Acceptance
- **estimate-skill-sitting**: R5; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_skill.py -q -k sitting _(id: [rec-bd586f77-929c-45d7-882a-438a63414019](.artifacts/records/project__acceptance/rec-bd586f77-929c-45d7-882a-438a63414019.md))_

### Check
- **estimate-skill-sitting**: rec-bd586f77-929c-45d7-882a-438a63414019; dirty; fail; tdd _(id: [rec-084cd0fd-376d-43d7-8e5d-85c170d463db](.artifacts/records/project__check-run/rec-084cd0fd-376d-43d7-8e5d-85c170d463db.md))_
- **estimate-skill-sitting**: rec-bd586f77-929c-45d7-882a-438a63414019; dirty; pass; tdd _(id: [rec-4b54f00b-37ee-4871-b92a-3cef04ef3f51](.artifacts/records/project__check-run/rec-4b54f00b-37ee-4871-b92a-3cef04ef3f51.md))_

## estimate-table

### Acceptance
- **estimate-table**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_header_sitting _(id: [rec-0334ff65-b695-433e-97e4-feed4a633233](.artifacts/records/project__acceptance/rec-0334ff65-b695-433e-97e4-feed4a633233.md))_

### Check
- **estimate-table**: rec-0334ff65-b695-433e-97e4-feed4a633233; dirty; pass; tdd _(id: [rec-87bb9a48-ea5a-4252-83c7-a8b9129c983f](.artifacts/records/project__check-run/rec-87bb9a48-ea5a-4252-83c7-a8b9129c983f.md))_
- **estimate-table**: rec-0334ff65-b695-433e-97e4-feed4a633233; dirty; fail; tdd _(id: [rec-d630673d-c238-4e70-9c85-e4f3a86f232e](.artifacts/records/project__check-run/rec-d630673d-c238-4e70-9c85-e4f3a86f232e.md))_

## estimate-table-clip

### Acceptance
- **estimate-table-clip**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_clip _(id: [rec-3c8dcd3a-d259-4881-b1d2-d5c39548776a](.artifacts/records/project__acceptance/rec-3c8dcd3a-d259-4881-b1d2-d5c39548776a.md))_

### Check
- **estimate-table-clip**: rec-3c8dcd3a-d259-4881-b1d2-d5c39548776a; dirty; pass; tdd _(id: [rec-c393e5c3-c7a4-4cfe-b716-003a6b61ff73](.artifacts/records/project__check-run/rec-c393e5c3-c7a4-4cfe-b716-003a6b61ff73.md))_
- **estimate-table-clip**: rec-3c8dcd3a-d259-4881-b1d2-d5c39548776a; dirty; fail; tdd _(id: [rec-ffb6dd08-6bf4-49bb-aaca-02acde2f9a22](.artifacts/records/project__check-run/rec-ffb6dd08-6bf4-49bb-aaca-02acde2f9a22.md))_

## estimate-table-elapsed

### Acceptance
- **estimate-table-elapsed**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_header_elapsed _(id: [rec-d4eb4fe3-27e9-44aa-ac89-9138f8666348](.artifacts/records/project__acceptance/rec-d4eb4fe3-27e9-44aa-ac89-9138f8666348.md))_

### Check
- **estimate-table-elapsed**: rec-d4eb4fe3-27e9-44aa-ac89-9138f8666348; dirty; pass; tdd _(id: [rec-37140203-c1a6-4c53-bbbc-908b2f4d0a54](.artifacts/records/project__check-run/rec-37140203-c1a6-4c53-bbbc-908b2f4d0a54.md))_
- **estimate-table-elapsed**: rec-d4eb4fe3-27e9-44aa-ac89-9138f8666348; dirty; fail; tdd _(id: [rec-f36c677b-5264-4da9-93b2-38ae1d433612](.artifacts/records/project__check-run/rec-f36c677b-5264-4da9-93b2-38ae1d433612.md))_

## estimate-table-partial

### Acceptance
- **estimate-table-partial**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_header_partial _(id: [rec-f4e5899d-ba88-4a58-ad18-718a28db0e16](.artifacts/records/project__acceptance/rec-f4e5899d-ba88-4a58-ad18-718a28db0e16.md))_

### Check
- **estimate-table-partial**: rec-f4e5899d-ba88-4a58-ad18-718a28db0e16; dirty; pass; tdd _(id: [rec-1fac2cf6-7f41-49d6-a4f0-c465aede6986](.artifacts/records/project__check-run/rec-1fac2cf6-7f41-49d6-a4f0-c465aede6986.md))_
- **estimate-table-partial**: rec-f4e5899d-ba88-4a58-ad18-718a28db0e16; dirty; fail; tdd _(id: [rec-6f35022c-32f0-4c9d-a30b-3b9b5e5abee3](.artifacts/records/project__check-run/rec-6f35022c-32f0-4c9d-a30b-3b9b5e5abee3.md))_

## estimate-table-suffix

### Acceptance
- **estimate-table-suffix**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_title_suffix _(id: [rec-c823c876-890c-4582-b8ac-0b8e804b6de6](.artifacts/records/project__acceptance/rec-c823c876-890c-4582-b8ac-0b8e804b6de6.md))_

### Check
- **estimate-table-suffix**: rec-c823c876-890c-4582-b8ac-0b8e804b6de6; dirty; fail; tdd _(id: [rec-2a34d0dc-66e9-4fa4-9611-8aa1d6f0b953](.artifacts/records/project__check-run/rec-2a34d0dc-66e9-4fa4-9611-8aa1d6f0b953.md))_
- **estimate-table-suffix**: rec-c823c876-890c-4582-b8ac-0b8e804b6de6; dirty; pass; tdd _(id: [rec-59eac60c-c027-49fe-87db-04e923f17fb4](.artifacts/records/project__check-run/rec-59eac60c-c027-49fe-87db-04e923f17fb4.md))_

## evidence-authority-review

### Check
- **evidence-authority-review**: evidence-authority-review; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; review _(id: [rec-0b95cf60-9a36-4f25-968b-89ded38ab29e](.artifacts/records/project__check-run/rec-0b95cf60-9a36-4f25-968b-89ded38ab29e.md))_
- **evidence-authority-review**: evidence-authority-review; 46f7be3e4062d8f39f62c3dd22958eb97ec022ad; fail; review _(id: [rec-4d74091c-1d1d-45b6-972a-e6f6ba942cf7](.artifacts/records/project__check-run/rec-4d74091c-1d1d-45b6-972a-e6f6ba942cf7.md))_

## evidence-model

### Acceptance
- **evidence-model**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and requirement' _(id: [rec-d9e2121e-cbda-488a-b93d-f162ca25e09d](.artifacts/records/project__acceptance/rec-d9e2121e-cbda-488a-b93d-f162ca25e09d.md))_

### Check
- **evidence-model**: rec-d9e2121e-cbda-488a-b93d-f162ca25e09d; dirty; pass; tdd _(id: [rec-75cc2533-737d-44ca-8886-1c7d65c86330](.artifacts/records/project__check-run/rec-75cc2533-737d-44ca-8886-1c7d65c86330.md))_

## evidence-model-activity

### Acceptance
- **evidence-model-activity**: R8; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and activity' _(id: [rec-40275e71-0386-466c-9431-b6a06ea32cc4](.artifacts/records/project__acceptance/rec-40275e71-0386-466c-9431-b6a06ea32cc4.md))_

### Check
- **evidence-model-activity**: rec-40275e71-0386-466c-9431-b6a06ea32cc4; dirty; pass; tdd _(id: [rec-ea4330a1-234c-4dcf-9b78-06336c4bfd7c](.artifacts/records/project__check-run/rec-ea4330a1-234c-4dcf-9b78-06336c4bfd7c.md))_

## evidence-model-detail

### Acceptance
- **evidence-model-detail**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and requirement_detail' _(id: [rec-03a4156f-4505-4c4a-84f8-b2dbf28dbc76](.artifacts/records/project__acceptance/rec-03a4156f-4505-4c4a-84f8-b2dbf28dbc76.md))_

### Check
- **evidence-model-detail**: rec-03a4156f-4505-4c4a-84f8-b2dbf28dbc76; dirty; pass; tdd _(id: [rec-58203183-8016-40e0-a8c2-548e817f4ef0](.artifacts/records/project__check-run/rec-58203183-8016-40e0-a8c2-548e817f4ef0.md))_

## evidence-model-legacy

### Acceptance
- **evidence-model-legacy**: R10; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and legacy' _(id: [rec-6d2b9680-5f62-4979-8450-8b3f99e1707b](.artifacts/records/project__acceptance/rec-6d2b9680-5f62-4979-8450-8b3f99e1707b.md))_

### Check
- **evidence-model-legacy**: rec-6d2b9680-5f62-4979-8450-8b3f99e1707b; dirty; pass; tdd _(id: [rec-32f00d17-d4df-4b3d-8848-cd9bdc0c2ec5](.artifacts/records/project__check-run/rec-32f00d17-d4df-4b3d-8848-cd9bdc0c2ec5.md))_

## evidence-model-needs

### Acceptance
- **evidence-model-needs**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and needs' _(id: [rec-b629a582-c0ce-42e7-a2c8-006bf618a411](.artifacts/records/project__acceptance/rec-b629a582-c0ce-42e7-a2c8-006bf618a411.md))_

### Check
- **evidence-model-needs**: rec-b629a582-c0ce-42e7-a2c8-006bf618a411; dirty; pass; tdd _(id: [rec-1867057b-8567-406b-bf2d-6b7c385ce15d](.artifacts/records/project__check-run/rec-1867057b-8567-406b-bf2d-6b7c385ce15d.md))_
- **evidence-model-needs**: rec-b629a582-c0ce-42e7-a2c8-006bf618a411; dirty; fail; tdd _(id: [rec-76f589e6-7586-4851-b503-a7807d36329d](.artifacts/records/project__check-run/rec-76f589e6-7586-4851-b503-a7807d36329d.md))_

## evidence-model-release

### Acceptance
- **evidence-model-release**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and release' _(id: [rec-0ebb72a4-a992-4c0d-804f-e4b659df3ff1](.artifacts/records/project__acceptance/rec-0ebb72a4-a992-4c0d-804f-e4b659df3ff1.md))_

### Check
- **evidence-model-release**: rec-0ebb72a4-a992-4c0d-804f-e4b659df3ff1; dirty; pass; tdd _(id: [rec-5b187fe6-6249-4331-9bec-26a159d82096](.artifacts/records/project__check-run/rec-5b187fe6-6249-4331-9bec-26a159d82096.md))_

## evidence-model-simple

### Acceptance
- **evidence-model-simple**: R9; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and simple' _(id: [rec-5cd3b306-dec8-422d-adcd-d051b9748117](.artifacts/records/project__acceptance/rec-5cd3b306-dec8-422d-adcd-d051b9748117.md))_

### Check
- **evidence-model-simple**: rec-5cd3b306-dec8-422d-adcd-d051b9748117; dirty; pass; tdd _(id: [rec-3998e8e0-527a-419b-a90d-2acf8a4909c6](.artifacts/records/project__check-run/rec-3998e8e0-527a-419b-a90d-2acf8a4909c6.md))_

## evidence-model-stage

### Acceptance
- **evidence-model-stage**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and stage' _(id: [rec-0efed917-d236-4ffc-893e-994b77883d20](.artifacts/records/project__acceptance/rec-0efed917-d236-4ffc-893e-994b77883d20.md))_

### Check
- **evidence-model-stage**: rec-0efed917-d236-4ffc-893e-994b77883d20; dirty; pass; tdd _(id: [rec-f9558ef2-206d-4a6a-804f-81110e945c61](.artifacts/records/project__check-run/rec-f9558ef2-206d-4a6a-804f-81110e945c61.md))_

## evidence-surfaces

### Acceptance
- **evidence-surfaces**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and tally' _(id: [rec-af8be786-2f56-46ed-95a4-4b0e2f42cfcc](.artifacts/records/project__acceptance/rec-af8be786-2f56-46ed-95a4-4b0e2f42cfcc.md))_

### Check
- **evidence-surfaces**: rec-af8be786-2f56-46ed-95a4-4b0e2f42cfcc; dirty; pass; tdd _(id: [rec-5cfeca21-9bd0-4256-8cca-420a1417d46f](.artifacts/records/project__check-run/rec-5cfeca21-9bd0-4256-8cca-420a1417d46f.md))_

## evidence-surfaces-activity

### Acceptance
- **evidence-surfaces-activity**: R8; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and activity' _(id: [rec-f0de4074-6f9b-4db2-96b2-64768ae46a3f](.artifacts/records/project__acceptance/rec-f0de4074-6f9b-4db2-96b2-64768ae46a3f.md))_

### Check
- **evidence-surfaces-activity**: rec-f0de4074-6f9b-4db2-96b2-64768ae46a3f; dirty; pass; tdd _(id: [rec-3be37906-a791-4b99-aad5-e25122eac65d](.artifacts/records/project__check-run/rec-3be37906-a791-4b99-aad5-e25122eac65d.md))_

## evidence-surfaces-needs

### Acceptance
- **evidence-surfaces-needs**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and needs' _(id: [rec-af74e732-3147-46e6-959b-9de2d204d9f8](.artifacts/records/project__acceptance/rec-af74e732-3147-46e6-959b-9de2d204d9f8.md))_

### Check
- **evidence-surfaces-needs**: rec-af74e732-3147-46e6-959b-9de2d204d9f8; dirty; pass; tdd _(id: [rec-08fc31bf-bd1a-40ad-9f21-ae408dc048a4](.artifacts/records/project__check-run/rec-08fc31bf-bd1a-40ad-9f21-ae408dc048a4.md))_

## evidence-surfaces-phase

### Acceptance
- **evidence-surfaces-phase**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and strip' _(id: [rec-11264441-69a2-49e7-bc6f-61337f037af7](.artifacts/records/project__acceptance/rec-11264441-69a2-49e7-bc6f-61337f037af7.md))_

### Check
- **evidence-surfaces-phase**: rec-11264441-69a2-49e7-bc6f-61337f037af7; dirty; pass; tdd _(id: [rec-90e826c4-484d-4d10-9fd5-8a6f87bf92ad](.artifacts/records/project__check-run/rec-90e826c4-484d-4d10-9fd5-8a6f87bf92ad.md))_

## evidence-surfaces-release

### Acceptance
- **evidence-surfaces-release**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and release' _(id: [rec-1e0e0e59-dc14-4393-96b8-8b865ab34368](.artifacts/records/project__acceptance/rec-1e0e0e59-dc14-4393-96b8-8b865ab34368.md))_

### Check
- **evidence-surfaces-release**: rec-1e0e0e59-dc14-4393-96b8-8b865ab34368; dirty; pass; tdd _(id: [rec-e03ccf51-fd4a-4e4a-a1f0-7d5093ac3e67](.artifacts/records/project__check-run/rec-e03ccf51-fd4a-4e4a-a1f0-7d5093ac3e67.md))_

## evidence-surfaces-requirements

### Acceptance
- **evidence-surfaces-requirements**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and requirement_list' _(id: [rec-4e3b28bd-22b8-4af2-8798-0bc134ff47ab](.artifacts/records/project__acceptance/rec-4e3b28bd-22b8-4af2-8798-0bc134ff47ab.md))_

### Check
- **evidence-surfaces-requirements**: rec-4e3b28bd-22b8-4af2-8798-0bc134ff47ab; dirty; pass; tdd _(id: [rec-ef989920-a210-4bd1-986d-f2b418d3ae09](.artifacts/records/project__check-run/rec-ef989920-a210-4bd1-986d-f2b418d3ae09.md))_

## evidence-surfaces-simple

### Acceptance
- **evidence-surfaces-simple**: R9; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and simple' _(id: [rec-6d5d3021-1e7d-4938-9385-d0112fce7aa8](.artifacts/records/project__acceptance/rec-6d5d3021-1e7d-4938-9385-d0112fce7aa8.md))_

### Check
- **evidence-surfaces-simple**: rec-6d5d3021-1e7d-4938-9385-d0112fce7aa8; dirty; pass; tdd _(id: [rec-dea38843-a2f4-4f86-97c7-5e6ced92905e](.artifacts/records/project__check-run/rec-dea38843-a2f4-4f86-97c7-5e6ced92905e.md))_

## evidence-surfaces-stepper

### Acceptance
- **evidence-surfaces-stepper**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and stepper' _(id: [rec-dea24b5b-9884-4880-a246-013ea423d317](.artifacts/records/project__acceptance/rec-dea24b5b-9884-4880-a246-013ea423d317.md))_

### Check
- **evidence-surfaces-stepper**: rec-dea24b5b-9884-4880-a246-013ea423d317; dirty; pass; tdd _(id: [rec-78421eb1-b798-4c33-9e5f-269a77204ed1](.artifacts/records/project__check-run/rec-78421eb1-b798-4c33-9e5f-269a77204ed1.md))_

## execute-landing

### Acceptance
- **execute-landing**: tdd; workflow-loop; python3 -m pytest tests/test_execute_landing.py -q _(id: [rec-b89f9c9f-d9f4-4db9-8375-3f877388c961](.artifacts/records/project__acceptance/rec-b89f9c9f-d9f4-4db9-8375-3f877388c961.md))_

### Check
- **execute-landing**: rec-b89f9c9f-d9f4-4db9-8375-3f877388c961; dirty; pass; tdd _(id: [rec-db1a2d05-c946-4377-9044-a73c9a9dfb5b](.artifacts/records/project__check-run/rec-db1a2d05-c946-4377-9044-a73c9a9dfb5b.md))_

## execute-wave-dispatch

### Acceptance
- **execute-wave-dispatch**: tdd; workflow-loop; python3 -m pytest tests/test_execute_wave_dispatch.py -q _(id: [rec-c95855b2-e077-44d7-ab61-b8b70ec6f7df](.artifacts/records/project__acceptance/rec-c95855b2-e077-44d7-ab61-b8b70ec6f7df.md))_

### Check
- **execute-wave-dispatch**: rec-c95855b2-e077-44d7-ab61-b8b70ec6f7df; dirty; pass; tdd _(id: [rec-07c3a7ec-2a6e-424c-84a0-b633eb4949bd](.artifacts/records/project__check-run/rec-07c3a7ec-2a6e-424c-84a0-b633eb4949bd.md))_

## finished-effort-view

### Acceptance
- **finished-effort-view**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k finished _(id: [rec-cc216932-78bb-4df8-b80d-8da0eb287a9c](.artifacts/records/project__acceptance/rec-cc216932-78bb-4df8-b80d-8da0eb287a9c.md))_

### Check
- **finished-effort-view**: rec-cc216932-78bb-4df8-b80d-8da0eb287a9c; 11fdbbe31fe4a60f1985ccc24fa41788fa83d1d5; pass; tdd _(id: [rec-9e17ccb9-1b70-4843-ade6-cabf22d52de2](.artifacts/records/project__check-run/rec-9e17ccb9-1b70-4843-ade6-cabf22d52de2.md))_

## fix-apply-ops

### Acceptance
- **fix-apply-ops**: R19; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_apply_ops.py::test_r19_apply_persists_supersede_correct_and_contradict tests/test_apply_ops.py::test_r19_apply_bad_line_does_not_abort tests/test_apply_ops.py::test_r19_command_apply_persists_supersede_correct_and_contradict tests/test_apply_ops.py::test_r19_command_apply_bad_line_does_not_abort -q _(id: [rec-8e9f45f6-685f-4008-bfc2-8bf6640e4ee1](.artifacts/records/project__acceptance/rec-8e9f45f6-685f-4008-bfc2-8bf6640e4ee1.md))_

### Check
- **fix-apply-ops**: rec-8e9f45f6-685f-4008-bfc2-8bf6640e4ee1; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-53616aa0-0b96-4978-b9bb-772b9a7a5fbd](.artifacts/records/project__check-run/rec-53616aa0-0b96-4978-b9bb-772b9a7a5fbd.md))_
- **fix-apply-ops**: rec-8e9f45f6-685f-4008-bfc2-8bf6640e4ee1; dirty; fail; tdd _(id: [rec-8d95b3f1-3772-4531-94ea-0a5b37c042c5](.artifacts/records/project__check-run/rec-8d95b3f1-3772-4531-94ea-0a5b37c042c5.md))_

## fix-claim-gate-e2e

### Acceptance
- **fix-claim-gate-e2e**: R1,R8,R9; check; library-boundary; python3 -m pytest tests/test_claim_clocks.py tests/test_close_batch.py tests/test_orchestra_callers.py tests/test_library_e2e.py "tests/test_verify_authority.py::test_close_batch_still_creates_manual_check_runs" -q _(id: [rec-063c49d8-6bef-4f8d-8003-02802dd9109b](.artifacts/records/project__acceptance/rec-063c49d8-6bef-4f8d-8003-02802dd9109b.md))_

### Check
- **fix-claim-gate-e2e**: rec-063c49d8-6bef-4f8d-8003-02802dd9109b; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-b39203b6-7f3a-4a22-aae3-0feced56cb1a](.artifacts/records/project__check-run/rec-b39203b6-7f3a-4a22-aae3-0feced56cb1a.md))_
- **fix-claim-gate-e2e**: rec-063c49d8-6bef-4f8d-8003-02802dd9109b; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-db612c89-afce-4bb3-bd20-44d57db3f69a](.artifacts/records/project__check-run/rec-db612c89-afce-4bb3-bd20-44d57db3f69a.md))_

## fix-claim-gate-hardening

### Acceptance
- **fix-claim-gate-hardening**: R5; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'claim_gate' _(id: [rec-43215a07-b490-49f1-9631-fb8bb14dbb93](.artifacts/records/project__acceptance/rec-43215a07-b490-49f1-9631-fb8bb14dbb93.md))_

### Check
- **fix-claim-gate-hardening**: rec-43215a07-b490-49f1-9631-fb8bb14dbb93; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-2fe17b26-d2fa-44a9-9b73-729701dc73ad](.artifacts/records/project__check-run/rec-2fe17b26-d2fa-44a9-9b73-729701dc73ad.md))_
- **fix-claim-gate-hardening**: rec-43215a07-b490-49f1-9631-fb8bb14dbb93; 46f7be3e4062d8f39f62c3dd22958eb97ec022ad; pass; tdd _(id: [rec-52a73c3d-1e32-440a-af4a-806a2bd9404d](.artifacts/records/project__check-run/rec-52a73c3d-1e32-440a-af4a-806a2bd9404d.md))_
- **fix-claim-gate-hardening**: rec-43215a07-b490-49f1-9631-fb8bb14dbb93; dirty; fail; tdd _(id: [rec-5db3b94d-948d-4f36-a05e-a0c69689bf50](.artifacts/records/project__check-run/rec-5db3b94d-948d-4f36-a05e-a0c69689bf50.md))_
- **fix-claim-gate-hardening**: rec-43215a07-b490-49f1-9631-fb8bb14dbb93; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-b9c96d24-986b-486c-a580-2da7aae1bb1d](.artifacts/records/project__check-run/rec-b9c96d24-986b-486c-a580-2da7aae1bb1d.md))_

## fix-claim-gate-regressions

### Acceptance
- **fix-claim-gate-regressions**: R1,R5,R6,R8; check; library-boundary; python3 -m pytest tests/test_claim_clocks.py tests/test_close_batch.py tests/test_orchestra_callers.py "tests/test_verify_authority.py::test_close_batch_still_creates_manual_check_runs" -q _(id: [rec-0a2ec5bf-6ac6-4f03-b4de-22432adc9b42](.artifacts/records/project__acceptance/rec-0a2ec5bf-6ac6-4f03-b4de-22432adc9b42.md))_

### Check
- **fix-claim-gate-regressions**: rec-0a2ec5bf-6ac6-4f03-b4de-22432adc9b42; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-cd9e532f-cf0f-4990-a7ea-0119121e28d6](.artifacts/records/project__check-run/rec-cd9e532f-cf0f-4990-a7ea-0119121e28d6.md))_
- **fix-claim-gate-regressions**: rec-0a2ec5bf-6ac6-4f03-b4de-22432adc9b42; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-d06e22df-fb90-4d65-9fec-3c1cabbe066d](.artifacts/records/project__check-run/rec-d06e22df-fb90-4d65-9fec-3c1cabbe066d.md))_
- **fix-claim-gate-regressions**: rec-0a2ec5bf-6ac6-4f03-b4de-22432adc9b42; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-d6aa29ed-7ea1-452a-bfc9-1cff7ccaaddb](.artifacts/records/project__check-run/rec-d6aa29ed-7ea1-452a-bfc9-1cff7ccaaddb.md))_

## fix-claim-gate-unit-hook

### Acceptance
- **fix-claim-gate-unit-hook**: R8; check; library-boundary; python3 -m pytest tests/test_close_batch.py tests/test_claim_clocks.py -q _(id: [rec-bc4ef8c1-37df-4189-8243-5f910bb0fe84](.artifacts/records/project__acceptance/rec-bc4ef8c1-37df-4189-8243-5f910bb0fe84.md))_

### Check
- **fix-claim-gate-unit-hook**: rec-bc4ef8c1-37df-4189-8243-5f910bb0fe84; 3ac0f0d6a5017dda68d15fd812ead47178e46029; pass; check _(id: [rec-2d0c6537-1800-46e7-98d0-faf6eaba180b](.artifacts/records/project__check-run/rec-2d0c6537-1800-46e7-98d0-faf6eaba180b.md))_
- **fix-claim-gate-unit-hook**: rec-bc4ef8c1-37df-4189-8243-5f910bb0fe84; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-43dae7c7-e35d-44b7-a6b1-cf7147e36b84](.artifacts/records/project__check-run/rec-43dae7c7-e35d-44b7-a6b1-cf7147e36b84.md))_
- **fix-claim-gate-unit-hook**: rec-bc4ef8c1-37df-4189-8243-5f910bb0fe84; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-fb871313-931f-4eae-a7b0-0ce027236a06](.artifacts/records/project__check-run/rec-fb871313-931f-4eae-a7b0-0ce027236a06.md))_

## fix-cli-runtime-surface

### Acceptance
- **fix-cli-runtime-surface**: R6; check; packaging; python3 -m pytest tests/test_cli_surface.py -q _(id: [rec-410904bd-1380-4a65-b217-c9bcdc1406f6](.artifacts/records/project__acceptance/rec-410904bd-1380-4a65-b217-c9bcdc1406f6.md))_

### Check
- **fix-cli-runtime-surface**: rec-410904bd-1380-4a65-b217-c9bcdc1406f6; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-52b278c9-9633-47c4-a1bd-50b4bb5060bf](.artifacts/records/project__check-run/rec-52b278c9-9633-47c4-a1bd-50b4bb5060bf.md))_
- **fix-cli-runtime-surface**: rec-410904bd-1380-4a65-b217-c9bcdc1406f6; 5a5e5b1aa2d88e6e64ace0dc6073134c5a8b9e45; pass; check _(id: [rec-d9206295-c966-47fc-bbb8-58ba4f1c77ca](.artifacts/records/project__check-run/rec-d9206295-c966-47fc-bbb8-58ba4f1c77ca.md))_

## fix-cli-runtime-surface-skills

### Acceptance
- **fix-cli-runtime-surface-skills**: R7; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k runtime _(id: [rec-01c893b8-ad15-48b9-be21-b4036a804a99](.artifacts/records/project__acceptance/rec-01c893b8-ad15-48b9-be21-b4036a804a99.md))_

### Check
- **fix-cli-runtime-surface-skills**: rec-01c893b8-ad15-48b9-be21-b4036a804a99; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-29d0d54b-555f-41b0-ac70-42fbda296d28](.artifacts/records/project__check-run/rec-29d0d54b-555f-41b0-ac70-42fbda296d28.md))_
- **fix-cli-runtime-surface-skills**: rec-01c893b8-ad15-48b9-be21-b4036a804a99; 5a5e5b1aa2d88e6e64ace0dc6073134c5a8b9e45; pass; check _(id: [rec-aff5814c-8fe3-4d73-ba9a-c6ef47cd85e9](.artifacts/records/project__check-run/rec-aff5814c-8fe3-4d73-ba9a-c6ef47cd85e9.md))_

## fix-cli-standalone

### Acceptance
- **fix-cli-standalone**: R5; check; packaging; python3 -m pytest tests/test_cli_packaging.py -q -k standalone _(id: [rec-7679b134-94c1-400d-b741-58f92ad52ba9](.artifacts/records/project__acceptance/rec-7679b134-94c1-400d-b741-58f92ad52ba9.md))_

### Check
- **fix-cli-standalone**: rec-7679b134-94c1-400d-b741-58f92ad52ba9; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-07056854-3849-4222-bd8e-a714210ba44a](.artifacts/records/project__check-run/rec-07056854-3849-4222-bd8e-a714210ba44a.md))_
- **fix-cli-standalone**: rec-7679b134-94c1-400d-b741-58f92ad52ba9; 5530668c970b18fc76a90f447874d1b9d67c5fbf; pass; check _(id: [rec-dba36a14-061b-470d-aa1d-096708d8fa85](.artifacts/records/project__check-run/rec-dba36a14-061b-470d-aa1d-096708d8fa85.md))_

## fix-contract-record-types

### Acceptance
- **fix-contract-record-types**: R3; check; workflow-loop; python3 -c "import json;from pathlib import Path;d=json.loads(Path('contract/project-design.json').read_text());assert 'record_types' not in d;types={t['name']:t for t in d['records']};a=types['acceptance'];assert 'test_ids' in a['payload'] and 'oracle_hashes' in a['payload'];assert 'oracle-amendment' in types" _(id: [rec-bb17c5ee-0385-4c8e-90d2-3fe5f9e2b519](.artifacts/records/project__acceptance/rec-bb17c5ee-0385-4c8e-90d2-3fe5f9e2b519.md))_

### Check
- **fix-contract-record-types**: rec-bb17c5ee-0385-4c8e-90d2-3fe5f9e2b519; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-aba4e75b-a9a6-4a25-b792-f30f48fee08b](.artifacts/records/project__check-run/rec-aba4e75b-a9a6-4a25-b792-f30f48fee08b.md))_

## fix-dashboard-uv-env

### Acceptance
- **fix-dashboard-uv-env**: R2; tdd; library-boundary; python3 -m pytest tests/test_dashboard_uv_env.py::test_r2 -q _(id: [rec-83da71d0-5c67-4995-94f0-d9e2f9a99e58](.artifacts/records/project__acceptance/rec-83da71d0-5c67-4995-94f0-d9e2f9a99e58.md))_

### Check
- **fix-dashboard-uv-env**: rec-83da71d0-5c67-4995-94f0-d9e2f9a99e58; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-823545ce-12f6-4087-b688-2168262355d5](.artifacts/records/project__check-run/rec-823545ce-12f6-4087-b688-2168262355d5.md))_
- **fix-dashboard-uv-env**: rec-83da71d0-5c67-4995-94f0-d9e2f9a99e58; 0e74b79533477eb27ae4523175667097f175b470; fail; tdd _(id: [rec-b73c9165-83eb-4223-a989-d7bf382ed36a](.artifacts/records/project__check-run/rec-b73c9165-83eb-4223-a989-d7bf382ed36a.md))_

## fix-docs-and-hooks

### Acceptance
- **fix-docs-and-hooks**: R15; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q _(id: [rec-b98522f2-478d-4583-aee3-5ed705b1cb80](.artifacts/records/project__acceptance/rec-b98522f2-478d-4583-aee3-5ed705b1cb80.md))_

### Check
- **fix-docs-and-hooks**: rec-b98522f2-478d-4583-aee3-5ed705b1cb80; 483c621e1d813b9fe92d70b0c9c59a53d3080f79; pass; check _(id: [rec-592559f9-0f53-4a62-b95a-d5cd7067580f](.artifacts/records/project__check-run/rec-592559f9-0f53-4a62-b95a-d5cd7067580f.md))_
- **fix-docs-and-hooks**: rec-b98522f2-478d-4583-aee3-5ed705b1cb80; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-87af8f6c-25d9-4579-aa87-eab9ff908432](.artifacts/records/project__check-run/rec-87af8f6c-25d9-4579-aa87-eab9ff908432.md))_

## fix-docs-and-hooks-claude

### Acceptance
- **fix-docs-and-hooks-claude**: R12; check; packaging; python3 -m pytest tests/test_installer.py -q -k hooks _(id: [rec-dbe94c7c-4d38-41c1-abb8-a0be5fac9de0](.artifacts/records/project__acceptance/rec-dbe94c7c-4d38-41c1-abb8-a0be5fac9de0.md))_

### Check
- **fix-docs-and-hooks-claude**: rec-dbe94c7c-4d38-41c1-abb8-a0be5fac9de0; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-95aa7eba-e710-4806-9f6c-5f65524bb8a1](.artifacts/records/project__check-run/rec-95aa7eba-e710-4806-9f6c-5f65524bb8a1.md))_
- **fix-docs-and-hooks-claude**: rec-dbe94c7c-4d38-41c1-abb8-a0be5fac9de0; 483c621e1d813b9fe92d70b0c9c59a53d3080f79; pass; check _(id: [rec-ffa8e912-7e53-4dcb-a8de-3f2a5e6744ff](.artifacts/records/project__check-run/rec-ffa8e912-7e53-4dcb-a8de-3f2a5e6744ff.md))_

## fix-human-gate-constraint

### Acceptance
- **fix-human-gate-constraint**: R7; check; workflow-loop; /home/andrewyin/adaptive-artifacts/bin/adaptive-artifacts --store /home/andrewyin/se-workflow/.artifacts list --type project:constraint --state active | python3 -c "import sys,json; d=json.load(sys.stdin); stmts=[(r['subject'], (r.get('payload') or {}).get('statement') or '') for r in d['records']]; hg=[t for s,t in stmts if s=='dashboard-human-gate-writes']; assert hg; t=hg[0].lower(); assert 'needs-you' in t or 'human' in t; assert 'backlog' in t and (('promote' in t) or ('dismiss' in t)); old={'dashboard-read-only','dashboard-read-only-dashboard-bugfix','dashboard-read-only-dashboard-features'}; assert not any('never writes' in x.lower() for s,x in stmts if s in old)" _(id: [rec-7cd14081-b40c-4643-9c77-8ead22c68483](.artifacts/records/project__acceptance/rec-7cd14081-b40c-4643-9c77-8ead22c68483.md))_

### Check
- **fix-human-gate-constraint**: rec-7cd14081-b40c-4643-9c77-8ead22c68483; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; check _(id: [rec-1ed320a3-c828-48d4-8de2-9969706b2fa7](.artifacts/records/project__check-run/rec-1ed320a3-c828-48d4-8de2-9969706b2fa7.md))_

## fix-journal-pager-timeout

### Acceptance
- **fix-journal-pager-timeout**: tdd; packaging; uv run --with textual --with pytest python -m pytest tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub -q _(id: [rec-83a0060b-ad9d-4ebf-9d9d-50a91677b1ff](.artifacts/records/project__acceptance/rec-83a0060b-ad9d-4ebf-9d9d-50a91677b1ff.md))_

### Check
- **fix-journal-pager-timeout**: rec-83a0060b-ad9d-4ebf-9d9d-50a91677b1ff; dirty; fail; tdd _(id: [rec-2483b603-ab08-40c0-b787-865baebd1002](.artifacts/records/project__check-run/rec-2483b603-ab08-40c0-b787-865baebd1002.md))_
- **fix-journal-pager-timeout**: rec-83a0060b-ad9d-4ebf-9d9d-50a91677b1ff; 3379fcf8a1d882d91330bec6e66a2889c71d3ece; pass; tdd _(id: [rec-67c47e4a-2545-4d89-93a9-c83f34293e09](.artifacts/records/project__check-run/rec-67c47e4a-2545-4d89-93a9-c83f34293e09.md))_

## fix-library-e2e-coverage

### Acceptance
- **fix-library-e2e-coverage**: R4; check; library-boundary; PATH="$(pwd)/bin:$PATH" python3 -m pytest tests/test_library_e2e.py::test_library_fixture_close -q && python3 -c 'import pathlib; text=pathlib.Path("tests/test_library_e2e.py").read_text(); assert "open_store" in text' _(id: [rec-1ffa67ad-1fe2-4897-b96a-6b604a6ebc20](.artifacts/records/project__acceptance/rec-1ffa67ad-1fe2-4897-b96a-6b604a6ebc20.md))_

### Check
- **fix-library-e2e-coverage**: rec-1ffa67ad-1fe2-4897-b96a-6b604a6ebc20; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-857934dd-06d9-4df4-a234-6801f37bd2ed](.artifacts/records/project__check-run/rec-857934dd-06d9-4df4-a234-6801f37bd2ed.md))_
- **fix-library-e2e-coverage**: rec-1ffa67ad-1fe2-4897-b96a-6b604a6ebc20; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-ebdea641-e61b-4331-b266-704231e53cf6](.artifacts/records/project__check-run/rec-ebdea641-e61b-4331-b266-704231e53cf6.md))_

## fix-library-e2e-coverage-close

### Acceptance
- **fix-library-e2e-coverage-close**: R5; check; library-boundary; PATH="$(pwd)/bin:$PATH" python3 -m pytest tests/test_library_e2e.py::test_library_fixture_close -q && python3 -c 'import pathlib; text=pathlib.Path("tests/test_library_e2e.py").read_text(); assert "except Exception" not in text; assert "close_batch.main" in text' _(id: [rec-4ac13b10-acd4-43c8-9be5-0caa34e731b7](.artifacts/records/project__acceptance/rec-4ac13b10-acd4-43c8-9be5-0caa34e731b7.md))_

### Check
- **fix-library-e2e-coverage-close**: rec-4ac13b10-acd4-43c8-9be5-0caa34e731b7; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-65c5af65-187c-491a-adb9-f5537d10b523](.artifacts/records/project__check-run/rec-65c5af65-187c-491a-adb9-f5537d10b523.md))_
- **fix-library-e2e-coverage-close**: rec-4ac13b10-acd4-43c8-9be5-0caa34e731b7; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-92760386-266a-48cb-bc28-41f48191f4c1](.artifacts/records/project__check-run/rec-92760386-266a-48cb-bc28-41f48191f4c1.md))_

## fix-library-e2e-coverage-quiet

### Acceptance
- **fix-library-e2e-coverage-quiet**: R6; check; library-boundary; PATH="$(pwd)/bin:$PATH" python3 -m pytest tests/test_library_e2e.py::test_library_fixture_close -q && python3 -c 'import pathlib; text=pathlib.Path("tests/test_library_e2e.py").read_text(); assert "adaptive-artifacts" in text and "\"aff\"" in text' _(id: [rec-7ac471de-c228-42b0-a323-a077f55f89a4](.artifacts/records/project__acceptance/rec-7ac471de-c228-42b0-a323-a077f55f89a4.md))_

### Check
- **fix-library-e2e-coverage-quiet**: rec-7ac471de-c228-42b0-a323-a077f55f89a4; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-20971657-cab3-4df7-8b8f-8a9c066148e1](.artifacts/records/project__check-run/rec-20971657-cab3-4df7-8b8f-8a9c066148e1.md))_
- **fix-library-e2e-coverage-quiet**: rec-7ac471de-c228-42b0-a323-a077f55f89a4; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-28c42bf4-ce33-4f81-bb6e-cc30c8cdb229](.artifacts/records/project__check-run/rec-28c42bf4-ce33-4f81-bb6e-cc30c8cdb229.md))_

## fix-opencode-shape

### Acceptance
- **fix-opencode-shape**: R12; check; packaging; python3 -m pytest tests/test_installer.py tests/integration/test_temp_home_install.py -q -k "opencode or hooks or temp_home" _(id: [rec-965ea0a8-074d-4189-8f2c-731114177cbc](.artifacts/records/project__acceptance/rec-965ea0a8-074d-4189-8f2c-731114177cbc.md))_

### Check
- **fix-opencode-shape**: rec-965ea0a8-074d-4189-8f2c-731114177cbc; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-2835ed57-1248-4044-ab66-ae8991640b9b](.artifacts/records/project__check-run/rec-2835ed57-1248-4044-ab66-ae8991640b9b.md))_
- **fix-opencode-shape**: rec-965ea0a8-074d-4189-8f2c-731114177cbc; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-8aaa5354-6d3c-45b4-a770-7c78d21bb20b](.artifacts/records/project__check-run/rec-8aaa5354-6d3c-45b4-a770-7c78d21bb20b.md))_

## fix-opencode-shape-agent

### Acceptance
- **fix-opencode-shape-agent**: R13; check; packaging; python3 -m pytest tests/test_agent_generation.py tests/test_installer.py -q -k "opencode" _(id: [rec-bfe782cd-0f27-4337-a426-f20168376f5f](.artifacts/records/project__acceptance/rec-bfe782cd-0f27-4337-a426-f20168376f5f.md))_

### Check
- **fix-opencode-shape-agent**: rec-bfe782cd-0f27-4337-a426-f20168376f5f; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-17bda9b5-5fdf-4905-9058-0a8c68a57760](.artifacts/records/project__check-run/rec-17bda9b5-5fdf-4905-9058-0a8c68a57760.md))_
- **fix-opencode-shape-agent**: rec-bfe782cd-0f27-4337-a426-f20168376f5f; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-48e98d32-826f-4ce5-8b55-bb34a5e671d7](.artifacts/records/project__check-run/rec-48e98d32-826f-4ce5-8b55-bb34a5e671d7.md))_

## fix-oracle-cli-tests

### Acceptance
- **fix-oracle-cli-tests**: R5; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'cli and (oracle or freeze or assertion_level or amendment)' _(id: [rec-8aba909a-63ea-4152-a144-11f5d525f8d5](.artifacts/records/project__acceptance/rec-8aba909a-63ea-4152-a144-11f5d525f8d5.md))_

### Check
- **fix-oracle-cli-tests**: rec-8aba909a-63ea-4152-a144-11f5d525f8d5; b9adc0ee0836b843fd963ca38ad105d5e2176b68; pass; tdd _(id: [rec-5ee53854-9e43-481e-997b-bee6443d52e6](.artifacts/records/project__check-run/rec-5ee53854-9e43-481e-997b-bee6443d52e6.md))_
- **fix-oracle-cli-tests**: rec-8aba909a-63ea-4152-a144-11f5d525f8d5; 977750c3c4f05015bcf03d4b82c77d25c8f039d3; fail; tdd _(id: [rec-6f50bc76-c2f3-44b2-bdfc-7279817d2ba4](.artifacts/records/project__check-run/rec-6f50bc76-c2f3-44b2-bdfc-7279817d2ba4.md))_
- **fix-oracle-cli-tests**: rec-8aba909a-63ea-4152-a144-11f5d525f8d5; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; tdd _(id: [rec-a11cc5d6-ce65-4990-b34c-b712b614669f](.artifacts/records/project__check-run/rec-a11cc5d6-ce65-4990-b34c-b712b614669f.md))_

## fix-oracle-red-missing-aff

### Acceptance
- **fix-oracle-red-missing-aff**: R9; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py::test_oracle_red_refuses_when_aff_cli_classification_fails tests/test_close_batch.py -q -k 'oracle_red or assertion' _(id: [rec-8975b1cb-f384-4cf1-8d8d-75ed45266b61](.artifacts/records/project__acceptance/rec-8975b1cb-f384-4cf1-8d8d-75ed45266b61.md))_

### Check
- **fix-oracle-red-missing-aff**: rec-8975b1cb-f384-4cf1-8d8d-75ed45266b61; dirty; fail; tdd _(id: [rec-4f7a3431-afff-4e85-8c91-91c8620b8cfa](.artifacts/records/project__check-run/rec-4f7a3431-afff-4e85-8c91-91c8620b8cfa.md))_
- **fix-oracle-red-missing-aff**: rec-8975b1cb-f384-4cf1-8d8d-75ed45266b61; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-6936786e-02c2-4af7-a00f-1a54cde54db2](.artifacts/records/project__check-run/rec-6936786e-02c2-4af7-a00f-1a54cde54db2.md))_
- **fix-oracle-red-missing-aff**: rec-8975b1cb-f384-4cf1-8d8d-75ed45266b61; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-c036675c-d67d-4c5c-b770-bd15365ac36d](.artifacts/records/project__check-run/rec-c036675c-d67d-4c5c-b770-bd15365ac36d.md))_

## fix-phase-gate-defaults

### Acceptance
- **fix-phase-gate-defaults**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py -q -k phase_gate && python3 -c "import json; from pathlib import Path; b=json.loads(Path('contract/project-design.json').read_text())['phase_gate']['suite']; assert b['mode']=='none' and b.get('command','')==''; a=json.loads(Path('.artifacts/project-design.json').read_text())['phase_gate']['suite']; assert a['mode']=='full' and a['gate']=='advisory' and 'pytest' in a['command']" _(id: [rec-bf2a6f65-d5f0-4838-ad1f-4c257fcf5ce1](.artifacts/records/project__acceptance/rec-bf2a6f65-d5f0-4838-ad1f-4c257fcf5ce1.md))_

### Check
- **fix-phase-gate-defaults**: rec-bf2a6f65-d5f0-4838-ad1f-4c257fcf5ce1; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; tdd _(id: [rec-1986d942-554f-4a01-810d-2a794235bc4a](.artifacts/records/project__check-run/rec-1986d942-554f-4a01-810d-2a794235bc4a.md))_
- **fix-phase-gate-defaults**: rec-bf2a6f65-d5f0-4838-ad1f-4c257fcf5ce1; 846e07f37ff5afe6fe37b1475facaeda210e6945; fail; tdd _(id: [rec-cb903d8e-dce4-4967-8446-4c01083b8c65](.artifacts/records/project__check-run/rec-cb903d8e-dce4-4967-8446-4c01083b8c65.md))_
- **fix-phase-gate-defaults**: rec-bf2a6f65-d5f0-4838-ad1f-4c257fcf5ce1; 3e813f617e5811a742014ffc95c70e6709dfc281; pass; tdd _(id: [rec-db0e8af2-7139-4546-a2a8-607b16e683a7](.artifacts/records/project__check-run/rec-db0e8af2-7139-4546-a2a8-607b16e683a7.md))_

## fix-reviewer-selfcontainment

### Acceptance
- **fix-reviewer-selfcontainment**: R1; check; packaging; python3 -m pytest tests/test_skill_portability.py -q _(id: [rec-dd72d8b5-6632-49e4-a7dd-e160e74495d2](.artifacts/records/project__acceptance/rec-dd72d8b5-6632-49e4-a7dd-e160e74495d2.md))_

### Check
- **fix-reviewer-selfcontainment**: rec-dd72d8b5-6632-49e4-a7dd-e160e74495d2; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-4d2a0e2c-7d35-485c-a47b-166ea6993a5e](.artifacts/records/project__check-run/rec-4d2a0e2c-7d35-485c-a47b-166ea6993a5e.md))_
- **fix-reviewer-selfcontainment**: rec-dd72d8b5-6632-49e4-a7dd-e160e74495d2; 72467c123d9963e2b98429e0d66738a53b65607a; pass; check _(id: [rec-5d794980-df90-4fd1-8dd1-e3d75eb204fb](.artifacts/records/project__check-run/rec-5d794980-df90-4fd1-8dd1-e3d75eb204fb.md))_

## fix-reviewer-selfcontainment-canonical

### Acceptance
- **fix-reviewer-selfcontainment-canonical**: R13; check; packaging; python3 -m pytest tests/test_agent_generation.py -q _(id: [rec-32789158-613a-4053-adf2-e25c9055898b](.artifacts/records/project__acceptance/rec-32789158-613a-4053-adf2-e25c9055898b.md))_

### Check
- **fix-reviewer-selfcontainment-canonical**: rec-32789158-613a-4053-adf2-e25c9055898b; 72467c123d9963e2b98429e0d66738a53b65607a; pass; check _(id: [rec-02dbcbfd-195f-4da5-989a-f0611710267f](.artifacts/records/project__check-run/rec-02dbcbfd-195f-4da5-989a-f0611710267f.md))_
- **fix-reviewer-selfcontainment-canonical**: rec-32789158-613a-4053-adf2-e25c9055898b; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-e3809802-0e45-42a0-a019-b2c0b0a097b3](.artifacts/records/project__check-run/rec-e3809802-0e45-42a0-a019-b2c0b0a097b3.md))_

## fix-test_dashboard_app

### Acceptance
- **fix-test_dashboard_app**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'running_row_status_shows_its_running_time or footer_has_no_palette or detail_related_panel_lists_related_records' _(id: [rec-d2f35534-584a-4e18-b439-3641ec83969d](.artifacts/records/project__acceptance/rec-d2f35534-584a-4e18-b439-3641ec83969d.md))_

### Check
- **fix-test_dashboard_app**: rec-d2f35534-584a-4e18-b439-3641ec83969d; dirty; pass; tdd _(id: [rec-c01b17e8-2ecb-4d56-a364-324cd98b402e](.artifacts/records/project__check-run/rec-c01b17e8-2ecb-4d56-a364-324cd98b402e.md))_
- **fix-test_dashboard_app**: rec-d2f35534-584a-4e18-b439-3641ec83969d; 2f7404eab494720b703ffd0e2e01078236a876ab; pass; tdd _(id: [rec-c2bb099d-b561-4751-9063-0c3a95a508ec](.artifacts/records/project__check-run/rec-c2bb099d-b561-4751-9063-0c3a95a508ec.md))_

## fix-test_dashboard_journal

### Acceptance
- **fix-test_dashboard_journal**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_journal.py -q -k journal_panel_shows_for_repair_kind _(id: [rec-3df8eb5b-21db-4624-8831-12b8bdc2a294](.artifacts/records/project__acceptance/rec-3df8eb5b-21db-4624-8831-12b8bdc2a294.md))_

### Check
- **fix-test_dashboard_journal**: rec-3df8eb5b-21db-4624-8831-12b8bdc2a294; dirty; pass; tdd _(id: [rec-0863cd5c-7440-4218-8155-5bf3d3c2ff35](.artifacts/records/project__check-run/rec-0863cd5c-7440-4218-8155-5bf3d3c2ff35.md))_
- **fix-test_dashboard_journal**: rec-3df8eb5b-21db-4624-8831-12b8bdc2a294; 2f7404eab494720b703ffd0e2e01078236a876ab; pass; tdd _(id: [rec-f968b020-0e52-4016-a7e1-432bc354f41b](.artifacts/records/project__check-run/rec-f968b020-0e52-4016-a7e1-432bc354f41b.md))_

## fix-test_discuss_skill

### Acceptance
- **fix-test_discuss_skill**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_discuss_skill.py -q -k plan_phase_opens_a_blocking_plan_review_question _(id: [rec-7a209b57-ff35-4f91-b06b-41f8057aecef](.artifacts/records/project__acceptance/rec-7a209b57-ff35-4f91-b06b-41f8057aecef.md))_

### Check
- **fix-test_discuss_skill**: rec-7a209b57-ff35-4f91-b06b-41f8057aecef; 2f7404eab494720b703ffd0e2e01078236a876ab; pass; tdd _(id: [rec-2db0a42c-4698-4121-bdc9-7daf4749d1d4](.artifacts/records/project__check-run/rec-2db0a42c-4698-4121-bdc9-7daf4749d1d4.md))_
- **fix-test_discuss_skill**: rec-7a209b57-ff35-4f91-b06b-41f8057aecef; dirty; fail; tdd _(id: [rec-5f1fbf64-77e1-4d1b-b3ce-5d52ea252a75](.artifacts/records/project__check-run/rec-5f1fbf64-77e1-4d1b-b3ce-5d52ea252a75.md))_

## fix-test_evidence_loop

### Acceptance
- **fix-test_evidence_loop**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_evidence_loop.py -q -k check_run_result_and_method_are_contract_enums _(id: [rec-be712a69-03e1-4ea1-a1e1-b0534ae0b828](.artifacts/records/project__acceptance/rec-be712a69-03e1-4ea1-a1e1-b0534ae0b828.md))_

### Check
- **fix-test_evidence_loop**: rec-be712a69-03e1-4ea1-a1e1-b0534ae0b828; 2f7404eab494720b703ffd0e2e01078236a876ab; pass; tdd _(id: [rec-a10d7f0b-0e2c-4f35-a269-2afd2c76ec1a](.artifacts/records/project__check-run/rec-a10d7f0b-0e2c-4f35-a269-2afd2c76ec1a.md))_
- **fix-test_evidence_loop**: rec-be712a69-03e1-4ea1-a1e1-b0534ae0b828; dirty; pass; tdd _(id: [rec-f36113f3-83c1-4d55-afb0-ae1ab32433d1](.artifacts/records/project__check-run/rec-f36113f3-83c1-4d55-afb0-ae1ab32433d1.md))_

## fix-test_plan_landing

### Acceptance
- **fix-test_plan_landing**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_plan_landing.py -q -k plan_review_stays_closed_until_landing _(id: [rec-47fbfa19-5038-4851-830d-42a55a72a49e](.artifacts/records/project__acceptance/rec-47fbfa19-5038-4851-830d-42a55a72a49e.md))_

### Check
- **fix-test_plan_landing**: rec-47fbfa19-5038-4851-830d-42a55a72a49e; 2f7404eab494720b703ffd0e2e01078236a876ab; pass; tdd _(id: [rec-3872f5a3-92d9-462a-bbc9-a18e3c83ba7e](.artifacts/records/project__check-run/rec-3872f5a3-92d9-462a-bbc9-a18e3c83ba7e.md))_
- **fix-test_plan_landing**: rec-47fbfa19-5038-4851-830d-42a55a72a49e; dirty; pass; tdd _(id: [rec-b585900a-70ef-43b3-ac03-688d876df257](.artifacts/records/project__check-run/rec-b585900a-70ef-43b3-ac03-688d876df257.md))_

## fix-test_plan_wave_rules

### Acceptance
- **fix-test_plan_wave_rules**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_plan_wave_rules.py -q -k plan_review_stays_closed_until_recipe _(id: [rec-f0ad8c81-df6e-457c-8553-9dd57d03f91e](.artifacts/records/project__acceptance/rec-f0ad8c81-df6e-457c-8553-9dd57d03f91e.md))_

### Check
- **fix-test_plan_wave_rules**: rec-f0ad8c81-df6e-457c-8553-9dd57d03f91e; dirty; pass; tdd _(id: [rec-010f08e6-8773-48a3-95de-c92efae83877](.artifacts/records/project__check-run/rec-010f08e6-8773-48a3-95de-c92efae83877.md))_
- **fix-test_plan_wave_rules**: rec-f0ad8c81-df6e-457c-8553-9dd57d03f91e; 2f7404eab494720b703ffd0e2e01078236a876ab; pass; tdd _(id: [rec-ab7a14d0-d11a-458f-a40e-c14ffe4dc4c0](.artifacts/records/project__check-run/rec-ab7a14d0-d11a-458f-a40e-c14ffe4dc4c0.md))_

## fix-test_verify_authority

### Acceptance
- **fix-test_verify_authority**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_authority.py -q -k 'skill_close_request_references_check_run_id or close_batch_does_not_emit_check_run_create' _(id: [rec-e09c9aac-f876-43da-9856-41ed79b75404](.artifacts/records/project__acceptance/rec-e09c9aac-f876-43da-9856-41ed79b75404.md))_

### Check
- **fix-test_verify_authority**: rec-e09c9aac-f876-43da-9856-41ed79b75404; dirty; pass; tdd _(id: [rec-5e5e7943-0cfe-47be-bdc1-7c6c5ca5fe32](.artifacts/records/project__check-run/rec-5e5e7943-0cfe-47be-bdc1-7c6c5ca5fe32.md))_
- **fix-test_verify_authority**: rec-e09c9aac-f876-43da-9856-41ed79b75404; 2f7404eab494720b703ffd0e2e01078236a876ab; pass; tdd _(id: [rec-9dbbcb14-8061-4f28-87e0-56bbddc01a16](.artifacts/records/project__check-run/rec-9dbbcb14-8061-4f28-87e0-56bbddc01a16.md))_

## fix-verify-authority-close-batch-import

### Acceptance
- **fix-verify-authority-close-batch-import**: tdd; packaging; uv run --with pytest python -m pytest tests/test_verify_authority.py -q _(id: [rec-a33322af-14f2-44fd-a072-5bc4073fa8a2](.artifacts/records/project__acceptance/rec-a33322af-14f2-44fd-a072-5bc4073fa8a2.md))_

### Check
- **fix-verify-authority-close-batch-import**: rec-a33322af-14f2-44fd-a072-5bc4073fa8a2; 8109e9aae50c888bd17a06bfb3b8f9e2f55665ab; pass; tdd _(id: [rec-5e5de649-bc10-4d3b-b158-d8f754e7c6c1](.artifacts/records/project__check-run/rec-5e5de649-bc10-4d3b-b158-d8f754e7c6c1.md))_
- **fix-verify-authority-close-batch-import**: rec-a33322af-14f2-44fd-a072-5bc4073fa8a2; dirty; fail; tdd _(id: [rec-774d2cea-d57a-49c8-93c4-0f7cb73285ac](.artifacts/records/project__check-run/rec-774d2cea-d57a-49c8-93c4-0f7cb73285ac.md))_

## format-gate

### Acceptance
- **format-gate**: R8; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store_format.py::test_r8_open_store_raises_for_unsupported_contract_format -q _(id: [rec-af52e6e4-1191-4b01-8d7a-637858e467b2](.artifacts/records/project__acceptance/rec-af52e6e4-1191-4b01-8d7a-637858e467b2.md))_

### Check
- **format-gate**: rec-af52e6e4-1191-4b01-8d7a-637858e467b2; 559343f7b683b2c79510e3b7781aba7a4e93721b; pass; tdd _(id: [rec-11ebce7c-e3de-4ab1-a6d2-6318703778c2](.artifacts/records/project__check-run/rec-11ebce7c-e3de-4ab1-a6d2-6318703778c2.md))_
- **format-gate**: rec-af52e6e4-1191-4b01-8d7a-637858e467b2; 8b5b6bb45b08e93ada5a737081faad5117d3538e; fail; tdd _(id: [rec-1be83400-44cd-4a84-9dd6-3c925de97548](.artifacts/records/project__check-run/rec-1be83400-44cd-4a84-9dd6-3c925de97548.md))_
- **format-gate**: rec-af52e6e4-1191-4b01-8d7a-637858e467b2; dirty; fail; tdd _(id: [rec-fff36c07-b76d-4c3c-a421-28949f5a9119](.artifacts/records/project__check-run/rec-fff36c07-b76d-4c3c-a421-28949f5a9119.md))_

## gates-landing

### Acceptance
- **gates-landing**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_gates.py -q -k 'landing and not (nogr or readonly)' _(id: [rec-79184477-3098-4868-8374-96e8edb0d92c](.artifacts/records/project__acceptance/rec-79184477-3098-4868-8374-96e8edb0d92c.md))_

### Check
- **gates-landing**: rec-79184477-3098-4868-8374-96e8edb0d92c; dirty; pass; tdd _(id: [rec-ac631f0f-5f7e-4ff1-87c5-eb980c002e01](.artifacts/records/project__check-run/rec-ac631f0f-5f7e-4ff1-87c5-eb980c002e01.md))_

## gates-landing-failsoft

### Acceptance
- **gates-landing-failsoft**: R10; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_gates.py -q -k 'nogr or no_git or fail' _(id: [rec-03da42d3-f54d-49ba-8ca2-afca1260b398](.artifacts/records/project__acceptance/rec-03da42d3-f54d-49ba-8ca2-afca1260b398.md))_

### Check
- **gates-landing-failsoft**: rec-03da42d3-f54d-49ba-8ca2-afca1260b398; dirty; pass; tdd _(id: [rec-77950a7e-4aba-4694-b411-a5cab13fe76d](.artifacts/records/project__check-run/rec-77950a7e-4aba-4694-b411-a5cab13fe76d.md))_

## gates-landing-readonly

### Acceptance
- **gates-landing-readonly**: R11; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_gates.py -q -k readonly _(id: [rec-3ba5ea87-0663-4f77-9a0e-ef0a6da1fc3e](.artifacts/records/project__acceptance/rec-3ba5ea87-0663-4f77-9a0e-ef0a6da1fc3e.md))_

### Check
- **gates-landing-readonly**: rec-3ba5ea87-0663-4f77-9a0e-ef0a6da1fc3e; dirty; pass; tdd _(id: [rec-30fee293-6832-4850-bdce-e7dc53b760a6](.artifacts/records/project__check-run/rec-30fee293-6832-4850-bdce-e7dc53b760a6.md))_

## gates-model

### Acceptance
- **gates-model**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_gates.py -q -k "gates and (merge or landing_item)" _(id: [rec-72691ffa-0dcd-45d0-a9dc-4cabce493d6e](.artifacts/records/project__acceptance/rec-72691ffa-0dcd-45d0-a9dc-4cabce493d6e.md))_

### Check
- **gates-model**: rec-72691ffa-0dcd-45d0-a9dc-4cabce493d6e; dirty; pass; tdd _(id: [rec-8953d20c-a86f-4baa-a24c-4e2880aff9bb](.artifacts/records/project__check-run/rec-8953d20c-a86f-4baa-a24c-4e2880aff9bb.md))_

## gates-model-quiet

### Acceptance
- **gates-model-quiet**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_tasks.py -q -k "gates and quiet" _(id: [rec-bbb94de7-ae26-498b-ae76-2528eb547de3](.artifacts/records/project__acceptance/rec-bbb94de7-ae26-498b-ae76-2528eb547de3.md))_

### Check
- **gates-model-quiet**: rec-bbb94de7-ae26-498b-ae76-2528eb547de3; dirty; pass; tdd _(id: [rec-49e5e75a-5390-4d96-a3ac-a3f19faa538a](.artifacts/records/project__check-run/rec-49e5e75a-5390-4d96-a3ac-a3f19faa538a.md))_

## gates-status

### Acceptance
- **gates-status**: R8; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests -q -m tmux -k "status and (gates or needs or segment)" _(id: [rec-bec7c314-2052-4053-9d5a-3f78a5db6663](.artifacts/records/project__acceptance/rec-bec7c314-2052-4053-9d5a-3f78a5db6663.md))_

### Check
- **gates-status**: rec-bec7c314-2052-4053-9d5a-3f78a5db6663; dirty; pass; tdd _(id: [rec-d5bb5ebd-2833-4597-bfc7-ecf8bfee067a](.artifacts/records/project__check-run/rec-d5bb5ebd-2833-4597-bfc7-ecf8bfee067a.md))_

## gates-ui

### Acceptance
- **gates-ui**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "gates and (copy or prompt)" _(id: [rec-6a06a80a-ba89-47c8-8d09-ef1c546ddbb6](.artifacts/records/project__acceptance/rec-6a06a80a-ba89-47c8-8d09-ef1c546ddbb6.md))_

### Check
- **gates-ui**: rec-6a06a80a-ba89-47c8-8d09-ef1c546ddbb6; dirty; pass; tdd _(id: [rec-b41e3704-d094-429c-8b4e-c0549f937bf9](.artifacts/records/project__check-run/rec-b41e3704-d094-429c-8b4e-c0549f937bf9.md))_

## gates-ui-alert

### Acceptance
- **gates-ui-alert**: R9; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "gates and (alert or bell or message)" _(id: [rec-eafbbe7b-d2e4-4c00-8ade-b19308d28efd](.artifacts/records/project__acceptance/rec-eafbbe7b-d2e4-4c00-8ade-b19308d28efd.md))_

### Check
- **gates-ui-alert**: rec-eafbbe7b-d2e4-4c00-8ade-b19308d28efd; dirty; pass; tdd _(id: [rec-11fa611b-b22c-4461-beda-193333d0b769](.artifacts/records/project__check-run/rec-11fa611b-b22c-4461-beda-193333d0b769.md))_

## gates-ui-next

### Acceptance
- **gates-ui-next**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "gates and next" _(id: [rec-f1684acd-c413-4721-bdc5-4b9b28b25793](.artifacts/records/project__acceptance/rec-f1684acd-c413-4721-bdc5-4b9b28b25793.md))_

### Check
- **gates-ui-next**: rec-f1684acd-c413-4721-bdc5-4b9b28b25793; dirty; pass; tdd _(id: [rec-d238e363-b7a8-42bb-8a24-a4a03abf0d89](.artifacts/records/project__check-run/rec-d238e363-b7a8-42bb-8a24-a4a03abf0d89.md))_

## gates-vocab

### Acceptance
- **gates-vocab**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'gates and (label or plan_review or action)' _(id: [rec-dda923b2-838f-49de-82f7-3d6b9e8e648d](.artifacts/records/project__acceptance/rec-dda923b2-838f-49de-82f7-3d6b9e8e648d.md))_

### Check
- **gates-vocab**: rec-dda923b2-838f-49de-82f7-3d6b9e8e648d; dirty; pass; tdd _(id: [rec-333e89ae-61cf-4b06-a898-ae1f07b3465f](.artifacts/records/project__check-run/rec-333e89ae-61cf-4b06-a898-ae1f07b3465f.md))_
- **gates-vocab**: rec-dda923b2-838f-49de-82f7-3d6b9e8e648d; dirty; pass; tdd _(id: [rec-722bd310-6ac0-48c4-96e1-312514ce34b9](.artifacts/records/project__check-run/rec-722bd310-6ac0-48c4-96e1-312514ce34b9.md))_

## gates-vocab-next

### Acceptance
- **gates-vocab-next**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'gates and next_step' _(id: [rec-3724b87a-e342-4a93-ad2e-32b3dbf21060](.artifacts/records/project__acceptance/rec-3724b87a-e342-4a93-ad2e-32b3dbf21060.md))_

### Check
- **gates-vocab-next**: rec-3724b87a-e342-4a93-ad2e-32b3dbf21060; dirty; pass; tdd _(id: [rec-461ab218-714c-4e32-b5ff-b5bd26054b97](.artifacts/records/project__check-run/rec-461ab218-714c-4e32-b5ff-b5bd26054b97.md))_

## gates-vocab-prompt

### Acceptance
- **gates-vocab-prompt**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'gates and prompt' _(id: [rec-287530b8-fbf2-465a-b92d-5e699772d5de](.artifacts/records/project__acceptance/rec-287530b8-fbf2-465a-b92d-5e699772d5de.md))_

### Check
- **gates-vocab-prompt**: rec-287530b8-fbf2-465a-b92d-5e699772d5de; dirty; pass; tdd _(id: [rec-b32e7854-688c-4f90-8680-870d767ee6ee](.artifacts/records/project__check-run/rec-b32e7854-688c-4f90-8680-870d767ee6ee.md))_

## gates-vocab-quiet

### Acceptance
- **gates-vocab-quiet**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'gates and quiet' _(id: [rec-0292d7ca-96a5-452c-aa18-2b9dd5029589](.artifacts/records/project__acceptance/rec-0292d7ca-96a5-452c-aa18-2b9dd5029589.md))_

### Check
- **gates-vocab-quiet**: rec-0292d7ca-96a5-452c-aa18-2b9dd5029589; dirty; pass; tdd _(id: [rec-f923fa9e-6830-4792-9fb7-223e0d9dbc54](.artifacts/records/project__check-run/rec-f923fa9e-6830-4792-9fb7-223e0d9dbc54.md))_

## goal-status-field

### Acceptance
- **goal-status-field**: tdd; workflow-loop; python3 -m pytest tests/test_goal_close.py -q _(id: [rec-1f0b047c-50e6-4c2d-8c91-10a6c7d220e0](.artifacts/records/project__acceptance/rec-1f0b047c-50e6-4c2d-8c91-10a6c7d220e0.md))_

### Check
- **goal-status-field**: rec-1f0b047c-50e6-4c2d-8c91-10a6c7d220e0; 8f1c9bbbb89ef3dc90f3fa36d00c83b924f2a721; pass; tdd _(id: [rec-700a7fec-ed34-4ade-8cb4-1f5c163aad2d](.artifacts/records/project__check-run/rec-700a7fec-ed34-4ade-8cb4-1f5c163aad2d.md))_

## handoff-by-effort

### Acceptance
- **handoff-by-effort**: tdd; workflow-loop; python3 -m pytest tests/test_phase_position.py -q _(id: [rec-ca16958b-e8a5-4605-a0cd-7bf1a556bd31](.artifacts/records/project__acceptance/rec-ca16958b-e8a5-4605-a0cd-7bf1a556bd31.md))_

### Check
- **handoff-by-effort**: rec-ca16958b-e8a5-4605-a0cd-7bf1a556bd31; 8d0b7fd43309d93b0b7f2b3db0a3f8a1022e405b; pass; tdd _(id: [rec-19b91624-50af-404d-b9b4-31576913a4be](.artifacts/records/project__check-run/rec-19b91624-50af-404d-b9b4-31576913a4be.md))_

## header-chrome

### Acceptance
- **header-chrome**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "tab_row or tab_labels or number_keys_filter or status_tabs_are_six" _(id: [rec-82ce4065-bcee-43f2-97b2-dfd7a995d323](.artifacts/records/project__acceptance/rec-82ce4065-bcee-43f2-97b2-dfd7a995d323.md))_

### Check
- **header-chrome**: rec-c87d332c-5c16-49a9-9ebe-8991ae8c0060; dirty; pass; tdd _(id: [rec-59a00c7d-27b5-4e7d-9bba-bd5f7d6dd8aa](.artifacts/records/project__check-run/rec-59a00c7d-27b5-4e7d-9bba-bd5f7d6dd8aa.md))_
- **header-chrome**: rec-f93137e4-8a54-4459-a68a-59963e362cbd; dirty; pass; tdd _(id: [rec-c7a5b9cc-1faa-4956-90c4-3a9f401b9c70](.artifacts/records/project__check-run/rec-c7a5b9cc-1faa-4956-90c4-3a9f401b9c70.md))_
- **header-chrome**: rec-82ce4065-bcee-43f2-97b2-dfd7a995d323; dirty; pass; tdd _(id: [rec-e76b0864-a17a-42d2-a008-193fc0b2c787](.artifacts/records/project__check-run/rec-e76b0864-a17a-42d2-a008-193fc0b2c787.md))_
- **header-chrome**: rec-c5330e71-ef6d-401a-856d-dbdfdeb167d6; dirty; pass; tdd _(id: [rec-f16ee258-cdfc-4735-8a63-31e1da8c699d](.artifacts/records/project__check-run/rec-f16ee258-cdfc-4735-8a63-31e1da8c699d.md))_

## header-chrome-headers

### Acceptance
- **header-chrome-headers**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k done_phases_collapse _(id: [rec-c5330e71-ef6d-401a-856d-dbdfdeb167d6](.artifacts/records/project__acceptance/rec-c5330e71-ef6d-401a-856d-dbdfdeb167d6.md))_

## header-chrome-once

### Acceptance
- **header-chrome-once**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k once_tally _(id: [rec-f93137e4-8a54-4459-a68a-59963e362cbd](.artifacts/records/project__acceptance/rec-f93137e4-8a54-4459-a68a-59963e362cbd.md))_

## header-chrome-stepper

### Acceptance
- **header-chrome-stepper**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k stepper _(id: [rec-c87d332c-5c16-49a9-9ebe-8991ae8c0060](.artifacts/records/project__acceptance/rec-c87d332c-5c16-49a9-9ebe-8991ae8c0060.md))_

## heading-spacing

### Acceptance
- **heading-spacing**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k heading _(id: [rec-e3cb339f-2f12-42bd-9dab-4439494334aa](.artifacts/records/project__acceptance/rec-e3cb339f-2f12-42bd-9dab-4439494334aa.md))_

### Check
- **heading-spacing**: rec-e3cb339f-2f12-42bd-9dab-4439494334aa; d6f518bc2b5c2f8f4ae54c678c9ffaf5c8949b6c; pass; tdd _(id: [rec-fb47b275-bf18-4ae2-8c81-21e6ebe99fce](.artifacts/records/project__check-run/rec-fb47b275-bf18-4ae2-8c81-21e6ebe99fce.md))_

## honest-runner-stamp

### Acceptance
- **honest-runner-stamp**: R1; tdd; workflow-loop; python3 -m pytest tests/test_affidavit_check.py::test_check_writes_runner_orchestra -q _(id: [rec-06168a96-378d-436e-91d5-0aee4b6a186f](.artifacts/records/project__acceptance/rec-06168a96-378d-436e-91d5-0aee4b6a186f.md))_

### Check
- **honest-runner-stamp**: rec-06168a96-378d-436e-91d5-0aee4b6a186f; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-2be99441-3065-4af3-8511-f19230c18bcf](.artifacts/records/project__check-run/rec-2be99441-3065-4af3-8511-f19230c18bcf.md))_
- **honest-runner-stamp**: rec-06168a96-378d-436e-91d5-0aee4b6a186f; 51cd740b7588ae41ef9a50360d992d6995d1e09d; fail; tdd _(id: [rec-310f3d2e-ec6e-4d02-be64-7390444cf945](.artifacts/records/project__check-run/rec-310f3d2e-ec6e-4d02-be64-7390444cf945.md))_
- **honest-runner-stamp**: rec-06168a96-378d-436e-91d5-0aee4b6a186f; dirty; fail; tdd _(id: [rec-50bd0186-353b-4152-a8b7-c74b1d545197](.artifacts/records/project__check-run/rec-50bd0186-353b-4152-a8b7-c74b1d545197.md))_
- **honest-runner-stamp**: rec-06168a96-378d-436e-91d5-0aee4b6a186f; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-75b1397f-10b1-4aac-8435-b143f39437dd](.artifacts/records/project__check-run/rec-75b1397f-10b1-4aac-8435-b143f39437dd.md))_
- **honest-runner-stamp**: rec-06168a96-378d-436e-91d5-0aee4b6a186f; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-88bf994b-dd80-432d-b50c-b1dfe8e375d7](.artifacts/records/project__check-run/rec-88bf994b-dd80-432d-b50c-b1dfe8e375d7.md))_
- **honest-runner-stamp**: rec-06168a96-378d-436e-91d5-0aee4b6a186f; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-b74a7e77-3e0f-4b96-ad85-7c2cc2ab9e93](.artifacts/records/project__check-run/rec-b74a7e77-3e0f-4b96-ad85-7c2cc2ab9e93.md))_
- **honest-runner-stamp**: rec-06168a96-378d-436e-91d5-0aee4b6a186f; dirty; fail; tdd _(id: [rec-ff39cce1-2af2-4a3a-9308-1091059707bc](.artifacts/records/project__check-run/rec-ff39cce1-2af2-4a3a-9308-1091059707bc.md))_

## honest-runner-stamp-accept

### Acceptance
- **honest-runner-stamp-accept**: R3; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py::test_close_batch_accepts_orchestra_runner_stamp -q _(id: [rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860](.artifacts/records/project__acceptance/rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860.md))_

### Check
- **honest-runner-stamp-accept**: rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-0345d65e-a00c-43d1-92ea-e1d24a8b12ad](.artifacts/records/project__check-run/rec-0345d65e-a00c-43d1-92ea-e1d24a8b12ad.md))_
- **honest-runner-stamp-accept**: rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-1606a5e2-947f-411f-a783-e03597054f61](.artifacts/records/project__check-run/rec-1606a5e2-947f-411f-a783-e03597054f61.md))_
- **honest-runner-stamp-accept**: rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860; dirty; fail; tdd _(id: [rec-3e6a6441-ebd9-4214-9dc2-ecad4bc227ca](.artifacts/records/project__check-run/rec-3e6a6441-ebd9-4214-9dc2-ecad4bc227ca.md))_
- **honest-runner-stamp-accept**: rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860; dirty; fail; tdd _(id: [rec-4148799b-a1bf-4712-8428-68727bb56ced](.artifacts/records/project__check-run/rec-4148799b-a1bf-4712-8428-68727bb56ced.md))_
- **honest-runner-stamp-accept**: rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860; 51cd740b7588ae41ef9a50360d992d6995d1e09d; fail; tdd _(id: [rec-9cd09c3f-313d-4e32-82cc-ca25483f41e7](.artifacts/records/project__check-run/rec-9cd09c3f-313d-4e32-82cc-ca25483f41e7.md))_
- **honest-runner-stamp-accept**: rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-d731193c-1e0f-4e23-8099-32ea3245896d](.artifacts/records/project__check-run/rec-d731193c-1e0f-4e23-8099-32ea3245896d.md))_
- **honest-runner-stamp-accept**: rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-df96cb00-b09a-41c4-8c37-f729f78681d2](.artifacts/records/project__check-run/rec-df96cb00-b09a-41c4-8c37-f729f78681d2.md))_

## honest-runner-stamp-refuse-aff

### Acceptance
- **honest-runner-stamp-refuse-aff**: R4; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py::test_close_batch_refuses_aff_runner_stamp -q _(id: [rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3](.artifacts/records/project__acceptance/rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3.md))_

### Check
- **honest-runner-stamp-refuse-aff**: rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3; dirty; fail; tdd _(id: [rec-1b79a96c-6b46-4aaf-a751-a9a4398c650b](.artifacts/records/project__check-run/rec-1b79a96c-6b46-4aaf-a751-a9a4398c650b.md))_
- **honest-runner-stamp-refuse-aff**: rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-3248e330-1e0f-4627-be87-98636fe42154](.artifacts/records/project__check-run/rec-3248e330-1e0f-4627-be87-98636fe42154.md))_
- **honest-runner-stamp-refuse-aff**: rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-41ebda06-0058-4a22-9abb-187b82d44e7c](.artifacts/records/project__check-run/rec-41ebda06-0058-4a22-9abb-187b82d44e7c.md))_
- **honest-runner-stamp-refuse-aff**: rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-bc1aec29-773b-4333-823f-6ccb81f92e47](.artifacts/records/project__check-run/rec-bc1aec29-773b-4333-823f-6ccb81f92e47.md))_
- **honest-runner-stamp-refuse-aff**: rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3; 51cd740b7588ae41ef9a50360d992d6995d1e09d; fail; tdd _(id: [rec-c84c6d57-f5b4-4db3-a90f-a31bf7472500](.artifacts/records/project__check-run/rec-c84c6d57-f5b4-4db3-a90f-a31bf7472500.md))_
- **honest-runner-stamp-refuse-aff**: rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-d98b69d2-4982-4a47-b13b-64c86f154eca](.artifacts/records/project__check-run/rec-d98b69d2-4982-4a47-b13b-64c86f154eca.md))_
- **honest-runner-stamp-refuse-aff**: rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3; dirty; fail; tdd _(id: [rec-ee6da65a-abd9-44fa-84f6-3d55a6e38ae2](.artifacts/records/project__check-run/rec-ee6da65a-abd9-44fa-84f6-3d55a6e38ae2.md))_

## honest-runner-stamp-suite

### Acceptance
- **honest-runner-stamp-suite**: R2; tdd; workflow-loop; python3 -m pytest tests/test_tiered_verification.py::test_suite_record_writes_runner_orchestra -q _(id: [rec-3a9261a1-b666-48fc-a9b4-068838f86307](.artifacts/records/project__acceptance/rec-3a9261a1-b666-48fc-a9b4-068838f86307.md))_

### Check
- **honest-runner-stamp-suite**: rec-3a9261a1-b666-48fc-a9b4-068838f86307; dirty; fail; tdd _(id: [rec-45ae5c08-ea40-48dc-ade1-3db6d4267cb7](.artifacts/records/project__check-run/rec-45ae5c08-ea40-48dc-ade1-3db6d4267cb7.md))_
- **honest-runner-stamp-suite**: rec-3a9261a1-b666-48fc-a9b4-068838f86307; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-59c6a01b-5e57-406f-b57a-e2b33b3cf38e](.artifacts/records/project__check-run/rec-59c6a01b-5e57-406f-b57a-e2b33b3cf38e.md))_
- **honest-runner-stamp-suite**: rec-3a9261a1-b666-48fc-a9b4-068838f86307; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-64fecb33-02ab-449d-9a55-39a030921686](.artifacts/records/project__check-run/rec-64fecb33-02ab-449d-9a55-39a030921686.md))_
- **honest-runner-stamp-suite**: rec-3a9261a1-b666-48fc-a9b4-068838f86307; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-7e7cad1d-ed29-4152-88e7-f028ac475604](.artifacts/records/project__check-run/rec-7e7cad1d-ed29-4152-88e7-f028ac475604.md))_
- **honest-runner-stamp-suite**: rec-3a9261a1-b666-48fc-a9b4-068838f86307; dirty; fail; tdd _(id: [rec-865a70c7-6a39-4d03-82ec-3691fbb45ac1](.artifacts/records/project__check-run/rec-865a70c7-6a39-4d03-82ec-3691fbb45ac1.md))_
- **honest-runner-stamp-suite**: rec-3a9261a1-b666-48fc-a9b4-068838f86307; 51cd740b7588ae41ef9a50360d992d6995d1e09d; fail; tdd _(id: [rec-d6f5cf54-d7e7-4cf5-9848-c1c584417a8b](.artifacts/records/project__check-run/rec-d6f5cf54-d7e7-4cf5-9848-c1c584417a8b.md))_
- **honest-runner-stamp-suite**: rec-3a9261a1-b666-48fc-a9b4-068838f86307; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-d8e675ea-fa2f-49c3-914f-88bd3413f8d1](.artifacts/records/project__check-run/rec-d8e675ea-fa2f-49c3-914f-88bd3413f8d1.md))_

## import-open

### Acceptance
- **import-open**: R7; check; library-boundary; PYTHONPATH=. python3 -c 'import os,subprocess; from pathlib import Path
for n in ("ADAPTIVE_ARTIFACTS_BIN","CLAUDE_PLUGIN_ROOT","CURSOR_PLUGIN_ROOT"): os.environ.pop(n, None)
seen=[]
real=subprocess.run
def spy(cmd,*a,**k):
 seen.append(cmd); return real(cmd,*a,**k)
subprocess.run=spy
import orchestra.aa as aa
aa.find_store_root(Path(".").resolve())
def bad(cmd):
 parts=cmd if isinstance(cmd,(list,tuple)) else [cmd]
 return any(Path(str(p)).name in {"adaptive-artifacts","artifacts.py"} for p in parts)
assert not any(bad(c) for c in seen)' _(id: [rec-625650b6-a012-4a20-b260-a24d0b258d9e](.artifacts/records/project__acceptance/rec-625650b6-a012-4a20-b260-a24d0b258d9e.md))_

### Check
- **import-open**: rec-625650b6-a012-4a20-b260-a24d0b258d9e; e3fe8e65d40593cda4d782a96e99c75f0e478cef; pass; check _(id: [rec-6ccb8aa5-1971-47bc-b2a9-d3010f5f74a8](.artifacts/records/project__check-run/rec-6ccb8aa5-1971-47bc-b2a9-d3010f5f74a8.md))_

## install-docs

### Acceptance
- **install-docs**: R15; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q _(id: [rec-b516429d-be99-4476-83d3-64a4b82392c8](.artifacts/records/project__acceptance/rec-b516429d-be99-4476-83d3-64a4b82392c8.md))_

### Check
- **install-docs**: rec-b516429d-be99-4476-83d3-64a4b82392c8; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-364e0e0b-6bcb-43e8-b4a6-6c9a0d13b8fe](.artifacts/records/project__check-run/rec-364e0e0b-6bcb-43e8-b4a6-6c9a0d13b8fe.md))_
- **install-docs**: rec-b516429d-be99-4476-83d3-64a4b82392c8; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-bfc44786-483b-4193-9d1e-1d8caaea980f](.artifacts/records/project__check-run/rec-bfc44786-483b-4193-9d1e-1d8caaea980f.md))_
- **install-docs**: rec-b516429d-be99-4476-83d3-64a4b82392c8; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-d17f9904-fd4b-43bb-8bc6-9043402edc45](.artifacts/records/project__check-run/rec-d17f9904-fd4b-43bb-8bc6-9043402edc45.md))_

## installer-cli-flags

### Acceptance
- **installer-cli-flags**: R1; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k tty_launches_wizard _(id: [rec-ac532bec-9f8b-47e4-89a3-67a34e6fdb1c](.artifacts/records/project__acceptance/rec-ac532bec-9f8b-47e4-89a3-67a34e6fdb1c.md))_

### Check
- **installer-cli-flags**: rec-ac532bec-9f8b-47e4-89a3-67a34e6fdb1c; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-43e2e091-a779-4afd-86df-cf9d21a3f5ad](.artifacts/records/project__check-run/rec-43e2e091-a779-4afd-86df-cf9d21a3f5ad.md))_

## installer-cli-flags-decline

### Acceptance
- **installer-cli-flags-decline**: R9; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k decline_writes_nothing _(id: [rec-99ea1141-cec9-436d-a16a-fb87159c4987](.artifacts/records/project__acceptance/rec-99ea1141-cec9-436d-a16a-fb87159c4987.md))_

### Check
- **installer-cli-flags-decline**: rec-99ea1141-cec9-436d-a16a-fb87159c4987; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-e2ac2898-1f59-44dc-bdc9-a403e1b45a17](.artifacts/records/project__check-run/rec-e2ac2898-1f59-44dc-bdc9-a403e1b45a17.md))_

## installer-cli-flags-dry-run

### Acceptance
- **installer-cli-flags-dry-run**: R16; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k dry_run_skips_confirmation _(id: [rec-fe8c1884-4010-4fd6-9898-a6e397f0c78e](.artifacts/records/project__acceptance/rec-fe8c1884-4010-4fd6-9898-a6e397f0c78e.md))_

### Check
- **installer-cli-flags-dry-run**: rec-fe8c1884-4010-4fd6-9898-a6e397f0c78e; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-fc442301-edb1-422d-975d-5ac479951da6](.artifacts/records/project__check-run/rec-fc442301-edb1-422d-975d-5ac479951da6.md))_

## installer-cli-flags-empty

### Acceptance
- **installer-cli-flags-empty**: R14; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k no_detection_no_tty _(id: [rec-1a4bcb36-db8d-495e-891c-d0d6a52337b1](.artifacts/records/project__acceptance/rec-1a4bcb36-db8d-495e-891c-d0d6a52337b1.md))_

### Check
- **installer-cli-flags-empty**: rec-1a4bcb36-db8d-495e-891c-d0d6a52337b1; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-e656c65e-f463-451b-854e-38febf582c29](.artifacts/records/project__check-run/rec-e656c65e-f463-451b-854e-38febf582c29.md))_

## installer-cli-flags-explicit

### Acceptance
- **installer-cli-flags-explicit**: R15; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k explicit_flags _(id: [rec-9d928709-d211-4d2c-b43e-6e2b75c8fbce](.artifacts/records/project__acceptance/rec-9d928709-d211-4d2c-b43e-6e2b75c8fbce.md))_

### Check
- **installer-cli-flags-explicit**: rec-9d928709-d211-4d2c-b43e-6e2b75c8fbce; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-e7b9cd8c-4103-443e-b186-e300fd9c40d5](.artifacts/records/project__check-run/rec-e7b9cd8c-4103-443e-b186-e300fd9c40d5.md))_

## installer-cli-flags-interactive

### Acceptance
- **installer-cli-flags-interactive**: R12; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k interactive_flag _(id: [rec-dceca8fc-0c62-44cd-bfcb-ba5992c27387](.artifacts/records/project__acceptance/rec-dceca8fc-0c62-44cd-bfcb-ba5992c27387.md))_

### Check
- **installer-cli-flags-interactive**: rec-dceca8fc-0c62-44cd-bfcb-ba5992c27387; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-20b03ef1-0070-4235-bd2e-506f36a3d6f1](.artifacts/records/project__check-run/rec-20b03ef1-0070-4235-bd2e-506f36a3d6f1.md))_

## installer-cli-flags-list

### Acceptance
- **installer-cli-flags-list**: R10; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k list_prints_matrix _(id: [rec-f201f103-557d-4837-8790-f1fd097db867](.artifacts/records/project__acceptance/rec-f201f103-557d-4837-8790-f1fd097db867.md))_

### Check
- **installer-cli-flags-list**: rec-f201f103-557d-4837-8790-f1fd097db867; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-586da61f-fa0a-4a43-b8b9-2d66a6945c7b](.artifacts/records/project__check-run/rec-586da61f-fa0a-4a43-b8b9-2d66a6945c7b.md))_

## installer-cli-flags-noninteractive

### Acceptance
- **installer-cli-flags-noninteractive**: R13; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k non_interactive _(id: [rec-8c5c3c0c-b20d-4231-a9ea-f04a94d5edf3](.artifacts/records/project__acceptance/rec-8c5c3c0c-b20d-4231-a9ea-f04a94d5edf3.md))_

### Check
- **installer-cli-flags-noninteractive**: rec-8c5c3c0c-b20d-4231-a9ea-f04a94d5edf3; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-dd9ddff3-538b-4a12-9eac-9b259dcc628a](.artifacts/records/project__check-run/rec-dd9ddff3-538b-4a12-9eac-9b259dcc628a.md))_

## installer-cli-flags-plan

### Acceptance
- **installer-cli-flags-plan**: R8; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k plan_confirmation _(id: [rec-2ec8813c-7593-496c-9319-4d2aeebf7291](.artifacts/records/project__acceptance/rec-2ec8813c-7593-496c-9319-4d2aeebf7291.md))_

### Check
- **installer-cli-flags-plan**: rec-2ec8813c-7593-496c-9319-4d2aeebf7291; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-b0f283a0-f2c8-4c4e-900a-746d5cc19b36](.artifacts/records/project__check-run/rec-b0f283a0-f2c8-4c4e-900a-746d5cc19b36.md))_

## installer-cli-flags-scope

### Acceptance
- **installer-cli-flags-scope**: R11; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k scope_flag _(id: [rec-dd3d65ca-7da3-4855-b94c-5702f51657ff](.artifacts/records/project__acceptance/rec-dd3d65ca-7da3-4855-b94c-5702f51657ff.md))_

### Check
- **installer-cli-flags-scope**: rec-dd3d65ca-7da3-4855-b94c-5702f51657ff; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-fcc088aa-34f2-46be-96d6-d8e3b0fa44f7](.artifacts/records/project__check-run/rec-fcc088aa-34f2-46be-96d6-d8e3b0fa44f7.md))_

## installer-cli-flags-uninstall

### Acceptance
- **installer-cli-flags-uninstall**: R17; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k uninstall_never_prompts _(id: [rec-598804ea-e846-4e2f-a1b5-607993d37076](.artifacts/records/project__acceptance/rec-598804ea-e846-4e2f-a1b5-607993d37076.md))_

### Check
- **installer-cli-flags-uninstall**: rec-598804ea-e846-4e2f-a1b5-607993d37076; d03a1f36c904694f8ce2c255ee24cecc8a8cdd67; pass; check _(id: [rec-c60b9dd1-388e-47f5-85a0-85d70d4f6cc6](.artifacts/records/project__check-run/rec-c60b9dd1-388e-47f5-85a0-85d70d4f6cc6.md))_

## installer-core

### Acceptance
- **installer-core**: R8; check; packaging; python3 -m pytest tests/test_installer.py -q -k flags _(id: [rec-2e2dd2e2-697e-4410-b9fc-959725def582](.artifacts/records/project__acceptance/rec-2e2dd2e2-697e-4410-b9fc-959725def582.md))_

### Check
- **installer-core**: rec-2e2dd2e2-697e-4410-b9fc-959725def582; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-9ea4bc14-fe39-4256-a43d-f4ec5059ef8a](.artifacts/records/project__check-run/rec-9ea4bc14-fe39-4256-a43d-f4ec5059ef8a.md))_
- **installer-core**: rec-2e2dd2e2-697e-4410-b9fc-959725def582; 730fa7a169a44a5bc9925078ce10ff6d4244e711; pass; check _(id: [rec-bc79092e-6e07-4f93-b8c1-f63c4d6c8d1d](.artifacts/records/project__check-run/rec-bc79092e-6e07-4f93-b8c1-f63c4d6c8d1d.md))_
- **installer-core**: rec-2e2dd2e2-697e-4410-b9fc-959725def582; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-c8793122-21f7-4417-9ffb-8db0ed7e9b30](.artifacts/records/project__check-run/rec-c8793122-21f7-4417-9ffb-8db0ed7e9b30.md))_

## installer-core-allowlist

### Acceptance
- **installer-core-allowlist**: R14; check; packaging; python3 -m pytest tests/test_installer.py -q -k allowlist _(id: [rec-8a1fddc0-a786-449b-93cc-79f585e6dae6](.artifacts/records/project__acceptance/rec-8a1fddc0-a786-449b-93cc-79f585e6dae6.md))_

### Check
- **installer-core-allowlist**: rec-8a1fddc0-a786-449b-93cc-79f585e6dae6; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-174da331-1cd1-4831-b420-98c24cef43ee](.artifacts/records/project__check-run/rec-174da331-1cd1-4831-b420-98c24cef43ee.md))_
- **installer-core-allowlist**: rec-8a1fddc0-a786-449b-93cc-79f585e6dae6; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-509471de-a34a-4a62-b0cb-5093d75a705f](.artifacts/records/project__check-run/rec-509471de-a34a-4a62-b0cb-5093d75a705f.md))_
- **installer-core-allowlist**: rec-8a1fddc0-a786-449b-93cc-79f585e6dae6; 730fa7a169a44a5bc9925078ce10ff6d4244e711; pass; check _(id: [rec-6c9c728e-6b87-458d-9001-96b3d5a4d70d](.artifacts/records/project__check-run/rec-6c9c728e-6b87-458d-9001-96b3d5a4d70d.md))_

## installer-core-idempotent

### Acceptance
- **installer-core-idempotent**: R9; check; packaging; python3 -m pytest tests/test_installer.py -q -k idempotent _(id: [rec-da67502b-5f52-4d4d-a298-122e688b553e](.artifacts/records/project__acceptance/rec-da67502b-5f52-4d4d-a298-122e688b553e.md))_

### Check
- **installer-core-idempotent**: rec-da67502b-5f52-4d4d-a298-122e688b553e; 730fa7a169a44a5bc9925078ce10ff6d4244e711; pass; check _(id: [rec-58ddd0fd-8119-464a-b7d4-0eed4be65fca](.artifacts/records/project__check-run/rec-58ddd0fd-8119-464a-b7d4-0eed4be65fca.md))_
- **installer-core-idempotent**: rec-da67502b-5f52-4d4d-a298-122e688b553e; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-64da64e5-cc39-42c9-bc4e-a0749207edca](.artifacts/records/project__check-run/rec-64da64e5-cc39-42c9-bc4e-a0749207edca.md))_
- **installer-core-idempotent**: rec-da67502b-5f52-4d4d-a298-122e688b553e; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-7928ffbc-2940-4f29-be83-3217696ba2ea](.artifacts/records/project__check-run/rec-7928ffbc-2940-4f29-be83-3217696ba2ea.md))_

## installer-detect

### Acceptance
- **installer-detect**: R2; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k detect_hosts _(id: [rec-656ef110-33d3-44a4-8ec5-aa66e39b0613](.artifacts/records/project__acceptance/rec-656ef110-33d3-44a4-8ec5-aa66e39b0613.md))_

### Check
- **installer-detect**: rec-656ef110-33d3-44a4-8ec5-aa66e39b0613; 677f1e07ee1975c99611bfcff791f6f37df663a5; pass; check _(id: [rec-5fabfb23-7488-4094-ac9a-c5395c80cc87](.artifacts/records/project__check-run/rec-5fabfb23-7488-4094-ac9a-c5395c80cc87.md))_

## installer-docs

### Acceptance
- **installer-docs**: R18; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q -k "wizard or documented_flags" _(id: [rec-578bd42b-a4b6-4ec3-a758-615a2f3f8655](.artifacts/records/project__acceptance/rec-578bd42b-a4b6-4ec3-a758-615a2f3f8655.md))_

### Check
- **installer-docs**: rec-578bd42b-a4b6-4ec3-a758-615a2f3f8655; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-21edd6e7-0e63-40c7-9699-0f824a19dc9c](.artifacts/records/project__check-run/rec-21edd6e7-0e63-40c7-9699-0f824a19dc9c.md))_

## installer-wizard-primitives

### Acceptance
- **installer-wizard-primitives**: R3; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k parse_host_selection _(id: [rec-6b69d84e-a4e5-441f-b77b-3a5db78dc59b](.artifacts/records/project__acceptance/rec-6b69d84e-a4e5-441f-b77b-3a5db78dc59b.md))_

### Check
- **installer-wizard-primitives**: rec-6b69d84e-a4e5-441f-b77b-3a5db78dc59b; f70d46ffba8b383757dc9c12de6e43c833a7346a; pass; check _(id: [rec-3eb9d194-5d02-489d-b1ae-26bc3b71ab9b](.artifacts/records/project__check-run/rec-3eb9d194-5d02-489d-b1ae-26bc3b71ab9b.md))_
- **installer-wizard-primitives**: rec-6b69d84e-a4e5-441f-b77b-3a5db78dc59b; f70d46ffba8b383757dc9c12de6e43c833a7346a; pass; check _(id: [rec-c1f0e300-364d-4825-8fe5-b9050de61740](.artifacts/records/project__check-run/rec-c1f0e300-364d-4825-8fe5-b9050de61740.md))_

## installer-wizard-primitives-defaults

### Acceptance
- **installer-wizard-primitives-defaults**: R4; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k blank_selection_uses_detected _(id: [rec-0e40afa2-1cd6-4208-a472-faadf203bc2a](.artifacts/records/project__acceptance/rec-0e40afa2-1cd6-4208-a472-faadf203bc2a.md))_

### Check
- **installer-wizard-primitives-defaults**: rec-0e40afa2-1cd6-4208-a472-faadf203bc2a; f70d46ffba8b383757dc9c12de6e43c833a7346a; pass; check _(id: [rec-5818e9a7-6d5f-493b-937f-d849b063d86a](.artifacts/records/project__check-run/rec-5818e9a7-6d5f-493b-937f-d849b063d86a.md))_

## installer-wizard-primitives-empty

### Acceptance
- **installer-wizard-primitives-empty**: R5; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k empty_selection_refuses _(id: [rec-ae8e0d92-8d86-477f-83b7-e83232f646b5](.artifacts/records/project__acceptance/rec-ae8e0d92-8d86-477f-83b7-e83232f646b5.md))_

### Check
- **installer-wizard-primitives-empty**: rec-ae8e0d92-8d86-477f-83b7-e83232f646b5; f70d46ffba8b383757dc9c12de6e43c833a7346a; pass; check _(id: [rec-1f9fbc46-d1e2-49f3-b66c-dd1f035d6b43](.artifacts/records/project__check-run/rec-1f9fbc46-d1e2-49f3-b66c-dd1f035d6b43.md))_

## installer-wizard-primitives-mode

### Acceptance
- **installer-wizard-primitives-mode**: R7; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k prompt_mode _(id: [rec-d0d04499-c3cb-4325-ba4d-ab179cfc9493](.artifacts/records/project__acceptance/rec-d0d04499-c3cb-4325-ba4d-ab179cfc9493.md))_

### Check
- **installer-wizard-primitives-mode**: rec-d0d04499-c3cb-4325-ba4d-ab179cfc9493; f70d46ffba8b383757dc9c12de6e43c833a7346a; pass; check _(id: [rec-2fe66c93-7fb3-4263-a2cc-c66872f4b2b2](.artifacts/records/project__check-run/rec-2fe66c93-7fb3-4263-a2cc-c66872f4b2b2.md))_

## installer-wizard-primitives-scope

### Acceptance
- **installer-wizard-primitives-scope**: R6; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k prompt_scope _(id: [rec-2dd0ae61-9b94-4a7f-b513-b128dcc8a9b3](.artifacts/records/project__acceptance/rec-2dd0ae61-9b94-4a7f-b513-b128dcc8a9b3.md))_

### Check
- **installer-wizard-primitives-scope**: rec-2dd0ae61-9b94-4a7f-b513-b128dcc8a9b3; f70d46ffba8b383757dc9c12de6e43c833a7346a; pass; check _(id: [rec-290c10fe-e013-4f21-b7cf-4043f028f4be](.artifacts/records/project__check-run/rec-290c10fe-e013-4f21-b7cf-4043f028f4be.md))_

## integrate-execute

### Acceptance
- **integrate-execute**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_integrate_rules.py -q _(id: [rec-bea1bd88-8f1c-41ef-8afe-fe7f17154d84](.artifacts/records/project__acceptance/rec-bea1bd88-8f1c-41ef-8afe-fe7f17154d84.md))_

### Check
- **integrate-execute**: rec-bea1bd88-8f1c-41ef-8afe-fe7f17154d84; dirty; pass; check _(id: [rec-681e2bb6-166a-4807-b709-6831affb3963](.artifacts/records/project__check-run/rec-681e2bb6-166a-4807-b709-6831affb3963.md))_

## journal-agent

### Acceptance
- **journal-agent**: R8; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_journal.py tests/test_dashboard_app.py -q -k 'agent or collaps' _(id: [rec-9a1b4afe-d1e3-4cb9-949c-3869f5a0cd76](.artifacts/records/project__acceptance/rec-9a1b4afe-d1e3-4cb9-949c-3869f5a0cd76.md))_

### Check
- **journal-agent**: rec-9a1b4afe-d1e3-4cb9-949c-3869f5a0cd76; 91ae11437c0099f16a861f551d7f5811bc9c2475; pass; tdd _(id: [rec-13fd0aa7-5391-4ad3-9cb5-459f3e69b9e8](.artifacts/records/project__check-run/rec-13fd0aa7-5391-4ad3-9cb5-459f3e69b9e8.md))_

## journal-model

### Acceptance
- **journal-model**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_journal.py -q -k 'journal and (load or order or scope or missing)' _(id: [rec-8c8cd3b5-eac9-461a-b480-58bd3af0f8fe](.artifacts/records/project__acceptance/rec-8c8cd3b5-eac9-461a-b480-58bd3af0f8fe.md))_

### Check
- **journal-model**: rec-8c8cd3b5-eac9-461a-b480-58bd3af0f8fe; 848314d1c97ebebc6edbee947927009b70f81aba; pass; tdd _(id: [rec-672d4d2c-be56-4039-be34-25ccce79ee87](.artifacts/records/project__check-run/rec-672d4d2c-be56-4039-be34-25ccce79ee87.md))_

## journal-model-kind

### Acceptance
- **journal-model-kind**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'journal and kind' _(id: [rec-ff941da0-90f7-4e86-8d29-fd9593cff4c9](.artifacts/records/project__acceptance/rec-ff941da0-90f7-4e86-8d29-fd9593cff4c9.md))_

### Check
- **journal-model-kind**: rec-ff941da0-90f7-4e86-8d29-fd9593cff4c9; 848314d1c97ebebc6edbee947927009b70f81aba; pass; tdd _(id: [rec-dde27824-3216-4173-a3b5-1600b1b62d0e](.artifacts/records/project__check-run/rec-dde27824-3216-4173-a3b5-1600b1b62d0e.md))_

## journal-panel

### Acceptance
- **journal-panel**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_journal.py -q -k "panel or kind" _(id: [rec-772b35fe-ecde-4213-8bc8-f56eb55a3517](.artifacts/records/project__acceptance/rec-772b35fe-ecde-4213-8bc8-f56eb55a3517.md))_

### Check
- **journal-panel**: rec-772b35fe-ecde-4213-8bc8-f56eb55a3517; 1eb4f7a6723b779267bc14d030951640dff5c6a3; pass; tdd _(id: [rec-1dedf93f-bdc1-42af-8c2b-4456392d1757](.artifacts/records/project__check-run/rec-1dedf93f-bdc1-42af-8c2b-4456392d1757.md))_

## journal-screen

### Acceptance
- **journal-screen**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_journal.py -q -k "screen or filter or detail or pager" _(id: [rec-5ac93260-7e5b-4f29-8ea4-54b09833796f](.artifacts/records/project__acceptance/rec-5ac93260-7e5b-4f29-8ea4-54b09833796f.md))_

### Check
- **journal-screen**: rec-5ac93260-7e5b-4f29-8ea4-54b09833796f; 1eb4f7a6723b779267bc14d030951640dff5c6a3; pass; tdd _(id: [rec-7dccd89d-a08b-4e67-a264-efc93e0bc27c](.artifacts/records/project__check-run/rec-7dccd89d-a08b-4e67-a264-efc93e0bc27c.md))_

## keyboard-focus

### Acceptance
- **keyboard-focus**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-97f2e49d-f874-4969-929c-d6c37a1ec61b](.artifacts/records/project__acceptance/rec-97f2e49d-f874-4969-929c-d6c37a1ec61b.md))_

### Check
- **keyboard-focus**: rec-97f2e49d-f874-4969-929c-d6c37a1ec61b; 2d1a3be; pass; tdd _(id: [rec-45530a2e-0c6f-4115-ad97-6032f7040919](.artifacts/records/project__check-run/rec-45530a2e-0c6f-4115-ad97-6032f7040919.md))_

### Finding
- **keyboard-focus**: Nothing focused the task table; the effort tab strip kept focus, so arrows never moved the cursor and enter always opened row 0; Real-store probe and 7 red keys-only tests before 2d1a3be; all pass after; A keys-only test fails to move or open a task after 2d1a3be; none _(id: [rec-60d1962e-aeb0-4972-8002-f424c61f615a](.artifacts/records/project__finding/rec-60d1962e-aeb0-4972-8002-f424c61f615a.md))_

## label-view-fields

### Acceptance
- **label-view-fields**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q _(id: [rec-0a970468-5d80-49a0-bf80-d5481a65814b](.artifacts/records/project__acceptance/rec-0a970468-5d80-49a0-bf80-d5481a65814b.md))_

### Check
- **label-view-fields**: rec-0a970468-5d80-49a0-bf80-d5481a65814b; 3ecceba31d1cb6a750fd59320ccc43bee095a686; pass; tdd _(id: [rec-8a416f43-46fb-47fc-aeb5-7d656b99024c](.artifacts/records/project__check-run/rec-8a416f43-46fb-47fc-aeb5-7d656b99024c.md))_

## library-e2e-review

### Check
- **library-e2e-review**: library-e2e-review; b624a3dcb27c119bdc37b928025d33959e9da77d; fail; review _(id: [rec-a3bd1bd5-2794-42a9-bd99-5bcb33e06992](.artifacts/records/project__check-run/rec-a3bd1bd5-2794-42a9-bd99-5bcb33e06992.md))_
- **library-e2e-review**: library-e2e-review; de86e0df31c753d04064576cf7725c5bc3e34880; pass; review _(id: [rec-b2a9e286-6eb2-4c71-bc8f-c85d60b6d7fb](.artifacts/records/project__check-run/rec-b2a9e286-6eb2-4c71-bc8f-c85d60b6d7fb.md))_

## library-fixture

### Acceptance
- **library-fixture**: R1; check; library-boundary; python3 -c 'import importlib.util,tempfile; from pathlib import Path; s=importlib.util.spec_from_file_location("e2e","tests/test_library_e2e.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); repo,_=m._repository(Path(tempfile.mkdtemp())); assert (repo/".git").is_dir()' _(id: [rec-ff6595e5-3e4e-4dcd-80ac-9efcba034eb0](.artifacts/records/project__acceptance/rec-ff6595e5-3e4e-4dcd-80ac-9efcba034eb0.md))_

### Check
- **library-fixture**: rec-ff6595e5-3e4e-4dcd-80ac-9efcba034eb0; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-2d2cd373-9038-4401-b104-4d0b92a0bd9e](.artifacts/records/project__check-run/rec-2d2cd373-9038-4401-b104-4d0b92a0bd9e.md))_
- **library-fixture**: rec-ff6595e5-3e4e-4dcd-80ac-9efcba034eb0; b624a3dcb27c119bdc37b928025d33959e9da77d; pass; check _(id: [rec-4d877358-4222-4502-834b-5ad3a76b74af](.artifacts/records/project__check-run/rec-4d877358-4222-4502-834b-5ad3a76b74af.md))_
- **library-fixture**: rec-ff6595e5-3e4e-4dcd-80ac-9efcba034eb0; cd3750829722c495d77ca2617183afc5d66fa14d; pass; check _(id: [rec-f6f0469f-81c5-41d2-b7b2-4cc76e921c16](.artifacts/records/project__check-run/rec-f6f0469f-81c5-41d2-b7b2-4cc76e921c16.md))_

## library-fixture-claim

### Acceptance
- **library-fixture-claim**: R3; check; library-boundary; python3 -c 'import importlib.util,json,tempfile; from pathlib import Path; s=importlib.util.spec_from_file_location("e2e","tests/test_library_e2e.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); repo,_=m._repository(Path(tempfile.mkdtemp())); manifest=json.loads((repo/".affidavit"/"manifest.json").read_text()); assert any(c.get("id")=="claim-widget" for c in manifest.get("claims",[]))' _(id: [rec-fc6f9ba3-255f-4c84-b1ce-8d3069f6ce67](.artifacts/records/project__acceptance/rec-fc6f9ba3-255f-4c84-b1ce-8d3069f6ce67.md))_

### Check
- **library-fixture-claim**: rec-fc6f9ba3-255f-4c84-b1ce-8d3069f6ce67; cd3750829722c495d77ca2617183afc5d66fa14d; pass; check _(id: [rec-0805d1a5-eced-41d4-be07-1f67c6af9a65](.artifacts/records/project__check-run/rec-0805d1a5-eced-41d4-be07-1f67c6af9a65.md))_
- **library-fixture-claim**: rec-fc6f9ba3-255f-4c84-b1ce-8d3069f6ce67; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-880ffeec-2f56-49c0-9f97-54bb29ece1ed](.artifacts/records/project__check-run/rec-880ffeec-2f56-49c0-9f97-54bb29ece1ed.md))_
- **library-fixture-claim**: rec-fc6f9ba3-255f-4c84-b1ce-8d3069f6ce67; b624a3dcb27c119bdc37b928025d33959e9da77d; pass; check _(id: [rec-941d3c76-95bd-4444-93aa-2486e05837fa](.artifacts/records/project__check-run/rec-941d3c76-95bd-4444-93aa-2486e05837fa.md))_

## library-fixture-close

### Acceptance
- **library-fixture-close**: R5; tdd; library-boundary; PATH="$(pwd)/bin:$PATH" python3 -m pytest tests/test_library_e2e.py::test_library_fixture_close -q _(id: [rec-cc3b93f7-9602-4827-83e3-15c0c50b15b4](.artifacts/records/project__acceptance/rec-cc3b93f7-9602-4827-83e3-15c0c50b15b4.md))_

### Check
- **library-fixture-close**: rec-cc3b93f7-9602-4827-83e3-15c0c50b15b4; b624a3dcb27c119bdc37b928025d33959e9da77d; pass; tdd _(id: [rec-228b960c-b51e-46e0-bcdf-1b481381309f](.artifacts/records/project__check-run/rec-228b960c-b51e-46e0-bcdf-1b481381309f.md))_
- **library-fixture-close**: rec-cc3b93f7-9602-4827-83e3-15c0c50b15b4; de86e0df31c753d04064576cf7725c5bc3e34880; pass; tdd _(id: [rec-37fa8278-7239-4aaa-a9c8-fec21b287d48](.artifacts/records/project__check-run/rec-37fa8278-7239-4aaa-a9c8-fec21b287d48.md))_
- **library-fixture-close**: rec-cc3b93f7-9602-4827-83e3-15c0c50b15b4; cd3750829722c495d77ca2617183afc5d66fa14d; fail; tdd _(id: [rec-3b047cd0-cbd5-4669-a417-7ede8d9ae108](.artifacts/records/project__check-run/rec-3b047cd0-cbd5-4669-a417-7ede8d9ae108.md))_
- **library-fixture-close**: rec-cc3b93f7-9602-4827-83e3-15c0c50b15b4; cd3750829722c495d77ca2617183afc5d66fa14d; fail; tdd _(id: [rec-af60ee04-c97b-463d-b330-4337b8ec0bca](.artifacts/records/project__check-run/rec-af60ee04-c97b-463d-b330-4337b8ec0bca.md))_

## library-fixture-create

### Acceptance
- **library-fixture-create**: R4; check; library-boundary; python3 -c 'import importlib.util,tempfile; from pathlib import Path; from adaptive_artifacts.project import open_store; s=importlib.util.spec_from_file_location("e2e","tests/test_library_e2e.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); repo,_=m._repository(Path(tempfile.mkdtemp())); assert any(r.get("subject")=="claim-widget" for r in open_store(repo).list("project:acceptance"))' _(id: [rec-5228e488-5a1f-43bc-8ca4-99c484556bea](.artifacts/records/project__acceptance/rec-5228e488-5a1f-43bc-8ca4-99c484556bea.md))_

### Check
- **library-fixture-create**: rec-5228e488-5a1f-43bc-8ca4-99c484556bea; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-030761ec-f4c5-4f8e-81b3-7827ec708ee6](.artifacts/records/project__check-run/rec-030761ec-f4c5-4f8e-81b3-7827ec708ee6.md))_
- **library-fixture-create**: rec-5228e488-5a1f-43bc-8ca4-99c484556bea; b624a3dcb27c119bdc37b928025d33959e9da77d; pass; check _(id: [rec-59958131-ccef-4567-9e33-e3530cd8ff2e](.artifacts/records/project__check-run/rec-59958131-ccef-4567-9e33-e3530cd8ff2e.md))_
- **library-fixture-create**: rec-5228e488-5a1f-43bc-8ca4-99c484556bea; cd3750829722c495d77ca2617183afc5d66fa14d; pass; check _(id: [rec-b19af625-bd0e-407f-96a3-e0f470b65139](.artifacts/records/project__check-run/rec-b19af625-bd0e-407f-96a3-e0f470b65139.md))_

## library-fixture-quiet

### Acceptance
- **library-fixture-quiet**: R6; check; library-boundary; PATH="$(pwd)/bin:$PATH" PYTHONPATH="$(pwd):$HOME/affidavit${PYTHONPATH:+:$PYTHONPATH}" python3 -c 'import importlib.util,json,os,subprocess,tempfile; from pathlib import Path; s=importlib.util.spec_from_file_location("e2e","tests/test_library_e2e.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); repo,request=m._repository(Path(tempfile.mkdtemp())); seen=[]; real=subprocess.run
class P(subprocess.Popen):
 def __init__(self, cmd, *a, **k):
  seen.append(cmd); super().__init__(cmd, *a, **k)
def spy(cmd, *a, **k):
 seen.append(cmd); return real(cmd, *a, **k)
subprocess.run=spy; subprocess.Popen=P
import orchestra.close_batch as cb
cb.subprocess.run=spy; cb.subprocess.Popen=P
path=repo/"close-request.json"; path.write_text(json.dumps(request)); os.chdir(repo); cb.main(["--input",str(path),"--out",str(repo/"out.ndjson"),"--cwd",str(repo)])
def bad(cmd):
 parts=cmd if isinstance(cmd,(list,tuple)) else [cmd]
 return any(Path(str(p)).name in {"aff","adaptive-artifacts"} for p in parts)
assert not any(bad(c) for c in seen)'  _(id: [rec-4f29f448-e9fd-417d-a1de-19ad50630264](.artifacts/records/project__acceptance/rec-4f29f448-e9fd-417d-a1de-19ad50630264.md))_

### Check
- **library-fixture-quiet**: rec-4f29f448-e9fd-417d-a1de-19ad50630264; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-030b1aca-f195-41a3-875a-d087a1540fcd](.artifacts/records/project__check-run/rec-030b1aca-f195-41a3-875a-d087a1540fcd.md))_
- **library-fixture-quiet**: rec-4f29f448-e9fd-417d-a1de-19ad50630264; b624a3dcb27c119bdc37b928025d33959e9da77d; pass; check _(id: [rec-500ca0f2-804e-438f-9711-810f240635fe](.artifacts/records/project__check-run/rec-500ca0f2-804e-438f-9711-810f240635fe.md))_
- **library-fixture-quiet**: rec-4f29f448-e9fd-417d-a1de-19ad50630264; cd3750829722c495d77ca2617183afc5d66fa14d; pass; check _(id: [rec-93fbdd47-e581-4e14-bc8f-f7f84168c6e7](.artifacts/records/project__check-run/rec-93fbdd47-e581-4e14-bc8f-f7f84168c6e7.md))_

## library-fixture-store

### Acceptance
- **library-fixture-store**: R2; check; library-boundary; python3 -c 'import importlib.util,tempfile; from pathlib import Path; s=importlib.util.spec_from_file_location("e2e","tests/test_library_e2e.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); repo,_=m._repository(Path(tempfile.mkdtemp())); assert any(p.name=="meta.json" for p in repo.rglob("meta.json"))' _(id: [rec-328bc0e2-5aa4-4c22-9d76-f2387e4a5e13](.artifacts/records/project__acceptance/rec-328bc0e2-5aa4-4c22-9d76-f2387e4a5e13.md))_

### Check
- **library-fixture-store**: rec-328bc0e2-5aa4-4c22-9d76-f2387e4a5e13; b624a3dcb27c119bdc37b928025d33959e9da77d; pass; check _(id: [rec-682183a2-d304-41ee-a247-d13f97b1130e](.artifacts/records/project__check-run/rec-682183a2-d304-41ee-a247-d13f97b1130e.md))_
- **library-fixture-store**: rec-328bc0e2-5aa4-4c22-9d76-f2387e4a5e13; cd3750829722c495d77ca2617183afc5d66fa14d; pass; check _(id: [rec-be277726-eaad-4de2-be47-05850d73bd93](.artifacts/records/project__check-run/rec-be277726-eaad-4de2-be47-05850d73bd93.md))_
- **library-fixture-store**: rec-328bc0e2-5aa4-4c22-9d76-f2387e4a5e13; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-e45cd95f-8d45-4f74-8319-00f9e986f3a6](.artifacts/records/project__check-run/rec-e45cd95f-8d45-4f74-8319-00f9e986f3a6.md))_

## loop-scenarios

### Acceptance
- **loop-scenarios**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_evidence_loop.py -q _(id: [rec-17e1c5a7-2e32-40d4-9df1-6d7d4f8bb488](.artifacts/records/project__acceptance/rec-17e1c5a7-2e32-40d4-9df1-6d7d4f8bb488.md))_

### Check
- **loop-scenarios**: rec-17e1c5a7-2e32-40d4-9df1-6d7d4f8bb488; dirty; pass; check _(id: [rec-2d41627d-8465-47a4-8299-fcff74f9f375](.artifacts/records/project__check-run/rec-2d41627d-8465-47a4-8299-fcff74f9f375.md))_

## matrix-model

### Acceptance
- **matrix-model**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_requirement.py -q -k matrix _(id: [rec-65e37e8b-25f6-4953-a8b2-9a0c0fddb74d](.artifacts/records/project__acceptance/rec-65e37e8b-25f6-4953-a8b2-9a0c0fddb74d.md))_

### Check
- **matrix-model**: rec-65e37e8b-25f6-4953-a8b2-9a0c0fddb74d; dirty; pass; tdd _(id: [rec-266fb4cc-1eed-4022-846a-12125240bfc0](.artifacts/records/project__check-run/rec-266fb4cc-1eed-4022-846a-12125240bfc0.md))_
- **matrix-model**: rec-65e37e8b-25f6-4953-a8b2-9a0c0fddb74d; dirty; pass; tdd _(id: [rec-46b9f311-d4f1-4e06-b938-eadf309eb074](.artifacts/records/project__check-run/rec-46b9f311-d4f1-4e06-b938-eadf309eb074.md))_
- **matrix-model**: rec-65e37e8b-25f6-4953-a8b2-9a0c0fddb74d; dirty; pass; tdd _(id: [rec-66ff9889-48bf-409a-a98c-f306a87278e4](.artifacts/records/project__check-run/rec-66ff9889-48bf-409a-a98c-f306a87278e4.md))_
- **matrix-model**: rec-65e37e8b-25f6-4953-a8b2-9a0c0fddb74d; dirty; pass; tdd _(id: [rec-8ab560a6-a96a-46de-b5c1-a990aaa2c1ad](.artifacts/records/project__check-run/rec-8ab560a6-a96a-46de-b5c1-a990aaa2c1ad.md))_
- **matrix-model**: rec-65e37e8b-25f6-4953-a8b2-9a0c0fddb74d; dirty; pass; tdd _(id: [rec-e4647efd-5712-41c4-9d54-cdc51014a6de](.artifacts/records/project__check-run/rec-e4647efd-5712-41c4-9d54-cdc51014a6de.md))_

## matrix-ui

### Acceptance
- **matrix-ui**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py -q -k matrix _(id: [rec-e60394f4-9d3c-494c-9b2c-e69db0de52ee](.artifacts/records/project__acceptance/rec-e60394f4-9d3c-494c-9b2c-e69db0de52ee.md))_

### Check
- **matrix-ui**: rec-e60394f4-9d3c-494c-9b2c-e69db0de52ee; dirty; pass; tdd _(id: [rec-3e25e616-2a2d-4fbc-9340-b95aaa00d53a](.artifacts/records/project__check-run/rec-3e25e616-2a2d-4fbc-9340-b95aaa00d53a.md))_
- **matrix-ui**: rec-e60394f4-9d3c-494c-9b2c-e69db0de52ee; dirty; pass; tdd _(id: [rec-a4e5ad10-f2fd-4494-b365-3e042c8f98e1](.artifacts/records/project__check-run/rec-a4e5ad10-f2fd-4494-b365-3e042c8f98e1.md))_
- **matrix-ui**: rec-e60394f4-9d3c-494c-9b2c-e69db0de52ee; dirty; pass; tdd _(id: [rec-cad7ff06-72a0-4efa-9208-969a2de691f9](.artifacts/records/project__check-run/rec-cad7ff06-72a0-4efa-9208-969a2de691f9.md))_

## matrix-ui-strip

### Acceptance
- **matrix-ui-strip**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py tests/test_dashboard_app.py -q -k "strip or glyph" _(id: [rec-2803f0e2-8159-46ac-90b0-d9cec7762a4a](.artifacts/records/project__acceptance/rec-2803f0e2-8159-46ac-90b0-d9cec7762a4a.md))_

### Check
- **matrix-ui-strip**: rec-2803f0e2-8159-46ac-90b0-d9cec7762a4a; dirty; pass; tdd _(id: [rec-967f4dc8-c14d-4f0f-b094-fdd4e4ed50d4](.artifacts/records/project__check-run/rec-967f4dc8-c14d-4f0f-b094-fdd4e4ed50d4.md))_

## milestone-nav-helpers

### Acceptance
- **milestone-nav-helpers**: R3; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestones.test.ts -t R3 _(id: [rec-2e55a392-c6be-4932-bd50-fb2d23b83fbc](.artifacts/records/project__acceptance/rec-2e55a392-c6be-4932-bd50-fb2d23b83fbc.md))_

### Check
- **milestone-nav-helpers**: rec-2e55a392-c6be-4932-bd50-fb2d23b83fbc; 0f572addc9d3ee72a6de5c2f6c9b2007a30a71de; pass; check _(id: [rec-0606ffaf-0eb3-484c-be68-49d062e988e0](.artifacts/records/project__check-run/rec-0606ffaf-0eb3-484c-be68-49d062e988e0.md))_

## milestone-nav-helpers-r7

### Acceptance
- **milestone-nav-helpers-r7**: R7; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestones.test.ts -t R7 _(id: [rec-cec6c732-e285-4853-a8e7-01f94ee49425](.artifacts/records/project__acceptance/rec-cec6c732-e285-4853-a8e7-01f94ee49425.md))_

### Check
- **milestone-nav-helpers-r7**: rec-cec6c732-e285-4853-a8e7-01f94ee49425; 0f572addc9d3ee72a6de5c2f6c9b2007a30a71de; pass; check _(id: [rec-271ce170-b86a-4c6d-9a66-cc7466bc7703](.artifacts/records/project__check-run/rec-271ce170-b86a-4c6d-9a66-cc7466bc7703.md))_

## milestone-nav-helpers-r8

### Acceptance
- **milestone-nav-helpers-r8**: R8; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestones.test.ts -t R8 _(id: [rec-b2803a64-6aa8-4749-b1ef-44d099372bb4](.artifacts/records/project__acceptance/rec-b2803a64-6aa8-4749-b1ef-44d099372bb4.md))_

### Check
- **milestone-nav-helpers-r8**: rec-b2803a64-6aa8-4749-b1ef-44d099372bb4; 0f572addc9d3ee72a6de5c2f6c9b2007a30a71de; pass; check _(id: [rec-6658f87d-6125-4b29-ac52-c3fb7951f599](.artifacts/records/project__check-run/rec-6658f87d-6125-4b29-ac52-c3fb7951f599.md))_

## milestone-nav-review

### Check
- **milestone-nav-review**: milestone-nav-review; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; review _(id: [rec-7cfcbe31-b806-4727-a8d1-b59ec7d3a74e](.artifacts/records/project__check-run/rec-7cfcbe31-b806-4727-a8d1-b59ec7d3a74e.md))_

## milestone-nav-ui

### Acceptance
- **milestone-nav-ui**: R1; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestoneNav.test.ts -t R1 _(id: [rec-0ba73bbb-99ad-44ef-8696-3cad46aa6fab](.artifacts/records/project__acceptance/rec-0ba73bbb-99ad-44ef-8696-3cad46aa6fab.md))_

### Check
- **milestone-nav-ui**: rec-0ba73bbb-99ad-44ef-8696-3cad46aa6fab; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-e4ac4288-45e8-4fdc-8a30-bd542932cb3e](.artifacts/records/project__check-run/rec-e4ac4288-45e8-4fdc-8a30-bd542932cb3e.md))_

## milestone-nav-ui-r10

### Acceptance
- **milestone-nav-ui-r10**: R10; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestoneNav.test.ts -t R10 _(id: [rec-863722d6-7ee4-430b-93a9-32919d31fcdc](.artifacts/records/project__acceptance/rec-863722d6-7ee4-430b-93a9-32919d31fcdc.md))_

### Check
- **milestone-nav-ui-r10**: rec-863722d6-7ee4-430b-93a9-32919d31fcdc; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-40452a65-b742-4637-a0d0-03e64d3775cd](.artifacts/records/project__check-run/rec-40452a65-b742-4637-a0d0-03e64d3775cd.md))_

## milestone-nav-ui-r2

### Acceptance
- **milestone-nav-ui-r2**: R2; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestoneNav.test.ts -t R2 _(id: [rec-85702607-79f3-4c96-b65d-ce0c8c20f1e1](.artifacts/records/project__acceptance/rec-85702607-79f3-4c96-b65d-ce0c8c20f1e1.md))_

### Check
- **milestone-nav-ui-r2**: rec-85702607-79f3-4c96-b65d-ce0c8c20f1e1; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-df1de636-2e38-418e-ab4e-f8f20de0d9a8](.artifacts/records/project__check-run/rec-df1de636-2e38-418e-ab4e-f8f20de0d9a8.md))_

## milestone-nav-ui-r4

### Acceptance
- **milestone-nav-ui-r4**: R4; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestoneNav.test.ts -t R4 _(id: [rec-ce00f555-db82-4549-a6c8-4598b2274f57](.artifacts/records/project__acceptance/rec-ce00f555-db82-4549-a6c8-4598b2274f57.md))_

### Check
- **milestone-nav-ui-r4**: rec-ce00f555-db82-4549-a6c8-4598b2274f57; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-5e3be4db-8e60-4378-a17e-14d7768d9a11](.artifacts/records/project__check-run/rec-5e3be4db-8e60-4378-a17e-14d7768d9a11.md))_

## milestone-nav-ui-r5

### Acceptance
- **milestone-nav-ui-r5**: R5; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestoneNav.test.ts -t R5 _(id: [rec-cbca727e-806c-4ace-b5f0-19afd144744d](.artifacts/records/project__acceptance/rec-cbca727e-806c-4ace-b5f0-19afd144744d.md))_

### Check
- **milestone-nav-ui-r5**: rec-cbca727e-806c-4ace-b5f0-19afd144744d; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-ac157edf-5a0a-46a4-a333-7827b4efdfc8](.artifacts/records/project__check-run/rec-ac157edf-5a0a-46a4-a333-7827b4efdfc8.md))_

## milestone-nav-ui-r6

### Acceptance
- **milestone-nav-ui-r6**: R6; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestoneNav.test.ts -t R6 _(id: [rec-a9f06f0b-ba41-4c2a-88c0-93d96ded3341](.artifacts/records/project__acceptance/rec-a9f06f0b-ba41-4c2a-88c0-93d96ded3341.md))_

### Check
- **milestone-nav-ui-r6**: rec-a9f06f0b-ba41-4c2a-88c0-93d96ded3341; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-9e586465-e2cf-4833-a41a-59ee02eaeb63](.artifacts/records/project__check-run/rec-9e586465-e2cf-4833-a41a-59ee02eaeb63.md))_

## milestone-nav-ui-r9

### Acceptance
- **milestone-nav-ui-r9**: R9; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestoneNav.test.ts -t R9 _(id: [rec-5f055263-a2ec-4551-9943-004890bb130e](.artifacts/records/project__acceptance/rec-5f055263-a2ec-4551-9943-004890bb130e.md))_

### Check
- **milestone-nav-ui-r9**: rec-5f055263-a2ec-4551-9943-004890bb130e; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-33df45a9-a62c-4e1b-9ed1-8be812c80f13](.artifacts/records/project__check-run/rec-33df45a9-a62c-4e1b-9ed1-8be812c80f13.md))_

## model-fixture-reuse

### Acceptance
- **model-fixture-reuse**: check; test-suite-speed; python3 -m pytest tests/test_dashboard_model.py -q --durations=5 _(id: [rec-660d84e9-e3f2-421c-8094-db9c8427c8da](.artifacts/records/project__acceptance/rec-660d84e9-e3f2-421c-8094-db9c8427c8da.md))_

## model-fixture-reuse-total

### Acceptance
- **model-fixture-reuse-total**: check; test-suite-speed; time python3 -m pytest -q _(id: [rec-db700c2c-4b03-4fb5-9aec-9517316abf2b](.artifacts/records/project__acceptance/rec-db700c2c-4b03-4fb5-9aec-9517316abf2b.md))_

## narrow-planned

### Acceptance
- **narrow-planned**: R5; check; workflow-loop; python3 -c 'import json, subprocess, sys
aa = ["python3", "/home/andrewyin/adaptive-artifacts/tools/artifacts.py", "--root", "/home/andrewyin/se-workflow"]
bad = "pytest tests -q -n 4"
subjects = ("verify-spec-view-suite", "verify-evidence-matrix-suite", "verify-journal-view-suite")
for s in subjects:
    result = subprocess.run([*aa, "list", "--type", "project:acceptance", "--subject", s, "--state", "active", "--full"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
    recs = json.loads(result.stdout)["records"]
    assert len(recs) == 1, s
    cmd = recs[0]["payload"]["verify_command"]
    assert bad not in cmd, cmd
    assert " -k " in cmd, cmd
ids = ("rec-79a4e4c1-cfcb-421b-a023-64563ff645f3", "rec-8432d854-983c-4de9-bb0f-f99b94ecae9a", "rec-f04fa83f-a51f-4800-b3be-9b658df17590")
for i in ids:
    result = subprocess.run([*aa, "get", "--type", "project:work-item", "--id", i], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
    body = json.loads(result.stdout)["body"].lower()
    assert "full suite" not in body, i
print("phase checks only")
' _(id: [rec-6d54e8ac-3496-44e6-beff-60a45f056733](.artifacts/records/project__acceptance/rec-6d54e8ac-3496-44e6-beff-60a45f056733.md))_

### Check
- **narrow-planned**: rec-6d54e8ac-3496-44e6-beff-60a45f056733; dirty; pass; check _(id: [rec-43c12516-0641-4a9c-940e-67524f75cb23](.artifacts/records/project__check-run/rec-43c12516-0641-4a9c-940e-67524f75cb23.md))_

## native-adapters

### Acceptance
- **native-adapters**: R10; check; packaging; python3 -m pytest tests/test_installer.py -q -k native _(id: [rec-9fab2257-d40f-49c2-88ac-c560a964d280](.artifacts/records/project__acceptance/rec-9fab2257-d40f-49c2-88ac-c560a964d280.md))_

### Check
- **native-adapters**: rec-9fab2257-d40f-49c2-88ac-c560a964d280; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-8d186316-2566-40be-a0a9-0609e48a820b](.artifacts/records/project__check-run/rec-8d186316-2566-40be-a0a9-0609e48a820b.md))_
- **native-adapters**: rec-9fab2257-d40f-49c2-88ac-c560a964d280; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-a0580b8f-9da5-4854-9527-f7f703a97486](.artifacts/records/project__check-run/rec-a0580b8f-9da5-4854-9527-f7f703a97486.md))_
- **native-adapters**: rec-9fab2257-d40f-49c2-88ac-c560a964d280; ddcf7222d66e76a0a258f476c1eab8da608b81d6; pass; check _(id: [rec-adcd2c4a-b37f-43dd-9060-3d18c011ff29](.artifacts/records/project__check-run/rec-adcd2c4a-b37f-43dd-9060-3d18c011ff29.md))_

## native-adapters-agent

### Acceptance
- **native-adapters-agent**: R13; check; packaging; python3 -m pytest tests/test_agent_generation.py -q _(id: [rec-81b797c0-4d67-4287-987f-a70f6d6d7b4a](.artifacts/records/project__acceptance/rec-81b797c0-4d67-4287-987f-a70f6d6d7b4a.md))_

### Check
- **native-adapters-agent**: rec-81b797c0-4d67-4287-987f-a70f6d6d7b4a; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-a0e11a85-9c80-4fdc-8768-086e5dc923d3](.artifacts/records/project__check-run/rec-a0e11a85-9c80-4fdc-8768-086e5dc923d3.md))_
- **native-adapters-agent**: rec-81b797c0-4d67-4287-987f-a70f6d6d7b4a; ddcf7222d66e76a0a258f476c1eab8da608b81d6; pass; check _(id: [rec-ad215422-61e7-4bdc-8601-b71c6f1f402f](.artifacts/records/project__check-run/rec-ad215422-61e7-4bdc-8601-b71c6f1f402f.md))_
- **native-adapters-agent**: rec-81b797c0-4d67-4287-987f-a70f6d6d7b4a; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-c043673d-20dc-4326-9598-d61583e1a3b5](.artifacts/records/project__check-run/rec-c043673d-20dc-4326-9598-d61583e1a3b5.md))_

## native-adapters-hooks

### Acceptance
- **native-adapters-hooks**: R12; check; packaging; python3 -m pytest tests/test_installer.py -q -k hooks _(id: [rec-1239637e-5651-4066-bcbb-f6078a6deb41](.artifacts/records/project__acceptance/rec-1239637e-5651-4066-bcbb-f6078a6deb41.md))_

### Check
- **native-adapters-hooks**: rec-1239637e-5651-4066-bcbb-f6078a6deb41; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-2cc9e530-74cb-42cf-90ba-d85a0d482558](.artifacts/records/project__check-run/rec-2cc9e530-74cb-42cf-90ba-d85a0d482558.md))_
- **native-adapters-hooks**: rec-1239637e-5651-4066-bcbb-f6078a6deb41; ddcf7222d66e76a0a258f476c1eab8da608b81d6; pass; check _(id: [rec-3f58c336-ac51-43d8-ad85-b2c24f7becf6](.artifacts/records/project__check-run/rec-3f58c336-ac51-43d8-ad85-b2c24f7becf6.md))_
- **native-adapters-hooks**: rec-1239637e-5651-4066-bcbb-f6078a6deb41; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-cb322a81-d8ee-424d-808b-a3923aac473c](.artifacts/records/project__check-run/rec-cb322a81-d8ee-424d-808b-a3923aac473c.md))_

## native-adapters-tail

### Acceptance
- **native-adapters-tail**: R11; check; packaging; python3 -m pytest tests/test_installer.py -q -k tail _(id: [rec-ec5854f8-474a-4aee-b6a1-5033611e7cde](.artifacts/records/project__acceptance/rec-ec5854f8-474a-4aee-b6a1-5033611e7cde.md))_

### Check
- **native-adapters-tail**: rec-ec5854f8-474a-4aee-b6a1-5033611e7cde; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-29ced538-537b-4c0f-8ef5-d09d1d736163](.artifacts/records/project__check-run/rec-29ced538-537b-4c0f-8ef5-d09d1d736163.md))_
- **native-adapters-tail**: rec-ec5854f8-474a-4aee-b6a1-5033611e7cde; ddcf7222d66e76a0a258f476c1eab8da608b81d6; pass; check _(id: [rec-4c66c559-9fff-49e0-b3bd-763808184938](.artifacts/records/project__check-run/rec-4c66c559-9fff-49e0-b3bd-763808184938.md))_
- **native-adapters-tail**: rec-ec5854f8-474a-4aee-b6a1-5033611e7cde; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-f3d84d62-d844-441a-95cd-976a2328c76b](.artifacts/records/project__check-run/rec-f3d84d62-d844-441a-95cd-976a2328c76b.md))_

## needs-you-list

### Acceptance
- **needs-you-list**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k needs_you _(id: [rec-7c8645dc-e818-4d9d-b2d1-807437c46a90](.artifacts/records/project__acceptance/rec-7c8645dc-e818-4d9d-b2d1-807437c46a90.md))_

### Check
- **needs-you-list**: rec-7c8645dc-e818-4d9d-b2d1-807437c46a90; 206678413361ffed9978beeaac5dbc557fc5d774; pass; tdd _(id: [rec-0c7f3233-7865-46a8-abf9-dd6a6f6a6ced](.artifacts/records/project__check-run/rec-0c7f3233-7865-46a8-abf9-dd6a6f6a6ced.md))_

## needs-you-records

### Acceptance
- **needs-you-records**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k needs _(id: [rec-79256814-feaf-46b4-b5da-3c97ec0838c0](.artifacts/records/project__acceptance/rec-79256814-feaf-46b4-b5da-3c97ec0838c0.md))_

### Check
- **needs-you-records**: rec-79256814-feaf-46b4-b5da-3c97ec0838c0; fa6d87206996583b3d87e54147d655e5bddf32f5; pass; tdd _(id: [rec-a6d17cef-9df4-4b82-b9b7-3379e10d87d0](.artifacts/records/project__check-run/rec-a6d17cef-9df4-4b82-b9b7-3379e10d87d0.md))_

### Observation
- **needs-you-records**: list --full for questions, findings and check-runs keeps dashboard-status at about 0.36 s on the real store with 56 check-runs (parent timing after merge).; dashboard-features _(id: [rec-6a8a8cb5-dd1b-42c3-a8fa-8b3b5baa06f1](.artifacts/records/project__investigation-observation/rec-6a8a8cb5-dd1b-42c3-a8fa-8b3b5baa06f1.md))_

## needs-you-tab-removal

### Acceptance
- **needs-you-tab-removal**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_view.py -q _(id: [rec-e781be72-47b4-4705-8bb4-82f57f1391ef](.artifacts/records/project__acceptance/rec-e781be72-47b4-4705-8bb4-82f57f1391ef.md))_

### Check
- **needs-you-tab-removal**: rec-e781be72-47b4-4705-8bb4-82f57f1391ef; 7fbde9ccd60decd8e171bbdd46d83d598cfd2adf; pass; tdd _(id: [rec-1d2fada7-d72d-4924-97ce-8e7317d3a0fa](.artifacts/records/project__check-run/rec-1d2fada7-d72d-4924-97ce-8e7317d3a0fa.md))_

### Observation
- **needs-you-tab-removal**: The Needs you tab matched needs-you subjects against task slugs, so effort-level questions and non-task subjects never counted and the tab disagreed with the panel.; dashboard-bugfix _(id: [rec-613913b9-0be9-46f8-a9b5-5f59739f368b](.artifacts/records/project__investigation-observation/rec-613913b9-0be9-46f8-a9b5-5f59739f368b.md))_

## open-store

### Acceptance
- **open-store**: R1; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r1_git_toplevel -q _(id: [rec-082c3521-bd06-4066-b644-8e918f6a5f4a](.artifacts/records/project__acceptance/rec-082c3521-bd06-4066-b644-8e918f6a5f4a.md))_

### Check
- **open-store**: rec-082c3521-bd06-4066-b644-8e918f6a5f4a; dirty; fail; tdd _(id: [rec-3ed48525-bdaf-46f9-bb25-a3227f9cbcc8](.artifacts/records/project__check-run/rec-3ed48525-bdaf-46f9-bb25-a3227f9cbcc8.md))_
- **open-store**: rec-082c3521-bd06-4066-b644-8e918f6a5f4a; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-6786bfa6-21e0-48ac-8b76-9171588c54b8](.artifacts/records/project__check-run/rec-6786bfa6-21e0-48ac-8b76-9171588c54b8.md))_
- **open-store**: rec-082c3521-bd06-4066-b644-8e918f6a5f4a; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-77299609-54b5-462c-8e75-ca7293ef3a81](.artifacts/records/project__check-run/rec-77299609-54b5-462c-8e75-ca7293ef3a81.md))_

## open-store-binding-missing

### Acceptance
- **open-store-binding-missing**: R11; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r11_binding_missing_meta -q _(id: [rec-12d189a7-91c8-4d00-b0bc-18b553f1bfc8](.artifacts/records/project__acceptance/rec-12d189a7-91c8-4d00-b0bc-18b553f1bfc8.md))_

### Check
- **open-store-binding-missing**: rec-12d189a7-91c8-4d00-b0bc-18b553f1bfc8; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-2d6ad5c9-5585-49db-992a-69cb83ce4549](.artifacts/records/project__check-run/rec-2d6ad5c9-5585-49db-992a-69cb83ce4549.md))_
- **open-store-binding-missing**: rec-12d189a7-91c8-4d00-b0bc-18b553f1bfc8; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-b0e8f503-a11d-49c2-b33d-3fa22a73d420](.artifacts/records/project__check-run/rec-b0e8f503-a11d-49c2-b33d-3fa22a73d420.md))_
- **open-store-binding-missing**: rec-12d189a7-91c8-4d00-b0bc-18b553f1bfc8; dirty; fail; tdd _(id: [rec-ff31b6e9-fc4b-4906-be06-84739fc4d72f](.artifacts/records/project__check-run/rec-ff31b6e9-fc4b-4906-be06-84739fc4d72f.md))_

## open-store-binding-value

### Acceptance
- **open-store-binding-value**: R12; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r12_binding_value -q _(id: [rec-0f6e3526-38ff-4cfa-a625-a49a1e5685c7](.artifacts/records/project__acceptance/rec-0f6e3526-38ff-4cfa-a625-a49a1e5685c7.md))_

### Check
- **open-store-binding-value**: rec-0f6e3526-38ff-4cfa-a625-a49a1e5685c7; dirty; fail; tdd _(id: [rec-23ecc762-4078-4996-a4ef-60cc43e2b7c9](.artifacts/records/project__check-run/rec-23ecc762-4078-4996-a4ef-60cc43e2b7c9.md))_
- **open-store-binding-value**: rec-0f6e3526-38ff-4cfa-a625-a49a1e5685c7; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-927561b0-32aa-49de-a6ea-f2ae67ca5ec7](.artifacts/records/project__check-run/rec-927561b0-32aa-49de-a6ea-f2ae67ca5ec7.md))_
- **open-store-binding-value**: rec-0f6e3526-38ff-4cfa-a625-a49a1e5685c7; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-b40c006d-cf35-43d3-8f12-e22f463d9acb](.artifacts/records/project__check-run/rec-b40c006d-cf35-43d3-8f12-e22f463d9acb.md))_

## open-store-committed-binding

### Acceptance
- **open-store-committed-binding**: R6; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r6_committed_binding_file -q _(id: [rec-dbece29d-2cc1-4ae8-99dc-300a3b7c8e3a](.artifacts/records/project__acceptance/rec-dbece29d-2cc1-4ae8-99dc-300a3b7c8e3a.md))_

### Check
- **open-store-committed-binding**: rec-dbece29d-2cc1-4ae8-99dc-300a3b7c8e3a; dirty; fail; tdd _(id: [rec-55f63a3f-e5a0-4912-b9b0-1857b9b18993](.artifacts/records/project__check-run/rec-55f63a3f-e5a0-4912-b9b0-1857b9b18993.md))_
- **open-store-committed-binding**: rec-dbece29d-2cc1-4ae8-99dc-300a3b7c8e3a; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-af472225-d7db-49e7-9356-11e515817bb4](.artifacts/records/project__check-run/rec-af472225-d7db-49e7-9356-11e515817bb4.md))_
- **open-store-committed-binding**: rec-dbece29d-2cc1-4ae8-99dc-300a3b7c8e3a; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-f2cf1ea2-d525-4c71-941e-7a06ee8e3f46](.artifacts/records/project__check-run/rec-f2cf1ea2-d525-4c71-941e-7a06ee8e3f46.md))_

## open-store-env

### Acceptance
- **open-store-env**: R4; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r4_artifacts_store_env -q _(id: [rec-c940e1b3-04da-48f6-97b8-8ddfaf906e09](.artifacts/records/project__acceptance/rec-c940e1b3-04da-48f6-97b8-8ddfaf906e09.md))_

### Check
- **open-store-env**: rec-c940e1b3-04da-48f6-97b8-8ddfaf906e09; dirty; fail; tdd _(id: [rec-0794f8f4-bb81-40b0-bc37-47ece6e4e9a8](.artifacts/records/project__check-run/rec-0794f8f4-bb81-40b0-bc37-47ece6e4e9a8.md))_
- **open-store-env**: rec-c940e1b3-04da-48f6-97b8-8ddfaf906e09; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-18721ded-2be3-42fa-86d6-a6de631f56c9](.artifacts/records/project__check-run/rec-18721ded-2be3-42fa-86d6-a6de631f56c9.md))_
- **open-store-env**: rec-c940e1b3-04da-48f6-97b8-8ddfaf906e09; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-ef06e8ab-4dd3-4027-828b-4d2c8485cb51](.artifacts/records/project__check-run/rec-ef06e8ab-4dd3-4027-828b-4d2c8485cb51.md))_

## open-store-env-missing

### Acceptance
- **open-store-env-missing**: R10; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r10_env_missing_meta -q _(id: [rec-5acb4008-cab3-4353-8e95-1d9eec168b36](.artifacts/records/project__acceptance/rec-5acb4008-cab3-4353-8e95-1d9eec168b36.md))_

### Check
- **open-store-env-missing**: rec-5acb4008-cab3-4353-8e95-1d9eec168b36; dirty; fail; tdd _(id: [rec-00a9fe73-6861-423f-9fdf-8ff6472c57be](.artifacts/records/project__check-run/rec-00a9fe73-6861-423f-9fdf-8ff6472c57be.md))_
- **open-store-env-missing**: rec-5acb4008-cab3-4353-8e95-1d9eec168b36; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-941b7bf7-0a61-47ca-b810-1a68919f39b2](.artifacts/records/project__check-run/rec-941b7bf7-0a61-47ca-b810-1a68919f39b2.md))_
- **open-store-env-missing**: rec-5acb4008-cab3-4353-8e95-1d9eec168b36; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-cb34334e-3db4-427d-a2ca-65023e04013e](.artifacts/records/project__check-run/rec-cb34334e-3db4-427d-a2ca-65023e04013e.md))_

## open-store-home-meta

### Acceptance
- **open-store-home-meta**: R8; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r8_home_meta -q _(id: [rec-9e503dfa-da78-44e7-8ad6-547ec487dd18](.artifacts/records/project__acceptance/rec-9e503dfa-da78-44e7-8ad6-547ec487dd18.md))_

### Check
- **open-store-home-meta**: rec-9e503dfa-da78-44e7-8ad6-547ec487dd18; dirty; fail; tdd _(id: [rec-8ffb202b-6819-4131-9ce4-bc7c99b1dac5](.artifacts/records/project__check-run/rec-8ffb202b-6819-4131-9ce4-bc7c99b1dac5.md))_
- **open-store-home-meta**: rec-9e503dfa-da78-44e7-8ad6-547ec487dd18; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-b894c6e6-f90b-4af3-9692-cdf9a42b1a2b](.artifacts/records/project__check-run/rec-b894c6e6-f90b-4af3-9692-cdf9a42b1a2b.md))_
- **open-store-home-meta**: rec-9e503dfa-da78-44e7-8ad6-547ec487dd18; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-cbb0bde6-e565-4117-94b0-809e959f6d1d](.artifacts/records/project__check-run/rec-cbb0bde6-e565-4117-94b0-809e959f6d1d.md))_

## open-store-local-binding

### Acceptance
- **open-store-local-binding**: R5; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r5_local_binding_file -q _(id: [rec-e5d4e992-8ac9-4166-b781-a2c6c8b8c552](.artifacts/records/project__acceptance/rec-e5d4e992-8ac9-4166-b781-a2c6c8b8c552.md))_

### Check
- **open-store-local-binding**: rec-e5d4e992-8ac9-4166-b781-a2c6c8b8c552; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-12ebe800-6c2d-4690-8b17-3d76383bbe03](.artifacts/records/project__check-run/rec-12ebe800-6c2d-4690-8b17-3d76383bbe03.md))_
- **open-store-local-binding**: rec-e5d4e992-8ac9-4166-b781-a2c6c8b8c552; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-47e0284c-a97c-4212-8b87-e734fa8c72f5](.artifacts/records/project__check-run/rec-47e0284c-a97c-4212-8b87-e734fa8c72f5.md))_
- **open-store-local-binding**: rec-e5d4e992-8ac9-4166-b781-a2c6c8b8c552; dirty; fail; tdd _(id: [rec-d0e4b724-af83-423c-b608-6797df742ade](.artifacts/records/project__check-run/rec-d0e4b724-af83-423c-b608-6797df742ade.md))_

## open-store-none

### Acceptance
- **open-store-none**: R13; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r13_no_store -q _(id: [rec-b2468aae-dbf8-49e0-9120-1c5ca88064be](.artifacts/records/project__acceptance/rec-b2468aae-dbf8-49e0-9120-1c5ca88064be.md))_

### Check
- **open-store-none**: rec-b2468aae-dbf8-49e0-9120-1c5ca88064be; dirty; fail; tdd _(id: [rec-79fea413-e71e-4d33-bec1-165a37c10436](.artifacts/records/project__check-run/rec-79fea413-e71e-4d33-bec1-165a37c10436.md))_
- **open-store-none**: rec-b2468aae-dbf8-49e0-9120-1c5ca88064be; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-d70d51c1-52fb-4c3a-8084-7b403cfb4fd9](.artifacts/records/project__check-run/rec-d70d51c1-52fb-4c3a-8084-7b403cfb4fd9.md))_
- **open-store-none**: rec-b2468aae-dbf8-49e0-9120-1c5ca88064be; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-ee49b68b-25a9-4ca2-96af-459934a5cd53](.artifacts/records/project__check-run/rec-ee49b68b-25a9-4ca2-96af-459934a5cd53.md))_

## open-store-outside-git

### Acceptance
- **open-store-outside-git**: R2; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r2_outside_git -q _(id: [rec-44418b65-e4db-4694-90d1-2dc3d84736aa](.artifacts/records/project__acceptance/rec-44418b65-e4db-4694-90d1-2dc3d84736aa.md))_

### Check
- **open-store-outside-git**: rec-44418b65-e4db-4694-90d1-2dc3d84736aa; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-4f7accd9-16cf-4c02-8bcb-6205b39726e7](.artifacts/records/project__check-run/rec-4f7accd9-16cf-4c02-8bcb-6205b39726e7.md))_
- **open-store-outside-git**: rec-44418b65-e4db-4694-90d1-2dc3d84736aa; dirty; fail; tdd _(id: [rec-b1e133c7-d223-48a1-a723-5935cabc5d05](.artifacts/records/project__check-run/rec-b1e133c7-d223-48a1-a723-5935cabc5d05.md))_
- **open-store-outside-git**: rec-44418b65-e4db-4694-90d1-2dc3d84736aa; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-f51b224d-56b6-4ce8-868c-1ab7eb598a41](.artifacts/records/project__check-run/rec-f51b224d-56b6-4ce8-868c-1ab7eb598a41.md))_

## open-store-path

### Acceptance
- **open-store-path**: R3; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r3_store_argument -q _(id: [rec-ddc8facb-29f9-4eab-985e-7dc9fdb38f5c](.artifacts/records/project__acceptance/rec-ddc8facb-29f9-4eab-985e-7dc9fdb38f5c.md))_

### Check
- **open-store-path**: rec-ddc8facb-29f9-4eab-985e-7dc9fdb38f5c; dirty; fail; tdd _(id: [rec-2a8f73da-344e-4863-b5c3-3363b8a45baa](.artifacts/records/project__check-run/rec-2a8f73da-344e-4863-b5c3-3363b8a45baa.md))_
- **open-store-path**: rec-ddc8facb-29f9-4eab-985e-7dc9fdb38f5c; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-668d12c4-ee48-4934-9eab-35adc60b1cb3](.artifacts/records/project__check-run/rec-668d12c4-ee48-4934-9eab-35adc60b1cb3.md))_
- **open-store-path**: rec-ddc8facb-29f9-4eab-985e-7dc9fdb38f5c; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-efb6f4fb-93bd-47a6-a985-45a4b493fea9](.artifacts/records/project__check-run/rec-efb6f4fb-93bd-47a6-a985-45a4b493fea9.md))_

## open-store-path-missing

### Acceptance
- **open-store-path-missing**: R9; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r9_store_argument_missing_meta -q _(id: [rec-3811bbf0-6494-42e2-ab30-c092aad94cec](.artifacts/records/project__acceptance/rec-3811bbf0-6494-42e2-ab30-c092aad94cec.md))_

### Check
- **open-store-path-missing**: rec-3811bbf0-6494-42e2-ab30-c092aad94cec; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-6f1b0d7d-443f-4e0f-be25-97ff96250ccf](.artifacts/records/project__check-run/rec-6f1b0d7d-443f-4e0f-be25-97ff96250ccf.md))_
- **open-store-path-missing**: rec-3811bbf0-6494-42e2-ab30-c092aad94cec; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-81239428-84f0-405c-a0b0-41bc4bbe9d26](.artifacts/records/project__check-run/rec-81239428-84f0-405c-a0b0-41bc4bbe9d26.md))_
- **open-store-path-missing**: rec-3811bbf0-6494-42e2-ab30-c092aad94cec; dirty; fail; tdd _(id: [rec-f8b9db41-adf1-43db-ba77-14dfb9cca7b7](.artifacts/records/project__check-run/rec-f8b9db41-adf1-43db-ba77-14dfb9cca7b7.md))_

## open-store-repo-meta

### Acceptance
- **open-store-repo-meta**: R7; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r7_repo_meta -q _(id: [rec-65abc0da-9938-42dc-873e-f20d2c598bf2](.artifacts/records/project__acceptance/rec-65abc0da-9938-42dc-873e-f20d2c598bf2.md))_

### Check
- **open-store-repo-meta**: rec-65abc0da-9938-42dc-873e-f20d2c598bf2; c979dd13c06c36eb1a4f9f042e97ec4846903d7a; pass; tdd _(id: [rec-4042347a-79ed-4952-b258-8ab0edba30e9](.artifacts/records/project__check-run/rec-4042347a-79ed-4952-b258-8ab0edba30e9.md))_
- **open-store-repo-meta**: rec-65abc0da-9938-42dc-873e-f20d2c598bf2; dirty; fail; tdd _(id: [rec-9f230c22-5bf4-402f-8074-7464982b4508](.artifacts/records/project__check-run/rec-9f230c22-5bf4-402f-8074-7464982b4508.md))_
- **open-store-repo-meta**: rec-65abc0da-9938-42dc-873e-f20d2c598bf2; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-b281b06e-5f09-4d79-8ecd-ca6b0bf71c95](.artifacts/records/project__check-run/rec-b281b06e-5f09-4d79-8ecd-ca6b0bf71c95.md))_

## oracle-assertion-red

### Acceptance
- **oracle-assertion-red**: R2; tdd; workflow-loop; python3 -m pytest tests/test_oracle_red.py tests/test_affidavit_check.py -q -k 'failing_node or assertion_level or oracle_red' _(id: [rec-e8dc7437-e410-4b96-81c3-62f7914a9a22](.artifacts/records/project__acceptance/rec-e8dc7437-e410-4b96-81c3-62f7914a9a22.md))_

### Check
- **oracle-assertion-red**: rec-e8dc7437-e410-4b96-81c3-62f7914a9a22; 17d18aadc4fc771e1b864b3610365c218ee71d03; pass; tdd _(id: [rec-4a69438c-71e7-4cca-b5ce-b8db4e2fd6fa](.artifacts/records/project__check-run/rec-4a69438c-71e7-4cca-b5ce-b8db4e2fd6fa.md))_
- **oracle-assertion-red**: rec-e8dc7437-e410-4b96-81c3-62f7914a9a22; dirty; fail; tdd _(id: [rec-9caf8368-76c6-4276-875a-8808648c2af0](.artifacts/records/project__check-run/rec-9caf8368-76c6-4276-875a-8808648c2af0.md))_
- **oracle-assertion-red**: rec-e8dc7437-e410-4b96-81c3-62f7914a9a22; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; tdd _(id: [rec-cdc4e647-b8af-43bc-ba63-9e63895e72e4](.artifacts/records/project__check-run/rec-cdc4e647-b8af-43bc-ba63-9e63895e72e4.md))_
- **oracle-assertion-red**: rec-e8dc7437-e410-4b96-81c3-62f7914a9a22; 17d18aadc4fc771e1b864b3610365c218ee71d03; pass; tdd _(id: [rec-ee7c32b2-5d6e-4e5c-a751-26fb29dc9fc1](.artifacts/records/project__check-run/rec-ee7c32b2-5d6e-4e5c-a751-26fb29dc9fc1.md))_

## oracle-contract

### Acceptance
- **oracle-contract**: R3; check; workflow-loop; python3 -c "import json;from pathlib import Path;d=json.loads(Path('contract/project-design.json').read_text());types={t['name']:t for t in d['records']};a=types['acceptance'];assert 'test_ids' in a['payload'] and 'oracle_hashes' in a['payload'];assert 'test_ids' in a.get('optional_payload',[]) and 'oracle_hashes' in a.get('optional_payload',[]);am=types['oracle-amendment'];assert set(am['required_sections'])>={'Reason','Change'};assert 'status' in am['payload'];assert set(am.get('payload_enum',{}).get('status',[]))>={'requested','approved','rejected'}" _(id: [rec-753fcb78-34c3-4d72-8da8-948d99fa75f2](.artifacts/records/project__acceptance/rec-753fcb78-34c3-4d72-8da8-948d99fa75f2.md))_

### Check
- **oracle-contract**: rec-753fcb78-34c3-4d72-8da8-948d99fa75f2; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-454f600e-d1e1-4aed-af39-72c848211a8b](.artifacts/records/project__check-run/rec-454f600e-d1e1-4aed-af39-72c848211a8b.md))_
- **oracle-contract**: rec-753fcb78-34c3-4d72-8da8-948d99fa75f2; 17d18aadc4fc771e1b864b3610365c218ee71d03; pass; check _(id: [rec-9e149444-faa6-4c09-a766-f3fec6d211df](.artifacts/records/project__check-run/rec-9e149444-faa6-4c09-a766-f3fec6d211df.md))_
- **oracle-contract**: rec-753fcb78-34c3-4d72-8da8-948d99fa75f2; 17d18aadc4fc771e1b864b3610365c218ee71d03; pass; check _(id: [rec-dd2ba630-92ec-4e03-a3dd-23831b7efb12](.artifacts/records/project__check-run/rec-dd2ba630-92ec-4e03-a3dd-23831b7efb12.md))_

## oracle-contract-amendment-type

### Acceptance
- **oracle-contract-amendment-type**: R4; check; workflow-loop; python3 -c "import json;from pathlib import Path;d=json.loads(Path('contract/project-design.json').read_text());am=next(t for t in d['records'] if t['name']=='oracle-amendment');assert am['payload_references'].get('acceptance')=='project:acceptance';assert 'old_hashes' in am['payload'] and 'new_hashes' in am['payload']" _(id: [rec-5cc71e22-8776-4d3e-838c-a4a08812d3cd](.artifacts/records/project__acceptance/rec-5cc71e22-8776-4d3e-838c-a4a08812d3cd.md))_

### Check
- **oracle-contract-amendment-type**: rec-5cc71e22-8776-4d3e-838c-a4a08812d3cd; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-4411c43e-7bba-43c9-8ae9-227dc55bbe75](.artifacts/records/project__check-run/rec-4411c43e-7bba-43c9-8ae9-227dc55bbe75.md))_
- **oracle-contract-amendment-type**: rec-5cc71e22-8776-4d3e-838c-a4a08812d3cd; 17d18aadc4fc771e1b864b3610365c218ee71d03; pass; check _(id: [rec-958d1b0a-bdef-4398-9786-1bdd5dcd6f8c](.artifacts/records/project__check-run/rec-958d1b0a-bdef-4398-9786-1bdd5dcd6f8c.md))_
- **oracle-contract-amendment-type**: rec-5cc71e22-8776-4d3e-838c-a4a08812d3cd; 17d18aadc4fc771e1b864b3610365c218ee71d03; pass; check _(id: [rec-aafee77e-19be-46d2-8672-2081b22231f0](.artifacts/records/project__check-run/rec-aafee77e-19be-46d2-8672-2081b22231f0.md))_

## oracle-freeze-close

### Acceptance
- **oracle-freeze-close**: R5; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'oracle or freeze or assertion_level' _(id: [rec-84698b95-b79b-442a-9166-f2e168797d33](.artifacts/records/project__acceptance/rec-84698b95-b79b-442a-9166-f2e168797d33.md))_

### Check
- **oracle-freeze-close**: rec-84698b95-b79b-442a-9166-f2e168797d33; dirty; fail; tdd _(id: [rec-1074b37c-28b2-4d11-b951-320ca1c4e43b](.artifacts/records/project__check-run/rec-1074b37c-28b2-4d11-b951-320ca1c4e43b.md))_
- **oracle-freeze-close**: rec-84698b95-b79b-442a-9166-f2e168797d33; 977750c3c4f05015bcf03d4b82c77d25c8f039d3; pass; tdd _(id: [rec-83dc1ca1-0dda-4af0-a93b-db44f156fbb4](.artifacts/records/project__check-run/rec-83dc1ca1-0dda-4af0-a93b-db44f156fbb4.md))_
- **oracle-freeze-close**: rec-84698b95-b79b-442a-9166-f2e168797d33; dirty; fail; tdd _(id: [rec-b994aff7-12fe-4f6e-a851-1f74a4d12192](.artifacts/records/project__check-run/rec-b994aff7-12fe-4f6e-a851-1f74a4d12192.md))_
- **oracle-freeze-close**: rec-84698b95-b79b-442a-9166-f2e168797d33; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; tdd _(id: [rec-db251c9d-5d63-4cb8-a6c5-dbe799f126c5](.artifacts/records/project__check-run/rec-db251c9d-5d63-4cb8-a6c5-dbe799f126c5.md))_

## oracle-freeze-close-hashes

### Acceptance
- **oracle-freeze-close-hashes**: R3; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'oracle_hash or freeze_hash or amendment' _(id: [rec-08e82b2b-f39f-4c7c-ac4e-b0c758b7f337](.artifacts/records/project__acceptance/rec-08e82b2b-f39f-4c7c-ac4e-b0c758b7f337.md))_

### Check
- **oracle-freeze-close-hashes**: rec-08e82b2b-f39f-4c7c-ac4e-b0c758b7f337; dirty; fail; tdd _(id: [rec-33588d05-618d-45c2-a209-ff09d2a78bcb](.artifacts/records/project__check-run/rec-33588d05-618d-45c2-a209-ff09d2a78bcb.md))_
- **oracle-freeze-close-hashes**: rec-08e82b2b-f39f-4c7c-ac4e-b0c758b7f337; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; tdd _(id: [rec-75de1caa-137c-4f02-8b69-2dc6fd05e7a8](.artifacts/records/project__check-run/rec-75de1caa-137c-4f02-8b69-2dc6fd05e7a8.md))_
- **oracle-freeze-close-hashes**: rec-08e82b2b-f39f-4c7c-ac4e-b0c758b7f337; 977750c3c4f05015bcf03d4b82c77d25c8f039d3; pass; tdd _(id: [rec-979f65bc-7e53-4d1e-b38c-8de0fb1ede36](.artifacts/records/project__check-run/rec-979f65bc-7e53-4d1e-b38c-8de0fb1ede36.md))_

## oracle-red-cli-surface

### Acceptance
- **oracle-red-cli-surface**: R8; tdd; workflow-loop; python3 -m pytest tests/test_affidavit_import_boundary.py::test_close_batch_does_not_import_affidavit -q _(id: [rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5](.artifacts/records/project__acceptance/rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5.md))_

### Check
- **oracle-red-cli-surface**: rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-1c03daa2-3450-4610-ba37-0f878c14381c](.artifacts/records/project__check-run/rec-1c03daa2-3450-4610-ba37-0f878c14381c.md))_
- **oracle-red-cli-surface**: rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-2a7f8d81-61ea-4b50-ac68-41e1ffd8ec5f](.artifacts/records/project__check-run/rec-2a7f8d81-61ea-4b50-ac68-41e1ffd8ec5f.md))_
- **oracle-red-cli-surface**: rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5; dirty; fail; tdd _(id: [rec-71acb210-c402-465e-9c0b-3fbcdbcf4b46](.artifacts/records/project__check-run/rec-71acb210-c402-465e-9c0b-3fbcdbcf4b46.md))_
- **oracle-red-cli-surface**: rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5; dirty; fail; tdd _(id: [rec-7f85da84-3084-4964-9d97-8a59f147ea18](.artifacts/records/project__check-run/rec-7f85da84-3084-4964-9d97-8a59f147ea18.md))_
- **oracle-red-cli-surface**: rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5; 51cd740b7588ae41ef9a50360d992d6995d1e09d; fail; tdd _(id: [rec-93f426b3-1a92-4883-814b-a9b03e925fdf](.artifacts/records/project__check-run/rec-93f426b3-1a92-4883-814b-a9b03e925fdf.md))_
- **oracle-red-cli-surface**: rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5; 61b77e4f1958556f05a740269859441df8726e10; fail; tdd _(id: [rec-a087de5a-721e-4d6d-9108-6c26894ce23c](.artifacts/records/project__check-run/rec-a087de5a-721e-4d6d-9108-6c26894ce23c.md))_
- **oracle-red-cli-surface**: rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-a873caba-da50-4b35-9ad2-b2d1bd87ee43](.artifacts/records/project__check-run/rec-a873caba-da50-4b35-9ad2-b2d1bd87ee43.md))_
- **oracle-red-cli-surface**: rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-f09e7021-d904-49db-8a46-fd9aa1cf59e6](.artifacts/records/project__check-run/rec-f09e7021-d904-49db-8a46-fd9aa1cf59e6.md))_

## oracle-red-cli-surface-invoke

### Acceptance
- **oracle-red-cli-surface-invoke**: R9; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py::test_oracle_backed_close_invokes_aff_cli_for_assertion_red tests/test_close_batch.py::test_oracle_red_refuses_when_aff_cli_classification_fails -q _(id: [rec-af80005c-c965-4740-b41e-08a8d9fd94a9](.artifacts/records/project__acceptance/rec-af80005c-c965-4740-b41e-08a8d9fd94a9.md))_

### Check
- **oracle-red-cli-surface-invoke**: rec-af80005c-c965-4740-b41e-08a8d9fd94a9; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-153c5b4f-6b2c-419e-8e80-16078ccda9e1](.artifacts/records/project__check-run/rec-153c5b4f-6b2c-419e-8e80-16078ccda9e1.md))_
- **oracle-red-cli-surface-invoke**: rec-af80005c-c965-4740-b41e-08a8d9fd94a9; dirty; fail; tdd _(id: [rec-1cb8e54a-13ad-4c7a-a0ec-47788ced1a64](.artifacts/records/project__check-run/rec-1cb8e54a-13ad-4c7a-a0ec-47788ced1a64.md))_
- **oracle-red-cli-surface-invoke**: rec-af80005c-c965-4740-b41e-08a8d9fd94a9; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; tdd _(id: [rec-2ad1a821-1a61-41b1-9460-6abeb383c9c3](.artifacts/records/project__check-run/rec-2ad1a821-1a61-41b1-9460-6abeb383c9c3.md))_
- **oracle-red-cli-surface-invoke**: rec-af80005c-c965-4740-b41e-08a8d9fd94a9; dirty; fail; tdd _(id: [rec-3df10181-2872-4355-a7a8-0f87419902cd](.artifacts/records/project__check-run/rec-3df10181-2872-4355-a7a8-0f87419902cd.md))_
- **oracle-red-cli-surface-invoke**: rec-af80005c-c965-4740-b41e-08a8d9fd94a9; 61b77e4f1958556f05a740269859441df8726e10; fail; tdd _(id: [rec-60aae5e0-40bf-4b5f-9624-fe13469d1f57](.artifacts/records/project__check-run/rec-60aae5e0-40bf-4b5f-9624-fe13469d1f57.md))_
- **oracle-red-cli-surface-invoke**: rec-af80005c-c965-4740-b41e-08a8d9fd94a9; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-df3c0383-e92f-4b2a-96dd-b6b431ce1819](.artifacts/records/project__check-run/rec-df3c0383-e92f-4b2a-96dd-b6b431ce1819.md))_
- **oracle-red-cli-surface-invoke**: rec-af80005c-c965-4740-b41e-08a8d9fd94a9; 51cd740b7588ae41ef9a50360d992d6995d1e09d; fail; tdd _(id: [rec-f78202bc-7d8f-48b7-834f-2ae17f383f45](.artifacts/records/project__check-run/rec-f78202bc-7d8f-48b7-834f-2ae17f383f45.md))_
- **oracle-red-cli-surface-invoke**: rec-af80005c-c965-4740-b41e-08a8d9fd94a9; 8e54d3f4dbe3f3e0767b78673243092a27b9aa75; pass; tdd _(id: [rec-fc4cfca0-63a1-4001-966e-32f6496891f5](.artifacts/records/project__check-run/rec-fc4cfca0-63a1-4001-966e-32f6496891f5.md))_

## oracle-skills

### Acceptance
- **oracle-skills**: R7; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q _(id: [rec-f9ef85f0-efd5-4a31-8262-9eb7d6858bee](.artifacts/records/project__acceptance/rec-f9ef85f0-efd5-4a31-8262-9eb7d6858bee.md))_

### Check
- **oracle-skills**: rec-f9ef85f0-efd5-4a31-8262-9eb7d6858bee; 977750c3c4f05015bcf03d4b82c77d25c8f039d3; pass; check _(id: [rec-036ef863-0d1b-4b8d-8472-b52458513058](.artifacts/records/project__check-run/rec-036ef863-0d1b-4b8d-8472-b52458513058.md))_
- **oracle-skills**: rec-f9ef85f0-efd5-4a31-8262-9eb7d6858bee; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-67da4e57-1c4e-43ea-9c29-8bdfe3247056](.artifacts/records/project__check-run/rec-67da4e57-1c4e-43ea-9c29-8bdfe3247056.md))_

## oracle-skills-execute-amend

### Acceptance
- **oracle-skills-execute-amend**: R4; check; workflow-loop; rg -n "oracle-amendment|frozen oracle|oracle_hashes" skills/execute-phase/SKILL.md skills/verify-work/SKILL.md _(id: [rec-53cde3fc-6823-4f72-a863-861b55a3bf11](.artifacts/records/project__acceptance/rec-53cde3fc-6823-4f72-a863-861b55a3bf11.md))_

### Check
- **oracle-skills-execute-amend**: rec-53cde3fc-6823-4f72-a863-861b55a3bf11; 977750c3c4f05015bcf03d4b82c77d25c8f039d3; pass; check _(id: [rec-14797e08-b8fe-46c5-b107-089b24adfd3b](.artifacts/records/project__check-run/rec-14797e08-b8fe-46c5-b107-089b24adfd3b.md))_
- **oracle-skills-execute-amend**: rec-53cde3fc-6823-4f72-a863-861b55a3bf11; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-251adde1-feb1-4894-b59a-1ecbd04d41cf](.artifacts/records/project__check-run/rec-251adde1-feb1-4894-b59a-1ecbd04d41cf.md))_

## oracle-skills-mechanical-verify

### Acceptance
- **oracle-skills-mechanical-verify**: R6; check; workflow-loop; rg -n "mechanical|assertion-level|oracle-backed" skills/verify-work/SKILL.md _(id: [rec-d3fde647-9d4d-468a-a9fc-7635ac187eeb](.artifacts/records/project__acceptance/rec-d3fde647-9d4d-468a-a9fc-7635ac187eeb.md))_

### Check
- **oracle-skills-mechanical-verify**: rec-d3fde647-9d4d-468a-a9fc-7635ac187eeb; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-0d4cfbfb-f968-49fe-86b2-633f95799a35](.artifacts/records/project__check-run/rec-0d4cfbfb-f968-49fe-86b2-633f95799a35.md))_
- **oracle-skills-mechanical-verify**: rec-d3fde647-9d4d-468a-a9fc-7635ac187eeb; 977750c3c4f05015bcf03d4b82c77d25c8f039d3; pass; check _(id: [rec-a02e9b4e-b827-4d24-bd92-e34673bdf924](.artifacts/records/project__check-run/rec-a02e9b4e-b827-4d24-bd92-e34673bdf924.md))_

## oracle-skills-plan-author

### Acceptance
- **oracle-skills-plan-author**: R1; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q -k 'oracle or freeze or plan_phase' _(id: [rec-0ecbff55-619a-4c5a-ad17-a582ef26dc85](.artifacts/records/project__acceptance/rec-0ecbff55-619a-4c5a-ad17-a582ef26dc85.md))_

### Check
- **oracle-skills-plan-author**: rec-0ecbff55-619a-4c5a-ad17-a582ef26dc85; 977750c3c4f05015bcf03d4b82c77d25c8f039d3; pass; check _(id: [rec-2a42fb6b-06c4-43b1-9591-0f374888c966](.artifacts/records/project__check-run/rec-2a42fb6b-06c4-43b1-9591-0f374888c966.md))_
- **oracle-skills-plan-author**: rec-0ecbff55-619a-4c5a-ad17-a582ef26dc85; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-8def3f22-55e5-4a8b-a5ef-f5e6c299186b](.artifacts/records/project__check-run/rec-8def3f22-55e5-4a8b-a5ef-f5e6c299186b.md))_

## oracle-witnesses-review

### Check
- **oracle-witnesses-review**: oracle-witnesses-review; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; review _(id: [rec-6b678de4-4001-4b62-a130-26c6281db2bd](.artifacts/records/project__check-run/rec-6b678de4-4001-4b62-a130-26c6281db2bd.md))_
- **oracle-witnesses-review**: oracle-witnesses-review; b9adc0ee0836b843fd963ca38ad105d5e2176b68; fail; review _(id: [rec-ed5c94f3-58c2-475a-a4cd-1d00f8b91157](.artifacts/records/project__check-run/rec-ed5c94f3-58c2-475a-a4cd-1d00f8b91157.md))_

## oracle-witnesses-suite

### Check
- **oracle-witnesses-suite**: oracle-witnesses-suite; e04bc30552d35b83b19337abee8df4c26cb55b61; fail; check _(id: [rec-3277801e-724c-40f9-a89d-61a1f47e16cb](.artifacts/records/project__check-run/rec-3277801e-724c-40f9-a89d-61a1f47e16cb.md))_

## orchestra-callers-review

### Check
- **orchestra-callers-review**: orchestra-callers-review; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; review _(id: [rec-2a6d8859-55ee-40e9-be27-ecd5bc4697f0](.artifacts/records/project__check-run/rec-2a6d8859-55ee-40e9-be27-ecd5bc4697f0.md))_
- **orchestra-callers-review**: orchestra-callers-review; 1014602caaf7264234fc5409e50ec63f80f9cd5a; fail; review _(id: [rec-d897afe3-bba8-4260-9e74-75a8ee24d365](.artifacts/records/project__check-run/rec-d897afe3-bba8-4260-9e74-75a8ee24d365.md))_

## package-install

### Acceptance
- **package-install**: check; dashboard; d=$(mktemp -d) && bash scripts/sync-plugin.sh "$d/p" && test -d "$d/p/dashboard" && "$d/p/dashboard/bin/dashboard" --once _(id: [rec-0379e3d0-879a-4bc5-982a-7ed054623149](.artifacts/records/project__acceptance/rec-0379e3d0-879a-4bc5-982a-7ed054623149.md))_

### Check
- **package-install**: rec-67e721d5-5b8f-482f-b2d7-f9f25c8ec7e3; dirty; pass; check _(id: [rec-1480d72c-012b-4fd8-a3f6-28eb7ff34e2d](.artifacts/records/project__check-run/rec-1480d72c-012b-4fd8-a3f6-28eb7ff34e2d.md))_
- **package-install**: rec-0379e3d0-879a-4bc5-982a-7ed054623149; dirty; pass; check _(id: [rec-901438c7-6124-42ac-8f32-370c6c494f2d](.artifacts/records/project__check-run/rec-901438c7-6124-42ac-8f32-370c6c494f2d.md))_

## package-install-docs

### Acceptance
- **package-install-docs**: check; dashboard; ! grep -nE 'scripts/(dashboard|tmux-dashboard)' README.md dashboard/tmux.conf _(id: [rec-67e721d5-5b8f-482f-b2d7-f9f25c8ec7e3](.artifacts/records/project__acceptance/rec-67e721d5-5b8f-482f-b2d7-f9f25c8ec7e3.md))_

## package-metadata

### Acceptance
- **package-metadata**: R1; tdd; library-boundary; AFFIDAVIT_ROOT=/home/andrewyin/affidavit/.worktrees/declared-install python3 -m pytest tests/test_declared_install_metadata.py::test_r1_affidavit_depends_on_adaptive_artifacts -q _(id: [rec-2d3bf9c9-bea6-4673-9d36-29d197dd81b0](.artifacts/records/project__acceptance/rec-2d3bf9c9-bea6-4673-9d36-29d197dd81b0.md))_

### Check
- **package-metadata**: rec-2d3bf9c9-bea6-4673-9d36-29d197dd81b0; eca028601fff7845f1b1cca665f4c09b267878d5; pass; tdd _(id: [rec-1eb274ce-4d93-4673-9b8f-da9a001a7070](.artifacts/records/project__check-run/rec-1eb274ce-4d93-4673-9b8f-da9a001a7070.md))_
- **package-metadata**: rec-2d3bf9c9-bea6-4673-9d36-29d197dd81b0; dirty; fail; tdd _(id: [rec-83f47560-8faa-4fd1-9f46-a430c9f1eb06](.artifacts/records/project__check-run/rec-83f47560-8faa-4fd1-9f46-a430c9f1eb06.md))_

## package-metadata-evidence

### Acceptance
- **package-metadata-evidence**: R4; tdd; library-boundary; AFFIDAVIT_ROOT=/home/andrewyin/affidavit/.worktrees/declared-install python3 -m pytest tests/test_declared_install_metadata.py::test_r4_evidence_extra_depends_on_affidavit -q _(id: [rec-d729a179-bd41-4a22-b54d-ca93eaa2c4fc](.artifacts/records/project__acceptance/rec-d729a179-bd41-4a22-b54d-ca93eaa2c4fc.md))_

### Check
- **package-metadata-evidence**: rec-d729a179-bd41-4a22-b54d-ca93eaa2c4fc; eca028601fff7845f1b1cca665f4c09b267878d5; pass; tdd _(id: [rec-74a66144-07ea-4d23-8590-6d17c461595c](.artifacts/records/project__check-run/rec-74a66144-07ea-4d23-8590-6d17c461595c.md))_
- **package-metadata-evidence**: rec-d729a179-bd41-4a22-b54d-ca93eaa2c4fc; dirty; fail; tdd _(id: [rec-d5fe7fb7-d2b7-45f4-b91b-69894c5d2a31](.artifacts/records/project__check-run/rec-d5fe7fb7-d2b7-45f4-b91b-69894c5d2a31.md))_

## package-metadata-optional

### Acceptance
- **package-metadata-optional**: R3; check; library-boundary; python3 -c 'import pathlib; t=pathlib.Path("pyproject.toml").read_text(); i=t.index("\ndependencies"); chunk=t[i:t.index("]", i)]; assert "affidavit" not in chunk' _(id: [rec-d16228da-0add-439f-bfe8-ced554846bc5](.artifacts/records/project__acceptance/rec-d16228da-0add-439f-bfe8-ced554846bc5.md))_

### Check
- **package-metadata-optional**: rec-d16228da-0add-439f-bfe8-ced554846bc5; eca028601fff7845f1b1cca665f4c09b267878d5; pass; check _(id: [rec-19a045df-5a1c-40c6-8db5-1e8a62c084af](.artifacts/records/project__check-run/rec-19a045df-5a1c-40c6-8db5-1e8a62c084af.md))_

## package-metadata-orchestra

### Acceptance
- **package-metadata-orchestra**: R2; check; library-boundary; python3 -c 'import pathlib; t=pathlib.Path("pyproject.toml").read_text(); i=t.index("\ndependencies"); chunk=t[i:t.index("]", i)]; assert "adaptive-artifacts" in chunk' _(id: [rec-f25bd119-e907-4f07-b265-1701c0ee8fb3](.artifacts/records/project__acceptance/rec-f25bd119-e907-4f07-b265-1701c0ee8fb3.md))_

### Check
- **package-metadata-orchestra**: rec-f25bd119-e907-4f07-b265-1701c0ee8fb3; eca028601fff7845f1b1cca665f4c09b267878d5; pass; check _(id: [rec-d98dae11-df0c-4b91-9b1f-e069719966f1](.artifacts/records/project__check-run/rec-d98dae11-df0c-4b91-9b1f-e069719966f1.md))_

## package-move

### Acceptance
- **package-move**: tdd; dashboard; test ! -e scripts/dashboard_app.py && test ! -e scripts/dashboard_model.py && test ! -e scripts/artifact_store.py && uv run --with pytest --with textual pytest tests/test_dashboard_app.py tests/test_dashboard_model.py tests/test_dashboard_launcher.py tests/test_dashboard_status.py tests/test_dashboard_view.py tests/test_dashboard_integration.py _(id: [rec-976f8b89-c8c7-4ced-855d-c8c5b3c6c2fb](.artifacts/records/project__acceptance/rec-976f8b89-c8c7-4ced-855d-c8c5b3c6c2fb.md))_

### Check
- **package-move**: rec-976f8b89-c8c7-4ced-855d-c8c5b3c6c2fb; dirty; pass; tdd _(id: [rec-524596ef-2c2e-488e-acc4-0b850f58362d](.artifacts/records/project__check-run/rec-524596ef-2c2e-488e-acc4-0b850f58362d.md))_
- **package-move**: rec-976f8b89-c8c7-4ced-855d-c8c5b3c6c2fb; dirty; pass; tdd _(id: [rec-938ca635-730a-422b-88a4-cd839b708d92](.artifacts/records/project__check-run/rec-938ca635-730a-422b-88a4-cd839b708d92.md))_
- **package-move**: rec-976f8b89-c8c7-4ced-855d-c8c5b3c6c2fb; dirty; pass; tdd _(id: [rec-cb7c9400-741c-4295-8e88-22fdbc1d748f](.artifacts/records/project__check-run/rec-cb7c9400-741c-4295-8e88-22fdbc1d748f.md))_

## pane-width-stable

### Acceptance
- **pane-width-stable**: tdd; dashboard; for i in $(seq 20); do uv run -q --with textual --with pytest --with pytest-xdist python -m pytest tests/test_dashboard_app.py -q -n 4 -p no:cacheprovider || break; done _(id: [rec-ef569598-f20a-4623-ba96-4f0c32edf9f1](.artifacts/records/project__acceptance/rec-ef569598-f20a-4623-ba96-4f0c32edf9f1.md))_

### Check
- **pane-width-stable**: rec-ef569598-f20a-4623-ba96-4f0c32edf9f1; 8d1ef88f88d964b4fc3a400ca293e63ac5fcf1fc; pass; tdd _(id: [rec-d3f599ae-0312-45ec-a47b-f4bcbb2dddd9](.artifacts/records/project__check-run/rec-d3f599ae-0312-45ec-a47b-f4bcbb2dddd9.md))_

### Observation
- **pane-width-stable**: Parent reran the acceptance loop on 8d1ef88: 20/20 clean, 204 passed each. Textual sends no Resize when a widget's own scrollbar toggles; the pane now refits on show_vertical_scrollbar.; dashboard-features _(id: [rec-9b177ada-79ac-4e14-b264-102f00afbf0c](.artifacts/records/project__investigation-observation/rec-9b177ada-79ac-4e14-b264-102f00afbf0c.md))_

## phase-detail-tasks

### Acceptance
- **phase-detail-tasks**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k phase_task _(id: [rec-2356a60d-0eda-499f-b3ab-ee4746d6aa45](.artifacts/records/project__acceptance/rec-2356a60d-0eda-499f-b3ab-ee4746d6aa45.md))_

### Check
- **phase-detail-tasks**: rec-2356a60d-0eda-499f-b3ab-ee4746d6aa45; 1a9ce2781018b688d55b0d949f3e18a2aca70873; pass; tdd _(id: [rec-f9db072e-5521-4e3a-9f86-d1675f5f4775](.artifacts/records/project__check-run/rec-f9db072e-5521-4e3a-9f86-d1675f5f4775.md))_

### Observation
- **phase-detail-tasks**: Cherry-pick onto task-detail-links conflicted only where both added a list class (LinkList, PhaseTaskList); parent kept both; the combined app tests pass (190).; dashboard-features _(id: [rec-31107cb0-d8f3-457b-acd6-e04ed4f3508f](.artifacts/records/project__investigation-observation/rec-31107cb0-d8f3-457b-acd6-e04ed4f3508f.md))_

## phase-end-cleanup

### Acceptance
- **phase-end-cleanup**: R22; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r22_phase_close_removes_each_task_worktree -q --tb=short _(id: [rec-e176758e-9b0f-49b0-a359-035a344da71f](.artifacts/records/project__acceptance/rec-e176758e-9b0f-49b0-a359-035a344da71f.md))_

### Check
- **phase-end-cleanup**: rec-e176758e-9b0f-49b0-a359-035a344da71f; dirty; fail; tdd _(id: [rec-18e4b72c-de25-435b-b369-e61e1ef9dd92](.artifacts/records/project__check-run/rec-18e4b72c-de25-435b-b369-e61e1ef9dd92.md))_
- **phase-end-cleanup**: rec-e176758e-9b0f-49b0-a359-035a344da71f; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-3c513114-f644-498b-9ecc-3e58d8ea0574](.artifacts/records/project__check-run/rec-3c513114-f644-498b-9ecc-3e58d8ea0574.md))_
- **phase-end-cleanup**: rec-e176758e-9b0f-49b0-a359-035a344da71f; dirty; fail; tdd _(id: [rec-8e13f762-c7bf-4f1d-a579-50b8938db4b0](.artifacts/records/project__check-run/rec-8e13f762-c7bf-4f1d-a579-50b8938db4b0.md))_
- **phase-end-cleanup**: rec-e176758e-9b0f-49b0-a359-035a344da71f; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-a07b5762-6957-442d-8894-c2d494ab0075](.artifacts/records/project__check-run/rec-a07b5762-6957-442d-8894-c2d494ab0075.md))_
- **phase-end-cleanup**: rec-e176758e-9b0f-49b0-a359-035a344da71f; dirty; fail; tdd _(id: [rec-c0983d5a-5578-4f8f-9e45-52557ed626b3](.artifacts/records/project__check-run/rec-c0983d5a-5578-4f8f-9e45-52557ed626b3.md))_
- **phase-end-cleanup**: rec-e176758e-9b0f-49b0-a359-035a344da71f; dirty; fail; tdd _(id: [rec-c323c6b8-56c1-4f6f-a0c3-f660eeb256a1](.artifacts/records/project__check-run/rec-c323c6b8-56c1-4f6f-a0c3-f660eeb256a1.md))_

## phase-end-cleanup-r23

### Acceptance
- **phase-end-cleanup-r23**: R23; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r23_phase_close_deletes_task_branches_contained_in_the_phase_branch -q --tb=short _(id: [rec-111eddcd-d564-4ec9-9857-c55931bc3ccd](.artifacts/records/project__acceptance/rec-111eddcd-d564-4ec9-9857-c55931bc3ccd.md))_

### Check
- **phase-end-cleanup-r23**: rec-111eddcd-d564-4ec9-9857-c55931bc3ccd; dirty; fail; tdd _(id: [rec-2a9ceac6-e488-420f-a408-69ecbdb7c4dd](.artifacts/records/project__check-run/rec-2a9ceac6-e488-420f-a408-69ecbdb7c4dd.md))_
- **phase-end-cleanup-r23**: rec-111eddcd-d564-4ec9-9857-c55931bc3ccd; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-568a7db2-74be-45f9-be0c-540adfe350c2](.artifacts/records/project__check-run/rec-568a7db2-74be-45f9-be0c-540adfe350c2.md))_
- **phase-end-cleanup-r23**: rec-111eddcd-d564-4ec9-9857-c55931bc3ccd; dirty; fail; tdd _(id: [rec-79cd801a-79f3-46da-a694-682e87d8d389](.artifacts/records/project__check-run/rec-79cd801a-79f3-46da-a694-682e87d8d389.md))_
- **phase-end-cleanup-r23**: rec-111eddcd-d564-4ec9-9857-c55931bc3ccd; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-9d64290a-e467-458b-b25c-3e4b218ade7d](.artifacts/records/project__check-run/rec-9d64290a-e467-458b-b25c-3e4b218ade7d.md))_
- **phase-end-cleanup-r23**: rec-111eddcd-d564-4ec9-9857-c55931bc3ccd; dirty; fail; tdd _(id: [rec-d0d8dce2-4d26-4421-959d-ff888b1743fb](.artifacts/records/project__check-run/rec-d0d8dce2-4d26-4421-959d-ff888b1743fb.md))_
- **phase-end-cleanup-r23**: rec-111eddcd-d564-4ec9-9857-c55931bc3ccd; dirty; fail; tdd _(id: [rec-f41206ea-e26c-4de3-9acc-9d48c68bdd67](.artifacts/records/project__check-run/rec-f41206ea-e26c-4de3-9acc-9d48c68bdd67.md))_

## phase-gate-contract

### Acceptance
- **phase-gate-contract**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py -q -k phase_gate _(id: [rec-6e293e6f-8e8d-48c3-9344-25b4e7b8e35d](.artifacts/records/project__acceptance/rec-6e293e6f-8e8d-48c3-9344-25b4e7b8e35d.md))_

### Check
- **phase-gate-contract**: rec-6e293e6f-8e8d-48c3-9344-25b4e7b8e35d; c681c767ae0c0a5888399c7d81df58df7cce6e16; pass; tdd _(id: [rec-4a315bf0-1e78-4241-9b2d-288bf6f8598d](.artifacts/records/project__check-run/rec-4a315bf0-1e78-4241-9b2d-288bf6f8598d.md))_
- **phase-gate-contract**: rec-6e293e6f-8e8d-48c3-9344-25b4e7b8e35d; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; tdd _(id: [rec-68bf5458-a2e6-4f10-9eb9-e4610516a1c1](.artifacts/records/project__check-run/rec-68bf5458-a2e6-4f10-9eb9-e4610516a1c1.md))_
- **phase-gate-contract**: rec-6e293e6f-8e8d-48c3-9344-25b4e7b8e35d; dirty; fail; tdd _(id: [rec-b368d91a-d2e3-49ae-a5be-577244db34a9](.artifacts/records/project__check-run/rec-b368d91a-d2e3-49ae-a5be-577244db34a9.md))_

## phase-gate-contract-repo

### Acceptance
- **phase-gate-contract-repo**: R6; check; workflow-loop; python3 -c "import json; from pathlib import Path; b=json.loads(Path('contract/project-design.json').read_text())['phase_gate']['suite']; assert b['mode']=='none'; s=json.loads(Path('.artifacts/project-design.json').read_text())['phase_gate']['suite']; assert s['mode']=='full' and s['gate']=='advisory' and 'pytest' in s['command']" _(id: [rec-a77cfc8e-569f-4671-b7c7-dc7a2481c024](.artifacts/records/project__acceptance/rec-a77cfc8e-569f-4671-b7c7-dc7a2481c024.md))_

### Check
- **phase-gate-contract-repo**: rec-a77cfc8e-569f-4671-b7c7-dc7a2481c024; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; check _(id: [rec-2f521435-2e77-4d2e-8167-531de2847990](.artifacts/records/project__check-run/rec-2f521435-2e77-4d2e-8167-531de2847990.md))_
- **phase-gate-contract-repo**: rec-a77cfc8e-569f-4671-b7c7-dc7a2481c024; c681c767ae0c0a5888399c7d81df58df7cce6e16; pass; check _(id: [rec-e98d300b-f1d2-4ec9-b96c-eff471dc746c](.artifacts/records/project__check-run/rec-e98d300b-f1d2-4ec9-b96c-eff471dc746c.md))_

## phase-model-selection

### Acceptance
- **phase-model-selection**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'default or selection' _(id: [rec-02c57648-41cf-4d1c-858e-45109cf1514f](.artifacts/records/project__acceptance/rec-02c57648-41cf-4d1c-858e-45109cf1514f.md))_

### Check
- **phase-model-selection**: rec-adb086d3-8dbf-4818-9b58-2c5838a1e177; dirty; pass; tdd _(id: [rec-492e9a12-7648-4645-9172-c34fa07ecca5](.artifacts/records/project__check-run/rec-492e9a12-7648-4645-9172-c34fa07ecca5.md))_
- **phase-model-selection**: rec-02c57648-41cf-4d1c-858e-45109cf1514f; dirty; pass; tdd _(id: [rec-4e8eb412-6a6c-4406-bf19-d3179cb04cd6](.artifacts/records/project__check-run/rec-4e8eb412-6a6c-4406-bf19-d3179cb04cd6.md))_
- **phase-model-selection**: rec-20aa09a5-4b31-4a35-b9c1-c6c1847d6d81; dirty; pass; tdd _(id: [rec-c5cfe635-9a9b-4497-8f2b-5c5bfb4588e3](.artifacts/records/project__check-run/rec-c5cfe635-9a9b-4497-8f2b-5c5bfb4588e3.md))_
- **phase-model-selection**: rec-345b233d-d1c8-4b73-9dd3-8ac45c2fd412; dirty; pass; tdd _(id: [rec-d7076287-a59e-4b85-96ba-303818121b0a](.artifacts/records/project__check-run/rec-d7076287-a59e-4b85-96ba-303818121b0a.md))_

## phase-model-selection-activity

### Acceptance
- **phase-model-selection-activity**: R10; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'activity' _(id: [rec-adb086d3-8dbf-4818-9b58-2c5838a1e177](.artifacts/records/project__acceptance/rec-adb086d3-8dbf-4818-9b58-2c5838a1e177.md))_

## phase-model-selection-follow

### Acceptance
- **phase-model-selection-follow**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'follow or pin' _(id: [rec-20aa09a5-4b31-4a35-b9c1-c6c1847d6d81](.artifacts/records/project__acceptance/rec-20aa09a5-4b31-4a35-b9c1-c6c1847d6d81.md))_

## phase-model-selection-nophase

### Acceptance
- **phase-model-selection-nophase**: R13; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'nophase or no_phase' _(id: [rec-345b233d-d1c8-4b73-9dd3-8ac45c2fd412](.artifacts/records/project__acceptance/rec-345b233d-d1c8-4b73-9dd3-8ac45c2fd412.md))_

## phase-once-render

### Acceptance
- **phase-once-render**: R14; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_integration.py -q -k 'once' _(id: [rec-65f00d59-aaa4-48e0-8f70-271787545434](.artifacts/records/project__acceptance/rec-65f00d59-aaa4-48e0-8f70-271787545434.md))_

### Check
- **phase-once-render**: rec-65f00d59-aaa4-48e0-8f70-271787545434; dirty; pass; check _(id: [rec-9dda60c8-bb7d-47e0-992b-245575ec5f5a](.artifacts/records/project__check-run/rec-9dda60c8-bb7d-47e0-992b-245575ec5f5a.md))_

## phase-overview-chrome

### Acceptance
- **phase-overview-chrome**: R1; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R1 _(id: [rec-b29164ce-f175-4ba4-82fa-321932c4e7de](.artifacts/records/project__acceptance/rec-b29164ce-f175-4ba4-82fa-321932c4e7de.md))_

### Check
- **phase-overview-chrome**: rec-b29164ce-f175-4ba4-82fa-321932c4e7de; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-c082ad1e-5484-41db-b3db-3da561e3b088](.artifacts/records/project__check-run/rec-c082ad1e-5484-41db-b3db-3da561e3b088.md))_

## phase-overview-chrome-r2

### Acceptance
- **phase-overview-chrome-r2**: R2; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R2 _(id: [rec-67018e2f-e797-40df-bef6-68cedebd96c0](.artifacts/records/project__acceptance/rec-67018e2f-e797-40df-bef6-68cedebd96c0.md))_

### Check
- **phase-overview-chrome-r2**: rec-67018e2f-e797-40df-bef6-68cedebd96c0; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-746a9592-0b3b-4a0a-8487-558f3527661c](.artifacts/records/project__check-run/rec-746a9592-0b3b-4a0a-8487-558f3527661c.md))_

## phase-overview-chrome-r3

### Acceptance
- **phase-overview-chrome-r3**: R3; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R3 _(id: [rec-88be0788-4c80-4ea1-a6b2-ed1b4d1c939f](.artifacts/records/project__acceptance/rec-88be0788-4c80-4ea1-a6b2-ed1b4d1c939f.md))_

### Check
- **phase-overview-chrome-r3**: rec-88be0788-4c80-4ea1-a6b2-ed1b4d1c939f; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-c3fc79d9-e102-48f5-bcac-82c03f2f6ea3](.artifacts/records/project__check-run/rec-c3fc79d9-e102-48f5-bcac-82c03f2f6ea3.md))_

## phase-overview-chrome-r4

### Acceptance
- **phase-overview-chrome-r4**: R4; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R4 _(id: [rec-1da92888-9b5b-44a7-8e29-0970c44cd76e](.artifacts/records/project__acceptance/rec-1da92888-9b5b-44a7-8e29-0970c44cd76e.md))_

### Check
- **phase-overview-chrome-r4**: rec-1da92888-9b5b-44a7-8e29-0970c44cd76e; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-a8927d2d-e338-441e-9ade-ed9afaf22204](.artifacts/records/project__check-run/rec-a8927d2d-e338-441e-9ade-ed9afaf22204.md))_

## phase-overview-chrome-r5

### Acceptance
- **phase-overview-chrome-r5**: R5; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R5 _(id: [rec-ac498629-cc10-4bae-bdf2-6c070f58a43c](.artifacts/records/project__acceptance/rec-ac498629-cc10-4bae-bdf2-6c070f58a43c.md))_

### Check
- **phase-overview-chrome-r5**: rec-ac498629-cc10-4bae-bdf2-6c070f58a43c; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-a5741ac8-92ed-4674-8687-4309f93369ae](.artifacts/records/project__check-run/rec-a5741ac8-92ed-4674-8687-4309f93369ae.md))_

## phase-overview-chrome-r6

### Acceptance
- **phase-overview-chrome-r6**: R6; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R6 _(id: [rec-67074614-68ef-49d5-84e1-70780ff98261](.artifacts/records/project__acceptance/rec-67074614-68ef-49d5-84e1-70780ff98261.md))_

### Check
- **phase-overview-chrome-r6**: rec-67074614-68ef-49d5-84e1-70780ff98261; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-3f511932-7d4e-40e8-b36e-51b173481d88](.artifacts/records/project__check-run/rec-3f511932-7d4e-40e8-b36e-51b173481d88.md))_

## phase-overview-chrome-r8

### Acceptance
- **phase-overview-chrome-r8**: R8; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R8 _(id: [rec-60eb2222-5daf-4fc0-af10-0a301472ca13](.artifacts/records/project__acceptance/rec-60eb2222-5daf-4fc0-af10-0a301472ca13.md))_

### Check
- **phase-overview-chrome-r8**: rec-60eb2222-5daf-4fc0-af10-0a301472ca13; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-48ac678e-7bba-474e-ab61-11589f5687bd](.artifacts/records/project__check-run/rec-48ac678e-7bba-474e-ab61-11589f5687bd.md))_

## phase-overview-review

### Check
- **phase-overview-review**: 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; review _(id: [rec-b9224051-8fbf-411a-b5e6-d5a6517c2e4d](.artifacts/records/project__check-run/rec-b9224051-8fbf-411a-b5e6-d5a6517c2e4d.md))_

## phase-overview-tabs

### Acceptance
- **phase-overview-tabs**: R7; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R7 _(id: [rec-9938dfb5-a08e-4b97-9779-fd9766636182](.artifacts/records/project__acceptance/rec-9938dfb5-a08e-4b97-9779-fd9766636182.md))_

### Check
- **phase-overview-tabs**: rec-9938dfb5-a08e-4b97-9779-fd9766636182; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-74c10b2a-c039-4063-98e7-18a58f550d70](.artifacts/records/project__check-run/rec-74c10b2a-c039-4063-98e7-18a58f550d70.md))_

## phase-overview-tabs-r9

### Acceptance
- **phase-overview-tabs-r9**: R9; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R9 _(id: [rec-3b4e5def-9aaf-4d52-bdf4-f67f33653119](.artifacts/records/project__acceptance/rec-3b4e5def-9aaf-4d52-bdf4-f67f33653119.md))_

### Check
- **phase-overview-tabs-r9**: rec-3b4e5def-9aaf-4d52-bdf4-f67f33653119; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-f24a7d19-98b7-4980-9dff-63c92715cf2a](.artifacts/records/project__check-run/rec-f24a7d19-98b7-4980-9dff-63c92715cf2a.md))_

## phase-position-skills

### Acceptance
- **phase-position-skills**: tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_phase_position.py -q _(id: [rec-9f326a41-7f0f-4d28-89c6-069154ad5a65](.artifacts/records/project__acceptance/rec-9f326a41-7f0f-4d28-89c6-069154ad5a65.md))_

### Check
- **phase-position-skills**: rec-9f326a41-7f0f-4d28-89c6-069154ad5a65; 8d0b7fd43309d93b0b7f2b3db0a3f8a1022e405b; pass; tdd _(id: [rec-77842b73-9ccb-479a-b84e-5cfd5dab3508](.artifacts/records/project__check-run/rec-77842b73-9ccb-479a-b84e-5cfd5dab3508.md))_

## phase-proof-packet-review

### Check
- **phase-proof-packet-review**: phase-proof-packet-review; c9c2d6a70719285637ba08662d4772f661e88a74; pass; review _(id: [rec-01b941b4-9d65-4f95-aedb-941960028b0a](.artifacts/records/project__check-run/rec-01b941b4-9d65-4f95-aedb-941960028b0a.md))_

## phase-reviewer-review

### Check
- **phase-reviewer-review**: rec-a5b4ff28-4664-45b7-9b25-489d4f58af19; 11a147e75daa100a2fbca2202399205b480b42e9; pass; review _(id: [rec-2b4e526d-ddb7-401f-910a-d4d5516c94f7](.artifacts/records/project__check-run/rec-2b4e526d-ddb7-401f-910a-d4d5516c94f7.md))_

## phase-sections

### Acceptance
- **phase-sections**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q _(id: [rec-611e26b5-b891-4e71-8951-3ebf07ecc715](.artifacts/records/project__acceptance/rec-611e26b5-b891-4e71-8951-3ebf07ecc715.md))_

### Check
- **phase-sections**: rec-611e26b5-b891-4e71-8951-3ebf07ecc715; 78548daa0ea66a4347d31d675b3f6fbd8c3b86f1; pass; tdd _(id: [rec-d0d98c8c-7d91-4cde-ac81-547b807803e4](.artifacts/records/project__check-run/rec-d0d98c8c-7d91-4cde-ac81-547b807803e4.md))_

## phase-selector-ui

### Acceptance
- **phase-selector-ui**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'selector or stepper' _(id: [rec-39f567da-de81-428f-91b0-131cded1ec16](.artifacts/records/project__acceptance/rec-39f567da-de81-428f-91b0-131cded1ec16.md))_

### Check
- **phase-selector-ui**: rec-bc7d46e2-0d5a-4792-882a-c2afecb5d2aa; dirty; pass; tdd _(id: [rec-6967f540-a927-465b-9c37-ac1e4332e470](.artifacts/records/project__check-run/rec-6967f540-a927-465b-9c37-ac1e4332e470.md))_
- **phase-selector-ui**: rec-c0a861da-d41b-4855-b6f9-44219c1f8343; dirty; pass; tdd _(id: [rec-80c77c92-de0b-4a05-881a-2aa137bfc366](.artifacts/records/project__check-run/rec-80c77c92-de0b-4a05-881a-2aa137bfc366.md))_
- **phase-selector-ui**: rec-39f567da-de81-428f-91b0-131cded1ec16; dirty; pass; tdd _(id: [rec-a7c8ebae-b28a-4560-8fc9-8e5d5b8c338a](.artifacts/records/project__check-run/rec-a7c8ebae-b28a-4560-8fc9-8e5d5b8c338a.md))_
- **phase-selector-ui**: rec-42fa4dd1-20c6-46e2-9809-1554757d18aa; dirty; pass; tdd _(id: [rec-b5fff2fe-47da-4626-9f2b-a673f58b4d89](.artifacts/records/project__check-run/rec-b5fff2fe-47da-4626-9f2b-a673f58b4d89.md))_
- **phase-selector-ui**: rec-1c86657d-12b9-4d8f-a50b-0f751e9410ad; dirty; pass; tdd _(id: [rec-e0dcb23a-fdc2-4672-a0a1-6fb3fed9201c](.artifacts/records/project__check-run/rec-e0dcb23a-fdc2-4672-a0a1-6fb3fed9201c.md))_
- **phase-selector-ui**: rec-eb4361b5-7a63-4383-980b-e9c14c7ea07a; dirty; pass; tdd _(id: [rec-ebd4715c-321c-4a4a-9fff-473b17f03734](.artifacts/records/project__check-run/rec-ebd4715c-321c-4a4a-9fff-473b17f03734.md))_
- **phase-selector-ui**: rec-551d6d24-2144-40d6-9686-91c183e78094; dirty; pass; tdd _(id: [rec-f2398b8d-43c8-4dc8-a030-e80949839060](.artifacts/records/project__check-run/rec-f2398b8d-43c8-4dc8-a030-e80949839060.md))_

## phase-selector-ui-finished

### Acceptance
- **phase-selector-ui-finished**: R11; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'finished or toggle' _(id: [rec-551d6d24-2144-40d6-9686-91c183e78094](.artifacts/records/project__acceptance/rec-551d6d24-2144-40d6-9686-91c183e78094.md))_

## phase-selector-ui-help

### Acceptance
- **phase-selector-ui-help**: R12; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'help or question' _(id: [rec-bc7d46e2-0d5a-4792-882a-c2afecb5d2aa](.artifacts/records/project__acceptance/rec-bc7d46e2-0d5a-4792-882a-c2afecb5d2aa.md))_

## phase-selector-ui-nav

### Acceptance
- **phase-selector-ui-nav**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'picker or navigate or step' _(id: [rec-42fa4dd1-20c6-46e2-9809-1554757d18aa](.artifacts/records/project__acceptance/rec-42fa4dd1-20c6-46e2-9809-1554757d18aa.md))_

## phase-selector-ui-phase

### Acceptance
- **phase-selector-ui-phase**: R8; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'phase_detail or open_phase' _(id: [rec-eb4361b5-7a63-4383-980b-e9c14c7ea07a](.artifacts/records/project__acceptance/rec-eb4361b5-7a63-4383-980b-e9c14c7ea07a.md))_

## phase-selector-ui-scope

### Acceptance
- **phase-selector-ui-scope**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'needs or activity' _(id: [rec-c0a861da-d41b-4855-b6f9-44219c1f8343](.artifacts/records/project__acceptance/rec-c0a861da-d41b-4855-b6f9-44219c1f8343.md))_

## phase-selector-ui-wave

### Acceptance
- **phase-selector-ui-wave**: R9; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'wave_strip or wave' _(id: [rec-1c86657d-12b9-4d8f-a50b-0f751e9410ad](.artifacts/records/project__acceptance/rec-1c86657d-12b9-4d8f-a50b-0f751e9410ad.md))_

## phase-table-scope

### Acceptance
- **phase-table-scope**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_tasks.py -q -k 'scope or selected or all_phases' _(id: [rec-a6cc79a2-1384-4e47-92ba-975717a38e99](.artifacts/records/project__acceptance/rec-a6cc79a2-1384-4e47-92ba-975717a38e99.md))_

### Check
- **phase-table-scope**: rec-36bb77d4-81a1-4fcd-b04a-e0b22bf49f14; dirty; pass; tdd _(id: [rec-04c64e66-0d38-4b90-a7d5-df898eaa5c5f](.artifacts/records/project__check-run/rec-04c64e66-0d38-4b90-a7d5-df898eaa5c5f.md))_
- **phase-table-scope**: rec-a6cc79a2-1384-4e47-92ba-975717a38e99; dirty; pass; tdd _(id: [rec-846ca2ef-d789-4ccb-aad7-a5fafe8f821b](.artifacts/records/project__check-run/rec-846ca2ef-d789-4ccb-aad7-a5fafe8f821b.md))_

## phase-table-scope-sections

### Acceptance
- **phase-table-scope-sections**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_tasks.py -q -k 'section' _(id: [rec-36bb77d4-81a1-4fcd-b04a-e0b22bf49f14](.artifacts/records/project__acceptance/rec-36bb77d4-81a1-4fcd-b04a-e0b22bf49f14.md))_

## plan-landing-rules

### Acceptance
- **plan-landing-rules**: tdd; workflow-loop; python3 -m pytest tests/test_plan_landing.py -q _(id: [rec-9f4b54cc-334e-4b5c-92fa-df0b713d662e](.artifacts/records/project__acceptance/rec-9f4b54cc-334e-4b5c-92fa-df0b713d662e.md))_

### Check
- **plan-landing-rules**: rec-9f4b54cc-334e-4b5c-92fa-df0b713d662e; dirty; pass; tdd _(id: [rec-6388f2a2-d1b0-4ff8-bdd6-202699546b5e](.artifacts/records/project__check-run/rec-6388f2a2-d1b0-4ff8-bdd6-202699546b5e.md))_

## plan-wave-rules

### Acceptance
- **plan-wave-rules**: tdd; workflow-loop; python3 -m pytest tests/test_plan_wave_rules.py -q _(id: [rec-b1c39c5f-6758-426d-bdcf-0ff6c57bcbc5](.artifacts/records/project__acceptance/rec-b1c39c5f-6758-426d-bdcf-0ff6c57bcbc5.md))_

### Check
- **plan-wave-rules**: rec-b1c39c5f-6758-426d-bdcf-0ff6c57bcbc5; dirty; pass; tdd _(id: [rec-89b14150-1845-47bc-aff7-14a220d85c8d](.artifacts/records/project__check-run/rec-89b14150-1845-47bc-aff7-14a220d85c8d.md))_

## plugin-root-and-cli-review

### Check
- **plugin-root-and-cli-review**: plugin-root-and-cli-review; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; review _(id: [rec-3c873e15-1bea-4d72-a177-9f32a90677b6](.artifacts/records/project__check-run/rec-3c873e15-1bea-4d72-a177-9f32a90677b6.md))_
- **plugin-root-and-cli-review**: plugin-root-and-cli-review; 3379fcf8a1d882d91330bec6e66a2889c71d3ece; pass; review _(id: [rec-3d55b74a-4806-47bc-8350-6063559d96a2](.artifacts/records/project__check-run/rec-3d55b74a-4806-47bc-8350-6063559d96a2.md))_
- **plugin-root-and-cli-review**: plugin-root-and-cli-review; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; review _(id: [rec-7051e337-86c9-4da4-b95b-b54d42acc8d3](.artifacts/records/project__check-run/rec-7051e337-86c9-4da4-b95b-b54d42acc8d3.md))_

## plugin-root-and-cli-tier2

### Check
- **plugin-root-and-cli-tier2**: plugin-root-and-cli-tier2; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; fail; check _(id: [rec-03c48fcc-54d8-468e-a2bd-31ecdfcd48b8](.artifacts/records/project__check-run/rec-03c48fcc-54d8-468e-a2bd-31ecdfcd48b8.md))_
- **plugin-root-and-cli-tier2**: plugin-root-and-cli-tier2; 8109e9aae50c888bd17a06bfb3b8f9e2f55665ab; fail; check _(id: [rec-04c9b0b0-d9f6-46a2-ad1e-8c1ad0db624e](.artifacts/records/project__check-run/rec-04c9b0b0-d9f6-46a2-ad1e-8c1ad0db624e.md))_
- **plugin-root-and-cli-tier2**: plugin-root-and-cli-tier2; 3379fcf8a1d882d91330bec6e66a2889c71d3ece; pass; manual; user _(id: [rec-af24fcc0-9a26-4be6-9737-fa78976f6316](.artifacts/records/project__check-run/rec-af24fcc0-9a26-4be6-9737-fa78976f6316.md))_
- **plugin-root-and-cli-tier2**: plugin-root-and-cli-tier2; 3379fcf8a1d882d91330bec6e66a2889c71d3ece; fail; check _(id: [rec-cc94529d-5679-4111-8618-30f3392e2f08](.artifacts/records/project__check-run/rec-cc94529d-5679-4111-8618-30f3392e2f08.md))_

## portable-skill-refs

### Acceptance
- **portable-skill-refs**: R1; check; packaging; python3 -m pytest tests/test_skill_portability.py -q _(id: [rec-928c5ad9-2a76-42cc-8403-9947807d381f](.artifacts/records/project__acceptance/rec-928c5ad9-2a76-42cc-8403-9947807d381f.md))_

### Check
- **portable-skill-refs**: rec-928c5ad9-2a76-42cc-8403-9947807d381f; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-51018393-702d-4be4-838e-ac6dec425d17](.artifacts/records/project__check-run/rec-51018393-702d-4be4-838e-ac6dec425d17.md))_
- **portable-skill-refs**: rec-928c5ad9-2a76-42cc-8403-9947807d381f; b4fc77a1a125f0526d9941a374d0c633886a6b96; pass; check _(id: [rec-df6debec-dccf-47d1-8778-5ecd7fc0c0e4](.artifacts/records/project__check-run/rec-df6debec-dccf-47d1-8778-5ecd7fc0c0e4.md))_
- **portable-skill-refs**: rec-928c5ad9-2a76-42cc-8403-9947807d381f; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-fd97844e-6172-42d0-9b4c-96c80eb9494d](.artifacts/records/project__check-run/rec-fd97844e-6172-42d0-9b4c-96c80eb9494d.md))_

## portable-skill-refs-drift

### Acceptance
- **portable-skill-refs-drift**: R3; check; packaging; python3 scripts/build_skills.py --check && python3 -m pytest tests/test_skill_portability.py -q -k drift _(id: [rec-415c1cc3-204c-4f52-9aca-5482488ef019](.artifacts/records/project__acceptance/rec-415c1cc3-204c-4f52-9aca-5482488ef019.md))_

### Check
- **portable-skill-refs-drift**: rec-415c1cc3-204c-4f52-9aca-5482488ef019; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-285545d7-c2df-4ada-9ae4-63744a75c7bd](.artifacts/records/project__check-run/rec-285545d7-c2df-4ada-9ae4-63744a75c7bd.md))_
- **portable-skill-refs-drift**: rec-415c1cc3-204c-4f52-9aca-5482488ef019; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-37cd7885-5dec-4485-8b61-aa07facfe88e](.artifacts/records/project__check-run/rec-37cd7885-5dec-4485-8b61-aa07facfe88e.md))_
- **portable-skill-refs-drift**: rec-415c1cc3-204c-4f52-9aca-5482488ef019; b4fc77a1a125f0526d9941a374d0c633886a6b96; pass; check _(id: [rec-546b9ac1-906f-47b0-81de-d8d728147ab9](.artifacts/records/project__check-run/rec-546b9ac1-906f-47b0-81de-d8d728147ab9.md))_

## portable-skill-refs-frontmatter

### Acceptance
- **portable-skill-refs-frontmatter**: R4; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k frontmatter _(id: [rec-3c605b52-67e1-444f-8b8a-4361446b4ba7](.artifacts/records/project__acceptance/rec-3c605b52-67e1-444f-8b8a-4361446b4ba7.md))_

### Check
- **portable-skill-refs-frontmatter**: rec-3c605b52-67e1-444f-8b8a-4361446b4ba7; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-85dd428f-c59e-45ba-bad5-b5b248dd5976](.artifacts/records/project__check-run/rec-85dd428f-c59e-45ba-bad5-b5b248dd5976.md))_
- **portable-skill-refs-frontmatter**: rec-3c605b52-67e1-444f-8b8a-4361446b4ba7; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-dfea145a-07e4-4553-97bd-66033cd3dbf6](.artifacts/records/project__check-run/rec-dfea145a-07e4-4553-97bd-66033cd3dbf6.md))_
- **portable-skill-refs-frontmatter**: rec-3c605b52-67e1-444f-8b8a-4361446b4ba7; b4fc77a1a125f0526d9941a374d0c633886a6b96; pass; check _(id: [rec-fef906b4-ef2e-4a5e-abe2-09a6b01ea6d5](.artifacts/records/project__check-run/rec-fef906b4-ef2e-4a5e-abe2-09a6b01ea6d5.md))_

## portable-skill-refs-generated

### Acceptance
- **portable-skill-refs-generated**: R2; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k generated _(id: [rec-e3a55126-ff30-4309-aa76-7a41043af0c5](.artifacts/records/project__acceptance/rec-e3a55126-ff30-4309-aa76-7a41043af0c5.md))_

### Check
- **portable-skill-refs-generated**: rec-e3a55126-ff30-4309-aa76-7a41043af0c5; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-a62943af-b14b-4a95-be5c-c2d74a451618](.artifacts/records/project__check-run/rec-a62943af-b14b-4a95-be5c-c2d74a451618.md))_
- **portable-skill-refs-generated**: rec-e3a55126-ff30-4309-aa76-7a41043af0c5; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-f3d8b69e-01fb-43b2-ac00-a6058390af47](.artifacts/records/project__check-run/rec-f3d8b69e-01fb-43b2-ac00-a6058390af47.md))_
- **portable-skill-refs-generated**: rec-e3a55126-ff30-4309-aa76-7a41043af0c5; b4fc77a1a125f0526d9941a374d0c633886a6b96; pass; check _(id: [rec-fd6f5ed9-2268-4466-b31d-e277eefe66ce](.artifacts/records/project__check-run/rec-fd6f5ed9-2268-4466-b31d-e277eefe66ce.md))_

## portable-skill-refs-paths

### Acceptance
- **portable-skill-refs-paths**: R6; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k paths _(id: [rec-26a7bcc5-61dc-4f46-ba57-7e01c963e3a7](.artifacts/records/project__acceptance/rec-26a7bcc5-61dc-4f46-ba57-7e01c963e3a7.md))_

### Check
- **portable-skill-refs-paths**: rec-26a7bcc5-61dc-4f46-ba57-7e01c963e3a7; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-0da3778f-4e5b-4468-8fd3-d654c599bbd1](.artifacts/records/project__check-run/rec-0da3778f-4e5b-4468-8fd3-d654c599bbd1.md))_
- **portable-skill-refs-paths**: rec-26a7bcc5-61dc-4f46-ba57-7e01c963e3a7; b4fc77a1a125f0526d9941a374d0c633886a6b96; pass; check _(id: [rec-357e0a00-9369-455c-a9fc-809ebb9e2e9a](.artifacts/records/project__check-run/rec-357e0a00-9369-455c-a9fc-809ebb9e2e9a.md))_
- **portable-skill-refs-paths**: rec-26a7bcc5-61dc-4f46-ba57-7e01c963e3a7; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-a88be341-41cc-498d-a2b8-58f0d9f422e2](.artifacts/records/project__check-run/rec-a88be341-41cc-498d-a2b8-58f0d9f422e2.md))_

## project-ops

### Acceptance
- **project-ops**: R15; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_project_ops.py::test_r15_get -q _(id: [rec-c142bb5d-e29f-464a-9fa7-d4d6ad4c89cc](.artifacts/records/project__acceptance/rec-c142bb5d-e29f-464a-9fa7-d4d6ad4c89cc.md))_

### Check
- **project-ops**: rec-c142bb5d-e29f-464a-9fa7-d4d6ad4c89cc; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-573e5e9d-ef7a-4ff2-9a52-11e22175c183](.artifacts/records/project__check-run/rec-573e5e9d-ef7a-4ff2-9a52-11e22175c183.md))_
- **project-ops**: rec-c142bb5d-e29f-464a-9fa7-d4d6ad4c89cc; dirty; fail; tdd _(id: [rec-5bc7c5b6-40c0-4774-b2ec-3371758a5b7d](.artifacts/records/project__check-run/rec-5bc7c5b6-40c0-4774-b2ec-3371758a5b7d.md))_
- **project-ops**: rec-c142bb5d-e29f-464a-9fa7-d4d6ad4c89cc; cc1cea322185b1faa60eaadfae14394d00e4c29d; pass; tdd _(id: [rec-99557937-7537-4b9a-a3e9-4ce343f73d26](.artifacts/records/project__check-run/rec-99557937-7537-4b9a-a3e9-4ce343f73d26.md))_

## project-ops-apply

### Acceptance
- **project-ops-apply**: R19; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_project_ops.py::test_r19_apply -q _(id: [rec-4002e494-85dd-433f-913e-5ee2cd5b8636](.artifacts/records/project__acceptance/rec-4002e494-85dd-433f-913e-5ee2cd5b8636.md))_

### Check
- **project-ops-apply**: rec-4002e494-85dd-433f-913e-5ee2cd5b8636; cc1cea322185b1faa60eaadfae14394d00e4c29d; pass; tdd _(id: [rec-66e6463a-8e21-4d51-b4a8-92f26c80dca0](.artifacts/records/project__check-run/rec-66e6463a-8e21-4d51-b4a8-92f26c80dca0.md))_
- **project-ops-apply**: rec-4002e494-85dd-433f-913e-5ee2cd5b8636; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-6c65e641-feda-4319-b583-3236563a6bf7](.artifacts/records/project__check-run/rec-6c65e641-feda-4319-b583-3236563a6bf7.md))_
- **project-ops-apply**: rec-4002e494-85dd-433f-913e-5ee2cd5b8636; dirty; fail; tdd _(id: [rec-d2551ad1-1429-4236-b2c1-5798dfa2e425](.artifacts/records/project__check-run/rec-d2551ad1-1429-4236-b2c1-5798dfa2e425.md))_

## project-ops-create

### Acceptance
- **project-ops-create**: R18; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_project_ops.py::test_r18_create -q _(id: [rec-af1deece-a7c4-410c-884c-7ba4ae9aa0c7](.artifacts/records/project__acceptance/rec-af1deece-a7c4-410c-884c-7ba4ae9aa0c7.md))_

### Check
- **project-ops-create**: rec-af1deece-a7c4-410c-884c-7ba4ae9aa0c7; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-2db55cae-7f31-494e-84ab-cdb7f21e1b15](.artifacts/records/project__check-run/rec-2db55cae-7f31-494e-84ab-cdb7f21e1b15.md))_
- **project-ops-create**: rec-af1deece-a7c4-410c-884c-7ba4ae9aa0c7; cc1cea322185b1faa60eaadfae14394d00e4c29d; pass; tdd _(id: [rec-9b8779ad-b1d1-4aa2-8b97-547bdd0fd5d3](.artifacts/records/project__check-run/rec-9b8779ad-b1d1-4aa2-8b97-547bdd0fd5d3.md))_
- **project-ops-create**: rec-af1deece-a7c4-410c-884c-7ba4ae9aa0c7; dirty; fail; tdd _(id: [rec-d1cdc114-9bf1-4dae-a4c0-c826ea135af2](.artifacts/records/project__check-run/rec-d1cdc114-9bf1-4dae-a4c0-c826ea135af2.md))_

## project-ops-list

### Acceptance
- **project-ops-list**: R17; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_project_ops.py::test_r17_list -q _(id: [rec-97d8ae4d-48e8-4fc6-81c4-f163ca7189ec](.artifacts/records/project__acceptance/rec-97d8ae4d-48e8-4fc6-81c4-f163ca7189ec.md))_

### Check
- **project-ops-list**: rec-97d8ae4d-48e8-4fc6-81c4-f163ca7189ec; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-07c066fe-b3de-488b-975e-cf0133abbd82](.artifacts/records/project__check-run/rec-07c066fe-b3de-488b-975e-cf0133abbd82.md))_
- **project-ops-list**: rec-97d8ae4d-48e8-4fc6-81c4-f163ca7189ec; cc1cea322185b1faa60eaadfae14394d00e4c29d; pass; tdd _(id: [rec-2df2cd70-6605-469a-97b6-70a35fe97316](.artifacts/records/project__check-run/rec-2df2cd70-6605-469a-97b6-70a35fe97316.md))_
- **project-ops-list**: rec-97d8ae4d-48e8-4fc6-81c4-f163ca7189ec; dirty; fail; tdd _(id: [rec-b5e56118-3cd3-4cb7-8a11-a28f033262c5](.artifacts/records/project__check-run/rec-b5e56118-3cd3-4cb7-8a11-a28f033262c5.md))_

## project-ops-missing

### Acceptance
- **project-ops-missing**: R16; tdd; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_project_ops.py::test_r16_get_missing -q _(id: [rec-5f4505cf-d588-401b-a1e7-0266390e1d70](.artifacts/records/project__acceptance/rec-5f4505cf-d588-401b-a1e7-0266390e1d70.md))_

### Check
- **project-ops-missing**: rec-5f4505cf-d588-401b-a1e7-0266390e1d70; dirty; fail; tdd _(id: [rec-45cefd56-de6b-491d-92d1-c39df933ae2e](.artifacts/records/project__check-run/rec-45cefd56-de6b-491d-92d1-c39df933ae2e.md))_
- **project-ops-missing**: rec-5f4505cf-d588-401b-a1e7-0266390e1d70; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; tdd _(id: [rec-678d066e-8a1a-4edb-af5c-00fd64b8e7db](.artifacts/records/project__check-run/rec-678d066e-8a1a-4edb-af5c-00fd64b8e7db.md))_
- **project-ops-missing**: rec-5f4505cf-d588-401b-a1e7-0266390e1d70; cc1cea322185b1faa60eaadfae14394d00e4c29d; pass; tdd _(id: [rec-e941eeae-956a-4d16-9aad-5c7c8f446b07](.artifacts/records/project__check-run/rec-e941eeae-956a-4d16-9aad-5c7c8f446b07.md))_

## proof-dashboard-ui

### Acceptance
- **proof-dashboard-ui**: R7; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_proof_dashboard.py -q _(id: [rec-cfd617ac-aa2f-42a8-9d87-4d37c0bb0cf8](.artifacts/records/project__acceptance/rec-cfd617ac-aa2f-42a8-9d87-4d37c0bb0cf8.md))_

### Check
- **proof-dashboard-ui**: rec-cfd617ac-aa2f-42a8-9d87-4d37c0bb0cf8; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-3233eb16-fd99-4f4d-91f1-ac140e1ca906](.artifacts/records/project__check-run/rec-3233eb16-fd99-4f4d-91f1-ac140e1ca906.md))_

## proof-packet-contract

### Acceptance
- **proof-packet-contract**: R1; check; workflow-loop; python3 -m pytest tests/test_proof_packet_contract.py::test_proof_packet_type_and_sections -q _(id: [rec-c0e494f2-6c30-4453-8e61-78a3d2dee8df](.artifacts/records/project__acceptance/rec-c0e494f2-6c30-4453-8e61-78a3d2dee8df.md))_

### Check
- **proof-packet-contract**: rec-c0e494f2-6c30-4453-8e61-78a3d2dee8df; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-95aebc70-6615-4bff-9799-eb478de6e681](.artifacts/records/project__check-run/rec-95aebc70-6615-4bff-9799-eb478de6e681.md))_

## proof-packet-contract-handoff

### Acceptance
- **proof-packet-contract-handoff**: R2; check; workflow-loop; python3 -m pytest tests/test_proof_packet_contract.py::test_handoff_latest_proof_role -q _(id: [rec-5805f781-09e8-420f-b329-e5f8cf095e1e](.artifacts/records/project__acceptance/rec-5805f781-09e8-420f-b329-e5f8cf095e1e.md))_

### Check
- **proof-packet-contract-handoff**: rec-5805f781-09e8-420f-b329-e5f8cf095e1e; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-4b797ec0-c988-4860-a5fe-846882e05880](.artifacts/records/project__check-run/rec-4b797ec0-c988-4860-a5fe-846882e05880.md))_

## proof-skills-execute

### Acceptance
- **proof-skills-execute**: R4; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_assembles_proof_packet -q _(id: [rec-54e6aa7d-586f-48a3-851d-afdbffe6d4ec](.artifacts/records/project__acceptance/rec-54e6aa7d-586f-48a3-851d-afdbffe6d4ec.md))_

### Check
- **proof-skills-execute**: rec-54e6aa7d-586f-48a3-851d-afdbffe6d4ec; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-e09fd23b-f572-418d-8ef9-eb7ea58ca05f](.artifacts/records/project__check-run/rec-e09fd23b-f572-418d-8ef9-eb7ea58ca05f.md))_

## proof-skills-execute-aff

### Acceptance
- **proof-skills-execute-aff**: R5; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_aff_hooks_and_incidental -q _(id: [rec-3e1bd988-4027-4da3-9631-38e7fa019995](.artifacts/records/project__acceptance/rec-3e1bd988-4027-4da3-9631-38e7fa019995.md))_

### Check
- **proof-skills-execute-aff**: rec-3e1bd988-4027-4da3-9631-38e7fa019995; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-5a81aeeb-3697-4ceb-b353-ff245022f572](.artifacts/records/project__check-run/rec-5a81aeeb-3697-4ceb-b353-ff245022f572.md))_

## proof-skills-execute-incidental

### Acceptance
- **proof-skills-execute-incidental**: R6; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_aff_hooks_and_incidental -q _(id: [rec-9184b85e-a6e2-44d6-b2de-222c16b71cc0](.artifacts/records/project__acceptance/rec-9184b85e-a6e2-44d6-b2de-222c16b71cc0.md))_

### Check
- **proof-skills-execute-incidental**: rec-9184b85e-a6e2-44d6-b2de-222c16b71cc0; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-824e7313-104d-4204-9166-fa21a394df0a](.artifacts/records/project__check-run/rec-824e7313-104d-4204-9166-fa21a394df0a.md))_

## proof-skills-settle-plan

### Acceptance
- **proof-skills-settle-plan**: R3; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_settle_and_plan_require_proof_section -q _(id: [rec-dd5f9851-b6af-4f8d-8123-158e5aa3be86](.artifacts/records/project__acceptance/rec-dd5f9851-b6af-4f8d-8123-158e5aa3be86.md))_

### Check
- **proof-skills-settle-plan**: rec-dd5f9851-b6af-4f8d-8123-158e5aa3be86; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-24678aa2-2bf7-4d53-a74f-35d95853d63f](.artifacts/records/project__check-run/rec-24678aa2-2bf7-4d53-a74f-35d95853d63f.md))_

## pyproject-pypi-review

### Check
- **pyproject-pypi-review**: pyproject-pypi-review; 5257818a25994a1b41742f10c48d12cb7e5d767c; pass; review _(id: [rec-78fcd18d-7b0e-4ade-acaa-1ced833efb54](.artifacts/records/project__check-run/rec-78fcd18d-7b0e-4ade-acaa-1ced833efb54.md))_

## readme-lifecycle

### Acceptance
- **readme-lifecycle**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_readme_lifecycle.py -q _(id: [rec-61e95277-ed36-4e3f-9307-df5f8e946151](.artifacts/records/project__acceptance/rec-61e95277-ed36-4e3f-9307-df5f8e946151.md))_

### Check
- **readme-lifecycle**: rec-61e95277-ed36-4e3f-9307-df5f8e946151; dirty; pass; check _(id: [rec-522c9649-86e2-408e-b3e4-3effae133ab9](.artifacts/records/project__check-run/rec-522c9649-86e2-408e-b3e4-3effae133ab9.md))_

## readme-quickstart

### Acceptance
- **readme-quickstart**: check; dashboard; grep -q '^## Quick start' README.md && grep -q "@plugin 'andrewy1n/se-workflow'" README.md && grep -q 'run-shell' README.md && ! grep -nE 'dashboard/tmux\.conf|SE_WORKFLOW_DASHBOARD|source-file' README.md _(id: [rec-757d4417-3c33-4df0-a29e-03c1c09bb8ad](.artifacts/records/project__acceptance/rec-757d4417-3c33-4df0-a29e-03c1c09bb8ad.md))_

### Check
- **readme-quickstart**: rec-757d4417-3c33-4df0-a29e-03c1c09bb8ad; dirty; pass; check _(id: [rec-af317ad2-59e8-4779-8b24-0e1b736e93da](.artifacts/records/project__check-run/rec-af317ad2-59e8-4779-8b24-0e1b736e93da.md))_

## recency-selection

### Acceptance
- **recency-selection**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q _(id: [rec-d854ca7d-767b-4729-92e1-18ef8853d92c](.artifacts/records/project__acceptance/rec-d854ca7d-767b-4729-92e1-18ef8853d92c.md))_

### Check
- **recency-selection**: rec-d854ca7d-767b-4729-92e1-18ef8853d92c; 6de1ff4; pass; tdd _(id: [rec-a9d8a1d2-3bb1-478b-9164-bad3436d3a9a](.artifacts/records/project__check-run/rec-a9d8a1d2-3bb1-478b-9164-bad3436d3a9a.md))_

### Observation
- **recency-selection**: View state digests hash store contents only; a recorded_at within-window role changes membership with time alone, so a digest-driven watch will not redraw when a done item ages out; watch-dashboard _(id: [rec-5b58d86c-922d-4747-8533-4f3b685d1c0d](.artifacts/records/project__investigation-observation/rec-5b58d86c-922d-4747-8533-4f3b685d1c0d.md))_

## rename-agent-affidavit-review

### Check
- **rename-agent-affidavit-review**: rename-agent-affidavit-review; ff37be68a378225c1b065efdeef9e4f611898e19; pass; review _(id: [rec-4b72cd48-8ce9-4b27-926d-7bb12e738e8a](.artifacts/records/project__check-run/rec-4b72cd48-8ce9-4b27-926d-7bb12e738e8a.md))_

## rename-agent-affidavit-tier2

### Check
- **rename-agent-affidavit-tier2**: rename-agent-affidavit-tier2; 3c8a5c2b46205e537b4b68926bc3f475d34b527f; pass; check _(id: [rec-0ea8ba6e-4ca8-424b-9f8a-0d4a2b617f56](.artifacts/records/project__check-run/rec-0ea8ba6e-4ca8-424b-9f8a-0d4a2b617f56.md))_

## rename-identity-surfaces

### Acceptance
- **rename-identity-surfaces**: R1; check; packaging; python3 scripts/check_affidavit_plugin_names.py _(id: [rec-57328b34-853e-4ba0-978d-19d5dc67a396](.artifacts/records/project__acceptance/rec-57328b34-853e-4ba0-978d-19d5dc67a396.md))_

### Check
- **rename-identity-surfaces**: rec-57328b34-853e-4ba0-978d-19d5dc67a396; 8c627a74e0bd084d4ebd103a6657af05bcf9d0e3; pass; check _(id: [rec-38b3fee1-194b-430e-94da-0d2c618a2c17](.artifacts/records/project__check-run/rec-38b3fee1-194b-430e-94da-0d2c618a2c17.md))_
- **rename-identity-surfaces**: rec-57328b34-853e-4ba0-978d-19d5dc67a396; 063e9925e6004a9432860c669ee84062986dbaa4; fail; check _(id: [rec-68ffe66c-bf9c-4e2d-b590-b529415d18e0](.artifacts/records/project__check-run/rec-68ffe66c-bf9c-4e2d-b590-b529415d18e0.md))_

## rename-identity-surfaces-contract

### Acceptance
- **rename-identity-surfaces-contract**: R3; check; packaging; python3 scripts/check_affidavit_contract_project.py && grep -q affidavit skills/ensure-store.md && ! grep -E 'other than .se-workflow|project. is .se-workflow' skills/ensure-store.md _(id: [rec-037fac04-00c1-4097-9c17-5d49622584df](.artifacts/records/project__acceptance/rec-037fac04-00c1-4097-9c17-5d49622584df.md))_

### Check
- **rename-identity-surfaces-contract**: rec-037fac04-00c1-4097-9c17-5d49622584df; 063e9925e6004a9432860c669ee84062986dbaa4; fail; check _(id: [rec-3516f920-52f9-42bb-b5c6-32fadbfcfc99](.artifacts/records/project__check-run/rec-3516f920-52f9-42bb-b5c6-32fadbfcfc99.md))_
- **rename-identity-surfaces-contract**: rec-037fac04-00c1-4097-9c17-5d49622584df; 8c627a74e0bd084d4ebd103a6657af05bcf9d0e3; pass; check _(id: [rec-76c7330a-fe10-46e7-bb1d-7f1ac19524cd](.artifacts/records/project__check-run/rec-76c7330a-fe10-46e7-bb1d-7f1ac19524cd.md))_

## rename-package-cli

### Acceptance
- **rename-package-cli**: R2; tdd; packaging; test -x bin/aff && ! test -e bin/se-workflow && bin/aff check --help >/dev/null && bin/aff close-batch --help >/dev/null && uv run --with pytest python -m pytest tests/test_aa_resolve.py tests/test_close_batch.py -q --collect-only >/dev/null && python3 -c "import importlib.util as u; import affidavit, affidavit.cli; assert u.find_spec('affidavit'); assert u.find_spec('se_workflow') is None" _(id: [rec-fa93899c-8721-4377-99f1-a99a14cbf1a2](.artifacts/records/project__acceptance/rec-fa93899c-8721-4377-99f1-a99a14cbf1a2.md))_

### Check
- **rename-package-cli**: rec-fa93899c-8721-4377-99f1-a99a14cbf1a2; e7604b05f15bedb13b9392681a2e950d415ebb4e; fail; tdd _(id: [rec-02c3f250-9fc5-4bb4-bac0-fb0d7e40e1d0](.artifacts/records/project__check-run/rec-02c3f250-9fc5-4bb4-bac0-fb0d7e40e1d0.md))_
- **rename-package-cli**: rec-fa93899c-8721-4377-99f1-a99a14cbf1a2; dirty; fail; tdd _(id: [rec-56ab10c0-fe2e-41f1-afe9-7e23d3a31d51](.artifacts/records/project__check-run/rec-56ab10c0-fe2e-41f1-afe9-7e23d3a31d51.md))_
- **rename-package-cli**: rec-fa93899c-8721-4377-99f1-a99a14cbf1a2; e7604b05f15bedb13b9392681a2e950d415ebb4e; pass; tdd _(id: [rec-5d1264d7-2fad-4bf4-b36f-41caddfe0211](.artifacts/records/project__check-run/rec-5d1264d7-2fad-4bf4-b36f-41caddfe0211.md))_
- **rename-package-cli**: rec-fa93899c-8721-4377-99f1-a99a14cbf1a2; e7604b05f15bedb13b9392681a2e950d415ebb4e; pass; tdd _(id: [rec-952b2548-e136-48f9-8eae-27ae0543945f](.artifacts/records/project__check-run/rec-952b2548-e136-48f9-8eae-27ae0543945f.md))_
- **rename-package-cli**: rec-fa93899c-8721-4377-99f1-a99a14cbf1a2; b25294a293fa584e95618865ade2ba4fab3e5ef9; fail; tdd _(id: [rec-a4362c08-8555-4a4f-a5a9-6b42d7695eac](.artifacts/records/project__check-run/rec-a4362c08-8555-4a4f-a5a9-6b42d7695eac.md))_

## rename-tests

### Acceptance
- **rename-tests**: R5; tdd; packaging; uv run --with pytest python -m pytest tests/test_aa_resolve.py tests/test_close_batch.py tests/test_skill_contract_consistency.py -q && grep -q affidavit scripts/sync-plugin.sh && ! grep -E 'se-workflow|se_workflow' scripts/sync-plugin.sh _(id: [rec-322f6c86-d91a-4ab6-95bb-82a9bbcd348f](.artifacts/records/project__acceptance/rec-322f6c86-d91a-4ab6-95bb-82a9bbcd348f.md))_

### Check
- **rename-tests**: rec-322f6c86-d91a-4ab6-95bb-82a9bbcd348f; ff37be68a378225c1b065efdeef9e4f611898e19; pass; tdd _(id: [rec-01a7d00a-b0ca-4610-8d73-d72713dc46f9](.artifacts/records/project__check-run/rec-01a7d00a-b0ca-4610-8d73-d72713dc46f9.md))_
- **rename-tests**: rec-322f6c86-d91a-4ab6-95bb-82a9bbcd348f; dirty; fail; tdd _(id: [rec-c915d276-1da0-45e5-9a16-5720f2fc4aa8](.artifacts/records/project__check-run/rec-c915d276-1da0-45e5-9a16-5720f2fc4aa8.md))_

## replace-resolvers

### Acceptance
- **replace-resolvers**: R1; tdd; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r1 -q _(id: [rec-89843013-38fa-4ad0-af4f-aceb43c5232e](.artifacts/records/project__acceptance/rec-89843013-38fa-4ad0-af4f-aceb43c5232e.md))_

### Check
- **replace-resolvers**: rec-89843013-38fa-4ad0-af4f-aceb43c5232e; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-053a5ad2-10b9-4681-9ddf-9dad3d474409](.artifacts/records/project__check-run/rec-053a5ad2-10b9-4681-9ddf-9dad3d474409.md))_
- **replace-resolvers**: rec-89843013-38fa-4ad0-af4f-aceb43c5232e; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; tdd _(id: [rec-4100c960-929d-40c1-b98f-fcc5e942704c](.artifacts/records/project__check-run/rec-4100c960-929d-40c1-b98f-fcc5e942704c.md))_
- **replace-resolvers**: rec-89843013-38fa-4ad0-af4f-aceb43c5232e; cdcb9861c1b7f82caf097b00472d16f902d8d5b9; fail; tdd _(id: [rec-4d88d3dc-ba3f-440d-8f77-3f579eaeef9b](.artifacts/records/project__check-run/rec-4d88d3dc-ba3f-440d-8f77-3f579eaeef9b.md))_
- **replace-resolvers**: rec-89843013-38fa-4ad0-af4f-aceb43c5232e; 0433a8abf93db41b1b243d9fd412b43b70ea3407; pass; tdd _(id: [rec-a0838046-193e-4f25-acdc-df42a293bade](.artifacts/records/project__check-run/rec-a0838046-193e-4f25-acdc-df42a293bade.md))_

## replace-resolvers-aa

### Acceptance
- **replace-resolvers-aa**: R3; tdd; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r3 -q _(id: [rec-2dfbc2f6-8e1a-430b-87d3-6e6b44627ca7](.artifacts/records/project__acceptance/rec-2dfbc2f6-8e1a-430b-87d3-6e6b44627ca7.md))_

### Check
- **replace-resolvers-aa**: rec-2dfbc2f6-8e1a-430b-87d3-6e6b44627ca7; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; tdd _(id: [rec-7c895230-5bc3-4ed1-89ce-2f8cea1db1b4](.artifacts/records/project__check-run/rec-7c895230-5bc3-4ed1-89ce-2f8cea1db1b4.md))_
- **replace-resolvers-aa**: rec-2dfbc2f6-8e1a-430b-87d3-6e6b44627ca7; cdcb9861c1b7f82caf097b00472d16f902d8d5b9; fail; tdd _(id: [rec-b0f44f6a-faf2-44cd-bf7a-692d27cbd496](.artifacts/records/project__check-run/rec-b0f44f6a-faf2-44cd-bf7a-692d27cbd496.md))_
- **replace-resolvers-aa**: rec-2dfbc2f6-8e1a-430b-87d3-6e6b44627ca7; 0433a8abf93db41b1b243d9fd412b43b70ea3407; pass; tdd _(id: [rec-ded0838e-77ac-40bb-b8ba-474309889320](.artifacts/records/project__check-run/rec-ded0838e-77ac-40bb-b8ba-474309889320.md))_
- **replace-resolvers-aa**: rec-2dfbc2f6-8e1a-430b-87d3-6e6b44627ca7; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-fe4438f2-3f76-4e1d-919a-6042766e17fe](.artifacts/records/project__check-run/rec-fe4438f2-3f76-4e1d-919a-6042766e17fe.md))_

## replace-resolvers-dashboard

### Acceptance
- **replace-resolvers-dashboard**: R2; tdd; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r2 -q _(id: [rec-3b225e8d-812f-4975-8b1f-06a0fa127aec](.artifacts/records/project__acceptance/rec-3b225e8d-812f-4975-8b1f-06a0fa127aec.md))_

### Check
- **replace-resolvers-dashboard**: rec-3b225e8d-812f-4975-8b1f-06a0fa127aec; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-36cb4991-2b58-4d4a-8c3e-529914bdb8b0](.artifacts/records/project__check-run/rec-36cb4991-2b58-4d4a-8c3e-529914bdb8b0.md))_
- **replace-resolvers-dashboard**: rec-3b225e8d-812f-4975-8b1f-06a0fa127aec; cdcb9861c1b7f82caf097b00472d16f902d8d5b9; fail; tdd _(id: [rec-3a2c4868-dc9d-47a4-897a-bbe69d3d9658](.artifacts/records/project__check-run/rec-3a2c4868-dc9d-47a4-897a-bbe69d3d9658.md))_
- **replace-resolvers-dashboard**: rec-3b225e8d-812f-4975-8b1f-06a0fa127aec; 0433a8abf93db41b1b243d9fd412b43b70ea3407; pass; tdd _(id: [rec-5f756070-db38-4690-ab2d-3d8d5407bbd4](.artifacts/records/project__check-run/rec-5f756070-db38-4690-ab2d-3d8d5407bbd4.md))_
- **replace-resolvers-dashboard**: rec-3b225e8d-812f-4975-8b1f-06a0fa127aec; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; tdd _(id: [rec-bca9fce2-404f-4887-9480-0f3797ab4b4a](.artifacts/records/project__check-run/rec-bca9fce2-404f-4887-9480-0f3797ab4b4a.md))_

## replace-resolvers-dashboard-file

### Acceptance
- **replace-resolvers-dashboard-file**: R4; tdd; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r4 -q _(id: [rec-407c508d-0394-41c4-96c1-6c510bfffbc8](.artifacts/records/project__acceptance/rec-407c508d-0394-41c4-96c1-6c510bfffbc8.md))_

### Check
- **replace-resolvers-dashboard-file**: rec-407c508d-0394-41c4-96c1-6c510bfffbc8; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-17fc981f-1fe6-42d3-ba18-41009816bf8c](.artifacts/records/project__check-run/rec-17fc981f-1fe6-42d3-ba18-41009816bf8c.md))_
- **replace-resolvers-dashboard-file**: rec-407c508d-0394-41c4-96c1-6c510bfffbc8; 0433a8abf93db41b1b243d9fd412b43b70ea3407; pass; tdd _(id: [rec-2511c3d8-cbe7-4928-91e9-640229867d20](.artifacts/records/project__check-run/rec-2511c3d8-cbe7-4928-91e9-640229867d20.md))_
- **replace-resolvers-dashboard-file**: rec-407c508d-0394-41c4-96c1-6c510bfffbc8; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; tdd _(id: [rec-c6fcb160-9731-49da-983d-6f45046d5f33](.artifacts/records/project__check-run/rec-c6fcb160-9731-49da-983d-6f45046d5f33.md))_
- **replace-resolvers-dashboard-file**: rec-407c508d-0394-41c4-96c1-6c510bfffbc8; cdcb9861c1b7f82caf097b00472d16f902d8d5b9; fail; tdd _(id: [rec-fdfff54d-270c-4692-996e-4497f639bddf](.artifacts/records/project__check-run/rec-fdfff54d-270c-4692-996e-4497f639bddf.md))_

## replace-resolvers-dep

### Acceptance
- **replace-resolvers-dep**: R10; tdd; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r10 -q _(id: [rec-58aa92a1-e53d-4679-bc46-86cd5c98618b](.artifacts/records/project__acceptance/rec-58aa92a1-e53d-4679-bc46-86cd5c98618b.md))_

### Check
- **replace-resolvers-dep**: rec-58aa92a1-e53d-4679-bc46-86cd5c98618b; 0433a8abf93db41b1b243d9fd412b43b70ea3407; pass; tdd _(id: [rec-34edec48-66ab-47c9-be52-5dab57436a48](.artifacts/records/project__check-run/rec-34edec48-66ab-47c9-be52-5dab57436a48.md))_
- **replace-resolvers-dep**: rec-58aa92a1-e53d-4679-bc46-86cd5c98618b; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; tdd _(id: [rec-3a9c92e9-af2b-40b6-9c09-09ae3c4c9ec6](.artifacts/records/project__check-run/rec-3a9c92e9-af2b-40b6-9c09-09ae3c4c9ec6.md))_
- **replace-resolvers-dep**: rec-58aa92a1-e53d-4679-bc46-86cd5c98618b; cdcb9861c1b7f82caf097b00472d16f902d8d5b9; fail; tdd _(id: [rec-5b48350e-6f41-49f7-a3f6-d4b39400e533](.artifacts/records/project__check-run/rec-5b48350e-6f41-49f7-a3f6-d4b39400e533.md))_
- **replace-resolvers-dep**: rec-58aa92a1-e53d-4679-bc46-86cd5c98618b; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; tdd _(id: [rec-6c9a354d-8219-44dd-b8b3-d2cb9c754ec9](.artifacts/records/project__check-run/rec-6c9a354d-8219-44dd-b8b3-d2cb9c754ec9.md))_

## requirement-links

### Acceptance
- **requirement-links**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and link and task' _(id: [rec-ceea1aa8-71eb-4308-925b-d17ce2d31253](.artifacts/records/project__acceptance/rec-ceea1aa8-71eb-4308-925b-d17ce2d31253.md))_

### Check
- **requirement-links**: rec-ceea1aa8-71eb-4308-925b-d17ce2d31253; dirty; pass; tdd _(id: [rec-10077915-9992-4211-8523-f34bdd4e5da7](.artifacts/records/project__check-run/rec-10077915-9992-4211-8523-f34bdd4e5da7.md))_
- **requirement-links**: rec-ceea1aa8-71eb-4308-925b-d17ce2d31253; dirty; fail; tdd _(id: [rec-555020ec-bbcd-475c-9760-afbf9ec6256d](.artifacts/records/project__check-run/rec-555020ec-bbcd-475c-9760-afbf9ec6256d.md))_

## requirement-links-needs

### Acceptance
- **requirement-links-needs**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and link and needs' _(id: [rec-b6a074dd-62de-4eea-85d1-100bd193b1bc](.artifacts/records/project__acceptance/rec-b6a074dd-62de-4eea-85d1-100bd193b1bc.md))_

### Check
- **requirement-links-needs**: rec-b6a074dd-62de-4eea-85d1-100bd193b1bc; dirty; pass; tdd _(id: [rec-41a4c06e-45dd-4b42-9f74-16996cf71a7c](.artifacts/records/project__check-run/rec-41a4c06e-45dd-4b42-9f74-16996cf71a7c.md))_
- **requirement-links-needs**: rec-b6a074dd-62de-4eea-85d1-100bd193b1bc; dirty; fail; tdd _(id: [rec-4787b2de-efbe-4c32-ab5d-e4da41c61579](.artifacts/records/project__check-run/rec-4787b2de-efbe-4c32-ab5d-e4da41c61579.md))_

## requirement-links-phase

### Acceptance
- **requirement-links-phase**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and link and phase' _(id: [rec-61730bf8-c287-4b79-a619-f974d0bef93d](.artifacts/records/project__acceptance/rec-61730bf8-c287-4b79-a619-f974d0bef93d.md))_

### Check
- **requirement-links-phase**: rec-61730bf8-c287-4b79-a619-f974d0bef93d; dirty; fail; tdd _(id: [rec-9c341d7e-065b-4c14-90b2-9e39a347a8f0](.artifacts/records/project__check-run/rec-9c341d7e-065b-4c14-90b2-9e39a347a8f0.md))_
- **requirement-links-phase**: rec-61730bf8-c287-4b79-a619-f974d0bef93d; dirty; pass; tdd _(id: [rec-cb97a248-814a-4806-9f3f-9896f03bb59f](.artifacts/records/project__check-run/rec-cb97a248-814a-4806-9f3f-9896f03bb59f.md))_

## requirement-screen

### Acceptance
- **requirement-screen**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_requirement.py -q _(id: [rec-fe7cbd3d-6b76-4bf1-b258-e4fa9361b6d8](.artifacts/records/project__acceptance/rec-fe7cbd3d-6b76-4bf1-b258-e4fa9361b6d8.md))_

### Check
- **requirement-screen**: rec-fe7cbd3d-6b76-4bf1-b258-e4fa9361b6d8; dirty; pass; tdd _(id: [rec-35e6d3ed-e3ba-41c5-96b9-e142d13d297a](.artifacts/records/project__check-run/rec-35e6d3ed-e3ba-41c5-96b9-e142d13d297a.md))_

## retry-dashboard

### Acceptance
- **retry-dashboard**: R8; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k "attempt_row or attempt_budget or attempt_snapshot or attempt_title" _(id: [rec-7bd7b9f7-ab98-40b6-9831-a074659941f7](.artifacts/records/project__acceptance/rec-7bd7b9f7-ab98-40b6-9831-a074659941f7.md))_

### Check
- **retry-dashboard**: rec-7bd7b9f7-ab98-40b6-9831-a074659941f7; 0077727e7e8d3b25e53d5aa1722b5c8f9ca58577; pass; tdd _(id: [rec-48ee479b-442e-4ce5-9c7c-d4dcdb02e4af](.artifacts/records/project__check-run/rec-48ee479b-442e-4ce5-9c7c-d4dcdb02e4af.md))_
- **retry-dashboard**: rec-7bd7b9f7-ab98-40b6-9831-a074659941f7; ee1a41be208bfdae700e1b78f9340296d82dae91; fail; tdd _(id: [rec-67c90e91-3195-4f2f-8740-ee38eb5249da](.artifacts/records/project__check-run/rec-67c90e91-3195-4f2f-8740-ee38eb5249da.md))_
- **retry-dashboard**: rec-17744c6d-ef91-4cf9-8072-298566ec8d16; 8ed3d5858b974a2fad5c321a09eb71edbd38bfb1; pass; tdd _(id: [rec-7bd4690f-7209-4c85-827e-68fd5125a8e8](.artifacts/records/project__check-run/rec-7bd4690f-7209-4c85-827e-68fd5125a8e8.md))_
- **retry-dashboard**: rec-17744c6d-ef91-4cf9-8072-298566ec8d16; ee1a41be208bfdae700e1b78f9340296d82dae91; pass; tdd _(id: [rec-867fca21-ef5a-4247-a438-bc49b8d485d5](.artifacts/records/project__check-run/rec-867fca21-ef5a-4247-a438-bc49b8d485d5.md))_
- **retry-dashboard**: rec-17744c6d-ef91-4cf9-8072-298566ec8d16; 0077727e7e8d3b25e53d5aa1722b5c8f9ca58577; pass; tdd _(id: [rec-a4506ee7-e01f-4925-8c0c-0de65f059c69](.artifacts/records/project__check-run/rec-a4506ee7-e01f-4925-8c0c-0de65f059c69.md))_

## retry-engine

### Acceptance
- **retry-engine**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_retry_loop.py -q _(id: [rec-09626673-9f46-4904-8541-2d2d5ecaf514](.artifacts/records/project__acceptance/rec-09626673-9f46-4904-8541-2d2d5ecaf514.md))_

### Check
- **retry-engine**: rec-09626673-9f46-4904-8541-2d2d5ecaf514; ee1a41be208bfdae700e1b78f9340296d82dae91; fail; tdd _(id: [rec-a518ce34-e098-4ab4-b526-3c2be4689d66](.artifacts/records/project__check-run/rec-a518ce34-e098-4ab4-b526-3c2be4689d66.md))_
- **retry-engine**: rec-09626673-9f46-4904-8541-2d2d5ecaf514; 0077727e7e8d3b25e53d5aa1722b5c8f9ca58577; pass; tdd _(id: [rec-a9ed2230-6a8f-4a1f-9990-c2ca852598d2](.artifacts/records/project__check-run/rec-a9ed2230-6a8f-4a1f-9990-c2ca852598d2.md))_

## retry-engine-contract

### Acceptance
- **retry-engine-contract**: R3; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_contract_self_consistency.py -q _(id: [rec-a40b0635-99ac-481f-a4fb-855a830b6fa1](.artifacts/records/project__acceptance/rec-a40b0635-99ac-481f-a4fb-855a830b6fa1.md))_

### Check
- **retry-engine-contract**: rec-a40b0635-99ac-481f-a4fb-855a830b6fa1; 0077727e7e8d3b25e53d5aa1722b5c8f9ca58577; pass; check _(id: [rec-732dbbeb-f099-4d3a-afe6-cd7f04062180](.artifacts/records/project__check-run/rec-732dbbeb-f099-4d3a-afe6-cd7f04062180.md))_

## retry-web-write-api

### Finding
- **retry-web-write-api**: R24 oracle asserts predecessor signed_by after correct-based sign; store puts signed_by on correction successor; test_r24_signer fail; direct dismiss_item reproduces; 8/9 other write tests pass at 4fc8cc27; oracle amended and R24 passes, or human withdrawn the claim; none _(id: [rec-39c0935d-669a-4825-a3a1-1450d9e4a1cc](.artifacts/records/project__finding/rec-39c0935d-669a-4825-a3a1-1450d9e4a1cc.md))_

## review-approval-constraints-spec-gap

### Finding
- **review-approval-constraints-spec-gap**: spec-gap on approval-constraints: exclusive human-gate constraint wording conflicts with preserved backlog promote/dismiss writes; dashboard-human-gate-writes says only Needs-you clears; backlog.py still supersedes with @current; constraint statement names backlog promote/dismiss as allowed or exclusivity is clarified without contradicting Non-goals, and reviewer re-run passes; none _(id: [rec-d3047fa6-a5cf-4f79-8d70-3a32f5590f8f](.artifacts/records/project__finding/rec-d3047fa6-a5cf-4f79-8d70-3a32f5590f8f.md))_

## review-claim-gate-missing-aff

### Finding
- **review-claim-gate-missing-aff**: missing aff raises FileNotFoundError instead of CloseRefused; phase-end reviewer NEEDS_WORK; fix lands and reviewer re-run passes; none _(id: [rec-3d72e525-d261-41ed-a19b-494bcc14660c](.artifacts/records/project__finding/rec-3d72e525-d261-41ed-a19b-494bcc14660c.md))_

## review-claim-gate-subject

### Finding
- **review-claim-gate-subject**: claim-gate uses acceptance.subject as claim id; dogfood subjects are task slugs; phase-end reviewer NEEDS_WORK; fix lands and reviewer re-run passes; none _(id: [rec-c8f43189-2581-4c49-82fd-8ea10694fd23](.artifacts/records/project__finding/rec-c8f43189-2581-4c49-82fd-8ea10694fd23.md))_

## review-claim-gate-success-test

### Finding
- **review-claim-gate-success-test**: no success-path test when verdict and recheck exit 0; phase-end reviewer NEEDS_WORK; fix lands and reviewer re-run passes; none _(id: [rec-b792b1f3-c487-476b-95fa-651ff6ba5aa8](.artifacts/records/project__finding/rec-b792b1f3-c487-476b-95fa-651ff6ba5aa8.md))_

## review-cli-package-behavior-bug

### Finding
- **review-cli-package-behavior-bug**: behavior-bug on cli-package: the installed orchestra console script eagerly imports affidavit.oracle_red, so it fails with a clean HOME and no affidavit checkout, breaking R5/R7 for every subcommand; Reviewer observed orchestra/cli.py:11 importing orchestra.close_batch, whose module import at close_batch.py:49 imports affidavit.oracle_red; pyproject declares no dependency; with HOME empty and no aff on PATH, python3 -m orchestra.cli --help raises ModuleNotFoundError: No module named 'affidavit'; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-60cd2a12-581c-4cd5-8864-212182d561e4](.artifacts/records/project__finding/rec-60cd2a12-581c-4cd5-8864-212182d561e4.md))_

## review-cli-package-invariant-violation

### Finding
- **review-cli-package-invariant-violation**: invariant-violation on cli-package: skills still call orchestra.reviewer, orchestra.suite, and orchestra.aa module APIs that the CLI does not expose, contradicting the 'CLI is the only runtime surface' invariant; Reviewer observed skills/execute-phase/SKILL.md:418,501,514,377,958 and shared/ensure-store.md:13,17 naming importable module APIs; orchestra/cli.py exposes only check, close-batch, install, contract, project-field, and sessions; fix lands and reviewer re-run passes, or human clears; human _(id: [rec-615efcde-152c-4962-8a78-f8c4253e298b](.artifacts/records/project__finding/rec-615efcde-152c-4962-8a78-f8c4253e298b.md))_

## review-command-facade-behavior-bug

### Finding
- **review-command-facade-behavior-bug**: behavior-bug on command-facade: cmd_apply dropped supersede, correct, and contradict; cmd_apply forwards every parsed line to Project.apply, so those verbs fail where base cli.py routed them through _do_supersede, _do_correct, and _do_contradict.; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-36820286-39ed-4bbc-8213-0ce1ff7ffcbf](.artifacts/records/project__finding/rec-36820286-39ed-4bbc-8213-0ce1ff7ffcbf.md))_

## review-criterion-views-minor

### Finding
- **review-criterion-views-minor**: missing-test minor: criterion_optional_in_contract omits view requires_payload; R4 view change landed; named test checks optional_payload only; test asserts brief/plan/verification roles omit criterion; none _(id: [rec-e0c7fb0b-8c5e-4768-a793-1eb732c512d1](.artifacts/records/project__finding/rec-e0c7fb0b-8c5e-4768-a793-1eb732c512d1.md))_

## review-install-docs-spec-gap

### Finding
- **review-install-docs-spec-gap**: spec-gap on install-docs: the pre-existing Agent Skills-host README section still tells users to copy five skills and keep shared docs two levels above, conflicting with the generated per-skill references payload; Reviewer observed README around line 110 still lists init/plan-phase/execute-phase/verify-work/engage and says to keep skills/kinds-and-focus.md and skills/ensure-store.md two levels above each SKILL.md, omitting settle-phase and analyze-sessions; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-e4f93753-3b86-4eb3-ba76-d2d630a1edc3](.artifacts/records/project__finding/rec-e4f93753-3b86-4eb3-ba76-d2d630a1edc3.md))_

## review-library-fixture-spec-gap

### Finding
- **review-library-fixture-spec-gap**: spec-gap on library-fixture: one integration test must read the created record with open_store, run close-batch to exit 0, and call the Python close so it accepts the fixture without starting aff or adaptive-artifacts; tests/test_library_e2e.py only asserts the close-batch command exit code; bind failures are discarded; the Python close is not called from the test; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-b174273d-f4c3-4b89-9bc4-19d56369b34a](.artifacts/records/project__finding/rec-b174273d-f4c3-4b89-9bc4-19d56369b34a.md))_

## review-native-adapters-behavior-bug

### Finding
- **review-native-adapters-behavior-bug**: behavior-bug on native-adapters: the Claude hook payload is written to .claude/hooks/hooks.json, which Claude does not read, so R12 is proven only by file presence; Reviewer observed Claude project hooks are read from .claude/settings.json and the installer never installs .claude-plugin/plugin.json or a plugin-root hooks/ directory; Cursor and OpenCode paths match the matrix; fix lands and reviewer re-run passes, or human clears; human _(id: [rec-4cbc622d-ceab-413d-9a05-a25d149589a3](.artifacts/records/project__finding/rec-4cbc622d-ceab-413d-9a05-a25d149589a3.md))_

## review-native-adapters-spec-gap

### Finding
- **review-native-adapters-spec-gap**: spec-gap on native-adapters: agents/se-reviewer.md and agents/reviewer.prompt.md define the same agent divergently, so R13's single canonical prompt is not actually the only source; Reviewer observed the pre-existing agents/se-reviewer.md remains in the same agents/ directory with divergent wording, while agents/reviewer.prompt.md declares the same agent name; the skill dispatches the stale file and GenericSkillsAdapter copies both; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-083ab868-b64c-4db6-9c78-274abae99bfa](.artifacts/records/project__finding/rec-083ab868-b64c-4db6-9c78-274abae99bfa.md))_

## review-negative-lint-judgment

### Finding
- **review-negative-lint-judgment**: judgment: no negative tests for compound/fat/missing requirement ids; spec wording vs skills+contract-only decision; positive examples only; human clears or later phase adds close lint; none _(id: [rec-6b971a14-51fd-4e3d-8c00-c07eb58f32f2](.artifacts/records/project__finding/rec-6b971a14-51fd-4e3d-8c00-c07eb58f32f2.md))_

## review-oracle-contract-record-types

### Finding
- **review-oracle-contract-record-types**: invariant-violation on oracle-contract: dual records/record_types catalogs; contract/project-design.json duplicates full record catalog under record_types; runtime uses records only; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-783374cb-2fc7-4b4a-a849-7ef8c983b528](.artifacts/records/project__finding/rec-783374cb-2fc7-4b4a-a849-7ef8c983b528.md))_

## review-oracle-red-path

### Finding
- **review-oracle-red-path**: pre-existing oracle suite requires real aff on PATH; phase-end reviewer NEEDS_WORK; fix lands and reviewer re-run passes; none _(id: [rec-04ad7abf-4e00-41da-8560-24684bcf3f3d](.artifacts/records/project__finding/rec-04ad7abf-4e00-41da-8560-24684bcf3f3d.md))_

## review-phase-gate-contract-behavior-bug

### Finding
- **review-phase-gate-contract-behavior-bug**: behavior-bug on phase-gate-contract: bundled contract ships full+advisory instead of mode=none; contract/project-design.json phase_gate.suite is full+advisory; ensure-store copies it to consumers; README claims mode=none default; bundled contract defaults to mode=none empty command; this repo pin full+advisory lives in live .artifacts design (or equivalent separated pin); reviewer re-run passes; none _(id: [rec-a9e2e213-922d-4157-96ac-2c835adba9d4](.artifacts/records/project__finding/rec-a9e2e213-922d-4157-96ac-2c835adba9d4.md))_

## review-phase-gate-contract-missing-test

### Finding
- **review-phase-gate-contract-missing-test**: missing-test on phase-gate-contract: plugin defaults test does not read bundled JSON; test_phase_gate_suite_plugin_defaults asserts a local constant only; this-repo test locks contract to full+advisory; tests assert bundled JSON mode=none separately from this-repo full+advisory pin; reviewer re-run passes; none _(id: [rec-2c6ee5f7-c7cb-4684-9b5c-d65c7bed255f](.artifacts/records/project__finding/rec-2c6ee5f7-c7cb-4684-9b5c-d65c7bed255f.md))_

## review-phase-gate-contract-spec-gap

### Finding
- **review-phase-gate-contract-spec-gap**: spec-gap on phase-gate-contract: live .artifacts/project-design.json not synced with this-repo suite pin; worktree .artifacts/project-design.json lacks phase_gate; runtime falls through to contract/; live design carries this-repo full+advisory (or documented equivalent) and resolve/pin is current; reviewer re-run passes; none _(id: [rec-56c5d5cb-3545-4a20-83d8-8e9fb3aa5ca3](.artifacts/records/project__finding/rec-56c5d5cb-3545-4a20-83d8-8e9fb3aa5ca3.md))_

## review-portable-skill-refs-spec-gap

### Finding
- **review-portable-skill-refs-spec-gap**: spec-gap on portable-skill-refs: skills/execute-phase/SKILL.md names agents/se-reviewer.md outside the skill directory, so R1's every-referenced-file-inside rule is unmet and a skills-only install has a dangling instruction; Reviewer observed skills/execute-phase/SKILL.md:422 dispatching agents/se-reviewer.md, while the installer generates that file under <host>/agents/ and the npx skills add tail ships no agents/ tree; tests/test_skill_portability.py only examines ./ ../ and references/ paths; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-7b48bc63-bdc3-4bff-bd47-9b9f388a03ec](.artifacts/records/project__finding/rec-7b48bc63-bdc3-4bff-bd47-9b9f388a03ec.md))_

## review-project-ops-behavior-bug

### Finding
- **review-project-ops-behavior-bug**: behavior-bug on project-ops: Project.apply must persist the NDJSON verbs the command already accepted; At 206fcd0, Project._apply_operation handles create and update only; supersede, correct, and contradict raise unsupported op.; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-25a1b825-fb83-49ea-a929-2b89d052c1c6](.artifacts/records/project__finding/rec-25a1b825-fb83-49ea-a929-2b89d052c1c6.md))_

## review-replace-resolvers-dashboard-behavior-bug

### Finding
- **review-replace-resolvers-dashboard-behavior-bug**: behavior-bug on replace-resolvers-dashboard: dashboard uv scripts do not include adaptive-artifacts; dashboard/bin/dashboard and dashboard/bin/web exec uv run --script on scripts whose PEP 723 dependencies omit adaptive-artifacts, while those scripts import adaptive_artifacts.project; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-c36525d8-29e8-4050-91e2-6e63c83aacdf](.artifacts/records/project__finding/rec-c36525d8-29e8-4050-91e2-6e63c83aacdf.md))_

## review-skills-oracle-red-docs

### Finding
- **review-skills-oracle-red-docs**: skills still document affidavit.oracle_red Python API while close-batch is CLI-only; reviewer judgment finding; docs updated or human clears; human _(id: [rec-ef1901ba-46da-4daf-a533-cb14f4552b2a](.artifacts/records/project__finding/rec-ef1901ba-46da-4daf-a533-cb14f4552b2a.md))_

## review-tests-brief-lock

### Finding
- **review-tests-brief-lock**: missing-test on tests-claim-chain: R5 original-text brief rules not locked by plan-trace; execute-phase skill updated but no test asserts quote/no-paraphrase wording; fix lands asserting execute-phase original-text brief rules and reviewer re-run passes; none _(id: [rec-e480f9cb-a79e-4c72-9feb-ad15b790c214](.artifacts/records/project__finding/rec-e480f9cb-a79e-4c72-9feb-ad15b790c214.md))_

## review2-npx-list-test

### Finding
- **review2-npx-list-test**: missing-test on the phase exit criterion: no test or installer path exercises `npx skills add --list` resolving a generic profile, as the specification requires; Specification line: 'A temporary-HOME install for Claude and OpenCode loads the generated skill dirs, and npx skills add --list resolves a generic profile (R11, R12).' Tests stub npx and only assert 'skills add -a codex'; fix lands and reviewer re-run passes, or human clears/amends the spec; human _(id: [rec-900eee65-bdef-4094-8e48-b994df91b105](.artifacts/records/project__finding/rec-900eee65-bdef-4094-8e48-b994df91b105.md))_

## review2-opencode-permission-action

### Finding
- **review2-opencode-permission-action**: behavior-bug (partly incorrect) on native-adapters: the generated OpenCode agent uses the correct plural permissions key, but also emits an inert write: deny action; write/apply_patch are gated by edit, which is already denied; Reviewer claimed OpenCode uses permission: singular; OpenCode V2 docs use permissions: plural and explicitly list legacy permission under fields not to use. installer/agents.py emits permissions: plus edit: deny and write: deny; tests assert both; fix lands and reviewer re-run passes, or human clears; human _(id: [rec-e64256f8-1083-4ca9-a94f-2b7b46510e3b](.artifacts/records/project__finding/rec-e64256f8-1083-4ca9-a94f-2b7b46510e3b.md))_

## review2-opencode-plugin-path

### Finding
- **review2-opencode-plugin-path**: behavior-bug on native-adapters: the OpenCode hook payload is installed at the install root as plugin.js, but OpenCode auto-loads plugins only from <root>/plugins/ (or a plugins config entry), so hook-start/hook-stop never run; OpenCode V2 docs: plugins under .opencode/plugins/ are loaded automatically; reviewer observed hosts/opencode/plugin.js merged at the install root by NativeAdapter.desired_entries, with tests pinning <root>/plugin.js; fix lands and reviewer re-run passes, or human clears; human _(id: [rec-265b5127-b459-474e-ab45-732925c68473](.artifacts/records/project__finding/rec-265b5127-b459-474e-ab45-732925c68473.md))_

## reviewer-brief

### Acceptance
- **reviewer-brief**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k brief _(id: [rec-880e5caf-3938-480b-ae11-a180c0b1ed38](.artifacts/records/project__acceptance/rec-880e5caf-3938-480b-ae11-a180c0b1ed38.md))_

### Check
- **reviewer-brief**: rec-880e5caf-3938-480b-ae11-a180c0b1ed38; dirty; fail; tdd _(id: [rec-a499089a-467b-44c5-842e-b71c171071f4](.artifacts/records/project__check-run/rec-a499089a-467b-44c5-842e-b71c171071f4.md))_
- **reviewer-brief**: rec-880e5caf-3938-480b-ae11-a180c0b1ed38; f063d7aa3b3a2311a9bcfdc6973e90c5065bd145; pass; tdd _(id: [rec-df5cf3a1-37b5-49ae-bdf7-aa9daf4ce6bb](.artifacts/records/project__check-run/rec-df5cf3a1-37b5-49ae-bdf7-aa9daf4ce6bb.md))_

## reviewer-execute

### Acceptance
- **reviewer-execute**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k "execute or parent_write or review_check" _(id: [rec-10c147f9-1f69-4746-8444-72e2fe310165](.artifacts/records/project__acceptance/rec-10c147f9-1f69-4746-8444-72e2fe310165.md))_

### Check
- **reviewer-execute**: rec-10c147f9-1f69-4746-8444-72e2fe310165; dirty; fail; tdd _(id: [rec-28c1dffc-6ced-43ed-838d-1ce61d9f2acc](.artifacts/records/project__check-run/rec-28c1dffc-6ced-43ed-838d-1ce61d9f2acc.md))_
- **reviewer-execute**: rec-10c147f9-1f69-4746-8444-72e2fe310165; 2eaa40ff59e34104c88b041622de2b51b24f18e0; pass; tdd _(id: [rec-77136380-2e02-4e65-9a92-f5d3b61847f8](.artifacts/records/project__check-run/rec-77136380-2e02-4e65-9a92-f5d3b61847f8.md))_

## reviewer-execute-fix

### Acceptance
- **reviewer-execute-fix**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k "fix_task or rerun or budget" _(id: [rec-7d0c4862-c22a-4fd3-bcae-3679c065e527](.artifacts/records/project__acceptance/rec-7d0c4862-c22a-4fd3-bcae-3679c065e527.md))_

### Check
- **reviewer-execute-fix**: rec-7d0c4862-c22a-4fd3-bcae-3679c065e527; dirty; fail; tdd _(id: [rec-2cc1e133-c736-4d61-865a-bd41be2b3493](.artifacts/records/project__check-run/rec-2cc1e133-c736-4d61-865a-bd41be2b3493.md))_
- **reviewer-execute-fix**: rec-7d0c4862-c22a-4fd3-bcae-3679c065e527; 2eaa40ff59e34104c88b041622de2b51b24f18e0; pass; tdd _(id: [rec-e1b9e60d-af01-48e4-a5a2-d02e91765703](.artifacts/records/project__check-run/rec-e1b9e60d-af01-48e4-a5a2-d02e91765703.md))_

## reviewer-execute-gate

### Acceptance
- **reviewer-execute-gate**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k gate _(id: [rec-4fe99528-e397-4b36-b07f-f93d2b1291f9](.artifacts/records/project__acceptance/rec-4fe99528-e397-4b36-b07f-f93d2b1291f9.md))_

### Check
- **reviewer-execute-gate**: rec-4fe99528-e397-4b36-b07f-f93d2b1291f9; dirty; fail; tdd _(id: [rec-0f807325-5bee-4853-a175-e0d84bc3f006](.artifacts/records/project__check-run/rec-0f807325-5bee-4853-a175-e0d84bc3f006.md))_
- **reviewer-execute-gate**: rec-4fe99528-e397-4b36-b07f-f93d2b1291f9; 2eaa40ff59e34104c88b041622de2b51b24f18e0; pass; tdd _(id: [rec-6042c68a-2624-42a7-8996-f9ebd5ee5766](.artifacts/records/project__check-run/rec-6042c68a-2624-42a7-8996-f9ebd5ee5766.md))_

## reviewer-execute-integration

### Acceptance
- **reviewer-execute-integration**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py tests/test_skill_contract_consistency.py -q -k "integration or test_skill_contract" _(id: [rec-87416dee-0be6-4e6a-bf05-d567fac451bf](.artifacts/records/project__acceptance/rec-87416dee-0be6-4e6a-bf05-d567fac451bf.md))_

### Check
- **reviewer-execute-integration**: rec-87416dee-0be6-4e6a-bf05-d567fac451bf; 2eaa40ff59e34104c88b041622de2b51b24f18e0; pass; check _(id: [rec-b69d1c07-b6e6-45d0-a8fe-29fe94c45625](.artifacts/records/project__check-run/rec-b69d1c07-b6e6-45d0-a8fe-29fe94c45625.md))_

## rj-join

### Acceptance
- **rj-join**: tdd; session-analysis; python3 -m pytest -q tests/test_record_join.py _(id: [rec-fa22cc2f-06e1-491e-a277-9c9ab01fa21e](.artifacts/records/project__acceptance/rec-fa22cc2f-06e1-491e-a277-9c9ab01fa21e.md))_

### Check
- **rj-join**: rec-fa22cc2f-06e1-491e-a277-9c9ab01fa21e; dirty; pass; tdd _(id: [rec-c6653684-ddd4-40ea-b5bf-2f494fe9e3bd](.artifacts/records/project__check-run/rec-c6653684-ddd4-40ea-b5bf-2f494fe9e3bd.md))_

## rj-record-reader

### Acceptance
- **rj-record-reader**: tdd; session-analysis; python3 -m pytest -q tests/test_record_reader.py _(id: [rec-f89ab522-1803-4881-b257-f9a885c2d0de](.artifacts/records/project__acceptance/rec-f89ab522-1803-4881-b257-f9a885c2d0de.md))_

### Check
- **rj-record-reader**: rec-f89ab522-1803-4881-b257-f9a885c2d0de; dirty; pass; tdd _(id: [rec-d0f1920c-4142-43ce-a7e2-a539e6d1ff02](.artifacts/records/project__check-run/rec-d0f1920c-4142-43ce-a7e2-a539e6d1ff02.md))_

## rj-report-records

### Acceptance
- **rj-report-records**: tdd; session-analysis; python3 -m pytest -q tests/test_session_report.py _(id: [rec-193dfd71-f09c-43b5-95db-e685a4a80e4f](.artifacts/records/project__acceptance/rec-193dfd71-f09c-43b5-95db-e685a4a80e4f.md))_

### Check
- **rj-report-records**: rec-193dfd71-f09c-43b5-95db-e685a4a80e4f; dirty; pass; tdd _(id: [rec-4ba0fea6-e2d0-4a40-a875-158c1643e93b](.artifacts/records/project__check-run/rec-4ba0fea6-e2d0-4a40-a875-158c1643e93b.md))_

### Finding
- **rj-report-records**: The project-plus-time-window join leaves 70% of attached records ambiguous (386 of 553), so per-session record counts are unreliable for overlapping sessions.; Real run of session_report.py --records over 247 sessions: 8 sessions have records, 553 records attach, 386 attach to two or more sessions.; Records carry a session id, or sessions get narrower activity windows that remove the overlap.; none _(id: [rec-b8213c07-3cf9-4b56-a2a5-e9f56bd93f78](.artifacts/records/project__finding/rec-b8213c07-3cf9-4b56-a2a5-e9f56bd93f78.md))_

## route-through-discuss

### Acceptance
- **route-through-discuss**: tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_discuss_skill.py -q _(id: [rec-aac400ee-30c6-4fd2-a3ba-9fbd756f740a](.artifacts/records/project__acceptance/rec-aac400ee-30c6-4fd2-a3ba-9fbd756f740a.md))_

### Check
- **route-through-discuss**: rec-aac400ee-30c6-4fd2-a3ba-9fbd756f740a; 8c697bc88db7147f17a058311b0323cd4a191fee; pass; tdd _(id: [rec-4faad849-e58b-43c3-971c-0273f995955c](.artifacts/records/project__check-run/rec-4faad849-e58b-43c3-971c-0273f995955c.md))_

## runtime-install

### Acceptance
- **runtime-install**: R5; tdd; library-boundary; python3 -m pytest tests/integration/test_declared_install.py::test_r5_clean_install_imports_adaptive_artifacts -q _(id: [rec-d790ab19-ac45-4a5c-a5e8-bec3225b397d](.artifacts/records/project__acceptance/rec-d790ab19-ac45-4a5c-a5e8-bec3225b397d.md))_

### Check
- **runtime-install**: rec-d790ab19-ac45-4a5c-a5e8-bec3225b397d; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; tdd _(id: [rec-3816e225-a1ec-48ad-bc8c-dfe48bde2d3c](.artifacts/records/project__check-run/rec-3816e225-a1ec-48ad-bc8c-dfe48bde2d3c.md))_
- **runtime-install**: rec-d790ab19-ac45-4a5c-a5e8-bec3225b397d; dirty; fail; tdd _(id: [rec-88337e3b-3709-43fc-b638-79f2d6ec22a0](.artifacts/records/project__check-run/rec-88337e3b-3709-43fc-b638-79f2d6ec22a0.md))_

## runtime-install-plain

### Acceptance
- **runtime-install-plain**: R6; tdd; library-boundary; python3 -m pytest tests/integration/test_declared_install.py::test_r6_plain_install_does_not_install_affidavit -q _(id: [rec-38889053-de00-4a96-b4cd-01664743ddf7](.artifacts/records/project__acceptance/rec-38889053-de00-4a96-b4cd-01664743ddf7.md))_

### Check
- **runtime-install-plain**: rec-38889053-de00-4a96-b4cd-01664743ddf7; dirty; fail; tdd _(id: [rec-23180767-d21f-41e8-85b4-0b41c8a3126e](.artifacts/records/project__check-run/rec-23180767-d21f-41e8-85b4-0b41c8a3126e.md))_
- **runtime-install-plain**: rec-38889053-de00-4a96-b4cd-01664743ddf7; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; tdd _(id: [rec-f98046bc-ca33-4bb7-a430-b5f76258fcb9](.artifacts/records/project__check-run/rec-f98046bc-ca33-4bb7-a430-b5f76258fcb9.md))_

## se-reviewer-agent

### Acceptance
- **se-reviewer-agent**: R1; check; workflow-loop; test -f agents/se-reviewer.md && grep -qiE "no Write|without Write" agents/se-reviewer.md && grep -q agents/ scripts/sync-plugin.sh && d=$(mktemp -d) && bash scripts/sync-plugin.sh "$d/p" && test -f "$d/p/agents/se-reviewer.md" _(id: [rec-b06d589a-93d4-47e0-b2a4-5e1bf1fd8f21](.artifacts/records/project__acceptance/rec-b06d589a-93d4-47e0-b2a4-5e1bf1fd8f21.md))_

### Check
- **se-reviewer-agent**: rec-b06d589a-93d4-47e0-b2a4-5e1bf1fd8f21; f063d7aa3b3a2311a9bcfdc6973e90c5065bd145; pass; check _(id: [rec-03654543-d5c3-4c12-9c95-d11fecb0ce53](.artifacts/records/project__check-run/rec-03654543-d5c3-4c12-9c95-d11fecb0ce53.md))_
- **se-reviewer-agent**: rec-b06d589a-93d4-47e0-b2a4-5e1bf1fd8f21; f063d7aa3b3a2311a9bcfdc6973e90c5065bd145; pass; check _(id: [rec-79c540d0-ba3c-4c3f-b914-523a542dc06e](.artifacts/records/project__check-run/rec-79c540d0-ba3c-4c3f-b914-523a542dc06e.md))_

## se-workflow-check

### Acceptance
- **se-workflow-check**: R7; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k "pass or fail or integration or cli" _(id: [rec-b5d23174-3de0-41c1-8cfd-028492fc5d87](.artifacts/records/project__acceptance/rec-b5d23174-3de0-41c1-8cfd-028492fc5d87.md))_

### Check
- **se-workflow-check**: rec-b5d23174-3de0-41c1-8cfd-028492fc5d87; c600c3ec9c7a7a01736618697ca4b3d5aebb9beb; pass; tdd _(id: [rec-5ece32a4-c85c-4570-a10d-bba1c2548df9](.artifacts/records/project__check-run/rec-5ece32a4-c85c-4570-a10d-bba1c2548df9.md))_

## se-workflow-check-dirty

### Acceptance
- **se-workflow-check-dirty**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k dirty _(id: [rec-6b1e869a-6b06-49a6-9d3f-33e8326e05c1](.artifacts/records/project__acceptance/rec-6b1e869a-6b06-49a6-9d3f-33e8326e05c1.md))_

### Check
- **se-workflow-check-dirty**: rec-6b1e869a-6b06-49a6-9d3f-33e8326e05c1; c600c3ec9c7a7a01736618697ca4b3d5aebb9beb; pass; tdd _(id: [rec-69f95f94-1349-4bd6-997f-edb71cbe9ad3](.artifacts/records/project__check-run/rec-69f95f94-1349-4bd6-997f-edb71cbe9ad3.md))_

## se-workflow-check-entry

### Acceptance
- **se-workflow-check-entry**: R8; check; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k "entry or sync or install or bin" _(id: [rec-28b0ca39-45c6-4c7c-ac2d-bf41ba33cdf4](.artifacts/records/project__acceptance/rec-28b0ca39-45c6-4c7c-ac2d-bf41ba33cdf4.md))_

### Check
- **se-workflow-check-entry**: rec-28b0ca39-45c6-4c7c-ac2d-bf41ba33cdf4; c600c3ec9c7a7a01736618697ca4b3d5aebb9beb; pass; check _(id: [rec-8101f194-ab18-4e13-ae54-60e3565ab681](.artifacts/records/project__check-run/rec-8101f194-ab18-4e13-ae54-60e3565ab681.md))_

## se-workflow-check-manual

### Acceptance
- **se-workflow-check-manual**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k manual _(id: [rec-8eee9825-6a0d-4e05-9a8e-0d7558c7ed45](.artifacts/records/project__acceptance/rec-8eee9825-6a0d-4e05-9a8e-0d7558c7ed45.md))_

### Check
- **se-workflow-check-manual**: rec-8eee9825-6a0d-4e05-9a8e-0d7558c7ed45; c600c3ec9c7a7a01736618697ca4b3d5aebb9beb; pass; tdd _(id: [rec-20a0c965-e869-4427-949a-3f333d850bca](.artifacts/records/project__check-run/rec-20a0c965-e869-4427-949a-3f333d850bca.md))_

## se-workflow-check-runner-fields

### Acceptance
- **se-workflow-check-runner-fields**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k "runner or fields or metadata or exit_code" _(id: [rec-7715368f-94c3-4b3d-9692-5061c4cabafe](.artifacts/records/project__acceptance/rec-7715368f-94c3-4b3d-9692-5061c4cabafe.md))_

### Check
- **se-workflow-check-runner-fields**: rec-7715368f-94c3-4b3d-9692-5061c4cabafe; c600c3ec9c7a7a01736618697ca4b3d5aebb9beb; pass; tdd _(id: [rec-e3bd1a4b-1d3a-41c2-99b0-a675670cbccd](.artifacts/records/project__check-run/rec-e3bd1a4b-1d3a-41c2-99b0-a675670cbccd.md))_

## shared-aa-resolver

### Acceptance
- **shared-aa-resolver**: R2; tdd; packaging; uv run --with pytest python -m pytest tests/test_aa_resolve.py -q _(id: [rec-15f765d5-4785-4b60-8e28-1e0c176acff4](.artifacts/records/project__acceptance/rec-15f765d5-4785-4b60-8e28-1e0c176acff4.md))_

### Check
- **shared-aa-resolver**: rec-15f765d5-4785-4b60-8e28-1e0c176acff4; dirty; fail; tdd _(id: [rec-570c80b2-13ad-4e0c-ad09-ddb8e3f82bb7](.artifacts/records/project__check-run/rec-570c80b2-13ad-4e0c-ad09-ddb8e3f82bb7.md))_
- **shared-aa-resolver**: rec-15f765d5-4785-4b60-8e28-1e0c176acff4; 23c6f922d2a051135dc323f67924f2364b3788db; pass; tdd _(id: [rec-5a71810f-915b-4628-b05b-538d32faa74b](.artifacts/records/project__check-run/rec-5a71810f-915b-4628-b05b-538d32faa74b.md))_
- **shared-aa-resolver**: rec-15f765d5-4785-4b60-8e28-1e0c176acff4; dirty; fail; tdd _(id: [rec-a9a1ceb3-58a7-4c54-bbf5-c3e778574d60](.artifacts/records/project__check-run/rec-a9a1ceb3-58a7-4c54-bbf5-c3e778574d60.md))_

## side-rail-calm-review

### Check
- **side-rail-calm-review**: side-rail-calm-review; c747adfaf64276bb807bb99e17174c1d3542a572; pass; review _(id: [rec-4a609646-0600-478a-91da-1c9197bfe476](.artifacts/records/project__check-run/rec-4a609646-0600-478a-91da-1c9197bfe476.md))_

## side-rail-home

### Acceptance
- **side-rail-home**: R1; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R1 _(id: [rec-2cc14bc7-6741-42cd-89ee-7d1ac0428631](.artifacts/records/project__acceptance/rec-2cc14bc7-6741-42cd-89ee-7d1ac0428631.md))_

### Check
- **side-rail-home**: rec-2cc14bc7-6741-42cd-89ee-7d1ac0428631; 4a95fb2856cf0e88cebd5fc684df29dfb638d742; pass; check _(id: [rec-bd90a161-0f69-445f-aa8b-35bba0e01a56](.artifacts/records/project__check-run/rec-bd90a161-0f69-445f-aa8b-35bba0e01a56.md))_

## side-rail-home-r2

### Acceptance
- **side-rail-home-r2**: R2; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R2 _(id: [rec-33d3807c-6eb6-45f7-b3b8-c3cf757b6da5](.artifacts/records/project__acceptance/rec-33d3807c-6eb6-45f7-b3b8-c3cf757b6da5.md))_

### Check
- **side-rail-home-r2**: rec-33d3807c-6eb6-45f7-b3b8-c3cf757b6da5; 4a95fb2856cf0e88cebd5fc684df29dfb638d742; pass; check _(id: [rec-c11d799e-5290-4fd9-95e2-d7fc55c10e62](.artifacts/records/project__check-run/rec-c11d799e-5290-4fd9-95e2-d7fc55c10e62.md))_

## side-rail-home-r3

### Acceptance
- **side-rail-home-r3**: R3; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R3 _(id: [rec-2bbcde12-f78c-4b03-abbb-0fd59939efed](.artifacts/records/project__acceptance/rec-2bbcde12-f78c-4b03-abbb-0fd59939efed.md))_

### Check
- **side-rail-home-r3**: rec-2bbcde12-f78c-4b03-abbb-0fd59939efed; 4a95fb2856cf0e88cebd5fc684df29dfb638d742; pass; check _(id: [rec-c7cf0887-9f4d-41e9-83af-7d33cad72029](.artifacts/records/project__check-run/rec-c7cf0887-9f4d-41e9-83af-7d33cad72029.md))_

## side-rail-home-r4

### Acceptance
- **side-rail-home-r4**: R4; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R4 _(id: [rec-049b56c1-fc81-42c4-944e-7431cd88dc5c](.artifacts/records/project__acceptance/rec-049b56c1-fc81-42c4-944e-7431cd88dc5c.md))_

### Check
- **side-rail-home-r4**: rec-049b56c1-fc81-42c4-944e-7431cd88dc5c; 4a95fb2856cf0e88cebd5fc684df29dfb638d742; pass; check _(id: [rec-0bac8c17-e305-49c2-8569-24978e969e9d](.artifacts/records/project__check-run/rec-0bac8c17-e305-49c2-8569-24978e969e9d.md))_

## side-rail-journal-screen

### Acceptance
- **side-rail-journal-screen**: R5; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R5 _(id: [rec-9f91c834-c5b5-4585-b668-7352942d7739](.artifacts/records/project__acceptance/rec-9f91c834-c5b5-4585-b668-7352942d7739.md))_

### Check
- **side-rail-journal-screen**: rec-9f91c834-c5b5-4585-b668-7352942d7739; c747adfaf64276bb807bb99e17174c1d3542a572; pass; check _(id: [rec-cbed4457-5010-48c5-b3b4-5bcd7c0ab5e5](.artifacts/records/project__check-run/rec-cbed4457-5010-48c5-b3b4-5bcd7c0ab5e5.md))_

## side-rail-journal-screen-r6

### Acceptance
- **side-rail-journal-screen-r6**: R6; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R6 _(id: [rec-783c3195-93d2-4203-863b-26c681a0db7f](.artifacts/records/project__acceptance/rec-783c3195-93d2-4203-863b-26c681a0db7f.md))_

### Check
- **side-rail-journal-screen-r6**: rec-783c3195-93d2-4203-863b-26c681a0db7f; c747adfaf64276bb807bb99e17174c1d3542a572; pass; check _(id: [rec-5e8cceaa-4d11-4c00-9b85-3f25a19f6290](.artifacts/records/project__check-run/rec-5e8cceaa-4d11-4c00-9b85-3f25a19f6290.md))_

## side-rail-journal-screen-r7

### Acceptance
- **side-rail-journal-screen-r7**: R7; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R7 _(id: [rec-92004460-e379-480b-8da4-3efc6c2369fa](.artifacts/records/project__acceptance/rec-92004460-e379-480b-8da4-3efc6c2369fa.md))_

### Check
- **side-rail-journal-screen-r7**: rec-92004460-e379-480b-8da4-3efc6c2369fa; c747adfaf64276bb807bb99e17174c1d3542a572; pass; check _(id: [rec-d2cb1092-04fa-4677-9ebb-e733188e250e](.artifacts/records/project__check-run/rec-d2cb1092-04fa-4677-9ebb-e733188e250e.md))_

## side-rail-journal-screen-r8

### Acceptance
- **side-rail-journal-screen-r8**: R8; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R8 _(id: [rec-0a5812b1-56a2-446d-96df-a719a84264c7](.artifacts/records/project__acceptance/rec-0a5812b1-56a2-446d-96df-a719a84264c7.md))_

### Check
- **side-rail-journal-screen-r8**: rec-0a5812b1-56a2-446d-96df-a719a84264c7; c747adfaf64276bb807bb99e17174c1d3542a572; pass; check _(id: [rec-53a4cbca-9310-4146-9dba-3e9fc5f81972](.artifacts/records/project__check-run/rec-53a4cbca-9310-4146-9dba-3e9fc5f81972.md))_

## side-rail-journal-screen-r9

### Acceptance
- **side-rail-journal-screen-r9**: R9; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R9 _(id: [rec-bbf8dd2d-c827-4d3b-98e8-9d7fd4163fe0](.artifacts/records/project__acceptance/rec-bbf8dd2d-c827-4d3b-98e8-9d7fd4163fe0.md))_

### Check
- **side-rail-journal-screen-r9**: rec-bbf8dd2d-c827-4d3b-98e8-9d7fd4163fe0; c747adfaf64276bb807bb99e17174c1d3542a572; pass; check _(id: [rec-b605ee55-c461-49f4-8a4e-2dfe2270d051](.artifacts/records/project__check-run/rec-b605ee55-c461-49f4-8a4e-2dfe2270d051.md))_

## skill-needs-clear

### Acceptance
- **skill-needs-clear**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_discuss_skill.py -q _(id: [rec-0e2c47f2-f119-466d-8e46-fe961b604d3b](.artifacts/records/project__acceptance/rec-0e2c47f2-f119-466d-8e46-fe961b604d3b.md))_

### Check
- **skill-needs-clear**: rec-0e2c47f2-f119-466d-8e46-fe961b604d3b; 8799ca930443a9a3144434eaf3b9e30e497adbce; pass; tdd _(id: [rec-dfedfe05-c9f6-436d-a9cb-10752f198063](.artifacts/records/project__check-run/rec-dfedfe05-c9f6-436d-a9cb-10752f198063.md))_

### Observation
- **skill-needs-clear**: kinds-and-focus and engage lacked Needs-you clear/remind; gate-opening skills lacked clear CLIs; supersede for findings is illegal at runtime; workflow-loop _(id: [rec-3e2848ab-45e5-46ae-8087-757079a4cb07](.artifacts/records/project__investigation-observation/rec-3e2848ab-45e5-46ae-8087-757079a4cb07.md))_

### Finding
- **skill-needs-clear**: Skills opened human Needs-you gates without documenting clear-at-event CLI and engage remind; finding clear must be update needs none not supersede; pre-fix skill text and failing doc assertions; runtime rejects finding supersede; kinds-and-focus/engage and gate skills document clears including update needs none and tests stay green; none _(id: [rec-2d62de79-b64c-433f-b4ba-55c9612ba420](.artifacts/records/project__finding/rec-2d62de79-b64c-433f-b4ba-55c9612ba420.md))_

## skill-needs-clear-engage

### Acceptance
- **skill-needs-clear-engage**: R2; check; workflow-loop; uv run --with pytest python -m pytest tests/test_discuss_skill.py -q -k engage _(id: [rec-152ce4a8-e20f-4b8c-87b9-aaf30fb53703](.artifacts/records/project__acceptance/rec-152ce4a8-e20f-4b8c-87b9-aaf30fb53703.md))_

### Check
- **skill-needs-clear-engage**: rec-152ce4a8-e20f-4b8c-87b9-aaf30fb53703; 8799ca930443a9a3144434eaf3b9e30e497adbce; pass; check _(id: [rec-8a447353-10e5-4b7f-bc4c-76b7c2f1ea8f](.artifacts/records/project__check-run/rec-8a447353-10e5-4b7f-bc4c-76b7c2f1ea8f.md))_

## skill-needs-clear-opens

### Acceptance
- **skill-needs-clear-opens**: R3; check; workflow-loop; uv run --with pytest python -m pytest tests/test_discuss_skill.py tests/test_skill_contract_consistency.py -q _(id: [rec-e154ee7d-d057-4d26-bd3e-9962592157f0](.artifacts/records/project__acceptance/rec-e154ee7d-d057-4d26-bd3e-9962592157f0.md))_

### Check
- **skill-needs-clear-opens**: rec-e154ee7d-d057-4d26-bd3e-9962592157f0; 8799ca930443a9a3144434eaf3b9e30e497adbce; pass; check _(id: [rec-91b822ea-acd7-4c65-81d6-fa35a64f4129](.artifacts/records/project__check-run/rec-91b822ea-acd7-4c65-81d6-fa35a64f4129.md))_

## skill-plugin-paths

### Acceptance
- **skill-plugin-paths**: R1; check; packaging; grep -q CLAUDE_PLUGIN_ROOT skills/ensure-store.md && grep -q CURSOR_PLUGIN_ROOT skills/ensure-store.md && ! grep -E '^[0-9]+\. .*\.cursor/plugins/local/se-workflow' skills/ensure-store.md _(id: [rec-1dc4bf40-0968-4e85-845f-c345a81a9768](.artifacts/records/project__acceptance/rec-1dc4bf40-0968-4e85-845f-c345a81a9768.md))_

### Check
- **skill-plugin-paths**: rec-1dc4bf40-0968-4e85-845f-c345a81a9768; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; check _(id: [rec-3d166850-209a-42d1-85c0-d13eebf7102a](.artifacts/records/project__check-run/rec-3d166850-209a-42d1-85c0-d13eebf7102a.md))_

## skill-plugin-paths-close

### Acceptance
- **skill-plugin-paths-close**: R3; check; packaging; grep -qE "se-workflow close-batch|bin/se-workflow close-batch" skills/verify-work/SKILL.md && ! grep -q scripts/close_batch.py skills/verify-work/SKILL.md _(id: [rec-05718b54-2ff0-42df-9d90-5563f4509289](.artifacts/records/project__acceptance/rec-05718b54-2ff0-42df-9d90-5563f4509289.md))_

### Check
- **skill-plugin-paths-close**: rec-05718b54-2ff0-42df-9d90-5563f4509289; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; check _(id: [rec-2fd379a5-8ec6-415d-b321-f9aa2fd3e4e5](.artifacts/records/project__check-run/rec-2fd379a5-8ec6-415d-b321-f9aa2fd3e4e5.md))_

## skill-plugin-paths-contract

### Acceptance
- **skill-plugin-paths-contract**: R4; check; packaging; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-3b720bda-fcdb-4cab-9cb2-e965636a73b0](.artifacts/records/project__acceptance/rec-3b720bda-fcdb-4cab-9cb2-e965636a73b0.md))_

### Check
- **skill-plugin-paths-contract**: rec-3b720bda-fcdb-4cab-9cb2-e965636a73b0; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; check _(id: [rec-3ca9c3cb-a02a-47bf-9ac9-79d2bf5d2a00](.artifacts/records/project__check-run/rec-3ca9c3cb-a02a-47bf-9ac9-79d2bf5d2a00.md))_

## skill-task-worktree

### Acceptance
- **skill-task-worktree**: R1; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r1_landing_creates_a_task_branch_except_the_verification_task -q --tb=short _(id: [rec-05063455-94b9-4240-a1c0-eda12599cf71](.artifacts/records/project__acceptance/rec-05063455-94b9-4240-a1c0-eda12599cf71.md))_

### Check
- **skill-task-worktree**: rec-05063455-94b9-4240-a1c0-eda12599cf71; dirty; fail; tdd _(id: [rec-14c32e53-c0ef-4a78-ae7d-f458a2def8ea](.artifacts/records/project__check-run/rec-14c32e53-c0ef-4a78-ae7d-f458a2def8ea.md))_
- **skill-task-worktree**: rec-05063455-94b9-4240-a1c0-eda12599cf71; dirty; fail; tdd _(id: [rec-1b8caffa-0f69-4ab0-a3f0-9557ffed6bda](.artifacts/records/project__check-run/rec-1b8caffa-0f69-4ab0-a3f0-9557ffed6bda.md))_
- **skill-task-worktree**: rec-05063455-94b9-4240-a1c0-eda12599cf71; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-74d90161-898a-456f-b9ec-7f6de8ba6337](.artifacts/records/project__check-run/rec-74d90161-898a-456f-b9ec-7f6de8ba6337.md))_
- **skill-task-worktree**: rec-05063455-94b9-4240-a1c0-eda12599cf71; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-b1540e97-40e9-4e52-84d7-35adeedfdeca](.artifacts/records/project__check-run/rec-b1540e97-40e9-4e52-84d7-35adeedfdeca.md))_
- **skill-task-worktree**: rec-05063455-94b9-4240-a1c0-eda12599cf71; dirty; fail; tdd _(id: [rec-d66e0603-72be-419d-a94d-c246521a74b3](.artifacts/records/project__check-run/rec-d66e0603-72be-419d-a94d-c246521a74b3.md))_

## skill-task-worktree-r10

### Acceptance
- **skill-task-worktree-r10**: R10; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r10_parent_does_not_merge_a_task_branch_whose_check_did_not_pass -q --tb=short _(id: [rec-f869e403-b8c6-4fc9-87d7-9dc306655ac7](.artifacts/records/project__acceptance/rec-f869e403-b8c6-4fc9-87d7-9dc306655ac7.md))_

### Check
- **skill-task-worktree-r10**: rec-f869e403-b8c6-4fc9-87d7-9dc306655ac7; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-21bb8566-0502-4a09-97e1-850716895aa6](.artifacts/records/project__check-run/rec-21bb8566-0502-4a09-97e1-850716895aa6.md))_
- **skill-task-worktree-r10**: rec-f869e403-b8c6-4fc9-87d7-9dc306655ac7; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-49d3cc37-cf51-4672-8b94-fc675f1fa454](.artifacts/records/project__check-run/rec-49d3cc37-cf51-4672-8b94-fc675f1fa454.md))_
- **skill-task-worktree-r10**: rec-f869e403-b8c6-4fc9-87d7-9dc306655ac7; dirty; fail; tdd _(id: [rec-6e97157b-1b9c-4242-8025-e48d881261d5](.artifacts/records/project__check-run/rec-6e97157b-1b9c-4242-8025-e48d881261d5.md))_
- **skill-task-worktree-r10**: rec-f869e403-b8c6-4fc9-87d7-9dc306655ac7; dirty; fail; tdd _(id: [rec-82a30c01-765b-44e9-8511-803508de4f51](.artifacts/records/project__check-run/rec-82a30c01-765b-44e9-8511-803508de4f51.md))_
- **skill-task-worktree-r10**: rec-f869e403-b8c6-4fc9-87d7-9dc306655ac7; dirty; fail; tdd _(id: [rec-db22c554-37b8-47e3-8914-647f46759ef9](.artifacts/records/project__check-run/rec-db22c554-37b8-47e3-8914-647f46759ef9.md))_

## skill-task-worktree-r11

### Acceptance
- **skill-task-worktree-r11**: R11; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r11_conflict_leaves_that_conflict_unresolved -q --tb=short _(id: [rec-d3795838-1047-40f0-ad9b-a8523c5ca6c2](.artifacts/records/project__acceptance/rec-d3795838-1047-40f0-ad9b-a8523c5ca6c2.md))_

### Check
- **skill-task-worktree-r11**: rec-d3795838-1047-40f0-ad9b-a8523c5ca6c2; dirty; fail; tdd _(id: [rec-2baf627f-eba5-4ede-b2f7-dd5e34b443b7](.artifacts/records/project__check-run/rec-2baf627f-eba5-4ede-b2f7-dd5e34b443b7.md))_
- **skill-task-worktree-r11**: rec-d3795838-1047-40f0-ad9b-a8523c5ca6c2; dirty; fail; tdd _(id: [rec-342581f7-ccc0-44f3-ab4f-9e8c882a52a4](.artifacts/records/project__check-run/rec-342581f7-ccc0-44f3-ab4f-9e8c882a52a4.md))_
- **skill-task-worktree-r11**: rec-d3795838-1047-40f0-ad9b-a8523c5ca6c2; dirty; fail; tdd _(id: [rec-41f6c08f-71c9-4e28-ad7a-7f2746e4e1bb](.artifacts/records/project__check-run/rec-41f6c08f-71c9-4e28-ad7a-7f2746e4e1bb.md))_
- **skill-task-worktree-r11**: rec-d3795838-1047-40f0-ad9b-a8523c5ca6c2; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-540a7cb8-cb63-4ea6-93a1-79d868e76a3f](.artifacts/records/project__check-run/rec-540a7cb8-cb63-4ea6-93a1-79d868e76a3f.md))_
- **skill-task-worktree-r11**: rec-d3795838-1047-40f0-ad9b-a8523c5ca6c2; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-5f7c1061-9fa6-422b-827d-34e93efe915d](.artifacts/records/project__check-run/rec-5f7c1061-9fa6-422b-827d-34e93efe915d.md))_

## skill-task-worktree-r12

### Acceptance
- **skill-task-worktree-r12**: R12; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r12_conflict_opens_a_blocking_continuity_question_on_the_effort -q --tb=short _(id: [rec-337eff4c-04fb-4528-a38d-43cfb332a3e1](.artifacts/records/project__acceptance/rec-337eff4c-04fb-4528-a38d-43cfb332a3e1.md))_

### Check
- **skill-task-worktree-r12**: rec-337eff4c-04fb-4528-a38d-43cfb332a3e1; dirty; fail; tdd _(id: [rec-3c903a6e-bf4c-451f-90d4-73c951c6af3c](.artifacts/records/project__check-run/rec-3c903a6e-bf4c-451f-90d4-73c951c6af3c.md))_
- **skill-task-worktree-r12**: rec-337eff4c-04fb-4528-a38d-43cfb332a3e1; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-3ef03313-d04a-4407-b398-1f7391966ab6](.artifacts/records/project__check-run/rec-3ef03313-d04a-4407-b398-1f7391966ab6.md))_
- **skill-task-worktree-r12**: rec-337eff4c-04fb-4528-a38d-43cfb332a3e1; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-b4d74256-f045-44af-817b-b99540f66415](.artifacts/records/project__check-run/rec-b4d74256-f045-44af-817b-b99540f66415.md))_
- **skill-task-worktree-r12**: rec-337eff4c-04fb-4528-a38d-43cfb332a3e1; dirty; fail; tdd _(id: [rec-b5c4e42c-12e6-4580-bbc8-1ed6cd856693](.artifacts/records/project__check-run/rec-b5c4e42c-12e6-4580-bbc8-1ed6cd856693.md))_
- **skill-task-worktree-r12**: rec-337eff4c-04fb-4528-a38d-43cfb332a3e1; dirty; fail; tdd _(id: [rec-fb0d5197-2e9c-4ed7-b5ab-622d5e21fb8d](.artifacts/records/project__check-run/rec-fb0d5197-2e9c-4ed7-b5ab-622d5e21fb8d.md))_

## skill-task-worktree-r13

### Acceptance
- **skill-task-worktree-r13**: R13; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r13_conflict_does_not_start_the_next_wave -q --tb=short _(id: [rec-e2d33f8f-465d-4c3a-9cae-fa60fb219f3c](.artifacts/records/project__acceptance/rec-e2d33f8f-465d-4c3a-9cae-fa60fb219f3c.md))_

### Check
- **skill-task-worktree-r13**: rec-e2d33f8f-465d-4c3a-9cae-fa60fb219f3c; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-0bb7b605-4f84-49cf-832f-99939c0c49f5](.artifacts/records/project__check-run/rec-0bb7b605-4f84-49cf-832f-99939c0c49f5.md))_
- **skill-task-worktree-r13**: rec-e2d33f8f-465d-4c3a-9cae-fa60fb219f3c; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-4f4e3028-0c80-40c3-8b59-b04d06422ccc](.artifacts/records/project__check-run/rec-4f4e3028-0c80-40c3-8b59-b04d06422ccc.md))_
- **skill-task-worktree-r13**: rec-e2d33f8f-465d-4c3a-9cae-fa60fb219f3c; dirty; fail; tdd _(id: [rec-96128fdb-cd4b-4996-87c9-c3b7de91dda9](.artifacts/records/project__check-run/rec-96128fdb-cd4b-4996-87c9-c3b7de91dda9.md))_
- **skill-task-worktree-r13**: rec-e2d33f8f-465d-4c3a-9cae-fa60fb219f3c; dirty; fail; tdd _(id: [rec-ccff30bd-f86b-4c6f-b95b-a642633189ed](.artifacts/records/project__check-run/rec-ccff30bd-f86b-4c6f-b95b-a642633189ed.md))_
- **skill-task-worktree-r13**: rec-e2d33f8f-465d-4c3a-9cae-fa60fb219f3c; dirty; fail; tdd _(id: [rec-f5771dcb-5302-402b-af67-014d1a293c1b](.artifacts/records/project__check-run/rec-f5771dcb-5302-402b-af67-014d1a293c1b.md))_

## skill-task-worktree-r14

### Acceptance
- **skill-task-worktree-r14**: R14; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r14_redispatch_reuses_the_task_branch -q --tb=short _(id: [rec-a456a15c-89ba-47a8-8ed5-3fa7658c76e6](.artifacts/records/project__acceptance/rec-a456a15c-89ba-47a8-8ed5-3fa7658c76e6.md))_

### Check
- **skill-task-worktree-r14**: rec-a456a15c-89ba-47a8-8ed5-3fa7658c76e6; dirty; fail; tdd _(id: [rec-4c293747-0c26-4d1a-8db7-f4ced0533a66](.artifacts/records/project__check-run/rec-4c293747-0c26-4d1a-8db7-f4ced0533a66.md))_
- **skill-task-worktree-r14**: rec-a456a15c-89ba-47a8-8ed5-3fa7658c76e6; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-a0ca9c78-e1f3-42c2-a266-8e57ded83242](.artifacts/records/project__check-run/rec-a0ca9c78-e1f3-42c2-a266-8e57ded83242.md))_
- **skill-task-worktree-r14**: rec-a456a15c-89ba-47a8-8ed5-3fa7658c76e6; dirty; fail; tdd _(id: [rec-bccb9b5e-0260-4c2d-b946-e55f7fc81317](.artifacts/records/project__check-run/rec-bccb9b5e-0260-4c2d-b946-e55f7fc81317.md))_
- **skill-task-worktree-r14**: rec-a456a15c-89ba-47a8-8ed5-3fa7658c76e6; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-c334827b-8994-4ee6-afdc-3e06719bad2b](.artifacts/records/project__check-run/rec-c334827b-8994-4ee6-afdc-3e06719bad2b.md))_
- **skill-task-worktree-r14**: rec-a456a15c-89ba-47a8-8ed5-3fa7658c76e6; dirty; fail; tdd _(id: [rec-cfa110cb-1402-4b7b-af1c-806428cf8b81](.artifacts/records/project__check-run/rec-cfa110cb-1402-4b7b-af1c-806428cf8b81.md))_

## skill-task-worktree-r15

### Acceptance
- **skill-task-worktree-r15**: R15; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r15_redispatch_reuses_the_task_worktree -q --tb=short _(id: [rec-4363b7ed-e4f5-43e4-9904-6bdd8adb3305](.artifacts/records/project__acceptance/rec-4363b7ed-e4f5-43e4-9904-6bdd8adb3305.md))_

### Check
- **skill-task-worktree-r15**: rec-4363b7ed-e4f5-43e4-9904-6bdd8adb3305; dirty; fail; tdd _(id: [rec-24452f84-873a-499d-9268-c5e367ce2729](.artifacts/records/project__check-run/rec-24452f84-873a-499d-9268-c5e367ce2729.md))_
- **skill-task-worktree-r15**: rec-4363b7ed-e4f5-43e4-9904-6bdd8adb3305; dirty; fail; tdd _(id: [rec-3a4bc253-e263-45c6-b4c6-411694c5eec5](.artifacts/records/project__check-run/rec-3a4bc253-e263-45c6-b4c6-411694c5eec5.md))_
- **skill-task-worktree-r15**: rec-4363b7ed-e4f5-43e4-9904-6bdd8adb3305; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-65a011e3-63c7-4171-901b-b286bf87313a](.artifacts/records/project__check-run/rec-65a011e3-63c7-4171-901b-b286bf87313a.md))_
- **skill-task-worktree-r15**: rec-4363b7ed-e4f5-43e4-9904-6bdd8adb3305; dirty; fail; tdd _(id: [rec-869edeea-7ac1-4b46-a639-066706445dde](.artifacts/records/project__check-run/rec-869edeea-7ac1-4b46-a639-066706445dde.md))_
- **skill-task-worktree-r15**: rec-4363b7ed-e4f5-43e4-9904-6bdd8adb3305; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-bb550706-e242-425d-8f1b-bcdf01b988f5](.artifacts/records/project__check-run/rec-bb550706-e242-425d-8f1b-bcdf01b988f5.md))_

## skill-task-worktree-r16

### Acceptance
- **skill-task-worktree-r16**: R16; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r16_redispatch_merges_the_phase_tip_into_the_task_branch -q --tb=short _(id: [rec-4591df96-ffef-4618-8e6e-07d98f9b4347](.artifacts/records/project__acceptance/rec-4591df96-ffef-4618-8e6e-07d98f9b4347.md))_

### Check
- **skill-task-worktree-r16**: rec-4591df96-ffef-4618-8e6e-07d98f9b4347; dirty; fail; tdd _(id: [rec-0a0c49cb-a31c-4ff7-bcf4-bef2820794d7](.artifacts/records/project__check-run/rec-0a0c49cb-a31c-4ff7-bcf4-bef2820794d7.md))_
- **skill-task-worktree-r16**: rec-4591df96-ffef-4618-8e6e-07d98f9b4347; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-40ac5943-35f2-40f6-ad62-f8c9946559c5](.artifacts/records/project__check-run/rec-40ac5943-35f2-40f6-ad62-f8c9946559c5.md))_
- **skill-task-worktree-r16**: rec-4591df96-ffef-4618-8e6e-07d98f9b4347; dirty; fail; tdd _(id: [rec-4895e141-9b1a-4713-abe6-fa935bdf706c](.artifacts/records/project__check-run/rec-4895e141-9b1a-4713-abe6-fa935bdf706c.md))_
- **skill-task-worktree-r16**: rec-4591df96-ffef-4618-8e6e-07d98f9b4347; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-6a1dfa67-10f5-4a63-abc5-dbd7da159b77](.artifacts/records/project__check-run/rec-6a1dfa67-10f5-4a63-abc5-dbd7da159b77.md))_
- **skill-task-worktree-r16**: rec-4591df96-ffef-4618-8e6e-07d98f9b4347; dirty; fail; tdd _(id: [rec-a78727c0-eafb-416f-9d32-2c1feeca3f5a](.artifacts/records/project__check-run/rec-a78727c0-eafb-416f-9d32-2c1feeca3f5a.md))_

## skill-task-worktree-r17

### Acceptance
- **skill-task-worktree-r17**: R17; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r17_verification_task_is_dispatched_in_the_phase_worktree -q --tb=short _(id: [rec-dea088d8-3b6d-448b-8754-7275de84ad54](.artifacts/records/project__acceptance/rec-dea088d8-3b6d-448b-8754-7275de84ad54.md))_

### Check
- **skill-task-worktree-r17**: rec-dea088d8-3b6d-448b-8754-7275de84ad54; dirty; fail; tdd _(id: [rec-2fece5d7-345c-47ab-b223-e9787ee25a6a](.artifacts/records/project__check-run/rec-2fece5d7-345c-47ab-b223-e9787ee25a6a.md))_
- **skill-task-worktree-r17**: rec-dea088d8-3b6d-448b-8754-7275de84ad54; dirty; fail; tdd _(id: [rec-68032fdb-06c6-4397-8915-952c38798dc6](.artifacts/records/project__check-run/rec-68032fdb-06c6-4397-8915-952c38798dc6.md))_
- **skill-task-worktree-r17**: rec-dea088d8-3b6d-448b-8754-7275de84ad54; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-a19d9e86-3f70-4f6f-8ccd-bf6bd7191288](.artifacts/records/project__check-run/rec-a19d9e86-3f70-4f6f-8ccd-bf6bd7191288.md))_
- **skill-task-worktree-r17**: rec-dea088d8-3b6d-448b-8754-7275de84ad54; dirty; fail; tdd _(id: [rec-b55edc78-8093-403a-992f-3ff1e981756d](.artifacts/records/project__check-run/rec-b55edc78-8093-403a-992f-3ff1e981756d.md))_
- **skill-task-worktree-r17**: rec-dea088d8-3b6d-448b-8754-7275de84ad54; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-d02ae3c9-b978-4c33-807f-9944584cde6b](.artifacts/records/project__check-run/rec-d02ae3c9-b978-4c33-807f-9944584cde6b.md))_

## skill-task-worktree-r18

### Acceptance
- **skill-task-worktree-r18**: R18; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r18_no_task_branch_for_the_verification_task -q --tb=short _(id: [rec-88951356-0702-4f6d-91e8-b76a478ba443](.artifacts/records/project__acceptance/rec-88951356-0702-4f6d-91e8-b76a478ba443.md))_

### Check
- **skill-task-worktree-r18**: rec-88951356-0702-4f6d-91e8-b76a478ba443; dirty; fail; tdd _(id: [rec-3ab8edee-3c53-44e6-869c-1577971f5c08](.artifacts/records/project__check-run/rec-3ab8edee-3c53-44e6-869c-1577971f5c08.md))_
- **skill-task-worktree-r18**: rec-88951356-0702-4f6d-91e8-b76a478ba443; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-4171ba65-bbdf-4175-8b7b-2f281c8dc6ee](.artifacts/records/project__check-run/rec-4171ba65-bbdf-4175-8b7b-2f281c8dc6ee.md))_
- **skill-task-worktree-r18**: rec-88951356-0702-4f6d-91e8-b76a478ba443; dirty; fail; tdd _(id: [rec-488ca6a0-f20d-432c-8281-fd782a9e4996](.artifacts/records/project__check-run/rec-488ca6a0-f20d-432c-8281-fd782a9e4996.md))_
- **skill-task-worktree-r18**: rec-88951356-0702-4f6d-91e8-b76a478ba443; dirty; fail; tdd _(id: [rec-58157bd2-862b-4e4e-93c6-12ff16a7978f](.artifacts/records/project__check-run/rec-58157bd2-862b-4e4e-93c6-12ff16a7978f.md))_
- **skill-task-worktree-r18**: rec-88951356-0702-4f6d-91e8-b76a478ba443; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-e6b0ceb1-e26e-4f98-ad2f-a81a45eb1b46](.artifacts/records/project__check-run/rec-e6b0ceb1-e26e-4f98-ad2f-a81a45eb1b46.md))_

## skill-task-worktree-r19

### Acceptance
- **skill-task-worktree-r19**: R19; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r19_no_task_worktree_for_the_verification_task -q --tb=short _(id: [rec-3163b04c-0b19-49de-8055-7eadd147518f](.artifacts/records/project__acceptance/rec-3163b04c-0b19-49de-8055-7eadd147518f.md))_

### Check
- **skill-task-worktree-r19**: rec-3163b04c-0b19-49de-8055-7eadd147518f; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-388224b6-835f-4408-89e9-042264f472da](.artifacts/records/project__check-run/rec-388224b6-835f-4408-89e9-042264f472da.md))_
- **skill-task-worktree-r19**: rec-3163b04c-0b19-49de-8055-7eadd147518f; dirty; fail; tdd _(id: [rec-74a7f953-1bd0-4f3f-99e3-82cc6093ea3d](.artifacts/records/project__check-run/rec-74a7f953-1bd0-4f3f-99e3-82cc6093ea3d.md))_
- **skill-task-worktree-r19**: rec-3163b04c-0b19-49de-8055-7eadd147518f; dirty; fail; tdd _(id: [rec-79e4da84-2c88-4cbf-ab99-340bf42b3bc7](.artifacts/records/project__check-run/rec-79e4da84-2c88-4cbf-ab99-340bf42b3bc7.md))_
- **skill-task-worktree-r19**: rec-3163b04c-0b19-49de-8055-7eadd147518f; dirty; fail; tdd _(id: [rec-c9d1c057-51c4-4b9f-a365-fc356e79f1f3](.artifacts/records/project__check-run/rec-c9d1c057-51c4-4b9f-a365-fc356e79f1f3.md))_
- **skill-task-worktree-r19**: rec-3163b04c-0b19-49de-8055-7eadd147518f; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-c9ed8f1a-383a-4b2f-b87a-3846740c76e8](.artifacts/records/project__check-run/rec-c9ed8f1a-383a-4b2f-b87a-3846740c76e8.md))_

## skill-task-worktree-r2

### Acceptance
- **skill-task-worktree-r2**: R2; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r2_landing_adds_a_task_worktree_except_the_verification_task -q --tb=short _(id: [rec-1ec290b8-4b8c-4d2d-afea-035c8c53235e](.artifacts/records/project__acceptance/rec-1ec290b8-4b8c-4d2d-afea-035c8c53235e.md))_

### Check
- **skill-task-worktree-r2**: rec-1ec290b8-4b8c-4d2d-afea-035c8c53235e; dirty; fail; tdd _(id: [rec-55beba58-5139-43b4-867c-f4ad1c868c86](.artifacts/records/project__check-run/rec-55beba58-5139-43b4-867c-f4ad1c868c86.md))_
- **skill-task-worktree-r2**: rec-1ec290b8-4b8c-4d2d-afea-035c8c53235e; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-64d6d8ce-fdd2-4553-b573-9868b68b6f59](.artifacts/records/project__check-run/rec-64d6d8ce-fdd2-4553-b573-9868b68b6f59.md))_
- **skill-task-worktree-r2**: rec-1ec290b8-4b8c-4d2d-afea-035c8c53235e; dirty; fail; tdd _(id: [rec-726d05a4-5d05-416b-934f-683797919f55](.artifacts/records/project__check-run/rec-726d05a4-5d05-416b-934f-683797919f55.md))_
- **skill-task-worktree-r2**: rec-1ec290b8-4b8c-4d2d-afea-035c8c53235e; dirty; fail; tdd _(id: [rec-84de1486-7128-41cf-93be-1f83dc0e9422](.artifacts/records/project__check-run/rec-84de1486-7128-41cf-93be-1f83dc0e9422.md))_
- **skill-task-worktree-r2**: rec-1ec290b8-4b8c-4d2d-afea-035c8c53235e; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-d081541e-42d1-4eb7-bddb-008fa2521174](.artifacts/records/project__check-run/rec-d081541e-42d1-4eb7-bddb-008fa2521174.md))_

## skill-task-worktree-r20

### Acceptance
- **skill-task-worktree-r20**: R20; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r20_absent_landing_does_not_create_a_task_branch tests/test_execute_landing.py::test_landing_worktree_confines_code_and_keeps_the_store_on_the_primary_checkout tests/test_execute_landing.py::test_gate_commits_the_phase_branch_merges_to_main_and_commits_the_store tests/test_execute_landing.py::test_push_only_when_it_is_a_human_stop tests/test_execute_landing.py::test_missing_landing_section_stays_in_the_current_checkout -q --tb=short _(id: [rec-6f21fdb6-ed88-4965-a020-b9e9b386f343](.artifacts/records/project__acceptance/rec-6f21fdb6-ed88-4965-a020-b9e9b386f343.md))_

### Check
- **skill-task-worktree-r20**: rec-6f21fdb6-ed88-4965-a020-b9e9b386f343; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-0a187b64-4ce1-475c-949d-114b9146fd8a](.artifacts/records/project__check-run/rec-0a187b64-4ce1-475c-949d-114b9146fd8a.md))_
- **skill-task-worktree-r20**: rec-6f21fdb6-ed88-4965-a020-b9e9b386f343; dirty; fail; tdd _(id: [rec-0ce05df9-4fec-49fa-80ec-5a82c1d5781d](.artifacts/records/project__check-run/rec-0ce05df9-4fec-49fa-80ec-5a82c1d5781d.md))_
- **skill-task-worktree-r20**: rec-6f21fdb6-ed88-4965-a020-b9e9b386f343; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-2d1ca6f3-aadb-42b1-af31-72373477011b](.artifacts/records/project__check-run/rec-2d1ca6f3-aadb-42b1-af31-72373477011b.md))_
- **skill-task-worktree-r20**: rec-6f21fdb6-ed88-4965-a020-b9e9b386f343; dirty; fail; tdd _(id: [rec-93e316e1-f879-4696-8605-3f562e743381](.artifacts/records/project__check-run/rec-93e316e1-f879-4696-8605-3f562e743381.md))_
- **skill-task-worktree-r20**: rec-6f21fdb6-ed88-4965-a020-b9e9b386f343; dirty; fail; tdd _(id: [rec-a99f307d-89d0-4423-9b2a-067fd8abbe93](.artifacts/records/project__check-run/rec-a99f307d-89d0-4423-9b2a-067fd8abbe93.md))_

## skill-task-worktree-r21

### Acceptance
- **skill-task-worktree-r21**: R21; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r21_absent_landing_does_not_add_a_task_worktree -q --tb=short _(id: [rec-d944f332-01b4-4677-8037-04da1b64e433](.artifacts/records/project__acceptance/rec-d944f332-01b4-4677-8037-04da1b64e433.md))_

### Check
- **skill-task-worktree-r21**: rec-d944f332-01b4-4677-8037-04da1b64e433; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-4c8f6f6c-824d-423a-8362-99a9b0672a35](.artifacts/records/project__check-run/rec-4c8f6f6c-824d-423a-8362-99a9b0672a35.md))_
- **skill-task-worktree-r21**: rec-d944f332-01b4-4677-8037-04da1b64e433; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-5c3bb6af-c002-495b-a1da-5b4ae3c7ed8e](.artifacts/records/project__check-run/rec-5c3bb6af-c002-495b-a1da-5b4ae3c7ed8e.md))_
- **skill-task-worktree-r21**: rec-d944f332-01b4-4677-8037-04da1b64e433; dirty; fail; tdd _(id: [rec-7515e30f-9a7d-4e5f-9d2b-ca77a8a98039](.artifacts/records/project__check-run/rec-7515e30f-9a7d-4e5f-9d2b-ca77a8a98039.md))_
- **skill-task-worktree-r21**: rec-d944f332-01b4-4677-8037-04da1b64e433; dirty; fail; tdd _(id: [rec-d3aa044b-87ab-497e-a69f-01fc1c46491b](.artifacts/records/project__check-run/rec-d3aa044b-87ab-497e-a69f-01fc1c46491b.md))_
- **skill-task-worktree-r21**: rec-d944f332-01b4-4677-8037-04da1b64e433; dirty; fail; tdd _(id: [rec-e2ae828e-7c15-4e7d-bef4-12e800aa9713](.artifacts/records/project__check-run/rec-e2ae828e-7c15-4e7d-bef4-12e800aa9713.md))_

## skill-task-worktree-r24

### Acceptance
- **skill-task-worktree-r24**: R24; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r24_orientation_names_the_task_worktree_as_the_write_root -q --tb=short _(id: [rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2](.artifacts/records/project__acceptance/rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2.md))_

### Check
- **skill-task-worktree-r24**: rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-144175f3-eb39-480f-87b1-031e67685bef](.artifacts/records/project__check-run/rec-144175f3-eb39-480f-87b1-031e67685bef.md))_
- **skill-task-worktree-r24**: rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2; dirty; fail; tdd _(id: [rec-17aa2640-eee0-4591-bed8-2c1cf8a60919](.artifacts/records/project__check-run/rec-17aa2640-eee0-4591-bed8-2c1cf8a60919.md))_
- **skill-task-worktree-r24**: rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2; dirty; fail; tdd _(id: [rec-64ad7ef3-6980-4f5f-ab08-1feaf527b080](.artifacts/records/project__check-run/rec-64ad7ef3-6980-4f5f-ab08-1feaf527b080.md))_
- **skill-task-worktree-r24**: rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-88889c7e-5fa4-4afe-822e-c138e7a636bf](.artifacts/records/project__check-run/rec-88889c7e-5fa4-4afe-822e-c138e7a636bf.md))_
- **skill-task-worktree-r24**: rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2; dirty; fail; tdd _(id: [rec-91b4b740-edbe-4b26-aefb-528dfca19488](.artifacts/records/project__check-run/rec-91b4b740-edbe-4b26-aefb-528dfca19488.md))_
- **skill-task-worktree-r24**: rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2; dirty; fail; tdd _(id: [rec-d949d285-1bf4-4dab-850d-8e868462c05d](.artifacts/records/project__check-run/rec-d949d285-1bf4-4dab-850d-8e868462c05d.md))_

## skill-task-worktree-r25

### Acceptance
- **skill-task-worktree-r25**: R25; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r25_orientation_does_not_tell_the_executor_to_avoid_git_add -q --tb=short _(id: [rec-33bf5b0b-95af-427f-b5ee-cf19266d4d47](.artifacts/records/project__acceptance/rec-33bf5b0b-95af-427f-b5ee-cf19266d4d47.md))_

### Check
- **skill-task-worktree-r25**: rec-33bf5b0b-95af-427f-b5ee-cf19266d4d47; dirty; fail; tdd _(id: [rec-304faeaf-14d5-4496-8293-6b86171d1fcb](.artifacts/records/project__check-run/rec-304faeaf-14d5-4496-8293-6b86171d1fcb.md))_
- **skill-task-worktree-r25**: rec-33bf5b0b-95af-427f-b5ee-cf19266d4d47; dirty; fail; tdd _(id: [rec-7a5551c0-91ee-4845-be65-8a6307345429](.artifacts/records/project__check-run/rec-7a5551c0-91ee-4845-be65-8a6307345429.md))_
- **skill-task-worktree-r25**: rec-33bf5b0b-95af-427f-b5ee-cf19266d4d47; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-8d0830a4-3771-44fa-9ca2-b45761e4decf](.artifacts/records/project__check-run/rec-8d0830a4-3771-44fa-9ca2-b45761e4decf.md))_
- **skill-task-worktree-r25**: rec-33bf5b0b-95af-427f-b5ee-cf19266d4d47; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-b028c61e-2147-4256-a12f-dc9e8c0058a5](.artifacts/records/project__check-run/rec-b028c61e-2147-4256-a12f-dc9e8c0058a5.md))_
- **skill-task-worktree-r25**: rec-33bf5b0b-95af-427f-b5ee-cf19266d4d47; dirty; fail; tdd _(id: [rec-c13bf238-9134-4344-8ae7-fbb04897d4ec](.artifacts/records/project__check-run/rec-c13bf238-9134-4344-8ae7-fbb04897d4ec.md))_

## skill-task-worktree-r26

### Acceptance
- **skill-task-worktree-r26**: R26; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r26_no_empty_commit_when_a_task_has_nothing_to_commit -q --tb=short _(id: [rec-e17c2106-cfde-42f1-a3b9-9a874f4c1292](.artifacts/records/project__acceptance/rec-e17c2106-cfde-42f1-a3b9-9a874f4c1292.md))_

### Check
- **skill-task-worktree-r26**: rec-e17c2106-cfde-42f1-a3b9-9a874f4c1292; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-01db6df7-7eac-4380-a097-aeb00f3611db](.artifacts/records/project__check-run/rec-01db6df7-7eac-4380-a097-aeb00f3611db.md))_
- **skill-task-worktree-r26**: rec-e17c2106-cfde-42f1-a3b9-9a874f4c1292; dirty; fail; tdd _(id: [rec-120dc2a9-89cb-4a3d-a4a1-98b8fd21c53c](.artifacts/records/project__check-run/rec-120dc2a9-89cb-4a3d-a4a1-98b8fd21c53c.md))_
- **skill-task-worktree-r26**: rec-e17c2106-cfde-42f1-a3b9-9a874f4c1292; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-514e39ba-12d2-45e5-9142-1a5fa1b17ebf](.artifacts/records/project__check-run/rec-514e39ba-12d2-45e5-9142-1a5fa1b17ebf.md))_
- **skill-task-worktree-r26**: rec-e17c2106-cfde-42f1-a3b9-9a874f4c1292; dirty; fail; tdd _(id: [rec-759b5224-85f6-49f2-b243-01b53cd6c25d](.artifacts/records/project__check-run/rec-759b5224-85f6-49f2-b243-01b53cd6c25d.md))_
- **skill-task-worktree-r26**: rec-e17c2106-cfde-42f1-a3b9-9a874f4c1292; dirty; fail; tdd _(id: [rec-e6ed0abd-bc12-44c6-aa54-ec99555e0912](.artifacts/records/project__check-run/rec-e6ed0abd-bc12-44c6-aa54-ec99555e0912.md))_

## skill-task-worktree-r27

### Acceptance
- **skill-task-worktree-r27**: R27; tdd; workflow-loop; python3 -m pytest tests/test_task_commit.py::test_r27_per_task_commit_path_is_the_task_worktree -q --tb=short _(id: [rec-1848327f-f58b-4e72-aeb3-ae082358e7c4](.artifacts/records/project__acceptance/rec-1848327f-f58b-4e72-aeb3-ae082358e7c4.md))_

### Check
- **skill-task-worktree-r27**: rec-1848327f-f58b-4e72-aeb3-ae082358e7c4; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-097aabe8-fcb9-4332-9728-54787f073a09](.artifacts/records/project__check-run/rec-097aabe8-fcb9-4332-9728-54787f073a09.md))_
- **skill-task-worktree-r27**: rec-1848327f-f58b-4e72-aeb3-ae082358e7c4; dirty; fail; tdd _(id: [rec-1fb77c37-3c2e-426e-9c35-ce0ea9775825](.artifacts/records/project__check-run/rec-1fb77c37-3c2e-426e-9c35-ce0ea9775825.md))_
- **skill-task-worktree-r27**: rec-1848327f-f58b-4e72-aeb3-ae082358e7c4; dirty; fail; tdd _(id: [rec-2c9aa2bf-ccce-422e-afcc-a094c9c81966](.artifacts/records/project__check-run/rec-2c9aa2bf-ccce-422e-afcc-a094c9c81966.md))_
- **skill-task-worktree-r27**: rec-1848327f-f58b-4e72-aeb3-ae082358e7c4; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-2f117514-3394-4fcc-8b10-5a07f3a34102](.artifacts/records/project__check-run/rec-2f117514-3394-4fcc-8b10-5a07f3a34102.md))_
- **skill-task-worktree-r27**: rec-1848327f-f58b-4e72-aeb3-ae082358e7c4; dirty; fail; tdd _(id: [rec-cfb6391b-3e72-444a-b203-35c39b273fc4](.artifacts/records/project__check-run/rec-cfb6391b-3e72-444a-b203-35c39b273fc4.md))_

## skill-task-worktree-r3

### Acceptance
- **skill-task-worktree-r3**: R3; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r3_per_task_commit_runs_in_that_task_worktree -q --tb=short _(id: [rec-9978c80a-6e9e-4a29-963c-5cdd28a10718](.artifacts/records/project__acceptance/rec-9978c80a-6e9e-4a29-963c-5cdd28a10718.md))_

### Check
- **skill-task-worktree-r3**: rec-9978c80a-6e9e-4a29-963c-5cdd28a10718; dirty; fail; tdd _(id: [rec-1d36f7d6-c312-4fc3-95a5-957ac1cf1f94](.artifacts/records/project__check-run/rec-1d36f7d6-c312-4fc3-95a5-957ac1cf1f94.md))_
- **skill-task-worktree-r3**: rec-9978c80a-6e9e-4a29-963c-5cdd28a10718; dirty; fail; tdd _(id: [rec-65e15abb-cd2d-40a9-acbb-211342ec39dc](.artifacts/records/project__check-run/rec-65e15abb-cd2d-40a9-acbb-211342ec39dc.md))_
- **skill-task-worktree-r3**: rec-9978c80a-6e9e-4a29-963c-5cdd28a10718; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-6ffa7b96-45a1-4a9e-8d2d-56f7221cb092](.artifacts/records/project__check-run/rec-6ffa7b96-45a1-4a9e-8d2d-56f7221cb092.md))_
- **skill-task-worktree-r3**: rec-9978c80a-6e9e-4a29-963c-5cdd28a10718; dirty; fail; tdd _(id: [rec-cddc0bc7-1cdb-45c6-b60b-b1b724f0ca72](.artifacts/records/project__check-run/rec-cddc0bc7-1cdb-45c6-b60b-b1b724f0ca72.md))_
- **skill-task-worktree-r3**: rec-9978c80a-6e9e-4a29-963c-5cdd28a10718; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-e38123ec-e187-496b-8955-7c2aa1bd14ab](.artifacts/records/project__check-run/rec-e38123ec-e187-496b-8955-7c2aa1bd14ab.md))_

## skill-task-worktree-r4

### Acceptance
- **skill-task-worktree-r4**: R4; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r4_per_task_commit_stages_with_git_add_excluding_artifacts -q --tb=short _(id: [rec-ef7174ed-e462-4077-8933-95f77cac0ce2](.artifacts/records/project__acceptance/rec-ef7174ed-e462-4077-8933-95f77cac0ce2.md))_

### Check
- **skill-task-worktree-r4**: rec-ef7174ed-e462-4077-8933-95f77cac0ce2; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-37401979-e848-487e-b93c-5c6a61b9ca4d](.artifacts/records/project__check-run/rec-37401979-e848-487e-b93c-5c6a61b9ca4d.md))_
- **skill-task-worktree-r4**: rec-ef7174ed-e462-4077-8933-95f77cac0ce2; dirty; fail; tdd _(id: [rec-4eada2d7-bc32-47b8-9f04-47462d630e02](.artifacts/records/project__check-run/rec-4eada2d7-bc32-47b8-9f04-47462d630e02.md))_
- **skill-task-worktree-r4**: rec-ef7174ed-e462-4077-8933-95f77cac0ce2; dirty; fail; tdd _(id: [rec-6fadcb9b-fbba-4327-85bc-7494190f5ea3](.artifacts/records/project__check-run/rec-6fadcb9b-fbba-4327-85bc-7494190f5ea3.md))_
- **skill-task-worktree-r4**: rec-ef7174ed-e462-4077-8933-95f77cac0ce2; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-801f032c-2102-422b-8c07-4f5ac879aa43](.artifacts/records/project__check-run/rec-801f032c-2102-422b-8c07-4f5ac879aa43.md))_
- **skill-task-worktree-r4**: rec-ef7174ed-e462-4077-8933-95f77cac0ce2; dirty; fail; tdd _(id: [rec-a139fb8c-48b1-4654-8379-4792ea33d3af](.artifacts/records/project__check-run/rec-a139fb8c-48b1-4654-8379-4792ea33d3af.md))_

## skill-task-worktree-r5

### Acceptance
- **skill-task-worktree-r5**: R5; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r5_verify_work_runs_in_that_task_worktree -q --tb=short _(id: [rec-0564be4b-8e30-47ec-85f3-55b1301fc0e6](.artifacts/records/project__acceptance/rec-0564be4b-8e30-47ec-85f3-55b1301fc0e6.md))_

### Check
- **skill-task-worktree-r5**: rec-0564be4b-8e30-47ec-85f3-55b1301fc0e6; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-0226fe5d-5bf8-43ec-9c4b-f603f1570610](.artifacts/records/project__check-run/rec-0226fe5d-5bf8-43ec-9c4b-f603f1570610.md))_
- **skill-task-worktree-r5**: rec-0564be4b-8e30-47ec-85f3-55b1301fc0e6; dirty; fail; tdd _(id: [rec-09b9f45a-ef19-492d-875d-fee194fa9149](.artifacts/records/project__check-run/rec-09b9f45a-ef19-492d-875d-fee194fa9149.md))_
- **skill-task-worktree-r5**: rec-0564be4b-8e30-47ec-85f3-55b1301fc0e6; dirty; fail; tdd _(id: [rec-1ce89a7e-88e8-4e81-8ff5-2dc494ff23fd](.artifacts/records/project__check-run/rec-1ce89a7e-88e8-4e81-8ff5-2dc494ff23fd.md))_
- **skill-task-worktree-r5**: rec-0564be4b-8e30-47ec-85f3-55b1301fc0e6; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-3e0c8a73-9302-462a-838b-6207fedfb516](.artifacts/records/project__check-run/rec-3e0c8a73-9302-462a-838b-6207fedfb516.md))_
- **skill-task-worktree-r5**: rec-0564be4b-8e30-47ec-85f3-55b1301fc0e6; dirty; fail; tdd _(id: [rec-a4d5b831-d9ea-44a5-a5ea-d508523caa4c](.artifacts/records/project__check-run/rec-a4d5b831-d9ea-44a5-a5ea-d508523caa4c.md))_

## skill-task-worktree-r6

### Acceptance
- **skill-task-worktree-r6**: R6; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r6_passing_check_run_records_that_task_commit -q --tb=short _(id: [rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b](.artifacts/records/project__acceptance/rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b.md))_

### Check
- **skill-task-worktree-r6**: rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b; dirty; fail; tdd _(id: [rec-13644abe-8f84-4115-a953-97b69c9a47c6](.artifacts/records/project__check-run/rec-13644abe-8f84-4115-a953-97b69c9a47c6.md))_
- **skill-task-worktree-r6**: rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-16902069-68a6-4350-b6fc-e442bcb4c64f](.artifacts/records/project__check-run/rec-16902069-68a6-4350-b6fc-e442bcb4c64f.md))_
- **skill-task-worktree-r6**: rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b; dirty; fail; tdd _(id: [rec-21f49a84-bc5f-4d15-ad1d-8aca034752a4](.artifacts/records/project__check-run/rec-21f49a84-bc5f-4d15-ad1d-8aca034752a4.md))_
- **skill-task-worktree-r6**: rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b; dirty; fail; tdd _(id: [rec-5c8db8bd-77bb-4f94-9ee1-c30cc2e3a202](.artifacts/records/project__check-run/rec-5c8db8bd-77bb-4f94-9ee1-c30cc2e3a202.md))_
- **skill-task-worktree-r6**: rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b; dirty; fail; tdd _(id: [rec-9e1f5d5a-f880-426b-b644-a788fe4b5712](.artifacts/records/project__check-run/rec-9e1f5d5a-f880-426b-b644-a788fe4b5712.md))_
- **skill-task-worktree-r6**: rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-a298e904-3ba3-4807-a3b9-13a997d05ad2](.artifacts/records/project__check-run/rec-a298e904-3ba3-4807-a3b9-13a997d05ad2.md))_

## skill-task-worktree-r7

### Acceptance
- **skill-task-worktree-r7**: R7; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r7_wave_end_merges_passing_task_branches_into_the_phase_branch -q --tb=short _(id: [rec-7e7db37d-173a-4938-93b0-91b2c18a98fc](.artifacts/records/project__acceptance/rec-7e7db37d-173a-4938-93b0-91b2c18a98fc.md))_

### Check
- **skill-task-worktree-r7**: rec-7e7db37d-173a-4938-93b0-91b2c18a98fc; dirty; fail; tdd _(id: [rec-00a42c51-99f2-4a12-9d36-5cd421fab32e](.artifacts/records/project__check-run/rec-00a42c51-99f2-4a12-9d36-5cd421fab32e.md))_
- **skill-task-worktree-r7**: rec-7e7db37d-173a-4938-93b0-91b2c18a98fc; dirty; fail; tdd _(id: [rec-3a02d438-05d6-4fdb-a29a-d3c35a35c8fe](.artifacts/records/project__check-run/rec-3a02d438-05d6-4fdb-a29a-d3c35a35c8fe.md))_
- **skill-task-worktree-r7**: rec-7e7db37d-173a-4938-93b0-91b2c18a98fc; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-63cecf3c-333a-47e3-acc8-a1fa700669f9](.artifacts/records/project__check-run/rec-63cecf3c-333a-47e3-acc8-a1fa700669f9.md))_
- **skill-task-worktree-r7**: rec-7e7db37d-173a-4938-93b0-91b2c18a98fc; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-6b2ac047-d658-4dbe-9d06-34fda1a0e71f](.artifacts/records/project__check-run/rec-6b2ac047-d658-4dbe-9d06-34fda1a0e71f.md))_
- **skill-task-worktree-r7**: rec-7e7db37d-173a-4938-93b0-91b2c18a98fc; dirty; fail; tdd _(id: [rec-c70e89fc-9ed8-444f-aca3-3b4cda521f44](.artifacts/records/project__check-run/rec-c70e89fc-9ed8-444f-aca3-3b4cda521f44.md))_

## skill-task-worktree-r8

### Acceptance
- **skill-task-worktree-r8**: R8; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r8_wave_end_merges_run_in_task_slug_order -q --tb=short _(id: [rec-f9b1ca3f-a5dd-4c48-8b32-b38f4728c9d2](.artifacts/records/project__acceptance/rec-f9b1ca3f-a5dd-4c48-8b32-b38f4728c9d2.md))_

### Check
- **skill-task-worktree-r8**: rec-f9b1ca3f-a5dd-4c48-8b32-b38f4728c9d2; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-2f0d7eea-331a-45da-830d-1b12913224e1](.artifacts/records/project__check-run/rec-2f0d7eea-331a-45da-830d-1b12913224e1.md))_
- **skill-task-worktree-r8**: rec-f9b1ca3f-a5dd-4c48-8b32-b38f4728c9d2; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-4d51e2ff-5502-42b8-b90f-91e3e51f816f](.artifacts/records/project__check-run/rec-4d51e2ff-5502-42b8-b90f-91e3e51f816f.md))_
- **skill-task-worktree-r8**: rec-f9b1ca3f-a5dd-4c48-8b32-b38f4728c9d2; dirty; fail; tdd _(id: [rec-6d51788d-8919-49a8-af23-11ce4652f341](.artifacts/records/project__check-run/rec-6d51788d-8919-49a8-af23-11ce4652f341.md))_
- **skill-task-worktree-r8**: rec-f9b1ca3f-a5dd-4c48-8b32-b38f4728c9d2; dirty; fail; tdd _(id: [rec-b6ce6027-73d7-4ba4-8f92-23a2e174840c](.artifacts/records/project__check-run/rec-b6ce6027-73d7-4ba4-8f92-23a2e174840c.md))_
- **skill-task-worktree-r8**: rec-f9b1ca3f-a5dd-4c48-8b32-b38f4728c9d2; dirty; fail; tdd _(id: [rec-c6923080-da50-4ef1-9586-87a19224ecb9](.artifacts/records/project__check-run/rec-c6923080-da50-4ef1-9586-87a19224ecb9.md))_

## skill-task-worktree-r9

### Acceptance
- **skill-task-worktree-r9**: R9; tdd; workflow-loop; python3 -m pytest tests/test_task_worktrees.py::test_r9_wave_end_integration_does_not_rebase_the_task_branch -q --tb=short _(id: [rec-c1742922-b91e-449a-94bc-9fce443f6d88](.artifacts/records/project__acceptance/rec-c1742922-b91e-449a-94bc-9fce443f6d88.md))_

### Check
- **skill-task-worktree-r9**: rec-c1742922-b91e-449a-94bc-9fce443f6d88; dirty; fail; tdd _(id: [rec-47ed6f0e-bd88-4c2f-b481-8dcff0cdff21](.artifacts/records/project__check-run/rec-47ed6f0e-bd88-4c2f-b481-8dcff0cdff21.md))_
- **skill-task-worktree-r9**: rec-c1742922-b91e-449a-94bc-9fce443f6d88; dirty; fail; tdd _(id: [rec-5a32f90c-a689-4c04-a575-93b2495908e4](.artifacts/records/project__check-run/rec-5a32f90c-a689-4c04-a575-93b2495908e4.md))_
- **skill-task-worktree-r9**: rec-c1742922-b91e-449a-94bc-9fce443f6d88; 55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8; pass; tdd _(id: [rec-7555cd24-7dde-4ab9-b806-f9c3d7aacd52](.artifacts/records/project__check-run/rec-7555cd24-7dde-4ab9-b806-f9c3d7aacd52.md))_
- **skill-task-worktree-r9**: rec-c1742922-b91e-449a-94bc-9fce443f6d88; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; tdd _(id: [rec-8711d599-ded8-4823-ba35-3cd35f99787f](.artifacts/records/project__check-run/rec-8711d599-ded8-4823-ba35-3cd35f99787f.md))_
- **skill-task-worktree-r9**: rec-c1742922-b91e-449a-94bc-9fce443f6d88; dirty; fail; tdd _(id: [rec-fa282884-5604-427b-a8ac-f2e6f35a4888](.artifacts/records/project__check-run/rec-fa282884-5604-427b-a8ac-f2e6f35a4888.md))_

## skills-backlog

### Acceptance
- **skills-backlog**: R2; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-95459f66-4633-441b-a73b-d1aa7b68957a](.artifacts/records/project__acceptance/rec-95459f66-4633-441b-a73b-d1aa7b68957a.md))_

### Check
- **skills-backlog**: rec-95459f66-4633-441b-a73b-d1aa7b68957a; cdb10d65ed56a425a426d5c291c0f5c1a8e69b71; pass; check _(id: [rec-e8570fcb-09a4-4c71-92bd-8d44ce81ac88](.artifacts/records/project__check-run/rec-e8570fcb-09a4-4c71-92bd-8d44ce81ac88.md))_

## skills-backlog-promote

### Acceptance
- **skills-backlog-promote**: R5; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-9dcc1726-0246-424d-a8f7-edd8b8c98ea6](.artifacts/records/project__acceptance/rec-9dcc1726-0246-424d-a8f7-edd8b8c98ea6.md))_

### Check
- **skills-backlog-promote**: rec-9dcc1726-0246-424d-a8f7-edd8b8c98ea6; cdb10d65ed56a425a426d5c291c0f5c1a8e69b71; pass; check _(id: [rec-0821a163-8752-41df-a60a-9421a9b67f50](.artifacts/records/project__check-run/rec-0821a163-8752-41df-a60a-9421a9b67f50.md))_

## skills-claim-handoff

### Acceptance
- **skills-claim-handoff**: R1; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-7d56f650-967d-4bae-8088-7461b40697de](.artifacts/records/project__acceptance/rec-7d56f650-967d-4bae-8088-7461b40697de.md))_

### Check
- **skills-claim-handoff**: rec-7d56f650-967d-4bae-8088-7461b40697de; 464d6813f21f624097f5bfbfb293c8ede2478e49; pass; check _(id: [rec-5c7bb871-de54-4b5e-a73e-09ddd31dd2d6](.artifacts/records/project__check-run/rec-5c7bb871-de54-4b5e-a73e-09ddd31dd2d6.md))_
- **skills-claim-handoff**: rec-7d56f650-967d-4bae-8088-7461b40697de; 464d6813f21f624097f5bfbfb293c8ede2478e49; fail; check _(id: [rec-8b852ada-6abb-48a1-8d2f-aa3c0a885012](.artifacts/records/project__check-run/rec-8b852ada-6abb-48a1-8d2f-aa3c0a885012.md))_
- **skills-claim-handoff**: rec-7d56f650-967d-4bae-8088-7461b40697de; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; check _(id: [rec-cc9d092f-e2bc-423a-8eb6-4aefaca7f2cb](.artifacts/records/project__check-run/rec-cc9d092f-e2bc-423a-8eb6-4aefaca7f2cb.md))_
- **skills-claim-handoff**: rec-7d56f650-967d-4bae-8088-7461b40697de; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-debea87d-e7a9-46b6-8a08-3c48755bb2a0](.artifacts/records/project__check-run/rec-debea87d-e7a9-46b6-8a08-3c48755bb2a0.md))_

## skills-claim-handoff-briefs

### Acceptance
- **skills-claim-handoff-briefs**: R5; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-5b5017ed-6e05-4149-9a16-a76488688d65](.artifacts/records/project__acceptance/rec-5b5017ed-6e05-4149-9a16-a76488688d65.md))_

### Check
- **skills-claim-handoff-briefs**: rec-5b5017ed-6e05-4149-9a16-a76488688d65; 464d6813f21f624097f5bfbfb293c8ede2478e49; fail; check _(id: [rec-09d0839a-84e7-4679-9c65-30d8577b4ffe](.artifacts/records/project__check-run/rec-09d0839a-84e7-4679-9c65-30d8577b4ffe.md))_
- **skills-claim-handoff-briefs**: rec-5b5017ed-6e05-4149-9a16-a76488688d65; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-8c18c7e9-3578-42a3-8774-5c7c1f8a77bb](.artifacts/records/project__check-run/rec-8c18c7e9-3578-42a3-8774-5c7c1f8a77bb.md))_
- **skills-claim-handoff-briefs**: rec-5b5017ed-6e05-4149-9a16-a76488688d65; 464d6813f21f624097f5bfbfb293c8ede2478e49; pass; check _(id: [rec-91dbaed4-4840-46fa-871c-19865088901d](.artifacts/records/project__check-run/rec-91dbaed4-4840-46fa-871c-19865088901d.md))_
- **skills-claim-handoff-briefs**: rec-5b5017ed-6e05-4149-9a16-a76488688d65; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; check _(id: [rec-ef366603-eab6-4e32-b28a-7d5935338fde](.artifacts/records/project__check-run/rec-ef366603-eab6-4e32-b28a-7d5935338fde.md))_

## skills-claim-handoff-one-id

### Acceptance
- **skills-claim-handoff-one-id**: R2; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-9d1ec1a9-0e4c-413e-abd7-3df6a51dd28f](.artifacts/records/project__acceptance/rec-9d1ec1a9-0e4c-413e-abd7-3df6a51dd28f.md))_

### Check
- **skills-claim-handoff-one-id**: rec-9d1ec1a9-0e4c-413e-abd7-3df6a51dd28f; 464d6813f21f624097f5bfbfb293c8ede2478e49; pass; check _(id: [rec-134a33cb-9872-4aa0-be04-bbd8c37d859f](.artifacts/records/project__check-run/rec-134a33cb-9872-4aa0-be04-bbd8c37d859f.md))_
- **skills-claim-handoff-one-id**: rec-9d1ec1a9-0e4c-413e-abd7-3df6a51dd28f; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-2fd60042-8e90-41fb-be20-27c8a22975a2](.artifacts/records/project__check-run/rec-2fd60042-8e90-41fb-be20-27c8a22975a2.md))_
- **skills-claim-handoff-one-id**: rec-9d1ec1a9-0e4c-413e-abd7-3df6a51dd28f; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; check _(id: [rec-34ab2d88-35ed-4a2f-a93b-7f5572b5948e](.artifacts/records/project__check-run/rec-34ab2d88-35ed-4a2f-a93b-7f5572b5948e.md))_
- **skills-claim-handoff-one-id**: rec-9d1ec1a9-0e4c-413e-abd7-3df6a51dd28f; 464d6813f21f624097f5bfbfb293c8ede2478e49; fail; check _(id: [rec-6fa7d816-db16-45aa-a7a4-25cb74145415](.artifacts/records/project__check-run/rec-6fa7d816-db16-45aa-a7a4-25cb74145415.md))_

## skills-claim-handoff-thin

### Acceptance
- **skills-claim-handoff-thin**: R3; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-177d102b-7173-412b-b4c0-2b7608eff04c](.artifacts/records/project__acceptance/rec-177d102b-7173-412b-b4c0-2b7608eff04c.md))_

### Check
- **skills-claim-handoff-thin**: rec-177d102b-7173-412b-b4c0-2b7608eff04c; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-1014b813-85f3-447f-a0c9-115c73d9b077](.artifacts/records/project__check-run/rec-1014b813-85f3-447f-a0c9-115c73d9b077.md))_
- **skills-claim-handoff-thin**: rec-177d102b-7173-412b-b4c0-2b7608eff04c; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; check _(id: [rec-3778b0f7-cda8-4bfa-bc8f-db866a70a821](.artifacts/records/project__check-run/rec-3778b0f7-cda8-4bfa-bc8f-db866a70a821.md))_
- **skills-claim-handoff-thin**: rec-177d102b-7173-412b-b4c0-2b7608eff04c; 464d6813f21f624097f5bfbfb293c8ede2478e49; pass; check _(id: [rec-45128b98-72fc-442f-8919-353f0b8b493a](.artifacts/records/project__check-run/rec-45128b98-72fc-442f-8919-353f0b8b493a.md))_
- **skills-claim-handoff-thin**: rec-177d102b-7173-412b-b4c0-2b7608eff04c; 464d6813f21f624097f5bfbfb293c8ede2478e49; fail; check _(id: [rec-a2467912-996e-4a69-9d83-96817281a7b9](.artifacts/records/project__check-run/rec-a2467912-996e-4a69-9d83-96817281a7b9.md))_

## skills-no-aff-runner

### Acceptance
- **skills-no-aff-runner**: R7; check; workflow-loop; python3 -m pytest tests/test_skill_runner_stamp.py -q _(id: [rec-5a365cb8-9626-4fd4-b02b-c536a920e439](.artifacts/records/project__acceptance/rec-5a365cb8-9626-4fd4-b02b-c536a920e439.md))_

### Check
- **skills-no-aff-runner**: rec-5a365cb8-9626-4fd4-b02b-c536a920e439; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; check _(id: [rec-becb54f0-1e57-4c85-84b2-d26f111a47d4](.artifacts/records/project__check-run/rec-becb54f0-1e57-4c85-84b2-d26f111a47d4.md))_
- **skills-no-aff-runner**: rec-5a365cb8-9626-4fd4-b02b-c536a920e439; 561f9a444b029e5c25752e81737c71009b486404; pass; check _(id: [rec-c5039c71-2780-41f7-a595-4cf82f6aec31](.artifacts/records/project__check-run/rec-c5039c71-2780-41f7-a595-4cf82f6aec31.md))_

## skills-red-first

### Acceptance
- **skills-red-first**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-4106666c-c561-474e-a8fd-4291869e42db](.artifacts/records/project__acceptance/rec-4106666c-c561-474e-a8fd-4291869e42db.md))_

### Check
- **skills-red-first**: rec-4106666c-c561-474e-a8fd-4291869e42db; c14dedbd9ec027e7e79b8eb1508b24d0d65063fc; pass; check _(id: [rec-5b667532-d22d-4457-9115-c3258f78d31b](.artifacts/records/project__check-run/rec-5b667532-d22d-4457-9115-c3258f78d31b.md))_

## spec-model

### Acceptance
- **spec-model**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'phase_screen and tabs' _(id: [rec-7d44b243-444f-4d8f-a42d-2d8bce0f9b6d](.artifacts/records/project__acceptance/rec-7d44b243-444f-4d8f-a42d-2d8bce0f9b6d.md))_

### Check
- **spec-model**: rec-7d44b243-444f-4d8f-a42d-2d8bce0f9b6d; dirty; pass; tdd _(id: [rec-854cf41f-e189-49ae-8b52-af9acd8b9163](.artifacts/records/project__check-run/rec-854cf41f-e189-49ae-8b52-af9acd8b9163.md))_

## spec-model-decisions

### Acceptance
- **spec-model-decisions**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'phase_screen and decision' _(id: [rec-403cd5dd-db5b-4e68-b04b-311599c18032](.artifacts/records/project__acceptance/rec-403cd5dd-db5b-4e68-b04b-311599c18032.md))_

### Check
- **spec-model-decisions**: rec-403cd5dd-db5b-4e68-b04b-311599c18032; dirty; pass; tdd _(id: [rec-f53066b4-a3ab-453b-a694-a647380fda14](.artifacts/records/project__check-run/rec-f53066b4-a3ab-453b-a694-a647380fda14.md))_

## spec-model-simple

### Acceptance
- **spec-model-simple**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'phase_screen and simple' _(id: [rec-0227d202-cb23-4c79-97e0-d7d58c3bb952](.artifacts/records/project__acceptance/rec-0227d202-cb23-4c79-97e0-d7d58c3bb952.md))_

### Check
- **spec-model-simple**: rec-0227d202-cb23-4c79-97e0-d7d58c3bb952; dirty; pass; tdd _(id: [rec-08a91db0-b1de-4066-bcd3-3190cd6967b2](.artifacts/records/project__check-run/rec-08a91db0-b1de-4066-bcd3-3190cd6967b2.md))_

## spec-pager

### Acceptance
- **spec-pager**: R11; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py tests/test_dashboard_pager.py -q -k pager _(id: [rec-05a167b0-042f-4057-b1a0-82dd15d96cbf](.artifacts/records/project__acceptance/rec-05a167b0-042f-4057-b1a0-82dd15d96cbf.md))_

### Check
- **spec-pager**: rec-05a167b0-042f-4057-b1a0-82dd15d96cbf; dirty; pass; tdd _(id: [rec-084043c2-20ee-4927-9e82-c4bf81e31a57](.artifacts/records/project__check-run/rec-084043c2-20ee-4927-9e82-c4bf81e31a57.md))_

## spec-screen

### Acceptance
- **spec-screen**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py -q -k "tab or open or key" _(id: [rec-b864e9ae-db02-462b-ae3a-227f4fdf5f0b](.artifacts/records/project__acceptance/rec-b864e9ae-db02-462b-ae3a-227f4fdf5f0b.md))_

### Check
- **spec-screen**: rec-b864e9ae-db02-462b-ae3a-227f4fdf5f0b; dirty; pass; tdd _(id: [rec-001af826-6491-4f9e-b224-e9be808fe140](.artifacts/records/project__check-run/rec-001af826-6491-4f9e-b224-e9be808fe140.md))_

## spec-screen-content

### Acceptance
- **spec-screen-content**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py -q -k "spec or design or decision or evidence or task or esc" _(id: [rec-fb12c32d-c03a-47d3-8f10-bff1fa09e822](.artifacts/records/project__acceptance/rec-fb12c32d-c03a-47d3-8f10-bff1fa09e822.md))_

### Check
- **spec-screen-content**: rec-fb12c32d-c03a-47d3-8f10-bff1fa09e822; dirty; pass; tdd _(id: [rec-579a1572-3f30-4d70-b1c2-ddf4a1826b5e](.artifacts/records/project__check-run/rec-579a1572-3f30-4d70-b1c2-ddf4a1826b5e.md))_

## spec-screen-pager

### Acceptance
- **spec-screen-pager**: R11; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py -q -k pager _(id: [rec-2c20fcfa-8ea0-4f55-b8ba-0fadcb3fe9b0](.artifacts/records/project__acceptance/rec-2c20fcfa-8ea0-4f55-b8ba-0fadcb3fe9b0.md))_

### Check
- **spec-screen-pager**: rec-2c20fcfa-8ea0-4f55-b8ba-0fadcb3fe9b0; dirty; pass; tdd _(id: [rec-5e7aff7f-586e-4bca-8339-b35891a0eb27](.artifacts/records/project__check-run/rec-5e7aff7f-586e-4bca-8339-b35891a0eb27.md))_

## specify-design

### Acceptance
- **specify-design**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_discuss_skill.py -q _(id: [rec-7683d746-1d29-4de5-bc76-3bdcc678f158](.artifacts/records/project__acceptance/rec-7683d746-1d29-4de5-bc76-3bdcc678f158.md))_

### Check
- **specify-design**: rec-7683d746-1d29-4de5-bc76-3bdcc678f158; dirty; pass; check _(id: [rec-871a92d2-51c9-4d46-babe-ea58c9695e02](.artifacts/records/project__check-run/rec-871a92d2-51c9-4d46-babe-ea58c9695e02.md))_

## status-line-from-snapshot

### Acceptance
- **status-line-from-snapshot**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_status.py -q _(id: [rec-fb5c210c-4e78-42c4-8fb9-f8f585e3f5f8](.artifacts/records/project__acceptance/rec-fb5c210c-4e78-42c4-8fb9-f8f585e3f5f8.md))_

### Check
- **status-line-from-snapshot**: rec-fb5c210c-4e78-42c4-8fb9-f8f585e3f5f8; afd60845e9ffcfcd44d028603b46bdcffadc313a; pass; tdd _(id: [rec-dc270731-1127-4bab-9491-3793856d02ff](.artifacts/records/project__check-run/rec-dc270731-1127-4bab-9491-3793856d02ff.md))_

### Observation
- **status-line-from-snapshot**: dashboard-status listed efforts from the contract dashboard view (grouped by work-item effort) while the app lists efforts with an active goal, so goal-less efforts appeared only in the status line.; dashboard-bugfix _(id: [rec-34b1b626-5692-42e3-87e5-d7c8562d6cf5](.artifacts/records/project__investigation-observation/rec-34b1b626-5692-42e3-87e5-d7c8562d6cf5.md))_

## status-tab-row

### Acceptance
- **status-tab-row**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k tab_row _(id: [rec-ba223a32-d09b-4dd0-9256-101bd04d0ea1](.artifacts/records/project__acceptance/rec-ba223a32-d09b-4dd0-9256-101bd04d0ea1.md))_

### Check
- **status-tab-row**: rec-ba223a32-d09b-4dd0-9256-101bd04d0ea1; ee6469389256ef6d9cf8f8e9c80cd93ef5fcb5aa; pass; tdd _(id: [rec-146b610c-0238-4e4b-9049-a5bb6d569c98](.artifacts/records/project__check-run/rec-146b610c-0238-4e4b-9049-a5bb6d569c98.md))_

## status-tabs

### Acceptance
- **status-tabs**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-5a31e5b1-1af0-4738-bf89-20d16bf3dcaa](.artifacts/records/project__acceptance/rec-5a31e5b1-1af0-4738-bf89-20d16bf3dcaa.md))_

### Check
- **status-tabs**: rec-5a31e5b1-1af0-4738-bf89-20d16bf3dcaa; 75e530c1e06c4584efe45adfad12d926e8843849; pass; check _(id: [rec-0734553d-7a25-4dd7-af9b-6ef24e128a1d](.artifacts/records/project__check-run/rec-0734553d-7a25-4dd7-af9b-6ef24e128a1d.md))_
- **status-tabs**: rec-5a31e5b1-1af0-4738-bf89-20d16bf3dcaa; f6153cee88400795bfb23fb4d0d97e48e69438c9; pass; check _(id: [rec-4bb08f27-39d2-46a7-9b11-69a848dc6b79](.artifacts/records/project__check-run/rec-4bb08f27-39d2-46a7-9b11-69a848dc6b79.md))_

### Finding
- **status-tabs**: status-tabs gap closed: 7 tabs, keys 1-7, left/right and README landed at 75e530c; Execution report rec-10a142d4 and a parent re-run of 116 passing tests at 75e530c; A tab, key or README row from the description is missing; none _(id: [rec-94362ae8-0f01-4ad1-bfcd-cffa426566b8](.artifacts/records/project__finding/rec-94362ae8-0f01-4ad1-bfcd-cffa426566b8.md))_

## status-tabs-fixture

### Acceptance
- **status-tabs-fixture**: R7; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k status_tabs _(id: [rec-a6aabc11-4cb5-47dd-84da-5c01fd225ab5](.artifacts/records/project__acceptance/rec-a6aabc11-4cb5-47dd-84da-5c01fd225ab5.md))_

### Check
- **status-tabs-fixture**: rec-a6aabc11-4cb5-47dd-84da-5c01fd225ab5; dirty; fail; tdd _(id: [rec-08bd8014-2867-4ca6-931c-09db1591de04](.artifacts/records/project__check-run/rec-08bd8014-2867-4ca6-931c-09db1591de04.md))_
- **status-tabs-fixture**: rec-a6aabc11-4cb5-47dd-84da-5c01fd225ab5; 11a147e75daa100a2fbca2202399205b480b42e9; pass; tdd _(id: [rec-925cc63c-17c3-4ab7-8b23-b9c66e8e0c93](.artifacts/records/project__check-run/rec-925cc63c-17c3-4ab7-8b23-b9c66e8e0c93.md))_

## stepper-wrap

### Acceptance
- **stepper-wrap**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k stepper _(id: [rec-c2df3f61-8b0b-44d8-89b3-f3033ebcf9d0](.artifacts/records/project__acceptance/rec-c2df3f61-8b0b-44d8-89b3-f3033ebcf9d0.md))_

### Check
- **stepper-wrap**: rec-c2df3f61-8b0b-44d8-89b3-f3033ebcf9d0; 0ec0a8bb801ff9f528cfd6366bd5c08208282ff4; pass; tdd _(id: [rec-6a6b6040-193a-42e4-b5fc-4bab45d162e8](.artifacts/records/project__check-run/rec-6a6b6040-193a-42e4-b5fc-4bab45d162e8.md))_

### Observation
- **stepper-wrap**: test_stepper_wraps_by_pane_width_and_keeps_glyph_with_label failed 3/10: stepper lines were wider than pane.scrollable_content_region.width. Hypothesis: the status-tab grid wraps, the pane overflows 20 rows, a vertical scrollbar appears after the stepper rendered, narrowing the content region without a pane resize, so EffortPane.on_resize never re-shows.; dashboard-features _(id: [rec-b3951803-56a0-4f76-aefb-68962a329e8a](.artifacts/records/project__investigation-observation/rec-b3951803-56a0-4f76-aefb-68962a329e8a.md))_

## store-client

### Acceptance
- **store-client**: R1; tdd; library-boundary; python3 -m pytest tests/test_store_client.py::test_store_client_create_observation -q _(id: [rec-a3c83cf3-598c-40d5-a651-7c24f3bebeeb](.artifacts/records/project__acceptance/rec-a3c83cf3-598c-40d5-a651-7c24f3bebeeb.md))_

### Check
- **store-client**: rec-a3c83cf3-598c-40d5-a651-7c24f3bebeeb; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; tdd _(id: [rec-3eca21a1-0962-40ba-bf98-35b381276c72](.artifacts/records/project__check-run/rec-3eca21a1-0962-40ba-bf98-35b381276c72.md))_
- **store-client**: rec-a3c83cf3-598c-40d5-a651-7c24f3bebeeb; dirty; fail; tdd _(id: [rec-fe883ac9-dcd6-496f-8813-fb160628bc9a](.artifacts/records/project__check-run/rec-fe883ac9-dcd6-496f-8813-fb160628bc9a.md))_

## store-client-binding

### Acceptance
- **store-client-binding**: R3; tdd; library-boundary; python3 -m pytest tests/test_store_client.py::test_store_client_create_binding -q _(id: [rec-93051b57-d9b6-494a-8230-6decee0ed8d6](.artifacts/records/project__acceptance/rec-93051b57-d9b6-494a-8230-6decee0ed8d6.md))_

### Check
- **store-client-binding**: rec-93051b57-d9b6-494a-8230-6decee0ed8d6; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; tdd _(id: [rec-4c765db4-e281-4cc2-b122-d857204bed35](.artifacts/records/project__check-run/rec-4c765db4-e281-4cc2-b122-d857204bed35.md))_
- **store-client-binding**: rec-93051b57-d9b6-494a-8230-6decee0ed8d6; dirty; fail; tdd _(id: [rec-8543fe1e-83da-4d7c-adb1-8080543885e7](.artifacts/records/project__check-run/rec-8543fe1e-83da-4d7c-adb1-8080543885e7.md))_

## store-client-binding-list

### Acceptance
- **store-client-binding-list**: R4; tdd; library-boundary; python3 -m pytest tests/test_store_client.py::test_store_client_list_bindings -q _(id: [rec-7b352367-9ce2-4514-a6f6-674073d920e4](.artifacts/records/project__acceptance/rec-7b352367-9ce2-4514-a6f6-674073d920e4.md))_

### Check
- **store-client-binding-list**: rec-7b352367-9ce2-4514-a6f6-674073d920e4; dirty; fail; tdd _(id: [rec-ca746c0a-ea3f-478e-b1d3-3b21a0d3fc9b](.artifacts/records/project__check-run/rec-ca746c0a-ea3f-478e-b1d3-3b21a0d3fc9b.md))_
- **store-client-binding-list**: rec-7b352367-9ce2-4514-a6f6-674073d920e4; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; tdd _(id: [rec-f4b45e76-3109-4463-82e7-87179c4cc2e9](.artifacts/records/project__check-run/rec-f4b45e76-3109-4463-82e7-87179c4cc2e9.md))_

## store-client-layout

### Acceptance
- **store-client-layout**: R6; tdd; library-boundary; python3 -m pytest tests/test_store_client_layout.py::test_store_client_layout_allows_library_and_record_types -q _(id: [rec-affed3b8-e9b0-41fa-b2d9-750e40282d87](.artifacts/records/project__acceptance/rec-affed3b8-e9b0-41fa-b2d9-750e40282d87.md))_

### Check
- **store-client-layout**: rec-affed3b8-e9b0-41fa-b2d9-750e40282d87; dirty; fail; tdd _(id: [rec-b2eaee7a-30c3-4d8f-888a-16ba4df1fa4d](.artifacts/records/project__check-run/rec-b2eaee7a-30c3-4d8f-888a-16ba4df1fa4d.md))_
- **store-client-layout**: rec-affed3b8-e9b0-41fa-b2d9-750e40282d87; dirty; fail; tdd _(id: [rec-bcf17c0a-aac2-455c-b8dc-e073da25737e](.artifacts/records/project__check-run/rec-bcf17c0a-aac2-455c-b8dc-e073da25737e.md))_
- **store-client-layout**: rec-affed3b8-e9b0-41fa-b2d9-750e40282d87; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; tdd _(id: [rec-ceff3be6-cd48-4340-83fd-da5143b57091](.artifacts/records/project__check-run/rec-ceff3be6-cd48-4340-83fd-da5143b57091.md))_

## store-client-list

### Acceptance
- **store-client-list**: R2; tdd; library-boundary; python3 -m pytest tests/test_store_client.py::test_store_client_list_observations -q _(id: [rec-a7279718-645e-45da-a1e8-7a02174c6138](.artifacts/records/project__acceptance/rec-a7279718-645e-45da-a1e8-7a02174c6138.md))_

### Check
- **store-client-list**: rec-a7279718-645e-45da-a1e8-7a02174c6138; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; tdd _(id: [rec-73ef36e5-d320-4852-bd62-6d9caab14f44](.artifacts/records/project__check-run/rec-73ef36e5-d320-4852-bd62-6d9caab14f44.md))_
- **store-client-list**: rec-a7279718-645e-45da-a1e8-7a02174c6138; dirty; fail; tdd _(id: [rec-e103b683-32c4-429e-ad3a-95366cfa8046](.artifacts/records/project__check-run/rec-e103b683-32c4-429e-ad3a-95366cfa8046.md))_

## store-client-subprocess

### Acceptance
- **store-client-subprocess**: R5; tdd; library-boundary; python3 -m pytest tests/test_store_client.py::test_store_client_no_adaptive_artifacts_process -q _(id: [rec-73566385-e695-4d8e-87c5-f4a28370eeb4](.artifacts/records/project__acceptance/rec-73566385-e695-4d8e-87c5-f4a28370eeb4.md))_

### Check
- **store-client-subprocess**: rec-73566385-e695-4d8e-87c5-f4a28370eeb4; dirty; fail; tdd _(id: [rec-040f6ae7-a55f-4732-8ba6-9be6344850b7](.artifacts/records/project__check-run/rec-040f6ae7-a55f-4732-8ba6-9be6344850b7.md))_
- **store-client-subprocess**: rec-73566385-e695-4d8e-87c5-f4a28370eeb4; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; tdd _(id: [rec-2decdafc-945e-4735-9f78-c5961707c143](.artifacts/records/project__check-run/rec-2decdafc-945e-4735-9f78-c5961707c143.md))_

## suite-advisory-atomic-claims

### Finding
- **suite-advisory-atomic-claims**: advisory suite fail for atomic-claims-suite; exit 1; assess_routing fixed in 0cdee54; remaining dashboard flakes [size0] related panel and journal pager stub; suite check-run passes at phase head, or human clears; none _(id: [rec-e7d8f857-fbb2-4990-946e-49e9f4f9f83e](.artifacts/records/project__finding/rec-e7d8f857-fbb2-4990-946e-49e9f4f9f83e.md))_

## suite-advisory-claim-witnesses

### Finding
- **suite-advisory-claim-witnesses**: advisory suite fail for claim-witnesses-suite; exit_code=1 failing_node_ids=[tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub]; suite check-run passes at phase head, or human clears; none _(id: [rec-787eda19-6106-46d7-8b5f-ac6c0ca59ddf](.artifacts/records/project__finding/rec-787eda19-6106-46d7-8b5f-ac6c0ca59ddf.md))_

## suite-advisory-oracle-witnesses

### Finding
- **suite-advisory-oracle-witnesses**: advisory suite fail for oracle-witnesses-suite; exit_code=1 failing_node_ids=[tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub]; suite check-run passes at phase head, or human clears; none _(id: [rec-6d403791-1093-4918-8e27-3fd127ae4c4d](.artifacts/records/project__finding/rec-6d403791-1093-4918-8e27-3fd127ae4c4d.md))_

## suite-dashboard

### Acceptance
- **suite-dashboard**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k suite _(id: [rec-2f993e5a-c83f-41e2-823b-8518a7b7d413](.artifacts/records/project__acceptance/rec-2f993e5a-c83f-41e2-823b-8518a7b7d413.md))_

### Check
- **suite-dashboard**: rec-2f993e5a-c83f-41e2-823b-8518a7b7d413; c681c767ae0c0a5888399c7d81df58df7cce6e16; fail; tdd _(id: [rec-263ae5cb-a596-454b-8f19-7eb52908f59a](.artifacts/records/project__check-run/rec-263ae5cb-a596-454b-8f19-7eb52908f59a.md))_
- **suite-dashboard**: rec-2f993e5a-c83f-41e2-823b-8518a7b7d413; 9021805f1b501bb9a35e4133e5f6ad4dfa3d4bd5; pass; tdd _(id: [rec-337a1917-a8b7-4796-9cd5-2fe382bbe547](.artifacts/records/project__check-run/rec-337a1917-a8b7-4796-9cd5-2fe382bbe547.md))_
- **suite-dashboard**: rec-2f993e5a-c83f-41e2-823b-8518a7b7d413; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; tdd _(id: [rec-4c3ab41f-da55-4ccc-9c24-7e041f26a43d](.artifacts/records/project__check-run/rec-4c3ab41f-da55-4ccc-9c24-7e041f26a43d.md))_

## suite-docs-tests

### Acceptance
- **suite-docs-tests**: R5; check; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-918209be-d62b-4b51-ae01-3ebf361b6e6d](.artifacts/records/project__acceptance/rec-918209be-d62b-4b51-ae01-3ebf361b6e6d.md))_

### Check
- **suite-docs-tests**: rec-918209be-d62b-4b51-ae01-3ebf361b6e6d; 846e07f37ff5afe6fe37b1475facaeda210e6945; pass; check _(id: [rec-2f01cbbb-bb20-4796-866e-52a5d97bd4a2](.artifacts/records/project__check-run/rec-2f01cbbb-bb20-4796-866e-52a5d97bd4a2.md))_
- **suite-docs-tests**: rec-918209be-d62b-4b51-ae01-3ebf361b6e6d; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; check _(id: [rec-d56381b3-338b-42c7-977f-0578d48533a6](.artifacts/records/project__check-run/rec-d56381b3-338b-42c7-977f-0578d48533a6.md))_

## suite-engine

### Acceptance
- **suite-engine**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "suite or gate or advisory or policy or mode" _(id: [rec-859d8cde-214e-470d-b492-8896741e83df](.artifacts/records/project__acceptance/rec-859d8cde-214e-470d-b492-8896741e83df.md))_

### Check
- **suite-engine**: rec-859d8cde-214e-470d-b492-8896741e83df; 9021805f1b501bb9a35e4133e5f6ad4dfa3d4bd5; pass; tdd _(id: [rec-19f6eb8f-2f76-4e28-8414-2ce1a32cf7d6](.artifacts/records/project__check-run/rec-19f6eb8f-2f76-4e28-8414-2ce1a32cf7d6.md))_
- **suite-engine**: rec-859d8cde-214e-470d-b492-8896741e83df; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; tdd _(id: [rec-a5c44c73-9e76-4b9b-bd36-70d510371c55](.artifacts/records/project__check-run/rec-a5c44c73-9e76-4b9b-bd36-70d510371c55.md))_
- **suite-engine**: rec-859d8cde-214e-470d-b492-8896741e83df; 3dd633136d118823c9deb72ac929b7f5ec20bdc5; pass; tdd _(id: [rec-bc63d11c-9216-4df7-a2cd-87275fb23d0d](.artifacts/records/project__check-run/rec-bc63d11c-9216-4df7-a2cd-87275fb23d0d.md))_
- **suite-engine**: rec-859d8cde-214e-470d-b492-8896741e83df; c681c767ae0c0a5888399c7d81df58df7cce6e16; pass; tdd _(id: [rec-f59eedf3-2266-4256-9776-968f177a7354](.artifacts/records/project__check-run/rec-f59eedf3-2266-4256-9776-968f177a7354.md))_

## suite-engine-authority

### Acceptance
- **suite-engine-authority**: R8; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_close_batch.py -q -k "tier2 or suite or red_first or red-first or phase_gate" _(id: [rec-f03a59ca-7763-49e7-9670-5e1fdbc30575](.artifacts/records/project__acceptance/rec-f03a59ca-7763-49e7-9670-5e1fdbc30575.md))_

### Check
- **suite-engine-authority**: rec-f03a59ca-7763-49e7-9670-5e1fdbc30575; 9021805f1b501bb9a35e4133e5f6ad4dfa3d4bd5; pass; check _(id: [rec-36795901-c395-4d7e-b97b-3bd9d2248701](.artifacts/records/project__check-run/rec-36795901-c395-4d7e-b97b-3bd9d2248701.md))_
- **suite-engine-authority**: rec-f03a59ca-7763-49e7-9670-5e1fdbc30575; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; check _(id: [rec-af00240f-add5-45cc-8716-ab86e73f2e11](.artifacts/records/project__check-run/rec-af00240f-add5-45cc-8716-ab86e73f2e11.md))_

## table-focus

### Acceptance
- **table-focus**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k focus _(id: [rec-2536ed50-f949-40fe-a914-f283c9633975](.artifacts/records/project__acceptance/rec-2536ed50-f949-40fe-a914-f283c9633975.md))_

### Check
- **table-focus**: rec-2536ed50-f949-40fe-a914-f283c9633975; 1aeb3058d93fa9ac486dd0d6de690d7c0d681388; pass; tdd _(id: [rec-d9988bf2-7166-422b-beb2-94ee365a1a0b](.artifacts/records/project__check-run/rec-d9988bf2-7166-422b-beb2-94ee365a1a0b.md))_

### Observation
- **table-focus**: After an empty status tab hides #tasks, a tab that shows it again leaves app.focused None; arrows do nothing and enter opens row 0. Root cause: select_status_tab never refocuses the table after fill_tasks hides it.; dashboard-bugfix _(id: [rec-2c0c2c80-ff18-40fe-801a-e3f95f11e0e0](.artifacts/records/project__investigation-observation/rec-2c0c2c80-ff18-40fe-801a-e3f95f11e0e0.md))_

## task-commit

### Acceptance
- **task-commit**: R6; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_task_commit.py tests/test_execute_landing.py tests/test_skill_contract_consistency.py -q -k 'commit or landing or task_commit' _(id: [rec-34f5bd84-dee8-4fa6-bf3a-1f646de23f5e](.artifacts/records/project__acceptance/rec-34f5bd84-dee8-4fa6-bf3a-1f646de23f5e.md))_

### Check
- **task-commit**: rec-34f5bd84-dee8-4fa6-bf3a-1f646de23f5e; 4ba5a390c79e1a6841c74467844b029055941985; pass; tdd _(id: [rec-116c845e-beb1-492c-bd63-156a5ccba707](.artifacts/records/project__check-run/rec-116c845e-beb1-492c-bd63-156a5ccba707.md))_

## task-detail-links

### Acceptance
- **task-detail-links**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k link _(id: [rec-79b9e2f6-49a8-4d48-8788-0da94d698726](.artifacts/records/project__acceptance/rec-79b9e2f6-49a8-4d48-8788-0da94d698726.md))_

### Check
- **task-detail-links**: rec-79b9e2f6-49a8-4d48-8788-0da94d698726; f1d91299f3812c61327da0d352b1541bebdc0d38; pass; tdd _(id: [rec-3c74b663-3b9f-4872-b3ef-a3e4e8acec7a](.artifacts/records/project__check-run/rec-3c74b663-3b9f-4872-b3ef-a3e4e8acec7a.md))_

## task-detail-model

### Acceptance
- **task-detail-model**: tdd; dashboard; python3 -m pytest tests/test_dashboard_model.py -q _(id: [rec-8f020a2f-f7de-43e3-b46f-423d52e44fe4](.artifacts/records/project__acceptance/rec-8f020a2f-f7de-43e3-b46f-423d52e44fe4.md))_

### Check
- **task-detail-model**: rec-8f020a2f-f7de-43e3-b46f-423d52e44fe4; 38c2399; pass; tdd _(id: [rec-93b50136-8ef3-4e78-a5fd-29d38ee008b8](.artifacts/records/project__check-run/rec-93b50136-8ef3-4e78-a5fd-29d38ee008b8.md))_

## task-detail-module

### Acceptance
- **task-detail-module**: tdd; dashboard; ! grep -n '^class TaskDetailScreen' dashboard/app.py && grep -c '^class TaskDetailScreen' dashboard/task_detail.py && uv run --with pytest --with textual pytest tests/test_dashboard_app.py _(id: [rec-7f83addf-fb83-4129-9116-b02371346c5d](.artifacts/records/project__acceptance/rec-7f83addf-fb83-4129-9116-b02371346c5d.md))_

### Check
- **task-detail-module**: rec-7f83addf-fb83-4129-9116-b02371346c5d; dirty; pass; tdd _(id: [rec-cc977b6d-5388-4c49-b3e7-edb62496015a](.artifacts/records/project__check-run/rec-cc977b6d-5388-4c49-b3e7-edb62496015a.md))_

## task-detail-screen

### Acceptance
- **task-detail-screen**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-421586f5-5f49-4a47-b715-eeb09ad69b90](.artifacts/records/project__acceptance/rec-421586f5-5f49-4a47-b715-eeb09ad69b90.md))_

### Check
- **task-detail-screen**: rec-421586f5-5f49-4a47-b715-eeb09ad69b90; e6cf774; pass; tdd _(id: [rec-d4342ee2-0473-4fa8-b8b8-4abc42c914ec](.artifacts/records/project__check-run/rec-d4342ee2-0473-4fa8-b8b8-4abc42c914ec.md))_

## task-graph-depends

### Acceptance
- **task-graph-depends**: R7; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k depends_on _(id: [rec-cdca8182-c377-49ef-bf7c-393abc9579e7](.artifacts/records/project__acceptance/rec-cdca8182-c377-49ef-bf7c-393abc9579e7.md))_

### Check
- **task-graph-depends**: rec-cdca8182-c377-49ef-bf7c-393abc9579e7; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-d50bb1ec-05d9-42ac-8ab6-694f258c70fa](.artifacts/records/project__check-run/rec-d50bb1ec-05d9-42ac-8ab6-694f258c70fa.md))_

## task-graph-review

### Check
- **task-graph-review**: bafc565bce46cca3f85b02a392c10073e42b300d; pass; review _(id: [rec-bbf0f42a-95d1-4b52-a772-dabf5232a686](.artifacts/records/project__check-run/rec-bbf0f42a-95d1-4b52-a772-dabf5232a686.md))_

## task-graph-ui

### Acceptance
- **task-graph-ui**: R1; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/taskGraph.test.ts -t R1 _(id: [rec-fb54d44f-9435-4a84-9dde-0579582ca22b](.artifacts/records/project__acceptance/rec-fb54d44f-9435-4a84-9dde-0579582ca22b.md))_

### Check
- **task-graph-ui**: rec-fb54d44f-9435-4a84-9dde-0579582ca22b; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-08f90ecf-f282-4390-9eb0-a27555852a5f](.artifacts/records/project__check-run/rec-08f90ecf-f282-4390-9eb0-a27555852a5f.md))_

## task-graph-ui-r2

### Acceptance
- **task-graph-ui-r2**: R2; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/taskGraph.test.ts -t R2 _(id: [rec-214d99fb-fb17-4658-9466-9fa14eb35fc9](.artifacts/records/project__acceptance/rec-214d99fb-fb17-4658-9466-9fa14eb35fc9.md))_

### Check
- **task-graph-ui-r2**: rec-214d99fb-fb17-4658-9466-9fa14eb35fc9; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-6476a573-8524-42bf-8905-9926480e409b](.artifacts/records/project__check-run/rec-6476a573-8524-42bf-8905-9926480e409b.md))_

## task-graph-ui-r3

### Acceptance
- **task-graph-ui-r3**: R3; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/taskGraph.test.ts -t R3 _(id: [rec-08b7da88-e954-41a8-8e3e-c256b7516b61](.artifacts/records/project__acceptance/rec-08b7da88-e954-41a8-8e3e-c256b7516b61.md))_

### Check
- **task-graph-ui-r3**: rec-08b7da88-e954-41a8-8e3e-c256b7516b61; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-6378a2c3-4f9a-4869-8130-e93e73608b86](.artifacts/records/project__check-run/rec-6378a2c3-4f9a-4869-8130-e93e73608b86.md))_

## task-graph-ui-r4

### Acceptance
- **task-graph-ui-r4**: R4; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/taskGraph.test.ts -t R4 _(id: [rec-a5b90888-5dcf-4c23-b8af-ef0a57e24cf0](.artifacts/records/project__acceptance/rec-a5b90888-5dcf-4c23-b8af-ef0a57e24cf0.md))_

### Check
- **task-graph-ui-r4**: rec-a5b90888-5dcf-4c23-b8af-ef0a57e24cf0; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-3163641d-7d0f-41b9-a4ac-58d0cb055478](.artifacts/records/project__check-run/rec-3163641d-7d0f-41b9-a4ac-58d0cb055478.md))_

## task-graph-ui-r5

### Acceptance
- **task-graph-ui-r5**: R5; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/taskGraph.test.ts -t R5 _(id: [rec-2c906ad1-71c8-4416-8f31-68a6cc327572](.artifacts/records/project__acceptance/rec-2c906ad1-71c8-4416-8f31-68a6cc327572.md))_

### Check
- **task-graph-ui-r5**: rec-2c906ad1-71c8-4416-8f31-68a6cc327572; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-f7bab6ef-6ff8-4af1-8d52-03d4c18278f4](.artifacts/records/project__check-run/rec-f7bab6ef-6ff8-4af1-8d52-03d4c18278f4.md))_

## task-graph-ui-r6

### Acceptance
- **task-graph-ui-r6**: R6; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/taskGraph.test.ts -t R6 _(id: [rec-861d45c6-1169-4ddd-ab16-c7caf5fabdfb](.artifacts/records/project__acceptance/rec-861d45c6-1169-4ddd-ab16-c7caf5fabdfb.md))_

### Check
- **task-graph-ui-r6**: rec-861d45c6-1169-4ddd-ab16-c7caf5fabdfb; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-58f6084c-08c7-4162-842f-3765fd6e19c5](.artifacts/records/project__check-run/rec-58f6084c-08c7-4162-842f-3765fd6e19c5.md))_

## task-list-filters

### Acceptance
- **task-list-filters**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-982fcf31-6ef8-41aa-97a6-03ec860bfccb](.artifacts/records/project__acceptance/rec-982fcf31-6ef8-41aa-97a6-03ec860bfccb.md))_

### Check
- **task-list-filters**: rec-982fcf31-6ef8-41aa-97a6-03ec860bfccb; e3b7751; pass; tdd _(id: [rec-faa84f50-9fb4-422a-b887-7877e889ac3b](.artifacts/records/project__check-run/rec-faa84f50-9fb4-422a-b887-7877e889ac3b.md))_

## task-row-cells

### Acceptance
- **task-row-cells**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'waits or running or phase_column' _(id: [rec-daa1a988-73f2-45f9-8cde-f795662613c1](.artifacts/records/project__acceptance/rec-daa1a988-73f2-45f9-8cde-f795662613c1.md))_

### Check
- **task-row-cells**: rec-daa1a988-73f2-45f9-8cde-f795662613c1; ef6325fb4ef1128ad071f79e64d709bd1d28781d; pass; tdd _(id: [rec-79370462-4380-4f9b-94d2-a90ed8569ee7](.artifacts/records/project__check-run/rec-79370462-4380-4f9b-94d2-a90ed8569ee7.md))_

## task-row-model

### Acceptance
- **task-row-model**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'waits or running' _(id: [rec-60e78986-208c-43d5-8207-9803afeab4df](.artifacts/records/project__acceptance/rec-60e78986-208c-43d5-8207-9803afeab4df.md))_

### Check
- **task-row-model**: rec-60e78986-208c-43d5-8207-9803afeab4df; 865fc75f021559acf6184b145f73f5b8ca57c313; pass; tdd _(id: [rec-f112e2ec-e4d3-46b7-9e18-40531b7f5da2](.artifacts/records/project__check-run/rec-f112e2ec-e4d3-46b7-9e18-40531b7f5da2.md))_

### Observation
- **task-row-model**: Withdrawn dependencies stay in waits_on, matching the engine: derived.ready only treats done as satisfied, so the task really is still waiting.; dashboard-features _(id: [rec-a6aba57e-2094-4cc5-9145-31dccbf7f288](.artifacts/records/project__investigation-observation/rec-a6aba57e-2094-4cc5-9145-31dccbf7f288.md))_

## task-table-module

### Acceptance
- **task-table-module**: tdd; dashboard; ! grep -nE '^(class TaskFilter|class SectionRow|def section_rows|def visible_tasks|class TaskTable)' dashboard/app.py && grep -c 'class TaskFilter' dashboard/tasks.py && uv run --with pytest --with textual pytest tests/test_dashboard_app.py tests/test_dashboard_tasks.py _(id: [rec-9a70606f-50c9-40b0-9b8c-107ff6573a06](.artifacts/records/project__acceptance/rec-9a70606f-50c9-40b0-9b8c-107ff6573a06.md))_

### Check
- **task-table-module**: rec-9a70606f-50c9-40b0-9b8c-107ff6573a06; dirty; pass; tdd _(id: [rec-4acae157-ca43-4995-93fc-cbfbf4e8ce80](.artifacts/records/project__check-run/rec-4acae157-ca43-4995-93fc-cbfbf4e8ce80.md))_

## task-worktrees-review

### Check
- **task-worktrees-review**: task-worktrees-review; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; review _(id: [rec-87f9db00-c642-4d83-89b8-9b1c95540161](.artifacts/records/project__check-run/rec-87f9db00-c642-4d83-89b8-9b1c95540161.md))_

## terminal-view-format

### Acceptance
- **terminal-view-format**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q _(id: [rec-afb68d05-d961-45dd-813e-948c8e137722](.artifacts/records/project__acceptance/rec-afb68d05-d961-45dd-813e-948c8e137722.md))_

### Check
- **terminal-view-format**: rec-afb68d05-d961-45dd-813e-948c8e137722; 0f8791a808f1a5d81eb5beb6e03a7b56905f1644; pass; tdd _(id: [rec-0a4f74c4-1ca9-485b-ad92-c50608f178e5](.artifacts/records/project__check-run/rec-0a4f74c4-1ca9-485b-ad92-c50608f178e5.md))_

## test-suite-speed

### Acceptance
- **test-suite-speed**: check; test-suite-speed; time uv run --with textual --with pytest python -m pytest tests -q _(id: [rec-6e6e5c69-9ab0-44f3-9016-49c3512fcd99](.artifacts/records/project__acceptance/rec-6e6e5c69-9ab0-44f3-9016-49c3512fcd99.md))_

### Check
- **test-suite-speed**: rec-6e6e5c69-9ab0-44f3-9016-49c3512fcd99; 6cb58b4; pass; check _(id: [rec-e81acb74-ed4a-4e0f-bb5c-9ea42abfa56e](.artifacts/records/project__check-run/rec-e81acb74-ed4a-4e0f-bb5c-9ea42abfa56e.md))_

## tests-brief-lock

### Acceptance
- **tests-brief-lock**: R5; tdd; workflow-loop; python3 -m pytest tests/test_plan_trace.py tests/test_skill_contract_consistency.py -q _(id: [rec-b760d3e8-594b-491c-b282-aa07923e1a38](.artifacts/records/project__acceptance/rec-b760d3e8-594b-491c-b282-aa07923e1a38.md))_

### Check
- **tests-brief-lock**: rec-b760d3e8-594b-491c-b282-aa07923e1a38; 3b2f808f60f93b4db108543986be05d184226566; pass; tdd _(id: [rec-0888e40d-41dc-48b0-b143-10e2941d5148](.artifacts/records/project__check-run/rec-0888e40d-41dc-48b0-b143-10e2941d5148.md))_
- **tests-brief-lock**: rec-b760d3e8-594b-491c-b282-aa07923e1a38; 50303893af61c747620551cd512239752b0528a1; pass; tdd _(id: [rec-38740f76-0e4d-45de-a723-ee81f20663df](.artifacts/records/project__check-run/rec-38740f76-0e4d-45de-a723-ee81f20663df.md))_
- **tests-brief-lock**: rec-b760d3e8-594b-491c-b282-aa07923e1a38; 50303893af61c747620551cd512239752b0528a1; pass; tdd _(id: [rec-9480d081-48fa-4537-afa5-46c3bb9a0818](.artifacts/records/project__check-run/rec-9480d081-48fa-4537-afa5-46c3bb9a0818.md))_
- **tests-brief-lock**: rec-b760d3e8-594b-491c-b282-aa07923e1a38; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; tdd _(id: [rec-adcbbbfb-05f6-4301-a35b-d4bc66d63f0c](.artifacts/records/project__check-run/rec-adcbbbfb-05f6-4301-a35b-d4bc66d63f0c.md))_

### Finding
- **tests-brief-lock**: tests-brief-lock closed done without red-first: predecessor suite verify_command already passed; new assertions are additive; At 3b2f808 the acceptance verify_command (full plan-trace+consistency) exits 0; tip 5030389 adds assertions. No runner fail exists for this criterion_id with ancestry to green.; a later phase requires red-first for additive test-only tasks, or a fail check-run for this criterion precedes green; none _(id: [rec-7c5115ae-6da3-4327-a386-7b7da037b865](.artifacts/records/project__finding/rec-7c5115ae-6da3-4327-a386-7b7da037b865.md))_

## tests-brief-lock-r4

### Acceptance
- **tests-brief-lock-r4**: R4; check; workflow-loop; python3 -m pytest tests/test_plan_trace.py -k criterion_optional_in_contract -q _(id: [rec-6525fff7-02a2-4ef2-8ae7-1b4fe8a3fe89](.artifacts/records/project__acceptance/rec-6525fff7-02a2-4ef2-8ae7-1b4fe8a3fe89.md))_

### Check
- **tests-brief-lock-r4**: rec-6525fff7-02a2-4ef2-8ae7-1b4fe8a3fe89; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; check _(id: [rec-3fead4a6-2d91-44ad-8ff2-9386f730a2a9](.artifacts/records/project__check-run/rec-3fead4a6-2d91-44ad-8ff2-9386f730a2a9.md))_
- **tests-brief-lock-r4**: rec-6525fff7-02a2-4ef2-8ae7-1b4fe8a3fe89; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-bb5c1cf9-af63-460e-9ac0-cf721099118a](.artifacts/records/project__check-run/rec-bb5c1cf9-af63-460e-9ac0-cf721099118a.md))_
- **tests-brief-lock-r4**: rec-6525fff7-02a2-4ef2-8ae7-1b4fe8a3fe89; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-ea4906dd-4b6d-4c73-9fa3-2997e5f49e07](.artifacts/records/project__check-run/rec-ea4906dd-4b6d-4c73-9fa3-2997e5f49e07.md))_

## tests-claim-chain

### Acceptance
- **tests-claim-chain**: R6; tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q _(id: [rec-14838183-7e65-45e7-8ac1-41a2ff0e912b](.artifacts/records/project__acceptance/rec-14838183-7e65-45e7-8ac1-41a2ff0e912b.md))_

### Check
- **tests-claim-chain**: rec-14838183-7e65-45e7-8ac1-41a2ff0e912b; 464d6813f21f624097f5bfbfb293c8ede2478e49; fail; tdd _(id: [rec-126b0567-b486-49ba-8113-a4807fb93310](.artifacts/records/project__check-run/rec-126b0567-b486-49ba-8113-a4807fb93310.md))_
- **tests-claim-chain**: rec-14838183-7e65-45e7-8ac1-41a2ff0e912b; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; tdd _(id: [rec-147f0251-a5ca-4a04-86e8-6f9e58e5683b](.artifacts/records/project__check-run/rec-147f0251-a5ca-4a04-86e8-6f9e58e5683b.md))_
- **tests-claim-chain**: rec-14838183-7e65-45e7-8ac1-41a2ff0e912b; 50303893af61c747620551cd512239752b0528a1; pass; tdd _(id: [rec-5d6b2aba-f785-4ba1-a96c-ad8c0926b48d](.artifacts/records/project__check-run/rec-5d6b2aba-f785-4ba1-a96c-ad8c0926b48d.md))_
- **tests-claim-chain**: rec-14838183-7e65-45e7-8ac1-41a2ff0e912b; 464d6813f21f624097f5bfbfb293c8ede2478e49; fail; tdd _(id: [rec-6f72268a-2d46-4c4d-b286-f1f7809c400a](.artifacts/records/project__check-run/rec-6f72268a-2d46-4c4d-b286-f1f7809c400a.md))_
- **tests-claim-chain**: rec-14838183-7e65-45e7-8ac1-41a2ff0e912b; 3b2f808f60f93b4db108543986be05d184226566; pass; tdd _(id: [rec-e51d4bd8-9ce4-4583-a71f-03083f2506d0](.artifacts/records/project__check-run/rec-e51d4bd8-9ce4-4583-a71f-03083f2506d0.md))_

## tier2-dashboard

### Acceptance
- **tier2-dashboard**: R6; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k tier2 _(id: [rec-b5eb3ea3-6ec1-4431-ab56-fcb60d7b1574](.artifacts/records/project__acceptance/rec-b5eb3ea3-6ec1-4431-ab56-fcb60d7b1574.md))_

### Check
- **tier2-dashboard**: rec-b5eb3ea3-6ec1-4431-ab56-fcb60d7b1574; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; tdd _(id: [rec-557c638d-ef97-48d0-8892-54706a5542b2](.artifacts/records/project__check-run/rec-557c638d-ef97-48d0-8892-54706a5542b2.md))_
- **tier2-dashboard**: rec-b5eb3ea3-6ec1-4431-ab56-fcb60d7b1574; dirty; fail; tdd _(id: [rec-c7a6acac-a090-445c-9efa-ff2f72cf3516](.artifacts/records/project__check-run/rec-c7a6acac-a090-445c-9efa-ff2f72cf3516.md))_

## tier2-engine

### Acceptance
- **tier2-engine**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "runner or background or check_run or tmux" _(id: [rec-66d14411-07cd-479e-bb45-abfd3ee105f3](.artifacts/records/project__acceptance/rec-66d14411-07cd-479e-bb45-abfd3ee105f3.md))_

### Check
- **tier2-engine**: rec-66d14411-07cd-479e-bb45-abfd3ee105f3; dirty; fail; tdd _(id: [rec-48587139-b25f-4095-84d6-f09a5fad4399](.artifacts/records/project__check-run/rec-48587139-b25f-4095-84d6-f09a5fad4399.md))_
- **tier2-engine**: rec-66d14411-07cd-479e-bb45-abfd3ee105f3; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; tdd _(id: [rec-5a5855fb-5dd7-499b-9c69-2b323dde9ee0](.artifacts/records/project__check-run/rec-5a5855fb-5dd7-499b-9c69-2b323dde9ee0.md))_

## tier2-engine-fix

### Acceptance
- **tier2-engine-fix**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "fix or cluster or budget" _(id: [rec-e54af7a4-185c-4adc-93b9-6ca9417d5f0f](.artifacts/records/project__acceptance/rec-e54af7a4-185c-4adc-93b9-6ca9417d5f0f.md))_

### Check
- **tier2-engine-fix**: rec-e54af7a4-185c-4adc-93b9-6ca9417d5f0f; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; tdd _(id: [rec-2ab5c73a-c1a5-4393-9cc7-1d2334a71432](.artifacts/records/project__check-run/rec-2ab5c73a-c1a5-4393-9cc7-1d2334a71432.md))_
- **tier2-engine-fix**: rec-e54af7a4-185c-4adc-93b9-6ca9417d5f0f; dirty; fail; tdd _(id: [rec-51ae3745-10a9-4740-ba5d-2965a47905b6](.artifacts/records/project__check-run/rec-51ae3745-10a9-4740-ba5d-2965a47905b6.md))_

## tier2-engine-gate

### Acceptance
- **tier2-engine-gate**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k gate _(id: [rec-5ad44d4e-6fd3-4829-be3e-95e48379990b](.artifacts/records/project__acceptance/rec-5ad44d4e-6fd3-4829-be3e-95e48379990b.md))_

### Check
- **tier2-engine-gate**: rec-5ad44d4e-6fd3-4829-be3e-95e48379990b; dirty; fail; tdd _(id: [rec-504fe546-d509-44bb-af08-7830343269b8](.artifacts/records/project__check-run/rec-504fe546-d509-44bb-af08-7830343269b8.md))_
- **tier2-engine-gate**: rec-5ad44d4e-6fd3-4829-be3e-95e48379990b; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; tdd _(id: [rec-deacd1a7-dd90-434b-b6de-bf7e06e1f237](.artifacts/records/project__check-run/rec-deacd1a7-dd90-434b-b6de-bf7e06e1f237.md))_

## tier2-engine-meta

### Acceptance
- **tier2-engine-meta**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "meta or fields or evidence_kind or digest" _(id: [rec-f434ce3c-77ee-4e17-80d6-ad308eadb1f2](.artifacts/records/project__acceptance/rec-f434ce3c-77ee-4e17-80d6-ad308eadb1f2.md))_

### Check
- **tier2-engine-meta**: rec-f434ce3c-77ee-4e17-80d6-ad308eadb1f2; dirty; fail; tdd _(id: [rec-013637c5-73ac-4c16-b70e-82fc55eaf098](.artifacts/records/project__check-run/rec-013637c5-73ac-4c16-b70e-82fc55eaf098.md))_
- **tier2-engine-meta**: rec-f434ce3c-77ee-4e17-80d6-ad308eadb1f2; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; tdd _(id: [rec-1f7b0d92-ecc5-419d-89a3-42a302d2b53b](.artifacts/records/project__check-run/rec-1f7b0d92-ecc5-419d-89a3-42a302d2b53b.md))_

## tier2-engine-scoped

### Acceptance
- **tier2-engine-scoped**: R7; check; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-97b46204-7027-47b9-bf84-e4b585da8849](.artifacts/records/project__acceptance/rec-97b46204-7027-47b9-bf84-e4b585da8849.md))_

### Check
- **tier2-engine-scoped**: rec-97b46204-7027-47b9-bf84-e4b585da8849; dirty; pass; check _(id: [rec-31522e93-58ea-4e24-83d5-28c4df9fbc85](.artifacts/records/project__check-run/rec-31522e93-58ea-4e24-83d5-28c4df9fbc85.md))_
- **tier2-engine-scoped**: rec-97b46204-7027-47b9-bf84-e4b585da8849; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; check _(id: [rec-6a37cb49-2c89-4c26-9228-8047de254e26](.artifacts/records/project__check-run/rec-6a37cb49-2c89-4c26-9228-8047de254e26.md))_

## tier2-journal-pager-flake

### Finding
- **tier2-journal-pager-flake**: test_journal_detail_pager_pages_record_with_stub timed out under tier-2 parallel load; tier-2 at 3379fcf still fails same test after 40s timeout; screen never loads under xdist; test passes stably under same suite or human accepts waiver; none _(id: [rec-c174fd42-e8c9-41ea-bb43-8aee75770421](.artifacts/records/project__finding/rec-c174fd42-e8c9-41ea-bb43-8aee75770421.md))_

## tier2-plugin-root-and-cli

### Finding
- **tier2-plugin-root-and-cli**: tier-2 failed at phase head: verify_authority import of scripts/close_batch + journal pager flake; exit 1; nodes ['tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub', 'tests/test_verify_authority.py']; tier-2 passes at new phase head; none _(id: [rec-c8de37ab-a66a-4589-ab5a-2299788a4be9](.artifacts/records/project__finding/rec-c8de37ab-a66a-4589-ab5a-2299788a4be9.md))_

## tiered-verification-review

### Check
- **tiered-verification-review**: tiered-verification-review; 2f7404eab494720b703ffd0e2e01078236a876ab; pass; review _(id: [rec-05620909-2f20-41d8-9e42-a7aa6720812a](.artifacts/records/project__check-run/rec-05620909-2f20-41d8-9e42-a7aa6720812a.md))_
- **tiered-verification-review**: tiered-verification-review; 6d43454d3673e4e693fce13d5d4ea328f36943a3; pass; review _(id: [rec-216b86b7-5b0a-42ef-a2b4-cf0d3fbfbea0](.artifacts/records/project__check-run/rec-216b86b7-5b0a-42ef-a2b4-cf0d3fbfbea0.md))_
- **tiered-verification-review**: tiered-verification-review; a19db351754f233dec442631abd4d94f28575f1c; pass; review _(id: [rec-24715006-cbd1-4a2f-9bf3-1ef1ac73a981](.artifacts/records/project__check-run/rec-24715006-cbd1-4a2f-9bf3-1ef1ac73a981.md))_
- **tiered-verification-review**: tiered-verification-review; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; review _(id: [rec-af99ba51-538e-40fb-84b3-ce8525aa5cd6](.artifacts/records/project__check-run/rec-af99ba51-538e-40fb-84b3-ce8525aa5cd6.md))_
- **tiered-verification-review**: tiered-verification-review; 5e07f9a48bc4b935d6a3a90f7fc7ef4edcfc0246; pass; review _(id: [rec-b0010871-e548-46b2-88e7-4dfc9b2d16b5](.artifacts/records/project__check-run/rec-b0010871-e548-46b2-88e7-4dfc9b2d16b5.md))_
- **tiered-verification-review**: tiered-verification-review; 8ea0179b2e0b93b47df97d43ba7973e0875fe449; pass; review _(id: [rec-d3d21029-e99b-463c-8359-a7cc03e11f7a](.artifacts/records/project__check-run/rec-d3d21029-e99b-463c-8359-a7cc03e11f7a.md))_

## tiered-verification-tier2

### Check
- **tiered-verification-tier2**: tiered-verification-tier2; dirty; fail; check _(id: [rec-22e4965f-ca79-4bb0-9cc7-f479ff1b8ed1](.artifacts/records/project__check-run/rec-22e4965f-ca79-4bb0-9cc7-f479ff1b8ed1.md))_
- **tiered-verification-tier2**: tiered-verification-tier2; 8ea0179b2e0b93b47df97d43ba7973e0875fe449; pass; check _(id: [rec-7d0ee8e0-42cb-4a53-bc2e-aab7573071e2](.artifacts/records/project__check-run/rec-7d0ee8e0-42cb-4a53-bc2e-aab7573071e2.md))_
- **tiered-verification-tier2**: tiered-verification-tier2; dirty; fail; check _(id: [rec-a24a9ec0-30f8-41e7-a2dc-c8552984c3ae](.artifacts/records/project__check-run/rec-a24a9ec0-30f8-41e7-a2dc-c8552984c3ae.md))_
- **tiered-verification-tier2**: tiered-verification-tier2; 5e07f9a48bc4b935d6a3a90f7fc7ef4edcfc0246; fail; check _(id: [rec-b029a228-d2e6-4916-a21c-0ee8d8d8e59d](.artifacts/records/project__check-run/rec-b029a228-d2e6-4916-a21c-0ee8d8d8e59d.md))_
- **tiered-verification-tier2**: tiered-verification-tier2; 2f7404eab494720b703ffd0e2e01078236a876ab; fail; check _(id: [rec-db63b61e-ff54-44f5-8f57-39dbb9737ba5](.artifacts/records/project__check-run/rec-db63b61e-ff54-44f5-8f57-39dbb9737ba5.md))_
- **tiered-verification-tier2**: tiered-verification-tier2; 6d43454d3673e4e693fce13d5d4ea328f36943a3; fail; check _(id: [rec-fd72157e-80df-43c2-aac6-744fbac2d367](.artifacts/records/project__check-run/rec-fd72157e-80df-43c2-aac6-744fbac2d367.md))_

## tiered-verification-tier2-budget

### Finding
- **tiered-verification-tier2-budget**: Tier-2 fix-task budget exhausted with remaining failing modules; tier-2 check-run rec-a24a9ec0-30f8-41e7-a2dc-c8552984c3ae failed with 10 node ids across 7 modules; created 3 fix tasks (dashboard_app, dashboard_journal, discuss_skill); remaining: evidence_loop, plan_landing, plan_wave_rules, verify_authority; remaining modules fixed and tier-2 passes at phase head, or human accepts scoped waiver; none _(id: [rec-b8101acf-ff6c-4dbc-8042-6499702bd5e5](.artifacts/records/project__finding/rec-b8101acf-ff6c-4dbc-8042-6499702bd5e5.md))_

## tm-cli

### Acceptance
- **tm-cli**: tdd; session-analysis; python3 -m pytest -q tests/test_session_report.py _(id: [rec-be629630-2798-4a55-92ca-322aba930e94](.artifacts/records/project__acceptance/rec-be629630-2798-4a55-92ca-322aba930e94.md))_

### Check
- **tm-cli**: rec-be629630-2798-4a55-92ca-322aba930e94; dirty; pass; tdd _(id: [rec-4f4277b5-896a-4a11-a64f-5db71bc729fb](.artifacts/records/project__check-run/rec-4f4277b5-896a-4a11-a64f-5db71bc729fb.md))_

## tm-parse-events

### Acceptance
- **tm-parse-events**: tdd; session-analysis; python3 -m pytest -q tests/test_session_metrics.py -k parse _(id: [rec-2df7a704-c3ba-43a0-966d-42474d3c2318](.artifacts/records/project__acceptance/rec-2df7a704-c3ba-43a0-966d-42474d3c2318.md))_

### Check
- **tm-parse-events**: rec-2df7a704-c3ba-43a0-966d-42474d3c2318; dirty; pass; tdd _(id: [rec-95a8ff7f-ad6e-4e72-8d4f-10f08cc8e68b](.artifacts/records/project__check-run/rec-95a8ff7f-ad6e-4e72-8d4f-10f08cc8e68b.md))_

## tm-session-fields

### Acceptance
- **tm-session-fields**: tdd; session-analysis; python3 -m pytest -q tests/test_session_fields.py _(id: [rec-5f8ebfcf-f591-4f07-932d-65fabc8871fb](.artifacts/records/project__acceptance/rec-5f8ebfcf-f591-4f07-932d-65fabc8871fb.md))_

### Check
- **tm-session-fields**: rec-5f8ebfcf-f591-4f07-932d-65fabc8871fb; dirty; pass; tdd _(id: [rec-da978d42-a6a0-4ac2-986b-6cc1e1121e13](.artifacts/records/project__check-run/rec-da978d42-a6a0-4ac2-986b-6cc1e1121e13.md))_

## tm-tool-metrics

### Acceptance
- **tm-tool-metrics**: tdd; session-analysis; python3 -m pytest -q tests/test_session_tools.py _(id: [rec-eb5399be-74fd-4403-bf2d-69fb1cb5bce9](.artifacts/records/project__acceptance/rec-eb5399be-74fd-4403-bf2d-69fb1cb5bce9.md))_

### Check
- **tm-tool-metrics**: rec-eb5399be-74fd-4403-bf2d-69fb1cb5bce9; dirty; pass; tdd _(id: [rec-61c34384-57d2-4cb4-9033-6a25173c9e45](.artifacts/records/project__check-run/rec-61c34384-57d2-4cb4-9033-6a25173c9e45.md))_

## tmux-conf-removal

### Acceptance
- **tmux-conf-removal**: check; dashboard; test ! -e dashboard/tmux.conf && ! grep -rnE 'dashboard/tmux\.conf|SE_WORKFLOW_DASHBOARD' dashboard scripts tests _(id: [rec-3aa70906-2826-4ae6-86f0-1b6d7a206306](.artifacts/records/project__acceptance/rec-3aa70906-2826-4ae6-86f0-1b6d7a206306.md))_

### Check
- **tmux-conf-removal**: rec-202b31bb-dba8-4bb0-ab9b-cae95af2386e; dirty; pass; check _(id: [rec-66c30d25-49c5-4f57-9f48-88678f80e597](.artifacts/records/project__check-run/rec-66c30d25-49c5-4f57-9f48-88678f80e597.md))_
- **tmux-conf-removal**: rec-3aa70906-2826-4ae6-86f0-1b6d7a206306; dirty; pass; check _(id: [rec-7a78f485-6ff0-4ac6-9af7-64e3e3e284d7](.artifacts/records/project__check-run/rec-7a78f485-6ff0-4ac6-9af7-64e3e3e284d7.md))_

## tmux-conf-removal-install

### Acceptance
- **tmux-conf-removal-install**: check; dashboard; d=$(mktemp -d) && bash scripts/sync-plugin.sh "$d/p" && test -x "$d/p/se-workflow.tmux" _(id: [rec-202b31bb-dba8-4bb0-ab9b-cae95af2386e](.artifacts/records/project__acceptance/rec-202b31bb-dba8-4bb0-ab9b-cae95af2386e.md))_

## tmux-entry-script

### Acceptance
- **tmux-entry-script**: tdd; dashboard; uv run --with pytest --with textual pytest -m tmux tests/test_tmux_entry.py -k default _(id: [rec-f6564330-b301-4302-a1d2-6e9c206c489b](.artifacts/records/project__acceptance/rec-f6564330-b301-4302-a1d2-6e9c206c489b.md))_

### Check
- **tmux-entry-script**: rec-f6564330-b301-4302-a1d2-6e9c206c489b; dirty; pass; tdd _(id: [rec-35197428-1805-468f-9d8d-36f62eb9a436](.artifacts/records/project__check-run/rec-35197428-1805-468f-9d8d-36f62eb9a436.md))_
- **tmux-entry-script**: rec-a19b9fe0-d373-4e93-a176-b941fa8236f0; dirty; pass; tdd _(id: [rec-efc1c7dd-67d6-4626-b64b-7289b0292719](.artifacts/records/project__check-run/rec-efc1c7dd-67d6-4626-b64b-7289b0292719.md))_

## tmux-entry-script-options

### Acceptance
- **tmux-entry-script-options**: tdd; dashboard; uv run --with pytest --with textual pytest -m tmux tests/test_tmux_entry.py -k custom_keys _(id: [rec-a19b9fe0-d373-4e93-a176-b941fa8236f0](.artifacts/records/project__acceptance/rec-a19b9fe0-d373-4e93-a176-b941fa8236f0.md))_

## tmux-suite-flake

### Finding
- **tmux-suite-flake**: One tmux integration test fails rarely: 1 of 19 serial tmux runs on e4484c4, test name not captured; Parent reruns on fix/dashboard-bugfix: 1 failed of 10 right after the xdist run, then 18 clean runs (15 full tmux runs, 3 full sequences); the extended popup test passed 12/12 alone; A tmux failure is captured with -rf and fixed, or 50 consecutive clean runs _(id: [rec-68330501-7b9a-446c-b24a-bf84af04e8e8](.artifacts/records/project__finding/rec-68330501-7b9a-446c-b24a-bf84af04e8e8.md))_

## tmux-test-waits

### Acceptance
- **tmux-test-waits**: check; test-suite-speed; python3 -m pytest tests/test_tmux_integration.py tests/test_e2e_dashboard.py -q --durations=6 _(id: [rec-572fa450-b4a2-45bb-b52e-b5198f0e9b91](.artifacts/records/project__acceptance/rec-572fa450-b4a2-45bb-b52e-b5198f0e9b91.md))_

## trace-plan

### Acceptance
- **trace-plan**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_plan_trace.py -q _(id: [rec-6aa2fdc3-4b8f-4d53-a585-a4405107bef5](.artifacts/records/project__acceptance/rec-6aa2fdc3-4b8f-4d53-a585-a4405107bef5.md))_

### Check
- **trace-plan**: rec-6aa2fdc3-4b8f-4d53-a585-a4405107bef5; dirty; pass; check _(id: [rec-6288d5e3-7aed-4c8a-ad22-2e2fa716b9fc](.artifacts/records/project__check-run/rec-6288d5e3-7aed-4c8a-ad22-2e2fa716b9fc.md))_

## unsigned-check-label

### Acceptance
- **unsigned-check-label**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k unsigned _(id: [rec-403febb3-cbe5-474d-8413-5687934c29d2](.artifacts/records/project__acceptance/rec-403febb3-cbe5-474d-8413-5687934c29d2.md))_

### Check
- **unsigned-check-label**: rec-403febb3-cbe5-474d-8413-5687934c29d2; 3ca5175c7dc8e6e60b0f501bf3c0e30309e9403d; pass; tdd _(id: [rec-7d02868c-4d2e-4265-8548-c3b0ab4de18c](.artifacts/records/project__check-run/rec-7d02868c-4d2e-4265-8548-c3b0ab4de18c.md))_

### Observation
- **unsigned-check-label**: _needs_you built unsigned-check text from the raw criterion_id and used the check-run subject, so the panel showed a rec- id instead of the criterion and task.; dashboard-bugfix _(id: [rec-45a1d50b-0dae-47ec-88c3-19cab12238ba](.artifacts/records/project__investigation-observation/rec-45a1d50b-0dae-47ec-88c3-19cab12238ba.md))_

## verdict-gate

### Acceptance
- **verdict-gate**: R7; check; library-boundary; python3 -m pytest tests/test_verdict_gate.py::test_verdict_gate_assertion_red_exits_zero -q _(id: [rec-29e0b3bf-94df-4a5d-9317-b6c12e6443a0](.artifacts/records/project__acceptance/rec-29e0b3bf-94df-4a5d-9317-b6c12e6443a0.md))_

### Check
- **verdict-gate**: rec-29e0b3bf-94df-4a5d-9317-b6c12e6443a0; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; check _(id: [rec-be8250e6-3e75-46d8-bbe1-ccbe6ad4fa52](.artifacts/records/project__check-run/rec-be8250e6-3e75-46d8-bbe1-ccbe6ad4fa52.md))_
- **verdict-gate**: rec-29e0b3bf-94df-4a5d-9317-b6c12e6443a0; 5a263e1304089ecc2b4feec91b990963a8c56b3c; pass; check _(id: [rec-e6b40278-2397-492f-9dc5-80956e0ed20f](.artifacts/records/project__check-run/rec-e6b40278-2397-492f-9dc5-80956e0ed20f.md))_

## verdict-gate-command

### Acceptance
- **verdict-gate-command**: R9; check; library-boundary; python3 -m pytest tests/test_verdict_gate.py::test_verdict_gate_command_calls_run_verdict -q _(id: [rec-b710f687-d91b-4206-a5bd-2d8431eb21d8](.artifacts/records/project__acceptance/rec-b710f687-d91b-4206-a5bd-2d8431eb21d8.md))_

### Check
- **verdict-gate-command**: rec-b710f687-d91b-4206-a5bd-2d8431eb21d8; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; check _(id: [rec-3cc22462-f711-4ad6-89a2-7d3bc1f46960](.artifacts/records/project__check-run/rec-3cc22462-f711-4ad6-89a2-7d3bc1f46960.md))_
- **verdict-gate-command**: rec-b710f687-d91b-4206-a5bd-2d8431eb21d8; 5a263e1304089ecc2b4feec91b990963a8c56b3c; pass; check _(id: [rec-99de6678-8a65-44bd-bf1d-a05338a57404](.artifacts/records/project__check-run/rec-99de6678-8a65-44bd-bf1d-a05338a57404.md))_

## verdict-gate-false

### Acceptance
- **verdict-gate-false**: R8; check; library-boundary; python3 -m pytest tests/test_verdict_gate.py::test_verdict_gate_assertion_red_exits_one -q _(id: [rec-6306a25f-9095-4f9e-aedd-4d473ecc2ee2](.artifacts/records/project__acceptance/rec-6306a25f-9095-4f9e-aedd-4d473ecc2ee2.md))_

### Check
- **verdict-gate-false**: rec-6306a25f-9095-4f9e-aedd-4d473ecc2ee2; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; check _(id: [rec-2268038c-c1ea-47bb-b951-1cf6030a2ea1](.artifacts/records/project__check-run/rec-2268038c-c1ea-47bb-b951-1cf6030a2ea1.md))_
- **verdict-gate-false**: rec-6306a25f-9095-4f9e-aedd-4d473ecc2ee2; 5a263e1304089ecc2b4feec91b990963a8c56b3c; pass; check _(id: [rec-4283b141-8834-46eb-a3ba-7a0caafc3d93](.artifacts/records/project__check-run/rec-4283b141-8834-46eb-a3ba-7a0caafc3d93.md))_

## verdict-gate-nostore

### Acceptance
- **verdict-gate-nostore**: R10; check; library-boundary; python3 -m pytest tests/test_verdict_gate.py::test_verdict_gate_without_store -q _(id: [rec-6b189dbb-4fb6-47eb-9577-68b320964fac](.artifacts/records/project__acceptance/rec-6b189dbb-4fb6-47eb-9577-68b320964fac.md))_

### Check
- **verdict-gate-nostore**: rec-6b189dbb-4fb6-47eb-9577-68b320964fac; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; check _(id: [rec-0cf1e7c4-ebec-44ad-b080-665065eb5f41](.artifacts/records/project__check-run/rec-0cf1e7c4-ebec-44ad-b080-665065eb5f41.md))_
- **verdict-gate-nostore**: rec-6b189dbb-4fb6-47eb-9577-68b320964fac; 5a263e1304089ecc2b4feec91b990963a8c56b3c; pass; check _(id: [rec-20d07d36-08dd-4858-9ce3-930349cff4dd](.artifacts/records/project__check-run/rec-20d07d36-08dd-4858-9ce3-930349cff4dd.md))_

## verification-policy-review

### Check
- **verification-policy-review**: verification-policy-review; 3e813f617e5811a742014ffc95c70e6709dfc281; pass; review _(id: [rec-8c978b25-1eab-4408-b1e2-9d7684d35597](.artifacts/records/project__check-run/rec-8c978b25-1eab-4408-b1e2-9d7684d35597.md))_
- **verification-policy-review**: verification-policy-review; 846e07f37ff5afe6fe37b1475facaeda210e6945; fail; review _(id: [rec-e7deca42-ed08-44e2-805e-3016a1859e0f](.artifacts/records/project__check-run/rec-e7deca42-ed08-44e2-805e-3016a1859e0f.md))_
- **verification-policy-review**: verification-policy-review; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; review _(id: [rec-f86d2016-3a1e-49f1-850c-24b3fdabd63f](.artifacts/records/project__check-run/rec-f86d2016-3a1e-49f1-850c-24b3fdabd63f.md))_

## verification-policy-suite

### Check
- **verification-policy-suite**: verification-policy-suite; 8119e8e0cc031286ad62da0fd4ba9750b7223749; fail; check _(id: [rec-f48be939-020c-4f90-a9a6-2ff91f978979](.artifacts/records/project__check-run/rec-f48be939-020c-4f90-a9a6-2ff91f978979.md))_

## verify-aa-library

### Acceptance
- **verify-aa-library**: R20; check; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_command_facade.py::test_r20_create_without_store -q _(id: [rec-1e8bcbfe-b605-42ac-b14d-d54a04b92a10](.artifacts/records/project__acceptance/rec-1e8bcbfe-b605-42ac-b14d-d54a04b92a10.md))_

### Check
- **verify-aa-library**: rec-1e8bcbfe-b605-42ac-b14d-d54a04b92a10; 206fcd0b22ed111d7a272c934bb1864271947591; pass; check _(id: [rec-0ee0826c-1f50-4697-9d0b-726c2ef18b94](.artifacts/records/project__check-run/rec-0ee0826c-1f50-4697-9d0b-726c2ef18b94.md))_
- **verify-aa-library**: rec-1e8bcbfe-b605-42ac-b14d-d54a04b92a10; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; check _(id: [rec-22d06ac1-58dd-42b0-8651-dfa3e2d7c2e8](.artifacts/records/project__check-run/rec-22d06ac1-58dd-42b0-8651-dfa3e2d7c2e8.md))_

## verify-aa-library-get

### Acceptance
- **verify-aa-library-get**: R21; check; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_command_facade.py::test_r21_get_without_store -q _(id: [rec-7dd35c7c-5161-4661-8352-04a3bc27f4df](.artifacts/records/project__acceptance/rec-7dd35c7c-5161-4661-8352-04a3bc27f4df.md))_

### Check
- **verify-aa-library-get**: rec-7dd35c7c-5161-4661-8352-04a3bc27f4df; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; check _(id: [rec-8b1a130b-1019-4290-91b4-660d518e3a07](.artifacts/records/project__check-run/rec-8b1a130b-1019-4290-91b4-660d518e3a07.md))_
- **verify-aa-library-get**: rec-7dd35c7c-5161-4661-8352-04a3bc27f4df; 206fcd0b22ed111d7a272c934bb1864271947591; pass; check _(id: [rec-b748279f-a865-40fc-98c1-95e905722078](.artifacts/records/project__check-run/rec-b748279f-a865-40fc-98c1-95e905722078.md))_

## verify-aa-library-scan

### Acceptance
- **verify-aa-library-scan**: R14; check; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_command_facade.py::test_r14_no_se_workflow_store -q _(id: [rec-9f00ff4c-6d08-4671-81b9-11169db780ec](.artifacts/records/project__acceptance/rec-9f00ff4c-6d08-4671-81b9-11169db780ec.md))_

### Check
- **verify-aa-library-scan**: rec-9f00ff4c-6d08-4671-81b9-11169db780ec; 387d8d48aa0ddd88b9de581c2c52ae31c235655d; pass; check _(id: [rec-536ce38b-790e-4592-9aea-87f9fde8b22e](.artifacts/records/project__check-run/rec-536ce38b-790e-4592-9aea-87f9fde8b22e.md))_
- **verify-aa-library-scan**: rec-9f00ff4c-6d08-4671-81b9-11169db780ec; 206fcd0b22ed111d7a272c934bb1864271947591; pass; check _(id: [rec-bb4a3d69-86bc-4bf4-90c6-216e422d0bc6](.artifacts/records/project__check-run/rec-bb4a3d69-86bc-4bf4-90c6-216e422d0bc6.md))_

## verify-affidavit-library

### Acceptance
- **verify-affidavit-library**: R5; check; library-boundary; python3 -m pytest tests/test_store_client.py::test_store_client_no_adaptive_artifacts_process -q _(id: [rec-425c5e1a-aa1f-4b9b-a774-029d1e18b9bd](.artifacts/records/project__acceptance/rec-425c5e1a-aa1f-4b9b-a774-029d1e18b9bd.md))_

### Check
- **verify-affidavit-library**: rec-425c5e1a-aa1f-4b9b-a774-029d1e18b9bd; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; check _(id: [rec-97f8d71e-496c-4c26-845d-e5774307b89f](.artifacts/records/project__check-run/rec-97f8d71e-496c-4c26-845d-e5774307b89f.md))_

## verify-affidavit-library-help

### Acceptance
- **verify-affidavit-library-help**: R9; check; library-boundary; bin/aff --help | python3 -c "import sys; t=sys.stdin.read(); missing=[w for w in ('verdict','recheck','assertion-red') if w not in t]; assert not missing, missing" _(id: [rec-53ece8a3-1c43-4ec1-8462-77e90d36a79a](.artifacts/records/project__acceptance/rec-53ece8a3-1c43-4ec1-8462-77e90d36a79a.md))_

### Check
- **verify-affidavit-library-help**: rec-53ece8a3-1c43-4ec1-8462-77e90d36a79a; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; check _(id: [rec-3a8dbcf0-85a1-470f-a344-809c047f6c90](.artifacts/records/project__check-run/rec-3a8dbcf0-85a1-470f-a344-809c047f6c90.md))_

## verify-affidavit-library-nostore

### Acceptance
- **verify-affidavit-library-nostore**: R10; check; library-boundary; python3 -m pytest tests/test_verdict_gate.py::test_verdict_gate_without_store -q _(id: [rec-8634b6ff-5faf-4552-84ad-656408272281](.artifacts/records/project__acceptance/rec-8634b6ff-5faf-4552-84ad-656408272281.md))_

### Check
- **verify-affidavit-library-nostore**: rec-8634b6ff-5faf-4552-84ad-656408272281; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; check _(id: [rec-f42f1779-498e-48d9-9ba6-30af23c27724](.artifacts/records/project__check-run/rec-f42f1779-498e-48d9-9ba6-30af23c27724.md))_

## verify-affidavit-library-red

### Acceptance
- **verify-affidavit-library-red**: R7; check; library-boundary; python3 -m pytest tests/test_verdict_gate.py::test_verdict_gate_assertion_red_exits_zero -q _(id: [rec-c74119bf-2348-45d8-8aae-5e65b7e190a7](.artifacts/records/project__acceptance/rec-c74119bf-2348-45d8-8aae-5e65b7e190a7.md))_

### Check
- **verify-affidavit-library-red**: rec-c74119bf-2348-45d8-8aae-5e65b7e190a7; 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538; pass; check _(id: [rec-daa17883-ea4a-4de4-8dcb-85d2864d76a7](.artifacts/records/project__check-run/rec-daa17883-ea4a-4de4-8dcb-85d2864d76a7.md))_

## verify-atomic-claims

### Acceptance
- **verify-atomic-claims**: R6; tdd; workflow-loop; python3 -m pytest tests/test_plan_trace.py -k 'thin_deliver and (capture or create or cli)' -q _(id: [rec-0cd6c518-1e3e-4149-8bbe-595d2465cdca](.artifacts/records/project__acceptance/rec-0cd6c518-1e3e-4149-8bbe-595d2465cdca.md))_

### Check
- **verify-atomic-claims**: rec-0cd6c518-1e3e-4149-8bbe-595d2465cdca; 464d6813f21f624097f5bfbfb293c8ede2478e49; fail; tdd _(id: [rec-1210bd14-9aeb-4ef1-b4a4-9d5b2b76f02b](.artifacts/records/project__check-run/rec-1210bd14-9aeb-4ef1-b4a4-9d5b2b76f02b.md))_
- **verify-atomic-claims**: rec-0cd6c518-1e3e-4149-8bbe-595d2465cdca; 3b2f808f60f93b4db108543986be05d184226566; pass; tdd _(id: [rec-2c960c5e-7be0-451c-bb3e-584e220cae76](.artifacts/records/project__check-run/rec-2c960c5e-7be0-451c-bb3e-584e220cae76.md))_
- **verify-atomic-claims**: rec-0cd6c518-1e3e-4149-8bbe-595d2465cdca; 50303893af61c747620551cd512239752b0528a1; pass; tdd _(id: [rec-a2e34148-a8b4-46e6-af13-d889aeb9c40d](.artifacts/records/project__check-run/rec-a2e34148-a8b4-46e6-af13-d889aeb9c40d.md))_
- **verify-atomic-claims**: rec-0cd6c518-1e3e-4149-8bbe-595d2465cdca; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; tdd _(id: [rec-d5549e61-cf67-43db-b15d-e13f4ec0b860](.artifacts/records/project__check-run/rec-d5549e61-cf67-43db-b15d-e13f4ec0b860.md))_

## verify-atomic-claims-contract

### Acceptance
- **verify-atomic-claims-contract**: R4; check; workflow-loop; python3 -m pytest tests/test_plan_trace.py -k criterion_optional_in_contract -q _(id: [rec-f6cf9299-6647-4ad0-b659-e4d890f6f3c3](.artifacts/records/project__acceptance/rec-f6cf9299-6647-4ad0-b659-e4d890f6f3c3.md))_

### Check
- **verify-atomic-claims-contract**: rec-f6cf9299-6647-4ad0-b659-e4d890f6f3c3; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-477b9291-31fa-4db1-9e05-902c07da1a7a](.artifacts/records/project__check-run/rec-477b9291-31fa-4db1-9e05-902c07da1a7a.md))_
- **verify-atomic-claims-contract**: rec-f6cf9299-6647-4ad0-b659-e4d890f6f3c3; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; check _(id: [rec-c315552f-a014-4323-bf84-2d406f4395a7](.artifacts/records/project__check-run/rec-c315552f-a014-4323-bf84-2d406f4395a7.md))_
- **verify-atomic-claims-contract**: rec-f6cf9299-6647-4ad0-b659-e4d890f6f3c3; 3b2f808f60f93b4db108543986be05d184226566; pass; check _(id: [rec-c353b2cb-5f03-4a8c-aa05-fe4dc0c5b581](.artifacts/records/project__check-run/rec-c353b2cb-5f03-4a8c-aa05-fe4dc0c5b581.md))_

## verify-atomic-claims-pytest

### Acceptance
- **verify-atomic-claims-pytest**: R6; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q _(id: [rec-e1380e66-3c40-4868-b412-12685050d7fd](.artifacts/records/project__acceptance/rec-e1380e66-3c40-4868-b412-12685050d7fd.md))_

### Check
- **verify-atomic-claims-pytest**: rec-e1380e66-3c40-4868-b412-12685050d7fd; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-44265bf0-a53c-477b-ba0a-106793305a01](.artifacts/records/project__check-run/rec-44265bf0-a53c-477b-ba0a-106793305a01.md))_
- **verify-atomic-claims-pytest**: rec-e1380e66-3c40-4868-b412-12685050d7fd; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; check _(id: [rec-5989ac83-4afa-4a3a-9b0b-23d6289ae218](.artifacts/records/project__check-run/rec-5989ac83-4afa-4a3a-9b0b-23d6289ae218.md))_
- **verify-atomic-claims-pytest**: rec-e1380e66-3c40-4868-b412-12685050d7fd; 3b2f808f60f93b4db108543986be05d184226566; pass; check _(id: [rec-83f49d0c-6adc-49e3-9fd4-c84204d2fef4](.artifacts/records/project__check-run/rec-83f49d0c-6adc-49e3-9fd4-c84204d2fef4.md))_

## verify-atomic-claims-skills

### Acceptance
- **verify-atomic-claims-skills**: R1; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q _(id: [rec-d0219464-ac52-415e-b926-d817876f0d8a](.artifacts/records/project__acceptance/rec-d0219464-ac52-415e-b926-d817876f0d8a.md))_

### Check
- **verify-atomic-claims-skills**: rec-d0219464-ac52-415e-b926-d817876f0d8a; 3b2f808f60f93b4db108543986be05d184226566; pass; check _(id: [rec-4697bb50-7c39-441a-a707-1e06ffcb070a](.artifacts/records/project__check-run/rec-4697bb50-7c39-441a-a707-1e06ffcb070a.md))_
- **verify-atomic-claims-skills**: rec-d0219464-ac52-415e-b926-d817876f0d8a; 50303893af61c747620551cd512239752b0528a1; pass; check _(id: [rec-6bb8fb98-b7e3-4d84-9e09-f5b5b95e6ae3](.artifacts/records/project__check-run/rec-6bb8fb98-b7e3-4d84-9e09-f5b5b95e6ae3.md))_
- **verify-atomic-claims-skills**: rec-d0219464-ac52-415e-b926-d817876f0d8a; 0cdee541c8b953f974e66ee9b99d79fa7eeccf26; pass; check _(id: [rec-dd491e60-fc28-49cf-a8c6-d8bd50fa1b07](.artifacts/records/project__check-run/rec-dd491e60-fc28-49cf-a8c6-d8bd50fa1b07.md))_

## verify-authority

### Acceptance
- **verify-authority**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_authority.py tests/test_skill_contract_consistency.py -q _(id: [rec-88c394e4-ca2e-45c8-a222-073b4b621bdd](.artifacts/records/project__acceptance/rec-88c394e4-ca2e-45c8-a222-073b4b621bdd.md))_

### Check
- **verify-authority**: rec-88c394e4-ca2e-45c8-a222-073b4b621bdd; 4bd42b96e925562686c726d6da61a27b99481255; pass; tdd _(id: [rec-36df2410-3b45-4803-bf95-3fca393989fe](.artifacts/records/project__check-run/rec-36df2410-3b45-4803-bf95-3fca393989fe.md))_

## verify-backlog-capture

### Acceptance
- **verify-backlog-capture**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_backlog_item.py -q _(id: [rec-91696e19-7aa5-4cf8-8215-8d8cf9f668df](.artifacts/records/project__acceptance/rec-91696e19-7aa5-4cf8-8215-8d8cf9f668df.md))_

### Check
- **verify-backlog-capture**: rec-91696e19-7aa5-4cf8-8215-8d8cf9f668df; 2ba3f658a6c7a374ef157640f4dd4a3024588e90; pass; tdd _(id: [rec-47c792b2-2a4c-4abb-90cb-10c624a2c9fd](.artifacts/records/project__check-run/rec-47c792b2-2a4c-4abb-90cb-10c624a2c9fd.md))_

## verify-backlog-capture-contract

### Acceptance
- **verify-backlog-capture-contract**: R1; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-2648b75d-644b-4eee-ba8d-4d1ff62f7f48](.artifacts/records/project__acceptance/rec-2648b75d-644b-4eee-ba8d-4d1ff62f7f48.md))_

### Check
- **verify-backlog-capture-contract**: rec-2648b75d-644b-4eee-ba8d-4d1ff62f7f48; 2ba3f658a6c7a374ef157640f4dd4a3024588e90; pass; check _(id: [rec-97baaa14-fc25-4b83-a734-e53b49728765](.artifacts/records/project__check-run/rec-97baaa14-fc25-4b83-a734-e53b49728765.md))_

## verify-backlog-capture-dashboard

### Acceptance
- **verify-backlog-capture-dashboard**: R6; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k backlog _(id: [rec-5607f8c7-adf7-44e7-89c3-fa6d5588b4ec](.artifacts/records/project__acceptance/rec-5607f8c7-adf7-44e7-89c3-fa6d5588b4ec.md))_

### Check
- **verify-backlog-capture-dashboard**: rec-5607f8c7-adf7-44e7-89c3-fa6d5588b4ec; 2ba3f658a6c7a374ef157640f4dd4a3024588e90; pass; tdd _(id: [rec-3ef4a9ef-2227-41b5-be04-18243536b5cc](.artifacts/records/project__check-run/rec-3ef4a9ef-2227-41b5-be04-18243536b5cc.md))_

## verify-backlog-capture-skills

### Acceptance
- **verify-backlog-capture-skills**: R2; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-f9cf16cd-69d0-4a84-86aa-b134b078c167](.artifacts/records/project__acceptance/rec-f9cf16cd-69d0-4a84-86aa-b134b078c167.md))_

### Check
- **verify-backlog-capture-skills**: rec-f9cf16cd-69d0-4a84-86aa-b134b078c167; 2ba3f658a6c7a374ef157640f4dd4a3024588e90; pass; check _(id: [rec-077b461e-5d00-4c30-8e8d-b8fab0b2e996](.artifacts/records/project__check-run/rec-077b461e-5d00-4c30-8e8d-b8fab0b2e996.md))_

## verify-check-runner

### Acceptance
- **verify-check-runner**: R7; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k "pass or fail or blocked or integration or cli" _(id: [rec-89a78033-b672-4f71-9f59-10deea6ef8bf](.artifacts/records/project__acceptance/rec-89a78033-b672-4f71-9f59-10deea6ef8bf.md))_

### Check
- **verify-check-runner**: rec-89a78033-b672-4f71-9f59-10deea6ef8bf; 4bd42b96e925562686c726d6da61a27b99481255; pass; tdd _(id: [rec-1cf0921c-d6f8-4b07-91c0-982887547c2b](.artifacts/records/project__check-run/rec-1cf0921c-d6f8-4b07-91c0-982887547c2b.md))_

## verify-check-runner-commit

### Acceptance
- **verify-check-runner-commit**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_task_commit.py tests/test_execute_landing.py tests/test_skill_contract_consistency.py -q -k "commit or landing or task_commit" _(id: [rec-efdf2173-e187-41a1-a65f-9539da56742e](.artifacts/records/project__acceptance/rec-efdf2173-e187-41a1-a65f-9539da56742e.md))_

### Check
- **verify-check-runner-commit**: rec-efdf2173-e187-41a1-a65f-9539da56742e; 4bd42b96e925562686c726d6da61a27b99481255; pass; check _(id: [rec-3317616f-d1b1-4f1e-b6dd-28d4e910cbef](.artifacts/records/project__check-run/rec-3317616f-d1b1-4f1e-b6dd-28d4e910cbef.md))_

## verify-check-runner-contract

### Acceptance
- **verify-check-runner-contract**: R4; check; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py tests/test_evidence_loop.py tests/test_assess_routing.py -q -k "enum or result or method or contract" _(id: [rec-d00ce191-345a-46ed-9dc8-4c0242f31984](.artifacts/records/project__acceptance/rec-d00ce191-345a-46ed-9dc8-4c0242f31984.md))_

### Check
- **verify-check-runner-contract**: rec-d00ce191-345a-46ed-9dc8-4c0242f31984; 4bd42b96e925562686c726d6da61a27b99481255; pass; check _(id: [rec-cd7664df-a8ea-42c5-8d6c-bd73a246680d](.artifacts/records/project__check-run/rec-cd7664df-a8ea-42c5-8d6c-bd73a246680d.md))_

## verify-check-runner-dirty

### Acceptance
- **verify-check-runner-dirty**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k dirty _(id: [rec-5c18090c-ca0b-43a3-aa61-78ebd2383d7e](.artifacts/records/project__acceptance/rec-5c18090c-ca0b-43a3-aa61-78ebd2383d7e.md))_

### Check
- **verify-check-runner-dirty**: rec-5c18090c-ca0b-43a3-aa61-78ebd2383d7e; 4bd42b96e925562686c726d6da61a27b99481255; pass; tdd _(id: [rec-a82aad47-82a2-4024-9f31-14314ea0c2ab](.artifacts/records/project__check-run/rec-a82aad47-82a2-4024-9f31-14314ea0c2ab.md))_

## verify-check-runner-skills

### Acceptance
- **verify-check-runner-skills**: R5; check; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_authority.py tests/test_skill_contract_consistency.py -q _(id: [rec-a831be0f-059e-414e-90bb-36c485017676](.artifacts/records/project__acceptance/rec-a831be0f-059e-414e-90bb-36c485017676.md))_

### Check
- **verify-check-runner-skills**: rec-a831be0f-059e-414e-90bb-36c485017676; 4bd42b96e925562686c726d6da61a27b99481255; pass; check _(id: [rec-ce3653a8-b5bd-40e1-a2af-0f37ef5045a8](.artifacts/records/project__check-run/rec-ce3653a8-b5bd-40e1-a2af-0f37ef5045a8.md))_

## verify-claim-clocks

### Acceptance
- **verify-claim-clocks**: R1; check; library-boundary; python3 -m pytest tests/test_claim_clocks.py -q _(id: [rec-c70acbe0-be38-4b79-a60b-9ff96e705e35](.artifacts/records/project__acceptance/rec-c70acbe0-be38-4b79-a60b-9ff96e705e35.md))_

### Check
- **verify-claim-clocks**: rec-c70acbe0-be38-4b79-a60b-9ff96e705e35; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-702a5827-9200-41af-b37c-aec201b4a23a](.artifacts/records/project__check-run/rec-702a5827-9200-41af-b37c-aec201b4a23a.md))_
- **verify-claim-clocks**: rec-c70acbe0-be38-4b79-a60b-9ff96e705e35; 0eeb43affeac04a97c98250569a39cac9ab779a8; pass; check _(id: [rec-a7a27541-06c5-46c0-9022-80fe045b66e0](.artifacts/records/project__check-run/rec-a7a27541-06c5-46c0-9022-80fe045b66e0.md))_
- **verify-claim-clocks**: rec-c70acbe0-be38-4b79-a60b-9ff96e705e35; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-d7f1c886-279e-41e4-ad0a-9b83cf8d4a5f](.artifacts/records/project__check-run/rec-d7f1c886-279e-41e4-ad0a-9b83cf8d4a5f.md))_

## verify-claim-clocks-cli

### Acceptance
- **verify-claim-clocks-cli**: R9; check; library-boundary; python3 -m pytest tests/test_close_batch.py -k "cli and claim_gate" -q _(id: [rec-07f427f6-14c8-4b26-8ad0-54bad2e08b50](.artifacts/records/project__acceptance/rec-07f427f6-14c8-4b26-8ad0-54bad2e08b50.md))_

### Check
- **verify-claim-clocks-cli**: rec-07f427f6-14c8-4b26-8ad0-54bad2e08b50; 0eeb43affeac04a97c98250569a39cac9ab779a8; pass; check _(id: [rec-6a522846-52d0-4a1a-a5a0-94ddc28e51aa](.artifacts/records/project__check-run/rec-6a522846-52d0-4a1a-a5a0-94ddc28e51aa.md))_
- **verify-claim-clocks-cli**: rec-07f427f6-14c8-4b26-8ad0-54bad2e08b50; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-9d2eef61-d596-4c52-9f2a-7209bbc93e19](.artifacts/records/project__check-run/rec-9d2eef61-d596-4c52-9f2a-7209bbc93e19.md))_
- **verify-claim-clocks-cli**: rec-07f427f6-14c8-4b26-8ad0-54bad2e08b50; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-c7352b53-d2c2-40b0-b09e-4a644b92bcc7](.artifacts/records/project__check-run/rec-c7352b53-d2c2-40b0-b09e-4a644b92bcc7.md))_

## verify-claim-clocks-missing

### Acceptance
- **verify-claim-clocks-missing**: R8; check; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_missing_acceptance_refuses -q _(id: [rec-42e1e517-d39b-470f-9703-b097126fadbe](.artifacts/records/project__acceptance/rec-42e1e517-d39b-470f-9703-b097126fadbe.md))_

### Check
- **verify-claim-clocks-missing**: rec-42e1e517-d39b-470f-9703-b097126fadbe; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-4e228b05-cb61-458e-858a-759323d312ea](.artifacts/records/project__check-run/rec-4e228b05-cb61-458e-858a-759323d312ea.md))_
- **verify-claim-clocks-missing**: rec-42e1e517-d39b-470f-9703-b097126fadbe; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-86979f94-f85f-483a-9fca-7bf7c30480a0](.artifacts/records/project__check-run/rec-86979f94-f85f-483a-9fca-7bf7c30480a0.md))_
- **verify-claim-clocks-missing**: rec-42e1e517-d39b-470f-9703-b097126fadbe; 0eeb43affeac04a97c98250569a39cac9ab779a8; pass; check _(id: [rec-b8718afc-5aee-4232-b3ef-462d4fabc0ff](.artifacts/records/project__check-run/rec-b8718afc-5aee-4232-b3ef-462d4fabc0ff.md))_

## verify-claim-clocks-verdict

### Acceptance
- **verify-claim-clocks-verdict**: R5; check; library-boundary; python3 -m pytest tests/test_claim_clocks.py::test_verdict_only_failure_names_verdict -q _(id: [rec-e1ec0158-c053-4a12-bd35-76eb069e534e](.artifacts/records/project__acceptance/rec-e1ec0158-c053-4a12-bd35-76eb069e534e.md))_

### Check
- **verify-claim-clocks-verdict**: rec-e1ec0158-c053-4a12-bd35-76eb069e534e; b1fbb43a3a24e4f8750bc7e729efd5d1836c47b2; pass; check _(id: [rec-b4e2dde0-176d-4e81-9125-f11f308de352](.artifacts/records/project__check-run/rec-b4e2dde0-176d-4e81-9125-f11f308de352.md))_
- **verify-claim-clocks-verdict**: rec-e1ec0158-c053-4a12-bd35-76eb069e534e; 0eeb43affeac04a97c98250569a39cac9ab779a8; pass; check _(id: [rec-b540a3a5-42a3-4d4d-bee5-78cf9c06d162](.artifacts/records/project__check-run/rec-b540a3a5-42a3-4d4d-bee5-78cf9c06d162.md))_
- **verify-claim-clocks-verdict**: rec-e1ec0158-c053-4a12-bd35-76eb069e534e; aa1d6be21a26e2ff7674deef9a84ab9112fef763; pass; check _(id: [rec-cc14f8c4-00a9-4068-abba-34caed767bb3](.artifacts/records/project__check-run/rec-cc14f8c4-00a9-4068-abba-34caed767bb3.md))_

## verify-claim-witnesses

### Acceptance
- **verify-claim-witnesses**: R1; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'cli and (fabricated or store_authority or mismatch)' -q _(id: [rec-7252d501-3ecd-40b3-8c19-db0da8a5c8a0](.artifacts/records/project__acceptance/rec-7252d501-3ecd-40b3-8c19-db0da8a5c8a0.md))_

### Check
- **verify-claim-witnesses**: rec-7252d501-3ecd-40b3-8c19-db0da8a5c8a0; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-41136e8a-310b-4497-890c-0f68f5c7e159](.artifacts/records/project__check-run/rec-41136e8a-310b-4497-890c-0f68f5c7e159.md))_
- **verify-claim-witnesses**: rec-7252d501-3ecd-40b3-8c19-db0da8a5c8a0; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-7b2bf65d-f1b6-4158-8c5a-e14012b93873](.artifacts/records/project__check-run/rec-7b2bf65d-f1b6-4158-8c5a-e14012b93873.md))_
- **verify-claim-witnesses**: rec-7252d501-3ecd-40b3-8c19-db0da8a5c8a0; dirty; fail; tdd _(id: [rec-9d792a11-4dfb-4ea3-98c9-b2c93e8aef47](.artifacts/records/project__check-run/rec-9d792a11-4dfb-4ea3-98c9-b2c93e8aef47.md))_

## verify-claim-witnesses-contract

### Acceptance
- **verify-claim-witnesses-contract**: R1; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-b50e926c-44f1-4c9a-80bb-af8bef0fd0de](.artifacts/records/project__acceptance/rec-b50e926c-44f1-4c9a-80bb-af8bef0fd0de.md))_

### Check
- **verify-claim-witnesses-contract**: rec-b50e926c-44f1-4c9a-80bb-af8bef0fd0de; d680521c3270c954d22b915c641c7e733595599f; pass; check _(id: [rec-164dd043-024a-4c3b-9a72-f7671d3219c6](.artifacts/records/project__check-run/rec-164dd043-024a-4c3b-9a72-f7671d3219c6.md))_

## verify-claim-witnesses-mutants

### Acceptance
- **verify-claim-witnesses-mutants**: R6; check; workflow-loop; python3 -m pytest tests/test_close_batch.py tests/test_affidavit_check.py -q _(id: [rec-4d4ab5a3-2608-4a28-a070-8d07d2bcf3f4](.artifacts/records/project__acceptance/rec-4d4ab5a3-2608-4a28-a070-8d07d2bcf3f4.md))_

### Check
- **verify-claim-witnesses-mutants**: rec-4d4ab5a3-2608-4a28-a070-8d07d2bcf3f4; d680521c3270c954d22b915c641c7e733595599f; pass; check _(id: [rec-85842156-7206-4b96-b4ea-d3bc1e348f22](.artifacts/records/project__check-run/rec-85842156-7206-4b96-b4ea-d3bc1e348f22.md))_

## verify-claim-witnesses-tdd-revision

### Acceptance
- **verify-claim-witnesses-tdd-revision**: R3; check; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'tdd_revision_without_red or revision_allowed_tdd' -q _(id: [rec-b059420c-342e-47a1-b52b-9d0103494e1c](.artifacts/records/project__acceptance/rec-b059420c-342e-47a1-b52b-9d0103494e1c.md))_

### Check
- **verify-claim-witnesses-tdd-revision**: rec-b059420c-342e-47a1-b52b-9d0103494e1c; d680521c3270c954d22b915c641c7e733595599f; pass; check _(id: [rec-afc2606a-7619-429c-ae05-c451e9719d20](.artifacts/records/project__check-run/rec-afc2606a-7619-429c-ae05-c451e9719d20.md))_

## verify-claim-witnesses-worktree

### Acceptance
- **verify-claim-witnesses-worktree**: R5; check; workflow-loop; python3 -m pytest tests/test_affidavit_check.py tests/test_close_batch.py -k 'worktree or cwd_primary or store_cwd' -q _(id: [rec-c63b67b2-6f9b-4a18-a1a7-901f75846af3](.artifacts/records/project__acceptance/rec-c63b67b2-6f9b-4a18-a1a7-901f75846af3.md))_

### Check
- **verify-claim-witnesses-worktree**: rec-c63b67b2-6f9b-4a18-a1a7-901f75846af3; d680521c3270c954d22b915c641c7e733595599f; pass; check _(id: [rec-b9f1fc89-3edc-4b4f-a430-e809670e2c77](.artifacts/records/project__check-run/rec-b9f1fc89-3edc-4b4f-a430-e809670e2c77.md))_

## verify-cross-harness-install

### Acceptance
- **verify-cross-harness-install**: R1; check; packaging; python3 -m pytest tests/test_skill_portability.py -q _(id: [rec-fafaad86-e26f-4d73-b5fa-73bcca66f5ac](.artifacts/records/project__acceptance/rec-fafaad86-e26f-4d73-b5fa-73bcca66f5ac.md))_

### Check
- **verify-cross-harness-install**: rec-fafaad86-e26f-4d73-b5fa-73bcca66f5ac; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-639ce80e-3375-4bc8-a56b-5add4c3527d1](.artifacts/records/project__check-run/rec-639ce80e-3375-4bc8-a56b-5add4c3527d1.md))_
- **verify-cross-harness-install**: rec-fafaad86-e26f-4d73-b5fa-73bcca66f5ac; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-fa718908-646e-468b-93e7-c65b83ba18c0](.artifacts/records/project__check-run/rec-fa718908-646e-468b-93e7-c65b83ba18c0.md))_

## verify-cross-harness-install-agent

### Acceptance
- **verify-cross-harness-install-agent**: R13; check; packaging; python3 -m pytest tests/test_agent_generation.py -q _(id: [rec-0e6b1bc4-d41f-461a-9964-42208f5109f6](.artifacts/records/project__acceptance/rec-0e6b1bc4-d41f-461a-9964-42208f5109f6.md))_

### Check
- **verify-cross-harness-install-agent**: rec-0e6b1bc4-d41f-461a-9964-42208f5109f6; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-006aa146-30fd-44ef-82ac-3c2cee2dd8bc](.artifacts/records/project__check-run/rec-006aa146-30fd-44ef-82ac-3c2cee2dd8bc.md))_
- **verify-cross-harness-install-agent**: rec-0e6b1bc4-d41f-461a-9964-42208f5109f6; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-9d7bd1fa-c090-4896-94ee-211f34f6dab3](.artifacts/records/project__check-run/rec-9d7bd1fa-c090-4896-94ee-211f34f6dab3.md))_

## verify-cross-harness-install-allowlist

### Acceptance
- **verify-cross-harness-install-allowlist**: R14; check; packaging; python3 -m pytest tests/test_installer.py -q -k allowlist _(id: [rec-ac3770b6-615a-446f-9a0a-65278e1eef1e](.artifacts/records/project__acceptance/rec-ac3770b6-615a-446f-9a0a-65278e1eef1e.md))_

### Check
- **verify-cross-harness-install-allowlist**: rec-ac3770b6-615a-446f-9a0a-65278e1eef1e; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-054967c3-2496-442c-b64d-70a9f9152127](.artifacts/records/project__check-run/rec-054967c3-2496-442c-b64d-70a9f9152127.md))_
- **verify-cross-harness-install-allowlist**: rec-ac3770b6-615a-446f-9a0a-65278e1eef1e; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-4e213071-d0f4-49e5-af8e-512879f317e2](.artifacts/records/project__check-run/rec-4e213071-d0f4-49e5-af8e-512879f317e2.md))_

## verify-cross-harness-install-cli

### Acceptance
- **verify-cross-harness-install-cli**: R5; check; packaging; python3 -m pytest tests/integration/test_cli_on_path.py -q _(id: [rec-e7ad94e4-40ae-4238-be13-de5a96665831](.artifacts/records/project__acceptance/rec-e7ad94e4-40ae-4238-be13-de5a96665831.md))_

### Check
- **verify-cross-harness-install-cli**: rec-e7ad94e4-40ae-4238-be13-de5a96665831; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-1dab18f3-e2d6-45d4-a0df-77688b962f1b](.artifacts/records/project__check-run/rec-1dab18f3-e2d6-45d4-a0df-77688b962f1b.md))_
- **verify-cross-harness-install-cli**: rec-e7ad94e4-40ae-4238-be13-de5a96665831; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-58f49a37-96e9-423d-bbb1-38bb4346a66f](.artifacts/records/project__check-run/rec-58f49a37-96e9-423d-bbb1-38bb4346a66f.md))_

## verify-cross-harness-install-docs

### Acceptance
- **verify-cross-harness-install-docs**: R15; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q _(id: [rec-8075e775-e831-46ba-8279-a733f640230f](.artifacts/records/project__acceptance/rec-8075e775-e831-46ba-8279-a733f640230f.md))_

### Check
- **verify-cross-harness-install-docs**: rec-8075e775-e831-46ba-8279-a733f640230f; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-509c1e43-2b4c-477b-b8be-321e98414a12](.artifacts/records/project__check-run/rec-509c1e43-2b4c-477b-b8be-321e98414a12.md))_
- **verify-cross-harness-install-docs**: rec-8075e775-e831-46ba-8279-a733f640230f; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-90ba9ac2-93ea-4b18-8bf1-332d8dff418f](.artifacts/records/project__check-run/rec-90ba9ac2-93ea-4b18-8bf1-332d8dff418f.md))_

## verify-cross-harness-install-hosts

### Acceptance
- **verify-cross-harness-install-hosts**: R12; check; packaging; python3 -m pytest tests/integration/test_temp_home_install.py -q _(id: [rec-053c64ab-c952-45da-9a00-fbd2fb9b1b2d](.artifacts/records/project__acceptance/rec-053c64ab-c952-45da-9a00-fbd2fb9b1b2d.md))_

### Check
- **verify-cross-harness-install-hosts**: rec-053c64ab-c952-45da-9a00-fbd2fb9b1b2d; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-24eabff7-cc9e-4b5c-b5eb-2a44b491236b](.artifacts/records/project__check-run/rec-24eabff7-cc9e-4b5c-b5eb-2a44b491236b.md))_
- **verify-cross-harness-install-hosts**: rec-053c64ab-c952-45da-9a00-fbd2fb9b1b2d; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-5f2fa860-2c5c-4ef0-b356-05fb7704462b](.artifacts/records/project__check-run/rec-5f2fa860-2c5c-4ef0-b356-05fb7704462b.md))_

## verify-cross-harness-install-idempotent

### Acceptance
- **verify-cross-harness-install-idempotent**: R9; check; packaging; python3 -m pytest tests/test_installer.py -q -k idempotent _(id: [rec-acfbb12a-ebd9-4870-aa4b-e056f7c9abd7](.artifacts/records/project__acceptance/rec-acfbb12a-ebd9-4870-aa4b-e056f7c9abd7.md))_

### Check
- **verify-cross-harness-install-idempotent**: rec-acfbb12a-ebd9-4870-aa4b-e056f7c9abd7; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-44374736-6a91-4dbe-acff-5d217f8eca0b](.artifacts/records/project__check-run/rec-44374736-6a91-4dbe-acff-5d217f8eca0b.md))_
- **verify-cross-harness-install-idempotent**: rec-acfbb12a-ebd9-4870-aa4b-e056f7c9abd7; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-7ffe3239-13ee-410f-9e50-7f0c45cd20d7](.artifacts/records/project__check-run/rec-7ffe3239-13ee-410f-9e50-7f0c45cd20d7.md))_

## verify-cross-harness-install-matrix

### Acceptance
- **verify-cross-harness-install-matrix**: R8; check; packaging; python3 -m pytest tests/test_installer.py -q -k flags _(id: [rec-9810dc0f-203f-4021-8cd3-2a4551476d7c](.artifacts/records/project__acceptance/rec-9810dc0f-203f-4021-8cd3-2a4551476d7c.md))_

### Check
- **verify-cross-harness-install-matrix**: rec-9810dc0f-203f-4021-8cd3-2a4551476d7c; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-0565e479-8b0b-4c1b-82e5-5052b90175a9](.artifacts/records/project__check-run/rec-0565e479-8b0b-4c1b-82e5-5052b90175a9.md))_
- **verify-cross-harness-install-matrix**: rec-9810dc0f-203f-4021-8cd3-2a4551476d7c; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-69d35ef3-c31b-4d16-868a-c45b988b89c3](.artifacts/records/project__check-run/rec-69d35ef3-c31b-4d16-868a-c45b988b89c3.md))_

## verify-cross-harness-install-native

### Acceptance
- **verify-cross-harness-install-native**: R10; check; packaging; python3 -m pytest tests/test_installer.py -q -k native _(id: [rec-c973b40f-0b61-4a16-9292-6906e6e1b14a](.artifacts/records/project__acceptance/rec-c973b40f-0b61-4a16-9292-6906e6e1b14a.md))_

### Check
- **verify-cross-harness-install-native**: rec-c973b40f-0b61-4a16-9292-6906e6e1b14a; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-a9d78b86-9989-4616-9336-198edccfb20e](.artifacts/records/project__check-run/rec-a9d78b86-9989-4616-9336-198edccfb20e.md))_
- **verify-cross-harness-install-native**: rec-c973b40f-0b61-4a16-9292-6906e6e1b14a; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-bb64310e-15cd-4aea-b776-639e6a599033](.artifacts/records/project__check-run/rec-bb64310e-15cd-4aea-b776-639e6a599033.md))_

## verify-cross-harness-install-paths

### Acceptance
- **verify-cross-harness-install-paths**: R6; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k paths _(id: [rec-41da4b56-b406-46e9-8fd8-a22d73b568c9](.artifacts/records/project__acceptance/rec-41da4b56-b406-46e9-8fd8-a22d73b568c9.md))_

### Check
- **verify-cross-harness-install-paths**: rec-41da4b56-b406-46e9-8fd8-a22d73b568c9; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-395ae3a1-804c-490a-9b65-6d33b3d4084e](.artifacts/records/project__check-run/rec-395ae3a1-804c-490a-9b65-6d33b3d4084e.md))_
- **verify-cross-harness-install-paths**: rec-41da4b56-b406-46e9-8fd8-a22d73b568c9; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-401718bb-b33d-45d5-af11-d15b396e1250](.artifacts/records/project__check-run/rec-401718bb-b33d-45d5-af11-d15b396e1250.md))_

## verify-cross-harness-install-subcommands

### Acceptance
- **verify-cross-harness-install-subcommands**: R7; check; packaging; python3 -m pytest tests/test_cli_packaging.py -q -k subcommands _(id: [rec-47950663-6415-4f04-b860-65ea692e3e66](.artifacts/records/project__acceptance/rec-47950663-6415-4f04-b860-65ea692e3e66.md))_

### Check
- **verify-cross-harness-install-subcommands**: rec-47950663-6415-4f04-b860-65ea692e3e66; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-ba695d36-c279-4af2-abf6-93243c39799d](.artifacts/records/project__check-run/rec-ba695d36-c279-4af2-abf6-93243c39799d.md))_
- **verify-cross-harness-install-subcommands**: rec-47950663-6415-4f04-b860-65ea692e3e66; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-cd7c099d-8df0-40c1-a309-03278ba7bd42](.artifacts/records/project__check-run/rec-cd7c099d-8df0-40c1-a309-03278ba7bd42.md))_

## verify-cross-harness-install-tail

### Acceptance
- **verify-cross-harness-install-tail**: R11; check; packaging; python3 -m pytest tests/test_installer.py -q -k tail _(id: [rec-0d490c96-f704-422d-ad79-754e960d4715](.artifacts/records/project__acceptance/rec-0d490c96-f704-422d-ad79-754e960d4715.md))_

### Check
- **verify-cross-harness-install-tail**: rec-0d490c96-f704-422d-ad79-754e960d4715; b473060144dca418b3d6e7fea7e4616461bc1e9a; pass; check _(id: [rec-0dd54749-a181-4fee-b998-a525db6ec8ec](.artifacts/records/project__check-run/rec-0dd54749-a181-4fee-b998-a525db6ec8ec.md))_
- **verify-cross-harness-install-tail**: rec-0d490c96-f704-422d-ad79-754e960d4715; 48bcc343f9edcfd9338a6a497293aabd9cd52300; pass; check _(id: [rec-6f2c9cbe-e699-4631-8791-a4d31a380548](.artifacts/records/project__check-run/rec-6f2c9cbe-e699-4631-8791-a4d31a380548.md))_

## verify-dashboard-actions-phase

### Acceptance
- **verify-dashboard-actions-phase**: check; dashboard; uv run --with textual --with pytest python -m pytest tests -q _(id: [rec-468f8719-9cf5-4262-aea7-6d372a9cd6a9](.artifacts/records/project__acceptance/rec-468f8719-9cf5-4262-aea7-6d372a9cd6a9.md))_

### Check
- **verify-dashboard-actions-phase**: rec-468f8719-9cf5-4262-aea7-6d372a9cd6a9; 03d561c; pass; check _(id: [rec-5d987a65-62e1-4cdf-b91a-3ecf881ab599](.artifacts/records/project__check-run/rec-5d987a65-62e1-4cdf-b91a-3ecf881ab599.md))_

## verify-dashboard-actions-phase-signoff

### Acceptance
- **verify-dashboard-actions-phase-signoff**: manual; dashboard _(id: [rec-aa7012e9-f5d9-427c-a0d5-74e173544519](.artifacts/records/project__acceptance/rec-aa7012e9-f5d9-427c-a0d5-74e173544519.md))_

### Check
- **verify-dashboard-actions-phase-signoff**: rec-aa7012e9-f5d9-427c-a0d5-74e173544519; 03d561c; pass; manual; ayin _(id: [rec-78f4574a-6127-4ae1-96c4-73dc987b5fb5](.artifacts/records/project__check-run/rec-78f4574a-6127-4ae1-96c4-73dc987b5fb5.md))_

## verify-dashboard-approvals

### Acceptance
- **verify-dashboard-approvals**: R1; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k approval _(id: [rec-5b8ab6e4-d17d-479a-b038-38d2f8a03d1e](.artifacts/records/project__acceptance/rec-5b8ab6e4-d17d-479a-b038-38d2f8a03d1e.md))_

### Check
- **verify-dashboard-approvals**: rec-5b8ab6e4-d17d-479a-b038-38d2f8a03d1e; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; tdd _(id: [rec-9c48b2f5-2c80-48c2-9307-e09626304985](.artifacts/records/project__check-run/rec-9c48b2f5-2c80-48c2-9307-e09626304985.md))_

## verify-dashboard-approvals-constraints

### Acceptance
- **verify-dashboard-approvals-constraints**: R7; check; workflow-loop; /home/andrewyin/adaptive-artifacts/bin/adaptive-artifacts --store /home/andrewyin/se-workflow/.artifacts list --type project:constraint --state active | python3 -c "import sys,json; d=json.load(sys.stdin); stmts=[(r['subject'], (r.get('payload') or {}).get('statement') or '') for r in d['records']]; assert any(s=='dashboard-human-gate-writes' for s,_ in stmts); hg=[t for s,t in stmts if s=='dashboard-human-gate-writes']; assert hg and ('human Needs-you' in hg[0] or 'human-gate' in hg[0].lower()); old={'dashboard-read-only','dashboard-read-only-dashboard-bugfix','dashboard-read-only-dashboard-features'}; assert not any('never writes' in t.lower() for s,t in stmts if s in old); assert all('Retired' in t or 'dashboard-human-gate-writes' in t for s,t in stmts if s in old)" _(id: [rec-9c7c3c55-1e86-41fd-bb53-3c6f41567cf4](.artifacts/records/project__acceptance/rec-9c7c3c55-1e86-41fd-bb53-3c6f41567cf4.md))_

### Check
- **verify-dashboard-approvals-constraints**: rec-9c7c3c55-1e86-41fd-bb53-3c6f41567cf4; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; check _(id: [rec-3dedc0b5-6009-4849-95dc-65f6e62f939d](.artifacts/records/project__check-run/rec-3dedc0b5-6009-4849-95dc-65f6e62f939d.md))_
- **verify-dashboard-approvals-constraints**: rec-9c7c3c55-1e86-41fd-bb53-3c6f41567cf4; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; check _(id: [rec-a640fb3c-6ccb-44b0-b00e-2b19a18336a8](.artifacts/records/project__check-run/rec-a640fb3c-6ccb-44b0-b00e-2b19a18336a8.md))_

## verify-dashboard-approvals-docs

### Acceptance
- **verify-dashboard-approvals-docs**: R8; check; workflow-loop; grep -E 'Approve|Reject|Accept risk' README.md && uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-a764fa17-a012-4fec-8c30-4b0eb791b434](.artifacts/records/project__acceptance/rec-a764fa17-a012-4fec-8c30-4b0eb791b434.md))_

### Check
- **verify-dashboard-approvals-docs**: rec-a764fa17-a012-4fec-8c30-4b0eb791b434; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; check _(id: [rec-2217d59f-1402-4be9-933a-989549a02264](.artifacts/records/project__check-run/rec-2217d59f-1402-4be9-933a-989549a02264.md))_

## verify-dashboard-approvals-revision

### Acceptance
- **verify-dashboard-approvals-revision**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and stale' _(id: [rec-84aa203e-910a-40ea-a99b-1e0c3efdda28](.artifacts/records/project__acceptance/rec-84aa203e-910a-40ea-a99b-1e0c3efdda28.md))_

### Check
- **verify-dashboard-approvals-revision**: rec-84aa203e-910a-40ea-a99b-1e0c3efdda28; a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d; pass; tdd _(id: [rec-dbe073f3-68cf-48fe-95cc-be9663767655](.artifacts/records/project__check-run/rec-dbe073f3-68cf-48fe-95cc-be9663767655.md))_

## verify-dashboard-package

### Acceptance
- **verify-dashboard-package**: tdd; dashboard; uv run --with pytest --with textual pytest tests/test_dashboard_launcher.py tests/test_dashboard_integration.py _(id: [rec-f6216dac-0349-43a1-86a4-f5dd48eb2f51](.artifacts/records/project__acceptance/rec-f6216dac-0349-43a1-86a4-f5dd48eb2f51.md))_

### Check
- **verify-dashboard-package**: rec-f6216dac-0349-43a1-86a4-f5dd48eb2f51; dirty; pass; tdd _(id: [rec-15e73fc5-ec3f-4de8-8efe-703fdbb29ff3](.artifacts/records/project__check-run/rec-15e73fc5-ec3f-4de8-8efe-703fdbb29ff3.md))_
- **verify-dashboard-package**: rec-92205670-6c11-4582-8a88-f1b38046ccb8; dirty; pass; check _(id: [rec-5d354ac3-5272-44ce-9569-01bca5b201da](.artifacts/records/project__check-run/rec-5d354ac3-5272-44ce-9569-01bca5b201da.md))_
- **verify-dashboard-package**: rec-1d30f9a6-5236-45c6-8ba7-265bc6a9ca53; dirty; pass; check _(id: [rec-8b1dab0f-4baf-4743-9d66-bce1fc4aab1b](.artifacts/records/project__check-run/rec-8b1dab0f-4baf-4743-9d66-bce1fc4aab1b.md))_
- **verify-dashboard-package**: rec-02b72b32-48e0-46c4-a910-8b9d64ded6a5; dirty; pass; check _(id: [rec-c37483d8-fe5d-4ce7-ab6b-56f94388ee51](.artifacts/records/project__check-run/rec-c37483d8-fe5d-4ce7-ab6b-56f94388ee51.md))_
- **verify-dashboard-package**: rec-78759ece-bf5a-4584-9ce1-17650f1217c6; dirty; pass; check _(id: [rec-d9db7e39-b1a3-49bc-adb2-44bba4167033](.artifacts/records/project__check-run/rec-d9db7e39-b1a3-49bc-adb2-44bba4167033.md))_

## verify-dashboard-package-entry-points

### Acceptance
- **verify-dashboard-package-entry-points**: check; dashboard; uv run --with pytest --with textual pytest -m tmux tests/test_tmux_integration.py tests/test_e2e_dashboard.py _(id: [rec-92205670-6c11-4582-8a88-f1b38046ccb8](.artifacts/records/project__acceptance/rec-92205670-6c11-4582-8a88-f1b38046ccb8.md))_

## verify-dashboard-package-full-suite

### Acceptance
- **verify-dashboard-package-full-suite**: check; dashboard; uv run --with pytest --with textual pytest _(id: [rec-02b72b32-48e0-46c4-a910-8b9d64ded6a5](.artifacts/records/project__acceptance/rec-02b72b32-48e0-46c4-a910-8b9d64ded6a5.md))_

## verify-dashboard-package-outside-scripts

### Acceptance
- **verify-dashboard-package-outside-scripts**: check; dashboard; test -f dashboard/app.py && test -f dashboard/model.py && ! ls scripts | grep -i dashboard _(id: [rec-78759ece-bf5a-4584-9ce1-17650f1217c6](.artifacts/records/project__acceptance/rec-78759ece-bf5a-4584-9ce1-17650f1217c6.md))_

## verify-dashboard-package-task-modules

### Acceptance
- **verify-dashboard-package-task-modules**: check; dashboard; test -f dashboard/tasks.py && test -f dashboard/task_detail.py && ! grep -nE '^class (TaskFilter|TaskTable|TaskDetailScreen)' dashboard/app.py _(id: [rec-1d30f9a6-5236-45c6-8ba7-265bc6a9ca53](.artifacts/records/project__acceptance/rec-1d30f9a6-5236-45c6-8ba7-265bc6a9ca53.md))_

## verify-dashboard-view-phase

### Acceptance
- **verify-dashboard-view-phase**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests/test_dashboard_integration.py -q _(id: [rec-35c98548-4ccf-4c7c-8286-3a1e7ba21185](.artifacts/records/project__acceptance/rec-35c98548-4ccf-4c7c-8286-3a1e7ba21185.md))_

### Check
- **verify-dashboard-view-phase**: rec-83fc3486-af5f-49af-9000-8d9fd6890f3c; 5ba4e0a; pass; manual; ayin _(id: [rec-2141a70f-c8a2-4b54-ae34-9dc12cbf02f2](.artifacts/records/project__check-run/rec-2141a70f-c8a2-4b54-ae34-9dc12cbf02f2.md))_
- **verify-dashboard-view-phase**: rec-83fc3486-af5f-49af-9000-8d9fd6890f3c; 5ba4e0a; pass; manual _(id: [rec-8a7977e1-dba3-47b2-a074-5f9b6b91fe15](.artifacts/records/project__check-run/rec-8a7977e1-dba3-47b2-a074-5f9b6b91fe15.md))_
- **verify-dashboard-view-phase**: rec-1a3c142c-b9c6-4f57-baf0-b38000b5bb9f; 5ba4e0a; fail; check _(id: [rec-8c16b297-2e38-48b5-8259-b8c2211f2a1f](.artifacts/records/project__check-run/rec-8c16b297-2e38-48b5-8259-b8c2211f2a1f.md))_
- **verify-dashboard-view-phase**: rec-1a3c142c-b9c6-4f57-baf0-b38000b5bb9f; aa:92f1e0d se:5ba4e0a; pass; check _(id: [rec-dd5cd8a1-81be-4583-a6a3-c30f14c9a1e4](.artifacts/records/project__check-run/rec-dd5cd8a1-81be-4583-a6a3-c30f14c9a1e4.md))_
- **verify-dashboard-view-phase**: rec-35c98548-4ccf-4c7c-8286-3a1e7ba21185; 5ba4e0a; pass; tdd _(id: [rec-e8e1a102-2225-493f-9dfb-f1fa5c21e3f1](.artifacts/records/project__check-run/rec-e8e1a102-2225-493f-9dfb-f1fa5c21e3f1.md))_

## verify-dashboard-view-phase-live

### Acceptance
- **verify-dashboard-view-phase-live**: manual; dashboard; ~/adaptive-artifacts/bin/adaptive-artifacts --store ~/.artifacts/se-workflow view --id project:dashboard _(id: [rec-83fc3486-af5f-49af-9000-8d9fd6890f3c](.artifacts/records/project__acceptance/rec-83fc3486-af5f-49af-9000-8d9fd6890f3c.md))_

## verify-dashboard-view-phase-suites

### Acceptance
- **verify-dashboard-view-phase-suites**: check; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q && cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-1a3c142c-b9c6-4f57-baf0-b38000b5bb9f](.artifacts/records/project__acceptance/rec-1a3c142c-b9c6-4f57-baf0-b38000b5bb9f.md))_

## verify-declared-install

### Acceptance
- **verify-declared-install**: R5; check; library-boundary; python3 -m pytest tests/integration/test_declared_install.py::test_r5_clean_install_imports_adaptive_artifacts -q _(id: [rec-8bbf1c94-b713-40b2-8276-3eb2776fc6c4](.artifacts/records/project__acceptance/rec-8bbf1c94-b713-40b2-8276-3eb2776fc6c4.md))_

### Check
- **verify-declared-install**: rec-8bbf1c94-b713-40b2-8276-3eb2776fc6c4; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; check _(id: [rec-c0ce8fdc-646b-49f6-8f2a-f4215d8d94bc](.artifacts/records/project__check-run/rec-c0ce8fdc-646b-49f6-8f2a-f4215d8d94bc.md))_

## verify-declared-install-dep

### Acceptance
- **verify-declared-install-dep**: R2; check; library-boundary; python3 -c 'import pathlib; t=pathlib.Path("pyproject.toml").read_text(); i=t.index("\ndependencies"); chunk=t[i:t.index("]", i)]; assert "adaptive-artifacts" in chunk' _(id: [rec-0f038f9b-8c8a-4456-ba18-b7275a3bb606](.artifacts/records/project__acceptance/rec-0f038f9b-8c8a-4456-ba18-b7275a3bb606.md))_

### Check
- **verify-declared-install-dep**: rec-0f038f9b-8c8a-4456-ba18-b7275a3bb606; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; check _(id: [rec-e2861dbb-7537-4e48-9ab6-5992c5a10e16](.artifacts/records/project__check-run/rec-e2861dbb-7537-4e48-9ab6-5992c5a10e16.md))_

## verify-declared-install-evidence

### Acceptance
- **verify-declared-install-evidence**: R4; check; library-boundary; AFFIDAVIT_ROOT=/home/andrewyin/affidavit/.worktrees/declared-install python3 -m pytest tests/test_declared_install_metadata.py::test_r4_evidence_extra_depends_on_affidavit -q _(id: [rec-a00aba68-b59e-4995-8a43-a19dea5d5a19](.artifacts/records/project__acceptance/rec-a00aba68-b59e-4995-8a43-a19dea5d5a19.md))_

### Check
- **verify-declared-install-evidence**: rec-a00aba68-b59e-4995-8a43-a19dea5d5a19; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; check _(id: [rec-7b84e41d-20eb-41d2-a74b-2dd86ed704b9](.artifacts/records/project__check-run/rec-7b84e41d-20eb-41d2-a74b-2dd86ed704b9.md))_

## verify-declared-install-format

### Acceptance
- **verify-declared-install-format**: R8; check; library-boundary; PYTHONPATH=src python3 -m pytest tests/test_open_store_format.py::test_r8_open_store_raises_for_unsupported_contract_format -q _(id: [rec-afef7cfe-f35b-488b-a287-7d59e5fc7f01](.artifacts/records/project__acceptance/rec-afef7cfe-f35b-488b-a287-7d59e5fc7f01.md))_

### Check
- **verify-declared-install-format**: rec-afef7cfe-f35b-488b-a287-7d59e5fc7f01; 559343f7b683b2c79510e3b7781aba7a4e93721b; pass; check _(id: [rec-fb25513e-9343-4978-92bf-bd650402a13c](.artifacts/records/project__check-run/rec-fb25513e-9343-4978-92bf-bd650402a13c.md))_

## verify-declared-install-graph

### Acceptance
- **verify-declared-install-graph**: R1; check; library-boundary; AFFIDAVIT_ROOT=/home/andrewyin/affidavit/.worktrees/declared-install python3 -m pytest tests/test_declared_install_metadata.py::test_r1_affidavit_depends_on_adaptive_artifacts -q _(id: [rec-d44dfb91-18af-4277-9888-510b5cbc93b1](.artifacts/records/project__acceptance/rec-d44dfb91-18af-4277-9888-510b5cbc93b1.md))_

### Check
- **verify-declared-install-graph**: rec-d44dfb91-18af-4277-9888-510b5cbc93b1; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; check _(id: [rec-8e60120a-640e-4f62-8e6d-ba53708e269d](.artifacts/records/project__check-run/rec-8e60120a-640e-4f62-8e6d-ba53708e269d.md))_

## verify-declared-install-import

### Acceptance
- **verify-declared-install-import**: R7; check; library-boundary; PYTHONPATH=. python3 -c 'import os,subprocess; from pathlib import Path
for n in ("ADAPTIVE_ARTIFACTS_BIN","CLAUDE_PLUGIN_ROOT","CURSOR_PLUGIN_ROOT"): os.environ.pop(n, None)
seen=[]
real=subprocess.run
def spy(cmd,*a,**k):
 seen.append(cmd); return real(cmd,*a,**k)
subprocess.run=spy
import orchestra.aa as aa
aa.find_store_root(Path(".").resolve())
def bad(cmd):
 parts=cmd if isinstance(cmd,(list,tuple)) else [cmd]
 return any(Path(str(p)).name in {"adaptive-artifacts","artifacts.py"} for p in parts)
assert not any(bad(c) for c in seen)' _(id: [rec-fdd19c14-fa8d-4061-8515-8cc125edf745](.artifacts/records/project__acceptance/rec-fdd19c14-fa8d-4061-8515-8cc125edf745.md))_

### Check
- **verify-declared-install-import**: rec-fdd19c14-fa8d-4061-8515-8cc125edf745; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; check _(id: [rec-4c55f350-d049-4f07-9baa-f979fab45b63](.artifacts/records/project__check-run/rec-4c55f350-d049-4f07-9baa-f979fab45b63.md))_

## verify-declared-install-optional

### Acceptance
- **verify-declared-install-optional**: R3; check; library-boundary; python3 -c 'import pathlib; t=pathlib.Path("pyproject.toml").read_text(); i=t.index("\ndependencies"); chunk=t[i:t.index("]", i)]; assert "affidavit" not in chunk' _(id: [rec-f39eab16-ee60-4647-830f-ab158286834f](.artifacts/records/project__acceptance/rec-f39eab16-ee60-4647-830f-ab158286834f.md))_

### Check
- **verify-declared-install-optional**: rec-f39eab16-ee60-4647-830f-ab158286834f; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; check _(id: [rec-0a998141-a010-4682-8a9a-9fde297ee811](.artifacts/records/project__check-run/rec-0a998141-a010-4682-8a9a-9fde297ee811.md))_

## verify-declared-install-plain

### Acceptance
- **verify-declared-install-plain**: R6; check; library-boundary; python3 -m pytest tests/integration/test_declared_install.py::test_r6_plain_install_does_not_install_affidavit -q _(id: [rec-a81a959e-7010-439c-8d32-317ad6ea4c2d](.artifacts/records/project__acceptance/rec-a81a959e-7010-439c-8d32-317ad6ea4c2d.md))_

### Check
- **verify-declared-install-plain**: rec-a81a959e-7010-439c-8d32-317ad6ea4c2d; 993cf14ce58b162b8cfe000cca89f3dcc6397309; pass; check _(id: [rec-3a31b731-ac08-4d5a-a85c-c5da79b622d3](.artifacts/records/project__check-run/rec-3a31b731-ac08-4d5a-a85c-c5da79b622d3.md))_

## verify-deep-links

### Acceptance
- **verify-deep-links**: R1; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/links.test.ts src/deepLinks.test.ts _(id: [rec-958aa792-491a-4872-ab24-f443c5842736](.artifacts/records/project__acceptance/rec-958aa792-491a-4872-ab24-f443c5842736.md))_

### Check
- **verify-deep-links**: rec-958aa792-491a-4872-ab24-f443c5842736; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-409ebd90-75f2-44e3-a883-2673437c7ee0](.artifacts/records/project__check-run/rec-409ebd90-75f2-44e3-a883-2673437c7ee0.md))_
- **verify-deep-links**: rec-958aa792-491a-4872-ab24-f443c5842736; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-87412726-0932-4ecc-b7d8-5479b712749b](.artifacts/records/project__check-run/rec-87412726-0932-4ecc-b7d8-5479b712749b.md))_

## verify-deep-links-demo

### Acceptance
- **verify-deep-links-demo**: R1; manual; dashboard _(id: [rec-b330e8d6-0aa3-4a11-af82-c9a3927ce746](.artifacts/records/project__acceptance/rec-b330e8d6-0aa3-4a11-af82-c9a3927ce746.md))_

### Check
- **verify-deep-links-demo**: rec-b330e8d6-0aa3-4a11-af82-c9a3927ce746; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; manual; auto-web-calm _(id: [rec-4e78aaa7-0fc1-4455-a9f8-e634d6d2abe0](.artifacts/records/project__check-run/rec-4e78aaa7-0fc1-4455-a9f8-e634d6d2abe0.md))_

## verify-deep-links-labels

### Acceptance
- **verify-deep-links-labels**: R7; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/links.test.ts -t R7 _(id: [rec-1e1557cd-967c-47c4-acbe-6bc916c297f2](.artifacts/records/project__acceptance/rec-1e1557cd-967c-47c4-acbe-6bc916c297f2.md))_

### Check
- **verify-deep-links-labels**: rec-1e1557cd-967c-47c4-acbe-6bc916c297f2; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-67b90c8a-25a8-4cb6-b8a6-7db5ab95fb34](.artifacts/records/project__check-run/rec-67b90c8a-25a8-4cb6-b8a6-7db5ab95fb34.md))_

## verify-deep-links-plain

### Acceptance
- **verify-deep-links-plain**: R8; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/links.test.ts -t R8 _(id: [rec-a2b0a193-5ddc-4681-850d-74299b46b1a6](.artifacts/records/project__acceptance/rec-a2b0a193-5ddc-4681-850d-74299b46b1a6.md))_

### Check
- **verify-deep-links-plain**: rec-a2b0a193-5ddc-4681-850d-74299b46b1a6; 55ca9dc45d79f715d395b404e894194c3e1bc074; pass; check _(id: [rec-e8a0c1b2-f535-4c9e-bf96-9fd4dc80fbbe](.artifacts/records/project__check-run/rec-e8a0c1b2-f535-4c9e-bf96-9fd4dc80fbbe.md))_

## verify-end-to-end-phase

### Acceptance
- **verify-end-to-end-phase**: check; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q && cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-a5e71d14-1f25-4868-a42e-3a2b17e16616](.artifacts/records/project__acceptance/rec-a5e71d14-1f25-4868-a42e-3a2b17e16616.md))_

### Check
- **verify-end-to-end-phase**: rec-a5e71d14-1f25-4868-a42e-3a2b17e16616; aa:227523b se:a3b4ee2; pass; check _(id: [rec-01016663-beda-482a-810a-0d16bd2c46b8](.artifacts/records/project__check-run/rec-01016663-beda-482a-810a-0d16bd2c46b8.md))_
- **verify-end-to-end-phase**: rec-a5e71d14-1f25-4868-a42e-3a2b17e16616; dirty; pass; check _(id: [rec-2e3f5376-89d0-4d9f-8029-3bb418ae2ef8](.artifacts/records/project__check-run/rec-2e3f5376-89d0-4d9f-8029-3bb418ae2ef8.md))_
- **verify-end-to-end-phase**: rec-9dce7bb8-9cc7-4a4d-9ebd-48a749f7cc85; se:a3b4ee2; fail; check _(id: [rec-a746fedb-faa4-4de5-b32c-ba6466e9fad6](.artifacts/records/project__check-run/rec-a746fedb-faa4-4de5-b32c-ba6466e9fad6.md))_
- **verify-end-to-end-phase**: rec-9dce7bb8-9cc7-4a4d-9ebd-48a749f7cc85; dirty; pass; check _(id: [rec-ae0525f6-a5fc-45bc-ba9e-b3798959856f](.artifacts/records/project__check-run/rec-ae0525f6-a5fc-45bc-ba9e-b3798959856f.md))_

## verify-end-to-end-phase-clear

### Acceptance
- **verify-end-to-end-phase-clear**: check; dashboard; ~/se-workflow/scripts/dashboard-status ~/se-workflow _(id: [rec-9dce7bb8-9cc7-4a4d-9ebd-48a749f7cc85](.artifacts/records/project__acceptance/rec-9dce7bb8-9cc7-4a4d-9ebd-48a749f7cc85.md))_

## verify-estimate-view

### Acceptance
- **verify-estimate-view**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_header_sitting && uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m "not tmux" && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-9b9d3ec2-b413-4471-8991-8546a7f1c82b](.artifacts/records/project__acceptance/rec-9b9d3ec2-b413-4471-8991-8546a7f1c82b.md))_

### Check
- **verify-estimate-view**: rec-9b9d3ec2-b413-4471-8991-8546a7f1c82b; dirty; pass; check _(id: [rec-efe08a21-419f-4d83-807f-611eb22ffb33](.artifacts/records/project__check-run/rec-efe08a21-419f-4d83-807f-611eb22ffb33.md))_
- **verify-estimate-view**: rec-9b9d3ec2-b413-4471-8991-8546a7f1c82b; dirty; fail; check _(id: [rec-fa5a5160-58ea-4624-a2ea-a639be11ad07](.artifacts/records/project__check-run/rec-fa5a5160-58ea-4624-a2ea-a639be11ad07.md))_

## verify-estimate-view-chips

### Acceptance
- **verify-estimate-view-chips**: R6; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_estimate.py -q -k estimate_view_chips _(id: [rec-eae79ebb-8d5c-4378-b484-8ce816861f28](.artifacts/records/project__acceptance/rec-eae79ebb-8d5c-4378-b484-8ce816861f28.md))_

### Check
- **verify-estimate-view-chips**: rec-eae79ebb-8d5c-4378-b484-8ce816861f28; dirty; pass; check _(id: [rec-97cd4f75-7ba9-4354-afd0-d489e7b0e7ec](.artifacts/records/project__check-run/rec-97cd4f75-7ba9-4354-afd0-d489e7b0e7ec.md))_

## verify-estimate-view-clip

### Acceptance
- **verify-estimate-view-clip**: R5; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_clip _(id: [rec-e58b5f93-f9e3-4650-9853-ddcd0d0a0470](.artifacts/records/project__acceptance/rec-e58b5f93-f9e3-4650-9853-ddcd0d0a0470.md))_

### Check
- **verify-estimate-view-clip**: rec-e58b5f93-f9e3-4650-9853-ddcd0d0a0470; dirty; pass; check _(id: [rec-82298d56-6212-428e-bd49-994cd0f3af76](.artifacts/records/project__check-run/rec-82298d56-6212-428e-bd49-994cd0f3af76.md))_

## verify-estimate-view-contract

### Acceptance
- **verify-estimate-view-contract**: R7; check; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_blank_executor && test -z "$(git diff --name-only main -- contract/project-design.json)" _(id: [rec-7303a69d-1a5e-4661-b5c4-228c5b3dc28d](.artifacts/records/project__acceptance/rec-7303a69d-1a5e-4661-b5c4-228c5b3dc28d.md))_

### Check
- **verify-estimate-view-contract**: rec-7303a69d-1a5e-4661-b5c4-228c5b3dc28d; dirty; pass; check _(id: [rec-29e6fa05-2c7e-46bc-9313-aa2159a8812e](.artifacts/records/project__check-run/rec-29e6fa05-2c7e-46bc-9313-aa2159a8812e.md))_

## verify-estimate-view-suffix

### Acceptance
- **verify-estimate-view-suffix**: R4; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_title_suffix _(id: [rec-f812f0d8-f363-4ec3-b7c8-32463a0d9d0b](.artifacts/records/project__acceptance/rec-f812f0d8-f363-4ec3-b7c8-32463a0d9d0b.md))_

### Check
- **verify-estimate-view-suffix**: rec-f812f0d8-f363-4ec3-b7c8-32463a0d9d0b; dirty; pass; check _(id: [rec-a4023a51-d70b-4eb6-97fc-ac9e6a44ad3c](.artifacts/records/project__check-run/rec-a4023a51-d70b-4eb6-97fc-ac9e6a44ad3c.md))_

## verify-estimate-view-unset

### Acceptance
- **verify-estimate-view-unset**: R3; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k 'estimate_view_unset_count or estimate_view_header_partial' _(id: [rec-8b8345bb-5686-47dc-869d-39897b52c173](.artifacts/records/project__acceptance/rec-8b8345bb-5686-47dc-869d-39897b52c173.md))_

### Check
- **verify-estimate-view-unset**: rec-8b8345bb-5686-47dc-869d-39897b52c173; dirty; pass; check _(id: [rec-49ba2a0e-e84e-4124-9686-0f46a64882d8](.artifacts/records/project__check-run/rec-49ba2a0e-e84e-4124-9686-0f46a64882d8.md))_

## verify-estimate-view-wave

### Acceptance
- **verify-estimate-view-wave**: R2; check; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_wave_rule _(id: [rec-29ba3627-46df-4308-bae9-8939ff93b2f1](.artifacts/records/project__acceptance/rec-29ba3627-46df-4308-bae9-8939ff93b2f1.md))_

### Check
- **verify-estimate-view-wave**: rec-29ba3627-46df-4308-bae9-8939ff93b2f1; dirty; pass; check _(id: [rec-94e4eecc-6d14-489c-b911-6aed5d9bec61](.artifacts/records/project__check-run/rec-94e4eecc-6d14-489c-b911-6aed5d9bec61.md))_

## verify-evidence-authority

### Acceptance
- **verify-evidence-authority**: R3; check; workflow-loop; python3 -m pytest tests/test_close_batch.py tests/test_affidavit_check.py tests/test_affidavit_import_boundary.py -q -k 'runner or orchestra or aff or oracle or import or verdict or recheck or assertion' _(id: [rec-0f7ff4db-5a19-40ce-b16e-f2391360d473](.artifacts/records/project__acceptance/rec-0f7ff4db-5a19-40ce-b16e-f2391360d473.md))_

### Check
- **verify-evidence-authority**: rec-0f7ff4db-5a19-40ce-b16e-f2391360d473; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; check _(id: [rec-709ea2bd-983b-4f03-8f5a-7e1724d16edc](.artifacts/records/project__check-run/rec-709ea2bd-983b-4f03-8f5a-7e1724d16edc.md))_
- **verify-evidence-authority**: rec-0f7ff4db-5a19-40ce-b16e-f2391360d473; 46f7be3e4062d8f39f62c3dd22958eb97ec022ad; pass; check _(id: [rec-dcaba730-2a07-4a10-9f8a-fe180ae56d68](.artifacts/records/project__check-run/rec-dcaba730-2a07-4a10-9f8a-fe180ae56d68.md))_
- **verify-evidence-authority**: rec-0f7ff4db-5a19-40ce-b16e-f2391360d473; 46f7be3e4062d8f39f62c3dd22958eb97ec022ad; pass; check _(id: [rec-ff1bcfd4-043b-4aed-82df-d70504ecfe1a](.artifacts/records/project__check-run/rec-ff1bcfd4-043b-4aed-82df-d70504ecfe1a.md))_

## verify-evidence-authority-claim-gate

### Acceptance
- **verify-evidence-authority-claim-gate**: R5; check; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'verdict or recheck or manifest or claim_gate' _(id: [rec-2e6f3bf6-bce0-4fce-b17a-b313291a0a60](.artifacts/records/project__acceptance/rec-2e6f3bf6-bce0-4fce-b17a-b313291a0a60.md))_

### Check
- **verify-evidence-authority-claim-gate**: rec-2e6f3bf6-bce0-4fce-b17a-b313291a0a60; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; check _(id: [rec-8e73674e-9e50-413d-bd99-772867aa8459](.artifacts/records/project__check-run/rec-8e73674e-9e50-413d-bd99-772867aa8459.md))_
- **verify-evidence-authority-claim-gate**: rec-2e6f3bf6-bce0-4fce-b17a-b313291a0a60; 46f7be3e4062d8f39f62c3dd22958eb97ec022ad; pass; check _(id: [rec-9fbc3ae4-5126-491e-8bd1-cee3ec94813d](.artifacts/records/project__check-run/rec-9fbc3ae4-5126-491e-8bd1-cee3ec94813d.md))_

## verify-evidence-authority-skills

### Acceptance
- **verify-evidence-authority-skills**: R7; check; workflow-loop; python3 -m pytest tests/test_skill_runner_stamp.py -q _(id: [rec-74ba756f-c23b-41e2-8bf6-b77c600124da](.artifacts/records/project__acceptance/rec-74ba756f-c23b-41e2-8bf6-b77c600124da.md))_

### Check
- **verify-evidence-authority-skills**: rec-74ba756f-c23b-41e2-8bf6-b77c600124da; 46f7be3e4062d8f39f62c3dd22958eb97ec022ad; pass; check _(id: [rec-00811694-4c2c-4b72-9d6d-3ee981911624](.artifacts/records/project__check-run/rec-00811694-4c2c-4b72-9d6d-3ee981911624.md))_
- **verify-evidence-authority-skills**: rec-74ba756f-c23b-41e2-8bf6-b77c600124da; 7353a01f2b3f60dfe41543f6f527c59bc283e3a0; pass; check _(id: [rec-d27a337e-f954-40d0-90d3-ec3bcd10868a](.artifacts/records/project__check-run/rec-d27a337e-f954-40d0-90d3-ec3bcd10868a.md))_

## verify-evidence-loop

### Acceptance
- **verify-evidence-loop**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_evidence_loop.py -q _(id: [rec-c6f57f2f-cef8-4daf-b8f1-7899cd1a7e27](.artifacts/records/project__acceptance/rec-c6f57f2f-cef8-4daf-b8f1-7899cd1a7e27.md))_

### Check
- **verify-evidence-loop**: rec-a072e603-a6d5-4e9c-9f0d-2b55f6543af8; dirty; pass; check _(id: [rec-77720c61-994f-4b64-a26e-e8bfd14c8d46](.artifacts/records/project__check-run/rec-77720c61-994f-4b64-a26e-e8bfd14c8d46.md))_
- **verify-evidence-loop**: rec-a7ead56b-fe80-4a0d-a5ae-9b34a976c46f; dirty; pass; check _(id: [rec-b7fea9c3-cbe2-4442-976f-5714774f6bdd](.artifacts/records/project__check-run/rec-b7fea9c3-cbe2-4442-976f-5714774f6bdd.md))_
- **verify-evidence-loop**: rec-c6f57f2f-cef8-4daf-b8f1-7899cd1a7e27; dirty; pass; check _(id: [rec-cfe8b022-b5b2-4c6a-91bd-8dfecf1b156e](.artifacts/records/project__check-run/rec-cfe8b022-b5b2-4c6a-91bd-8dfecf1b156e.md))_
- **verify-evidence-loop**: rec-19a87492-4386-45cb-9b12-53cf66c22e09; dirty; pass; check _(id: [rec-dfb1b6e8-b07f-42b2-a6cc-671f86b19583](.artifacts/records/project__check-run/rec-dfb1b6e8-b07f-42b2-a6cc-671f86b19583.md))_

## verify-evidence-loop-contract

### Acceptance
- **verify-evidence-loop-contract**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-19a87492-4386-45cb-9b12-53cf66c22e09](.artifacts/records/project__acceptance/rec-19a87492-4386-45cb-9b12-53cf66c22e09.md))_

## verify-evidence-loop-readme

### Acceptance
- **verify-evidence-loop-readme**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_readme_lifecycle.py -q _(id: [rec-a072e603-a6d5-4e9c-9f0d-2b55f6543af8](.artifacts/records/project__acceptance/rec-a072e603-a6d5-4e9c-9f0d-2b55f6543af8.md))_

## verify-evidence-loop-skills

### Acceptance
- **verify-evidence-loop-skills**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_discuss_skill.py tests/test_plan_trace.py tests/test_integrate_rules.py tests/test_assess_routing.py -q _(id: [rec-a7ead56b-fe80-4a0d-a5ae-9b34a976c46f](.artifacts/records/project__acceptance/rec-a7ead56b-fe80-4a0d-a5ae-9b34a976c46f.md))_

## verify-evidence-matrix

### Acceptance
- **verify-evidence-matrix**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_requirement.py tests/test_dashboard_phase_screen.py -q -k matrix _(id: [rec-44755f3e-cfe0-44bf-8751-6f8850f4700a](.artifacts/records/project__acceptance/rec-44755f3e-cfe0-44bf-8751-6f8850f4700a.md))_

### Check
- **verify-evidence-matrix**: rec-44755f3e-cfe0-44bf-8751-6f8850f4700a; dirty; pass; check _(id: [rec-701861ae-0cbf-431d-b38f-8500d7ba6486](.artifacts/records/project__check-run/rec-701861ae-0cbf-431d-b38f-8500d7ba6486.md))_

## verify-evidence-matrix-suite

### Acceptance
- **verify-evidence-matrix-suite**: R8; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_requirement.py tests/test_dashboard_phase_screen.py -q -k matrix _(id: [rec-90a86f40-7f74-4dc3-875a-9d1043564b55](.artifacts/records/project__acceptance/rec-90a86f40-7f74-4dc3-875a-9d1043564b55.md))_

### Check
- **verify-evidence-matrix-suite**: rec-90a86f40-7f74-4dc3-875a-9d1043564b55; dirty; pass; check _(id: [rec-af62d62f-5d5b-4918-85b1-f1d681f7a05e](.artifacts/records/project__check-run/rec-af62d62f-5d5b-4918-85b1-f1d681f7a05e.md))_
- **verify-evidence-matrix-suite**: rec-242ca52f-0229-46fb-8334-e9d041b5c06d; dirty; pass; check _(id: [rec-db8ec3ec-aca0-46a3-b3ac-d073165f0ad7](.artifacts/records/project__check-run/rec-db8ec3ec-aca0-46a3-b3ac-d073165f0ad7.md))_

## verify-evidence-view

### Acceptance
- **verify-evidence-view**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_e2e_dashboard.py -q -m tmux -k evidence _(id: [rec-7ed13ebd-7b0a-436b-9c12-dfd4ef8cefcd](.artifacts/records/project__acceptance/rec-7ed13ebd-7b0a-436b-9c12-dfd4ef8cefcd.md))_

### Check
- **verify-evidence-view**: rec-7ed13ebd-7b0a-436b-9c12-dfd4ef8cefcd; dirty; pass; tdd _(id: [rec-e9556130-ae13-4c2f-9877-8be6e9aed7b5](.artifacts/records/project__check-run/rec-e9556130-ae13-4c2f-9877-8be6e9aed7b5.md))_

## verify-evidence-view-app

### Acceptance
- **verify-evidence-view-app**: R3; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_requirement.py -q _(id: [rec-08b630d4-2e32-4b18-a674-8d21a0733158](.artifacts/records/project__acceptance/rec-08b630d4-2e32-4b18-a674-8d21a0733158.md))_

### Check
- **verify-evidence-view-app**: rec-08b630d4-2e32-4b18-a674-8d21a0733158; dirty; pass; check _(id: [rec-c3d8c774-9eba-446a-851a-c14513e7f9f7](.artifacts/records/project__check-run/rec-c3d8c774-9eba-446a-851a-c14513e7f9f7.md))_

## verify-evidence-view-legacy

### Acceptance
- **verify-evidence-view-legacy**: R10; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and legacy' _(id: [rec-04bc526a-2703-4f22-8c56-9b068bc7869b](.artifacts/records/project__acceptance/rec-04bc526a-2703-4f22-8c56-9b068bc7869b.md))_

### Check
- **verify-evidence-view-legacy**: rec-04bc526a-2703-4f22-8c56-9b068bc7869b; dirty; pass; check _(id: [rec-16ef55d5-c4c5-42dd-9dc3-f12f8ed4711c](.artifacts/records/project__check-run/rec-16ef55d5-c4c5-42dd-9dc3-f12f8ed4711c.md))_

## verify-evidence-view-model

### Acceptance
- **verify-evidence-view-model**: R2; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k evidence _(id: [rec-ab6549b4-827c-4cb8-9fd1-4adcc54de77d](.artifacts/records/project__acceptance/rec-ab6549b4-827c-4cb8-9fd1-4adcc54de77d.md))_

### Check
- **verify-evidence-view-model**: rec-ab6549b4-827c-4cb8-9fd1-4adcc54de77d; dirty; pass; check _(id: [rec-571ad7b4-d991-4250-8066-99335077a868](.artifacts/records/project__check-run/rec-571ad7b4-d991-4250-8066-99335077a868.md))_

## verify-evidence-view-readme

### Acceptance
- **verify-evidence-view-readme**: R5; check; dashboard; grep -qi 'requirement detail' README.md && grep -q 'verified' README.md && grep -qi 'release ready' README.md && grep -qi 'stage' README.md _(id: [rec-338cf500-251e-4741-8168-ea67b1147ccc](.artifacts/records/project__acceptance/rec-338cf500-251e-4741-8168-ea67b1147ccc.md))_

### Check
- **verify-evidence-view-readme**: rec-338cf500-251e-4741-8168-ea67b1147ccc; dirty; pass; check _(id: [rec-869ea489-1127-4ac8-b27d-f003336f11d3](.artifacts/records/project__check-run/rec-869ea489-1127-4ac8-b27d-f003336f11d3.md))_

## verify-evidence-view-suite

### Acceptance
- **verify-evidence-view-suite**: R9; check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-ffb67717-3553-4bc6-9497-fb877731866f](.artifacts/records/project__acceptance/rec-ffb67717-3553-4bc6-9497-fb877731866f.md))_

### Check
- **verify-evidence-view-suite**: rec-ffb67717-3553-4bc6-9497-fb877731866f; dirty; pass; check _(id: [rec-546ad19a-e086-4be8-ad6d-39ff6135a78f](.artifacts/records/project__check-run/rec-546ad19a-e086-4be8-ad6d-39ff6135a78f.md))_

## verify-human-gates

### Acceptance
- **verify-human-gates**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_integration.py -q -k "gates or once" _(id: [rec-c61f4280-d622-4017-83d1-4a8222faed84](.artifacts/records/project__acceptance/rec-c61f4280-d622-4017-83d1-4a8222faed84.md))_

### Check
- **verify-human-gates**: rec-c61f4280-d622-4017-83d1-4a8222faed84; dirty; pass; check _(id: [rec-65fe5f9e-0653-44de-a8a1-b48a7afa10d3](.artifacts/records/project__check-run/rec-65fe5f9e-0653-44de-a8a1-b48a7afa10d3.md))_

## verify-human-gates-app

### Acceptance
- **verify-human-gates-app**: R3; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k gates _(id: [rec-d63e9f38-6953-44e4-a67f-8793531de963](.artifacts/records/project__acceptance/rec-d63e9f38-6953-44e4-a67f-8793531de963.md))_

### Check
- **verify-human-gates-app**: rec-d63e9f38-6953-44e4-a67f-8793531de963; dirty; pass; check _(id: [rec-92a4682a-8b32-4f73-bfcb-6d3c812c1af4](.artifacts/records/project__check-run/rec-92a4682a-8b32-4f73-bfcb-6d3c812c1af4.md))_

## verify-human-gates-model

### Acceptance
- **verify-human-gates-model**: R5; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_gates.py -q -k gates _(id: [rec-8ca825cb-80c2-47cc-9b12-ebfeb449dca9](.artifacts/records/project__acceptance/rec-8ca825cb-80c2-47cc-9b12-ebfeb449dca9.md))_

### Check
- **verify-human-gates-model**: rec-8ca825cb-80c2-47cc-9b12-ebfeb449dca9; dirty; pass; check _(id: [rec-882ec15d-d5e0-4cf1-b2cf-34855cb81c4a](.artifacts/records/project__check-run/rec-882ec15d-d5e0-4cf1-b2cf-34855cb81c4a.md))_

## verify-human-gates-suite

### Acceptance
- **verify-human-gates-suite**: R11; check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m "not tmux" && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-84b6b2c0-f0cc-49a6-93fd-ebd2e5390f9a](.artifacts/records/project__acceptance/rec-84b6b2c0-f0cc-49a6-93fd-ebd2e5390f9a.md))_

### Check
- **verify-human-gates-suite**: rec-84b6b2c0-f0cc-49a6-93fd-ebd2e5390f9a; dirty; pass; check _(id: [rec-4d33d4c5-08df-486b-99d0-ce5aab20392e](.artifacts/records/project__check-run/rec-4d33d4c5-08df-486b-99d0-ce5aab20392e.md))_

## verify-human-gates-tmux

### Acceptance
- **verify-human-gates-tmux**: R8; check; dashboard; uv run --with textual --with pytest python -m pytest tests -q -m tmux -k "status and (gates or needs or segment)" _(id: [rec-fa10fcaa-3669-4d69-a554-844faf4d41b6](.artifacts/records/project__acceptance/rec-fa10fcaa-3669-4d69-a554-844faf4d41b6.md))_

### Check
- **verify-human-gates-tmux**: rec-fa10fcaa-3669-4d69-a554-844faf4d41b6; dirty; pass; check _(id: [rec-281456a3-47c1-4258-b732-c664aa99a58b](.artifacts/records/project__check-run/rec-281456a3-47c1-4258-b732-c664aa99a58b.md))_

## verify-installer-wizard

### Acceptance
- **verify-installer-wizard**: R1; check; packaging; python3 -m pytest tests/integration/test_installer_wizard.py -q -k interactive _(id: [rec-acf4a6db-a339-4336-b3f3-0e8ac7c2de8e](.artifacts/records/project__acceptance/rec-acf4a6db-a339-4336-b3f3-0e8ac7c2de8e.md))_

### Check
- **verify-installer-wizard**: rec-acf4a6db-a339-4336-b3f3-0e8ac7c2de8e; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-935c2a8c-1adf-47ca-817f-054e9c09af1d](.artifacts/records/project__check-run/rec-935c2a8c-1adf-47ca-817f-054e9c09af1d.md))_
- **verify-installer-wizard**: rec-acf4a6db-a339-4336-b3f3-0e8ac7c2de8e; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-b4029575-9fbf-4970-9e4e-8dcb6c8db579](.artifacts/records/project__check-run/rec-b4029575-9fbf-4970-9e4e-8dcb6c8db579.md))_

## verify-installer-wizard-decline

### Acceptance
- **verify-installer-wizard-decline**: R9; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k decline_writes_nothing _(id: [rec-74169835-5c97-4b3e-9231-bffe6d6c030e](.artifacts/records/project__acceptance/rec-74169835-5c97-4b3e-9231-bffe6d6c030e.md))_

### Check
- **verify-installer-wizard-decline**: rec-74169835-5c97-4b3e-9231-bffe6d6c030e; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-2b5de2d2-e3c9-4d89-adc7-db8a30730f1a](.artifacts/records/project__check-run/rec-2b5de2d2-e3c9-4d89-adc7-db8a30730f1a.md))_
- **verify-installer-wizard-decline**: rec-74169835-5c97-4b3e-9231-bffe6d6c030e; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-fb8ece1c-be2a-477a-8a3e-4617562ee616](.artifacts/records/project__check-run/rec-fb8ece1c-be2a-477a-8a3e-4617562ee616.md))_

## verify-installer-wizard-detection

### Acceptance
- **verify-installer-wizard-detection**: R2; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k detect_hosts _(id: [rec-4530d459-8eb9-4209-a3ef-7e6c8f8de50d](.artifacts/records/project__acceptance/rec-4530d459-8eb9-4209-a3ef-7e6c8f8de50d.md))_

### Check
- **verify-installer-wizard-detection**: rec-4530d459-8eb9-4209-a3ef-7e6c8f8de50d; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-5a6c798f-344c-4c50-aa54-44a6c85486d8](.artifacts/records/project__check-run/rec-5a6c798f-344c-4c50-aa54-44a6c85486d8.md))_
- **verify-installer-wizard-detection**: rec-4530d459-8eb9-4209-a3ef-7e6c8f8de50d; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-89f15b67-70c9-4a47-a9ba-1e71d6aba00a](.artifacts/records/project__check-run/rec-89f15b67-70c9-4a47-a9ba-1e71d6aba00a.md))_

## verify-installer-wizard-docs

### Acceptance
- **verify-installer-wizard-docs**: R18; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q -k "wizard or documented_flags" _(id: [rec-1b604149-4595-4b3a-92d1-ead9d4b9777d](.artifacts/records/project__acceptance/rec-1b604149-4595-4b3a-92d1-ead9d4b9777d.md))_

### Check
- **verify-installer-wizard-docs**: rec-1b604149-4595-4b3a-92d1-ead9d4b9777d; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-4c3ad4b0-592f-4214-bf58-7bff0c11e709](.artifacts/records/project__check-run/rec-4c3ad4b0-592f-4214-bf58-7bff0c11e709.md))_
- **verify-installer-wizard-docs**: rec-1b604149-4595-4b3a-92d1-ead9d4b9777d; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-f1c857c3-f7a8-4ef2-b29d-bf65d4bb87d9](.artifacts/records/project__check-run/rec-f1c857c3-f7a8-4ef2-b29d-bf65d4bb87d9.md))_

## verify-installer-wizard-dry-run

### Acceptance
- **verify-installer-wizard-dry-run**: R16; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k dry_run_skips_confirmation _(id: [rec-f93569c3-5532-41a7-a270-7a5370d7169f](.artifacts/records/project__acceptance/rec-f93569c3-5532-41a7-a270-7a5370d7169f.md))_

### Check
- **verify-installer-wizard-dry-run**: rec-f93569c3-5532-41a7-a270-7a5370d7169f; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-3beadd7e-47e5-41de-b342-c0b4e0397f67](.artifacts/records/project__check-run/rec-3beadd7e-47e5-41de-b342-c0b4e0397f67.md))_
- **verify-installer-wizard-dry-run**: rec-f93569c3-5532-41a7-a270-7a5370d7169f; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-e4e8040f-8e37-4dc4-b72c-c3bac2dab5db](.artifacts/records/project__check-run/rec-e4e8040f-8e37-4dc4-b72c-c3bac2dab5db.md))_

## verify-installer-wizard-empty

### Acceptance
- **verify-installer-wizard-empty**: R14; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k no_detection_no_tty _(id: [rec-aa8e61d2-36cf-45f3-b20a-6486e51f00e2](.artifacts/records/project__acceptance/rec-aa8e61d2-36cf-45f3-b20a-6486e51f00e2.md))_

### Check
- **verify-installer-wizard-empty**: rec-aa8e61d2-36cf-45f3-b20a-6486e51f00e2; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-144e09ad-f5ca-4972-9ce9-16e5f2741ab7](.artifacts/records/project__check-run/rec-144e09ad-f5ca-4972-9ce9-16e5f2741ab7.md))_
- **verify-installer-wizard-empty**: rec-aa8e61d2-36cf-45f3-b20a-6486e51f00e2; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-51631791-38dc-45f3-a111-8e20c9916396](.artifacts/records/project__check-run/rec-51631791-38dc-45f3-a111-8e20c9916396.md))_

## verify-installer-wizard-explicit

### Acceptance
- **verify-installer-wizard-explicit**: R15; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k explicit_flags _(id: [rec-8e8f839f-0410-4871-9823-48a5f66a77bf](.artifacts/records/project__acceptance/rec-8e8f839f-0410-4871-9823-48a5f66a77bf.md))_

### Check
- **verify-installer-wizard-explicit**: rec-8e8f839f-0410-4871-9823-48a5f66a77bf; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-a9ba8e00-dc28-4cbe-a9d2-1dffe77aa2f3](.artifacts/records/project__check-run/rec-a9ba8e00-dc28-4cbe-a9d2-1dffe77aa2f3.md))_
- **verify-installer-wizard-explicit**: rec-8e8f839f-0410-4871-9823-48a5f66a77bf; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-c49fe638-b475-4f87-91a7-6a30d2de172c](.artifacts/records/project__check-run/rec-c49fe638-b475-4f87-91a7-6a30d2de172c.md))_

## verify-installer-wizard-interactive

### Acceptance
- **verify-installer-wizard-interactive**: R12; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k interactive_flag _(id: [rec-cc55da6d-936d-404e-a8d1-869ae468d85c](.artifacts/records/project__acceptance/rec-cc55da6d-936d-404e-a8d1-869ae468d85c.md))_

### Check
- **verify-installer-wizard-interactive**: rec-cc55da6d-936d-404e-a8d1-869ae468d85c; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-0e584719-6b82-42a8-bfa5-a6692afd3631](.artifacts/records/project__check-run/rec-0e584719-6b82-42a8-bfa5-a6692afd3631.md))_
- **verify-installer-wizard-interactive**: rec-cc55da6d-936d-404e-a8d1-869ae468d85c; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-bbcac675-7acf-4dee-bc96-5c1d0f744093](.artifacts/records/project__check-run/rec-bbcac675-7acf-4dee-bc96-5c1d0f744093.md))_

## verify-installer-wizard-list

### Acceptance
- **verify-installer-wizard-list**: R10; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k list_prints_matrix _(id: [rec-65ba7907-50e3-45e3-bc15-2b70be1216fb](.artifacts/records/project__acceptance/rec-65ba7907-50e3-45e3-bc15-2b70be1216fb.md))_

### Check
- **verify-installer-wizard-list**: rec-65ba7907-50e3-45e3-bc15-2b70be1216fb; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-4cf4b209-1a73-428c-b601-78a47e507ba5](.artifacts/records/project__check-run/rec-4cf4b209-1a73-428c-b601-78a47e507ba5.md))_
- **verify-installer-wizard-list**: rec-65ba7907-50e3-45e3-bc15-2b70be1216fb; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-7eedc572-74ed-434a-8061-03caf3f17a95](.artifacts/records/project__check-run/rec-7eedc572-74ed-434a-8061-03caf3f17a95.md))_

## verify-installer-wizard-noninteractive

### Acceptance
- **verify-installer-wizard-noninteractive**: R13; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k non_interactive _(id: [rec-76ceed00-92a2-45bd-8d57-ff55f5da6bc2](.artifacts/records/project__acceptance/rec-76ceed00-92a2-45bd-8d57-ff55f5da6bc2.md))_

### Check
- **verify-installer-wizard-noninteractive**: rec-76ceed00-92a2-45bd-8d57-ff55f5da6bc2; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-7f745d91-1307-4e03-859c-a00ef10144c1](.artifacts/records/project__check-run/rec-7f745d91-1307-4e03-859c-a00ef10144c1.md))_
- **verify-installer-wizard-noninteractive**: rec-76ceed00-92a2-45bd-8d57-ff55f5da6bc2; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-dea103a6-1cae-4bbb-9a7e-485e5d8e4f78](.artifacts/records/project__check-run/rec-dea103a6-1cae-4bbb-9a7e-485e5d8e4f78.md))_

## verify-installer-wizard-plan

### Acceptance
- **verify-installer-wizard-plan**: R8; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k plan_confirmation _(id: [rec-7eef54c2-8e15-4f80-b9c7-14248672160c](.artifacts/records/project__acceptance/rec-7eef54c2-8e15-4f80-b9c7-14248672160c.md))_

### Check
- **verify-installer-wizard-plan**: rec-7eef54c2-8e15-4f80-b9c7-14248672160c; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-16303aef-5057-456e-84cf-1d23af7ead2f](.artifacts/records/project__check-run/rec-16303aef-5057-456e-84cf-1d23af7ead2f.md))_
- **verify-installer-wizard-plan**: rec-7eef54c2-8e15-4f80-b9c7-14248672160c; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-29019bab-8676-4e9c-a552-9d61abe5b975](.artifacts/records/project__check-run/rec-29019bab-8676-4e9c-a552-9d61abe5b975.md))_

## verify-installer-wizard-scope

### Acceptance
- **verify-installer-wizard-scope**: R11; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k scope_flag _(id: [rec-079ec8d1-3ec5-4f7e-a748-d094ee954f85](.artifacts/records/project__acceptance/rec-079ec8d1-3ec5-4f7e-a748-d094ee954f85.md))_

### Check
- **verify-installer-wizard-scope**: rec-079ec8d1-3ec5-4f7e-a748-d094ee954f85; 970540048d3d45dfa3e6ecc68e9b0c690fb0b9e6; pass; check _(id: [rec-bd7614f5-0663-414f-874c-ff99e6dae191](.artifacts/records/project__check-run/rec-bd7614f5-0663-414f-874c-ff99e6dae191.md))_
- **verify-installer-wizard-scope**: rec-079ec8d1-3ec5-4f7e-a748-d094ee954f85; 095f90000c7d4681c2e97a6674d246cb29e8eafe; pass; check _(id: [rec-cdc9094f-96ad-4328-a2f5-da85e5eefbda](.artifacts/records/project__check-run/rec-cdc9094f-96ad-4328-a2f5-da85e5eefbda.md))_

## verify-journal-view

### Acceptance
- **verify-journal-view**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_journal.py tests/test_dashboard_app.py -q -k journal _(id: [rec-23b9ae39-56ef-401b-b2df-9b05b78d4967](.artifacts/records/project__acceptance/rec-23b9ae39-56ef-401b-b2df-9b05b78d4967.md))_

### Check
- **verify-journal-view**: rec-23b9ae39-56ef-401b-b2df-9b05b78d4967; 1eb4f7a6723b779267bc14d030951640dff5c6a3; pass; check _(id: [rec-64cc1377-67d4-40d8-9e29-eed31077423b](.artifacts/records/project__check-run/rec-64cc1377-67d4-40d8-9e29-eed31077423b.md))_

## verify-journal-view-suite

### Acceptance
- **verify-journal-view-suite**: R9; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_journal.py tests/test_dashboard_app.py -q -k journal _(id: [rec-628b0b42-c0af-421a-a077-8f9238c5eb0b](.artifacts/records/project__acceptance/rec-628b0b42-c0af-421a-a077-8f9238c5eb0b.md))_

### Check
- **verify-journal-view-suite**: rec-628b0b42-c0af-421a-a077-8f9238c5eb0b; 1eb4f7a6723b779267bc14d030951640dff5c6a3; pass; check _(id: [rec-fd830ba3-b57a-46b3-807f-15d1ebd1197f](.artifacts/records/project__check-run/rec-fd830ba3-b57a-46b3-807f-15d1ebd1197f.md))_

## verify-layout-phase

### Acceptance
- **verify-layout-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux -rf _(id: [rec-5d64f143-cdea-49dc-8cb4-7ca9fb9f2517](.artifacts/records/project__acceptance/rec-5d64f143-cdea-49dc-8cb4-7ca9fb9f2517.md))_

### Check
- **verify-layout-phase**: rec-5d64f143-cdea-49dc-8cb4-7ca9fb9f2517; d9e3eebae5096d3bfd0852e9a910fe4e8df9a725; pass; check _(id: [rec-b2b9ebb8-5411-4a63-93c3-1028295a1ce7](.artifacts/records/project__check-run/rec-b2b9ebb8-5411-4a63-93c3-1028295a1ce7.md))_

## verify-library-e2e

### Acceptance
- **verify-library-e2e**: R4; check; library-boundary; python3 -c 'import importlib.util,tempfile; from pathlib import Path; from adaptive_artifacts.project import open_store; s=importlib.util.spec_from_file_location("e2e","tests/test_library_e2e.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); repo,_=m._repository(Path(tempfile.mkdtemp())); assert any(r.get("subject")=="claim-widget" for r in open_store(repo).list("project:acceptance"))' _(id: [rec-6165972b-a96c-4128-b13a-a309fcdb10d8](.artifacts/records/project__acceptance/rec-6165972b-a96c-4128-b13a-a309fcdb10d8.md))_

### Check
- **verify-library-e2e**: rec-6165972b-a96c-4128-b13a-a309fcdb10d8; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-688ddd44-4ea4-448a-b3ef-30c253e493fb](.artifacts/records/project__check-run/rec-688ddd44-4ea4-448a-b3ef-30c253e493fb.md))_
- **verify-library-e2e**: rec-6165972b-a96c-4128-b13a-a309fcdb10d8; b624a3dcb27c119bdc37b928025d33959e9da77d; pass; check _(id: [rec-9d538865-e0ac-45e5-acfd-3a2a2f3a29c4](.artifacts/records/project__check-run/rec-9d538865-e0ac-45e5-acfd-3a2a2f3a29c4.md))_

## verify-library-e2e-close

### Acceptance
- **verify-library-e2e-close**: R5; check; library-boundary; PATH="$(pwd)/bin:$PATH" python3 -m pytest tests/test_library_e2e.py::test_library_fixture_close -q _(id: [rec-112bd5ec-359a-410c-80d4-77c364b63587](.artifacts/records/project__acceptance/rec-112bd5ec-359a-410c-80d4-77c364b63587.md))_

### Check
- **verify-library-e2e-close**: rec-112bd5ec-359a-410c-80d4-77c364b63587; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-0e5f6cf1-c6f2-4949-833b-0b5a44b51d08](.artifacts/records/project__check-run/rec-0e5f6cf1-c6f2-4949-833b-0b5a44b51d08.md))_
- **verify-library-e2e-close**: rec-112bd5ec-359a-410c-80d4-77c364b63587; b624a3dcb27c119bdc37b928025d33959e9da77d; pass; check _(id: [rec-a4c12cd5-2e0b-4aa0-8c90-2235a2f9625e](.artifacts/records/project__check-run/rec-a4c12cd5-2e0b-4aa0-8c90-2235a2f9625e.md))_

## verify-library-e2e-quiet

### Acceptance
- **verify-library-e2e-quiet**: R6; check; library-boundary; PATH="$(pwd)/bin:$PATH" PYTHONPATH="$(pwd):$HOME/affidavit${PYTHONPATH:+:$PYTHONPATH}" python3 -c 'import importlib.util,json,os,subprocess,tempfile; from pathlib import Path; s=importlib.util.spec_from_file_location("e2e","tests/test_library_e2e.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); repo,request=m._repository(Path(tempfile.mkdtemp())); seen=[]; real=subprocess.run
class P(subprocess.Popen):
 def __init__(self, cmd, *a, **k):
  seen.append(cmd); super().__init__(cmd, *a, **k)
def spy(cmd, *a, **k):
 seen.append(cmd); return real(cmd, *a, **k)
subprocess.run=spy; subprocess.Popen=P
import orchestra.close_batch as cb
cb.subprocess.run=spy; cb.subprocess.Popen=P
path=repo/"close-request.json"; path.write_text(json.dumps(request)); os.chdir(repo); cb.main(["--input",str(path),"--out",str(repo/"out.ndjson"),"--cwd",str(repo)])
def bad(cmd):
 parts=cmd if isinstance(cmd,(list,tuple)) else [cmd]
 return any(Path(str(p)).name in {"aff","adaptive-artifacts"} for p in parts)
assert not any(bad(c) for c in seen)'  _(id: [rec-197d8185-f42f-4030-9af7-94d992fe37d5](.artifacts/records/project__acceptance/rec-197d8185-f42f-4030-9af7-94d992fe37d5.md))_

### Check
- **verify-library-e2e-quiet**: rec-197d8185-f42f-4030-9af7-94d992fe37d5; de86e0df31c753d04064576cf7725c5bc3e34880; pass; check _(id: [rec-5600dd8d-c5f8-4eff-bc8d-d222b5cb8eda](.artifacts/records/project__check-run/rec-5600dd8d-c5f8-4eff-bc8d-d222b5cb8eda.md))_
- **verify-library-e2e-quiet**: rec-197d8185-f42f-4030-9af7-94d992fe37d5; b624a3dcb27c119bdc37b928025d33959e9da77d; pass; check _(id: [rec-ec6b0fa4-6866-401d-bf8c-5c897177eba0](.artifacts/records/project__check-run/rec-ec6b0fa4-6866-401d-bf8c-5c897177eba0.md))_

## verify-milestone-nav

### Acceptance
- **verify-milestone-nav**: R1; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestones.test.ts src/milestoneNav.test.ts _(id: [rec-2bc35113-9f94-41d8-966d-6f05da4eb36e](.artifacts/records/project__acceptance/rec-2bc35113-9f94-41d8-966d-6f05da4eb36e.md))_

### Check
- **verify-milestone-nav**: rec-2bc35113-9f94-41d8-966d-6f05da4eb36e; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-f80519b7-1cc1-4709-aec3-044292f40f97](.artifacts/records/project__check-run/rec-f80519b7-1cc1-4709-aec3-044292f40f97.md))_

## verify-milestone-nav-collapse

### Acceptance
- **verify-milestone-nav-collapse**: R7; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestones.test.ts -t R7 _(id: [rec-9a9e8ab6-940c-47e3-8f7d-0794f661b0a2](.artifacts/records/project__acceptance/rec-9a9e8ab6-940c-47e3-8f7d-0794f661b0a2.md))_

### Check
- **verify-milestone-nav-collapse**: rec-9a9e8ab6-940c-47e3-8f7d-0794f661b0a2; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-f55a0fc1-ba87-44b9-b58c-5ee939c95031](.artifacts/records/project__check-run/rec-f55a0fc1-ba87-44b9-b58c-5ee939c95031.md))_

## verify-milestone-nav-demo

### Acceptance
- **verify-milestone-nav-demo**: R2; manual; dashboard _(id: [rec-d0e08589-06f0-495e-8d77-b6847225d2bc](.artifacts/records/project__acceptance/rec-d0e08589-06f0-495e-8d77-b6847225d2bc.md))_

### Check
- **verify-milestone-nav-demo**: rec-d0e08589-06f0-495e-8d77-b6847225d2bc; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; manual; agent _(id: [rec-d7150eac-733e-41da-834b-a50be2711e0f](.artifacts/records/project__check-run/rec-d7150eac-733e-41da-834b-a50be2711e0f.md))_

## verify-milestone-nav-flat

### Acceptance
- **verify-milestone-nav-flat**: R4; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestoneNav.test.ts -t R4 _(id: [rec-0b22571b-615f-4ee7-9dcc-9010f606b323](.artifacts/records/project__acceptance/rec-0b22571b-615f-4ee7-9dcc-9010f606b323.md))_

### Check
- **verify-milestone-nav-flat**: rec-0b22571b-615f-4ee7-9dcc-9010f606b323; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-9a5ab22d-02a6-484a-8f72-903620a5dfc0](.artifacts/records/project__check-run/rec-9a5ab22d-02a6-484a-8f72-903620a5dfc0.md))_

## verify-milestone-nav-scope

### Acceptance
- **verify-milestone-nav-scope**: R5; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/milestoneNav.test.ts -t R5 _(id: [rec-97b373dc-cd68-47cd-9c1a-95c221f28a7c](.artifacts/records/project__acceptance/rec-97b373dc-cd68-47cd-9c1a-95c221f28a7c.md))_

### Check
- **verify-milestone-nav-scope**: rec-97b373dc-cd68-47cd-9c1a-95c221f28a7c; d374a278d97ad9418d03fa09ae76bee9ec64c95a; pass; check _(id: [rec-d7ed7814-c7f2-4606-9220-e14d56040444](.artifacts/records/project__check-run/rec-d7ed7814-c7f2-4606-9220-e14d56040444.md))_

## verify-navigation-phase

### Acceptance
- **verify-navigation-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux -rf _(id: [rec-d1da938c-12b5-4cb9-9f02-e4a6731c1222](.artifacts/records/project__acceptance/rec-d1da938c-12b5-4cb9-9f02-e4a6731c1222.md))_

### Check
- **verify-navigation-phase**: rec-d1da938c-12b5-4cb9-9f02-e4a6731c1222; b892587e80bbd40f785d3e104581a5587c250406; pass; check _(id: [rec-f864bb3e-40ce-4a6d-b048-471044f223c5](.artifacts/records/project__check-run/rec-f864bb3e-40ce-4a6d-b048-471044f223c5.md))_

## verify-needs-you-close

### Acceptance
- **verify-needs-you-close**: R4; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k dismiss _(id: [rec-acabf3ed-70af-4c45-bbc2-55df0b063fec](.artifacts/records/project__acceptance/rec-acabf3ed-70af-4c45-bbc2-55df0b063fec.md))_

### Check
- **verify-needs-you-close**: rec-acabf3ed-70af-4c45-bbc2-55df0b063fec; 8799ca930443a9a3144434eaf3b9e30e497adbce; pass; tdd _(id: [rec-5c64fd33-a70b-495b-966f-eda2ef698239](.artifacts/records/project__check-run/rec-5c64fd33-a70b-495b-966f-eda2ef698239.md))_

### Observation
- **verify-needs-you-close**: All three phase verify_commands passed: dismiss 4, refuse/fail 2, skills 18; workflow-loop _(id: [rec-ca617edc-862b-403f-b7f0-193fd05ff8bb](.artifacts/records/project__investigation-observation/rec-ca617edc-862b-403f-b7f0-193fd05ff8bb.md))_

## verify-needs-you-close-refuse

### Acceptance
- **verify-needs-you-close-refuse**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'dismiss and (refuse or fail or error)' _(id: [rec-519937ac-4467-4bbd-8f45-7786679a7d4f](.artifacts/records/project__acceptance/rec-519937ac-4467-4bbd-8f45-7786679a7d4f.md))_

### Check
- **verify-needs-you-close-refuse**: rec-519937ac-4467-4bbd-8f45-7786679a7d4f; 8799ca930443a9a3144434eaf3b9e30e497adbce; pass; tdd _(id: [rec-0971c5bf-012b-47c8-846d-25a165e3d9b1](.artifacts/records/project__check-run/rec-0971c5bf-012b-47c8-846d-25a165e3d9b1.md))_

## verify-needs-you-close-skills

### Acceptance
- **verify-needs-you-close-skills**: R1; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_discuss_skill.py -q _(id: [rec-53401a27-dd75-4ef2-adbb-a699505dc9fc](.artifacts/records/project__acceptance/rec-53401a27-dd75-4ef2-adbb-a699505dc9fc.md))_

### Check
- **verify-needs-you-close-skills**: rec-53401a27-dd75-4ef2-adbb-a699505dc9fc; 8799ca930443a9a3144434eaf3b9e30e497adbce; pass; check _(id: [rec-2bc38933-9600-44a1-af0c-4a16f8c7f191](.artifacts/records/project__check-run/rec-2bc38933-9600-44a1-af0c-4a16f8c7f191.md))_

## verify-needs-you-data-phase

### Acceptance
- **verify-needs-you-data-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-fe83e6fe-5005-4c88-97e8-3c15e744047a](.artifacts/records/project__acceptance/rec-fe83e6fe-5005-4c88-97e8-3c15e744047a.md))_

### Check
- **verify-needs-you-data-phase**: rec-fe83e6fe-5005-4c88-97e8-3c15e744047a; e4484c4c6ed29016f301e3e963957a2aa7bfdcac; pass; check _(id: [rec-0d607cff-8414-4a07-886b-115e54b99dbe](.artifacts/records/project__check-run/rec-0d607cff-8414-4a07-886b-115e54b99dbe.md))_

## verify-needs-you-phase

### Acceptance
- **verify-needs-you-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-d5958a14-e6a7-4c20-b110-5ae0c0ee54a3](.artifacts/records/project__acceptance/rec-d5958a14-e6a7-4c20-b110-5ae0c0ee54a3.md))_

### Check
- **verify-needs-you-phase**: rec-d5958a14-e6a7-4c20-b110-5ae0c0ee54a3; 94e39818ef6151434de8ef1617c69e0c9dcbda6b; pass; check _(id: [rec-e5ff5760-6474-4fc5-8f68-9d1e0a3d4453](.artifacts/records/project__check-run/rec-e5ff5760-6474-4fc5-8f68-9d1e0a3d4453.md))_

### Observation
- **verify-needs-you-phase**: tab from a live effort with Needs you items to a pane whose task table is hidden bounces back: Screen._reset_focus moves focus from the hidden TaskTable to the sibling NeedsList, and TabbedContent re-activates the pane holding focus. Reproduces every run; absent without Needs you items.; dashboard-features _(id: [rec-63c67821-d6d9-4012-8437-37c5beda8310](.artifacts/records/project__investigation-observation/rec-63c67821-d6d9-4012-8437-37c5beda8310.md))_

## verify-oracle-witnesses

### Acceptance
- **verify-oracle-witnesses**: R5; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'cli and (oracle or freeze or assertion_level or amendment)' _(id: [rec-c295c01e-9f40-460e-b8f9-4b0b26299a6e](.artifacts/records/project__acceptance/rec-c295c01e-9f40-460e-b8f9-4b0b26299a6e.md))_

### Check
- **verify-oracle-witnesses**: rec-c295c01e-9f40-460e-b8f9-4b0b26299a6e; b9adc0ee0836b843fd963ca38ad105d5e2176b68; pass; tdd _(id: [rec-0c86f52f-28de-4d06-9f45-48a6da28364b](.artifacts/records/project__check-run/rec-0c86f52f-28de-4d06-9f45-48a6da28364b.md))_
- **verify-oracle-witnesses**: rec-c295c01e-9f40-460e-b8f9-4b0b26299a6e; 977750c3c4f05015bcf03d4b82c77d25c8f039d3; fail; tdd _(id: [rec-39f7cca6-c11e-498c-b40c-48ba1cc8d731](.artifacts/records/project__check-run/rec-39f7cca6-c11e-498c-b40c-48ba1cc8d731.md))_
- **verify-oracle-witnesses**: rec-c295c01e-9f40-460e-b8f9-4b0b26299a6e; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; tdd _(id: [rec-5826c84b-95ff-46ad-9072-9396857c9fd0](.artifacts/records/project__check-run/rec-5826c84b-95ff-46ad-9072-9396857c9fd0.md))_

## verify-oracle-witnesses-freeze-fields

### Acceptance
- **verify-oracle-witnesses-freeze-fields**: R3; check; workflow-loop; python3 -c "import json;from pathlib import Path;d=json.loads(Path('contract/project-design.json').read_text());a=next(t for t in d['records'] if t['name']=='acceptance');assert 'test_ids' in a['payload'] and 'oracle_hashes' in a['payload'];assert 'oracle-amendment' in {t['name'] for t in d['records']}" _(id: [rec-702fc0af-6e5d-4df2-ba30-0b17e614f28d](.artifacts/records/project__acceptance/rec-702fc0af-6e5d-4df2-ba30-0b17e614f28d.md))_

### Check
- **verify-oracle-witnesses-freeze-fields**: rec-702fc0af-6e5d-4df2-ba30-0b17e614f28d; b9adc0ee0836b843fd963ca38ad105d5e2176b68; pass; check _(id: [rec-5f177a58-4811-4b74-b4b3-579a30074e91](.artifacts/records/project__check-run/rec-5f177a58-4811-4b74-b4b3-579a30074e91.md))_
- **verify-oracle-witnesses-freeze-fields**: rec-702fc0af-6e5d-4df2-ba30-0b17e614f28d; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-7bb1d973-b1b1-4435-bd9c-89df33e56ac5](.artifacts/records/project__check-run/rec-7bb1d973-b1b1-4435-bd9c-89df33e56ac5.md))_

## verify-oracle-witnesses-mechanical-close

### Acceptance
- **verify-oracle-witnesses-mechanical-close**: R6; check; workflow-loop; python3 -m pytest tests/test_close_batch.py tests/test_oracle_red.py -q -k 'oracle or freeze or assertion_level' _(id: [rec-e671315a-55d8-4a48-82a8-29555da56b42](.artifacts/records/project__acceptance/rec-e671315a-55d8-4a48-82a8-29555da56b42.md))_

### Check
- **verify-oracle-witnesses-mechanical-close**: rec-e671315a-55d8-4a48-82a8-29555da56b42; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-584ac600-c30f-4c7b-b6b8-edd2e50fe872](.artifacts/records/project__check-run/rec-584ac600-c30f-4c7b-b6b8-edd2e50fe872.md))_
- **verify-oracle-witnesses-mechanical-close**: rec-e671315a-55d8-4a48-82a8-29555da56b42; b9adc0ee0836b843fd963ca38ad105d5e2176b68; pass; check _(id: [rec-86243b03-012a-484a-813d-7043c980edb8](.artifacts/records/project__check-run/rec-86243b03-012a-484a-813d-7043c980edb8.md))_

## verify-oracle-witnesses-skills

### Acceptance
- **verify-oracle-witnesses-skills**: R7; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_oracle_red.py -q _(id: [rec-f05bed1e-a34d-456b-9979-59572fc49c56](.artifacts/records/project__acceptance/rec-f05bed1e-a34d-456b-9979-59572fc49c56.md))_

### Check
- **verify-oracle-witnesses-skills**: rec-f05bed1e-a34d-456b-9979-59572fc49c56; e04bc30552d35b83b19337abee8df4c26cb55b61; pass; check _(id: [rec-826e8165-2d49-46d1-8352-1ea8e08a394f](.artifacts/records/project__check-run/rec-826e8165-2d49-46d1-8352-1ea8e08a394f.md))_
- **verify-oracle-witnesses-skills**: rec-f05bed1e-a34d-456b-9979-59572fc49c56; b9adc0ee0836b843fd963ca38ad105d5e2176b68; pass; check _(id: [rec-d6ee89f3-7ea5-4c28-99f1-48eb510ca759](.artifacts/records/project__check-run/rec-d6ee89f3-7ea5-4c28-99f1-48eb510ca759.md))_

## verify-orchestra-callers

### Acceptance
- **verify-orchestra-callers**: R3; check; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r3 -q _(id: [rec-9ce2990b-82e2-4cbb-b6bf-1181472432d3](.artifacts/records/project__acceptance/rec-9ce2990b-82e2-4cbb-b6bf-1181472432d3.md))_

### Check
- **verify-orchestra-callers**: rec-9ce2990b-82e2-4cbb-b6bf-1181472432d3; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; check _(id: [rec-71144b6c-bcca-4a51-985c-45361bb8da50](.artifacts/records/project__check-run/rec-71144b6c-bcca-4a51-985c-45361bb8da50.md))_
- **verify-orchestra-callers**: rec-9ce2990b-82e2-4cbb-b6bf-1181472432d3; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; check _(id: [rec-e3ef997a-8d1f-45c6-b8c2-f16903813387](.artifacts/records/project__check-run/rec-e3ef997a-8d1f-45c6-b8c2-f16903813387.md))_

## verify-orchestra-callers-help

### Acceptance
- **verify-orchestra-callers-help**: R8; check; library-boundary; python3 -c 'import os,subprocess,sys,tempfile; from pathlib import Path; root=Path.cwd(); b=Path(tempfile.mkdtemp()); (b/"sitecustomize.py").write_text("import sys\nclass Block:\n def find_spec(self, name, path, target=None):\n  if name==\"affidavit\" or name.startswith(\"affidavit.\"):\n   raise ImportError(name)\n  return None\nsys.meta_path.insert(0, Block())\n"); env=os.environ.copy(); pp=env.get("PYTHONPATH",""); env["PYTHONPATH"]=str(b)+os.pathsep+str(root)+(os.pathsep+pp if pp else ""); p=subprocess.run([sys.executable, str(root/"bin"/"orchestra"), "--help"], cwd=root, env=env); raise SystemExit(p.returncode)' _(id: [rec-4255a827-d9d0-439f-bfc0-a6a75b248a9f](.artifacts/records/project__acceptance/rec-4255a827-d9d0-439f-bfc0-a6a75b248a9f.md))_

### Check
- **verify-orchestra-callers-help**: rec-4255a827-d9d0-439f-bfc0-a6a75b248a9f; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; check _(id: [rec-603e7c79-7e5b-4765-93dc-bfc4e4c6d777](.artifacts/records/project__check-run/rec-603e7c79-7e5b-4765-93dc-bfc4e4c6d777.md))_
- **verify-orchestra-callers-help**: rec-4255a827-d9d0-439f-bfc0-a6a75b248a9f; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; check _(id: [rec-c3d32ea8-cc40-41b3-ab33-4d499a37758b](.artifacts/records/project__check-run/rec-c3d32ea8-cc40-41b3-ab33-4d499a37758b.md))_

## verify-orchestra-callers-missing

### Acceptance
- **verify-orchestra-callers-missing**: R9; check; library-boundary; python3 -m pytest tests/test_orchestra_callers.py::test_r9 -q _(id: [rec-8d395711-29a7-4afe-b1ff-54d5930d7c09](.artifacts/records/project__acceptance/rec-8d395711-29a7-4afe-b1ff-54d5930d7c09.md))_

### Check
- **verify-orchestra-callers-missing**: rec-8d395711-29a7-4afe-b1ff-54d5930d7c09; e26118f3fdf05b46721f3c9b487eb2dcb9752e41; pass; check _(id: [rec-1f14e45b-d373-4d3e-9d40-a78cb332726e](.artifacts/records/project__check-run/rec-1f14e45b-d373-4d3e-9d40-a78cb332726e.md))_
- **verify-orchestra-callers-missing**: rec-8d395711-29a7-4afe-b1ff-54d5930d7c09; 1014602caaf7264234fc5409e50ec63f80f9cd5a; pass; check _(id: [rec-8abd62ea-8b0b-484a-8ef6-1fb2fb86307a](.artifacts/records/project__check-run/rec-8abd62ea-8b0b-484a-8ef6-1fb2fb86307a.md))_

## verify-path-test-gaps

### Acceptance
- **verify-path-test-gaps**: R5; tdd; workflow-loop; python3 -m pytest tests/test_affidavit_check.py tests/test_close_batch.py -k 'worktree or cwd_primary or store_cwd' -q _(id: [rec-42e9d09d-8bf3-4c5c-8abf-ba99dc9533c2](.artifacts/records/project__acceptance/rec-42e9d09d-8bf3-4c5c-8abf-ba99dc9533c2.md))_

### Check
- **verify-path-test-gaps**: rec-42e9d09d-8bf3-4c5c-8abf-ba99dc9533c2; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-8007795a-a9ed-425c-b890-fec1ac67d2b9](.artifacts/records/project__check-run/rec-8007795a-a9ed-425c-b890-fec1ac67d2b9.md))_
- **verify-path-test-gaps**: rec-42e9d09d-8bf3-4c5c-8abf-ba99dc9533c2; dirty; fail; tdd _(id: [rec-826ae905-3d18-4a8b-8f35-90d9ab8c830a](.artifacts/records/project__check-run/rec-826ae905-3d18-4a8b-8f35-90d9ab8c830a.md))_
- **verify-path-test-gaps**: rec-42e9d09d-8bf3-4c5c-8abf-ba99dc9533c2; dirty; fail; tdd _(id: [rec-cce5b8dd-4a86-47d6-b27f-863e910b2292](.artifacts/records/project__check-run/rec-cce5b8dd-4a86-47d6-b27f-863e910b2292.md))_
- **verify-path-test-gaps**: rec-42e9d09d-8bf3-4c5c-8abf-ba99dc9533c2; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-de0222e8-736e-41b9-a24d-be270109fad3](.artifacts/records/project__check-run/rec-de0222e8-736e-41b9-a24d-be270109fad3.md))_

## verify-path-test-gaps-mutants

### Acceptance
- **verify-path-test-gaps-mutants**: R6; tdd; workflow-loop; python3 -m pytest tests/test_affidavit_check.py -k 'timeout or empty_verify or cwd_forwarded or blocked_timeout' -q _(id: [rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e](.artifacts/records/project__acceptance/rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e.md))_

### Check
- **verify-path-test-gaps-mutants**: rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e; dirty; fail; tdd _(id: [rec-2e624aef-602a-4e59-88c4-73f40cf12ca1](.artifacts/records/project__check-run/rec-2e624aef-602a-4e59-88c4-73f40cf12ca1.md))_
- **verify-path-test-gaps-mutants**: rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-3dc8a2b6-a3e5-434a-889b-64f72b476b86](.artifacts/records/project__check-run/rec-3dc8a2b6-a3e5-434a-889b-64f72b476b86.md))_
- **verify-path-test-gaps-mutants**: rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e; d680521c3270c954d22b915c641c7e733595599f; pass; tdd _(id: [rec-6e6a6e19-9e94-460f-b911-72c1d781285b](.artifacts/records/project__check-run/rec-6e6a6e19-9e94-460f-b911-72c1d781285b.md))_
- **verify-path-test-gaps-mutants**: rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e; dirty; fail; tdd _(id: [rec-cadfe683-4856-43be-b1d4-26afc188824c](.artifacts/records/project__check-run/rec-cadfe683-4856-43be-b1d4-26afc188824c.md))_

## verify-phase-landing

### Acceptance
- **verify-phase-landing**: tdd; workflow-loop; python3 -m pytest tests/test_phase_landing.py tests/test_plan_landing.py tests/test_execute_landing.py -q _(id: [rec-5f277ff6-f5de-48ae-a3fa-43825f135561](.artifacts/records/project__acceptance/rec-5f277ff6-f5de-48ae-a3fa-43825f135561.md))_

### Check
- **verify-phase-landing**: rec-c376fad0-9993-4448-9e97-21adc7a1ec8d; dirty; pass; tdd _(id: [rec-1795aff9-df1b-49c3-97ae-46cc6beb5a7b](.artifacts/records/project__check-run/rec-1795aff9-df1b-49c3-97ae-46cc6beb5a7b.md))_
- **verify-phase-landing**: rec-5f277ff6-f5de-48ae-a3fa-43825f135561; dirty; pass; tdd _(id: [rec-55600d6d-b7b7-4816-8df3-1680e8abfb98](.artifacts/records/project__check-run/rec-55600d6d-b7b7-4816-8df3-1680e8abfb98.md))_
- **verify-phase-landing**: rec-58522d3a-4f28-4cd8-bcf8-4f8ab951dd54; dirty; pass; tdd _(id: [rec-99acf357-0cc7-4cce-8a8b-d102945d8956](.artifacts/records/project__check-run/rec-99acf357-0cc7-4cce-8a8b-d102945d8956.md))_

## verify-phase-landing-execute

### Acceptance
- **verify-phase-landing-execute**: tdd; workflow-loop; python3 -m pytest tests/test_execute_landing.py -q _(id: [rec-c376fad0-9993-4448-9e97-21adc7a1ec8d](.artifacts/records/project__acceptance/rec-c376fad0-9993-4448-9e97-21adc7a1ec8d.md))_

## verify-phase-landing-plan

### Acceptance
- **verify-phase-landing-plan**: tdd; workflow-loop; python3 -m pytest tests/test_plan_landing.py -q _(id: [rec-58522d3a-4f28-4cd8-bcf8-4f8ab951dd54](.artifacts/records/project__acceptance/rec-58522d3a-4f28-4cd8-bcf8-4f8ab951dd54.md))_

## verify-phase-overview

### Acceptance
- **verify-phase-overview**: R1; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts _(id: [rec-39f2269c-55c0-45e5-83d0-b799213be189](.artifacts/records/project__acceptance/rec-39f2269c-55c0-45e5-83d0-b799213be189.md))_

### Check
- **verify-phase-overview**: rec-39f2269c-55c0-45e5-83d0-b799213be189; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-938ffdcc-ca3f-4732-bd16-39a0242b0891](.artifacts/records/project__check-run/rec-938ffdcc-ca3f-4732-bd16-39a0242b0891.md))_

## verify-phase-overview-demo

### Acceptance
- **verify-phase-overview-demo**: R7; manual; dashboard _(id: [rec-be401439-0cbf-4a09-8b24-9954747001ac](.artifacts/records/project__acceptance/rec-be401439-0cbf-4a09-8b24-9954747001ac.md))_

### Check
- **verify-phase-overview-demo**: 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; manual; auto-web-calm _(id: [rec-561a3e29-1d9a-4289-85e7-3ba73d12a1bf](.artifacts/records/project__check-run/rec-561a3e29-1d9a-4289-85e7-3ba73d12a1bf.md))_

## verify-phase-overview-nav

### Acceptance
- **verify-phase-overview-nav**: R5; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R5 _(id: [rec-223e3c0d-95ea-4880-a5f9-9bd4978afbd3](.artifacts/records/project__acceptance/rec-223e3c0d-95ea-4880-a5f9-9bd4978afbd3.md))_

### Check
- **verify-phase-overview-nav**: rec-223e3c0d-95ea-4880-a5f9-9bd4978afbd3; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-54724cb0-0a88-4f2d-b357-fd777a30e40b](.artifacts/records/project__check-run/rec-54724cb0-0a88-4f2d-b357-fd777a30e40b.md))_

## verify-phase-overview-tabs

### Acceptance
- **verify-phase-overview-tabs**: R7; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/phaseOverview.test.ts -t R7 _(id: [rec-2215dfd0-ba68-4253-ac8b-fd214c0bfd01](.artifacts/records/project__acceptance/rec-2215dfd0-ba68-4253-ac8b-fd214c0bfd01.md))_

### Check
- **verify-phase-overview-tabs**: rec-2215dfd0-ba68-4253-ac8b-fd214c0bfd01; 42d8187d49206aeb1ee9de8cae589935123d6e0b; pass; check _(id: [rec-ee419342-994a-446c-b600-bdb262d94052](.artifacts/records/project__check-run/rec-ee419342-994a-446c-b600-bdb262d94052.md))_

## verify-phase-proof-packet

### Acceptance
- **verify-phase-proof-packet**: R1; check; workflow-loop; python3 -m pytest tests/test_proof_packet_smoke.py -q _(id: [rec-c5fcd5d0-174f-488f-8582-6da3b29d4380](.artifacts/records/project__acceptance/rec-c5fcd5d0-174f-488f-8582-6da3b29d4380.md))_

### Check
- **verify-phase-proof-packet**: rec-c5fcd5d0-174f-488f-8582-6da3b29d4380; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-42447699-7a4c-46cc-804b-cf73845cede6](.artifacts/records/project__check-run/rec-42447699-7a4c-46cc-804b-cf73845cede6.md))_

## verify-phase-proof-packet-aff

### Acceptance
- **verify-phase-proof-packet-aff**: R5; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_aff_hooks_and_incidental -q _(id: [rec-820335d0-4534-4dd1-ae84-a99cc199f21e](.artifacts/records/project__acceptance/rec-820335d0-4534-4dd1-ae84-a99cc199f21e.md))_

### Check
- **verify-phase-proof-packet-aff**: rec-820335d0-4534-4dd1-ae84-a99cc199f21e; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-bf04c8dd-9620-460a-86da-6820d9164fd4](.artifacts/records/project__check-run/rec-bf04c8dd-9620-460a-86da-6820d9164fd4.md))_

## verify-phase-proof-packet-execute

### Acceptance
- **verify-phase-proof-packet-execute**: R4; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_assembles_proof_packet -q _(id: [rec-1320e937-f410-499c-9b9b-2d00af612b57](.artifacts/records/project__acceptance/rec-1320e937-f410-499c-9b9b-2d00af612b57.md))_

### Check
- **verify-phase-proof-packet-execute**: rec-1320e937-f410-499c-9b9b-2d00af612b57; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-d6df75cb-ce9d-4a62-9f79-6bd86797c75b](.artifacts/records/project__check-run/rec-d6df75cb-ce9d-4a62-9f79-6bd86797c75b.md))_

## verify-phase-proof-packet-handoff

### Acceptance
- **verify-phase-proof-packet-handoff**: R2; check; workflow-loop; python3 -m pytest tests/test_proof_packet_contract.py::test_handoff_latest_proof_role -q _(id: [rec-7890d964-d81b-43e2-af75-0bf270341fdb](.artifacts/records/project__acceptance/rec-7890d964-d81b-43e2-af75-0bf270341fdb.md))_

### Check
- **verify-phase-proof-packet-handoff**: rec-7890d964-d81b-43e2-af75-0bf270341fdb; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-352fa70a-d727-4b8b-928f-93ffc0f580d9](.artifacts/records/project__check-run/rec-352fa70a-d727-4b8b-928f-93ffc0f580d9.md))_

## verify-phase-proof-packet-incidental

### Acceptance
- **verify-phase-proof-packet-incidental**: R6; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_aff_hooks_and_incidental -q _(id: [rec-aa688749-5f2f-4c3f-ae17-4564467fa7a0](.artifacts/records/project__acceptance/rec-aa688749-5f2f-4c3f-ae17-4564467fa7a0.md))_

### Check
- **verify-phase-proof-packet-incidental**: rec-aa688749-5f2f-4c3f-ae17-4564467fa7a0; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-83799466-e489-47a8-b51b-08907b4c4e5a](.artifacts/records/project__check-run/rec-83799466-e489-47a8-b51b-08907b4c4e5a.md))_

## verify-phase-proof-packet-skills

### Acceptance
- **verify-phase-proof-packet-skills**: R3; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_settle_and_plan_require_proof_section -q _(id: [rec-9a89b92e-b3d6-4688-b1be-b8599bb5745b](.artifacts/records/project__acceptance/rec-9a89b92e-b3d6-4688-b1be-b8599bb5745b.md))_

### Check
- **verify-phase-proof-packet-skills**: rec-9a89b92e-b3d6-4688-b1be-b8599bb5745b; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-1a2f6b98-ccf3-4e2e-af37-f2c9731c466d](.artifacts/records/project__check-run/rec-1a2f6b98-ccf3-4e2e-af37-f2c9731c466d.md))_

## verify-phase-proof-packet-ui

### Acceptance
- **verify-phase-proof-packet-ui**: R7; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_proof_dashboard.py -q _(id: [rec-39cf9d37-3116-4b83-be09-b948e9f81574](.artifacts/records/project__acceptance/rec-39cf9d37-3116-4b83-be09-b948e9f81574.md))_

### Check
- **verify-phase-proof-packet-ui**: rec-39cf9d37-3116-4b83-be09-b948e9f81574; c9c2d6a70719285637ba08662d4772f661e88a74; pass; check _(id: [rec-d9aad1d8-4cac-40db-be64-e11a019b2dd9](.artifacts/records/project__check-run/rec-d9aad1d8-4cac-40db-be64-e11a019b2dd9.md))_

## verify-phase-reviewer

### Acceptance
- **verify-phase-reviewer**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q _(id: [rec-a5b4ff28-4664-45b7-9b25-489d4f58af19](.artifacts/records/project__acceptance/rec-a5b4ff28-4664-45b7-9b25-489d4f58af19.md))_

### Check
- **verify-phase-reviewer**: rec-a5b4ff28-4664-45b7-9b25-489d4f58af19; e5b769d5e7bf6a24f52d7ec7abc6b77190aad96a; fail; tdd _(id: [rec-1f4f33ef-460a-44cc-8c60-c7beee639790](.artifacts/records/project__check-run/rec-1f4f33ef-460a-44cc-8c60-c7beee639790.md))_
- **verify-phase-reviewer**: rec-a5b4ff28-4664-45b7-9b25-489d4f58af19; 11a147e75daa100a2fbca2202399205b480b42e9; pass; tdd _(id: [rec-ffac3710-847f-458c-a367-9a5061c23261](.artifacts/records/project__check-run/rec-ffac3710-847f-458c-a367-9a5061c23261.md))_

## verify-phase-reviewer-agent

### Acceptance
- **verify-phase-reviewer-agent**: R1; check; workflow-loop; test -f agents/se-reviewer.md && grep -qiE "no Write|without Write" agents/se-reviewer.md && grep -q agents/ scripts/sync-plugin.sh && grep -qiE "reviewer|se-reviewer" skills/execute-phase/SKILL.md _(id: [rec-1c47f604-3a3d-43ce-b488-7f0dc461180e](.artifacts/records/project__acceptance/rec-1c47f604-3a3d-43ce-b488-7f0dc461180e.md))_

### Check
- **verify-phase-reviewer-agent**: rec-1c47f604-3a3d-43ce-b488-7f0dc461180e; 11a147e75daa100a2fbca2202399205b480b42e9; pass; check _(id: [rec-5078fe00-d85e-49a7-b9ea-e9793ef902eb](.artifacts/records/project__check-run/rec-5078fe00-d85e-49a7-b9ea-e9793ef902eb.md))_

## verify-phase-reviewer-contract

### Acceptance
- **verify-phase-reviewer-contract**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_contract_self_consistency.py -q _(id: [rec-5fe7f197-7081-4e2e-a8dd-bd9014170eaf](.artifacts/records/project__acceptance/rec-5fe7f197-7081-4e2e-a8dd-bd9014170eaf.md))_

### Check
- **verify-phase-reviewer-contract**: rec-5fe7f197-7081-4e2e-a8dd-bd9014170eaf; 11a147e75daa100a2fbca2202399205b480b42e9; pass; check _(id: [rec-3012d3ea-a62d-4087-8c33-d3422223f820](.artifacts/records/project__check-run/rec-3012d3ea-a62d-4087-8c33-d3422223f820.md))_

## verify-phase-reviewer-fixture

### Acceptance
- **verify-phase-reviewer-fixture**: R7; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k status_tabs _(id: [rec-14227c0e-f22a-4354-92b7-eb89f4eba878](.artifacts/records/project__acceptance/rec-14227c0e-f22a-4354-92b7-eb89f4eba878.md))_

### Check
- **verify-phase-reviewer-fixture**: rec-14227c0e-f22a-4354-92b7-eb89f4eba878; 11a147e75daa100a2fbca2202399205b480b42e9; pass; tdd _(id: [rec-5b936122-cc58-4c04-871d-68359835b5da](.artifacts/records/project__check-run/rec-5b936122-cc58-4c04-871d-68359835b5da.md))_
- **verify-phase-reviewer-fixture**: rec-14227c0e-f22a-4354-92b7-eb89f4eba878; e5b769d5e7bf6a24f52d7ec7abc6b77190aad96a; fail; tdd _(id: [rec-cc0d0a68-bc39-41f2-aefa-ab1e8a01c42f](.artifacts/records/project__check-run/rec-cc0d0a68-bc39-41f2-aefa-ab1e8a01c42f.md))_

## verify-phase-reviewer-gate

### Acceptance
- **verify-phase-reviewer-gate**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k gate _(id: [rec-47250685-0161-4993-80af-7bd73bdce32b](.artifacts/records/project__acceptance/rec-47250685-0161-4993-80af-7bd73bdce32b.md))_

### Check
- **verify-phase-reviewer-gate**: rec-47250685-0161-4993-80af-7bd73bdce32b; e5b769d5e7bf6a24f52d7ec7abc6b77190aad96a; fail; tdd _(id: [rec-59db4225-ccae-4eb8-b66a-5ae39fc0f6df](.artifacts/records/project__check-run/rec-59db4225-ccae-4eb8-b66a-5ae39fc0f6df.md))_
- **verify-phase-reviewer-gate**: rec-47250685-0161-4993-80af-7bd73bdce32b; 11a147e75daa100a2fbca2202399205b480b42e9; pass; tdd _(id: [rec-e4302069-0e0a-4871-bc13-0bda3c12a807](.artifacts/records/project__check-run/rec-e4302069-0e0a-4871-bc13-0bda3c12a807.md))_

## verify-phase-selector

### Acceptance
- **verify-phase-selector**: R14; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_integration.py -q -k once _(id: [rec-a14d5cc4-9daf-4279-9625-b803a75d93cb](.artifacts/records/project__acceptance/rec-a14d5cc4-9daf-4279-9625-b803a75d93cb.md))_

### Check
- **verify-phase-selector**: rec-c559dd9b-03f5-4cb5-8d62-8dff85a9ad2e; dirty; pass; check _(id: [rec-0ed70697-b26d-4565-ac2b-aa9667183cb7](.artifacts/records/project__check-run/rec-0ed70697-b26d-4565-ac2b-aa9667183cb7.md))_
- **verify-phase-selector**: rec-a11805b7-bc3c-4f57-bcb4-db7d8ffa9ed9; dirty; fail; check _(id: [rec-2e3ddfae-c775-4b2e-8497-05064b8042fa](.artifacts/records/project__check-run/rec-2e3ddfae-c775-4b2e-8497-05064b8042fa.md))_
- **verify-phase-selector**: rec-2924db08-5149-4136-bbd9-b6deb59a93b8; dirty; pass; check _(id: [rec-9b7a3ab5-4d12-4e39-ae0a-c64d2dc14669](.artifacts/records/project__check-run/rec-9b7a3ab5-4d12-4e39-ae0a-c64d2dc14669.md))_
- **verify-phase-selector**: rec-a14d5cc4-9daf-4279-9625-b803a75d93cb; dirty; pass; check _(id: [rec-f836b11f-ee98-4e95-a264-3ea7f5f761bb](.artifacts/records/project__check-run/rec-f836b11f-ee98-4e95-a264-3ea7f5f761bb.md))_
- **verify-phase-selector**: rec-a11805b7-bc3c-4f57-bcb4-db7d8ffa9ed9; dirty; pass; check _(id: [rec-fe8dbe67-529a-4306-a1d4-9fcf5698bd41](.artifacts/records/project__check-run/rec-fe8dbe67-529a-4306-a1d4-9fcf5698bd41.md))_

## verify-phase-selector-app

### Acceptance
- **verify-phase-selector-app**: R2; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-2924db08-5149-4136-bbd9-b6deb59a93b8](.artifacts/records/project__acceptance/rec-2924db08-5149-4136-bbd9-b6deb59a93b8.md))_

## verify-phase-selector-model

### Acceptance
- **verify-phase-selector-model**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_tasks.py -q _(id: [rec-c559dd9b-03f5-4cb5-8d62-8dff85a9ad2e](.artifacts/records/project__acceptance/rec-c559dd9b-03f5-4cb5-8d62-8dff85a9ad2e.md))_

## verify-phase-selector-suite

### Acceptance
- **verify-phase-selector-suite**: R4; check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m not tmux && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-a11805b7-bc3c-4f57-bcb4-db7d8ffa9ed9](.artifacts/records/project__acceptance/rec-a11805b7-bc3c-4f57-bcb4-db7d8ffa9ed9.md))_

## verify-plugin-dep-marketplace

### Acceptance
- **verify-plugin-dep-marketplace**: R2; check; packaging; claude plugin validate . && python3 -c "import json;p=json.load(open('.claude-plugin/plugin.json'));d=p.get('dependencies',[]);assert 'adaptive-artifacts' in d or any(isinstance(x,dict) and x.get('name')=='adaptive-artifacts' for x in d);m=json.load(open('.claude-plugin/marketplace.json'));assert {x.get('name') for x in m['plugins']}>= {'se-workflow','adaptive-artifacts'}" _(id: [rec-463ee27b-5093-4184-bbf6-7b80770d43ac](.artifacts/records/project__acceptance/rec-463ee27b-5093-4184-bbf6-7b80770d43ac.md))_

### Check
- **verify-plugin-dep-marketplace**: rec-463ee27b-5093-4184-bbf6-7b80770d43ac; 40db2970236ac7ff04afd9eaf08292f072a912a2; pass; check _(id: [rec-b1f44839-d82d-48a0-86c5-662ab8a5aa40](.artifacts/records/project__check-run/rec-b1f44839-d82d-48a0-86c5-662ab8a5aa40.md))_

## verify-plugin-dep-marketplace-readme

### Acceptance
- **verify-plugin-dep-marketplace-readme**: R4; check; packaging; grep -q 'claude plugin marketplace add andrewy1n/se-workflow' README.md && grep -qi Cursor README.md && ! grep -qiE 'Cursor.*(auto-?install|plugin dependenc).*adaptive-artifacts' README.md _(id: [rec-c30aaca7-94df-4c02-a6f3-fcce0c8d6b00](.artifacts/records/project__acceptance/rec-c30aaca7-94df-4c02-a6f3-fcce0c8d6b00.md))_

### Check
- **verify-plugin-dep-marketplace-readme**: rec-c30aaca7-94df-4c02-a6f3-fcce0c8d6b00; 40db2970236ac7ff04afd9eaf08292f072a912a2; pass; check _(id: [rec-78e62280-8d1d-4f1d-95ba-eabd70e4efeb](.artifacts/records/project__check-run/rec-78e62280-8d1d-4f1d-95ba-eabd70e4efeb.md))_

## verify-plugin-root-and-cli

### Acceptance
- **verify-plugin-root-and-cli**: R2; tdd; packaging; uv run --with pytest python -m pytest tests/test_aa_resolve.py -q && grep -q CLAUDE_PLUGIN_ROOT skills/ensure-store.md && grep -q CURSOR_PLUGIN_ROOT skills/ensure-store.md && ! grep -E '^[0-9]+\. .*\.cursor/plugins/local/se-workflow' skills/ensure-store.md && ! grep -n "Path.home() / \"adaptive-artifacts\"" se_workflow/aa.py dashboard/artifact_store.py _(id: [rec-d1532551-f82b-44a4-94c5-de313a93d078](.artifacts/records/project__acceptance/rec-d1532551-f82b-44a4-94c5-de313a93d078.md))_

### Check
- **verify-plugin-root-and-cli**: rec-d1532551-f82b-44a4-94c5-de313a93d078; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; tdd _(id: [rec-2c5ab419-57ca-454c-bb77-b31fa827c8f9](.artifacts/records/project__check-run/rec-2c5ab419-57ca-454c-bb77-b31fa827c8f9.md))_
- **verify-plugin-root-and-cli**: rec-d1532551-f82b-44a4-94c5-de313a93d078; dirty; fail; tdd _(id: [rec-48b7e94c-45cb-4821-a3ed-6419005cf989](.artifacts/records/project__check-run/rec-48b7e94c-45cb-4821-a3ed-6419005cf989.md))_
- **verify-plugin-root-and-cli**: rec-d1532551-f82b-44a4-94c5-de313a93d078; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; tdd _(id: [rec-63797327-51f1-4c0f-82ef-e872e3955d6e](.artifacts/records/project__check-run/rec-63797327-51f1-4c0f-82ef-e872e3955d6e.md))_
- **verify-plugin-root-and-cli**: rec-e2174663-bdbf-4250-aa23-5075f95e0c8d; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; manual; inline _(id: [rec-f6cba71a-4b1d-46dc-bf7d-aa1ca14e1b26](.artifacts/records/project__check-run/rec-f6cba71a-4b1d-46dc-bf7d-aa1ca14e1b26.md))_

## verify-plugin-root-and-cli-close

### Acceptance
- **verify-plugin-root-and-cli-close**: R3; tdd; packaging; uv run --with pytest python -m pytest tests/test_close_batch.py -q && grep -qE 'se-workflow close-batch|bin/se-workflow close-batch' skills/verify-work/SKILL.md && ! grep -q scripts/close_batch.py skills/verify-work/SKILL.md && uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-db3cca7b-c7b5-482b-be36-b59f59c5621b](.artifacts/records/project__acceptance/rec-db3cca7b-c7b5-482b-be36-b59f59c5621b.md))_

### Check
- **verify-plugin-root-and-cli-close**: rec-db3cca7b-c7b5-482b-be36-b59f59c5621b; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; tdd _(id: [rec-03d83276-1c06-4e72-8435-27ec1f7d47dd](.artifacts/records/project__check-run/rec-03d83276-1c06-4e72-8435-27ec1f7d47dd.md))_
- **verify-plugin-root-and-cli-close**: rec-db3cca7b-c7b5-482b-be36-b59f59c5621b; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; tdd _(id: [rec-a6dede01-8956-457b-8b51-e0c8892a835b](.artifacts/records/project__check-run/rec-a6dede01-8956-457b-8b51-e0c8892a835b.md))_
- **verify-plugin-root-and-cli-close**: rec-db3cca7b-c7b5-482b-be36-b59f59c5621b; dirty; fail; tdd _(id: [rec-be6d0d5a-d576-41c7-9466-22e2c25a6304](.artifacts/records/project__check-run/rec-be6d0d5a-d576-41c7-9466-22e2c25a6304.md))_

## verify-plugin-root-and-cli-landing

### Acceptance
- **verify-plugin-root-and-cli-landing**: R4; manual; packaging _(id: [rec-e2174663-bdbf-4250-aa23-5075f95e0c8d](.artifacts/records/project__acceptance/rec-e2174663-bdbf-4250-aa23-5075f95e0c8d.md))_

### Check
- **verify-plugin-root-and-cli-landing**: rec-e2174663-bdbf-4250-aa23-5075f95e0c8d; 269ab7bde409ee04e1d7fa5de38363d9acb46c1e; pass; manual; inline _(id: [rec-50bafa17-3590-4c1e-8b34-946abf764d36](.artifacts/records/project__check-run/rec-50bafa17-3590-4c1e-8b34-946abf764d36.md))_

## verify-pyproject-pypi

### Acceptance
- **verify-pyproject-pypi**: R2; check; packaging; ~/adaptive-artifacts/scripts/prove_uv_tool_install.sh _(id: [rec-080abeb4-e1c8-4c6d-a325-fa84f67bf3a5](.artifacts/records/project__acceptance/rec-080abeb4-e1c8-4c6d-a325-fa84f67bf3a5.md))_

### Check
- **verify-pyproject-pypi**: rec-080abeb4-e1c8-4c6d-a325-fa84f67bf3a5; 5257818a25994a1b41742f10c48d12cb7e5d767c; pass; check _(id: [rec-50e47795-e749-40c1-be41-f18cdf41896e](.artifacts/records/project__check-run/rec-50e47795-e749-40c1-be41-f18cdf41896e.md))_
- **verify-pyproject-pypi**: rec-cd94256a-2af1-4b2a-894c-58ebd9cb594f; 5257818a25994a1b41742f10c48d12cb7e5d767c; pass; manual; andrewyin _(id: [rec-c93fe80d-45e4-4e83-b404-0291a764e7bc](.artifacts/records/project__check-run/rec-c93fe80d-45e4-4e83-b404-0291a764e7bc.md))_

## verify-pyproject-pypi-aa-gate

### Acceptance
- **verify-pyproject-pypi-aa-gate**: R8; manual; packaging _(id: [rec-cd94256a-2af1-4b2a-894c-58ebd9cb594f](.artifacts/records/project__acceptance/rec-cd94256a-2af1-4b2a-894c-58ebd9cb594f.md))_

### Check
- **verify-pyproject-pypi-aa-gate**: rec-cd94256a-2af1-4b2a-894c-58ebd9cb594f; 5257818a25994a1b41742f10c48d12cb7e5d767c; pass; manual; andrewyin _(id: [rec-f4ef0011-3019-4081-aacb-23ead5a6870c](.artifacts/records/project__check-run/rec-f4ef0011-3019-4081-aacb-23ead5a6870c.md))_

## verify-pyproject-pypi-readme

### Acceptance
- **verify-pyproject-pypi-readme**: R6; check; packaging; grep -qiE "uv tool install" README.md && grep -qiE "git\+https://github.com/andrewy1n/adaptive-artifacts" README.md && grep -qiE "PyPI.*(defer|later|not yet|wait)" README.md && ! test -f pyproject.toml _(id: [rec-df1c71df-699a-42b3-ae6d-8c7d0a764007](.artifacts/records/project__acceptance/rec-df1c71df-699a-42b3-ae6d-8c7d0a764007.md))_

### Check
- **verify-pyproject-pypi-readme**: rec-df1c71df-699a-42b3-ae6d-8c7d0a764007; 5257818a25994a1b41742f10c48d12cb7e5d767c; pass; check _(id: [rec-6294ebb8-e5a0-45f9-869b-c194ce90b164](.artifacts/records/project__check-run/rec-6294ebb8-e5a0-45f9-869b-c194ce90b164.md))_

## verify-pyproject-pypi-shims

### Acceptance
- **verify-pyproject-pypi-shims**: R4; check; packaging; ~/adaptive-artifacts/bin/adaptive-artifacts --help >/dev/null && python3 ~/adaptive-artifacts/tools/artifacts.py --help >/dev/null _(id: [rec-064ae8ac-d426-4a95-a9a5-71cd77ec4dfd](.artifacts/records/project__acceptance/rec-064ae8ac-d426-4a95-a9a5-71cd77ec4dfd.md))_

### Check
- **verify-pyproject-pypi-shims**: rec-064ae8ac-d426-4a95-a9a5-71cd77ec4dfd; 5257818a25994a1b41742f10c48d12cb7e5d767c; pass; check _(id: [rec-7edd7ced-8ab6-4b9f-b1b4-0344aaa94f50](.artifacts/records/project__check-run/rec-7edd7ced-8ab6-4b9f-b1b4-0344aaa94f50.md))_

## verify-quiet-header

### Acceptance
- **verify-quiet-header**: check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k once_tally _(id: [rec-bc634371-b551-458a-a1c6-a010d02af538](.artifacts/records/project__acceptance/rec-bc634371-b551-458a-a1c6-a010d02af538.md))_

### Check
- **verify-quiet-header**: rec-bc634371-b551-458a-a1c6-a010d02af538; dirty; pass; check _(id: [rec-41d5454e-4c98-49ed-be3a-95a1619ced7d](.artifacts/records/project__check-run/rec-41d5454e-4c98-49ed-be3a-95a1619ced7d.md))_
- **verify-quiet-header**: rec-47663207-ae0c-4fd9-a2f8-e127cd7a753c; dirty; pass; check _(id: [rec-51df4b07-20c8-45d4-89b3-c227730a94d2](.artifacts/records/project__check-run/rec-51df4b07-20c8-45d4-89b3-c227730a94d2.md))_
- **verify-quiet-header**: rec-6fe96e57-e909-4bac-8895-59df57721d8d; dirty; pass; check _(id: [rec-6bc349cc-7f8f-4b98-9664-501e66f4361e](.artifacts/records/project__check-run/rec-6bc349cc-7f8f-4b98-9664-501e66f4361e.md))_
- **verify-quiet-header**: rec-b888f503-6a00-4777-899c-1887b314935d; dirty; pass; check _(id: [rec-9ca5e7d0-234a-40fa-b3d6-b1c664a9923b](.artifacts/records/project__check-run/rec-9ca5e7d0-234a-40fa-b3d6-b1c664a9923b.md))_
- **verify-quiet-header**: rec-ed5ce2ba-5329-44cc-9895-c8dc5586000b; dirty; pass; check _(id: [rec-9e451d65-8e48-4164-a466-b937fdb49495](.artifacts/records/project__check-run/rec-9e451d65-8e48-4164-a466-b937fdb49495.md))_
- **verify-quiet-header**: rec-40732634-5a9c-4595-bc25-89fe2a6a00cc; dirty; pass; check _(id: [rec-e485556f-ed51-46d1-a61f-2fb4d396d904](.artifacts/records/project__check-run/rec-e485556f-ed51-46d1-a61f-2fb4d396d904.md))_

## verify-quiet-header-headers

### Acceptance
- **verify-quiet-header-headers**: check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k done_phases_collapse _(id: [rec-47663207-ae0c-4fd9-a2f8-e127cd7a753c](.artifacts/records/project__acceptance/rec-47663207-ae0c-4fd9-a2f8-e127cd7a753c.md))_

## verify-quiet-header-keys

### Acceptance
- **verify-quiet-header-keys**: check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "number_keys_filter or status_tabs_are_six" _(id: [rec-6fe96e57-e909-4bac-8895-59df57721d8d](.artifacts/records/project__acceptance/rec-6fe96e57-e909-4bac-8895-59df57721d8d.md))_

## verify-quiet-header-stepper

### Acceptance
- **verify-quiet-header-stepper**: check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k stepper _(id: [rec-ed5ce2ba-5329-44cc-9895-c8dc5586000b](.artifacts/records/project__acceptance/rec-ed5ce2ba-5329-44cc-9895-c8dc5586000b.md))_

## verify-quiet-header-suite

### Acceptance
- **verify-quiet-header-suite**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m "not tmux" && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-40732634-5a9c-4595-bc25-89fe2a6a00cc](.artifacts/records/project__acceptance/rec-40732634-5a9c-4595-bc25-89fe2a6a00cc.md))_

## verify-quiet-header-tabs

### Acceptance
- **verify-quiet-header-tabs**: check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "tab_row or tab_labels" _(id: [rec-b888f503-6a00-4777-899c-1887b314935d](.artifacts/records/project__acceptance/rec-b888f503-6a00-4777-899c-1887b314935d.md))_

## verify-readable-layout-phase

### Acceptance
- **verify-readable-layout-phase**: check; dashboard; uv run --with textual --with pytest python -m pytest tests -q _(id: [rec-b9c2eff5-a486-4b57-89bc-cc4a3aa95314](.artifacts/records/project__acceptance/rec-b9c2eff5-a486-4b57-89bc-cc4a3aa95314.md))_

### Check
- **verify-readable-layout-phase**: rec-b9c2eff5-a486-4b57-89bc-cc4a3aa95314; 360ebcc; pass; check _(id: [rec-0efdae3e-e624-4a9e-9b04-d42daa11fd0f](.artifacts/records/project__check-run/rec-0efdae3e-e624-4a9e-9b04-d42daa11fd0f.md))_

## verify-readable-layout-phase-signoff

### Acceptance
- **verify-readable-layout-phase-signoff**: manual; dashboard _(id: [rec-83820e9f-6ff5-407c-aa8f-deb4e441d5a5](.artifacts/records/project__acceptance/rec-83820e9f-6ff5-407c-aa8f-deb4e441d5a5.md))_

### Check
- **verify-readable-layout-phase-signoff**: rec-83820e9f-6ff5-407c-aa8f-deb4e441d5a5; 360ebcc; pass; manual; ayin _(id: [rec-ca53b246-7587-4e4e-9c59-75ca4deed553](.artifacts/records/project__check-run/rec-ca53b246-7587-4e4e-9c59-75ca4deed553.md))_

## verify-red-first

### Acceptance
- **verify-red-first**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_pass_only _(id: [rec-c954223e-18ce-4392-ba4a-051f35046275](.artifacts/records/project__acceptance/rec-c954223e-18ce-4392-ba4a-051f35046275.md))_

### Check
- **verify-red-first**: rec-c954223e-18ce-4392-ba4a-051f35046275; b3159b685f2992638a84ad36d56a81f9ed8e8151; fail; tdd _(id: [rec-28189b12-afcd-4c2b-a2c5-9800c98bf66b](.artifacts/records/project__check-run/rec-28189b12-afcd-4c2b-a2c5-9800c98bf66b.md))_
- **verify-red-first**: rec-c954223e-18ce-4392-ba4a-051f35046275; c14dedbd9ec027e7e79b8eb1508b24d0d65063fc; pass; tdd _(id: [rec-7ee60230-c110-4f33-b770-23ed56cf32bb](.artifacts/records/project__check-run/rec-7ee60230-c110-4f33-b770-23ed56cf32bb.md))_

## verify-red-first-escape

### Acceptance
- **verify-red-first-escape**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_escape _(id: [rec-964973af-b0ff-4bdc-b880-c49820487c8a](.artifacts/records/project__acceptance/rec-964973af-b0ff-4bdc-b880-c49820487c8a.md))_

### Check
- **verify-red-first-escape**: rec-964973af-b0ff-4bdc-b880-c49820487c8a; b3159b685f2992638a84ad36d56a81f9ed8e8151; fail; tdd _(id: [rec-1cff2ee9-9d3b-4ca1-b202-6ad73892bc91](.artifacts/records/project__check-run/rec-1cff2ee9-9d3b-4ca1-b202-6ad73892bc91.md))_
- **verify-red-first-escape**: rec-964973af-b0ff-4bdc-b880-c49820487c8a; c14dedbd9ec027e7e79b8eb1508b24d0d65063fc; pass; tdd _(id: [rec-acd4ed29-d9f3-456b-bec8-9d7269cb547a](.artifacts/records/project__check-run/rec-acd4ed29-d9f3-456b-bec8-9d7269cb547a.md))_

## verify-red-first-methods

### Acceptance
- **verify-red-first-methods**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_other_methods _(id: [rec-9167287b-ab92-4409-89bd-e19a6db7f820](.artifacts/records/project__acceptance/rec-9167287b-ab92-4409-89bd-e19a6db7f820.md))_

### Check
- **verify-red-first-methods**: rec-9167287b-ab92-4409-89bd-e19a6db7f820; b3159b685f2992638a84ad36d56a81f9ed8e8151; fail; tdd _(id: [rec-98211ba1-fc74-4a39-80ce-91eab05e1526](.artifacts/records/project__check-run/rec-98211ba1-fc74-4a39-80ce-91eab05e1526.md))_
- **verify-red-first-methods**: rec-9167287b-ab92-4409-89bd-e19a6db7f820; c14dedbd9ec027e7e79b8eb1508b24d0d65063fc; pass; tdd _(id: [rec-be32d9b7-5a1f-47e1-8095-3353c79104fa](.artifacts/records/project__check-run/rec-be32d9b7-5a1f-47e1-8095-3353c79104fa.md))_

## verify-red-first-order

### Acceptance
- **verify-red-first-order**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_order _(id: [rec-cb28d166-0f0f-49ed-8751-925ad1e8d708](.artifacts/records/project__acceptance/rec-cb28d166-0f0f-49ed-8751-925ad1e8d708.md))_

### Check
- **verify-red-first-order**: rec-cb28d166-0f0f-49ed-8751-925ad1e8d708; c14dedbd9ec027e7e79b8eb1508b24d0d65063fc; pass; tdd _(id: [rec-449bcc1e-5bc3-4938-86e4-9db40d324a2f](.artifacts/records/project__check-run/rec-449bcc1e-5bc3-4938-86e4-9db40d324a2f.md))_
- **verify-red-first-order**: rec-cb28d166-0f0f-49ed-8751-925ad1e8d708; b3159b685f2992638a84ad36d56a81f9ed8e8151; fail; tdd _(id: [rec-bb86ff24-33c3-4950-b075-453cfc1ceaff](.artifacts/records/project__check-run/rec-bb86ff24-33c3-4950-b075-453cfc1ceaff.md))_

## verify-red-first-skills

### Acceptance
- **verify-red-first-skills**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-5990039c-6afc-47d7-9a08-43aafa3d1a8e](.artifacts/records/project__acceptance/rec-5990039c-6afc-47d7-9a08-43aafa3d1a8e.md))_

### Check
- **verify-red-first-skills**: rec-5990039c-6afc-47d7-9a08-43aafa3d1a8e; c14dedbd9ec027e7e79b8eb1508b24d0d65063fc; pass; check _(id: [rec-423e77e6-9e33-4dd6-b9be-7823d6b85ac6](.artifacts/records/project__check-run/rec-423e77e6-9e33-4dd6-b9be-7823d6b85ac6.md))_

## verify-rename-agent-affidavit

### Acceptance
- **verify-rename-agent-affidavit**: R2; tdd; packaging; test -x bin/aff && ! test -e bin/se-workflow && bin/aff check --help >/dev/null && bin/aff close-batch --help >/dev/null && python3 -c "import importlib.util as u; assert u.find_spec('affidavit'); assert u.find_spec('se_workflow') is None" _(id: [rec-d5e70a1b-64c9-4d59-9de9-81f5d57e751f](.artifacts/records/project__acceptance/rec-d5e70a1b-64c9-4d59-9de9-81f5d57e751f.md))_

### Check
- **verify-rename-agent-affidavit**: rec-d5e70a1b-64c9-4d59-9de9-81f5d57e751f; ff37be68a378225c1b065efdeef9e4f611898e19; pass; tdd _(id: [rec-7c95d9c8-1ea1-4342-9be3-e88dbfebd173](.artifacts/records/project__check-run/rec-7c95d9c8-1ea1-4342-9be3-e88dbfebd173.md))_
- **verify-rename-agent-affidavit**: rec-d5e70a1b-64c9-4d59-9de9-81f5d57e751f; dirty; fail; tdd _(id: [rec-ed1ff607-9aa3-4ce2-a15f-42e74cb302e2](.artifacts/records/project__check-run/rec-ed1ff607-9aa3-4ce2-a15f-42e74cb302e2.md))_

## verify-rename-agent-affidavit-identity

### Acceptance
- **verify-rename-agent-affidavit-identity**: R1; check; packaging; python3 scripts/check_affidavit_plugin_names.py && python3 scripts/check_affidavit_contract_project.py && uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-63816a0d-c37b-4fb3-8bbf-a0a33a762939](.artifacts/records/project__acceptance/rec-63816a0d-c37b-4fb3-8bbf-a0a33a762939.md))_

### Check
- **verify-rename-agent-affidavit-identity**: rec-63816a0d-c37b-4fb3-8bbf-a0a33a762939; ff37be68a378225c1b065efdeef9e4f611898e19; fail; check _(id: [rec-1ff5d32d-498d-4e09-ad97-0a7206b3004d](.artifacts/records/project__check-run/rec-1ff5d32d-498d-4e09-ad97-0a7206b3004d.md))_
- **verify-rename-agent-affidavit-identity**: rec-63816a0d-c37b-4fb3-8bbf-a0a33a762939; ff37be68a378225c1b065efdeef9e4f611898e19; pass; check _(id: [rec-ae7b25fa-5520-4ffc-8d4d-5e06eb1ce477](.artifacts/records/project__check-run/rec-ae7b25fa-5520-4ffc-8d4d-5e06eb1ce477.md))_

## verify-retry-loop

### Acceptance
- **verify-retry-loop**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_retry_loop.py -q _(id: [rec-882f6075-f91a-479c-b426-a0eee0ffba59](.artifacts/records/project__acceptance/rec-882f6075-f91a-479c-b426-a0eee0ffba59.md))_

### Check
- **verify-retry-loop**: rec-882f6075-f91a-479c-b426-a0eee0ffba59; ee1a41be208bfdae700e1b78f9340296d82dae91; fail; tdd _(id: [rec-06ceed68-9985-49ab-8afe-cb6f5ae46934](.artifacts/records/project__check-run/rec-06ceed68-9985-49ab-8afe-cb6f5ae46934.md))_
- **verify-retry-loop**: rec-882f6075-f91a-479c-b426-a0eee0ffba59; 0077727e7e8d3b25e53d5aa1722b5c8f9ca58577; pass; tdd _(id: [rec-1f8ce933-3053-4082-acc2-205434fa5917](.artifacts/records/project__check-run/rec-1f8ce933-3053-4082-acc2-205434fa5917.md))_

## verify-retry-loop-contract

### Acceptance
- **verify-retry-loop-contract**: R9; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_contract_self_consistency.py -q _(id: [rec-0b667469-29df-4007-a46b-05a8b860091a](.artifacts/records/project__acceptance/rec-0b667469-29df-4007-a46b-05a8b860091a.md))_

### Check
- **verify-retry-loop-contract**: rec-0b667469-29df-4007-a46b-05a8b860091a; 0077727e7e8d3b25e53d5aa1722b5c8f9ca58577; pass; check _(id: [rec-88071789-8032-4b6c-b4cf-208f9d56ad30](.artifacts/records/project__check-run/rec-88071789-8032-4b6c-b4cf-208f9d56ad30.md))_

## verify-retry-loop-dashboard

### Acceptance
- **verify-retry-loop-dashboard**: R8; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k "attempt_row or attempt_budget or attempt_snapshot or attempt_title" _(id: [rec-7d873780-5fa8-4f70-af41-851701195ec5](.artifacts/records/project__acceptance/rec-7d873780-5fa8-4f70-af41-851701195ec5.md))_

### Check
- **verify-retry-loop-dashboard**: rec-7d873780-5fa8-4f70-af41-851701195ec5; ee1a41be208bfdae700e1b78f9340296d82dae91; fail; tdd _(id: [rec-64f16e57-2fb5-429d-a774-fbe5113cef83](.artifacts/records/project__check-run/rec-64f16e57-2fb5-429d-a774-fbe5113cef83.md))_
- **verify-retry-loop-dashboard**: rec-7d873780-5fa8-4f70-af41-851701195ec5; 0077727e7e8d3b25e53d5aa1722b5c8f9ca58577; pass; tdd _(id: [rec-8ff6e514-0880-4828-8e5b-ca7a6c8dca7b](.artifacts/records/project__check-run/rec-8ff6e514-0880-4828-8e5b-ca7a6c8dca7b.md))_

## verify-run-facts

### Acceptance
- **verify-run-facts**: R1; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_cli.py -q _(id: [rec-421c70cd-39cf-4be7-8247-8e651bd0617d](.artifacts/records/project__acceptance/rec-421c70cd-39cf-4be7-8247-8e651bd0617d.md))_

### Check
- **verify-run-facts**: rec-421c70cd-39cf-4be7-8247-8e651bd0617d; dirty; pass; tdd _(id: [rec-34c7b8d2-ea71-440b-9a57-ebcee0786044](.artifacts/records/project__check-run/rec-34c7b8d2-ea71-440b-9a57-ebcee0786044.md))_

## verify-run-facts-contract

### Acceptance
- **verify-run-facts-contract**: R2; check; dashboard; uv run --with pytest python -m pytest tests/test_estimate_contract.py -q _(id: [rec-559ae6f2-7bcd-483a-b04a-47312542235e](.artifacts/records/project__acceptance/rec-559ae6f2-7bcd-483a-b04a-47312542235e.md))_

### Check
- **verify-run-facts-contract**: rec-559ae6f2-7bcd-483a-b04a-47312542235e; dirty; pass; check _(id: [rec-47b6c395-57d0-4db2-9d8c-b67bba203107](.artifacts/records/project__check-run/rec-47b6c395-57d0-4db2-9d8c-b67bba203107.md))_

## verify-run-facts-dashboard

### Acceptance
- **verify-run-facts-dashboard**: R6; check; dashboard; test -z "$(git diff --name-only main -- dashboard/)" _(id: [rec-3a8cb50a-c1bf-4698-8b25-1a91d9ad70a2](.artifacts/records/project__acceptance/rec-3a8cb50a-c1bf-4698-8b25-1a91d9ad70a2.md))_

### Check
- **verify-run-facts-dashboard**: rec-3a8cb50a-c1bf-4698-8b25-1a91d9ad70a2; dirty; pass; check _(id: [rec-c79fee1b-527c-4ba9-bb42-803676decc50](.artifacts/records/project__check-run/rec-c79fee1b-527c-4ba9-bb42-803676decc50.md))_

## verify-run-facts-skill

### Acceptance
- **verify-run-facts-skill**: R3; check; dashboard; uv run --with pytest python -m pytest tests/test_estimate_skill.py tests/test_skill_contract_consistency.py tests/test_plan_wave_rules.py tests/test_plan_trace.py -q _(id: [rec-a7ce611e-022e-44b3-a49b-512336cf04a6](.artifacts/records/project__acceptance/rec-a7ce611e-022e-44b3-a49b-512336cf04a6.md))_

### Check
- **verify-run-facts-skill**: rec-a7ce611e-022e-44b3-a49b-512336cf04a6; dirty; pass; check _(id: [rec-1061f910-3272-419b-a5a1-6284f7ed3d6f](.artifacts/records/project__check-run/rec-1061f910-3272-419b-a5a1-6284f7ed3d6f.md))_

## verify-run-facts-suite

### Acceptance
- **verify-run-facts-suite**: R1; check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m "not tmux" && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-b43db00d-52de-4ffe-ba39-07011280cbbb](.artifacts/records/project__acceptance/rec-b43db00d-52de-4ffe-ba39-07011280cbbb.md))_

### Check
- **verify-run-facts-suite**: rec-b43db00d-52de-4ffe-ba39-07011280cbbb; dirty; fail; check _(id: [rec-389edfb5-bb7e-4fff-9659-263ef95dcf07](.artifacts/records/project__check-run/rec-389edfb5-bb7e-4fff-9659-263ef95dcf07.md))_
- **verify-run-facts-suite**: rec-b43db00d-52de-4ffe-ba39-07011280cbbb; dirty; pass; check _(id: [rec-39c113c6-6e92-4900-bc66-5b3abb6be177](.artifacts/records/project__check-run/rec-39c113c6-6e92-4900-bc66-5b3abb6be177.md))_

## verify-side-rail-calm

### Acceptance
- **verify-side-rail-calm**: R1; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts _(id: [rec-a9846788-5dff-47fa-9846-c377b3a877fa](.artifacts/records/project__acceptance/rec-a9846788-5dff-47fa-9846-c377b3a877fa.md))_

### Check
- **verify-side-rail-calm**: rec-a9846788-5dff-47fa-9846-c377b3a877fa; c747adfaf64276bb807bb99e17174c1d3542a572; pass; check _(id: [rec-5379216c-6283-4d16-86e8-b286ae40c83a](.artifacts/records/project__check-run/rec-5379216c-6283-4d16-86e8-b286ae40c83a.md))_

## verify-side-rail-calm-demo

### Acceptance
- **verify-side-rail-calm-demo**: R2; manual; dashboard _(id: [rec-01b90989-ee7e-4df1-b446-676d3674695f](.artifacts/records/project__acceptance/rec-01b90989-ee7e-4df1-b446-676d3674695f.md))_

### Check
- **verify-side-rail-calm-demo**: rec-01b90989-ee7e-4df1-b446-676d3674695f; c747adfaf64276bb807bb99e17174c1d3542a572; pass; manual; agent _(id: [rec-f996d945-2488-4e2e-93f6-7ac93a873ebe](.artifacts/records/project__check-run/rec-f996d945-2488-4e2e-93f6-7ac93a873ebe.md))_

## verify-side-rail-calm-overlay

### Acceptance
- **verify-side-rail-calm-overlay**: R8; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R8 _(id: [rec-bae7396a-0f2c-42db-a6bf-dbd6893863fc](.artifacts/records/project__acceptance/rec-bae7396a-0f2c-42db-a6bf-dbd6893863fc.md))_

### Check
- **verify-side-rail-calm-overlay**: rec-bae7396a-0f2c-42db-a6bf-dbd6893863fc; c747adfaf64276bb807bb99e17174c1d3542a572; pass; check _(id: [rec-346ae04f-9c9d-45dc-b1cd-999340d699f0](.artifacts/records/project__check-run/rec-346ae04f-9c9d-45dc-b1cd-999340d699f0.md))_

## verify-side-rail-calm-route

### Acceptance
- **verify-side-rail-calm-route**: R5; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R5 _(id: [rec-9bcd444d-4c5f-4668-bd26-f96097527713](.artifacts/records/project__acceptance/rec-9bcd444d-4c5f-4668-bd26-f96097527713.md))_

### Check
- **verify-side-rail-calm-route**: rec-9bcd444d-4c5f-4668-bd26-f96097527713; c747adfaf64276bb807bb99e17174c1d3542a572; pass; check _(id: [rec-39f022b1-7bc5-4bfc-8177-3db31cc2dad5](.artifacts/records/project__check-run/rec-39f022b1-7bc5-4bfc-8177-3db31cc2dad5.md))_

## verify-side-rail-calm-teaser

### Acceptance
- **verify-side-rail-calm-teaser**: R3; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/sideRailCalm.test.ts -t R3 _(id: [rec-8fd2727a-4e1b-4fcf-bff9-fe3f092710c2](.artifacts/records/project__acceptance/rec-8fd2727a-4e1b-4fcf-bff9-fe3f092710c2.md))_

### Check
- **verify-side-rail-calm-teaser**: rec-8fd2727a-4e1b-4fcf-bff9-fe3f092710c2; c747adfaf64276bb807bb99e17174c1d3542a572; pass; check _(id: [rec-49be90d1-5177-41bc-a847-d8aa46d81189](.artifacts/records/project__check-run/rec-49be90d1-5177-41bc-a847-d8aa46d81189.md))_

## verify-spec-view

### Acceptance
- **verify-spec-view**: R2; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py tests/test_dashboard_integration.py -q -k "phase_screen or once" _(id: [rec-323fc48e-f2ba-4fcf-bea1-344c61a9f338](.artifacts/records/project__acceptance/rec-323fc48e-f2ba-4fcf-bea1-344c61a9f338.md))_

### Check
- **verify-spec-view**: rec-323fc48e-f2ba-4fcf-bea1-344c61a9f338; dirty; pass; check _(id: [rec-145ad5aa-3475-4107-a9d7-d1a124b58d38](.artifacts/records/project__check-run/rec-145ad5aa-3475-4107-a9d7-d1a124b58d38.md))_

## verify-spec-view-model

### Acceptance
- **verify-spec-view-model**: R7; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k phase_screen _(id: [rec-b45738a2-3a4d-4384-8296-2710d92c7f41](.artifacts/records/project__acceptance/rec-b45738a2-3a4d-4384-8296-2710d92c7f41.md))_

### Check
- **verify-spec-view-model**: rec-b45738a2-3a4d-4384-8296-2710d92c7f41; dirty; pass; check _(id: [rec-0251f9f1-1d20-4445-8112-ebd2b8119d44](.artifacts/records/project__check-run/rec-0251f9f1-1d20-4445-8112-ebd2b8119d44.md))_

## verify-spec-view-suite

### Acceptance
- **verify-spec-view-suite**: R13; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py tests/test_dashboard_integration.py -q -k "phase_screen or once" _(id: [rec-09c72984-b31a-4157-a36c-f922a4700458](.artifacts/records/project__acceptance/rec-09c72984-b31a-4157-a36c-f922a4700458.md))_

### Check
- **verify-spec-view-suite**: rec-09c72984-b31a-4157-a36c-f922a4700458; dirty; pass; check _(id: [rec-8402b94b-7bc4-4593-b0e7-26789e290d82](.artifacts/records/project__check-run/rec-8402b94b-7bc4-4593-b0e7-26789e290d82.md))_

## verify-status-line-phase

### Acceptance
- **verify-status-line-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-2e2b15a3-c245-48ab-874a-9efbfd69ff60](.artifacts/records/project__acceptance/rec-2e2b15a3-c245-48ab-874a-9efbfd69ff60.md))_

### Check
- **verify-status-line-phase**: rec-2e2b15a3-c245-48ab-874a-9efbfd69ff60; afd60845e9ffcfcd44d028603b46bdcffadc313a; pass; check _(id: [rec-43db24a6-a3a6-4320-b00e-64c22fd00fa5](.artifacts/records/project__check-run/rec-43db24a6-a3a6-4320-b00e-64c22fd00fa5.md))_

## verify-table-state-phase

### Acceptance
- **verify-table-state-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-c31c7b82-4a88-43bf-877c-1ffabb4f08e3](.artifacts/records/project__acceptance/rec-c31c7b82-4a88-43bf-877c-1ffabb4f08e3.md))_

### Check
- **verify-table-state-phase**: rec-c31c7b82-4a88-43bf-877c-1ffabb4f08e3; 3d740d2b7c02175520ca2f03e713c70c450c6603; pass; check _(id: [rec-cdcf77bc-e4da-4c06-8707-0180febff2ce](.artifacts/records/project__check-run/rec-cdcf77bc-e4da-4c06-8707-0180febff2ce.md))_

### Observation
- **verify-table-state-phase**: Without b104980 the stale-width resize race fails the tmux test in about 4 of 5 runs; the pilot test from b104980 is the deterministic guard.; dashboard-bugfix _(id: [rec-9feddfcd-4869-456a-9597-16da85a789cc](.artifacts/records/project__investigation-observation/rec-9feddfcd-4869-456a-9597-16da85a789cc.md))_

## verify-task-details-phase

### Acceptance
- **verify-task-details-phase**: check; dashboard; uv run --with textual --with pytest python -m pytest tests -q _(id: [rec-98ab04e9-ab1a-488f-8712-716c9a11b7ba](.artifacts/records/project__acceptance/rec-98ab04e9-ab1a-488f-8712-716c9a11b7ba.md))_

### Check
- **verify-task-details-phase**: rec-98ab04e9-ab1a-488f-8712-716c9a11b7ba; 70b0501; pass; check _(id: [rec-d63e8d3d-8054-4434-9f6a-908518f99237](.artifacts/records/project__check-run/rec-d63e8d3d-8054-4434-9f6a-908518f99237.md))_

## verify-task-details-phase-signoff

### Acceptance
- **verify-task-details-phase-signoff**: manual; dashboard _(id: [rec-11643a9d-4693-4761-b94a-ba3a6be27ad6](.artifacts/records/project__acceptance/rec-11643a9d-4693-4761-b94a-ba3a6be27ad6.md))_

### Check
- **verify-task-details-phase-signoff**: rec-11643a9d-4693-4761-b94a-ba3a6be27ad6; 03d561c; pass; manual; ayin _(id: [rec-3049cecc-9049-4792-b1d6-8d607534885f](.artifacts/records/project__check-run/rec-3049cecc-9049-4792-b1d6-8d607534885f.md))_

## verify-task-graph

### Acceptance
- **verify-task-graph**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k depends_on && npm --prefix dashboard/web/ui exec -- vitest run src/taskGraph.test.ts _(id: [rec-ec5f4fea-f3c7-4318-a7b9-3d4f121f3d48](.artifacts/records/project__acceptance/rec-ec5f4fea-f3c7-4318-a7b9-3d4f121f3d48.md))_

### Check
- **verify-task-graph**: rec-ec5f4fea-f3c7-4318-a7b9-3d4f121f3d48; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-7064a0e7-7d08-417b-a44c-4cd8f5e8d1ed](.artifacts/records/project__check-run/rec-7064a0e7-7d08-417b-a44c-4cd8f5e8d1ed.md))_

## verify-task-graph-demo

### Acceptance
- **verify-task-graph-demo**: R1; manual; dashboard _(id: [rec-377f96ac-6702-495f-88f4-6e17a3557cc7](.artifacts/records/project__acceptance/rec-377f96ac-6702-495f-88f4-6e17a3557cc7.md))_

### Check
- **verify-task-graph-demo**: rec-377f96ac-6702-495f-88f4-6e17a3557cc7; bafc565bce46cca3f85b02a392c10073e42b300d; pass; manual; auto-web-calm _(id: [rec-6e8deae4-9e71-4a22-a3b3-a9cd25683df9](.artifacts/records/project__check-run/rec-6e8deae4-9e71-4a22-a3b3-a9cd25683df9.md))_

## verify-task-graph-nav

### Acceptance
- **verify-task-graph-nav**: R4; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/taskGraph.test.ts -t R4 _(id: [rec-a87f3f4e-894c-403c-a566-334b61819b69](.artifacts/records/project__acceptance/rec-a87f3f4e-894c-403c-a566-334b61819b69.md))_

### Check
- **verify-task-graph-nav**: rec-a87f3f4e-894c-403c-a566-334b61819b69; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-cd327540-7571-4e55-9c6f-fc7b786eabfb](.artifacts/records/project__check-run/rec-cd327540-7571-4e55-9c6f-fc7b786eabfb.md))_

## verify-task-graph-skip

### Acceptance
- **verify-task-graph-skip**: R6; check; dashboard; npm --prefix dashboard/web/ui exec -- vitest run src/taskGraph.test.ts -t R6 _(id: [rec-f107d90f-d6c7-4057-8d27-d2fb1d9160ee](.artifacts/records/project__acceptance/rec-f107d90f-d6c7-4057-8d27-d2fb1d9160ee.md))_

### Check
- **verify-task-graph-skip**: rec-f107d90f-d6c7-4057-8d27-d2fb1d9160ee; bafc565bce46cca3f85b02a392c10073e42b300d; pass; check _(id: [rec-d2cae125-bc2a-4bcf-bca2-b85c5a09dc4d](.artifacts/records/project__check-run/rec-d2cae125-bc2a-4bcf-bca2-b85c5a09dc4d.md))_

## verify-task-navigation-phase

### Acceptance
- **verify-task-navigation-phase**: check; dashboard; uv run --with textual --with pytest python -m pytest tests -q _(id: [rec-b9307639-88bf-43f4-8ad7-d0e4a77db060](.artifacts/records/project__acceptance/rec-b9307639-88bf-43f4-8ad7-d0e4a77db060.md))_

### Check
- **verify-task-navigation-phase**: rec-892a40a7-5d4e-4027-a096-a484d58b9787; 671220afbe8e7adb39f8e250bfafed07823d11c4; pass; manual; Andrew Yin _(id: [rec-553ce6d1-ba21-49fc-9c32-cbab20dab9ca](.artifacts/records/project__check-run/rec-553ce6d1-ba21-49fc-9c32-cbab20dab9ca.md))_
- **verify-task-navigation-phase**: rec-b9307639-88bf-43f4-8ad7-d0e4a77db060; 671220afbe8e7adb39f8e250bfafed07823d11c4; pass; check _(id: [rec-ac579a85-7728-4f68-9674-bdc27b578da9](.artifacts/records/project__check-run/rec-ac579a85-7728-4f68-9674-bdc27b578da9.md))_
- **verify-task-navigation-phase**: rec-b9307639-88bf-43f4-8ad7-d0e4a77db060; 671220afbe8e7adb39f8e250bfafed07823d11c4; pass; check _(id: [rec-f5162a90-c6e6-48fe-b3ae-2aaffcf1ddae](.artifacts/records/project__check-run/rec-f5162a90-c6e6-48fe-b3ae-2aaffcf1ddae.md))_

## verify-task-navigation-phase-signoff

### Acceptance
- **verify-task-navigation-phase-signoff**: manual; dashboard _(id: [rec-892a40a7-5d4e-4027-a096-a484d58b9787](.artifacts/records/project__acceptance/rec-892a40a7-5d4e-4027-a096-a484d58b9787.md))_

## verify-task-rows-phase

### Acceptance
- **verify-task-rows-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux -rf _(id: [rec-92df6b15-9068-4342-b3fa-899bc28247b3](.artifacts/records/project__acceptance/rec-92df6b15-9068-4342-b3fa-899bc28247b3.md))_

### Check
- **verify-task-rows-phase**: rec-92df6b15-9068-4342-b3fa-899bc28247b3; e6591ab8dd58b85e63d1bed9702b6edaf0b236a1; pass; check _(id: [rec-07e2fbea-ed1f-4ea9-95b1-0b6416449996](.artifacts/records/project__check-run/rec-07e2fbea-ed1f-4ea9-95b1-0b6416449996.md))_

## verify-task-worktrees

### Acceptance
- **verify-task-worktrees**: R27; check; workflow-loop; python3 -m pytest tests/test_task_commit.py tests/test_task_worktrees.py -q _(id: [rec-0536d65f-7df9-474c-a91b-95c0903d21fb](.artifacts/records/project__acceptance/rec-0536d65f-7df9-474c-a91b-95c0903d21fb.md))_

### Check
- **verify-task-worktrees**: rec-0536d65f-7df9-474c-a91b-95c0903d21fb; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; check _(id: [rec-87f26400-af63-4f7c-9086-24c546e71761](.artifacts/records/project__check-run/rec-87f26400-af63-4f7c-9086-24c546e71761.md))_

## verify-task-worktrees-landing

### Acceptance
- **verify-task-worktrees-landing**: R21; check; workflow-loop; python3 -m pytest tests/test_execute_landing.py tests/test_task_commit.py -q _(id: [rec-0e0a57cf-e8ba-4b5d-b90a-22402bd2890b](.artifacts/records/project__acceptance/rec-0e0a57cf-e8ba-4b5d-b90a-22402bd2890b.md))_

### Check
- **verify-task-worktrees-landing**: rec-0e0a57cf-e8ba-4b5d-b90a-22402bd2890b; ac64d0816c9e14410dce73596abbe3681637d0cc; pass; check _(id: [rec-a836e0c0-1eee-4550-8668-61ce977a583e](.artifacts/records/project__check-run/rec-a836e0c0-1eee-4550-8668-61ce977a583e.md))_

## verify-tiered-verification

### Acceptance
- **verify-tiered-verification**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "runner or background or check_run" _(id: [rec-e094b9fe-4161-4ebd-81ad-00b66dce7444](.artifacts/records/project__acceptance/rec-e094b9fe-4161-4ebd-81ad-00b66dce7444.md))_

### Check
- **verify-tiered-verification**: rec-e094b9fe-4161-4ebd-81ad-00b66dce7444; dirty; fail; tdd _(id: [rec-3e568900-d5ec-445c-9d0c-ba14ccaeae3f](.artifacts/records/project__check-run/rec-3e568900-d5ec-445c-9d0c-ba14ccaeae3f.md))_
- **verify-tiered-verification**: rec-e094b9fe-4161-4ebd-81ad-00b66dce7444; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; tdd _(id: [rec-a20e2413-ec98-4a31-ab42-c74cd5d6c8bd](.artifacts/records/project__check-run/rec-a20e2413-ec98-4a31-ab42-c74cd5d6c8bd.md))_

## verify-tiered-verification-fix

### Acceptance
- **verify-tiered-verification-fix**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "fix or cluster or budget" _(id: [rec-3441488d-4728-4c7e-855a-ef05fc967f31](.artifacts/records/project__acceptance/rec-3441488d-4728-4c7e-855a-ef05fc967f31.md))_

### Check
- **verify-tiered-verification-fix**: rec-3441488d-4728-4c7e-855a-ef05fc967f31; dirty; fail; tdd _(id: [rec-60a08648-2453-4612-b2a3-9cc4610430ef](.artifacts/records/project__check-run/rec-60a08648-2453-4612-b2a3-9cc4610430ef.md))_
- **verify-tiered-verification-fix**: rec-3441488d-4728-4c7e-855a-ef05fc967f31; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; tdd _(id: [rec-b050a616-916d-499f-8922-b9a2917b1a95](.artifacts/records/project__check-run/rec-b050a616-916d-499f-8922-b9a2917b1a95.md))_

## verify-tiered-verification-gate

### Acceptance
- **verify-tiered-verification-gate**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k gate _(id: [rec-6c629730-fc3a-4ca1-9d42-88c84c5b8b34](.artifacts/records/project__acceptance/rec-6c629730-fc3a-4ca1-9d42-88c84c5b8b34.md))_

### Check
- **verify-tiered-verification-gate**: rec-6c629730-fc3a-4ca1-9d42-88c84c5b8b34; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; tdd _(id: [rec-2774e5e4-c77b-434e-b925-10be104a10cc](.artifacts/records/project__check-run/rec-2774e5e4-c77b-434e-b925-10be104a10cc.md))_
- **verify-tiered-verification-gate**: rec-6c629730-fc3a-4ca1-9d42-88c84c5b8b34; dirty; fail; tdd _(id: [rec-de87e2d2-4a36-4ff8-9e04-33e7452816a3](.artifacts/records/project__check-run/rec-de87e2d2-4a36-4ff8-9e04-33e7452816a3.md))_

## verify-tiered-verification-surfaces

### Acceptance
- **verify-tiered-verification-surfaces**: R6; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k tier2 && uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-07249524-c6b9-49bf-8823-074594abbd01](.artifacts/records/project__acceptance/rec-07249524-c6b9-49bf-8823-074594abbd01.md))_

### Check
- **verify-tiered-verification-surfaces**: rec-07249524-c6b9-49bf-8823-074594abbd01; dirty; fail; check _(id: [rec-2b894e41-e3ec-4ceb-b87d-ff1946dd257f](.artifacts/records/project__check-run/rec-2b894e41-e3ec-4ceb-b87d-ff1946dd257f.md))_
- **verify-tiered-verification-surfaces**: rec-07249524-c6b9-49bf-8823-074594abbd01; 87fb88a22889fc016d21b6dbece2e02836fca56a; pass; check _(id: [rec-c8aff61d-c10a-4960-9f58-9e583315e4d1](.artifacts/records/project__check-run/rec-c8aff61d-c10a-4960-9f58-9e583315e4d1.md))_

## verify-tmux-integration-phase

### Acceptance
- **verify-tmux-integration-phase**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests/test_tmux_integration.py -q _(id: [rec-66a8f44a-bfea-4ee2-aea0-cbe426d17d69](.artifacts/records/project__acceptance/rec-66a8f44a-bfea-4ee2-aea0-cbe426d17d69.md))_

### Check
- **verify-tmux-integration-phase**: rec-66a8f44a-bfea-4ee2-aea0-cbe426d17d69; ea5a5c9; pass; tdd _(id: [rec-08b2c386-6b30-4edb-ae03-1e4897affc66](.artifacts/records/project__check-run/rec-08b2c386-6b30-4edb-ae03-1e4897affc66.md))_
- **verify-tmux-integration-phase**: rec-4a323bc2-c820-4133-8409-d9be1a13b97a; aa:227523b se:ea5a5c9; pass; check _(id: [rec-9298f363-45b4-4925-a9fa-c1d4ab529196](.artifacts/records/project__check-run/rec-9298f363-45b4-4925-a9fa-c1d4ab529196.md))_

## verify-tmux-integration-phase-suites

### Acceptance
- **verify-tmux-integration-phase-suites**: check; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q && cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-4a323bc2-c820-4133-8409-d9be1a13b97a](.artifacts/records/project__acceptance/rec-4a323bc2-c820-4133-8409-d9be1a13b97a.md))_

## verify-tmux-plugin-entry

### Acceptance
- **verify-tmux-plugin-entry**: tdd; dashboard; uv run --with pytest --with textual pytest -m tmux tests/test_tmux_integration.py tests/test_e2e_dashboard.py tests/test_tmux_entry.py _(id: [rec-307dcaee-56c1-444b-8e02-b54d47eb903a](.artifacts/records/project__acceptance/rec-307dcaee-56c1-444b-8e02-b54d47eb903a.md))_

### Check
- **verify-tmux-plugin-entry**: rec-81b6561f-39c6-4892-91e4-e2a043e7dd9b; dirty; pass; check _(id: [rec-08bdaf65-fa59-4c53-a5c6-33301962123b](.artifacts/records/project__check-run/rec-08bdaf65-fa59-4c53-a5c6-33301962123b.md))_
- **verify-tmux-plugin-entry**: rec-22a2f699-9b2e-4971-8f8f-72f726491c0f; dirty; pass; check _(id: [rec-332dbaf0-4782-47d9-8e6d-e17b37b70058](.artifacts/records/project__check-run/rec-332dbaf0-4782-47d9-8e6d-e17b37b70058.md))_
- **verify-tmux-plugin-entry**: rec-307dcaee-56c1-444b-8e02-b54d47eb903a; dirty; pass; tdd _(id: [rec-9895eccc-a929-4aab-9958-a100220972af](.artifacts/records/project__check-run/rec-9895eccc-a929-4aab-9958-a100220972af.md))_
- **verify-tmux-plugin-entry**: rec-bc65d5e2-9428-4c8c-966d-4ebaa8e3cc34; dirty; pass; check _(id: [rec-c4d7e14c-d49a-48ce-808d-e768c5fa4c15](.artifacts/records/project__check-run/rec-c4d7e14c-d49a-48ce-808d-e768c5fa4c15.md))_
- **verify-tmux-plugin-entry**: rec-c78b573b-fc0f-4ab7-8f1a-52f73766dc61; dirty; pass; check _(id: [rec-f6d58704-063a-4a24-b4d0-0bdab29d2da6](.artifacts/records/project__check-run/rec-f6d58704-063a-4a24-b4d0-0bdab29d2da6.md))_

## verify-tmux-plugin-entry-conf-gone

### Acceptance
- **verify-tmux-plugin-entry-conf-gone**: check; dashboard; test ! -e dashboard/tmux.conf && ! grep -rnE 'dashboard/tmux\.conf|SE_WORKFLOW_DASHBOARD' dashboard scripts tests README.md _(id: [rec-bc65d5e2-9428-4c8c-966d-4ebaa8e3cc34](.artifacts/records/project__acceptance/rec-bc65d5e2-9428-4c8c-966d-4ebaa8e3cc34.md))_

## verify-tmux-plugin-entry-full-suite

### Acceptance
- **verify-tmux-plugin-entry-full-suite**: check; dashboard; uv run --with pytest --with textual pytest && uv run --with pytest --with textual pytest -m tmux _(id: [rec-c78b573b-fc0f-4ab7-8f1a-52f73766dc61](.artifacts/records/project__acceptance/rec-c78b573b-fc0f-4ab7-8f1a-52f73766dc61.md))_

## verify-tmux-plugin-entry-key-options

### Acceptance
- **verify-tmux-plugin-entry-key-options**: check; dashboard; uv run --with pytest --with textual pytest -m tmux tests/test_tmux_entry.py -k 'default or custom_keys' _(id: [rec-22a2f699-9b2e-4971-8f8f-72f726491c0f](.artifacts/records/project__acceptance/rec-22a2f699-9b2e-4971-8f8f-72f726491c0f.md))_

## verify-tmux-plugin-entry-readme

### Acceptance
- **verify-tmux-plugin-entry-readme**: check; dashboard; grep -q '^## Quick start' README.md && grep -q "@plugin 'andrewy1n/se-workflow'" README.md && grep -q 'run-shell' README.md _(id: [rec-81b6561f-39c6-4892-91e4-e2a043e7dd9b](.artifacts/records/project__acceptance/rec-81b6561f-39c6-4892-91e4-e2a043e7dd9b.md))_

## verify-verification-policy

### Acceptance
- **verify-verification-policy**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "suite or gate or advisory or policy or mode" _(id: [rec-fd7dcee3-a0a0-44f8-9fda-fad42f6c1aca](.artifacts/records/project__acceptance/rec-fd7dcee3-a0a0-44f8-9fda-fad42f6c1aca.md))_

### Check
- **verify-verification-policy**: rec-fd7dcee3-a0a0-44f8-9fda-fad42f6c1aca; 5e6aacbe37d3cc675d6909aec8c75eee3a8e6178; pass; tdd _(id: [rec-068c5eae-7227-4e60-ae31-8ffe7f6126e0](.artifacts/records/project__check-run/rec-068c5eae-7227-4e60-ae31-8ffe7f6126e0.md))_
- **verify-verification-policy**: rec-fd7dcee3-a0a0-44f8-9fda-fad42f6c1aca; 846e07f37ff5afe6fe37b1475facaeda210e6945; pass; tdd _(id: [rec-372c2f03-1786-4f66-a48d-95648123f71b](.artifacts/records/project__check-run/rec-372c2f03-1786-4f66-a48d-95648123f71b.md))_
- **verify-verification-policy**: rec-fd7dcee3-a0a0-44f8-9fda-fad42f6c1aca; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; tdd _(id: [rec-f5376189-183e-4a58-8173-a75935d81b1d](.artifacts/records/project__check-run/rec-f5376189-183e-4a58-8173-a75935d81b1d.md))_

## verify-verification-policy-contract

### Acceptance
- **verify-verification-policy-contract**: R1; check; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py -q -k phase_gate && python3 -c "import json; from pathlib import Path; b=json.loads(Path('contract/project-design.json').read_text())['phase_gate']['suite']; assert b['mode']=='none'; s=json.loads(Path('.artifacts/project-design.json').read_text())['phase_gate']['suite']; assert s['mode']=='full' and s['gate']=='advisory'" _(id: [rec-6992e9a1-3262-42cf-97d9-ae33c2935da4](.artifacts/records/project__acceptance/rec-6992e9a1-3262-42cf-97d9-ae33c2935da4.md))_

### Check
- **verify-verification-policy-contract**: rec-6992e9a1-3262-42cf-97d9-ae33c2935da4; 846e07f37ff5afe6fe37b1475facaeda210e6945; pass; check _(id: [rec-1e27c349-a4bd-4e49-9e86-112429d486fe](.artifacts/records/project__check-run/rec-1e27c349-a4bd-4e49-9e86-112429d486fe.md))_
- **verify-verification-policy-contract**: rec-6992e9a1-3262-42cf-97d9-ae33c2935da4; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; check _(id: [rec-59c323a9-5de8-4c6b-8823-426d35a256d3](.artifacts/records/project__check-run/rec-59c323a9-5de8-4c6b-8823-426d35a256d3.md))_

## verify-verification-policy-surfaces

### Acceptance
- **verify-verification-policy-surfaces**: R5; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k suite && uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-0e593cda-ace5-410a-b548-a5ab4c5c18fd](.artifacts/records/project__acceptance/rec-0e593cda-ace5-410a-b548-a5ab4c5c18fd.md))_

### Check
- **verify-verification-policy-surfaces**: rec-0e593cda-ace5-410a-b548-a5ab4c5c18fd; 846e07f37ff5afe6fe37b1475facaeda210e6945; pass; check _(id: [rec-1c611eee-4a0b-407b-a9ec-a30e43736876](.artifacts/records/project__check-run/rec-1c611eee-4a0b-407b-a9ec-a30e43736876.md))_
- **verify-verification-policy-surfaces**: rec-0e593cda-ace5-410a-b548-a5ab4c5c18fd; 8119e8e0cc031286ad62da0fd4ba9750b7223749; pass; check _(id: [rec-c8bad3a0-abce-48df-be19-dee9f835b0be](.artifacts/records/project__check-run/rec-c8bad3a0-abce-48df-be19-dee9f835b0be.md))_

## verify-verify-budget

### Acceptance
- **verify-verify-budget**: R5; check; workflow-loop; python3 -c 'import json, subprocess, sys
aa = ["python3", "/home/andrewyin/adaptive-artifacts/tools/artifacts.py", "--root", "/home/andrewyin/se-workflow"]
bad = "pytest tests -q -n 4"
subjects = ("verify-spec-view-suite", "verify-evidence-matrix-suite", "verify-journal-view-suite")
for s in subjects:
    result = subprocess.run([*aa, "list", "--type", "project:acceptance", "--subject", s, "--state", "active", "--full"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
    recs = json.loads(result.stdout)["records"]
    assert len(recs) == 1, s
    cmd = recs[0]["payload"]["verify_command"]
    assert bad not in cmd, cmd
    assert " -k " in cmd, cmd
ids = ("rec-79a4e4c1-cfcb-421b-a023-64563ff645f3", "rec-8432d854-983c-4de9-bb0f-f99b94ecae9a", "rec-f04fa83f-a51f-4800-b3be-9b658df17590")
for i in ids:
    result = subprocess.run([*aa, "get", "--type", "project:work-item", "--id", i], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
    body = json.loads(result.stdout)["body"].lower()
    assert "full suite" not in body, i
print("phase checks only")
' _(id: [rec-0ebd4258-1ee3-4bc5-86e9-617467468a47](.artifacts/records/project__acceptance/rec-0ebd4258-1ee3-4bc5-86e9-617467468a47.md))_

### Check
- **verify-verify-budget**: rec-0ebd4258-1ee3-4bc5-86e9-617467468a47; dirty; pass; check _(id: [rec-d3a7ce5d-d6b6-43d7-a373-e9d9460885e0](.artifacts/records/project__check-run/rec-d3a7ce5d-d6b6-43d7-a373-e9d9460885e0.md))_

## verify-verify-budget-skills

### Acceptance
- **verify-verify-budget-skills**: R1; check; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-fe773a87-15bf-4633-9fc3-54fe95587755](.artifacts/records/project__acceptance/rec-fe773a87-15bf-4633-9fc3-54fe95587755.md))_

### Check
- **verify-verify-budget-skills**: rec-fe773a87-15bf-4633-9fc3-54fe95587755; dirty; pass; check _(id: [rec-aed285c3-4165-45a9-9d64-aa9c9526a564](.artifacts/records/project__check-run/rec-aed285c3-4165-45a9-9d64-aa9c9526a564.md))_

## verify-waits-on-compact

### Acceptance
- **verify-waits-on-compact**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'waiting_row or waits' _(id: [rec-2229ea3a-838b-401d-a6cf-cfe1a00067db](.artifacts/records/project__acceptance/rec-2229ea3a-838b-401d-a6cf-cfe1a00067db.md))_

### Check
- **verify-waits-on-compact**: rec-2229ea3a-838b-401d-a6cf-cfe1a00067db; 98bcbd8 dirty; pass; tdd _(id: [rec-d500da71-250f-4225-885b-d760f0cd9bea](.artifacts/records/project__check-run/rec-d500da71-250f-4225-885b-d760f0cd9bea.md))_

## verify-waits-on-compact-detail

### Acceptance
- **verify-waits-on-compact-detail**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'detail and (Depends or blocked)' _(id: [rec-adf5aef7-5c16-4f3a-bd91-f3b8a49d2e84](.artifacts/records/project__acceptance/rec-adf5aef7-5c16-4f3a-bd91-f3b8a49d2e84.md))_

### Check
- **verify-waits-on-compact-detail**: rec-adf5aef7-5c16-4f3a-bd91-f3b8a49d2e84; 98bcbd8 dirty; pass; tdd _(id: [rec-9800fc0a-7581-41ce-a0c4-5eff49d7be82](.artifacts/records/project__check-run/rec-9800fc0a-7581-41ce-a0c4-5eff49d7be82.md))_

## verify-waits-on-compact-suite

### Acceptance
- **verify-waits-on-compact-suite**: R3; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_tasks.py tests/test_dashboard_app.py -q -k 'waits or title_cell or waiting_row' _(id: [rec-2ad10a07-f300-4aee-b79c-4cabb9cb3e3f](.artifacts/records/project__acceptance/rec-2ad10a07-f300-4aee-b79c-4cabb9cb3e3f.md))_

### Check
- **verify-waits-on-compact-suite**: rec-2ad10a07-f300-4aee-b79c-4cabb9cb3e3f; 98bcbd8 dirty; pass; check _(id: [rec-6e68d8cc-6b7f-42c7-ad57-e5ceaa1451f4](.artifacts/records/project__check-run/rec-6e68d8cc-6b7f-42c7-ad57-e5ceaa1451f4.md))_

## verify-watch-renderer-phase

### Acceptance
- **verify-watch-renderer-phase**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q -k watch_integration _(id: [rec-cadda757-0424-444f-8ae1-31d415d18e6d](.artifacts/records/project__acceptance/rec-cadda757-0424-444f-8ae1-31d415d18e6d.md))_

### Check
- **verify-watch-renderer-phase**: rec-02bac654-25f6-4bc0-b6ec-5efa03a4941e; 227523b; pass; check _(id: [rec-5e3ceb64-1808-4d83-b107-c53695f20ae2](.artifacts/records/project__check-run/rec-5e3ceb64-1808-4d83-b107-c53695f20ae2.md))_
- **verify-watch-renderer-phase**: rec-cadda757-0424-444f-8ae1-31d415d18e6d; 227523b; pass; tdd _(id: [rec-61d5c15f-2e8c-444c-a58b-aa9eeccae777](.artifacts/records/project__check-run/rec-61d5c15f-2e8c-444c-a58b-aa9eeccae777.md))_
- **verify-watch-renderer-phase**: rec-02bac654-25f6-4bc0-b6ec-5efa03a4941e; 227523b; pass; check _(id: [rec-c5dbe94f-0573-4d20-b91b-25ada50fd363](.artifacts/records/project__check-run/rec-c5dbe94f-0573-4d20-b91b-25ada50fd363.md))_
- **verify-watch-renderer-phase**: rec-02bac654-25f6-4bc0-b6ec-5efa03a4941e; 227523b; pass; check _(id: [rec-c8eab97a-7fef-4703-b22a-527699417339](.artifacts/records/project__check-run/rec-c8eab97a-7fef-4703-b22a-527699417339.md))_

## verify-watch-renderer-phase-suites

### Acceptance
- **verify-watch-renderer-phase-suites**: check; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q && cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-02bac654-25f6-4bc0-b6ec-5efa03a4941e](.artifacts/records/project__acceptance/rec-02bac654-25f6-4bc0-b6ec-5efa03a4941e.md))_

## verify-wave-executor

### Acceptance
- **verify-wave-executor**: tdd; workflow-loop; python3 -m pytest tests/test_wave_executor_phase.py -q _(id: [rec-5fe7bba7-cd21-447d-a698-ed9bb1379f58](.artifacts/records/project__acceptance/rec-5fe7bba7-cd21-447d-a698-ed9bb1379f58.md))_

### Check
- **verify-wave-executor**: rec-5fe7bba7-cd21-447d-a698-ed9bb1379f58; dirty; pass; tdd _(id: [rec-040c3fe0-5e55-4cc6-9299-f428da66edf9](.artifacts/records/project__check-run/rec-040c3fe0-5e55-4cc6-9299-f428da66edf9.md))_
- **verify-wave-executor**: rec-d8b61721-30cb-41fd-885d-85e673c7d6d7; dirty; pass; tdd _(id: [rec-68993ac9-1572-4d48-85b6-daf3d3211fb8](.artifacts/records/project__check-run/rec-68993ac9-1572-4d48-85b6-daf3d3211fb8.md))_
- **verify-wave-executor**: rec-61bdf854-1a06-491f-8af6-aeda309ec357; dirty; pass; tdd _(id: [rec-cde58bbe-0260-4526-b43a-d37ef52a05ca](.artifacts/records/project__check-run/rec-cde58bbe-0260-4526-b43a-d37ef52a05ca.md))_

## verify-wave-executor-execute

### Acceptance
- **verify-wave-executor-execute**: tdd; workflow-loop; python3 -m pytest tests/test_execute_wave_dispatch.py -q _(id: [rec-d8b61721-30cb-41fd-885d-85e673c7d6d7](.artifacts/records/project__acceptance/rec-d8b61721-30cb-41fd-885d-85e673c7d6d7.md))_

## verify-wave-executor-plan

### Acceptance
- **verify-wave-executor-plan**: tdd; workflow-loop; python3 -m pytest tests/test_plan_wave_rules.py -q _(id: [rec-61bdf854-1a06-491f-8af6-aeda309ec357](.artifacts/records/project__acceptance/rec-61bdf854-1a06-491f-8af6-aeda309ec357.md))_

## verify-web-dashboard

### Acceptance
- **verify-web-dashboard**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r1_loopback -q _(id: [rec-a0a942d1-9498-4c85-be22-ed91224e3c51](.artifacts/records/project__acceptance/rec-a0a942d1-9498-4c85-be22-ed91224e3c51.md))_

### Check
- **verify-web-dashboard**: rec-a0a942d1-9498-4c85-be22-ed91224e3c51; db84ee9ef00088870c2ac53a685f08dfbc15512a; pass; check _(id: [rec-41ab3a72-19f6-4cec-b5ef-fe2131eb90ce](.artifacts/records/project__check-run/rec-41ab3a72-19f6-4cec-b5ef-fe2131eb90ce.md))_

## verify-web-dashboard-api

### Acceptance
- **verify-web-dashboard-api**: R21; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py -q -k 'snapshot or token or approve or reject or sign or signer or accept_note or refused or backlog or stale' _(id: [rec-9a2e2a15-7ba6-4893-a2ae-9b818d4d101b](.artifacts/records/project__acceptance/rec-9a2e2a15-7ba6-4893-a2ae-9b818d4d101b.md))_

### Check
- **verify-web-dashboard-api**: rec-9a2e2a15-7ba6-4893-a2ae-9b818d4d101b; db84ee9ef00088870c2ac53a685f08dfbc15512a; pass; check _(id: [rec-eaba4d94-0aa4-48bc-8eb9-2640554ca545](.artifacts/records/project__check-run/rec-eaba4d94-0aa4-48bc-8eb9-2640554ca545.md))_

## verify-web-dashboard-build

### Acceptance
- **verify-web-dashboard-build**: R30; check; dashboard; npm --prefix dashboard/web/ui run build && uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r30_serves_build -q _(id: [rec-a7887505-0f2e-4300-8417-e14f31924643](.artifacts/records/project__acceptance/rec-a7887505-0f2e-4300-8417-e14f31924643.md))_

### Check
- **verify-web-dashboard-build**: rec-a7887505-0f2e-4300-8417-e14f31924643; db84ee9ef00088870c2ac53a685f08dfbc15512a; pass; check _(id: [rec-20077269-1d71-4f0a-9d52-fe8875d863b0](.artifacts/records/project__check-run/rec-20077269-1d71-4f0a-9d52-fe8875d863b0.md))_

## verify-web-dashboard-store

### Acceptance
- **verify-web-dashboard-store**: R2; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r2_same_store -q _(id: [rec-45a69ce8-9954-4521-a332-3b7b311543ee](.artifacts/records/project__acceptance/rec-45a69ce8-9954-4521-a332-3b7b311543ee.md))_

### Check
- **verify-web-dashboard-store**: rec-45a69ce8-9954-4521-a332-3b7b311543ee; db84ee9ef00088870c2ac53a685f08dfbc15512a; pass; check _(id: [rec-855aa55c-0c55-4113-a3b4-6da6ae6d1c21](.artifacts/records/project__check-run/rec-855aa55c-0c55-4113-a3b4-6da6ae6d1c21.md))_

## verify-web-write-body

### Acceptance
- **verify-web-write-body**: R1; tdd; dashboard; uv run --with textual --with pytest --with fastapi --with httpx python -m pytest tests/test_web_fastapi_writes.py::test_r1_backlog_dismiss -q _(id: [rec-b633ae9b-ad8f-4fa8-947f-e93af2b70315](.artifacts/records/project__acceptance/rec-b633ae9b-ad8f-4fa8-947f-e93af2b70315.md))_

### Check
- **verify-web-write-body**: rec-b633ae9b-ad8f-4fa8-947f-e93af2b70315; 29fec4bceaa72b8880b50dc8ceda560810cdfb09; pass; tdd _(id: [rec-00880b27-7a79-4325-80bb-de4bcac133fc](.artifacts/records/project__check-run/rec-00880b27-7a79-4325-80bb-de4bcac133fc.md))_
- **verify-web-write-body**: rec-b633ae9b-ad8f-4fa8-947f-e93af2b70315; dirty; fail; tdd _(id: [rec-aa27cfe4-91f6-4a9f-a659-5fbcf9dbeb4d](.artifacts/records/project__check-run/rec-aa27cfe4-91f6-4a9f-a659-5fbcf9dbeb4d.md))_

## verify-web-write-body-needs

### Acceptance
- **verify-web-write-body-needs**: R2; tdd; dashboard; uv run --with textual --with pytest --with fastapi --with httpx python -m pytest tests/test_web_fastapi_writes.py::test_r2_needs_clear -q _(id: [rec-307e2b98-1902-4327-845a-b03beb6b8b86](.artifacts/records/project__acceptance/rec-307e2b98-1902-4327-845a-b03beb6b8b86.md))_

### Check
- **verify-web-write-body-needs**: rec-307e2b98-1902-4327-845a-b03beb6b8b86; 29fec4bceaa72b8880b50dc8ceda560810cdfb09; pass; tdd _(id: [rec-87179b7d-fa4b-445e-ac04-097927e47781](.artifacts/records/project__check-run/rec-87179b7d-fa4b-445e-ac04-097927e47781.md))_
- **verify-web-write-body-needs**: rec-307e2b98-1902-4327-845a-b03beb6b8b86; dirty; fail; tdd _(id: [rec-d7ffc4ee-62f4-41a6-88f5-4c6d54ef8418](.artifacts/records/project__check-run/rec-d7ffc4ee-62f4-41a6-88f5-4c6d54ef8418.md))_

## verify-web-write-body-openapi

### Acceptance
- **verify-web-write-body-openapi**: R3; tdd; dashboard; uv run --with textual --with pytest --with fastapi --with httpx python -m pytest tests/test_web_fastapi_writes.py::test_r3_openapi -q _(id: [rec-8421d92b-4b6a-409d-bbdb-cb03d1d3a967](.artifacts/records/project__acceptance/rec-8421d92b-4b6a-409d-bbdb-cb03d1d3a967.md))_

### Check
- **verify-web-write-body-openapi**: rec-8421d92b-4b6a-409d-bbdb-cb03d1d3a967; 29fec4bceaa72b8880b50dc8ceda560810cdfb09; pass; tdd _(id: [rec-549ef08f-89b3-421f-9ad2-8981e6d4c1ed](.artifacts/records/project__check-run/rec-549ef08f-89b3-421f-9ad2-8981e6d4c1ed.md))_
- **verify-web-write-body-openapi**: rec-8421d92b-4b6a-409d-bbdb-cb03d1d3a967; dirty; fail; tdd _(id: [rec-cc6e02f8-c3ae-4f98-a745-b40135a8c87a](.artifacts/records/project__check-run/rec-cc6e02f8-c3ae-4f98-a745-b40135a8c87a.md))_

## watch-command

### Acceptance
- **watch-command**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q _(id: [rec-ec792cef-650b-492a-ac2d-eed325546c19](.artifacts/records/project__acceptance/rec-ec792cef-650b-492a-ac2d-eed325546c19.md))_

### Check
- **watch-command**: rec-ec792cef-650b-492a-ac2d-eed325546c19; 846188f; pass; tdd _(id: [rec-f370db55-4f74-4981-bfae-1d39e925d6ff](.artifacts/records/project__check-run/rec-f370db55-4f74-4981-bfae-1d39e925d6ff.md))_

## web-dashboard-review

### Check
- **web-dashboard-review**: web-dashboard-review; db84ee9ef00088870c2ac53a685f08dfbc15512a; pass; review _(id: [rec-21c8124b-5084-4114-98d6-28382bef610e](.artifacts/records/project__check-run/rec-21c8124b-5084-4114-98d6-28382bef610e.md))_

## web-launcher

### Acceptance
- **web-launcher**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r1_loopback -q _(id: [rec-7a86817f-5f89-4984-895a-d94f86fa0cff](.artifacts/records/project__acceptance/rec-7a86817f-5f89-4984-895a-d94f86fa0cff.md))_

### Check
- **web-launcher**: rec-7a86817f-5f89-4984-895a-d94f86fa0cff; a5bb973439b75ea27af3feb25e5885781618108b; pass; tdd _(id: [rec-63fa6553-d1c1-4e28-a42d-71af67297629](.artifacts/records/project__check-run/rec-63fa6553-d1c1-4e28-a42d-71af67297629.md))_
- **web-launcher**: rec-7a86817f-5f89-4984-895a-d94f86fa0cff; dirty; fail; tdd _(id: [rec-d324acbc-a03e-4ab0-a084-d6c37bfd3ac2](.artifacts/records/project__check-run/rec-d324acbc-a03e-4ab0-a084-d6c37bfd3ac2.md))_
- **web-launcher**: rec-7a86817f-5f89-4984-895a-d94f86fa0cff; dirty; fail; tdd _(id: [rec-d9312cd8-147d-4c79-98ea-61879ed1ae5c](.artifacts/records/project__check-run/rec-d9312cd8-147d-4c79-98ea-61879ed1ae5c.md))_

## web-launcher-r2

### Acceptance
- **web-launcher-r2**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r2_same_store -q _(id: [rec-c07ba87d-fac0-453e-9d85-5633e2d11198](.artifacts/records/project__acceptance/rec-c07ba87d-fac0-453e-9d85-5633e2d11198.md))_

### Check
- **web-launcher-r2**: rec-c07ba87d-fac0-453e-9d85-5633e2d11198; a5bb973439b75ea27af3feb25e5885781618108b; pass; tdd _(id: [rec-2a42741b-8f21-41ee-a12a-c0970ac0c2e9](.artifacts/records/project__check-run/rec-2a42741b-8f21-41ee-a12a-c0970ac0c2e9.md))_
- **web-launcher-r2**: rec-c07ba87d-fac0-453e-9d85-5633e2d11198; dirty; fail; tdd _(id: [rec-34615448-e651-4ea1-a407-a36fdf7e5a51](.artifacts/records/project__check-run/rec-34615448-e651-4ea1-a407-a36fdf7e5a51.md))_
- **web-launcher-r2**: rec-c07ba87d-fac0-453e-9d85-5633e2d11198; dirty; fail; tdd _(id: [rec-9d9503cb-dae7-4cbc-9349-c9ac5b5efae6](.artifacts/records/project__check-run/rec-9d9503cb-dae7-4cbc-9349-c9ac5b5efae6.md))_

## web-launcher-r30

### Acceptance
- **web-launcher-r30**: R30; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r30_serves_build -q _(id: [rec-4330f7e7-99ff-4cc6-be02-27c78971fba1](.artifacts/records/project__acceptance/rec-4330f7e7-99ff-4cc6-be02-27c78971fba1.md))_

### Check
- **web-launcher-r30**: rec-4330f7e7-99ff-4cc6-be02-27c78971fba1; dirty; fail; tdd _(id: [rec-aa3a32d6-53bb-4c3f-b1c7-ce3293d77840](.artifacts/records/project__check-run/rec-aa3a32d6-53bb-4c3f-b1c7-ce3293d77840.md))_
- **web-launcher-r30**: rec-4330f7e7-99ff-4cc6-be02-27c78971fba1; a5bb973439b75ea27af3feb25e5885781618108b; pass; tdd _(id: [rec-b568f9e3-06c7-4276-8d72-21d36bd2c9fd](.artifacts/records/project__check-run/rec-b568f9e3-06c7-4276-8d72-21d36bd2c9fd.md))_
- **web-launcher-r30**: rec-4330f7e7-99ff-4cc6-be02-27c78971fba1; dirty; fail; tdd _(id: [rec-b6cd8012-a7ae-42ac-a3cb-aabff33a7847](.artifacts/records/project__check-run/rec-b6cd8012-a7ae-42ac-a3cb-aabff33a7847.md))_

## web-read-api

### Acceptance
- **web-read-api**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r3_snapshot -q _(id: [rec-39750da5-4bed-4a37-b46b-012d58a8be55](.artifacts/records/project__acceptance/rec-39750da5-4bed-4a37-b46b-012d58a8be55.md))_

### Check
- **web-read-api**: rec-39750da5-4bed-4a37-b46b-012d58a8be55; dirty; fail; tdd _(id: [rec-3d32e09d-f05b-4f5f-aedf-749d9ae1be97](.artifacts/records/project__check-run/rec-3d32e09d-f05b-4f5f-aedf-749d9ae1be97.md))_
- **web-read-api**: rec-39750da5-4bed-4a37-b46b-012d58a8be55; dirty; fail; tdd _(id: [rec-4688c1f4-7368-472b-b561-76f2f3703cb6](.artifacts/records/project__check-run/rec-4688c1f4-7368-472b-b561-76f2f3703cb6.md))_
- **web-read-api**: rec-39750da5-4bed-4a37-b46b-012d58a8be55; 16c78c65bb32bc35e06543a002726cea3b7bcaa3; pass; tdd _(id: [rec-f31243e8-9d14-4275-82a9-133b8ca5c67e](.artifacts/records/project__check-run/rec-f31243e8-9d14-4275-82a9-133b8ca5c67e.md))_

## web-read-api-r4

### Acceptance
- **web-read-api-r4**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r4_token -q _(id: [rec-ceb6e37a-647b-44c6-a74b-a4662a589b8d](.artifacts/records/project__acceptance/rec-ceb6e37a-647b-44c6-a74b-a4662a589b8d.md))_

### Check
- **web-read-api-r4**: rec-ceb6e37a-647b-44c6-a74b-a4662a589b8d; 16c78c65bb32bc35e06543a002726cea3b7bcaa3; pass; tdd _(id: [rec-2f486e0e-8c7e-4632-b41a-de9d205379d8](.artifacts/records/project__check-run/rec-2f486e0e-8c7e-4632-b41a-de9d205379d8.md))_
- **web-read-api-r4**: rec-ceb6e37a-647b-44c6-a74b-a4662a589b8d; dirty; fail; tdd _(id: [rec-90528fb4-566f-4579-8b82-1354e15c907d](.artifacts/records/project__check-run/rec-90528fb4-566f-4579-8b82-1354e15c907d.md))_
- **web-read-api-r4**: rec-ceb6e37a-647b-44c6-a74b-a4662a589b8d; dirty; fail; tdd _(id: [rec-dc9980d9-b3c3-4c87-9577-3e6533af3677](.artifacts/records/project__check-run/rec-dc9980d9-b3c3-4c87-9577-3e6533af3677.md))_

## web-ui-actions

### Acceptance
- **web-ui-actions**: R20; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/actions.test.ts -t R20 _(id: [rec-87efd039-2c55-4091-842b-2f1f8fdfa4ac](.artifacts/records/project__acceptance/rec-87efd039-2c55-4091-842b-2f1f8fdfa4ac.md))_

### Check
- **web-ui-actions**: rec-87efd039-2c55-4091-842b-2f1f8fdfa4ac; db84ee9ef00088870c2ac53a685f08dfbc15512a; pass; check _(id: [rec-4bfcd762-e256-4fde-8713-6a813ef61e1f](.artifacts/records/project__check-run/rec-4bfcd762-e256-4fde-8713-6a813ef61e1f.md))_

## web-ui-actions-r27

### Acceptance
- **web-ui-actions-r27**: R27; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/actions.test.ts -t R27 _(id: [rec-4d957b43-25b5-4fdc-be50-2200606af70a](.artifacts/records/project__acceptance/rec-4d957b43-25b5-4fdc-be50-2200606af70a.md))_

### Check
- **web-ui-actions-r27**: rec-4d957b43-25b5-4fdc-be50-2200606af70a; db84ee9ef00088870c2ac53a685f08dfbc15512a; pass; check _(id: [rec-9abf0a29-ea7f-4d4e-8318-a440fa7a131f](.artifacts/records/project__check-run/rec-9abf0a29-ea7f-4d4e-8318-a440fa7a131f.md))_

## web-ui-detail

### Acceptance
- **web-ui-detail**: R14; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R14 _(id: [rec-0d6a38bb-bc45-42a1-b025-3870a65c4fef](.artifacts/records/project__acceptance/rec-0d6a38bb-bc45-42a1-b025-3870a65c4fef.md))_

### Check
- **web-ui-detail**: rec-0d6a38bb-bc45-42a1-b025-3870a65c4fef; 1290682a207e913a96aad7b31406f6fe8fa3a243; pass; check _(id: [rec-11e54937-c8c8-42f3-8ebc-db432022199d](.artifacts/records/project__check-run/rec-11e54937-c8c8-42f3-8ebc-db432022199d.md))_

## web-ui-detail-r15

### Acceptance
- **web-ui-detail-r15**: R15; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R15 _(id: [rec-4ed43d96-3a8c-4458-864f-aa756818ca4b](.artifacts/records/project__acceptance/rec-4ed43d96-3a8c-4458-864f-aa756818ca4b.md))_

### Check
- **web-ui-detail-r15**: rec-4ed43d96-3a8c-4458-864f-aa756818ca4b; 1290682a207e913a96aad7b31406f6fe8fa3a243; pass; check _(id: [rec-3912dc24-c0ed-4a10-8c51-04221bc732c4](.artifacts/records/project__check-run/rec-3912dc24-c0ed-4a10-8c51-04221bc732c4.md))_

## web-ui-detail-r16

### Acceptance
- **web-ui-detail-r16**: R16; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R16 _(id: [rec-90f3f583-7e47-4375-a5ad-d13cc55eb3f9](.artifacts/records/project__acceptance/rec-90f3f583-7e47-4375-a5ad-d13cc55eb3f9.md))_

### Check
- **web-ui-detail-r16**: rec-90f3f583-7e47-4375-a5ad-d13cc55eb3f9; 1290682a207e913a96aad7b31406f6fe8fa3a243; pass; check _(id: [rec-5c39b8f4-0655-4824-ad5e-98207fb50310](.artifacts/records/project__check-run/rec-5c39b8f4-0655-4824-ad5e-98207fb50310.md))_

## web-ui-detail-r17

### Acceptance
- **web-ui-detail-r17**: R17; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R17 _(id: [rec-e12cb025-c028-4658-a406-c31efdc3dae8](.artifacts/records/project__acceptance/rec-e12cb025-c028-4658-a406-c31efdc3dae8.md))_

### Check
- **web-ui-detail-r17**: rec-e12cb025-c028-4658-a406-c31efdc3dae8; 1290682a207e913a96aad7b31406f6fe8fa3a243; pass; check _(id: [rec-872e08f3-f09f-442d-b239-aa9e1027cadf](.artifacts/records/project__check-run/rec-872e08f3-f09f-442d-b239-aa9e1027cadf.md))_

## web-ui-detail-r18

### Acceptance
- **web-ui-detail-r18**: R18; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R18 _(id: [rec-a40c0868-5897-4f8e-b2ac-7ef034005115](.artifacts/records/project__acceptance/rec-a40c0868-5897-4f8e-b2ac-7ef034005115.md))_

### Check
- **web-ui-detail-r18**: rec-a40c0868-5897-4f8e-b2ac-7ef034005115; 1290682a207e913a96aad7b31406f6fe8fa3a243; pass; check _(id: [rec-24f8ecd8-2613-438f-9051-e94694b9ab4e](.artifacts/records/project__check-run/rec-24f8ecd8-2613-438f-9051-e94694b9ab4e.md))_

## web-ui-detail-r19

### Acceptance
- **web-ui-detail-r19**: R19; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R19 _(id: [rec-3f65034a-4cc6-4d11-9a4b-dd1e53ebe264](.artifacts/records/project__acceptance/rec-3f65034a-4cc6-4d11-9a4b-dd1e53ebe264.md))_

### Check
- **web-ui-detail-r19**: rec-3f65034a-4cc6-4d11-9a4b-dd1e53ebe264; 1290682a207e913a96aad7b31406f6fe8fa3a243; pass; check _(id: [rec-185a300c-550e-4cf5-aca3-e1c38ac26c8c](.artifacts/records/project__check-run/rec-185a300c-550e-4cf5-aca3-e1c38ac26c8c.md))_

## web-ui-main

### Acceptance
- **web-ui-main**: R5; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R5 _(id: [rec-e7d85f56-4f37-4f13-9e82-edf9ad112beb](.artifacts/records/project__acceptance/rec-e7d85f56-4f37-4f13-9e82-edf9ad112beb.md))_

### Check
- **web-ui-main**: rec-e7d85f56-4f37-4f13-9e82-edf9ad112beb; 4dfbd2b07cc25406bee4e3bae5161f5dd4790522; pass; check _(id: [rec-331f7817-a76c-443e-8b50-e6f322f7c548](.artifacts/records/project__check-run/rec-331f7817-a76c-443e-8b50-e6f322f7c548.md))_

## web-ui-main-r10

### Acceptance
- **web-ui-main-r10**: R10; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R10 _(id: [rec-e0feebb8-d9a5-4c8b-8a50-6cafa4a0eea3](.artifacts/records/project__acceptance/rec-e0feebb8-d9a5-4c8b-8a50-6cafa4a0eea3.md))_

### Check
- **web-ui-main-r10**: rec-e0feebb8-d9a5-4c8b-8a50-6cafa4a0eea3; 4dfbd2b07cc25406bee4e3bae5161f5dd4790522; pass; check _(id: [rec-bf78b6df-1cbc-4798-8f1e-6b7bd0f11c7c](.artifacts/records/project__check-run/rec-bf78b6df-1cbc-4798-8f1e-6b7bd0f11c7c.md))_

## web-ui-main-r32

### Acceptance
- **web-ui-main-r32**: R32; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R32 _(id: [rec-eb1dc00c-fb0b-4407-ab50-7e4a12e2ece9](.artifacts/records/project__acceptance/rec-eb1dc00c-fb0b-4407-ab50-7e4a12e2ece9.md))_

### Check
- **web-ui-main-r32**: rec-eb1dc00c-fb0b-4407-ab50-7e4a12e2ece9; 4dfbd2b07cc25406bee4e3bae5161f5dd4790522; pass; check _(id: [rec-abcda6a9-4a07-42ca-a811-39a180804064](.artifacts/records/project__check-run/rec-abcda6a9-4a07-42ca-a811-39a180804064.md))_

## web-ui-main-r33

### Acceptance
- **web-ui-main-r33**: R33; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R33 _(id: [rec-6fabe656-f50c-40cc-8910-d6cbb842aa98](.artifacts/records/project__acceptance/rec-6fabe656-f50c-40cc-8910-d6cbb842aa98.md))_

### Check
- **web-ui-main-r33**: rec-6fabe656-f50c-40cc-8910-d6cbb842aa98; 4dfbd2b07cc25406bee4e3bae5161f5dd4790522; pass; check _(id: [rec-ba987433-4b8f-431a-9172-bf6e5bad9c91](.artifacts/records/project__check-run/rec-ba987433-4b8f-431a-9172-bf6e5bad9c91.md))_

## web-ui-main-r6

### Acceptance
- **web-ui-main-r6**: R6; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R6 _(id: [rec-f36e227a-f954-4654-a364-e7472ed899ca](.artifacts/records/project__acceptance/rec-f36e227a-f954-4654-a364-e7472ed899ca.md))_

### Check
- **web-ui-main-r6**: rec-f36e227a-f954-4654-a364-e7472ed899ca; 4dfbd2b07cc25406bee4e3bae5161f5dd4790522; pass; check _(id: [rec-c727a823-d19d-4057-aaba-936ec1b3a456](.artifacts/records/project__check-run/rec-c727a823-d19d-4057-aaba-936ec1b3a456.md))_

## web-ui-main-r7

### Acceptance
- **web-ui-main-r7**: R7; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R7 _(id: [rec-7b6d6bac-572f-42c3-8fe7-ec6de93c3559](.artifacts/records/project__acceptance/rec-7b6d6bac-572f-42c3-8fe7-ec6de93c3559.md))_

### Check
- **web-ui-main-r7**: rec-7b6d6bac-572f-42c3-8fe7-ec6de93c3559; 4dfbd2b07cc25406bee4e3bae5161f5dd4790522; pass; check _(id: [rec-ea1fee30-851b-4357-a303-33e342ef89aa](.artifacts/records/project__check-run/rec-ea1fee30-851b-4357-a303-33e342ef89aa.md))_

## web-ui-main-r8

### Acceptance
- **web-ui-main-r8**: R8; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R8 _(id: [rec-e8680ef6-df90-4957-be9d-85133eaf99b2](.artifacts/records/project__acceptance/rec-e8680ef6-df90-4957-be9d-85133eaf99b2.md))_

### Check
- **web-ui-main-r8**: rec-e8680ef6-df90-4957-be9d-85133eaf99b2; 4dfbd2b07cc25406bee4e3bae5161f5dd4790522; pass; check _(id: [rec-d0969602-30a1-4588-a662-455004d36cf3](.artifacts/records/project__check-run/rec-d0969602-30a1-4588-a662-455004d36cf3.md))_

## web-ui-main-r9

### Acceptance
- **web-ui-main-r9**: R9; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R9 _(id: [rec-89de12fa-d78d-497a-a4b8-b1fafc7442f9](.artifacts/records/project__acceptance/rec-89de12fa-d78d-497a-a4b8-b1fafc7442f9.md))_

### Check
- **web-ui-main-r9**: rec-89de12fa-d78d-497a-a4b8-b1fafc7442f9; 4dfbd2b07cc25406bee4e3bae5161f5dd4790522; pass; check _(id: [rec-e5a5b88b-dd0c-4f62-a7de-6a8f371fecae](.artifacts/records/project__check-run/rec-e5a5b88b-dd0c-4f62-a7de-6a8f371fecae.md))_

## web-ui-scaffold

### Acceptance
- **web-ui-scaffold**: R31; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/scaffold.test.ts -t R31 _(id: [rec-987406c8-3ff3-475e-aea1-1a74584e5693](.artifacts/records/project__acceptance/rec-987406c8-3ff3-475e-aea1-1a74584e5693.md))_

### Check
- **web-ui-scaffold**: rec-987406c8-3ff3-475e-aea1-1a74584e5693; 16c78c65bb32bc35e06543a002726cea3b7bcaa3; pass; check _(id: [rec-dea484af-b47c-4fd0-a657-2a60b1b8cb99](.artifacts/records/project__check-run/rec-dea484af-b47c-4fd0-a657-2a60b1b8cb99.md))_

## web-ui-scaffold-r35

### Acceptance
- **web-ui-scaffold-r35**: R35; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/scaffold.test.ts -t R35 _(id: [rec-15b25cbd-fd4c-419a-bb7f-808bee8f71bd](.artifacts/records/project__acceptance/rec-15b25cbd-fd4c-419a-bb7f-808bee8f71bd.md))_

### Check
- **web-ui-scaffold-r35**: rec-15b25cbd-fd4c-419a-bb7f-808bee8f71bd; 16c78c65bb32bc35e06543a002726cea3b7bcaa3; pass; check _(id: [rec-1d7479c4-5350-4090-a8a8-f6b3d3df5a14](.artifacts/records/project__check-run/rec-1d7479c4-5350-4090-a8a8-f6b3d3df5a14.md))_

## web-ui-scaffold-r36

### Acceptance
- **web-ui-scaffold-r36**: R36; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/scaffold.test.ts -t R36 _(id: [rec-2b879879-e526-4499-a9b6-a47e8b79653c](.artifacts/records/project__acceptance/rec-2b879879-e526-4499-a9b6-a47e8b79653c.md))_

### Check
- **web-ui-scaffold-r36**: rec-2b879879-e526-4499-a9b6-a47e8b79653c; 16c78c65bb32bc35e06543a002726cea3b7bcaa3; pass; check _(id: [rec-c208a35a-52b3-42b5-8865-60a9c6f05bfa](.artifacts/records/project__check-run/rec-c208a35a-52b3-42b5-8865-60a9c6f05bfa.md))_

## web-ui-side

### Acceptance
- **web-ui-side**: R11; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/side.test.ts -t R11 _(id: [rec-c86fdf26-17c0-4a94-ba8f-38366fc6c692](.artifacts/records/project__acceptance/rec-c86fdf26-17c0-4a94-ba8f-38366fc6c692.md))_

### Check
- **web-ui-side**: rec-c86fdf26-17c0-4a94-ba8f-38366fc6c692; 4f4573b597aa9fc16d0563e4e39db05c63ec374c; pass; check _(id: [rec-744383b5-92f9-40b6-ab63-b2053e0b988f](.artifacts/records/project__check-run/rec-744383b5-92f9-40b6-ab63-b2053e0b988f.md))_

## web-ui-side-r12

### Acceptance
- **web-ui-side-r12**: R12; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/side.test.ts -t R12 _(id: [rec-77f4d05e-75d4-49a9-9ee0-f9a28ee00c6b](.artifacts/records/project__acceptance/rec-77f4d05e-75d4-49a9-9ee0-f9a28ee00c6b.md))_

### Check
- **web-ui-side-r12**: rec-77f4d05e-75d4-49a9-9ee0-f9a28ee00c6b; 4f4573b597aa9fc16d0563e4e39db05c63ec374c; pass; check _(id: [rec-0dbb1afd-6600-4873-9725-432ba7cefe74](.artifacts/records/project__check-run/rec-0dbb1afd-6600-4873-9725-432ba7cefe74.md))_

## web-ui-side-r13

### Acceptance
- **web-ui-side-r13**: R13; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/side.test.ts -t R13 _(id: [rec-9d2656c6-797f-4f4a-b134-7f375d396110](.artifacts/records/project__acceptance/rec-9d2656c6-797f-4f4a-b134-7f375d396110.md))_

### Check
- **web-ui-side-r13**: rec-9d2656c6-797f-4f4a-b134-7f375d396110; 4f4573b597aa9fc16d0563e4e39db05c63ec374c; pass; check _(id: [rec-2a405833-3f83-4ac8-92e4-ccd6165847d0](.artifacts/records/project__check-run/rec-2a405833-3f83-4ac8-92e4-ccd6165847d0.md))_

## web-write-annotations

### Acceptance
- **web-write-annotations**: R1; tdd; dashboard; uv run --with textual --with pytest --with fastapi --with httpx python -m pytest tests/test_web_fastapi_writes.py::test_r1_backlog_dismiss -q _(id: [rec-5678aa33-8261-4197-814e-c3045faf122d](.artifacts/records/project__acceptance/rec-5678aa33-8261-4197-814e-c3045faf122d.md))_

### Check
- **web-write-annotations**: rec-5678aa33-8261-4197-814e-c3045faf122d; 29fec4bceaa72b8880b50dc8ceda560810cdfb09; pass; tdd _(id: [rec-a33baee6-16e9-4a9a-8393-8d7bf2c95585](.artifacts/records/project__check-run/rec-a33baee6-16e9-4a9a-8393-8d7bf2c95585.md))_
- **web-write-annotations**: rec-5678aa33-8261-4197-814e-c3045faf122d; dirty; fail; tdd _(id: [rec-a5039054-e72c-4030-8c1a-42cb42ad742f](.artifacts/records/project__check-run/rec-a5039054-e72c-4030-8c1a-42cb42ad742f.md))_
- **web-write-annotations**: rec-5678aa33-8261-4197-814e-c3045faf122d; dirty; fail; tdd _(id: [rec-deab58bb-0a02-40ca-868e-de425b27531e](.artifacts/records/project__check-run/rec-deab58bb-0a02-40ca-868e-de425b27531e.md))_

### Observation
- **web-write-annotations**: Before the edit, backlog and needs posts returned 422 for a missing request query parameter and openapi returned 500. After the edit the three tests passed.; dashboard _(id: [rec-5b5b5aa3-42a4-4fc4-b8cd-c102bef4f137](.artifacts/records/project__investigation-observation/rec-5b5b5aa3-42a4-4fc4-b8cd-c102bef4f137.md))_

### Finding
- **web-write-annotations**: Postponed annotations made FastAPI require a query parameter named request, so confirm writes returned 422.; Assertion failures on test_r1_backlog_dismiss and test_r2_needs_clear before the edit, and passes at 29fec4bc after deleting from __future__ import annotations.; POST /api/backlog or POST /api/needs returns 422 for a missing request query parameter again on the FastAPI app.; none _(id: [rec-42013bd8-7f75-4189-bf0e-419834013782](.artifacts/records/project__finding/rec-42013bd8-7f75-4189-bf0e-419834013782.md))_

## web-write-annotations-needs

### Acceptance
- **web-write-annotations-needs**: R2; tdd; dashboard; uv run --with textual --with pytest --with fastapi --with httpx python -m pytest tests/test_web_fastapi_writes.py::test_r2_needs_clear -q _(id: [rec-9838800f-6424-4ad6-a78a-dc34180d8345](.artifacts/records/project__acceptance/rec-9838800f-6424-4ad6-a78a-dc34180d8345.md))_

### Check
- **web-write-annotations-needs**: rec-9838800f-6424-4ad6-a78a-dc34180d8345; dirty; fail; tdd _(id: [rec-0b518d65-b4c2-4360-a1c3-bfcb93d4ccf6](.artifacts/records/project__check-run/rec-0b518d65-b4c2-4360-a1c3-bfcb93d4ccf6.md))_
- **web-write-annotations-needs**: rec-9838800f-6424-4ad6-a78a-dc34180d8345; 29fec4bceaa72b8880b50dc8ceda560810cdfb09; pass; tdd _(id: [rec-2f5f36b7-f8ca-4d0b-a849-5ba379c31b15](.artifacts/records/project__check-run/rec-2f5f36b7-f8ca-4d0b-a849-5ba379c31b15.md))_
- **web-write-annotations-needs**: rec-9838800f-6424-4ad6-a78a-dc34180d8345; dirty; fail; tdd _(id: [rec-90b704cf-1178-47ba-94b4-79a7f4426f3f](.artifacts/records/project__check-run/rec-90b704cf-1178-47ba-94b4-79a7f4426f3f.md))_

## web-write-annotations-openapi

### Acceptance
- **web-write-annotations-openapi**: R3; tdd; dashboard; uv run --with textual --with pytest --with fastapi --with httpx python -m pytest tests/test_web_fastapi_writes.py::test_r3_openapi -q _(id: [rec-6667c3cf-fe62-4bd5-8087-7e49ff965b17](.artifacts/records/project__acceptance/rec-6667c3cf-fe62-4bd5-8087-7e49ff965b17.md))_

### Check
- **web-write-annotations-openapi**: rec-6667c3cf-fe62-4bd5-8087-7e49ff965b17; dirty; fail; tdd _(id: [rec-67a58b69-b669-4333-8c04-abd2c30cba11](.artifacts/records/project__check-run/rec-67a58b69-b669-4333-8c04-abd2c30cba11.md))_
- **web-write-annotations-openapi**: rec-6667c3cf-fe62-4bd5-8087-7e49ff965b17; 29fec4bceaa72b8880b50dc8ceda560810cdfb09; pass; tdd _(id: [rec-acf86e2a-b549-4189-b8f7-d28e78f3fa5b](.artifacts/records/project__check-run/rec-acf86e2a-b549-4189-b8f7-d28e78f3fa5b.md))_
- **web-write-annotations-openapi**: rec-6667c3cf-fe62-4bd5-8087-7e49ff965b17; dirty; fail; tdd _(id: [rec-e056f340-6754-40ba-ad8d-0753864175ac](.artifacts/records/project__check-run/rec-e056f340-6754-40ba-ad8d-0753864175ac.md))_

## web-write-api

### Acceptance
- **web-write-api**: R21; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r21_approve -q _(id: [rec-9b753d3c-769f-458b-a279-f9821408f1dd](.artifacts/records/project__acceptance/rec-9b753d3c-769f-458b-a279-f9821408f1dd.md))_

### Check
- **web-write-api**: rec-9b753d3c-769f-458b-a279-f9821408f1dd; dirty; fail; tdd _(id: [rec-a2643c5d-d9e0-429d-9c82-0670c9af9b60](.artifacts/records/project__check-run/rec-a2643c5d-d9e0-429d-9c82-0670c9af9b60.md))_
- **web-write-api**: rec-9b753d3c-769f-458b-a279-f9821408f1dd; dirty; fail; tdd _(id: [rec-a57266f0-718f-429d-b04c-cca183cabc1a](.artifacts/records/project__check-run/rec-a57266f0-718f-429d-b04c-cca183cabc1a.md))_
- **web-write-api**: rec-9b753d3c-769f-458b-a279-f9821408f1dd; 6cacba9e9fb325600fd0805d74b574e3323eec73; pass; tdd _(id: [rec-f9d8dff9-3ac9-4e0e-82d8-53089f45f8df](.artifacts/records/project__check-run/rec-f9d8dff9-3ac9-4e0e-82d8-53089f45f8df.md))_

## web-write-api-r22

### Acceptance
- **web-write-api-r22**: R22; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r22_reject_note -q _(id: [rec-d32c9db3-448d-4fca-a0aa-d8b10bb49c8a](.artifacts/records/project__acceptance/rec-d32c9db3-448d-4fca-a0aa-d8b10bb49c8a.md))_

### Check
- **web-write-api-r22**: rec-d32c9db3-448d-4fca-a0aa-d8b10bb49c8a; dirty; fail; tdd _(id: [rec-35269b3c-d00e-46aa-befb-a18403212c67](.artifacts/records/project__check-run/rec-35269b3c-d00e-46aa-befb-a18403212c67.md))_
- **web-write-api-r22**: rec-d32c9db3-448d-4fca-a0aa-d8b10bb49c8a; 6cacba9e9fb325600fd0805d74b574e3323eec73; pass; tdd _(id: [rec-a893a7fc-2002-43b5-b0e1-56f9f9bf001f](.artifacts/records/project__check-run/rec-a893a7fc-2002-43b5-b0e1-56f9f9bf001f.md))_
- **web-write-api-r22**: rec-d32c9db3-448d-4fca-a0aa-d8b10bb49c8a; dirty; fail; tdd _(id: [rec-cb10ecaa-3ad0-4f65-bbed-115695f2befa](.artifacts/records/project__check-run/rec-cb10ecaa-3ad0-4f65-bbed-115695f2befa.md))_

## web-write-api-r23

### Acceptance
- **web-write-api-r23**: R23; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r23_sign -q _(id: [rec-bc24f370-7c8a-44f7-9f4f-783754b2d3a5](.artifacts/records/project__acceptance/rec-bc24f370-7c8a-44f7-9f4f-783754b2d3a5.md))_

### Check
- **web-write-api-r23**: rec-bc24f370-7c8a-44f7-9f4f-783754b2d3a5; dirty; fail; tdd _(id: [rec-0596f91a-da9e-491d-8873-d963034729cb](.artifacts/records/project__check-run/rec-0596f91a-da9e-491d-8873-d963034729cb.md))_
- **web-write-api-r23**: rec-bc24f370-7c8a-44f7-9f4f-783754b2d3a5; dirty; fail; tdd _(id: [rec-5020dbab-8704-4fd4-acff-32524235bfb7](.artifacts/records/project__check-run/rec-5020dbab-8704-4fd4-acff-32524235bfb7.md))_
- **web-write-api-r23**: rec-bc24f370-7c8a-44f7-9f4f-783754b2d3a5; 6cacba9e9fb325600fd0805d74b574e3323eec73; pass; tdd _(id: [rec-9f0f85cd-8174-487f-a5f3-35e213774678](.artifacts/records/project__check-run/rec-9f0f85cd-8174-487f-a5f3-35e213774678.md))_

## web-write-api-r24

### Acceptance
- **web-write-api-r24**: R24; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r24_signer -q _(id: [rec-be370437-14d1-4c3e-8316-a940155e8cec](.artifacts/records/project__acceptance/rec-be370437-14d1-4c3e-8316-a940155e8cec.md))_

### Check
- **web-write-api-r24**: rec-be370437-14d1-4c3e-8316-a940155e8cec; dirty; fail; tdd _(id: [rec-1e987af2-bb5a-40e6-8d86-b8a84d241dff](.artifacts/records/project__check-run/rec-1e987af2-bb5a-40e6-8d86-b8a84d241dff.md))_
- **web-write-api-r24**: rec-be370437-14d1-4c3e-8316-a940155e8cec; dirty; fail; tdd _(id: [rec-1fdc0598-5c95-450a-8dbf-a1f5e2c7d2dc](.artifacts/records/project__check-run/rec-1fdc0598-5c95-450a-8dbf-a1f5e2c7d2dc.md))_
- **web-write-api-r24**: rec-be370437-14d1-4c3e-8316-a940155e8cec; 6cacba9e9fb325600fd0805d74b574e3323eec73; pass; tdd _(id: [rec-83fbf9f4-59f3-4a69-92e3-283b231622a6](.artifacts/records/project__check-run/rec-83fbf9f4-59f3-4a69-92e3-283b231622a6.md))_

## web-write-api-r25

### Acceptance
- **web-write-api-r25**: R25; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r25_accept_note -q _(id: [rec-78629b0a-b92e-40cc-8c10-31c3a02dd766](.artifacts/records/project__acceptance/rec-78629b0a-b92e-40cc-8c10-31c3a02dd766.md))_

### Check
- **web-write-api-r25**: rec-78629b0a-b92e-40cc-8c10-31c3a02dd766; 6cacba9e9fb325600fd0805d74b574e3323eec73; pass; tdd _(id: [rec-1c35d160-9b35-44be-b207-671b51728175](.artifacts/records/project__check-run/rec-1c35d160-9b35-44be-b207-671b51728175.md))_
- **web-write-api-r25**: rec-78629b0a-b92e-40cc-8c10-31c3a02dd766; dirty; fail; tdd _(id: [rec-2fcea7dc-b97a-4517-b22c-06ec755f5751](.artifacts/records/project__check-run/rec-2fcea7dc-b97a-4517-b22c-06ec755f5751.md))_
- **web-write-api-r25**: rec-78629b0a-b92e-40cc-8c10-31c3a02dd766; dirty; fail; tdd _(id: [rec-80e7669a-af79-4642-b01d-e47fcfc99bdf](.artifacts/records/project__check-run/rec-80e7669a-af79-4642-b01d-e47fcfc99bdf.md))_

## web-write-api-r26

### Acceptance
- **web-write-api-r26**: R26; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r26_refused -q _(id: [rec-171cb043-59ae-41a2-bd02-431687ff5663](.artifacts/records/project__acceptance/rec-171cb043-59ae-41a2-bd02-431687ff5663.md))_

### Check
- **web-write-api-r26**: rec-171cb043-59ae-41a2-bd02-431687ff5663; 6cacba9e9fb325600fd0805d74b574e3323eec73; pass; tdd _(id: [rec-2002c809-9bf4-4144-80ba-07db664513bd](.artifacts/records/project__check-run/rec-2002c809-9bf4-4144-80ba-07db664513bd.md))_
- **web-write-api-r26**: rec-171cb043-59ae-41a2-bd02-431687ff5663; dirty; fail; tdd _(id: [rec-2d8b8380-f1bd-4c0a-8e9b-fdc1f2ceb818](.artifacts/records/project__check-run/rec-2d8b8380-f1bd-4c0a-8e9b-fdc1f2ceb818.md))_
- **web-write-api-r26**: rec-171cb043-59ae-41a2-bd02-431687ff5663; dirty; fail; tdd _(id: [rec-ea01b841-7a8f-4587-bfac-d3f9783414db](.artifacts/records/project__check-run/rec-ea01b841-7a8f-4587-bfac-d3f9783414db.md))_

## web-write-api-r28

### Acceptance
- **web-write-api-r28**: R28; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r28_backlog_dismiss -q _(id: [rec-a9fc00b5-7ae8-4396-9013-c753ce9da519](.artifacts/records/project__acceptance/rec-a9fc00b5-7ae8-4396-9013-c753ce9da519.md))_

### Check
- **web-write-api-r28**: rec-a9fc00b5-7ae8-4396-9013-c753ce9da519; 6cacba9e9fb325600fd0805d74b574e3323eec73; pass; tdd _(id: [rec-03bb3279-6d04-4c10-bdec-14a52c6876cf](.artifacts/records/project__check-run/rec-03bb3279-6d04-4c10-bdec-14a52c6876cf.md))_
- **web-write-api-r28**: rec-a9fc00b5-7ae8-4396-9013-c753ce9da519; dirty; fail; tdd _(id: [rec-76ff0313-0868-4c0e-9e80-eb44ec18b89f](.artifacts/records/project__check-run/rec-76ff0313-0868-4c0e-9e80-eb44ec18b89f.md))_
- **web-write-api-r28**: rec-a9fc00b5-7ae8-4396-9013-c753ce9da519; dirty; fail; tdd _(id: [rec-d4586113-b01e-45b8-b5b9-d04df5a7ce16](.artifacts/records/project__check-run/rec-d4586113-b01e-45b8-b5b9-d04df5a7ce16.md))_

## web-write-api-r29

### Acceptance
- **web-write-api-r29**: R29; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r29_backlog_promote -q _(id: [rec-85c4cf39-fd64-41fa-8e03-3aa46331d06f](.artifacts/records/project__acceptance/rec-85c4cf39-fd64-41fa-8e03-3aa46331d06f.md))_

### Check
- **web-write-api-r29**: rec-85c4cf39-fd64-41fa-8e03-3aa46331d06f; dirty; fail; tdd _(id: [rec-6c3b4a8b-a3f1-4dc0-883a-def50378184a](.artifacts/records/project__check-run/rec-6c3b4a8b-a3f1-4dc0-883a-def50378184a.md))_
- **web-write-api-r29**: rec-85c4cf39-fd64-41fa-8e03-3aa46331d06f; dirty; fail; tdd _(id: [rec-7ed439b8-f3bf-4aa5-9439-1eaeaf0fa57d](.artifacts/records/project__check-run/rec-7ed439b8-f3bf-4aa5-9439-1eaeaf0fa57d.md))_
- **web-write-api-r29**: rec-85c4cf39-fd64-41fa-8e03-3aa46331d06f; 6cacba9e9fb325600fd0805d74b574e3323eec73; pass; tdd _(id: [rec-af8ac0fc-d719-4f8d-a418-61bf350e2f27](.artifacts/records/project__check-run/rec-af8ac0fc-d719-4f8d-a418-61bf350e2f27.md))_

## web-write-api-r34

### Acceptance
- **web-write-api-r34**: R34; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r34_stale -q _(id: [rec-a3e1d953-95ac-48dc-a4e6-e5835b4e1a26](.artifacts/records/project__acceptance/rec-a3e1d953-95ac-48dc-a4e6-e5835b4e1a26.md))_

### Check
- **web-write-api-r34**: rec-a3e1d953-95ac-48dc-a4e6-e5835b4e1a26; 6cacba9e9fb325600fd0805d74b574e3323eec73; pass; tdd _(id: [rec-223fa910-2803-4557-855f-42da4cf4302e](.artifacts/records/project__check-run/rec-223fa910-2803-4557-855f-42da4cf4302e.md))_
- **web-write-api-r34**: rec-a3e1d953-95ac-48dc-a4e6-e5835b4e1a26; dirty; fail; tdd _(id: [rec-5049a8ef-b726-46b9-8e09-41be10b5c137](.artifacts/records/project__check-run/rec-5049a8ef-b726-46b9-8e09-41be10b5c137.md))_
- **web-write-api-r34**: rec-a3e1d953-95ac-48dc-a4e6-e5835b4e1a26; dirty; fail; tdd _(id: [rec-b87f64ec-3f67-4d4c-b94f-46a5a83e3d8f](.artifacts/records/project__check-run/rec-b87f64ec-3f67-4d4c-b94f-46a5a83e3d8f.md))_

## web-write-body-review

### Check
- **web-write-body-review**: web-write-body-review; 29fec4bceaa72b8880b50dc8ceda560810cdfb09; pass; review _(id: [rec-09a020ff-b81a-4600-9b28-feb8d546f0f1](.artifacts/records/project__check-run/rec-09a020ff-b81a-4600-9b28-feb8d546f0f1.md))_
