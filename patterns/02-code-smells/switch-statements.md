---
name: Switch Statements
slug: switch-statements
family: 02-code-smells
category: Object-Orientation Abusers
aliases: [Type Code Switch, Case Statement Smell, Switch on Type]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999, Refactoring, Improving the Design of Existing Code"
maturity: canonical
related: [factory-method, alternative-classes-with-different-interfaces, refused-bequest, primitive-obsession, data-class]
incompatible_with: []
verified: 2026-08-02
---

# Switch Statements

## 1. Name, aliases, and lineage

The canonical name is Switch Statements. It is one of the original smells
catalogued in Martin Fowler, with Kent Beck, John Brant, William Opdyke, and
Don Roberts, *Refactoring, Improving the Design of Existing Code*,
Addison-Wesley, 1999, Chapter 3, "Bad Smells in Code". The book pairs the
smell with a set of matching cures rather than a single one, because a switch
on a type code can be dissolved several different ways depending on what the
switch actually does. The primary companion refactoring is Replace Conditional
with Polymorphism, documented on Fowler's own maintained catalog site with the
bird-plumage worked example. a switch that inspects a bird's species field and
returns a plumage description is replaced by giving each bird subclass its own
`plumage` method, source
https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html,
verified 2026-08-02. The same catalog also lists two sibling refactorings that
attack the smell from a different angle, Replace Type Code with Subclasses
(aliased Extract Subclass and Replace Type Code with State/Strategy) and
Remove Flag Argument (aliased Replace Parameter with Explicit Methods),
confirmed present in the live catalog index at
https://refactoring.com/catalog/, verified 2026-08-02. Three separate named
refactorings existing for one smell is itself evidence that "switch on a type
code" is not one problem with one fix, it is a family of related problems that
happen to share a syntax.

This repository groups Switch Statements under Object-Orientation Abusers, a
category label used consistently across the sibling entries for Refused
Bequest and Alternative Classes with Different Interfaces in this same
family. As those entries note, the category grouping is a widely used way of
summarizing the 1999 catalogue in secondary teaching sources rather than a
direct quotation from the book itself, and it is presented here as
engineering categorization on that same honesty basis.

The most common alias in day to day conversation is Type Code Switch, used
whenever the discussion needs to distinguish a switch that dispatches on an
open ended type discriminant (the smell) from a switch that dispatches on a
genuinely closed, small, non extensible set of values, which is not the
smell at all, see dimension 4. Case Statement Smell appears in Pascal and
Ada influenced writing where the construct is spelled `case` rather than
`switch`. Switch on Type is a common paraphrase used specifically when the
discriminant is a runtime type tag or a `kind` field on a tagged union,
which is the shape of the majority of real occurrences discussed in this
entry.

A test that separates a legitimate switch from the smell recurs through
every dimension below, so it is stated once here. Does the set of case
labels grow every time the business adds a new kind of the thing being
switched on, and does that same set of case labels reappear, case for case,
in more than one function across the codebase? If both are true, this is the
smell. If the case labels are fixed by something outside the codebase's
control, an HTTP status code, a day of the week, an opcode defined by
hardware, the test fails and the construct is simply a switch statement
doing its job, see dimension 4.

## 2. Problem and context

The problem starts small and grows by exactly the mechanism the smell is
named for, switching.

A codebase introduces a type discriminant, most often a string, an enum
member, or a `kind` field on an otherwise plain data object, to distinguish
between a handful of related variants of one concept, shapes, payment
methods, notification channels, document formats. The first function that
needs to behave differently per variant writes a switch statement over the
discriminant. This is fine and often the right call for a single function; a
switch is fast to write, fast to read for a reader unfamiliar with the
codebase, and requires no new types.

The problem appears when a second function needs to behave differently per
variant too, and a third, and the codebase now has to decide between two
options at each new call site. Either it copies the switch, case labels and
all, into the new function, or it reaches into a shared helper and starts
passing extra parameters through it to distinguish the callers. Both moves
degrade the design in the same specific way. the list of variants is now
implicit knowledge distributed across every switch, rather than a single
place a reader or a compiler can point to. Adding one new variant, say a new
shape kind, now means finding every switch that enumerates the existing
kinds and adding a matching case to each one, by hand, with no mechanical way
to know the search is complete unless the language's exhaustiveness checking
happens to catch the gap (see dimension 8), or unless a `default` case masks
the omission by silently doing nothing.

This is the same failure mode Shotgun Surgery describes at a higher level of
abstraction. One conceptual change, a new variant, requires many small edits
scattered across the codebase, every switch that enumerates variants, and
Switch Statements is the specific, mechanically detectable code shape that
produces that Shotgun Surgery outcome.

The context in which this problem is real, not hypothetical, has three
ingredients present at once.

- The set of variants is genuinely open over the lifetime of the system, new
  payment methods, new document formats, new notification channels arrive on
  at a pace measured in months or years, not never.
- More than one function or method needs variant specific behaviour for the
  same discriminant. A single switch used once, in one place, is not this
  smell no matter how many cases it has, because there is nothing to keep in
  sync.
- The variant specific behaviour is genuinely coupled to the variant's own
  data, not merely a lookup of a constant. A switch that only maps an enum to
  a display string is a weaker case of the smell than one that computes
  something from fields that differ per variant, because the fix for the
  first is often a lookup table, not a type hierarchy, see dimension 8.

## 3. Forces

The following pressures are named as engineering judgement. they describe
the trade-offs practitioners weigh when deciding whether the smell has
become expensive enough to fix, not facts drawn from a single citable
source.

- **Change amplification.** Sacrificed by the smell, favoured by the fix. The
  more call sites carry a copy of the same switch, the more edits a single
  new variant costs, and the harder it is to prove all copies were found and
  updated. This is the dominant force and the reason the smell is worth
  naming at all.
- **Locality of reasoning.** Favoured by the smell in its early life, because
  a reader who wants to understand what happens for one variant can read
  one function top to bottom without following a virtual dispatch into a
  separate file. This reverses once the switch is duplicated three or more
  times, because now understanding the full behaviour of one variant means
  finding every one of those switches.
