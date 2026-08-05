---
name: Long Parameter List
slug: long-parameter-list
family: 02-code-smells
category: Code Smell
aliases: [Parameter Bloat, Argument List Overload]
first_described: "Fowler, Beck 1999, Refactoring, 1st edition, chapter 3"
maturity: canonical
related: [introduce-parameter-object, preserve-whole-object, builder, data-clumps, feature-envy]
incompatible_with: []
verified: 2026-08-02
---

# Long Parameter List

## 1. Name, aliases, and lineage

The canonical name is Long Parameter List, and it appears under that exact
name in the smell catalog of Martin Fowler's Refactoring, first published in
1999 and co-credited to Kent Beck for the smells chapter itself. Fowler,
Refactoring. Improving the Design of Existing Code, 1st edition, chapter 3,
"Bad Smells in Code," https://martinfowler.com/books/refactoring.html,
verified 2026-08-02. The second edition (2018) keeps the same name and the
same diagnosis, now retitled to the JavaScript examples but unchanged in
substance. Some teams call it Parameter Bloat or Argument List Overload in
code review shorthand, but neither term appears in a formal catalog, they are
informal aliases only, and this entry treats Fowler's name as authoritative.

The smell itself predates its naming. Every procedural language that supports
functions has always been capable of accumulating parameters, and the
Win32 API's CreateWindowExW, standardized well before Refactoring was
published, is a twelve-parameter function that programmers have complained
about for decades without a formal name for the complaint (see dimension 9).
What Fowler and Beck did was give the accumulation a name, place it in a
catalog next to its cure, and tie the cure to specific refactorings, most
directly Introduce Parameter Object and Preserve Whole Object. Before that
naming, the standard advice was folk wisdom passed between senior engineers
rather than a documented, cross-referenced pattern with a known fix.

## 2. Problem and context

A function, method, or constructor accumulates parameters over its lifetime,
usually one at a time, usually each addition individually reasonable, until
the call site becomes difficult to read, difficult to call correctly, and
difficult to change safely. The smell is not about a fixed number. A
three-argument geometry function, `distance(x1, y1, x2, y2)`, is often
perfectly fine because the four numbers form one coherent idea, a pair of
points, and any caller who knows what a point is can supply them without
consulting documentation. A six-argument function that mixes an identifier, a
boolean flag, a nullable callback, a timeout in milliseconds, a currency code,
and an enum for retry behavior is a problem at four parameters, because
nothing about the shape tells the caller what order they belong in or which
ones can be omitted.

The context in which this smell arises is almost always incremental growth.
A function starts with two or three parameters that form a natural group. A
requirement appears that needs one more piece of information, so a parameter
is appended, because appending is the path of least resistance in every
mainstream language. It does not require touching a type definition, it does
not require a migration of existing call sites beyond adding one more
argument, and the diff is small and easy to review in isolation. Repeat this
five or six times across a function's life, at different times, by different
authors, none of whom read the whole call site before adding their own
parameter, and the function accretes into an argument list that nobody
designed. The smell is a symptom of a design that emerged rather than a
design that was chosen, and it is one of the most reliable tells in a code
review that a function has been the target of many small, uncoordinated
extensions rather than one deliberate one.

The problem sharpens in languages and codebases without named arguments or
strong static typing at the call site. A Java or C++ or Go call with eight
positional arguments of similar or identical types is a minefield. Swapping
two `int` arguments compiles cleanly and fails silently, sometimes only under
a specific input that surfaces in production. Python, TypeScript, Swift, and
C# soften this with named or keyword arguments, but even there the smell
persists in the function's own signature, its overload resolution, and its
cognitive load at the definition site, even if the call site becomes safer.

## 3. Forces

- **Cohesion versus incrementality.** A well-cohered parameter list groups
  data that belongs together. Incrementality, the everyday practice of adding
  one more piece of information a function now needs, works against cohesion
  because appending a parameter is always cheaper in the moment than
  redesigning the signature.
- **Caller ergonomics versus flexibility.** Every parameter added to a
  function extends what it can express, but it also raises the burden on
  every caller who must decide what to pass, in what order, and whether a
  default applies. A function that can do more, expressed by having more
  knobs, is often a function that is harder to use correctly.
- **Positional clarity versus positional risk.** Positional arguments are
  terse at the call site when the count is small and the meaning is obvious
  from context, for example the arguments to a two-dimensional point
  constructor. Positional arguments are dangerous at the call site when the
  count grows and several parameters share a type, because the compiler
  cannot catch a transposition of two same-typed values.
- **Encapsulation versus data hiding.** Long parameter lists often form
  because the caller is unwrapping an object it already holds and handing
  the fields across one at a time, which both breaks the encapsulation of the
  caller's object and forces the callee to reassemble meaning from
  disconnected primitives, a pattern closely tied to the Feature Envy and
  Data Clumps smells.
