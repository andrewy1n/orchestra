# Project Brief

> Derived view — not authoritative. Edit underlying records, not this file.
> Store state: sha256:79204d0cf63268285b4b8014a2214b8acb7ef8f964ab6fb3cdcacb6a7e968776

## aa-installable-package

### Acceptance
- **aa-installable-package**: R1; check; packaging; test -f ~/adaptive-artifacts/pyproject.toml && grep -q adaptive-artifacts ~/adaptive-artifacts/pyproject.toml && grep -qE "scripts|entry.points|project.scripts" ~/adaptive-artifacts/pyproject.toml _(id: [rec-5926eafe-efb8-47ac-a314-50c1ff066f90](.artifacts/records/project__acceptance/rec-5926eafe-efb8-47ac-a314-50c1ff066f90.md))_

## aa-installable-package-plugin-bin

### Acceptance
- **aa-installable-package-plugin-bin**: R4; check; packaging; ~/adaptive-artifacts/bin/adaptive-artifacts --help >/dev/null _(id: [rec-de0125fd-b020-48fc-bd52-f66a04de6cbf](.artifacts/records/project__acceptance/rec-de0125fd-b020-48fc-bd52-f66a04de6cbf.md))_

## aa-installable-package-tools-shim

### Acceptance
- **aa-installable-package-tools-shim**: R5; check; packaging; python3 ~/adaptive-artifacts/tools/artifacts.py --help >/dev/null _(id: [rec-d7737207-7463-4fa3-828f-647c738784bf](.artifacts/records/project__acceptance/rec-d7737207-7463-4fa3-828f-647c738784bf.md))_

## aa-packaging-amendment

### Acceptance
- **aa-packaging-amendment**: R8; manual; packaging _(id: [rec-f9dc41e0-3e64-4707-b78a-db7b4f48eeb4](.artifacts/records/project__acceptance/rec-f9dc41e0-3e64-4707-b78a-db7b4f48eeb4.md))_

## aa-uv-tool-install-proof

### Acceptance
- **aa-uv-tool-install-proof**: R2; check; packaging; test -x ~/adaptive-artifacts/scripts/prove_uv_tool_install.sh && ~/adaptive-artifacts/scripts/prove_uv_tool_install.sh _(id: [rec-33598676-02a1-45b7-9d6f-379587854c4e](.artifacts/records/project__acceptance/rec-33598676-02a1-45b7-9d6f-379587854c4e.md))_

## aa-uv-tool-install-proof-store

### Acceptance
- **aa-uv-tool-install-proof-store**: R3; check; packaging; ~/adaptive-artifacts/scripts/prove_uv_tool_install.sh _(id: [rec-d9c4add2-b3a0-4106-8778-46d3711d3c7e](.artifacts/records/project__acceptance/rec-d9c4add2-b3a0-4106-8778-46d3711d3c7e.md))_

## activity-failures

### Acceptance
- **activity-failures**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k fail _(id: [rec-7d228e89-762a-4794-9c56-adfca651899a](.artifacts/records/project__acceptance/rec-7d228e89-762a-4794-9c56-adfca651899a.md))_

## adaptive-artifacts-change-gate

### Constraint
- **adaptive-artifacts-change-gate**: Runtime changes in the adaptive-artifacts repo follow its AGENTS.md gate: capture them in that repo's store and apply only with human approval; work-items that edit ~/adaptive-artifacts; dashboard _(id: [rec-0b5620e8-3bf4-45f3-9de4-6d10a46c578b](.artifacts/records/project__constraint/rec-0b5620e8-3bf4-45f3-9de4-6d10a46c578b.md))_

## add-dashboard-view

### Acceptance
- **add-dashboard-view**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-b6ae7140-2e58-4194-9294-6cc47d132fb4](.artifacts/records/project__acceptance/rec-b6ae7140-2e58-4194-9294-6cc47d132fb4.md))_

## add-dashboard-view-render

### Acceptance
- **add-dashboard-view-render**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q -k dashboard _(id: [rec-1dceda28-8bfd-43df-b3ca-53d3a7740286](.artifacts/records/project__acceptance/rec-1dceda28-8bfd-43df-b3ca-53d3a7740286.md))_

## advisory-suite-verification-policy

### Finding
- **advisory-suite-verification-policy**: advisory suite fail for verification-policy-suite; exit_code=1; failing journal pager tests under full suite; suite check-run passes at phase head, or human clears; none _(id: [rec-bc32b08c-6674-4bef-ac01-5f0442fae56c](.artifacts/records/project__finding/rec-bc32b08c-6674-4bef-ac01-5f0442fae56c.md))_

## affidavit-readme-git-tool

### Acceptance
- **affidavit-readme-git-tool**: R6; check; packaging; grep -qiE 'uv tool install' README.md && grep -qiE 'git\+https://github.com/andrewy1n/adaptive-artifacts' README.md && grep -qiE 'PyPI.*(defer|later|not yet|wait)' README.md && ! test -f pyproject.toml _(id: [rec-7e5deb60-6cc8-4796-9c46-325a846307cb](.artifacts/records/project__acceptance/rec-7e5deb60-6cc8-4796-9c46-325a846307cb.md))_

## affidavit-readme-git-tool-nopypi

### Acceptance
- **affidavit-readme-git-tool-nopypi**: R7; check; packaging; ! test -f pyproject.toml && ! grep -qiE 'twine upload|uv publish|pypi.org/project/adaptive-artifacts' README.md _(id: [rec-53c95333-c05e-4e8d-ad66-cd3d97bfc055](.artifacts/records/project__acceptance/rec-53c95333-c05e-4e8d-ad66-cd3d97bfc055.md))_

## ag-aggregate-cli

### Acceptance
- **ag-aggregate-cli**: tdd; session-analysis; python3 -m pytest -q tests/test_session_aggregate.py _(id: [rec-efaa257a-446d-4f97-a738-4d098747043f](.artifacts/records/project__acceptance/rec-efaa257a-446d-4f97-a738-4d098747043f.md))_

## ag-effort-rollup

### Acceptance
- **ag-effort-rollup**: tdd; session-analysis; python3 -m pytest -q tests/test_effort_rollup.py _(id: [rec-d0cbaaf6-d767-45f6-aa4d-f32b9415b6bc](.artifacts/records/project__acceptance/rec-d0cbaaf6-d767-45f6-aa4d-f32b9415b6bc.md))_

## ag-outliers

### Acceptance
- **ag-outliers**: tdd; session-analysis; python3 -m pytest -q tests/test_session_outliers.py _(id: [rec-4b4378e7-5443-435e-86ab-02ad515ebb4d](.artifacts/records/project__acceptance/rec-4b4378e7-5443-435e-86ab-02ad515ebb4d.md))_

## ag-tool-skill-rollup

### Acceptance
- **ag-tool-skill-rollup**: tdd; session-analysis; python3 -m pytest -q tests/test_tool_skill_rollup.py _(id: [rec-f283ff9c-78e6-439b-ae65-90ef88690304](.artifacts/records/project__acceptance/rec-f283ff9c-78e6-439b-ae65-90ef88690304.md))_

## approval-confirm-ux

### Acceptance
- **approval-confirm-ux**: R1; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and (detail or confirm or cancel)' _(id: [rec-18701e87-22d6-4a86-add9-8b350996cbcf](.artifacts/records/project__acceptance/rec-18701e87-22d6-4a86-add9-8b350996cbcf.md))_

## approval-confirm-ux-actions

### Acceptance
- **approval-confirm-ux-actions**: R3; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and (approve or reject or sign or accept)' _(id: [rec-cfce9c2b-44e5-4324-913a-5bb887a7aa33](.artifacts/records/project__acceptance/rec-cfce9c2b-44e5-4324-913a-5bb887a7aa33.md))_

## approval-confirm-ux-readme

### Acceptance
- **approval-confirm-ux-readme**: R8; check; workflow-loop; grep -E 'Approve|Reject|Accept risk|Sign' README.md && grep -E 'Needs you|dismiss|confirm' README.md _(id: [rec-454294d0-2d0a-4652-92d3-ddfd22b795fd](.artifacts/records/project__acceptance/rec-454294d0-2d0a-4652-92d3-ddfd22b795fd.md))_

## approval-constraints

### Acceptance
- **approval-constraints**: R7; check; workflow-loop; /home/andrewyin/adaptive-artifacts/bin/adaptive-artifacts --store /home/andrewyin/se-workflow/.artifacts list --type project:constraint --state active | python3 -c "import sys,json; d=json.load(sys.stdin); stmts=[(r['subject'], (r.get('payload') or {}).get('statement') or '') for r in d['records']]; assert any(s=='dashboard-human-gate-writes' for s,_ in stmts); hg=[t for s,t in stmts if s=='dashboard-human-gate-writes']; assert hg and ('human Needs-you' in hg[0] or 'human-gate' in hg[0].lower()); old={'dashboard-read-only','dashboard-read-only-dashboard-bugfix','dashboard-read-only-dashboard-features'}; assert not any('never writes' in t.lower() for s,t in stmts if s in old); assert all('Retired' in t or 'dashboard-human-gate-writes' in t for s,t in stmts if s in old)" _(id: [rec-7927a6c7-eea1-4224-b9a1-9d4800dce4b0](.artifacts/records/project__acceptance/rec-7927a6c7-eea1-4224-b9a1-9d4800dce4b0.md))_

## approval-contract

### Acceptance
- **approval-contract**: R8; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py -q -k approval_optional_payload_note_fields _(id: [rec-de3c1982-720c-4be7-90ef-54f23b74e65e](.artifacts/records/project__acceptance/rec-de3c1982-720c-4be7-90ef-54f23b74e65e.md))_

## approval-dismiss

### Acceptance
- **approval-dismiss**: R4; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k 'approval and (dismiss or revision or reject)' _(id: [rec-6709bf08-2353-479f-ae3d-993edd2c640c](.artifacts/records/project__acceptance/rec-6709bf08-2353-479f-ae3d-993edd2c640c.md))_

## approval-dismiss-stale

### Acceptance
- **approval-dismiss-stale**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and stale' _(id: [rec-5acd72b1-7099-4efa-a8b1-ac7f5c99ebd1](.artifacts/records/project__acceptance/rec-5acd72b1-7099-4efa-a8b1-ac7f5c99ebd1.md))_

## as-cost-null

### Acceptance
- **as-cost-null**: tdd; session-analysis; python3 -m pytest -q tests/test_session_fields.py _(id: [rec-36001c1e-b274-4757-b5b3-44fd1a44e292](.artifacts/records/project__acceptance/rec-36001c1e-b274-4757-b5b3-44fd1a44e292.md))_

### Finding
- **as-cost-null**: Null cost_usd on 140 of 247 sessions is a data gap: those transcripts have no cost-state line, so cost totals are a lower bound over 107 sessions.; Streamed all 140 null transcripts: 0 cost-state lines and 0 cost-named keys. The 107 non-null sessions parse correctly.; Claude Code starts writing cost-state lines for more sessions, or a different cost field appears in transcripts.; none _(id: [rec-8aa9b9e5-9088-4e73-a8ec-facffa2d3833](.artifacts/records/project__finding/rec-8aa9b9e5-9088-4e73-a8ec-facffa2d3833.md))_

## as-dry-run

### Acceptance
- **as-dry-run**: manual; session-analysis _(id: [rec-2fa1b9d2-53f0-4a38-bc7f-ace90efeb566](.artifacts/records/project__acceptance/rec-2fa1b9d2-53f0-4a38-bc7f-ace90efeb566.md))_

### Finding
- **as-dry-run**: The analyze-sessions skill yields 4 specific, metric-backed candidates on real data, but it lacks rules the agent had to guess: temp directory, pattern and noise, severity, and tool-level session ids.; Dry run over 243 sessions: 4 candidates each with a metric, session references and a target; 4 patterns dropped; 6 of 7 done-when criteria met (step 7 deferred to the caller). I re-checked the Bash, jira_create_issue and error-outlier numbers against a fresh run and they match.; SKILL.md defines the missing rules and a second dry run needs no manual report.jsonl lookups.; none _(id: [rec-1e84d081-a11f-4cf3-b588-672c9f99d52b](.artifacts/records/project__finding/rec-1e84d081-a11f-4cf3-b588-672c9f99d52b.md))_

## as-dry-run-rerun

### Finding
- **as-dry-run-rerun**: After the rules fix the skill needs no guessed rules for pattern, noise, severity or tool-level session references, but two gaps remain: project identity for worktree paths, and candidate edits that need a transcript read.; Second dry run over 243 sessions: 2 candidates with full session ids and targets, 2 patterns dropped, 1 noise session. The agent named remaining gaps: worktree project strings, double counting of slots across patterns, edits that cannot be named from metrics, cost outliers with empty efforts have no target, cross-repo fix locations.; SKILL.md and targets.md state the project-identity, double counting, evidence-needed and cross-repo rules and a third run needs no guesses.; none _(id: [rec-b393a226-8a19-4952-abff-ecfaf8532b8b](.artifacts/records/project__finding/rec-b393a226-8a19-4952-abff-ecfaf8532b8b.md))_

## as-skill

### Acceptance
- **as-skill**: tdd; session-analysis; python3 -m pytest -q tests/test_analyze_sessions_skill.py tests/test_skill_contract_consistency.py _(id: [rec-d186eb9e-852f-4f75-96aa-313e576c0f8b](.artifacts/records/project__acceptance/rec-d186eb9e-852f-4f75-96aa-313e576c0f8b.md))_

## as-skill-rules

### Acceptance
- **as-skill-rules**: tdd; session-analysis; python3 -m pytest -q tests/test_analyze_sessions_skill.py tests/test_skill_contract_consistency.py _(id: [rec-f0c76da5-b91f-4660-bcc7-e221a00ac3e8](.artifacts/records/project__acceptance/rec-f0c76da5-b91f-4660-bcc7-e221a00ac3e8.md))_

## as-targets

### Acceptance
- **as-targets**: tdd; session-analysis; python3 -m pytest -q tests/test_analyze_sessions_targets.py _(id: [rec-9c15a1e4-c392-4ce0-8482-7bea7dd7f367](.artifacts/records/project__acceptance/rec-9c15a1e4-c392-4ce0-8482-7bea7dd7f367.md))_

## assess-route

### Acceptance
- **assess-route**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_assess_routing.py -q _(id: [rec-fb7cdbf9-8de6-4066-a413-41f688ed3792](.artifacts/records/project__acceptance/rec-fb7cdbf9-8de6-4066-a413-41f688ed3792.md))_

## backlog-lifecycle

### Acceptance
- **backlog-lifecycle**: R3; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_backlog_item.py -q _(id: [rec-fc666597-85d7-42c1-a7e9-3f67d996e0c2](.artifacts/records/project__acceptance/rec-fc666597-85d7-42c1-a7e9-3f67d996e0c2.md))_

## backlog-lifecycle-promote

### Acceptance
- **backlog-lifecycle-promote**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_backlog_item.py -q _(id: [rec-a19b9909-b798-4b7d-a0e1-c2eac876dc42](.artifacts/records/project__acceptance/rec-a19b9909-b798-4b7d-a0e1-c2eac876dc42.md))_

## backlog-lifecycle-status

### Acceptance
- **backlog-lifecycle-status**: R4; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_backlog_item.py -q _(id: [rec-f5bbe8ab-d0e6-4929-9293-f23518096569](.artifacts/records/project__acceptance/rec-f5bbe8ab-d0e6-4929-9293-f23518096569.md))_

## budget-instructions

### Acceptance
- **budget-instructions**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py -q -k plan_phase_limits _(id: [rec-b147b60a-bac3-473f-bff5-6ea8db7fe2e9](.artifacts/records/project__acceptance/rec-b147b60a-bac3-473f-bff5-6ea8db7fe2e9.md))_

## budget-instructions-close

### Acceptance
- **budget-instructions-close**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py -q -k close_instructions _(id: [rec-a12edd10-9c55-4760-b80f-7fc1177203da](.artifacts/records/project__acceptance/rec-a12edd10-9c55-4760-b80f-7fc1177203da.md))_

## budget-instructions-filter

### Acceptance
- **budget-instructions-filter**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py -q -k rejects_whole_suite _(id: [rec-61d66067-90f5-4d51-b24b-0afb76d408d1](.artifacts/records/project__acceptance/rec-61d66067-90f5-4d51-b24b-0afb76d408d1.md))_

## budget-instructions-stop

### Acceptance
- **budget-instructions-stop**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py -q -k verification_failure _(id: [rec-4c85a8d1-dde4-448b-bfe6-aee86654a15e](.artifacts/records/project__acceptance/rec-4c85a8d1-dde4-448b-bfe6-aee86654a15e.md))_

## check-run-contract

### Acceptance
- **check-run-contract**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py tests/test_evidence_loop.py tests/test_assess_routing.py -q -k 'enum or result or method or contract' _(id: [rec-88363d0c-d058-4a0d-8c04-4a697bbe457d](.artifacts/records/project__acceptance/rec-88363d0c-d058-4a0d-8c04-4a697bbe457d.md))_

## claude-shared-marketplace

### Acceptance
- **claude-shared-marketplace**: R1; check; packaging; claude plugin validate . && python3 -c "import json;p=json.load(open('.claude-plugin/plugin.json'));d=p.get('dependencies',[]);assert 'adaptive-artifacts' in d or any(isinstance(x,dict) and x.get('name')=='adaptive-artifacts' for x in d);m=json.load(open('.claude-plugin/marketplace.json'));assert {x.get('name') for x in m['plugins']}>= {'se-workflow','adaptive-artifacts'}" _(id: [rec-a60c0f0a-abb6-4cfe-b569-657d0edb4722](.artifacts/records/project__acceptance/rec-a60c0f0a-abb6-4cfe-b569-657d0edb4722.md))_

## claude-shared-marketplace-readme

### Acceptance
- **claude-shared-marketplace-readme**: R4; check; packaging; grep -q 'claude plugin marketplace add andrewy1n/se-workflow' README.md && grep -qi Cursor README.md && ! grep -qiE 'Cursor.*(auto-?install|plugin dependenc).*adaptive-artifacts' README.md _(id: [rec-49384b6f-6de8-4e22-b43c-f27f3e8f06ad](.artifacts/records/project__acceptance/rec-49384b6f-6de8-4e22-b43c-f27f3e8f06ad.md))_

## cli-package

### Acceptance
- **cli-package**: R5; check; packaging; python3 -m pytest tests/test_cli_packaging.py -q -k path _(id: [rec-9ffe3fb9-03cc-47ac-a3a2-186887e34afd](.artifacts/records/project__acceptance/rec-9ffe3fb9-03cc-47ac-a3a2-186887e34afd.md))_

## cli-package-subcommands

### Acceptance
- **cli-package-subcommands**: R7; check; packaging; python3 -m pytest tests/test_cli_packaging.py -q -k subcommands _(id: [rec-813d0fb9-e4f2-4b91-8d62-c995948029de](.artifacts/records/project__acceptance/rec-813d0fb9-e4f2-4b91-8d62-c995948029de.md))_

## close-batch-cli

### Acceptance
- **close-batch-cli**: R3; tdd; packaging; uv run --with pytest python -m pytest tests/test_close_batch.py -q _(id: [rec-45b51bb0-0c79-4f85-9120-374742d1d297](.artifacts/records/project__acceptance/rec-45b51bb0-0c79-4f85-9120-374742d1d297.md))_

## close-batch-store-verify

### Acceptance
- **close-batch-store-verify**: R1; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'store_authority or fabricated or mismatch' -q _(id: [rec-a4a45232-6634-47b1-bbaf-11633085234e](.artifacts/records/project__acceptance/rec-a4a45232-6634-47b1-bbaf-11633085234e.md))_

## close-batch-store-verify-missing

### Acceptance
- **close-batch-store-verify-missing**: R4; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'missing_check_run_id or missing_result or result_optional' -q _(id: [rec-3c86fb99-228d-40b6-99f7-5d48aa05de37](.artifacts/records/project__acceptance/rec-3c86fb99-228d-40b6-99f7-5d48aa05de37.md))_

## close-batch-store-verify-red

### Acceptance
- **close-batch-store-verify-red**: R2; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'red_store or dirty_green or missing_green_revision' -q _(id: [rec-3fd581e7-7b66-4e35-9f7d-174b45144862](.artifacts/records/project__acceptance/rec-3fd581e7-7b66-4e35-9f7d-174b45144862.md))_

## close-batch-store-verify-revision

### Acceptance
- **close-batch-store-verify-revision**: R3; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'tdd_revision_without_red or revision_allowed_tdd' -q _(id: [rec-b97cbd55-140b-4868-8652-f4dda7f99ae8](.artifacts/records/project__acceptance/rec-b97cbd55-140b-4868-8652-f4dda7f99ae8.md))_

## close-red-first

### Acceptance
- **close-red-first**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first _(id: [rec-e7b02db3-cbf8-492f-8363-9844982d7753](.artifacts/records/project__acceptance/rec-e7b02db3-cbf8-492f-8363-9844982d7753.md))_

## close-red-first-escape

### Acceptance
- **close-red-first-escape**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k 'red_first_escape or red_first_other_methods' _(id: [rec-c8b5c4cd-99a6-4906-a91c-7b4385187029](.artifacts/records/project__acceptance/rec-c8b5c4cd-99a6-4906-a91c-7b4385187029.md))_

## close-red-first-methods

### Acceptance
- **close-red-first-methods**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_other_methods _(id: [rec-20f81a2f-2df9-4e5d-9eec-63da3defeec3](.artifacts/records/project__acceptance/rec-20f81a2f-2df9-4e5d-9eec-63da3defeec3.md))_

## close-red-first-order

### Acceptance
- **close-red-first-order**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_order _(id: [rec-6e4d8f33-f843-4db1-a990-e3c5ea1abbd7](.artifacts/records/project__acceptance/rec-6e4d8f33-f843-4db1-a990-e3c5ea1abbd7.md))_

## close-red-first-request

### Acceptance
- **close-red-first-request**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_request _(id: [rec-be6e5c30-7b5f-44e1-b497-7dcbccbea6ad](.artifacts/records/project__acceptance/rec-be6e5c30-7b5f-44e1-b497-7dcbccbea6ad.md))_

## close-step-skill

### Acceptance
- **close-step-skill**: tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-8bcac210-20bd-42a8-b0ea-953bd412937a](.artifacts/records/project__acceptance/rec-8bcac210-20bd-42a8-b0ea-953bd412937a.md))_

## column-resize

### Acceptance
- **column-resize**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k resize _(id: [rec-4b32e614-7d7e-4a55-be85-301c98fe6ef9](.artifacts/records/project__acceptance/rec-4b32e614-7d7e-4a55-be85-301c98fe6ef9.md))_

## commit-stat-width

### Acceptance
- **commit-stat-width**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-de68bee3-9f99-4495-8545-8aa7b453e373](.artifacts/records/project__acceptance/rec-de68bee3-9f99-4495-8545-8aa7b453e373.md))_

## contract-backlog

### Acceptance
- **contract-backlog**: R1; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-23b30985-3712-43f6-b1e4-f9240d9a632c](.artifacts/records/project__acceptance/rec-23b30985-3712-43f6-b1e4-f9240d9a632c.md))_

## contract-backlog-effort

### Acceptance
- **contract-backlog-effort**: R3; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-1686fb83-3253-4571-8f6d-9b927f916c77](.artifacts/records/project__acceptance/rec-1686fb83-3253-4571-8f6d-9b927f916c77.md))_

## contract-backlog-status

### Acceptance
- **contract-backlog-status**: R4; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-7f83aff0-87bd-4dfa-9d94-12920f3a46aa](.artifacts/records/project__acceptance/rec-7f83aff0-87bd-4dfa-9d94-12920f3a46aa.md))_

## contract-loop

### Acceptance
- **contract-loop**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-6d715e64-501c-42c0-b057-42d81bbb01b8](.artifacts/records/project__acceptance/rec-6d715e64-501c-42c0-b057-42d81bbb01b8.md))_

## contract-thin-criterion

### Acceptance
- **contract-thin-criterion**: R4; check; workflow-loop; python3 -c "import json; from pathlib import Path; d=json.loads(Path('contract/project-design.json').read_text()); acc=next(r for r in d['records'] if r['name']=='acceptance'); assert 'criterion' in acc['optional_payload']; assert 'criterion' not in (set(acc['payload'])-set(acc['optional_payload'])); views={v.get('name') or v.get('id'): v for v in (d['views'] if isinstance(d['views'], list) else list(d['views'].values()))}; bad=[n for n,v in views.items() for r in v.get('roles',[]) if (r.get('occupant')=='acceptance' or r.get('name')=='acceptance') and 'criterion' in r.get('requires_payload',[])]; assert not bad, bad" _(id: [rec-c79b18fc-3e2f-4a36-8417-9799d980ae1d](.artifacts/records/project__acceptance/rec-c79b18fc-3e2f-4a36-8417-9799d980ae1d.md))_

## copy-and-commit-actions

### Acceptance
- **copy-and-commit-actions**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-b0782695-b6a8-443a-b1ed-fd39a65b5de8](.artifacts/records/project__acceptance/rec-b0782695-b6a8-443a-b1ed-fd39a65b5de8.md))_

## dashboard

### Position
- **dashboard**: All web-calm phases settled; next is plan-phase for milestone-nav; effort _(id: [rec-9eef7d5f-8f2e-4ec3-9678-65c9632f2381](.artifacts/records/project__current-position/rec-9eef7d5f-8f2e-4ec3-9678-65c9632f2381.md))_

## dashboard-app

### Acceptance
- **dashboard-app**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-607927c0-6e77-499d-ae1f-ee7a890cfd07](.artifacts/records/project__acceptance/rec-607927c0-6e77-499d-ae1f-ee7a890cfd07.md))_

### Amendment
- **dashboard-app**: dashboard-app; dashboard-ui _(id: [rec-28e50357-bdf1-45e3-8b4c-eecbdd3839d2](.artifacts/records/project__assignment-amendment/rec-28e50357-bdf1-45e3-8b4c-eecbdd3839d2.md))_

## dashboard-autonomy-dashboard-bugfix

### Constraint
- **dashboard-autonomy-dashboard-bugfix**: Plan and promote each next phase without asking once the current one closes; stop only for failures, needs-human findings, or a push or merge; dashboard-bugfix; dashboard _(id: [rec-d758928c-9ec7-4707-8093-e9ba5a5a7cc4](.artifacts/records/project__constraint/rec-d758928c-9ec7-4707-8093-e9ba5a5a7cc4.md))_

