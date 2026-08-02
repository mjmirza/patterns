---
name: Interpreter
slug: interpreter
family: 01-gof
category: Behavioral
aliases: [Little Language, Expression Tree, Embedded DSL Evaluator]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [composite, visitor, flyweight, iterator, strategy, builder, specification]
incompatible_with: []
verified: 2026-08-02
---

# Interpreter

## 1. Name, aliases, and lineage

The canonical name is Interpreter. It is one of the eleven behavioral patterns in
the Gang of Four catalog, described in Erich Gamma, Richard Helm, Ralph Johnson
and John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented
Software*, Addison-Wesley, 1994, chapter 5 (Behavioral Patterns), Interpreter.
The book states the intent as follows. Given a language, define a representation
for its grammar along with an interpreter that uses the representation to
interpret sentences in the language
([GoF Interpreter reference text, University of North Carolina mirror](https://www.cs.unc.edu/~stotts/GOF/hires/pat5c.htm),
verified 2026-08-02).

Aliases in real use are less standardised than for most GoF patterns, because
the pattern is usually met under the name of the thing it produces rather than
under its own name.

- **Little Language.** The term predates the pattern and comes from the Unix
  tradition of small special-purpose notations. Practitioners who reach for
  Interpreter frequently describe the result as a little language rather than as
  an instance of the pattern.
- **Expression Tree.** The name used across the .NET ecosystem for the same
  structure. Microsoft's C# documentation states that expression trees represent
  code in a tree-like data structure where each node is an expression, for
  example a method call or a binary operation such as `x < y`
  ([Microsoft Learn, Expression Trees, C#](https://learn.microsoft.com/en-us/dotnet/csharp/advanced-topics/expression-trees/),
  verified 2026-08-02).
- **Embedded DSL Evaluator.** The name that appears when the grammar is not
  parsed from text at all but written directly in the host language, as with
  Django `Q` objects or SQLAlchemy expressions.

### The omission worth documenting

Interpreter is absent from most modern pattern catalogues aimed at working
developers. The most widely read of them, refactoring.guru, lists twenty-two of
the twenty-three GoF patterns. Its catalogue page names five creational
patterns, seven structural patterns, and ten behavioral patterns
(Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State,
Strategy, Template Method, Visitor). Interpreter is the single GoF pattern that
does not appear
([refactoring.guru design pattern catalog](https://refactoring.guru/design-patterns/catalog),
verified 2026-08-02).

That omission is not an oversight to be corrected. It is a fact about the
pattern's real place, and reading it correctly is more useful than restoring the
missing entry.

Three reasons account for it. First, the pattern's applicability window is
narrow in a way the other twenty-two are not. The GoF text itself limits it to
simple grammars and says plainly that for complex grammars the class hierarchy
becomes large and unmanageable, and that tools such as parser generators are a
better alternative in those cases (UNC GoF mirror, verified 2026-08-02). A
catalogue written for the median application developer can reasonably decide
that the median application developer should not be encouraged toward it.

Second, the pattern's payload has migrated into libraries. A developer in 1994
who wanted pattern matching over strings wrote an expression hierarchy. A
developer today calls a regular expression engine that already contains one.
The pattern did not stop being used. It stopped being hand-written by
application programmers, which is exactly what a successful pattern does.

Third, the pattern is difficult to demonstrate honestly in a short tutorial. A
convincing example needs a grammar, a parser to build the tree, an evaluation
context, and error handling. A short example that skips the parser and hands the
reader a manually constructed tree teaches the shape but hides the cost, and the
cost is where the design decision actually lives.

The consequence for a reader is a specific inversion. For most GoF patterns the
useful question is how to apply it. For Interpreter the useful question is
whether to apply it at all, and the answer is usually no. This entry is
organised around that fact.

## 2. Problem and context

A system has to make a decision, a computation, or a selection whose rule is not
known when the system is compiled. The rule is supplied later, by a user, by an
administrator, by a configuration file, by a database row, or by a caller who
composes it from parts.

Recognising the problem in a codebase is straightforward once the shape is
named. The symptoms are these.

A configuration column holds a string that the application parses on every
request with a chain of string splitting and conditionals. A permissions check
runs a hand-rolled evaluation of `role == admin OR (team == owner AND
project.public == false)` written as nested `if` statements that a product
manager keeps asking to change. A pricing engine has a method that grew from one
discount rule to forty, each one a branch. A search feature accepts a query
string from users and translates it into database predicates through a function
that is now the longest in the repository, and every new operator adds another
`else if`.

The common structure under all four is that the *rule* is data, the rule has
internal structure, and the rule has to be evaluated repeatedly against varying
inputs. String parsing on each evaluation is wasteful and error prone. A flat
conditional cannot express nesting. What the code needs is a representation of
the rule as objects, evaluated by walking that representation.

The context that makes Interpreter the right answer, rather than one of the
alternatives in dimension 4, has four parts.

- **The language is small and stable.** A dozen node types, not a hundred. If the
  grammar has recursion, precedence levels, statements, scoping, and type rules,
  the pattern is the wrong tool and dimension 4 explains what to reach for.
- **The same rule is evaluated many times.** Building a tree once and walking it
  many times pays back the construction cost. A rule evaluated once may as well
  be interpreted directly from its source text.
- **Evaluation speed is not the binding constraint.** The GoF applicability
  section is explicit here. The pattern suits situations where efficiency is not
  a critical concern, and it observes that the most efficient interpreters are
  usually not built by interpreting parse trees directly but by first
  translating them into another form (UNC GoF mirror, verified 2026-08-02).
- **The grammar changes more often than the evaluator's plumbing.** The pattern
  optimises for adding and changing rules. If instead the rules are fixed and
  the evaluation strategy keeps changing, a Visitor over a fixed node set fits
  better, see dimension 13.

Outside that context the pattern is an anti-pattern, and the failures it
produces are catalogued in dimension 11.

## 3. Forces

The pattern balances the following competing pressures. The entry states which
each is favoured and which each is sacrificed, because a pattern that gives up
nothing has been described wrongly.

- **Extensibility of the grammar.** Favoured, and this is the main reason to
  adopt the pattern. Adding an operator means adding one class that implements
  the expression interface. No existing class is edited. The GoF consequences
  section states that it is easy to change and extend the grammar, because
  inheritance lets rules be modified incrementally (UNC GoF mirror, verified
  2026-08-02).
- **Latency.** Sacrificed, and this is the main reason not to. Every evaluation
  is a recursive walk over heap-allocated nodes joined by pointers. Robert
  Nystrom's analysis of exactly this structure in *Crafting Interpreters* is
  that scattering data across the heap in a loosely connected web of objects
  harms spatial locality, and that each step following a reference to a child
  node may fall outside the cache and stall the processor while data is fetched
  from main memory
  ([Crafting Interpreters, chapter 14, Chunks of Bytecode](https://craftinginterpreters.com/chunks-of-bytecode.html),
  verified 2026-08-02). Dimension 8 covers what to do when this becomes binding.
- **Coupling.** Favoured between the caller and the rule. The caller depends on
  one expression interface and never on any concrete node type. Sacrificed
  inside the node set, because every node type has to agree on the shape of the
  evaluation method and on the shape of the context object, and changing either
  ripples to every node.
- **Cognitive load.** Sacrificed twice over. A reader has to hold two languages
  in mind, the host language and the interpreted one, and has to understand that
  a stack trace inside evaluation describes the shape of the *rule*, not the
  shape of the program. This is the cost that surprises teams most, because it
  lands on whoever is on call rather than on whoever wrote the code.
- **Consistency.** Favoured. Because every rule flows through one evaluator,
  semantics cannot drift between call sites the way they drift when each feature
  reimplements its own predicate logic.
- **Operability.** Mixed, and the mix is what makes the pattern worth its cost in
  some systems. The rule is a data structure, so it can be printed, hashed,
  compared, validated, versioned, and stored. That is far better than a rule
  buried in compiled conditionals. Against that, an error deep in a nested
  evaluation reports a node type and gives no indication of which part of the
  user's original text produced it, unless source positions were deliberately
  carried through, see dimension 16.
- **Cost.** Favoured over the long run when rules change weekly, because a rule
  change becomes a data change rather than a deployment. Sacrificed at adoption,
  because the first working version of an interpreter costs more than the
  conditional it replaces, and there is no partial credit for a half-built one.
- **Team topology.** Favoured, and this is often the real motivation even when it
  is not stated. The pattern draws a boundary where a platform team owns the
  node types and the evaluator, and other teams, or non-engineers, author rules
  in the resulting language. That boundary is why rules engines exist.
- **Safety.** Sacrificed sharply once the rule text comes from outside the trust
  boundary. An interpreter is an execution engine, and dimension 17 treats it as
  such.

## 4. Applicability and non-applicability

Reach for Interpreter when the following hold together. Any one of them alone is
not enough.

- The grammar of the rule language is small, closed, and slow-moving. A useful
  bound in practice is that the whole node set fits on one screen and a new
  engineer can name every node type after a day.
- The same rule is evaluated repeatedly against different inputs, so parsing once
  into a tree and walking the tree many times is cheaper than reparsing.
- Rules must be treated as data at rest. Stored in a database, diffed in review,
  versioned, shown back to a user, or authored by someone who does not deploy
  code.
- Combination matters. The value comes from composing small rules into larger
  ones with `and`, `or`, `not`, or a similar closed set of combinators, so that
  the composite has the same type as its parts.
- Multiple interpretations of the same tree are useful. Evaluating it, printing
  it, translating it to SQL, computing its cost. The tree becomes a shared
  representation rather than a private implementation detail, and Visitor takes
  over from there, see dimension 13.

Do NOT reach for Interpreter in the following cases. This list matters more than
the one above, because misuse of this pattern is more common than use of it.

- **The grammar is a real programming language.** Statements, scoping, functions,
  types, precedence tables, error recovery. The GoF applicability text is direct
  about this. For complex grammars the class hierarchy for the grammar becomes
  large and unmanageable, and parser generators are the better alternative (UNC
  GoF mirror, verified 2026-08-02). Use a parser generator or a hand-written
  recursive descent parser producing a plain AST, and keep evaluation out of the
  node classes. Dimension 12 compares the two directly.
- **The rule set is fixed and known at compile time.** If the rules cannot change
  without a deployment, the interpreter buys nothing that a plain function does
  not already provide, and it costs a class hierarchy plus an evaluation layer.
  Write the function.
- **The choice is a flat selection among a handful of behaviours.** One of five
  named strategies picked by an enum is Strategy, not Interpreter. Interpreter
  earns its cost only when rules *nest*.
- **Evaluation sits on a hot path with a tight budget.** A tree walk per request
  in an inner loop is a poor use of the pattern. Nystrom's point stands. The
  overhead of pointer chasing over scattered nodes is structural and cannot be
  optimised away while the representation stays a tree of objects (Crafting
  Interpreters, chapter 14, verified 2026-08-02). Compile the tree to a flat
  representation, or to a closure, or to bytecode, see dimension 8.
- **The host language already has a suitable expression facility.** In C#, LINQ
  expression trees exist, are compiler-generated from lambdas, and are consumed
  by libraries such as Entity Framework to translate a C# query into SQL that
  runs in the database engine (Microsoft Learn, Expression Trees, verified
  2026-08-02). Building a parallel node hierarchy beside them duplicates a
  facility the platform maintains.
- **The rule text comes from untrusted input and the node set is not restricted.**
  An interpreter over attacker-supplied text with nodes that can call arbitrary
  methods is a remote code execution primitive. If the pattern is used here it
  needs the controls in dimension 17, and if those controls cannot be
  implemented the pattern must not be used.
- **A single regular expression would do.** Text matching is the one place where
  the library form of this pattern is universally available. Reimplementing it
  as a node hierarchy is work with no return.
- **The team cannot support two languages.** The pattern creates a second
  language that needs documentation, error messages, tests, tooling, and an
  upgrade story. A team of three that already struggles to maintain one language
  will maintain the second one badly, and a badly maintained rule language is
  worse than the conditional it replaced because failures now occur in
  production data rather than at compile time.
- **The requirement is one-shot transformation, not repeated evaluation.** A
  migration script that reads a rule once and applies it once should parse and
  act, not build a tree.

## 5. Structure

Five participants, named by the role each plays.

- **AbstractExpression.** The interface that every node in the tree implements.
  It declares one operation, conventionally `interpret(context)`, that produces
  the node's contribution to the result. Its return type is the single most
  consequential design decision in the pattern, because it determines whether
  the language is typed, whether errors are values or exceptions, and whether
  evaluation can be lazy. Dimension 8 covers the choices.
- **TerminalExpression.** A leaf. It has no children and produces its result
  directly, from a literal it carries or from a lookup in the context. Literals,
  variable references, and constants are terminals. Terminals are usually
  immutable and are the natural candidates for sharing, see the Flyweight
  relationship in dimension 13.
- **NonterminalExpression.** An interior node. It holds one or more child
  expressions and produces its result by asking those children for theirs and
  combining them. Every operator, every combinator, every quantifier is a
  nonterminal. There is one nonterminal class per grammar rule, and that
  one-to-one mapping is both the pattern's clarity and its scaling limit.
- **Context.** The state that evaluation needs but the tree does not carry.
  Variable bindings, the input being matched, the current position in that
  input, accumulated output, a clock, a random source. Whether the context is
  mutable is the second consequential design decision, because a mutable context
  makes evaluation order observable and makes the tree unsafe to share across
  threads.
- **Client.** Builds or obtains the tree, supplies a context, and calls
  `interpret` on the root. The client is deliberately outside the pattern. The
  GoF description does not say how the tree is built, and the Wikipedia summary
  makes the same point, that the pattern does not describe how to build an
  abstract syntax tree and that this can be done manually by a client or
  automatically by a parser
  ([Wikipedia, Interpreter pattern](https://en.wikipedia.org/wiki/Interpreter_pattern),
  verified 2026-08-02). That omission is the source of the most common
  disappointment with the pattern, because the parser is usually the larger half
  of the work.

### The Composite relationship, made explicit

Interpreter does not describe a new structure. It describes a behaviour layered
onto a structure that Composite already provides, and the GoF text says so in
its Related Patterns section, that the abstract syntax tree is an instance of the
Composite pattern (UNC GoF mirror, verified 2026-08-02).

The mapping is exact and worth stating term by term, because seeing it removes
most of the mystery from the pattern.

| Composite role | Interpreter role | Shared property |
|---|---|---|
| Component | AbstractExpression | One interface for leaves and containers alike |
| Leaf | TerminalExpression | No children, produces a result on its own |
| Composite | NonterminalExpression | Holds children, delegates to them, combines results |
| `operation()` | `interpret(context)` | Uniform recursive operation over the whole tree |

The consequences carry over unchanged. Client code treats a single node and a
whole tree identically, which is what makes `and(a, or(b, c))` typecheck the
same way `a` does. Recursion terminates at leaves. Depth is unbounded unless
bounded deliberately, which is why unbounded nesting is a denial of service
vector in dimension 17.

The one property Interpreter adds beyond Composite is the context parameter.
Composite's uniform operation usually takes no argument and acts on state the
nodes already hold. Interpreter's operation takes the world it is being
evaluated against. That single parameter is what turns a static structure into a
language. Everything else about the structure is Composite, and an entry that
teaches Interpreter without teaching Composite first has skipped the foundation.

## 6. ASCII structure diagram

```
                    +-----------------------------+
   Client --------> |     AbstractExpression      |
   builds the tree, |-----------------------------|
   supplies Context | + interpret(Context): Result|
                    +-----------------------------+
                          ^                 ^
             implements   |                 |   implements
                          |                 |
   +-------------------------+     +------------------------------+
   |   TerminalExpression    |     |   NonterminalExpression      |
   |-------------------------|     |------------------------------|
   | - literal or var name   |     | - left : AbstractExpression  |
   | + interpret(ctx)        |     | - right: AbstractExpression  |
   |   returns directly      |     | + interpret(ctx)             |
   +-------------------------+     |   combines child results     |
                                   +------------------------------+
                                            |          |
                                    holds   |          |  holds
                                            v          v
                                     (any AbstractExpression,
                                      terminal or nonterminal)

   +-----------------------------+
   |          Context            |   passed down the whole walk.
   |-----------------------------|   Holds variable bindings, the
   | + lookup(name): Value       |   input under evaluation, and any
   | + input, position, output   |   accumulated state.
   +-----------------------------+

   The child aggregation is the Composite pattern. The Context
   parameter is the only part Interpreter adds on top of it.
```

## 7. Dynamics

Two flows matter and they happen at different times. Conflating them is the
source of the most common performance mistake with the pattern, which is
rebuilding the tree on every evaluation.

**Phase one, construction.** The rule text is turned into a tree. This happens
once per rule, ideally at startup or at the moment the rule is saved, never per
request. The GoF pattern does not cover this phase, so it is either a
hand-written parser, a parser generator, or direct construction in the host
language by a fluent builder.

**Phase two, evaluation.** The tree is walked with a context. This happens once
per input. It is a depth-first, post-order traversal. Each nonterminal asks its
children first, then combines.

```
Client        AndExpr        EqualsExpr      VarExpr      Context
  |              |                |             |            |
  |- parse("role == admin and active") --------------------->|
  |   (once, at rule save time)                              |
  |                                                          |
  |- interpret(ctx) -->|                                     |
  |              |     |                                     |
  |              |- interpret(ctx) ------>|                  |
  |              |     (left child)       |                  |
  |              |                        |- lookup("role") ->|
  |              |                        |<-- "admin" ------ |
  |              |<-- true ---------------|                  |
  |              |                                           |
  |              |   short circuit check: left was true,     |
  |              |   so the right child must be evaluated    |
  |              |                                           |
  |              |- interpret(ctx) --------------->|         |
  |              |     (right child, VarExpr)      |         |
  |              |                                 |- lookup("active")
  |              |                                 |<-- true |
  |              |<-- true ------------------------|         |
  |              |                                           |
  |<-- true -----|                                           |
  |                                                          |
```

Three properties of the flow are worth stating because they are where bugs
appear.

**Evaluation order is defined by the tree, not by the source text.** A reader
debugging a rule sees calls in post-order. The leftmost leaf reports first. If
error messages do not carry the original source position, the operator is left
matching a node type against a rule they wrote in a different order.

**Short circuiting is a node's own responsibility.** Nothing in the pattern makes
`and` stop early. A nonterminal that evaluates both children before combining
will evaluate the right side even when the left already decided the answer. When
children have side effects, or are expensive, or can fail, that difference is
observable behaviour rather than an optimisation. Decide it deliberately per
node and write it into the node's tests.

**Recursion depth equals tree depth.** A deeply nested rule produces a deep call
stack. On the JVM, in CPython, and in most runtimes without tail call
elimination, a sufficiently nested rule terminates the process with a stack
overflow rather than returning an error. This is the mechanism behind the denial
of service note in dimension 17, and the depth limit belongs in the parser, not
in the evaluator.

## 8. Implementation variants

**Evaluation method on the node.** The classical GoF form. Each node class
carries its own `interpret`. Advantage, adding a node type touches exactly one
file, which is the whole point of the pattern. Disadvantage, adding a second
*operation* over the tree, such as pretty printing or cost estimation, touches
every node class. This is the expression problem, and the standard escape is the
next variant.

**Visitor over a data-only node set.** Nodes carry structure and no behaviour.
Operations live in visitor classes. The GoF Related Patterns section points at
this directly, that Visitor can maintain the behaviour in each node in one class
(UNC GoF mirror, verified 2026-08-02). Advantage, a new operation is one new
class. Disadvantage, a new node type now touches every visitor. Choose by
guessing which axis will move more. Node types move more in an evolving rule
language, operations move more in a stable one. .NET's expression trees take
this route, and the documentation states plainly that expression trees are
immutable and that modifying one means building a new tree by copying the
existing one and replacing nodes, using an expression tree visitor to traverse
it (Microsoft Learn, Expression Trees, verified 2026-08-02).

**Closure compilation.** Instead of returning a result, each node's build step
returns a function that will produce the result when given a context. The tree
is walked once at compile time, and the resulting call graph of closures is what
runs per evaluation. This removes the per-node dispatch on node type and the
repeated field reads, and it is the highest-return single change available when
a tree walk is too slow while the pattern is otherwise the right shape. The
representation is still a graph of heap objects, so it does not fix locality,
but it removes a layer of interpretation. The cost is that the compiled form is
opaque. It can no longer be printed, diffed, or translated, which forfeits the
operability advantage from dimension 3.

**Compilation to a flat instruction sequence.** The tree is lowered into a linear
array of operations, evaluated by a loop over a stack. This is the standard
answer when performance becomes binding, and it is the transition Nystrom's book
is built around. His characterisation is that bytecode sits between a tree walker
and native code, keeping the portability of the tree walker and trading some
simplicity for a performance improvement, and that a dense linear sequence of
instructions keeps overhead low and works well with the cache (Crafting
Interpreters, chapter 14, verified 2026-08-02). At this point the design has
moved past the GoF pattern, and what remains is a compiler with a small virtual
machine. Dimension 12 treats that as a named alternative rather than a variant,
because the engineering commitment is different in kind.

**Fluent host-language construction with no parser.** The tree is built by method
calls or operator overloads in the host language rather than parsed from text.
This removes the entire parsing problem, gives compile-time checking of rule
structure for free, and gives editor completion. It is the form most production
libraries actually ship. Django `Q` objects are the clearest example. The Django
documentation states that `Q` objects can be combined with the `&`, `|`, and `^`
operators, that an operator applied to two `Q` objects yields a new `Q` object,
that a `Q` object can be negated with `~`, and that statements of arbitrary
complexity can be composed by combining `Q` objects with those operators and
parenthetical grouping
([Django 5.2 documentation, Making queries, Complex lookups with Q objects](https://docs.djangoproject.com/en/5.2/topics/db/queries/),
verified 2026-08-02). The limitation is that rules can no longer come from
outside the codebase, which forfeits the reason many teams adopt the pattern.

**Result type as a value rather than an exception.** `interpret` returns a result
type carrying either a value or an error, instead of throwing. Advantage, partial
evaluation becomes expressible, a rule can report every error rather than the
first, and a failure carries the node that produced it. Disadvantage, every
nonterminal now contains explicit propagation, which roughly doubles the size of
each node and makes the code less pleasant to read. Worth it for a rule language
authored by non-engineers, because those authors need every error at once.

**Immutable tree with an immutable context.** Nodes hold no mutable state and the
context is replaced rather than mutated as evaluation descends. Advantage, the
tree becomes safe to share across threads and to cache globally, which is what
makes the compile-once pattern viable in a server. Disadvantage, contexts that
change during evaluation, such as a matcher's position in an input string,
require threading a new context through every return, which the mutable form
gets without ceremony. Java's regular expression package resolves the same
tension by splitting the two. The `Pattern` documentation states that a regular
expression must first be compiled into an instance of that class, that the
resulting pattern is used to create a `Matcher` that can match arbitrary
character sequences, and that all of the state involved in performing a match
resides in the matcher, so many matchers can share the same pattern
([Java SE 21 API, java.util.regex.Pattern](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/regex/Pattern.html),
verified 2026-08-02). That split, an immutable shared tree plus a per-evaluation
mutable context, is the shape to copy.

**Interning of terminals.** Repeated literals and variable references are shared
rather than duplicated. The GoF Related Patterns section names this, that
Flyweight shows how to share terminal symbols within the abstract syntax tree
(UNC GoF mirror, verified 2026-08-02). It matters only when many similar trees
exist at once, for example one compiled rule per tenant across thousands of
tenants, and it requires the terminals to be immutable.

**Language notes.** The pattern translates cleanly to any language with subtype
polymorphism, so Java, C#, TypeScript, Python, Swift and Kotlin all take the
classical shape unchanged. Go has no inheritance but the pattern needs none, an
interface with one method plus structs that implement it is the whole
requirement, and Go's form is arguably cleaner than the Java one because there
is no base class to tempt anyone into putting shared behaviour in it. Rust takes
either a trait object form or, more idiomatically, an `enum` of node variants
plus a `match` in the evaluator, which trades open extension for exhaustiveness
checking and is usually the better trade for a closed grammar. In languages with
algebraic data types the `enum` form is preferred by convention, and it is worth
saying plainly that this form is not the GoF pattern, because extension by
adding a variant edits the evaluator rather than adding a class.

## 9. Known production uses

**Java regular expressions, `java.util.regex`.** A regular expression is compiled
once into a `Pattern` and matched many times through `Matcher` objects. The
class documentation states that `Pattern` is a compiled representation of a
regular expression, that a regular expression specified as a string must first be
compiled into an instance of the class, and that all of the state involved in
performing a match resides in the matcher so many matchers can share the same
pattern. Java SE 21 API specification, `java.util.regex.Pattern`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/regex/Pattern.html
verified 2026-08-02. This is the pattern in its purest production form. A small
closed grammar, compiled once, evaluated many times, with the immutable tree and
mutable context split from dimension 8.

**.NET expression trees, `System.Linq.Expressions`.** Code is represented as a
tree of expression node objects. The documentation states that expression trees
represent code in a tree-like data structure where each node is an expression,
that they represent code as a structure that can be examined, modified or
executed, that Entity Framework's LINQ APIs accept expression trees and use them
to translate a query written in C# into SQL that executes in the database
engine, and that a visitor is used to traverse a tree when producing a modified
copy. Microsoft Learn, "Expression Trees, C#",
https://learn.microsoft.com/en-us/dotnet/csharp/advanced-topics/expression-trees/
verified 2026-08-02. This is the multiple-interpretations case from dimension 4.
The same tree is compiled and run in process, or translated to SQL, or inspected
by a mocking library.

**Django `Q` objects.** A database predicate is an object, and predicates compose
into larger predicates. The documentation states that `Q` objects can be combined
using the `&`, `|` and `^` operators, that combining two of them yields a new `Q`
object, that they can be negated with `~`, and gives the example that
`Q(question__startswith="Who") | Q(question__startswith="What")` is equivalent to
the SQL clause `WHERE question LIKE 'Who%' OR question LIKE 'What%'`. Django 5.2
documentation, "Making queries", section "Complex lookups with Q objects",
https://docs.djangoproject.com/en/5.2/topics/db/queries/ verified 2026-08-02.
This is the SQL `WHERE` clause builder case, and it is a nonterminal set of
exactly three members over an open terminal set.

**SQLAlchemy Core expression language.** SQL statements are built as composable
Python objects rather than assembled as strings. The tutorial states that most
Python operators such as `==`, `!=`, `<` and `>=` generate new SQL Expression
objects rather than plain boolean values, that those objects are passed to
`Select.where()` to generate the WHERE clause, and that `select()` builds up a
statement using a generative approach where each method adds more state onto the
object. SQLAlchemy 2.0 documentation, "Using SELECT Statements",
https://docs.sqlalchemy.org/en/20/tutorial/data_select.html verified 2026-08-02.
The interesting property here is that the tree is never evaluated in Python at
all. It is translated to a target dialect, which is the Visitor variant from
dimension 8 rather than the classical one.

**Spring Expression Language.** A rule written as a string is parsed into an
expression object and evaluated against a context. The reference documentation
describes SpEL as an expression language supporting querying and manipulating an
object graph at runtime, and shows the three-participant shape directly.
`ExpressionParser` parses a string into an `Expression`, the `Expression` is
evaluated to produce a value, and the `EvaluationContext` is used during
evaluation to resolve properties, methods or fields and to help perform type
conversion. Spring Framework reference documentation, "Spring Expression
Language (SpEL)" and its "Evaluation" section,
https://docs.spring.io/spring-framework/reference/core/expressions/evaluation.html
verified 2026-08-02. Spring ships two context implementations, a restricted one
and a full-featured one, which is the security control described in dimension 17
implemented at the framework level.

**Drools rule language.** Business rules are authored in a text language and
matched against facts. The user guide gives the rule structure as a rule name, a
`when` block holding conditions, and a `then` block holding actions. Drools User
Guide 8.44.0.Final, "Rule Language Reference",
https://docs.drools.org/latest/drools-docs/drools/language-reference/index.html
verified 2026-08-02. Drools is the case where the pattern has been pushed past
its GoF limits deliberately and the cost paid in full. The condition side is not
walked naively per fact. It is compiled into a network so that shared conditions
across rules are evaluated once, which is precisely the translation into another
form that the GoF applicability section recommends for cases where efficiency
matters.

**Specification objects.** The pattern's analysis-level sibling. Eric Evans and
Martin Fowler describe specifications as a way to separate the statement of how
to match a candidate from the candidate object it is matched against, and the
composite form combines specifications with boolean operators. Eric Evans and
Martin Fowler, "Specifications", https://martinfowler.com/apsupp/spec.pdf
verified 2026-08-02 that the document resolves at that URL. Note on verification,
the PDF resolves but did not yield extractable text through the tooling used
here, so the description of its contents is corroborated against Eric Evans,
*Domain-Driven Design*, Addison-Wesley, 2003, where Specification is presented as
a pattern, as recorded by
[Wikipedia, Specification pattern](https://en.wikipedia.org/wiki/Specification_pattern),
verified 2026-08-02. A specification with `and`, `or` and `not` combinators and
an `isSatisfiedBy` method is Interpreter with a boolean result type and a single
terminal shape, and recognising that saves a team from designing it twice.

## 10. Consequences

Positive.

- Adding a grammar rule is adding one class. No existing class is edited, which
  is the Open Closed Principle applied to a language. The GoF consequences text
  makes this the first listed benefit, that it is easy to change and extend the
  grammar (UNC GoF mirror, verified 2026-08-02).
- Implementing each rule is mechanical. The GoF text observes that classes
  defining nodes have similar implementations, which means the second node type
  costs far less than the first and a new contributor can add one safely on
  their first week.
- Rules become inspectable data. They can be stored, versioned, diffed in code
  review, rendered back to the author, and compared for equality. A rule encoded
  in conditionals has none of these properties.
- One tree supports several operations. Evaluate it, print it, translate it to
  another language, estimate its cost, statically check it. This is the property
  that makes .NET expression trees carry both LINQ to Objects and LINQ to a
  database over the same representation.
- The authoring audience widens. Non-engineers can write rules in the resulting
  language without a deployment, which is the actual business case behind most
  rules engines.
- Testing is unusually easy for a behavioral pattern, because a node is a pure
  function of its children and the context. See dimension 15.

Negative.

- One class per grammar rule does not scale. The GoF consequences text says
  directly that complex grammars are hard to maintain, since the pattern defines
  at least one class for every rule and a grammar with many rules can be hard to
  manage.
- Evaluation is slow relative to compiled code, by construction and not by
  accident, for the pointer-chasing and cache reasons quoted in dimension 3.
- A second language now exists and needs everything a language needs.
  Documentation, error messages good enough for its authors, a test suite, a
  versioning story for stored rules, and someone who owns it.
- Debugging crosses a boundary. A stack trace describes the rule's shape rather
  than the program's, and without deliberate source position tracking there is no
  path from a failure back to the text the author wrote.
- Errors move from compile time to runtime, and often to production. A rule
  stored in a database is not type-checked by the compiler that built the
  application reading it.
- The parser is not provided. The pattern covers representation and evaluation
  and stops there, so the team owns the largest and least interesting part of the
  work.

## 11. Failure modes and misuse

Each entry gives the observable symptom first, because the abstract mistake is
not what an engineer encounters.

**The accidental programming language.** Symptom. The rule language has grown
variables, then conditionals, then a way to define reusable fragments, and the
issue tracker now contains a request for loops. Rule authors ask for a debugger.
The node count has passed forty and nobody can name them all. Cause. The
applicability bound in dimension 4 was crossed one small feature at a time, with
each step locally reasonable. Fix. Stop and choose deliberately between two
paths. Either freeze the language and refuse further features, writing that
refusal down as a design decision, or accept that a language is being built and
adopt the tools for one, a parser generator or a hand-written parser plus a
plain AST plus a separate evaluator, and budget accordingly.

**Reparsing on every request.** Symptom. A CPU profile where a large share of
time sits in parsing or tree construction rather than in evaluation, and latency
that grows with the length of the rule text rather than with the size of the
input. Cause. The two phases in dimension 7 were collapsed, so the tree is built
per call. Fix. Build once and cache the tree, keyed by the rule text or by the
rule's version identifier. This requires the immutable-tree variant from
dimension 8, because a cached tree is shared across concurrent requests.

**Shared mutable state in the tree.** Symptom. Intermittent wrong results under
load that never reproduce in a single-threaded test, and results that depend on
which request ran previously. Cause. A node caches something from the last
evaluation in a field, most often a memoised sub-result or a position counter.
Fix. Move every piece of per-evaluation state into the context, and make the node
fields final. The `Pattern` and `Matcher` split in Java's regex package is the
canonical shape here (Java SE 21 API, verified 2026-08-02).

**Stack overflow from a nested rule.** Symptom. The process terminates rather
than returning an error, on one specific stored rule, and the crash has no
useful application-level trace. Cause. Evaluation recursion depth follows tree
depth, and nothing bounded the depth at parse time. Fix. Impose a maximum nesting
depth in the parser and reject deeper rules with a clear message. Bounding at
evaluation time is later than needed and leaves the bad rule in storage.

**Silent short circuit mismatch.** Symptom. A rule with a side effect, such as
one that records an audit entry or increments a counter, fires more or fewer
times than the author expects, and the discrepancy depends on the order of the
operands. Cause. One nonterminal evaluates both children eagerly while another
short circuits, and the difference was never decided. Fix. Decide per node,
document it in the language reference, and add a test per node that asserts
whether the second child is evaluated when the first already determines the
result.

**The expression problem, discovered late.** Symptom. A change request to add
pretty printing turns into a pull request touching thirty node classes, and a
second one for cost estimation touches the same thirty. Cause. Behaviour was
placed on nodes when operations, not node types, were the moving axis. Fix.
Introduce a Visitor and migrate operations to it, keeping evaluation on the node
if that one operation is stable. Adding a visitor to an existing node set is a
mechanical refactor, and dimension 14 gives the steps.

**Untrusted rules with an unrestricted node set.** Symptom. A security finding,
or worse, an incident, in which a rule stored by a low-privilege user caused
method invocation or file access on the server. Cause. The node set includes a
node that can reach arbitrary host functionality, and the rule source was not
inside the trust boundary. Fix. Restrict the node set for untrusted sources, run
evaluation with a restricted context, and treat the full-featured context as a
privileged facility. Dimension 17 covers this properly.

**The one-rule interpreter.** Symptom. A package with nine classes, a parser, and
a test suite, used to evaluate a single predicate that has not changed since it
was written. Cause. The pattern was adopted for anticipated variation that never
arrived. Fix. Delete it and inline the predicate. This is speculative generality
and the refactoring path out is in dimension 14.

**Error messages that name node types.** Symptom. Rule authors file support
tickets asking what `NonterminalComparisonExpression cannot coerce` means, and
the support team's only recourse is to read the rule and guess. Cause. Source
positions were not carried on the nodes, so no error can point at the text.
Fix. Give every node the source span it was parsed from, and format errors
against the original text with a caret. This is inexpensive at parse time and
impossible to add retroactively without reparsing.

**Unbounded rule cache.** Symptom. Steadily growing heap in a long-running
process, retained by a map of rule text to compiled tree. Cause. The
compile-once fix above was applied without an eviction policy, and rule text
turns out to vary more than expected, often because it embeds a user-supplied
literal. Fix. Bound the cache, and key it on a rule identifier rather than on the
full text where an identifier exists.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3. The
alternatives are real approaches that a team would genuinely choose between, not
strawmen.

| Force | Interpreter (GoF) | Parser generator plus AST plus Visitor | Compile to bytecode or a VM | Strategy with a fixed set | Hard-coded conditionals | Host-language embedded DSL (Q objects, SQLAlchemy) |
|---|---|---|---|---|---|---|
| Grammar size supported | Small only, GoF says so | Large, that is its purpose | Large | One flat axis of choice | Small before it rots | Small to medium, bounded by host syntax |
| Adding a grammar rule | One new class, no edits | Edit the grammar file, regenerate, add a visitor case | Edit the grammar, the lowering step, and the VM | New strategy class, no nesting possible | Edit a conditional chain | New operator overload or method |
| Adding a new operation over the tree | Edits every node class | One new visitor, no node edits | Not the concern | Not applicable | Not applicable | One new translator |
| Latency of evaluation | Poor. Pointer chasing, cache misses | Poor if walked, same as Interpreter | Good. Linear instruction stream | Excellent. One virtual call | Excellent. Branches | Not evaluated in host, translated instead |
| Adoption cost | Medium. Nodes are easy, the parser is not | High. A toolchain plus a grammar to learn | Very high. A compiler and a VM to maintain | Very low | Lowest | Low. No parser at all |
| Rules authored outside the codebase | Yes, that is the point | Yes | Yes | No | No | No, rules live in code |
| Rules as inspectable data | Yes | Yes | Lost after lowering unless kept | No | No | Yes |
| Error message quality for rule authors | Poor by default, good with source spans | Good. Parser generators give position tracking | Good at compile time, poor at run time | Not applicable | Not applicable | Excellent. The host compiler reports it |
| Cognitive load | Medium. Two languages | High. Grammar notation plus generated code | Highest | Low | Lowest, until the chain grows | Low for host-language users |
| Operability | Tree can be printed and versioned | Same, plus a canonical grammar to point at | Poor. Bytecode is opaque | Trivial | Trivial | Good |
| Safety with untrusted input | Depends entirely on the node set | Same, plus a validated grammar | Same, plus sandboxing options | Safe | Safe | Safe, no external input |
| Team topology fit | Platform team owns nodes, others author rules | Same, with a steeper platform skill requirement | Requires a compiler-literate owner | Single team | Single team | Single team, engineers only |

Reading of the table. Interpreter occupies one narrow column and it is a real
one. Small grammar, rules from outside the codebase, evaluation speed not
binding. Move right on grammar size and the parser generator wins. Move down on
latency and the bytecode VM wins. Remove the need for external rule authors and
the embedded DSL wins on every remaining axis, which is why so many library
implementations of this pattern take that form. Remove nesting from the problem
entirely and Strategy wins, at a fraction of the cost.

## 13. Related and incompatible patterns

- **Composite.** The foundation, not a peer. Interpreter's tree *is* a Composite,
  as the GoF Related Patterns section states (UNC GoF mirror, verified
  2026-08-02). Dimension 5 gives the role-by-role mapping. The practical
  consequence is that Composite's guidance on uniform interfaces, on where to
  put child management, and on the safety versus uniformity trade applies to
  Interpreter without change. Read Composite first.
- **Visitor.** The standard partner and the standard escape. The GoF text names
  it as the way to keep behaviour for each node in one class rather than spread
  across the node hierarchy. Adopt it when operations over the tree outnumber
  changes to the node set. The two patterns together are how .NET expression
  trees support both execution and translation to SQL over one representation.
- **Flyweight.** A memory optimisation inside the tree, named in the same Related
  Patterns section as the way to share terminal symbols. Relevant when many trees
  coexist and share literals. It requires immutable terminals, so it composes
  with the immutable-tree variant and conflicts with any node that caches per
  evaluation state.
- **Iterator.** A traversal alternative. The GoF text notes that Iterator can be
  used to traverse the structure. In practice, external iteration over an
  expression tree is rare, because evaluation is recursive and post-order by
  nature, and flattening it into an iterator loses the natural combination step.
  Useful for analysis passes that only need to visit every node without regard
  to structure, such as collecting every variable name referenced.
- **Specification.** The same structure arrived at from domain modelling rather
  than from language design. Evans and Fowler present it as a way to separate the
  statement of how to match a candidate from the candidate itself
  ([Specifications, Evans and Fowler](https://martinfowler.com/apsupp/spec.pdf),
  URL verified 2026-08-02), and the composite form combines specifications with
  boolean operators (Wikipedia, Specification pattern, verified 2026-08-02). A
  team building composable specifications is building an Interpreter whose result
  type is boolean. Knowing that in advance gets the context object, the
  short-circuit decision, and the translation-to-SQL question onto the table
  early instead of after the third rewrite.
- **Strategy.** A substitute when the problem turns out not to nest. If the rule
  space is a flat choice among named behaviours, Strategy delivers it with one
  interface and no tree. A team that finds every rule in production is a single
  terminal with no combinators has built an Interpreter where a Strategy was
  wanted.
- **Builder.** A construction partner. The fluent host-language variant in
  dimension 8 is a Builder producing an expression tree, and separating the
  building interface from the node types keeps the nodes free of convenience
  methods that only the authoring path needs.
- **Command.** Frequently confused because both turn a request into an object.
  The distinction is composition and evaluation. A Command is executed for its
  effect and does not combine with other Commands into a larger Command of the
  same type. An expression node returns a value and composes. A Composite of
  Commands narrows the gap, and at that point the choice is a naming decision
  rather than a structural one.
- **Memento.** Sometimes needed alongside, not in conflict. When evaluation
  mutates the context and has to backtrack, as a regular expression matcher does
  on a failed alternative, the saved and restored context state is a Memento.
- **Template Method.** A minor partner. A common base nonterminal that implements
  the child traversal and leaves the combination step abstract is a Template
  Method, and it removes duplication across binary operators.
- **Singleton.** Conflicts in practice. A globally shared evaluator or context
  removes the per-evaluation isolation the pattern needs and produces the shared
  mutable state failure from dimension 11. If a single instance is genuinely
  wanted, share the immutable tree and never the context.

## 14. Refactoring path in and out

### Introducing the pattern

The starting point is code with a growing conditional chain over a rule that
wants to nest. Order matters, and each step keeps the tests green.

1. Name the language before writing a class. Write down the complete node set on
   one page, with an example of each. If the page does not fit, stop. That is the
   applicability bound from dimension 4 telling you the answer before you have
   spent anything.
2. Define the expression interface with one method and a deliberately chosen
   return type. Decide now whether errors are exceptions or values, and whether
   the context is mutable, because both decisions ripple to every node.
3. Extract the existing conditional chain's leaves into terminal nodes first.
   Literals and variable lookups. These have no children and are provable in
   isolation.
4. Add one nonterminal at a time, each with its own test, wiring it into the
   existing chain rather than replacing the chain. The chain and the tree
   coexist for as long as the migration needs.
5. Build the tree by hand in the host language before writing any parser. This
   validates the node set against real rules at a fraction of the cost, and if
   the fluent form turns out to be enough, the parser is never written at all.
   That is the outcome to hope for, see the embedded DSL variant in dimension 8.
6. Write the parser only when rules must come from outside the codebase. Carry
   source positions on every node from the first line of the parser, because
   retrofitting them means reparsing everything.
7. Move rule storage. Take rules out of code and into the database or config,
   with a version field, and add the compile-once cache from dimension 11.
8. Delete the original conditional chain and its tests, replacing them with tests
   that drive the same cases through the tree.

The named refactoring closest to steps three and four is Replace Conditional with
Polymorphism, applied once per grammar rule rather than once overall, see the
refactoring family entry. Step five is Introduce Builder. Step eight is Remove
Dead Code.

### Removing the pattern

Signals that it should go. The node set has one terminal and no combinators. No
rule has changed in a year. Every rule in production is one of four shapes.
Evaluation appears in the top three entries of a CPU profile and the language is
not going to shrink.

The path out differs by which signal fired.

If the language never varied, the path is collapse.

1. Query production for the distinct set of rules actually in use. This is the
   step teams skip, and it is the one that decides the rest.
2. If the distinct set is small and stable, write one named function per distinct
   rule and route by identifier.
3. Move call sites to the functions one at a time, keeping the interpreter as the
   fallback until the fallback is never taken. Instrument the fallback so the
   move is evidence-based rather than hopeful.
4. Delete the node classes, the parser, and the rule storage. This is Inline
   Class repeated, plus Replace Conditional with Polymorphism run backwards.

If the language is genuine and the problem is speed, the path is not removal but
lowering, and the pattern is kept at the authoring layer.

1. Keep the parser and the node set unchanged. They are the part that works.
2. Add a compilation step from the tree to closures, per dimension 8. Measure.
   This frequently recovers enough to end the exercise.
3. If it does not, add a lowering step from the tree to a flat instruction array
   and a loop-based evaluator. Keep the tree as the canonical form so printing,
   diffing and validation continue to work against it.
4. Keep both evaluators behind one interface and run them against each other on
   production rules until the outputs agree on every case. Differential testing
   is the only affordable way to trust the second implementation.

If the language is genuine and the problem is size, the path is out of the
pattern and into a parser generator, keeping the evaluator. The node classes
become plain data, the generated parser replaces the hand-written one, and a
Visitor replaces the evaluation method on each node.

## 15. Testing and verification

### Easier because of the pattern

- A node is a pure function of its children and its context. That makes a unit
  test for a node three lines and no mocking framework. Construct two stub
  children returning fixed values, construct the node, call `interpret` with a
  small context, assert the result. This is the strongest testability property
  the pattern offers and it is the reason a rule language can reach high coverage
  cheaply.
- Stub children are trivially written by hand. A `ConstantExpression` returning a
  fixed value doubles as a production node and a test double, so a project
  needing test doubles for expressions usually already has them.
- The tree is data, so tests can be table-driven over rule text and expected
  results, with the table stored beside the language documentation. Rule authors
  can read and extend the table without reading the implementation.
- Because the tree is comparable, a parser can be tested by asserting structural
  equality against a hand-built expected tree, separating parser bugs from
  evaluator bugs completely.

### Harder because of the pattern

- Coverage of the language is not coverage of the code. Every node class can be
  covered while combinations that appear in production are not. Node coverage is
  the wrong metric here and reporting it produces false confidence.
- Failures found in production are found in stored rules rather than in code, so
  a regression test has to import a rule fixture, which means rule fixtures need
  the same review discipline as code.
- Error paths multiply combinatorially. Every node can fail, and every parent has
  to handle a failing child, so the error behaviour of the language needs its own
  test strategy rather than incidental coverage.

### Techniques that apply

- **Property-based testing over generated trees.** Generate random well-formed
  trees from the node set and assert invariants. Evaluation terminates.
  Evaluation is deterministic for a fixed context. Printing a tree and reparsing
  the result yields an equal tree. This last one, the round-trip property, is the
  single highest-value test for a rule language because it catches parser and
  printer bugs together, and it is nearly free once a generator exists.
- **Differential testing against a reference.** When a second evaluator is added
  for speed, per dimension 14, run both over the same generated trees and assert
  identical results. Also applicable when replacing a hand-written parser with a
  generated one.
- **Golden-file tests for error messages.** The error text is part of the language
  contract for its authors, so freeze it. A change to an error message should be
  a deliberate diff in review, not an accident.
- **Contract test over the node interface.** One abstract test class asserting
  the properties every node must have, subclassed once per node type. Purity,
  no mutation of the context where the language says the context is immutable,
  and correct propagation of a failing child.
- **Fuzzing the parser.** The parser takes untrusted text in most deployments,
  so it is the right target for a fuzzer. The bug class to hunt is not a wrong
  parse, it is a crash, an unbounded allocation, or a stack overflow, which are
  the denial of service vectors from dimension 17.
- **Depth and size limit tests.** Assert that a rule exceeding the configured
  nesting depth is rejected at parse time with a clear message, and that the
  rejection happens before any allocation proportional to the input.

## 16. Observability signals

The pattern makes the rule invisible to a reader of the application source, so
the rule has to appear in telemetry or an incident cannot be diagnosed. This is
the same problem Factory Method has with the concrete product type, one level
larger, because here the hidden thing has internal structure.

What to record.

- **On compilation, one event per rule.** Rule identifier, rule version, node
  count, maximum depth, and compilation duration. This is low volume, one event
  per rule per process start, and it is the single most useful record because it
  proves which version of which rule the process is actually running.
- **On evaluation, a span or a counter labelled by rule identifier, never by rule
  text.** Rule text as a metric label produces an unbounded number of label
  values and will damage the metrics backend. Use a stable identifier or a hash.
- **A histogram of evaluation duration per rule identifier.** The distribution is
  what reveals a rule that is correct but pathological, which is common when
  authors are not engineers.
- **A counter of evaluation failures labelled by rule identifier and error kind.**
  Error kind means the language-level category, such as unknown variable or type
  mismatch, not the host exception class.
- **A counter of nodes visited per evaluation, or a sample of it.** This is the
  cheapest proxy for whether a rule is doing more work than its author intends,
  and it detects the short-circuit mismatch failure from dimension 11 without
  needing per-node instrumentation.
- **Cache statistics for the compiled-tree cache.** Hits, misses, evictions, and
  a gauge of entries. The eviction rate answers whether the cache key is right.
- **Parse rejections labelled by reason.** Depth exceeded, size exceeded, syntax
  error. A rising depth-exceeded count is either an author fighting a limit or an
  attacker probing one, and the two are distinguishable by source.

A healthy instance on a dashboard. The compilation event count matches the number
of active rules multiplied by the number of processes, and moves only on deploy
or on a rule change. Evaluation duration is flat and small relative to the
request it sits inside, with a tight distribution per rule. Nodes visited per
evaluation is stable per rule identifier. The compiled-tree cache hit rate is
near one, and the entry gauge is flat. Failures are near zero and concentrated in
whichever rule was last edited.

A failing instance. Compilation events appear continuously rather than at
startup, which means the compile-once cache is missing or its key varies, and
this shows up as evaluation latency that tracks rule text length. Or one rule's
duration histogram grows a long tail while its node count is unchanged, which
points at the context rather than the rule, usually a lookup that has become a
database call. Or nodes visited per evaluation doubles after a rule edit while
the result distribution is unchanged, which is a short circuit lost during the
edit. Or the cache entry gauge climbs monotonically, which is the unbounded rule
cache leak. Or parse rejections for depth exceeded rise sharply from one source
address, which is the denial of service probe in dimension 17 and warrants rate
limiting rather than a limit increase.

One practical note on tracing. Do not create a span per node. A rule of a hundred
nodes evaluated per request produces a trace that is unreadable and a tracing
bill that is not worth paying. One span per evaluation, with node count and depth
as attributes, carries the same diagnostic value at a thousandth of the cost.

## 17. Security and privacy implications

This is the dimension where Interpreter differs most from its neighbours in the
catalog, and where an entry that stays silent would be doing a disservice. Most
GoF patterns are close to neutral on security. This one builds an execution
engine, and the engine's attack surface is decided by the node set.

**The trust boundary question comes first.** Before any control below, answer one
question. Can the rule text be influenced by someone who is not trusted to run
code in this process. If the rules are authored only by engineers and shipped in
the repository, the pattern's security exposure is small and the remaining
paragraphs are largely precautionary. If rules are authored by customers,
administrators, or anyone whose input crosses a trust boundary, the interpreter
is a code execution feature and has to be treated as one.

**Node set restriction is the primary control.** The capability of the language
is exactly the union of what its nodes can do. A node that can invoke an
arbitrary method on an object reachable from the context turns the rule language
into a general-purpose one, and property access chains reach further than they
appear to, because one reachable object usually reaches many. Spring implements
this control at the framework level by shipping two evaluation contexts, a
restricted implementation supporting a subset of features and a full one
supporting the whole language (Spring Framework reference documentation,
Evaluation section, verified 2026-08-02). Copy the shape. Define the restricted
node set and the restricted context explicitly, make the restricted one the
default, and require a deliberate act to obtain the full one.

**Denial of service through evaluation cost.** A tree is a program and a program
can be made expensive. Three distinct vectors exist and each needs its own limit.
Depth, which produces stack exhaustion as described in dimension 7 and is bounded
at parse time. Breadth, where a rule with thousands of sibling terms is
individually cheap per node and expensive in aggregate, bounded by a node count
limit. And multiplicative cost, where a node evaluates its child repeatedly, for
example a repetition or a quantifier, so cost grows as a product rather than a
sum. The last one is where catastrophic backtracking in regular expressions comes
from, and it is the reason a regular expression accepted from a user is a denial
of service risk even though the engine is mature and well tested. Bound total
work with a step counter checked inside the evaluation loop, not with a wall
clock timeout alone, because a timeout does not stop the work it interrupts from
having already allocated.

**Untrusted rules must not read the whole context.** The context is the world the
rule sees. If it holds the current user, the request, a database session, and a
configuration object, then a rule language with property access is an arbitrary
read primitive over all of it. Build a separate, minimal context for untrusted
rules containing only the fields those rules are documented to use, rather than
passing the application's rich context and relying on the node set to restrain
access.

**Injection at the translation boundary.** When the tree is translated to another
language rather than evaluated, as SQLAlchemy and Entity Framework both do, the
security property comes from the translation producing parameters rather than
concatenated text. This is a genuine benefit of the pattern and worth stating
positively. An expression tree translated into a parameterised query is immune by
construction to the injection that string building invites. The property holds
only while every terminal becomes a parameter, so a node type that emits raw text
into the target language reopens the hole for the whole language, and any such
node needs review as a security boundary rather than as a convenience.

**Error messages leak structure.** A verbose evaluation error that names
properties, types, or values from the context tells an untrusted rule author
about the internals of the system they are running inside. That is useful to a
legitimate author and equally useful to an attacker probing the shape of the
context. Return detailed errors to trusted authors and a category plus a
correlation identifier to untrusted ones.

**On privacy.** The pattern is neutral in itself, with two practical caveats that
follow from dimension 16. First, rule text can contain personal data, because
authors write literals such as an email address or a customer identifier into
rules. Logging rule text on a parse error therefore writes personal data into
logs, so log the rule identifier and a redacted form rather than the source.
Second, a stored rule is a record of a business decision about a person, and in
jurisdictions with a right to an explanation for automated decisions, the tree is
the artifact that explains the decision. That is an advantage over conditionals
buried in compiled code, and it becomes one only if rule versions are retained
alongside the decisions they produced.

## Code examples

Three languages where the pattern is idiomatic in visibly different ways. Java
shows the classical form with an interface per node and evaluation on the node.
TypeScript shows the discriminated-union form plus constructor helpers. Python
shows the same structure with operator overloading, which is how Django `Q`
objects and SQLAlchemy expressions present themselves to their users.

Go is omitted because its version of the classical form is identical in shape to
the Java one with a struct in place of a class, which teaches nothing new. Rust
is omitted from the examples for a different reason worth stating. Its idiomatic
form is an `enum` of variants matched in a single evaluator function, which gives
exhaustiveness checking and loses the open extension that is the pattern's stated
benefit, so it is a different design rather than a translation. Dimension 8
records both.

All three examples implement the same small language. Boolean expressions over
named variables with `and`, `or`, `not`, and equality against a literal.

### Java

Classical form. One class per grammar rule, evaluation on the node, immutable
tree, read-only context.

```java
import java.util.Map;

interface Expr {
    boolean interpret(Map<String, String> ctx);
}

final class Equals implements Expr {
    private final String name;
    private final String literal;

    Equals(String name, String literal) {
        this.name = name;
        this.literal = literal;
    }

    public boolean interpret(Map<String, String> ctx) {
        return literal.equals(ctx.get(name));
    }
}

final class And implements Expr {
    private final Expr left;
    private final Expr right;

    And(Expr left, Expr right) {
        this.left = left;
        this.right = right;
    }

    // Short circuits deliberately. Documented, and tested for.
    public boolean interpret(Map<String, String> ctx) {
        return left.interpret(ctx) && right.interpret(ctx);
    }
}

final class Or implements Expr {
    private final Expr left;
    private final Expr right;

    Or(Expr left, Expr right) {
        this.left = left;
        this.right = right;
    }

    public boolean interpret(Map<String, String> ctx) {
        return left.interpret(ctx) || right.interpret(ctx);
    }
}

final class Not implements Expr {
    private final Expr inner;

    Not(Expr inner) {
        this.inner = inner;
    }

    public boolean interpret(Map<String, String> ctx) {
        return !inner.interpret(ctx);
    }
}

public final class Demo {
    public static void main(String[] args) {
        Expr rule = new And(
            new Equals("role", "admin"),
            new Not(new Equals("status", "locked")));

        Map<String, String> ctx = Map.of("role", "admin", "status", "active");
        System.out.println(rule.interpret(ctx));

        Map<String, String> locked = Map.of("role", "admin", "status", "locked");
        System.out.println(rule.interpret(locked));
    }
}
```

Expected output is `true` then `false`.

### TypeScript

The discriminated-union form, which is what a TypeScript codebase reaches for
when the grammar is closed, plus small constructor helpers that hide the node
shapes from callers.

```typescript
type Ctx = Record<string, string>;

type Expr =
  | { kind: "equals"; name: string; literal: string }
  | { kind: "and"; left: Expr; right: Expr }
  | { kind: "or"; left: Expr; right: Expr }
  | { kind: "not"; inner: Expr };

function interpret(e: Expr, ctx: Ctx): boolean {
  switch (e.kind) {
    case "equals":
      return ctx[e.name] === e.literal;
    case "and":
      return interpret(e.left, ctx) && interpret(e.right, ctx);
    case "or":
      return interpret(e.left, ctx) || interpret(e.right, ctx);
    case "not":
      return !interpret(e.inner, ctx);
  }
}

const eq = (name: string, literal: string): Expr =>
  ({ kind: "equals", name, literal });
const and = (left: Expr, right: Expr): Expr => ({ kind: "and", left, right });
const not = (inner: Expr): Expr => ({ kind: "not", inner });

const rule = and(eq("role", "admin"), not(eq("status", "locked")));
console.log(interpret(rule, { role: "admin", status: "active" }));
console.log(interpret(rule, { role: "admin", status: "locked" }));
```

The switch is exhaustive and the compiler proves it, so adding a node type
produces a compile error at the evaluator rather than a silent gap. That is the
opposite trade from the Java version, where adding a node type touches no
existing file and nothing checks that every operation handles it.

A second operation over the same tree, showing why the tree being data pays.

```typescript
function print(e: Expr): string {
  switch (e.kind) {
    case "equals":
      return `${e.name} == "${e.literal}"`;
    case "and":
      return `(${print(e.left)} and ${print(e.right)})`;
    case "or":
      return `(${print(e.left)} or ${print(e.right)})`;
    case "not":
      return `not ${print(e.inner)}`;
  }
}

console.log(print(rule));
```

### Python

Operator overloading, which is the form that Django `Q` objects and SQLAlchemy
expressions present to their users. The tree is built with `&`, `|` and `~`
rather than with constructor calls, so the rule reads as an expression in the
host language.

```python
from __future__ import annotations
from abc import ABC, abstractmethod


class Expr(ABC):
    @abstractmethod
    def interpret(self, ctx: dict[str, str]) -> bool: ...

    def __and__(self, other: Expr) -> Expr:
        return And(self, other)

    def __or__(self, other: Expr) -> Expr:
        return Or(self, other)

    def __invert__(self) -> Expr:
        return Not(self)


class Equals(Expr):
    def __init__(self, name: str, literal: str) -> None:
        self.name = name
        self.literal = literal

    def interpret(self, ctx: dict[str, str]) -> bool:
        return ctx.get(self.name) == self.literal


class And(Expr):
    def __init__(self, left: Expr, right: Expr) -> None:
        self.left = left
        self.right = right

    def interpret(self, ctx: dict[str, str]) -> bool:
        return self.left.interpret(ctx) and self.right.interpret(ctx)


class Or(Expr):
    def __init__(self, left: Expr, right: Expr) -> None:
        self.left = left
        self.right = right

    def interpret(self, ctx: dict[str, str]) -> bool:
        return self.left.interpret(ctx) or self.right.interpret(ctx)


class Not(Expr):
    def __init__(self, inner: Expr) -> None:
        self.inner = inner

    def interpret(self, ctx: dict[str, str]) -> bool:
        return not self.inner.interpret(ctx)


if __name__ == "__main__":
    rule = Equals("role", "admin") & ~Equals("status", "locked")
    print(rule.interpret({"role": "admin", "status": "active"}))
    print(rule.interpret({"role": "admin", "status": "locked"}))
```

The closure-compilation variant from dimension 8, in the same language, showing
the change in shape. The tree is walked once and the result is a callable.

```python
from typing import Callable

Compiled = Callable[[dict[str, str]], bool]


def compile_expr(e: Expr) -> Compiled:
    if isinstance(e, Equals):
        name, literal = e.name, e.literal
        return lambda ctx: ctx.get(name) == literal
    if isinstance(e, And):
        left, right = compile_expr(e.left), compile_expr(e.right)
        return lambda ctx: left(ctx) and right(ctx)
    if isinstance(e, Or):
        left, right = compile_expr(e.left), compile_expr(e.right)
        return lambda ctx: left(ctx) or right(ctx)
    if isinstance(e, Not):
        inner = compile_expr(e.inner)
        return lambda ctx: not inner(ctx)
    raise TypeError(f"unknown node: {type(e).__name__}")
```

Verification note. The Python examples were executed and produce `True` then
`False` for the classical form, and the compiled form produces the same results
for the same inputs. The Java and TypeScript examples were written against the
same logic and reviewed by hand but were not compiled in this environment, so
they are stated as reviewed rather than as executed.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Interpreter.
   Source of the intent, the five participants, the applicability limits on
   grammar size and efficiency, the consequences, and the Related Patterns links
   to Composite, Flyweight, Iterator and Visitor. Reference text verified against
   the University of North Carolina teaching mirror,
   https://www.cs.unc.edu/~stotts/GOF/hires/pat5c.htm verified 2026-08-02.
2. Refactoring.Guru. *Design Patterns Catalog*.
   https://refactoring.guru/design-patterns/catalog
   Verified 2026-08-02. Source for the claim in dimension 1 that this catalogue
   lists twenty-two GoF patterns and omits Interpreter.
3. Wikipedia contributors. "Interpreter pattern".
   https://en.wikipedia.org/wiki/Interpreter_pattern
   Verified 2026-08-02. Used to confirm the participant names and the statement
   that the pattern does not describe how the abstract syntax tree is built.
4. Robert Nystrom. *Crafting Interpreters*, chapter 14, "Chunks of Bytecode".
   https://craftinginterpreters.com/chunks-of-bytecode.html
   Verified 2026-08-02. Source for the analysis of tree-walking performance,
   pointer overhead per node, spatial locality, cache stalls, and the position of
   bytecode between a tree walker and native code.
5. Oracle. *Java SE 21 API Specification*, `java.util.regex.Pattern`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/regex/Pattern.html
   Verified 2026-08-02. Source for the compiled-pattern production use and for
   the immutable-tree plus mutable-matcher split in dimension 8.
6. Microsoft. *C# documentation*, "Expression Trees".
   https://learn.microsoft.com/en-us/dotnet/csharp/advanced-topics/expression-trees/
   Verified 2026-08-02. Source for the expression tree production use, the
   immutability and visitor-based modification, and the Entity Framework
   translation to SQL.
7. Django Software Foundation. *Django 5.2 documentation*, "Making queries",
   section "Complex lookups with Q objects".
   https://docs.djangoproject.com/en/5.2/topics/db/queries/
   Verified 2026-08-02. Source for the `Q` object production use and the operator
   composition with `&`, `|`, `^` and `~`.
8. SQLAlchemy authors. *SQLAlchemy 2.0 documentation*, "Using SELECT Statements".
   https://docs.sqlalchemy.org/en/20/tutorial/data_select.html
   Verified 2026-08-02. Source for the claim that Python comparison operators
   generate SQL expression objects rather than boolean values, and that those
   objects build the WHERE clause.
9. VMware Tanzu. *Spring Framework reference documentation*, "Spring Expression
   Language (SpEL)", Evaluation section.
   https://docs.spring.io/spring-framework/reference/core/expressions/evaluation.html
   Verified 2026-08-02. Source for the `ExpressionParser`, `Expression` and
   `EvaluationContext` shape, and for the two evaluation context implementations
   cited as a security control in dimension 17.
10. Drools project. *Drools User Guide 8.44.0.Final*, "Rule Language Reference".
    https://docs.drools.org/latest/drools-docs/drools/language-reference/index.html
    Verified 2026-08-02. Source for the DRL rule structure of name, `when`
    conditions and `then` actions.
11. Eric Evans, Martin Fowler. "Specifications".
    https://martinfowler.com/apsupp/spec.pdf
    URL verified 2026-08-02 to resolve and return the paper. The document body
    could not be extracted from the PDF by the tooling used here, so no direct
    quotation is made from it and the description of its content in dimensions 9
    and 13 is corroborated by reference 12.
12. Wikipedia contributors. "Specification pattern".
    https://en.wikipedia.org/wiki/Specification_pattern
    Verified 2026-08-02. Used to corroborate the attribution of the Specification
    pattern to Eric Evans and Martin Fowler, its presence in Evans,
    *Domain-Driven Design*, Addison-Wesley, 2003, and the composite form with
    and, or and not combinators over an `isSatisfiedBy` operation.
