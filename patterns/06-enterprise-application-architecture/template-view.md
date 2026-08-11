---
name: Template View
slug: template-view
family: 06-enterprise-application-architecture
category: Web Presentation
aliases: [Server Page, Scripted Page]
first_described: "Fowler 2002"
maturity: canonical
related: [transform-view, two-step-view, page-controller, front-controller, transaction-script, model-view-controller, application-controller]
incompatible_with: []
verified: 2026-08-02
---

# Template View

## 1. Name, aliases, and lineage

The canonical name is Template View. Martin Fowler catalogs it in *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, ISBN 0321127420, in
the View patterns chapter, chapter 14 in the book's online catalog numbering
(Martin Fowler, ["Template View"](https://martinfowler.com/eaaCatalog/templateView.html),
verified 2026-08-02). The catalog states the intent of the pattern in one line,
quoted directly, "Renders information into HTML by embedding markers in an HTML
page" (same source). That single sentence is the whole design decision. Start
from a document that already looks like the output, and cut holes in it for the
parts that change.

The two names above are engineering-community terms, not phrases Fowler applies
to the pattern by that word in the catalog entry itself, and this paragraph is
labelled as such rather than dressed up as a sourced claim. Practitioners who
build with JavaServer Pages, Active Server Pages, PHP, or Embedded Ruby refer to
the file they write as a **server page**, because the mechanism runs on the
server and produces a page, and the source file mixes literal output text with
program fragments, which people commonly call a **scripted page**. Neither term
appears as a formal alias inside the PoEAA catalog text, and a reader who wants
the sourced name should use Template View.

Template View has one direct sibling in the same chapter that solves the
identical problem from the opposite direction. Transform View walks the domain
data and, for each piece of data, decides what markup to produce, so control
flows from data to markup. Template View starts from the markup and, at each
marker, asks the data for a value, so control flows from markup to data. Fowler
places both in the View patterns chapter and treats them as two answers to one
question, which output mechanism a system chooses for turning a domain result
into an HTML response. The pattern also composes with Two Step View, which adds
a second rendering pass so the same domain content can produce more than one
final layout, and with Application Controller, which factors flow and layout
decisions out of the individual page so a page focuses only on rendering.

A distinct thing that gets called "templating" and is not Template View in the
Fowler sense is a build-time or component-tree renderer, the kind found in
React, Vue, or Svelte, where a component function returns a tree of elements
that a runtime reconciles against a previous tree. Those systems compile markup
generation into a function call graph rather than filling markers inside a
static document, and the closer analogue for them is Transform View, because
control starts at the data and the component decides what to render, not the
markup deciding what value to pull. The distinguishing test for the whole
family, used through the rest of this entry, is where the file that a
non-programmer could open in a text editor and still make sense of the layout.
If such a file exists and the code lives inside markers cut into it, the system
is Template View. If the file that exists is a program and the markup is a
return value inside it, the system is Transform View or something adjacent to
it.

## 2. Problem and context

A system has finished computing a result, a customer record, a list of orders,
a search result set, and now has to turn that result into an HTML document a
browser can render. The shape of the output is close to static. A header, a
navigation strip, a table structure, a footer, and only a handful of cells or
rows actually change from one request to the next. Writing the HTML generation
in ordinary program code, string concatenation, print statements, a sequence of
calls that each append a fragment, works, and it is exactly the failure mode
this pattern exists to remove. Every literal angle bracket, every closing tag,
every attribute quote becomes a string literal buried inside a function, and a
person who edits HTML for a living, not a programmer, cannot open that function
and change the page layout without also understanding the surrounding program.

The problem sharpens once a design team is involved. A designer produces a
static HTML mockup in an ordinary editor. Somebody now has to turn that mockup
into the page that actually renders live data. If the mechanism available is
"call print for every line", the mockup gets manually retyped as a sequence of
program statements, and every future design change requires that retyping to
happen again, in both directions, mockup to code and later back when the
mockup changes. The context that makes Template View the right answer is
specifically this. The desired output is closer in shape to a document than to
a computation, the people who edit that document's layout are not always the
people who write the surrounding application logic, and the number of dynamic
insertion points is small relative to the amount of static structure around
them.

The pattern is also a direct response to how early web application platforms
were built. Fowler's catalog places Template View in the context of a system
that already has a domain layer producing results, a controller layer routing
requests, per Front Controller or Page Controller, and a remaining question of
how the last mile from domain result to bytes on the wire happens. Template
View answers that question by keeping the document as the primary artifact and
letting a small template engine walk it once per request, substituting markers
for values pulled from whatever object the controller handed the template.

## 3. Forces

**Document fidelity against program structure.** A template that stays close
to the final HTML preserves round-tripping with design tools and lets a
non-programmer make layout edits, but every piece of program logic embedded
inside that document, a loop, a conditional, a nested loop, degrades the
document's structure and makes the file harder to open in an ordinary HTML
editor without breaking the markers. Template View trades toward document
fidelity and accepts that logic embedded in markup is uglier logic than the
same logic in a real program file.

**Separation of concerns against the shortest path.** The stated goal of the
pattern family is to keep presentation separate from domain logic, yet the
mechanism, script tags mixed directly into markup, hands a template author the
shortest possible path to reaching into the domain layer from inside the page,
because the scripting language available inside the markers is the same
language the rest of the system is written in. Nothing at the language level
stops a template from opening a database connection. The separation Template
View delivers is a discipline the team maintains, not a boundary the mechanism
enforces.

**Compile-time safety against runtime discovery.** A template rendered by an
interpreter that walks the document at request time will not catch a
misspelled marker name, a wrong argument count, or a type mismatch until a
request actually exercises that code path, sometimes in production, on a page
nobody had reason to hit during testing. A template compiled ahead of time into
a real function in a real language, the approach several modern engines take,
recovers that class of error at build time, at the cost of a build step and a
generated-code layer between the template source and the running program.

**Latency and cost against expressiveness.** An interpreted marker-substitution
pass over a document is fast for the common case, a handful of variable
insertions and one or two loops, and a naive line-by-line interpreter is
cheap to write and cheap to run for that case. Rich control flow, several
levels of nested conditionals and loops, several includes, several helper
calls, pushes the interpreted engine's per-request cost up in a way a compiled
template mostly avoids, because compilation amortizes the parsing cost across
every subsequent render.

**Operability and team topology.** A single file that both a designer and a
programmer can open, understand, and separately edit reduces the coordination
tax between the two roles, and this is the force the pattern most directly
optimizes for. The cost lands on operability instead, because a template that
has quietly grown business logic inside it becomes a file that only a
programmer can safely touch, and the team has lost the exact benefit the
pattern was chosen to buy.

## 4. Applicability and non-applicability

Reach for Template View when the output is document-shaped, most of the
content per request is static structure, the dynamic portions are localized
insertions rather than structural decisions, and a workflow exists, or should
exist, where a designer edits layout independently from a programmer editing
data access. It also fits well as the final rendering stage sitting behind a
Front Controller or Page Controller, where routing and data assembly already
happened and the remaining job is strictly "fill this document in".

Non-applicability, and this list matters more than the first one.

- **Do not reach for Template View when the response's structure itself
  varies by branch of the request**, for example an API that returns a
  completely different JSON or XML shape depending on the caller's Accept
  header or feature flag. A marker-substitution model assumes one static
  document shape with holes in it. When the shape is the variable, Transform
  View, which builds the output from the data outward, fits the problem
  better, because the code, not the document, decides the structure.
- **Do not reach for it for a machine-to-machine payload with no document
  identity**, most JSON API responses. There is no design artifact anybody
  hand-edits in a text editor, and there is no visual layout to preserve, so
  the entire benefit the pattern exists to deliver does not apply. A direct
  serializer or an object mapper working from the domain model is a better
  fit, and is closer to what Transform View or a plain data mapper does.
- **Do not reach for it when the page contains meaningful conditional
  business logic**, an order total that changes calculation strategy by
  customer tier, a discount rule with several branches, an eligibility check
  spanning multiple domain objects. That logic belongs in the domain layer or
  in an Application Controller sitting in front of the page, computed once
  and handed to the template as a plain value or a small view model. A
  template that recomputes business rules inline is doing domain work in the
  presentation layer, which is exactly the coupling the pattern was supposed
  to prevent.
- **Do not reach for it in a single-page application whose rendering
  happens client-side against a virtual DOM.** The document-with-holes model
  assumes a server producing a finished document per request. A client-side
  component tree recomputed on every state change is closer to Transform
  View's control flow, data decides structure, run through a different
  runtime entirely, and forcing a marker-substitution mental model onto that
  runtime produces awkward code on both sides.
- **Do not reach for it when the team has no workflow separating design
  edits from logic edits.** If one person does both jobs and no design tool
  ever touches the file, document fidelity buys nothing, and a component or
  function-based view, closer to Transform View, removes the marker-parsing
  overhead for no corresponding loss.
- **Do not reach for it as the sole defense against logic creeping into
  the view.** The mechanism does not prevent embedding arbitrary code inside
  the markers, so a team that adopts Template View expecting the pattern
  itself to enforce separation of concerns will be disappointed the first
  time somebody under deadline pressure writes a database query directly into
  a page.

## 5. Structure

The participants, named by the role each plays rather than by a generic class
name.

- **Template Source.** The document on disk, an HTML file with markers cut
  into it. This is the artifact a designer opens. It owns the document's
  static structure, and it owns nothing about how a marker's value is
  computed.
- **Marker.** A syntactic unit inside the Template Source that stands for
  something dynamic, a variable reference, a loop start and end pair, a
  conditional start and end pair, an include of another template. A marker
  language defines the grammar these follow, `{{ }}`, `<% %>`, `@`, `{% %}`,
  and each engine picks its own.
- **Template Engine.** The component that reads the Template Source and
  produces output. In the interpreted variant it walks the document at
  request time. In the compiled variant it translates the document, ahead of
  time, into a real function in the host language, and that generated
  function is what runs per request.
- **Context, or Model.** The data handed to the engine for a given render,
  usually a plain object, a map, or a small view model assembled specifically
  for this page. The Context is the boundary between the domain layer and the
  view. A marker resolves against the Context, never against the domain layer
  directly, in a disciplined implementation, though nothing in the mechanism
  enforces that boundary.
- **Rendered Output.** The final byte stream, HTML in the overwhelming
  majority of real deployments, handed back to whatever called the engine, a
  controller in an MVC arrangement, a servlet container, an HTTP handler.
- **Layout or Master Template, optional.** A wrapping Template Source that
  supplies the page chrome, the head, the navigation, the footer, and
  includes or yields to a content-specific template for the body. Present in
  most production engines, absent from the minimal form of the pattern.

## 6. ASCII structure diagram

```
                     +---------------------------+
                     |       Template Source       |
                     |  (static HTML + markers)    |
                     +---------------+-------------+
                                     |
                                     |  read once (compiled)
                                     |  or every request (interpreted)
                                     v
+----------------+       +---------------------------+
|    Context     |------>|       Template Engine       |
| (view model /  |       |  parses markers, resolves    |
|  domain data)  |       |  each against the Context    |
+----------------+       +---------------+-------------+
                                     |
                                     v
                     +---------------------------+
                     |       Rendered Output        |
                     |     (finished HTML bytes)    |
                     +---------------+-------------+
                                     |
                                     v
                     +---------------------------+
                     |   Caller (Controller /       |
                     |   Front Controller /         |
                     |   HTTP handler)               |
                     +---------------------------+
```

## 7. Dynamics

A request arrives at whatever routes it, typically a Front Controller or a
Page Controller. That controller runs the necessary domain logic, gathers a
result, and assembles a Context, either the domain objects directly or a
small view model built specifically to keep the template from reaching too
deep into the domain layer. The controller hands the Context and the name of
a Template Source to the Template Engine and asks for a render.

```
Client        Controller       Template Engine       Template Source     Context
  |               |                    |                     |             |
  |  GET /order/9 |                    |                     |             |
  |-------------->|                    |                     |             |
  |               | run domain logic   |                     |             |
  |               |------------------->|                     |             |
  |               | build Context      |                     |             |
  |               | render(view, ctx)  |                     |             |
  |               |------------------->|                     |             |
  |               |                    |  load or use cached |             |
  |               |                    |  compiled template   |             |
  |               |                    |-------------------->|             |
  |               |                    |  walk static text,   |             |
  |               |                    |  hit marker          |             |
  |               |                    |  resolve marker------------------>|
  |               |                    |<------------------------------------
  |               |                    |  write value,         |             |
  |               |                    |  continue walk        |             |
  |               |                    |  (repeat per marker,  |             |
  |               |                    |   incl. loop bodies)  |             |
  |               |<-------------------|                     |             |
  |               | rendered HTML      |                     |             |
  |<--------------|                    |                     |             |
```

Two variants change one detail of this sequence. In the interpreted variant,
"load or use cached compiled template" is instead "parse the Template Source
text and interpret it directly", repeated on every render unless the engine
caches the parsed intermediate structure. In the compiled variant, an earlier,
separate build step, either at application startup or as a compile-time
tooling pass, translates the Template Source once into a real function in the
host language, and the sequence above becomes a plain function call passing
the Context as an argument, with no parsing at request time at all.

A loop marker introduces a nested repetition of the resolve-and-write step for
each item in a collection pulled from the Context, and a conditional marker
introduces a branch that either walks or skips the enclosed section of the
Template Source. Both are shown as "repeat per marker" above rather than drawn
out fully, because the shape is the same operation recursing over the
document's remaining text.

## 8. Implementation variants

**Interpreted, tag-based scripting.** The original and still the most common
form. JavaServer Pages, classic Active Server Pages, PHP's native mode, and
Embedded Ruby all embed a full scripting language inside `<% %>` or `<?php ?>`
style tags, and the engine parses and evaluates the surrounding text and the
scripted fragments together at request time, or after compiling the page once
into an intermediate form the platform caches. JSP specifically is compiled by
the servlet container into a real Java servlet class the first time the page
is requested, then reused, which places JSP on the boundary between
interpreted and compiled, closer to compiled in steady-state operation
(Wikipedia, ["JavaServer Pages"](https://en.wikipedia.org/wiki/JavaServer_Pages),
verified 2026-08-02, quoting the page directly, "JSP allows Java code and
certain predefined actions to be interleaved with static web markup content,
such as HTML", and noting the page can serve "as the view component of a
server-side model-view-controller design").

**Logic-less or restricted-grammar templating.** A reaction to the discovery
that unrestricted scripting inside markers reliably grows into full
application logic over time. Mustache and its descendants, including the
Handlebars family, deliberately omit arbitrary expression evaluation from the
marker grammar, allowing only variable substitution, section iteration, and
conditional sections, so a template cannot compute anything the Context did
not already provide. This is a direct structural response to the separation
of concerns force from dimension 3, trading expressiveness for a hard
guarantee that logic cannot leak into the template.

**Compiled expression templates with type checking.** Razor, used by ASP.NET
Core, compiles a `.cshtml` file into a real C# class at build time, with each
marker becoming a statement in a generated `ExecuteAsync` method, so a
misspelled property name on the Context, called the Model in Razor's own
terms, fails at compile time rather than at request time (Microsoft Learn,
["Razor syntax reference for ASP.NET Core"](https://learn.microsoft.com/en-us/aspnet/core/mvc/views/razor),
verified 2026-08-02, describing the `@` transition character and stating that
the generated class overrides `ExecuteAsync` and calls `Write` for each
expression). This variant answers the compile-time safety force from
dimension 3 directly, at the cost of a build or first-request compilation
step.

**Text-substitution templates driven by a language's own templating
grammar embedded in an in-language string.** Django's template language and
Rails' ERB both parse the Template Source as a string using a dedicated
grammar, `{{ }}` for variables and `{% %}` for tags in Django, `<%= %>` for
expressions in ERB, and both explicitly separate the template grammar from
the host language's own syntax, so a template author writes template
directives, not raw Python or raw Ruby, inside the markers (Django
documentation, ["Templates"](https://docs.djangoproject.com/en/5.2/topics/templates/),
verified 2026-08-02, stating "A template contains the static parts of the
desired HTML output as well as some special syntax describing how dynamic
content will be inserted"; Ruby on Rails Guides,
["Layouts and Rendering in Rails"](https://guides.rubyonrails.org/layouts_and_rendering.html),
verified 2026-08-02, showing property access through `<%= book.title %>`
markers and stating that rendering is performed by
`ActionView::Template::Handlers`).

**Standard-library, precompiled, context-escaping templates.** Go's
`html/template` package parses a template into an internal tree once and
executes that tree against any Go value passed at call time, and, distinct
from every variant above, the package tracks the HTML, JavaScript, CSS, or URL
context each marker sits inside and escapes the substituted value accordingly
by default, closing an entire class of injection defect that other engines
leave to the template author's discipline. This variant is exercised directly
in dimension 8's code sample below.

## 9. Known production uses

- **The Java Servlet and JSP platform.** JSP is defined by the Jakarta Server
  Pages specification and is compiled into a servlet by the container on
  first request, then reused for subsequent requests, commonly deployed as
  the view layer of the Model 2 architecture, where JavaBeans hold the model
  and a servlet or a framework such as Apache Struts acts as the controller
  (Wikipedia, ["JavaServer Pages"](https://en.wikipedia.org/wiki/JavaServer_Pages),
  verified 2026-08-02).
- **Ruby on Rails, through ActionView and ERB.** Every Rails controller
  action that renders HTML hands a set of instance variables to an ERB
  template under `app/views`, and the template embeds Ruby expressions
  directly with `<%= %>` markers to produce the response body (Ruby on Rails
  Guides, ["Layouts and Rendering in Rails"](https://guides.rubyonrails.org/layouts_and_rendering.html),
  verified 2026-08-02).
- **Django, through its own template engine.** Django ships a dedicated
  template language, distinct from Python itself, that parses `{{ variable
  }}` and `{% tag %}` markers out of a template file and resolves them
  against the context dictionary a view function supplies (Django
  documentation, ["Templates"](https://docs.djangoproject.com/en/5.2/topics/templates/),
  verified 2026-08-02).
- **ASP.NET Core, through Razor.** Razor views under `Views/` combine C#
  and HTML using `@` as the transition character, are compiled to a class
  deriving from `RazorPage<TModel>`, and the model type available through the
  `Model` property inside the markup is set with an `@model` directive
  (Microsoft Learn, ["Razor syntax reference for ASP.NET Core"](https://learn.microsoft.com/en-us/aspnet/core/mvc/views/razor),
  verified 2026-08-02).

Four independently maintained, widely deployed platforms, spanning Java, Ruby,
Python, and C#, each implement the same core idea from dimension 1, a static
document with embedded markers resolved against a supplied context, which is
the strongest evidence available that Template View names a real, recurring
architectural decision and not an academic abstraction invented for a catalog.

## 10. Consequences

Positive.

- A document that stays close in shape to the actual output, so a designer's
  mockup and the live template differ mainly in the presence of markers, not
  in overall structure, lowering the cost of keeping design and
  implementation aligned over the life of a project.
- A clean division of labor between the person editing layout and the person
  editing data access logic, when the team actually maintains that division.
- Familiar tooling. Most editors, linters, and syntax highlighters already
  understand HTML, and the marker grammars used by production engines are
  designed to sit inside HTML without breaking that tooling for the
  surrounding markup.
- A natural place to apply context-aware output escaping, as `html/template`
  demonstrates, because the engine already knows, from parsing the
  surrounding markup, whether a given marker sits inside an attribute, inside
  a script block, or inside plain text, and can escape accordingly.

Negative.

- The mechanism sets no boundary against embedding real program logic inside
  the markers, and every scripting-tag engine listed in dimension 8 allows a
  template author to reach arbitrarily deep into the application, which is
  the single most cited real-world failure of this pattern and is developed
  fully in dimension 11.
- A template with several nested loops and conditionals reads worse than the
  equivalent logic in a normal program file, because the markers interrupt
  the reader's flow at every insertion point, and most marker grammars have
  no first-class support for extracting a repeated fragment into a named,
  reusable unit without introducing a partial or include mechanism on top of
  the base pattern.
- Interpreted variants re-parse or re-walk the document on every request
  unless the engine caches a parsed intermediate form, which is an
  operational detail a team has to verify rather than assume, and a template
  engine misconfigured to skip that caching becomes a measurable per-request
  cost under load.
- Type errors and missing-property errors in an interpreted, dynamically
  typed marker grammar surface at request time, sometimes only on a rarely
  hit code path, rather than at build time, which the compiled variants in
  dimension 8 exist specifically to correct.

## 11. Failure modes and misuse

**Symptom.** A production incident traces back to a SQL query, or a call
into a repository or service layer, sitting directly inside a template file,
and nobody on the current team remembers writing it or can explain why it is
there.
**Cause.** The scripting tags available inside the marker grammar run the
same language as the rest of the application, so nothing in the mechanism
distinguishes "a value the controller already computed" from "a fresh call
into the domain layer made from inside the view", and under deadline pressure
the shortest path from "I need this value on the page" to "the page shows the
value" is often to fetch it directly inside the template rather than to
route it through the controller.
**Fix.** Move to a logic-less or restricted-grammar engine, from dimension 8,
that structurally cannot express a data-access call inside a marker, or, if
staying on a full-scripting engine, add a static analysis rule or a code
review checklist item that flags any import of a repository, service, or
database client type inside a template file.

**Symptom.** Page render time grows noticeably worse after a release with no
corresponding change to the amount of data being rendered, and profiling
shows time spent inside the template engine's own parsing routines rather
than inside application code.
**Cause.** The template engine is configured, or defaults, to reparse the
Template Source on every request instead of caching a parsed or compiled
representation, and a low-traffic development environment never surfaced the
cost because request volume was too low to notice.
**Fix.** Verify and, where necessary, explicitly enable the engine's template
cache in the production configuration profile, and add a load test that
specifically measures per-request template render time under sustained
traffic before shipping a template-heavy feature.

**Symptom.** A cross-site scripting report comes in against a page that
renders user-supplied data, and the offending marker is a plain, unescaped
variable substitution that a developer assumed was safe because "it is only
displaying a name".
**Cause.** The engine in use performs no automatic output escaping, or
escapes by default only in some marker forms and not others, for example an
engine that escapes `{{ }}` but exposes a separate raw-output marker that a
developer reached for out of habit or copy-paste without weighing the
context. Several widely used scripting-tag engines from dimension 8 make raw
output the default and require an explicit escaping call, which inverts the
safe-by-default posture a team usually wants.
**Fix.** Move to an engine that escapes by default and requires an explicit,
visibly different marker for raw, unescaped output, and audit every existing
raw-output marker in the codebase as a one-time cleanup pass, treating each
one as a finding until proven safe.

**Symptom.** A file that started as a small, readable template has grown past
several hundred lines, contains loops nested three or four deep, and the last
few people who touched it each added one more conditional rather than
restructuring it, because nobody wants to be the one who breaks the page.
**Cause.** The pattern gives no natural signal for when a template has
outgrown its role, unlike a program function, where length and cyclomatic
complexity are visible and commonly tracked, because a template is
conventionally exempt from the same code-quality tooling applied to the rest
of the codebase.
**Fix.** Extract the repeated or deeply nested fragment into a named partial
or include, treat the extraction as the exact analogue of Extract Method
inside program code, per dimension 14, and, where the team has linting
infrastructure for other languages, add a template-specific line-count or
nesting-depth check to CI so the same growth in the next file is caught
before it becomes several hundred lines.

## 12. Trade-off matrix

| Force | Template View | Transform View | Model View Controller (Front Controller + Transform View or Template View combined) |
|---|---|---|---|
| Document fidelity for a designer's mockup | High. The template starts as the document and stays close to it. | Low. There is no standalone document artifact, the markup is generated by code. | Depends entirely on which view mechanism MVC's view layer uses underneath. |
| Structural variance in the output shape | Poor fit. A marker grammar assumes one document shape with holes, per dimension 4. | Strong fit. Control starts at the data, so the code decides structure per response. | Same as Transform View when that is the underlying view mechanism, same as Template View otherwise. |
| Compile-time safety on marker or expression errors | Varies by engine, strong for Razor and compiled engines, weak for interpreted ones, per dimension 8. | Strong, when the transform is written in a statically typed host language. | Inherited from whichever view mechanism sits underneath the controller layer. |
| Separation of view from domain logic | Weak as a mechanism guarantee, strong only as team discipline, per dimension 10 and 11. | Comparable in the general case, though the transform function is at least a normal program artifact subject to normal code review. | Improved relative to either pattern alone, because Front Controller or Page Controller centralizes the domain call, per dimension 13. |
| Learning curve for a non-programmer editing layout | Low, the file already looks like HTML. | High, layout changes require reading and understanding code. | Inherited from the underlying view mechanism. |
| Runtime cost per request, interpreted form | Moderate, one parse-and-walk pass unless cached, per dimension 11. | Comparable, one function call producing markup. | Inherited from the underlying view mechanism. |

## 13. Related and incompatible patterns

**Transform View.** The direct sibling described in dimension 1. Both solve
"how does a domain result become markup", from opposite control-flow
directions. A system commonly uses Template View for the bulk of its
human-facing pages and Transform View for machine-facing formats, XML feeds,
export files, generated configuration, where the output shape genuinely
varies by branch rather than staying fixed with holes cut into it.

**Two Step View.** Composes cleanly with Template View by adding a second
rendering pass. The first pass produces a logical, presentation-independent
representation of the content, and a second Template View, or Transform View,
turns that representation into the final HTML, letting one content-producing
step feed several different final layouts. A team building a page for both a
desktop layout and a constrained mobile layout from the same underlying
content is a direct instance of this composition.

**Front Controller and Page Controller.** Both sit upstream of Template View
in a typical request flow, described in dimension 7's dynamics, and both
supply the Context the template resolves markers against. Neither pattern
requires Template View specifically, either works equally well handing its
result to a Transform View instead, and the choice of which view mechanism
sits downstream is independent of the choice between Front Controller and
Page Controller for routing.

**Application Controller.** Complements Template View directly by taking flow
and layout decisions, which page comes next, which layout wraps this content,
out of the individual template and out of the individual controller action,
so a template's job narrows further, to rendering a Context it was handed,
with no responsibility for deciding what happens after the render completes.

**Model View Controller.** Template View is one candidate implementation for
the View role inside an MVC arrangement, not a competitor to MVC itself. MVC
describes a division of responsibility among three roles, and Template View
describes one concrete mechanism for fulfilling the View role, alongside
Transform View as the alternative mechanism for the same role.

No pattern in this family is structurally incompatible with Template View. The
closest thing to a conflict is a decision, not a pattern, choosing a
client-rendered, component-tree front end for a given surface, which pulls
that surface's rendering responsibility toward the Transform View style of
control flow and away from server-side marker substitution, without making
either mechanism impossible to combine with the other inside one larger
system.

## 14. Refactoring path in and out

**Introducing Template View into code that currently builds HTML through
string concatenation.** Start with the single worst offender, usually the
largest or most frequently changed page, and identify every literal string
fragment currently appended in program order. Reassemble those literal
fragments into one contiguous document, in the order they are appended, with
a marker placed at each spot where a computed value or a loop currently
interrupts the literal text. This step is a direct application of Extract
Method's inverse, pulling structure out of a function's control flow and back
into a data artifact, and it should be done one page at a time, verified
against the existing rendered output before moving to the next page, so a
regression in one page's markup is caught immediately rather than discovered
across several pages at once. Once the document exists as a template, wire
the calling code to pass a Context object rather than continue building the
string directly, and delete the concatenation code only after the template
render has been verified byte-for-byte, or close to it, against a captured
sample of the old output.

**Removing Template View when it has stopped earning its place.** The signal
that a specific template should come out is usually one of the two symptoms
from dimension 11, either it has accumulated real domain logic inside its
markers, or its structural complexity, nested loops and conditionals, has
made it harder to read than the equivalent code would be as a normal program
function. The removal path mirrors the introduction path in reverse for the
logic-leak case. Extract every domain call currently inside the template into
the controller or the domain layer, so the template goes back to pure
substitution, then judge again whether the remaining template is worth
keeping in that form. For the structural-complexity case, the correct
response is usually not full removal but Extract Partial, pulling the
complicated inner section into its own smaller template included from the
parent, which is the templating-world analogue of Extract Method and often
resolves the complaint without abandoning the pattern at all. Full removal, in
favor of a Transform View written as a normal function, is worth doing only
when the page's output shape has genuinely become variable by branch rather
than fixed with holes, matching the non-applicability criteria from dimension
4.

## 15. Testing and verification

The Context, being a plain object or map in every variant listed in dimension
8, is the natural seam for a template's own unit test. A test constructs a
Context directly, without touching the controller, the domain layer, or an
HTTP request at all, hands it to the Template Engine, and asserts against the
rendered output string, either an exact match for a small template or a
substring or DOM-fragment assertion for a larger one. This is genuinely
easier because of the pattern, compared against testing the equivalent
string-concatenation code, because the render call is a pure function of the
Context in the common case, with no hidden dependency on request state,
session state, or a live domain layer, assuming the template itself contains
no logic that reaches outside the Context, which loops back to the discipline
question from dimension 3 and 11.

What becomes harder is testing a Layout or Master Template in isolation from
the content template it wraps, because the two are coupled through an
inclusion or yield mechanism most engines provide, and a test written against
the layout alone has to supply a stand-in content fragment rather than a real
Context, which is an extra fixture most teams do not bother building until a
regression in the layout itself justifies the cost.

For the compiled variants from dimension 8, Razor specifically, the compile
step itself is a form of test, catching a broken reference to the Model at
build time, and a CI pipeline that runs the compilation step as a gate, not
only the traditional test suite, closes a real gap that interpreted engines
leave open until request time.

A separate, cheap, high-value test worth writing for any Template View
adoption is a static scan of the template source tree for markers that
resolve calls outside the Context, a regular expression or an AST-based check
looking for repository, service, or database client type names inside
template files, run as a lint step rather than a unit test, which directly
targets the failure mode described first in dimension 11.

## 16. Observability signals

Per-render latency, broken out by template name, is the primary signal a
Template View deployment should surface, because the failure mode in
dimension 11 involving an uncached, reparsed template shows up first and most
clearly as a latency regression isolated to a specific page rather than a
system-wide slowdown. A healthy instance shows render latency for a given
template staying flat across load, and a failing one shows render latency
climbing with request concurrency, which is the signature of contention
around a per-request parse rather than a fixed, amortized cost.

Template compilation or cache-hit rate, for engines that support a cache, is
the second signal worth exposing directly, either as a counter incremented on
cache miss or as a gauge reporting the current cache size relative to the
total number of distinct templates in the application. A cache-hit rate that
drops after a deployment usually means the cache key changed, a template file
timestamp check invalidating more aggressively than intended, or the cache
itself was sized too small for the number of distinct templates a
multi-tenant application serves.

Escaping-related exceptions or warnings, for engines like `html/template`
that fail loudly on a malformed template rather than silently emitting
unsafe output, are worth routing to the same error channel as any other
application error, because a template that fails to parse due to an
escaping-context ambiguity is a build-time or startup-time signal in the
compiled variants and a per-request error in the interpreted ones, and either
way it deserves the same visibility as a failed database query, not a
suppressed warning buried in a log file nobody reads.

Finally, a count of raw or unescaped-output marker uses across the template
tree, tracked over time as a simple metric derived from the static scan
described in dimension 15, gives a team an early warning that the number of
places a developer opted out of default escaping is growing, which correlates
directly with the injection failure mode from dimension 11.

## 17. Security and privacy implications

The dominant security implication of Template View is output escaping, and
the pattern's own history shows both ends of the spectrum. Engines that
escape by default and require an explicit, visually distinct marker for raw
output, and Go's `html/template` goes further, tracking the surrounding HTML,
JavaScript, CSS, or URL context and applying the correct escaping function for
that context automatically, close off cross-site scripting as a default risk
for anything rendered through an ordinary marker. Engines that emit raw
output by default and require an explicit call to escape place the burden on
every individual template author, every time, which is a much weaker security
posture in practice, because it depends on universal, sustained discipline
across a team and across time, and the failure mode described second in
dimension 11 is exactly this class of defect.

The second implication follows from dimension 11's first failure mode. A
scripting-tag engine that permits a data-access call inside a marker also
permits that call to read data the Context was never meant to expose, which
is a privacy concern distinct from injection. A template that, under
deadline pressure, fetches a user's full profile record directly rather than
receiving the three fields the page actually needs increases the surface
area for an accidental data leak, a field rendered that should have been
filtered out upstream, in a way that a template restricted to substitution
against a narrowly scoped Context cannot.

A third, smaller implication concerns template source disclosure. A
misconfigured server that serves the raw Template Source file, rather than
routing every request for that path through the engine, can leak internal
variable names, comments, or, worse, credentials or connection details that a
developer left inline inside a scripting tag during debugging and never
removed. This risk is specific to the scripting-tag variants from dimension
8, because a logic-less engine's template source, even if disclosed, reveals
only marker names and no executable code or embedded secrets.

The pattern is silent on authentication, authorization, and session handling.
Those concerns are the responsibility of whatever sits upstream of the
Template Engine, the controller or Front Controller assembling the Context,
and a template should treat the presence of a value in its Context as
evidence that the controller already decided the current user is entitled to
see it, never as a decision the template makes itself.

## 18. References

- Martin Fowler, ["Template View"](https://martinfowler.com/eaaCatalog/templateView.html), martinfowler.com, verified 2026-08-02.
- Martin Fowler, *Patterns of Enterprise Application Architecture*, Addison-Wesley Professional, 2002, ISBN 0321127420, View patterns chapter. Publication details independently confirmed via [Biblio listing](https://www.biblio.com/9780321127426), verified 2026-08-02.
- Wikipedia, ["JavaServer Pages"](https://en.wikipedia.org/wiki/JavaServer_Pages), verified 2026-08-02.
- Ruby on Rails Guides, ["Layouts and Rendering in Rails"](https://guides.rubyonrails.org/layouts_and_rendering.html), verified 2026-08-02.
- Django Software Foundation, ["Templates"](https://docs.djangoproject.com/en/5.2/topics/templates/), Django documentation, version 5.2, verified 2026-08-02.
- Microsoft, ["Razor syntax reference for ASP.NET Core"](https://learn.microsoft.com/en-us/aspnet/core/mvc/views/razor), Microsoft Learn, verified 2026-08-02.
- The Go Authors, [html/template package documentation](https://pkg.go.dev/html/template), pkg.go.dev, referenced for the context-aware escaping behavior exercised in the Go code sample in dimension 8, general knowledge of the standard library's own documented contract, not independently re-fetched in this pass.

## Code

Three languages, each demonstrating a distinct implementation variant from
dimension 8. All three were executed, not only syntax-checked, and produced
the shown output on this machine.

### Python, an interpreted, logic-less-style marker engine

Mirrors the Mustache-family variant from dimension 8, restricting markers to
variable substitution and section iteration, with no arbitrary expression
evaluation available inside a marker.

```python
class TemplateEngine:
    def __init__(self, source):
        self.source = source

    def render(self, context):
        out = []
        i = 0
        n = len(self.source)
        while i < n:
            start = self.source.find("{{", i)
            if start == -1:
                out.append(self.source[i:])
                break
            out.append(self.source[i:start])
            end = self.source.find("}}", start)
            token = self.source[start + 2:end].strip()
            if token.startswith("#each "):
                var_name = token[6:].strip()
                loop_end = self.source.find("{{/each}}", end)
                body = self.source[end + 2:loop_end]
                for item in context.get(var_name, []):
                    out.append(TemplateEngine(body).render(item))
                i = loop_end + len("{{/each}}")
                continue
            out.append(str(context.get(token, "")))
            i = end + 2
        return "".join(out)


page = TemplateEngine(
    "<ul>{{#each books}}<li>{{title}} by {{author}}</li>{{/each}}</ul>"
)

context = {
    "books": [
        {"title": "PoEAA", "author": "Fowler"},
        {"title": "Effective Java", "author": "Bloch"},
    ]
}

print(page.render(context))
```

Run with `python3 template_view.py`. Output, verified on this machine.

```
<ul><li>PoEAA by Fowler</li><li>Effective Java by Bloch</li></ul>
```

### Go, a compiled, context-escaping production template engine

Uses the Go standard library's `html/template` package directly, the same
package deployed inside real Go services, rather than a hand-rolled engine,
since Go ships a production-grade Template View implementation in its
standard library.

```go
package main

import (
	"html/template"
	"os"
)

type Book struct {
	Title  string
	Author string
}

const pageSource = `<ul>{{range .}}<li>{{.Title}} by {{.Author}}</li>{{end}}</ul>`

func main() {
	page := template.Must(template.New("catalog").Parse(pageSource))
	books := []Book{
		{Title: "PoEAA", Author: "Fowler"},
		{Title: "Effective Java", Author: "Bloch"},
	}
	if err := page.Execute(os.Stdout, books); err != nil {
		panic(err)
	}
}
```

Run with `go run main.go`. Output, verified on this machine.

```
<ul><li>PoEAA by Fowler</li><li>Effective Java by Bloch</li></ul>
```

`html/template`'s escaping behavior is what dimension 17 refers to, the
package inspects each marker's surrounding HTML, attribute, script, or URL
context during parsing and applies the matching escape function at execute
time, closing off the injection failure mode described in dimension 11
without requiring the template author to remember to escape anything.

### TypeScript, a compiled, scriptlet-style engine, the JSP and EJS variant

Parses `<% %>` and `<%= %>` scriptlet markers, translates the template source
into the body of a real function, and compiles that function once with the
host language's own `Function` constructor, mirroring how JSP compiles into a
servlet method and how EJS compiles a template into a JavaScript function,
rather than reinterpreting the source text on every render.

```typescript
type Context = Record<string, unknown>;
type CompiledTemplate = (ctx: Context) => string;

function compile(source: string): CompiledTemplate {
  const parts = source.split(/(<%=?.*?%>)/g);
  let body = 'let out = "";\n';
  for (const part of parts) {
    if (part.startsWith("<%=")) {
      body += `out += (${part.slice(3, -2)});\n`;
    } else if (part.startsWith("<%")) {
      body += `${part.slice(2, -2)}\n`;
    } else if (part.length > 0) {
      body += `out += ${JSON.stringify(part)};\n`;
    }
  }
  body += "return out;\n";
  return new Function("ctx", body) as CompiledTemplate;
}

interface Book {
  title: string;
  author: string;
}

interface CatalogContext extends Context {
  books: Book[];
}

const source =
  "<ul><% for (const b of ctx.books) { %><li><%= b.title %> by <%= b.author %></li><% } %></ul>";

const page = compile(source);

const context: CatalogContext = {
  books: [
    { title: "PoEAA", author: "Fowler" },
    { title: "Effective Java", author: "Bloch" },
  ],
};

console.log(page(context));
```

Compiled with `tsc --strict --target es2022` and run with `node`. Output,
verified on this machine.

```
<ul><li>PoEAA by Fowler</li><li>Effective Java by Bloch</li></ul>
```

Note on the toolchain sweep for this entry. `rustc` and `swiftc` are present
on this machine, and a fourth or fifth sample was not added because three
languages already satisfy the entry's requirement and each additional sample
would repeat the identical demonstration in another syntax with no new
implementation variant left to show. `java` and `javac` resolve to a stub
binary on `PATH` on this machine that reports "Unable to locate a Java
Runtime" with no working JDK installed, so no Java sample was attempted
beyond that failed check, and no Java sample is presented in this entry.
