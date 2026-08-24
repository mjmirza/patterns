---
name: Slot and Children as API
slug: slot-and-children-as-api
family: 13-frontend-ui
category: Composition
aliases: [Named Slots, Children Prop, Content Projection]
first_described: "React documentation, Passing Props to a Component"
maturity: canonical
related: [headless-component, atomic-design]
incompatible_with: []
verified: 2026-08-21
---

# Slot and Children as API

## 1. Name, aliases, and lineage

The canonical name is Slot and Children as API, a composition
technique where a component exposes one or more placeholders that the
consumer fills with their own markup, rather than the component
dictating every piece of content it renders. React's own documentation
states the underlying mechanism directly. "When you nest content
inside a JSX tag, the parent component will receive that content in a
prop called children," and describes the effect precisely. "You can
think of a component with a children prop as having a hole that can
be filled in by its parent components with arbitrary JSX."

The alias **Named Slots** names the web-standard version of the same
idea, where a component exposes several distinct, individually
addressable placeholders rather than a single undifferentiated one.
**Children Prop** names React's own specific mechanism for the
single-placeholder case. **Content Projection** describes the pattern
from the framework-implementation side, projecting content supplied
by the consumer into a position the component itself controls.

## 2. Problem and context

A component that hard-codes every piece of its own content forces a
consumer to accept exactly that content, or to duplicate the entire
component only to change one piece of it. A card component that
renders a fixed heading and a fixed body, for instance, cannot be
reused for a card whose content genuinely differs from consumer to
consumer without either parameterizing every possible piece of
content through props, which grows unwieldy as the variety of
possible content grows, or duplicating the component's structural
markup for each variant. Slot and Children as API solves this by
letting the component own its structural shell, the wrapper, the
layout, the styling, while leaving specific positions within that
shell open for the consumer to fill with whatever content they
actually need, MDN's own documentation calls this "composing
different DOM trees together."

## 3. Forces

The pattern balances the following competing pressures.

- **Reusing structural markup across varied content.** Favored. The
  component's own wrapper, layout, and styling are written once and
  reused, while the specific content filling each slot varies freely
  per consumer, avoiding both prop sprawl and structural duplication.
- **Consumer control over content, without touching structure.**
  Favored. React's own documentation frames this precisely, the
  component "doesn't need to know what's being rendered inside it,"
  since the consumer's own JSX is passed through the children prop or
  a named slot without the component needing to parse or understand
  it.
- **Precision for multiple, distinct content areas.** In tension. A
  single children slot suffices for a component with one content
  area, but a component with several genuinely distinct content
  regions, a header, a body, a footer, needs named slots, which MDN's
  own documentation identifies by their name attribute, to let a
  consumer target each region individually.
- **Loss of control over exactly what gets rendered inside a slot.**
  Sacrificed. Because the component does not inspect or constrain
  what a consumer places into a slot, the component gives up some
  ability to guarantee the slotted content behaves or looks a
  specific way.

## 4. Applicability and non-applicability

Reach for Slot and Children as API when the following hold.

- The component's own structural shell, layout, and styling are
  genuinely reusable, while the specific content filling it varies
  in a real way from consumer to consumer.
- A consumer genuinely needs to supply arbitrary markup, not only a
  simple string or a small, enumerable set of variants that a plain
  prop could represent more simply.
- The component has one clear content area, favoring a single
  children slot, or several genuinely distinct content areas, favoring
  named slots for each.

Do NOT reach for Slot and Children as API in these cases, and the
reason matters more than the rule.

- **The content varies only across a small, enumerable set of known
  variants**, a plain prop, a string, a boolean, an enum value,
  represents that variation more simply and more explicitly than an
  open-ended slot would, and lets the component itself render the
  appropriate markup for each variant.
- **The component genuinely needs to control or validate exactly what
  gets rendered inside a given position**, an open slot accepts
  arbitrary content the component cannot inspect or constrain, so a
  position that genuinely needs that control is better served by a
  typed prop the component itself renders from.
- **There is only ever a single, fixed piece of content for this
  position across every consumer**, exposing a slot for content that
  never actually varies adds an unnecessary indirection with no
  corresponding reuse benefit.

## 5. Structure

Slot and Children as API has two structural parts.

- **The component shell**, the structural markup, layout, and styling
  a component owns and controls, with one or more open positions left
  within it.
- **The slotted content**, the markup a consumer supplies to fill a
  given open position, passed through by the component without being
  parsed or transformed.

## 6. ASCII structure diagram

