---
name: Routing
slug: routing
family: 17-ai-agentic
category: Workflow
aliases: [Model Router, Content-Based Router (agentic variant), Classify-and-Dispatch, Intent Routing, LLM Router]
first_described: "Anthropic engineering blog, Building Effective Agents, 2024"
maturity: canonical
related: [prompt-chaining, orchestrator-workers, evaluator-optimizer, chain-of-responsibility, fallback-chain]
incompatible_with: []
verified: 2026-08-02
---

# Routing

## 1. Name, aliases, and lineage

The canonical name in the agentic-systems literature is Routing, one of the five
workflow patterns Anthropic names in its engineering post Building Effective
Agents. prompt chaining, routing, parallelization, orchestrator-workers, and
evaluator-optimizer. The post defines the pattern in one sentence, "Routing
classifies an input and directs it to a specialized followup task. This
workflow allows for separation of concerns, and building more specialized
prompts." (Anthropic, [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents),
verified 2026-08-02). The post names two concrete applications. directing
distinct customer-service query types (general questions, refund requests,
technical support) to distinct downstream prompts and tools, and directing
easy or common questions to a smaller, cheaper model while hard or unusual
questions go to a more capable one, naming Claude Haiku and Claude Sonnet as
the cheap and capable ends respectively (Anthropic, same source).

The pattern is not new in kind, only in what sits at the branch points. The
Enterprise Integration Patterns catalog names the identical shape twenty years
earlier as the Content-Based Router, defined as "Use a Content-Based Router to
route each message to the correct recipient based on message content," which
"examines the message content and routes the message onto a different channel
based on data contained in the message" (Gregor Hohpe and Bobby Woolf,
*Enterprise Integration Patterns*, Addison-Wesley, 2003; exact definition text
verified against [enterpriseintegrationpatterns.com](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html),
verified 2026-08-02). The Gang of Four's Chain of Responsibility pattern is a
structural cousin rather than an alias. it passes a request along a chain until
some handler accepts it, whereas Routing (in both the messaging and the LLM
sense) computes a classification first and then makes one direct dispatch,
never a chain walk. See dimension 13 for the precise boundary.

In LLM-specific usage the pattern also goes by Model Router (the term OpenAI
and Microsoft use for their production systems, dimension 9), Intent Routing
(the term common in chatbot and voice-assistant literature, where the
classification target is a conversational intent rather than a task
category), and LLM Router (the general academic term used by the RouteLLM
paper, dimension 9). This entry uses Routing throughout to match Anthropic's
naming, since that is the term this family of the catalog inherits from
(family 17, AI and Agentic Patterns, workflow subgroup). Do not confuse this
pattern with URL routing in a web framework (React Router, Express routing) or
network routing (BGP, Kubernetes Ingress host and path rules). Those are real,
older uses of the word "routing" that solve a different problem. they route a
request to a destination based on a URL or network address, not a
classification of natural-language or task content. Kubernetes Ingress
supports exactly two native rule types for that job, host-based and
path-based routing (verified against a live Kubernetes ingress reference,
2026-08-02), and neither one performs the semantic classification step that
defines this pattern.

## 2. Problem and context

A single LLM call, driven by one prompt, is asked to handle every shape of
input a system receives. As the input variety grows the prompt grows with it.
one clause for refunds, one for technical support, one for sales questions,
each clause hedging against the others so the model does not blend a refund
policy answer into a technical support answer. Each new category makes the
prompt longer, makes every existing category's instructions marginally less
reliable because they now compete for the model's attention with unrelated
instructions, and makes the prompt harder for a human to review because a
single reviewer must hold every category's rules in mind at once to judge
whether a change to one clause silently changed the meaning of another.

