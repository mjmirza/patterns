---
name: Atomic Design
slug: atomic-design
family: 13-frontend-ui
category: Component Architecture
aliases: [Atoms Molecules Organisms, Component Hierarchy Design]
first_described: "Brad Frost, 10 June 2013"
maturity: established
related: [provider-pattern, higher-order-component, render-props]
incompatible_with: []
verified: 2026-08-21
---

# Atomic Design

## 1. Name, aliases, and lineage

The canonical name is Atomic Design, a methodology for structuring a
component library into five distinct levels of composition, borrowed
from chemistry's own hierarchy of matter. Its creator, Brad Frost,
states the idea directly in the original 2013 post. "Atomic design is
methodology for creating design systems," built on the observation
that "we're not designing pages, we're designing systems of
components."

The alias **Atoms Molecules Organisms** names the first three, and
best known, levels of the five-level hierarchy. **Component Hierarchy
Design** is a more generic, descriptive name for the same layered
composition idea, used by teams who adopt the underlying structure
without the chemistry-derived vocabulary.

## 2. Problem and context

Before Atomic Design, a component library commonly organized
components by feature or by page, a folder for the checkout flow next
to a folder for the settings page, which left no explicit, shared
vocabulary for talking about how small a given component actually is
relative to the rest of the system, and no natural place for a truly
tiny, reusable primitive such as a button or a label to live
independent of any specific feature. Atomic Design solves this by
defining five explicit levels of composition, atoms, molecules,
organisms, templates, and pages, each level built only from the level
directly below it, giving every component in the system a
well-defined size and a well-defined place, independent of which
feature happens to use it.

## 3. Forces

The pattern balances the following competing pressures.

- **A shared vocabulary for component granularity.** Favored. Naming
  a component an atom, a molecule, or an organism gives a team a
  precise, shared way to talk about how small and how reusable a
  given component is, rather than relying on vague terms such as
  small component or big component.
- **Composition from the smallest reusable pieces upward.** Favored.
  Building organisms only from molecules, and molecules only from
  atoms, forces a genuinely bottom-up composition discipline, so a
  large, feature-specific organism is still built from primitives
  that remain independently reusable elsewhere.
- **Rigid level assignment for a component that does not fit
  cleanly.** Sacrificed unless the team stays flexible. A real
  component sometimes sits ambiguously between two levels, and a team
  applying the taxonomy too literally can spend more effort arguing
  about which level a component belongs to than building the
  component itself.
- **A single, systematic path from primitive to full page.** Favored.
  Because templates and pages are explicitly the top two levels,
  composed from organisms, the taxonomy gives every component a
  traceable path from its smallest constituent atoms all the way up
  to a fully assembled page.

## 4. Applicability and non-applicability

Reach for Atomic Design when the following hold.

- The team is building or maintaining a genuine design system, a
  shared component library intended to be reused across several
  products or several teams, where a precise, shared vocabulary for
  component granularity earns its keep.
- The interface has enough distinct, reusable primitives, buttons,
  labels, inputs, that composing them upward into progressively
  larger, named groupings genuinely clarifies the system rather than
  adding ceremony on top of a handful of one-off components.
- The team is prepared to apply the taxonomy loosely where a
  component does not fit cleanly, rather than treating the five
  levels as a rigid classification every component must be forced
  into.

Do NOT reach for Atomic Design in these cases, and the reason matters
more than the rule.

- **The project is a small, single-purpose application with few
  reusable components**, imposing five named levels on a handful of
  components that are each used in exactly one place adds a
  vocabulary and a folder structure the project does not need.
- **The team treats the five levels as a rigid classification that
  must be argued to consensus for every component**, the taxonomy's
  value is a shared vocabulary, not a bureaucratic gate, and forcing
  every ambiguous case to a strict verdict defeats the purpose.
- **The interface has almost no shared primitives across features**,
  a design with little genuine reuse gains little from a taxonomy
  whose entire value rests on components being composed upward from
  a small, shared set of atoms.

## 5. Structure

Atomic Design defines five levels, each built only from the level
directly below it.

- **Atoms**, the smallest, indivisible building blocks, described in
  Frost's own words as "our HTML tags, such as a form label, an
  input or a button."