```
  Component shell

  +----------------------------------------------------------+
  | Card wrapper (owned by the component)                      |
  |                                                              |
  |   +--------------------------------------------------+       |
  |   | children slot, filled by the consumer               |       |
  |   +--------------------------------------------------+       |
  |                                                              |
  +----------------------------------------------------------+

  Named slots, several distinct positions

  +----------------------------------------------------------+
  | Dialog wrapper (owned by the component)                    |
  |                                                              |
  |   +----------------------+                                  |
  |   | header slot            |  filled by the consumer          |
  |   +----------------------+                                  |
  |   +----------------------+                                  |
  |   | body slot              |  filled by the consumer          |
  |   +----------------------+                                  |
  |   +----------------------+                                  |
  |   | footer slot            |  filled by the consumer          |
  |   +----------------------+                                  |
  |                                                              |
  +----------------------------------------------------------+
```

## 7. Dynamics

The trace below shows two consumers filling the same component's
slots with entirely different content.

```
Consumer A uses the Card component

Consumer A nests an Avatar element inside the Card
   |-- the Card component receives that Avatar as its children prop
   |-- the Card renders its own wrapper markup, and renders
       children, whatever that turns out to be, inside it
   |-- the Card itself never needed to know an Avatar was involved

Consumer B uses the same Card component

Consumer B nests a completely different piece of content, a form,
inside the same Card component
   |-- the Card component receives that form as its children prop
   |-- the Card renders the identical wrapper markup as before, with
       the form now filling the same slot the Avatar filled for
       Consumer A
   |-- the Card's own structural code never changed between the two
       uses, only the slotted content did
```

## 8. Implementation variants

**Single children slot.** The most common form, a component with one
open position, filled by whatever a consumer nests directly inside
its opening and closing tags.

**Named slots.** A component exposes several distinct, individually
addressable positions, letting a consumer target a specific slot by
name, MDN's own documentation describes this directly for web
components, where "slots are identified by their name attribute."

**Render-prop-style slots.** Instead of accepting markup directly, a
slot accepts a function that returns markup, letting the component
pass data back into the function so the consumer's supplied content
can depend on state the component itself owns.

**Slot with a default.** A slot that renders fallback content when
the consumer does not supply anything for that position, MDN's own
documentation shows this pattern directly, with a `<slot>` element
that has default content nested inside it, used only when the
consumer provides nothing to fill that slot.

## 9. Known production uses

**React's own documentation, defining the children prop and its
"hole" analogy.** React states the mechanism and the analogy
directly. "When you nest content inside a JSX tag, the parent
component will receive that content in a prop called children," and
"you can think of a component with a children prop as having a hole
that can be filled in by its parent components with arbitrary JSX."
React, "Passing Props to a Component,"
https://react.dev/learn/passing-props-to-a-component, verified
2026-08-21.

**MDN's own documentation, defining the web-standard slot element.**
MDN states the definition and the composing effect directly. A slot
is "a placeholder inside a web component that users can fill with
their own markup, with the effect of composing different DOM trees
together," and "slots are identified by their name attribute." MDN
Web Docs, "Using templates and slots,"
https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_templates_and_slots,
verified 2026-08-21.

## 10. Consequences

Positive.

- Structural markup, layout, and styling are written once and reused
  across every consumer, while the specific content filling each slot
  varies freely, avoiding both prop sprawl and structural duplication.
- The component does not need to know or inspect what is being
  rendered inside its slots, keeping the component's own code simple
  and genuinely decoupled from the content that fills it.
- Named slots let a component expose several genuinely distinct
  content areas, each individually addressable, rather than forcing
  every piece of varied content through a single undifferentiated
  position.

Negative.

- The component gives up the ability to inspect, validate, or
  constrain exactly what gets rendered inside a slot, since arbitrary
  consumer-supplied markup passes through largely unchecked.
- A consumer must understand which slots exist and what each expects,
  an implicit contract that is less explicit and less
  self-documenting than a typed, named prop would be.
- Overusing slots for content that could be represented as a simple,
  enumerable prop trades explicitness for flexibility the use case
  did not actually need.

## 11. Failure modes and misuse

**Exposing a slot for content that only ever varies across a small,
known set of options.** Symptom. Every consumer ends up passing nearly
identical markup into the slot, differing only in a small, predictable
way, such as a label's text or an icon's name, that a plain prop
would have represented far more simply and explicitly. Cause.
Reaching for a slot by default for any varying content, rather than
considering whether the actual variation is simple enough for a typed
prop instead. Fix. Use a plain prop for content that varies across a
small, enumerable set of known options, reserving slots for content
that is genuinely open-ended or arbitrary in its structure.

**Providing no fallback content for a slot a consumer may reasonably
leave empty.** Symptom. A component renders visibly broken or empty
markup when a consumer omits content for an optional slot, rather
than showing a sensible default. Cause. Designing the slot without
considering the case where a consumer has nothing specific to put
there. Fix. Provide default content for an optional slot, rendered
only when the consumer supplies nothing to fill it, the pattern MDN's
own documentation shows directly for the standard slot element.

