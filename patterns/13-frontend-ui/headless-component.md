---
name: Headless Component
slug: headless-component
family: 13-frontend-ui
category: Composition
aliases: [Unstyled Component, Logic-only Component, Renderless Component]
first_described: "Martin Fowler's website, Headless Component article"
maturity: established
related: [slot-and-children-as-api, reducer-hook, context-selector]
incompatible_with: []
verified: 2026-08-21
---

# Headless Component

## 1. Name, aliases, and lineage

The canonical name is Headless Component, a design pattern where a
component owns a piece of behavior, state, or logic without
prescribing any specific visual markup for it, leaving the rendering
entirely to whatever consumes it. Martin Fowler's website states the
definition directly. "A Headless Component is a design pattern in
React where a component, normally implemented as React hooks, is
responsible solely for logic and state management without
prescribing any specific UI."

The alias **Unstyled Component** names the pattern from the visual
side, a component that ships with no styling opinions at all, letting
the consumer supply every visual detail. **Logic-only Component**
names it from the behavioral side, emphasizing that only state and
logic live inside it. **Renderless Component** is the term used in
some other component toolsets for the same underlying idea, a
component that manages behavior but renders nothing of its own.

## 2. Problem and context

A component that bundles its behavior and its visual markup together
forces every consumer to accept both, even when a consumer genuinely
needs the same behavior, an accessible dropdown's open and close
logic, a form field's validation state, but wants an entirely
different visual presentation than the one the component happens to
ship with. Duplicating the behavior for each new visual variant
repeats real, often subtle logic, keyboard handling, focus
management, accessibility attributes, that is easy to get wrong the
second time even when the first implementation was correct. The
Headless Component pattern solves this by drawing a clean boundary
between the two concerns, the component owns the behavior and state,
while exposing that state and the functions to change it through a
plain interface the consumer's own markup can use however it needs
to.

## 3. Forces

The pattern balances the following competing pressures.

- **Reusing correct, hard-won behavior.** Favored. Logic such as
  keyboard navigation, focus trapping, or accessibility attribute
  management is genuinely difficult to get right, and a headless
  component lets that correctness be written once and reused across
  every visual variant that needs it.
- **Full visual control for each consumer.** Favored. Radix UI's own
  documentation states this directly for its own headless primitives.
  "Components ship without styles, giving you complete control over
  the look and feel," letting each consumer's markup and styling
  differ completely while sharing the same underlying behavior.
- **A more indirect, less immediately visible API.** Sacrificed. A
  consumer of a headless component must wire up the exposed state and
  handlers into their own markup by hand, a more work upfront than
  a fully styled, ready-to-render component would require.
- **Consistency across consumers.** Sacrificed. Because visual
  presentation is left entirely to the consumer, nothing in the
  pattern itself enforces that different consumers of the same
  headless component end up visually or interactively consistent with
  each other.

## 4. Applicability and non-applicability

Reach for a Headless Component when the following hold.

- The component's behavior, keyboard handling, accessibility
  attributes, open and close state, genuinely needs to be reused
  across visually distinct implementations.
- Different consumers of the same behavior have genuinely different
  visual requirements, a design system's own styled variant versus a
  fully custom one-off implementation.
- The team building the headless component has the expertise to get
  the behavior, especially accessibility behavior, genuinely correct,
  since consumers will trust that correctness without re-verifying it
  themselves.

Do NOT reach for a Headless Component in these cases, and the reason
matters more than the rule.

- **There is only ever one visual presentation for this behavior**,
  building a headless abstraction for behavior that will only ever be
  rendered one way adds the indirection cost of a headless component
  with none of the reuse benefit that justifies it.
- **The behavior itself is simple enough that duplicating it across a
  small number of visual variants is genuinely cheap and low-risk**,
  the pattern's main benefit is avoiding the reimplementation of
  genuinely hard, error-prone logic, and applying it to trivial logic
  adds structure without a corresponding benefit.
- **The consuming team lacks the context to correctly wire the exposed
  state and handlers into their own markup**, a headless component
  shifts real implementation responsibility, including accessibility
  correctness in the resulting markup, onto the consumer, which is
  the wrong trade when that consumer cannot reliably carry it.

