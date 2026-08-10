---
name: Unix Philosophy (CUPID)
slug: unix-philosophy-cupid
family: 04-principles-and-laws
category: Design Principle
aliases: [The U in CUPID, Do One Thing Well, Narrow Interface Principle]
first_described: "Daniel Terhorst-North, CUPID. for joyful coding, dannorth.net, 10 February 2022, drawing on M. D. McIlroy, quoted in Peter H. Salus, A Quarter Century of UNIX, Addison-Wesley, 1994, chapter 2, and dated to a 1978 internal Bell Labs memorandum"
maturity: established
related: [composable, single-responsibility-principle, interface-segregation-principle, pipes-filters, keep-it-simple, low-coupling, high-cohesion, you-are-not-gonna-need-it, separation-of-concerns]
incompatible_with: []
verified: 2026-08-02
---

# Unix Philosophy (CUPID)

## 1. Name, aliases, and lineage

This entry covers the U in CUPID, the second of five code properties that
Daniel Terhorst-North named in his 2022 essay CUPID. for joyful coding
(dannorth.net/2022/02/10/cupid-for-joyful-coding/, verified 2026-08-02). CUPID
is an acronym for Composable, Unix philosophy, Predictable, Idiomatic, and
Domain-based. North proposed it as a deliberate successor to SOLID, arguing in
the same essay that SOLID's five principles describe internal code structure
while telling a reader nothing about how the code feels to work with, and that
a property-based framing, a spectrum a codebase moves along, fits how software
actually improves better than a rule-based framing, a binary pass or fail
check. The full property set and North's supporting material live at
cupid.dev, a companion site maintained by North and contributors
(https://cupid.dev/properties/unix-philosophy/, verified 2026-08-02).

North did not invent the Unix philosophy itself. He named it as a property a
unit of code can possess in greater or lesser degree, and borrowed its content
from the design culture of Bell Labs Unix in the 1970s. The two names most
commonly attached to that culture are Doug McIlroy, who invented the Unix pipe
and is credited with the tersest formulation, and Rob Pike and Brian
Kernighan, who wrote the philosophy down as working guidance for tool authors
rather than as a retrospective label. McIlroy's own words, given in an
internal Bell Labs document from 1978 and reprinted by Peter Salus, read as
follows. write programs that do one thing and do it well, write programs to
work together, write programs to handle text streams because that is a
universal interface (M. D. McIlroy, quoted in Peter H. Salus, A Quarter
Century of UNIX, Addison-Wesley, 1994, chapter 2, corroborated by the Bell
System Technical Journal Unix Time-Sharing System issue, vol. 57, no. 6, 1978,
https://en.wikipedia.org/wiki/Unix_philosophy, verified 2026-08-02). Kernighan
and Pike, in the preface to The UNIX Programming Environment, Prentice-Hall,
1984, put the same idea in terms of relationships between programs rather than
the programs themselves. the power of a system comes more from the
relationships among programs than from the programs themselves, many UNIX
programs do quite trivial things in isolation, but, combined with other
programs, become general and useful tools (Brian W. Kernighan, Rob Pike, The
UNIX Programming Environment, Prentice-Hall, 1984, preface,
https://en.wikipedia.org/wiki/Unix_philosophy, verified 2026-08-02).

A third source, later and more systematic, is Eric S. Raymond's The Art of
Unix Programming, Addison-Wesley, 2003, chapter 1. Raymond distilled the loose
oral culture around McIlroy's memo into seventeen named rules, among them the
Rule of Modularity, write simple parts connected by clean interfaces, the Rule
of Composition, design programs to be connected to other programs, the Rule of
Separation, separate policy from mechanism and separate interfaces from
engines, the Rule of Silence, when a program has nothing surprising to say it
should say nothing, and the Rule of Least Surprise, in interface design always
do the least surprising thing (E. S. Raymond, The Art of Unix Programming,
Addison-Wesley, 2003, chapter 1,
https://www.oreilly.com/library/view/the-art-of/9781098141349/c07.xhtml,
verified 2026-08-02). North's CUPID property compresses this lineage into a
single test a reader can apply to a function, module, or service, not only to
a command-line tool. does this unit do one well-bounded thing, and does it
expose a narrow enough interface that another unit can use it without reading
its internals first.

This entry treats the CUPID Unix philosophy property as the applied,
code-level reading of the older Unix design culture, and treats
[Composable](composable.md) as the sibling CUPID property that names the
outcome, units that combine cleanly, rather than the discipline that produces
it, units that stay narrow. The two properties are deliberately adjacent in
North's own ordering and are frequently invoked together, but they are not the
same claim. Composable asks can this be combined. Unix philosophy asks is this
narrow enough to be worth combining.

## 2. Problem and context

A function, class, module, or service accumulates responsibility over time
because adding one more branch to something that already exists is almost
always locally cheaper than creating a new unit and wiring it in. Each
addition is defensible on its own. the codebase as a whole slides toward units
that do several unrelated things, expose wide interfaces with many optional
parameters, and can only be understood by reading their full implementation
rather than their signature. The Unix philosophy property names the discipline
that resists this slide at the point of first design, not as a later
refactor. it asks, before a unit is written, what is the one thing this does,
and what is the narrowest surface through which something else can use it.

The context in which this matters most is exactly the context CUPID targets.
teams that read and modify each other's code constantly, where a wide,
ad-hoc interface on one unit becomes every caller's problem the moment that
unit's author moves to a different task. It matters less inside a single,
short-lived script nobody else will ever read, where the cost of a wide
interface is paid once, by the same person who created it, and never again.

## 3. Forces

The property trades initial design effort and the discipline of
decomposition against implementation speed and perceived up-front simplicity.
Splitting one function that does three things into three functions that each
do one thing, connected through explicit parameters or a pipe, costs more
typing and more decisions at the moment of writing, what exactly is the
narrow interface between these three pieces, than leaving the combined
function as it is. It pays that cost back later, when any one of the three
concerns needs to change, be tested, or be reused, because the change is now
localized to the one unit responsible for it. The property also trades
runtime cost for compositional flexibility in some readings. a shell pipeline
of five small text filters is measurably slower than one hand-fused program
doing the same five things, because each stage pays process-startup and
data-marshalling overhead the fused program does not. Raymond's own Rule of
Economy, programmer time is expensive and machine time is cheap, is the
explicit justification for accepting that cost (E. S. Raymond, The Art of Unix
Programming, Addison-Wesley, 2003, chapter 1, verified 2026-08-02), and it is
a judgement call, not a universal truth. on a genuinely hot path, the
trade-off inverts and a fused implementation is the correct choice. This entry
labels that inversion a matter of engineering judgement rather than a sourced
claim, because the correct answer depends on the actual measured cost of the
boundary in a specific system.

A second force is discoverability against composability. A narrow, single-purpose
unit is easy to understand from its signature alone, which favors
discoverability. but a system built from many narrow units pushes the burden
of understanding onto the composition, the caller now has to know how the
pieces fit together, which is a cost the Unix shell hides behind the pipe
operator and most other languages do not hide at all. The property is honest
about only doing half the job. narrowing the unit is necessary but not
sufficient. the composition mechanism, whether a pipe, a function call chain,
or a message queue, has to be equally disciplined or the narrowing does not
pay off.

## 4. Applicability and non-applicability

Reach for the Unix philosophy property when a unit's responsibility can be
named in one short sentence without the word and, when the unit will plausibly
be reused or recombined by code its author has not yet written, when the
interface between units can be expressed as a simple, well-known shape, a
byte stream, a plain data structure, a single well-typed function signature,
rather than a bespoke protocol, and when the team values the ability to test,
replace, or reason about each piece in isolation more than it values the
marginal runtime cost of the boundary between pieces.

Do not reach for it in these cases.

- **A genuinely single-purpose script or throwaway tool with one caller,
  known and fixed for its whole life.** Splitting a fifteen-line one-off
  script into three files with an interface between them adds indirection
  with no future reader who benefits from it. This is the same judgement
  [You Aren't Gonna Need It](you-are-not-gonna-need-it.md) makes about
  speculative generality.
- **A hot path where the measured cost of the interface boundary, a process
  spawn, a serialization step, an extra allocation, is the dominant cost in
  the system.** Raymond's own book concedes this with the Rule of
  Optimization, prototype before polishing, fuse only after profiling shows
  the boundary is the bottleneck, never before (E. S. Raymond, The Art of
  Unix Programming, Addison-Wesley, 2003, chapter 1, verified 2026-08-02).
- **A domain where the concerns genuinely cannot be separated without losing
  correctness**, for example a database transaction that must commit reads
  and writes atomically. splitting it into a narrow read unit and a narrow
  write unit for the sake of the property would introduce the exact race
  condition the transaction exists to prevent.
- **A team of one, working alone, on code with a lifespan shorter than the
  time it would take another person to learn the interface.** The property's
  payoff is compositional and social. it accrues to future readers and future
  callers. it has close to zero payoff when there will be neither.
- **When the narrow interface would have to encode so much shared context,
  configuration objects with dozens of fields, session state threaded
  through every call, that the interface itself becomes the wide, opaque
  thing the property exists to avoid.** A narrow signature hiding a wide,
  implicit contract is worse than an honestly wide signature, because the
  narrowness is then a lie about the unit's real coupling.

## 5. Structure

The property has three participants, none of them classes in the
object-oriented sense. a Unit, the function, CLI tool, service, or module
being evaluated, an Interface, the narrow, explicit surface through which
the unit is invoked, ideally a well-known shape such as a byte stream, a
value type, or a single typed function signature rather than a bespoke,
stateful protocol, and a Composer, whatever mechanism connects two or more
units, most often a shell pipe, a function composition, a message queue, or a
plain function call that passes one unit's output as another's input. A
fourth, implicit participant is the Policy versus Mechanism split Raymond
names as the Rule of Separation. the Unit should implement mechanism, the how,
and leave policy, the what and when, to its caller (E. S. Raymond, The Art of
Unix Programming, Addison-Wesley, 2003, chapter 1, verified 2026-08-02). A
text filter that reads bytes and transforms them is mechanism. deciding which
files to run it on is policy that belongs to the caller, typically the shell
invocation or the orchestrating script, not the filter itself.

The property is satisfied when the Unit's one responsibility can be stated
without a conjunction, the Interface exposes only what the Composer needs and
nothing about the Unit's internal state or implementation choices, and the
Unit contains no embedded policy about when or in what order it should run
relative to other units.

## 6. ASCII structure diagram

```
  BEFORE, a wide unit, no property

  +----------------------------------------+
  |            report_generator()          |
  |  reads CSV, validates rows, computes    |
  |  totals, formats currency, writes PDF,  |
  |  emails the result, logs to database    |
  +----------------------------------------+
       one call site, one unit, seven
       unrelated concerns fused together


  AFTER, narrow units, the Composer wires them

  +-----------+  bytes   +------------+  rows   +-----------+
  | read_csv  |--------->| validate   |-------->| totals    |
  +-----------+          +------------+         +-----------+
                                                       |
                                                       | totals
                                                       v
  +-----------+  pdf     +------------+  pdf    +-----------+
  | send_mail |<---------| render_pdf |<--------| format_ccy|
  +-----------+          +------------+         +-----------+

  each box, one stated responsibility, narrow typed interface
  arrows, the Composer, an explicit pipeline the caller controls
  the log-to-database concern is dropped, or becomes an
  observer the Composer wires in, never a hidden side effect
  inside any of the boxes above
```

## 7. Dynamics

At design time, the author states the Unit's responsibility as one sentence
without and. if the sentence needs and, the Unit is split at that seam before
any code is written. The author then chooses the Interface shape by asking
what is the smallest, most conventional data shape the next caller will
already understand, preferring types the language or platform already has,
a stream, a list, a plain record, over a bespoke class with getters and
setters that leak the Unit's internal representation.

At composition time, the Composer, whether a shell pipeline, a chain of
function calls, or an explicit orchestration function, decides the order and
the wiring. it, not any individual Unit, is the only place policy about
sequencing lives. A concrete pipeline dynamic looks like this in a Unix
shell, the canonical execution of the property.

```
  $ grep ERROR access.log | cut -d' ' -f1 | sort | uniq -c | sort -rn
    |          |               |         |          |
    v          v               v         v          v
  filter     select          order     count      re-order
  matching   the IP          the       repeats    by count,
  lines      column          lines                descending

  each stage, one responsibility, reads stdin, writes stdout
  the shell, the Composer, owns sequencing and data flow
  no stage knows the others exist
```

A programmatic equivalent runs the same shape in-process. a caller builds a
list or a stream, hands it to the first narrow function, and threads the
result through the next, each function ignorant of what came before it or
what comes after, exactly mirroring the shell case but inside one process
boundary.

## 8. Implementation variants

- **The Unix pipeline itself**, the literal shell composition of small
  filter programs connected by anonymous byte-stream pipes, is the reference
  implementation the property is named after and the one North points to
  directly in the CUPID material (https://cupid.dev/properties/unix-philosophy/,
  verified 2026-08-02).
- **Function composition in a general-purpose language**, chaining small,
  single-purpose functions with a language's own composition operator or by
  hand, `f(g(h(x)))` or, in languages with a pipe operator, `x |> h |> g |>
  f`, applies the same discipline without spawning a process per stage.
- **The Pipes and Filters architectural pattern**, an explicit architecture
  where each Filter has a single transformation responsibility and Pipes
  carry data between them, generalizes the shell case to a full system
  architecture rather than a single command line. see
  [Pipes and Filters](../05-architectural/pipes-filters.md) for the
  architecture-level treatment.
- **Small, single-purpose command-line tools that read stdin and write
  stdout**, the modern continuation of the original Unix toolset, `jq` for
  JSON, `sed` and `awk` for text transformation, `xargs` for argument
  fan-out, each independently maintained and composed only through the
  shell, never through direct coupling between the tools' source code.
- **Single-purpose containers wired together by an orchestrator**, where
  each container image runs one process with one responsibility and Docker's
  own guidance frames the composition explicitly. it's best practice to
  separate areas of concern by using one service per container (Docker Inc.,
  Docker documentation, Run multiple services in a container,
  https://docs.docker.com/config/containers/multi-service_container/,
  verified 2026-08-02). Kubernetes extends the same shape at the Pod level,
  where the one-container-per-Pod model is described as the most common
  Kubernetes use case, and a multi-container Pod is reserved for containers
  that are tightly coupled and need to share resources, a pattern the docs
  call a relatively advanced use case reserved for specific instances
  (Kubernetes documentation, Pods, How Pods manage multiple containers,
  https://kubernetes.io/docs/concepts/workloads/pods/#how-pods-manage-multiple-containers,
  verified 2026-08-02).
- **Single-purpose serverless functions**, where a function handler is scoped
  to one triggering event and one narrow transformation, is the same
  discipline applied at the deployment-unit granularity of a cloud platform
  rather than a process or a container.

## 9. Known production uses

- **GNU coreutils and the POSIX text-processing toolset**, `grep`, `sed`,
  `awk`, `cut`, `sort`, `uniq`, `wc`, each a narrow, single-purpose filter
  composed exclusively through shell pipes, is the direct, continuously
  maintained descendant of the Unix design culture McIlroy described in 1978
  and remains the standard toolset shipped on every Linux distribution and
  macOS (Free Software Foundation, GNU Coreutils manual,
  https://www.gnu.org/software/coreutils/manual/coreutils.html, verified
  2026-08-02).
- **`jq`**, a widely used command-line JSON processor, is designed
  specifically to be a filter in the Unix sense, reading JSON from stdin,
  applying one query or transformation, and writing JSON to stdout for the
  next stage of a pipeline, extending the classic text-stream composition
  model to structured data (jq manual, https://jqlang.org/manual/, verified
  2026-08-02).
- **Docker's single-process-per-container guidance**, cited in dimension 8
  above, is a direct, named production application of the do-one-thing
  discipline at the level of a deployable unit rather than a command-line
  program, and is Docker's own documented best practice, not a third-party
  interpretation (Docker Inc., Docker documentation, Run multiple services
  in a container, https://docs.docker.com/config/containers/multi-service_container/,
  verified 2026-08-02).
- **Kubernetes' one-container-per-Pod default**, cited in dimension 8 above,
  applies the same discipline at the orchestration layer. the Kubernetes
  project documents it as the default and most common shape, and explicitly
  reserves multi-container Pods for the narrow case of tightly coupled
  helper processes such as sidecars and init containers (Kubernetes
  documentation, Pods,
  https://kubernetes.io/docs/concepts/workloads/pods/#how-pods-manage-multiple-containers,
  verified 2026-08-02).
- **CUPID itself, as adopted guidance inside teams that have publicly
  written about restructuring code review checklists around it**, for
  example the Infrastructure as Code community's own published mapping of
  the five CUPID properties, including Unix philosophy, onto Terraform module
  design as a named, applied review discipline (Infrastructure as Code,
  Unpacking Dan North's CUPID properties for joyful coding,
  https://infrastructure-as-code.com/posts/cupid-for-infrastructure.html,
  verified 2026-08-02).

## 10. Consequences

Positive.

- Each unit can be tested in isolation with a small, enumerable set of inputs
  and outputs, because its interface is narrow and its responsibility is
  singular.
- Units can be replaced or reimplemented without touching their callers, as
  long as the narrow interface is preserved, because the Composer, not the
  Unit, owns the wiring.
- New behavior is frequently reachable by recomposing existing narrow units
  in a new order, rather than by writing new code, which is the entire
  economic case McIlroy made for the pipe in the first place.
- The one-sentence-without-and test is cheap to apply during code review and
  catches responsibility creep earlier than a metric-based check would.

Negative.

- Composition has a real, measurable runtime cost, process spawns, extra
  serialization, extra function-call indirection, that a fused implementation
  does not pay, and that cost is easy to underestimate until it is profiled.
- A system built from many narrow units pushes understanding-cost onto the
  reader who has to trace the composition, which can be harder to follow than
  one wider unit for a reader unfamiliar with the pipeline, especially when
  the Composer's wiring is implicit rather than written down in one place.
- Over-application produces the opposite failure to the one the property
  prevents. units so narrow that using any of them requires assembling four
  or five of them correctly, which just moves the complexity from inside one
  unit to the composition between many, without reducing it.
- Interfaces that are narrow in name but still leak implementation detail, a
  stream of a bespoke, undocumented record shape rather than a well-known
  type, give the appearance of the property without its benefit.

## 11. Failure modes and misuse

**Symptom.** A pull request adds a fourth optional parameter to a function
whose name still describes one thing. **Cause.** the function's actual scope
grew past its stated responsibility one small addition at a time, and nobody
re-evaluated the one-sentence test at each addition. **Fix.** split the
function at the seam the new parameter introduces, before merging, rather
than after the fifth parameter makes the split expensive.

**Symptom.** A team has dozens of tiny helper functions, and a new feature
still takes as long to build as it did before the decomposition, because
every feature requires correctly assembling six or seven of them in the right
order. **Cause.** the property was applied to the units without equal
discipline applied to the Composer. narrowing without a clear, documented
composition point just relocates the complexity. **Fix.** name and document
the composition explicitly, as a single orchestrating function or pipeline
definition, so assembling the narrow units is itself a narrow, well-known
operation rather than tribal knowledge.

**Symptom.** A shell script pipeline silently drops rows and nobody notices
for weeks, because one stage in the middle failed and the pipeline kept
running with an empty or partial stream. **Cause.** the classic and
documented weakness of the pipeline composition model, that by default a
shell pipeline's exit status reflects only the last command, masking a
mid-pipeline failure, is documented POSIX shell behavior. bash exposes
`PIPESTATUS` and `set -o pipefail` specifically to address it (GNU Bash
Reference Manual, section 6.7, Arrays,
https://www.gnu.org/software/bash/manual/bash.html, verified 2026-08-02).
**Fix.** treat pipeline failure propagation as part of the Composer's
responsibility, use `pipefail` or the language-level equivalent, and never
assume silence from an upstream stage means success.

**Symptom.** A narrow REST endpoint or function signature takes a single
config object parameter, and every caller has to read the object's full
shape to use the function correctly. **Cause.** the interface was narrowed in
arity, one parameter, without being narrowed in actual surface area, the
object still exposes everything the wide multi-parameter version did.
**Fix.** apply the property to the shape of the single parameter too, not
only to the parameter count.

## 12. Trade-off matrix

| Force | Unix Philosophy property | Single Responsibility Principle | Monolithic module, no decomposition |
|---|---|---|---|
| Runtime overhead of composition | Real and measurable, process spawn, IPC, or call indirection | Low, applies inside one process, usually one call | None, single call path |
| Testability in isolation | High, each unit has a small enumerable input and output space | High, for the same reason, scoped to class responsibility | Low, one test must exercise all combined concerns |
| Reusability across unrelated call sites | High, units compose with callers they were never written for | Moderate, classes are usually reused within their own domain | Low, the unit's behavior is bound to its one caller |
| Cognitive load to trace one feature | Higher, spread across the Composer and several units | Moderate, usually one class hierarchy | Lower for a single reader, all logic is in one place |
| Cost of a requirements change | Localized to the one affected unit | Localized to the one affected class | Global, any change risks the fused whole |
| Best granularity | Function, CLI tool, or process boundary | Class or module | Whole application, appropriate only when small |

## 13. Related and incompatible patterns

[Composable](composable.md) is the outcome CUPID's Unix philosophy property
exists to enable. a unit that is narrow and single-purpose is composable by
construction, but composability is the broader property, it also concerns
whether the Interface's types line up with the next unit's expected types,
which is a separate, additional condition beyond narrowness alone.

[Single Responsibility Principle](single-responsibility-principle.md) makes
almost the identical claim at the class level inside an object-oriented
design, one reason to change per class. The Unix philosophy property is the
same discipline applied one level up, at the boundary between deployable or
callable units rather than at the boundary between classes, and it adds the
explicit runtime-composition angle, connect through streams or narrow
function calls, that SRP does not require.

[Interface Segregation Principle](interface-segregation-principle.md) shares
the narrow-interface half of the property directly, no client should be
forced to depend on methods it does not use, which is the interface-shape
argument this entry makes in dimension 11's fourth failure mode.

[Pipes and Filters](../05-architectural/pipes-filters.md) is the
architecture-level pattern that formalizes the Composer participant named in
dimension 5 as an explicit architectural element, and is the pattern most
directly descended from the shell pipeline example in dimension 7.

[Keep It Simple](keep-it-simple.md) and
[You Aren't Gonna Need It](you-are-not-gonna-need-it.md) bound the property
from the other direction. both warn against decomposing further than the
actual, present need justifies, which is exactly the over-application failure
named in dimension 11.

[Low Coupling](low-coupling.md) and [High Cohesion](high-cohesion.md) name
the two conditions the property tries to hold simultaneously, a narrow unit
with a single, cohesive responsibility, high cohesion, connected to its
neighbors through the smallest possible interface, low coupling.

No pattern in this catalog is flatly incompatible with the property, because
it is a design discipline rather than a structural commitment. it is,
however, in active tension with any pattern whose entire value proposition is
a single, wide, do-everything facade, such as an unbounded God Object, and
the tension there is the point. the property exists specifically to prevent
that shape.

## 14. Refactoring path in and out

**Introducing the property into code that lacks it.** Start from the
one-sentence test. write, for the unit under review, the shortest possible
sentence describing what it does. If the sentence requires and, note the seam
where and appears, that is the split point. Extract the piece after and into
its own unit with its own narrow interface, typically the return value or
argument list the two pieces would naturally exchange if they were separate.
Repeat until every resulting unit's sentence has no and left in it. Then
introduce or identify the Composer, the one place that will call the newly
split units in the right order, and move any sequencing logic that was
implicit inside the original unit into that Composer explicitly. This mirrors
the classic Extract Function refactoring, described at length in Martin
Fowler, Refactoring. Improving the Design of Existing Code, 2nd edition,
Addison-Wesley, 2018, chapter 6, applied specifically at the seam the
one-sentence test surfaces rather than at an arbitrary boundary.

**Removing the property when it stops earning its place.** When a set of
narrow units is always, in every observed call site, invoked together in the
same fixed order with no independent reuse anywhere in the codebase, the
narrowness is paying its runtime and cognitive cost without collecting its
composability benefit. Inline the units back into one, following Fowler's
Inline Function, and keep the single-sentence discipline only if a genuinely
independent second caller appears later. this is a reversible decision, not
a one-way door, and reversing it is itself an application of You Aren't Gonna
Need It.

## 15. Testing and verification

A unit that satisfies the property is, almost definitionally, easy to test in
isolation. its narrow interface bounds the input space to something an
example-based or property-based test suite can enumerate or generate, and its
single responsibility means a failing test points at one concern rather than
requiring the reader to first determine which of several fused
responsibilities actually broke. The Composer becomes the harder thing to
test, because its correctness depends on the interaction of several units
rather than any one of them, and unit-level green tests for every piece do
not guarantee the composition is correct. Integration or pipeline-level
tests, asserting on the end-to-end output of the full composed sequence
against known input, are the verification technique that actually catches
composition bugs, the exact class of bug named in dimension 11's third
failure mode, a mid-pipeline stage silently failing. For shell-level
compositions specifically, verification should assert on exit status with
`pipefail` enabled, not only on the final stage's stdout, because stdout can
look correct while an earlier stage silently failed and produced a partial
stream.

## 16. Observability signals

For a narrow unit, a healthy instance in production shows a small, stable set
of input shapes and a latency distribution with a tight variance, because a
genuinely single-purpose unit is not doing conditional, branchy work that
would widen its own latency profile across call types. An unhealthy instance
shows growing branching in its logs or traces, sudden new argument
combinations appearing, or an increasingly wide latency spread, all signals
that the unit has quietly regained the responsibility creep the property was
introduced to prevent. For a Composer, the signal to watch is per-stage
timing and per-stage error rate in a trace, a well-instrumented pipeline
Composer emits one span per unit it calls, so an operator can see which
narrow unit in the chain is slow or failing without having to reason about
the fused whole. The absence of per-stage spans, one opaque span covering the
entire composed operation, is itself an observability regression that
correlates with the property having eroded at the Composer level even if
each individual unit still looks narrow in isolation.

## 17. Security and privacy implications

A narrow interface reduces the attack surface a caller can exploit, because
there are fewer parameters, fewer optional code paths, and fewer implicit
behaviors triggered by unexpected input combinations, which is the same
argument that motivates the security principle of least privilege applied to
API design rather than to user permissions. The composition side introduces
its own, distinct risk. data passed between units through a shared, generic
channel, a Unix pipe, an in-memory queue, a plain data structure, carries
whatever the previous unit produced without the receiving unit necessarily
validating it, on the assumption that narrow, well-tested units upstream have
already done so. This assumption fails when one unit in a long-lived,
frequently modified pipeline is a new or third-party addition that has not
been through the same scrutiny as the original units, and the classic shell
injection class of vulnerability, where a value assumed to be plain text data
is instead interpreted as a command by a downstream stage, is a direct,
well-documented instance of a Composer trusting an Interface's contents
without validating them (OWASP, OS Command Injection,
https://owasp.org/www-community/attacks/Command_Injection, verified
2026-08-02). The property itself is silent on validation. it narrows what a
unit does, not what it must check before doing it, so the practical
implication is that each unit in a composed chain still needs its own input
validation at its boundary, the narrowness of the interface does not
substitute for that.

## 18. References

1. Daniel Terhorst-North, CUPID. for joyful coding, Dan North & Associates
   Limited, 10 February 2022,
   https://dannorth.net/2022/02/10/cupid-for-joyful-coding/, verified
   2026-08-02.
2. Daniel Terhorst-North and contributors, Unix Philosophy, CUPID. for
   joyful code, https://cupid.dev/properties/unix-philosophy/, verified
   2026-08-02.
3. Peter H. Salus, A Quarter Century of UNIX, Addison-Wesley, 1994, chapter
   2, records the M. D. McIlroy 1978 formulation.
4. Bell System Technical Journal, Unix Time-Sharing System, vol. 57, no. 6,
   1978, cited via https://en.wikipedia.org/wiki/Unix_philosophy, verified
   2026-08-02.
5. Brian W. Kernighan, Rob Pike, The UNIX Programming Environment,
   Prentice-Hall, 1984, preface.
6. Eric S. Raymond, The Art of Unix Programming, Addison-Wesley, 2003,
   chapter 1, https://www.oreilly.com/library/view/the-art-of/9781098141349/c07.xhtml,
   verified 2026-08-02.
7. Docker Inc., Run multiple services in a container, Docker documentation,
   https://docs.docker.com/config/containers/multi-service_container/,
   verified 2026-08-02.
8. Kubernetes documentation, Pods, How Pods manage multiple containers,
   https://kubernetes.io/docs/concepts/workloads/pods/#how-pods-manage-multiple-containers,
   verified 2026-08-02.
9. Free Software Foundation, GNU Coreutils manual,
   https://www.gnu.org/software/coreutils/manual/coreutils.html, verified
   2026-08-02.
10. jq manual, https://jqlang.org/manual/, verified 2026-08-02.
11. Infrastructure as Code, Unpacking Dan North's CUPID properties for
    joyful coding, https://infrastructure-as-code.com/posts/cupid-for-infrastructure.html,
    verified 2026-08-02.
12. GNU Bash Reference Manual, section 6.7, Arrays, PIPESTATUS and
    pipefail, https://www.gnu.org/software/bash/manual/bash.html, verified
    2026-08-02.
13. OWASP, OS Command Injection,
    https://owasp.org/www-community/attacks/Command_Injection, verified
    2026-08-02.
14. Martin Fowler, Refactoring. Improving the Design of Existing Code, 2nd
    edition, Addison-Wesley, 2018, chapter 6, Extract Function, Inline
    Function.

## Code

### TypeScript. narrow function composition

```typescript
// Each function does one thing. the pipe composes them, owning the order.
type Fn<A, B> = (a: A) => B;

function pipe<A, B, C>(f: Fn<A, B>, g: Fn<B, C>): Fn<A, C> {
  return (a: A) => g(f(a));
}

const parseLines: Fn<string, string[]> = (text) => text.split("\n").filter(Boolean);
const keepErrors: Fn<string[], string[]> = (lines) => lines.filter((l) => l.includes("ERROR"));
const extractIps: Fn<string[], string[]> = (lines) => lines.map((l) => l.split(" ")[0]);
const countByIp: Fn<string[], Map<string, number>> = (ips) => {
  const counts = new Map<string, number>();
  for (const ip of ips) counts.set(ip, (counts.get(ip) ?? 0) + 1);
  return counts;
};

const analyzeErrors = pipe(
  pipe(pipe(parseLines, keepErrors), extractIps),
  countByIp
);

const log = "1.2.3.4 ERROR bad\n5.6.7.8 INFO ok\n1.2.3.4 ERROR bad\n";
console.log([...analyzeErrors(log).entries()]);
```

### Python. small filters composed by a Composer function

```python
from typing import Iterable, Iterator


def parse_lines(text: str) -> Iterator[str]:
    for line in text.splitlines():
        if line:
            yield line


def keep_errors(lines: Iterable[str]) -> Iterator[str]:
    for line in lines:
        if "ERROR" in line:
            yield line


def extract_ip(lines: Iterable[str]) -> Iterator[str]:
    for line in lines:
        yield line.split(" ")[0]


def analyze_errors(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ip in extract_ip(keep_errors(parse_lines(text))):
        counts[ip] = counts.get(ip, 0) + 1
    return counts


if __name__ == "__main__":
    log = "1.2.3.4 ERROR bad\n5.6.7.8 INFO ok\n1.2.3.4 ERROR bad\n"
    print(analyze_errors(log))
```

### Go. a Unix-style filter reading stdin, writing stdout

```go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// filterErrors does one thing. it copies lines containing "ERROR"
// from an input stream to an output stream. it knows nothing about
// files, sockets, or its caller. that is the Composer's job.
func filterErrors(in *bufio.Scanner, out *bufio.Writer) error {
	for in.Scan() {
		line := in.Text()
		if strings.Contains(line, "ERROR") {
			if _, err := fmt.Fprintln(out, line); err != nil {
				return err
			}
		}
	}
	return in.Err()
}

func main() {
	scanner := bufio.NewScanner(strings.NewReader(
		"1.2.3.4 ERROR bad\n5.6.7.8 INFO ok\n1.2.3.4 ERROR bad\n",
	))
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	if err := filterErrors(scanner, writer); err != nil {
		fmt.Fprintln(os.Stderr, "filterErrors:", err)
		os.Exit(1)
	}
}
```