**Requiring a specific number or exact structure of children without
the component actually validating or communicating that requirement.**
Symptom. A consumer nests the wrong number, or the wrong shape, of
children into a component that silently breaks or renders incorrectly
without any clear indication of what went wrong. Cause. Designing a
component's rendering logic around an implicit assumption about its
children's shape, without validating that assumption or documenting
it clearly for consumers. Fix. Either validate the children's shape
explicitly and surface a clear error when the assumption is violated,
or design the component to handle a genuinely arbitrary set of
children gracefully, rather than silently assuming a specific shape.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Slot and Children as API | Typed content prop, enumerable variants | Fully hard-coded content |
|---|---|---|---|
| Reuse of structural markup across varied content | Strong, one shell, arbitrary content | Strong, one shell, a bounded set of content shapes | Weak, structure must be duplicated per content variant |
| Explicitness of what content is expected | Weak, an implicit contract | Strong, a typed, self-documenting prop | Not applicable, no variation exists |
| Flexibility for genuinely arbitrary content | Strong | Weak, bounded to the enumerated variants | Weak, no variation at all |
| Component's ability to inspect and validate content | Weak, content passes through largely unchecked | Strong, the component controls exactly what each variant renders | Strong, but at the cost of no reuse |

Reading of the table. Slot and Children as API wins specifically when
content is genuinely open-ended or arbitrary in its structure, and a
typed prop cannot reasonably enumerate the variation. A typed content
prop wins when the variation is genuinely bounded and explicitness
matters more than open-ended flexibility, and hard-coded content
remains correct only when no real variation exists at all.

## 13. Related and incompatible patterns

- **Headless Component.** A complementary technique frequently
  combined with slots, a headless component exposes behavior and
  state through a plain interface while the consumer's slotted
  content supplies the actual visual markup that behavior drives.
- **Atomic Design.** The structural vocabulary, atoms, molecules,
  organisms, that a component exposing slots often sits inside,
  since a molecule or organism frequently owns its own structural
  shell while accepting atoms or other molecules as slotted content.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing component whose content is
currently hard-coded or over-parameterized through many individual
props.

1. Identify the component's structural shell, the layout, wrapper,
   and styling that genuinely stays constant across every consumer.
2. Identify the specific content that genuinely varies per consumer,
   distinguishing content that is open-ended or arbitrary in its structure
   from content that is really a small, enumerable set of variants.
3. Replace the open-ended, arbitrary content with a children prop or
   a named slot, letting the consumer supply that content directly
   rather than the component parameterizing it through individual
   props.
4. Keep the genuinely enumerable content as typed props, rather than
   converting everything into slots by default.
5. Add default content for any slot a consumer may reasonably leave
   empty, so the component renders sensibly without it.

Removing the pattern when it stops earning its place, most relevant
when a slot's content has, in practice, settled into a small,
predictable set of variants across every real consumer.

1. Confirm, by surveying actual consumers, that the slot's content has
   genuinely settled into a small, enumerable set of variants, rather
   than assuming so without checking.
2. Replace the slot with a typed prop representing that enumerable set,
   letting the component itself render the appropriate markup for
   each variant.
3. Update each consumer to pass the new typed prop instead of the
   previously slotted markup, confirming the resulting rendered output
   is unchanged.

## 15. Testing and verification

Easier because of the pattern.

- A test can assert the component's shell renders correctly with
  arbitrary placeholder content in its slot, without needing to
  account for every possible real-world content variation
  individually.
- Because the component does not inspect its slotted content, testing
  the component's own structural behavior is decoupled from testing
  whatever content a specific consumer happens to supply.

Harder because of the pattern.

- Verifying that a specific consumer's slotted content renders
  correctly within the component's shell needs a test for that
  specific consumer's combination, since the component's own tests
  say nothing about any particular consumer's actual content.
- Testing a component's behavior when a slot is left empty, or filled
  with unexpected content, needs deliberate edge-case coverage, since
  the component's open-ended acceptance of arbitrary content makes it
  easy to overlook the empty or malformed case.

Techniques that apply.

- **Shell-only rendering tests.** Render the component with simple
  placeholder content in each slot, asserting the shell's own
  structure, layout, and styling render correctly independent of any
  real content.
- **Per-consumer integration tests.** For a specific consumer's real
  slotted content, test that the combination of shell and content
  renders and behaves correctly together.
- **Empty and default slot tests.** Render the component with a given
  slot deliberately left empty, asserting the correct default content,
  or the correct empty-state behavior, renders instead.
- **Malformed content tests.** Where a component makes an implicit
  assumption about its children's shape, test that assumption being
  violated, confirming the component either handles it gracefully or
  surfaces a clear error.

## 16. Observability signals

Slot and Children as API has a small, mostly structural runtime
footprint, so the more honest signal here is about consistency and
correct usage across consumers rather than raw performance.