## 5. Structure

A Headless Component has two structural parts.

- **The behavior layer**, the logic, state, and event handling a
  headless component owns internally, exposed through a plain
  interface, most commonly a hook's return value or a render-prop
  function's argument.
- **The consumer's own markup**, supplied entirely by whatever uses
  the headless component, wiring the exposed state and handlers into
  whatever visual elements the consumer chooses.

## 6. ASCII structure diagram

```
  +----------------------------------------------------------+
  | Headless component, e.g. useDisclosure()                  |
  |   owns: isOpen, open(), close(), toggle()                  |
  |   owns: keyboard handling, focus management                |
  |   exposes: { isOpen, open, close, toggle } via a hook       |
  +----------------------------------------------------------+
                  |                        |
                  v                        v
  +----------------------+   +----------------------+
  | Consumer A's markup    |   | Consumer B's markup    |
  | a styled dropdown      |   | a completely custom     |
  | using the design        |   | one-off implementation  |
  | system's own visuals    |   | with entirely different |
  |                          |   | markup and styling       |
  +----------------------+   +----------------------+
```

## 7. Dynamics

The trace below shows two consumers reusing the same headless
component's behavior with entirely different visual presentations.

```
Consumer A renders a dropdown

Consumer A calls the headless useDisclosure hook
   |-- receives { isOpen, open, close, toggle } and the internal
       keyboard and focus handling that comes with it
   |-- renders its own styled button and panel markup, wiring
       onClick to toggle and the panel's visibility to isOpen

Consumer B renders a completely different visual

Consumer B calls the same headless useDisclosure hook
   |-- receives the identical { isOpen, open, close, toggle } state
       and the identical correct keyboard and focus behavior
   |-- renders entirely different markup, a custom animated overlay
       instead of a plain dropdown panel, wiring the same exposed
       state and handlers into that different visual structure

Both consumers share the same correct behavior

if a keyboard-handling bug is fixed inside the headless component
   |-- both Consumer A's and Consumer B's visually distinct
       implementations receive the fix automatically, since neither
       duplicated the behavior itself
```

## 8. Implementation variants

**Hook-based headless components.** The behavior is exposed as a
custom hook returning state and handler functions, the dominant
modern form in a hook-based UI framework, letting a consumer call the
hook directly inside their own component's markup.

**Render-prop headless components.** The behavior is exposed by
calling a function passed as a prop, with the component's own return
value coming from that function's result, an older but still used
form that predates the widespread adoption of hooks.

**Unstyled primitive libraries.** A library ships a full suite of
headless components covering common interactive patterns, dropdowns,
dialogs, comboboxes, each handling its own accessibility and keyboard
behavior while remaining entirely unstyled, letting an application
build a fully custom design system on top of correct, shared
behavior.

**Compound headless components.** Several related headless pieces are
composed together, a root component managing shared state and several
child components each exposing a specific piece of that state and
behavior, giving a consumer fine-grained control over exactly which
pieces of markup receive which pieces of behavior.

## 9. Known production uses

**Martin Fowler's website, defining the pattern.** The site states
the definition directly. "A Headless Component is a design pattern in
React where a component, normally implemented as React hooks, is
responsible solely for logic and state management without
prescribing any specific UI." Martin Fowler, "Headless Component,"
https://martinfowler.com/articles/headless-component.html, verified
2026-08-21.

**Radix UI's own documentation, on its unstyled primitive library.**
Radix UI describes its own library directly as "a low-level UI
component library with a focus on accessibility, customization and
developer experience," where "components ship without styles, giving
you complete control over the look and feel." Radix UI,
"Introduction," https://www.radix-ui.com/primitives/docs/overview/introduction,
verified 2026-08-21.

## 10. Consequences

Positive.

- Genuinely hard, error-prone logic, especially accessibility
  behavior such as keyboard navigation and focus management, is
  written once and correctly, then reused across every visual variant
  that needs it, exactly the benefit Radix UI's own documentation
  points to when it names accessibility and developer experience as
  its focus.
- Each consumer retains complete visual control, since the headless
  component ships no styling opinions at all, allowing an entirely
  custom look and feel per consumer.