- **Molecules**, small groups of atoms joined together, described as
  "the smallest fundamental units of a compound," taking on distinct
  properties the atoms alone do not have. Frost's later book on the
  methodology restates the same layer plainly. "Molecules are
  collections of atoms that form relatively simple UI components."
- **Organisms**, described as "groups of molecules joined together to
  form a relatively complex, distinct section of an interface," such
  as a header combining a logo, a navigation molecule, and a search
  molecule.
- **Templates**, collections of organisms arranged to show a page's
  layout and structure, using placeholder content rather than real
  content.
- **Pages**, described as "specific instances of templates," where
  "placeholder content is replaced with real representative content."

## 6. ASCII structure diagram

```
  Pages          [ Real content assembled into a template's layout ]
                              ^
                              |
  Templates      [ Organisms arranged to show layout, placeholder content ]
                              ^
                              |
  Organisms      [ Header = Logo(atom) + NavMenu(molecule) + SearchBar(molecule) ]
                              ^
                              |
  Molecules      [ SearchBar = Label(atom) + Input(atom) + Button(atom) ]
                              ^
                              |
  Atoms          [ Label ]  [ Input ]  [ Button ]
```

## 7. Dynamics

The trace below shows a search feature composed bottom-up, from its
constituent atoms through to a rendered page.

```
Defining the atoms

three atoms are defined independently
   |-- Label, a plain HTML label
   |-- Input, a plain HTML text input
   |-- Button, a plain HTML button

Composing the molecule

a SearchBar molecule combines the three atoms
   |-- Label, Input, and Button are composed together
   |-- the molecule takes on a distinct property none of the atoms
       had alone, submitting a search query

Composing the organism

a Header organism combines the SearchBar molecule with others
   |-- SearchBar molecule, a Logo atom, and a NavMenu molecule
       are composed together into one Header organism

Assembling the template and the page

a SearchResultsTemplate arranges organisms with placeholder content
   |-- the Header organism is placed at the top of the layout
   |-- a ResultsList organism is placed below it, holding placeholder
       result items

a SearchResultsPage replaces the placeholder content with real data
   |-- the template's placeholder result items are replaced with the
       user's actual search results
```

## 8. Implementation variants

**Folder-per-level organization.** A component library's source tree
organized into five top-level folders, `atoms/`, `molecules/`,
`organisms/`, `templates/`, and `pages/`, the most literal
implementation of the taxonomy.

**A living style guide or component catalog.** A tool such as
Storybook, organized to browse and document every component grouped
by its atomic level, letting a designer or developer see the entire
system's building blocks at every level of composition in one place.
Frost's own follow-up post on pairing the methodology with Storybook
states the practice directly. "we find it valuable to bucket our
components based on the atomic design vernacular," organizing a
component library's catalog entries by level, such as titling an
alert component's story `Molecules/Messaging/Alert`.

**Loosely applied vocabulary without a strict folder structure.** A
team that adopts the naming and the bottom-up composition discipline
in conversation and in code review, without enforcing a literal
folder-per-level file layout, applying the taxonomy as a shared
mental model rather than a mandatory directory structure.

**Design-tool component libraries mirroring the same hierarchy.** A
design tool's own component and variant system, organized to mirror
the same atoms-through-organisms hierarchy, so the design file and
the codebase's component library stay conceptually aligned.

## 9. Known production uses

**Brad Frost's original 2013 methodology post, defining the five
levels.** Frost's own post states the core idea directly. "Atomic
design is methodology for creating design systems," and frames the
whole approach around the observation that "we're not designing
pages, we're designing systems of components." The post defines each
level in Frost's own words, atoms as "our HTML tags, such as a form
label, an input or a button," organisms as "groups of molecules
joined together to form a relatively complex, distinct section of an
interface," and pages as "specific instances of templates" where
"placeholder content is replaced with real representative content."
Brad Frost, "Atomic Web Design,"
https://bradfrost.com/blog/post/atomic-web-design/, verified
2026-08-21.

## 10. Consequences

Positive.

- The five named levels give a team a precise, shared vocabulary for
  discussing how small and how reusable a given component is,
  replacing vague terms such as small component or big component.