What to record.

- The variety and shape of content different consumers actually place
  into a given slot, since a slot receiving wildly inconsistent or
  unexpected content shapes may indicate the slot's implicit contract
  is unclear or the slot itself may need to become a more explicit,
  typed prop.
- Reports of rendering issues specifically tied to a component's
  slotted content, since these point at either a shell that does not
  gracefully handle the range of content consumers actually supply,
  or a missing default for an optional slot.

A healthy state. Consumers supply a genuinely varied but
compatible range of content into each slot, and the component's shell
renders correctly regardless of which specific consumer's content
fills it.

A failing state. A slot consistently receives content narrow enough
in shape that it could have been a typed prop instead, suggesting the
slot's flexibility is not earning its implicit-contract cost, or the
component's shell breaks or renders incorrectly for some consumers'
content, pointing at an unhandled edge case in how the shell composes
with arbitrary slotted content.

## 17. Security and privacy implications

Slot and Children as API carries a real, specific implication worth
naming directly, since it means a component's shell renders content
it did not author and does not control.

**When the slotted content itself originates from an untrusted
source, such as user-generated content rendered through a slot rather
than through the framework's own safe text-rendering path, the
component's acceptance of arbitrary content can become a cross-site
scripting vector if that untrusted content is inserted as raw markup
rather than safely escaped or sanitized text.** The component's own
job is to compose whatever content it receives, not to sanitize it,
so the responsibility for confirming slotted content is safe to render
belongs to whichever layer sources that content, not to the slotting
mechanism itself, and a component accepting a slot should document
clearly whether it expects the consumer to have already ensured the
content is safe.

## 18. References

1. React. "Passing Props to a Component".
   https://react.dev/learn/passing-props-to-a-component
   Verified 2026-08-21. Source of the children prop and "hole" analogy
   quotes used in dimensions 1, 3, and 9.
2. MDN Web Docs. "Using templates and slots".
   https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_templates_and_slots
   Verified 2026-08-21. Source of the web-standard slot definition and
   named-slot quotes used in dimensions 1, 8, and 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a component shell
accepting a children-style slot the way React's own children prop
works, kept free of JSX and any specific framework's package so the
sample compiles as plain TypeScript, representing the slotted content
as a generic render function. Python shows the conceptual shape of
the same shell-and-slot composition using a minimal, framework-agnostic
implementation, since Python has no browser-facing component model
and therefore no single dominant slot implementation the way
TypeScript has React's children prop and the web-standard slot
element. Swift shows the same conceptual shape using a minimal model,
analogous to how SwiftUI's own ViewBuilder-based composition lets a
view accept arbitrary child content supplied by whoever uses it. Java,
Go, and Rust are omitted, since none has a dominant, idiomatic
browser-facing component framework this specifically UI-composition
pattern maps to as directly as TypeScript does.

### TypeScript

```typescript
interface CardShellOptions {
  title: string;
  renderContent: () => string;
}

function renderCardShell(options: CardShellOptions): string {
  const content = options.renderContent();
  return "Card[" + options.title + "]: " + content;
}

function renderAvatarContent(): string {
  return "Avatar(Katsuko Saruhashi)";
}

function renderFormContent(): string {
  return "Form(fields: name, email)";
}

const cardA = renderCardShell({
  title: "Profile",
  renderContent: renderAvatarContent,
});

const cardB = renderCardShell({
  title: "Signup",
  renderContent: renderFormContent,
});

console.log(cardA);
console.log(cardB);
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class CardShellOptions:
    title: str
    render_content: Callable[[], str]


def render_card_shell(options: CardShellOptions) -> str:
    content = options.render_content()
    return f"Card[{options.title}]: {content}"


def render_avatar_content() -> str:
    return "Avatar(Katsuko Saruhashi)"


def render_form_content() -> str:
    return "Form(fields: name, email)"


if __name__ == "__main__":
    card_a = render_card_shell(CardShellOptions(title="Profile", render_content=render_avatar_content))
    card_b = render_card_shell(CardShellOptions(title="Signup", render_content=render_form_content))

    print(card_a)
    print(card_b)
```

### Swift

```swift
struct CardShellOptions {
    let title: String
    let renderContent: () -> String
}

func renderCardShell(_ options: CardShellOptions) -> String {
    let content = options.renderContent()
    return "Card[" + options.title + "]: " + content
}

func renderAvatarContent() -> String {
    "Avatar(Katsuko Saruhashi)"
}

func renderFormContent() -> String {
    "Form(fields: name, email)"
}

let cardA = renderCardShell(CardShellOptions(title: "Profile", renderContent: renderAvatarContent))
let cardB = renderCardShell(CardShellOptions(title: "Signup", renderContent: renderFormContent))

print(cardA)
print(cardB)
```
