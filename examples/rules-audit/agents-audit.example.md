# Agent Rules Self-Audit Report

Generated: 2026-06-25T22:45:00+09:00
Repo: `C:\GitRepositories\example-product`

## Summary

- Context files scanned: 3
- MUST_FIX findings: 1
- SHOULD_CHECK findings: 2

## Findings

### MUST_FIX: AUTOMATION_WITHOUT_APPROVAL_BOUNDARY

Nightly automation is mentioned, but no approval boundary is written.

Evidence:

- `AGENTS.md:31 - Run nightly automation to update rule files.`

Recommendation: make nightly jobs report-only unless a human or primary coding agent approves the exact patch.

### SHOULD_CHECK: BROAD_READ_VS_TOKEN_BUDGET

The rules tell the agent to read broadly while also asking it to save context.

Evidence:

- `AGENTS.md:12 - Read all relevant docs before coding.`
- `AGENTS.md:19 - Keep token use low.`

Recommendation: add a routing rule: inspect index/registry first, then load only the narrow reference files needed for the task.

### SHOULD_CHECK: BROKEN_REFERENCE

A routed document path does not exist.

Evidence:

- `AGENTS.md:44 -> docs/old-review-flow.md`

Recommendation: fix the path, remove the stale reference, or add the missing file.

## Grill-Me Questions

1. What exact files can a nightly job change without approval, if any?
2. When a rule says to read broadly, what routing file should be checked first to avoid token waste?
3. Which rule source wins when AGENTS.md, a skill, and a task-specific handoff disagree?
4. What evidence is required before a new rule is added?

## Patch Candidates

- Add an `Agent Rules Maintenance` section.
- Add a `Rule Source Priority` section.
- Add a `Routing Before Reading` section.
- Repair or delete unresolved file references.