- Building strictly bottom-up, organisms only from molecules and
  molecules only from atoms, keeps small primitives genuinely
  reusable, since they are never accidentally coupled to a specific
  feature's larger composition.
- Templates and pages give a design system a traceable, systematic
  path from its smallest constituent atoms all the way up to a fully
  assembled, real page.

Negative.

- A component that does not fit cleanly into one of the five levels
  can cost a team more debate over which level it belongs to than the
  taxonomy's clarity is worth for that specific component.
- A small, single-purpose application with few genuinely reusable
  components gains little from five named levels of composition, and
  pays a real folder-structure and vocabulary cost for it regardless.
- The taxonomy names structure, not behavior, so a team can organize
  a component library perfectly along atomic lines while still
  producing components that are individually poorly designed or
  inconsistent in behavior.

## 11. Failure modes and misuse

**Forcing every component into a strict, single, agreed level before
any work can proceed.** Symptom. Design and development reviews spend
a real amount of time debating whether a given component is a
molecule or an organism, rather than discussing whether the component
itself is well designed. Cause. Treating the five levels as a rigid
classification that every component must be resolved to, rather than
a loose, shared vocabulary. Fix. Apply the taxonomy loosely, letting
an ambiguous component sit at whichever level is most useful for
communication, and move on rather than litigating the boundary case.

**Building a molecule or an organism that secretly depends on a
feature-specific detail, breaking the bottom-up reusability the
taxonomy is meant to guarantee.** Symptom. A molecule that appears
reusable by name and by folder location cannot actually be reused
elsewhere, because it silently depends on a specific page's data
shape or a specific feature's business logic. Cause. Organizing
components into the correct folders without actually keeping each
level's components free of dependencies on anything above their own
level. Fix. Keep atoms and molecules free of any dependency on a
specific feature, page, or data shape, so the folder structure the
taxonomy implies is also true in practice.

**Treating the five-level taxonomy as a substitute for actual design
system governance.** Symptom. A component library is neatly organized
into atoms, molecules, and organisms, yet individual components
remain visually inconsistent, since no design tokens, style guide, or
review process enforces consistency across them. Cause. Assuming the
taxonomy's organizational structure alone produces design
consistency, when the taxonomy only names how components compose,
not whether they are individually consistent. Fix. Pair the taxonomy
with a real design token system and a review process, so structural
organization and visual consistency are both maintained, not the
structure alone.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Atomic Design | Feature-based organization | Flat component folder | Domain-driven component organization |
|---|---|---|---|---|
| Shared vocabulary for component size | Strong, five named, precise levels | Weak, no explicit granularity vocabulary | Weak, the same gap | Weak, organized by domain, not by size |
| Encourages bottom-up reusable primitives | Strong, by construction | Weak, components often stay feature-local | Neutral, depends entirely on discipline | Weak, primitives can hide inside domain folders |
| Clarity for a small, single-purpose app | Weak, unneeded ceremony | Strong | Strong | Weak, unneeded ceremony |
| Fit for a genuine, multi-team design system | Strong | Weak, features do not naturally align across teams | Weak, no organizational signal at all | Moderate, good for domain clarity, weaker for granularity |
| Risk of rigid, unproductive level debates | Real, if applied strictly | Not applicable | Not applicable | Not applicable |

Reading of the table. Atomic Design wins specifically for a genuine,
multi-team design system where a shared vocabulary for component
granularity earns real value. A small, single-purpose application, or
a team that already has a clear feature or domain-based organization
that works, gains little from adopting five additional named levels.

## 13. Related and incompatible patterns

- **Provider Pattern.** A complementary pattern used to supply shared
  context, such as a design system's theme, down through every level
  of the atomic hierarchy without threading it through each
  component's props individually.
- **Higher-Order Component.** A pattern often used to add
  cross-cutting behavior, such as analytics tracking, to a component
  at any of the five atomic levels without changing that component's
  own internal implementation.
- **Render Props.** An alternative composition mechanism sometimes
  used inside a molecule or organism to make its child's rendering
  logic itself an injectable, reusable piece.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a component library whose organization has
grown feature-based or flat enough that reusable primitives are
becoming hard to find and duplicate work is common.

1. Inventory the existing components and classify each one as an
   atom, a molecule, an organism, a template, or a page, based on
   what it is actually composed of today.
