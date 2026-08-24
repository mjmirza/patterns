---
name: Pattern Matching
slug: pattern-matching
family: 16-functional
category: Functional
aliases: [Match Expression, Case Analysis, Destructuring Match, Structural Pattern Matching]
first_described: "functional language lineage, including Hope, ML, Haskell, OCaml, Erlang"
maturity: established
related: [algebraic-data-type, result-either, option-maybe, visitor, parser-combinator, finite-state-machine]
incompatible_with: [large-type-switch, catch-all-default-flow, reflective-dispatch]
verified: 2026-08-02
---

# Pattern Matching

## 1. Name, aliases, and lineage

The canonical name is Pattern Matching. In this catalog it means a control-flow
and binding pattern that compares a subject value against ordered patterns,
selects the first fitting branch, and binds named parts of that value for use
inside the selected branch. Functional programmers also call the same shape
**case analysis**, **match expression**, **destructuring match**, and, in
languages that match object or collection shape, **structural pattern
matching**.

The lineage is older than the name of this catalog entry. The Edinburgh
Laboratory for Foundations of Computer Science history page records that Rod
Burstall's work on POP, NPL, and Hope led to pattern matching facilities that
are now standard in most functional languages, and that Robin Milner developed
ML at Edinburgh (https://informatics.ed.ac.uk/lfcs/research/programming-languages-and-foundations/history,
verified 2026-08-02). Haskell 2010 defines pattern matching in section 3.17
and says patterns appear in lambda abstractions, function definitions, pattern
bindings, list comprehensions, `do` expressions, and `case` expressions
(https://www.haskell.org/onlinereport/haskell2010/haskellch3.html#x8-530003.17,
verified 2026-08-02). OCaml 5.5 documents patterns as templates that select
data structures of a shape and bind identifiers to components
(https://ocaml.org/manual/5.5/patterns.html, verified 2026-08-02). Erlang
documents pattern matching as the mechanism used by `case`, `receive`, `try`,
and the match operator (https://www.erlang.org/doc/system/patterns.html,
verified 2026-08-02). Python adopted structural pattern matching in Python
3.10 through PEP 634, which is the normative specification for the `match`
statement (https://peps.python.org/pep-0634/, verified 2026-08-02).

The term is contested at the edges. In ML-family languages, a pattern usually
means a syntactic form with constructors, literals, wildcards, variables, and
guards. In TypeScript, teams often say "pattern matching" when they mean a
`switch` over a discriminated union plus an exhaustiveness check with `never`.
That TypeScript form is a useful approximation, but it lacks native nested
destructuring in branch labels. In object-oriented design catalogs, the Visitor
pattern is sometimes offered as the object-oriented replacement for pattern
matching when operations vary more often than data variants. This entry treats
Visitor as a related alternative, not as the same pattern.

Engineering judgement. Pattern Matching is best understood as a reusable
program shape, not a single GoF-style named invention. Its mature form appears
when sum types, product types, branch selection, binding, and exhaustiveness
checking meet in one language or local discipline.

## 2. Problem and context

A program receives a value whose exact case, shape, or constructor determines
the next computation. The value may be an algebraic data type, an AST node, an
error result, a protocol message, a tuple, a map, an enum with associated data,
or a small tagged record. The code has to choose an action, bind fields from
the value, reject unsupported shapes, and keep the handling readable as cases
grow.

Without Pattern Matching, the same work often turns into scattered checks. One
branch tests a tag, then another branch casts, then a later line reads a field
that only exists for one case. A parser asks whether a token is an identifier,
then calls a second method to read the identifier text. A service receives a
message map, checks a string key, and then reads values with unchecked
lookups. An error handler tests `is_ok`, then asserts that the value is `Ok`.
Those shapes separate the question "what case is this?" from the action "use
the fields of that case." The gap is where missed cases, stale casts, and
runtime key errors enter.

Pattern Matching joins the test and the binding. A branch label says both "the
subject must have this shape" and "these names are available if it does." When
the language has a closed set of constructors, the compiler can report missing
cases or unreachable branches. Rust says patterns are used in `let`
declarations, function parameters, `match`, `if let`, `while let`, and `for`
expressions, and its reference documents destructuring for structs, enums, and
tuples (https://doc.rust-lang.org/stable/reference/patterns.html, verified
2026-08-02). Swift's language reference documents wildcard, identifier, value
binding, tuple, enum case, optional, type-casting, and expression patterns
(https://docs.swift.org/swift-book/ReferenceManual/Patterns.html, verified
2026-08-02). Python PEP 634 defines literal, capture, wildcard, value,
sequence, mapping, and class patterns (https://peps.python.org/pep-0634/,
verified 2026-08-02).

The context matters. Pattern Matching earns its place when the subject has a
small, meaningful shape vocabulary and when each branch has a business action
that belongs next to the case definition. It is less useful when the choice is
open-ended plugin dispatch, when runtime configuration drives the branch, or
when the action should be supplied by the data variant itself through
polymorphism.

## 3. Forces

Engineering judgement. This dimension weighs design pressure. The trade-offs
vary by language, because compiler exhaustiveness and runtime matching rules
change the cost profile.

- **Coupling.** Favoured when callers depend on a closed data shape instead of
  concrete subclasses. Sacrificed when every operation knows every data variant.
- **Consistency.** Favoured in languages with exhaustiveness checking. Missing
  cases become compiler errors or warnings rather than latent incidents.
- **Latency.** Usually neutral for small enums. Can be sacrificed when guards
  run side-effecting or costly code, or when a dynamic language performs
  attribute lookups and equality checks during matching.
- **Operability.** Favoured when branch names map to domain cases and can be
  logged as low-cardinality labels. Sacrificed when a catch-all branch hides
  new cases from metrics.
- **Cost of change.** Favoured when adding a new operation over a stable data
  set. Sacrificed when adding a new data variant, because many matches may need
  edits.
- **Team topology.** Favoured when one team owns a closed protocol or AST and
  other teams add operations over it. Sacrificed when separate teams need to
  add variants without coordinating branch updates.
- **Cognitive load.** Favoured when nested structure replaces cast ladders and
  nullable field reads. Sacrificed when patterns become dense mini-programs.
- **Security and privacy.** Favoured when malformed input is rejected by shape
  before field reads. Sacrificed when broad mapping or class patterns invoke
  user-controlled equality, attribute, or length behavior.

The pattern favours explicit shape handling and local reasoning. It sacrifices
open extensibility along the data-variant axis unless paired with a separate
extension mechanism.

## 4. Applicability and non-applicability

Reach for Pattern Matching when the following hold.

- The subject has a closed or slowly changing set of cases, such as an enum,
  result, option, AST node, protocol message, or command.
- Branch code needs fields from the matched case, and binding them in the case
  label removes casts or unchecked lookups.
- The language or local style can check exhaustiveness, or tests can enumerate
  all known cases.
- The operation varies more often than the data variants. Adding a new report
  over an AST is cheaper as one match than as many visitor methods.
- The branch labels form a domain table that a reader can scan from top to
  bottom.
- Invalid input should be rejected by shape before the business action runs.

Do NOT reach for Pattern Matching in these cases.

- **The data variants are open to external plugins.** A closed match in the
  host must be edited for every plugin. Prefer a registry, Command, Strategy,
  or polymorphic method.
- **The branch condition is mostly numeric policy.** A table, rule engine, or
  decision table is clearer when the conditions are thresholds, ranges, dates,
  or pricing rules maintained by non-programmers.
- **A default branch would swallow future cases.** If the data set is meant to
  be closed, a catch-all branch removes the pressure that would reveal missing
  handling.
- **The matched object hides expensive behavior behind accessors.** Dynamic
  class and mapping patterns may call equality, attribute access, `len`, or map
  access. Use explicit validation when those operations are untrusted.
- **The operation belongs to the variant.** If each variant already owns the
  behavior and the caller does not need to coordinate across variants,
  polymorphism can keep code closer to the data.
- **The data shape changes more often than the operations.** Visitor or methods
  may localize change better when adding variants is common and adding
  operations is rare.
- **The match is a long sequence of unrelated cases.** That is a dispatch
  table, router, or registry in disguise.
- **The branch bodies mutate shared state in different ways.** A finite-state
  machine table, command log, or transaction script may expose transitions more
  plainly.
- **The language has no native support and the emulation is opaque.** In such
  a language, a small tagged union plus a `switch` can be fine. A heavy library
  that hides ordinary control flow may not pay for itself.

## 5. Structure

The main participants are roles, not classes.

- **Subject.** The value being inspected. It can be an enum value, tuple,
  record, map, AST node, token, message, or result.
- **Pattern set.** The ordered list of candidate patterns. Each pattern states
  a shape, literal, constructor, type, tuple layout, map keys, or wildcard.
- **Binder.** The part of the matcher that introduces names for components
  when a pattern succeeds. In source code the binder is the variable names
  written inside the pattern.
- **Guard.** An optional boolean condition evaluated after the structural part
  succeeds. Python PEP 634 specifies that guards are evaluated once the pattern
  succeeds and that guard evaluation proceeds in case order
  (https://peps.python.org/pep-0634/, verified 2026-08-02).
- **Branch body.** The computation selected by the first matching pattern and
  guard pair.
- **Exhaustiveness checker.** The compiler, linter, or test runner that
  decides whether every value in the subject's domain is handled. Rust's
  compiler development guide says usefulness checking detects unreachable
  branches and checks whether matches are exhaustive
  (https://rustc-dev-guide.rust-lang.org/pat-exhaustive-checking.html,
  verified 2026-08-02).
- **Fallback.** A wildcard, default, error branch, or impossible marker. It is
  valid for open inputs and dangerous for closed domains.

The key relationship is one-way. The branch body can trust the binder only
because the pattern already succeeded. The guard can use the bound names, but
the guard must not be treated as part of the structural proof. If a guard fails,
the matcher resumes with later patterns in languages that define guards that
way, as OCaml does for `when` guards
(https://ocaml.org/manual/4.05/expr.html, verified 2026-08-02).

## 6. ASCII structure diagram

```
   +--------------------+
   |      Subject       |
   |--------------------|
   | tag, fields, shape |
   +---------+----------+
             |
             v
   +--------------------+       binds        +------------------+
   |     Pattern Set    |------------------->|      Binder      |
   |--------------------|                    |------------------|
   | Pattern 1 + guard  |                    | names for fields |
   | Pattern 2 + guard  |                    +------------------+
   | Pattern 3          |
   | Fallback           |        selects      +------------------+
   +---------+----------+------------------->|   Branch Body    |
             |                               |------------------|
             | checked by                    | domain action    |
             v                               +------------------+
   +--------------------+
   | Exhaustiveness     |
   | Checker            |
   |--------------------|
   | missing cases      |
   | unreachable cases  |
   +--------------------+
```

## 7. Dynamics

At runtime the matcher evaluates the subject, tries patterns in the language's
defined order, binds names for a successful structural match, evaluates the
guard if one exists, and runs the selected body. Python PEP 634 specifies that
the subject is evaluated first, a tuple is built when the subject expression
contains a comma, and the first case whose pattern succeeds and whose guard is
truthy is selected (https://peps.python.org/pep-0634/, verified 2026-08-02).
Swift's statements reference says a `switch` behaves as if pattern matching is
performed in source order, and only the first matching case runs
(https://docs.swift.org/swift-book/documentation/the-swift-programming-language/statements/,
verified 2026-08-02).

```
Caller          Matcher          Pattern A        Guard A        Branch A
  |                |                 |               |              |
  |-- subject ---->|                 |               |              |
  |                |-- test shape -->|               |              |
  |                |<-- succeeds ----|               |              |
  |                |-- bind fields ----------------->|              |
  |                |---------------- guard --------->|              |
  |                |<--------------- true ----------|              |
  |                |---------------------------------------------->|
  |                |<---------------- result ----------------------|
  |<-- result -----|                 |               |              |

If Pattern A fails, the matcher tries Pattern B.
If Guard A fails, the matcher resumes at the next pattern.
If no pattern matches, the language chooses compile error, runtime error,
no-op match completion, or a required fallback, depending on its rules.
```

The sequence has two traps. First, a name bound by a failed dynamic pattern may
have language-specific behavior. PEP 634 explicitly leaves some failed-match
binding behavior unspecified so implementations can optimize
(https://peps.python.org/pep-0634/, verified 2026-08-02). Second, a guard is
ordinary code. If it reads time, random state, a database, or mutable globals,
the match is no longer a pure case table.

## 8. Implementation variants

**ML-family algebraic matching.** Haskell, OCaml, FSharp, Rust, and Swift style
matching over enums or algebraic data types is the clearest form. Constructors
name cases, nested patterns destructure fields, and the compiler can reason
about missing constructors. Haskell 2010 says case alternatives are tried
sequentially and pattern matching is specified in section 3.17
(https://www.haskell.org/onlinereport/haskell2010/haskellch3.html#x8-530003.17,
verified 2026-08-02).

**Expression versus statement.** In Rust and Haskell a match can produce a
value, so all branch bodies must agree on a type. In Python the `match`
construct is a statement, so it selects statements and does not itself produce
a value. The expression form helps keep transformations total. The statement
form fits command-style code and can make early exits easier.

**Destructuring assignment.** `let (x, y) = point` and similar forms use
irrefutable patterns. They bind structure but do not branch. They are Pattern
Matching's low-risk sibling and work well when the shape is already known.

**Partial matching forms.** `if let`, `guard case`, `while let`, and Python
single-case `match` blocks handle one interesting case and let the rest pass.
They reduce indentation for optional and result flows, but they can hide
missing cases when the subject domain is closed.

**Guards.** Guards attach value-level predicates to structural patterns. They
are useful for ranges, authorization state, and cross-field checks. They reduce
the ability of the compiler to prove coverage, because a structurally complete
pattern may still reject at runtime.

**Or patterns.** Or patterns let several shapes share one body. Python requires
each subpattern in an OR pattern to bind the same names
(https://peps.python.org/pep-0634/, verified 2026-08-02). That rule keeps the
branch body from depending on a name that exists only in one alternative.

**Mapping and class patterns.** Python's structural patterns can match mappings
and classes, including `__match_args__` for positional class matching
(https://peps.python.org/pep-0634/, verified 2026-08-02). This is powerful for
edge input and domain objects. It is also where side effects and surprising
lookups enter.

**TypeScript discriminated unions.** TypeScript does not have native pattern
labels like Rust or Swift. The practical form is a union with a literal
discriminator and a `switch`. The `never` assignment in the default branch
turns unhandled variants into a type error. This gives exhaustiveness for the
top-level tag but not nested structural matching.

**Visitor replacement.** Visitor moves branch selection into double dispatch.
It is useful when adding operations across stable variants is common in a
language without native matching. It is heavier than a match expression and
often spreads one operation across many files.

**Router or dispatch-table generation.** Phoenix documents that its router
uses macros to compile routes to a single case statement with pattern matching
rules optimized by the Erlang VM
(https://github.com/phoenixframework/phoenix/blob/main/lib/phoenix/router.ex,
verified 2026-08-02). This is Pattern Matching as generated code, not as
handwritten branch lists.

## 9. Known production uses

**Rust compiler, exhaustiveness and usefulness checking.** The Rust compiler
uses pattern analysis to detect unreachable match arms and non-exhaustive
matches. The Rust compiler development guide names the `rustc_pattern_analysis`
crate and the usefulness module as the implementation area for this checking
(https://rustc-dev-guide.rust-lang.org/pat-exhaustive-checking.html, verified
2026-08-02). This is a production use of Pattern Matching as a language
contract and as compiler analysis.

**Phoenix Router.** Phoenix documents that router macros compile routes into a
single case statement with pattern matching rules, optimized by the Erlang VM
(https://github.com/phoenixframework/phoenix/blob/main/lib/phoenix/router.ex,
verified 2026-08-02). The production pattern is generated route dispatch over
HTTP method and path shape.

**Erlang OTP `gen_server`.** Erlang's `gen_server` behavior calls callback
functions such as `Module:handle_call/3`, passes the request term, and
interprets tagged tuple return values such as `{reply, Reply, NewState}` and
`{noreply, NewState}` (https://www.erlang.org/docs/26/man/gen_server.html,
verified 2026-08-02). Erlang system documentation states that pattern matching
occurs in function clauses, `case`, `receive`, and match expressions
(https://www.erlang.org/doc/system/patterns.html, verified 2026-08-02).
Production OTP servers commonly write separate callback clauses for request
and return shapes.

**Python standard language feature.** PEP 634 is the normative specification
for Python 3.10 structural pattern matching
(https://peps.python.org/pep-0634/, verified 2026-08-02). The PEP also states
that namedtuples and dataclasses receive generated `__match_args__` support,
which makes pattern matching part of standard library data modeling.

**Erlang receive loops.** Erlang concurrent programming documentation says a
process `receive` scans messages and tries patterns in order, keeping messages
that do not match while later messages may match
(https://www.erlang.org/doc/system/conc_prog.html, verified 2026-08-02). That
is production message dispatch by pattern, built into the runtime model.

## 10. Consequences

Positive.

- Branch selection and field binding happen in one construct, so branch bodies
  contain less casting and fewer unchecked reads.
- Closed-domain handling becomes visible. In languages with compiler support,
  a new enum case can force edits at every relevant match.
- Code that transforms algebraic data can read like the data grammar.
- Invalid shapes can be rejected before the branch reads fields.
- Branch labels can become useful trace labels when logged at low cardinality.
- Tests can be table-driven by subject value and expected branch result.
- Parser, evaluator, reducer, and message-handler code often becomes shorter
  without losing explicitness.

Negative.

- Adding a new data variant may require many matches to change.
- Long matches become local god functions when branch bodies grow.
- Catch-all defaults can erase compiler help and hide new cases.
- Dense nested patterns can be harder to read than small helper predicates.
- Guards can make coverage analysis weaker and behavior less predictable.
- In dynamic languages, pattern matching may call user-defined equality,
  attribute access, length, or mapping operations.
- Public APIs that expose raw variants can freeze representation choices.

Engineering judgement. The central cost is the expression problem. Pattern
Matching makes it easy to add operations over a closed data set. It makes it
harder to add data variants without visiting those operations.

## 11. Failure modes and misuse

Engineering judgement. These are production failure shapes to watch for. The
symptoms are observable in code review, tests, telemetry, or incidents.

- **Symptom.** A new enum case ships and user requests fall into a generic
  "unknown" path. **Cause.** A wildcard branch was used on a closed domain.
  **Fix.** Replace the wildcard with named cases and let the checker report
  missing cases. Keep a fallback only at untrusted input boundaries.
- **Symptom.** A match has fifty lines per branch and every branch opens a
  database transaction. **Cause.** Branch selection and business workflow were
  combined. **Fix.** Keep the match as a router to small named functions, then
  test each function directly.
- **Symptom.** A branch intended for a rare case never runs. **Cause.** A broad
  pattern appears before the narrow pattern. **Fix.** Order from narrow to
  broad, and add unreachable-pattern warnings to the build where the language
  can provide them.
- **Symptom.** Metrics show high fallback counts after a deploy, but no error
  is raised. **Cause.** Open input and closed domain cases use the same
  fallback branch. **Fix.** Split parse or validation from domain matching, and
  emit a counted error for unknown external shapes.
- **Symptom.** Python matching sometimes calls slow or unsafe methods. **Cause.**
  Class, mapping, equality, or length behavior is user-defined. PEP 634 notes
  that matching may rely on attribute access, instance checks, `len`, equality,
  item access, and class-name evaluation (https://peps.python.org/pep-0634/,
  verified 2026-08-02). **Fix.** Normalize untrusted input into plain data
  before matching.
- **Symptom.** A guard logs twice, writes twice, or reads changing state.
  **Cause.** Guards are treated as declarative patterns though they are code.
  **Fix.** Keep guards pure and move side effects into the branch body.
- **Symptom.** TypeScript reports no error after a union grows. **Cause.** The
  `switch` has a `default` that returns a value instead of assigning to
  `never`. **Fix.** Use a named `assertNever` or `const x: never = value`.
- **Symptom.** Developers avoid adding cases because every operation needs
  edits. **Cause.** Pattern Matching was chosen for an open variant axis.
  **Fix.** Move to Visitor, Strategy, or polymorphic methods for that axis.
- **Symptom.** Tests cover happy cases but miss malformed structures. **Cause.**
  The match is treated as self-testing. **Fix.** Add tests for unknown tags,
  missing fields, extra fields, empty collections, and guard failure.

## 12. Trade-off matrix

| Force | Pattern Matching | Visitor | Strategy | Registry dispatch |
|---|---|---|---|---|
| Coupling | Operation depends on all variants | Variants depend on visitor interface | Caller depends on chosen strategy | Dispatcher depends on registration keys |
| New operation | Cheap, add one match | Costly, add visitor methods | Cheap if operation is one strategy family | Cheap, add handler |
| New variant | Costly, edit matches | Cheap after visitor method exists | Often cheap | Cheap if key can register |
| Exhaustiveness | Strong in Rust, Swift, ML style | Strong only by interface discipline | Weak | Weak unless registry is checked |
| Local readability | High for small closed domains | Lower, operation spread across types | High per strategy | High for flat dispatch |
| Runtime cost | Low for small cases | Low virtual dispatch | Low virtual or function dispatch | Lookup cost plus handler |
| Team topology | Good for shared closed data | Good for variant-owning teams | Good for independent behavior teams | Good for plugin teams |
| Operability | Branch labels can be logged | Visitor names need instrumentation | Strategy names are natural labels | Keys are natural labels |
| Failure mode | Catch-all hides cases | Boilerplate drift | Wrong strategy wired | Missing registration |

Engineering judgement. If the data set is closed and operations grow, Pattern
Matching usually wins. If variants grow independently, Visitor or polymorphism
wins. If behavior is selected by configuration, Strategy or Registry dispatch
wins.

## 13. Related and incompatible patterns

**Algebraic Data Type** is the natural partner. Pattern Matching becomes most
valuable when the subject is a sum type whose constructors are known.

**Result Either** and **Option Maybe** rely on Pattern Matching for explicit
handling. `Ok` and `Err`, or `Some` and `None`, are small closed domains where
exhaustiveness is high-value.

**Visitor** replaces Pattern Matching when an object-oriented language needs
closed variants with many operations and lacks native matching. Visitor keeps
variant-specific code in methods, while Pattern Matching keeps one operation in
one place.

**Finite State Machine** composes with Pattern Matching when state and event
are both closed data. The match selects a transition. A table-driven state
machine may be better when transitions are data maintained outside code.

**Parser Combinator** often produces AST nodes consumed by Pattern Matching.
The parser builds the shape. The evaluator, pretty-printer, or analyzer matches
the shape.

**Command** conflicts when the matched value already carries executable
behavior. If the message is a command object with an `execute` method, a large
match over command classes duplicates dispatch.

**Large Type Switch** is the degraded form. It branches on runtime type, then
casts and reads fields. Pattern Matching can repair it when the language has
safe type or class patterns. Polymorphism can remove it when behavior belongs
to the type.

**Catch-all Default Flow** conflicts with closed-domain matching because it
turns future cases into silent old behavior.

## 14. Refactoring path in and out

To introduce Pattern Matching:

1. Find a branch chain where each branch tests the same subject's tag, type, or
   shape.
2. Name the subject type. If the shape is implicit, introduce a small enum,
   sealed union, tagged record, or dataclass hierarchy.
3. Move casts and field reads into branch labels or the smallest local
   destructuring step.
4. Replace broad conditions with narrow cases ordered from specific to broad.
5. Remove the catch-all if the domain is closed. If input is open, keep a
   fallback that returns a parse or validation error.
6. Add an exhaustiveness check. In TypeScript, use `never`. In Rust and Swift,
   let the compiler check enum cases. In Python, use table tests over known
   variants.
7. Pull long branch bodies into functions named after the action, not after the
   pattern syntax.
8. Add branch-label logging only after the behavior is correct.

To remove Pattern Matching:

1. Count how often data variants change versus operations. If variants change
   more often, plan the move.
2. For behavior owned by each variant, move branch bodies into methods on the
   variants or into strategy objects.
3. For plugin systems, replace the match with a registry keyed by message type
   or capability.
4. For policy tables, move threshold and range decisions to a decision table
   and keep code as validation plus interpreter.
5. Keep the old match as a compatibility wrapper until all callers use the new
   dispatch path.
6. Delete the fallback last, after tests prove every old subject maps to the new
   path.

Cross reference the refactoring family entries for Replace Conditional with
Polymorphism, Decompose Conditional, Extract Function, Introduce Parameter
Object, and Replace Type Code with Subclasses where those entries fit the host
language.

## 15. Testing and verification

Engineering judgement. Good tests treat the match as a domain table and test
both shape and branch behavior.

- Use a case matrix. One row per variant, with representative field values and
  expected result.
- Test boundary guards. If a guard says `amount > 0`, test zero, negative, and
  positive values.
- Test fallback behavior. Open input should return a named validation failure.
  Closed input should have no fallback or an impossible marker.
- Test unreachable branches through compiler settings. In Rust, keep warnings
  visible. In TypeScript, enforce `never` in the default path.
- Use mutation testing where available. Deleting a branch or changing a tag
  should fail a test.
- Test serialization boundaries separately. Convert raw JSON, maps, or messages
  to a typed subject before matching domain cases.
- Use property tests for recursive data such as ASTs and trees. Generate all
  node types and assert that transformations preserve invariants.
- Snapshot branch labels only if they are part of logs or public diagnostics.

Pattern Matching makes selected branch tests easier because a subject value
fully determines the branch. It makes global coverage harder when matches are
scattered across a large codebase. The verification response is a mix of
compiler checks, grep-able branch labels, and small table tests.

## 16. Observability signals

Engineering judgement. Make the match visible without logging full subject
payloads.

Log the selected case name, not the entire value. For external input, log
normalization failures with a reason such as `missing_kind`, `unknown_kind`, or
`bad_shape`. For closed domains, a fallback counter should be zero in healthy
production. Any nonzero fallback count after a deploy deserves investigation.

Trace attributes should include the subject family and branch label, for
example `payment_event.case=refund` or `ast_node.case=binary_expr`. Keep labels
low-cardinality. Do not include user text, raw JSON, card numbers, or full
exception messages as labels.

Metrics to collect:

- Branch counts per case.
- Fallback counts per boundary.
- Guard failure counts where guards represent business rejection.
- Match latency if guards or dynamic accessors can be expensive.
- Unknown-case rate after deployments.
- Dead-branch count from compiler or linter reports.

A healthy dashboard has stable branch distributions, zero closed-domain
fallbacks, and guard rejection rates that match business expectations. A
failing instance shows a spike in unknown cases, a sudden drop to the catch-all
branch, or guard latency rising after a change to subject accessors.

## 17. Security and privacy implications

Engineering judgement. Pattern Matching is not a security boundary by itself,
but it can make validation clearer when used at the right boundary.

The pattern closes risk by making illegal shape handling explicit. A raw message
can be parsed into a closed domain value, and later code can match that value
without rechecking keys. It also helps avoid "check then use" races inside one
function because the branch body receives bound values from the successful
pattern.

The pattern opens risk when dynamic matching invokes user-controlled behavior.
Python PEP 634 states that matching may rely on attribute access, instance
checks, `len`, equality, item access, value-pattern evaluation, and class-name
evaluation, and that side-effect behavior is partly undefined
(https://peps.python.org/pep-0634/, verified 2026-08-02). Do not pattern-match
rich untrusted objects before normalizing them. Convert to plain dicts, enums,
dataclasses, or validated records first.

Privacy risk appears in observability. The subject often contains user input,
tokens, addresses, or document text. Log case names and validation reasons, not
payloads. Branch labels are usually safe. Bound values often are not.

Authorization must not live only in pattern shape. A pattern can prove that a
message is `DeleteAccount(id)`. It cannot prove that the caller may delete that
account. Keep authorization as an explicit branch step or precondition.

## 18. References

- Brandt Bucher, Guido van Rossum, PEP 634, "Structural Pattern Matching:
  Specification", Python Enhancement Proposals, Python 3.10, sections
  "Syntax and Semantics", "Patterns", "Guards", "Side Effects and Undefined
  Behavior", https://peps.python.org/pep-0634/, verified 2026-08-02.
- Daniel F Moisset, PEP 636, "Structural Pattern Matching: Tutorial", Python
  Enhancement Proposals, Python 3.10,
  https://peps.python.org/pep-0636/, verified 2026-08-02.
- The Rust Project Developers, "Patterns", The Rust Reference, sections
  "Patterns", "Destructuring", "Reference patterns",
  https://doc.rust-lang.org/stable/reference/patterns.html, verified
  2026-08-02.
- The Rust Project Developers, "Match expressions", The Rust Reference,
  https://doc.rust-lang.org/reference/expressions/match-expr.html, verified
  2026-08-02.
- The Rust Compiler Developers, "Pattern and exhaustiveness checking", Rust
  Compiler Development Guide,
  https://rustc-dev-guide.rust-lang.org/pat-exhaustive-checking.html, verified
  2026-08-02.
- Apple Inc. and the Swift Project Authors, "Patterns", The Swift Programming
  Language, Language Reference,
  https://docs.swift.org/swift-book/ReferenceManual/Patterns.html, verified
  2026-08-02.
- Apple Inc. and the Swift Project Authors, "Statements", The Swift Programming
  Language, Language Reference,
  https://docs.swift.org/swift-book/documentation/the-swift-programming-language/statements/,
  verified 2026-08-02.
- Simon Marlow, editor, "Haskell 2010 Language Report", chapter 3, sections
  3.13 and 3.17, https://www.haskell.org/onlinereport/haskell2010/,
  verified 2026-08-02.
- OCaml Developers, "The OCaml language, Patterns", OCaml Manual 5.5,
  https://ocaml.org/manual/5.5/patterns.html, verified 2026-08-02.
- OCaml Developers, "Expressions", OCaml Manual 4.05, section "Case
  expression" and "Guards in pattern-matchings",
  https://ocaml.org/manual/4.05/expr.html, verified 2026-08-02.
- Erlang/OTP Documentation Team, "Pattern Matching", Erlang System
  Documentation v29.0.5, https://www.erlang.org/doc/system/patterns.html,
  verified 2026-08-02.
- Erlang/OTP Documentation Team, "Concurrent Programming", Erlang System
  Documentation v29.0.5, section on `receive`,
  https://www.erlang.org/doc/system/conc_prog.html, verified 2026-08-02.
- Erlang/OTP Documentation Team, "gen_server", STDLIB Reference Manual,
  version 5.2.3.6, https://www.erlang.org/docs/26/man/gen_server.html,
  verified 2026-08-02.
- Phoenix Framework, `Phoenix.Router` documentation and source,
  https://github.com/phoenixframework/phoenix/blob/main/lib/phoenix/router.ex,
  verified 2026-08-02.
- LFCS, School of Informatics, University of Edinburgh, "History of Research on
  Programming Languages at Edinburgh University",
  https://informatics.ed.ac.uk/lfcs/research/programming-languages-and-foundations/history,
  verified 2026-08-02.

## Code examples

The following samples were compiled or run on 2026-08-21 with `python3`,
`rustc`, `swiftc`, and `npx tsc` plus `node`. Swift needed
`CLANG_MODULE_CACHE_PATH` set to a writable directory under `/private/tmp`.

Python 3.10 or newer. Native structural pattern matching.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    amount: int
    currency: str


def classify(event):
    match event:
        case {"type": "refund", "amount": amount} if amount > 0:
            return f"refund:{amount}"
        case {"type": "charge", "payment": Card(amount, "USD")}:
            return f"usd-charge:{amount}"
        case {"type": kind}:
            return f"other:{kind}"
        case _:
            return "invalid"


print(classify({"type": "charge", "payment": Card(35, "USD")}))
print(classify({"type": "refund", "amount": 12}))
```

Rust. Native enum matching with guards and exhaustiveness.

```rust
enum Event {
    Charge { amount: i32, currency: &'static str },
    Refund(i32),
    Unknown,
}

fn classify(event: Event) -> String {
    match event {
        Event::Charge { amount, currency: "USD" } if amount > 0 => {
            format!("usd-charge:{amount}")
        }
        Event::Refund(amount) if amount > 0 => format!("refund:{amount}"),
        Event::Charge { currency, .. } => format!("charge:{currency}"),
        Event::Refund(_) | Event::Unknown => "invalid".to_string(),
    }
}

fn main() {
    println!("{}", classify(Event::Charge { amount: 35, currency: "USD" }));
    println!("{}", classify(Event::Refund(12)));
    println!("{}", classify(Event::Unknown));
}
```

Swift. Enum cases with associated values and `where` guards.

```swift
enum Event {
    case charge(amount: Int, currency: String)
    case refund(Int)
    case unknown
}

func classify(_ event: Event) -> String {
    switch event {
    case let .charge(amount, "USD") where amount > 0:
        return "usd-charge:\(amount)"
    case let .refund(amount) where amount > 0:
        return "refund:\(amount)"
    case let .charge(_, currency):
        return "charge:\(currency)"
    case .refund, .unknown:
        return "invalid"
    }
}

print(classify(.charge(amount: 35, currency: "USD")))
print(classify(.refund(12)))
print(classify(.unknown))
```

TypeScript. Discriminated union plus `never` exhaustiveness.

```typescript
type DomainEvent =
  | { kind: "charge"; amount: number; currency: "USD" | "EUR" }
  | { kind: "refund"; amount: number }
  | { kind: "unknown" };

function classify(event: DomainEvent): string {
  switch (event.kind) {
    case "charge":
      return event.currency === "USD" && event.amount > 0
        ? `usd-charge:${event.amount}`
        : `charge:${event.currency}`;
    case "refund":
      return event.amount > 0 ? `refund:${event.amount}` : "invalid";
    case "unknown":
      return "invalid";
    default: {
      const neverEvent: never = event;
      return neverEvent;
    }
  }
}

console.log(classify({ kind: "charge", amount: 35, currency: "USD" }));
console.log(classify({ kind: "refund", amount: 12 }));
```