- **Extensibility by outsiders.** Sacrificed by the smell when the variant
  set lives inside the same module as the switches. A plugin author, a
  downstream team, or a client of a library cannot add a new variant without
  editing source they may not own, because the switch's `default` case, or
  its absence, is the only extension point and it offers no structure.
  Polymorphism fixes this by turning "add a case" into "add a class that
  satisfies an interface", which does not require editing existing code.
- **Compile-time safety.** A wash, decided entirely by language and tooling.
  A switch with no default in Rust, or a pattern matching switch over a
  sealed hierarchy in Java 21, is exhaustiveness checked by the compiler, so
  missing a case is a build failure rather than a silent runtime gap (see
  dimension 8). The identical switch shape in older Java, in Go's type
  switch, or in JavaScript is not checked by the compiler at all, and the
  smell's real cost rises sharply in exactly those languages.
- **Cyclomatic complexity.** Sacrificed as the case count grows, presented
  here as judgement rather than a sourced fact. Static analysis tooling
  conventionally counts each additional case label as one more independent
  path through the enclosing function, an extension of Thomas J. McCabe's
  1976 decision-point metric that his original definition covers for `if`
  statements and conditional loops but does not itself spell out for switch
  case labels, confirmed by the absence of any explicit switch treatment in
  the general summary of the metric, source
  https://en.wikipedia.org/wiki/Cyclomatic_complexity, verified 2026-08-02.
  Each case that survives a Fix A refactor moves to its own method on its
  own class, where it contributes far less to the complexity of any single
  function.
- **Cognitive load per site.** Favoured by the smell for the first reader,
  sacrificed by the fix. Polymorphism trades one big, linear, easy to scan
  function for several small classes, each of which is easy to read alone
  but harder to survey as a set, because there is no longer one place that
  lists every variant's behaviour side by side. This is why some codebases
  keep the switch and add a completeness test instead of refactoring away
  from it entirely, see dimension 14.
- **Testability of the dispatch itself.** Favoured by neither shape
  automatically. A switch and a polymorphic dispatch are equally
  straightforward to unit test per variant; the difference shows up in how
  easy it is to test that the dispatch is complete, which favours whichever
  shape the language can exhaustiveness-check.

No fix here is free. Removing the smell always trades a flat, linear read for
a distributed one, and the entry's job is to help a reader decide when that
trade is worth making, not to declare switch statements universally wrong.

## 4. Applicability and non-applicability

Treat the switch as a smell, and reach for a fix, when the following hold.

- The same discriminant is switched on in two or more functions, methods, or
  files, and the case lists have to be kept in sync by hand.
- New variants arrive often enough that a missed switch becomes a real,
  recurring incident rather than a one time event.
- The variant specific logic is more than a constant lookup. it branches
  further, calls different collaborators, or has different failure modes per
  variant.
- Downstream code outside the module that owns the switch needs to add new
  variants, and editing the switch's source is not an option for that code.
- The language offers no compiler-checked exhaustiveness for the switch, so
  a missed case fails silently or throws at runtime instead of failing the
  build.

Do NOT reach for a fix, and do not treat the construct as a smell, when any
of the following hold. This list is deliberately as long as the first,
because most catalogs skip it and it is where the majority of switch
statements in real code correctly live.

- The variant set is closed by something outside the codebase's control and
  will not grow. an HTTP method, a day of the week, a small fixed set of
  currency codes for a payment provider that will not add a seventh major
  currency next quarter, an instruction opcode defined by a CPU
  specification. A closed, externally fixed set has nothing to synchronize,
  because there is only ever one place it is enumerated.
- The switch appears exactly once in the entire codebase and there is no
  second call site to drift out of sync with the first. A single switch,
  however many cases it has, is not Shotgun Surgery risk on its own; it only
  becomes risk when it is copied.
- The switch is the dispatch mechanism inside a parser, compiler, bytecode
  interpreter, or protocol decoder operating over a syntax or wire format
  that is itself fixed and versioned. These systems are built around a
  single canonical switch, or an equivalent jump table, on purpose, because
  a table lookup or a switch compiles to something close to an indexed jump,
  and the alternative, a class per token kind with a virtual dispatch per
  token, would add both an allocation and an indirection to a hot loop that
  runs once per character or per byte.
- The behaviour per case is a pure, side-effect-free constant or a one line
  expression, and the whole switch fits in the width of a screen. Replacing
  a five line lookup table's worth of logic with five classes trades a
  smaller problem, a switch nobody has ever mis-synced because it never
  changes, for a larger one, five new files to open, five new places a
  reader has to visit to answer one question.
- The language's own idiom for the job is a switch, and fighting the idiom
  costs more than it returns. Go's `type switch` over an interface's dynamic
  type, used to distinguish concrete implementations for the purpose of one
  local operation such as JSON encoding, is Go's normal way to do this, not
  a smell, precisely because Go has no inheritance-based polymorphism to
  refactor toward; the honest alternative in Go is closer to the Visitor
  pattern or an interface method, which is itself judged on the same
  criteria above.
- Performance in a measured hot path depends on it. A switch that the
  compiler turns into a jump table is, in the languages and runtimes where
  that optimisation applies, faster than a virtual call through an interface
  or vtable, because it avoids an indirect branch through memory the branch
  predictor has less history on. This is a real force but a narrow one. it
  only applies once profiling has shown the dispatch itself, not the work
  inside each case, is the bottleneck.

## 5. Structure

The smell has one shape and the fix has several, described together here so
the relationship between what is wrong and what replaces it is visible in
one place rather than split across two dimensions.

- **The smell.** A discriminant value, `kind` in the examples below, lives
  on a shared data shape, a class with a type tag, a tagged union, or a
  plain string. One or more independent functions each open with a switch
  over that same discriminant, and the list of case labels is duplicated,
  by hand, across every one of those functions.
