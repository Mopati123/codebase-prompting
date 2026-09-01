# Governed Developer OS v1

Phase N v1 composes Repository Intelligence and the already certified OpenHands
capabilities into a deterministic proposal-only developer plan.

The lifecycle is:

```text
change request
  -> repository graph
  -> change impact
  -> repo.read scope
  -> baseline test scope
  -> repo.patch scope
  -> retest scope
  -> repository intelligence recompute
  -> evidence finalization
```

The planner does not call OpenHands and does not mint HPL authority.

Every generated plan records:

```text
authority_semantics = proposal_plan_only
execution_authorized = false
```

The patch stage explicitly requires HPL execution authority. A run is not
reconciled unless every stage has a receipt, every stage succeeded, and the patch
receipt proves an execution token was present.

v1 is orchestration-contract infrastructure. It does not yet perform cross-repo
execution against the governed kernel.