- **Static language rigidity versus runtime flexibility.** Statically typed
  languages without named arguments (older Java, C, Go) push a parameter-list
  problem toward either the constructor overload explosion or the Builder
  pattern, because the language has no cheaper alternative. Languages with
  keyword or named arguments (Python, Swift, Kotlin, TypeScript with object
  types, C#) can address part of the problem in-place without a redesign,
  which changes where the pain shows up but does not eliminate the smell,
  because the definition site still carries the same list.
- **Backward compatibility versus signature cleanliness.** Once a function is
  public API, removing or reordering parameters is a breaking change. This
  pressure alone explains a large share of the long parameter lists found in
  widely used libraries. Authors append rather than redesign because
  redesign breaks every existing caller, and the accretion becomes permanent.

The smell favors incrementality, backward compatibility, and short-term
caller convenience over long-term readability and correctness, the fix
favors the reverse, and the cost of the fix is almost always a one-time
redesign against an ongoing stream of small, individually cheap patches.

## 4. Applicability and non-applicability

### When this diagnosis applies

- A function's parameter count keeps growing across its git history, one or
  two parameters added per change, with no coordinated redesign.
- Several parameters at a call site share a type (multiple strings, multiple
  ints, multiple booleans), so the compiler or interpreter cannot catch a
  transposition, and a reviewer has to trace the definition to know the order.
- Some subset of the parameters are always passed together across multiple
  functions in the same subsystem, a strong signal that they belong to a
  missing type rather than to the individual function's signature (this
  overlaps directly with the Data Clumps smell).
- Call sites routinely pass `null`, `0`, `false`, `undefined`, or a sentinel
  value for several trailing parameters because most callers do not need
  them, which usually indicates the function is doing more than one job or
  the parameters represent optional configuration that belongs in its own
  structure.
- A reviewer or new team member cannot correctly call the function from
  memory or from its name alone and must open the definition every time.

### When this diagnosis does not apply

- A small, stable, semantically coherent group of parameters that reads as
  one idea at the call site, for example `Point(x, y)`, `RGB(r, g, b)`, or
  `Range(start, end)`. Wrapping these in an object purely to reduce a
  parameter count from two or three down to one, when the two or three
  already read as a unit and have not grown and are unlikely to grow, adds an
  allocation and a type without adding clarity. Fowler and Beck's own catalog
  treats "how many is too many" as a judgment call tied to whether the group
  forms a concept, not a fixed threshold, see dimension 3 above.
- A mathematical or numeric function whose parameters are genuinely
  independent and where introducing a wrapper object would only relocate the
  same list into a struct's field order with no gain in meaning, for example
  a four-coefficient polynomial evaluator, `evaluate(a, b, c, d, x)`, where
  the parameters correspond to a well-known external convention (polynomial
  coefficients) and grouping them changes nothing about how a caller reasons
  about the call.
- Language-level constructs whose parameter shape is fixed by an external
  standard, protocol, or hardware interface that the codebase does not
  control, most notably C bindings to operating system or hardware APIs
  where the parameter order is dictated by the ABI. Refactoring the caller's
  own wrapper is applicable, refactoring the underlying system call is not.
- Variadic or spread-style functions where the "many parameters" are
  genuinely homogeneous and unbounded in count, such as `Math.max(...values)`
  or a logging function's format arguments. These are not a long parameter
  list in Fowler's sense, they are a single, repeated parameter, and treating
  them as a list to be objectified misreads the smell.
- Test helper functions and fixtures where an explicit, positional argument
  list intentionally documents every value the test cares about and an
  object parameter would hide a mismatched or missing value behind a
  default. Test code sometimes deliberately privileges explicitness over
  brevity, and that is a legitimate trade-off, not a smell, provided the test
  helper stays small in scope and does not itself accrete unrelated concerns.

## 5. Structure

Long Parameter List is a smell rather than a structural pattern, so it has
no participants in the pattern-catalog sense. What it has is a recognizable
shape at two points in the code, and the refactoring that resolves it
introduces the participants below.

- **The offending function or constructor.** The unit whose signature has
  grown past what a caller can hold in working memory or express safely.
- **Call sites.** Every place that invokes the offending function, each of
  which pays the cost of the long list on every invocation.
- **The parameter object (the fix).** A new, named type introduced by the
  Introduce Parameter Object refactoring, whose fields are the subset of the
  original parameters that form a coherent group. It becomes a single
  parameter that replaces several.