## dashboard-autonomy-dashboard-features

### Constraint
- **dashboard-autonomy-dashboard-features**: Plan and promote each next phase without asking once the current one closes; stop only for failures, needs-human findings, or a push or merge; dashboard-features; dashboard _(id: [rec-b67f5d65-3a49-440a-b695-c02c2b1bd644](.artifacts/records/project__constraint/rec-b67f5d65-3a49-440a-b695-c02c2b1bd644.md))_

## dashboard-backlog

### Acceptance
- **dashboard-backlog**: R6; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k backlog _(id: [rec-00466274-876f-4c8b-a54e-a8db1e61fbda](.artifacts/records/project__acceptance/rec-00466274-876f-4c8b-a54e-a8db1e61fbda.md))_

## dashboard-backlog-actions

### Acceptance
- **dashboard-backlog-actions**: R6; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k backlog _(id: [rec-644805a3-42e4-4437-8ffc-cd772a363cea](.artifacts/records/project__acceptance/rec-644805a3-42e4-4437-8ffc-cd772a363cea.md))_

## dashboard-branches-dashboard-bugfix

### Constraint
- **dashboard-branches-dashboard-bugfix**: Work on stacked branches: fix/dashboard-bugfix from main, feat/dashboard-features from it; one commit per task; commit at each effort end; no merge to main until both efforts are done and the user says so; dashboard-bugfix; dashboard _(id: [rec-c99978db-a6a5-496c-a8ea-6f88e1bdcc4b](.artifacts/records/project__constraint/rec-c99978db-a6a5-496c-a8ea-6f88e1bdcc4b.md))_

## dashboard-branches-dashboard-features

### Constraint
- **dashboard-branches-dashboard-features**: Work on stacked branches: fix/dashboard-bugfix from main, feat/dashboard-features from it; one commit per task; commit at each effort end; no merge to main until both efforts are done and the user says so; dashboard-features; dashboard _(id: [rec-c1e52997-e4a1-4599-a252-2f9b0f7f5de9](.artifacts/records/project__constraint/rec-c1e52997-e4a1-4599-a252-2f9b0f7f5de9.md))_

## dashboard-closed-goals

### Acceptance
- **dashboard-closed-goals**: tdd; workflow-loop; python3 -m pytest tests/test_dashboard_model.py -q _(id: [rec-f02ec3b2-3bd6-496f-933a-1506d3b4a877](.artifacts/records/project__acceptance/rec-f02ec3b2-3bd6-496f-933a-1506d3b4a877.md))_

## dashboard-dismiss

### Acceptance
- **dashboard-dismiss**: R4; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k dismiss _(id: [rec-3399e692-0dd4-4842-9cb1-3ff2a3f95513](.artifacts/records/project__acceptance/rec-3399e692-0dd4-4842-9cb1-3ff2a3f95513.md))_

### Finding
- **dashboard-dismiss**: Dashboard mirrored open human gates but never dismissed them via adaptive-artifacts CLI; pre-fix UI had no d-dismiss; pilots now pass for clear/refuse/CLI-fail; dismiss pilots fail or dashboard invents a local dismiss cache; none _(id: [rec-02f2b892-db35-4a29-8220-d89cbe33ab4c](.artifacts/records/project__finding/rec-02f2b892-db35-4a29-8220-d89cbe33ab4c.md))_

## dashboard-dismiss-refuse

### Acceptance
- **dashboard-dismiss-refuse**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'dismiss and (refuse or fail or error)' _(id: [rec-76204de3-ed47-4406-9096-db2caa3f9d68](.artifacts/records/project__acceptance/rec-76204de3-ed47-4406-9096-db2caa3f9d68.md))_

## dashboard-human-gate-writes

### Constraint
- **dashboard-human-gate-writes**: The dashboard may write to the artifact store only for: (1) human Needs-you gates (continuity-question answer/reject-routing, unsigned manual check sign, finding accept-risk) via the adaptive-artifacts CLI using the displayed record revision and a recorded decision or note as designed; and (2) backlog promote/dismiss of project:backlog-item via the adaptive-artifacts CLI (existing backlog path). No other dashboard store writes.; dashboard/dismiss.py, dashboard Needs-you confirm UX, and dashboard/backlog.py promote/dismiss; workflow-loop _(id: [rec-d7e838f6-8bcb-409b-a42f-b7c275fd572a](.artifacts/records/project__constraint/rec-d7e838f6-8bcb-409b-a42f-b7c275fd572a.md))_

## dashboard-launcher

### Acceptance
- **dashboard-launcher**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-e4e1b7a5-4c4b-45ce-8a02-bb12452e15ea](.artifacts/records/project__acceptance/rec-e4e1b7a5-4c4b-45ce-8a02-bb12452e15ea.md))_

## dashboard-launcher-switch

### Acceptance
- **dashboard-launcher-switch**: tdd; dashboard; python3 -m pytest tests/test_dashboard_launcher.py tests/test_tmux_integration.py -q _(id: [rec-7fbf25bf-c639-424e-a4a2-66a5d640f23a](.artifacts/records/project__acceptance/rec-7fbf25bf-c639-424e-a4a2-66a5d640f23a.md))_

## dashboard-read-only

### Constraint
- **dashboard-read-only**: Retired: see active constraint dashboard-human-gate-writes for the allowed dashboard human-gate write set.; superseded — do not enforce; workflow-loop _(id: [rec-4166b95d-091d-4916-a329-98947bc115ef](.artifacts/records/project__constraint/rec-4166b95d-091d-4916-a329-98947bc115ef.md))_

## dashboard-read-only-dashboard-bugfix

### Constraint
- **dashboard-read-only-dashboard-bugfix**: Retired: see active constraint dashboard-human-gate-writes for the allowed dashboard human-gate write set.; superseded — do not enforce; workflow-loop _(id: [rec-c5efee3b-e0f7-46c6-ba6d-fbb490dac319](.artifacts/records/project__constraint/rec-c5efee3b-e0f7-46c6-ba6d-fbb490dac319.md))_

## dashboard-read-only-dashboard-features

### Constraint
- **dashboard-read-only-dashboard-features**: Retired: see active constraint dashboard-human-gate-writes for the allowed dashboard human-gate write set.; superseded — do not enforce; workflow-loop _(id: [rec-2279d7f2-696c-40dc-a787-d70ff5871593](.artifacts/records/project__constraint/rec-2279d7f2-696c-40dc-a787-d70ff5871593.md))_

## dashboard-snapshot

### Acceptance
- **dashboard-snapshot**: tdd; dashboard; python3 -m pytest tests/test_dashboard_model.py -q _(id: [rec-8f27fb0c-0113-4d37-9083-5f9767e2d6e6](.artifacts/records/project__acceptance/rec-8f27fb0c-0113-4d37-9083-5f9767e2d6e6.md))_

### Amendment
- **dashboard-snapshot**: dashboard-snapshot; dashboard-ui _(id: [rec-4c7d0765-e159-46f2-b4d4-c84dbbcd2d15](.artifacts/records/project__assignment-amendment/rec-4c7d0765-e159-46f2-b4d4-c84dbbcd2d15.md))_

## dashboard-status-segment

### Acceptance
- **dashboard-status-segment**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-e7e94ca1-9742-44b2-9fe1-7a014b58ef3d](.artifacts/records/project__acceptance/rec-e7e94ca1-9742-44b2-9fe1-7a014b58ef3d.md))_

## dashboard-ux-plan-before-execute

### Constraint
- **dashboard-ux-plan-before-execute**: Do not execute any of the five dashboard UX phases until all five have been discussed and planned; phase-selector,human-gates,spec-view,evidence-matrix,journal-view; dashboard _(id: [rec-9c441f5e-4313-4d89-9ec2-1d2df485e1ea](.artifacts/records/project__constraint/rec-9c441f5e-4313-4d89-9ec2-1d2df485e1ea.md))_

## detail-redraw-race

### Acceptance
- **detail-redraw-race**: check; dashboard; for i in $(seq 30); do uv run --with textual --with pytest python -m pytest 'tests/test_dashboard_app.py::test_detail_screen_redraws_when_the_store_changes' -q || exit 1; done _(id: [rec-c4742568-196f-4b86-89ea-4a12a7490978](.artifacts/records/project__acceptance/rec-c4742568-196f-4b86-89ea-4a12a7490978.md))_

### Finding
- **detail-redraw-race**: The detail screen paint queried #related after awaits without re-checking that the screen was still attached, so a poll-triggered redraw racing teardown raised NoMatches; Traceback apply -> paint query_one(#related) in 5 of 25 loaded runs; 30/30 loaded and 30/30 alone after re-checking is_attached after the awaits; The test fails again with NoMatches after 03d561c; none _(id: [rec-5018f385-7ec4-40ba-9736-d651d7b2af88](.artifacts/records/project__finding/rec-5018f385-7ec4-40ba-9736-d651d7b2af88.md))_

## discuss-skill

### Acceptance
- **discuss-skill**: tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_discuss_skill.py -q _(id: [rec-29f17960-fd84-4c12-9d0b-9589e7b71980](.artifacts/records/project__acceptance/rec-29f17960-fd84-4c12-9d0b-9589e7b71980.md))_

## drop-row-waits-on

### Acceptance
- **drop-row-waits-on**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_tasks.py -q -k 'title_cell and waits' _(id: [rec-873b510b-7eeb-42da-a7e7-fc83684576e7](.artifacts/records/project__acceptance/rec-873b510b-7eeb-42da-a7e7-fc83684576e7.md))_

### Finding
- **drop-row-waits-on**: title_cell appended an unclipped waits-on dependency list that overflowed and wrapped task rows; code inspection of title_cell plus failing then passing TDD slice; title_cell again appends waits on text or detail loses Depends on links; none _(id: [rec-8a2bc307-f417-4d2f-a4b7-507724e2e977](.artifacts/records/project__finding/rec-8a2bc307-f417-4d2f-a4b7-507724e2e977.md))_

## drop-row-waits-on-detail

### Acceptance
- **drop-row-waits-on-detail**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'detail and (Depends or blocked or waiting)' _(id: [rec-d2f45e59-d643-45ff-97f9-72e4edd0debb](.artifacts/records/project__acceptance/rec-d2f45e59-d643-45ff-97f9-72e4edd0debb.md))_

## drop-row-waits-on-oneline

### Acceptance
- **drop-row-waits-on-oneline**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'waiting_row' _(id: [rec-171c0948-9d2c-48a5-8622-a063778e21bf](.artifacts/records/project__acceptance/rec-171c0948-9d2c-48a5-8622-a063778e21bf.md))_

## e2e-real-execute-run

### Acceptance
- **e2e-real-execute-run**: manual; dashboard _(id: [rec-70f9c43d-01d7-438e-8df6-ad97b7fd46ce](.artifacts/records/project__acceptance/rec-70f9c43d-01d7-438e-8df6-ad97b7fd46ce.md))_

## e2e-scripted-run

### Acceptance
- **e2e-scripted-run**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests -q -k e2e _(id: [rec-5f7f36da-ec22-4619-b31b-8ff7fb3b85ee](.artifacts/records/project__acceptance/rec-5f7f36da-ec22-4619-b31b-8ff7fb3b85ee.md))_

## effort-switch-focus

### Acceptance
- **effort-switch-focus**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k switch _(id: [rec-768f3192-cdcf-45d9-9421-2282f78e8bef](.artifacts/records/project__acceptance/rec-768f3192-cdcf-45d9-9421-2282f78e8bef.md))_

## estimate-chips

### Acceptance
- **estimate-chips**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_estimate.py -q -k estimate_view_chips _(id: [rec-9151bd53-c190-48d4-a538-e887e6f192bd](.artifacts/records/project__acceptance/rec-9151bd53-c190-48d4-a538-e887e6f192bd.md))_

## estimate-contract

### Acceptance
- **estimate-contract**: R1; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_contract.py -q -k size _(id: [rec-1f969ece-cd7e-42c2-944a-899e5ff0f266](.artifacts/records/project__acceptance/rec-1f969ece-cd7e-42c2-944a-899e5ff0f266.md))_

## estimate-contract-minutes

### Acceptance
- **estimate-contract-minutes**: R2; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_contract.py -q -k minutes _(id: [rec-5a0f9f85-407d-497d-b412-1e314d15e91d](.artifacts/records/project__acceptance/rec-5a0f9f85-407d-497d-b412-1e314d15e91d.md))_

## estimate-model

### Acceptance
- **estimate-model**: R1; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_sitting_phrase _(id: [rec-7eabd5f4-5519-4834-b2f5-2330ed0ff75e](.artifacts/records/project__acceptance/rec-7eabd5f4-5519-4834-b2f5-2330ed0ff75e.md))_

## estimate-model-blank

### Acceptance
- **estimate-model-blank**: R7; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_blank_executor _(id: [rec-910eed74-aa0f-4d5f-af8b-aa7323cf0f9a](.artifacts/records/project__acceptance/rec-910eed74-aa0f-4d5f-af8b-aa7323cf0f9a.md))_

## estimate-model-row

### Acceptance
- **estimate-model-row**: R4; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_row_fields _(id: [rec-18fd0fc9-9da2-4cc0-a5e1-a968d60dac73](.artifacts/records/project__acceptance/rec-18fd0fc9-9da2-4cc0-a5e1-a968d60dac73.md))_

## estimate-model-unset

### Acceptance
- **estimate-model-unset**: R3; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_unset_count _(id: [rec-12a895aa-399e-41fb-9955-825515f54673](.artifacts/records/project__acceptance/rec-12a895aa-399e-41fb-9955-825515f54673.md))_

## estimate-model-wave

### Acceptance
- **estimate-model-wave**: R2; tdd; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_wave_rule _(id: [rec-70638ad0-75c0-4b42-8827-77ec817e3cfd](.artifacts/records/project__acceptance/rec-70638ad0-75c0-4b42-8827-77ec817e3cfd.md))_

## estimate-skill

### Acceptance
- **estimate-skill**: R3; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_skill.py -q -k write _(id: [rec-0106101c-dc9b-4060-bef9-b1dd59a2bd68](.artifacts/records/project__acceptance/rec-0106101c-dc9b-4060-bef9-b1dd59a2bd68.md))_

## estimate-skill-rollup

### Acceptance
- **estimate-skill-rollup**: R4; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_skill.py -q -k rollup _(id: [rec-8ea82af0-405d-4dbb-bb7c-a73bdf063adf](.artifacts/records/project__acceptance/rec-8ea82af0-405d-4dbb-bb7c-a73bdf063adf.md))_

## estimate-skill-sitting

### Acceptance
- **estimate-skill-sitting**: R5; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_skill.py -q -k sitting _(id: [rec-bd586f77-929c-45d7-882a-438a63414019](.artifacts/records/project__acceptance/rec-bd586f77-929c-45d7-882a-438a63414019.md))_

## estimate-table

### Acceptance
- **estimate-table**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_header_sitting _(id: [rec-0334ff65-b695-433e-97e4-feed4a633233](.artifacts/records/project__acceptance/rec-0334ff65-b695-433e-97e4-feed4a633233.md))_

## estimate-table-clip

### Acceptance
- **estimate-table-clip**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_clip _(id: [rec-3c8dcd3a-d259-4881-b1d2-d5c39548776a](.artifacts/records/project__acceptance/rec-3c8dcd3a-d259-4881-b1d2-d5c39548776a.md))_

## estimate-table-elapsed

### Acceptance
- **estimate-table-elapsed**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_header_elapsed _(id: [rec-d4eb4fe3-27e9-44aa-ac89-9138f8666348](.artifacts/records/project__acceptance/rec-d4eb4fe3-27e9-44aa-ac89-9138f8666348.md))_

## estimate-table-partial

### Acceptance
- **estimate-table-partial**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_header_partial _(id: [rec-f4e5899d-ba88-4a58-ad18-718a28db0e16](.artifacts/records/project__acceptance/rec-f4e5899d-ba88-4a58-ad18-718a28db0e16.md))_

## estimate-table-suffix

### Acceptance
- **estimate-table-suffix**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_title_suffix _(id: [rec-c823c876-890c-4582-b8ac-0b8e804b6de6](.artifacts/records/project__acceptance/rec-c823c876-890c-4582-b8ac-0b8e804b6de6.md))_

## evidence-model

### Acceptance
- **evidence-model**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and requirement' _(id: [rec-d9e2121e-cbda-488a-b93d-f162ca25e09d](.artifacts/records/project__acceptance/rec-d9e2121e-cbda-488a-b93d-f162ca25e09d.md))_

### Amendment
- **evidence-model**: evidence-model; dashboard _(id: [rec-57f0a62f-d115-4453-a551-1bb3e4f0713e](.artifacts/records/project__assignment-amendment/rec-57f0a62f-d115-4453-a551-1bb3e4f0713e.md))_

## evidence-model-activity

### Acceptance
- **evidence-model-activity**: R8; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and activity' _(id: [rec-40275e71-0386-466c-9431-b6a06ea32cc4](.artifacts/records/project__acceptance/rec-40275e71-0386-466c-9431-b6a06ea32cc4.md))_

## evidence-model-detail

### Acceptance
- **evidence-model-detail**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and requirement_detail' _(id: [rec-03a4156f-4505-4c4a-84f8-b2dbf28dbc76](.artifacts/records/project__acceptance/rec-03a4156f-4505-4c4a-84f8-b2dbf28dbc76.md))_

## evidence-model-legacy

### Acceptance
- **evidence-model-legacy**: R10; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and legacy' _(id: [rec-6d2b9680-5f62-4979-8450-8b3f99e1707b](.artifacts/records/project__acceptance/rec-6d2b9680-5f62-4979-8450-8b3f99e1707b.md))_

## evidence-model-needs

### Acceptance
- **evidence-model-needs**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and needs' _(id: [rec-b629a582-c0ce-42e7-a2c8-006bf618a411](.artifacts/records/project__acceptance/rec-b629a582-c0ce-42e7-a2c8-006bf618a411.md))_

## evidence-model-release

### Acceptance
- **evidence-model-release**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and release' _(id: [rec-0ebb72a4-a992-4c0d-804f-e4b659df3ff1](.artifacts/records/project__acceptance/rec-0ebb72a4-a992-4c0d-804f-e4b659df3ff1.md))_

## evidence-model-simple

### Acceptance
- **evidence-model-simple**: R9; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and simple' _(id: [rec-5cd3b306-dec8-422d-adcd-d051b9748117](.artifacts/records/project__acceptance/rec-5cd3b306-dec8-422d-adcd-d051b9748117.md))_

## evidence-model-stage

### Acceptance
- **evidence-model-stage**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and stage' _(id: [rec-0efed917-d236-4ffc-893e-994b77883d20](.artifacts/records/project__acceptance/rec-0efed917-d236-4ffc-893e-994b77883d20.md))_

## evidence-surfaces

### Acceptance
- **evidence-surfaces**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and tally' _(id: [rec-af8be786-2f56-46ed-95a4-4b0e2f42cfcc](.artifacts/records/project__acceptance/rec-af8be786-2f56-46ed-95a4-4b0e2f42cfcc.md))_

## evidence-surfaces-activity

### Acceptance
- **evidence-surfaces-activity**: R8; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and activity' _(id: [rec-f0de4074-6f9b-4db2-96b2-64768ae46a3f](.artifacts/records/project__acceptance/rec-f0de4074-6f9b-4db2-96b2-64768ae46a3f.md))_

## evidence-surfaces-needs

### Acceptance
- **evidence-surfaces-needs**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and needs' _(id: [rec-af74e732-3147-46e6-959b-9de2d204d9f8](.artifacts/records/project__acceptance/rec-af74e732-3147-46e6-959b-9de2d204d9f8.md))_

## evidence-surfaces-phase

### Acceptance
- **evidence-surfaces-phase**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and strip' _(id: [rec-11264441-69a2-49e7-bc6f-61337f037af7](.artifacts/records/project__acceptance/rec-11264441-69a2-49e7-bc6f-61337f037af7.md))_

## evidence-surfaces-release

### Acceptance
- **evidence-surfaces-release**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and release' _(id: [rec-1e0e0e59-dc14-4393-96b8-8b865ab34368](.artifacts/records/project__acceptance/rec-1e0e0e59-dc14-4393-96b8-8b865ab34368.md))_

## evidence-surfaces-requirements

### Acceptance
- **evidence-surfaces-requirements**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and requirement_list' _(id: [rec-4e3b28bd-22b8-4af2-8798-0bc134ff47ab](.artifacts/records/project__acceptance/rec-4e3b28bd-22b8-4af2-8798-0bc134ff47ab.md))_

## evidence-surfaces-simple

### Acceptance
- **evidence-surfaces-simple**: R9; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and simple' _(id: [rec-6d5d3021-1e7d-4938-9385-d0112fce7aa8](.artifacts/records/project__acceptance/rec-6d5d3021-1e7d-4938-9385-d0112fce7aa8.md))_

## evidence-surfaces-stepper

### Acceptance
- **evidence-surfaces-stepper**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and stepper' _(id: [rec-dea24b5b-9884-4880-a246-013ea423d317](.artifacts/records/project__acceptance/rec-dea24b5b-9884-4880-a246-013ea423d317.md))_

## execute-landing

### Acceptance
- **execute-landing**: tdd; workflow-loop; python3 -m pytest tests/test_execute_landing.py -q _(id: [rec-b89f9c9f-d9f4-4db9-8375-3f877388c961](.artifacts/records/project__acceptance/rec-b89f9c9f-d9f4-4db9-8375-3f877388c961.md))_

## execute-wave-dispatch

### Acceptance
- **execute-wave-dispatch**: tdd; workflow-loop; python3 -m pytest tests/test_execute_wave_dispatch.py -q _(id: [rec-c95855b2-e077-44d7-ab61-b8b70ec6f7df](.artifacts/records/project__acceptance/rec-c95855b2-e077-44d7-ab61-b8b70ec6f7df.md))_

## finished-effort-view

### Acceptance
- **finished-effort-view**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k finished _(id: [rec-cc216932-78bb-4df8-b80d-8da0eb287a9c](.artifacts/records/project__acceptance/rec-cc216932-78bb-4df8-b80d-8da0eb287a9c.md))_

## fix-cli-runtime-surface

### Acceptance
- **fix-cli-runtime-surface**: R6; check; packaging; python3 -m pytest tests/test_cli_surface.py -q _(id: [rec-410904bd-1380-4a65-b217-c9bcdc1406f6](.artifacts/records/project__acceptance/rec-410904bd-1380-4a65-b217-c9bcdc1406f6.md))_

## fix-cli-runtime-surface-skills

### Acceptance
- **fix-cli-runtime-surface-skills**: R7; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k runtime _(id: [rec-01c893b8-ad15-48b9-be21-b4036a804a99](.artifacts/records/project__acceptance/rec-01c893b8-ad15-48b9-be21-b4036a804a99.md))_

## fix-cli-standalone

### Acceptance
- **fix-cli-standalone**: R5; check; packaging; python3 -m pytest tests/test_cli_packaging.py -q -k standalone _(id: [rec-7679b134-94c1-400d-b741-58f92ad52ba9](.artifacts/records/project__acceptance/rec-7679b134-94c1-400d-b741-58f92ad52ba9.md))_

## fix-contract-record-types

### Acceptance
- **fix-contract-record-types**: R3; check; workflow-loop; python3 -c "import json;from pathlib import Path;d=json.loads(Path('contract/project-design.json').read_text());assert 'record_types' not in d;types={t['name']:t for t in d['records']};a=types['acceptance'];assert 'test_ids' in a['payload'] and 'oracle_hashes' in a['payload'];assert 'oracle-amendment' in types" _(id: [rec-bb17c5ee-0385-4c8e-90d2-3fe5f9e2b519](.artifacts/records/project__acceptance/rec-bb17c5ee-0385-4c8e-90d2-3fe5f9e2b519.md))_

## fix-docs-and-hooks

### Acceptance
- **fix-docs-and-hooks**: R15; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q _(id: [rec-b98522f2-478d-4583-aee3-5ed705b1cb80](.artifacts/records/project__acceptance/rec-b98522f2-478d-4583-aee3-5ed705b1cb80.md))_

## fix-docs-and-hooks-claude

### Acceptance
- **fix-docs-and-hooks-claude**: R12; check; packaging; python3 -m pytest tests/test_installer.py -q -k hooks _(id: [rec-dbe94c7c-4d38-41c1-abb8-a0be5fac9de0](.artifacts/records/project__acceptance/rec-dbe94c7c-4d38-41c1-abb8-a0be5fac9de0.md))_

## fix-human-gate-constraint

### Acceptance
- **fix-human-gate-constraint**: R7; check; workflow-loop; /home/andrewyin/adaptive-artifacts/bin/adaptive-artifacts --store /home/andrewyin/se-workflow/.artifacts list --type project:constraint --state active | python3 -c "import sys,json; d=json.load(sys.stdin); stmts=[(r['subject'], (r.get('payload') or {}).get('statement') or '') for r in d['records']]; hg=[t for s,t in stmts if s=='dashboard-human-gate-writes']; assert hg; t=hg[0].lower(); assert 'needs-you' in t or 'human' in t; assert 'backlog' in t and (('promote' in t) or ('dismiss' in t)); old={'dashboard-read-only','dashboard-read-only-dashboard-bugfix','dashboard-read-only-dashboard-features'}; assert not any('never writes' in x.lower() for s,x in stmts if s in old)" _(id: [rec-7cd14081-b40c-4643-9c77-8ead22c68483](.artifacts/records/project__acceptance/rec-7cd14081-b40c-4643-9c77-8ead22c68483.md))_

## fix-journal-pager-timeout

### Acceptance
- **fix-journal-pager-timeout**: tdd; packaging; uv run --with textual --with pytest python -m pytest tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub -q _(id: [rec-83a0060b-ad9d-4ebf-9d9d-50a91677b1ff](.artifacts/records/project__acceptance/rec-83a0060b-ad9d-4ebf-9d9d-50a91677b1ff.md))_

## fix-opencode-shape

### Acceptance
- **fix-opencode-shape**: R12; check; packaging; python3 -m pytest tests/test_installer.py tests/integration/test_temp_home_install.py -q -k "opencode or hooks or temp_home" _(id: [rec-965ea0a8-074d-4189-8f2c-731114177cbc](.artifacts/records/project__acceptance/rec-965ea0a8-074d-4189-8f2c-731114177cbc.md))_

## fix-opencode-shape-agent