- **Fix A, Replace Conditional with Polymorphism.** The discriminant and its
  per-variant data are absorbed into a small class hierarchy or a set of
  types implementing a shared interface. Each switch collapses into one
  method per behaviour on that interface, and each case body becomes the
  matching subclass's implementation of that method. Call sites that used to
  switch now call the interface method and let dynamic dispatch pick the
  implementation.
- **Fix B, Replace Type Code with Subclasses, State, or Strategy.** Closest
  to Fix A but framed from the data side rather than the behaviour side. the
  `kind` field itself is eliminated in favour of the object's own runtime
  type, or, when the variant can change during the object's lifetime, in
  favour of a held reference to a small strategy or state object that can be
  swapped out. This is the correct framing when the variant is not fixed at
  construction time, a state machine transitioning between named states
  being the canonical case, see dimension 13, the GoF State pattern.
- **Fix C, a dispatch table.** A map from the discriminant to a function or
  an object. When the per-variant behaviour is genuinely stateless and does
  not need its own fields, a plain associative structure, keyed by the
  discriminant and holding either a function reference or a small handler
  object, replaces the switch with a single lookup plus a call. This keeps
  the one-function-one-job shape of the original switch's case bodies while
  making the list of known variants a single collection literal rather than
  a set of `case` keywords repeated per function.
- **Fix D, exhaustiveness checked switch, no structural change.** In a
  language that offers it, the switch itself is kept, but the
  discriminant's type is changed to something the compiler can prove is
  fully covered, for example a sealed class hierarchy in Java, a
  discriminated union in TypeScript checked with the `never` idiom, or an
  enum matched exhaustively in Rust or Swift. This does not remove
  duplication across call sites, but it removes the silent-gap failure
  mode, converting a forgotten case from a runtime bug into a compile error
  at every one of those call sites independently.

## 6. ASCII structure diagram

```
BEFORE, the smell
--------------------------------------------------------------

  +------------------+        +------------------+
  |  areaOf(shape)    |        | perimeterOf(shape)|
  +------------------+        +------------------+
  | switch shape.kind |        | switch shape.kind |
  |   case circle:    |        |   case circle:    |
  |   case square:    |        |   case square:    |
  |   case triangle:  |        |   case triangle:  |
  +------------------+        +------------------+
           ^                            ^
           |    duplicated case list    |
           +-------------+--------------+
                          |
                 +-----------------+
                 |  Shape (data)   |
                 |  kind: string   |
                 |  radius, side.. |
                 +-----------------+

AFTER, Replace Conditional with Polymorphism
--------------------------------------------------------------

                 +-------------------+
                 |  <<interface>>    |
                 |      Shape        |
                 |  area(): number   |
                 |  perimeter(): num |
                 +-------------------+
                    ^      ^      ^
                    |      |      |
        +-----------+  +---+---+  +-----------+
        |  Circle   |  |Square |  | Triangle  |
        | radius    |  | side  |  | base,height|
        | area()    |  | area()|  | area()    |
        | perimeter()| |perim()|  | perimeter()|
        +-----------+  +-------+  +-----------+

Callers now hold a Shape and call shape.area(), never a switch.
```

## 7. Dynamics

```
BEFORE, at each call site, the same shape of runtime path repeats
--------------------------------------------------------------

  caller -> areaOf(shape)
              | read shape.kind
              | compare against literal "circle"    (miss)
              | compare against literal "square"    (miss)
              | compare against literal "triangle"  (hit)
              | execute triangle's area formula inline
              v
            return number

  caller -> perimeterOf(shape)
              | read shape.kind                     <- same field, re-read
              | compare against literal "circle"    (miss)
              | compare against literal "square"    (miss)
              | compare against literal "triangle"  (hit) <- same 3 labels
              | execute triangle's perimeter formula inline
              v
            return string

  A new shape kind means editing BOTH linear paths above, by hand, with no
  link between them the compiler or runtime can check.

AFTER, dynamic dispatch does the branching once, at the call boundary
--------------------------------------------------------------

  caller -> shape.area()
              | runtime looks up shape's concrete vtable / method table
              | one indirect jump straight to Triangle.area()
              v
            return number

  caller -> shape.perimeter()
              | same lookup, same object, different method slot
              v
            return string

  A new shape kind means writing one new class that implements Shape.
  Every existing caller compiles and works against it unchanged, because
  every caller only ever asked for the Shape's area, never which kind.
```

## 8. Implementation variants

- **Plain switch, no exhaustiveness checking (pre-2020 Java, Go's classic
  `switch`, JavaScript, PHP).** The default shape. A missing `default`
  either silently does nothing, falling through the whole statement, or, if
  the author remembered to add one, throws or logs at runtime the first
  time a new variant reaches it in production, not at build time.
- **Pattern matching switch over sealed types (Java 21 onward).** The
  selector's static type is declared `sealed` with an explicit `permits`
  list, and a switch expression whose case labels are patterns rather than
  constants is checked by the compiler for coverage of every permitted
  subtype; a switch that omits a permitted subtype and supplies no default
  fails to compile, confirmed against the official language documentation,
  which further notes that if a sealed hierarchy gains a new permitted type
  after a switch was compiled against the old hierarchy, and the code is
  run without recompiling that switch, the JVM throws `MatchException` at
  runtime rather than silently doing nothing, source
  https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch-expressions-and-statements.html,
  verified 2026-08-02.
- **Discriminated union with a `never`-typed exhaustiveness guard
  (TypeScript).** The variants are modelled as a tagged union type, and the
  switch's `default` branch assigns the narrowed remaining value to a
  variable declared `never`. Because `never` accepts no value, the compiler
  raises an error at that assignment the moment a new union member is added
  and left unhandled, turning a runtime gap into a build failure at every
  switch that uses the idiom, confirmed against the official TypeScript
  Handbook's narrowing chapter, source
  https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
  2026-08-02.
- **Exhaustive `match` over an enum (Rust, and the closely related pattern
  in Swift and OCaml).** The compiler statically rejects a `match` that
  does not cover every variant of the matched enum, reporting error `E0004`
  ("non-exhaustive patterns") at compile time rather than at run time,
  confirmed against the official Rust Book's chapter on `match`, source
  https://doc.rust-lang.org/book/ch06-02-match.html, verified 2026-08-02.
  This is the strongest form available among the languages surveyed here,
  because there is no way to opt out of the check short of an explicit
  wildcard arm that the author had to write on purpose.
