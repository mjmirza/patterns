---
name: Free Monad
slug: free-monad
family: 16-functional
category: Functional
aliases: [Free, FreeM, Freer Monad, Operational Monad]
first_described: "Swierstra 2008, Voigtlaender 2008"
maturity: established
related: [functor, monad, applicative, tagless-final, interpreter, command, trampolining]
incompatible_with: [opaque-effect-stack, direct-style-io-only, performance-critical-hot-loop]
verified: 2026-08-02
---

# Free Monad

## 1. Name, aliases, and lineage

The canonical name is Free Monad. In software design, the name means a monad
generated from an instruction functor without adding domain behavior to the
monad itself. The usual shape is `Free f a`, where `f` describes one layer of
instructions and `a` is the result returned after the program finishes. Hackage
documents `Control.Monad.Free` as "The `Free` `Monad` for a `Functor` `f`" and
states the formal property in terms of monad homomorphisms from `Free f` to a
target monad and natural transformations from `f` to that target
(https://hackage.haskell.org/package/free-4.12.4/docs/Control-Monad-Free.html,
verified 2026-08-02).

The common aliases are **Free**, **FreeM**, **Freer Monad**, and
**Operational Monad**. The last two names are related but not identical to the
basic encoding. In ordinary architecture discussion, "free monad" usually
means an embedded program represented as data, smart constructors that lift
domain operations into that data, and one or more interpreters that fold the
program into a real effect or a pure model.