### Acceptance
- **fix-opencode-shape-agent**: R13; check; packaging; python3 -m pytest tests/test_agent_generation.py tests/test_installer.py -q -k "opencode" _(id: [rec-bfe782cd-0f27-4337-a426-f20168376f5f](.artifacts/records/project__acceptance/rec-bfe782cd-0f27-4337-a426-f20168376f5f.md))_

## fix-oracle-cli-tests

### Acceptance
- **fix-oracle-cli-tests**: R5; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'cli and (oracle or freeze or assertion_level or amendment)' _(id: [rec-8aba909a-63ea-4152-a144-11f5d525f8d5](.artifacts/records/project__acceptance/rec-8aba909a-63ea-4152-a144-11f5d525f8d5.md))_

## fix-phase-gate-defaults

### Acceptance
- **fix-phase-gate-defaults**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py -q -k phase_gate && python3 -c "import json; from pathlib import Path; b=json.loads(Path('contract/project-design.json').read_text())['phase_gate']['suite']; assert b['mode']=='none' and b.get('command','')==''; a=json.loads(Path('.artifacts/project-design.json').read_text())['phase_gate']['suite']; assert a['mode']=='full' and a['gate']=='advisory' and 'pytest' in a['command']" _(id: [rec-bf2a6f65-d5f0-4838-ad1f-4c257fcf5ce1](.artifacts/records/project__acceptance/rec-bf2a6f65-d5f0-4838-ad1f-4c257fcf5ce1.md))_

## fix-reviewer-selfcontainment

### Acceptance
- **fix-reviewer-selfcontainment**: R1; check; packaging; python3 -m pytest tests/test_skill_portability.py -q _(id: [rec-dd72d8b5-6632-49e4-a7dd-e160e74495d2](.artifacts/records/project__acceptance/rec-dd72d8b5-6632-49e4-a7dd-e160e74495d2.md))_

## fix-reviewer-selfcontainment-canonical

### Acceptance
- **fix-reviewer-selfcontainment-canonical**: R13; check; packaging; python3 -m pytest tests/test_agent_generation.py -q _(id: [rec-32789158-613a-4053-adf2-e25c9055898b](.artifacts/records/project__acceptance/rec-32789158-613a-4053-adf2-e25c9055898b.md))_

## fix-test_dashboard_app

### Acceptance
- **fix-test_dashboard_app**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'running_row_status_shows_its_running_time or footer_has_no_palette or detail_related_panel_lists_related_records' _(id: [rec-d2f35534-584a-4e18-b439-3641ec83969d](.artifacts/records/project__acceptance/rec-d2f35534-584a-4e18-b439-3641ec83969d.md))_

## fix-test_dashboard_journal

### Acceptance
- **fix-test_dashboard_journal**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_journal.py -q -k journal_panel_shows_for_repair_kind _(id: [rec-3df8eb5b-21db-4624-8831-12b8bdc2a294](.artifacts/records/project__acceptance/rec-3df8eb5b-21db-4624-8831-12b8bdc2a294.md))_

## fix-test_discuss_skill

### Acceptance
- **fix-test_discuss_skill**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_discuss_skill.py -q -k plan_phase_opens_a_blocking_plan_review_question _(id: [rec-7a209b57-ff35-4f91-b06b-41f8057aecef](.artifacts/records/project__acceptance/rec-7a209b57-ff35-4f91-b06b-41f8057aecef.md))_

## fix-test_evidence_loop

### Acceptance
- **fix-test_evidence_loop**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_evidence_loop.py -q -k check_run_result_and_method_are_contract_enums _(id: [rec-be712a69-03e1-4ea1-a1e1-b0534ae0b828](.artifacts/records/project__acceptance/rec-be712a69-03e1-4ea1-a1e1-b0534ae0b828.md))_

## fix-test_plan_landing

### Acceptance
- **fix-test_plan_landing**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_plan_landing.py -q -k plan_review_stays_closed_until_landing _(id: [rec-47fbfa19-5038-4851-830d-42a55a72a49e](.artifacts/records/project__acceptance/rec-47fbfa19-5038-4851-830d-42a55a72a49e.md))_

## fix-test_plan_wave_rules

### Acceptance
- **fix-test_plan_wave_rules**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_plan_wave_rules.py -q -k plan_review_stays_closed_until_recipe _(id: [rec-f0ad8c81-df6e-457c-8553-9dd57d03f91e](.artifacts/records/project__acceptance/rec-f0ad8c81-df6e-457c-8553-9dd57d03f91e.md))_

## fix-test_verify_authority

### Acceptance
- **fix-test_verify_authority**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_authority.py -q -k 'skill_close_request_references_check_run_id or close_batch_does_not_emit_check_run_create' _(id: [rec-e09c9aac-f876-43da-9856-41ed79b75404](.artifacts/records/project__acceptance/rec-e09c9aac-f876-43da-9856-41ed79b75404.md))_

## fix-verify-authority-close-batch-import

### Acceptance
- **fix-verify-authority-close-batch-import**: tdd; packaging; uv run --with pytest python -m pytest tests/test_verify_authority.py -q _(id: [rec-a33322af-14f2-44fd-a072-5bc4073fa8a2](.artifacts/records/project__acceptance/rec-a33322af-14f2-44fd-a072-5bc4073fa8a2.md))_

## gates-landing

### Acceptance
- **gates-landing**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_gates.py -q -k 'landing and not (nogr or readonly)' _(id: [rec-79184477-3098-4868-8374-96e8edb0d92c](.artifacts/records/project__acceptance/rec-79184477-3098-4868-8374-96e8edb0d92c.md))_

## gates-landing-failsoft

### Acceptance
- **gates-landing-failsoft**: R10; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_gates.py -q -k 'nogr or no_git or fail' _(id: [rec-03da42d3-f54d-49ba-8ca2-afca1260b398](.artifacts/records/project__acceptance/rec-03da42d3-f54d-49ba-8ca2-afca1260b398.md))_

## gates-landing-readonly

### Acceptance
- **gates-landing-readonly**: R11; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_gates.py -q -k readonly _(id: [rec-3ba5ea87-0663-4f77-9a0e-ef0a6da1fc3e](.artifacts/records/project__acceptance/rec-3ba5ea87-0663-4f77-9a0e-ef0a6da1fc3e.md))_

## gates-model

### Acceptance
- **gates-model**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_gates.py -q -k "gates and (merge or landing_item)" _(id: [rec-72691ffa-0dcd-45d0-a9dc-4cabce493d6e](.artifacts/records/project__acceptance/rec-72691ffa-0dcd-45d0-a9dc-4cabce493d6e.md))_

## gates-model-quiet

### Acceptance
- **gates-model-quiet**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_tasks.py -q -k "gates and quiet" _(id: [rec-bbb94de7-ae26-498b-ae76-2528eb547de3](.artifacts/records/project__acceptance/rec-bbb94de7-ae26-498b-ae76-2528eb547de3.md))_

## gates-status

### Acceptance
- **gates-status**: R8; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests -q -m tmux -k "status and (gates or needs or segment)" _(id: [rec-bec7c314-2052-4053-9d5a-3f78a5db6663](.artifacts/records/project__acceptance/rec-bec7c314-2052-4053-9d5a-3f78a5db6663.md))_

## gates-ui

### Acceptance
- **gates-ui**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "gates and (copy or prompt)" _(id: [rec-6a06a80a-ba89-47c8-8d09-ef1c546ddbb6](.artifacts/records/project__acceptance/rec-6a06a80a-ba89-47c8-8d09-ef1c546ddbb6.md))_

## gates-ui-alert

### Acceptance
- **gates-ui-alert**: R9; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "gates and (alert or bell or message)" _(id: [rec-eafbbe7b-d2e4-4c00-8ade-b19308d28efd](.artifacts/records/project__acceptance/rec-eafbbe7b-d2e4-4c00-8ade-b19308d28efd.md))_

## gates-ui-next

### Acceptance
- **gates-ui-next**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "gates and next" _(id: [rec-f1684acd-c413-4721-bdc5-4b9b28b25793](.artifacts/records/project__acceptance/rec-f1684acd-c413-4721-bdc5-4b9b28b25793.md))_

## gates-vocab

### Acceptance
- **gates-vocab**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'gates and (label or plan_review or action)' _(id: [rec-dda923b2-838f-49de-82f7-3d6b9e8e648d](.artifacts/records/project__acceptance/rec-dda923b2-838f-49de-82f7-3d6b9e8e648d.md))_

## gates-vocab-next

### Acceptance
- **gates-vocab-next**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'gates and next_step' _(id: [rec-3724b87a-e342-4a93-ad2e-32b3dbf21060](.artifacts/records/project__acceptance/rec-3724b87a-e342-4a93-ad2e-32b3dbf21060.md))_

## gates-vocab-prompt

### Acceptance
- **gates-vocab-prompt**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'gates and prompt' _(id: [rec-287530b8-fbf2-465a-b92d-5e699772d5de](.artifacts/records/project__acceptance/rec-287530b8-fbf2-465a-b92d-5e699772d5de.md))_

## gates-vocab-quiet

### Acceptance
- **gates-vocab-quiet**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'gates and quiet' _(id: [rec-0292d7ca-96a5-452c-aa18-2b9dd5029589](.artifacts/records/project__acceptance/rec-0292d7ca-96a5-452c-aa18-2b9dd5029589.md))_

## goal-status-field

### Acceptance
- **goal-status-field**: tdd; workflow-loop; python3 -m pytest tests/test_goal_close.py -q _(id: [rec-1f0b047c-50e6-4c2d-8c91-10a6c7d220e0](.artifacts/records/project__acceptance/rec-1f0b047c-50e6-4c2d-8c91-10a6c7d220e0.md))_

## handoff-by-effort

### Acceptance
- **handoff-by-effort**: tdd; workflow-loop; python3 -m pytest tests/test_phase_position.py -q _(id: [rec-ca16958b-e8a5-4605-a0cd-7bf1a556bd31](.artifacts/records/project__acceptance/rec-ca16958b-e8a5-4605-a0cd-7bf1a556bd31.md))_

## header-chrome

### Acceptance
- **header-chrome**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k "tab_row or tab_labels or number_keys_filter or status_tabs_are_six" _(id: [rec-82ce4065-bcee-43f2-97b2-dfd7a995d323](.artifacts/records/project__acceptance/rec-82ce4065-bcee-43f2-97b2-dfd7a995d323.md))_

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

## install-docs

### Acceptance
- **install-docs**: R15; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q _(id: [rec-b516429d-be99-4476-83d3-64a4b82392c8](.artifacts/records/project__acceptance/rec-b516429d-be99-4476-83d3-64a4b82392c8.md))_

## installer-cli-flags

### Acceptance
- **installer-cli-flags**: R1; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k tty_launches_wizard _(id: [rec-ac532bec-9f8b-47e4-89a3-67a34e6fdb1c](.artifacts/records/project__acceptance/rec-ac532bec-9f8b-47e4-89a3-67a34e6fdb1c.md))_

## installer-cli-flags-decline

### Acceptance
- **installer-cli-flags-decline**: R9; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k decline_writes_nothing _(id: [rec-99ea1141-cec9-436d-a16a-fb87159c4987](.artifacts/records/project__acceptance/rec-99ea1141-cec9-436d-a16a-fb87159c4987.md))_

## installer-cli-flags-dry-run

### Acceptance
- **installer-cli-flags-dry-run**: R16; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k dry_run_skips_confirmation _(id: [rec-fe8c1884-4010-4fd6-9898-a6e397f0c78e](.artifacts/records/project__acceptance/rec-fe8c1884-4010-4fd6-9898-a6e397f0c78e.md))_

## installer-cli-flags-empty

### Acceptance
- **installer-cli-flags-empty**: R14; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k no_detection_no_tty _(id: [rec-1a4bcb36-db8d-495e-891c-d0d6a52337b1](.artifacts/records/project__acceptance/rec-1a4bcb36-db8d-495e-891c-d0d6a52337b1.md))_

## installer-cli-flags-explicit

### Acceptance
- **installer-cli-flags-explicit**: R15; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k explicit_flags _(id: [rec-9d928709-d211-4d2c-b43e-6e2b75c8fbce](.artifacts/records/project__acceptance/rec-9d928709-d211-4d2c-b43e-6e2b75c8fbce.md))_

## installer-cli-flags-interactive

### Acceptance
- **installer-cli-flags-interactive**: R12; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k interactive_flag _(id: [rec-dceca8fc-0c62-44cd-bfcb-ba5992c27387](.artifacts/records/project__acceptance/rec-dceca8fc-0c62-44cd-bfcb-ba5992c27387.md))_

## installer-cli-flags-list

### Acceptance
- **installer-cli-flags-list**: R10; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k list_prints_matrix _(id: [rec-f201f103-557d-4837-8790-f1fd097db867](.artifacts/records/project__acceptance/rec-f201f103-557d-4837-8790-f1fd097db867.md))_

## installer-cli-flags-noninteractive

### Acceptance
- **installer-cli-flags-noninteractive**: R13; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k non_interactive _(id: [rec-8c5c3c0c-b20d-4231-a9ea-f04a94d5edf3](.artifacts/records/project__acceptance/rec-8c5c3c0c-b20d-4231-a9ea-f04a94d5edf3.md))_

## installer-cli-flags-plan

### Acceptance
- **installer-cli-flags-plan**: R8; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k plan_confirmation _(id: [rec-2ec8813c-7593-496c-9319-4d2aeebf7291](.artifacts/records/project__acceptance/rec-2ec8813c-7593-496c-9319-4d2aeebf7291.md))_

## installer-cli-flags-scope

### Acceptance
- **installer-cli-flags-scope**: R11; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k scope_flag _(id: [rec-dd3d65ca-7da3-4855-b94c-5702f51657ff](.artifacts/records/project__acceptance/rec-dd3d65ca-7da3-4855-b94c-5702f51657ff.md))_

## installer-cli-flags-uninstall

### Acceptance
- **installer-cli-flags-uninstall**: R17; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k uninstall_never_prompts _(id: [rec-598804ea-e846-4e2f-a1b5-607993d37076](.artifacts/records/project__acceptance/rec-598804ea-e846-4e2f-a1b5-607993d37076.md))_

## installer-core

### Acceptance
- **installer-core**: R8; check; packaging; python3 -m pytest tests/test_installer.py -q -k flags _(id: [rec-2e2dd2e2-697e-4410-b9fc-959725def582](.artifacts/records/project__acceptance/rec-2e2dd2e2-697e-4410-b9fc-959725def582.md))_

## installer-core-allowlist

### Acceptance
- **installer-core-allowlist**: R14; check; packaging; python3 -m pytest tests/test_installer.py -q -k allowlist _(id: [rec-8a1fddc0-a786-449b-93cc-79f585e6dae6](.artifacts/records/project__acceptance/rec-8a1fddc0-a786-449b-93cc-79f585e6dae6.md))_

## installer-core-idempotent

### Acceptance
- **installer-core-idempotent**: R9; check; packaging; python3 -m pytest tests/test_installer.py -q -k idempotent _(id: [rec-da67502b-5f52-4d4d-a298-122e688b553e](.artifacts/records/project__acceptance/rec-da67502b-5f52-4d4d-a298-122e688b553e.md))_

## installer-detect

### Acceptance
- **installer-detect**: R2; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k detect_hosts _(id: [rec-656ef110-33d3-44a4-8ec5-aa66e39b0613](.artifacts/records/project__acceptance/rec-656ef110-33d3-44a4-8ec5-aa66e39b0613.md))_

## installer-docs

### Acceptance
- **installer-docs**: R18; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q -k "wizard or documented_flags" _(id: [rec-578bd42b-a4b6-4ec3-a758-615a2f3f8655](.artifacts/records/project__acceptance/rec-578bd42b-a4b6-4ec3-a758-615a2f3f8655.md))_

## installer-wizard-primitives

### Acceptance
- **installer-wizard-primitives**: R3; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k parse_host_selection _(id: [rec-6b69d84e-a4e5-441f-b77b-3a5db78dc59b](.artifacts/records/project__acceptance/rec-6b69d84e-a4e5-441f-b77b-3a5db78dc59b.md))_

## installer-wizard-primitives-defaults

### Acceptance
- **installer-wizard-primitives-defaults**: R4; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k blank_selection_uses_detected _(id: [rec-0e40afa2-1cd6-4208-a472-faadf203bc2a](.artifacts/records/project__acceptance/rec-0e40afa2-1cd6-4208-a472-faadf203bc2a.md))_

## installer-wizard-primitives-empty

### Acceptance
- **installer-wizard-primitives-empty**: R5; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k empty_selection_refuses _(id: [rec-ae8e0d92-8d86-477f-83b7-e83232f646b5](.artifacts/records/project__acceptance/rec-ae8e0d92-8d86-477f-83b7-e83232f646b5.md))_

## installer-wizard-primitives-mode

### Acceptance
- **installer-wizard-primitives-mode**: R7; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k prompt_mode _(id: [rec-d0d04499-c3cb-4325-ba4d-ab179cfc9493](.artifacts/records/project__acceptance/rec-d0d04499-c3cb-4325-ba4d-ab179cfc9493.md))_

## installer-wizard-primitives-scope

### Acceptance
- **installer-wizard-primitives-scope**: R6; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k prompt_scope _(id: [rec-2dd0ae61-9b94-4a7f-b513-b128dcc8a9b3](.artifacts/records/project__acceptance/rec-2dd0ae61-9b94-4a7f-b513-b128dcc8a9b3.md))_

## integrate-execute

### Acceptance
- **integrate-execute**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_integrate_rules.py -q _(id: [rec-bea1bd88-8f1c-41ef-8afe-fe7f17154d84](.artifacts/records/project__acceptance/rec-bea1bd88-8f1c-41ef-8afe-fe7f17154d84.md))_

## journal-agent

### Acceptance
- **journal-agent**: R8; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_journal.py tests/test_dashboard_app.py -q -k 'agent or collaps' _(id: [rec-9a1b4afe-d1e3-4cb9-949c-3869f5a0cd76](.artifacts/records/project__acceptance/rec-9a1b4afe-d1e3-4cb9-949c-3869f5a0cd76.md))_

## journal-model

### Acceptance
- **journal-model**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_journal.py -q -k 'journal and (load or order or scope or missing)' _(id: [rec-8c8cd3b5-eac9-461a-b480-58bd3af0f8fe](.artifacts/records/project__acceptance/rec-8c8cd3b5-eac9-461a-b480-58bd3af0f8fe.md))_

## journal-model-kind

### Acceptance
- **journal-model-kind**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'journal and kind' _(id: [rec-ff941da0-90f7-4e86-8d29-fd9593cff4c9](.artifacts/records/project__acceptance/rec-ff941da0-90f7-4e86-8d29-fd9593cff4c9.md))_

## journal-panel

### Acceptance
- **journal-panel**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_journal.py -q -k "panel or kind" _(id: [rec-772b35fe-ecde-4213-8bc8-f56eb55a3517](.artifacts/records/project__acceptance/rec-772b35fe-ecde-4213-8bc8-f56eb55a3517.md))_

## journal-screen

### Acceptance
- **journal-screen**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_journal.py -q -k "screen or filter or detail or pager" _(id: [rec-5ac93260-7e5b-4f29-8ea4-54b09833796f](.artifacts/records/project__acceptance/rec-5ac93260-7e5b-4f29-8ea4-54b09833796f.md))_

## keyboard-focus

### Acceptance
- **keyboard-focus**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-97f2e49d-f874-4969-929c-d6c37a1ec61b](.artifacts/records/project__acceptance/rec-97f2e49d-f874-4969-929c-d6c37a1ec61b.md))_

### Finding
- **keyboard-focus**: Nothing focused the task table; the effort tab strip kept focus, so arrows never moved the cursor and enter always opened row 0; Real-store probe and 7 red keys-only tests before 2d1a3be; all pass after; A keys-only test fails to move or open a task after 2d1a3be; none _(id: [rec-60d1962e-aeb0-4972-8002-f424c61f615a](.artifacts/records/project__finding/rec-60d1962e-aeb0-4972-8002-f424c61f615a.md))_

## label-view-fields

### Acceptance
- **label-view-fields**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q _(id: [rec-0a970468-5d80-49a0-bf80-d5481a65814b](.artifacts/records/project__acceptance/rec-0a970468-5d80-49a0-bf80-d5481a65814b.md))_

## loop-scenarios

### Acceptance
- **loop-scenarios**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_evidence_loop.py -q _(id: [rec-17e1c5a7-2e32-40d4-9df1-6d7d4f8bb488](.artifacts/records/project__acceptance/rec-17e1c5a7-2e32-40d4-9df1-6d7d4f8bb488.md))_

## matrix-model

### Acceptance
- **matrix-model**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_requirement.py -q -k matrix _(id: [rec-65e37e8b-25f6-4953-a8b2-9a0c0fddb74d](.artifacts/records/project__acceptance/rec-65e37e8b-25f6-4953-a8b2-9a0c0fddb74d.md))_

## matrix-ui

### Acceptance
- **matrix-ui**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py -q -k matrix _(id: [rec-e60394f4-9d3c-494c-9b2c-e69db0de52ee](.artifacts/records/project__acceptance/rec-e60394f4-9d3c-494c-9b2c-e69db0de52ee.md))_

## matrix-ui-strip

### Acceptance
- **matrix-ui-strip**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py tests/test_dashboard_app.py -q -k "strip or glyph" _(id: [rec-2803f0e2-8159-46ac-90b0-d9cec7762a4a](.artifacts/records/project__acceptance/rec-2803f0e2-8159-46ac-90b0-d9cec7762a4a.md))_

## milestone-nav

### Position
- **milestone-nav**: milestone-nav in_progress; materializing work-items for plan review; phase _(id: [rec-d0249c73-7e7d-4392-bd3f-da5661001d0f](.artifacts/records/project__current-position/rec-d0249c73-7e7d-4392-bd3f-da5661001d0f.md))_

## milestone-nav-helpers

### Work
- **milestone-nav-helpers**: Milestone grouping and expand helpers; milestone-nav; deliver; dashboard _(id: [rec-6d3e248d-13a3-46fd-b113-d36c911b2d3d](.artifacts/records/project__work-item/rec-6d3e248d-13a3-46fd-b113-d36c911b2d3d.md))_

### Acceptance
- **milestone-nav-helpers**: R3; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestones.test.ts -t R3 _(id: [rec-2e55a392-c6be-4932-bd50-fb2d23b83fbc](.artifacts/records/project__acceptance/rec-2e55a392-c6be-4932-bd50-fb2d23b83fbc.md))_

## milestone-nav-helpers-r7

### Acceptance
- **milestone-nav-helpers-r7**: R7; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestones.test.ts -t R7 _(id: [rec-cec6c732-e285-4853-a8e7-01f94ee49425](.artifacts/records/project__acceptance/rec-cec6c732-e285-4853-a8e7-01f94ee49425.md))_

## milestone-nav-helpers-r8

### Acceptance
- **milestone-nav-helpers-r8**: R8; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestones.test.ts -t R8 _(id: [rec-b2803a64-6aa8-4749-b1ef-44d099372bb4](.artifacts/records/project__acceptance/rec-b2803a64-6aa8-4749-b1ef-44d099372bb4.md))_

## milestone-nav-ui

### Work
- **milestone-nav-ui**: Phases block UI in App; milestone-nav; deliver; dashboard _(id: [rec-a18ab51a-b527-4d5b-b647-6914c61aa744](.artifacts/records/project__work-item/rec-a18ab51a-b527-4d5b-b647-6914c61aa744.md))_

### Acceptance
- **milestone-nav-ui**: R1; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestoneNav.test.ts -t R1 _(id: [rec-0ba73bbb-99ad-44ef-8696-3cad46aa6fab](.artifacts/records/project__acceptance/rec-0ba73bbb-99ad-44ef-8696-3cad46aa6fab.md))_

## milestone-nav-ui-r10

### Acceptance
- **milestone-nav-ui-r10**: R10; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestoneNav.test.ts -t R10 _(id: [rec-863722d6-7ee4-430b-93a9-32919d31fcdc](.artifacts/records/project__acceptance/rec-863722d6-7ee4-430b-93a9-32919d31fcdc.md))_

## milestone-nav-ui-r2

### Acceptance
- **milestone-nav-ui-r2**: R2; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestoneNav.test.ts -t R2 _(id: [rec-85702607-79f3-4c96-b65d-ce0c8c20f1e1](.artifacts/records/project__acceptance/rec-85702607-79f3-4c96-b65d-ce0c8c20f1e1.md))_

## milestone-nav-ui-r4

### Acceptance
- **milestone-nav-ui-r4**: R4; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestoneNav.test.ts -t R4 _(id: [rec-ce00f555-db82-4549-a6c8-4598b2274f57](.artifacts/records/project__acceptance/rec-ce00f555-db82-4549-a6c8-4598b2274f57.md))_

## milestone-nav-ui-r5

### Acceptance
- **milestone-nav-ui-r5**: R5; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestoneNav.test.ts -t R5 _(id: [rec-cbca727e-806c-4ace-b5f0-19afd144744d](.artifacts/records/project__acceptance/rec-cbca727e-806c-4ace-b5f0-19afd144744d.md))_

## milestone-nav-ui-r6

### Acceptance
- **milestone-nav-ui-r6**: R6; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestoneNav.test.ts -t R6 _(id: [rec-a9f06f0b-ba41-4c2a-88c0-93d96ded3341](.artifacts/records/project__acceptance/rec-a9f06f0b-ba41-4c2a-88c0-93d96ded3341.md))_

## milestone-nav-ui-r9

### Acceptance
- **milestone-nav-ui-r9**: R9; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestoneNav.test.ts -t R9 _(id: [rec-5f055263-a2ec-4551-9943-004890bb130e](.artifacts/records/project__acceptance/rec-5f055263-a2ec-4551-9943-004890bb130e.md))_

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

## native-adapters

### Acceptance
- **native-adapters**: R10; check; packaging; python3 -m pytest tests/test_installer.py -q -k native _(id: [rec-9fab2257-d40f-49c2-88ac-c560a964d280](.artifacts/records/project__acceptance/rec-9fab2257-d40f-49c2-88ac-c560a964d280.md))_

## native-adapters-agent

### Acceptance
- **native-adapters-agent**: R13; check; packaging; python3 -m pytest tests/test_agent_generation.py -q _(id: [rec-81b797c0-4d67-4287-987f-a70f6d6d7b4a](.artifacts/records/project__acceptance/rec-81b797c0-4d67-4287-987f-a70f6d6d7b4a.md))_