- A behavior fix or improvement made inside the headless component
  propagates automatically to every consumer, without needing to
  patch each visually distinct implementation separately.

Negative.

- A consumer must do real work wiring the exposed state and handlers
  into their own markup, more upfront effort than a fully styled,
  ready-to-render component would require.
- Nothing in the pattern itself enforces visual or interactive
  consistency across different consumers of the same headless
  component, since presentation is left entirely up to each one.
- The correctness of the resulting accessible markup still depends on
  the consumer wiring the exposed attributes and handlers correctly,
  so a headless component reduces but does not eliminate the risk of
  an inaccessible final implementation.

## 11. Failure modes and misuse

**Building a headless abstraction for behavior that only ever needs
one visual presentation.** Symptom. The application carries the
indirection cost of a hook or render-prop interface, and the extra
wiring work at every call site, with no actual reuse benefit ever
materializing. Cause. Applying the pattern speculatively, anticipating
a future visual variant that never actually arrives. Fix. Keep
behavior and markup together until a genuine second visual
presentation actually needs the same behavior, extracting the
headless component only at that point.

**Exposing internal state or handlers that leak implementation
details the consumer should not need to know about.** Symptom. A
consumer's markup breaks, or behaves unexpectedly, when the headless
component's internal implementation changes, even though the
consumer never touched anything the component's public interface was
supposed to guarantee. Cause. Designing the exposed interface around
whatever happened to be convenient internally, rather than around
what a consumer genuinely needs to correctly wire up the behavior.
Fix. Design the headless component's exposed interface deliberately,
exposing only the state and handlers a consumer genuinely needs, and
treating everything else as a private implementation detail that can
change freely.

**Shipping a headless component whose exposed interface makes it easy
for a consumer to omit required accessibility wiring, such as ARIA
attributes the component computes but does not enforce being
applied.** Symptom. Different consumers of the same headless
component end up with inconsistent, sometimes inaccessible, final
markup, even though the underlying behavior logic is shared and
correct. Cause. Treating the headless component's job as complete once
state and handlers are exposed, without also making the correct
accessibility wiring as easy and as hard to skip as possible. Fix.
Design the exposed interface so the correct, accessible wiring is the
natural, low-friction path, such as returning a spreadable props
object that already includes the necessary ARIA attributes, rather
than leaving every attribute for the consumer to remember and apply
individually.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Headless Component | Fully styled component | Duplicated logic per visual variant |
|---|---|---|---|
| Reusing correct, hard-won behavior | Strong, written once and shared | Weak, tied to one specific visual implementation | Weak, each duplication risks its own bugs |
| Full visual control per consumer | Strong, no styling opinions at all | Weak, styling is baked in unless deliberately overridden | Strong, but at the cost of reimplementing behavior each time |
| Upfront wiring effort per consumer | Weak, consumer must wire state into markup | Strong, prepared to render with minimal wiring | Weak, consumer must build both behavior and markup |
| Consistency across consumers | Weak, nothing enforces it | Strong, a single shared visual implementation | Weak, each duplication can drift independently |

Reading of the table. A Headless Component wins specifically when
genuinely hard, reusable behavior needs to serve multiple, genuinely
different visual presentations. A fully styled component wins when
consistency and low wiring effort matter more than visual
flexibility, and duplicating logic per variant is rarely the right
trade unless the logic itself is trivial enough that correctness risk
is genuinely low.

## 13. Related and incompatible patterns

- **Slot and Children as API.** A complementary technique frequently
  paired with headless components, letting a consumer pass their own
  markup into specific positions within a still-managed structure,
  rather than wiring every piece of state by hand.
- **Reducer Hook.** The state-management mechanism a headless
  component's internal logic is frequently built on top of, managing
  the behavior state the headless interface then exposes.
- **Context Selector.** A complementary technique for sharing a
  headless component's state across a deeply nested consumer tree
  without prop drilling every exposed value down manually.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing fully styled component whose
behavior a second, visually distinct consumer now genuinely needs.

1. Confirm a second consumer genuinely needs the same behavior with a
   genuinely different visual presentation, rather than extracting a
   headless component speculatively.
