# Codebase Prompting → Repository Intelligence

This repository is being evolved from file-dump prompting scripts into a deterministic repository-intelligence engine for governed software development.

## v3 capabilities + Phase N Developer OS v1

- SHA-256 repository file inventory;
- Python symbol/import/call graphs;
- relative JS/TS dependency graph;
- test-to-code mapping;
- change-impact traversal with impacted tests/components;
- optional architecture-component contracts with typed component dependencies;
- deterministic architecture-contract digests;
- machine-readable OpenHands proposal scopes;
- deterministic graph, impact, and scope digests;
- CLI suitable for CI and governed developer workflows.

## CLI

```bash
repo-intel graph /path/to/repo --architecture architecture.json --out repository-graph.json
repo-intel impact repository-graph.json src/example.py --depth 3 --out change-impact.json
repo-intel openhands-scope repository-graph.json change-impact.json --operation repo.patch --out openhands-scope.json
```

## Authority boundary

Repository Intelligence proposes bounded read/test/write scope. It never grants
execution authority. Generated OpenHands scopes explicitly set
`execution_authorized=false`; HPL remains the separate execution authority.

## Static-analysis truth boundary

The graph is intentionally conservative. Dynamic imports, reflection,
monkey-patching, generated code, runtime dependency injection, and many
cross-language semantic relationships remain outside v3 coverage.

## Legacy scripts

`base_print.py` and `base_print_ai_model.py` remain preserved as historical utilities.


## Governed Developer OS v1

```bash
repo-intel developer-plan repository-graph.json change-impact.json \
  --change-request "Fix the requested behavior" \
  --out developer-plan.json
```

The generated plan is proposal-only. It composes bounded `repo.read`,
`test.execute`, and `repo.patch` scopes, requires retesting after mutation,
requires repository-intelligence recomputation, and requires final evidence.
The patch stage remains subject to separate HPL execution authority.


## Governed Developer OS HPL binding v2

Phase N v2 emits HPL-compatible admission payloads for the already-certified
OpenHands `repo.read`, `test.execute`, and `repo.patch` capabilities.

The binding layer remains proposal-only and network-free. HPL must still admit
the consequential request and mint the ExecutionToken before any mutation can
occur.


## Cross-repository kernel harness v3

```bash
repo-intel kernel-run hpl-read-binding.json \
  --kernel-root /path/to/apex-hpl-governed-kernel \
  --out kernel-harness-receipt.json
```

The harness pins the kernel checkout to the certified Developer OS Agentic
Runner head and defaults to admission-only. External effects require explicit
`--execute`, after which HPL admission still remains mandatory.


## Admission-only end-to-end rehearsal v4

```bash
repo-intel rehearse-admission /path/to/target-repo README.md \
  --change-request "Inspect README impact" \
  --inspect-path README.md \
  --conversation-id 123e4567-e89b-12d3-a456-426614174000 \
  --kernel-root /path/to/apex-hpl-governed-kernel \
  --out developer-os-admission-rehearsal.json
```

This composes repository intelligence through HPL scheduler admission and then
stops. It cannot execute an OpenHands effect.