- **`switch (action.type)` as the idiomatic Redux reducer body
  (JavaScript/TypeScript).** Redux's own documentation presents the switch
  directly as the standard shape for a reducer, stating plainly that
  repeated `if`/`else` chains "quickly grow tiresome, so it's very common to
  use `switch` statements instead", and pairs every example with an
  explicit `default: return state` case to guarantee an unrecognised action
  is a no-op rather than an error, source
  https://redux.js.org/usage/structuring-reducers/basic-reducer-structure,
  verified 2026-08-02. This is Fix D's approach of keeping the switch while
  making the failure mode safe, adopted as the standard idiom across the
  whole Redux user base, and it is a legitimate choice precisely because a
  reducer's default case, returning the unchanged state, is a genuinely
  safe default in a way that a shape's area is not.
- **A dispatch table replacing the switch entirely.** In languages that
  treat functions as values, a plain object, `Map`, or dictionary literal
  keyed by the discriminant, mapping each key to a handler function, does
  the same job as a switch with two structural differences. adding a
  variant is one new entry in one literal rather than one new `case` label
  per function, and the set of known keys can be inspected and iterated at
  runtime (`Object.keys(table)`), which a switch's case list cannot be
  without parsing source.
- **Go's `type switch`.** Go has no class inheritance, so the natural
  refactor target for the smell, a shared interface with per-type methods,
  is already how idiomatic Go solves the same problem; a `type switch` is
  reserved for the smaller number of call sites, most often serialisation,
  formatting, and error unwrapping, where the code genuinely needs to ask
  which concrete type this is rather than calling that type's own method.

## 9. Known production uses

Named systems, each with a source, that either exhibit the switch-on-type
idiom directly or exist specifically to manage its risks.

- **Redux reducers**, in the framework's own documentation and, by
  extension, in every application built on Redux or Redux Toolkit, use
  `switch (action.type)` as the documented, standard reducer shape, source
  https://redux.js.org/usage/structuring-reducers/basic-reducer-structure,
  verified 2026-08-02. Redux's own guidance is explicit that the `default`
  branch exists specifically to keep the reducer safe when it receives an
  action type it does not recognise, which is this entry's Fix D applied at
  large scale rather than removed.
- **ESLint**, one of the most widely deployed static analysis tools in the
  JavaScript and TypeScript world, ships two core rules dedicated to
  the two most common ways a switch statement misbehaves. `default-case`
  requires every switch to declare a `default` (or an explicit
  `// no default` comment acknowledging the omission was intentional),
  source https://eslint.org/docs/latest/rules/default-case, verified
  2026-08-02, and `no-fallthrough` flags a `case` that reaches the next
  `case` without an explicit `break`, `return`, `throw`, or fallthrough
  comment, source https://eslint.org/docs/latest/rules/no-fallthrough,
  verified 2026-08-02. The existence of two dedicated, independently
  maintained lint rules for one language construct is direct evidence that
  the failure modes named in dimension 11 are common enough in real code
  to justify mechanical enforcement.
- **The OpenJDK language platform itself, from Java 21 onward**, extended
  `switch` with pattern matching specifically so that a switch dispatching
  on the runtime type of a sealed hierarchy can be proven exhaustive by the
  compiler instead of relying on a human to keep the case list in sync,
  source
  https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch-expressions-and-statements.html,
  verified 2026-08-02. A general-purpose language investing multiple
  language enhancements into making one control-flow construct provably
  complete is itself evidence, at the scale of the entire Java user base,
  that a missing case going unnoticed was a real, recurring cost worth
  solving at the language level rather than leaving to code review.
- **The TypeScript compiler's own exhaustiveness idiom**, the `never`-typed
  default branch documented in the official Handbook, is the pattern
  reproduced throughout TypeScript code in the wild, including inside large
  open-source TypeScript codebases that model domain concepts as
  discriminated unions, to give a switch the same compile-time safety Fix D
  describes without changing which language feature is used, source
  https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
  2026-08-02.

## 10. Consequences

Positive, describing what is gained once the smell is fixed, or, where
noted, what is gained by keeping the switch and applying Fix D instead of a
structural rewrite.

- A new variant is added in one place, a new subclass, a new dispatch-table
  entry, or a new enum member plus its case arms, rather than N edits spread
  across N call sites.
- Where the target language supports it, an omitted case becomes a build
  failure instead of a silent no-op or an unhandled runtime exception,
  regardless of which fix, structural or Fix D, is chosen, as long as the
  discriminant's type is one the compiler can reason about exhaustively.
- Downstream code that does not own the original switch can add a new
  variant by implementing an interface, without editing source it may not
  have access to. This is the specific benefit structural fixes A, B, and C
  add over Fix D, which does not open the variant set to outsiders at all.
- Reading everything a single variant does becomes possible by opening one
  file once the fix is structural, rather than grepping every function for
  one string literal.

Negative, the costs paid for those gains.

- The variant list is no longer visible in one place. A reader who wants to
  survey every kind of shape and what each one does for area must now open
  every subclass file, whereas the original switch, however duplicated,
  showed the whole list on one screen per function.
- Class or file count grows by one per variant, per structural fix chosen.
  A domain with forty variants and three behaviours per variant produces
  forty new small classes, which is a real navigation cost in an IDE with
  no fuzzy jump-to-implementation support.
- Adding a new behaviour, a new virtual method on the shared interface, now
  requires touching every existing variant class to implement it, which is
  the mirror image of the problem being solved. polymorphism trades "adding
  a variant is expensive" for "adding a behaviour is expensive". This
  trade-off is the classic expression problem, and no fix in this entry
  escapes it; a language with proper sum types and exhaustive matching,
  Fix D done thoroughly, is the shape that makes adding a behaviour cheap
  again at the cost of reintroducing a single dispatch point per behaviour,
  which is, in its shape, a switch statement written in a different syntax.