- **The builder (an alternative fix for constructors).** A separate,
  mutable, fluent object described in Effective Java (Bloch, Joshua, Effective
  Java, 3rd edition, Item 2, "Consider a builder when faced with many
  constructor parameters," Addison-Wesley, 2018), whose job is to accept
  parameters incrementally through named setter-like methods and produce the
  final, validated, immutable object on `build()`.
- **The context or options object (the fix for optional/configuration
  parameters).** A plain data type, often used with default values per
  field, that groups the parameters a caller usually does not need to touch
  and lets a majority of callers omit the whole group rather than pass
  several individual sentinels.

## 6. ASCII structure diagram

```
BEFORE (the smell)

  Client
    |
    | createReservation(
    |   guestName, guestEmail, roomNumber,
    |   checkInDate, checkOutDate,
    |   numberOfGuests, breakfastIncluded,
    |   paymentMethod, discountCode
    | )
    v
  +----------------------------------+
  | createReservation(9 parameters)  |
  +----------------------------------+


AFTER (Introduce Parameter Object applied to the date pair
        and the guest details, Preserve Whole Object applied
        to the caller's existing Guest record)

  Client
    | already holds a Guest record
    |
    | createReservation(guest, stay, options)
    v
  +----------------------------------+
  | createReservation(3 parameters)  |
  +----------------------------------+
         |            |          |
         v            v          v
  +-----------+  +----------+  +-------------------+
  | Guest     |  | StayDates|  | ReservationOptions |
  |  name     |  |  checkIn |  |  breakfastIncluded |
  |  email    |  |  checkOut|  |  paymentMethod     |
  +-----------+  +----------+  |  discountCode      |
                                +-------------------+
```

```
AFTER (Builder applied to a constructor with many optional
        fields, following Effective Java Item 2)

  Client
    |
    | new Pizza.Builder(size)
    |     .addTopping(PEPPERONI)
    |     .addTopping(MUSHROOM)
    |     .build()
    v
  +----------------+        +-----------------------+
  |  Pizza.Builder |------->|  Pizza (immutable)     |
  |  (fluent,      | build()|  size, toppings, ...   |
  |   mutable)     |        +-----------------------+
  +----------------+
```

## 7. Dynamics

At runtime, the smell itself has no dynamics beyond the ordinary call and
return of a function. The interesting dynamics are in how the code evolves
over time and how the fix changes the call sequence.

Growth dynamic, before the fix.

```
t0: createReservation(guestName, guestEmail, roomNumber,
                       checkInDate, checkOutDate)
       - 5 parameters, one coherent idea per pair, still readable

t1: + numberOfGuests appended
       - 6 parameters, still tolerable

t2: + breakfastIncluded appended
       - 7 parameters, a reviewer starts needing the definition

t3: + paymentMethod appended
       - 8 parameters, two callers pass arguments in the wrong
         order and it compiles cleanly (guestEmail and
         paymentMethod are both strings)

t4: + discountCode appended, defaulting to null in 90% of calls
       - 9 parameters, most call sites now pass null as the
         last argument, a sentinel signaling optionality that
         does not belong in a required position
```

Call dynamic after Introduce Parameter Object and Preserve Whole Object.

```
Client already holds:  Guest{name, email}

1. Client constructs StayDates{checkIn, checkOut}
      (or receives it from a form-parsing step upstream)
2. Client constructs ReservationOptions{breakfastIncluded,
      paymentMethod, discountCode} with named fields and
      language-level defaults for the optional ones
3. Client calls createReservation(guest, stay, options)
4. createReservation destructures each object internally,
      exactly once, at the point where each value is used,
      rather than the caller destructuring Guest before the call
```

Call dynamic when a Builder is used instead (Effective Java Item 2 pattern),
relevant when the target type must end up immutable and partially
constructed intermediate state must never be observable.

```
1. Client calls new Pizza.Builder(requiredSize)
      - constructor enforces the parameters that have no
        sensible default
2. Client chains zero or more .addTopping(...) or
      .setCrust(...) calls, each returning the same builder
3. Client calls .build()
      - build() validates the accumulated state as a whole,
        for example rejecting an empty topping list combined
        with the "supreme" size flag, a cross-field check that
        a plain constructor could only express with more
        parameters or with post-construction mutation
4. build() returns an immutable Pizza; the builder itself is
      discarded and never escapes to code that only needed the
      finished object
```

## 8. Implementation variants

- **Introduce Parameter Object.** The dominant fix when a subset of the
  parameters recur together across more than one function. Extract them into
  a small, named, typically immutable type, then replace the group with a
  single parameter of that type everywhere it occurs. Fowler and Beck cover
  this as the paired refactoring for the smell (Fowler, Refactoring, 2nd
  edition, "Introduce Parameter Object," https://refactoring.com/catalog/introduceParameterObject.html,
  verified 2026-08-02).
- **Preserve Whole Object.** The fix when the caller already holds an object
  and is extracting individual fields from it to pass across. Instead of
  unpacking, pass the object itself and let the callee pull what it needs.
  Fowler, Refactoring, 2nd edition, "Preserve Whole Object,"
  https://refactoring.com/catalog/preserveWholeObject.html, verified
  2026-08-02. This differs from Introduce Parameter Object in direction. the
  grouping type already exists on the caller's side, so no new type is
  created, only the call site and signature are simplified.
- **Builder.** Preferred for constructors, specifically when most fields are
  optional, when validation needs to run once against the fully assembled
  state rather than field-by-field, and when the target object must be
  immutable once built. Bloch, Effective Java, 3rd edition, Item 2. This is
  more machinery than a parameter object for a plain function, and is
  usually reserved for constructors of value-like types with several
  optional fields, not for ordinary method calls.
- **Named or keyword arguments (language-native fix).** In Python, Kotlin,
  Swift, C#, and JavaScript object destructuring, the language itself
  removes the positional-transposition risk without introducing a new type,
  by letting the caller label each argument at the call site. This does not
  reduce the count on the definition side and does not solve the case where
  several parameters logically belong to a reusable concept, but it is
  often sufficient when the parameters are independent and the count is
  moderate. Python's keyword-only parameters, introduced by PEP 3102 and
  documented at https://docs.python.org/3/glossary.html#term-parameter-1,
  verified 2026-08-02, are the language mechanism (`def f(a, b, *, c, d)`)
  that forces callers to name the trailing parameters, directly reducing the
  transposition risk that motivates Fowler's original smell.
- **Fluent setters on a mutable configuration object, without a terminal
  `build()`.** A lighter-weight cousin of Builder used when the target
  object is already mutable and there is no cross-field validation step
  worth centralizing, common in configuration and options types across many
  languages, for example an HTTP client's request-configuration object.
- **Function currying or partial application, in languages that support
  it.** In functional-leaning code (TypeScript, Rust with closures, Kotlin),
  a long parameter list is sometimes decomposed by splitting the function
  into a sequence of single-argument functions applied in stages, so each
  call site only supplies the arguments relevant to it and the rest are
  captured by an earlier partial application. This is a less common variant
  than the object-based fixes and fits best when different call sites
  genuinely have different subsets of information available at different
  times, rather than when the whole group is always known at once.

## 9. Known production uses

- **Win32 `CreateWindowExW`.** Twelve parameters (`dwExStyle`,
  `lpClassName`, `lpWindowName`, `dwStyle`, `X`, `Y`, `nWidth`, `nHeight`,
  `hWndParent`, `hMenu`, `hInstance`, `lpParam`), most of them optional,
  several sharing type `int` or a handle type, in a fixed positional order
  mandated by the Windows API since Windows 2000. Microsoft Learn,
  "CreateWindowExW function (winuser.h)," https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw,
  verified 2026-08-02. Because this is a system call whose ABI cannot be
  changed, Windows application frameworks have historically wrapped it
  behind higher-level constructor or builder-style APIs (visible in the
  Microsoft-published example code on that same page, which wraps the raw
  call in a `Create` helper with default-valued parameters) rather than
  exposing the raw twelve-argument call to application authors.
- **`java.util.Calendar.set(int year, int month, int date, int hourOfDay,
  int minute, int second)`.** A six-`int` overload where five of the six
  parameters share exactly the same type, making a transposed pair of
  arguments a silent, compiling bug. Oracle, Java SE 8 API documentation,
  `java.util.Calendar`, method `set(int, int, int, int, int, int)`,
  https://docs.oracle.com/javase/8/docs/api/java/util/Calendar.html,
  verified 2026-08-02. This exact signature is one of the most frequently
  cited real-world examples of the smell in Java literature because the
  overload is still present and still used in modern Java code despite the
  language having added no positional-argument safety net for it.
- **`java.lang.StringBuilder` and the broader Effective Java "Builder"
  guidance.** Bloch's Item 2 in Effective Java is written specifically
  against the "telescoping constructor" pattern, in which a class exposes an
  overload for every combination of optional parameters, and recommends the
  Builder pattern as the fix once a constructor's parameter count and the
  proportion of optional parameters both grow past a small handful. Bloch,
  Joshua, Effective Java, 3rd edition, Addison-Wesley, 2018, Item 2. The
  pattern this item recommends, a static nested Builder class with a
  chained, fluent API terminating in `build()`, is the same shape widely
  adopted afterward across the Java ecosystem, for example in
  `okhttp3.Request.Builder` and `com.google.common.collect.ImmutableList.Builder`,
  both of which follow the identical structure of accumulating optional
  state through chained calls before producing an immutable result.

## 10. Consequences

### Positive, of applying the fix

- Call sites become self-describing. A parameter object's field names
  replace positional guesswork, so a reader does not need the function
  definition open to understand a call.
- Adding a new, optional field to the grouped concept becomes a change to
  one type rather than a change to every call site of every function that
  used the old parameter list, because existing calls that construct the
  object with named fields, or via a builder with sensible defaults, keep
  compiling.
- The compiler or type checker can catch a large class of transposition
  errors that were previously invisible, because two differently named
  fields of the same primitive type inside a labeled object are far less
  likely to be silently swapped than two positional arguments of the same
  type.
- Validation that spans several of the previously separate parameters, for
  example "checkOutDate must be after checkInDate," gets one obvious home,
  the constructor or builder of the new type, instead of being duplicated at
  every call site or, worse, omitted at some of them.
- The new type becomes reusable on its own, independent of the original
  function. A `StayDates` object extracted from one method's parameter list
  is immediately available to any other method that also needs a check-in
  and check-out pair, which is exactly the signal that the group was a
  missing concept and not merely bloat.

### Negative, of applying the fix

- Introducing a new type for a small, stable, self-evidently coherent group
  of parameters (see dimension 4, non-applicability) adds indirection and an
  allocation for no readability gain, and can make a short, frequently
  called, hot-path function marginally slower in languages where heap
  allocation is not free, a cost worth measuring rather than assuming in
  performance-sensitive code.
- A parameter object or builder can itself become a dumping ground. Once a
  team has a convenient place to add "just one more field," the same
  incremental-growth force that created the original long parameter list can
  recreate the smell one level up, inside the new type, unless the team is
  disciplined about what belongs together.
- Builders in particular add real code volume, one field, one setter or
  chained method, and one line of `build()`-time validation per field, which
  is a meaningful maintenance cost for a type with only a few optional
  fields. The fix should be sized to the problem, and a plain object literal
  or keyword arguments are frequently sufficient.
- Changing an existing, widely called function's signature from a long
  positional list to a single object parameter is itself a breaking API
  change for every external caller, which is exactly the same
  backward-compatibility force listed under dimension 3 that caused many
  long parameter lists to form in the first place. Public library authors
  often cannot apply this fix without a major version bump.

## 11. Failure modes and misuse

- **Symptom.** Two arguments swapped, code compiles, wrong result at
  runtime, discovered only under a specific input combination.
  **Cause.** Two or more parameters of the same primitive type in a long
  positional list, with no compiler-visible distinction between them, as in
  `Calendar.set` above.
  **Fix.** Apply Introduce Parameter Object so the fields carry names, or
  in a language that supports it, force keyword-only arguments so the
  compiler rejects an unlabeled call.
- **Symptom.** A function is called with several `null`, `0`, or `false`
  arguments in a row at most call sites, and reviewers cannot tell at a
  glance which trailing arguments matter for a given call.
  **Cause.** Optional configuration parameters were appended to a required
  parameter list instead of being separated into their own type with
  defaults.
  **Fix.** Extract the optional subset into an options or configuration
  object with per-field defaults, so a caller that does not need them omits
  the whole group instead of padding the call with sentinels.
- **Symptom.** The "fix" is a single object parameter named `options`,
  `params`, or `config` whose type is a loosely typed map or dictionary
  rather than a defined type, so the original problem, unclear expectations
  at the call site, has simply moved inside an untyped container.
  **Cause.** A team recognizes the smell and reaches for "pass an object"
  without also introducing a real, named type with fixed, checkable fields.
  **Fix.** Give the extracted parameter object an actual type or interface,
  even in a dynamically typed language, using a schema, a dataclass, a
  TypeScript interface, or equivalent, so the fields the function expects
  are checkable rather than merely conventional.
- **Symptom.** After refactoring to a Builder, callers still commonly build
  and discard the builder in a single expression, and no cross-field
  validation is ever exercised, yet the builder machinery persists.
  **Cause.** Builder was applied where a plain parameter object or keyword
  arguments would have sufficed, because the team pattern-matched "many
  parameters, therefore Builder" without checking whether the object needed
  incremental, staged construction or cross-field validation at all.
  **Fix.** Downgrade to Introduce Parameter Object with named-field
  construction. A builder earns its complexity only when construction
  genuinely happens in stages or the target type must remain immutable
  while intermediate, partially-built state must never be observed.
- **Symptom.** A function's parameter list did shrink to one parameter
  object, but the function's cyclomatic complexity and branching logic
  inside its body did not change at all.
  **Cause.** Long Parameter List was treated as the whole diagnosis, when
  in fact the real underlying smell is that the function does too many
  distinct things and each of those things needed its own subset of the
  original arguments, a case closer to Divergent Change or a missing
  Extract Function than to a parameter-shape problem alone.
  **Fix.** After grouping the parameters, re-examine whether the function's
  body should also be split, one function per responsibility, each taking
  only the parameter group its own responsibility needs.

## 12. Trade-off matrix

Comparing the long parameter list itself against its two dominant named
fixes, across the forces identified in dimension 3.

| Force | Long parameter list (unfixed) | Introduce Parameter Object | Builder |
|---|---|---|---|
| Call-site readability | Low once past roughly four to five parameters; requires opening the definition to confirm order | High; named fields self-document the call | High; chained, named calls self-document, and optional fields can simply be omitted |
| Transposition safety | None in statically typed positional languages; same-typed adjacent parameters are silently swappable | High; fields are named, not ordered, so a transposition requires typing the wrong field name, which is far rarer | High; same benefit as parameter object, plus staged construction avoids ever presenting an inconsistent partial state |
| Cost to add one more optional field later | Low per change, but the cumulative cost across many additions is exactly this smell | Low; add a field with a default, existing named-field call sites keep compiling | Low; add a chained setter method, existing chains keep compiling |
| Cross-field validation (e.g., "end date after start date") | Must be duplicated at every call site or, commonly, omitted entirely | Centralized in the object's constructor, run once regardless of how many callers exist | Centralized in `build()`, and can validate the fully accumulated state rather than each field in isolation |
| Runtime and code-volume cost | None beyond the parameters themselves | Small; one allocation for the grouping type, offset by removed duplication elsewhere | Larger; a full builder class, one method per field, plus the `build()` validation step |
| Fit for a small, genuinely coherent, stable group (e.g., a 2D point) | Fine as-is; wrapping it changes nothing for the better | Overkill; adds a type for a group that already reads clearly | Overkill; staged construction machinery for something constructed in one obvious step |
| Fit for backward-compatible evolution of a public API | Poor; every appended parameter risks colliding with positional callers unless placed last with a default, which is itself the accretion this smell describes | Requires a breaking signature change to introduce, unless offered as a new overload alongside the old one | Requires a breaking signature change to introduce the builder itself, though the builder's own fluent API is then extensible without further breaks |

## 13. Related and incompatible patterns

- **Introduce Parameter Object** and **Preserve Whole Object** (both
  Fowler refactorings) are the two most direct fixes and are described in
  full in dimension 8. They are complementary rather than exclusive, one
  used when a new grouping type must be created, the other when an existing
  object is being needlessly unpacked before the call.
- **Builder** (Gamma, Helm, Johnson, Vlissides, Design Patterns, 1994, and
  independently re-popularized for many-optional-field constructors by
  Bloch's Effective Java Item 2) composes with Introduce Parameter Object.
  The type a builder ultimately produces is frequently the same kind of
  cohesive value type a parameter object would be, the difference is purely
  in how construction happens, staged and validated versus assembled all at
  once.
- **Data Clumps**, the sibling smell in the same catalog, describes the
  broader pattern of the same group of data items appearing together
  repeatedly across a codebase, not only as function parameters but also as
  fields on multiple classes. A long parameter list is frequently the first
  visible symptom of an underlying, uncaught data clump, and fixing the
  clump (extracting the shared type once) often fixes several long
  parameter lists across the codebase simultaneously rather than one at a
  time.
- **Feature Envy** relates when the long parameter list exists specifically
  because a function needs several fields belonging to one other object. If
  the function is really operating on that other object's data more than
  its own, the correct fix may be to move the function onto that object
  entirely (addressing the envy) rather than merely grouping its parameters.
- **Primitive Obsession**, a closely adjacent smell not covered in this
  entry, is often the deeper root cause. A codebase that represents concepts
  like a date range, a monetary amount, or an email address as bare
  primitives rather than as small value types will keep regenerating long
  parameter lists at every new function that needs those concepts together,
  because there is no existing type to reach for. Introducing the missing
  value types (addressing Primitive Obsession directly) prevents the smell
  from recurring at the next function rather than only curing the current one.
- **Incompatible or in tension with** an intentionally minimal, dependency-free
  style favored in some systems programming contexts (embedded C, certain
  performance-critical kernels) where introducing a heap-allocated grouping
  struct is explicitly avoided to keep call overhead and memory layout fully
  predictable. In those contexts a long but flat, stack-passed parameter
  list, or a caller-allocated, caller-owned struct passed by pointer with no
  hidden allocation, is sometimes the deliberate choice over an
  object-oriented parameter object, and applying Introduce Parameter Object
  mechanically without regard for that constraint would be a misapplication.

## 14. Refactoring path in and out

### Introducing the fix (in)

1. Identify the full set of parameters at every call site of the offending
   function, not only the function's own signature, and cluster them by
   which ones vary together and which ones are always present or always
   absent as a group. A parameter that is sometimes `null` at every call
   site is a strong signal of a missing optional-configuration group.
2. For a cluster that recurs across more than one function, or that maps
   onto a concept the domain already has a name for (a date range, an
   address, a set of shipping options), create a small, named type holding
   exactly those fields, following Introduce Parameter Object.
3. Where the caller already owns an object and is currently extracting
   individual fields from it before the call, stop extracting and pass the
   object itself, following Preserve Whole Object. Verify the callee only
   needs a genuine subset of the object's public surface, or this step can
   leak unrelated data or create an unwanted coupling to the whole caller
   object.
4. Change the function's signature to accept the new grouped type or types
   in place of the individual parameters it replaces, update every call
   site, and run the full test suite. Because this changes the function's
   signature, every call site must be updated in the same change, this is
   not a step that can be done gradually one call site at a time without an
   interim overload.
5. If the target is a constructor with several optional fields and
   cross-field validation that should run once against the fully assembled
   state, replace step 4 with introducing a Builder instead. Define the
   builder with one method per field, defaulted where appropriate, and a
   `build()` that performs the validation and returns the immutable target
   type.
6. Re-examine the function body itself once the signature has shrunk. If the
   internal logic still branches heavily on which subset of the original
   parameters was supplied, the parameter-shape fix alone did not address
   the underlying responsibility overload, and Extract Function or a
   Strategy-style split may be the next, separate refactoring, per the
   failure mode noted in dimension 11.

### Removing the fix (out), when a grouping stops earning its place

1. Confirm the grouped type is used at exactly one call site and has not
   grown further since it was introduced. A parameter object that never
   became reusable and never gained more fields may have been unnecessary
   in the first place, especially if it wraps only two or three primitives
   that already read clearly as a positional pair.
2. Inline the type's fields back into positional or keyword parameters at
   that single call site, verifying no cross-field validation logic was
   living inside the type's constructor. If such validation exists, move it
   into the function body before deleting the type, so the check is not
   silently lost.
3. Delete the now-unused type, and re-run the type system's or linter's
   unused-symbol check to confirm nothing else, including serialization
   code or a schema definition, still depends on it.
4. Prefer this removal only when the grouping has demonstrably not
   generalized. A group that recurs even once across a second function is
   evidence the extraction was correct and should be kept, not reversed.

## 15. Testing and verification

Long Parameter List code is comparatively hard to test correctly precisely
because the same property that harms readability, an undifferentiated
sequence of same-typed values, also makes it easy to write a test that
passes arguments in the wrong order and still passes, since the test author
made the identical mental slip the production caller might make. A
`createReservation("2026-08-05", "guest@example.com", "Jane Doe", ...)` test
where the date and the name have been silently swapped will typically fail
loudly downstream, but a swap between two structurally similar strings, two
email-shaped values, or two numeric IDs, will often pass a test that only
checks that "a reservation was created" rather than checking each field's
specific value ended up in the right place.

After the Introduce Parameter Object fix, tests gain the ability to
construct the grouped type once, by name, and reuse it across every test
case that needs "a valid stay," which both removes the duplicated
transposition risk from every test and gives a single, obvious place to add
a test-only default or builder-style test factory (a common pattern,
`aStayDates().withCheckIn(...).build()`, sometimes called an Object Mother or
a Test Data Builder, distinct from but structurally similar to the
production Builder pattern). Equality on the parameter object, if the
language supports value-type equality (Python dataclasses, Kotlin data
classes, Java records, Swift structs conforming to `Equatable`), also lets
assertions compare the whole object in one line instead of asserting on each
field individually, which both shortens the test and makes a future field
addition to the type automatically covered by existing equality assertions
rather than silently unchecked.

For the Builder variant, the specific behavior worth testing directly is
`build()`'s cross-field validation. A well-designed test suite for a builder
should include at least one test per invalid combination the validation is
meant to reject, not only tests for the happy path, since the entire
justification for introducing a builder over a parameter object was usually
that validation needed to run against the assembled whole.

## 16. Observability signals

Long Parameter List is a static-code-structure smell, not a runtime failure
mode by itself, so it produces no direct metric of its own. Its
observability signals are indirect, visible either in code-quality tooling
or in the downstream defects it causes.

- Static analysis and linter parameter-count thresholds (for example
  ESLint's `max-params`, SonarQube's parameter-count rule, or a custom
  linter check) flag a function once it crosses a configured count, commonly
  four to seven depending on the tool's default. Treating a linter warning
  here as a hard gate rather than a prompt for judgment risks forcing the
  false-positive extractions described in dimension 4.
- Git blame and code-review history on a specific function showing repeated,
  small, single-parameter-adding commits over its lifetime is a strong
  leading indicator, even before the count crosses any fixed threshold,
  because it reveals the incremental-growth mechanism described in
  dimension 2 rather than only its current-state symptom.
- In production, the downstream signal is rarely "long parameter list"
  directly. It appears instead as a spike in a specific class of defect,
  wrong data in the wrong field, discovered post-deploy, that traces back
  through the stack to a call site with several same-typed positional
  arguments in a nonstandard or recently changed order. Correlating a bug
  report against a recent parameter-order or parameter-count change to a
  function's signature is a useful triage step once this smell is suspected.
- Code review comment patterns, specifically reviewers repeatedly asking "in
  what order do these go" or "what does the fourth argument do here" on a
  given function across multiple, unrelated pull requests, is a practical,
  low-tooling signal that a human reviewer keeps re-deriving what a linter
  or a type system could otherwise guarantee.

## 17. Security and privacy implications

The direct security implication is narrow but real. When a long parameter
list mixes several string-typed values, one of which may be a credential, a
token, or personally identifiable data, and another of which is ordinary
display text, a positional transposition can place sensitive data into a
field intended for non-sensitive display text, for example a caller
accidentally swapping an authentication token argument with an adjacent
username argument in a function that logs one of its arguments for
debugging and not the other. Because the swap compiles and often produces
no immediately visible failure, this class of defect can persist in
production for a period before discovery, during which the wrong value is
logged, displayed, or transmitted in the wrong context. Introduce Parameter
Object and named-argument styles reduce this specific risk because a named
field like `authToken` or `displayName` cannot be silently transposed the
way two adjacent positional string arguments can.

There is a secondary, more general implication rather than a sourced,
specific one. This is engineering judgment, not a documented finding.
Functions with many parameters are harder to review carefully in full, and a
reviewer's attention is a finite resource that is spent faster per line on a
call site whose meaning is not self-evident from the signature. Beyond
these two points, this smell has no privacy-specific implication of its
own. Where the underlying data is sensitive, the relevant privacy controls
(access control, encryption at rest, data minimization) apply identically
regardless of whether the data arrives via a long parameter list or a
well-named parameter object, and this entry does not claim otherwise.

## 18. References

1. Fowler, Martin, with Kent Beck. Refactoring. Improving the Design of
   Existing Code, 1st edition, chapter 3, "Bad Smells in Code."
   Addison-Wesley, 1999. https://martinfowler.com/books/refactoring.html,
   verified 2026-08-02.
2. Fowler, Martin. "Introduce Parameter Object." Refactoring catalog, 2nd
   edition companion site. https://refactoring.com/catalog/introduceParameterObject.html,
   verified 2026-08-02.
3. Fowler, Martin. "Preserve Whole Object." Refactoring catalog, 2nd edition
   companion site. https://refactoring.com/catalog/preserveWholeObject.html,
   verified 2026-08-02.
4. Bloch, Joshua. Effective Java, 3rd edition, Item 2, "Consider a builder
   when faced with many constructor parameters." Addison-Wesley, 2018.
5. Gamma, Erich, Richard Helm, Ralph Johnson, and John Vlissides. Design
   Patterns. Elements of Reusable Object-Oriented Software. Addison-Wesley,
   1994. (Origin of the Builder pattern referenced in dimensions 5, 8, and 9.)
6. Microsoft. "CreateWindowExW function (winuser.h) - Win32 apps." Microsoft
   Learn. https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw,
   verified 2026-08-02.
7. Oracle. "Calendar (Java SE 8)," method `set(int, int, int, int, int,
   int)`. Java SE 8 API documentation.
   https://docs.oracle.com/javase/8/docs/api/java/util/Calendar.html,
   verified 2026-08-02.
8. Python Software Foundation. "Glossary," entries for keyword-only and
   positional-only parameters (PEP 3102).
   https://docs.python.org/3/glossary.html#term-parameter-1, verified
   2026-08-02.

## Code examples

### TypeScript

```typescript
// Before: long parameter list, transposable string arguments.
function createReservationBad(
  guestName: string,
  guestEmail: string,
  roomNumber: number,
  checkInDate: string,
  checkOutDate: string,
  numberOfGuests: number,
  breakfastIncluded: boolean,
  paymentMethod: string,
  discountCode: string | null,
): string {
  return `${guestName} <${guestEmail}> room ${roomNumber} ` +
    `${checkInDate}..${checkOutDate} guests=${numberOfGuests} ` +
    `breakfast=${breakfastIncluded} pay=${paymentMethod} ` +
    `discount=${discountCode ?? "none"}`;
}

// After: Introduce Parameter Object + Preserve Whole Object.
interface Guest {
  name: string;
  email: string;
}

interface StayDates {
  checkIn: string;
  checkOut: string;
}

interface ReservationOptions {
  breakfastIncluded: boolean;
  paymentMethod: string;
  discountCode?: string;
}

function createReservation(
  guest: Guest,
  roomNumber: number,
  stay: StayDates,
  numberOfGuests: number,
  options: ReservationOptions,
): string {
  const discount = options.discountCode ?? "none";
  return `${guest.name} <${guest.email}> room ${roomNumber} ` +
    `${stay.checkIn}..${stay.checkOut} guests=${numberOfGuests} ` +
    `breakfast=${options.breakfastIncluded} pay=${options.paymentMethod} ` +
    `discount=${discount}`;
}

const guest: Guest = { name: "Jane Doe", email: "jane@example.com" };
const stay: StayDates = { checkIn: "2026-08-10", checkOut: "2026-08-12" };
const options: ReservationOptions = {
  breakfastIncluded: true,
  paymentMethod: "card",
};

console.log(createReservation(guest, 204, stay, 2, options));
console.log(
  createReservationBad(
    "Jane Doe",
    "jane@example.com",
    204,
    "2026-08-10",
    "2026-08-12",
    2,
    true,
    "card",
    null,
  ),
);
```

### Python

```python
from dataclasses import dataclass
from typing import Optional


# Before: long parameter list.
def create_reservation_bad(
    guest_name: str,
    guest_email: str,
    room_number: int,
    check_in: str,
    check_out: str,
    number_of_guests: int,
    breakfast_included: bool,
    payment_method: str,
    discount_code: Optional[str] = None,
) -> str:
    return (
        f"{guest_name} <{guest_email}> room {room_number} "
        f"{check_in}..{check_out} guests={number_of_guests} "
        f"breakfast={breakfast_included} pay={payment_method} "
        f"discount={discount_code or 'none'}"
    )


# After: Introduce Parameter Object, using dataclasses for value equality.
@dataclass(frozen=True)
class Guest:
    name: str
    email: str


@dataclass(frozen=True)
class StayDates:
    check_in: str
    check_out: str


@dataclass(frozen=True)
class ReservationOptions:
    breakfast_included: bool
    payment_method: str
    discount_code: Optional[str] = None


def create_reservation(
    guest: Guest,
    room_number: int,
    stay: StayDates,
    number_of_guests: int,
    options: ReservationOptions,
) -> str:
    discount = options.discount_code or "none"
    return (
        f"{guest.name} <{guest.email}> room {room_number} "
        f"{stay.check_in}..{stay.check_out} guests={number_of_guests} "
        f"breakfast={options.breakfast_included} pay={options.payment_method} "
        f"discount={discount}"
    )


if __name__ == "__main__":
    guest = Guest(name="Jane Doe", email="jane@example.com")
    stay = StayDates(check_in="2026-08-10", check_out="2026-08-12")
    options = ReservationOptions(breakfast_included=True, payment_method="card")
    print(create_reservation(guest, 204, stay, 2, options))
    print(
        create_reservation_bad(
            "Jane Doe",
            "jane@example.com",
            204,
            "2026-08-10",
            "2026-08-12",
            2,
            True,
            "card",
        )
    )
```

### Java

```java
import java.util.Objects;

public class LongParameterListDemo {

    // Before: constructor with a long parameter list and no cross-field
    // validation, the pattern Bloch's Item 2 argues against directly.
    static class PizzaBad {
        PizzaBad(int size, boolean pepperoni, boolean mushroom,
                 boolean extraCheese, boolean thinCrust) {
            System.out.println(
                "PizzaBad size=" + size + " pepperoni=" + pepperoni
                    + " mushroom=" + mushroom + " extraCheese=" + extraCheese
                    + " thinCrust=" + thinCrust);
        }
    }

    // After: Builder, following Effective Java Item 2.
    static final class Pizza {
        private final int size;
        private final boolean pepperoni;
        private final boolean mushroom;
        private final boolean extraCheese;
        private final boolean thinCrust;

        private Pizza(Builder b) {
            this.size = b.size;
            this.pepperoni = b.pepperoni;
            this.mushroom = b.mushroom;
            this.extraCheese = b.extraCheese;
            this.thinCrust = b.thinCrust;
        }

        static final class Builder {
            private final int size;
            private boolean pepperoni = false;
            private boolean mushroom = false;
            private boolean extraCheese = false;
            private boolean thinCrust = false;

            Builder(int size) {
                this.size = size;
            }

            Builder pepperoni(boolean value) {
                this.pepperoni = value;
                return this;
            }

            Builder mushroom(boolean value) {
                this.mushroom = value;
                return this;
            }

            Builder extraCheese(boolean value) {
                this.extraCheese = value;
                return this;
            }

            Builder thinCrust(boolean value) {
                this.thinCrust = value;
                return this;
            }

            Pizza build() {
                if (extraCheese && thinCrust && size < 10) {
                    throw new IllegalStateException(
                        "thin crust with extra cheese needs size >= 10");
                }
                return new Pizza(this);
            }
        }

        @Override
        public String toString() {
            return "Pizza size=" + size + " pepperoni=" + pepperoni
                + " mushroom=" + mushroom + " extraCheese=" + extraCheese
                + " thinCrust=" + thinCrust;
        }
    }

    public static void main(String[] args) {
        Pizza p = new Pizza.Builder(12)
            .pepperoni(true)
            .mushroom(true)
            .build();
        System.out.println(Objects.requireNonNull(p));

        PizzaBad bad = new PizzaBad(12, true, true, false, false);
        System.out.println(bad);
    }
}
```

## Available toolchains and what was actually run

TypeScript, Python, and Java were all compiled or run directly in this
environment.

- TypeScript. Type-checked with `npx tsc --noEmit --strict` against a
  standalone copy of the example above. It passed with zero diagnostics, and
  transpiled and ran under Node to confirm the runtime output.
- Python. Run directly with `python3` against a standalone copy of the
  example above. It printed the expected lines with no exceptions.
- Java. Compiled with `javac` and run with `java` against a standalone copy
  of the example above. It compiled cleanly and printed the expected
  `Pizza` and `PizzaBad` lines, including the `build()` validation branch
  exercised by a supplementary manual check for the `IllegalStateException`
  path (size 8, thin crust, extra cheese), which threw as designed.

Go, Rust, and Swift were available on this machine (`go`, `rustc`, and
`swiftc` all resolved), but this entry omits code samples in those three
languages by design rather than by oversight. The two fixes this smell most
directly motivates, a value-type parameter object and a fluent, staged
builder, are already fully demonstrated across TypeScript (structural
typing, object literals), Python (dataclasses, keyword-only defaults), and
Java (the canonical Builder shape from Effective Java Item 2 itself, the
book cited directly in dimension 8). Go's idiomatic answer to this same
smell, an options struct with functional options, and Rust's idiomatic
answer, the typestate or builder-with-`impl` pattern, are genuinely
different implementation variants worth a full example in a future revision
of this entry, but are left out here rather than added as a thin,
non-idiomatic restatement of the Java or TypeScript examples solely to
claim broader language coverage.
