---
name: Expand-Contract Migration
slug: expand-contract-migration
family: 20-release-deployment
maturity: canonical
category: Deployment
aliases: [Parallel Change, Expand and Contract, Expand Contract Pattern]
first_described: 'Martin Fowler, ParallelChange bliki article; Ambler and Sadalage, Refactoring Databases'
related: [branch-by-abstraction, feature-toggle]
verified: true
---

# Expand-Contract Migration

## Name and Lineage

Expand-Contract Migration (also called Parallel Change, or Expand and Contract) safely evolves a database schema or an API contract in production with no downtime, by splitting a backward-incompatible change into three distinct phases. Martin Fowler's bliki names it Parallel Change and gives it its canonical three-phase definition, and the technique for database schema evolution specifically is documented by Scott Ambler and Pramod Sadalage in Refactoring Databases, where it is the standard way to change a live schema without a maintenance window.

## Problem and Context

A schema or an API contract cannot always be changed in a single, instantaneous step without breaking something. A big-bang cutover, where the old version stops working the moment the new one starts, requires every caller (or every reader and writer of the schema) to switch at exactly the same instant, which is rarely achievable when callers are deployed independently, or when a database migration itself takes time to run against live data. Expand-Contract Migration solves this by making the old and new versions coexist for a controlled period, so callers can move one at a time, and the migration completes only once every caller has genuinely finished moving.

## Forces

- Every caller of the interface, or every reader and writer of the schema, must keep working throughout the migration, none can be forced to update at the exact same instant as any other.
- The old and new versions must be kept consistent with each other for as long as both exist, any write through one path must be reflected in a way the other path can also see.
- The migrate phase, where callers move one at a time, is often the longest phase, especially when some callers are external and outside the team's direct control.
- The contract phase, removing the old version, must not happen until every caller has genuinely finished migrating, removing it too early breaks whatever has not yet moved.
- Each of the three phases can itself be released independently, so the migration composes naturally with continuous delivery rather than requiring one large release.

## Applicability

Use Expand-Contract Migration when a database schema or an API contract needs a backward-incompatible change made safely in production, with callers or readers and writers that cannot all switch to the new version at the same instant, and when the team can afford the old and new versions to coexist for a transition period.

### Non-applicability

Not the right choice for a purely additive, backward-compatible change, where nothing existing needs to keep working differently and there is no old version to contract away. Not the right choice when the old and new versions genuinely cannot be kept consistent with each other during a transition, for example when the new representation cannot be derived from or reconciled with the old one at all. Not a substitute for coordinating with truly external, third-party callers who may need far more notice and a far longer migrate phase than an internal migration would.

## Structure

The change is split into three phases against a single interface or schema. In the expand phase, the new schema field, table, or API version is added alongside the existing one, so both are available simultaneously and nothing existing is removed. In the migrate phase, callers and writers are updated, one at a time, to use the new version instead of the old one, and any data already written under the old version is backfilled into the new one. In the contract phase, once every caller has moved, the old schema element or API version is removed, leaving only the new one.

## ASCII Diagram

```
  EXPAND                MIGRATE                CONTRACT
  ------                -------                --------
  old schema/API   old schema/API          old schema/API
  new schema/API   new schema/API   -->     (removed)
  both present     callers move            new schema/API
                   one at a time            only
```

## Dynamics

The team introduces the new schema element or API version in the expand phase, deploying it alongside the old one, with both fully functional. Callers are then migrated to the new version incrementally during the migrate phase, each caller's move being its own small, independently releasable change, while any data or state written through the old path continues to be kept consistent with the new one. Once monitoring confirms every caller has genuinely stopped using the old version, the team performs the contract phase, removing the old schema element or API version and the code that supported it, leaving the system running on the new version alone.

## Implementation Variants

- **Database column or table expand-contract.** a new column or table is added, a dual-write or backfill process keeps it in sync with the old one, readers move over one at a time, then the old column or table is dropped.
- **API version expand-contract.** a new API version or field is added alongside the old one, clients migrate to the new version, then the old version is deprecated and removed.
- **Toggle-gated expand-contract.** a Feature Toggle controls which version a given caller or code path uses during the migrate phase, making it easy to move callers gradually and roll a specific caller back if needed.
- **Dual-write migration.** during the migrate phase, writes go to both the old and new schema simultaneously, so reads can be safely moved to the new schema at any point without any data gap.

## Known Production Uses

Martin Fowler's bliki (https://martinfowler.com/bliki/ParallelChange.html) documents Parallel Change as particularly useful when practicing continuous delivery, since it allows code to be released in any of the three phases independently rather than requiring one large, risky release. Scott Ambler and Pramod Sadalage's Refactoring Databases establishes expand/contract as the standard technique for evolving a production database schema without downtime, treating each schema change as its own small, reversible, independently deployable step.

## Consequences

### Benefits