- A dispatch table, Fix C, hides its contents from static analysis in
  languages without first-class function types checked at the type level;
  a typo'd key silently never matches instead of failing to compile, which
  can be a worse failure mode than the switch it replaced in a language
  that could have exhaustiveness-checked the original switch instead.

## 11. Failure modes and misuse

Each item names an observable symptom first, then its cause, then its fix.

- A new payment method works everywhere except one screen, where it
  silently falls back to displaying nothing or throws a generic error. The
  cause is that one of several duplicated switches over the payment kind
  discriminant was never updated when the new payment method was added, and
  it has no `default` case that fails loudly, so the omission produced no
  warning anywhere, not in the build, not in code review, not in a log
  line, until a real user hit it. The fix is to consolidate the duplicated
  switches into a single dispatch point, Fix A, B, or C, or, if the switch
  must stay for now, to add an exhaustiveness-checked discriminant type,
  Fix D, so every remaining copy of the switch fails to compile the moment
  a new variant appears, rather than failing to compile only the one copy
  the author remembered to update.
- A bug report says the discount applies twice for gift cards, and the
  discount code, when read, has one `case "giftcard":` block with no
  `break`, `return`, or `throw` before the next `case`. The cause is
  fallthrough, the switch's default per-case behaviour in every C-family
  language, executing the gift card branch and then continuing straight
  into the next case's logic as well, because the author forgot the
  terminating statement. The fix is to add an explicit terminator to every
  case arm, and to adopt a linter rule such as ESLint's `no-fallthrough`
  (see dimension 9) so a missing terminator fails the build instead of
  shipping, or to move to a language and switch-expression form, Java's
  arrow-form switch expressions or Rust's `match`, where fallthrough is not
  the default behaviour and must be requested explicitly.
- Two engineers, working on different features in the same sprint, both add
  handling for a brand new wire-transfer payment method to the same switch
  in the same file, in two separate branches, and the merge conflicts every
  time on the same three lines. The cause is that the switch has become a
  single, heavily contended file that every new variant must touch,
  concentrating unrelated work into one location that would not conflict at
  all if each variant lived in its own file, a symptom of the Divergent
  Change smell playing out at the level of a single construct rather than a
  single class. The fix is to move to a structural fix, A, B, or C, so a
  new variant is a new file, which by construction cannot conflict with
  another new file added in a different branch.
- A code reviewer approves a pull request that adds a `default` case
  returning a hardcoded fallback value, and three months later a support
  ticket traces a wrong invoice total back to that exact fallback silently
  firing for a legitimate, but newly added, invoice type. The cause is that
  a `default` case that returns a plausible-looking value instead of
  failing loudly converts a missing-case bug from something visible, a
  crash or a build failure, into something invisible, a wrong number that
  looks like a right number, which is exactly the danger `default-case` and
  its cousin rules exist to catch at review time, but only when the
  default is required to be explicit about doing nothing, not when it is
  allowed to quietly compute a guess. The fix is to reserve `default` for
  cases that are genuinely, provably safe to no-op, Redux's returning the
  state unchanged is the textbook safe default, and for everything else to
  throw, log, or, in a language with exhaustiveness checking, remove the
  `default` entirely so the compiler proves nothing was missed.
- A profiler shows a hot loop spending measurable time in a chain of
  virtual calls, and the engineer who refactored a five-case,
  once-called-per-frame switch into five classes six months earlier is now
  asked to explain a frame rate regression. The cause is that Replace
  Conditional with Polymorphism was applied to a call site that failed
  dimension 4's performance criterion, a switch that a compiler could turn
  into a jump table was replaced with an indirect call through a vtable
  inside a loop that runs thousands of times per second, and the
  indirection cost more than the switch ever did. The fix is to revert the
  hot path specifically to a switch or a dispatch table, keeping the
  polymorphic fix everywhere else in the codebase where the loop does not
  run at that frequency, and to profile before applying either fix in a
  genuinely hot loop rather than after.

## 12. Trade-off matrix

Compared against the two most common named alternatives for eliminating
type-conditional dispatch, plus the option of keeping the switch and only
adding exhaustiveness checking.

| Force | Keep the switch, add exhaustiveness (Fix D) | Replace Conditional with Polymorphism (Fix A) | Dispatch table / Strategy map (Fix C) | GoF State pattern (see dimension 13) |
|---|---|---|---|---|
| Fixes duplication across call sites | No, each copy still exists, but each copy independently fails to compile on a gap | Yes, one interface, one implementation per variant | Partially, one table per behaviour, tables can still drift from each other | Yes, for the specific case of one object whose behaviour changes with an internal state it owns |
| Opens variant set to code outside the owning module | No | Yes, a new class implementing the interface | Depends on language, only if the table itself is exposed and mutable | Yes, a new state class |
| Adds a build-time safety net for missing cases | Yes, this is the entire point of the fix | Yes, if the language also checks interface implementation completeness, which most do not do automatically | No, a missing table entry is a runtime lookup miss unless the table's keys are themselves an exhaustively typed enum | Same as polymorphism, inherits its guarantees |
| New file or class count | Zero, no structural change | One new type per variant | Zero to one, depending on whether handlers are inline functions or objects | One new state class per state, plus explicit transition wiring |
| Cost of adding a new cross-cutting behaviour later | Low, one new switch, still duplicated across call sites as before | High, every existing variant class must implement the new method, the expression problem | Low to moderate, one new table | High, same as polymorphism |
| Fits a hot, frequently executed loop | Best fit, compiles to a jump table in most languages that support it | Worst fit, one indirect call per invocation | Comparable to the switch, one hash or array lookup per invocation | Comparable to polymorphism |
| Requires the variant to be a runtime type at all | No, works on any discriminant, string, int, or enum | Yes, the variant must become a class or a value the type system can dispatch on | No, works on any hashable key | Yes, and additionally requires the containing object to hold a swappable reference |

## 13. Related and incompatible patterns

