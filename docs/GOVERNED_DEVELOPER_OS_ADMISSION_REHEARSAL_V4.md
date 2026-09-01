# Governed Developer OS admission rehearsal v4

Phase N v4 adds a single admission-only rehearsal that composes the entire
non-mutating control path:

```text
target repository
  -> repository graph
  -> change impact
  -> Developer OS plan
  -> bounded repo.read binding
  -> pinned kernel harness
  -> HPL AgenticAdmissionPolicy
  -> scheduler admission
  -> ExecutionPlan + ExecutionToken
  -> STOP
```

The rehearsal always invokes the kernel harness with `execute=False` and
refuses any unexpected runtime result. Its output records deterministic hashes
for the repository graph, impact, developer plan, binding, kernel harness
receipt, and rehearsal receipt.

The kernel harness v4 also prepends the pinned kernel's `src/` directory to
`PYTHONPATH` and prefers `<kernel>/.venv/bin/python` when present. This makes
the local cross-repository invocation executable without assuming the kernel is
installed into the Developer OS Python environment.

CI tests the composed contract with the kernel subprocess mocked. A real local
rehearsal against the exact certified kernel checkout is a separate operational
proof and still performs no OpenHands network effect because the runner remains
admission-only.