## native-adapters-hooks

### Acceptance
- **native-adapters-hooks**: R12; check; packaging; python3 -m pytest tests/test_installer.py -q -k hooks _(id: [rec-1239637e-5651-4066-bcbb-f6078a6deb41](.artifacts/records/project__acceptance/rec-1239637e-5651-4066-bcbb-f6078a6deb41.md))_

## native-adapters-tail

### Acceptance
- **native-adapters-tail**: R11; check; packaging; python3 -m pytest tests/test_installer.py -q -k tail _(id: [rec-ec5854f8-474a-4aee-b6a1-5033611e7cde](.artifacts/records/project__acceptance/rec-ec5854f8-474a-4aee-b6a1-5033611e7cde.md))_

## needs-you-list

### Acceptance
- **needs-you-list**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k needs_you _(id: [rec-7c8645dc-e818-4d9d-b2d1-807437c46a90](.artifacts/records/project__acceptance/rec-7c8645dc-e818-4d9d-b2d1-807437c46a90.md))_

## needs-you-records

### Acceptance
- **needs-you-records**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k needs _(id: [rec-79256814-feaf-46b4-b5da-3c97ec0838c0](.artifacts/records/project__acceptance/rec-79256814-feaf-46b4-b5da-3c97ec0838c0.md))_

## needs-you-tab-removal

### Acceptance
- **needs-you-tab-removal**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_view.py -q _(id: [rec-e781be72-47b4-4705-8bb4-82f57f1391ef](.artifacts/records/project__acceptance/rec-e781be72-47b4-4705-8bb4-82f57f1391ef.md))_

## oracle-assertion-red

### Acceptance
- **oracle-assertion-red**: R2; tdd; workflow-loop; python3 -m pytest tests/test_oracle_red.py tests/test_affidavit_check.py -q -k 'failing_node or assertion_level or oracle_red' _(id: [rec-e8dc7437-e410-4b96-81c3-62f7914a9a22](.artifacts/records/project__acceptance/rec-e8dc7437-e410-4b96-81c3-62f7914a9a22.md))_

## oracle-contract

### Acceptance
- **oracle-contract**: R3; check; workflow-loop; python3 -c "import json;from pathlib import Path;d=json.loads(Path('contract/project-design.json').read_text());types={t['name']:t for t in d['records']};a=types['acceptance'];assert 'test_ids' in a['payload'] and 'oracle_hashes' in a['payload'];assert 'test_ids' in a.get('optional_payload',[]) and 'oracle_hashes' in a.get('optional_payload',[]);am=types['oracle-amendment'];assert set(am['required_sections'])>={'Reason','Change'};assert 'status' in am['payload'];assert set(am.get('payload_enum',{}).get('status',[]))>={'requested','approved','rejected'}" _(id: [rec-753fcb78-34c3-4d72-8da8-948d99fa75f2](.artifacts/records/project__acceptance/rec-753fcb78-34c3-4d72-8da8-948d99fa75f2.md))_

## oracle-contract-amendment-type

### Acceptance
- **oracle-contract-amendment-type**: R4; check; workflow-loop; python3 -c "import json;from pathlib import Path;d=json.loads(Path('contract/project-design.json').read_text());am=next(t for t in d['records'] if t['name']=='oracle-amendment');assert am['payload_references'].get('acceptance')=='project:acceptance';assert 'old_hashes' in am['payload'] and 'new_hashes' in am['payload']" _(id: [rec-5cc71e22-8776-4d3e-838c-a4a08812d3cd](.artifacts/records/project__acceptance/rec-5cc71e22-8776-4d3e-838c-a4a08812d3cd.md))_

## oracle-freeze-close

### Acceptance
- **oracle-freeze-close**: R5; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'oracle or freeze or assertion_level' _(id: [rec-84698b95-b79b-442a-9166-f2e168797d33](.artifacts/records/project__acceptance/rec-84698b95-b79b-442a-9166-f2e168797d33.md))_

## oracle-freeze-close-hashes

### Acceptance
- **oracle-freeze-close-hashes**: R3; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'oracle_hash or freeze_hash or amendment' _(id: [rec-08e82b2b-f39f-4c7c-ac4e-b0c758b7f337](.artifacts/records/project__acceptance/rec-08e82b2b-f39f-4c7c-ac4e-b0c758b7f337.md))_

## oracle-skills

### Acceptance
- **oracle-skills**: R7; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q _(id: [rec-f9ef85f0-efd5-4a31-8262-9eb7d6858bee](.artifacts/records/project__acceptance/rec-f9ef85f0-efd5-4a31-8262-9eb7d6858bee.md))_

## oracle-skills-execute-amend

### Acceptance
- **oracle-skills-execute-amend**: R4; check; workflow-loop; rg -n "oracle-amendment|frozen oracle|oracle_hashes" skills/execute-phase/SKILL.md skills/verify-work/SKILL.md _(id: [rec-53cde3fc-6823-4f72-a863-861b55a3bf11](.artifacts/records/project__acceptance/rec-53cde3fc-6823-4f72-a863-861b55a3bf11.md))_

## oracle-skills-mechanical-verify

### Acceptance
- **oracle-skills-mechanical-verify**: R6; check; workflow-loop; rg -n "mechanical|assertion-level|oracle-backed" skills/verify-work/SKILL.md _(id: [rec-d3fde647-9d4d-468a-a9fc-7635ac187eeb](.artifacts/records/project__acceptance/rec-d3fde647-9d4d-468a-a9fc-7635ac187eeb.md))_

## oracle-skills-plan-author

### Acceptance
- **oracle-skills-plan-author**: R1; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q -k 'oracle or freeze or plan_phase' _(id: [rec-0ecbff55-619a-4c5a-ad17-a582ef26dc85](.artifacts/records/project__acceptance/rec-0ecbff55-619a-4c5a-ad17-a582ef26dc85.md))_

## package-install

### Acceptance
- **package-install**: check; dashboard; d=$(mktemp -d) && bash scripts/sync-plugin.sh "$d/p" && test -d "$d/p/dashboard" && "$d/p/dashboard/bin/dashboard" --once _(id: [rec-0379e3d0-879a-4bc5-982a-7ed054623149](.artifacts/records/project__acceptance/rec-0379e3d0-879a-4bc5-982a-7ed054623149.md))_

## package-install-docs

### Acceptance
- **package-install-docs**: check; dashboard; ! grep -nE 'scripts/(dashboard|tmux-dashboard)' README.md dashboard/tmux.conf _(id: [rec-67e721d5-5b8f-482f-b2d7-f9f25c8ec7e3](.artifacts/records/project__acceptance/rec-67e721d5-5b8f-482f-b2d7-f9f25c8ec7e3.md))_

## package-move

### Acceptance
- **package-move**: tdd; dashboard; test ! -e scripts/dashboard_app.py && test ! -e scripts/dashboard_model.py && test ! -e scripts/artifact_store.py && uv run --with pytest --with textual pytest tests/test_dashboard_app.py tests/test_dashboard_model.py tests/test_dashboard_launcher.py tests/test_dashboard_status.py tests/test_dashboard_view.py tests/test_dashboard_integration.py _(id: [rec-976f8b89-c8c7-4ced-855d-c8c5b3c6c2fb](.artifacts/records/project__acceptance/rec-976f8b89-c8c7-4ced-855d-c8c5b3c6c2fb.md))_

## packaging

### Position
- **packaging**: installer-wizard done at 97054004; symlink settings fix 04737710; OpenCode V2 plugin fix with real-server integration 45921326; packaging backlog: version-compat-check, version-tag-releases; effort _(id: [rec-3095e807-4488-4af4-b3e9-19b41caf4de7](.artifacts/records/project__current-position/rec-3095e807-4488-4af4-b3e9-19b41caf4de7.md))_

## pane-width-stable

### Acceptance
- **pane-width-stable**: tdd; dashboard; for i in $(seq 20); do uv run -q --with textual --with pytest --with pytest-xdist python -m pytest tests/test_dashboard_app.py -q -n 4 -p no:cacheprovider || break; done _(id: [rec-ef569598-f20a-4623-ba96-4f0c32edf9f1](.artifacts/records/project__acceptance/rec-ef569598-f20a-4623-ba96-4f0c32edf9f1.md))_

## phase-detail-tasks

### Acceptance
- **phase-detail-tasks**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k phase_task _(id: [rec-2356a60d-0eda-499f-b3ab-ee4746d6aa45](.artifacts/records/project__acceptance/rec-2356a60d-0eda-499f-b3ab-ee4746d6aa45.md))_

## phase-gate-contract

### Acceptance
- **phase-gate-contract**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py -q -k phase_gate _(id: [rec-6e293e6f-8e8d-48c3-9344-25b4e7b8e35d](.artifacts/records/project__acceptance/rec-6e293e6f-8e8d-48c3-9344-25b4e7b8e35d.md))_

## phase-gate-contract-repo

### Acceptance
- **phase-gate-contract-repo**: R6; check; workflow-loop; python3 -c "import json; from pathlib import Path; b=json.loads(Path('contract/project-design.json').read_text())['phase_gate']['suite']; assert b['mode']=='none'; s=json.loads(Path('.artifacts/project-design.json').read_text())['phase_gate']['suite']; assert s['mode']=='full' and s['gate']=='advisory' and 'pytest' in s['command']" _(id: [rec-a77cfc8e-569f-4671-b7c7-dc7a2481c024](.artifacts/records/project__acceptance/rec-a77cfc8e-569f-4671-b7c7-dc7a2481c024.md))_

## phase-model-selection

### Acceptance
- **phase-model-selection**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'default or selection' _(id: [rec-02c57648-41cf-4d1c-858e-45109cf1514f](.artifacts/records/project__acceptance/rec-02c57648-41cf-4d1c-858e-45109cf1514f.md))_

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

## phase-position-skills

### Acceptance
- **phase-position-skills**: tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_phase_position.py -q _(id: [rec-9f326a41-7f0f-4d28-89c6-069154ad5a65](.artifacts/records/project__acceptance/rec-9f326a41-7f0f-4d28-89c6-069154ad5a65.md))_

## phase-proof-packet

### Position
- **phase-proof-packet**: phase-proof-packet done; proof packet + Proof tab landed on main; phase _(id: [rec-208d6247-9c02-44fa-af8a-8739274184b6](.artifacts/records/project__current-position/rec-208d6247-9c02-44fa-af8a-8739274184b6.md))_

## phase-reviewer

### Position
- **phase-reviewer**: phase-reviewer done; next up: tiered-verification; phase _(id: [rec-db17b780-4178-4359-b4ee-119fb52aba18](.artifacts/records/project__current-position/rec-db17b780-4178-4359-b4ee-119fb52aba18.md))_

## phase-sections

### Acceptance
- **phase-sections**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q _(id: [rec-611e26b5-b891-4e71-8951-3ebf07ecc715](.artifacts/records/project__acceptance/rec-611e26b5-b891-4e71-8951-3ebf07ecc715.md))_

## phase-selector-ui

### Acceptance
- **phase-selector-ui**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'selector or stepper' _(id: [rec-39f567da-de81-428f-91b0-131cded1ec16](.artifacts/records/project__acceptance/rec-39f567da-de81-428f-91b0-131cded1ec16.md))_

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

## phase-table-scope-sections

### Acceptance
- **phase-table-scope-sections**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_tasks.py -q -k 'section' _(id: [rec-36bb77d4-81a1-4fcd-b04a-e0b22bf49f14](.artifacts/records/project__acceptance/rec-36bb77d4-81a1-4fcd-b04a-e0b22bf49f14.md))_

## plan-landing-rules

### Acceptance
- **plan-landing-rules**: tdd; workflow-loop; python3 -m pytest tests/test_plan_landing.py -q _(id: [rec-9f4b54cc-334e-4b5c-92fa-df0b713d662e](.artifacts/records/project__acceptance/rec-9f4b54cc-334e-4b5c-92fa-df0b713d662e.md))_

## plan-wave-rules

### Acceptance
- **plan-wave-rules**: tdd; workflow-loop; python3 -m pytest tests/test_plan_wave_rules.py -q _(id: [rec-b1c39c5f-6758-426d-bdcf-0ff6c57bcbc5](.artifacts/records/project__acceptance/rec-b1c39c5f-6758-426d-bdcf-0ff6c57bcbc5.md))_

## portable-skill-refs

### Acceptance
- **portable-skill-refs**: R1; check; packaging; python3 -m pytest tests/test_skill_portability.py -q _(id: [rec-928c5ad9-2a76-42cc-8403-9947807d381f](.artifacts/records/project__acceptance/rec-928c5ad9-2a76-42cc-8403-9947807d381f.md))_

## portable-skill-refs-drift

### Acceptance
- **portable-skill-refs-drift**: R3; check; packaging; python3 scripts/build_skills.py --check && python3 -m pytest tests/test_skill_portability.py -q -k drift _(id: [rec-415c1cc3-204c-4f52-9aca-5482488ef019](.artifacts/records/project__acceptance/rec-415c1cc3-204c-4f52-9aca-5482488ef019.md))_

## portable-skill-refs-frontmatter

### Acceptance
- **portable-skill-refs-frontmatter**: R4; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k frontmatter _(id: [rec-3c605b52-67e1-444f-8b8a-4361446b4ba7](.artifacts/records/project__acceptance/rec-3c605b52-67e1-444f-8b8a-4361446b4ba7.md))_

## portable-skill-refs-generated

### Acceptance
- **portable-skill-refs-generated**: R2; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k generated _(id: [rec-e3a55126-ff30-4309-aa76-7a41043af0c5](.artifacts/records/project__acceptance/rec-e3a55126-ff30-4309-aa76-7a41043af0c5.md))_

## portable-skill-refs-paths

### Acceptance
- **portable-skill-refs-paths**: R6; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k paths _(id: [rec-26a7bcc5-61dc-4f46-ba57-7e01c963e3a7](.artifacts/records/project__acceptance/rec-26a7bcc5-61dc-4f46-ba57-7e01c963e3a7.md))_

## proof-dashboard-ui

### Acceptance
- **proof-dashboard-ui**: R7; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_proof_dashboard.py -q _(id: [rec-cfd617ac-aa2f-42a8-9d87-4d37c0bb0cf8](.artifacts/records/project__acceptance/rec-cfd617ac-aa2f-42a8-9d87-4d37c0bb0cf8.md))_

## proof-packet-contract

### Acceptance
- **proof-packet-contract**: R1; check; workflow-loop; python3 -m pytest tests/test_proof_packet_contract.py::test_proof_packet_type_and_sections -q _(id: [rec-c0e494f2-6c30-4453-8e61-78a3d2dee8df](.artifacts/records/project__acceptance/rec-c0e494f2-6c30-4453-8e61-78a3d2dee8df.md))_

## proof-packet-contract-handoff

### Acceptance
- **proof-packet-contract-handoff**: R2; check; workflow-loop; python3 -m pytest tests/test_proof_packet_contract.py::test_handoff_latest_proof_role -q _(id: [rec-5805f781-09e8-420f-b329-e5f8cf095e1e](.artifacts/records/project__acceptance/rec-5805f781-09e8-420f-b329-e5f8cf095e1e.md))_

## proof-skills-execute

### Acceptance
- **proof-skills-execute**: R4; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_assembles_proof_packet -q _(id: [rec-54e6aa7d-586f-48a3-851d-afdbffe6d4ec](.artifacts/records/project__acceptance/rec-54e6aa7d-586f-48a3-851d-afdbffe6d4ec.md))_

## proof-skills-execute-aff

### Acceptance
- **proof-skills-execute-aff**: R5; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_aff_hooks_and_incidental -q _(id: [rec-3e1bd988-4027-4da3-9631-38e7fa019995](.artifacts/records/project__acceptance/rec-3e1bd988-4027-4da3-9631-38e7fa019995.md))_

## proof-skills-execute-incidental

### Acceptance
- **proof-skills-execute-incidental**: R6; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_aff_hooks_and_incidental -q _(id: [rec-9184b85e-a6e2-44d6-b2de-222c16b71cc0](.artifacts/records/project__acceptance/rec-9184b85e-a6e2-44d6-b2de-222c16b71cc0.md))_

## proof-skills-settle-plan

### Acceptance
- **proof-skills-settle-plan**: R3; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_settle_and_plan_require_proof_section -q _(id: [rec-dd5f9851-b6af-4f8d-8123-158e5aa3be86](.artifacts/records/project__acceptance/rec-dd5f9851-b6af-4f8d-8123-158e5aa3be86.md))_

## readme-lifecycle

### Acceptance
- **readme-lifecycle**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_readme_lifecycle.py -q _(id: [rec-61e95277-ed36-4e3f-9307-df5f8e946151](.artifacts/records/project__acceptance/rec-61e95277-ed36-4e3f-9307-df5f8e946151.md))_

## readme-quickstart

### Acceptance
- **readme-quickstart**: check; dashboard; grep -q '^## Quick start' README.md && grep -q "@plugin 'andrewy1n/se-workflow'" README.md && grep -q 'run-shell' README.md && ! grep -nE 'dashboard/tmux\.conf|SE_WORKFLOW_DASHBOARD|source-file' README.md _(id: [rec-757d4417-3c33-4df0-a29e-03c1c09bb8ad](.artifacts/records/project__acceptance/rec-757d4417-3c33-4df0-a29e-03c1c09bb8ad.md))_

## recency-selection

### Acceptance
- **recency-selection**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q _(id: [rec-d854ca7d-767b-4729-92e1-18ef8853d92c](.artifacts/records/project__acceptance/rec-d854ca7d-767b-4729-92e1-18ef8853d92c.md))_

## rename-agent-affidavit

### Position
- **rename-agent-affidavit**: rename-agent-affidavit done; merged to main at 3c8a5c2; GitHub andrewy1n/affidavit; plugins synced; AA docs updated; phase _(id: [rec-171be925-f0aa-4465-99bf-ea74cc7dffb2](.artifacts/records/project__current-position/rec-171be925-f0aa-4465-99bf-ea74cc7dffb2.md))_

## rename-identity-surfaces

### Acceptance
- **rename-identity-surfaces**: R1; check; packaging; python3 scripts/check_affidavit_plugin_names.py _(id: [rec-57328b34-853e-4ba0-978d-19d5dc67a396](.artifacts/records/project__acceptance/rec-57328b34-853e-4ba0-978d-19d5dc67a396.md))_

## rename-identity-surfaces-contract

### Acceptance
- **rename-identity-surfaces-contract**: R3; check; packaging; python3 scripts/check_affidavit_contract_project.py && grep -q affidavit skills/ensure-store.md && ! grep -E 'other than .se-workflow|project. is .se-workflow' skills/ensure-store.md _(id: [rec-037fac04-00c1-4097-9c17-5d49622584df](.artifacts/records/project__acceptance/rec-037fac04-00c1-4097-9c17-5d49622584df.md))_

## rename-package-cli

### Acceptance
- **rename-package-cli**: R2; tdd; packaging; test -x bin/aff && ! test -e bin/se-workflow && bin/aff check --help >/dev/null && bin/aff close-batch --help >/dev/null && uv run --with pytest python -m pytest tests/test_aa_resolve.py tests/test_close_batch.py -q --collect-only >/dev/null && python3 -c "import importlib.util as u; import affidavit, affidavit.cli; assert u.find_spec('affidavit'); assert u.find_spec('se_workflow') is None" _(id: [rec-fa93899c-8721-4377-99f1-a99a14cbf1a2](.artifacts/records/project__acceptance/rec-fa93899c-8721-4377-99f1-a99a14cbf1a2.md))_

## rename-tests

### Acceptance
- **rename-tests**: R5; tdd; packaging; uv run --with pytest python -m pytest tests/test_aa_resolve.py tests/test_close_batch.py tests/test_skill_contract_consistency.py -q && grep -q affidavit scripts/sync-plugin.sh && ! grep -E 'se-workflow|se_workflow' scripts/sync-plugin.sh _(id: [rec-322f6c86-d91a-4ab6-95bb-82a9bbcd348f](.artifacts/records/project__acceptance/rec-322f6c86-d91a-4ab6-95bb-82a9bbcd348f.md))_

## requirement-links

### Acceptance
- **requirement-links**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and link and task' _(id: [rec-ceea1aa8-71eb-4308-925b-d17ce2d31253](.artifacts/records/project__acceptance/rec-ceea1aa8-71eb-4308-925b-d17ce2d31253.md))_

## requirement-links-needs

### Acceptance
- **requirement-links-needs**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and link and needs' _(id: [rec-b6a074dd-62de-4eea-85d1-100bd193b1bc](.artifacts/records/project__acceptance/rec-b6a074dd-62de-4eea-85d1-100bd193b1bc.md))_

## requirement-links-phase

### Acceptance
- **requirement-links-phase**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'evidence and link and phase' _(id: [rec-61730bf8-c287-4b79-a619-f974d0bef93d](.artifacts/records/project__acceptance/rec-61730bf8-c287-4b79-a619-f974d0bef93d.md))_

## requirement-screen

### Acceptance
- **requirement-screen**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_requirement.py -q _(id: [rec-fe7cbd3d-6b76-4bf1-b258-e4fa9361b6d8](.artifacts/records/project__acceptance/rec-fe7cbd3d-6b76-4bf1-b258-e4fa9361b6d8.md))_

## retry-dashboard

### Acceptance
- **retry-dashboard**: R8; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k "attempt_row or attempt_budget or attempt_snapshot or attempt_title" _(id: [rec-7bd7b9f7-ab98-40b6-9831-a074659941f7](.artifacts/records/project__acceptance/rec-7bd7b9f7-ab98-40b6-9831-a074659941f7.md))_

## retry-engine

### Acceptance
- **retry-engine**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_retry_loop.py -q _(id: [rec-09626673-9f46-4904-8541-2d2d5ecaf514](.artifacts/records/project__acceptance/rec-09626673-9f46-4904-8541-2d2d5ecaf514.md))_

## retry-engine-contract

### Acceptance
- **retry-engine-contract**: R3; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_contract_self_consistency.py -q _(id: [rec-a40b0635-99ac-481f-a4fb-855a830b6fa1](.artifacts/records/project__acceptance/rec-a40b0635-99ac-481f-a4fb-855a830b6fa1.md))_

## retry-web-write-api

### Finding
- **retry-web-write-api**: R24 oracle asserts predecessor signed_by after correct-based sign; store puts signed_by on correction successor; test_r24_signer fail; direct dismiss_item reproduces; 8/9 other write tests pass at 4fc8cc27; oracle amended and R24 passes, or human withdrawn the claim; none _(id: [rec-39c0935d-669a-4825-a3a1-1450d9e4a1cc](.artifacts/records/project__finding/rec-39c0935d-669a-4825-a3a1-1450d9e4a1cc.md))_

## review-approval-constraints-spec-gap

### Finding
- **review-approval-constraints-spec-gap**: spec-gap on approval-constraints: exclusive human-gate constraint wording conflicts with preserved backlog promote/dismiss writes; dashboard-human-gate-writes says only Needs-you clears; backlog.py still supersedes with @current; constraint statement names backlog promote/dismiss as allowed or exclusivity is clarified without contradicting Non-goals, and reviewer re-run passes; none _(id: [rec-d3047fa6-a5cf-4f79-8d70-3a32f5590f8f](.artifacts/records/project__finding/rec-d3047fa6-a5cf-4f79-8d70-3a32f5590f8f.md))_

## review-cli-package-behavior-bug

### Finding
- **review-cli-package-behavior-bug**: behavior-bug on cli-package: the installed orchestra console script eagerly imports affidavit.oracle_red, so it fails with a clean HOME and no affidavit checkout, breaking R5/R7 for every subcommand; Reviewer observed orchestra/cli.py:11 importing orchestra.close_batch, whose module import at close_batch.py:49 imports affidavit.oracle_red; pyproject declares no dependency; with HOME empty and no aff on PATH, python3 -m orchestra.cli --help raises ModuleNotFoundError: No module named 'affidavit'; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-60cd2a12-581c-4cd5-8864-212182d561e4](.artifacts/records/project__finding/rec-60cd2a12-581c-4cd5-8864-212182d561e4.md))_

## review-cli-package-invariant-violation

### Finding
- **review-cli-package-invariant-violation**: invariant-violation on cli-package: skills still call orchestra.reviewer, orchestra.suite, and orchestra.aa module APIs that the CLI does not expose, contradicting the 'CLI is the only runtime surface' invariant; Reviewer observed skills/execute-phase/SKILL.md:418,501,514,377,958 and shared/ensure-store.md:13,17 naming importable module APIs; orchestra/cli.py exposes only check, close-batch, install, contract, project-field, and sessions; fix lands and reviewer re-run passes, or human clears; human _(id: [rec-615efcde-152c-4962-8a78-f8c4253e298b](.artifacts/records/project__finding/rec-615efcde-152c-4962-8a78-f8c4253e298b.md))_

## review-criterion-views-minor

### Finding
- **review-criterion-views-minor**: missing-test minor: criterion_optional_in_contract omits view requires_payload; R4 view change landed; named test checks optional_payload only; test asserts brief/plan/verification roles omit criterion; none _(id: [rec-e0c7fb0b-8c5e-4768-a793-1eb732c512d1](.artifacts/records/project__finding/rec-e0c7fb0b-8c5e-4768-a793-1eb732c512d1.md))_

## review-install-docs-spec-gap

### Finding
- **review-install-docs-spec-gap**: spec-gap on install-docs: the pre-existing Agent Skills-host README section still tells users to copy five skills and keep shared docs two levels above, conflicting with the generated per-skill references payload; Reviewer observed README around line 110 still lists init/plan-phase/execute-phase/verify-work/engage and says to keep skills/kinds-and-focus.md and skills/ensure-store.md two levels above each SKILL.md, omitting settle-phase and analyze-sessions; fix lands and reviewer re-run passes, or human clears; none _(id: [rec-e4f93753-3b86-4eb3-ba76-d2d630a1edc3](.artifacts/records/project__finding/rec-e4f93753-3b86-4eb3-ba76-d2d630a1edc3.md))_

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

## reviewer-execute

### Acceptance
- **reviewer-execute**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k "execute or parent_write or review_check" _(id: [rec-10c147f9-1f69-4746-8444-72e2fe310165](.artifacts/records/project__acceptance/rec-10c147f9-1f69-4746-8444-72e2fe310165.md))_

## reviewer-execute-fix

### Acceptance
- **reviewer-execute-fix**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k "fix_task or rerun or budget" _(id: [rec-7d0c4862-c22a-4fd3-bcae-3679c065e527](.artifacts/records/project__acceptance/rec-7d0c4862-c22a-4fd3-bcae-3679c065e527.md))_