- **Factory Method.** A closely related and easily confused sibling. Factory
  Method (see the entry in family 01-design-patterns-gof) solves which concrete type to
  construct, using subclass-level dispatch to pick a product. Switch
  Statements as a smell most often appears alongside a Simple Factory, an
  unrelated idiom, a plain function with a switch or a map that constructs
  and returns one of several concrete types based on a discriminant; that
  entry's own dimension 1 draws this exact line, and the fix for a Simple
  Factory that has grown unwieldy is frequently the same Replace Type Code
  with Subclasses refactoring described here.
- **GoF State pattern (Design Patterns, Addison-Wesley 1994/1995).** The
  canonical named alternative when the discriminant is not fixed at
  construction but changes over the object's own lifetime. Wikipedia's
  summary of the pattern, itself citing the GoF book, describes the
  motivation directly, explaining that implementing state-dependent
  behaviour with conditional logic inside a single class "is inflexible
  because it commits the class to a particular behavior and makes it
  impossible to add a new state or change the behavior of an existing state
  later, independently from the class, without changing the class", and
  frames the pattern as the fix that lets the object's behaviour change by
  swapping which state object it delegates to, source
  https://en.wikipedia.org/wiki/State_pattern, verified 2026-08-02. The
  distinction from Fix A above is narrow but real. Replace Conditional with
  Polymorphism assumes the variant is fixed once an object is constructed,
  a Circle is always a Circle, while State assumes the variant can change
  while the object's identity stays the same, an Order transitions from
  Pending to Shipped without becoming a new object.
- **GoF Strategy pattern.** Related the same way State is, but for
  behaviour selected once, from the outside, rather than transitioning
  internally. A dispatch table of strategy objects, Fix C when the table's
  values are objects rather than bare functions, is Strategy applied at the
  scale of a whole switch's worth of cases at once, rather than one
  strategy chosen per call.
- **Visitor pattern.** The named alternative for the specific case where the
  operations, not the variants, are what changes over time, and the variant
  set is genuinely closed, an AST node hierarchy defined once by a compiler
  author, for example. Visitor deliberately keeps a form of the switch's
  centralised, per-operation view, each visit method lists every node type
  it handles, while still using dynamic dispatch to route to the right
  visit method, and is the honest choice when dimension 4's closed variant
  set case applies but the codebase still wants compiler help.
- **Alternative Classes with Different Interfaces (sibling entry, this
  family).** A frequent downstream consequence of applying Fix A carelessly.
  once a switch's case bodies are split into separate classes, if those
  classes are written independently rather than against a shared interface
  from the start, they can drift into classes that do equivalent jobs with
  incompatible method names, reintroducing a smell at one level of
  indirection higher than the one that was fixed.
- **Primitive Obsession (sibling entry, this family).** Frequently the root
  cause underneath a Switch Statements instance. the discriminant is a bare
  string or integer rather than a proper type, which is precisely what
  removes any chance of the compiler checking the switch's coverage. Fixing
  Primitive Obsession first, by turning the discriminant into an enum, a
  sealed hierarchy, or a discriminated union, is a prerequisite for Fix D
  and makes Fix A mechanically easier because the variant list already
  exists as a type the refactoring tool or the compiler can enumerate.
- **Incompatible with.** none. Switch Statements as a smell is not mutually
  exclusive with any other named pattern in this catalogue; every one of
  the fixes above composes with the rest of a codebase's design rather than
  ruling anything else out.

## 14. Refactoring path in and out

### How the smell usually arrives

A single function needs variant-specific behaviour for the first time; a
switch is written; this is not yet a problem. The smell begins the moment a
second, independent function needs the same discriminant and the fastest
available option, copying the existing case list, is taken instead of
extracting a shared abstraction. Recognising this exact moment, the second
copy of the case list, is the cheapest point at which to intervene, before a
third and fourth copy make the eventual fix proportionally more expensive.

### Refactoring out toward Replace Conditional with Polymorphism (Fix A)

1. Identify every function that switches on the same discriminant. Grep for
   the discriminant field's name or the string literals used as case
   labels; in a language with exhaustiveness checking already available,
   temporarily changing the discriminant's type is a fast way to make the
   compiler list every affected location.
2. Introduce an interface, or, in a language without them, a common
   superclass, whose methods correspond, one for one, to the distinct
   pieces of behaviour currently found across the switches, one method per
   switch that was found in step 1.
3. For each variant, create a class implementing that interface, moving the
   corresponding case body from every switch into the matching method on
   that class. Move, do not copy; each case body has exactly one new home.
4. Replace the construction of the old data-plus-discriminant shape with
   construction of the matching new class, at the smallest number of
   creation points possible, ideally one, guarded by whatever Fix A leaves
   in its own place. ordinarily nothing, because a Simple Factory or a
   small map from discriminant to constructor now stands in the single
   place a type code once had to be interpreted repeatedly.
5. Replace every call site that used to switch with a direct call to the
   interface method, and delete the now empty switches.
6. Delete the discriminant field once nothing reads it, confirming with the
   same search used in step 1.

### Refactoring out toward exhaustiveness only, no structural change (Fix D)

1. Confirm dimension 4's non-applicability criteria genuinely apply; this
   path is a deliberate choice to keep the switch, not a shortcut around
   doing the harder refactor.
2. Change the discriminant's declared type from a bare primitive to
   whatever the language's exhaustiveness mechanism requires. a sealed
   interface with a fixed `permits` list in Java, a discriminated union in
   TypeScript, or an enum in Rust or Swift.
3. Remove any `default` case that silently swallows unmatched values,
   replacing it, where the language requires one syntactically, with an
   explicit failure, a thrown exception or, in TypeScript, the `never`
   assignment idiom described in dimension 8, so the compiler, not a
   `default`, is what proves coverage.
4. Re-run the build. Every switch over the changed discriminant that omits
   a variant now fails to compile, which is the mechanism this fix trades
   for the structural change Fix A would have made.

### Refactoring back in, when a fix has been over-applied

