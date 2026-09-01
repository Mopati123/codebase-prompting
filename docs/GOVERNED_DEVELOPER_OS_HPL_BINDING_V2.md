# Governed Developer OS HPL Binding v2

Phase N v2 translates deterministic Developer OS scopes into HPL-compatible
OpenHands admission payloads.

Supported bindings:

- `repo.read` → `OPENHANDS_REPO_READ`
- `test.execute` → `OPENHANDS_TEST_EXECUTE`
- `repo.patch` → `OPENHANDS_REPO_PATCH`

Each binding contains:

- ProposalEnvelope-compatible `proposal`;
- CapabilityRequest-compatible `request`;
- AgenticAdmissionPolicy-compatible `policy`;
- deterministic `binding_sha256`.

The bridge does not import the HPL kernel and does not call OpenHands. It emits
the exact data shape required for the separate HPL admission boundary.

For `repo.patch`, `allow_consequential=true` is emitted, but
`execution_authorized=false` remains explicit until the HPL scheduler admits
the request and mints an ExecutionToken.

The patch binding remains one complete-file replacement for one existing file,
matching the certified kernel v1 capability.