## reviewer-execute-gate

### Acceptance
- **reviewer-execute-gate**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k gate _(id: [rec-4fe99528-e397-4b36-b07f-f93d2b1291f9](.artifacts/records/project__acceptance/rec-4fe99528-e397-4b36-b07f-f93d2b1291f9.md))_

## reviewer-execute-integration

### Acceptance
- **reviewer-execute-integration**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py tests/test_skill_contract_consistency.py -q -k "integration or test_skill_contract" _(id: [rec-87416dee-0be6-4e6a-bf05-d567fac451bf](.artifacts/records/project__acceptance/rec-87416dee-0be6-4e6a-bf05-d567fac451bf.md))_

## rj-join

### Acceptance
- **rj-join**: tdd; session-analysis; python3 -m pytest -q tests/test_record_join.py _(id: [rec-fa22cc2f-06e1-491e-a277-9c9ab01fa21e](.artifacts/records/project__acceptance/rec-fa22cc2f-06e1-491e-a277-9c9ab01fa21e.md))_

## rj-record-reader

### Acceptance
- **rj-record-reader**: tdd; session-analysis; python3 -m pytest -q tests/test_record_reader.py _(id: [rec-f89ab522-1803-4881-b257-f9a885c2d0de](.artifacts/records/project__acceptance/rec-f89ab522-1803-4881-b257-f9a885c2d0de.md))_

## rj-report-records

### Acceptance
- **rj-report-records**: tdd; session-analysis; python3 -m pytest -q tests/test_session_report.py _(id: [rec-193dfd71-f09c-43b5-95db-e685a4a80e4f](.artifacts/records/project__acceptance/rec-193dfd71-f09c-43b5-95db-e685a4a80e4f.md))_

### Finding
- **rj-report-records**: The project-plus-time-window join leaves 70% of attached records ambiguous (386 of 553), so per-session record counts are unreliable for overlapping sessions.; Real run of session_report.py --records over 247 sessions: 8 sessions have records, 553 records attach, 386 attach to two or more sessions.; Records carry a session id, or sessions get narrower activity windows that remove the overlap.; none _(id: [rec-b8213c07-3cf9-4b56-a2a5-e9f56bd93f78](.artifacts/records/project__finding/rec-b8213c07-3cf9-4b56-a2a5-e9f56bd93f78.md))_

## route-through-discuss

### Acceptance
- **route-through-discuss**: tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_discuss_skill.py -q _(id: [rec-aac400ee-30c6-4fd2-a3ba-9fbd756f740a](.artifacts/records/project__acceptance/rec-aac400ee-30c6-4fd2-a3ba-9fbd756f740a.md))_

## sa-code-in-plugin-repo

### Constraint
- **sa-code-in-plugin-repo**: The code lives in this plugin repo under scripts/ and skills/.; session-analysis; session-analysis _(id: [rec-1c7e8113-66b4-44e2-9183-b441364268a4](.artifacts/records/project__constraint/rec-1c7e8113-66b4-44e2-9183-b441364268a4.md))_

## sa-propose-only

### Constraint
- **sa-propose-only**: The analysis skill proposes edits and changes nothing until the user picks a candidate.; analysis-skill; session-analysis _(id: [rec-f0c6d77a-de74-4f43-a52c-28afe55af78c](.artifacts/records/project__constraint/rec-f0c6d77a-de74-4f43-a52c-28afe55af78c.md))_

## sa-reports-local

### Constraint
- **sa-reports-local**: Reports hold metrics and references, not raw transcript text, and stay local.; report output; session-analysis _(id: [rec-2f9e4b33-f25f-4f27-b860-1939df3fe318](.artifacts/records/project__constraint/rec-2f9e4b33-f25f-4f27-b860-1939df3fe318.md))_

## sa-script-read-only

### Constraint
- **sa-script-read-only**: The analysis script reads the store and never writes to it.; scripts; session-analysis _(id: [rec-bcd11e56-a54f-4d85-9055-63d13bb03ee8](.artifacts/records/project__constraint/rec-bcd11e56-a54f-4d85-9055-63d13bb03ee8.md))_

## se-reviewer-agent

### Acceptance
- **se-reviewer-agent**: R1; check; workflow-loop; test -f agents/se-reviewer.md && grep -qiE "no Write|without Write" agents/se-reviewer.md && grep -q agents/ scripts/sync-plugin.sh && d=$(mktemp -d) && bash scripts/sync-plugin.sh "$d/p" && test -f "$d/p/agents/se-reviewer.md" _(id: [rec-b06d589a-93d4-47e0-b2a4-5e1bf1fd8f21](.artifacts/records/project__acceptance/rec-b06d589a-93d4-47e0-b2a4-5e1bf1fd8f21.md))_

## se-workflow-check

### Acceptance
- **se-workflow-check**: R7; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k "pass or fail or integration or cli" _(id: [rec-b5d23174-3de0-41c1-8cfd-028492fc5d87](.artifacts/records/project__acceptance/rec-b5d23174-3de0-41c1-8cfd-028492fc5d87.md))_

## se-workflow-check-dirty

### Acceptance
- **se-workflow-check-dirty**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k dirty _(id: [rec-6b1e869a-6b06-49a6-9d3f-33e8326e05c1](.artifacts/records/project__acceptance/rec-6b1e869a-6b06-49a6-9d3f-33e8326e05c1.md))_

## se-workflow-check-entry

### Acceptance
- **se-workflow-check-entry**: R8; check; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k "entry or sync or install or bin" _(id: [rec-28b0ca39-45c6-4c7c-ac2d-bf41ba33cdf4](.artifacts/records/project__acceptance/rec-28b0ca39-45c6-4c7c-ac2d-bf41ba33cdf4.md))_

## se-workflow-check-manual

### Acceptance
- **se-workflow-check-manual**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k manual _(id: [rec-8eee9825-6a0d-4e05-9a8e-0d7558c7ed45](.artifacts/records/project__acceptance/rec-8eee9825-6a0d-4e05-9a8e-0d7558c7ed45.md))_

## se-workflow-check-runner-fields

### Acceptance
- **se-workflow-check-runner-fields**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k "runner or fields or metadata or exit_code" _(id: [rec-7715368f-94c3-4b3d-9692-5061c4cabafe](.artifacts/records/project__acceptance/rec-7715368f-94c3-4b3d-9692-5061c4cabafe.md))_

## session-analysis

### Position
- **session-analysis**: All four phases done. Run the analyze-sessions skill to review sessions. Code and skill are uncommitted. Two findings are open: the join is approximate, and the skill has minor judgment gaps.; repo _(id: [rec-428082e4-c07e-4c73-81c0-ffcb6c5e876c](.artifacts/records/project__current-position/rec-428082e4-c07e-4c73-81c0-ffcb6c5e876c.md))_

## shared-aa-resolver

### Acceptance
- **shared-aa-resolver**: R2; tdd; packaging; uv run --with pytest python -m pytest tests/test_aa_resolve.py -q _(id: [rec-15f765d5-4785-4b60-8e28-1e0c176acff4](.artifacts/records/project__acceptance/rec-15f765d5-4785-4b60-8e28-1e0c176acff4.md))_

## skill-needs-clear

### Acceptance
- **skill-needs-clear**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_discuss_skill.py -q _(id: [rec-0e2c47f2-f119-466d-8e46-fe961b604d3b](.artifacts/records/project__acceptance/rec-0e2c47f2-f119-466d-8e46-fe961b604d3b.md))_

### Finding
- **skill-needs-clear**: Skills opened human Needs-you gates without documenting clear-at-event CLI and engage remind; finding clear must be update needs none not supersede; pre-fix skill text and failing doc assertions; runtime rejects finding supersede; kinds-and-focus/engage and gate skills document clears including update needs none and tests stay green; none _(id: [rec-2d62de79-b64c-433f-b4ba-55c9612ba420](.artifacts/records/project__finding/rec-2d62de79-b64c-433f-b4ba-55c9612ba420.md))_

### Amendment
- **skill-needs-clear**: skill-needs-clear; workflow-loop _(id: [rec-97281986-6398-4076-b01f-fa8c63ff28a0](.artifacts/records/project__assignment-amendment/rec-97281986-6398-4076-b01f-fa8c63ff28a0.md))_

## skill-needs-clear-engage

### Acceptance
- **skill-needs-clear-engage**: R2; check; workflow-loop; uv run --with pytest python -m pytest tests/test_discuss_skill.py -q -k engage _(id: [rec-152ce4a8-e20f-4b8c-87b9-aaf30fb53703](.artifacts/records/project__acceptance/rec-152ce4a8-e20f-4b8c-87b9-aaf30fb53703.md))_

## skill-needs-clear-opens

### Acceptance
- **skill-needs-clear-opens**: R3; check; workflow-loop; uv run --with pytest python -m pytest tests/test_discuss_skill.py tests/test_skill_contract_consistency.py -q _(id: [rec-e154ee7d-d057-4d26-bd3e-9962592157f0](.artifacts/records/project__acceptance/rec-e154ee7d-d057-4d26-bd3e-9962592157f0.md))_

## skill-plugin-paths

### Acceptance
- **skill-plugin-paths**: R1; check; packaging; grep -q CLAUDE_PLUGIN_ROOT skills/ensure-store.md && grep -q CURSOR_PLUGIN_ROOT skills/ensure-store.md && ! grep -E '^[0-9]+\. .*\.cursor/plugins/local/se-workflow' skills/ensure-store.md _(id: [rec-1dc4bf40-0968-4e85-845f-c345a81a9768](.artifacts/records/project__acceptance/rec-1dc4bf40-0968-4e85-845f-c345a81a9768.md))_

## skill-plugin-paths-close

### Acceptance
- **skill-plugin-paths-close**: R3; check; packaging; grep -qE "se-workflow close-batch|bin/se-workflow close-batch" skills/verify-work/SKILL.md && ! grep -q scripts/close_batch.py skills/verify-work/SKILL.md _(id: [rec-05718b54-2ff0-42df-9d90-5563f4509289](.artifacts/records/project__acceptance/rec-05718b54-2ff0-42df-9d90-5563f4509289.md))_

## skill-plugin-paths-contract

### Acceptance
- **skill-plugin-paths-contract**: R4; check; packaging; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-3b720bda-fcdb-4cab-9cb2-e965636a73b0](.artifacts/records/project__acceptance/rec-3b720bda-fcdb-4cab-9cb2-e965636a73b0.md))_

## skills-backlog

### Acceptance
- **skills-backlog**: R2; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-95459f66-4633-441b-a73b-d1aa7b68957a](.artifacts/records/project__acceptance/rec-95459f66-4633-441b-a73b-d1aa7b68957a.md))_

## skills-backlog-promote

### Acceptance
- **skills-backlog-promote**: R5; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-9dcc1726-0246-424d-a8f7-edd8b8c98ea6](.artifacts/records/project__acceptance/rec-9dcc1726-0246-424d-a8f7-edd8b8c98ea6.md))_

## skills-claim-handoff

### Acceptance
- **skills-claim-handoff**: R1; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-7d56f650-967d-4bae-8088-7461b40697de](.artifacts/records/project__acceptance/rec-7d56f650-967d-4bae-8088-7461b40697de.md))_

## skills-claim-handoff-briefs

### Acceptance
- **skills-claim-handoff-briefs**: R5; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-5b5017ed-6e05-4149-9a16-a76488688d65](.artifacts/records/project__acceptance/rec-5b5017ed-6e05-4149-9a16-a76488688d65.md))_

## skills-claim-handoff-one-id

### Acceptance
- **skills-claim-handoff-one-id**: R2; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-9d1ec1a9-0e4c-413e-abd7-3df6a51dd28f](.artifacts/records/project__acceptance/rec-9d1ec1a9-0e4c-413e-abd7-3df6a51dd28f.md))_

## skills-claim-handoff-thin

### Acceptance
- **skills-claim-handoff-thin**: R3; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-177d102b-7173-412b-b4c0-2b7608eff04c](.artifacts/records/project__acceptance/rec-177d102b-7173-412b-b4c0-2b7608eff04c.md))_

## skills-red-first

### Acceptance
- **skills-red-first**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-4106666c-c561-474e-a8fd-4291869e42db](.artifacts/records/project__acceptance/rec-4106666c-c561-474e-a8fd-4291869e42db.md))_

## spec-model

### Acceptance
- **spec-model**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'phase_screen and tabs' _(id: [rec-7d44b243-444f-4d8f-a42d-2d8bce0f9b6d](.artifacts/records/project__acceptance/rec-7d44b243-444f-4d8f-a42d-2d8bce0f9b6d.md))_

## spec-model-decisions

### Acceptance
- **spec-model-decisions**: R7; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'phase_screen and decision' _(id: [rec-403cd5dd-db5b-4e68-b04b-311599c18032](.artifacts/records/project__acceptance/rec-403cd5dd-db5b-4e68-b04b-311599c18032.md))_

## spec-model-simple

### Acceptance
- **spec-model-simple**: R5; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'phase_screen and simple' _(id: [rec-0227d202-cb23-4c79-97e0-d7d58c3bb952](.artifacts/records/project__acceptance/rec-0227d202-cb23-4c79-97e0-d7d58c3bb952.md))_

## spec-pager

### Acceptance
- **spec-pager**: R11; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py tests/test_dashboard_pager.py -q -k pager _(id: [rec-05a167b0-042f-4057-b1a0-82dd15d96cbf](.artifacts/records/project__acceptance/rec-05a167b0-042f-4057-b1a0-82dd15d96cbf.md))_

## spec-screen

### Acceptance
- **spec-screen**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py -q -k "tab or open or key" _(id: [rec-b864e9ae-db02-462b-ae3a-227f4fdf5f0b](.artifacts/records/project__acceptance/rec-b864e9ae-db02-462b-ae3a-227f4fdf5f0b.md))_

## spec-screen-content

### Acceptance
- **spec-screen-content**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py -q -k "spec or design or decision or evidence or task or esc" _(id: [rec-fb12c32d-c03a-47d3-8f10-bff1fa09e822](.artifacts/records/project__acceptance/rec-fb12c32d-c03a-47d3-8f10-bff1fa09e822.md))_

## spec-screen-pager

### Acceptance
- **spec-screen-pager**: R11; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py -q -k pager _(id: [rec-2c20fcfa-8ea0-4f55-b8ba-0fadcb3fe9b0](.artifacts/records/project__acceptance/rec-2c20fcfa-8ea0-4f55-b8ba-0fadcb3fe9b0.md))_

## specify-design

### Acceptance
- **specify-design**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_discuss_skill.py -q _(id: [rec-7683d746-1d29-4de5-bc76-3bdcc678f158](.artifacts/records/project__acceptance/rec-7683d746-1d29-4de5-bc76-3bdcc678f158.md))_

## status-line-from-snapshot

### Acceptance
- **status-line-from-snapshot**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_status.py -q _(id: [rec-fb5c210c-4e78-42c4-8fb9-f8f585e3f5f8](.artifacts/records/project__acceptance/rec-fb5c210c-4e78-42c4-8fb9-f8f585e3f5f8.md))_

## status-tab-row

### Acceptance
- **status-tab-row**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k tab_row _(id: [rec-ba223a32-d09b-4dd0-9256-101bd04d0ea1](.artifacts/records/project__acceptance/rec-ba223a32-d09b-4dd0-9256-101bd04d0ea1.md))_

## status-tabs

### Acceptance
- **status-tabs**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-5a31e5b1-1af0-4738-bf89-20d16bf3dcaa](.artifacts/records/project__acceptance/rec-5a31e5b1-1af0-4738-bf89-20d16bf3dcaa.md))_

### Finding
- **status-tabs**: status-tabs gap closed: 7 tabs, keys 1-7, left/right and README landed at 75e530c; Execution report rec-10a142d4 and a parent re-run of 116 passing tests at 75e530c; A tab, key or README row from the description is missing; none _(id: [rec-94362ae8-0f01-4ad1-bfcd-cffa426566b8](.artifacts/records/project__finding/rec-94362ae8-0f01-4ad1-bfcd-cffa426566b8.md))_

### Amendment
- **status-tabs**: status-tabs; dashboard-ui _(id: [rec-9d00fbec-bc87-40b3-b37b-38e00bea73db](.artifacts/records/project__assignment-amendment/rec-9d00fbec-bc87-40b3-b37b-38e00bea73db.md))_
- **status-tabs**: status-tabs; dashboard-ui _(id: [rec-e076f208-265b-4f3a-8365-0f04b6b421a8](.artifacts/records/project__assignment-amendment/rec-e076f208-265b-4f3a-8365-0f04b6b421a8.md))_

## status-tabs-fixture

### Acceptance
- **status-tabs-fixture**: R7; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k status_tabs _(id: [rec-a6aabc11-4cb5-47dd-84da-5c01fd225ab5](.artifacts/records/project__acceptance/rec-a6aabc11-4cb5-47dd-84da-5c01fd225ab5.md))_

## stepper-wrap

### Acceptance
- **stepper-wrap**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k stepper _(id: [rec-c2df3f61-8b0b-44d8-89b3-f3033ebcf9d0](.artifacts/records/project__acceptance/rec-c2df3f61-8b0b-44d8-89b3-f3033ebcf9d0.md))_

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

## suite-docs-tests

### Acceptance
- **suite-docs-tests**: R5; check; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-918209be-d62b-4b51-ae01-3ebf361b6e6d](.artifacts/records/project__acceptance/rec-918209be-d62b-4b51-ae01-3ebf361b6e6d.md))_

## suite-engine

### Acceptance
- **suite-engine**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "suite or gate or advisory or policy or mode" _(id: [rec-859d8cde-214e-470d-b492-8896741e83df](.artifacts/records/project__acceptance/rec-859d8cde-214e-470d-b492-8896741e83df.md))_

## suite-engine-authority

### Acceptance
- **suite-engine-authority**: R8; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_close_batch.py -q -k "tier2 or suite or red_first or red-first or phase_gate" _(id: [rec-f03a59ca-7763-49e7-9670-5e1fdbc30575](.artifacts/records/project__acceptance/rec-f03a59ca-7763-49e7-9670-5e1fdbc30575.md))_

## table-focus

### Acceptance
- **table-focus**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k focus _(id: [rec-2536ed50-f949-40fe-a914-f283c9633975](.artifacts/records/project__acceptance/rec-2536ed50-f949-40fe-a914-f283c9633975.md))_

## task-commit

### Acceptance
- **task-commit**: R6; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_task_commit.py tests/test_execute_landing.py tests/test_skill_contract_consistency.py -q -k 'commit or landing or task_commit' _(id: [rec-34f5bd84-dee8-4fa6-bf3a-1f646de23f5e](.artifacts/records/project__acceptance/rec-34f5bd84-dee8-4fa6-bf3a-1f646de23f5e.md))_

## task-detail-links

### Acceptance
- **task-detail-links**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k link _(id: [rec-79b9e2f6-49a8-4d48-8788-0da94d698726](.artifacts/records/project__acceptance/rec-79b9e2f6-49a8-4d48-8788-0da94d698726.md))_

## task-detail-model

### Acceptance
- **task-detail-model**: tdd; dashboard; python3 -m pytest tests/test_dashboard_model.py -q _(id: [rec-8f020a2f-f7de-43e3-b46f-423d52e44fe4](.artifacts/records/project__acceptance/rec-8f020a2f-f7de-43e3-b46f-423d52e44fe4.md))_

## task-detail-module

### Acceptance
- **task-detail-module**: tdd; dashboard; ! grep -n '^class TaskDetailScreen' dashboard/app.py && grep -c '^class TaskDetailScreen' dashboard/task_detail.py && uv run --with pytest --with textual pytest tests/test_dashboard_app.py _(id: [rec-7f83addf-fb83-4129-9116-b02371346c5d](.artifacts/records/project__acceptance/rec-7f83addf-fb83-4129-9116-b02371346c5d.md))_

## task-detail-screen

### Acceptance
- **task-detail-screen**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-421586f5-5f49-4a47-b715-eeb09ad69b90](.artifacts/records/project__acceptance/rec-421586f5-5f49-4a47-b715-eeb09ad69b90.md))_

### Amendment
- **task-detail-screen**: task-detail-screen; dashboard-ui _(id: [rec-6956b3e6-05e0-49a3-92ed-79f0db8c4db8](.artifacts/records/project__assignment-amendment/rec-6956b3e6-05e0-49a3-92ed-79f0db8c4db8.md))_

## task-list-filters

### Acceptance
- **task-list-filters**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q _(id: [rec-982fcf31-6ef8-41aa-97a6-03ec860bfccb](.artifacts/records/project__acceptance/rec-982fcf31-6ef8-41aa-97a6-03ec860bfccb.md))_

## task-row-cells

### Acceptance
- **task-row-cells**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'waits or running or phase_column' _(id: [rec-daa1a988-73f2-45f9-8cde-f795662613c1](.artifacts/records/project__acceptance/rec-daa1a988-73f2-45f9-8cde-f795662613c1.md))_

## task-row-model

### Acceptance
- **task-row-model**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'waits or running' _(id: [rec-60e78986-208c-43d5-8207-9803afeab4df](.artifacts/records/project__acceptance/rec-60e78986-208c-43d5-8207-9803afeab4df.md))_

## task-table-module

### Acceptance
- **task-table-module**: tdd; dashboard; ! grep -nE '^(class TaskFilter|class SectionRow|def section_rows|def visible_tasks|class TaskTable)' dashboard/app.py && grep -c 'class TaskFilter' dashboard/tasks.py && uv run --with pytest --with textual pytest tests/test_dashboard_app.py tests/test_dashboard_tasks.py _(id: [rec-9a70606f-50c9-40b0-9b8c-107ff6573a06](.artifacts/records/project__acceptance/rec-9a70606f-50c9-40b0-9b8c-107ff6573a06.md))_

## terminal-view-format

### Acceptance
- **terminal-view-format**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q _(id: [rec-afb68d05-d961-45dd-813e-948c8e137722](.artifacts/records/project__acceptance/rec-afb68d05-d961-45dd-813e-948c8e137722.md))_

## test-suite-speed

### Acceptance
- **test-suite-speed**: check; test-suite-speed; time uv run --with textual --with pytest python -m pytest tests -q _(id: [rec-6e6e5c69-9ab0-44f3-9016-49c3512fcd99](.artifacts/records/project__acceptance/rec-6e6e5c69-9ab0-44f3-9016-49c3512fcd99.md))_

## tests-brief-lock

### Acceptance
- **tests-brief-lock**: R5; tdd; workflow-loop; python3 -m pytest tests/test_plan_trace.py tests/test_skill_contract_consistency.py -q _(id: [rec-b760d3e8-594b-491c-b282-aa07923e1a38](.artifacts/records/project__acceptance/rec-b760d3e8-594b-491c-b282-aa07923e1a38.md))_

### Finding
- **tests-brief-lock**: tests-brief-lock closed done without red-first: predecessor suite verify_command already passed; new assertions are additive; At 3b2f808 the acceptance verify_command (full plan-trace+consistency) exits 0; tip 5030389 adds assertions. No runner fail exists for this criterion_id with ancestry to green.; a later phase requires red-first for additive test-only tasks, or a fail check-run for this criterion precedes green; none _(id: [rec-7c5115ae-6da3-4327-a386-7b7da037b865](.artifacts/records/project__finding/rec-7c5115ae-6da3-4327-a386-7b7da037b865.md))_

## tests-brief-lock-r4

### Acceptance
- **tests-brief-lock-r4**: R4; check; workflow-loop; python3 -m pytest tests/test_plan_trace.py -k criterion_optional_in_contract -q _(id: [rec-6525fff7-02a2-4ef2-8ae7-1b4fe8a3fe89](.artifacts/records/project__acceptance/rec-6525fff7-02a2-4ef2-8ae7-1b4fe8a3fe89.md))_

## tests-claim-chain

### Acceptance
- **tests-claim-chain**: R6; tdd; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q _(id: [rec-14838183-7e65-45e7-8ac1-41a2ff0e912b](.artifacts/records/project__acceptance/rec-14838183-7e65-45e7-8ac1-41a2ff0e912b.md))_

## tier2-dashboard

### Acceptance
- **tier2-dashboard**: R6; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k tier2 _(id: [rec-b5eb3ea3-6ec1-4431-ab56-fcb60d7b1574](.artifacts/records/project__acceptance/rec-b5eb3ea3-6ec1-4431-ab56-fcb60d7b1574.md))_

## tier2-engine

### Acceptance
- **tier2-engine**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "runner or background or check_run or tmux" _(id: [rec-66d14411-07cd-479e-bb45-abfd3ee105f3](.artifacts/records/project__acceptance/rec-66d14411-07cd-479e-bb45-abfd3ee105f3.md))_

## tier2-engine-fix

### Acceptance
- **tier2-engine-fix**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "fix or cluster or budget" _(id: [rec-e54af7a4-185c-4adc-93b9-6ca9417d5f0f](.artifacts/records/project__acceptance/rec-e54af7a4-185c-4adc-93b9-6ca9417d5f0f.md))_

## tier2-engine-gate

### Acceptance
- **tier2-engine-gate**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k gate _(id: [rec-5ad44d4e-6fd3-4829-be3e-95e48379990b](.artifacts/records/project__acceptance/rec-5ad44d4e-6fd3-4829-be3e-95e48379990b.md))_

## tier2-engine-meta

### Acceptance
- **tier2-engine-meta**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "meta or fields or evidence_kind or digest" _(id: [rec-f434ce3c-77ee-4e17-80d6-ad308eadb1f2](.artifacts/records/project__acceptance/rec-f434ce3c-77ee-4e17-80d6-ad308eadb1f2.md))_

## tier2-engine-scoped

### Acceptance
- **tier2-engine-scoped**: R7; check; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-97b46204-7027-47b9-bf84-e4b585da8849](.artifacts/records/project__acceptance/rec-97b46204-7027-47b9-bf84-e4b585da8849.md))_

## tier2-journal-pager-flake

### Finding
- **tier2-journal-pager-flake**: test_journal_detail_pager_pages_record_with_stub timed out under tier-2 parallel load; tier-2 at 3379fcf still fails same test after 40s timeout; screen never loads under xdist; test passes stably under same suite or human accepts waiver; none _(id: [rec-c174fd42-e8c9-41ea-bb43-8aee75770421](.artifacts/records/project__finding/rec-c174fd42-e8c9-41ea-bb43-8aee75770421.md))_

