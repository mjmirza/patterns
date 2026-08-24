---
name: Computer Use
slug: computer-use
family: 17-ai-agentic
category: Agentic
aliases: [GUI Agent, Screen Agent, Computer-Using Agent (CUA), Autonomous Desktop Control]
first_described: "Anthropic, 22 October 2024"
maturity: emerging
related: [function-calling, react-prompting, human-in-the-loop, prompt-injection-defense, sub-agent-isolation, llm-circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

# Computer Use

## 1. Name, aliases, and lineage

Computer Use is a specialization of tool use in which the tool's action space
is not a documented API but the same screenshot-and-input surface a human
uses, a rendered screen, a pointer, and a keyboard. The model reasons over an
image of the current display and emits discrete input events, click here,
type this, press that key, rather than a call to a typed function.

Anthropic gave the pattern its current name and shipped the first mainstream
vendor implementation on 22 October 2024, describing it as an API through
which Claude 3.5 Sonnet could "perceive and interact with computer
interfaces" by moving a cursor, clicking buttons, and typing text (Anthropic,
"Developing a computer use model", 22 October 2024,
https://www.anthropic.com/news/developing-computer-use, verified 2026-08-02).
The technical reference for the tool itself lives in Anthropic's API
documentation under the name computer use tool, exposed through tool types
named `computer_20241022`, `computer_20250124`, and `computer_20251124` as
the action set grew across model generations (Anthropic, "Computer use
tool", platform documentation,
https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool,
verified 2026-08-02).

OpenAI ships the same category of capability under a different name. Its
platform documentation describes a `computer-use-preview` model and a
`computer_use_preview` tool type as the mechanism behind Operator, OpenAI's
browsing agent, referring to the underlying model class as a
Computer-Using Agent, CUA, in its research materials (OpenAI, "Computer use",
API documentation,
https://developers.openai.com/api/docs/guides/tools-computer-use, verified
2026-08-02). Community usage settled on Computer-Using Agent as a
model-family name and GUI agent as a research-literature term for the
broader pattern, which predates either vendor's product. The benchmark most
commonly used to grade this pattern, OSWorld, was published five months
before Anthropic's announcement and already framed the target capability as
"autonomous agents that accomplish complex computer tasks with minimal human
interventions" across real Ubuntu, Windows, and macOS environments (Xie,
Zhang, Chen, Li, Zhao, Cao, Hua, Cheng, Shin, Lei, Liu, Xu, Zhou, Savarese,
Xiong, Zhong, Yu, "OSWorld, Benchmarking Multimodal Agents for Open-Ended
Tasks in Real Computer Environments", arXiv:2404.07972, submitted 11 April
2024, verified 2026-08-02). This entry treats Computer Use as the canonical
name because it is the term both major vendors converged on in
customer-facing documentation, and treats GUI Agent, Screen Agent, and CUA
as aliases for the same underlying mechanism rather than as distinct
patterns.

