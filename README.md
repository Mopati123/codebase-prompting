# Codebase Prompting → Repository Intelligence

This repository is being evolved from file-dump prompting scripts into a deterministic repository-intelligence engine for governed software development.

## v3 capabilities

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