The same growth happens on the cost axis even when the categories do not
compete for attention. A support system receives a mix of trivial questions
("what are your hours") and hard questions ("my production database is
returning corrupted rows after your migration"). Answering both with the same
frontier reasoning model wastes money on the trivial ninety percent to buy
correctness on the hard ten percent. Answering both with a cheap model risks
the hard ten percent, which is usually the ten percent where a wrong answer
costs the most.

The context in which Routing earns its place is a system whose inputs fall
into a small number of distinguishable categories, where each category is
better served by a distinct downstream configuration (a distinct prompt, a
distinct model, a distinct tool set, or a distinct retrieval corpus), and where
that category can be determined from the input itself before the specialized
work begins. The pattern is a poor fit for a system whose inputs are
genuinely homogeneous, or whose categories cannot be told apart cheaply and
reliably before the specialized work runs. dimension 4 makes both
non-applicability conditions explicit.

## 3. Forces

**Latency.** A router adds one call, or one inference pass, before the real
work starts. When the classifier is a small model or a rule the added latency
is small, often under 100 milliseconds for an embedding-based or fine-tuned
classifier, and can be near zero for a keyword or regex rule. When the
classifier is itself an LLM call the added latency is a second full round
trip. The pattern favors correctness and cost over the lowest possible
latency, and the classifier's own latency budget is a design decision, not a
given.

**Coupling.** Routing decouples the calling code from the specialized handling
logic. The caller sends every input to one entry point and never needs to know
which category handled it. This is a genuine win for maintainability, at the
cost of a new coupling point. every specialized handler, and the router
itself, must agree on the category taxonomy. Adding a category means touching
both the router and adding a new handler; changing a category's meaning means
auditing every place that assumed the old meaning.

**Consistency.** Because the router makes a single classification and then
commits to one path, the pattern gives up the ability for one input to be
handled by more than one specialization at once, unless the router explicitly
supports fan-out (dimension 8 covers multi-label routers). This trades
flexibility for a predictable, auditable decision. a support ticket has
exactly one owner category, and that ownership is visible in a log line.

**Operability.** A router is a natural place to put an observable seam. every
routing decision is a discrete event that can be logged, counted, and
alerted on, which is a genuine operational win over a single monolithic
prompt whose internal behavior is opaque. The cost is that the taxonomy
itself becomes an operational asset that must be maintained. a category that
silently stops firing, or a category whose classifier accuracy degrades, is
now a thing the operator has to notice.

**Cost.** This is the force Anthropic's own example leans on hardest, and the
force behind every commercial LLM router named in dimension 9. A cheap
classifier deciding between a cheap and an expensive downstream model turns a
single flat cost per request into a cost distribution shaped by actual
difficulty, and the RouteLLM paper reports over 2x cost reduction in some
configurations while holding quality (Isaac Ong, Amjad Almahairi, Vincent Wu,
Wei-Lin Chiang, Tianhao Wu, Joseph E. Gonzalez, M. Waleed Kadous, Ion Stoica,
"RouteLLM. Learning to Route LLMs with Preference Data," [arXiv 2406.18665](https://arxiv.org/abs/2406.18665),
verified 2026-08-02).

**Team topology.** In a large organization, Routing lets separate teams own
separate downstream handlers behind one shared classification boundary. the
support team owns the refund handler, the platform team owns the technical
handler, and neither has to coordinate on prompt wording as long as they
agree on the category contract. This mirrors why the Content-Based Router
exists in enterprise integration. it lets a message producer send to one
channel and stay decoupled from every consumer (Hohpe and Woolf, cited above).

**Cognitive load.** For the person reading the system, a routed system is
easier to reason about locally, one category at a time, but harder to reason
about globally, because understanding the whole system means understanding
the classifier's boundary decisions as well as every handler. A monolithic
prompt is the reverse. hard to read locally, but there is only one thing to
read.

## 4. Applicability and non-applicability

Reach for Routing when.

- Inputs fall into a small number of genuinely distinct categories, each of
  which is better served by a distinct prompt, model, tool set, or corpus.
  Anthropic's own phrasing is "complex tasks where there are distinct
  categories that are better handled separately, and where classification
  can be handled accurately" (Anthropic, cited above).
- Classification is materially cheaper than the specialized work it gates,
  either in latency, in dollars, or in both. cheap-classifier,
  expensive-executor is the shape that makes the pattern pay for itself.
- Different categories carry genuinely different risk or cost profiles, so
  sending everything through the most capable and most expensive path is
  wasteful, and sending everything through the cheapest path is risky.
- The categories are stable enough to be worth encoding as a taxonomy. a
  taxonomy that reshuffles every week costs more to maintain than the routing
  saves.
- Ownership of different categories needs to live with different teams,
  prompts, or models, and a shared classification boundary is the natural
  contract between them.

Do NOT reach for Routing when.

- The input space is genuinely homogeneous. there is one job and one way to
  do it. adding a router here adds latency and a taxonomy to maintain for
  zero benefit, and a single well-tuned prompt is strictly simpler.
- Classification itself is as hard, or harder, than doing the actual work.
  if determining the category requires reading the whole answer, the router
  has not saved anything; it has doubled the work while adding a second
  failure surface. This is the standard argument against a heavyweight LLM
  classifier gating trivial handlers.
- The correct response genuinely depends on more than one category at once,
  and the system cannot tolerate a single, exclusive dispatch. a ticket that
  is simultaneously a refund request and a technical bug report needs either
  a multi-label router (dimension 8) or a pattern built for combination, such
  as Orchestrator-Workers, not a single-label Router.
- The categories are unstable or unknown in advance, and there is no reliable
  labeled or heuristic signal to classify on yet. building a router taxonomy
  before the categories are understood produces a taxonomy that fights the
  real traffic shape.
- A single branching prompt already handles the variety correctly and cheaply
  enough that the added infrastructure, monitoring, and taxonomy maintenance
  of a real router would cost more than it saves. Anthropic itself frames
  every workflow pattern as opt-in complexity, not a default. "when building
  applications with LLMs, we recommend finding the simplest solution
  possible, and only increasing complexity when needed" (Anthropic, cited
  above).
- The system must guarantee every input reaches the single best-available
  handler with zero tolerance for misclassification, and no fallback path is
  acceptable. Routing without a fallback path is a liability, not a feature;
  if a system truly cannot afford a misroute, that argues for a stricter
  gate (human review, deterministic rules) ahead of the specialized handler,
  not a probabilistic router alone.

## 5. Structure

- **Classifier.** The component that inspects the input and produces a
  category label, or a set of labels with confidence scores. Concretely a
  small fine-tuned model, an embedding similarity match against category
  exemplars, a prompt to a cheap LLM asking for a structured category label,
  or a deterministic rule (a regex, a keyword list, a schema field). The
  classifier's only job is to decide where the input goes, never to answer
  it.
- **Route table.** The mapping from a category label to a handler. Concretely
  a dictionary, a switch statement, or a configuration file. The route table
  is the taxonomy made concrete, and it is the single place that must be kept
  in sync with every handler that exists.
- **Handler.** The specialized downstream unit bound to one category. a
  distinct prompt, a distinct model, a distinct tool, a distinct retrieval
  index, or any combination. Each handler is written and tuned for exactly
  its category, which is the entire justification for the pattern (dimension
  3, cognitive load and coupling).
- **Fallback (or default) handler.** The handler invoked when the classifier
  produces no confident match, an unrecognized label, or a confidence below a
  configured floor. A router without a fallback is a router that drops
  requests silently the day the classifier meets an input it was not built
  for; see dimension 11.
- **Confidence threshold (optional but recommended).** A configured floor
  below which the classifier's output is treated as unreliable and the
  fallback is invoked instead of the nominally matched handler. This is what
  separates a Routing implementation that degrades gracefully from one that
  confidently dispatches a wrong classification straight into a wrong
  handler.
- **Observability hook.** The point at which the classification decision,
  its confidence, and the chosen handler are recorded before dispatch. This
  is what turns Routing from a black box back into an auditable system
  (dimension 16).

## 6. ASCII structure diagram

```
                          +----------------------+
        input ----------->|      Classifier      |
                          | (rule, embedding,    |
                          |  small model, or      |
                          |  cheap LLM call)      |
                          +----------+-----------+
                                     |
                                     v
                          +----------------------+
                          |     Route Table      |
                          |  label -> handler     |
                          +----------+-----------+
                                     |
                confidence >= floor  |  confidence < floor
                and label known      |  or label unknown
                        +------------+-------------+
                        v                           v
             +---------------------+     +----------------------+
             |  Specialized Handler |     |  Fallback / Default  |
             |  (prompt A / model A |     |       Handler         |
             |   / tool set A)      |     +----------------------+
             +---------------------+                |
                        |                            |
                        v                            v
                  +-----------------------------------+
                  |         Observability sink         |
                  |  (label, confidence, latency, cost) |
                  +-----------------------------------+
                                     |
                                     v
                                  output
```

## 7. Dynamics

```
caller            classifier          route table        handler A       fallback
  |  send(input)      |                    |                  |               |
  |------------------>|                    |                  |               |
  |                   | classify(input)    |                  |               |
  |                   |------------------->|                  |               |
  |                   |                    | look up label    |               |
  |                   |<-------------------|                  |               |
  |                   |  {label, conf}     |                  |               |
  |                   |                    |                  |               |
  |         conf >= floor and label found  |                  |               |
  |                   |----------------------------------------->|            |
  |                   |                    |          handle(input)           |
  |                   |                    |               |                  |
  |<------------------------------------------------------- result -----------|
  |                   |                    |                  |               |
  |         (alternate path. low confidence or unknown label)                 |
  |                   |-------------------------------------------------------->|
  |                   |                    |                  |    handle(input)
  |<---------------------------------------------------------------- result ---|
```

The classification call happens once, before any specialized work begins.
The dispatch decision is made exactly once per input; there is no retry loop
across categories inside the router itself (a retry loop across models on
failure is a distinct concern, covered by the Fallback Chain pattern in the
same family, and can sit downstream of a specific handler without changing
the router's own dynamics). Every path, nominal or fallback, converges on the
same observability sink so the caller and any downstream monitoring see one
uniform event shape regardless of which branch fired.

## 8. Implementation variants

- **Rule-based classifier.** Regex, keyword match, or a schema field already
  present on the input (a form's "topic" dropdown, a webhook's event type).
  Zero added latency, zero added model cost, perfectly interpretable, and
  brittle against paraphrase. Appropriate when the category signal is
  already structured, or when the category space is small and the
  vocabulary is stable.
- **Embedding similarity classifier.** Compute an embedding of the input and
  compare it against a small set of category exemplar embeddings, choosing
  the nearest by cosine similarity. This is the approach the open-source
  semantic-router library implements, describing itself as "a superfast
  decision-making layer for your LLMs and agents that uses semantic vector
  space to make tool-use decisions by routing requests using semantic
  meaning" (Aurelio AI, [aurelio-labs/semantic-router](https://github.com/aurelio-labs/semantic-router),
  verified 2026-08-02). Fast, cheap, and tolerant of paraphrase, at the cost
  of needing representative exemplars per category and periodic tuning of
  the similarity threshold.
- **Small fine-tuned classifier model.** A lightweight model (a distilled
  transformer, a logistic regression over embeddings, a gradient-boosted
  tree over hand features) trained specifically to predict the category.
  RouteLLM evaluates exactly this shape, training routers including BERT
  classifiers and LLM-based classifiers on preference data between a strong
  and a weak model, and the paper reports that the trained routers retain
  most of their accuracy when the strong or weak model is swapped out at
  test time, which the authors treat as evidence of real transfer learning
  rather than overfitting to one specific model pair (Ong et al., cited
  above). This variant needs a labeled or preference dataset up front but
  gives the best latency and cost profile of any learned classifier.
- **LLM-as-classifier.** A cheap, fast LLM call asked to emit a structured
  category label, typically constrained with a JSON schema or an enum. This
  is the variant Anthropic's own example uses for the customer-service case,
  and it is the easiest variant to bootstrap because it needs no training
  data, only a clear prompt describing the categories. The trade is the
  added latency and cost of a full model call before the real work starts,
  and the classifier itself can be wrong in the same fuzzy ways any LLM call
  can be wrong.
- **Multi-label / weighted routing.** Instead of committing to exactly one
  category, the classifier returns a distribution or a top-k set, and the
  router either fans the input out to several handlers and merges results,
  or picks the top label with a runner-up recorded for audit. This variant
  is the bridge toward Orchestrator-Workers when a single input genuinely
  spans more than one specialization.
- **Cost-quality mode routing.** The router is given an explicit operating
  mode (favor cost, favor quality, or balance both) rather than a fixed
  confidence floor, and the same classifier output is interpreted
  differently depending on the mode. Microsoft's Model Router in Microsoft
  Foundry implements exactly this shape with three named modes, Balanced,
  Cost, and Quality (Microsoft, [Model router for Microsoft Foundry
  concepts](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router),
  verified 2026-08-02).
- **Learned meta-model over model outputs.** Rather than classifying the
  input alone, the router can predict, per candidate downstream model,
  whether that model will answer well, and pick the model with the best
  predicted outcome. Not Diamond's public description is exactly this. it
  "trains a meta-model that predicts which downstream LLM will perform best
  on a given query," going beyond routing into prompt adaptation for the
  chosen model (Not Diamond, verified via [notdiamond.ai](https://www.notdiamond.ai/)
  and corroborating third-party coverage, 2026-08-02). This variant treats
  routing as a prediction problem over the full set of candidate handlers
  rather than a discrete-category lookup, and it is closer to a learned
  policy than to a route table.

Language-idiomatic notes. in a language with first-class functions (the code
samples below use TypeScript, Python, Go, and Rust), the route table is
naturally a dictionary or hash map from label to closure, which is the
cleanest realization of the pattern and needs no class hierarchy at all. This
is worth naming explicitly because catalogs written before closures were
common idiom (including the original GoF-adjacent messaging literature)
sometimes present the analogous shape as a class hierarchy of routers; in any
language with closures that hierarchy is unnecessary ceremony.

## 9. Known production uses

- **OpenAI GPT-5 real-time router.** GPT-5 ships as "a unified system with a
  smart, efficient model that answers most questions, a deeper reasoning
  model (GPT-5 thinking) for harder problems, and a real-time router that
  quickly decides which to use based on conversation type, complexity, tool
  needs, and explicit user intent," and OpenAI states the router "is
  continuously trained on real signals, including when users switch models,
  preference rates for responses, and measured correctness" (OpenAI,
  Introducing GPT-5, verified via search-indexed page content from
  openai.com, 2026-08-02; direct fetch of openai.com returned an HTTP 403 at
  verification time, so this claim rests on the search engine's indexed
  quotation of the page rather than a direct fetch, noted here for honesty).
- **Microsoft Foundry Model Router (Azure AI Foundry).** A production,
  general-availability-track feature described as "a purpose-built, trained
  machine-learning model that analyzes each prompt in real time and routes
  it to the most suitable large language model," offered in three modes
  (Balanced, Cost, Quality), with Microsoft's own published measurement
  showing cost savings of 4.5 percent in Balanced mode, 4.7 percent in Cost
  mode, and 14.2 percent in Quality mode against an unrouted baseline
  (Microsoft, [Model router for Microsoft Foundry concepts](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router),
  verified 2026-08-02).
- **OpenRouter Auto Router.** A production, publicly billed routing endpoint,
  `openrouter/auto`, described by OpenRouter as automatically choosing "the
  best model for your prompt," sending simpler requests to cheaper models
  and harder ones to stronger models at no extra routing fee beyond the
  chosen model's standard rate, and stated to be powered by Not Diamond
  (OpenRouter, verified via [openrouter.ai](https://openrouter.ai/openrouter/auto)
  and its documentation, 2026-08-02).
- **LlamaIndex RouterQueryEngine.** A widely used open-source library
  component in the retrieval-augmented-generation ecosystem. "The router
  query engine will select the most appropriate query engine based on the
  query," using a pluggable selector (an LLM-based selector that emits
  structured JSON, or a Pydantic-typed selector) to pick one query engine
  from a set of candidates exposed as tools with metadata, with a distinct
  multi-selector variant for fanning a query out to more than one index at
  once (LlamaIndex, [Router Query Engine documentation](https://developers.llamaindex.ai/python/framework/module_guides/querying/router/),
  verified 2026-08-02). This is the pattern realized as a library primitive
  rather than a hosted service, and it is a direct instance of the
  multi-label variant named in dimension 8.

## 10. Consequences

Positive.

- Separation of concerns. each handler is written, tested, and tuned for
  exactly one category, and can be reasoned about, reviewed, and changed
  without touching the others.
- Cost control. cheap categories, or cheap-versus-expensive model choices,
  can be priced and paid for independently, which is the entire commercial
  argument behind every production router named in dimension 9.
- Team ownership. different teams can own different handlers behind a
  shared, explicit classification contract, reducing coordination cost.
- Observability. every request produces a discrete, loggable decision
  (which category, at what confidence), which is a strictly stronger
  observability surface than a monolithic prompt whose internal reasoning is
  opaque.
- Graceful specialization growth. adding a new category is, in the best
  case, additive. a new route-table entry and a new handler, without editing
  the classifier's decision logic for existing categories (though the
  classifier itself may need retraining or reprompting to recognize the new
  category reliably, which is not free, see dimension 11).

Negative.

- A new failure surface. the classifier can be wrong, and being wrong at the
  routing step is different from being wrong inside a monolithic prompt. a
  misrouted request is handled confidently and completely by the wrong
  specialist, which can be worse than a monolithic prompt hedging poorly
  across categories, because the wrong specialist has no signal that
  anything is off.
- Added latency and cost from the classification step itself, which is pure
  overhead on every request that would have been correctly handled by a
  single well-designed prompt in the first place.
- Taxonomy maintenance debt. the route table and the classifier's category
  definitions must be kept synchronized with every handler that exists, and
  with the real shape of incoming traffic, which drifts over time.
- Reduced flexibility for inputs that genuinely span more than one category,
  unless the multi-label variant (dimension 8) is deliberately built in from
  the start.
- A second thing to test, tune, and monitor, doubling the surface area of
  the system relative to a single prompt.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| A category of requests silently gets worse answers over time, with no error visible in logs | Classifier accuracy has drifted because real traffic shifted away from the exemplars or training data the classifier was built on, and nobody is monitoring per-category accuracy | Track per-category confidence distributions and, where feasible, a periodic human-labeled sample of routed traffic; alert when a category's confidence distribution shifts, not only when the router errors outright |
| A user reports getting a nonsensical or off-topic answer for a perfectly ordinary question | The classifier misrouted the request into a specialized handler whose prompt assumes a category the input does not actually belong to, and the handler answered confidently anyway because it has no signal that it received the wrong kind of input | Add a confidence floor and a fallback handler (dimension 5); make specialized handlers check, where feasible, whether the input plausibly matches the category before committing to a full specialized answer, rather than assuming the router is always right |
| Requests intermittently vanish or return an empty or generic error | There is no fallback handler, and an unrecognized label (a new category the classifier was never told about, or a malformed classifier output) has no route-table entry to dispatch to | Every route table has a mandatory default entry, per dimension 5. treat "no matching route" as a first-class, tested case, not an exception path discovered in production |
| Cost savings from routing to a cheap model evaporate over a few weeks | The classifier's confidence floor was tuned once against an initial traffic sample and never revisited as the traffic mix shifted, so an increasing share of requests fall through to the expensive fallback even though most of them are genuinely easy | Re-tune the confidence floor against current traffic on a schedule, and log the reason each request took the fallback path (low confidence versus unknown label versus explicit escalation) so drift is distinguishable from genuine difficulty |
| Two engineers each add a new category and the router now has two overlapping labels that both fire on similar inputs, with non-deterministic-looking results | The taxonomy has no single owner and no review gate, so category boundaries were added independently without checking for overlap against the existing set | Treat the route table and category taxonomy as a reviewed artifact with a single owning team or a lightweight RFC step before a new category is added, the same discipline applied to a shared API contract |
| The system correctly routes an input, and the specialized handler then fails, and the whole request fails with no retry | The router treats routing and execution as one atomic step with no separation between deciding which handler should answer and confirming that handler succeeded, so a downstream handler failure has nowhere to fall back to | Compose Routing with a Fallback Chain or Circuit Breaker on the handler side, so a handler failure (timeout, tool error, model outage) can fall back to the default handler or a degraded response, independent of the routing decision itself |

## 12. Trade-off matrix

Compared against the named alternatives that solve an adjacent problem.

| Force | Routing | Single prompt with branching instructions | Chain of Responsibility | Orchestrator-Workers | Content-Based Router (integration-messaging) |
|---|---|---|---|---|---|
| Latency overhead | One classification step, tunable from near zero (rules) to a full model call | None, one call total | Up to N handler checks walked in sequence before a match | An orchestrator call plus N worker calls, generally the highest of this set | Same shape as Routing, latency dominated by the routing logic, which in messaging systems is typically a cheap rule, not a model call |
| Cost control granularity | Per-category, can bind cheap and expensive models to distinct categories | None, every request pays the cost of the one prompt regardless of difficulty | Per-handler in the chain, but every handler upstream of the match may still run some check logic | Highest granularity, per-worker, but highest total cost since multiple workers may run | Per-channel, analogous to Routing, but the cost being optimized is typically infrastructure or SLA, not LLM token spend |
| Handles multi-category inputs | Only with the explicit multi-label variant (dimension 8) | Naturally, since one prompt can address several concerns in one pass | No, a chain commits to the first handler that accepts, not a combination | Yes, this is the pattern's purpose, combining several specialized workers into one answer | Only with an explicit Recipient List variant layered on top, not the base Content-Based Router |
| Failure mode when misclassified | Wrong specialist answers confidently unless a fallback and confidence floor are built in (dimension 11) | No misclassification possible, since there is no branch decision to get wrong, though the single prompt can still reason poorly | A chain that finds no matching handler fails closed if a default is not the last link, similar risk to Routing's missing-fallback case | A misassigned worker produces a wrong partial result that can corrupt the orchestrator's merge step | Same risk profile as Routing. a Content-Based Router with no default channel drops or dead-letters the message |
| Maintainability as categories grow | Additive in the common case, new label plus new handler, but taxonomy drift is a real ongoing cost (dimension 11) | Prompt grows linearly and instructions increasingly compete for attention, degrading every category as more are added | Chain grows linearly and ordering starts to matter a great deal, since an earlier handler can shadow a later, more specific one | Additive per worker, but the orchestrator's merge logic must be revisited for every new combination of workers that can co-occur | Same additive profile as Routing, well proven at scale in messaging middleware over two decades |
| Observability | Strong. every request logs a discrete category and confidence (dimension 16) | Weak. a single prompt's internal reasoning is not naturally decomposed into a loggable decision | Moderate. can log which handler in the chain accepted, but not why earlier handlers declined unless each logs its own rejection | Strong on the per-worker level, but the orchestrator's combination logic is its own opaque decision | Strong, this is a mature operational pattern in messaging with established monitoring conventions |

## 13. Related and incompatible patterns

- **Prompt Chaining** (same family, workflow subgroup). Chaining decomposes
  one task into an ordered sequence of LLM calls where each step's output
  feeds the next step's input. Routing decomposes a population of distinct
  tasks into parallel, independent handlers chosen by classification. The
  two compose cleanly. a router can dispatch a category to a handler that is
  itself a prompt chain, and Anthropic's own diagram of the workflow
  patterns treats them as siblings that are frequently combined rather than
  alternatives.
- **Orchestrator-Workers** (same family). Where Routing makes one exclusive
  choice among peers, Orchestrator-Workers dynamically decomposes a task
  into several subtasks that a central orchestrator dispatches to workers
  and then synthesizes. A Routing system that grows a genuine need to
  combine more than one category's output for a single input has outgrown
  Routing and should become Orchestrator-Workers rather than bolting
  ad-hoc fan-out onto a router; dimension 8's multi-label variant is the
  narrow middle ground between the two.
- **Evaluator-Optimizer** (same family). Orthogonal to Routing. an
  evaluator-optimizer loop critiques and refines a single response, and can
  sit inside any one of a router's specialized handlers without changing
  the router's own structure.
- **Chain of Responsibility** (GoF, structural cousin, not an alias). Both
  patterns pick exactly one handler from a set based on the request's
  properties, but they differ in decision shape. Chain of Responsibility
  walks a sequence, asking each handler in turn whether it will accept the
  request, until one does, and the calling code never sees the decision
  logic. Routing computes a classification once, up front, and looks the
  answer up in a table, so the decision logic is centralized and
  inspectable rather than distributed across handler predicates. A system
  built as a long Chain of Responsibility where handler order encodes
  priority is a reasonable candidate to refactor into Routing once the
  accept-or-decline predicates stabilize into a clean, nameable taxonomy
  (dimension 14).
- **Fallback Chain** (same family, safety and ops subgroup). Fallback Chain
  retries a failed operation against a sequence of alternative
  implementations (a different model, a cached response, a degraded static
  answer). It is the natural companion sitting downstream of a chosen
  handler. Routing picks which specialist should try first, Fallback Chain
  handles what happens when that specialist itself fails at runtime. The two
  solve different failure classes (misclassification versus handler
  failure) and are not substitutes for one another.
- **Content-Based Router** (Enterprise Integration Patterns, dimension 1).
  The direct lineage ancestor in message-oriented middleware. The structural
  shape (inspect content, pick a channel) is identical; the difference is
  entirely in what does the inspecting (a deterministic rule over structured
  message headers in classic EIP, versus a learned or LLM-based classifier
  over unstructured natural-language content in the agentic variant).
- **Incompatible with.** nothing in this catalog is structurally
  incompatible with Routing; the closest thing to a conflict is applying
  Routing and Chain of Responsibility to the same decision point
  simultaneously, which produces two competing, redundant classification
  mechanisms rather than a genuine combination, and should be resolved by
  picking one (dimension 14 covers the refactor direction).

## 14. Refactoring path in and out

**Introducing Routing into code that does not have it.** Start from a single
prompt or function that has grown a set of `if`/`else if` branches, each
handling a distinct case with materially different logic. First, extract each
branch's body into its own named function or prompt, unchanged in behavior.
Second, extract the branch conditions into a single classification step that
runs once, before any branch body executes, and produces a label rather than
directly executing a branch. Third, replace the `if`/`else if` chain with a
lookup from that label into a route table mapping labels to the extracted
functions. Fourth, add an explicit default entry in the route table and wire
it to whatever the original code did when no condition matched (or, if the
original code had no such case, add one and decide deliberately what it
should do, since a route table with no default is dimension 11's most common
failure mode). Fifth, add an observability hook that logs the label and
confidence before dispatch. At each step the system's external behavior does
not change; only the internal shape does, which keeps the refactor safe to do
incrementally and to verify against existing behavior at every step (Martin
Fowler's discipline for behavior-preserving refactoring, the general
principle any refactoring family entry in this catalog inherits, applies
directly here. change structure, not behavior, one small step at a time).

**Removing Routing when it stops earning its place.** The signal that a
router should be removed is the reverse of dimension 4's applicability
conditions. the categories have converged to the point that most handlers do
functionally the same thing with minor variation, or traffic has become so
homogeneous that one category now receives nearly all requests and the
others are vestigial. When that happens, first measure actual category
distribution over a representative window rather than assuming from memory,
since taxonomy drift (dimension 11) means the router's original design
assumptions may no longer match reality. If one category dominates,
consider collapsing the rare categories into the fallback handler rather
than maintaining dedicated code paths for traffic that no longer exists, and
if the remaining categories are functionally near-identical, merge their
handlers and remove the router entirely in favor of one prompt, folding
back into the shape dimension 2 describes as the starting point. Remove the
route table and classifier only after handlers are merged and confirmed
equivalent under the same test suite used before the router existed, never
before.

## 15. Testing and verification

Routing decomposes naturally into two independently testable concerns, which
is one of its genuine testing advantages over a monolithic prompt.

- **Classifier tests are pure unit tests.** given a fixed input, assert the
  classifier returns the expected label and a confidence above (or, for
  known-ambiguous inputs, deliberately below) the configured floor. Because
  the classifier's contract is input-to-label, not input-to-final-answer,
  these tests do not need to mock or stub downstream handlers at all, and
  they run fast and deterministically for rule-based and small-model
  classifiers. For LLM-based classifiers, pin the model version and
  temperature (ideally zero or near-zero for a classification task) and
  treat any observed non-determinism as a signal to move toward a smaller,
  deterministic classifier rather than something to work around with
  retries.
- **Handler tests are ordinary unit or integration tests for each
  specialized unit**, run entirely independent of the router, because
  dimension 3's coupling force means handlers only need to agree with the
  router on the label contract, so each handler can be developed, tested,
  and deployed without ever invoking the classifier.
- **Route table tests verify the contract, not the content.** assert every
  label the classifier can emit has a corresponding entry, and assert a
  default entry exists. This is the test that catches dimension 11's
  silently-vanishing-requests failure mode before it reaches production,
  and it is cheap. a route table is a small, enumerable structure, and this
  test can be exhaustive rather than sampled.
- **End-to-end tests should be a small, deliberately curated set** covering
  one representative input per category plus at least one input designed to
  be ambiguous or unclassifiable, to confirm the fallback path actually
  fires when it should. Do not attempt exhaustive end-to-end coverage of
  every classifier-handler combination; the classifier and handler unit
  tests already cover that combinatorially, and a large end-to-end suite for
  a routed system mostly retests the same handler logic once per category
  redundantly.
- **Confidence-floor tuning is an evaluation problem, not a unit-test
  problem.** maintain a labeled evaluation set of real or representative
  traffic and measure classifier accuracy, and the rate of fallback
  invocation, against it whenever the classifier, the categories, or the
  floor changes. This is the same evaluation discipline RouteLLM's own
  methodology depends on, since the paper's routers are trained and
  evaluated against human preference data specifically because a router's
  real quality claim, whether the cheap path actually preserves response
  quality, is an empirical question rather than a unit-testable one (Ong et
  al., cited above).

## 16. Observability signals

- **Per-request routing decision.** category label, confidence score, and
  which handler ultimately ran, logged as a single structured event per
  request. This is the minimum signal needed to answer why a request got
  the answer it got.
- **Fallback invocation rate.** the fraction of requests that hit the
  default handler because confidence fell below the floor or the label was
  unrecognized. A healthy router shows this rate roughly stable over time
  for a given confidence floor; a rising trend is the leading indicator of
  the taxonomy drift failure mode in dimension 11, and should be alerted on
  before it becomes a user-visible quality regression.
- **Per-category volume and latency distribution.** how many requests each
  category receives and how long each category's handler takes. This is
  what makes cost claims (dimension 3, dimension 9) auditable rather than
  assumed. it is the difference between believing a router saves money and
  measuring, per category, whether it actually does.
- **Classifier confidence distribution over time.** not only the pass or
  fail rate against the floor, but the shape of the confidence distribution
  itself. a distribution that used to cluster near 0.9 for a category and
  now clusters near 0.6 is a drift signal even before any request actually
  crosses the floor into fallback.
- **A healthy dashboard** shows stable per-category volumes matching known
  traffic composition, a low and stable fallback rate, and confidence
  distributions clustered well above the configured floor for the dominant
  categories. **A failing instance** shows a rising fallback rate, a
  confidence distribution drifting toward the floor for a previously
  healthy category, or a category whose volume has dropped to near zero
  while related complaint or escalation volume has risen, which usually
  means real traffic for that category is being misclassified into a
  different label rather than genuinely disappearing.

## 17. Security and privacy implications

The classifier is a new place that sees every input before any access
control or content policy specific to a downstream handler has been applied,
which means it inherits the full sensitivity of the raw input regardless of
which category eventually handles it. Two concrete implications follow.
First, if any category's handling logic is more privileged than another's (a
technical-support handler with tool access to internal systems, versus a
general-questions handler with none), the classification decision is now a
security boundary, and an attacker who can influence the classifier's output
(a form of prompt injection aimed at the classification step rather than the
final answer) can potentially route a request into a more privileged handler
than the input's true content warrants. Treat the router's dispatch decision
with the same suspicion as any other input-derived authorization decision,
and do not let classifier output alone grant access to a more privileged
tool set without an independent check inside the privileged handler itself.
Second, if the classifier is a third-party or hosted LLM call (the LLM-as-
classifier variant, dimension 8), every input is now transmitted to that
service purely to determine a category, even for inputs that a rule-based or
locally hosted classifier could have categorized without leaving the trust
boundary at all. For inputs carrying regulated or sensitive data, prefer a
locally hosted or rule-based classifier specifically to avoid an
unnecessary data-egress point that exists only to answer a routing question,
not to answer the user's actual request. This entry does not identify a
routing-specific encryption or storage concern beyond these two points; the
data-handling obligations of whichever handler ultimately processes the
request govern the rest, unchanged by the presence of a router in front of
it.

## 18. References

1. Anthropic. "Building Effective Agents." Anthropic Engineering Blog, 2024.
   https://www.anthropic.com/engineering/building-effective-agents. Verified
   2026-08-02.
2. Gregor Hohpe and Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   Content-Based Router pattern. Definition cross-checked against
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html.
   Verified 2026-08-02.
3. Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, Tianhao Wu, Joseph
   E. Gonzalez, M. Waleed Kadous, Ion Stoica. "RouteLLM. Learning to Route
   LLMs with Preference Data." arXiv, 2406.18665, 2024.
   https://arxiv.org/abs/2406.18665. Verified 2026-08-02.
4. OpenAI. "Introducing GPT-5." OpenAI, 2025. https://openai.com/index/introducing-gpt-5/.
   Router description quoted from search-engine-indexed page content;
   direct fetch returned HTTP 403 at verification time on 2026-08-02, so
   this claim carries that caveat explicitly.
5. Microsoft. "Model router for Microsoft Foundry concepts." Microsoft
   Learn. https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router.
   Verified 2026-08-02.
6. OpenRouter. "Auto Router." OpenRouter documentation and product page.
   https://openrouter.ai/openrouter/auto. Verified 2026-08-02.
7. LlamaIndex. "Router Query Engine." LlamaIndex documentation.
   https://developers.llamaindex.ai/python/framework/module_guides/querying/router/.
   Verified 2026-08-02.
8. Aurelio AI. "semantic-router." GitHub repository, aurelio-labs.
   https://github.com/aurelio-labs/semantic-router. Verified 2026-08-02.
9. Not Diamond. Product description. https://www.notdiamond.ai/. Verified
   2026-08-02.
10. Kubernetes documentation and reference material on Ingress host-based
    and path-based routing, consulted to establish the boundary between
    network/URL routing and the agentic Routing pattern described in this
    entry. Verified 2026-08-02.

## Code examples

Every sample implements the same shape. a classifier that inspects the
input, a route table mapping category labels to specialized handlers, a
confidence floor, and a fallback handler invoked when the floor is not met
or the label is unrecognized. All four were compiled or run against the
toolchains available on the authoring machine and produced the expected
output.

### TypeScript

```typescript
type Category = "refund" | "technical" | "general";

interface ClassificationResult {
  category: Category;
  confidence: number;
}

type Handler = (query: string) => string;

class Router {
  private routes: Map<Category, Handler> = new Map();
  private fallback: Handler;
  private confidenceFloor: number;

  constructor(fallback: Handler, confidenceFloor = 0.55) {
    this.fallback = fallback;
    this.confidenceFloor = confidenceFloor;
  }

  register(category: Category, handler: Handler): void {
    this.routes.set(category, handler);
  }

  dispatch(query: string, classify: (q: string) => ClassificationResult): string {
    const result = classify(query);
    if (result.confidence < this.confidenceFloor) {
      return this.fallback(query);
    }
    const handler = this.routes.get(result.category);
    if (!handler) {
      return this.fallback(query);
    }
    return handler(query);
  }
}

function classify(query: string): ClassificationResult {
  const lower = query.toLowerCase();
  if (lower.includes("refund")) return { category: "refund", confidence: 0.92 };
  if (lower.includes("error") || lower.includes("crash")) {
    return { category: "technical", confidence: 0.81 };
  }
  return { category: "general", confidence: 0.4 };
}

const router = new Router((q) => `general-desk handling: ${q}`);
router.register("refund", (q) => `refund-desk handling: ${q}`);
router.register("technical", (q) => `technical-desk handling: ${q}`);

const inputs = [
  "I want a refund for my order",
  "The app keeps crash on launch",
  "Tell me about your hours",
];

for (const input of inputs) {
  console.log(router.dispatch(input, classify));
}
```

Verified with `npx tsc --strict --target es2020 --module commonjs router.ts`
followed by `node router.js`, output.

```
refund-desk handling: I want a refund for my order
technical-desk handling: The app keeps crash on launch
general-desk handling: Tell me about your hours
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass
class Classification:
    label: str
    confidence: float


class Router:
    def __init__(self, fallback: Callable[[str], str], confidence_floor: float = 0.6) -> None:
        self._routes: Dict[str, Callable[[str], str]] = {}
        self._fallback = fallback
        self._confidence_floor = confidence_floor

    def register(self, label: str, handler: Callable[[str], str]) -> None:
        self._routes[label] = handler

    def dispatch(self, query: str, classify: Callable[[str], Classification]) -> str:
        result = classify(query)
        if result.confidence < self._confidence_floor:
            return self._fallback(query)
        handler: Optional[Callable[[str], str]] = self._routes.get(result.label)
        if handler is None:
            return self._fallback(query)
        return handler(query)


def cheap_classifier(query: str) -> Classification:
    lowered = query.lower()
    if "invoice" in lowered or "billing" in lowered:
        return Classification("billing", 0.88)
    if "outage" in lowered or "down" in lowered:
        return Classification("incident", 0.9)
    return Classification("unknown", 0.3)


def billing_handler(query: str) -> str:
    return f"billing-model (cheap) answered: {query}"


def incident_handler(query: str) -> str:
    return f"incident-model (expensive, on-call) answered: {query}"


def fallback_handler(query: str) -> str:
    return f"general-model (fallback) answered: {query}"


def main() -> None:
    router = Router(fallback_handler, confidence_floor=0.6)
    router.register("billing", billing_handler)
    router.register("incident", incident_handler)

    queries = [
        "Why is my invoice higher this month",
        "Production is down for all customers",
        "What is the weather like",
    ]
    for query in queries:
        print(router.dispatch(query, cheap_classifier))


if __name__ == "__main__":
    main()
```

Verified with `python3 router.py`, output.

```
billing-model (cheap) answered: Why is my invoice higher this month
incident-model (expensive, on-call) answered: Production is down for all customers
general-model (fallback) answered: What is the weather like
```

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type classification struct {
	label      string
	confidence float64
}

type handler func(query string) string

type router struct {
	routes          map[string]handler
	fallback        handler
	confidenceFloor float64
}

func newRouter(fallback handler, floor float64) *router {
	return &router{routes: make(map[string]handler), fallback: fallback, confidenceFloor: floor}
}

func (r *router) register(label string, h handler) {
	r.routes[label] = h
}

func (r *router) dispatch(query string, classify func(string) classification) string {
	result := classify(query)
	if result.confidence < r.confidenceFloor {
		return r.fallback(query)
	}
	h, ok := r.routes[result.label]
	if !ok {
		return r.fallback(query)
	}
	return h(query)
}

func classify(query string) classification {
	lower := strings.ToLower(query)
	switch {
	case strings.Contains(lower, "password"):
		return classification{label: "auth", confidence: 0.9}
	case strings.Contains(lower, "price"):
		return classification{label: "sales", confidence: 0.85}
	default:
		return classification{label: "unknown", confidence: 0.25}
	}
}

func main() {
	r := newRouter(func(q string) string {
		return fmt.Sprintf("general-desk handled: %s", q)
	}, 0.5)
	r.register("auth", func(q string) string {
		return fmt.Sprintf("auth-desk handled: %s", q)
	})
	r.register("sales", func(q string) string {
		return fmt.Sprintf("sales-desk handled: %s", q)
	})

	queries := []string{
		"I forgot my password",
		"What is the price for the enterprise plan",
		"Do you sell cats",
	}
	for _, q := range queries {
		fmt.Println(r.dispatch(q, classify))
	}
}
```

Verified with `go run main.go`, output.

```
auth-desk handled: I forgot my password
sales-desk handled: What is the price for the enterprise plan
general-desk handled: Do you sell cats
```

### Rust

```rust
use std::collections::HashMap;

struct Classification {
    label: String,
    confidence: f64,
}

struct Router {
    routes: HashMap<String, Box<dyn Fn(&str) -> String>>,
    fallback: Box<dyn Fn(&str) -> String>,
    confidence_floor: f64,
}

impl Router {
    fn new(fallback: Box<dyn Fn(&str) -> String>, confidence_floor: f64) -> Self {
        Router {
            routes: HashMap::new(),
            fallback,
            confidence_floor,
        }
    }

    fn register(&mut self, label: &str, handler: Box<dyn Fn(&str) -> String>) {
        self.routes.insert(label.to_string(), handler);
    }

    fn dispatch<F>(&self, query: &str, classify: F) -> String
    where
        F: Fn(&str) -> Classification,
    {
        let result = classify(query);
        if result.confidence < self.confidence_floor {
            return (self.fallback)(query);
        }
        match self.routes.get(&result.label) {
            Some(handler) => handler(query),
            None => (self.fallback)(query),
        }
    }
}

fn classify(query: &str) -> Classification {
    let lower = query.to_lowercase();
    if lower.contains("legal") {
        Classification { label: "legal".to_string(), confidence: 0.93 }
    } else if lower.contains("bug") {
        Classification { label: "engineering".to_string(), confidence: 0.87 }
    } else {
        Classification { label: "unknown".to_string(), confidence: 0.3 }
    }
}

fn main() {
    let fallback: Box<dyn Fn(&str) -> String> =
        Box::new(|q: &str| format!("general-desk handled: {}", q));
    let mut router = Router::new(fallback, 0.5);
    router.register(
        "legal",
        Box::new(|q: &str| format!("legal-desk handled: {}", q)),
    );
    router.register(
        "engineering",
        Box::new(|q: &str| format!("engineering-desk handled: {}", q)),
    );

    let queries = [
        "I need a legal review of this contract",
        "There is a bug in the checkout flow",
        "How is the weather today",
    ];

    for q in queries.iter() {
        println!("{}", router.dispatch(q, classify));
    }
}
```

Verified with `rustc src/main.rs -o router_bin` followed by `./router_bin`,
output.

```
legal-desk handled: I need a legal review of this contract
engineering-desk handled: There is a bug in the checkout flow
general-desk handled: How is the weather today
```

Java and Kotlin were not attempted. no Java runtime or compiler (`javac`)
was available on the authoring machine at verification time, and Kotlin was
not installed either, so neither sample could be honestly claimed as
compiled or run.