## tier2-plugin-root-and-cli

### Finding
- **tier2-plugin-root-and-cli**: tier-2 failed at phase head: verify_authority import of scripts/close_batch + journal pager flake; exit 1; nodes ['tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub', 'tests/test_verify_authority.py']; tier-2 passes at new phase head; none _(id: [rec-c8de37ab-a66a-4589-ab5a-2299788a4be9](.artifacts/records/project__finding/rec-c8de37ab-a66a-4589-ab5a-2299788a4be9.md))_

## tiered-verification-tier2-budget

### Finding
- **tiered-verification-tier2-budget**: Tier-2 fix-task budget exhausted with remaining failing modules; tier-2 check-run rec-a24a9ec0-30f8-41e7-a2dc-c8552984c3ae failed with 10 node ids across 7 modules; created 3 fix tasks (dashboard_app, dashboard_journal, discuss_skill); remaining: evidence_loop, plan_landing, plan_wave_rules, verify_authority; remaining modules fixed and tier-2 passes at phase head, or human accepts scoped waiver; none _(id: [rec-b8101acf-ff6c-4dbc-8042-6499702bd5e5](.artifacts/records/project__finding/rec-b8101acf-ff6c-4dbc-8042-6499702bd5e5.md))_

## tm-cli

### Acceptance
- **tm-cli**: tdd; session-analysis; python3 -m pytest -q tests/test_session_report.py _(id: [rec-be629630-2798-4a55-92ca-322aba930e94](.artifacts/records/project__acceptance/rec-be629630-2798-4a55-92ca-322aba930e94.md))_

## tm-parse-events

### Acceptance
- **tm-parse-events**: tdd; session-analysis; python3 -m pytest -q tests/test_session_metrics.py -k parse _(id: [rec-2df7a704-c3ba-43a0-966d-42474d3c2318](.artifacts/records/project__acceptance/rec-2df7a704-c3ba-43a0-966d-42474d3c2318.md))_

## tm-session-fields

### Acceptance
- **tm-session-fields**: tdd; session-analysis; python3 -m pytest -q tests/test_session_fields.py _(id: [rec-5f8ebfcf-f591-4f07-932d-65fabc8871fb](.artifacts/records/project__acceptance/rec-5f8ebfcf-f591-4f07-932d-65fabc8871fb.md))_

## tm-tool-metrics

### Acceptance
- **tm-tool-metrics**: tdd; session-analysis; python3 -m pytest -q tests/test_session_tools.py _(id: [rec-eb5399be-74fd-4403-bf2d-69fb1cb5bce9](.artifacts/records/project__acceptance/rec-eb5399be-74fd-4403-bf2d-69fb1cb5bce9.md))_

## tmux-conf-removal

### Acceptance
- **tmux-conf-removal**: check; dashboard; test ! -e dashboard/tmux.conf && ! grep -rnE 'dashboard/tmux\.conf|SE_WORKFLOW_DASHBOARD' dashboard scripts tests _(id: [rec-3aa70906-2826-4ae6-86f0-1b6d7a206306](.artifacts/records/project__acceptance/rec-3aa70906-2826-4ae6-86f0-1b6d7a206306.md))_

## tmux-conf-removal-install

### Acceptance
- **tmux-conf-removal-install**: check; dashboard; d=$(mktemp -d) && bash scripts/sync-plugin.sh "$d/p" && test -x "$d/p/se-workflow.tmux" _(id: [rec-202b31bb-dba8-4bb0-ab9b-cae95af2386e](.artifacts/records/project__acceptance/rec-202b31bb-dba8-4bb0-ab9b-cae95af2386e.md))_

## tmux-entry-script

### Acceptance
- **tmux-entry-script**: tdd; dashboard; uv run --with pytest --with textual pytest -m tmux tests/test_tmux_entry.py -k default _(id: [rec-f6564330-b301-4302-a1d2-6e9c206c489b](.artifacts/records/project__acceptance/rec-f6564330-b301-4302-a1d2-6e9c206c489b.md))_

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

## unsigned-check-label

### Acceptance
- **unsigned-check-label**: tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k unsigned _(id: [rec-403febb3-cbe5-474d-8413-5687934c29d2](.artifacts/records/project__acceptance/rec-403febb3-cbe5-474d-8413-5687934c29d2.md))_

## verify-atomic-claims

### Acceptance
- **verify-atomic-claims**: R6; tdd; workflow-loop; python3 -m pytest tests/test_plan_trace.py -k 'thin_deliver and (capture or create or cli)' -q _(id: [rec-0cd6c518-1e3e-4149-8bbe-595d2465cdca](.artifacts/records/project__acceptance/rec-0cd6c518-1e3e-4149-8bbe-595d2465cdca.md))_

## verify-atomic-claims-contract

### Acceptance
- **verify-atomic-claims-contract**: R4; check; workflow-loop; python3 -m pytest tests/test_plan_trace.py -k criterion_optional_in_contract -q _(id: [rec-f6cf9299-6647-4ad0-b659-e4d890f6f3c3](.artifacts/records/project__acceptance/rec-f6cf9299-6647-4ad0-b659-e4d890f6f3c3.md))_

## verify-atomic-claims-pytest

### Acceptance
- **verify-atomic-claims-pytest**: R6; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q _(id: [rec-e1380e66-3c40-4868-b412-12685050d7fd](.artifacts/records/project__acceptance/rec-e1380e66-3c40-4868-b412-12685050d7fd.md))_

## verify-atomic-claims-skills

### Acceptance
- **verify-atomic-claims-skills**: R1; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_plan_trace.py -q _(id: [rec-d0219464-ac52-415e-b926-d817876f0d8a](.artifacts/records/project__acceptance/rec-d0219464-ac52-415e-b926-d817876f0d8a.md))_

## verify-authority

### Acceptance
- **verify-authority**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_authority.py tests/test_skill_contract_consistency.py -q _(id: [rec-88c394e4-ca2e-45c8-a222-073b4b621bdd](.artifacts/records/project__acceptance/rec-88c394e4-ca2e-45c8-a222-073b4b621bdd.md))_

## verify-backlog-capture

### Acceptance
- **verify-backlog-capture**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_backlog_item.py -q _(id: [rec-91696e19-7aa5-4cf8-8215-8d8cf9f668df](.artifacts/records/project__acceptance/rec-91696e19-7aa5-4cf8-8215-8d8cf9f668df.md))_

## verify-backlog-capture-contract

### Acceptance
- **verify-backlog-capture-contract**: R1; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_contract_self_consistency.py -q _(id: [rec-2648b75d-644b-4eee-ba8d-4d1ff62f7f48](.artifacts/records/project__acceptance/rec-2648b75d-644b-4eee-ba8d-4d1ff62f7f48.md))_

## verify-backlog-capture-dashboard

### Acceptance
- **verify-backlog-capture-dashboard**: R6; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k backlog _(id: [rec-5607f8c7-adf7-44e7-89c3-fa6d5588b4ec](.artifacts/records/project__acceptance/rec-5607f8c7-adf7-44e7-89c3-fa6d5588b4ec.md))_

## verify-backlog-capture-skills

### Acceptance
- **verify-backlog-capture-skills**: R2; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-f9cf16cd-69d0-4a84-86aa-b134b078c167](.artifacts/records/project__acceptance/rec-f9cf16cd-69d0-4a84-86aa-b134b078c167.md))_

## verify-check-runner

### Acceptance
- **verify-check-runner**: R7; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k "pass or fail or blocked or integration or cli" _(id: [rec-89a78033-b672-4f71-9f59-10deea6ef8bf](.artifacts/records/project__acceptance/rec-89a78033-b672-4f71-9f59-10deea6ef8bf.md))_

## verify-check-runner-commit

### Acceptance
- **verify-check-runner-commit**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_task_commit.py tests/test_execute_landing.py tests/test_skill_contract_consistency.py -q -k "commit or landing or task_commit" _(id: [rec-efdf2173-e187-41a1-a65f-9539da56742e](.artifacts/records/project__acceptance/rec-efdf2173-e187-41a1-a65f-9539da56742e.md))_

## verify-check-runner-contract

### Acceptance
- **verify-check-runner-contract**: R4; check; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py tests/test_evidence_loop.py tests/test_assess_routing.py -q -k "enum or result or method or contract" _(id: [rec-d00ce191-345a-46ed-9dc8-4c0242f31984](.artifacts/records/project__acceptance/rec-d00ce191-345a-46ed-9dc8-4c0242f31984.md))_

## verify-check-runner-dirty

### Acceptance
- **verify-check-runner-dirty**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k dirty _(id: [rec-5c18090c-ca0b-43a3-aa61-78ebd2383d7e](.artifacts/records/project__acceptance/rec-5c18090c-ca0b-43a3-aa61-78ebd2383d7e.md))_

## verify-check-runner-skills

### Acceptance
- **verify-check-runner-skills**: R5; check; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_authority.py tests/test_skill_contract_consistency.py -q _(id: [rec-a831be0f-059e-414e-90bb-36c485017676](.artifacts/records/project__acceptance/rec-a831be0f-059e-414e-90bb-36c485017676.md))_

## verify-claim-witnesses

### Acceptance
- **verify-claim-witnesses**: R1; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'cli and (fabricated or store_authority or mismatch)' -q _(id: [rec-7252d501-3ecd-40b3-8c19-db0da8a5c8a0](.artifacts/records/project__acceptance/rec-7252d501-3ecd-40b3-8c19-db0da8a5c8a0.md))_

## verify-claim-witnesses-contract

### Acceptance
- **verify-claim-witnesses-contract**: R1; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-b50e926c-44f1-4c9a-80bb-af8bef0fd0de](.artifacts/records/project__acceptance/rec-b50e926c-44f1-4c9a-80bb-af8bef0fd0de.md))_

## verify-claim-witnesses-mutants

### Acceptance
- **verify-claim-witnesses-mutants**: R6; check; workflow-loop; python3 -m pytest tests/test_close_batch.py tests/test_affidavit_check.py -q _(id: [rec-4d4ab5a3-2608-4a28-a070-8d07d2bcf3f4](.artifacts/records/project__acceptance/rec-4d4ab5a3-2608-4a28-a070-8d07d2bcf3f4.md))_

## verify-claim-witnesses-tdd-revision

### Acceptance
- **verify-claim-witnesses-tdd-revision**: R3; check; workflow-loop; python3 -m pytest tests/test_close_batch.py -k 'tdd_revision_without_red or revision_allowed_tdd' -q _(id: [rec-b059420c-342e-47a1-b52b-9d0103494e1c](.artifacts/records/project__acceptance/rec-b059420c-342e-47a1-b52b-9d0103494e1c.md))_

## verify-claim-witnesses-worktree

### Acceptance
- **verify-claim-witnesses-worktree**: R5; check; workflow-loop; python3 -m pytest tests/test_affidavit_check.py tests/test_close_batch.py -k 'worktree or cwd_primary or store_cwd' -q _(id: [rec-c63b67b2-6f9b-4a18-a1a7-901f75846af3](.artifacts/records/project__acceptance/rec-c63b67b2-6f9b-4a18-a1a7-901f75846af3.md))_

## verify-cross-harness-install

### Acceptance
- **verify-cross-harness-install**: R1; check; packaging; python3 -m pytest tests/test_skill_portability.py -q _(id: [rec-fafaad86-e26f-4d73-b5fa-73bcca66f5ac](.artifacts/records/project__acceptance/rec-fafaad86-e26f-4d73-b5fa-73bcca66f5ac.md))_

## verify-cross-harness-install-agent

### Acceptance
- **verify-cross-harness-install-agent**: R13; check; packaging; python3 -m pytest tests/test_agent_generation.py -q _(id: [rec-0e6b1bc4-d41f-461a-9964-42208f5109f6](.artifacts/records/project__acceptance/rec-0e6b1bc4-d41f-461a-9964-42208f5109f6.md))_

## verify-cross-harness-install-allowlist

### Acceptance
- **verify-cross-harness-install-allowlist**: R14; check; packaging; python3 -m pytest tests/test_installer.py -q -k allowlist _(id: [rec-ac3770b6-615a-446f-9a0a-65278e1eef1e](.artifacts/records/project__acceptance/rec-ac3770b6-615a-446f-9a0a-65278e1eef1e.md))_

## verify-cross-harness-install-cli

### Acceptance
- **verify-cross-harness-install-cli**: R5; check; packaging; python3 -m pytest tests/integration/test_cli_on_path.py -q _(id: [rec-e7ad94e4-40ae-4238-be13-de5a96665831](.artifacts/records/project__acceptance/rec-e7ad94e4-40ae-4238-be13-de5a96665831.md))_

## verify-cross-harness-install-docs

### Acceptance
- **verify-cross-harness-install-docs**: R15; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q _(id: [rec-8075e775-e831-46ba-8279-a733f640230f](.artifacts/records/project__acceptance/rec-8075e775-e831-46ba-8279-a733f640230f.md))_

## verify-cross-harness-install-hosts

### Acceptance
- **verify-cross-harness-install-hosts**: R12; check; packaging; python3 -m pytest tests/integration/test_temp_home_install.py -q _(id: [rec-053c64ab-c952-45da-9a00-fbd2fb9b1b2d](.artifacts/records/project__acceptance/rec-053c64ab-c952-45da-9a00-fbd2fb9b1b2d.md))_

## verify-cross-harness-install-idempotent

### Acceptance
- **verify-cross-harness-install-idempotent**: R9; check; packaging; python3 -m pytest tests/test_installer.py -q -k idempotent _(id: [rec-acfbb12a-ebd9-4870-aa4b-e056f7c9abd7](.artifacts/records/project__acceptance/rec-acfbb12a-ebd9-4870-aa4b-e056f7c9abd7.md))_

## verify-cross-harness-install-matrix

### Acceptance
- **verify-cross-harness-install-matrix**: R8; check; packaging; python3 -m pytest tests/test_installer.py -q -k flags _(id: [rec-9810dc0f-203f-4021-8cd3-2a4551476d7c](.artifacts/records/project__acceptance/rec-9810dc0f-203f-4021-8cd3-2a4551476d7c.md))_

## verify-cross-harness-install-native

### Acceptance
- **verify-cross-harness-install-native**: R10; check; packaging; python3 -m pytest tests/test_installer.py -q -k native _(id: [rec-c973b40f-0b61-4a16-9292-6906e6e1b14a](.artifacts/records/project__acceptance/rec-c973b40f-0b61-4a16-9292-6906e6e1b14a.md))_

## verify-cross-harness-install-paths

### Acceptance
- **verify-cross-harness-install-paths**: R6; check; packaging; python3 -m pytest tests/test_skill_portability.py -q -k paths _(id: [rec-41da4b56-b406-46e9-8fd8-a22d73b568c9](.artifacts/records/project__acceptance/rec-41da4b56-b406-46e9-8fd8-a22d73b568c9.md))_

## verify-cross-harness-install-subcommands

### Acceptance
- **verify-cross-harness-install-subcommands**: R7; check; packaging; python3 -m pytest tests/test_cli_packaging.py -q -k subcommands _(id: [rec-47950663-6415-4f04-b860-65ea692e3e66](.artifacts/records/project__acceptance/rec-47950663-6415-4f04-b860-65ea692e3e66.md))_

## verify-cross-harness-install-tail

### Acceptance
- **verify-cross-harness-install-tail**: R11; check; packaging; python3 -m pytest tests/test_installer.py -q -k tail _(id: [rec-0d490c96-f704-422d-ad79-754e960d4715](.artifacts/records/project__acceptance/rec-0d490c96-f704-422d-ad79-754e960d4715.md))_

## verify-dashboard-actions-phase

### Acceptance
- **verify-dashboard-actions-phase**: check; dashboard; uv run --with textual --with pytest python -m pytest tests -q _(id: [rec-468f8719-9cf5-4262-aea7-6d372a9cd6a9](.artifacts/records/project__acceptance/rec-468f8719-9cf5-4262-aea7-6d372a9cd6a9.md))_

## verify-dashboard-actions-phase-signoff

### Acceptance
- **verify-dashboard-actions-phase-signoff**: manual; dashboard _(id: [rec-aa7012e9-f5d9-427c-a0d5-74e173544519](.artifacts/records/project__acceptance/rec-aa7012e9-f5d9-427c-a0d5-74e173544519.md))_

## verify-dashboard-approvals

### Acceptance
- **verify-dashboard-approvals**: R1; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k approval _(id: [rec-5b8ab6e4-d17d-479a-b038-38d2f8a03d1e](.artifacts/records/project__acceptance/rec-5b8ab6e4-d17d-479a-b038-38d2f8a03d1e.md))_

## verify-dashboard-approvals-constraints

### Acceptance
- **verify-dashboard-approvals-constraints**: R7; check; workflow-loop; /home/andrewyin/adaptive-artifacts/bin/adaptive-artifacts --store /home/andrewyin/se-workflow/.artifacts list --type project:constraint --state active | python3 -c "import sys,json; d=json.load(sys.stdin); stmts=[(r['subject'], (r.get('payload') or {}).get('statement') or '') for r in d['records']]; assert any(s=='dashboard-human-gate-writes' for s,_ in stmts); hg=[t for s,t in stmts if s=='dashboard-human-gate-writes']; assert hg and ('human Needs-you' in hg[0] or 'human-gate' in hg[0].lower()); old={'dashboard-read-only','dashboard-read-only-dashboard-bugfix','dashboard-read-only-dashboard-features'}; assert not any('never writes' in t.lower() for s,t in stmts if s in old); assert all('Retired' in t or 'dashboard-human-gate-writes' in t for s,t in stmts if s in old)" _(id: [rec-9c7c3c55-1e86-41fd-bb53-3c6f41567cf4](.artifacts/records/project__acceptance/rec-9c7c3c55-1e86-41fd-bb53-3c6f41567cf4.md))_

## verify-dashboard-approvals-docs

### Acceptance
- **verify-dashboard-approvals-docs**: R8; check; workflow-loop; grep -E 'Approve|Reject|Accept risk' README.md && uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-a764fa17-a012-4fec-8c30-4b0eb791b434](.artifacts/records/project__acceptance/rec-a764fa17-a012-4fec-8c30-4b0eb791b434.md))_

## verify-dashboard-approvals-revision

### Acceptance
- **verify-dashboard-approvals-revision**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and stale' _(id: [rec-84aa203e-910a-40ea-a99b-1e0c3efdda28](.artifacts/records/project__acceptance/rec-84aa203e-910a-40ea-a99b-1e0c3efdda28.md))_

## verify-dashboard-package

### Acceptance
- **verify-dashboard-package**: tdd; dashboard; uv run --with pytest --with textual pytest tests/test_dashboard_launcher.py tests/test_dashboard_integration.py _(id: [rec-f6216dac-0349-43a1-86a4-f5dd48eb2f51](.artifacts/records/project__acceptance/rec-f6216dac-0349-43a1-86a4-f5dd48eb2f51.md))_

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

## verify-dashboard-view-phase-live

### Acceptance
- **verify-dashboard-view-phase-live**: manual; dashboard; ~/adaptive-artifacts/bin/adaptive-artifacts --store ~/.artifacts/se-workflow view --id project:dashboard _(id: [rec-83fc3486-af5f-49af-9000-8d9fd6890f3c](.artifacts/records/project__acceptance/rec-83fc3486-af5f-49af-9000-8d9fd6890f3c.md))_

## verify-dashboard-view-phase-suites

### Acceptance
- **verify-dashboard-view-phase-suites**: check; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q && cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-1a3c142c-b9c6-4f57-baf0-b38000b5bb9f](.artifacts/records/project__acceptance/rec-1a3c142c-b9c6-4f57-baf0-b38000b5bb9f.md))_

## verify-end-to-end-phase

### Acceptance
- **verify-end-to-end-phase**: check; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q && cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-a5e71d14-1f25-4868-a42e-3a2b17e16616](.artifacts/records/project__acceptance/rec-a5e71d14-1f25-4868-a42e-3a2b17e16616.md))_

## verify-end-to-end-phase-clear

### Acceptance
- **verify-end-to-end-phase-clear**: check; dashboard; ~/se-workflow/scripts/dashboard-status ~/se-workflow _(id: [rec-9dce7bb8-9cc7-4a4d-9ebd-48a749f7cc85](.artifacts/records/project__acceptance/rec-9dce7bb8-9cc7-4a4d-9ebd-48a749f7cc85.md))_

## verify-estimate-view

### Acceptance
- **verify-estimate-view**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_header_sitting && uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m "not tmux" && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-9b9d3ec2-b413-4471-8991-8546a7f1c82b](.artifacts/records/project__acceptance/rec-9b9d3ec2-b413-4471-8991-8546a7f1c82b.md))_

## verify-estimate-view-chips

### Acceptance
- **verify-estimate-view-chips**: R6; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_estimate.py -q -k estimate_view_chips _(id: [rec-eae79ebb-8d5c-4378-b484-8ce816861f28](.artifacts/records/project__acceptance/rec-eae79ebb-8d5c-4378-b484-8ce816861f28.md))_

## verify-estimate-view-clip

### Acceptance
- **verify-estimate-view-clip**: R5; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_clip _(id: [rec-e58b5f93-f9e3-4650-9853-ddcd0d0a0470](.artifacts/records/project__acceptance/rec-e58b5f93-f9e3-4650-9853-ddcd0d0a0470.md))_

## verify-estimate-view-contract

### Acceptance
- **verify-estimate-view-contract**: R7; check; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_blank_executor && test -z "$(git diff --name-only main -- contract/project-design.json)" _(id: [rec-7303a69d-1a5e-4661-b5c4-228c5b3dc28d](.artifacts/records/project__acceptance/rec-7303a69d-1a5e-4661-b5c4-228c5b3dc28d.md))_

## verify-estimate-view-suffix

### Acceptance
- **verify-estimate-view-suffix**: R4; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k estimate_view_title_suffix _(id: [rec-f812f0d8-f363-4ec3-b7c8-32463a0d9d0b](.artifacts/records/project__acceptance/rec-f812f0d8-f363-4ec3-b7c8-32463a0d9d0b.md))_

## verify-estimate-view-unset

### Acceptance
- **verify-estimate-view-unset**: R3; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k 'estimate_view_unset_count or estimate_view_header_partial' _(id: [rec-8b8345bb-5686-47dc-869d-39897b52c173](.artifacts/records/project__acceptance/rec-8b8345bb-5686-47dc-869d-39897b52c173.md))_

## verify-estimate-view-wave

### Acceptance
- **verify-estimate-view-wave**: R2; check; dashboard; uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_wave_rule _(id: [rec-29ba3627-46df-4308-bae9-8939ff93b2f1](.artifacts/records/project__acceptance/rec-29ba3627-46df-4308-bae9-8939ff93b2f1.md))_

## verify-evidence-loop

### Acceptance
- **verify-evidence-loop**: check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_evidence_loop.py -q _(id: [rec-c6f57f2f-cef8-4daf-b8f1-7899cd1a7e27](.artifacts/records/project__acceptance/rec-c6f57f2f-cef8-4daf-b8f1-7899cd1a7e27.md))_

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

## verify-evidence-matrix-suite

### Acceptance
- **verify-evidence-matrix-suite**: R8; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_requirement.py tests/test_dashboard_phase_screen.py -q -k matrix _(id: [rec-90a86f40-7f74-4dc3-875a-9d1043564b55](.artifacts/records/project__acceptance/rec-90a86f40-7f74-4dc3-875a-9d1043564b55.md))_

## verify-evidence-view

### Acceptance
- **verify-evidence-view**: R6; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_e2e_dashboard.py -q -m tmux -k evidence _(id: [rec-7ed13ebd-7b0a-436b-9c12-dfd4ef8cefcd](.artifacts/records/project__acceptance/rec-7ed13ebd-7b0a-436b-9c12-dfd4ef8cefcd.md))_

## verify-evidence-view-app

### Acceptance
- **verify-evidence-view-app**: R3; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_requirement.py -q _(id: [rec-08b630d4-2e32-4b18-a674-8d21a0733158](.artifacts/records/project__acceptance/rec-08b630d4-2e32-4b18-a674-8d21a0733158.md))_

## verify-evidence-view-legacy

### Acceptance
- **verify-evidence-view-legacy**: R10; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k 'evidence and legacy' _(id: [rec-04bc526a-2703-4f22-8c56-9b068bc7869b](.artifacts/records/project__acceptance/rec-04bc526a-2703-4f22-8c56-9b068bc7869b.md))_

## verify-evidence-view-model

### Acceptance
- **verify-evidence-view-model**: R2; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k evidence _(id: [rec-ab6549b4-827c-4cb8-9fd1-4adcc54de77d](.artifacts/records/project__acceptance/rec-ab6549b4-827c-4cb8-9fd1-4adcc54de77d.md))_

## verify-evidence-view-readme

### Acceptance
- **verify-evidence-view-readme**: R5; check; dashboard; grep -qi 'requirement detail' README.md && grep -q 'verified' README.md && grep -qi 'release ready' README.md && grep -qi 'stage' README.md _(id: [rec-338cf500-251e-4741-8168-ea67b1147ccc](.artifacts/records/project__acceptance/rec-338cf500-251e-4741-8168-ea67b1147ccc.md))_

## verify-evidence-view-suite

### Acceptance
- **verify-evidence-view-suite**: R9; check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-ffb67717-3553-4bc6-9497-fb877731866f](.artifacts/records/project__acceptance/rec-ffb67717-3553-4bc6-9497-fb877731866f.md))_

## verify-human-gates

### Acceptance
- **verify-human-gates**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_integration.py -q -k "gates or once" _(id: [rec-c61f4280-d622-4017-83d1-4a8222faed84](.artifacts/records/project__acceptance/rec-c61f4280-d622-4017-83d1-4a8222faed84.md))_

## verify-human-gates-app

### Acceptance
- **verify-human-gates-app**: R3; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k gates _(id: [rec-d63e9f38-6953-44e4-a67f-8793531de963](.artifacts/records/project__acceptance/rec-d63e9f38-6953-44e4-a67f-8793531de963.md))_

## verify-human-gates-model

### Acceptance
- **verify-human-gates-model**: R5; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_gates.py -q -k gates _(id: [rec-8ca825cb-80c2-47cc-9b12-ebfeb449dca9](.artifacts/records/project__acceptance/rec-8ca825cb-80c2-47cc-9b12-ebfeb449dca9.md))_

## verify-human-gates-suite

