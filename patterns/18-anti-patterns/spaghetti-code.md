---
name: Spaghetti Code
slug: spaghetti-code
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Rat's Nest Code, Kangaroo Code, Pretzel Logic, Ravioli Code (transitional variant)]
first_described: "Hopkins 1972 (earliest documented use); Conway 1978 and Noll 1979 (named in book titles)"
maturity: canonical
related: [big-ball-of-mud, god-object, structured-programming, extract-method, guard-clauses, state-pattern, strategy]
incompatible_with: [structured-programming, guard-clauses]
verified: 2026-08-02
---

# Spaghetti Code

## 1. Name, aliases, and lineage

Spaghetti code is the name given to source code whose control flow is so
tangled that a reader cannot follow the path an execution will take through
it without running it, or without holding an unreasonable amount of state
in their head at once. The metaphor is a plate of cooked spaghetti. every
strand crosses every other strand, and pulling on one strand to see where it
leads pulls in a dozen others.

The exact coining of the phrase has no single citable first use, and this
entry states that plainly rather than inventing a precise origin, following
the judgement versus sourced claim rule this repository holds itself to. What
can be sourced is a documented trail through the 1970s. Martin Hopkins, in a
1972 discussion of reducing the use of the goto statement, wrote that the
hope was that "the resulting programs will not look like a bowl of
spaghetti," which is the earliest widely cited written appearance of the
metaphor applied to code
([Wikipedia, Spaghetti code, citing Hopkins 1972](https://en.wikipedia.org/wiki/Spaghetti_code),
verified 2026-08-02). Richard Conway, in *A Primer on Disciplined
Programming Using PL/I, PL/CS, and PL/CT*, 1978, described programs that
"have the same clean logical structure as a plate of spaghetti," and Paul
Noll used "spaghetti code" and "rat's nest" as interchangeable terms for
poorly structured source in *Structured Programming for the COBOL
Programmer*, 1979, both cited in the same Wikipedia entry and both
independently checkable through library catalog records of those titles.
By the end of the 1970s the term was established enough to appear in book
titles aimed at working programmers, which is strong evidence it was already
common shop talk before it was common print.

The term is inseparable from the goto statement in its earliest usage,
because in the languages of that era (assembly, early FORTRAN, early BASIC,
COBOL) an unrestricted jump instruction was the only tool available for
non-linear control flow, and a program built from enough of them, added
gradually by different hands over years, naturally accreted the tangled
shape the metaphor describes. Richard Hamming is quoted, in the same source,
describing early binary machine programming as requiring jumps to empty
storage locations to patch in corrections, which caused the program's
control paths to resemble "a can of spaghetti" even before higher level
languages existed to name the problem
([Wikipedia, Spaghetti code](https://en.wikipedia.org/wiki/Spaghetti_code),
verified 2026-08-02). The structured programming movement of the following
decade, discussed in dimension 14 below, was in large part a direct
response to this observed failure mode, and its central technical claim,
that any program can be built from sequence, selection, and iteration alone
without unrestricted jumps, is the theoretical basis for treating
spaghetti code as fixable rather than as an unavoidable cost of software
that grows over time.

This entry's subject is narrower than two adjacent, frequently confused
anti-patterns cataloged elsewhere in this family. Spaghetti code names a
failure in control flow, the sequence in which statements execute and the
paths a reader must trace to understand that sequence. It is not, by
itself, a claim about class boundaries (see the god-object entry) or about
whole-system architectural erosion (see the big-ball-of-mud entry), although
in practice a codebase that has one of these three failures often
accumulates the other two alongside it, because the underlying cause,
incremental local decisions made under time pressure with no active
counter-pressure, is the same cause behind all three.

## 2. Problem and context

A program begins as a short, linear sequence of statements that a single
author can hold entirely in their head. As requirements accumulate, new
conditions are added to existing branches rather than factored into new
functions, because adding one more `if` to an existing block is faster in
the moment than extracting a new function, naming it, and wiring it in. Each
individual addition is locally reasonable. a bug is found and a special
case is patched in place, a new customer segment needs one more branch, a
deadline means the fastest fix wins over the cleanest one. No single commit
looks like a mistake in code review. What accumulates is not a bad decision
but a bad shape, formed from hundreds of individually defensible decisions,
none of which was made with the resulting shape in view.

The context in which this happens most reliably has four ingredients
present together. First, a language or era that makes unstructured jumps
cheap, historically the unrestricted goto in assembly, FORTRAN, and BASIC,
and in modern codebases the equivalent role is often played by deeply
nested conditionals, mutable flag variables that gate later branches, and
callback or event-handler chains connected only by shared mutable state
rather than by an explicit call graph. Second, sustained feature pressure
with no enforced code review practice that specifically watches nesting
depth, branch count, or nonlocal jumps. Third, a single author or a small
founding team who each individually hold the tangled logic in memory and
therefore do not experience it as tangled, followed by turnover that
replaces that team with people who cannot reconstruct the mental model from
the code alone. Fourth, the absence of automated tests around the affected
logic, because a large, well-maintained test suite is one of the few forces
that makes the cost of tangled control flow visible early rather than
late.

The observable symptom a reader can recognize without knowing the pattern
name is direct. To understand what a single function does, the reader has
to open several other functions or scroll far up and down the same file,
track two or more boolean flags that are set in one place and checked in
another, unrelated place, and mentally simulate an execution path rather
than read a description of one. A second, closely related symptom is that
fixing one reported bug reliably introduces a second bug elsewhere, because
the paths through the code are not independent, a change to one path
changes the shared state that another, seemingly unrelated path also
depends on. This second symptom, sometimes called the "whack a mole" bug
pattern in practitioner discussion, is the most reliable single signal that
control flow, not merely class design, is the root failure, and it is the
signal that should route a reader to this entry rather than to the
god-object or big-ball-of-mud entries, both of which present differently
even though all three can coexist in the same file.

## 3. Forces

Local editing cost pulls toward tangle. Adding one more condition to an
existing `if` chain, or one more mutable flag that a later branch checks,
costs a line or two and no design decision. Extracting the same logic into
a named function, giving it a clear contract, and calling it from the
original site costs more thought in the moment even though it costs less
over the life of the change. Under any deadline this force wins by default
on each individual decision, because the discipline required to resist it
has to be paid up front while the cost of not resisting it is deferred to
whoever reads the code next, who is frequently a different person.

Familiarity with the existing shape pulls the same direction for the
original author. Someone who wrote the tangled logic, or who has worked in
it long enough to build a mental model of its jumps, experiences no
friction reading it, because they are not actually parsing the control flow
from the text, they are recalling it from memory and using the text only to
confirm details. This is why the person most qualified to judge whether a
piece of code is spaghetti code is reliably the worst judge of it. familiarity
substitutes for clarity in their own reading experience and hides the cost
from the person best positioned to fix it early.

Correctness pressure pulls toward preserving the existing tangle rather
than restructuring it. Once a function has accreted enough special-case
branches to handle a wide range of real inputs correctly, each branch
usually encodes a real, previously observed failure that someone spent real
debugging time discovering. Restructuring that function risks silently
losing one of those branches, and the fear of that loss, well founded in
codebases with thin test coverage, is a legitimate force against touching
the code at all, not merely a lazy excuse. Joel Spolsky makes exactly this
argument about a codebase widely called "a mess," pointing out that what
looks like clutter to a reader unfamiliar with the history is frequently
"bug fixes. Each of these bugs took weeks of real-world usage before they
were found"
([Joel Spolsky, "Things You Should Never Do, Part I," joelonsoftware.com](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/),
verified 2026-08-02). This force does not excuse tangled control flow, but
it explains why restructuring it safely requires characterization tests
before the restructuring, discussed in dimension 15, rather than a
confident rewrite from a reader who has not yet earned the right to be
confident.

Readability and testability pull the opposite direction, toward structured,
linear, single-entry, single-exit control flow, because a reader who can
trace a straight line through a function without holding external state in
mind can also write a test that exercises that same straight line, and a
function with one entry and predictable exits is trivially composable with
other such functions. This force is silent and long term. it never blocks a
single commit, it only accumulates cost across every future commit that has
to route around the tangle, which is exactly why it consistently loses the
moment-to-moment contest against the three forces above unless something
external, a linter threshold, a review checklist, an enforced complexity
budget, actively represents it in the room.

## 4. Applicability and non-applicability

Recognizing spaghetti code correctly, and recognizing when the diagnosis
does not apply, matters more for this entry than for most, because the term
is used loosely in casual conversation to mean simply "code I do not like,"
and that loose usage causes real, working, well-tested code to be rewritten
for no benefit, which is its own documented failure mode discussed further
in dimension 11.

Diagnose spaghetti code, and treat this entry's remedies as applicable,
when the following are jointly true.

1. Understanding a single function or module requires tracing execution
   across two or more other functions or files connected only through
   shared mutable state, rather than through an explicit, named call.
2. Two or more mutable flag variables gate branches in a way that a reader
   cannot resolve by reading top to bottom, because a flag set in one
   branch is checked in a branch that appears earlier in the source order
   or in an unrelated function.
3. The nesting depth of conditionals in the hot path of a function exceeds
   what a reader can hold in short-term working memory while reading, a
   threshold most style guides and static analysis tools place between
   three and five levels, and this is confirmed by a measurable complexity
   score, discussed under observability in dimension 16.
4. Bug fixes to the affected code reliably introduce new defects elsewhere
   in the same function or module, indicating the paths through the code
   are not actually independent of each other despite appearing to be
   separate branches.
5. New contributors report, independent of each other, that they cannot
   predict what a change to the code will do without running it, which is
   the practical, human-centered form of the same technical diagnosis.

Do not diagnose spaghetti code, and do not apply this entry's remedies,
in the following situations.

1. **Dense but linear code.** A function with many sequential steps and no
   branching, even a long one, is not spaghetti code. it may be a Long
   Method smell that benefits from extraction for readability, but its
   control flow is a straight line and a reader can trace it by scanning
   top to bottom. Conflating length with tangle leads to unnecessary
   rewrites of code that was never actually hard to trace.
2. **Disciplined single-exit goto for cleanup, as used in the Linux
   kernel.** The kernel's own coding style explicitly recommends goto for
   centralized error cleanup, stating that "the goto statement comes in
   handy when a function exits from multiple locations and some common
   work such as cleanup has to be done," on the grounds that this produces
   fewer, more predictable exit points than an equivalent set of nested
   conditionals would
   ([Linux kernel coding style, "Centralized exiting of functions," kernel.org](https://www.kernel.org/doc/html/latest/process/coding-style.html),
   verified 2026-08-02). This is the presence of the historically
   maligned goto keyword without the underlying symptom, unpredictable,
   untraceable control flow, and it is the clearest evidence available
   that the anti-pattern is the tangle itself, not any single keyword
   associated with it.
3. **Dense mathematical or numerical code with heavy branching that
   directly mirrors a specification.** A parser's state machine, or a
   numerical routine implementing a documented algorithm with many
   documented edge cases, can look superficially similar to spaghetti
   code, deep nesting, many conditions, but if each branch traces
   directly and legibly to a line in a specification or a well-known
   algorithm, the complexity is inherent to the problem rather than
   accidental, and restructuring it can make it harder, not easier, to
   verify against the specification it implements.
4. **Legacy code that is stable, rarely touched, and has no planned future
   changes.** If a piece of tangled control flow has not been modified in
   years, works correctly, and nobody has a concrete plan to extend it,
   the cost of a restructuring effort, including the risk of
   characterization test gaps discussed in dimension 15, can exceed the
   benefit. This entry's remedies earn their cost specifically at the
   point where a change to the tangled code is already required for some
   other reason.
5. **Code that merely looks unfamiliar because it uses an idiom the reader
   has not learned.** Recursive descent, continuation passing, or a
   well-factored visitor dispatch can read as confusing to someone
   unfamiliar with the idiom on first encounter, but familiarity with a
   correct idiom is a training problem, not a control flow problem, and
   the fix is documentation or pairing, not a rewrite.

## 5. Structure

Spaghetti code does not have participants in the sense that a design
pattern does, because it is the absence of an intentional structure rather
than the presence of one. What can be named are the structural elements
whose interaction, unmanaged, produces the tangle, and naming them is what
makes the remedy tractable.

**Shared mutable state** is any variable, field, or global that is written
in one location and read in a distant, textually unrelated location, and
whose current value therefore silently determines which branch a later
piece of code will take. In the anti-pattern this state substitutes for an
explicit parameter or an explicit call, so the connection between the write
and the read is invisible in the local text a reader is looking at.

**Nonlocal jumps** are any control transfer, an unrestricted goto, a
deeply nested `break` or `continue` targeting an outer loop, or an
exception used purely for ordinary control flow rather than for an
exceptional condition, that moves execution to a location the reader cannot
predict from the surrounding lexical structure alone.

**Flag-gated branches** are conditionals whose condition is a boolean
variable set far away rather than a direct check of the actual data the
branch cares about, so the branch's true trigger is hidden behind one level
of indirection that carries no explanatory name of its own.

**The implicit sequencer** is the mental model, held only in the head of
whoever wrote the code, of what order the branches, jumps, and flags will
actually execute in for a given input. In well-structured code this
sequencer is made explicit as the call graph or the state machine
definition itself. in spaghetti code it exists only as tribal knowledge,
and its loss when the original author leaves is the moment the code
transitions from merely ugly to actively dangerous to change.

The remedy structure, shown in the code examples and the refactoring path
below, replaces these four elements with named collaborators that
communicate through explicit parameters and return values, arranged so
that each collaborator has one entry point, one predictable set of exits,
and no dependency on state it did not receive as an argument.

## 6. ASCII structure diagram

```
SPAGHETTI SHAPE (undirected tangle through shared mutable state)

  +----------+     +----------+     +----------+
  | branch A |<--->| branch B |<--->| branch C |
  +----------+     +----------+     +----------+
       ^                 ^                ^
       |                 |                |
       +--------+--------+--------+-------+
                |                 |
          +-----------+     +-----------+
          | flag: ok  |     | flag: seen|
          +-----------+     +-----------+
   (each branch both reads and writes both flags;
    the actual path taken depends on execution order,
    which is not visible from reading any single branch)


STRUCTURED SHAPE (directed, single-entry single-exit collaborators)

  caller
    |
    v
  +-------------+     +-------------+     +-------------+
  | validate()  | --> |   price()   | --> |  persist()  |
  +-------------+     +-------------+     +-------------+
    one input,          one input,          one input,
    one output,         one output,         one output,
    no shared state,    no shared state,    no shared state,
    no jumps             no jumps            no jumps

  (each box has exactly one arrow in and one arrow out;
   the sequence is readable top to bottom without
   tracing state across the diagram)
```

## 7. Dynamics

At runtime, spaghetti code executes correctly in the ordinary sense, the
processor follows exactly the instructions it is given, but the path it
takes is not the path a reader would predict from a linear reading of the
source, because the actual next step depends on the current value of state
that was set somewhere else in the program's history rather than on the
input the reader can see at the current call site. This is the
runtime signature. two calls with what looks like the same input from the
call site can take different paths, because the difference lives in state
the reader cannot see without also tracking every prior call that touched
the same shared variables.

The sequence below traces a single order-processing request through the
tangled shape shown in the diagram above, illustrating how a change to the
order in which two earlier calls happened can change the outcome of a
later, apparently unrelated call, without any change to that later call's
own code.

```
STEP  ACTION                              STATE AFTER STEP
----  ----------------------------------  ---------------------------
1     caller invokes branch A(order 1)    ok=false, seen=false
2     branch A sets seen=true, jumps to   ok=false, seen=true
      branch C because seen was false
      when A itself started
3     branch C reads ok (still false      ok=false, seen=true
      from step 1), rejects order 1
4     caller invokes branch A(order 2)    ok=false, seen=true
5     branch A sets ok=true this time,    ok=true,  seen=true
      because seen is now true from the
      PREVIOUS order, jumps to branch B
6     branch B accepts order 2 using a    ok=true,  seen=true
      flag that has nothing to do with
      order 2's own data

RESULT: order 1, which was a normal, valid order, was rejected because
of a flag left over from before it arrived. order 2 was accepted for a
reason that has nothing to do with order 2's own contents. Neither
outcome can be explained by reading branch A, B, or C in isolation.
```

The structured shape's dynamics are, by construction, the opposite of this.
`validate`, `price`, and `persist` each receive their entire input as
parameters and return their entire output as a value, so two calls to
`placeOrder` with the same arguments always produce the same sequence of
internal calls and the same result, which is the definition of a
predictable, composable function chain, and it is precisely the property
the tangled version lacks.

## 8. Implementation variants

Spaghetti code is not a single fixed shape, it is a family of variants that
share the underlying failure, unmanaged, implicit control transfer, while
differing in which language-level feature carries the tangle.

**Classic goto-based spaghetti**, historically the original meaning of the
term, in languages such as early BASIC and FORTRAN, or in modern C or Go
code, where an unrestricted, unnamed-purpose goto jumps into the middle of
unrelated logic rather than to a single, clearly labeled cleanup point.
This variant is directly distinguishable from the disciplined,
single-purpose cleanup goto discussed in dimension 4, because the tangled
variant has multiple jump targets that cross each other, while the
disciplined variant has a small number of forward-only jumps to a shared
tail.

**Flag-driven state-machine spaghetti**, common in languages without a
goto, where a mutable "phase" or "step" variable, or several independent
boolean flags, are checked and mutated across a wide function or across
several functions, simulating the goto's nonlocal jump using ordinary
assignment and conditionals instead of an actual jump instruction. This
variant is the one shown in this entry's code examples, because it is the
form most likely to appear in a codebase written after the 1980s.

**Callback and event-handler spaghetti**, sometimes called "callback hell"
or the "pyramid of doom" in the JavaScript and Node.js community, where
deeply nested asynchronous callbacks each capture and mutate variables from
an enclosing scope, so that understanding what happens after an operation
completes requires reading inward through several levels of nesting while
tracking which enclosing variables each level has already changed. This is
functionally the same tangle as flag-driven spaghetti, expressed through
closures over shared scope rather than through explicit flags, and it is
documented as a distinct, named failure by the JavaScript community itself,
with `callbackhell.com`, maintained by Max Ogden, prescribing the same
remedy family this entry recommends. named functions instead of anonymous
nesting, and small modules that "each do one thing," assembled by a thin
coordinator
([Max Ogden, callbackhell.com](http://callbackhell.com/), verified
2026-08-02).

**Copy-paste spaghetti**, where the tangle is produced not by jumps or
flags within one function but by the same logic, slightly modified, pasted
into many call sites, so that tracing "what happens when this input
arrives" requires locating every pasted copy and checking whether each one
has since diverged. This variant shares the readability symptom of the
other three, understanding requires locating and reconciling scattered
logic, but its remedy is closer to the Extract Method and Pull Up Method
refactorings than to the guard-clause and state-machine remedies that fit
the other three variants, because there is no shared mutable state to
eliminate, only duplicated logic to consolidate.

## 9. Known production uses

Spaghetti code is unusual among the entries in this family in that its
clearest documented production instances are historical and linguistic
rather than a single named modern codebase, because the anti-pattern
predates by decades the practice of writing public case studies about
software architecture, and because a codebase that is genuinely
unstructured to the degree this entry describes is, by its own nature,
rarely written up formally by the team that owns it. The instances below
are each independently checkable.

**Line-numbered BASIC and GOTO-heavy FORTRAN of the 1970s and 1980s.**
BASIC's original design used numbered lines and an unrestricted GOTO as its
only means of nonlinear control flow, and Wikipedia's entry on spaghetti
code presents a numbered BASIC program as its own worked example of code
"that can be more easily understood with structured control flow instead
of using goto"
([Wikipedia, Spaghetti code](https://en.wikipedia.org/wiki/Spaghetti_code),
verified 2026-08-02). A 1981 humor piece in the University of
Michigan student engineering magazine *The Michigan Technic*, quoted in the
same entry, described FORTRAN as a language that "consists entirely of
spaghetti code," a claim notable less for its accuracy about the language
itself and more as documented evidence that by 1981 the phrase was common
enough in undergraduate engineering culture to be used as a punchline
without explanation.

**Legacy COBOL systems in United States government tax and unemployment
infrastructure, patched under emergency conditions in 2020.** During the
COVID-19 pandemic, "several US states reported a shortage of skilled
COBOL programmers to support the legacy systems used for unemployment
benefit management," and the Internal Revenue Service needed to urgently
patch its own COBOL systems to distribute Coronavirus Aid, Relief, and
Economic Security Act payments, according to Wikipedia's entry on COBOL,
which further notes that planned modernization of these systems had been
suspended before the crisis
([Wikipedia, COBOL](https://en.wikipedia.org/wiki/COBOL), verified
2026-08-02). This is judgement, not a sourced claim about control flow
specifically. COBOL systems of this vintage are not automatically spaghetti
code merely by being old or by being written in COBOL, but the well
documented shortage of engineers willing and able to safely modify these
systems is consistent with, and commonly attributed by practitioners to,
decades of incremental patching without structural review, which is
exactly the accumulation process this entry describes in dimension 2.

**The Netscape Communicator codebase of the late 1990s.** Joel Spolsky's
widely cited essay on the decision to rewrite Netscape's browser from
scratch describes the engineering team's consensus that "the old Netscape
code base was really bad," while also arguing that much of what looked
like mess to unfamiliar readers was in fact "bug fixes" earned through real
world use rather than careless tangle
([Joel Spolsky, "Things You Should Never Do, Part I," joelonsoftware.com](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/),
verified 2026-08-02). This case is included specifically for the nuance it
adds rather than as a clean example, it is real, named, and widely
discussed evidence that a codebase can be perceived as spaghetti code by
readers unfamiliar with its history while some of its apparent tangle is
in fact hard-won correctness, which is exactly the misdiagnosis warned
against in dimension 4 and dimension 11.

**JavaScript callback pyramids in the pre-Promise, pre-async/await Node.js
ecosystem.** `callbackhell.com`, maintained by developer Max Ogden with
source available on GitHub, exists specifically to document and remediate
the deeply nested, hard to follow callback structure that became endemic
in asynchronous JavaScript code once Node.js made callback-based I/O the
default idiom, recommending named functions, small single-purpose modules,
and, for code wanting "flow control that reads top to bottom," Promises and
async and await as remedies
([Max Ogden, callbackhell.com](http://callbackhell.com/), verified
2026-08-02). The guide does not itself use the words "spaghetti code," and
this entry does not claim it does. it is presented here as the JavaScript
ecosystem's own named production instance of the same underlying failure,
unmanaged, hard to trace control flow, expressed through nested closures
rather than through goto or flags.

## 10. Consequences

Positive consequences of the shape the anti-pattern produces are, honestly,
almost entirely about the moment of writing rather than any property of
the resulting code, and are stated here for completeness rather than as an
endorsement. Writing one more branch or one more flag into existing code
is faster in the immediate moment than designing a new collaborator, and
for a genuinely small, genuinely short-lived script that will never be read
by anyone but its author and will never be extended, this speed can be a
real, rational trade, which is exactly why dimension 4 excludes such code
from the anti-pattern's applicability in the first place. Once code is
expected to be read, modified, or extended by more than its original
author, or to live longer than a single sitting, these apparent benefits do
not survive contact with a second reader.

Negative consequences are extensive. Comprehension cost rises sharply,
because a reader must trace execution across nonlocal jumps and shared
mutable state rather than reading a straight line, and this cost compounds
every time the code is touched again. Defect rate rises for the same
structural reason, because paths are not independent, a change made to
satisfy one requirement can silently break a different, seemingly unrelated
path that shares the same mutable state, producing the "whack a mole"
symptom described in dimension 2. Testability collapses, because a
function's behavior depends on flags set by unrelated earlier calls and
cannot be isolated without first reproducing that earlier call sequence,
which is precisely the difficulty addressed by characterization testing in
dimension 15. Onboarding cost rises, because new team members cannot build
a correct mental model from reading the code and must instead trace
execution by hand or rely on the departing expert who built the original
model, a dependency that becomes unrecoverable the moment that person
leaves. Finally, structural complexity metrics, cyclomatic complexity chief
among them and discussed in dimension 16, rise directly with the branching
this anti-pattern produces, giving an early, measurable warning signal
before the qualitative symptoms above become acute.

## 11. Failure modes and misuse

**Symptom.** A single reported bug fix reliably produces one or more new
defects in a location the fixing engineer did not touch and was not aware
was related.
**Cause.** Two or more code paths share mutable state that is not visible
from either path's own local text, so a change to how one path uses that
state silently changes the other path's behavior, exactly as traced in
dimension 7's dynamics walkthrough.
**Fix.** Identify every read and write of the shared state across the
tangled region, and replace each write-then-distant-read pair with an
explicit parameter or explicit return value passed directly between the
two collaborators that actually need to communicate, following the
refactoring path in dimension 14.

**Symptom.** Estimates for small, apparently isolated changes to a
specific module are consistently far larger, and far less reliable, than
estimates for equally sized changes elsewhere in the same codebase.
**Cause.** The engineers giving the estimate know from experience that
they cannot predict a change's blast radius in that module without
manually tracing execution paths first, which is unpredictable work that
resists estimation, and the resulting estimate padding is a rational
response to genuine uncertainty rather than a process failure.
**Fix.** Treat consistently unreliable estimates for one module as a
diagnostic signal in its own right, and prioritize restructuring that
module the next time a change to it is already required, rather than
continuing to pad estimates indefinitely around a cost that compounds.

**Symptom.** A reader unfamiliar with a piece of code declares it
"spaghetti code" and proposes a full rewrite, and the rewrite, once shipped,
reintroduces bugs that the original code had already silently fixed years
earlier.
**Cause.** This is the misuse side of the anti-pattern's name, applying the
label to any code the reader finds unfamiliar or verbose rather than to
code that specifically exhibits nonlocal jumps or flag-gated distant state,
and then treating a rewrite as a costless improvement without first
capturing the original code's actual, tested behavior through
characterization tests. This is precisely the trap Joel Spolsky's essay,
cited in dimension 3 and dimension 9, warns against, where what looked
like mess to an unfamiliar reader was "bug fixes" earned through real
world exposure
([Joel Spolsky, "Things You Should Never Do, Part I," joelonsoftware.com](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/),
verified 2026-08-02).
**Fix.** Apply the applicability checklist in dimension 4 before diagnosing
spaghetti code at all, and when a genuine diagnosis is confirmed, follow
the step by step refactoring path in dimension 14 behind a
characterization test suite rather than a from-scratch rewrite, so that
every existing branch's behavior, including the ones whose reason has been
forgotten, is preserved unless a specific, documented decision removes it.

**Symptom.** A team introduces a rule that forbids all use of a specific
keyword, most often goto, and reports no measurable improvement in defect
rate or comprehension time afterward.
**Cause.** The keyword is a carrier of the anti-pattern in some codebases
and languages, not the anti-pattern itself, and banning the keyword while
leaving the equivalent flag-driven or callback-driven variant untouched,
as described in dimension 8, removes the symptom's most visible surface
form while leaving the underlying nonlocal, implicit control transfer
completely intact under a different syntax.
**Fix.** Target the underlying property, whether a reader can predict
control flow from local, explicit information alone, using the structural
complexity metrics in dimension 16, rather than targeting a specific
keyword, and recognize, as the Linux kernel's own style guide does, that a
disciplined, single-purpose use of even a historically maligned keyword can
be the more readable choice in the right, narrow context described in
dimension 4.

## 12. Trade-off matrix

| Force | Spaghetti Code (unstructured control flow) | Structured Control Flow (guard clauses, extracted functions) | Big Ball of Mud (architecture-wide erosion) | God Object (concentrated responsibility) |
|---|---|---|---|---|
| Local edit speed, single change | Fastest in the immediate moment. one more flag or branch | Slower per change. requires naming and wiring a collaborator | Comparable to spaghetti code at the module level, but the erosion is architectural, not local | Fast locally, since most needed state is already in the one class |
| Comprehension cost for a new reader | Highest. requires tracing nonlocal state across the file or files | Lowest. each function reads top to bottom with an explicit contract | High, but the difficulty is locating the responsible module, not tracing control flow within one | Moderate. one large file to read, but its internal flow may itself be linear |
| Testability in isolation | Very poor. tests must reproduce prior call sequences to set shared state correctly | Strong. each collaborator takes explicit input and returns explicit output | Poor for the same reason as spaghetti code, compounded by unclear module boundaries | Poor for a different reason. the class has too many dependencies to instantiate cheaply in a test |
| Defect propagation between changes | High. shared mutable state links paths that appear unrelated | Low. explicit parameters prevent silent, distant coupling | High, but propagates through shared architecture rather than shared control flow variables | Moderate. changes to shared class state can affect any of its many callers |
| Primary named remedy | Guard clauses, Extract Method, explicit state machine (dimension 14) | Not applicable, this is the target state | Strangler Fig migration, defined module boundaries | Extract Class, Facade, single-responsibility decomposition |
| Cited source for the remedy family | Fowler and Beck, *Refactoring*, 2018 ([martinfowler.com](https://martinfowler.com/books/refactoring.html), verified 2026-08-02) | same | Foote and Yoder, "Big Ball of Mud," PLoP '97/EuroPLoP '97, 1997 | Brown, Malveau, McCormick, Mowbray, *AntiPatterns*, 1998 |

## 13. Related and incompatible patterns

**Structured programming** is the direct historical remedy this entry's
existence responds to, and the two are related as diagnosis and treatment
rather than as peers. Edsger Dijkstra's 1968 letter "Go To Statement
Considered Harmful," published in *Communications of the ACM*, volume 11,
issue 3, pages 147 to 148, argued that unrestricted goto statements
"complicated the task of analyzing and verifying the correctness of
programs," particularly those involving loops, and that the construct was
"too primitive" and "too much an invitation to make a mess of one's
program"
([Dijkstra, "Go To Statement Considered Harmful," CACM 11(3), 1968, cited via Wikipedia](https://en.wikipedia.org/wiki/Goto),
verified 2026-08-02). This letter became the foundational argument for
building control flow only from sequence, selection, and iteration, and
that discipline is the direct, named opposite of the shape this entry
describes.

**Big Ball of Mud** shares a surface-level reputation with spaghetti code,
both names are used loosely to mean "bad code," but the two are formally
distinct in scope. Brian Foote and Joseph Yoder's 1997 paper, which credits
Brian Marick with coining the phrase, describes "a haphazardly structured,
sprawling, sloppy" system with promiscuous information sharing and no
perceivable overall design
([Foote and Yoder, "Big Ball of Mud," PLoP '97/EuroPLoP '97, 1997, cited via Wikipedia](https://en.wikipedia.org/wiki/Big_ball_of_mud),
verified 2026-08-02). That paper's subject is architecture-wide, module and
layer boundaries eroded across an entire system, while spaghetti code's
subject is control flow within one function or one small cluster of
functions. A system can be a big ball of mud with no individual function
that is internally spaghetti code, if each module is locally readable but
the boundaries between modules have collapsed, and a single function can be
spaghetti code inside an otherwise cleanly layered system. The two
frequently coexist because their root cause, incremental local decisions
under time pressure, is shared, but they are diagnosed and treated at
different scopes.

**God Object** is likewise a frequent neighbor rather than a synonym.
concentrating many responsibilities into one class, the god-object entry's
subject, does not by itself imply that the control flow inside that class's
methods is tangled, a god object's individual methods can each be
internally linear. Conversely, a small, single-responsibility function can
still be internally spaghetti code if its own control flow uses nonlocal
jumps or flag-gated distant state. The two are commonly found together
because a class that has become a dumping ground for unrelated
responsibilities is also a class whose methods are frequently patched with
one more special case rather than extended cleanly, which is the same
force described in dimension 3.

**Guard Clauses**, **Extract Method**, and the **State pattern** are the
principal compositional remedies, discussed in detail in dimension 14, and
each composes cleanly with the others. guard clauses remove nesting at the
top of a function, Extract Method turns the remaining linear steps into
named, independently testable collaborators, and the State pattern gives an
explicit, inspectable name to what was previously an implicit flag-driven
phase variable, replacing the informal sequencer described in dimension 5
with a formal one that a reader, and a test, can inspect directly.

Spaghetti code is directly incompatible with structured programming and
with the guard-clause discipline by definition. a function cannot
simultaneously rely on nonlocal jumps through shared mutable state and also
exhibit the single-entry, predictable-exit property those two remedies
exist to establish. Applying either remedy to a function necessarily
removes the anti-pattern from that function, which is the sense in which
the two are formally incompatible rather than merely in tension.

## 14. Refactoring path in and out

**Introducing this anti-pattern**, which should never be done
deliberately but is documented here because understanding how it arrives
is the fastest way to recognize it early, happens through a small number
of individually reasonable steps repeated many times. A conditional is
added inside an existing conditional rather than extracted. a boolean flag
is introduced to remember a decision made earlier in a function so a later
branch does not have to recompute it, and that flag quietly becomes the
only record of that decision once the code that originally made it is
edited or removed. A goto, or its structured-language equivalent, a deeply
nested `break` labeled to an outer loop, is used to short-circuit out of an
inconvenient nesting depth rather than restructuring the nesting itself.
None of these steps, taken alone, produces spaghetti code. the anti-pattern
is the cumulative effect of dozens of such steps, each locally defensible,
compounding over months or years with no active force pushing back.

**Removing this anti-pattern** is a staged process, and skipping the first
stage is the single most common cause of introducing new defects during a
cleanup, since the tangled function's exact current behavior, including
branches whose original reason is forgotten, is the thing being preserved,
not merely the thing being read.

1. **Write characterization tests first, before changing any logic.**
   A characterization test asserts what the code currently does for a
   representative set of inputs, including edge cases discovered by
   exercising every reachable branch, without asserting what it should do.
   This step directly answers the correctness-preservation force described
   in dimension 3, giving the person doing the restructuring a safety net
   that the original code, by construction, did not have. Fowler and
   Beck's *Refactoring. Improving the Design of Existing Code* frames this
   general discipline, of behavior-preserving structural change verified by
   tests, as the definition of refactoring itself
   ([Fowler and Beck, *Refactoring*, 2nd ed., 2018, and 1st ed., 1999](https://martinfowler.com/books/refactoring.html),
   verified 2026-08-02).
2. **Replace nested conditionals at function entry with guard clauses.**
   Any condition near the top of a function whose failure means the rest
   of the function has nothing meaningful to do should return, or throw,
   immediately, rather than wrapping the remaining logic in an additional
   level of nesting. This single mechanical change is often enough on its
   own to remove one or two levels of nesting depth across an entire
   function, which the complexity metrics in dimension 16 will show
   directly.
3. **Extract each remaining linear segment into a named function with an
   explicit signature.** Every segment of the tangled function that reads
   or writes one of the shared mutable variables identified in dimension 5
   becomes a small function that takes that data as a parameter and
   returns it as a value, removing the read-write-at-a-distance
   relationship that made the original tangle hard to trace.
4. **Replace any remaining flag-driven phase variable with an explicit
   state representation.** Where a single mutable variable tracks "which
   step we are on," and multiple branches read and write it, introduce an
   explicit enumeration or a State pattern implementation, so the current
   phase is a first-class, inspectable value rather than an implicit fact
   a reader must reconstruct from prior assignments.
5. **Re-run the characterization tests from step one after each individual
   extraction**, not only at the end of the process, so that any behavior
   change is caught at the smallest possible step rather than discovered
   only after several extractions have compounded.
6. **Delete the characterization tests that duplicate the coverage of the
   new, intention-revealing tests written against the extracted
   collaborators**, once those collaborators exist and are independently
   tested, keeping only the characterization tests that still exercise
   genuine edge cases the new tests do not yet cover.

## 15. Testing and verification

Code that exhibits this anti-pattern is difficult to test by construction,
which is itself one of the clearest diagnostic signals available, discussed
in dimension 4 and dimension 16. A unit test generally wants to supply a
known input to a unit and assert a known output, holding everything else
constant, and a function whose behavior depends on mutable state set by an
unrelated, earlier call cannot be tested this way without first
reproducing that earlier call's exact sequence, which couples the test's
setup to implementation history rather than to the function's documented
contract. This is why test suites around genuinely tangled code are, in
practice, either sparse, because writing each test is disproportionately
expensive, or brittle, because each test secretly depends on execution
order and breaks when an unrelated part of the suite is reordered or run in
isolation.

Before any restructuring, characterization tests, described in dimension
14, are the correct testing technique, because their purpose is explicitly
to record current behavior rather than to specify intended behavior, which
matters because the intended behavior of long-tangled code is frequently
unknown even to its current maintainers. A characterization test suite for
this anti-pattern should specifically target the boundary conditions of
each shared mutable flag identified in dimension 5, exercising the code
with that flag in each of its observed states, since these boundary
crossings are exactly where the "whack a mole" defect propagation described
in dimension 2 and dimension 10 originates.

After restructuring, the extracted collaborators produced by the
refactoring path in dimension 14 should each be tested independently,
against their explicit parameter and return contract, with no setup step
required beyond constructing their direct inputs. The presence or absence
of this kind of test, one that requires no shared fixture beyond the
function's own declared parameters, is itself a reliable, mechanical proxy
for whether the restructuring succeeded. a collaborator that still needs
an elaborate setup sequence to test in isolation has not yet been fully
separated from the shared state it originally depended on.

## 16. Observability signals

The single most established, most independently verifiable observability
signal for this anti-pattern is cyclomatic complexity, introduced by
Thomas J. McCabe in "A Complexity Measure," published in *IEEE Transactions
on Software Engineering*, volume SE-2, issue 4, pages 308 to 320, December
1976, which counts the number of linearly independent paths through a
function's control-flow graph, computed as edges minus nodes plus two for a
single connected function
([McCabe, "A Complexity Measure," IEEE TSE SE-2(4), 1976, cited via Wikipedia](https://en.wikipedia.org/wiki/Cyclomatic_complexity),
verified 2026-08-02). A rising cyclomatic complexity score on a function
that has not gained new, independently justified business rules is a
direct, measurable signal that branching, and with it the risk of the
tangle this entry describes, is accumulating. Most static analysis
tooling flags functions above a configurable threshold, commonly in the
range of ten to fifteen, for review.

A newer, complementary metric, Cognitive Complexity, was formulated by G.
Ann Campbell at SonarSource specifically "to more accurately measure the
relative understandability of methods," explicitly building on cyclomatic
complexity while adding penalties for nesting depth and for control-flow
structures that break the linear flow a human reader expects, on the
premise that two functions with an identical cyclomatic complexity score
can differ sharply in how hard a human actually finds them to read
([G. Ann Campbell, "Cognitive Complexity," SonarSource](https://www.sonarsource.com/resources/cognitive-complexity/),
verified 2026-08-02). Because this metric was designed specifically to
weight nesting and jump structures more heavily than raw branch count, a
sustained gap where Cognitive Complexity rises faster than cyclomatic
complexity on the same function is a stronger, more specific signal of
this entry's anti-pattern than either metric alone, since it indicates the
branching that exists is disproportionately non-linear rather than merely
numerous.

Beyond static metrics, three runtime and process signals corroborate a
diagnosis. First, defect density measured per function or per module, cross
referenced against complexity scores for the same units, since the
correlation between the two is the practical evidence that the metric is
detecting a real, not merely theoretical, cost in this specific codebase.
Second, the "whack a mole" pattern described in dimension 2 and dimension
10, tracked by counting how many bug reports against a given module are
followed, within a short window, by a second, previously unreported defect
in the same module. a module with a high ratio of second-defects-per-fix is
exhibiting the shared-state coupling this entry describes even if its
complexity score has not yet crossed a configured threshold. Third, code
review latency and estimate variance for changes to a specific module,
tracked as described in dimension 11's second failure mode, is a
human-centered signal that corroborates what the automated metrics report,
and is often visible to engineering leadership well before a formal
complexity audit is run.

## 17. Security and privacy implications

Spaghetti code's security implication is largely indirect but well
established through general software engineering practice, rather than
through any incident this entry can cite specifically as caused by control
flow tangle alone, and this entry states that limitation plainly rather
than inventing a precise causal chain. Because reviewers cannot reliably
predict all the paths a change to tangled code will actually take,
security-relevant logic embedded inside such code, an authorization check
guarded by a flag that is also set by unrelated business logic, or a
validation step that a later branch can be reached without passing through
first, is disproportionately likely to have a path that bypasses it
entirely without that path being obvious from a code review of the
function alone. This is a structural risk that follows directly from the
comprehension and defect-propagation costs described in dimension 10, not
a distinct security-specific mechanism.

A closely related, more concrete implication concerns dead or unreachable
branches left behind by the accumulation process described in dimension 2.
a flag-gated branch that was intended to be permanently disabled, or an
old code path superseded by a newer one but never removed because removing
it risked breaking the tangled state it shared with other branches, can
remain reachable under conditions its current maintainers no longer
understand or test for. Where such a branch implements weaker or bypassed
security controls, its continued reachability is a genuine, exploitable
risk, and its detection is exactly the kind of finding the observability
signals in dimension 16, particularly a module-level defect density and
complexity audit, are positioned to surface before an incident does. This
entry does not claim a specific, named breach was caused by spaghetti code
control flow specifically, and readers should treat this dimension as
judgement about a structural risk factor, not as a sourced account of a
particular event.

Privacy implications follow the same indirect path. code that handles
personal data through a tangled sequence of flag-gated branches is harder
to audit for a specific, provable claim, such as "this data is only ever
written to storage X and never to storage Y," because proving such a claim
requires tracing every path through the code, which is precisely the task
this anti-pattern makes disproportionately expensive. Structured,
single-entry, single-exit collaborators, the target state of the
refactoring path in dimension 14, are correspondingly easier to audit for
exactly this kind of data-flow claim, because each collaborator's inputs
and outputs are explicit and enumerable rather than implicit in shared
state.

## 18. References

1. Wikipedia, "Spaghetti code," citing Martin Hopkins (1972), Richard
   Conway, *A Primer on Disciplined Programming Using PL/I, PL/CS, and
   PL/CT* (1978), Paul Noll, *Structured Programming for the COBOL
   Programmer* (1979), and a 1981 piece in *The Michigan Technic*.
   https://en.wikipedia.org/wiki/Spaghetti_code, verified 2026-08-02.
2. Edsger W. Dijkstra, "Letters to the editor. Go to statement considered
   harmful," *Communications of the ACM*, volume 11, issue 3, pages 147
   to 148, March 1968, cited via
   https://en.wikipedia.org/wiki/Goto, verified 2026-08-02.
3. Thomas J. McCabe, "A Complexity Measure," *IEEE Transactions on
   Software Engineering*, volume SE-2, issue 4, pages 308 to 320,
   December 1976, cited via
   https://en.wikipedia.org/wiki/Cyclomatic_complexity, verified
   2026-08-02.
4. Brian Foote and Joseph Yoder, "Big Ball of Mud," Fourth Conference on
   Pattern Languages of Programs, PLoP '97 / EuroPLoP '97, Monticello,
   Illinois, September 1997, cited via
   https://en.wikipedia.org/wiki/Big_ball_of_mud, verified 2026-08-02.
5. Martin Fowler with Kent Beck, *Refactoring. Improving the Design of
   Existing Code*, first edition 1999, second edition 2018.
   https://martinfowler.com/books/refactoring.html, verified 2026-08-02.
6. G. Ann Campbell, "Cognitive Complexity," SonarSource.
   https://www.sonarsource.com/resources/cognitive-complexity/, verified
   2026-08-02.
7. Linux kernel documentation, "A Tour Through the Kernel's Coding Style,"
   section "Centralized exiting of functions."
   https://www.kernel.org/doc/html/latest/process/coding-style.html,
   verified 2026-08-02.
8. Wikipedia, "COBOL," section on the COVID-19 pandemic COBOL programmer
   shortage and IRS CARES Act payment systems.
   https://en.wikipedia.org/wiki/COBOL, verified 2026-08-02.
9. Joel Spolsky, "Things You Should Never Do, Part I,"
   joelonsoftware.com, April 2000.
   https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/,
   verified 2026-08-02.
10. Max Ogden, callbackhell.com, source at github.com/maxogden/callback-hell.
    http://callbackhell.com/, verified 2026-08-02.
11. Wikipedia, "ISO/IEC 25010," maintainability characteristic and
    sub-characteristics.
    https://en.wikipedia.org/wiki/ISO/IEC_25010, verified 2026-08-02.

## Code examples

Three languages, each showing the same order-processing flow first as
control-flow spaghetti, using the state-and-flag variant discussed in
dimension 8 as the most representative modern form, then refactored using
guard clauses and Extract Method into a small set of single-purpose
collaborators. Java is omitted from this entry in favor of Go, because the
Go example also demonstrates the historically literal, keyword-level form
of the anti-pattern using an actual goto statement, immediately followed by
its disciplined structured counterpart, which is a variant worth showing
explicitly for this specific entry.

### TypeScript

```typescript
// ANTI-PATTERN: a mutable "phase" variable drives control flow through
// a loop, and module-level state is read and written across branches
// that a reader cannot resolve without mentally simulating execution.
let stock: Record<string, number> = { "sku-1": 5, "sku-2": 0 };
let phase = "start";
let total = 0;

function processOrderSpaghetti(sku: string, qty: number, isLoyal: boolean): [number, boolean] {
  phase = "start";
  total = 0;
  while (true) {
    if (phase === "start") {
      if ((stock[sku] ?? 0) < qty) {
        phase = "reject";
      } else {
        phase = "price";
      }
    } else if (phase === "price") {
      total = qty * 10;
      phase = isLoyal ? "discount" : "commit";
    } else if (phase === "discount") {
      total = total * 0.9;
      phase = "commit";
    } else if (phase === "commit") {
      stock[sku] -= qty;
      return [total, true];
    } else if (phase === "reject") {
      return [0, false];
    }
  }
}

console.log(processOrderSpaghetti("sku-1", 3, true));

// REFACTOR: a guard clause replaces the reject branch, each remaining
// step is an explicit, independently testable collaborator, and there
// is no shared mutable phase variable to trace.
interface Inventory {
  stock: Record<string, number>;
}

function hasStock(inv: Inventory, sku: string, qty: number): boolean {
  return (inv.stock[sku] ?? 0) >= qty;
}

function reserve(inv: Inventory, sku: string, qty: number): void {
  inv.stock[sku] -= qty;
}

function price(qty: number, isLoyal: boolean, loyaltyDiscount = 0.1): number {
  const subtotal = qty * 10;
  return isLoyal ? subtotal * (1 - loyaltyDiscount) : subtotal;
}

function placeOrder(inv: Inventory, sku: string, qty: number, isLoyal: boolean): [number, boolean] {
  if (!hasStock(inv, sku, qty)) return [0, false];
  const total = price(qty, isLoyal);
  reserve(inv, sku, qty);
  return [total, true];
}

const inv: Inventory = { stock: { "sku-1": 5, "sku-2": 0 } };
console.log(placeOrder(inv, "sku-1", 3, true));
```

Both `processOrderSpaghetti` and `placeOrder` print `[ 27, true ]` for the
same input, confirming the refactor keeps the same behavior, which was
verified by compiling both with `tsc` and running the emitted output with
`node`.

### Python

```python
"""Anti-pattern: state lives in module globals and control flow moves
through a loop driven by a mutable step variable that is checked and
mutated by branches a reader must trace out of source order."""

stock = {"sku-1": 5, "sku-2": 0}
step = "start"
total = 0.0
loyal = False


def process_order_spaghetti(sku, qty, is_loyal):
    global step, total, loyal
    loyal = is_loyal
    step = "start"
    while True:
        if step == "start":
            if stock.get(sku, 0) < qty:
                step = "reject"
            else:
                step = "price"
        elif step == "price":
            total = qty * 10.0
            step = "discount" if loyal else "commit"
        elif step == "discount":
            total = total * 0.9
            step = "commit"
        elif step == "commit":
            stock[sku] -= qty
            return total, True
        elif step == "reject":
            return 0, False


print(process_order_spaghetti("sku-1", 3, True))


# Refactor: each concern is a small function with one input and one
# output, wired together by a thin, linear coordinator.
from dataclasses import dataclass, field


@dataclass
class Inventory:
    stock: dict = field(default_factory=lambda: {"sku-1": 5, "sku-2": 0})

    def has_stock(self, sku, qty):
        return self.stock.get(sku, 0) >= qty

    def reserve(self, sku, qty):
        self.stock[sku] -= qty


def price(qty, is_loyal, loyalty_discount=0.10):
    subtotal = qty * 10.0
    return subtotal * (1 - loyalty_discount) if is_loyal else subtotal


def place_order(inventory, sku, qty, is_loyal):
    if not inventory.has_stock(sku, qty):
        return 0.0, False
    total = price(qty, is_loyal)
    inventory.reserve(sku, qty)
    return total, True


inv = Inventory()
print(place_order(inv, "sku-1", 3, True))
```

Running this file with `python3` prints `(27.0, True)` twice, once for
each implementation, confirming both produce the same result for the same
input.

### Go

```go
package main

import "fmt"

// ANTI-PATTERN: the historically literal form. an unrestricted goto
// carries execution between labeled sections that a reader cannot
// order correctly without tracing every jump by hand.
var stock = map[string]int{"sku-1": 5, "sku-2": 0}
var discountApplied bool
var loyaltyChecked bool
var total float64

func processOrderSpaghetti(sku string, qty int, isLoyal bool) (float64, bool) {
	if stock[sku] < qty {
		goto fail
	}
	if isLoyal && !loyaltyChecked {
		loyaltyChecked = true
		goto applyDiscount
	}
	goto computeTotal

applyDiscount:
	if !discountApplied {
		discountApplied = true
	}
	goto computeTotal

computeTotal:
	total = float64(qty) * 10.0
	if discountApplied {
		total = total * 0.9
	}
	goto done

fail:
	return 0, false

done:
	stock[sku] -= qty
	return total, true
}

// REFACTOR: structured, single-entry single-exit collaborators, no
// goto, no shared mutable state, an explicit error return instead
// of a jump to a labeled failure section.
type Inventory struct{ stock map[string]int }

func (inv *Inventory) HasStock(sku string, qty int) bool { return inv.stock[sku] >= qty }
func (inv *Inventory) Reserve(sku string, qty int)       { inv.stock[sku] -= qty }

type PricingPolicy struct{ loyaltyDiscount float64 }

func (p PricingPolicy) Price(qty int, isLoyal bool) float64 {
	subtotal := float64(qty) * 10.0
	if isLoyal {
		subtotal *= 1 - p.loyaltyDiscount
	}
	return subtotal
}

func PlaceOrder(inv *Inventory, pricing PricingPolicy, sku string, qty int, isLoyal bool) (float64, error) {
	if !inv.HasStock(sku, qty) {
		return 0, fmt.Errorf("insufficient stock for %s", sku)
	}
	total := pricing.Price(qty, isLoyal)
	inv.Reserve(sku, qty)
	return total, nil
}

func main() {
	spaghettiTotal, spaghettiOK := processOrderSpaghetti("sku-1", 3, true)
	fmt.Println(spaghettiTotal, spaghettiOK)

	inv := &Inventory{stock: map[string]int{"sku-1": 5, "sku-2": 0}}
	pricing := PricingPolicy{loyaltyDiscount: 0.10}
	structuredTotal, err := PlaceOrder(inv, pricing, "sku-1", 3, true)
	fmt.Println(structuredTotal, err)
}
```

Running this file with `go run` prints `27 true` followed by `27 <nil>`,
confirming both implementations reserve the same quantity and compute the
same discounted total for the same input, and that the structured version
returns an idiomatic Go error rather than a bare boolean.
