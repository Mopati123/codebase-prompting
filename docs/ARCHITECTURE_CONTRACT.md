# Repository Intelligence Architecture Contract v1

An optional architecture contract gives repository intelligence an explicit,
machine-readable component model.

Example:

```json
{
  "schema_version": "1.0",
  "components": [
    {"name": "runtime", "paths": ["src/runtime/**"]},
    {"name": "tests", "paths": ["tests/**"]}
  ],
  "dependencies": [
    {"from": "tests", "to": "runtime", "type": "depends_on"}
  ]
}
```

Allowed dependency types are `depends_on`, `configures`, and `deploys`.
The contract is normalized and SHA-256 identified.

This contract describes architecture; it does not grant execution authority.