### Acceptance
- **verify-human-gates-suite**: R11; check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m "not tmux" && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-84b6b2c0-f0cc-49a6-93fd-ebd2e5390f9a](.artifacts/records/project__acceptance/rec-84b6b2c0-f0cc-49a6-93fd-ebd2e5390f9a.md))_

## verify-human-gates-tmux

### Acceptance
- **verify-human-gates-tmux**: R8; check; dashboard; uv run --with textual --with pytest python -m pytest tests -q -m tmux -k "status and (gates or needs or segment)" _(id: [rec-fa10fcaa-3669-4d69-a554-844faf4d41b6](.artifacts/records/project__acceptance/rec-fa10fcaa-3669-4d69-a554-844faf4d41b6.md))_

## verify-installer-wizard

### Acceptance
- **verify-installer-wizard**: R1; check; packaging; python3 -m pytest tests/integration/test_installer_wizard.py -q -k interactive _(id: [rec-acf4a6db-a339-4336-b3f3-0e8ac7c2de8e](.artifacts/records/project__acceptance/rec-acf4a6db-a339-4336-b3f3-0e8ac7c2de8e.md))_

## verify-installer-wizard-decline

### Acceptance
- **verify-installer-wizard-decline**: R9; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k decline_writes_nothing _(id: [rec-74169835-5c97-4b3e-9231-bffe6d6c030e](.artifacts/records/project__acceptance/rec-74169835-5c97-4b3e-9231-bffe6d6c030e.md))_

## verify-installer-wizard-detection

### Acceptance
- **verify-installer-wizard-detection**: R2; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k detect_hosts _(id: [rec-4530d459-8eb9-4209-a3ef-7e6c8f8de50d](.artifacts/records/project__acceptance/rec-4530d459-8eb9-4209-a3ef-7e6c8f8de50d.md))_

## verify-installer-wizard-docs

### Acceptance
- **verify-installer-wizard-docs**: R18; check; packaging; python3 -m pytest tests/test_readme_matrix.py -q -k "wizard or documented_flags" _(id: [rec-1b604149-4595-4b3a-92d1-ead9d4b9777d](.artifacts/records/project__acceptance/rec-1b604149-4595-4b3a-92d1-ead9d4b9777d.md))_

## verify-installer-wizard-dry-run

### Acceptance
- **verify-installer-wizard-dry-run**: R16; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k dry_run_skips_confirmation _(id: [rec-f93569c3-5532-41a7-a270-7a5370d7169f](.artifacts/records/project__acceptance/rec-f93569c3-5532-41a7-a270-7a5370d7169f.md))_

## verify-installer-wizard-empty

### Acceptance
- **verify-installer-wizard-empty**: R14; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k no_detection_no_tty _(id: [rec-aa8e61d2-36cf-45f3-b20a-6486e51f00e2](.artifacts/records/project__acceptance/rec-aa8e61d2-36cf-45f3-b20a-6486e51f00e2.md))_

## verify-installer-wizard-explicit

### Acceptance
- **verify-installer-wizard-explicit**: R15; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k explicit_flags _(id: [rec-8e8f839f-0410-4871-9823-48a5f66a77bf](.artifacts/records/project__acceptance/rec-8e8f839f-0410-4871-9823-48a5f66a77bf.md))_

## verify-installer-wizard-interactive

### Acceptance
- **verify-installer-wizard-interactive**: R12; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k interactive_flag _(id: [rec-cc55da6d-936d-404e-a8d1-869ae468d85c](.artifacts/records/project__acceptance/rec-cc55da6d-936d-404e-a8d1-869ae468d85c.md))_

## verify-installer-wizard-list

### Acceptance
- **verify-installer-wizard-list**: R10; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k list_prints_matrix _(id: [rec-65ba7907-50e3-45e3-bc15-2b70be1216fb](.artifacts/records/project__acceptance/rec-65ba7907-50e3-45e3-bc15-2b70be1216fb.md))_

## verify-installer-wizard-noninteractive

### Acceptance
- **verify-installer-wizard-noninteractive**: R13; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k non_interactive _(id: [rec-76ceed00-92a2-45bd-8d57-ff55f5da6bc2](.artifacts/records/project__acceptance/rec-76ceed00-92a2-45bd-8d57-ff55f5da6bc2.md))_

## verify-installer-wizard-plan

### Acceptance
- **verify-installer-wizard-plan**: R8; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k plan_confirmation _(id: [rec-7eef54c2-8e15-4f80-b9c7-14248672160c](.artifacts/records/project__acceptance/rec-7eef54c2-8e15-4f80-b9c7-14248672160c.md))_

## verify-installer-wizard-scope

### Acceptance
- **verify-installer-wizard-scope**: R11; check; packaging; python3 -m pytest tests/test_installer_wizard.py -q -k scope_flag _(id: [rec-079ec8d1-3ec5-4f7e-a748-d094ee954f85](.artifacts/records/project__acceptance/rec-079ec8d1-3ec5-4f7e-a748-d094ee954f85.md))_

## verify-journal-view

### Acceptance
- **verify-journal-view**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_journal.py tests/test_dashboard_app.py -q -k journal _(id: [rec-23b9ae39-56ef-401b-b2df-9b05b78d4967](.artifacts/records/project__acceptance/rec-23b9ae39-56ef-401b-b2df-9b05b78d4967.md))_

## verify-journal-view-suite

### Acceptance
- **verify-journal-view-suite**: R9; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_journal.py tests/test_dashboard_app.py -q -k journal _(id: [rec-628b0b42-c0af-421a-a077-8f9238c5eb0b](.artifacts/records/project__acceptance/rec-628b0b42-c0af-421a-a077-8f9238c5eb0b.md))_

## verify-layout-phase

### Acceptance
- **verify-layout-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux -rf _(id: [rec-5d64f143-cdea-49dc-8cb4-7ca9fb9f2517](.artifacts/records/project__acceptance/rec-5d64f143-cdea-49dc-8cb4-7ca9fb9f2517.md))_

## verify-milestone-nav

### Work
- **verify-milestone-nav**: Verify milestone-nav; milestone-nav; deliver; dashboard _(id: [rec-e84c286f-6ece-4473-8270-ccb055ab5f7f](.artifacts/records/project__work-item/rec-e84c286f-6ece-4473-8270-ccb055ab5f7f.md))_

### Acceptance
- **verify-milestone-nav**: R1; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestones.test.ts src/milestoneNav.test.ts _(id: [rec-2bc35113-9f94-41d8-966d-6f05da4eb36e](.artifacts/records/project__acceptance/rec-2bc35113-9f94-41d8-966d-6f05da4eb36e.md))_

## verify-milestone-nav-collapse

### Acceptance
- **verify-milestone-nav-collapse**: R7; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestones.test.ts -t R7 _(id: [rec-9a9e8ab6-940c-47e3-8f7d-0794f661b0a2](.artifacts/records/project__acceptance/rec-9a9e8ab6-940c-47e3-8f7d-0794f661b0a2.md))_

## verify-milestone-nav-demo

### Acceptance
- **verify-milestone-nav-demo**: R2; manual; dashboard _(id: [rec-d0e08589-06f0-495e-8d77-b6847225d2bc](.artifacts/records/project__acceptance/rec-d0e08589-06f0-495e-8d77-b6847225d2bc.md))_

## verify-milestone-nav-flat

### Acceptance
- **verify-milestone-nav-flat**: R4; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestoneNav.test.ts -t R4 _(id: [rec-0b22571b-615f-4ee7-9dcc-9010f606b323](.artifacts/records/project__acceptance/rec-0b22571b-615f-4ee7-9dcc-9010f606b323.md))_

## verify-milestone-nav-scope

### Acceptance
- **verify-milestone-nav-scope**: R5; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/milestoneNav.test.ts -t R5 _(id: [rec-97b373dc-cd68-47cd-9c1a-95c221f28a7c](.artifacts/records/project__acceptance/rec-97b373dc-cd68-47cd-9c1a-95c221f28a7c.md))_

## verify-navigation-phase

### Acceptance
- **verify-navigation-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux -rf _(id: [rec-d1da938c-12b5-4cb9-9f02-e4a6731c1222](.artifacts/records/project__acceptance/rec-d1da938c-12b5-4cb9-9f02-e4a6731c1222.md))_

## verify-needs-you-close

### Acceptance
- **verify-needs-you-close**: R4; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k dismiss _(id: [rec-acabf3ed-70af-4c45-bbc2-55df0b063fec](.artifacts/records/project__acceptance/rec-acabf3ed-70af-4c45-bbc2-55df0b063fec.md))_

## verify-needs-you-close-refuse

### Acceptance
- **verify-needs-you-close-refuse**: R5; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'dismiss and (refuse or fail or error)' _(id: [rec-519937ac-4467-4bbd-8f45-7786679a7d4f](.artifacts/records/project__acceptance/rec-519937ac-4467-4bbd-8f45-7786679a7d4f.md))_

## verify-needs-you-close-skills

### Acceptance
- **verify-needs-you-close-skills**: R1; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_discuss_skill.py -q _(id: [rec-53401a27-dd75-4ef2-adbb-a699505dc9fc](.artifacts/records/project__acceptance/rec-53401a27-dd75-4ef2-adbb-a699505dc9fc.md))_

## verify-needs-you-data-phase

### Acceptance
- **verify-needs-you-data-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-fe83e6fe-5005-4c88-97e8-3c15e744047a](.artifacts/records/project__acceptance/rec-fe83e6fe-5005-4c88-97e8-3c15e744047a.md))_

## verify-needs-you-phase

### Acceptance
- **verify-needs-you-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-d5958a14-e6a7-4c20-b110-5ae0c0ee54a3](.artifacts/records/project__acceptance/rec-d5958a14-e6a7-4c20-b110-5ae0c0ee54a3.md))_

### Amendment
- **verify-needs-you-phase**: verify-needs-you-phase; dashboard-features _(id: [rec-3192a53d-1a55-41cb-8f06-71bdbabdcbd2](.artifacts/records/project__assignment-amendment/rec-3192a53d-1a55-41cb-8f06-71bdbabdcbd2.md))_

## verify-oracle-witnesses

### Acceptance
- **verify-oracle-witnesses**: R5; tdd; workflow-loop; python3 -m pytest tests/test_close_batch.py -q -k 'cli and (oracle or freeze or assertion_level or amendment)' _(id: [rec-c295c01e-9f40-460e-b8f9-4b0b26299a6e](.artifacts/records/project__acceptance/rec-c295c01e-9f40-460e-b8f9-4b0b26299a6e.md))_

### Amendment
- **verify-oracle-witnesses**: verify-oracle-witnesses; workflow-loop _(id: [rec-56ffac73-b6c4-41cd-bf78-b96f8158430b](.artifacts/records/project__assignment-amendment/rec-56ffac73-b6c4-41cd-bf78-b96f8158430b.md))_

## verify-oracle-witnesses-freeze-fields

### Acceptance
- **verify-oracle-witnesses-freeze-fields**: R3; check; workflow-loop; python3 -c "import json;from pathlib import Path;d=json.loads(Path('contract/project-design.json').read_text());a=next(t for t in d['records'] if t['name']=='acceptance');assert 'test_ids' in a['payload'] and 'oracle_hashes' in a['payload'];assert 'oracle-amendment' in {t['name'] for t in d['records']}" _(id: [rec-702fc0af-6e5d-4df2-ba30-0b17e614f28d](.artifacts/records/project__acceptance/rec-702fc0af-6e5d-4df2-ba30-0b17e614f28d.md))_

## verify-oracle-witnesses-mechanical-close

### Acceptance
- **verify-oracle-witnesses-mechanical-close**: R6; check; workflow-loop; python3 -m pytest tests/test_close_batch.py tests/test_oracle_red.py -q -k 'oracle or freeze or assertion_level' _(id: [rec-e671315a-55d8-4a48-82a8-29555da56b42](.artifacts/records/project__acceptance/rec-e671315a-55d8-4a48-82a8-29555da56b42.md))_

## verify-oracle-witnesses-skills

### Acceptance
- **verify-oracle-witnesses-skills**: R7; check; workflow-loop; python3 -m pytest tests/test_skill_contract_consistency.py tests/test_oracle_red.py -q _(id: [rec-f05bed1e-a34d-456b-9979-59572fc49c56](.artifacts/records/project__acceptance/rec-f05bed1e-a34d-456b-9979-59572fc49c56.md))_

## verify-path-test-gaps

### Acceptance
- **verify-path-test-gaps**: R5; tdd; workflow-loop; python3 -m pytest tests/test_affidavit_check.py tests/test_close_batch.py -k 'worktree or cwd_primary or store_cwd' -q _(id: [rec-42e9d09d-8bf3-4c5c-8abf-ba99dc9533c2](.artifacts/records/project__acceptance/rec-42e9d09d-8bf3-4c5c-8abf-ba99dc9533c2.md))_

## verify-path-test-gaps-mutants

### Acceptance
- **verify-path-test-gaps-mutants**: R6; tdd; workflow-loop; python3 -m pytest tests/test_affidavit_check.py -k 'timeout or empty_verify or cwd_forwarded or blocked_timeout' -q _(id: [rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e](.artifacts/records/project__acceptance/rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e.md))_

## verify-phase-landing

### Acceptance
- **verify-phase-landing**: tdd; workflow-loop; python3 -m pytest tests/test_phase_landing.py tests/test_plan_landing.py tests/test_execute_landing.py -q _(id: [rec-5f277ff6-f5de-48ae-a3fa-43825f135561](.artifacts/records/project__acceptance/rec-5f277ff6-f5de-48ae-a3fa-43825f135561.md))_

## verify-phase-landing-execute

### Acceptance
- **verify-phase-landing-execute**: tdd; workflow-loop; python3 -m pytest tests/test_execute_landing.py -q _(id: [rec-c376fad0-9993-4448-9e97-21adc7a1ec8d](.artifacts/records/project__acceptance/rec-c376fad0-9993-4448-9e97-21adc7a1ec8d.md))_

## verify-phase-landing-plan

### Acceptance
- **verify-phase-landing-plan**: tdd; workflow-loop; python3 -m pytest tests/test_plan_landing.py -q _(id: [rec-58522d3a-4f28-4cd8-bcf8-4f8ab951dd54](.artifacts/records/project__acceptance/rec-58522d3a-4f28-4cd8-bcf8-4f8ab951dd54.md))_

## verify-phase-proof-packet

### Acceptance
- **verify-phase-proof-packet**: R1; check; workflow-loop; python3 -m pytest tests/test_proof_packet_smoke.py -q _(id: [rec-c5fcd5d0-174f-488f-8582-6da3b29d4380](.artifacts/records/project__acceptance/rec-c5fcd5d0-174f-488f-8582-6da3b29d4380.md))_

## verify-phase-proof-packet-aff

### Acceptance
- **verify-phase-proof-packet-aff**: R5; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_aff_hooks_and_incidental -q _(id: [rec-820335d0-4534-4dd1-ae84-a99cc199f21e](.artifacts/records/project__acceptance/rec-820335d0-4534-4dd1-ae84-a99cc199f21e.md))_

## verify-phase-proof-packet-execute

### Acceptance
- **verify-phase-proof-packet-execute**: R4; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_assembles_proof_packet -q _(id: [rec-1320e937-f410-499c-9b9b-2d00af612b57](.artifacts/records/project__acceptance/rec-1320e937-f410-499c-9b9b-2d00af612b57.md))_

## verify-phase-proof-packet-handoff

### Acceptance
- **verify-phase-proof-packet-handoff**: R2; check; workflow-loop; python3 -m pytest tests/test_proof_packet_contract.py::test_handoff_latest_proof_role -q _(id: [rec-7890d964-d81b-43e2-af75-0bf270341fdb](.artifacts/records/project__acceptance/rec-7890d964-d81b-43e2-af75-0bf270341fdb.md))_

## verify-phase-proof-packet-incidental

### Acceptance
- **verify-phase-proof-packet-incidental**: R6; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_execute_aff_hooks_and_incidental -q _(id: [rec-aa688749-5f2f-4c3f-ae17-4564467fa7a0](.artifacts/records/project__acceptance/rec-aa688749-5f2f-4c3f-ae17-4564467fa7a0.md))_

## verify-phase-proof-packet-skills

### Acceptance
- **verify-phase-proof-packet-skills**: R3; check; workflow-loop; python3 -m pytest tests/test_proof_skills.py::test_settle_and_plan_require_proof_section -q _(id: [rec-9a89b92e-b3d6-4688-b1be-b8599bb5745b](.artifacts/records/project__acceptance/rec-9a89b92e-b3d6-4688-b1be-b8599bb5745b.md))_

## verify-phase-proof-packet-ui

### Acceptance
- **verify-phase-proof-packet-ui**: R7; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_proof_dashboard.py -q _(id: [rec-39cf9d37-3116-4b83-be09-b948e9f81574](.artifacts/records/project__acceptance/rec-39cf9d37-3116-4b83-be09-b948e9f81574.md))_

## verify-phase-reviewer

### Acceptance
- **verify-phase-reviewer**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q _(id: [rec-a5b4ff28-4664-45b7-9b25-489d4f58af19](.artifacts/records/project__acceptance/rec-a5b4ff28-4664-45b7-9b25-489d4f58af19.md))_

## verify-phase-reviewer-agent

### Acceptance
- **verify-phase-reviewer-agent**: R1; check; workflow-loop; test -f agents/se-reviewer.md && grep -qiE "no Write|without Write" agents/se-reviewer.md && grep -q agents/ scripts/sync-plugin.sh && grep -qiE "reviewer|se-reviewer" skills/execute-phase/SKILL.md _(id: [rec-1c47f604-3a3d-43ce-b488-7f0dc461180e](.artifacts/records/project__acceptance/rec-1c47f604-3a3d-43ce-b488-7f0dc461180e.md))_

## verify-phase-reviewer-contract

### Acceptance
- **verify-phase-reviewer-contract**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_contract_self_consistency.py -q _(id: [rec-5fe7f197-7081-4e2e-a8dd-bd9014170eaf](.artifacts/records/project__acceptance/rec-5fe7f197-7081-4e2e-a8dd-bd9014170eaf.md))_

## verify-phase-reviewer-fixture

### Acceptance
- **verify-phase-reviewer-fixture**: R7; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k status_tabs _(id: [rec-14227c0e-f22a-4354-92b7-eb89f4eba878](.artifacts/records/project__acceptance/rec-14227c0e-f22a-4354-92b7-eb89f4eba878.md))_

## verify-phase-reviewer-gate

### Acceptance
- **verify-phase-reviewer-gate**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k gate _(id: [rec-47250685-0161-4993-80af-7bd73bdce32b](.artifacts/records/project__acceptance/rec-47250685-0161-4993-80af-7bd73bdce32b.md))_

## verify-phase-selector

### Acceptance
- **verify-phase-selector**: R14; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_integration.py -q -k once _(id: [rec-a14d5cc4-9daf-4279-9625-b803a75d93cb](.artifacts/records/project__acceptance/rec-a14d5cc4-9daf-4279-9625-b803a75d93cb.md))_

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

## verify-plugin-dep-marketplace-readme

### Acceptance
- **verify-plugin-dep-marketplace-readme**: R4; check; packaging; grep -q 'claude plugin marketplace add andrewy1n/se-workflow' README.md && grep -qi Cursor README.md && ! grep -qiE 'Cursor.*(auto-?install|plugin dependenc).*adaptive-artifacts' README.md _(id: [rec-c30aaca7-94df-4c02-a6f3-fcce0c8d6b00](.artifacts/records/project__acceptance/rec-c30aaca7-94df-4c02-a6f3-fcce0c8d6b00.md))_

## verify-plugin-root-and-cli

### Acceptance
- **verify-plugin-root-and-cli**: R2; tdd; packaging; uv run --with pytest python -m pytest tests/test_aa_resolve.py -q && grep -q CLAUDE_PLUGIN_ROOT skills/ensure-store.md && grep -q CURSOR_PLUGIN_ROOT skills/ensure-store.md && ! grep -E '^[0-9]+\. .*\.cursor/plugins/local/se-workflow' skills/ensure-store.md && ! grep -n "Path.home() / \"adaptive-artifacts\"" se_workflow/aa.py dashboard/artifact_store.py _(id: [rec-d1532551-f82b-44a4-94c5-de313a93d078](.artifacts/records/project__acceptance/rec-d1532551-f82b-44a4-94c5-de313a93d078.md))_

## verify-plugin-root-and-cli-close

### Acceptance
- **verify-plugin-root-and-cli-close**: R3; tdd; packaging; uv run --with pytest python -m pytest tests/test_close_batch.py -q && grep -qE 'se-workflow close-batch|bin/se-workflow close-batch' skills/verify-work/SKILL.md && ! grep -q scripts/close_batch.py skills/verify-work/SKILL.md && uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-db3cca7b-c7b5-482b-be36-b59f59c5621b](.artifacts/records/project__acceptance/rec-db3cca7b-c7b5-482b-be36-b59f59c5621b.md))_

## verify-plugin-root-and-cli-landing

### Acceptance
- **verify-plugin-root-and-cli-landing**: R4; manual; packaging _(id: [rec-e2174663-bdbf-4250-aa23-5075f95e0c8d](.artifacts/records/project__acceptance/rec-e2174663-bdbf-4250-aa23-5075f95e0c8d.md))_

## verify-pyproject-pypi

### Acceptance
- **verify-pyproject-pypi**: R2; check; packaging; ~/adaptive-artifacts/scripts/prove_uv_tool_install.sh _(id: [rec-080abeb4-e1c8-4c6d-a325-fa84f67bf3a5](.artifacts/records/project__acceptance/rec-080abeb4-e1c8-4c6d-a325-fa84f67bf3a5.md))_

## verify-pyproject-pypi-aa-gate

### Acceptance
- **verify-pyproject-pypi-aa-gate**: R8; manual; packaging _(id: [rec-cd94256a-2af1-4b2a-894c-58ebd9cb594f](.artifacts/records/project__acceptance/rec-cd94256a-2af1-4b2a-894c-58ebd9cb594f.md))_

## verify-pyproject-pypi-readme

### Acceptance
- **verify-pyproject-pypi-readme**: R6; check; packaging; grep -qiE "uv tool install" README.md && grep -qiE "git\+https://github.com/andrewy1n/adaptive-artifacts" README.md && grep -qiE "PyPI.*(defer|later|not yet|wait)" README.md && ! test -f pyproject.toml _(id: [rec-df1c71df-699a-42b3-ae6d-8c7d0a764007](.artifacts/records/project__acceptance/rec-df1c71df-699a-42b3-ae6d-8c7d0a764007.md))_

## verify-pyproject-pypi-shims

### Acceptance
- **verify-pyproject-pypi-shims**: R4; check; packaging; ~/adaptive-artifacts/bin/adaptive-artifacts --help >/dev/null && python3 ~/adaptive-artifacts/tools/artifacts.py --help >/dev/null _(id: [rec-064ae8ac-d426-4a95-a9a5-71cd77ec4dfd](.artifacts/records/project__acceptance/rec-064ae8ac-d426-4a95-a9a5-71cd77ec4dfd.md))_

## verify-quiet-header

### Acceptance
- **verify-quiet-header**: check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k once_tally _(id: [rec-bc634371-b551-458a-a1c6-a010d02af538](.artifacts/records/project__acceptance/rec-bc634371-b551-458a-a1c6-a010d02af538.md))_

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

## verify-readable-layout-phase-signoff

### Acceptance
- **verify-readable-layout-phase-signoff**: manual; dashboard _(id: [rec-83820e9f-6ff5-407c-aa8f-deb4e441d5a5](.artifacts/records/project__acceptance/rec-83820e9f-6ff5-407c-aa8f-deb4e441d5a5.md))_

## verify-red-first

### Acceptance
- **verify-red-first**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_pass_only _(id: [rec-c954223e-18ce-4392-ba4a-051f35046275](.artifacts/records/project__acceptance/rec-c954223e-18ce-4392-ba4a-051f35046275.md))_

## verify-red-first-escape

### Acceptance
- **verify-red-first-escape**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_escape _(id: [rec-964973af-b0ff-4bdc-b880-c49820487c8a](.artifacts/records/project__acceptance/rec-964973af-b0ff-4bdc-b880-c49820487c8a.md))_

## verify-red-first-methods

### Acceptance
- **verify-red-first-methods**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_other_methods _(id: [rec-9167287b-ab92-4409-89bd-e19a6db7f820](.artifacts/records/project__acceptance/rec-9167287b-ab92-4409-89bd-e19a6db7f820.md))_

## verify-red-first-order

### Acceptance
- **verify-red-first-order**: R3; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_order _(id: [rec-cb28d166-0f0f-49ed-8751-925ad1e8d708](.artifacts/records/project__acceptance/rec-cb28d166-0f0f-49ed-8751-925ad1e8d708.md))_

## verify-red-first-skills

### Acceptance
- **verify-red-first-skills**: R6; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_assess_routing.py -q _(id: [rec-5990039c-6afc-47d7-9a08-43aafa3d1a8e](.artifacts/records/project__acceptance/rec-5990039c-6afc-47d7-9a08-43aafa3d1a8e.md))_

## verify-rename-agent-affidavit

### Acceptance
- **verify-rename-agent-affidavit**: R2; tdd; packaging; test -x bin/aff && ! test -e bin/se-workflow && bin/aff check --help >/dev/null && bin/aff close-batch --help >/dev/null && python3 -c "import importlib.util as u; assert u.find_spec('affidavit'); assert u.find_spec('se_workflow') is None" _(id: [rec-d5e70a1b-64c9-4d59-9de9-81f5d57e751f](.artifacts/records/project__acceptance/rec-d5e70a1b-64c9-4d59-9de9-81f5d57e751f.md))_

## verify-rename-agent-affidavit-identity

### Acceptance
- **verify-rename-agent-affidavit-identity**: R1; check; packaging; python3 scripts/check_affidavit_plugin_names.py && python3 scripts/check_affidavit_contract_project.py && uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q _(id: [rec-63816a0d-c37b-4fb3-8bbf-a0a33a762939](.artifacts/records/project__acceptance/rec-63816a0d-c37b-4fb3-8bbf-a0a33a762939.md))_

## verify-retry-loop

### Acceptance
- **verify-retry-loop**: R1; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_retry_loop.py -q _(id: [rec-882f6075-f91a-479c-b426-a0eee0ffba59](.artifacts/records/project__acceptance/rec-882f6075-f91a-479c-b426-a0eee0ffba59.md))_

## verify-retry-loop-contract