A separate implementation lineage grounds the same pattern in a different
representation of the screen. Instead of pixels and coordinates, an agent
can read the browser's Document Object Model, resolve interactive elements
by their accessibility role and bounding box, and act on element references
rather than raw coordinates. The open source project browser-use, with
over 107,000 GitHub stars at the time of writing, is the most widely adopted
implementation of this DOM-grounded variant and works with Claude, GPT, and
Gemini interchangeably (browser-use, GitHub repository,
https://github.com/browser-use/browser-use, verified 2026-08-02). Dimension
8 treats pixel grounding and DOM grounding as two implementation strategies
for one pattern, not as two patterns, because both share the same
structural shape, a stateless model proposing one action per turn against a
transcript maintained by the calling application.

## 2. Problem and context

Most of the software a person or a business depends on every day was never
built with an API for an autonomous agent to call. A decade-old internal
finance tool, a government portal, a vendor's desktop application with no
public integration surface, a competitor's website with deliberately no
public feed, a legacy Windows program still running the accounting
department, none of these expose a documented, versioned, machine-readable
way to ask a system to submit a form or read a table. The only interface any
of them guarantees is the one built for a person with eyes and hands, a
rendered screen and a set of input events.

Function calling and tool use solve the integration problem when a
documented API exists, see the function-calling entry in this family. They
do nothing for the much larger set of tasks that live behind a UI with no
API at all, or behind a workflow that spans several such tools that were
never designed to talk to each other. Robotic process automation addressed
part of this problem for two decades using scripted selectors or
computer-vision templates bound tightly to one specific screen layout, and
it breaks the moment a vendor ships a UI update that moves a button five
pixels. Computer Use is the answer that emerged once vision-language models
became reliable enough to look at an arbitrary, previously unseen screen and
decide, in natural language reasoning, what a human would click next,
without a developer having pre-recorded that exact screen.

The context in which this pattern earns its cost is specific, the target
system genuinely lacks an API, or the workflow spans multiple systems that
do not share one, and the task is valuable enough to absorb multi-second,
multi-dollar per-step latency in exchange for not building or maintaining a
bespoke integration. Outside that context, in particular whenever a
documented API for the same operation exists, this pattern is strictly the
wrong tool, a point the applicability list in dimension 4 makes explicit.

## 3. Forces

**Generality against latency.** A model that operates a screen the way a
person does can, in principle, operate any application that renders a
screen. That generality is purchased with latency an API call never pays,
a screenshot must be captured, transmitted, and reasoned over by a large
multimodal model before a single click happens, and OSWorld's own numbers
show current systems spend most of a multi-step task on this loop without
reaching the same 72 percent completion rate humans reach on the identical
tasks (Xie et al., arXiv:2404.07972, verified 2026-08-02).

**Coverage against grounding accuracy.** The pattern's whole appeal is that
it needs no per-application integration work. The cost is that the model
must predict, from pixels alone or from a DOM tree, exactly where the
element it means to click actually sits, and a coordinate or element
reference that is a few pixels or one level off in the accessibility tree
fails the entire step. OSWorld's authors attribute most of the human-model
gap specifically to weak GUI grounding and operational knowledge, not to
reasoning failures (Xie et al., arXiv:2404.07972, verified 2026-08-02).

**Autonomy against security exposure.** The value of the pattern rises with
how much of a workflow it can complete unattended, but every step of
unattended browsing of live, attacker-reachable content is a step where
content on the screen can carry instructions the model was never told to
trust. Anthropic's own red-teaming measured a 23.6 percent baseline attack
success rate for prompt injection against Claude for Chrome before
mitigations were applied (Anthropic, "Claude for Chrome", 25 August 2025,
https://claude.com/blog/claude-for-chrome, verified 2026-08-02). Autonomy
and exposure move together, not against each other, which is the
uncomfortable version of this force.

**Cost per step against task value.** Every turn of the loop is a full
multimodal inference call carrying at least one image, and vendor
documentation on image size limits and coordinate downscaling exists
precisely because screenshots are expensive to transmit and reason over
(Anthropic, "Computer use tool", verified 2026-08-02). A task cheap enough
to be worth automating with a documented API is rarely cheap enough to be
worth automating at several dollars and dozens of seconds per attempt using
Computer Use, the pattern earns its cost on tasks whose alternative is a
person doing the same clicking by hand, not on tasks with a cheaper
automatable path.

**Auditability against fidelity.** A typed function call produces a compact,
replayable log entry. A screenshot-driven action stream produces a sequence
of images and coordinates that is harder to diff, harder to redact of
personal data before storage, and harder to prove was interpreted correctly
after the fact, even though it is, in another sense, the most faithful
record of what the agent actually saw and did.

This entry favors coverage, in the sense that Computer Use exists to reach
software nothing else can reach, and it deliberately sacrifices latency,
cost efficiency, and a large part of the auditability that a typed API call
would give for free. A team that reaches for this pattern accepts that
trade going in, or the trade will surprise them in production.

## 4. Applicability and non-applicability

Reach for Computer Use when the following hold.

- No documented API exists for the operation, and building one is not an
  option because the target system is a third party's product, a legacy
  internal tool nobody maintains, or a competitor's public site.
- A workflow spans several applications that share no common integration
  surface, and a person today completes it by switching between windows.
- The task is inherently visual, confirming that a rendered page looks
  correct, verifying a generated UI against a design, or reading a chart
  image that has no underlying data export.
- The volume of the task is low enough, occasional operator-run workflows,
  QA smoke checks, one-off data retrieval, that multi-second, multi-dollar
  steps are an acceptable cost against the alternative of a person doing it
  by hand.
- The environment can be isolated, a dedicated browser profile or sandboxed
  virtual machine with no standing access to credentials the task does not
  need.

Do not reach for Computer Use when any of the following hold.

- A documented API exists for the same operation. Function calling against
  that API is cheaper per call by roughly two orders of magnitude, more
  reliable because it removes the grounding-accuracy failure mode entirely,
  and produces a replayable audit log for free. This is the single most
  common misuse of the pattern, building a screen-clicking agent for a task
  that a REST call would complete in one round trip.
- The workload needs high throughput. A screenshot-round-trip loop measured
  in seconds per step cannot serve thousands of transactions per second the
  way a typed API integration can, OSWorld's own reported completion times
  make this concrete rather than theoretical (Xie et al., arXiv:2404.07972,
  verified 2026-08-02).
- The action has an irreversible real-world consequence, a financial
  transfer, an account deletion, a legal submission, and no human
  confirmation gate sits between the model's proposal and its execution.
  Anthropic's own guidance explicitly asks integrators to require human
  confirmation before tasks requiring affirmative consent, such as
  accepting cookies, completing financial transactions, or agreeing to
  terms of service (Anthropic, "Computer use tool", verified 2026-08-02).
- The agent would be exposed to arbitrary, untrusted third-party content,
  the open web in particular, without sandboxing, credential isolation, and
  a domain allowlist. This is not a hardening detail, both vendors document
  it as a load-bearing requirement, not an optional extra (Anthropic,
  "Computer use tool", verified 2026-08-02; OpenAI, "Computer use", verified
  2026-08-02).
- The task needs precision finer than current grounding accuracy supports,
  fine-grained image editing, CAD manipulation, pixel-level design work.
  This is exactly the class of failure OSWorld's authors flag as the
  dominant weakness of current systems (Xie et al., arXiv:2404.07972,
  verified 2026-08-02).
- The goal is bulk structured data extraction rather than interaction. A
  DOM read, a scraper, or a documented export is strictly cheaper and more
  reliable than driving a mouse across a page to read numbers off it, the
  DOM-grounded variant covered in dimension 8 exists partly to reduce
  reliance on pixel grounding for exactly this class of task, but a true
  extraction job usually needs neither variant.
- The task is long-horizon with no natural checkpoint. Errors compound
  silently across dozens of turns before anything catches them, which is
  the largest single contributor to the low completion rate OSWorld
  measures on multi-step tasks (Xie et al., arXiv:2404.07972, verified
  2026-08-02).

## 5. Structure

- **Task specification.** The natural-language goal a person or an
  upstream orchestrator gives the loop, for example a request to save a
  picture of a cat to the desktop (Anthropic, "Computer use tool", verified
  2026-08-02). It is supplied once, at the start of the loop, and is not
  renegotiated mid-task.
- **Perception source.** A screenshot of the current display, or in the
  DOM-grounded variant, a structured extract of interactive elements with
  their roles and bounding boxes. This is the only channel through which
  the model learns anything about the effect of its previous action, the
  model itself holds no persistent memory of the environment between calls.
- **Policy model.** A vision-language model that receives the task, the
  running transcript of prior actions and their results, and the latest
  perception, and returns exactly one proposed action per turn, formatted
  as a structured tool call rather than free text.
- **Action vocabulary.** A fixed, versioned set of primitive input events
  the model is allowed to name, click at a coordinate or on an element,
  type text, press a key combination, scroll, drag, wait, and capture a
  fresh screenshot. Anthropic's tool exposes this vocabulary as an explicit
  schema that grows across tool versions, from a small basic set in
  `computer_20241022` to a superset including drag, hold-key, and a
  region-zoom action in later versions (Anthropic, "Computer use tool",
  verified 2026-08-02).
- **Action dispatcher.** The calling application's code, not the model,
  that receives a proposed action, translates it into a real operating
  system event, and returns the resulting screenshot or an error. Vendor
  documentation is explicit that Claude cannot run the tool directly, the
  calling application is responsible for implementation (Anthropic,
  "Computer use tool", verified 2026-08-02).
- **Sandboxed environment.** The actual machine or browser profile being
  controlled, isolated from any credential or data the task does not need.
  Anthropic's reference implementation runs a virtual X11 display, a
  lightweight desktop, and a small set of preinstalled applications inside
  a Docker container built for exactly this purpose (Anthropic, "Computer
  use tool", verified 2026-08-02).
- **Safety layer.** A combination of a domain or application allowlist, a
  confirmation gate for actions marked consequential, and, on Anthropic's
  side, an automatic classifier that inspects incoming screenshots for
  injected instructions and can force the loop to pause for user
  confirmation (Anthropic, "Computer use tool", verified 2026-08-02).
- **Transcript.** The append-only history of every screenshot, proposed
  action, and execution result, resent to the model on every turn because
  the model itself carries no state between API calls.

## 6. ASCII structure diagram

```
  task text
      |
      v
+-----------+   screenshot + transcript   +----------------+
|  Policy   |<----------------------------|   Transcript   |
|  model    |----------------------------->|   (append-     |
|  (VLM)    |   one proposed Action         |   only state)  |
+-----------+                              +----------------+
      |
      | Action { name, args }
      v
+-----------------+   allow / deny / hold  +------------------+
|  Safety layer     |----------------------->|  Confirmation    |
|  allowlist,        |                        |  prompt to the   |
|  injection check   |<-----------------------|  human operator  |
+-----------------+   confirm / cancel      +------------------+
      | executed
      v
+-------------------+   input event    +-----------------------+
|  Action dispatcher |----------------->|  Sandboxed environment |
|  (X11, CDP, or      |<-----------------|  (VM, container, or    |
|  accessibility API)  |   screenshot     |  isolated browser)     |
+-------------------+                  +-----------------------+
```

## 7. Dynamics

```
User          Dispatcher        Policy model      Safety layer     Environment
 |  task text     |                   |                 |               |
 |--------------->|                   |                 |               |
 |                |--- screenshot --->|                 |               |
 |                |                   |--- capture ---------------------->|
 |                |                   |<-- screenshot --------------------|
 |                |<-- proposed action|                 |                |
 |                |----- check ------------------------>|                |
 |                |                   |    allowed      |                |
 |                |<--------------------------------- ok |                |
 |                |------------------ execute event -------------------->|
 |                |<----------------- new screenshot -----------------------|
 |                |--- new screenshot + result --------->|(sent to policy)|
 |                |                   |  loop repeats until              |
 |                |                   |  stop_reason != tool_use or      |
 |                |                   |  step budget exhausted           |
 |<-------------------------------- final result --------|                |
```

The repetition of proposing, checking, executing, and feeding back the
result without any new input from the user is what vendor documentation
calls the agent loop, "Claude responding with a tool use request and your
application responding to Claude with the results of evaluating that
request" (Anthropic, "Computer use tool", verified 2026-08-02). A second
branch exists off this main loop, triggered when the safety layer's injection
classifier flags the incoming screenshot as carrying a possible instruction
override, the loop pauses and routes to the human operator for confirmation
before the next action executes, rather than continuing automatically
(Anthropic, "Computer use tool", verified 2026-08-02).

## 8. Implementation variants

**Pixel-grounded, coordinate-based.** The model is shown a screenshot and
returns raw `[x, y]` pixel coordinates for clicks and drags. This is what
Anthropic's `computer_20241022` through `computer_20251124` tool types and
OpenAI's `computer-use-preview` model both implement (Anthropic, "Computer
use tool", verified 2026-08-02; OpenAI, "Computer use", verified
2026-08-02). It generalizes to any application that renders pixels,
including canvas-based apps and remote desktops a DOM-grounded agent cannot
reach, at the cost of a hard grounding-accuracy problem, the model must
learn a mapping from visual features to exact screen positions, and that
mapping degrades whenever the resolution the model reasons over differs
from the resolution the environment actually renders at, which is why
vendor documentation devotes a dedicated section to keeping
`display_width_px` and `display_height_px` synchronized with the real
screenshot dimensions (Anthropic, "Computer use tool", verified 2026-08-02).

**DOM or accessibility-tree grounded.** Instead of pixels, the calling
application extracts the page's structured element tree, interactive
elements with a role, a label, and a bounding box, and the model selects an
element reference rather than a coordinate, the dispatcher then resolves
that reference to a native click or fill event. The browser-use project is
the most widely adopted open source implementation of this variant, describing its
approach as identifying interactive elements programmatically rather than
through vision-based screenshot analysis (browser-use, GitHub repository,
verified 2026-08-02). This trades away generality, it only works where the
target renders an accessible DOM, canvas games and many legacy desktop
applications do not qualify, for a large reliability gain, element
resolution removes the pixel-coordinate regression problem entirely and
tends to be cheaper because the model reasons over structured text rather
than an image on every turn, though many DOM-grounded agents still send an
occasional screenshot to resolve visual ambiguity a DOM alone cannot
express.

**Set-of-marks visual grounding.** A hybrid used in several research
baselines and open agent frameworks, where the calling application overlays
numbered boxes on top of detected interactive regions in the screenshot
before sending it to the model, and the model returns a mark number rather
than a coordinate. This turns a continuous coordinate-regression problem
into a discrete classification problem, reducing the specific failure mode
of a near-miss click, at the cost of an extra detection pass to find and
number the candidate regions before every turn.

**Native accessibility API grounding.** The same element-reference idea
applied outside the browser, to native desktop or mobile applications
through their platform accessibility APIs, Windows UI Automation, macOS
Accessibility, Android's accessibility service. This is the natural
extension of the DOM-grounded variant to targets that have no browser DOM
at all but do expose an accessibility tree, and it inherits the same trade,
strong reliability where the tree is well-labeled, and no coverage at all
where an application ships with poor or absent accessibility metadata.

**Supervisory dispatcher wrapper.** Orthogonal to all four grounding
strategies above, production deployments add a policy layer between the
model's proposed action and its execution, an allowlist of reachable
domains or applications, a confirmation gate for actions flagged
consequential, and a session log for later audit. This is not a grounding
choice, it is a deployment discipline every variant needs, and the Go
example in this entry demonstrates the shape of it directly.

## 9. Known production uses

Anthropic's computer use tool shipped inside the Claude API on 22 October
2024 and was, by the vendor's own account, already being explored at launch
by named partners including Asana, Canva, Cognition, DoorDash, Replit, and
The Browser Company, with Replit specifically using it to develop a key
feature that evaluates apps inside Replit Agent (Anthropic, "Developing a
computer use model", verified 2026-08-02).

Claude for Chrome, Anthropic's own browser extension, is a direct
productization of the same tool inside everyday browsing rather than a
sandboxed demo environment. It piloted with 1,000 Max plan subscribers in
August 2025, expanded to all Max subscribers by November 2025, and reached
Pro, Team, and Enterprise plans by December 2025, at which point Anthropic
also published measured prompt injection attack success rates for the
product, dropping from a 23.6 percent baseline to 11.2 percent after
mitigations, with browser-specific attacks reduced from 35.7 percent to
zero (Anthropic, "Claude for Chrome", verified 2026-08-02).

OpenAI's Operator, and the `computer-use-preview` model behind it, is the
second major vendor's shipped instance of the same pattern, documented in
OpenAI's own developer guide as a model that receives screenshots and
returns structured click, scroll, type, keypress, and drag actions inside
an isolated browsing environment (OpenAI, "Computer use", verified
2026-08-02). The guide's own migration notes describing
`computer-use-preview` as deprecated in favor of newer tool versions are
themselves evidence of a production deployment history long enough to
require a deprecation path.

browser-use is the most adopted open source instance of the DOM-grounded
variant, at over 107,000 GitHub stars, built to make websites accessible
for AI agents and used across form filling, data extraction, and automated
QA workflows, with support for Anthropic, OpenAI, Google, and locally
hosted models through Ollama behind one interface (browser-use, GitHub
repository, verified 2026-08-02).

## 10. Consequences

Positive consequences.

- Reaches software with no documented integration surface at all,
  collapsing what would otherwise be a bespoke, per-target integration
  project into one general-purpose tool the model already knows how to
  operate.
- Decouples an agent's capability from the willingness or ability of a
  third party to build an API, which matters for legacy internal tools and
  for products whose vendor will never ship one.
- Enables workflows that cross several applications with no shared
  integration surface, because the model operates the same window switching
  and copy-paste steps a person already performs.
- Provides a visual verification channel no typed API call can offer, the
  agent can confirm that a page renders correctly, not merely that an
  endpoint returned a 200 status.

Negative consequences.

- Costs substantially more per step than a typed function call, in both
  latency and tokens, because every turn carries at least one image through
  a full multimodal inference (Anthropic, "Computer use tool", verified
  2026-08-02).
- Fails at a rate that makes it unsuitable for unattended, high-value, or
  high-volume work today, OSWorld's own comparison of a roughly 72 percent
  human completion rate against a far lower best-model rate is the clearest
  evidence available that this gap is real and not a vendor-specific
  limitation (Xie et al., arXiv:2404.07972, verified 2026-08-02).
- Opens a security surface that a typed API call does not have, rendered
  content the model reads can carry instructions the model was never given
  permission to follow, and both major vendors now publish measured attack
  success rates against this specific risk (Anthropic, "Claude for Chrome",
  verified 2026-08-02).
- Produces an audit trail that is heavier, harder to redact, and harder to
  diff than a structured API call log, because the record of what happened
  is a sequence of screenshots and coordinates rather than a typed request.
- Is fragile to environment drift, a resolution change, a UI redesign, or a
  different operating system in the target environment can silently break
  grounding accuracy in a way a versioned API contract would have caught at
  build time instead of at run time.

## 11. Failure modes and misuse

**Symptom.** The agent clicks repeatedly in roughly the right region of
the screen but never lands on the intended element, across many attempts on
the same task. **Cause.** The resolution the model was shown in the tool
definition, `display_width_px` and `display_height_px`, no longer matches
the resolution of the screenshot actually sent, often because the image was
resized after the tool definition was set once at startup. **Fix.** Keep
the reported display dimensions equal to the true dimensions of every
screenshot sent, and if the real screen exceeds the model's supported image
size, resize deliberately and rescale returned coordinates back to the real
screen space in application code, exactly the transformation demonstrated
in this entry's TypeScript example (Anthropic, "Computer use tool", verified
2026-08-02).

**Symptom.** The agent reports a task complete, for example that a form
was submitted, while the following screenshot still shows the form open
with a visible error message. **Cause.** The model inferred the outcome of
its own action from intent rather than verifying it against the next
screenshot, a failure mode vendor documentation names directly, that
"Claude sometimes assumes outcomes of its actions without explicitly
checking their results" (Anthropic, "Computer use tool", verified
2026-08-02). **Fix.** Require an explicit verification step in the system
prompt after every state-changing action, asking the model to compare the
new screenshot against the expected outcome before moving on, rather than
trusting a self-reported success claim.

**Symptom.** During an unattended browsing task, the agent begins
performing actions the user never asked for, submitting a purchase,
navigating to an unrelated page, or revealing information it was not asked
to reveal. **Cause.** Prompt injection, instructions embedded in rendered
page content override the user's original task, a risk both vendors
document explicitly and that Anthropic measured at a 23.6 percent baseline
success rate before mitigations on Claude for Chrome (Anthropic, "Claude
for Chrome", verified 2026-08-02). **Fix.** Isolate the browsing session
from standing credentials, enforce a domain allowlist, require explicit
human confirmation before any consequential action executes, and treat
vendor-provided injection classifiers as one layer of defense rather than
the only one.

**Symptom.** The task fails consistently on a specific class of widget,
custom dropdowns, scrollbars, or drag-based sliders, even though ordinary
clicks and typed text work reliably elsewhere in the same session.
**Cause.** Some interface elements resist reliable manipulation through
mouse coordinates alone, vendor guidance names dropdowns and scrollbars
directly as elements that are tricky for Claude to manipulate using mouse
movements (Anthropic, "Computer use tool", verified 2026-08-02).
**Fix.** Prompt the model toward keyboard-driven alternatives, tab
navigation and arrow-key selection, for that class of widget, or route that
portion of the workflow through a DOM-grounded implementation where the
element can be selected and set directly.

**Symptom.** A task a person completes in under a minute runs the agent
through twenty or more turns and still does not finish, or finishes having
drifted from the original goal partway through. **Cause.** No checkpoint
exists between the start and end of the task, so an early small error
compounds silently across many subsequent turns before anything catches
it, this is the dominant driver behind the large gap OSWorld measures
between human and model completion rates on multi-step tasks (Xie et al.,
arXiv:2404.07972, verified 2026-08-02). **Fix.** Decompose the task into
checkpointed sub-goals with an explicit verification of state after each
one, and cap the step budget per sub-goal rather than only per whole task,
so a drift is caught close to where it started.

**Symptom.** A workflow that passed every test in a development
environment fails intermittently once deployed to a different machine.
**Cause.** The reference implementation's fixed defaults, a specific screen
resolution and a specific desktop environment inside a container, were
baked into prompts or examples instead of being read from the real runtime
environment. **Fix.** Treat display resolution and environment identity as
runtime parameters passed into every tool call, never as constants copied
from a quickstart example, so the same task definition behaves the same way
regardless of where the sandboxed environment actually runs.

## 12. Trade-off matrix

| Force | Computer Use (pixel-grounded) | Function Calling against a documented API | DOM/accessibility-grounded agent (browser-use style) | Legacy selector-based RPA |
|---|---|---|---|---|
| Latency per step | High, seconds, one multimodal call per action | Low, one typed request | Medium, faster than pixel grounding, still model-in-the-loop | Very low, no model call at all |
| Coverage where no API exists | High, works on anything rendered | None, requires an API | Medium, requires a DOM or accessibility tree | Medium, but brittle to layout change |
| Reliability of targeting | Lower, pixel-coordinate regression is the main failure mode | Highest, no targeting problem exists | Higher than pixel grounding, element reference resolution is more stable | High until the UI changes, then it breaks outright |
| Cost per action | Highest, image tokens plus inference | Lowest | Medium, lower than pixel grounding when vision is not needed | Lowest at run time, high maintenance cost over time |
| Security exposure to rendered content | High, direct exposure to prompt injection | None, no page content is read as instructions | High, same rendered-content exposure as pixel grounding | Low, no natural-language interpretation of content |
| Resilience to UI redesign | Medium, the model can adapt to new layouts it has never seen | Not applicable, the API contract does not change with the UI | Medium, breaks if element labels or roles change | Low, a scripted selector or template usually breaks immediately |
| Auditability | Low, screenshots are heavy and hard to diff | High, typed requests are easy to log and replay | Medium, element references log more compactly than pixels | High, scripted steps are fully deterministic |

## 13. Related and incompatible patterns

Computer Use is a specialization of function calling, entry
`function-calling` in this family, the same tool-use, tool-result loop
described there governs the API surface, only the tool's own action
vocabulary is unusually narrow and unusually stateful. Anthropic's own
documentation treats computer use as one tool type among several a single
`tools` array can carry alongside a bash tool and a text editor tool
(Anthropic, "Computer use tool", verified 2026-08-02), which is the clearest
evidence that it is a tool-use instance rather than a separate loop
architecture.

The reasoning loop that decides when to reach for the computer use tool at
all, and when to stop and report a result, is typically an instance of
ReAct, entry `react-prompting`, the model alternates between a reasoning
step, deciding what the next screenshot suggests should happen, and an
acting step, emitting the next tool call.

Human-in-the-loop, entry `human-in-the-loop`, is not optional decoration on
top of Computer Use, it is the mechanism vendor safety guidance repeatedly
names as the required gate before any consequential action executes
(Anthropic, "Computer use tool", verified 2026-08-02).

Prompt injection defense, entry `prompt-injection-defense`, is the direct
security counterpart to this pattern's largest documented risk, the
attack-success-rate numbers cited in dimension 9 and dimension 11 are the
concrete evidence that this pairing is not theoretical.

Sub-agent isolation, entry `sub-agent-isolation`, describes the broader
practice of running a risky capability inside its own bounded context and
environment, of which the sandboxed VM or container described in dimension
5 is a specific, physical instance rather than a logical context boundary
alone.

LLM circuit breaker, entry `llm-circuit-breaker`, is the pattern that bounds
runaway loops by cost or step count, directly addressing the long-horizon
failure mode described in dimension 11, a task that should take five steps
silently running for fifty.

**Incompatibility worth naming plainly.** Function calling designs that
assume an action is safely retryable, a `GET` request returning the same
data twice with no side effect, do not carry over to Computer Use. A
`left_click` is not idempotent, retrying it after an ambiguous or timed-out
result risks a double submission, a double purchase, or a second, unwanted
navigation, because the action has already changed the state of a real
interface the first time it ran, whether or not the calling application
received clear confirmation of that. Any retry logic built for Computer Use
has to be written from this assumption, not borrowed from an idempotent API
client.

## 14. Refactoring path in and out

Introducing this pattern usually starts from function calling against
whatever documented API already exists, and Computer Use is added only as
a fallback branch for the specific operations that API cannot reach, no
endpoint exists for that action, or the workflow crosses into a second
system with no shared integration. The sandboxed environment, the domain
or application allowlist, and the confirmation gate for consequential
actions are built and wired in before the tool is ever given network
access, not added afterward once a task has already run unattended. Each
subtask introduced this way is worth validating against a small, held-out,
OSWorld-style task set before it ships broadly, so grounding accuracy on
the specific target application is measured rather than assumed.

The path out runs the opposite direction. Once a workflow the loop performs
regularly has stabilized, the same transcript the loop already logs, which
network requests actually fired, which DOM elements were actually
manipulated, becomes the specification for a typed integration, capture the
underlying API calls with a network trace, or capture the stable DOM
selectors the DOM-grounded variant already resolved, and replace the
screen-driving loop with a direct call to that mechanism. The healthy
trajectory for this pattern in a mature system is temporary and narrowing
over time, exploratory coverage of the long tail of applications that lack
an API, feeding a small and growing set of durable integrations, not a
permanent architecture a team keeps running indefinitely for tasks that
would be cheaper and more reliable as a typed call.

## 15. Testing and verification

Golden-trace regression testing is the primary technique, record a known
good sequence of screenshots, proposed actions, and outcomes for a
representative task, then replay the task against the current model and
environment and diff the final outcome state, not the exact coordinate
sequence, because two runs that reach the identical end state through
slightly different pixel paths both count as passing. Property-based tests
on the action dispatcher itself are cheap and high value, and this entry's
Python and Go examples are literally the surface those tests exercise, a
click at coordinates outside the current display bounds must raise a
bounds error rather than silently executing, demonstrated by the
`BoundsError` case in the Python example, and a navigation to a host
outside the configured allowlist must be rejected before it ever reaches
the environment, demonstrated by the `errBlockedDomain` case in the Go
example. Fault injection against the safety layer specifically, feeding a
scripted page carrying an injected instruction and asserting the
confirmation gate actually intercepts it rather than merely logging it, is
the direct test of the mitigation vendors report measured attack-success
numbers for (Anthropic, "Claude for Chrome", verified 2026-08-02).

What is genuinely harder to test is full end-to-end determinism. A
vision-language model's output is not deterministic run to run even at a
fixed temperature setting close to zero, and a target application's layout
can shift between test runs for reasons entirely outside the test's
control. The practical response is to assert properties rather than exact
traces, the loop never crossed the domain allowlist, the loop never
exceeded its configured step budget, and the loop eventually reached one of
a small, enumerated set of acceptable end states, rather than asserting a
single expected sequence of clicks. A benchmark suite built on the same
methodology as OSWorld, real environments, task-completion checks written
against final state rather than action traces, is the appropriate tool for
measuring generalization to previously unseen screens (Xie et al.,
arXiv:2404.07972, verified 2026-08-02).

## 16. Observability signals

Log every proposed action together with whether it executed, was blocked
by the allowlist, or required confirmation, a rising block or confirmation
rate on a task that used to run cleanly is an early signal of model or
environment drift before a full task failure is visible. Track step count
per task and per checkpoint separately, because step count is the loop's
own proxy for both cost and drift, and a task whose step count has crept
upward without a corresponding UI change usually means grounding accuracy
has degraded. Hash or diff the screenshot before and after every
state-changing action to catch the specific failure named in dimension 11
where the agent believes an action succeeded but the environment did not
actually change. Track the safety layer's own trigger rate directly,
classifier flags and confirmation-gate denials per thousand actions, as the
primary health metric for the security posture of the deployment, this is
the same category of number Anthropic published for Claude for Chrome, a
measured attack success rate before and after mitigation (Anthropic,
"Claude for Chrome", verified 2026-08-02). Measure per-action latency as a
distribution, not an average, split into screenshot capture time, model
round-trip time, and dispatcher execution time, so an environment slowdown
is distinguishable from a model regression. Maintain a histogram of
navigated hosts against the configured allowlist to catch an agent that has
started drifting toward domains it was never meant to reach, before that
drift becomes a security incident rather than a metric.

## 17. Security and privacy implications

Security is not a peripheral concern for this pattern, it is close to the
whole of what makes the pattern dangerous to deploy carelessly. Every piece
of content the agent reads off a screen is a potential instruction, not
merely data, because the model has no reliable way to distinguish the
user's original task from text rendered on a page it is now looking at,
Anthropic states this plainly, that Claude will follow commands found in
content even when they conflict with the user's instructions in some
circumstances (Anthropic, "Computer use tool", verified 2026-08-02), and
both vendors ask integrators to treat rendered content as untrusted input
by default. The measured baseline attack success rate against this
specific risk, 23.6 percent before mitigation on a shipped product, is not
a hypothetical number, it is the observed rate at which a real deployment
was successfully manipulated (Anthropic, "Claude for Chrome", verified
2026-08-02).

Credential exposure is the second concern. An agent given direct access to
a session already authenticated into sensitive systems inherits whatever
that session can do, and a successful injection then inherits it too. The
correct default is a dedicated, minimally privileged session or sandboxed
environment holding no credentials the current task does not strictly
need, exactly the isolation both vendors' own security guidance recommends
(Anthropic, "Computer use tool", verified 2026-08-02; OpenAI, "Computer
use", verified 2026-08-02).

Screenshot capture is itself a privacy-sensitive artifact in a way a typed
API log is not, a screen can render personal data, authentication tokens
visible in a password manager, or content the person on the other end of a
shared screen never expected to be logged, and a team storing screenshots
for audit purposes takes on the same redaction and retention discipline
that applies to any session-recording tool, not a lighter version of it.

Irreversible actions deserve a control enforced in the dispatcher, not a
control merely requested in a prompt. A model can be instructed not to
submit a payment without confirmation and can still, under the right
combination of ambiguity or injection, propose exactly that action, the
confirmation gate has to sit in code the model cannot talk its way past,
which is the entire point of the `Consequential` flag and the `Confirm`
callback in this entry's Go example.

Finally, the sandboxed environment itself is a supply-chain surface. A
container image or virtual machine template used across many task runs
should be pinned to a known-good version and refreshed deliberately, the
same discipline any team already applies to a build environment, because a
compromised base image would compromise every task the agent subsequently
runs inside it.

## 18. References

- Anthropic, "Developing a computer use model", 22 October 2024,
  https://www.anthropic.com/news/developing-computer-use, verified
  2026-08-02.
- Anthropic, "Computer use tool", platform documentation,
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool,
  verified 2026-08-02.
- Anthropic, "Claude for Chrome", 25 August 2025,
  https://claude.com/blog/claude-for-chrome, verified 2026-08-02.
- OpenAI, "Computer use", API documentation,
  https://developers.openai.com/api/docs/guides/tools-computer-use, verified
  2026-08-02.
- browser-use, GitHub repository,
  https://github.com/browser-use/browser-use, verified 2026-08-02.
- Xie, Zhang, Chen, Li, Zhao, Cao, Hua, Cheng, Shin, Lei, Liu, Xu, Zhou,
  Savarese, Xiong, Zhong, Yu, "OSWorld, Benchmarking Multimodal Agents for
  Open-Ended Tasks in Real Computer Environments", arXiv:2404.07972,
  submitted 11 April 2024, https://arxiv.org/abs/2404.07972, verified
  2026-08-02.

## Code examples

Three implementation-adjacent excerpts, chosen because each demonstrates a
distinct part of the control surface this pattern needs in production, the
action-dispatch loop itself, the coordinate rescaling that pixel grounding
requires, and the supervisory allowlist and confirmation gate that safety
guidance asks for. Java, Rust, and Swift are omitted here because none of
the three brings anything idiomatic to a pattern whose interesting
structure lives in the calling application's control flow rather than in
language-specific type or memory features, Python covers the
vendor-SDK-adjacent scripting style most reference implementations use,
TypeScript covers the browser-native and client-side control style used by
tools such as browser-use, and Go covers the infrastructure-grade
supervisory wrapper style a production deployment adds on top of either.

All three samples below were compiled or run directly, `python3
agent_loop.py`, `npx tsc --strict` followed by `node`, and `go vet` followed
by `go run`, and each produced the exact output shown in its own comment
free of manual editing after the run.

```python
"""Computer use agent loop, capture, propose, dispatch, repeat."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


class Screen(Protocol):
    width: int
    height: int

    def capture(self) -> bytes: ...
    def click(self, x: int, y: int) -> None: ...
    def type_text(self, text: str) -> None: ...


@dataclass
class Action:
    name: str
    args: dict = field(default_factory=dict)


class BoundsError(ValueError):
    """A proposed action targets coordinates off the canvas."""


class UnknownActionError(ValueError):
    """The model named an action the controller never registered."""


class ComputerUseLoop:
    """Runs perceive, propose, execute for a fixed number of turns."""

    def __init__(self, screen: Screen, propose: Callable[[bytes, list[Action]], Action | None]):
        self.screen = screen
        self.propose = propose
        self.handlers: dict[str, Callable[[dict], str]] = {
            "left_click": self._left_click,
            "type": self._type,
            "screenshot": lambda args: "ok",
        }
        self.transcript: list[Action] = []

    def _left_click(self, args: dict) -> str:
        x, y = args["coordinate"]
        if not (0 <= x < self.screen.width and 0 <= y < self.screen.height):
            raise BoundsError(
                f"({x}, {y}) is outside display bounds "
                f"({self.screen.width}x{self.screen.height})"
            )
        self.screen.click(x, y)
        return f"clicked ({x}, {y})"

    def _type(self, args: dict) -> str:
        self.screen.type_text(args["text"])
        return f"typed {args['text']!r}"

    def run(self, max_turns: int = 20) -> list[str]:
        results: list[str] = []
        for _ in range(max_turns):
            shot = self.screen.capture()
            action = self.propose(shot, self.transcript)
            if action is None:
                break
            handler = self.handlers.get(action.name)
            if handler is None:
                raise UnknownActionError(f"no handler registered for {action.name!r}")
            results.append(handler(action.args))
            self.transcript.append(action)
        return results


class FakeScreen:
    """In-memory stand-in for the sandboxed X11 display."""

    def __init__(self, width: int = 1024, height: int = 768):
        self.width = width
        self.height = height
        self.log: list[str] = []

    def capture(self) -> bytes:
        return b"\x00" * 4

    def click(self, x: int, y: int) -> None:
        self.log.append(f"click {x},{y}")

    def type_text(self, text: str) -> None:
        self.log.append(f"type {text}")


def scripted_model(script: list[Action]):
    it = iter(script)

    def propose(_shot: bytes, _transcript: list[Action]) -> Action | None:
        return next(it, None)

    return propose


def main() -> None:
    screen = FakeScreen()
    script = [
        Action("screenshot"),
        Action("left_click", {"coordinate": [500, 300]}),
        Action("type", {"text": "hello computer use"}),
    ]
    loop = ComputerUseLoop(screen, scripted_model(script))
    for line in loop.run():
        print(line)
    # ok
    # clicked (500, 300)
    # typed 'hello computer use'

    bad = ComputerUseLoop(screen, scripted_model([Action("left_click", {"coordinate": [9000, 9000]})]))
    try:
        bad.run()
    except BoundsError as exc:
        print(f"rejected: {exc}")
    # rejected: (9000, 9000) is outside display bounds (1024x768)


if __name__ == "__main__":
    main()
```

```typescript
// Discriminated action union plus coordinate rescaling between the
// resolution the model reasons over and the real display it controls.

type Click = { action: "click"; x: number; y: number; button?: "left" | "right" };
type DoubleClick = { action: "double_click"; x: number; y: number };
type Scroll = { action: "scroll"; x: number; y: number; deltaX: number; deltaY: number };
type TypeText = { action: "type"; text: string };
type KeyPress = { action: "keypress"; keys: string[] };
type Drag = { action: "drag"; path: Array<{ x: number; y: number }> };
type Wait = { action: "wait"; ms: number };
type Screenshot = { action: "screenshot" };

type ComputerAction =
  | Click
  | DoubleClick
  | Scroll
  | TypeText
  | KeyPress
  | Drag
  | Wait
  | Screenshot;

interface Viewport {
  width: number;
  height: number;
}

class OutOfBoundsError extends Error {}

// Maps a model-space point back onto the real screen resolution.
function rescale(point: { x: number; y: number }, modelSpace: Viewport, realSpace: Viewport) {
  const scaleX = realSpace.width / modelSpace.width;
  const scaleY = realSpace.height / modelSpace.height;
  const x = Math.round(point.x * scaleX);
  const y = Math.round(point.y * scaleY);
  if (x < 0 || x >= realSpace.width || y < 0 || y >= realSpace.height) {
    throw new OutOfBoundsError(`(${x}, ${y}) falls outside ${realSpace.width}x${realSpace.height}`);
  }
  return { x, y };
}

function describe(action: ComputerAction): string {
  switch (action.action) {
    case "click":
      return `click ${action.button ?? "left"} at (${action.x}, ${action.y})`;
    case "double_click":
      return `double_click at (${action.x}, ${action.y})`;
    case "scroll":
      return `scroll dx=${action.deltaX} dy=${action.deltaY} at (${action.x}, ${action.y})`;
    case "type":
      return `type "${action.text}"`;
    case "keypress":
      return `keypress ${action.keys.join("+")}`;
    case "drag":
      return `drag through ${action.path.length} points`;
    case "wait":
      return `wait ${action.ms}ms`;
    case "screenshot":
      return "screenshot";
  }
}

function main() {
  const modelSpace: Viewport = { width: 1366, height: 768 };
  const realSpace: Viewport = { width: 2732, height: 1536 };

  const proposed: ComputerAction[] = [
    { action: "screenshot" },
    { action: "click", x: 640, y: 40 },
    { action: "type", text: "computer use" },
    { action: "keypress", keys: ["ctrl", "enter"] },
  ];

  for (const action of proposed) {
    console.log(describe(action));
  }
  // screenshot
  // click left at (640, 40)
  // type "computer use"
  // keypress ctrl+enter

  const rescaled = rescale({ x: 640, y: 40 }, modelSpace, realSpace);
  console.log(`rescaled click target: (${rescaled.x}, ${rescaled.y})`);
  // rescaled click target: (1280, 80)

  try {
    rescale({ x: 5000, y: 5000 }, modelSpace, realSpace);
  } catch (err) {
    if (err instanceof OutOfBoundsError) {
      console.log(`rejected: ${err.message}`);
    }
    // rejected: (10000, 10000) falls outside 2732x1536
  }
}

main();
```

```go
// A supervisory controller around a computer use executor, a domain
// allowlist plus a human confirmation gate for consequential actions.
package main

import (
	"errors"
	"fmt"
	"net/url"
	"strings"
)

type Action struct {
	Name          string
	Args          map[string]string
	Consequential bool
}

var errBlockedDomain = errors.New("domain not on allowlist")
var errNeedsConfirmation = errors.New("consequential action requires confirmation")

type Controller struct {
	AllowedDomains map[string]bool
	Confirm        func(Action) bool
	Executed       []string
}

func NewController(allowed []string, confirm func(Action) bool) *Controller {
	set := make(map[string]bool, len(allowed))
	for _, d := range allowed {
		set[d] = true
	}
	return &Controller{AllowedDomains: set, Confirm: confirm}
}

func hostOf(raw string) (string, error) {
	u, err := url.Parse(raw)
	if err != nil {
		return "", err
	}
	return strings.ToLower(u.Hostname()), nil
}

func (c *Controller) Run(a Action) error {
	if a.Name == "navigate" {
		host, err := hostOf(a.Args["url"])
		if err != nil {
			return err
		}
		if !c.AllowedDomains[host] {
			return fmt.Errorf("%w: %s", errBlockedDomain, host)
		}
	}
	if a.Consequential {
		if c.Confirm == nil || !c.Confirm(a) {
			return fmt.Errorf("%w: %s", errNeedsConfirmation, a.Name)
		}
	}
	c.Executed = append(c.Executed, describe(a))
	return nil
}

func describe(a Action) string {
	if a.Name == "navigate" {
		return "navigate to " + a.Args["url"]
	}
	return a.Name
}

func main() {
	controller := NewController(
		[]string{"docs.internal.example"},
		func(a Action) bool { return a.Name == "submit_payment" },
	)

	actions := []Action{
		{Name: "navigate", Args: map[string]string{"url": "https://docs.internal.example/page"}},
		{Name: "navigate", Args: map[string]string{"url": "https://evil.example/steal"}},
		{Name: "submit_payment", Consequential: true},
		{Name: "delete_account", Consequential: true},
	}

	for _, a := range actions {
		err := controller.Run(a)
		if err != nil {
			fmt.Println("rejected:", err)
			continue
		}
		fmt.Println("executed:", describe(a))
	}

	fmt.Println("log:", controller.Executed)
	// executed: navigate to https://docs.internal.example/page
	// rejected: domain not on allowlist: evil.example
	// executed: submit_payment
	// rejected: consequential action requires confirmation: delete_account
	// log: [navigate to https://docs.internal.example/page submit_payment]
}
```