2. Extract the component's state and event-handling logic into a
   hook, or an equivalent behavior-only interface, returning exactly
   the state and handlers a consumer needs.
3. Design the exposed interface so correct, accessible wiring is the
   natural path, including any ARIA attributes the behavior itself
   computes.
4. Rebuild the original visual implementation as a consumer of the new
   headless interface, confirming it behaves identically to before
   the extraction.
5. Build the second visual variant as a second consumer of the same
   headless interface, confirming it shares the same correct
   behavior.

Removing the pattern when it stops earning its place, most relevant
when an application has consolidated down to a single visual
presentation for a given behavior.

1. Confirm, rather than assume, that only one visual consumer of the
   headless component's behavior remains, and that no near-term second
   consumer is genuinely expected.
2. Fold the headless component's behavior directly back into the one
   remaining visual implementation.
3. Remove the now-unused headless interface, confirming the merged
   implementation still behaves correctly.

## 15. Testing and verification

Easier because of the pattern.

- Because the behavior is isolated from any specific markup, a test
  can exercise the headless component's state transitions and
  handlers directly, without needing to render any particular visual
  implementation at all.
- A behavior fix or a new test case written once against the headless
  interface protects every consumer of that behavior, rather than
  needing to be duplicated across each visual implementation's own
  test suite.

Harder because of the pattern.

- Testing the final, rendered result for a specific consumer still
  needs a separate test exercising that consumer's own markup, since
  the headless component's own tests say nothing about whether a
  given consumer wired the exposed state and handlers correctly.
- Verifying accessibility specifically needs testing the actual
  rendered markup a consumer produces, since the headless component
  can compute correct ARIA attributes internally while a consumer's
  markup still fails to apply them.

Techniques that apply.

- **Isolated behavior tests.** Directly test the headless component's
  hook or render-prop interface, asserting state transitions and
  handler behavior without rendering any specific visual
  implementation.
- **Per-consumer integration tests.** For each visual consumer of the
  headless component, test that consumer's actual rendered output and
  interaction behavior, confirming it correctly wired the exposed
  interface.
- **Accessibility audits per consumer.** Run an accessibility check
  against each consumer's actual rendered markup, since correctness
  at the headless behavior layer does not guarantee correctness at
  the consumer's markup layer.
- **Interface contract tests.** Assert the headless component's
  exposed interface, its shape and the guarantees it makes, remains
  stable across changes, catching a regression that would silently
  break every consumer relying on that interface.

## 16. Observability signals

A headless component's own runtime footprint is usually small,
since it manages state and logic rather than performing heavy work
itself, so the more honest signal here is about API stability and
correct usage rather than performance.

What to record.

- The number and diversity of distinct consumers actually using a
  given headless component's interface, since a component with many
  varied consumers is exactly the case the pattern is meant to serve,
  and a component with only one consumer may be a candidate for
  simplification per dimension 14's removal path.
- Reports of accessibility issues specifically tied to a headless
  component's consumers, since these point at either a gap in the
  behavior layer itself or a wiring mistake repeated across multiple
  consumers, both worth investigating regardless of which.

A healthy state. The headless component serves multiple genuinely
different visual consumers, each correctly wired, with accessibility
behavior consistent across all of them because the underlying logic
is shared rather than duplicated.

A failing state. A headless component has only ever had one consumer
long after its extraction, suggesting the abstraction cost is not
earning its keep, or multiple consumers show inconsistent
accessibility behavior for behavior the headless component is
supposed to guarantee, pointing at a gap between what the component
computes and what consumers actually apply.

## 17. Security and privacy implications

Headless Component is close to neutral for security, being a
UI-composition pattern rather than a data-handling one, and inventing
a dedicated attack surface here would be dishonest. One practical
implication is worth naming.

