---
name: Interpreter Architecture
slug: interpreter-architecture
family: 05-architectural
category: Architectural
aliases: [Tree-Walking Interpreter, AST Interpreter, Language Workbench Interpreter]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [interpreter-gof, visitor, composite, specification, builder, strategy]
incompatible_with: []
verified: 2026-08-02
---

# Interpreter Architecture

## 1. Name, aliases, and lineage

The canonical name inside this catalog is Interpreter Architecture, and it
names the system-level discipline of building a small language, an
abstract syntax tree that represents sentences in that language, and an
evaluator that walks the tree to produce a result. This entry sits in the
architectural family because it is about the shape of a whole subsystem,
grammar, parser, tree, evaluator, host integration, rather than the single
class-level object structure that the GoF book describes under the name
Interpreter. The GoF Interpreter pattern, filed separately in this catalog
under `interpreter-gof`, is the narrow structural idiom this entry's
evaluator commonly uses once the tree exists. This entry is the wider story
of what it takes to ship that idiom as a real subsystem.

The pattern traces to Erich Gamma, Richard Helm, Ralph Johnson and John
Vlissides, *Design Patterns. Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994, chapter 3, Behavioral Patterns, Interpreter. The book
states the intent as, given a language, define a representation for its
grammar along with an interpreter that uses the representation to interpret
sentences in the language. A concise restatement of that intent, including
the roles of AbstractExpression, TerminalExpression, NonTerminalExpression,
Context, and Client, is recorded at
[Wikipedia, Interpreter pattern](https://en.wikipedia.org/wiki/Interpreter_pattern)
(verified 2026-08-02), which also names SQL as a specialized query language
commonly represented this way.

Common aliases in industry usage, none of them from the GoF text itself.
**Tree-Walking Interpreter** is the term compiler and language-implementation
literature uses for an evaluator that recurses directly over a parsed AST
rather than compiling to bytecode or machine code first. Robert Nystrom's
*Crafting Interpreters* (Genever Benning, 2021) uses this term throughout
part two of the book and states plainly, when describing an evaluator whose
behaviour lives in methods attached to the tree node classes, "this exact
thing is literally called the Interpreter pattern"
([craftinginterpreters.com, Representing Code](https://craftinginterpreters.com/representing-code.html),
verified 2026-08-02). **AST Interpreter** is the same idea stated as a noun
phrase and appears throughout compiler course material and JVM literature.
**Language Workbench Interpreter** is Martin Fowler's framing for the case
where the tree comes from a domain-specific language authored by non-engineers
and interpreted at runtime rather than compiled ahead of time. The alias
matters because it signals scope. this entry covers everything from a
five-line boolean expression evaluator to a production rule engine, and the
architectural decisions differ sharply across that range.

A distinction worth drawing at the outset, because it recurs through every
dimension below. an interpreter is not the only way to execute a small
language. The alternatives are a compiler that emits bytecode or native code
ahead of a separate execution phase, and a transpiler that emits source in
another language. Tree-walking interpretation is the cheapest of the three to
build and the most expensive per operation to run, and choosing it is a
deliberate trade discussed in dimension 3.

## 2. Problem and context

A system needs to accept a piece of behaviour, a rule, a query, a formula, a
policy, that was not known when the system was compiled, and that behaviour
must be safe to run inside the host process without the full trust extended
to the host's own code.

The shape recurs in a specific way. Somewhere in the codebase there is a
`switch` or a chain of `if` statements that grew past what anyone wants to
maintain, because the thing being switched on is not really a fixed enum, it
is an expression a user typed, a rule an operations team configured, a filter
a customer built in a UI, or a formula a spreadsheet cell contains. The team
tries first to solve this with more configuration, a JSON object carrying an
`"operator"` field set to `"and"` and a `"conditions"` array, and that JSON
object is already, whether anyone names it or not, an abstract syntax tree.
The question the team is actually answering, usually without realizing it,
is whether to keep growing that ad hoc tree-walking `switch` by hand or to
name it, give it a grammar, and build the interpreter architecture properly.

The context that makes this the right answer, rather than embedding a general
purpose scripting language, has three parts.

- The language is genuinely small and closed. It has a bounded set of
  operators, literals, and combinators that the team controls, not the full
  surface of a general purpose language. Once a feature request needs
  arbitrary loops, user-defined functions, and mutable state that outlives one
  evaluation, the problem has usually outgrown a purpose-built interpreter and
  is asking for an embedded general purpose language such as Lua instead.
- The rules or expressions come from outside the compiled binary, at
  configuration time, request time, or from an end user, and must be evaluated
  repeatedly without a redeploy. If the set of expressions is fixed and known
  at compile time, hand-writing the logic in the host language is simpler and
  faster, and the interpreter buys nothing.
- Sandboxing matters. the evaluator must be able to run untrusted or
  semi-trusted input without granting it access to the filesystem, the
  network, or arbitrary host objects, something a general purpose scripting
  language embedding usually cannot guarantee without substantial extra work.
  Apache Commons JEXL states this trade-off directly in its own documentation,
  contrasting itself with Groovy and Nashorn, saying it interprets a parsed
  syntax tree rather than compiling scripts to bytecode or defining new
  classes per script
  ([Apache Commons JEXL](https://commons.apache.org/proper/commons-jexl/),
  verified 2026-08-02), a direct statement of the tree-walking choice made
  specifically to bound the attack surface and the memory footprint.

## 3. Forces

Latency versus build cost. A tree-walking interpreter is the cheapest
architecture to build, often a working evaluator in an afternoon for a small
grammar, but it is the slowest architecture to run, because every node visit
re-dispatches through virtual calls or a switch and re-derives work a compiled
representation would have done once. A bytecode virtual machine is roughly an
order of magnitude more work to build correctly, including a compiler pass
from AST to bytecode, and typically two to ten times faster to execute for
the same program, because dispatch becomes a flat instruction loop instead of
a recursive tree walk. Teams under-estimate this gap constantly, discover it
in production under load, and then face a rewrite instead of an incremental
upgrade, which is why dimension 14 below treats the tree-walker to
bytecode-VM path as a first class refactor, not an afterthought.

Expressiveness versus sandboxing. Every additional feature the language
grows, user-defined functions, closures, mutable variables that outlive a
single evaluation, host object access, is a feature that widens what an
untrusted author of a rule or expression can do inside the process. The
force pulls in opposite directions depending on who authors expressions.
When only trusted engineers author them, richer expressiveness is close to
free. When an end user or a customer-facing UI authors them, every added
capability is a new line item on a security review, and the honest answer is
frequently to keep the language deliberately anemic.

Coupling to the host object model. An interpreter that reaches directly into
host language objects, calling arbitrary methods by reflection so users can
write something like a dotted field path against a live object graph, is far
more convenient to author expressions in and far harder to keep safe, because
the surface exposed is the entire public API of whatever object graph gets
passed in. An interpreter with an explicit, enumerated set of accessor
functions is safer and more auditable and noticeably more work to keep in
sync as the host model changes.

Consistency and determinism. A rule engine or formula evaluator that people
trust to reproduce the same decision from the same inputs must be free of
hidden nondeterminism, ambient clock reads, random number generation, network
calls, unordered map iteration leaking into output order. This is a force
the interpreter architecture must design for explicitly, because a general
purpose host language makes all of that trivially reachable by accident the
moment host objects are exposed.

Operability and observability. Because the "code" being run is data, not a
compiled artifact, the operational question changes shape. instead of asking
which binary is deployed, the team must ask which version of a rule or
expression executed for a given decision, and be able to reconstruct that
after the fact. This is a genuinely different operability profile from
ordinary application code, discussed further in dimension 16.

Cognitive load on the maintainer of the grammar versus the author of an
expression. A small grammar with three operators is trivial for both. A
grammar that has grown organically to twenty operators, precedence rules
nobody wrote down, and quiet special cases for backward compatibility,
becomes a system only its original author can safely extend, which is
precisely the failure mode dimension 11 documents as grammar creep.

## 4. Applicability and non-applicability

Reach for an interpreter architecture when the language is small and under
the team's control, when expressions or rules are supplied at runtime by
configuration, an end user, or a separate business team, when the set of
operators is expected to grow slowly and predictably rather than explode,
when sandboxing untrusted input matters more than raw throughput, and when
the audience authoring expressions benefits from a notation closer to their
own domain than to the host programming language, a business analyst writing
a plain age and country condition rather than a pull request.

Do not reach for it in these cases, each with the concrete reason.

- **The set of behaviours is fixed and known at compile time.** If every rule
  the system will ever need is known when the code is written, a `switch` or
  a table of function pointers in the host language is faster to build,
  faster to run, and easier for the next engineer to read, because there is
  no grammar to learn on top of the host language everyone already knows.
- **The language would need general purpose expressiveness.** Loops with
  unbounded iteration, first-class functions, and mutable state that persists
  across evaluations are exactly the features that turn "a small interpreter"
  into "an unmaintained, under-tested scripting language," and at that point
  embedding an actual general purpose language such as Lua, with its own
  mature tooling, sandboxing model, and community-tested implementation, is
  the honest choice rather than continuing to extend a homegrown one.
- **Performance is on the hot path and the expression set changes rarely.**
  If the same handful of predicates run millions of times per second, a
  tree-walking interpreter's per-node dispatch overhead is frequently the
  biggest cost in the whole request path. Compiling the expression once into
  a closure, a bytecode routine, or native code, and caching that compiled
  form, removes the recurring dispatch cost. If the compiled form can be
  produced once and cached, the interpreter's simplicity buys nothing on the
  hot path and a compile step should replace it.
- **The problem is really just data validation.** A rule engine is
  overkill for a problem that JSON Schema, a set of typed guard clauses, or a
  handful of `if` statements solves completely. Reaching for a grammar and a
  tree because the word "rules" appeared in a requirements document, without
  first checking whether the rules are actually just validation constraints,
  is a common and expensive over-engineering mistake.
- **No untrusted or semi-trusted party ever supplies the expression.** If
  every expression the system will ever evaluate is written and reviewed by
  the same engineers who ship the host binary, the sandboxing force that
  motivates most interpreter architectures does not apply, and the honest
  cost-benefit favours ordinary compiled code.

## 5. Structure

The full architecture has more moving parts than the GoF class diagram
alone, because a production interpreter is a pipeline, not a single object
graph.

- **Grammar.** The formal definition of what a valid sentence in the
  language looks like, usually written as a set of production rules, whether
  or not it is ever expressed in a grammar description language such as
  ANTLR's `.g4` files or a hand-written recursive descent parser's structure.
- **Lexer (Scanner).** Converts raw source text into a stream of tokens,
  stripping whitespace and comments, recognizing literals, identifiers,
  keywords, and operator symbols. Small grammars sometimes fold this into the
  parser, larger ones keep it a distinct pass because error messages and
  incremental re-parsing both benefit from the separation.
- **Parser.** Consumes the token stream and produces the abstract syntax
  tree, enforcing precedence and associativity, and is the place where a
  malformed expression is rejected before evaluation ever begins.
- **Abstract Syntax Tree (AST) nodes.** The GoF AbstractExpression,
  TerminalExpression, and NonTerminalExpression roles live here.
  TerminalExpression nodes are leaves, a literal number, a variable reference,
  a string. NonTerminalExpression nodes are internal nodes that hold child
  expressions and combine their results, an addition node holding a left and
  right operand, an `and` node holding a list of conditions.
- **Context.** Carries whatever state the interpretation of a given tree
  needs, variable bindings, a symbol table, the object the rule is being
  evaluated against. The GoF Context role. Passed alongside the tree, never
  stored inside the AST nodes themselves, so the same immutable tree can be
  evaluated against many different contexts without cloning it.
- **Evaluator.** The mechanism that walks the tree and produces a result,
  either as an `interpret` method on each node, the classic GoF shape, or as
  an external Visitor that dispatches on node type, discussed as a variant in
  dimension 8.
- **Client.** Builds or receives the AST, whether by parsing source text, by
  deserializing a JSON representation, or by a fluent builder API, and drives
  evaluation against a Context.
- **Host integration boundary.** The explicit, audited surface through which
  the interpreter can read from or act on the surrounding system, function
  registries, variable resolvers, and any capability the language exposes to
  its authors. This is the component most catalogs omit and the one most
  responsible for whether the resulting system is safe.

## 6. ASCII structure diagram

```
                 +----------------------------+
                 |          Client            |
                 |  parses/builds source into  |
                 |     an AST, drives eval      |
                 +--------------+--------------+
                                |
                                v
   +----------------+   +--------------+   +------------------+
   |     Lexer      |-->|    Parser    |-->|   AST (tree of    |
   | text -> tokens |   | tokens -> AST|   | AbstractExpression |
   +----------------+   +--------------+   |     nodes)         |
                                            +---------+----------+
                                                      |
                                     +----------------+----------------+
                                     |                                 |
                                     v                                 v
                        +------------------------+       +------------------------+
                        |  TerminalExpression     |       | NonTerminalExpression  |
                        |  (literal, variable ref) |       | (and, or, +, function  |
                        |  interpret(ctx) -> value |       |  call). holds children |
                        +------------------------+       |  interpret(ctx) ->      |
                                                            |  combine children      |
                                                            +------------------------+
                                     |                                 |
                                     +----------------+----------------+
                                                      |
                                                      v
                                          +------------------------+
                                          |        Context         |
                                          | variable bindings,      |
                                          | function registry,      |
                                          | the object under test   |
                                          +-----------+-------------+
                                                      |
                                                      v
                                          +------------------------+
                                          |  Host integration       |
                                          |  boundary (explicit,    |
                                          |  audited accessors)     |
                                          +------------------------+
```

## 7. Dynamics

The pipeline runs in two distinct phases that many under-designed
implementations blur together, parse-once evaluate-many, and separating them
is the single most valuable architectural decision available.

```
PARSE PHASE (runs once per distinct expression source, cacheable)

  raw text ----> Lexer ----> token stream ----> Parser ----> AST
                                                     |
                                          (syntax error here is
                                           rejected before any
                                           evaluation attempt)

EVALUATION PHASE (runs once per Context, potentially millions of times
                   against the same already-parsed AST)

  Client
    |
    | interpret(context_1)
    v
  AST root (a NonTerminalExpression, e.g. "and")
    |
    +--> left.interpret(context_1)  --> recurses into its own children
    |        until a TerminalExpression is reached, which reads a value
    |        directly from context_1 or returns a literal
    |
    +--> right.interpret(context_1) --> same recursive descent
    |
    +--> combine(left_result, right_result) --> boolean/value result
    |
    v
  result_1 returned to Client

    ... later, same AST, a different context ...

  Client
    |
    | interpret(context_2)
    v
  AST root -----> same recursive walk against context_2's bindings
    |
    v
  result_2 returned to Client (AST itself was never mutated)
```

The property worth naming explicitly. the AST is immutable once parsed, and
every piece of state that varies between evaluations lives in the Context,
never in the tree nodes. This is what makes the parse-once evaluate-many
shape safe under concurrency, many threads can call `interpret` on the same
shared tree simultaneously as long as each carries its own Context, with no
locking required on the tree itself, because there is nothing on the tree
that ever changes after construction.

## 8. Implementation variants

**Method-per-node (classic GoF Composite-style dispatch).** Each AST node
class implements its own `interpret` method, and the tree evaluates itself
through ordinary polymorphic dispatch. Simplest to write for a small,
stable grammar. Adding a new node type is one new class. Adding a new
operation across every node type, adding a pretty-printer alongside the
evaluator, means touching every node class, the classic expression problem
that Nystrom's *Crafting Interpreters* names directly when introducing the
Visitor pattern as the fix
([craftinginterpreters.com, Representing Code](https://craftinginterpreters.com/representing-code.html),
verified 2026-08-02).

**External Visitor dispatch.** Node classes hold only data, and a separate
Visitor class implements `interpret`, `prettyPrint`, `typeCheck`, and any
other tree operation as its own method with one case per node type. Adding a
new operation is one new Visitor, no change to existing node classes.
Adding a new node type means touching every existing Visitor. This is the
variant used through most of *Crafting Interpreters* and through most
production-grade language tooling, because new operations, type checkers,
optimizers, linters, formatters, tend to arrive far more often than new
grammar productions once a language stabilizes.

**Recursive function over a tagged union or enum (functional style).** In
languages with pattern matching, Rust, Swift, F#, OCaml, the AST is a tagged
enum and `interpret` is a single recursive function with one match arm per
variant, rather than a method on each type or a separate Visitor class. This
collapses the class hierarchy the GoF diagram implies into a single
exhaustive `match`, and the compiler enforces that every case is handled
whenever a new variant is added, which is effectively the Visitor pattern's
benefit without the boilerplate, paid for by requiring a language with
algebraic data types and exhaustiveness checking.

**Direct-threaded and closure-based interpretation.** Instead of a switch
that re-dispatches on node type at every visit, the parser compiles each AST
node once into a closure that captures its already-resolved children as
other closures, so evaluation becomes a chain of direct function calls with
no further type dispatch. This keeps the tree-walking simplicity of build
while removing the repeated dispatch cost of a naive walker, and is a
common middle step between a pure tree-walker and a full bytecode VM.

**Bytecode compilation with a separate VM loop.** The AST is compiled once
into a flat sequence of instructions for a small stack or register machine,
and a tight interpreter loop executes that instruction stream. This is not
the GoF Interpreter pattern's node-level dispatch at all, it is the
architecture's escape hatch when the tree-walker's per-call overhead becomes
the bottleneck, and it is the shape CPython, the Java Virtual Machine, and
Lua's reference implementation all use rather than walking a tree directly
at execution time.

**JIT compilation of hot expressions.** For expressions evaluated at very
high frequency, the interpreter can profile which expressions are hot and
compile just those to native code at runtime, keeping the tree-walker as the
fallback for cold paths. This is the architecture V8 and the JVM's HotSpot
compiler use for general purpose languages, and it appears in narrower form
in some high-throughput rule engines, though most purpose-built business
rule interpreters never need it because their throughput requirements sit
well below the threshold where JIT compilation pays for its own complexity.

## 9. Known production uses

**Apache Commons JEXL**, an expression language interpreter for the JVM used
to embed dynamic scripting features in Java applications and frameworks.
JEXL's own documentation states its architecture directly, that it
interprets a parsed syntax tree rather than compiling scripts to bytecode or
defining new classes per script, naming the trade-off of predictable memory
usage and reduced attack surface as the reason for choosing tree-walking
interpretation over Groovy's or Nashorn's bytecode compilation
([Apache Commons JEXL project page](https://commons.apache.org/proper/commons-jexl/),
verified 2026-08-02).

**jq**, the command-line JSON processor, is built around a small filter
language whose programs are trees of composed filters. Its own manual states
the core model plainly, that a jq program is a filter, it takes an input and
produces an output, with filters combined by piping, the comma operator, and
array or object construction, the same NonTerminalExpression-combines-
children-into-a-result shape this entry describes
([jq manual](https://jqlang.org/manual/), verified 2026-08-02).

**Backtracking regular expression engines** used in Perl, the PCRE library,
Python, Ruby, and Java are, at the implementation level, recursive
tree-walking interpreters over the parsed regular expression's structure,
attempting one alternative and backtracking on failure. Russ Cox's widely
cited analysis states that Perl, PCRE, Python, Ruby, Java, and many other
languages have regular expression implementations based on recursive
backtracking that are simple but can be excruciatingly slow, and contrasts
this tree-walking approach against Ken Thompson's NFA simulation, which
processes the same pattern without walking the parsed structure at match
time
([Russ Cox, "Regular Expression Matching Can Be Simple And Fast"](https://swtch.com/~rsc/regexp/regexp1.html),
verified 2026-08-02). This is a genuinely useful production example precisely
because it also demonstrates the performance force from dimension 3, the
same regex feature implemented as a tree-walking interpreter versus an
automaton-based evaluator differs in Cox's own benchmark by roughly six
orders of magnitude on a pathological input.

**SQL database engines**, in the specific sense that a database's query
executor walks a parsed representation of the `WHERE` clause's boolean
expression tree to decide, row by row or in a vectorized batch, whether a
given row satisfies the predicate. Wikipedia's summary of the GoF pattern
names SQL directly as the canonical example of a specialized computer
language the pattern was designed to represent
([Wikipedia, Interpreter pattern](https://en.wikipedia.org/wiki/Interpreter_pattern),
verified 2026-08-02), and this is the production use most engineers meet
first without ever naming it, because the object-relational mapping layer
that builds a `WHERE` clause from chained method calls, an ORM's fluent query
builder, is constructing exactly the AST this entry describes before handing
it to the database's own interpreter.

## 10. Consequences

Positive.

- The grammar can grow to accommodate new operators or literal types by
  adding new AST node classes, without modifying the parser's core control
  flow or the evaluator's dispatch mechanism, so long as the change stays
  within the existing precedence and structure.
- Expressions supplied at runtime, from configuration, from an end user, or
  from a separate business team, execute without a redeploy of the host
  binary, decoupling the release cadence of the rules from the release
  cadence of the application.
- The evaluator can be sandboxed precisely, because the only capabilities an
  expression has are the ones the host integration boundary explicitly
  exposes, in contrast to embedding a general purpose scripting language
  where the sandbox boundary is far larger and harder to audit.
- The same AST, once parsed, can be evaluated repeatedly against many
  different contexts without re-parsing, which amortizes the one real fixed
  cost, parsing, across an arbitrary number of evaluations.
- Because the tree is data, it can be introspected, serialized, logged,
  diffed between versions, and explained to a non-engineer, a case where a
  rule matched because two named conditions were both true, in a way
  compiled host-language logic cannot be without a separate audit layer.

Negative.

- Per-node dispatch overhead makes a naive tree-walking evaluator
  meaningfully slower per operation than the equivalent hand-written host
  language code, an overhead that compounds badly on hot paths, as the regex
  production example in dimension 9 demonstrates at the extreme.
- The grammar becomes its own maintenance burden separate from the host
  application's normal code, requiring its own tests, its own documentation,
  and its own versioning discipline, work that is easy to under-budget at
  design time because it does not look like ordinary feature work.
- A poorly bounded language invites grammar creep, discussed in dimension
  11, where each new business requirement adds one more special-case
  operator rather than being expressed in terms of the operators already
  present, until the language is larger and less coherent than the host
  language it was built to avoid touching.
- Error messages from a hand-rolled parser are frequently worse than
  compiler error messages from the host language, because building a parser
  that produces genuinely helpful diagnostics, correct line and column
  numbers, a clear explanation of what was expected, is a substantial extra
  engineering investment most teams skip until users complain.
- Debugging a running interpretation is harder than debugging ordinary code,
  because standard debuggers step through the evaluator's own recursive
  calls rather than through the semantics of the interpreted language, and a
  team that needs to explain why a rule returned false under production
  pressure needs purpose-built tracing, not a debugger breakpoint.

## 11. Failure modes and misuse

Symptom, cause, fix, for the failure modes that recur in real interpreter
architectures.

- **Symptom.** The rule engine's evaluation time grows noticeably worse
  release over release, with no single change anyone can point to.
  **Cause.** Grammar creep. Each new business requirement was solved by
  adding one more operator or one more special-case node type rather than
  composing the operators already present, so the AST for a typical
  expression has grown deeper and the evaluator now walks substantially more
  nodes per evaluation than it did a year earlier, and nobody tracked the
  growth because no single commit looked expensive. **Fix.** Establish a
  concrete node-count or tree-depth budget per expression class, measure it
  in CI against representative expressions, and treat a request for a new
  primitive operator as a design review rather than a routine pull request,
  actively asking whether the new requirement can be expressed by composing
  existing operators first.

- **Symptom.** A production incident traces back to a user-authored
  expression that read a field, an object, or a method the interpreter's
  authors never intended to expose. **Cause.** The host integration boundary
  was implemented by reflection over the full host object graph rather than
  through an explicit, enumerated accessor registry, so the actual reachable
  surface for an expression was never a bounded, auditable set, it was
  everything reachable from the root object passed into Context, including
  private state the object's own class never intended to expose through its
  public API. **Fix.** Replace reflective host access with an explicit
  function and variable registry that the interpreter's authors control line
  by line, and treat any addition to that registry as a reviewed API surface
  change, exactly as if it were a new public method on the host system.

- **Symptom.** Two engineers debugging the same failing rule get different
  answers about what it evaluated to, or a rule that worked in staging
  produces a different result in production against what looks like the
  same input. **Cause.** The interpreter's Context or a TerminalExpression
  reads ambient state that is not part of the explicit input, the current
  wall-clock time read directly instead of passed in, a random number
  generator, an unordered map whose iteration order leaked into the output
  when the language allowed multiple matching branches and picked the first
  one nondeterministically. **Fix.** Audit every TerminalExpression and
  every built-in function for a source of nondeterminism, and require that
  any time-dependent or random behaviour be threaded explicitly through the
  Context as an input rather than read ambiently, so the same AST-and-Context
  pair is guaranteed to produce the same result every time.

- **Symptom.** The interpreter's throughput becomes the biggest cost on a
  request path that used to be governed by a database call or a network
  call, and profiling points squarely at the `interpret` recursion. **Cause.**
  A tree-walking interpreter, chosen originally for build simplicity when
  expression volume was low, was never revisited as volume grew by two or
  three orders of magnitude, and per-node dispatch overhead that was
  invisible at low volume is now the bottleneck. **Fix.** Add a compilation
  cache that turns a parsed AST into a closure chain or a small bytecode
  routine the first time it is seen, and reuse the compiled form on
  subsequent evaluations, following the incremental path described in
  dimension 14 rather than a full rewrite.

- **Symptom.** A parse error message a user sees is a stack trace, a
  cryptic token mismatch, or a line number that does not correspond to
  anything the user actually typed. **Cause.** The parser was built purely
  to accept valid input and reject invalid input, with no investment in
  producing a diagnostic that names what was expected at the point of
  failure, because that investment felt like polish rather than a
  correctness requirement during initial development. **Fix.** Treat parser
  error messages as a first-class deliverable with their own test suite,
  asserting the exact message text for a representative set of malformed
  inputs, the same discipline applied to any other user-facing error
  surface.

## 12. Trade-off matrix

| Force | Interpreter Architecture (tree-walking) | Bytecode VM | Embedded general purpose language (e.g. Lua) | Compiled host-language logic (no interpreter) |
|---|---|---|---|---|
| Build cost | Low. days to weeks for a small grammar | High. a compiler pass plus a VM loop | Low if a mature embedding exists, high if hand-rolled | Lowest. no grammar, no parser |
| Runtime latency per evaluation | Higher. recursive dispatch per node | Lower. flat instruction loop | Comparable to bytecode VM, mature JIT in some cases | Lowest. ordinary compiled or JIT'd host code |
| Sandboxing untrusted authors | Strong, if host integration boundary is explicit | Same as tree-walker, inherited from the same grammar | Weaker by default, larger surface to audit | Not applicable, authors are trusted engineers |
| Runtime redeploy of new rules | Yes, no host rebuild needed | Yes, no host rebuild needed | Yes, no host rebuild needed | No, requires a code change and deploy |
| Debuggability for the language's authors | Moderate, needs purpose-built tracing | Lower, an extra compiled layer to reason about | Often good, mature language tooling exists | Best, host language's own debugger applies directly |
| Best fit | Small, bounded, runtime-supplied language, sandboxing matters | Same language, once throughput demands it | Genuinely general purpose scripting needed | Fixed, compile-time-known logic |

## 13. Related and incompatible patterns

**Interpreter (GoF, class-level).** Filed separately in this catalog under
`interpreter-gof`. This entry is the system that surrounds and motivates that
narrower structural idiom, the grammar, the parser, the host integration
boundary, and the production concerns of running it. A team implementing
this architecture will very often implement the GoF Interpreter pattern as
one piece of it, the `interpret` method per node, but the architecture is a
larger commitment than the class diagram alone represents.

**Visitor.** The external-dispatch implementation variant from dimension 8
is a direct application of Visitor to the AST, and most production-grade
interpreters that expect to add operations, type checking, optimization,
pretty printing, over time choose Visitor dispatch over method-per-node for
exactly the expression-problem reason Nystrom names.

**Composite.** The AST itself is a Composite structure, a
NonTerminalExpression is a composite that holds child expressions and
recurses into them, a TerminalExpression is a leaf. The Interpreter
architecture is frequently described as Composite plus a shared operation,
`interpret`, applied uniformly across the tree.

**Specification.** In domain modelling, a Specification object that
combines smaller specifications with `and`, `or`, and `not` and exposes an
`isSatisfiedBy` check over a candidate object is, structurally, the same
tree-and-evaluate shape this entry describes, applied specifically to
business rule predicates rather than a general expression language. A team
building a rule engine for boolean business conditions is frequently better
served by recognizing this relationship and reaching for the narrower,
well-understood Specification shape before building a general-purpose
grammar.

**Builder.** A fluent API for constructing an AST programmatically, an ORM's
query builder is the clearest production example, is commonly implemented as
a Builder that assembles Interpreter-architecture nodes without ever
exposing a textual grammar or a parser to the caller at all.

**Strategy.** Where the "language" collapses to choosing among a small,
fixed set of whole algorithms rather than composing operators into an
expression tree, Strategy is the simpler, correct pattern, and building an
interpreter architecture for that case is over-engineering, a direct
instance of the non-applicability case in dimension 4.

**Incompatible with.** None recorded as a structural conflict. The pattern
does interact unfavourably with a hard requirement for compile-time
exhaustiveness checking of every possible input without any runtime parsing
step at all, in which case there is no interpreter to build in the first
place, the logic belongs in the host language directly.

## 14. Refactoring path in and out

**Introducing the architecture into code that does not have it.** Start from
the ad hoc `switch` or nested `if` chain that motivated dimension 2's
problem statement. First, extract the conditions that switch is branching on
into small, named, immutable value objects, one per condition, without yet
introducing any grammar or parser, this is Martin Fowler's Extract Class
applied to what will become the TerminalExpression nodes. Second, introduce a
single shared interface those value objects implement, an `interpret` method
that takes a Context and returns a result, and rewrite the original branching
code to call that interface instead of switching on a type code, which is
the moment the code has adopted the GoF Interpreter idiom without yet having
a textual grammar at all. Third, only if expressions genuinely need to be
authored outside the compiled binary, add a parser that builds the same tree
from text or from a JSON representation, keeping the tree of value objects
from step one and two completely unchanged, so the parser is additive rather
than a rewrite of the evaluator. This staged path is deliberate. it lets a
team stop after step two if the sandboxing and runtime-configurability
forces from dimension 3 turn out not to be needed, which is a materially
cheaper outcome than building the full grammar and parser up front and
discovering afterward that nobody needed runtime-supplied expressions.

**Refactoring out, tree-walker to bytecode VM.** When the failure mode in
dimension 11, throughput governed by interpretation overhead, actually
materializes, the incremental path is a compile-and-cache layer inserted
between the parser and the evaluator, not a rewrite of the grammar or the
parser. Add a compilation pass that walks the AST once and produces either a
closure chain, per the direct-threaded variant in dimension 8, or a flat
instruction sequence for a small VM, and cache that compiled form keyed by
the parsed AST's identity. The grammar, the parser, and the semantics of
every operator are untouched. what changes is purely the mechanism between
the AST existing and a result being produced, which keeps the blast radius
of the refactor to the evaluator alone and leaves every existing test that
asserts on evaluation results, rather than on evaluator internals, passing
unmodified.

**Removing the architecture entirely.** When the set of expressions has
stabilized and stopped changing at runtime, meaning nobody has actually
authored a new expression through the runtime path in a meaningful window,
consider inlining the now-fixed set of expressions as ordinary host-language
functions and removing the parser and grammar altogether. This is the mirror
image of the introduction path, and the same value-object tree from step one
of introduction is frequently exactly the intermediate shape to fall back
to, still testable, still named, but no longer parsed from text.

## 15. Testing and verification

Test the grammar and the evaluator as two separate concerns, because they
fail independently and conflating them in one test suite hides which layer
actually broke.

For the parser, golden-file or table-driven tests that assert the exact AST
shape produced by a representative set of source strings, including
deliberately malformed input, are the most valuable investment, because a
parser bug produces a silently wrong tree far more often than it produces a
crash, and only an assertion on the tree's actual shape catches that.
Property-based testing is a strong fit here specifically, generate random
but grammatically valid expressions, parse them, pretty-print the resulting
tree back to source, and assert that re-parsing the pretty-printed output
produces an identical tree, a round-trip property that catches an entire
class of parser and pretty-printer bugs that example-based tests miss.

For the evaluator, test each TerminalExpression and each
NonTerminalExpression's `interpret` behaviour in isolation against a
directly-constructed tree, bypassing the parser entirely, so an evaluator
test failure can never be caused by a parser bug and vice versa. This is
where the Interpreter architecture's Context separation pays off directly
for testability, because the same tree can be evaluated against many
different hand-built Context fixtures without any parsing step, making it
cheap to enumerate edge cases, empty collections, boundary numeric values,
missing variable bindings, that would be awkward to express as source
strings.

For the host integration boundary specifically, add a dedicated test suite
that asserts the exact set of functions and variables an expression can
reach, a form of allowlist testing that fails loudly the moment someone
widens the boundary, whether deliberately or by accident, which is the
concrete test-level defense against the host-integration failure mode named
in dimension 11.

For determinism, run the same AST and Context pair through evaluation
multiple times in a test and assert bit-for-bit identical results, and where
the language permits time or randomness as explicit inputs, fuzz those
inputs specifically rather than trusting a single fixed value in every test.

## 16. Observability signals

Because the executing "code" is data rather than a compiled artifact, the
observability question that matters most is provenance, being able to
answer, for any given evaluation, exactly which version of which expression
ran and against which inputs. Log, at minimum, a content hash or version
identifier of the AST that was evaluated alongside every result, never just
the result itself, so a later investigation can reconstruct precisely what
logic produced a given decision even after the expression has since been
edited or replaced.

Track parse failure rate and parse latency separately from evaluation
failure rate and evaluation latency, because a spike in either signals a
different problem, a rising parse failure rate usually points at a client
sending malformed expressions or a schema mismatch, a rising evaluation
failure rate usually points at a host integration boundary function that
started throwing, a variable binding that is now unexpectedly absent from
Context.

Track a distribution of AST node count and tree depth per distinct
expression over time, not just per evaluation, as the direct operational
signal for the grammar creep failure mode from dimension 11, a slow upward
drift in typical tree size across releases is visible in this metric long
before it shows up as a latency regression.

For a rule engine specifically, emit, per evaluation, which branches or
sub-expressions actually contributed to the final result, an explanation
trace rather than only the final boolean or value, because the ability to
show that a rule matched because one condition was true and a second
condition was short-circuited is frequently a product requirement in its own
right for audit-sensitive domains, and is comparatively cheap to add at the
evaluator level by having each NonTerminalExpression record which children
it actually visited.

## 17. Security and privacy implications

The host integration boundary from dimension 5 is the entire security
surface of this architecture, and every claim in this dimension traces back
to how tightly that boundary is scoped. An interpreter whose accessor
functions are hand-enumerated and reviewed like any other public API exposes
exactly the capabilities its authors intended and nothing else. An
interpreter that reaches into the host object graph by reflection exposes
whatever is reachable from the root object, which in a typical object
oriented codebase includes far more than its authors would knowingly choose
to expose, private fields readable through a getter that was never meant to
be called from untrusted code, methods with side effects that were written
assuming only trusted internal callers.

Resource exhaustion is a concrete and easily overlooked risk specific to
interpreters that accept untrusted expression text. an attacker who can
supply arbitrary syntax can attempt deeply nested expressions to cause stack
overflow during recursive parsing or recursive evaluation, extremely large
literal collections to exhaust memory, or, in a language rich enough to
permit unbounded loops or recursion inside the expression language itself,
an infinite loop that starves the host process. A production interpreter
accepting untrusted input needs explicit, enforced limits on parse depth,
tree size, and evaluation step count or wall-clock time, none of which are
provided automatically by the interpreter architecture itself and all of
which must be designed in deliberately.

Where the Context carries personal data, account balances, health records,
identity attributes, into the evaluator so that expressions can reference
them, the interpreter's logging and tracing layer from dimension 16 becomes
a data handling surface in its own right. an explanation trace that records
which fields a condition compared is, by design, logging the sensitive value
it just compared, and a team building the observability layer for a rule
engine over personal data must treat that trace output with the same
handling discipline as the underlying data itself, not as generic diagnostic
logging exempt from data protection review.

Where expressions are authored by one party and evaluated on behalf of
another, a multi-tenant rule engine where tenant A's rules run against
tenant B's data under some shared evaluation service, the host integration
boundary must additionally prevent cross-tenant data leakage through the
expression language's own error messages, a parse or evaluation error that
echoes back a fragment of the data it was evaluating against can leak
another tenant's data through what looks like an innocuous diagnostic
message, and error paths deserve the same audit applied to the success path.

## Code examples

A small boolean rule interpreter, the shape a business rule engine or an
access-control policy engine actually takes in production. TypeScript, Python,
and Go, three languages where the same tree-and-Context shape is idiomatic in
different ways. TypeScript and Python both use ordinary class polymorphism,
the method-per-node variant from dimension 8. Go has no inheritance, so the
same variant appears as a small interface implemented by several structs,
which is the language-idiomatic form Go code actually uses for this pattern.
All three build the identical AST by hand, an And node holding two Compare
leaves, and evaluate it against three different Context values, demonstrating
the parse-once evaluate-many property from dimension 7 without a parser at
all, only the tree and the evaluator.

### TypeScript

```typescript
type Context = Record<string, number | string>;

interface Expression {
  interpret(ctx: Context): boolean;
}

class Compare implements Expression {
  constructor(
    private readonly field: string,
    private readonly op: ">=" | "==" | "in",
    private readonly value: number | string | string[],
  ) {}

  interpret(ctx: Context): boolean {
    const actual = ctx[this.field];
    if (this.op === ">=") return (actual as number) >= (this.value as number);
    if (this.op === "==") return actual === this.value;
    return (this.value as string[]).includes(actual as string);
  }
}

class And implements Expression {
  constructor(private readonly children: Expression[]) {}
  interpret(ctx: Context): boolean {
    return this.children.every((c) => c.interpret(ctx));
  }
}

class Or implements Expression {
  constructor(private readonly children: Expression[]) {}
  interpret(ctx: Context): boolean {
    return this.children.some((c) => c.interpret(ctx));
  }
}

class Not implements Expression {
  constructor(private readonly child: Expression) {}
  interpret(ctx: Context): boolean {
    return !this.child.interpret(ctx);
  }
}

const rule: Expression = new And([
  new Compare("age", ">=", 18),
  new Compare("country", "in", ["DE", "AT"]),
]);

const adultDe: Context = { age: 21, country: "DE" };
const minorDe: Context = { age: 15, country: "DE" };
const adultUs: Context = { age: 30, country: "US" };

console.log(rule.interpret(adultDe));
console.log(rule.interpret(minorDe));
console.log(rule.interpret(adultUs));

const notRule: Expression = new Not(new Compare("country", "==", "US"));
console.log(notRule.interpret(adultUs));
```

Output, in order.

```
true
false
false
false
```

### Python

The class-attribute-free, dataclass-based form Python rule engines use most
often, one frozen dataclass per node, each implementing the same abstract
`interpret` method.

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass

Context = dict[str, object]


class Expression(ABC):
    @abstractmethod
    def interpret(self, ctx: Context) -> bool: ...


@dataclass(frozen=True)
class Compare(Expression):
    field: str
    op: str
    value: object

    def interpret(self, ctx: Context) -> bool:
        actual = ctx.get(self.field)
        if self.op == ">=":
            return actual >= self.value  # type: ignore[operator]
        if self.op == "==":
            return actual == self.value
        if self.op == "in":
            return actual in self.value  # type: ignore[operator]
        raise ValueError(f"unknown operator {self.op}")


@dataclass(frozen=True)
class And(Expression):
    children: tuple[Expression, ...]

    def interpret(self, ctx: Context) -> bool:
        return all(child.interpret(ctx) for child in self.children)


@dataclass(frozen=True)
class Or(Expression):
    children: tuple[Expression, ...]

    def interpret(self, ctx: Context) -> bool:
        return any(child.interpret(ctx) for child in self.children)


@dataclass(frozen=True)
class Not(Expression):
    child: Expression

    def interpret(self, ctx: Context) -> bool:
        return not self.child.interpret(ctx)


def main() -> None:
    rule: Expression = And(
        (
            Compare("age", ">=", 18),
            Compare("country", "in", ("DE", "AT")),
        )
    )

    adult_de: Context = {"age": 21, "country": "DE"}
    minor_de: Context = {"age": 15, "country": "DE"}
    adult_us: Context = {"age": 30, "country": "US"}

    print(rule.interpret(adult_de))
    print(rule.interpret(minor_de))
    print(rule.interpret(adult_us))

    not_rule: Expression = Not(Compare("country", "==", "US"))
    print(not_rule.interpret(adult_us))


if __name__ == "__main__":
    main()
```

Output, identical in shape to the TypeScript run.

```
True
False
False
False
```

### Go

Go has no class inheritance, so the method-per-node variant becomes a small
`Expression` interface implemented by several structs, exactly the idiom Go
libraries use for this shape rather than a translation of the class diagram.

```go
package main

import "fmt"

type Context map[string]any

type Expression interface {
	Interpret(ctx Context) bool
}

type Compare struct {
	Field string
	Op    string
	Value any
}

func (c Compare) Interpret(ctx Context) bool {
	actual := ctx[c.Field]
	switch c.Op {
	case ">=":
		return actual.(int) >= c.Value.(int)
	case "==":
		return actual == c.Value
	case "in":
		for _, v := range c.Value.([]string) {
			if v == actual {
				return true
			}
		}
		return false
	default:
		panic("unknown operator " + c.Op)
	}
}

type And struct{ Children []Expression }

func (a And) Interpret(ctx Context) bool {
	for _, child := range a.Children {
		if !child.Interpret(ctx) {
			return false
		}
	}
	return true
}

type Or struct{ Children []Expression }

func (o Or) Interpret(ctx Context) bool {
	for _, child := range o.Children {
		if child.Interpret(ctx) {
			return true
		}
	}
	return false
}

type Not struct{ Child Expression }

func (n Not) Interpret(ctx Context) bool {
	return !n.Child.Interpret(ctx)
}

func main() {
	rule := And{Children: []Expression{
		Compare{Field: "age", Op: ">=", Value: 18},
		Compare{Field: "country", Op: "in", Value: []string{"DE", "AT"}},
	}}

	adultDE := Context{"age": 21, "country": "DE"}
	minorDE := Context{"age": 15, "country": "DE"}
	adultUS := Context{"age": 30, "country": "US"}

	fmt.Println(rule.Interpret(adultDE))
	fmt.Println(rule.Interpret(minorDE))
	fmt.Println(rule.Interpret(adultUS))

	notRule := Not{Child: Compare{Field: "country", Op: "==", Value: "US"}}
	fmt.Println(notRule.Interpret(adultUS))
}
```

Output, identical in shape to the other two.

```
true
false
false
false
```

All three samples compiled and ran, TypeScript via `tsc --strict` and `node`,
Python via `python3`, Go via `go run`, and produced the identical four-line
result shown above for each.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
   Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
   1994, chapter 3, Behavioral Patterns, Interpreter. Primary source for the
   pattern's name, intent, and canonical class structure.
2. [Wikipedia, "Interpreter pattern"](https://en.wikipedia.org/wiki/Interpreter_pattern),
   verified 2026-08-02. Secondary summary of the GoF intent, structure, and
   the SQL production example.
3. Robert Nystrom, *Crafting Interpreters*, Genever Benning, 2021, part two,
   "A Tree-Walk Interpreter." Online edition,
   [craftinginterpreters.com, "Representing Code"](https://craftinginterpreters.com/representing-code.html),
   verified 2026-08-02. Source for the Tree-Walking Interpreter alias, the
   Visitor pattern's role as the expression-problem fix, and the explicit
   statement that method-per-node dispatch is literally called the
   Interpreter pattern.
4. [Apache Commons JEXL, project overview](https://commons.apache.org/proper/commons-jexl/),
   verified 2026-08-02. Source for the JEXL production use and its explicit
   architectural rationale for tree-walking interpretation over bytecode
   compilation.
5. [jq manual](https://jqlang.org/manual/), verified 2026-08-02. Source for
   the jq production use and its filter composition model.
6. Russ Cox, "Regular Expression Matching Can Be Simple And Fast",
   [swtch.com/~rsc/regexp/regexp1.html](https://swtch.com/~rsc/regexp/regexp1.html),
   2007, verified 2026-08-02. Source for the backtracking regex engine
   production example and the tree-walking versus automaton-simulation
   performance comparison.
7. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018.
   Cross-referenced from the Factory Method entry in this catalog for the
   related discussion of static factories, not directly cited for a claim in
   this entry.

Engineering judgement, not independently sourced. The grammar creep failure
mode in dimension 11, the specific node-count and tree-depth budgeting
recommendation, and the resource-exhaustion limits in dimension 17 are drawn
from general production engineering practice with interpreters and rule
engines rather than from a single citable source, and are labelled as
judgement per this repository's dimension 11 convention.
