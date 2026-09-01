# OpenHands proposal scope v1

Repository Intelligence can convert a deterministic change-impact result into a
machine-readable candidate scope for OpenHands.

Supported operations:

- `repo.read`
- `test.execute`
- `repo.patch`

For `repo.patch`, only the originally changed paths are emitted as writable;
reverse-dependency files remain readable and impacted tests remain executable
test candidates.

Every scope includes:

- graph SHA-256;
- impact SHA-256;
- readable paths;
- writable paths;
- test paths;
- impacted components;
- unknown paths;
- deterministic scope SHA-256.

The scope always records:

```text
authority_semantics = proposal_scope_only
execution_authorized = false
```

A separate HPL admission decision must authorize any consequential effect.
