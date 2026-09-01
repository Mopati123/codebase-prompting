# Cross-repository Developer OS harness v3

This tranche connects the Developer OS repository to the separately certified
HPL kernel runner.

The harness does not import kernel internals. It invokes:

```text
python -m hpl.runtime.agentic_runner
```

inside an explicitly supplied kernel checkout.

Before invocation, the harness requires the kernel checkout HEAD to equal the
certified runner baseline:

```text
a5d2d913e41fd9a80212825921d0919fd8320b3b
```

This prevents a different local kernel implementation from silently receiving a
binding.

Default behavior is admission-only. `--execute` is never implied; the caller
must request it explicitly. Even then, the kernel runner must still admit the
binding and mint the HPL ExecutionToken before RuntimeEngine can execute.

The harness does not inject credentials, OpenHands endpoints, or authorization
material. Operator environment configuration remains outside this layer.

CI mocks the subprocess boundary. It proves command construction, commit pinning,
admission-only defaults, and explicit execution semantics; it does not perform a
live cross-repository or OpenHands effect.