### Acceptance
- **verify-retry-loop-contract**: R9; check; workflow-loop; uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_contract_self_consistency.py -q _(id: [rec-0b667469-29df-4007-a46b-05a8b860091a](.artifacts/records/project__acceptance/rec-0b667469-29df-4007-a46b-05a8b860091a.md))_

## verify-retry-loop-dashboard

### Acceptance
- **verify-retry-loop-dashboard**: R8; tdd; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k "attempt_row or attempt_budget or attempt_snapshot or attempt_title" _(id: [rec-7d873780-5fa8-4f70-af41-851701195ec5](.artifacts/records/project__acceptance/rec-7d873780-5fa8-4f70-af41-851701195ec5.md))_

## verify-run-facts

### Acceptance
- **verify-run-facts**: R1; tdd; dashboard; uv run --with pytest python -m pytest tests/test_estimate_cli.py -q _(id: [rec-421c70cd-39cf-4be7-8247-8e651bd0617d](.artifacts/records/project__acceptance/rec-421c70cd-39cf-4be7-8247-8e651bd0617d.md))_

## verify-run-facts-contract

### Acceptance
- **verify-run-facts-contract**: R2; check; dashboard; uv run --with pytest python -m pytest tests/test_estimate_contract.py -q _(id: [rec-559ae6f2-7bcd-483a-b04a-47312542235e](.artifacts/records/project__acceptance/rec-559ae6f2-7bcd-483a-b04a-47312542235e.md))_

## verify-run-facts-dashboard

### Acceptance
- **verify-run-facts-dashboard**: R6; check; dashboard; test -z "$(git diff --name-only main -- dashboard/)" _(id: [rec-3a8cb50a-c1bf-4698-8b25-1a91d9ad70a2](.artifacts/records/project__acceptance/rec-3a8cb50a-c1bf-4698-8b25-1a91d9ad70a2.md))_

## verify-run-facts-skill

### Acceptance
- **verify-run-facts-skill**: R3; check; dashboard; uv run --with pytest python -m pytest tests/test_estimate_skill.py tests/test_skill_contract_consistency.py tests/test_plan_wave_rules.py tests/test_plan_trace.py -q _(id: [rec-a7ce611e-022e-44b3-a49b-512336cf04a6](.artifacts/records/project__acceptance/rec-a7ce611e-022e-44b3-a49b-512336cf04a6.md))_

## verify-run-facts-suite

### Acceptance
- **verify-run-facts-suite**: R1; check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m "not tmux" && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-b43db00d-52de-4ffe-ba39-07011280cbbb](.artifacts/records/project__acceptance/rec-b43db00d-52de-4ffe-ba39-07011280cbbb.md))_

## verify-spec-view

### Acceptance
- **verify-spec-view**: R2; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py tests/test_dashboard_integration.py -q -k "phase_screen or once" _(id: [rec-323fc48e-f2ba-4fcf-bea1-344c61a9f338](.artifacts/records/project__acceptance/rec-323fc48e-f2ba-4fcf-bea1-344c61a9f338.md))_

### Amendment
- **verify-spec-view**: verify-spec-view; dashboard _(id: [rec-44e67a63-0663-4353-bedd-0d19e0916041](.artifacts/records/project__assignment-amendment/rec-44e67a63-0663-4353-bedd-0d19e0916041.md))_

## verify-spec-view-model

### Acceptance
- **verify-spec-view-model**: R7; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py -q -k phase_screen _(id: [rec-b45738a2-3a4d-4384-8296-2710d92c7f41](.artifacts/records/project__acceptance/rec-b45738a2-3a4d-4384-8296-2710d92c7f41.md))_

## verify-spec-view-suite

### Acceptance
- **verify-spec-view-suite**: R13; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py tests/test_dashboard_integration.py -q -k "phase_screen or once" _(id: [rec-09c72984-b31a-4157-a36c-f922a4700458](.artifacts/records/project__acceptance/rec-09c72984-b31a-4157-a36c-f922a4700458.md))_

## verify-status-line-phase

### Acceptance
- **verify-status-line-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-2e2b15a3-c245-48ab-874a-9efbfd69ff60](.artifacts/records/project__acceptance/rec-2e2b15a3-c245-48ab-874a-9efbfd69ff60.md))_

## verify-table-state-phase

### Acceptance
- **verify-table-state-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux _(id: [rec-c31c7b82-4a88-43bf-877c-1ffabb4f08e3](.artifacts/records/project__acceptance/rec-c31c7b82-4a88-43bf-877c-1ffabb4f08e3.md))_

## verify-task-details-phase

### Acceptance
- **verify-task-details-phase**: check; dashboard; uv run --with textual --with pytest python -m pytest tests -q _(id: [rec-98ab04e9-ab1a-488f-8712-716c9a11b7ba](.artifacts/records/project__acceptance/rec-98ab04e9-ab1a-488f-8712-716c9a11b7ba.md))_

## verify-task-details-phase-signoff

### Acceptance
- **verify-task-details-phase-signoff**: manual; dashboard _(id: [rec-11643a9d-4693-4761-b94a-ba3a6be27ad6](.artifacts/records/project__acceptance/rec-11643a9d-4693-4761-b94a-ba3a6be27ad6.md))_

## verify-task-navigation-phase

### Acceptance
- **verify-task-navigation-phase**: check; dashboard; uv run --with textual --with pytest python -m pytest tests -q _(id: [rec-b9307639-88bf-43f4-8ad7-d0e4a77db060](.artifacts/records/project__acceptance/rec-b9307639-88bf-43f4-8ad7-d0e4a77db060.md))_

## verify-task-navigation-phase-signoff

### Acceptance
- **verify-task-navigation-phase-signoff**: manual; dashboard _(id: [rec-892a40a7-5d4e-4027-a096-a484d58b9787](.artifacts/records/project__acceptance/rec-892a40a7-5d4e-4027-a096-a484d58b9787.md))_

## verify-task-rows-phase

### Acceptance
- **verify-task-rows-phase**: check; dashboard; uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m 'not tmux' && uv run --with textual --with pytest python -m pytest tests -q -m tmux -rf _(id: [rec-92df6b15-9068-4342-b3fa-899bc28247b3](.artifacts/records/project__acceptance/rec-92df6b15-9068-4342-b3fa-899bc28247b3.md))_

## verify-tiered-verification

### Acceptance
- **verify-tiered-verification**: R2; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "runner or background or check_run" _(id: [rec-e094b9fe-4161-4ebd-81ad-00b66dce7444](.artifacts/records/project__acceptance/rec-e094b9fe-4161-4ebd-81ad-00b66dce7444.md))_

## verify-tiered-verification-fix

### Acceptance
- **verify-tiered-verification-fix**: R5; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k "fix or cluster or budget" _(id: [rec-3441488d-4728-4c7e-855a-ef05fc967f31](.artifacts/records/project__acceptance/rec-3441488d-4728-4c7e-855a-ef05fc967f31.md))_

## verify-tiered-verification-gate

### Acceptance
- **verify-tiered-verification-gate**: R4; tdd; workflow-loop; uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k gate _(id: [rec-6c629730-fc3a-4ca1-9d42-88c84c5b8b34](.artifacts/records/project__acceptance/rec-6c629730-fc3a-4ca1-9d42-88c84c5b8b34.md))_

## verify-tiered-verification-surfaces

### Acceptance
- **verify-tiered-verification-surfaces**: R6; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k tier2 && uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-07249524-c6b9-49bf-8823-074594abbd01](.artifacts/records/project__acceptance/rec-07249524-c6b9-49bf-8823-074594abbd01.md))_

## verify-tmux-integration-phase

### Acceptance
- **verify-tmux-integration-phase**: tdd; dashboard; cd ~/se-workflow && python3 -m pytest tests/test_tmux_integration.py -q _(id: [rec-66a8f44a-bfea-4ee2-aea0-cbe426d17d69](.artifacts/records/project__acceptance/rec-66a8f44a-bfea-4ee2-aea0-cbe426d17d69.md))_

## verify-tmux-integration-phase-suites

### Acceptance
- **verify-tmux-integration-phase-suites**: check; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q && cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-4a323bc2-c820-4133-8409-d9be1a13b97a](.artifacts/records/project__acceptance/rec-4a323bc2-c820-4133-8409-d9be1a13b97a.md))_

## verify-tmux-plugin-entry

### Acceptance
- **verify-tmux-plugin-entry**: tdd; dashboard; uv run --with pytest --with textual pytest -m tmux tests/test_tmux_integration.py tests/test_e2e_dashboard.py tests/test_tmux_entry.py _(id: [rec-307dcaee-56c1-444b-8e02-b54d47eb903a](.artifacts/records/project__acceptance/rec-307dcaee-56c1-444b-8e02-b54d47eb903a.md))_

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

## verify-verification-policy-contract

### Acceptance
- **verify-verification-policy-contract**: R1; check; workflow-loop; uv run --with pytest python -m pytest tests/test_contract_self_consistency.py -q -k phase_gate && python3 -c "import json; from pathlib import Path; b=json.loads(Path('contract/project-design.json').read_text())['phase_gate']['suite']; assert b['mode']=='none'; s=json.loads(Path('.artifacts/project-design.json').read_text())['phase_gate']['suite']; assert s['mode']=='full' and s['gate']=='advisory'" _(id: [rec-6992e9a1-3262-42cf-97d9-ae33c2935da4](.artifacts/records/project__acceptance/rec-6992e9a1-3262-42cf-97d9-ae33c2935da4.md))_

## verify-verification-policy-surfaces

### Acceptance
- **verify-verification-policy-surfaces**: R5; check; workflow-loop; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k suite && uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-0e593cda-ace5-410a-b548-a5ab4c5c18fd](.artifacts/records/project__acceptance/rec-0e593cda-ace5-410a-b548-a5ab4c5c18fd.md))_

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

## verify-verify-budget-skills

### Acceptance
- **verify-verify-budget-skills**: R1; check; workflow-loop; uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q _(id: [rec-fe773a87-15bf-4633-9fc3-54fe95587755](.artifacts/records/project__acceptance/rec-fe773a87-15bf-4633-9fc3-54fe95587755.md))_

## verify-waits-on-compact

### Acceptance
- **verify-waits-on-compact**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'waiting_row or waits' _(id: [rec-2229ea3a-838b-401d-a6cf-cfe1a00067db](.artifacts/records/project__acceptance/rec-2229ea3a-838b-401d-a6cf-cfe1a00067db.md))_

## verify-waits-on-compact-detail

### Acceptance
- **verify-waits-on-compact-detail**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'detail and (Depends or blocked)' _(id: [rec-adf5aef7-5c16-4f3a-bd91-f3b8a49d2e84](.artifacts/records/project__acceptance/rec-adf5aef7-5c16-4f3a-bd91-f3b8a49d2e84.md))_

## verify-waits-on-compact-suite

### Acceptance
- **verify-waits-on-compact-suite**: R3; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_dashboard_tasks.py tests/test_dashboard_app.py -q -k 'waits or title_cell or waiting_row' _(id: [rec-2ad10a07-f300-4aee-b79c-4cabb9cb3e3f](.artifacts/records/project__acceptance/rec-2ad10a07-f300-4aee-b79c-4cabb9cb3e3f.md))_

## verify-watch-renderer-phase

### Acceptance
- **verify-watch-renderer-phase**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q -k watch_integration _(id: [rec-cadda757-0424-444f-8ae1-31d415d18e6d](.artifacts/records/project__acceptance/rec-cadda757-0424-444f-8ae1-31d415d18e6d.md))_

## verify-watch-renderer-phase-suites

### Acceptance
- **verify-watch-renderer-phase-suites**: check; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q && cd ~/se-workflow && python3 -m pytest tests -q _(id: [rec-02bac654-25f6-4bc0-b6ec-5efa03a4941e](.artifacts/records/project__acceptance/rec-02bac654-25f6-4bc0-b6ec-5efa03a4941e.md))_

## verify-wave-executor

### Acceptance
- **verify-wave-executor**: tdd; workflow-loop; python3 -m pytest tests/test_wave_executor_phase.py -q _(id: [rec-5fe7bba7-cd21-447d-a698-ed9bb1379f58](.artifacts/records/project__acceptance/rec-5fe7bba7-cd21-447d-a698-ed9bb1379f58.md))_

## verify-wave-executor-execute

### Acceptance
- **verify-wave-executor-execute**: tdd; workflow-loop; python3 -m pytest tests/test_execute_wave_dispatch.py -q _(id: [rec-d8b61721-30cb-41fd-885d-85e673c7d6d7](.artifacts/records/project__acceptance/rec-d8b61721-30cb-41fd-885d-85e673c7d6d7.md))_

## verify-wave-executor-plan

### Acceptance
- **verify-wave-executor-plan**: tdd; workflow-loop; python3 -m pytest tests/test_plan_wave_rules.py -q _(id: [rec-61bdf854-1a06-491f-8af6-aeda309ec357](.artifacts/records/project__acceptance/rec-61bdf854-1a06-491f-8af6-aeda309ec357.md))_

## verify-web-dashboard

### Acceptance
- **verify-web-dashboard**: R1; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r1_loopback -q _(id: [rec-a0a942d1-9498-4c85-be22-ed91224e3c51](.artifacts/records/project__acceptance/rec-a0a942d1-9498-4c85-be22-ed91224e3c51.md))_

## verify-web-dashboard-api

### Acceptance
- **verify-web-dashboard-api**: R21; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py -q -k 'snapshot or token or approve or reject or sign or signer or accept_note or refused or backlog or stale' _(id: [rec-9a2e2a15-7ba6-4893-a2ae-9b818d4d101b](.artifacts/records/project__acceptance/rec-9a2e2a15-7ba6-4893-a2ae-9b818d4d101b.md))_

## verify-web-dashboard-build

### Acceptance
- **verify-web-dashboard-build**: R30; check; dashboard; npm --prefix dashboard/web/ui run build && uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r30_serves_build -q _(id: [rec-a7887505-0f2e-4300-8417-e14f31924643](.artifacts/records/project__acceptance/rec-a7887505-0f2e-4300-8417-e14f31924643.md))_

## verify-web-dashboard-store

### Acceptance
- **verify-web-dashboard-store**: R2; check; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r2_same_store -q _(id: [rec-45a69ce8-9954-4521-a332-3b7b311543ee](.artifacts/records/project__acceptance/rec-45a69ce8-9954-4521-a332-3b7b311543ee.md))_

## watch-command

### Acceptance
- **watch-command**: tdd; dashboard; cd ~/adaptive-artifacts && python3 -m pytest tools/runtime/tests -q _(id: [rec-ec792cef-650b-492a-ac2d-eed325546c19](.artifacts/records/project__acceptance/rec-ec792cef-650b-492a-ac2d-eed325546c19.md))_

## web-launcher

### Acceptance
- **web-launcher**: R1; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r1_loopback -q _(id: [rec-7a86817f-5f89-4984-895a-d94f86fa0cff](.artifacts/records/project__acceptance/rec-7a86817f-5f89-4984-895a-d94f86fa0cff.md))_

## web-launcher-r2

### Acceptance
- **web-launcher-r2**: R2; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r2_same_store -q _(id: [rec-c07ba87d-fac0-453e-9d85-5633e2d11198](.artifacts/records/project__acceptance/rec-c07ba87d-fac0-453e-9d85-5633e2d11198.md))_

## web-launcher-r30

### Acceptance
- **web-launcher-r30**: R30; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard_launch.py::test_r30_serves_build -q _(id: [rec-4330f7e7-99ff-4cc6-be02-27c78971fba1](.artifacts/records/project__acceptance/rec-4330f7e7-99ff-4cc6-be02-27c78971fba1.md))_

## web-read-api

### Acceptance
- **web-read-api**: R3; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r3_snapshot -q _(id: [rec-39750da5-4bed-4a37-b46b-012d58a8be55](.artifacts/records/project__acceptance/rec-39750da5-4bed-4a37-b46b-012d58a8be55.md))_

## web-read-api-r4

### Acceptance
- **web-read-api-r4**: R4; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r4_token -q _(id: [rec-ceb6e37a-647b-44c6-a74b-a4662a589b8d](.artifacts/records/project__acceptance/rec-ceb6e37a-647b-44c6-a74b-a4662a589b8d.md))_

## web-ui-actions

### Acceptance
- **web-ui-actions**: R20; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/actions.test.ts -t R20 _(id: [rec-87efd039-2c55-4091-842b-2f1f8fdfa4ac](.artifacts/records/project__acceptance/rec-87efd039-2c55-4091-842b-2f1f8fdfa4ac.md))_

## web-ui-actions-r27

### Acceptance
- **web-ui-actions-r27**: R27; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/actions.test.ts -t R27 _(id: [rec-4d957b43-25b5-4fdc-be50-2200606af70a](.artifacts/records/project__acceptance/rec-4d957b43-25b5-4fdc-be50-2200606af70a.md))_

## web-ui-detail

### Acceptance
- **web-ui-detail**: R14; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R14 _(id: [rec-0d6a38bb-bc45-42a1-b025-3870a65c4fef](.artifacts/records/project__acceptance/rec-0d6a38bb-bc45-42a1-b025-3870a65c4fef.md))_

## web-ui-detail-r15

### Acceptance
- **web-ui-detail-r15**: R15; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R15 _(id: [rec-4ed43d96-3a8c-4458-864f-aa756818ca4b](.artifacts/records/project__acceptance/rec-4ed43d96-3a8c-4458-864f-aa756818ca4b.md))_

## web-ui-detail-r16

### Acceptance
- **web-ui-detail-r16**: R16; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R16 _(id: [rec-90f3f583-7e47-4375-a5ad-d13cc55eb3f9](.artifacts/records/project__acceptance/rec-90f3f583-7e47-4375-a5ad-d13cc55eb3f9.md))_

## web-ui-detail-r17

### Acceptance
- **web-ui-detail-r17**: R17; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R17 _(id: [rec-e12cb025-c028-4658-a406-c31efdc3dae8](.artifacts/records/project__acceptance/rec-e12cb025-c028-4658-a406-c31efdc3dae8.md))_

## web-ui-detail-r18

### Acceptance
- **web-ui-detail-r18**: R18; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R18 _(id: [rec-a40c0868-5897-4f8e-b2ac-7ef034005115](.artifacts/records/project__acceptance/rec-a40c0868-5897-4f8e-b2ac-7ef034005115.md))_

## web-ui-detail-r19

### Acceptance
- **web-ui-detail-r19**: R19; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/detail.test.ts -t R19 _(id: [rec-3f65034a-4cc6-4d11-9a4b-dd1e53ebe264](.artifacts/records/project__acceptance/rec-3f65034a-4cc6-4d11-9a4b-dd1e53ebe264.md))_

## web-ui-main

### Acceptance
- **web-ui-main**: R5; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R5 _(id: [rec-e7d85f56-4f37-4f13-9e82-edf9ad112beb](.artifacts/records/project__acceptance/rec-e7d85f56-4f37-4f13-9e82-edf9ad112beb.md))_

## web-ui-main-r10

### Acceptance
- **web-ui-main-r10**: R10; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R10 _(id: [rec-e0feebb8-d9a5-4c8b-8a50-6cafa4a0eea3](.artifacts/records/project__acceptance/rec-e0feebb8-d9a5-4c8b-8a50-6cafa4a0eea3.md))_

## web-ui-main-r32

### Acceptance
- **web-ui-main-r32**: R32; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R32 _(id: [rec-eb1dc00c-fb0b-4407-ab50-7e4a12e2ece9](.artifacts/records/project__acceptance/rec-eb1dc00c-fb0b-4407-ab50-7e4a12e2ece9.md))_

## web-ui-main-r33

### Acceptance
- **web-ui-main-r33**: R33; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R33 _(id: [rec-6fabe656-f50c-40cc-8910-d6cbb842aa98](.artifacts/records/project__acceptance/rec-6fabe656-f50c-40cc-8910-d6cbb842aa98.md))_

## web-ui-main-r6

### Acceptance
- **web-ui-main-r6**: R6; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R6 _(id: [rec-f36e227a-f954-4654-a364-e7472ed899ca](.artifacts/records/project__acceptance/rec-f36e227a-f954-4654-a364-e7472ed899ca.md))_

## web-ui-main-r7

### Acceptance
- **web-ui-main-r7**: R7; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R7 _(id: [rec-7b6d6bac-572f-42c3-8fe7-ec6de93c3559](.artifacts/records/project__acceptance/rec-7b6d6bac-572f-42c3-8fe7-ec6de93c3559.md))_

## web-ui-main-r8

### Acceptance
- **web-ui-main-r8**: R8; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R8 _(id: [rec-e8680ef6-df90-4957-be9d-85133eaf99b2](.artifacts/records/project__acceptance/rec-e8680ef6-df90-4957-be9d-85133eaf99b2.md))_

## web-ui-main-r9

### Acceptance
- **web-ui-main-r9**: R9; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/main.test.ts -t R9 _(id: [rec-89de12fa-d78d-497a-a4b8-b1fafc7442f9](.artifacts/records/project__acceptance/rec-89de12fa-d78d-497a-a4b8-b1fafc7442f9.md))_

## web-ui-scaffold

### Acceptance
- **web-ui-scaffold**: R31; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/scaffold.test.ts -t R31 _(id: [rec-987406c8-3ff3-475e-aea1-1a74584e5693](.artifacts/records/project__acceptance/rec-987406c8-3ff3-475e-aea1-1a74584e5693.md))_

## web-ui-scaffold-r35

### Acceptance
- **web-ui-scaffold-r35**: R35; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/scaffold.test.ts -t R35 _(id: [rec-15b25cbd-fd4c-419a-bb7f-808bee8f71bd](.artifacts/records/project__acceptance/rec-15b25cbd-fd4c-419a-bb7f-808bee8f71bd.md))_

## web-ui-scaffold-r36

### Acceptance
- **web-ui-scaffold-r36**: R36; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/scaffold.test.ts -t R36 _(id: [rec-2b879879-e526-4499-a9b6-a47e8b79653c](.artifacts/records/project__acceptance/rec-2b879879-e526-4499-a9b6-a47e8b79653c.md))_

## web-ui-side

### Acceptance
- **web-ui-side**: R11; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/side.test.ts -t R11 _(id: [rec-c86fdf26-17c0-4a94-ba8f-38366fc6c692](.artifacts/records/project__acceptance/rec-c86fdf26-17c0-4a94-ba8f-38366fc6c692.md))_

## web-ui-side-r12

### Acceptance
- **web-ui-side-r12**: R12; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/side.test.ts -t R12 _(id: [rec-77f4d05e-75d4-49a9-9ee0-f9a28ee00c6b](.artifacts/records/project__acceptance/rec-77f4d05e-75d4-49a9-9ee0-f9a28ee00c6b.md))_

## web-ui-side-r13

### Acceptance
- **web-ui-side-r13**: R13; check; dashboard; npm --prefix dashboard/web/ui exec vitest run src/side.test.ts -t R13 _(id: [rec-9d2656c6-797f-4f4a-b134-7f375d396110](.artifacts/records/project__acceptance/rec-9d2656c6-797f-4f4a-b134-7f375d396110.md))_

## web-write-api

### Acceptance
- **web-write-api**: R21; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r21_approve -q _(id: [rec-9b753d3c-769f-458b-a279-f9821408f1dd](.artifacts/records/project__acceptance/rec-9b753d3c-769f-458b-a279-f9821408f1dd.md))_

### Amendment
- **web-write-api**: web-write-api; dashboard _(id: [rec-2e47e731-b348-4f6a-a8fe-c3a9e7a444b7](.artifacts/records/project__assignment-amendment/rec-2e47e731-b348-4f6a-a8fe-c3a9e7a444b7.md))_

## web-write-api-r22

### Acceptance
- **web-write-api-r22**: R22; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r22_reject_note -q _(id: [rec-d32c9db3-448d-4fca-a0aa-d8b10bb49c8a](.artifacts/records/project__acceptance/rec-d32c9db3-448d-4fca-a0aa-d8b10bb49c8a.md))_

## web-write-api-r23

### Acceptance
- **web-write-api-r23**: R23; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r23_sign -q _(id: [rec-bc24f370-7c8a-44f7-9f4f-783754b2d3a5](.artifacts/records/project__acceptance/rec-bc24f370-7c8a-44f7-9f4f-783754b2d3a5.md))_

## web-write-api-r24

### Acceptance
- **web-write-api-r24**: R24; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r24_signer -q _(id: [rec-be370437-14d1-4c3e-8316-a940155e8cec](.artifacts/records/project__acceptance/rec-be370437-14d1-4c3e-8316-a940155e8cec.md))_

## web-write-api-r25

### Acceptance
- **web-write-api-r25**: R25; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r25_accept_note -q _(id: [rec-78629b0a-b92e-40cc-8c10-31c3a02dd766](.artifacts/records/project__acceptance/rec-78629b0a-b92e-40cc-8c10-31c3a02dd766.md))_

## web-write-api-r26

### Acceptance
- **web-write-api-r26**: R26; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r26_refused -q _(id: [rec-171cb043-59ae-41a2-bd02-431687ff5663](.artifacts/records/project__acceptance/rec-171cb043-59ae-41a2-bd02-431687ff5663.md))_

## web-write-api-r28

### Acceptance
- **web-write-api-r28**: R28; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r28_backlog_dismiss -q _(id: [rec-a9fc00b5-7ae8-4396-9013-c753ce9da519](.artifacts/records/project__acceptance/rec-a9fc00b5-7ae8-4396-9013-c753ce9da519.md))_

## web-write-api-r29

### Acceptance
- **web-write-api-r29**: R29; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r29_backlog_promote -q _(id: [rec-85c4cf39-fd64-41fa-8e03-3aa46331d06f](.artifacts/records/project__acceptance/rec-85c4cf39-fd64-41fa-8e03-3aa46331d06f.md))_

## web-write-api-r34

### Acceptance
- **web-write-api-r34**: R34; tdd; dashboard; uv run --with textual --with pytest python -m pytest tests/test_web_dashboard.py::test_r34_stale -q _(id: [rec-a3e1d953-95ac-48dc-a4e6-e5835b4e1a26](.artifacts/records/project__acceptance/rec-a3e1d953-95ac-48dc-a4e6-e5835b4e1a26.md))_

## workflow-loop

### Position
- **workflow-loop**: phase-proof-packet done; next up: evidence-kind or packaging backlog; effort _(id: [rec-ed13dfbc-5d73-403a-8113-3085a3ab08fa](.artifacts/records/project__current-position/rec-ed13dfbc-5d73-403a-8113-3085a3ab08fa.md))_
