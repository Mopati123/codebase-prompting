# Codebase Prompting → Repository Intelligence

This repository is being evolved from file-dump prompting scripts into a deterministic repository-intelligence engine for governed software development.

## v1 capabilities

- repository file inventory with SHA-256 content identity;
- Python top-level symbol graph;
- Python import dependency graph;
- relative JS/TS import dependency graph;
- reverse dependency change-impact analysis;
- deterministic graph and impact digests;
- CLI suitable for CI and OpenHands/agent consumption.

No LLM is required for v1 graph construction. This keeps repository structure and change-impact evidence reproducible.

## CLI

```bash
repo-intel graph /path/to/repo --out repository-graph.json
repo-intel impact repository-graph.json src/example.py --depth 3 --out change-impact.json
```

## Legacy scripts

`base_print.py` and `base_print_ai_model.py` are preserved as historical utilities. They are not the architectural foundation of the new repository-intelligence layer.