2. Extract any component that is secretly a molecule or an organism
   but currently hand-writes its own atoms inline, replacing the
   inline markup with genuine atom components.
3. Reorganize the component library's folder structure, or its
   catalog tool's grouping, along the five levels, so the
   organization reflects the classification from step 1.
4. Establish a lightweight review convention for new components,
   confirming a proposed component is composed only from the level
   directly below it, without demanding a strict, argued verdict for
   every ambiguous case.
5. Add a test or a linting rule asserting that no atom or molecule
   component imports anything from a feature-specific or page-level
   module, keeping the bottom-up dependency direction genuinely
   enforced.

Removing the pattern when it stops earning its place, most relevant
when a project has shrunk to a small, single-purpose application, or
the taxonomy's five levels have become a source of unproductive
debate rather than clarity.

1. Confirm the design system's genuine multi-team reuse has actually
   shrunk, rather than assuming so without review.
2. Collapse the five-level folder structure into whatever simpler
   organization, feature-based or flat, best matches the project's
   current, smaller scope, preserving each component's external
   interface so consumers require minimal changes.
3. Retire the atomic-level vocabulary from code review and
   documentation once the folder structure itself no longer reflects
   it.

## 15. Testing and verification

Easier because of the pattern.

- An atom, being the smallest indivisible building block, is
  trivially testable in isolation, since it has no dependency on
  anything else in the system by construction.
- Because each level is composed only from the level directly below
  it, a bug traced to a specific organism can be narrowed down by
  testing its constituent molecules independently, rather than
  needing to test the whole assembled page to isolate the fault.

Harder because of the pattern.

- Testing a template or a page needs assembling several real
  organisms together, which can need more setup than testing an
  equivalent flat component that happens to render the same output
  without formal composition.
- The taxonomy itself provides no signal about whether the components
  it organizes are individually well tested, so a project can be
  neatly organized into atoms and molecules while still having weak
  test coverage of the actual component behavior.

Techniques that apply.

- **Visual regression testing per level.** Render each atom, each
  molecule, and each organism in isolation and compare against a
  known-good screenshot, catching an unintended visual change at the
  smallest level where it originated.
- **Isolated atom unit tests.** Test each atom's behavior directly,
  independent of any molecule or organism that later composes it.
- **Composition tests at the organism level.** Assert that an
  organism correctly composes and passes data down to its constituent
  molecules and atoms, catching a wiring bug the individual atom and
  molecule tests would not surface.
- **Full-page integration tests.** Render an assembled page with real
  data and assert the end-to-end behavior, confirming the bottom-up
  composition genuinely produces the intended top-level result.

## 16. Observability signals

Atomic Design is a source-level and design-system organizational
methodology with no independent runtime footprint of its own, and
inventing a dedicated production signal purely for the pattern would
be dishonest. Two things are worth watching in a codebase that uses
it.

What to record.

- How often a genuinely new atom or molecule is introduced versus how
  often an existing one is reused, since a design system where every
  new feature introduces new atoms rather than reusing existing ones
  is a signal the taxonomy's reuse benefit is not actually being
  realized.
- The size and count of the components at each level over time, since
  a component library that keeps its distribution weighted toward
  atoms and molecules, rather than accumulating an ever-growing pile
  of one-off organisms, is a healthier design system.

A healthy state. New features are built primarily by composing
existing atoms and molecules into new organisms and templates, rather
than by writing new atoms for every feature.

A failing state. A steadily growing count of near-duplicate atoms or
molecules that differ only slightly from an existing one, pointing at
a design system whose components are not actually being discovered
and reused, defeating the pattern's core purpose.

## 17. Security and privacy implications

Atomic Design is close to neutral for security, being a component
organization methodology rather than a data-handling one, and
inventing a dedicated attack surface here would be dishonest. One
practical implication is worth naming.

