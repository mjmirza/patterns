---
name: Branch by Abstraction
slug: branch-by-abstraction
family: 20-release-deployment
maturity: canonical
category: Deployment
aliases: [Branch By Abstraction]
first_described: 'Paul Hammant; documented on trunkbaseddevelopment.com and Martin Fowler bliki'
related: [feature-toggle, dark-launch]
verified: true
---

# Branch by Abstraction

## Name and Lineage

Branch by Abstraction is a technique credited to Paul Hammant for making a large-scale, long-to-complete structural change (swapping a core library, replacing a subsystem) directly on trunk, in small continuously-integrated increments, instead of on a long-lived version-control branch. trunkbaseddevelopment.com names it a set-piece technique to effect a longer-to-complete change in the trunk, and Martin Fowler's bliki documents the same technique under the same name.

## Problem and Context

A large structural change (replacing a library, swapping a subsystem's implementation) is too big to land as one commit but too risky to leave half-finished on trunk where every other commit must build and pass on top of it. The traditional answer is a long-lived feature branch, where the change is built in isolation and merged back once complete, but a long-lived branch drifts further from trunk the longer it lives, and the eventual merge becomes a large, risky, painful event of its own, often re-introducing exactly the integration risk the branch was meant to avoid. Branch by Abstraction solves this by keeping the change entirely on trunk, behind an abstraction that lets both the old and new implementation coexist safely while the new one is built incrementally.

## Forces

- Trunk must remain buildable and releasable at every commit throughout the change, no commit is allowed to jeopardize the ability to ship.
- The abstraction introduced adds a real, if temporary, layer of indirection that the rest of the codebase must call through instead of the old implementation directly.
- The new implementation is built incrementally behind the abstraction, so for a period of time it exists in the codebase without being live, adding code that is not yet exercised in production.
- Switching from the old to the new implementation, and eventually removing the old one and the abstraction itself, are each separate steps that must be sequenced deliberately.
- The technique trades a single large merge risk for a longer period of coordinated, incremental work, which is only worth it when the change is genuinely too large to land safely in one step.

## Applicability

Use Branch by Abstraction when a structural change is large enough that it cannot be completed in a single commit, but the team wants to avoid a long-lived branch and its eventual painful merge, and is willing to do the work in small, continuously-integrated increments on trunk instead.

### Non-applicability

Not the right choice for a small, quickly-completable change, where the overhead of introducing and later removing an abstraction outweighs any branching risk it would have carried. Not the right choice when the old and new implementations cannot reasonably coexist behind a shared abstraction, because their behavior, data model, or contract differs too fundamentally to unify behind one interface even temporarily. Not a substitute for genuine trunk-based development discipline, since the technique still assumes every commit keeps trunk in a shippable state.

## Structure

An abstraction (an interface, a facade, an injectable seam) is introduced in front of the code being replaced, and every caller is updated to go through the abstraction rather than the concrete old implementation directly. The old implementation becomes the abstraction's sole implementer at first. A new implementation of the same abstraction is then built incrementally, committed to trunk as it progresses, but not yet wired up to be used. Once the new implementation is complete and trusted, a switch (often a Feature Toggle) flips callers from the old implementation to the new one. Once the new implementation is proven in production, the old implementation and, eventually, the abstraction itself, are removed.

## ASCII Diagram

```
  step 1              step 2                step 3              step 4-5
  ------              ------                ------              --------
  caller               caller                caller              caller
    |                    |                     |                   |
    v                    v                     v                   v
  [Old impl]     [Abstraction]           [Abstraction]        [New impl]
                  +---+---+                flag: ON             only
             [Old impl] [New impl]       [Old impl](unused)
                (off)     (building)      [New impl](live)
```

## Dynamics

The team identifies the component to be replaced and introduces an abstraction directly in front of it, committing that abstraction to trunk with the old implementation as its only implementer, so behavior is unchanged. Over subsequent small commits, the team builds a second implementation of the same abstraction, each commit landing safely on trunk since the new implementation is not yet wired up to be used. Once the new implementation is complete, a switch (a toggle, a configuration flip) is turned on, and callers begin using the new implementation through the same abstraction, with the old implementation still present but no longer exercised. Once the new implementation has proven itself, the old implementation is deleted, and finally, once the abstraction has served its purpose, it too can be removed if it is no longer needed for any other reason.

## Implementation Variants

- **Interface-based abstraction.** a language-level interface or protocol is introduced, with the old and new implementations as two concrete classes implementing it.
- **Toggle-switched abstraction.** the abstraction internally checks a Feature Toggle to decide which implementation to delegate to, letting the switch happen at runtime without a deployment.
- **Facade over a subsystem boundary.** the abstraction sits at a subsystem or service boundary rather than a single class, appropriate when the change spans many internal components behind one external contract.
- **Parallel-run abstraction.** the abstraction runs both implementations for a period, comparing their outputs, similar in spirit to Shadow Traffic, before fully cutting over to the new one.

## Known Production Uses

trunkbaseddevelopment.com (https://trunkbaseddevelopment.com/branch-by-abstraction/) documents Branch by Abstraction as a core technique of trunk-based development for making longer-to-complete changes without leaving trunk, with an explicit rule that no commit pushed to the shared repository should jeopardize the ability to go live. Martin Fowler's bliki independently documents the same technique under the same name, describing it as a way to make a large-scale change to a software system gradually while continuing to release the system regularly.

## Consequences

### Benefits

- A large structural change is made entirely on trunk, in small increments, avoiding a long-lived branch and its eventual risky merge.
- Trunk stays releasable throughout the change, since every commit either does not touch the live behavior yet or has already been proven safe to switch to.
- The old implementation stays available as an instant fallback until the new one is fully trusted, since the switch itself is a small, reversible step.

### Costs

- The abstraction and, temporarily, both implementations add real code and complexity to the codebase for the duration of the change.
- The new implementation exists, partly built, in the codebase for a period before it is ever live, which is code that must still be maintained and kept building.
- The technique requires discipline to actually remove the old implementation and the abstraction once they are no longer needed, or the temporary complexity becomes permanent.

## Failure Modes

- **Abandoned migration.** the switch to the new implementation is made, but the old implementation and the now-unneeded abstraction are never cleaned up, leaving dead code and indirection behind indefinitely.
- **Leaky abstraction.** the abstraction does not fully capture the old implementation's real behavior or edge cases, so the new implementation built behind it diverges from what callers actually need once it goes live.
- **Premature switch.** the new implementation is switched to before it is genuinely ready, because the incremental, low-visibility nature of building it behind an abstraction makes it easy to underestimate how much validation it still needs.
- **Callers bypassing the abstraction.** new code is written that calls the old implementation directly instead of through the abstraction, undermining the whole point of the seam.

## Trade-off Matrix

| Dimension | Branch by Abstraction | Long-lived feature branch | Feature Toggle alone |
|---|---|---|---|
| Stays on trunk throughout | Yes | No | Yes |
| Risk of a large, painful merge | None, no merge event | High, grows with branch lifetime | None |
| Suited to a large structural change | Yes, its purpose | Possible, but risk grows over time | Only if the change fits behind a single toggle check |
| Adds temporary code complexity | Yes, the abstraction and two implementations | No, the branch itself carries the complexity | Minimal, a single toggle check |

## Related and Incompatible Patterns

Related to Feature Toggle, which is commonly used as the switch mechanism that flips callers from the old implementation to the new one behind the abstraction, and to Dark Launch, since the new implementation can be exercised live behind the abstraction before its output is trusted to be the one callers actually see. Incompatible with a long-lived feature branch used for the same change, since the two techniques solve the same problem in mutually exclusive ways, one keeps everything on trunk, the other deliberately diverges from it.

## Refactoring Path

### Introducing It

Start from planning a large structural change as a long-lived branch. Introduce an abstraction directly in front of the component to be replaced, land it on trunk with the old implementation as the sole implementer, then build the new implementation incrementally behind that same abstraction, each step landing safely on trunk.

### Removing It

Once the new implementation has been switched on and proven in production, remove the old implementation, and once the abstraction is no longer needed for any other reason (a second implementation, a testing seam), remove the abstraction itself, so the temporary structure introduced for the migration does not become permanent.

## Testing and Verification

Verify every commit made while building the new implementation still leaves trunk in a releasable state, by running the full test suite against trunk at each step. Verify the new implementation's behavior matches the old implementation's for the same inputs before switching, either through direct tests against the abstraction or a parallel-run comparison. Verify, after the switch, that the old implementation is genuinely unused before it is deleted.

## Observability Signals

Track which implementation (old or new) is actually being used behind the abstraction at any point in time, and for how long the migration has been in progress, to catch a migration that has stalled partway. Track the build and test status of trunk throughout the change, to confirm no commit has jeopardized its releasable state. Track error rates and behavior differences between the old and new implementation during any period both are compared, before the old one is removed.

## Security and Privacy Implications

Any security review or access-control property the old implementation satisfied must be verified against the new implementation before the switch, since the abstraction can otherwise silently hide a security regression behind an interface that looks unchanged from the caller's perspective. If the change involves data storage or a data-handling boundary, both implementations existing simultaneously means the data-protection requirements apply to both for as long as they coexist.

## Code Examples

### Swift

```swift
protocol PaymentProcessor {
    func charge(cents: Int) -> Bool
}

struct LegacyPaymentProcessor: PaymentProcessor {
    func charge(cents: Int) -> Bool { true }
}

struct NewPaymentProcessor: PaymentProcessor {
    func charge(cents: Int) -> Bool { true }
}

struct PaymentProcessorSwitch {
    var useNewImplementation: Bool

    // Both implementations satisfy the same abstraction, so callers
    // never see which one is live behind the switch.
    func current() -> PaymentProcessor {
        return useNewImplementation ? NewPaymentProcessor() : LegacyPaymentProcessor()
    }
}
```

### Kotlin

```kotlin
interface PaymentProcessor {
    fun charge(cents: Int): Boolean
}

class LegacyPaymentProcessor : PaymentProcessor {
    override fun charge(cents: Int): Boolean = true
}

class NewPaymentProcessor : PaymentProcessor {
    override fun charge(cents: Int): Boolean = true
}

class PaymentProcessorSwitch(private val useNewImplementation: Boolean) {
    // Both implementations satisfy the same abstraction, so callers
    // never see which one is live behind the switch.
    fun current(): PaymentProcessor {
        return if (useNewImplementation) NewPaymentProcessor() else LegacyPaymentProcessor()
    }
}
```

### Python

```python
class PaymentProcessor:
    def charge(self, cents):
        raise NotImplementedError


class LegacyPaymentProcessor(PaymentProcessor):
    def charge(self, cents):
        return True


class NewPaymentProcessor(PaymentProcessor):
    def charge(self, cents):
        return True


class PaymentProcessorSwitch:
    def __init__(self, use_new_implementation):
        self.use_new_implementation = use_new_implementation

    def current(self):
        # Both implementations satisfy the same abstraction, so callers
        # never see which one is live behind the switch.
        return NewPaymentProcessor() if self.use_new_implementation else LegacyPaymentProcessor()
```

## References

- trunkbaseddevelopment.com, Branch by Abstraction, https://trunkbaseddevelopment.com/branch-by-abstraction/
- Martin Fowler, BranchByAbstraction, https://martinfowler.com/bliki/BranchByAbstraction.html
