# Codebase Prompting → Repository Intelligence

This repository is being evolved from file-dump prompting scripts into a deterministic repository-intelligence engine for governed software development.

## v2 capabilities

- repository file inventory with SHA-256 content identity;
- Python top-level symbol graph;
- Python import dependency graph;
- conservative Python symbol-call graph;
- relative JS/TS import dependency graph;
- test-to-code dependency edges;
- top-level repository component mapping;
- reverse dependency change-impact analysis;
- impacted test and component identification;
- deterministic graph and impact digests;
- CLI suitable for CI and OpenHands/agent consumption.

No LLM is required for graph construction. This keeps repository structure and change-impact evidence reproducible.

## CLI

```bash
repo-intel graph /path/to/repo --out repository-graph.json
repo-intel impact repository-graph.json src/example.py --depth 3 --out change-impact.json
```

## Static-analysis truth boundary

The graph is intentionally conservative. It does not claim complete semantic program analysis. Dynamic imports, reflection, monkey-patching, generated code, runtime dependency injection, and many cross-language call relationships require later analyzers.

## Legacy scripts

`base_print.py` and `base_print_ai_model.py` are preserved as historical utilities. They are not the architectural foundation of the repository-intelligence layer.