If profiling shows Fix A's dynamic dispatch is the measured bottleneck in a
genuinely hot loop (see dimension 11's last failure mode), or if the
polymorphic classes have accumulated so many cross-cutting methods that
every new behaviour requires touching every class (the expression-problem
cost named in dimension 10), reversing toward a switch or a dispatch table
for that specific call site is a legitimate, targeted move; it does not
require reverting the fix everywhere the original smell was found, only at
the site where the trade turned out to favour the switch after all.

## 15. Testing and verification

What becomes easier once the smell is fixed with Fix A or B. each variant's
behaviour lives in its own class, so a unit test for how a Circle computes
its area instantiates exactly one Circle and calls one method, with no need
to construct a discriminant value correctly or to worry that the test
happens to exercise the `default` branch by accident. Contract tests are
also easier to write and to keep honest. a single test suite that runs
against the shared interface, parameterised over every known
implementation, both documents the interface's contract and, because it
iterates the concrete list of implementing classes, can be made to fail
loudly the moment a new implementation is added without matching test
coverage, giving back some of the single-list-of-variants visibility that
Fix A costs elsewhere (see dimension 10).

What becomes easier once the smell is fixed with Fix D, exhaustiveness
checking without structural change. the compiler itself becomes a test that
runs on every build rather than only when the specific unit test for that
switch happens to be executed. This is strictly cheaper to maintain than a
hand-written completeness test, at the cost of applying only to the one
switch that was given the exhaustiveness-checked type, not to any other
copy of the same case list elsewhere in the codebase, which is exactly why
dimension 10's consequences section lists this as Fix D's limitation.

What becomes harder either way. testing that the dispatch mechanism itself
is complete, when there is no compiler exhaustiveness available, requires
an explicit test that enumerates every known discriminant value and asserts
the switch, or the dispatch table, handles each one without falling into
the `default` branch. Writing this test once, and keeping the enumerated
list in the test itself synchronised with the real list of discriminant
values, is the manual substitute for compiler-checked exhaustiveness in a
language, such as plain JavaScript or pre-2021 Java, that offers none.

## 16. Observability signals

A switch that reaches its `default` case in production, when the codebase
believed the variant set was fixed, is the single most important signal to
make visible. Log the unmatched discriminant value at the point the
`default` fires, at a severity that pages someone rather than one that
scrolls silently past in a debug log, because a `default` reached in
production is direct evidence that a variant was added somewhere upstream,
a new payment method configured in an admin panel, a new message type
published onto a queue, without every consuming switch being updated to
match, which is dimension 11's first named failure mode happening in real
time.

A healthy instance of a switch that owns Fix D's exhaustiveness guarantee
produces no such signal at all, because the compiler refuses
to build code that could reach an unhandled case, there is no `default`
branch left to instrument, and the corresponding observability signal is
absent by construction, which is itself something to record on a dashboard or in a
migration checklist as an explicit statement that no unmatched-variant
alerts are configured for this switch because none are possible, rather
than a silent gap in monitoring coverage.

Where the fix was structural, Fix A, B, or C, the equivalent healthy signal
is a metric on how many concrete implementations of the shared interface
exist, checked against how many are exercised by the contract test
described in dimension 15; a mismatch between the count of classes
registered and the count of classes covered by the shared test suite
surfaces the same missing-coverage risk the switch's `default` branch used
to surface at runtime, but earlier, at CI time.

## 17. Security and privacy implications

Largely a matter of what the `default` branch does rather than something
inherent to the switch construct itself. A `default` case that fails open,
allowing an unrecognised discriminant value through to a permissive code
path rather than rejecting it, converts an incomplete case list from a
correctness bug into an access-control gap. an authorization check written
as a switch over role names, with a `default` that grants access rather
than denying it, will silently admit any role string the check's author did
not anticipate, including a typo or a role introduced by a later, unrelated
change to the identity system. The general security guidance that follows
directly from this entry's own reasoning is to prefer a `default` that
denies or throws over one that permits, exactly as dimension 11's fourth
failure mode recommends for correctness reasons, and this recommendation is
stronger, not weaker, when the switch in question gates access to data or
actions rather than computing a display value. Beyond the `default`
branch's own behaviour, the smell carries no privacy implication of its
own; it neither handles nor exposes data differently from any other
control-flow construct.

## 18. References

- Martin Fowler, with Kent Beck, John Brant, William Opdyke, Don Roberts,
  *Refactoring, Improving the Design of Existing Code*, Addison-Wesley,
  1999, Chapter 3, "Bad Smells in Code", the original catalogue entry for
  Switch Statements and its companion refactorings.
- Martin Fowler's refactoring catalog, "Replace Conditional with
  Polymorphism", https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html,
  verified 2026-08-02.
- Martin Fowler's refactoring catalog index, listing "Replace Type Code with
  Subclasses" and "Remove Flag Argument" alongside the polymorphism
  refactoring, https://refactoring.com/catalog/, verified 2026-08-02.
- Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
  Patterns, Elements of Reusable Object-Oriented Software*, Addison-Wesley,
  1994/1995, the State and Strategy pattern chapters, cited here via
  Wikipedia's summary of the State pattern's motivation,
  https://en.wikipedia.org/wiki/State_pattern, verified 2026-08-02.
- Oracle, "Pattern Matching for switch Expressions and Statements", Java SE
  21 language documentation, describing exhaustiveness checking over sealed
  types and the runtime `MatchException`,
  https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch-expressions-and-statements.html,
  verified 2026-08-02.
- TypeScript documentation, "Narrowing", the official Handbook chapter
  describing the `never`-typed exhaustiveness check idiom,
  https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
  2026-08-02.
- The Rust Programming Language, the official Rust Book, Chapter 6.2, "The
  match Control Flow Construct", describing the compiler's exhaustive match
  requirement and error `E0004`,
  https://doc.rust-lang.org/book/ch06-02-match.html, verified 2026-08-02.
- Redux documentation, "Basic Reducer Structure", describing the switch
  statement as the standard reducer shape,
  https://redux.js.org/usage/structuring-reducers/basic-reducer-structure,
  verified 2026-08-02.
- ESLint documentation, rule `default-case`,
  https://eslint.org/docs/latest/rules/default-case, verified 2026-08-02.
- ESLint documentation, rule `no-fallthrough`,
  https://eslint.org/docs/latest/rules/no-fallthrough, verified 2026-08-02.
- Wikipedia, "Cyclomatic complexity", summarising Thomas J. McCabe's 1976
  original decision-point metric, consulted to confirm the article makes
  no explicit claim about switch case labels specifically; this entry's
  dimension 3 discussion of the metric's extension to switch statements is
  accordingly presented as engineering judgement rather than a sourced
  claim from that article,
  https://en.wikipedia.org/wiki/Cyclomatic_complexity, verified 2026-08-02.

## Code examples

Three languages, each compiled and run to produce the printed output shown
in a comment at the end of the smell version. The examples model the same
domain used in dimensions 6 and 7. a `Shape` with an `area` and a
`perimeterHint`, first as the smell, then as Fix A.

### TypeScript, the smell

```typescript
type ShapeKind = "circle" | "square" | "triangle";
interface Shape {
  kind: ShapeKind;
  radius?: number;
  side?: number;
  base?: number;
  height?: number;
}

function area(s: Shape): number {
  switch (s.kind) {
    case "circle":
      return Math.PI * (s.radius ?? 0) ** 2;
    case "square":
      return (s.side ?? 0) ** 2;
    case "triangle":
      return 0.5 * (s.base ?? 0) * (s.height ?? 0);
  }
}

// A second, independent function repeats the same three case labels.
function perimeterHint(s: Shape): string {
  switch (s.kind) {
    case "circle":
      return "2*pi*r";
    case "square":
      return "4*s";
    case "triangle":
      return "a+b+c";
  }
}

const c: Shape = { kind: "circle", radius: 2 };
console.log(area(c).toFixed(2), perimeterHint(c));
// compiled with tsc --strict, ran with node, prints "12.57 2*pi*r"
```

### TypeScript, Fix A applied

```typescript
interface Shape {
  area(): number;
  perimeterHint(): string;
}

class Circle implements Shape {
  constructor(private radius: number) {}
  area(): number { return Math.PI * this.radius ** 2; }
  perimeterHint(): string { return "2*pi*r"; }
}

class Square implements Shape {
  constructor(private side: number) {}
  area(): number { return this.side ** 2; }
  perimeterHint(): string { return "4*s"; }
}

class Triangle implements Shape {
  constructor(private base: number, private height: number) {}
  area(): number { return 0.5 * this.base * this.height; }
  perimeterHint(): string { return "a+b+c"; }
}

const shapes: Shape[] = [new Circle(2), new Square(3), new Triangle(4, 5)];
for (const s of shapes) {
  console.log(s.area().toFixed(2), s.perimeterHint());
}
// compiled with tsc --strict, ran with node
// prints, in order.
// 12.57 2*pi*r
// 9.00 4*s
// 10.00 a+b+c
```

### Go, the smell (and why Go's fix looks slightly different, see dimension 8)

```go
package main

import (
	"fmt"
	"math"
)

type Shape struct {
	Kind                       string
	Radius, Side, Base, Height float64
}

func area(s Shape) float64 {
	switch s.Kind {
	case "circle":
		return math.Pi * s.Radius * s.Radius
	case "square":
		return s.Side * s.Side
	case "triangle":
		return 0.5 * s.Base * s.Height
	default:
		panic("unknown shape kind, " + s.Kind)
	}
}

func main() {
	c := Shape{Kind: "circle", Radius: 2}
	fmt.Printf("%.2f\n", area(c))
}
// ran with go run, prints "12.57"
```

### Go, Fix A applied, an interface, Go's own idiom for this

```go
package main

import (
	"fmt"
	"math"
)

type Shape interface {
	Area() float64
}

type Circle struct{ Radius float64 }

func (c Circle) Area() float64 { return math.Pi * c.Radius * c.Radius }

type Square struct{ Side float64 }

func (s Square) Area() float64 { return s.Side * s.Side }

func main() {
	shapes := []Shape{Circle{Radius: 2}, Square{Side: 3}}
	for _, s := range shapes {
		fmt.Printf("%.2f\n", s.Area())
	}
}
// ran with go run, prints "12.57" then "9.00"
```

### Rust, the smell, already exhaustiveness checked, see dimension 8

```rust
enum Shape {
    Circle { radius: f64 },
    Square { side: f64 },
    Triangle { base: f64, height: f64 },
}

fn area(s: &Shape) -> f64 {
    match s {
        Shape::Circle { radius } => std::f64::consts::PI * radius * radius,
        Shape::Square { side } => side * side,
        Shape::Triangle { base, height } => 0.5 * base * height,
    }
}

fn main() {
    let c = Shape::Circle { radius: 2.0 };
    println!("{:.2}", area(&c));
}
// compiled with rustc -O, prints "12.57"
// note. the same match, with a new variant added to the enum and left out
// of this match, fails to compile with error E0004 rather than running,
// which is Fix D already built into the language for this case.
```

### Rust, Fix A applied, a trait, when per-variant state genuinely differs

```rust
trait Shape {
    fn area(&self) -> f64;
}

struct Circle { radius: f64 }
impl Shape for Circle {
    fn area(&self) -> f64 { std::f64::consts::PI * self.radius * self.radius }
}

struct Square { side: f64 }
impl Shape for Square {
    fn area(&self) -> f64 { self.side * self.side }
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle { radius: 2.0 }),
        Box::new(Square { side: 3.0 }),
    ];
    for s in &shapes {
        println!("{:.2}", s.area());
    }
}
// compiled with rustc -O, prints "12.57" then "9.00"
```

All six samples above were compiled and executed on the authoring machine,
`tsc` plus `node` for TypeScript, `go run` for Go, `rustc -O` for Rust, and
produced exactly the output shown in each trailing comment. A Java sample
using the pattern-matching switch documented in dimension 8 was drafted
against the cited language documentation but could not be executed on the
authoring machine because no Java runtime was installed there; the Java
behaviour described in this entry is drawn entirely from the cited Oracle
documentation, not from a local run, and that limitation is stated here
rather than left implicit.
