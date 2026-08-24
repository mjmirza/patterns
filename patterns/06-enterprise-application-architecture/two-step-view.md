---
name: Two Step View
slug: two-step-view
family: 06-enterprise-application-architecture
category: Web Presentation
aliases: [Two Phase Rendering, Logical Page Then Format]
first_described: "Fowler 2002"
maturity: canonical
related: [transform-view, template-view, model-view-controller, front-controller, page-controller]
incompatible_with: []
verified: 2026-08-02
---

# Two Step View

## 1. Name, aliases, and lineage

The canonical name is Two Step View. It is cataloged as a Web Presentation
pattern in Martin Fowler, *Patterns of Enterprise Application Architecture*,
Addison-Wesley, 2002, chapter 14. The catalog entry states the intent directly.
turn domain data into HTML "first by forming some kind of logical page, then
rendering the logical page into HTML"
([Two Step View, martinfowler.com/eaaCatalog/twoStepView.html](https://martinfowler.com/eaaCatalog/twoStepView.html),
verified 2026-08-02).

Fowler places Two Step View alongside two sibling patterns in the same
chapter, Template View (fill placeholders inside an HTML skeleton) and
Transform View (a single-stage element-by-element transform of the domain
data into markup). All three answer the same question, how does a server turn
data into a rendered page, and they differ in how much indirection sits
between the data and the final markup.

No alternate name dominates the literature the way Virtual Constructor
dominates for Factory Method. Practitioners commonly call the technique Two
Phase Rendering when describing it informally, because the word "step" in
Fowler's name is sometimes read as referring to a UI wizard step rather than a
processing phase. Fowler's own catalog entry preserves the two-stage
description, forming a logical page first and rendering it into HTML second
([Two Step View, martinfowler.com](https://martinfowler.com/eaaCatalog/twoStepView.html),
verified 2026-08-02).

The pattern predates the 2002 book by several years in practice. XSLT reached
Recommendation status in 1999, and two-stage XSLT pipelines, one stylesheet
turning domain XML into a presentation-neutral XML vocabulary, a second
stylesheet turning that vocabulary into HTML, were already common in XML
publishing toolchains by the time Fowler wrote the catalog entry. Fowler
names this the most common concrete technique for implementing the pattern in
his own description of the XSLT variant
([Two Step View, martinfowler.com](https://martinfowler.com/eaaCatalog/twoStepView.html),
verified 2026-08-02).

## 2. Problem and context

A web application with more than a handful of pages needs every page to share
a consistent visual identity. The header, the navigation chrome, the color
scheme, the typography, and the overall page structure should look the same
whether the visitor is on the product page, the checkout page, or the search
results page. When a site is built with Template View or Transform View
alone, that consistency is produced by discipline, not by structure. Each
page template, or each transform module, independently encodes the decision
that a section heading renders as an h2 element with a particular class, that
a table of results renders with a particular border and striping, that a
money value renders with a particular currency symbol and decimal formatting.

The problem surfaces the moment the business asks for a site-wide visual
change, a new brand color, a switch from a two-column to a three-column
results layout, a move from imperial to metric units on every page that shows
a measurement. With duplicated presentation logic, that one business request
becomes a find-and-replace exercise across every page template in the
application, and a page that is missed silently drifts out of visual sync
with the rest of the site. The same problem recurs when the business asks for
a second look and feel entirely, a mobile-optimized rendering of the same
pages, or a white-labeled skin for a reseller, because the presentation
decisions are not isolated anywhere a developer can point to and replace as a
unit.

The context in which Two Step View earns its keep is therefore a site or
application with many pages that must share one presentation, or that must
support more than one presentation of the same content, where the cost of a
duplicated formatting decision is paid repeatedly as the site grows. A
single-page application, an internal tool with one screen, or a site where
every page is genuinely different in structure does not create this pressure,
and the pattern's extra indirection buys nothing there.

## 3. Forces

Web presentation design is a negotiation between several pressures that pull
against each other, and Two Step View resolves the negotiation in a specific
direction.

- **Consistency versus per-page flexibility.** A single second-stage renderer
  applied to every page's logical representation is what makes a site-wide
  visual change a one-file edit. The same mechanism makes an intentionally
  unique page harder to build, because that page's markup is generated by the
  same rules as everyone else's, and an escape hatch to bypass the renderer
  for one page reintroduces the duplication the pattern exists to prevent.
- **Indirection versus directness.** Building an intermediate, presentation-
  neutral representation of the page before formatting it is an extra step
  that a developer must design, name, and maintain. Transform View skips this
  step and goes straight from domain data to markup. The intermediate
  representation pays for itself only when it is reused by more than one
  renderer, or edited independently of the domain logic often enough to
  justify its own vocabulary.
- **Multiple output formats versus a single rendering path.** Once a logical
  page exists as a self-contained structure, rendering it to a second format,
  a mobile layout, a plain-text email digest, a printable PDF, is a matter of
  writing a second renderer against the same logical page. A single-stage
  approach requires either duplicating the domain-to-markup logic per format
  or threading a format parameter through every formatting decision in one
  sprawling template.
- **Development team boundaries.** The two stages are natural points to split
  ownership. A backend team owns the code that decides what the logical page
  contains, a frontend or design team owns the renderer that decides how it
  looks. This split works only when the intermediate representation is stable
  enough that the design team is not blocked waiting on backend changes.
- **Runtime cost.** Building an intermediate structure and then walking it a
  second time to produce markup is measurably more work per request than
  writing directly to an output stream once. For most web applications this
  cost is dwarfed by database and network latency, but a pattern that adds a
  full page's worth of allocation and traversal on every request is a real,
  nonzero cost that a very high throughput system will notice.

Two Step View favors consistency, multi-format support, and team-boundary
clarity. It sacrifices directness and pays a small runtime cost for the
indirection it buys.

## 4. Applicability and non-applicability

Reach for Two Step View when the following hold.

- The site has enough pages, or enough page templates, that a single visual
  change currently requires touching more than one file, and that has
  actually happened more than once.
- The same content must render in more than one format, an HTML page and a
  plain-text or PDF version of the same report, a desktop layout and a
  reduced mobile layout, a default skin and a white-labeled skin for a
  reseller.
- The organization wants a clean line between the people who decide what data
  a page shows and the people who decide how that data looks, and that line
  needs to survive as a real interface, not a verbal agreement.
- The domain data is naturally hierarchical or reportlike, tables, sections,
  headings, repeating groups, which maps cleanly onto an intermediate logical
  page structure without an awkward translation step.

Do NOT reach for Two Step View when the following hold.

- The application has one page, or a handful of pages that are each visually
  unique, because there is no shared second stage to factor out and the
  intermediate representation is pure overhead.
- The team is already using a component-based UI framework, React, Vue,
  Svelte, where reusable components already solve the consistency problem by
  composition rather than by a two-stage pipeline, and adding a logical-page
  layer on top duplicates the framework's own job.
- Rendering performance under high request volume is the dominant constraint
  and profiling has already shown the domain-to-markup step as a bottleneck,
  because Two Step View adds allocation and a second traversal that a direct
  Transform View avoids.
- The presentation decisions genuinely differ per page in ways that resist
  generalization, an intermediate vocabulary expressive enough to cover every
  page's real differences collapses into a second copy of HTML with extra
  steps, and at that point the pattern has stopped paying for itself.
- The site or service produces exactly one output format for the foreseeable
  future and no organizational pressure exists to keep presentation logic in
  one place, in which case Transform View or Template View is less code for
  the same result.

## 5. Structure

Two Step View names two collaborating roles plus the artifact that passes
between them.

- **Logical Page Builder.** Consumes the domain model for a single request
  and produces a Logical Page, a tree of presentation-neutral nodes that
  describe the semantic content of the page, what sections it has, what
  headings and repeating groups it contains, what values are money amounts
  versus dates versus plain text, without deciding what HTML tag or CSS
  class represents any of that. This role has no knowledge of the eventual
  output format.
- **Logical Page.** The intermediate artifact itself. An in-memory tree of
  small node types (a page, a section, a heading, a field, a repeating list)
  or, in the XSLT variant, an XML document in a presentation-oriented but
  format-neutral vocabulary. The Logical Page is the contract between the two
  stages, and its stability is what lets the two stages be built, tested, and
  changed independently.
- **Formatter, the second-stage renderer.** Walks the Logical Page and
  decides, for every node type, the concrete markup, CSS class, currency
  symbol, or layout that represents it in one specific output format. A site
  with more than one Formatter, an HTML Formatter and a plain-text Formatter,
  gets multiple outputs from one Logical Page Builder for free.
- **Coordinator.** The code, usually a controller action or a request
  handler, that calls the Logical Page Builder to produce the Logical Page,
  then hands that Logical Page to the selected Formatter and returns the
  Formatter's output as the response body. In the XSLT variant this role is
  played by the pipeline configuration that chains the two stylesheets.

## 6. ASCII structure diagram

```
+--------------------------------+
| Domain Model                   |
| (order, invoice, article, ...) |
+--------------------------------+
           | builds
           v
+----------------------+
| Logical Page Builder |
+----------------------+
           | produces
           v
+----------------------------+
| Logical Page               |
| (presentation-neutral tree |
| or XML vocabulary)         |
+----------------------------+
           |
     +-----+-----+
     |           |
+----------------------+  +----------------------+
| HTML Formatter       |  | PDF/Text Formatter   |
+----------------------+  +----------------------+
     |           |
     v           v
HTML response   PDF or plain-text response
```

## 7. Dynamics

The runtime flow has two hard boundaries. domain data crosses into the
Logical Page, and the Logical Page crosses into the final output. Neither
boundary is crossed more than once per request.

```
Coordinator          LogicalPageBuilder        LogicalPage         Formatter
    |                        |                      |                  |
    |-- handle(request) ---->|                      |                  |
    |                        |-- read domain model  |                  |
    |                        |   and build tree ---->|                  |
    |                        |<-- Logical Page ------|                  |
    |<-- Logical Page -------|                      |                  |
    |                                                                   |
    |-- render(logicalPage, format) ------------------------------------>
    |                                                                   |-- walk tree
    |                                                                   |   node by node
    |                                                                   |-- emit markup
    |                                                                   |   per node type
    |<-- rendered output ------------------------------------------------|
    |
    |-- write response body
```

In the XSLT variant the same two crossings exist but run inside a
transformation pipeline rather than in-process objects. a first stylesheet
transforms domain-oriented XML into presentation-oriented XML, a second
stylesheet transforms that presentation-oriented XML into HTML
([Two Step View, martinfowler.com](https://martinfowler.com/eaaCatalog/twoStepView.html),
verified 2026-08-02). A pipeline processor, Apache Cocoon's sitemap being the
best-documented example, chains generator, transformer, and serializer
components so that the intermediate XML never leaves the server process
([Cocoon Tutorials](https://cocoon.apache.org/2.1/tutorial/index.html),
verified 2026-08-02).

## 8. Implementation variants

- **In-memory object tree.** The Logical Page Builder constructs a small
  hierarchy of plain objects or structs, one type per semantic concept (page,
  section, field, repeating list). The Formatter is a visitor or a recursive
  function that switches on node type. This is the variant most idiomatic in
  general-purpose languages and the one demonstrated in the code examples
  below.
- **Two-stage XSLT.** The Logical Page is a genuine XML document in a
  house-defined, presentation-oriented vocabulary. The first XSLT stylesheet
  transforms domain XML into that vocabulary, the second transforms the
  vocabulary into HTML, PDF-via-XSL-FO, or any other markup. Fowler documents
  this as the primary technique behind the pattern
  ([Two Step View, martinfowler.com](https://martinfowler.com/eaaCatalog/twoStepView.html),
  verified 2026-08-02).
- **XSL-FO as the intermediate vocabulary, targeting print.** Instead of a
  house-defined vocabulary, the intermediate document is the standard XSL
  Formatting Objects vocabulary, and the second-stage renderer is a formatter
  such as Apache FOP rather than a second XSLT stylesheet. Apache FOP's own
  documentation describes exactly this two-stage flow, "the most common
  method is to convert semantic XML to XSL-FO, using an XSLT transformation,"
  after which FOP "reads a formatting object (FO) tree and renders the
  resulting pages to a specified output"
  ([Apache FOP](https://xmlgraphics.apache.org/fop/),
  verified 2026-08-02).
- **JSON logical page for a client-rendered second stage.** A server-side
  Logical Page Builder emits a JSON document describing the page's semantic
  structure, and the second stage runs in the browser, a JavaScript renderer
  that walks the JSON and produces DOM nodes. This variant trades the
  server-side Formatter for a client-side one and is common in server-driven
  UI systems for native mobile apps, where the server decides content and the
  client decides layout per platform.
- **Streaming Logical Page.** For very large pages, a reporting export with
  many thousands of rows being the common case, the Logical Page Builder does
  not materialize the whole tree before formatting begins. It emits Logical
  Page events, "section started," "field emitted," "section ended," to a
  streaming Formatter that writes output incrementally. This preserves the
  two-stage separation of concerns while avoiding the memory cost of holding
  a full intermediate tree, at the price of a more constrained node API, a
  streaming Formatter cannot look ahead or back across the tree the way an
  in-memory Formatter can.

## 9. Known production uses

- **Apache Cocoon.** Cocoon's sitemap pipeline model chains a Generator that
  produces SAX events representing XML, one or more Transformers that alter
  the event stream, typically via XSLT, and a Serializer that produces the
  final output stream. A common Cocoon pipeline transforms domain XML into a
  presentation-oriented XML vocabulary in one transformer stage and renders
  that vocabulary to HTML in a later stage, which is the pipeline shape Two
  Step View describes
  ([Cocoon Tutorials, cocoon.apache.org](https://cocoon.apache.org/2.1/tutorial/index.html),
  verified 2026-08-02).
- **Apache FOP with XSLT-to-XSL-FO toolchains.** Publishing systems that need
  a print-quality PDF alongside an HTML page commonly transform domain XML
  into XSL-FO, an intermediate, presentation-oriented but output-neutral
  vocabulary, using an XSLT stylesheet, then hand that XSL-FO document to
  Apache FOP, which renders it to PDF, PostScript, PCL, AFP, or PNG without
  reprocessing the original source XML. Apache FOP's own project page states
  this directly, describing itself as a print formatter driven by XSL
  formatting objects and supporting multiple output targets from one
  intermediate document
  ([Apache FOP, xmlgraphics.apache.org](https://xmlgraphics.apache.org/fop/),
  verified 2026-08-02).
- **Fowler's own catalog example, the XSLT two-stage transform.** Fowler
  presents the XSLT variant as the concrete worked example for the pattern in
  the *Patterns of Enterprise Application Architecture* catalog, describing
  two XSLT stylesheets chained so that a global visual change requires
  editing only the second stylesheet, and multiple looks can share one first
  stylesheet
  ([Two Step View, martinfowler.com](https://martinfowler.com/eaaCatalog/twoStepView.html),
  verified 2026-08-02). This is the pattern's canonical worked example rather
  than a third-party adopter, and it is included here because it is the
  primary documented instance of the technique in production book form,
  distinct in mechanism from the Cocoon pipeline and the FOP toolchain above.

## 10. Consequences

Positive consequences.

- A site-wide visual change becomes a change to one Formatter instead of a
  change to every page template, because every page's Logical Page passes
  through the same second stage.
- Supporting a second output format, a mobile layout, a printable version, an
  alternate brand skin, costs one new Formatter rather than a rewrite of the
  domain-to-markup logic for every page.
- The Logical Page is a natural seam for automated testing, because
  asserting on the shape of a Logical Page (does the report have three
  sections, does the total field carry the right value) is independent of
  whatever HTML happens to render it, and survives a visual redesign
  untouched.
- Backend and frontend concerns separate cleanly along the Logical Page
  boundary, letting the two teams change their half of the system on
  different schedules as long as the intermediate vocabulary stays stable.

Negative consequences.

- Every request pays the cost of building a full intermediate structure and
  then traversing it a second time, which is strictly more work than writing
  markup directly from domain data in one pass.
- Designing a Logical Page vocabulary that is expressive enough to represent
  every page's real content, without degenerating into a second copy of HTML
  with different tag names, is genuine design work that a single-stage
  Transform View skips entirely.
- The team must maintain two things instead of one, the Logical Page Builder
  and the Formatter, and a change that spans both, a new field type that
  needs new handling in every Formatter, touches more files than the
  equivalent single-stage change would.
- Debugging a rendering problem now requires checking two places, whether the
  Logical Page itself is wrong or the Formatter mishandled a correct Logical
  Page, which is an extra step compared with reading one template top to
  bottom.

## 11. Failure modes and misuse

Symptom. A new page type is added, and the developer discovers that
representing its content forces adding several one-off fields to the Logical
Page vocabulary that no other page uses.
Cause. The Logical Page vocabulary was designed around the first page or two
that used it, rather than around the genuine range of content the site needs
to represent, so new page types keep forcing special cases into a vocabulary
that was never built to hold them.
Fix. Treat the Logical Page vocabulary as a small, deliberately designed
interface, not an incidental byproduct of the first Formatter's needs, and
revisit it explicitly, per this repository's Extract Interface refactoring
family, when a second or third page type needs a shape the current vocabulary
cannot express cleanly.

Symptom. The Formatter contains conditional branches that check for a
specific page name or a specific field's identity, rather than switching
purely on node type.
Cause. A one-off visual requirement for a single page was solved by
special-casing that page inside the shared Formatter instead of by adding a
new node type or a new Formatter, which quietly reintroduces the per-page
duplication the pattern exists to prevent, only moved one layer down.
Fix. Push the special requirement back into the Logical Page as a distinct
node type or a node attribute the Formatter can handle generically, so the
Formatter never needs to know which page it is rendering.

Symptom. Two Formatters, an HTML Formatter and a PDF Formatter, produce
visibly inconsistent output for the same Logical Page, a total that renders
right-aligned in one and left-aligned in the other, a date format that
differs between the two.
Cause. The Logical Page vocabulary left formatting decisions, not only
content decisions, ambiguous, so each Formatter independently invented an
answer, and the two answers drifted.
Fix. Move any decision that must be consistent across every Formatter, which
fields are currency, which are dates, which fields sort in which direction,
into the Logical Page itself as explicit node metadata, so a Formatter reads
the decision rather than making it.

Symptom. The Logical Page Builder starts importing HTML-specific concepts, a
CSS class name, a div-wrapper hint, into the intermediate tree.
Cause. Under deadline pressure, a developer takes a shortcut and lets a
presentation detail leak into the supposedly presentation-neutral stage,
because it is faster than adding a proper node type and updating every
Formatter.
Fix. Treat any HTML- or format-specific token appearing in the Logical Page
Builder's code as a defect, and add a lint or code review check that flags
markup-shaped strings appearing outside the Formatter package.

## 12. Trade-off matrix

| Force | Two Step View | Transform View | Template View | MVC (component-based UI) |
|---|---|---|---|---|
| Site-wide visual consistency | High, one shared second stage | Low, each transform module decides its own markup | Low, each template decides its own markup | High, but achieved through component reuse, not a two-stage pipeline |
| Cost of adding a second output format | Low, write one new Formatter | High, duplicate the domain-to-markup logic per format | High, duplicate templates per format | Medium, depends on whether components abstract layout from content |
| Runtime cost per request | Higher, builds and walks an intermediate tree | Lower, writes output in one pass | Lower, writes output in one pass | Depends on framework, typically comparable to Transform View |
| Design effort up front | High, must design a stable intermediate vocabulary | Low, transform logic is written directly against domain data | Low, template placeholders map directly to domain fields | Medium, must design a component hierarchy, a different kind of up-front cost |
| Backend and frontend separation | Clean, the Logical Page is the contract | Weak, presentation and domain-to-markup logic are the same code | Weak, template designers still touch domain field references directly | Clean, components are the contract, but ownership usually sits entirely with frontend |
| Best fit | Many pages, one shared identity, multiple output formats | Few transforms, XML-native pipeline already in place | Few pages, simple substitution, no multi-format need | Modern client-heavy web apps where component reuse already solves consistency |

## 13. Related and incompatible patterns

- **Transform View.** The direct competitor within Fowler's own Web
  Presentation family. Transform View walks domain data and emits markup in
  one pass, with no intermediate representation. Two Step View is Transform
  View with a deliberate seam inserted in the middle, and the choice between
  them is exactly the trade-off in dimension 12, one shared second stage
  versus lower per-request cost and less up-front design.
- **Template View.** Fills placeholders inside a page skeleton with domain
  values. It composes poorly with Two Step View directly, because a Template
  View skeleton already encodes presentation decisions inline, but a
  Formatter in the Two Step View sense can itself be implemented internally
  as a set of small Template Views, one per node type, each filling a tiny
  skeleton for that node.
- **Front Controller and Page Controller.** Either controller pattern
  typically plays the Coordinator role in dimension 5, receiving the request,
  invoking the Logical Page Builder, then invoking the Formatter, and
  returning the result. Two Step View does not compete with these patterns,
  it slots underneath whichever controller pattern the application already
  uses.
- **Model View Controller.** Two Step View is a refinement of the View half
  of MVC. Where a plain MVC view is one component that reads the model and
  produces output, Two Step View splits that one component into a
  model-to-logical-page stage and a logical-page-to-output stage, without
  changing the Controller's or the Model's responsibilities.
- **Visitor.** The Formatter in an in-memory-tree implementation is
  frequently structured as a Visitor over the Logical Page's node types,
  particularly in statically typed languages where a switch over node type
  benefits from exhaustiveness checking. This repository's Visitor entry
  covers the double-dispatch mechanics that a Formatter can use once the
  Logical Page vocabulary is fixed.
- **Incompatible with nothing structurally**, but pairs poorly with a
  component-based client framework applied at the same layer, because both
  approaches solve the consistency problem, and stacking them means paying
  the cost of Two Step View's intermediate tree while also paying for
  component composition, for one consistency guarantee.

## 14. Refactoring path in and out

Introducing Two Step View into code that renders markup directly.

1. Identify one page, or one family of similar pages, where a visual change
   has recently had to touch more than one file. This is the concrete pain
   the refactor is solving, and it anchors the scope of the first pass.
2. Read the existing rendering code for that page and list every distinct
   semantic concept it expresses, a heading, a repeating list of rows, a
   money field, a date field, without listing the HTML tags used to express
   them. This list becomes the first draft of the Logical Page node types.
3. Introduce the Logical Page node types as small, dumb data structures with
   no rendering knowledge, and write a Logical Page Builder that constructs
   an instance of these types from the domain data the page already uses.
   Nothing observable changes yet, because nothing consumes the Logical Page.
4. Write a Formatter that walks the Logical Page and reproduces the existing
   markup exactly, then swap the page's rendering call to go through the
   Logical Page Builder and the Formatter instead of the old direct code
   path. A snapshot test of the rendered HTML before and after this step,
   asserting byte-for-byte equality, is the cheapest possible proof the
   refactor changed nothing observable.
5. Delete the old direct rendering code once the Formatter path is confirmed
   equivalent, and repeat for the next page or page family, extending the
   Logical Page vocabulary only when a genuinely new concept appears, never
   speculatively.

Removing Two Step View when it stops earning its place.

1. Confirm the actual trigger, most often that the application settled on a
   single output format permanently, or that a component-based frontend
   framework was adopted and now owns the consistency guarantee that the
   Logical Page used to provide.
2. For each page, inline the Formatter's logic for that page's node types
   directly against the domain data, effectively performing the introduction
   refactor in reverse, one page at a time, verified the same way with a
   before-and-after snapshot of the rendered output.
3. Once no page routes through the Logical Page Builder, delete the Logical
   Page node types and the Formatter classes. Do this last, and only after
   every call site has been migrated, so an incomplete removal never leaves
   half the site depending on a partially deleted intermediate layer.

## 15. Testing and verification

Two Step View is easier to test than a single-stage Transform View precisely
because it exposes a seam. Each side of the seam is testable independently
and the two kinds of test catch different classes of bug.

- **Testing the Logical Page Builder.** Feed it a known domain model and
  assert on the shape of the resulting Logical Page, not on any rendered
  markup. Does the report have the right number of sections, does the total
  field carry the correct value and the correct semantic type (money, not a
  plain number), does an empty result set produce an empty-state node rather
  than an empty list. These tests never need to change when the visual
  design changes, because they never look at markup.
- **Testing the Formatter in isolation.** Construct a Logical Page by hand,
  a small fixture with one of every node type the Formatter must handle, and
  assert on the rendered output for that fixture. This decouples formatter
  tests from the domain layer entirely, so a Formatter test suite can run
  without a database or any domain object, and a change to how the domain
  model is built never breaks a Formatter test.
- **Snapshot testing the full pipeline.** For a handful of representative
  pages, run the full Coordinator flow, Logical Page Builder then Formatter,
  and compare the rendered output against a stored snapshot. This is the
  test that catches regressions in the wiring between the two stages, the
  case where the Builder and the Formatter each pass their own unit tests but
  disagree about the contract between them, for example the Builder emitting
  a date as an ISO string while the Formatter expects a language-native date
  object.
- **Testing a new Formatter for an existing Logical Page vocabulary.** Reuse
  the same Logical Page fixtures already written for the first Formatter.
  If a fixture cannot be reused without modification, that is itself a
  signal the vocabulary leaked a detail specific to the first Formatter's
  output format, per the failure mode in dimension 11.

## 16. Observability signals

- **Logical Page build duration, tagged separately from Formatter duration.**
  Because the two stages are distinct calls, timing them separately in a
  trace or a metric immediately answers whether a slow page is slow because
  the domain-to-logical-page step is doing too much work, querying the
  database inefficiently, or because the Formatter is doing too much,
  walking the tree inefficiently or doing expensive string formatting per
  node. A single combined render-time metric hides this distinction.
- **Logical Page size, node count or serialized byte size.** A page whose
  Logical Page has grown unexpectedly large, hundreds of nodes for what
  should be a small page, is an early signal that the vocabulary is being
  misused to represent something it should not, per the leaking-detail
  failure mode, before that misuse becomes a rendering bug.
- **Formatter error rate, per Formatter and per node type.** Because
  multiple Formatters share one Logical Page, a spike in errors from one
  specific Formatter while others stay healthy points at a Formatter bug
  rather than a Logical Page Builder bug, and errors clustered on one node
  type across every Formatter point the other way, at the Builder or at the
  vocabulary itself.
- A healthy instance shows Logical Page build time and Formatter render
  time both small and stable relative to total request time, with the two
  metrics moving independently of each other when only one side of the
  pipeline changes. A failing instance shows either metric growing
  unboundedly with data size, node counts far outside the expected range for
  a page's content, or Formatter errors concentrated on a specific node type
  right after a vocabulary change ships, indicating the change was not
  propagated to every Formatter that needed it.

## 17. Security and privacy implications

The Logical Page boundary is a genuine security control point, not merely an
architectural convenience, and treating it that way closes off a class of
bug that a single-stage Transform View makes easy to introduce accidentally.

- **Output encoding belongs in the Formatter, not the Builder.** Because the
  Logical Page Builder never produces markup, it cannot accidentally emit an
  unescaped value into an HTML attribute or a script context. Every escaping
  decision, HTML-entity encoding a text field, escaping quotes inside an
  attribute value, lives in exactly one place, the Formatter, which makes an
  escaping audit a search over one small module instead of a search over
  every page template in the application.
- **A shared Formatter is a single point of failure for encoding bugs.**
  A missing-escaping defect in the Formatter's handling of one node type
  affects every page that uses that node type at once, which is the same
  double-edged property as dimension 10's consistency benefit, applied to
  security. This argues for the Formatter's node-rendering functions
  carrying focused, well-tested coverage for every node type, per dimension
  15, because a single bug there has a wide blast radius.
- **The Logical Page can become an unintended data leak surface.** If the
  Logical Page Builder is built generically, for example by reflecting over
  a domain object and including every field, it can carry sensitive fields
  through to a Formatter that was never audited to withhold them, a Logical
  Page vocabulary meant for a public HTML Formatter accidentally reused by an
  internal debug Formatter that dumps the whole tree. The Builder should
  construct the Logical Page by explicit selection of fields to include,
  never by reflecting over the full domain object, so a sensitive field the
  domain model happens to carry cannot reach any Formatter that was not
  deliberately given it.
- **Caching the Logical Page is a privacy decision, not only a performance
  one.** Because the Logical Page can be reused across multiple Formatters,
  and because an intermediate representation is a tempting place to add a
  cache, caching it for a personalized page risks serving one user's Logical
  Page, and therefore their data, to a different user if the cache key does
  not correctly incorporate the identity or authorization context of the
  request.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 14, Web Presentation Patterns, Two Step View.
- Two Step View, Martin Fowler's Enterprise Application Architecture catalog,
  https://martinfowler.com/eaaCatalog/twoStepView.html, verified 2026-08-02.
- Cocoon Tutorials, The Apache Software Foundation,
  https://cocoon.apache.org/2.1/tutorial/index.html, verified 2026-08-02.
- Apache FOP, XML Graphics Project, The Apache Software Foundation,
  https://xmlgraphics.apache.org/fop/, verified 2026-08-02.

## Code examples

Three languages where the in-memory-tree variant of the pattern is genuinely
idiomatic. TypeScript shows the discriminated-union form, where the compiler
enforces that every Formatter handles every node kind. Python shows the
dataclass form typical of a Django or Flask reporting module. Go shows the
interface form, where multiple Formatter implementations satisfy one small
interface without inheritance. All three build one Logical Page from the same
domain data and render it through two independent Formatters, an HTML
Formatter and a plain-text Formatter, to demonstrate the multi-format benefit
from dimension 10. Compiled and run with tsc 7.0.2 plus node, CPython 3.14.6,
and go 1.26.4 respectively.

### TypeScript

```typescript
type LogicalNode =
  | { kind: "page"; title: string; sections: LogicalNode[] }
  | { kind: "section"; heading: string; rows: LogicalNode[] }
  | { kind: "field"; label: string; value: string; type: "text" | "money" | "date" };

interface Article {
  title: string;
  author: string;
  publishedAt: Date;
  priceCents: number;
}

function buildLogicalPage(articles: Article[]): LogicalNode {
  return {
    kind: "page",
    title: "Catalog",
    sections: [
      {
        kind: "section",
        heading: "Articles",
        rows: articles.flatMap((a) => [
          { kind: "field", label: "Title", value: a.title, type: "text" },
          { kind: "field", label: "Author", value: a.author, type: "text" },
          {
            kind: "field",
            label: "Published",
            value: a.publishedAt.toISOString().slice(0, 10),
            type: "date",
          },
          {
            kind: "field",
            label: "Price",
            value: (a.priceCents / 100).toFixed(2),
            type: "money",
          },
        ]),
      },
    ],
  };
}

function formatAsHtml(node: LogicalNode): string {
  switch (node.kind) {
    case "page":
      return `<html><body><h1>${node.title}</h1>${node.sections
        .map(formatAsHtml)
        .join("")}</body></html>`;
    case "section":
      return `<section><h2>${node.heading}</h2><ul>${node.rows
        .map(formatAsHtml)
        .join("")}</ul></section>`;
    case "field":
      if (node.type === "money") {
        return `<li>${node.label}. $${node.value}</li>`;
      }
      return `<li>${node.label}. ${node.value}</li>`;
  }
}

function formatAsPlainText(node: LogicalNode): string {
  switch (node.kind) {
    case "page":
      return `${node.title.toUpperCase()}\n${node.sections
        .map(formatAsPlainText)
        .join("\n")}`;
    case "section":
      return `-- ${node.heading} --\n${node.rows.map(formatAsPlainText).join("\n")}`;
    case "field":
      const value = node.type === "money" ? `USD ${node.value}` : node.value;
      return `  ${node.label}: ${value}`;
  }
}

const articles: Article[] = [
  {
    title: "Two Step View Explained",
    author: "M. Fowler",
    publishedAt: new Date("2002-11-15"),
    priceCents: 4999,
  },
];

const logicalPage = buildLogicalPage(articles);
console.log(formatAsHtml(logicalPage));
console.log("---");
console.log(formatAsPlainText(logicalPage));
```

### Python

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Article:
    title: str
    author: str
    published_on: date
    price_cents: int


@dataclass
class FieldNode:
    label: str
    value: str
    field_type: str  # "text", "money", "date"


@dataclass
class SectionNode:
    heading: str
    rows: list[FieldNode] = field(default_factory=list)


@dataclass
class PageNode:
    title: str
    sections: list[SectionNode] = field(default_factory=list)


def build_logical_page(articles: list[Article]) -> PageNode:
    rows = []
    for a in articles:
        rows.append(FieldNode("Title", a.title, "text"))
        rows.append(FieldNode("Author", a.author, "text"))
        rows.append(FieldNode("Published", a.published_on.isoformat(), "date"))
        rows.append(FieldNode("Price", f"{a.price_cents / 100:.2f}", "money"))
    return PageNode(title="Catalog", sections=[SectionNode(heading="Articles", rows=rows)])


class HtmlFormatter:
    def render(self, page: PageNode) -> str:
        sections = "".join(self._render_section(s) for s in page.sections)
        return f"<html><body><h1>{page.title}</h1>{sections}</body></html>"

    def _render_section(self, section: SectionNode) -> str:
        rows = "".join(self._render_field(r) for r in section.rows)
        return f"<section><h2>{section.heading}</h2><ul>{rows}</ul></section>"

    def _render_field(self, node: FieldNode) -> str:
        value = f"${node.value}" if node.field_type == "money" else node.value
        return f"<li>{node.label}. {value}</li>"


class PlainTextFormatter:
    def render(self, page: PageNode) -> str:
        lines = [page.title.upper()]
        for section in page.sections:
            lines.append(self._render_section(section))
        return "\n".join(lines)

    def _render_section(self, section: SectionNode) -> str:
        lines = [f"-- {section.heading} --"]
        for r in section.rows:
            value = f"USD {r.value}" if r.field_type == "money" else r.value
            lines.append(f"  {r.label}: {value}")
        return "\n".join(lines)


def main() -> None:
    articles = [
        Article(
            title="Two Step View Explained",
            author="M. Fowler",
            published_on=date(2002, 11, 15),
            price_cents=4999,
        )
    ]
    logical_page = build_logical_page(articles)
    print(HtmlFormatter().render(logical_page))
    print("---")
    print(PlainTextFormatter().render(logical_page))


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type FieldType int

const (
	Text FieldType = iota
	Money
	DateVal
)

type FieldNode struct {
	Label string
	Value string
	Type  FieldType
}

type SectionNode struct {
	Heading string
	Rows    []FieldNode
}

type PageNode struct {
	Title    string
	Sections []SectionNode
}

type Article struct {
	Title       string
	Author      string
	PublishedOn string
	PriceCents  int
}

func buildLogicalPage(articles []Article) PageNode {
	var rows []FieldNode
	for _, a := range articles {
		rows = append(rows, FieldNode{"Title", a.Title, Text})
		rows = append(rows, FieldNode{"Author", a.Author, Text})
		rows = append(rows, FieldNode{"Published", a.PublishedOn, DateVal})
		rows = append(rows, FieldNode{"Price", fmt.Sprintf("%.2f", float64(a.PriceCents)/100), Money})
	}
	return PageNode{Title: "Catalog", Sections: []SectionNode{{Heading: "Articles", Rows: rows}}}
}

type Formatter interface {
	Render(page PageNode) string
}

type HtmlFormatter struct{}

func (HtmlFormatter) Render(page PageNode) string {
	var b strings.Builder
	b.WriteString("<html><body><h1>" + page.Title + "</h1>")
	for _, s := range page.Sections {
		b.WriteString("<section><h2>" + s.Heading + "</h2><ul>")
		for _, r := range s.Rows {
			value := r.Value
			if r.Type == Money {
				value = "$" + value
			}
			b.WriteString("<li>" + r.Label + ". " + value + "</li>")
		}
		b.WriteString("</ul></section>")
	}
	b.WriteString("</body></html>")
	return b.String()
}

type PlainTextFormatter struct{}

func (PlainTextFormatter) Render(page PageNode) string {
	var b strings.Builder
	b.WriteString(strings.ToUpper(page.Title) + "\n")
	for _, s := range page.Sections {
		b.WriteString("-- " + s.Heading + " --\n")
		for _, r := range s.Rows {
			value := r.Value
			if r.Type == Money {
				value = "USD " + value
			}
			b.WriteString(fmt.Sprintf("  %s: %s\n", r.Label, value))
		}
	}
	return strings.TrimRight(b.String(), "\n")
}

func main() {
	articles := []Article{
		{Title: "Two Step View Explained", Author: "M. Fowler", PublishedOn: "2002-11-15", PriceCents: 4999},
	}
	page := buildLogicalPage(articles)

	var htmlFmt Formatter = HtmlFormatter{}
	var textFmt Formatter = PlainTextFormatter{}

	fmt.Println(htmlFmt.Render(page))
	fmt.Println("---")
	fmt.Println(textFmt.Render(page))
}
```