**Because a headless component exposes internal state and handlers
directly to whatever consumer calls it, a headless component that
manages genuinely sensitive state, such as authentication status or
a permission check, must not rely on the consumer's own markup or
rendering choices as the actual security boundary, since a
consumer's incorrect or malicious use of the exposed interface can
diverge from what the headless component's own internal logic
intended.** The real authorization decision for sensitive state
belongs to the server or the data layer supplying that state, not to
whichever consumer happens to render it, and a headless component
exposing a permission flag is providing a rendering hint, not
enforcing an actual restriction on its own.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a headless disclosure
component the way a hook-based UI framework would expose it, kept
free of JSX and any specific framework's package so the sample
compiles as plain TypeScript. Python shows the conceptual shape of the
same behavior-only state manager using a minimal, framework-agnostic
implementation, since Python has no browser-facing component model
and therefore no single dominant headless-component implementation
the way TypeScript has React hooks and Radix UI's own primitives.
Swift shows the same conceptual shape using a minimal model,
analogous to how a native app might separate a view model's state and
logic from the specific view that renders it. Java, Go, and Rust are
omitted, since none has a dominant, idiomatic browser-facing
component framework this specifically UI-composition pattern maps to
as directly as TypeScript does.

### TypeScript

```typescript
interface DisclosureState {
  isOpen: boolean;
  open(): void;
  close(): void;
  toggle(): void;
}

function createDisclosure(initialOpen: boolean): DisclosureState {
  let isOpen = initialOpen;

  const state: DisclosureState = {
    get isOpen() {
      return isOpen;
    },
    open() {
      isOpen = true;
    },
    close() {
      isOpen = false;
    },
    toggle() {
      isOpen = !isOpen;
    },
  };

  return state;
}

function renderDropdownConsumer(disclosure: DisclosureState): void {
  console.log("dropdown consumer, isOpen:", disclosure.isOpen);
}

function renderCustomOverlayConsumer(disclosure: DisclosureState): void {
  console.log("custom overlay consumer, isOpen:", disclosure.isOpen);
}

const disclosureA = createDisclosure(false);
renderDropdownConsumer(disclosureA);
disclosureA.toggle();
renderDropdownConsumer(disclosureA);

const disclosureB = createDisclosure(false);
renderCustomOverlayConsumer(disclosureB);
disclosureB.open();
renderCustomOverlayConsumer(disclosureB);
```

### Python

```python
from dataclasses import dataclass


@dataclass
class DisclosureState:
    is_open: bool = False

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def toggle(self) -> None:
        self.is_open = not self.is_open


def render_dropdown_consumer(disclosure: DisclosureState) -> None:
    print("dropdown consumer, is_open:", disclosure.is_open)


def render_custom_overlay_consumer(disclosure: DisclosureState) -> None:
    print("custom overlay consumer, is_open:", disclosure.is_open)


if __name__ == "__main__":
    disclosure_a = DisclosureState()
    render_dropdown_consumer(disclosure_a)
    disclosure_a.toggle()
    render_dropdown_consumer(disclosure_a)

    disclosure_b = DisclosureState()
    render_custom_overlay_consumer(disclosure_b)
    disclosure_b.open()
    render_custom_overlay_consumer(disclosure_b)
```

### Swift

```swift
final class DisclosureState {
    private(set) var isOpen: Bool

    init(initialOpen: Bool) {
        isOpen = initialOpen
    }

    func open() {
        isOpen = true
    }

    func close() {
        isOpen = false
    }

    func toggle() {
        isOpen.toggle()
    }
}

func renderDropdownConsumer(_ disclosure: DisclosureState) {
    print("dropdown consumer, isOpen: " + String(disclosure.isOpen))
}

func renderCustomOverlayConsumer(_ disclosure: DisclosureState) {
    print("custom overlay consumer, isOpen: " + String(disclosure.isOpen))
}

let disclosureA = DisclosureState(initialOpen: false)
renderDropdownConsumer(disclosureA)
disclosureA.toggle()
renderDropdownConsumer(disclosureA)

let disclosureB = DisclosureState(initialOpen: false)
renderCustomOverlayConsumer(disclosureB)
disclosureB.open()
renderCustomOverlayConsumer(disclosureB)
```

## 18. References

1. Martin Fowler. "Headless Component".
   https://martinfowler.com/articles/headless-component.html
   Verified 2026-08-21. Source of the defining pattern quote used in
   dimensions 1 and 9.
2. Radix UI. "Introduction".
   https://www.radix-ui.com/primitives/docs/overview/introduction
   Verified 2026-08-21. Source of the unstyled-library and
   full-visual-control quotes used in dimensions 3 and 9.