The lineage has two strands. The mathematical word "free" comes from algebra
and category theory: build the least structure that satisfies the requested
interface and imposes no extra equations beyond the laws of that interface.
The software pattern became widely visible through work on modular interpreters
and embedded languages. Wouter Swierstra's "Data types a la carte", published
in *Journal of Functional Programming* 18(4), pages 423 through 436, presents
a technique for assembling data types and functions from isolated components
and says the same technology can combine free monads to structure Haskell's IO
monad (https://www.cambridge.org/core/journals/journal-of-functional-programming/article/data-types-a-la-carte/14416CB20C4637164EA9F77097909409,
verified 2026-08-02). Janis Voigtlaender's "Asymptotic Improvement of
Computations over Free Monads" appeared in MPC 2008, LNCS 5133, pages 388
through 403, and focused on improving the performance of computations over
free monads (https://janis-voigtlaender.eu/papers.html, verified 2026-08-02).
Runar Oli Bjarnason later popularized the Scala angle in "Stackless Scala with
Free Monads", presented around Scala Days 2012
(https://apocalisp.wordpress.com/2012/05/15/stackless-scala-with-free-monads-2/,
verified 2026-08-02).

Typelevel Cats documents `Free[_]` as a way to represent stateful computations
as data, run recursive computations in a stack safe way, build embedded DSLs,
and retarget a computation to another interpreter by natural transformations
(https://typelevel.org/cats/datatypes/freemonad.html, verified 2026-08-02).
Those four uses explain why the pattern sits between functional programming,
interpreter, command, and architecture patterns rather than in only one family.

Judgement. The clearest operational test is this: if the program can be
inspected, transformed, logged, optimized, or interpreted in more than one
target before any effect occurs, the design has crossed from an ordinary
monadic effect into Free Monad territory.

## 2. Problem and context

A team has a domain language whose operations need to be composed in dependent
order, but the team also needs to delay the meaning of those operations. The
program should be a value before it is run. The same workflow may need a real
interpreter, a test interpreter, a trace interpreter, a dry run interpreter, an
authorization interpreter, or a compiler to another runtime.

The usual code smell appears as a service interface mixed with immediate
effects. A payment workflow calls a gateway, writes an audit row, asks a risk
service, and publishes an event. A document workflow reads a source, validates
it, emits warnings, and writes a transformed artifact. A database workflow
opens a connection, prepares a statement, binds parameters, reads rows, and
maps results. In direct style, every operation both describes the next action
and performs it. That makes unit tests slow, rewrites hard, and dry runs
awkward. It also ties the authoring language to one runtime: "run this in IO
now".

Free Monad separates the instruction vocabulary from the interpreter. The
domain author defines an instruction functor such as `Read`, `Write`, `Ask`,
`Tell`, `Get`, `Put`, or `Query`. Smart constructors lift those instructions
into `Free`. Application code composes them with `flatMap`, `bind`, `for`
syntax, `do` syntax, or callbacks. No instruction has operational meaning
until an interpreter folds the `Free` value into a target monad or runtime.

The context matters. Free Monad is not a way to make every function more
functional. It is a way to represent an effectful language as syntax. The
benefit arrives when syntax as data is valuable. That value may be testing,
multi-target interpretation, simulation, audit, retry planning, static
rewriting, or teaching a framework about operations without granting it the
right to perform those operations during construction.

There is also a modularity context. Swierstra's "Data types a la carte" attacks
the expression problem by composing independent functors and interpreters
(https://www.cambridge.org/core/journals/journal-of-functional-programming/article/data-types-a-la-carte/14416CB20C4637164EA9F77097909409,
verified 2026-08-02). Free Monad is one way to give such a composed instruction
set a monadic sequencing interface. The program author writes a normal
dependent flow, while the platform author can interpret each instruction set
separately.

Judgement. The strongest fit is a small embedded language with costly or
dangerous effects, where the team wants ordinary sequential composition at the
call site but explicit control at the boundary.

## 3. Forces

Judgement. The pattern balances the following pressures. It favors separation
of description from execution and pays for that separation with allocation,
indirection, and a steeper type story.

- **Coupling.** Favoured. Program authors depend on smart constructors and the
  result type, not on a concrete runtime. Interpreters depend on the instruction
  functor, not on every program.
- **Latency.** Sacrificed on hot paths. A naive free monad allocates one node
  per instruction plus bind nodes or continuations. Hackage notes that
  `Control.Monad.Free.Church` can improve asymptotic behavior for construction
  by reassociating bind use
  (https://hackage.haskell.org/package/free-4.12.4/docs/Control-Monad-Free.html,
  verified 2026-08-02).
- **Consistency.** Favoured when all effects pass through one interpreter.
  Authorization, tracing, retries, and resource policy can be placed in one
  fold instead of copied across call sites.
- **Operability.** Favoured if the interpreter emits instruction names and
  program ids. Sacrificed if the interpreter is opaque, because stack traces
  show an evaluator rather than the domain flow.
- **Cost.** Sacrificed for simple flows. The team must maintain instruction
  types, smart constructors, interpreters, and tests for interpreter laws.
- **Team topology.** Favoured when platform and product teams split work. One
  team can own the instruction vocabulary and runtime, while another authors
  workflows as data.
- **Cognitive load.** Sacrificed. Readers must understand `Functor`, `Monad`,
  lifting, interpretation, and the difference between syntax and semantics.
- **Change control.** Favoured for adding interpreters. Sacrificed for changing
  instruction constructors, because all interpreters must respond.

Free Monad also balances expression power against static analysis. It supports
dependent sequencing: later instructions can depend on earlier results. That is
more expressive than Free Applicative, but it hides the future program shape
behind previous results. A static analyzer can read the next suspended layer,
but cannot always know the whole operation tree without interpreting earlier
steps.

## 4. Applicability and non-applicability

Reach for Free Monad when these conditions hold.

- A domain workflow must be authored as a value before it runs.
- The same program needs two or more interpreters, such as production IO,
  in-memory test, dry run, tracing, migration preview, or code generation.
- The operation sequence is dependent: later commands need values returned by
  earlier commands.
- A framework should accept user programs without granting them immediate
  access to effects.
- You need a precise audit trail of domain operations rather than a trace of
  low-level calls.
- You are already using a functional language or library where higher-kinded
  types, natural transformations, or an equivalent encoding are normal.
- You need stack safe recursion through a trampoline-like evaluator. Cats lists
  stack safe recursive computations as one practical use of `Free`
  (https://typelevel.org/cats/datatypes/freemonad.html, verified 2026-08-02).

Do NOT reach for Free Monad in these cases.

- **There is one interpreter and no inspection need.** Direct calls, dependency
  injection, or a plain interface are easier to read and cheaper to run.
- **The workflow is independent, not dependent.** Use Free Applicative when all
  requested effects can be known before any result is available. It keeps more
  static structure.
- **The operation vocabulary changes every sprint.** Every new constructor
  touches every interpreter. A port interface or tagless final algebra may
  lower churn.
- **The team does not understand the host language type features.** A pattern
  that nobody can debug becomes architecture theater. Use a small command list
  plus a switch interpreter first.
- **The path is latency critical.** A tight parser inner loop, market data
  decoder, graphics frame path, or allocation-sensitive service may not have
  room for free structure allocation.
- **You need resource lifetime tied to lexical scope.** Free programs can model
  acquire and release, but direct bracket APIs or structured concurrency often
  express lifetime more clearly.
- **The target runtime already supplies a good effect system.** Cats Effect
  `IO`, ZIO, Effect TS, Kotlin coroutines, or Swift async code may give typed
  composition, cancellation, and test runtimes without a syntax tree.
- **You need full static optimization before values are known.** Free Monad
  permits dependent branching. Use an applicative request description, a query
  AST, or a planner DSL when the optimizer must see the whole graph up front.
- **The only goal is mocking.** A plain interface with a fake is smaller. Free
  Monad earns its keep when the program data has more than one use.

## 5. Structure

The pattern has six participants.

- **Instruction functor.** A parameterized algebra of one-step operations. Each
  constructor stores the data for one command and carries the continuation slot
  or result parameter needed for `map`.
- **Free program.** The recursive data structure. It is either a pure final
  value or one suspended instruction layer whose children are more free
  programs. Many libraries use a faster internal encoding, but the public idea
  remains "pure value or suspended instruction".
- **Smart constructor.** A function such as `readFile`, `put`, `ask`, or
  `query` that builds one instruction and lifts it into the free program type.
  It hides the raw instruction constructors from application code.
- **Program author.** Application code that combines smart constructors with
  `bind` or `flatMap`. This code describes a workflow and returns a program
  value.
- **Interpreter.** A natural transformation from the instruction functor to a
  target monad, or an equivalent function that consumes one instruction layer.
  The interpreter gives semantics to each command.
- **Runner.** The fold, evaluator, compiler, or runtime adapter that walks the
  free program, applies the interpreter, and returns the target computation.

The key relationship is one-way. Programs mention smart constructors. Smart
constructors mention the instruction functor and `Free`. Interpreters mention
the instruction functor and a target. Domain workflows do not mention sockets,
databases, file handles, mutable maps, or test doubles unless those concepts
are part of the instruction language.

The minimal algebraic shape can be written as two cases: `Pure(a)` and
`Suspend(freeLayer)`. Binding replaces each pure leaf with another program and
grafts the resulting structure into place. Hackage describes the practical view
as many layers of `f` wrapped around final values, with bind performing
substitution and grafting layers
(https://hackage.haskell.org/package/free-4.12.4/docs/Control-Monad-Free.html,
verified 2026-08-02).

## 6. ASCII structure diagram

```text
   +====================+        lift          +======================+
   | Instruction Functor| ===================> |     Free Program     |
   |====================|                      |======================|
   | Read(next)         |                      | Pure(value)          |
   | Write(text,next)   |                      | Suspend(f layer)     |
   | Query(sql,k)       |                      +==========+===========+
   +==========+=========+                                 |
              ^                                           | bind
              | map continuation                          v
   +==========+=========+                      +======================+
   |  Smart Constructors|                      |   Program Author     |
   |====================|                      |======================|
   | read(): Free       |                      | workflow(): Free A   |
   | write(x): Free     |                      +==========+===========+
   +====================+                                 |
                                                          | foldMap
                                                          v
   +====================+       natural        +======================+
   |    Interpreter     | ===================> |    Target Monad      |
   |====================|   transformation     |======================|
   | Read -> IO/String  |                      | IO, State, Either    |
   | Write -> IO/Unit   |                      | TestLog, Promise     |
   +====================+                      +======================+
```

## 7. Dynamics

At runtime, two phases are separated. The authoring phase builds a program
value. The interpretation phase consumes that value. No command has real-world
meaning until the second phase.

```text
Program code          Free builder          Free value          Interpreter
     |                    |                     |                    |
     | readUser           |                     |                    |
     |===================>|                     |                    |
     |                    | Suspend(Read k)     |                    |
     |<===================|                     |                    |
     | bind user -> load  |                     |                    |
     |===================>|                     |                    |
     |                    | FlatMap node        |                    |
     |<===================|                     |                    |
     | return program     |                     |                    |
     |=========================================>|                    |
     |                    |                     | foldMap            |
     |                    |                     |===================>|
     |                    |                     | Read instruction   |
     |                    |                     |===================>|
     |                    |                     | target effect      |
     |                    |                     |<===================|
     |                    |                     | continuation(user) |
     |                    |                     |===================>|
     |                    |                     | next instruction   |
     |                    |                     |===================>|
     |                    |                     | final target value |
     |<=============================================================|
```

The interpreter loop usually takes one evaluation step, sees either a final
value or a suspended instruction, interprets that instruction in the target
monad, then resumes with the next program. Cats exposes methods such as
`flatMap`, `resume`, and `foldMap` in its `Free` implementation source, and
its documentation presents `foldMap` as the operation that runs a free program
through a natural transformation
(https://github.com/typelevel/cats/blob/main/free/src/main/scala/cats/free/Free.scala,
verified 2026-08-02;
https://typelevel.org/cats/datatypes/freemonad.html, verified 2026-08-02).

Dynamics differ from an ordinary Command list in one way. The next command may
be a function of a previous result. That is why the continuation matters. A
program can read a user id, choose a tenant-specific query from that id, and
then choose a later branch from the row returned by the query. A static list
cannot express that without embedding callbacks or an interpreter-specific
state machine.

## 8. Implementation variants

**Naive recursive encoding.** The teaching form is `Pure a | Free (f (Free f
a))`. It is direct, easy to print, and easy to explain. It can perform poorly
with left-associated bind chains because each bind may walk existing structure.
Use it for small programs, documentation, and languages where flows are short.

**Gosub or continuation encoding.** The implementation stores binds as nodes
and reassociates them during evaluation. Scalaz documentation states that
binding is done using the heap rather than the stack, allowing tail-call
elimination (https://javadoc.io/static/org.scalaz/scalaz-core_3/7.4.0-M17/scalaz/Free.html,
verified 2026-08-02). Cats source also reassociates left-nested binds in
`step` and `resume`
(https://github.com/typelevel/cats/blob/main/free/src/main/scala/cats/free/Free.scala,
verified 2026-08-02). Use this when free programs may be long.

**Church encoded Free.** A Church encoding represents the fold rather than the
tree. Hackage points to `Control.Monad.Free.Church` for more efficient
construction and the `improve` combinator
(https://hackage.haskell.org/package/free-4.12.4/docs/Control-Monad-Free.html,
verified 2026-08-02). It is less transparent for inspection but better for
heavy bind construction.

**Coyoneda-assisted instruction functor.** Some instruction sets are awkward to
make `Functor`. Wrapping the instruction functor in Coyoneda can supply the map
machinery while keeping instruction constructors focused on operation data.
This is a judgement-based implementation tactic, not a sourced claim about a
specific library in this entry.

**Free transformer.** `FreeT f m a` combines a free instruction layer with a
base monad `m`. Use it when interpretation must be interleaved with a base
effect or when suspension itself is effectful. It raises complexity and should
not be the first encoding in a small DSL.

**Freer and extensible effects.** Freer encodings remove the explicit
`Functor f` requirement and represent requests with continuations. They often
lead toward effect systems. Use them when composing many independent effects is
more valuable than inspecting a simple instruction functor.

**Object-oriented command interpreter.** In Java, Go, TypeScript, and Python,
teams often encode the same design as command objects plus an interpreter
interface. The program is a command tree with continuations. It is not as
compact as higher-kinded `Free`, but it keeps the same architectural split.

Judgement. The variant choice should be made from the first operational use,
not from theory preference. If the main value is a second interpreter for
tests, start with the clearest encoding the team can inspect. If the main value
is long recursive control flow, start with a stack safe library encoding. If
the main value is combining many independently owned instruction families,
spend the design effort on algebra boundaries and naming before tuning the
runner. Most failed adoptions choose the hardest encoding first, then never
prove that program data is useful outside the production interpreter.

The following original examples are intentionally small and were run in this
repository session.

Python:

```python
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union

A = TypeVar("A")
B = TypeVar("B")

@dataclass(frozen=True)
class Pure(Generic[A]):
    value: A

@dataclass(frozen=True)
class Ask(Generic[A]):
    prompt: str
    cont: Callable[[str], "Program[A]"]

@dataclass(frozen=True)
class Tell(Generic[A]):
    text: str
    next: "Program[A]"

Program = Union[Pure[A], Ask[A], Tell[A]]

def bind(p: Program[A], f: Callable[[A], Program[B]]) -> Program[B]:
    if isinstance(p, Pure):
        return f(p.value)
    if isinstance(p, Ask):
        return Ask(p.prompt, lambda s: bind(p.cont(s), f))
    return Tell(p.text, bind(p.next, f))

def ask(prompt: str) -> Program[str]:
    return Ask(prompt, Pure)

def tell(text: str) -> Program[None]:
    return Tell(text, Pure(None))

def run_test(p: Program[A], answers: dict[str, str], log: list[str]) -> A:
    while True:
        if isinstance(p, Pure):
            return p.value
        if isinstance(p, Ask):
            p = p.cont(answers[p.prompt])
        else:
            log.append(p.text)
            p = p.next

program = bind(ask("name"), lambda n: tell("hello " + n))
out: list[str] = []
run_test(program, {"name": "Ada"}, out)
print(out[0])
```

Go:

```go
package main

import "fmt"

type Program interface{ isProgram() }

type Pure struct{ Value string }
func (Pure) isProgram() {}

type Ask struct {
	Prompt string
	Cont   func(string) Program
}
func (Ask) isProgram() {}

type Tell struct {
	Text string
	Next Program
}
func (Tell) isProgram() {}

func Bind(p Program, f func(string) Program) Program {
	switch v := p.(type) {
	case Pure:
		return f(v.Value)
	case Ask:
		return Ask{v.Prompt, func(s string) Program { return Bind(v.Cont(s), f) }}
	case Tell:
		return Tell{v.Text, Bind(v.Next, f)}
	default:
		panic("unknown program")
	}
}

func AskName(prompt string) Program {
	return Ask{prompt, func(s string) Program { return Pure{s} }}
}

func TellText(text string) Program {
	return Tell{text, Pure{""}}
}

func Run(p Program, answers map[string]string) []string {
	log := []string{}
	for {
		switch v := p.(type) {
		case Pure:
			return log
		case Ask:
			p = v.Cont(answers[v.Prompt])
		case Tell:
			log = append(log, v.Text)
			p = v.Next
		}
	}
}

func main() {
	p := Bind(AskName("name"), func(n string) Program { return TellText("hello " + n) })
	fmt.Println(Run(p, map[string]string{"name": "Ada"})[0])
}
```

Rust:

```rust
enum Program<A> {
    Pure(A),
    Ask(&'static str, Box<dyn Fn(String) -> Program<A>>),
    Tell(String, Box<Program<A>>),
}

fn bind<A: 'static, B: 'static>(
    p: Program<A>,
    f: std::rc::Rc<dyn Fn(A) -> Program<B>>,
) -> Program<B> {
    match p {
        Program::Pure(a) => f(a),
        Program::Ask(prompt, cont) => {
            let f2 = f.clone();
            Program::Ask(prompt, Box::new(move |s| bind(cont(s), f2.clone())))
        }
        Program::Tell(text, next) => Program::Tell(text, Box::new(bind(*next, f))),
    }
}

fn ask(prompt: &'static str) -> Program<String> {
    Program::Ask(prompt, Box::new(Program::Pure))
}

fn tell(text: String) -> Program<()> {
    Program::Tell(text, Box::new(Program::Pure(())))
}

fn run(mut p: Program<()>, answer: &str) -> Vec<String> {
    let mut log = Vec::new();
    loop {
        match p {
            Program::Pure(()) => return log,
            Program::Ask(_, cont) => p = cont(answer.to_string()),
            Program::Tell(text, next) => {
                log.push(text);
                p = *next;
            }
        }
    }
}

fn main() {
    let p = bind(ask("name"), std::rc::Rc::new(|n| tell(format!("hello {}", n))));
    println!("{}", run(p, "Ada")[0]);
}
```

## 9. Known production uses

**doobie.** doobie is a Scala functional JDBC layer. Its connection
documentation says that all doobie monads are implemented through `Free`, have
no operational semantics by themselves, and are run by transforming a `FooIO`
program to a monad with meaning. It also describes an interpreter from free
monads to `Kleisli[M, Foo, ?]` given `Async[M]`
(https://typelevel.org/doobie/docs/03-Connecting.html, verified 2026-08-02).
This is a direct production-grade use: JDBC operations are described as
programs and later interpreted against Java SQL carrier objects.

**Typelevel Cats.** Cats publishes a `cats-free` module for free structures,
including the free monad, and documents a key-value DSL that is compiled by a
natural transformation using `foldMap`
(https://typelevel.org/cats/datatypes/freemonad.html, verified 2026-08-02).
The source for `cats.free.Free` contains the public `Free[S, A]` type and
operations such as `flatMap`, `resume`, and `foldMap`
(https://github.com/typelevel/cats/blob/main/free/src/main/scala/cats/free/Free.scala,
verified 2026-08-02). Cats is a widely used functional programming library for
Scala, and its `Free` type is the standard Scala library implementation many
projects learned from or depended on.

**Haskell `free` package.** The Hackage package `free` provides
`Control.Monad.Free`, `Control.Monad.Free.Church`, free applicatives, and
related structures. Its documentation defines `data Free f a` and lists
interpreting functions such as `iter`, `iterM`, `retract`, and `hoistFree`
(https://hackage.haskell.org/package/free-4.12.4/docs/Control-Monad-Free.html,
verified 2026-08-02). The Haskell Communities and Activities Report for May
2014 reported the `free` package as actively developed and described it as
providing common definitions for free monads and free applicatives useful for
EDSLs (https://www.haskell.org/communities/05-2014/html/report.html, verified
2026-08-02).

**PureScript examples and library ecosystem.** *PureScript by Example* uses the
`free` library in a chapter on domain-specific languages, states that `Free`
can turn any `Functor` into a `Monad`, and builds an HTML content DSL whose
representation is separated from interpretation
(https://book.purescript.org/chapter14.html, verified 2026-08-02). This is a
named ecosystem use rather than a single product deployment, but it is a real
library-backed teaching and practice path for PureScript DSL construction.

Judgement. doobie is the strongest evidence in this list because the source
ties the pattern to a concrete runtime boundary, JDBC. Cats, Haskell `free`,
and PureScript `free` show the pattern's library-level maturity across
languages.

## 10. Consequences

Positive consequences.

- Programs become data. They can be stored, printed, analyzed, rewritten, or
  interpreted later.
- Effects move to interpreters. The construction phase can stay pure, which
  gives tests a smaller surface.
- Multiple targets are natural. A program can run against IO, state, logs,
  mocks, remote calls, or code generation by changing the interpreter.
- Domain APIs become small. Users call smart constructors rather than manually
  constructing operation trees.
- Cross-cutting policy can sit in one evaluator. Logging, retries, limits, and
  authorization checks can be attached to instruction handling.
- Recursive flows can be stack safe when the implementation uses a trampoline,
  Gosub, Church encoding, or another reassociation technique. Cats and Scalaz
  both expose stack-oriented implementation details in their Free material
  (https://typelevel.org/cats/datatypes/freemonad.html, verified 2026-08-02;
  https://javadoc.io/static/org.scalaz/scalaz-core_3/7.4.0-M17/scalaz/Free.html,
  verified 2026-08-02).

Negative consequences.

- Allocation rises. Each operation is a node or continuation, and each bind may
  add another layer.
- Type signatures become harder for newcomers. The result may mention
  higher-kinded types, natural transformations, coproducts, and type lambdas.
- Debugging can move away from domain stack traces toward interpreter loops.
- Error handling may become split across the instruction algebra, the target
  monad, and interpreter exceptions.
- Static analysis is limited for dependent programs. A later instruction may
  not exist until an earlier result is interpreted.
- Boilerplate grows. Each operation usually needs a constructor, functor map,
  smart constructor, production interpreter case, test interpreter case, and
  documentation.
- Law violations are subtle. If `map`, `bind`, or an interpreter breaks its
  expected laws, small refactors can change behavior.

Judgement. Free Monad is an architecture pattern with real carrying cost. It
should make an operational boundary clearer. If it only makes a local function
look more abstract, remove it.

## 11. Failure modes and misuse

Judgement. The following are production failure modes stated as observable
Symptom, Cause, Fix triples.

**Symptom.** A simple request path allocates heavily and shows more time in the
free evaluator than in domain work. **Cause.** The team used naive `Free` for a
hot loop or a long left-associated bind chain. **Fix.** Move the hot path to a
direct interpreter, use a Church or Gosub encoding, or collapse the local
language into a specialized data structure.

**Symptom.** A test interpreter passes but production fails with missing
authorization, tracing, or retry behavior. **Cause.** Interpreters drifted and
the tests validated only program shape, not interpreter parity. **Fix.** Add
shared interpreter conformance tests over the instruction algebra, and run a
small golden program through each interpreter.

**Symptom.** A new instruction takes days because every interpreter must be
edited across repositories. **Cause.** The instruction vocabulary is too
volatile for a closed algebra. **Fix.** Split the algebra by ownership, use
coproduct composition, or switch to a port interface where the unstable part is
owned locally.

**Symptom.** Logs show `foldMap`, `resume`, or `runFree` with no useful domain
name. **Cause.** The interpreter emits technical events instead of instruction
events. **Fix.** Add operation names, program ids, input sizes, and target
names at the interpreter boundary.

**Symptom.** A dry run says an operation is safe, then production performs
different calls. **Cause.** The dry run interpreter approximates semantics
instead of sharing validation code with the real interpreter. **Fix.** Put
validation in a shared interpreter layer or make the dry run return a plan
compiled from the same instruction cases.

**Symptom.** A code reviewer cannot tell where an effect happens. **Cause.**
Smart constructors, interpreters, and runners are spread across unrelated
modules with no naming convention. **Fix.** Co-locate each instruction family
with its smart constructors and interpreter contracts, then place runners at
system boundaries.

**Symptom.** A static analyzer misses a later query or command. **Cause.** The
program is monadic, and later commands depend on earlier results. **Fix.** Use
Free Applicative for analyzable requests, or restrict the DSL so branches are
explicit data.

**Symptom.** Error messages mention erased casts or impossible cases. **Cause.**
The host language cannot express the result type of each instruction cleanly,
so the interpreter uses unchecked casts. **Fix.** Use a GADT-capable language,
encode typed operations with witnesses, or lower expectations and use an
untyped command language with validation.

## 12. Trade-off matrix

<table>
<thead>
<tr><th>Force</th><th>Free Monad</th><th>Tagless Final</th><th>Free Applicative</th><th>Command List</th><th>Direct IO</th></tr>
</thead>
<tbody>
<tr><td>Coupling</td><td>Program syntax decoupled from runtime</td><td>Algebra decoupled through type classes or interfaces</td><td>Requests decoupled from runtime</td><td>Commands decoupled if list is pure</td><td>Callers know runtime</td></tr>
<tr><td>Latency</td><td>Higher allocation unless optimized</td><td>Low overhead after inlining</td><td>Usually lower than monadic Free</td><td>Low for simple lists</td><td>Lowest</td></tr>
<tr><td>Consistency</td><td>Central interpreter can govern policy</td><td>Each instance governs policy</td><td>Central interpreter sees whole request graph</td><td>Central interpreter can govern policy</td><td>Policy scattered unless wrapped</td></tr>
<tr><td>Operability</td><td>Good if instructions are named</td><td>Good if instances log well</td><td>Strong for pre-run plans</td><td>Good for linear plans</td><td>Native stack traces</td></tr>
<tr><td>Cost</td><td>High type and boilerplate cost</td><td>Medium type cost</td><td>Medium boilerplate cost</td><td>Low type cost, lower expressiveness</td><td>Low pattern cost</td></tr>
<tr><td>Team topology</td><td>Strong for platform-owned DSLs</td><td>Strong for library-owned algebras</td><td>Strong for request planning teams</td><td>Good for small teams</td><td>Good for single owner</td></tr>
<tr><td>Cognitive load</td><td>High</td><td>Medium to high</td><td>Medium</td><td>Low</td><td>Low</td></tr>
<tr><td>Static analysis</td><td>Partial due dependent binds</td><td>Weak unless algebra records calls</td><td>Strong because graph is known</td><td>Strong for fixed lists</td><td>Weak</td></tr>
<tr><td>Adding operations</td><td>Requires interpreter updates</td><td>Requires instance updates</td><td>Requires interpreter updates</td><td>Requires switch updates</td><td>Requires call-site edits</td></tr>
<tr><td>Adding runtimes</td><td>Natural via new interpreter</td><td>Natural via new instance</td><td>Natural via new interpreter</td><td>Natural via new interpreter</td><td>Often invasive</td></tr>
</tbody>
</table>

Judgement. Free Monad sits between a full AST and a direct effect API. It is
best when the program needs dependent sequencing and later interpretation. If
the program can be planned without dependent results, Free Applicative is often
cleaner. If no program data is needed, Tagless Final or Direct IO is smaller.

## 13. Related and incompatible patterns

**Monad** is the base abstraction. Free Monad supplies a monad from an
instruction functor and gives bind semantics without requiring the instruction
author to write a domain-specific monad instance.

**Functor** is the input requirement in the classic encoding. The instruction
functor must be mappable so continuations can be rewritten under each suspended
instruction. Libraries may hide the mapping machinery, but the idea remains.

**Interpreter** is the closest behavioral partner. A free program is syntax,
and an interpreter supplies semantics. Without at least one interpreter, a free
program is inert data.

**Command** relates at the instruction level. Each instruction constructor is a
typed command. Free Monad differs by making the result of a command feed the
continuation of the program.

**Free Applicative** is a sibling, not a weaker version. It represents
independent effects and supports stronger static analysis. Use it when later
steps do not depend on earlier values.

**Tagless Final** often replaces Free Monad. It represents operations as an
interface or type class interpreted directly into a target effect. It reduces
allocation and boilerplate but gives up ordinary syntax tree inspection unless
the chosen instance builds data.

**Trampolining** composes with Free Monad. Bjarnason's "Stackless Scala with
Free Monads" connects free monads to stack safe sequencing in Scala
(https://apocalisp.wordpress.com/2012/05/15/stackless-scala-with-free-monads-2/,
verified 2026-08-02). Use the trampoline angle when stack safety is the main
concern.

**Monad Transformer** may conflict with Free Monad if both are used to model
the same effect stack. A small transformer stack can be clearer for ordinary
effects. FreeT can combine the worlds, but it raises the reader burden.

**Opaque effect stack** is incompatible when the goal is inspection. If all
effects are hidden inside a single `IO` or `Task` value, the program can run
but cannot be read as domain syntax.

## 14. Refactoring path in and out

To introduce Free Monad:

1. Identify an effect boundary with repeated operations and at least two
   plausible interpreters.
2. Name the instruction vocabulary. Keep the first algebra small, often five
   commands or fewer.
3. Define the instruction functor or command cases. Each case should represent
   one domain operation, not one low-level library call.
4. Add smart constructors that return the free program type. Hide raw
   constructors if the host language permits it.
5. Rewrite one workflow to return a program value rather than running effects.
6. Write a production interpreter that targets the existing runtime.
7. Write a test or dry run interpreter that proves the separation has value.
8. Add observability at the interpreter boundary before converting more
   workflows.
9. Convert call sites in small slices. The refactoring family entry "Extract
   Function" applies when lifting effectful blocks into smart constructors, and
   "Replace Conditional with Polymorphism" may apply when a large interpreter
   switch becomes separate interpreters by target.

To remove Free Monad:

1. Count real interpreters. If only one remains, mark the pattern as suspect.
2. Inline smart constructors into a port interface or service method while
   preserving operation names in logs.
3. Replace free programs with direct calls in one workflow.
4. Keep the test interpreter behavior as contract tests for the direct service.
5. Delete unused instruction cases after all workflows move.
6. Remove the runner last, because it is the system boundary and carries
   observability.

Judgement. The best migration in either direction keeps the instruction names
stable. Names such as `ChargeCard`, `LoadAccount`, or `PublishEvent` are
domain assets even if the encoding changes.

## 15. Testing and verification

Judgement. Free Monad improves testing only when teams test both the program
data and the interpreters. Testing only smart constructors gives false
confidence.

Test the instruction functor. Verify that mapping over an instruction changes
only the continuation and not the command payload. For GADT-like encodings,
check that result witnesses survive interpretation.

Test smart constructors. A smart constructor should build exactly one
instruction, carry the right payload, and return the expected result into the
continuation. Golden structure tests work well for small languages.

Test program shape. For domain workflows, run the program through a recording
interpreter and assert the instruction sequence, payload classes, and branch
decisions. Avoid asserting private `Free` node shapes if the library reserves
the right to change encodings.

Test interpreter conformance. Build a small suite of shared programs and run
them through every interpreter. Compare observable behavior: output values,
log entries, state changes, errors, retries, and resource cleanup.

Test laws where the host ecosystem supports it. Haskell, Scala, and PureScript
ecosystems often have law-checking tools for `Functor`, `Applicative`, and
`Monad` instances. The repository's Monad entry cites Haskell `Control.Monad`
for monad laws, and those laws matter here because Free exposes a monadic
interface (https://hackage.haskell.org/package/base/docs/Control-Monad.html,
verified 2026-08-02).

Test failure paths. Interpreters must be tested for command rejection,
downstream failure, cancellation, timeouts, and cleanup after partial progress.
The free program itself does not solve those behaviors. The target monad and
interpreter own them.

The examples in dimension 8 were verified in this session with `python3`,
`go run`, and `rustc`. That verification checks syntax and basic behavior, not
the correctness of any library implementation.

## 16. Observability signals

Judgement. A healthy Free Monad deployment makes the interpreted language
visible, not the implementation mechanics.

Log one event per interpreted instruction when volume permits. Include program
name, program id, instruction name, interpreter name, target runtime, tenant or
account key when allowed, result class, elapsed time, and failure class. Redact
payloads by instruction type.

Trace the runner as a span with child spans for expensive instructions. The
span name should be the domain program, such as `billing.charge_customer`, not
`free.fold_map`. Child span names should be instruction names, such as
`LoadInvoice`, `AuthorizeCard`, and `WriteAudit`.

Measure program length. Track instruction count, bind depth when available,
maximum continuation depth, and interpreter step count. A rising p95 length may
explain latency or memory growth before service-level metrics fail.

Measure interpreter split. For each program, record which interpreter ran:
production, test, dry run, replay, migration, or simulation. This prevents dry
run data from being mistaken for real effects and helps incident review.

Measure allocation and evaluator time when the runtime exposes them. The
pattern can hide allocation behind a clean API. A dashboard should show whether
time is spent in domain targets, such as database and network calls, or in free
program construction and interpretation.

Healthy signs: stable instruction count per workflow, low interpreter error
rate, clear trace names, and similar behavior across test and production
interpreters. Failing signs: many unknown instruction names, large programs in
latency-sensitive paths, interpreter exceptions without domain context, or
branch counts that drift after a release.

One useful dashboard splits time into construction, interpretation overhead,
and target work. Construction covers smart constructors and bind allocation.
Interpretation overhead covers runner steps, continuation dispatch, and any
generic policy layer. Target work covers database calls, file IO, network IO,
or pure state updates performed by the interpreter. This split tells the team
whether the pattern itself is costing the request or whether the interpreted
operations dominate. It also gives a migration signal: when interpretation
overhead stays near zero and target work dominates, the pattern is probably not
the latency problem. When interpretation overhead grows with program length and
target work stays flat, the team should evaluate a different encoding or move
that workflow out of Free.

## 17. Security and privacy implications

Judgement. Free Monad is not a security pattern, but it changes where security
policy can be placed.

The benefit is a single interpretation boundary. Authorization checks,
redaction, rate limits, tenant scoping, and audit events can be applied when an
instruction is interpreted. A production interpreter can refuse commands that a
test interpreter accepts, but that split must be deliberate and documented.

The risk is that programs are data. If free programs can be serialized,
queued, logged, replayed, or accepted from another process, they become an
input language. Treat them like requests. Validate version, tenant, operation
set, payload size, and allowed interpreter before running. Never treat a
serialized free program from an untrusted source as harmless because it is
"only data".

Privacy risk concentrates in instruction payloads. A `Query` instruction may
carry SQL text. A `SendEmail` instruction may carry addresses and message
content. A `WriteAudit` instruction may carry user identifiers. Observability
must log instruction names and safe metadata rather than raw payloads by
default.

Replay is another risk. A free program that represents effects can be run more
than once unless the interpreter prevents it. For payments, messages, file
writes, and database mutations, interpreters should use idempotency keys,
deduplication, or explicit replay guards.

Capability leakage can occur when an interpreter exposes a broad runtime to a
small DSL. The interpreter should translate only known instruction cases, not
hand the program author a general database connection, shell, or HTTP client.

Free Monad is silent on cryptography, memory safety, transport security, and
access control models. Those concerns belong to the target runtime and
interpreter. The pattern gives a place to enforce policy, but it does not
define the policy.

## 18. References

- Hackage. `Control.Monad.Free`, package `free-4.12.4`. Defines `Free f a`,
  `liftF`, `iter`, `iterM`, `hoistFree`, and describes the formal free monad
  property. https://hackage.haskell.org/package/free-4.12.4/docs/Control-Monad-Free.html,
  verified 2026-08-02.
- Typelevel Cats. "Free Monad". Documents `Free[_]`, `cats-free`, DSL
  construction, `foldMap`, natural transformations, and practical uses.
  https://typelevel.org/cats/datatypes/freemonad.html, verified 2026-08-02.
- Typelevel Cats source. `cats/free/src/main/scala/cats/free/Free.scala`.
  Shows `Free[S, A]`, `flatMap`, `resume`, `step`, and `foldMap`.
  https://github.com/typelevel/cats/blob/main/free/src/main/scala/cats/free/Free.scala,
  verified 2026-08-02.
- Wouter Swierstra. "Data types a la carte". *Journal of Functional
  Programming* 18(4), Cambridge University Press, 2008, pages 423 through 436.
  Cambridge abstract and metadata. https://www.cambridge.org/core/journals/journal-of-functional-programming/article/data-types-a-la-carte/14416CB20C4637164EA9F77097909409,
  verified 2026-08-02.
- Janis Voigtlaender. "Asymptotic Improvement of Computations over Free
  Monads". In *Mathematics of Program Construction*, MPC 2008, LNCS 5133,
  Springer, pages 388 through 403. Author publication page.
  https://janis-voigtlaender.eu/papers.html, verified 2026-08-02.
- Runar Oli Bjarnason. "Stackless Scala with Free Monads". Apocalisp post
  linking the Scala Days 2012 paper. https://apocalisp.wordpress.com/2012/05/15/stackless-scala-with-free-monads-2/,
  verified 2026-08-02.
- doobie documentation. "Connecting to a Database". States that doobie monads
  are implemented through `Free` and interpreted to `Kleisli`.
  https://typelevel.org/doobie/docs/03-Connecting.html, verified 2026-08-02.
- Scalaz API documentation. `scalaz.Free`. Documents a free monad for a type
  constructor and stack-oriented binding behavior.
  https://javadoc.io/static/org.scalaz/scalaz-core_3/7.4.0-M17/scalaz/Free.html,
  verified 2026-08-02.
- Phil Freeman. *PureScript by Example*, chapter "Domain-Specific Languages".
  Uses the `free` library and builds an HTML content DSL with interpretation.
  https://book.purescript.org/chapter14.html, verified 2026-08-02.
- Hackage. `Control.Monad`, package `base`. States monad laws for Haskell's
  `Monad` class. https://hackage.haskell.org/package/base/docs/Control-Monad.html,
  verified 2026-08-02.
- Haskell Communities and Activities Report, May 2014. Section "free, Free
  Monads" reports the Haskell `free` package and its EDSL use.
  https://www.haskell.org/communities/05-2014/html/report.html, verified
  2026-08-02.