**A shared atom or molecule reused across many features becomes a
single point of consequence for a security or accessibility defect,
since a flaw introduced into a widely reused atom, such as a form
input that fails to sanitize its display value, propagates to every
organism, template, and page that composes it.** Because the whole
value of Atomic Design rests on wide reuse of a small set of
primitives, a team adopting it should hold its atoms and molecules to
a higher bar of security and accessibility review than a one-off,
feature-specific component would need, precisely because a defect at
that level reaches so much of the system at once.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models an atom composed into
a molecule the way a component library structures the hierarchy,
kept free of JSX and any specific framework's package so the sample
compiles as plain TypeScript. Python shows the same conceptual split
using a minimal, framework-agnostic function-based composition,
representing atoms, molecules, and organisms as plain data structures
that render to a string, since Python has no single dominant
component-hierarchy UI framework the way TypeScript has React or Vue.
Swift shows the pattern using SwiftUI-style struct composition, an
atom view composed into a molecule view, closely analogous to how the
taxonomy is applied in native mobile design systems. Java, Go, and
Rust are omitted, since none has a dominant, idiomatic UI-component
framework this specifically frontend and design-system pattern maps
to as directly as TypeScript and Swift do.

### TypeScript

```typescript
interface Atom {
  render(): string;
}

class LabelAtom implements Atom {
  constructor(private text: string) {}

  render(): string {
    return "<label>" + this.text + "</label>";
  }
}

class InputAtom implements Atom {
  constructor(private placeholder: string) {}

  render(): string {
    return "<input placeholder='" + this.placeholder + "' />";
  }
}

class ButtonAtom implements Atom {
  constructor(private label: string) {}

  render(): string {
    return "<button>" + this.label + "</button>";
  }
}

class SearchBarMolecule implements Atom {
  private label: LabelAtom;
  private input: InputAtom;
  private button: ButtonAtom;

  constructor() {
    this.label = new LabelAtom("Search");
    this.input = new InputAtom("Type to search");
    this.button = new ButtonAtom("Go");
  }

  render(): string {
    return (
      this.label.render() + this.input.render() + this.button.render()
    );
  }
}

const searchBar = new SearchBarMolecule();
console.log(searchBar.render());
```

### Python

```python
from dataclasses import dataclass


@dataclass
class LabelAtom:
    text: str

    def render(self) -> str:
        return f"<label>{self.text}</label>"


@dataclass
class InputAtom:
    placeholder: str

    def render(self) -> str:
        return f"<input placeholder='{self.placeholder}' />"


@dataclass
class ButtonAtom:
    label: str

    def render(self) -> str:
        return f"<button>{self.label}</button>"


@dataclass
class SearchBarMolecule:
    label: LabelAtom
    input_field: InputAtom
    button: ButtonAtom

    def render(self) -> str:
        return self.label.render() + self.input_field.render() + self.button.render()


if __name__ == "__main__":
    search_bar = SearchBarMolecule(
        label=LabelAtom(text="Search"),
        input_field=InputAtom(placeholder="Type to search"),
        button=ButtonAtom(label="Go"),
    )
    print(search_bar.render())
```

### Swift

```swift
struct LabelAtom {
    let text: String

    func render() -> String {
        "<label>" + text + "</label>"
    }
}

struct InputAtom {
    let placeholder: String

    func render() -> String {
        "<input placeholder='" + placeholder + "' />"
    }
}

struct ButtonAtom {
    let label: String

    func render() -> String {
        "<button>" + label + "</button>"
    }
}

struct SearchBarMolecule {
    let label: LabelAtom
    let input: InputAtom
    let button: ButtonAtom

    func render() -> String {
        label.render() + input.render() + button.render()
    }
}

let searchBar = SearchBarMolecule(
    label: LabelAtom(text: "Search"),
    input: InputAtom(placeholder: "Type to search"),
    button: ButtonAtom(label: "Go")
)

print(searchBar.render())
```

## 18. References

1. Brad Frost. "Atomic Web Design".
   https://bradfrost.com/blog/post/atomic-web-design/
   Verified 2026-08-21. Source of the defining sentence and all five
   level definitions quoted in dimensions 1, 5, and 9.
2. Brad Frost. "Atomic Design," Chapter 2.
   https://atomicdesign.bradfrost.com/chapter-2/
   Verified 2026-08-21. Source of the molecules definition quoted in
   dimension 5.
3. Brad Frost. "Atomic Design and Storybook".
   https://bradfrost.com/blog/post/atomic-design-and-storybook/
   Verified 2026-08-21. Source of the Storybook organization quote in
   dimension 8.