- A backward-incompatible schema or API change is made safely in production, with no downtime and no requirement that every caller switch at the same instant.
- Each of the three phases is its own small, independently releasable change, so the migration fits naturally into continuous delivery instead of requiring one large, risky release.
- Callers that have not yet migrated keep working throughout the migrate phase, since the old version stays available until the contract phase.

### Costs

- The old and new versions must be kept consistent with each other for the whole migrate phase, which is real ongoing work, not a one-time cost.
- The migrate phase can be the longest phase of the whole change, especially with external callers outside the team's direct control.
- The contract phase is easy to defer or forget, leaving the old version's code and schema lingering long after every caller has actually moved.

## Failure Modes

- **Premature contract.** the old version is removed before every caller has genuinely finished migrating, breaking whatever had not yet moved.
- **Drift between old and new.** the old and new versions fall out of sync during the migrate phase, because the backfill or dual-write mechanism keeping them consistent has a bug or a gap.
- **Stalled migration.** the migrate phase never completes, because there is no forcing function or deadline for callers to move, so the old version lingers indefinitely and the contract phase never happens.
- **Untracked callers.** a caller nobody knew about is still using the old version when it is removed, because there was no reliable way to observe which callers had actually migrated.

## Trade-off Matrix

| Dimension | Expand-Contract Migration | Big-bang cutover | Branch by Abstraction |
|---|---|---|---|
| Requires all callers to switch at once | No | Yes | No (behind the abstraction) |
| Old and new coexist during the change | Yes, for the migrate phase | No, momentarily neither may fully work | Yes, behind the abstraction |
| Applies to a schema or API contract | Yes, its purpose | Yes, but riskier | Typically an internal implementation swap, not an external contract |
| Each step independently releasable | Yes | No, one large release | Yes |

## Related and Incompatible Patterns

Related to Branch by Abstraction, which solves the same coexist-then-cut-over problem for an internal implementation swap the way Expand-Contract solves it for a schema or API contract, and to Feature Toggle, which is commonly used to control which version a given caller uses during the migrate phase. Incompatible with a big-bang cutover for the same change, since the two techniques solve the compatibility problem in mutually exclusive ways, one keeps both versions running together, the other requires every caller to move at the same instant.

## Refactoring Path

### Introducing It

Start from planning a schema or API change as a single, all-at-once cutover. Introduce the new schema element or API version alongside the old one (expand), migrate callers to it incrementally while keeping both consistent (migrate), and only then remove the old version once every caller has moved (contract).

### Removing It

The technique is inherently self-removing, once the contract phase completes, the old version and the machinery keeping it consistent with the new one are gone, and the migration is finished. There is no separate step to remove the pattern itself beyond confirming the contract phase is not skipped.

## Testing and Verification

Verify the new schema element or API version genuinely works correctly during the expand phase, before any real caller depends on it. Verify the old and new versions stay consistent with each other throughout the migrate phase, by testing the backfill or dual-write mechanism directly. Verify, before the contract phase, that no caller is still using the old version, through real usage monitoring rather than an assumption.

## Observability Signals

Track which callers or code paths are still using the old version versus the new one throughout the migrate phase, to know when the contract phase is genuinely safe. Track any divergence between the old and new versions during the period both are kept in sync. Track how long the migrate phase has been open, to catch a migration that has stalled and never reaches the contract phase.

## Security and Privacy Implications

Any access-control or data-protection property enforced on the old schema or API version must also be enforced on the new one from the moment the expand phase makes it available, since a caller could otherwise reach the new version through a path that has not yet had the same controls applied. If the migration involves personal data, the old and new copies coexisting during the migrate phase both fall under the same data-protection requirements for as long as both exist.

## References

- Martin Fowler, ParallelChange, https://martinfowler.com/bliki/ParallelChange.html
- Martin Fowler, ParallelChange (continuous delivery rationale), https://martinfowler.com/bliki/ParallelChange.html

## Code Examples

### Swift

```swift
struct ExpandContractMigration {
    var writeOld: (String) -> Void
    var writeNew: (String) -> Void
    var contractComplete: Bool

    // During expand and migrate, every write goes to both versions.
    // Once contractComplete flips, only the new version is written.
    func write(value: String) {
        if !contractComplete {
            writeOld(value)
        }
        writeNew(value)
    }
}
```

### Kotlin

```kotlin
class ExpandContractMigration(
    private val writeOld: (String) -> Unit,
    private val writeNew: (String) -> Unit,
    private val contractComplete: Boolean
) {
    // During expand and migrate, every write goes to both versions.
    // Once contractComplete flips, only the new version is written.
    fun write(value: String) {
        if (!contractComplete) {
            writeOld(value)
        }
        writeNew(value)
    }
}
```

### Python

```python
class ExpandContractMigration:
    def __init__(self, write_old, write_new, contract_complete):
        self.write_old = write_old
        self.write_new = write_new
        self.contract_complete = contract_complete

    def write(self, value):
        # During expand and migrate, every write goes to both versions.
        # Once contract_complete flips, only the new version is written.
        if not self.contract_complete:
            self.write_old(value)
        self.write_new(value)
```
