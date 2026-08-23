---
name: Wizard
slug: wizard
family: 26-interaction-hci
category: Interaction and HCI
aliases: [Setup Assistant, Multi-Step Form, Step-by-Step Wizard]
first_described: "Microsoft, Windows User Experience guideline, ms997609(v=msdn.10), 1999"
maturity: established
related: [undo]
incompatible_with: []
verified: 2026-08-23
---

# Wizard

## 1. Name, aliases, and lineage

A wizard, also called a setup assistant or a multi-step form, breaks a
single complex task into a sequence of discrete, ordered pages presented
one at a time, each carrying its own focused subset of the overall input,
so a person is guided through a process too large or too error-prone to
present as one flat form.

Microsoft's own current Windows UX guidance gives the plainest functional
definition, wizards are used to perform multi-step tasks, and multiple
steps of a wizard are presented as a sequence of pages. The direct
ancestor of that guidance is Microsoft's own 1999 Windows User Experience
document, archived on Microsoft Learn, which defines the pattern more
formally, a wizard is a special form of user assistance that automates a
task through a dialogue with the user, and states its intended scope
plainly, they are especially useful for presenting complex and infrequent
tasks that the user may have difficulty learning or doing. That same 1999
document already codifies a simple-versus-advanced taxonomy, a simple
wizard runs three pages or fewer with no Welcome or Completion page, an
advanced wizard has multiple decision points and includes both, and it
prescribes the exact button conventions, Back, Next, Finish, and Cancel,
still recognizable in wizards today.

Wikipedia's own account of the pattern's history independently
corroborates and dates Microsoft's role, when developing the first
version of Microsoft Publisher around 1991, Microsoft wanted to help
users create well-presented documents in spite of their lack of graphic
design skills, and traces wizards forward from there, Excel 4.0 for Mac
introduced wizards for crosstab tables in 1992, Microsoft Access shipped
with wizards in November 1992, and by 2001 wizards were commonplace
across consumer operating systems. So the pattern's origin sits earlier
than the Windows 95-era installer software it is often associated with,
already mature enough by 1999 to warrant a formal internal taxonomy.

This entry could not verify whether Jenifer Tidwell's Designing
Interfaces names this pattern directly. Every attempted URL for the book
and its companion site returned a connection failure rather than content,
consistent with the same book being unreachable in this catalogue's other
family 26 entries, and this entry does not rely on it anywhere below.

## 2. Problem and context

A single flat form with many fields overwhelms a person and increases
both error rate and abandonment, a wizard trades that for a lower
per-screen cognitive load at the cost of extra navigation, more clicks,
more page loads, and less ability to see the whole picture or jump
directly to one field. Microsoft's own current guidance states the trade
plainly, wizards are a relatively heavy form of user interface, if there
is a suitable, lighter-weight solution available, use it.

Baymard Institute's own checkout research gives a real, dated numeric
grounding for the field-count half of this trade, the average checkout
flow for a new user is 5.1 steps long, and the average checkout contains
11.3 form fields, with 17 percent of users having abandoned due to
checkout complexity. Baymard's own analysis names which half of that
actually drives the pain, what is more important is what the user has to
do at each of those steps, the number of form fields in a checkout
impacts overall usability far more than the number of steps, a genuinely
useful correction to the assumption that fewer steps alone fixes a wizard.
This entry could not find a source giving a direct, controlled comparison
of completion or error rates between a wizard and an equivalent flat form,
and states that plainly rather than inventing a percentage.

## 3. Forces

Cognitive load per screen sits against total navigation overhead, the
central trade named in section 2. Microsoft's own guidance names a second
force directly, frequency of use against wizard length, pay attention to
how frequently the particular task might be performed, an infrequent task
may deploy a longer wizard, whereas frequent tasks should definitely
favor brevity, the same reasoning this family's own applicability section
draws on.

A third force is branching against orientation. Microsoft's guidance
gives a concrete numeric limit on how far branching can go before a
person loses their place, prefer non-branching wizard design over
branching, if you must branch, limit the number of branches to one or two
within a single wizard, never include more than one branch within a
branch, a nested branch, and separately names the failure mode directly,
if you have a wizard that includes multiple decision points and branches,
and frequently results in users losing track of their navigation path,
you have exceeded a practical limit.

A fourth force, named by Microsoft as a documented tendency rather than a
hypothetical, is text length against clarity, wizards have a tendency to
over-communicate, it is like a variation on Parkinson's Law, UI text will
expand to fill the space available, a real cost that offsets the
guidance benefit a wizard is meant to provide in the first place.

## 4. Applicability and non-applicability

The U.S. Web Design System's own Step Indicator component documentation
gives the clearest, most explicit applicability test found for this
entry. Reach for a wizard when a person is working through a form or
process that will span several different pages, suited to linear
progression, complementing standard back and next navigation. Avoid it
for long forms with conditional logic, for nonlinear progression, or for
very short forms with fewer than three sections.

Microsoft's own guidance gives the procedural version of the same test,
a wizard earns its complexity when the task is a single, atomic task that
cannot be reduced to fewer pages through sensible defaults, and where the
questions genuinely must be answered in sequence, not merely several
probable but optional questions, which its own guidance redirects to a
tabbed dialog instead, citing a print-options dialog as the correct
counter-example.

The UK Government's own Service Manual gives the frequency-of-use
non-applicability case directly, for a task a person repeats often, user
research will tell you when you can merge pages together, for example if
you are designing an internal service for government users who need to
repeat and switch between tasks quickly, precisely the case this family's
own forces section names as where a wizard's extra navigation becomes
friction rather than guidance rather than help.

## 5. Structure

Microsoft's own current guidance names the actual page taxonomy almost
exactly, wizards typically include choice pages, used to gather
information and allow users to make choices, a commit page, used to
perform an action that cannot be undone by clicking Back or Cancel, and a
progress page, used to show the progress of a lengthy operation. Every
page shares a title bar with a Back button, a main instruction, a content
area, and a command area carrying at least one commit button.

Stripe's own Connect onboarding documentation gives a real, currently
documented, production example of this structure in full. The hosted
onboarding form is dynamically generated per connected account based on
its country and business type, and applies live data validation
including real-time verification where possible. It supports a persisted
draft across steps, an account-holder can save for later at any point
and Stripe routes back to that exact state on return, and it supports
review and edit of previously provided information through a dedicated
account-update link that shows the already-filled attributes.

The UK Government's own Service Manual gives a second, independently
sourced production structure, one thing per page, split a form across
multiple pages with each page containing just one piece of information
the person is told, one decision they have to make, or one question they
have to answer, and this shape lets a user's answers be saved
automatically as they go and captures analytics about each individual
question.

## 6. ASCII structure diagram

```
   +--------+     +--------+     +--------+     +--------+     +--------+
   |        | --> |        | --> |        | --> | REVIEW | --> | SUBMIT |
   | STEP 1 |     | STEP 2 |     | STEP 3 |     |        |     |        |
   |        | <-- |        | <-- |        | <-- |        |     |        |
   +--------+     +--------+     +--------+     +--------+     +--------+
       |               |               |             |
       |               |               |             |
       +---------------+---------------+-------------+
                               |
                               v
                     +-------------------+
                     |  persisted draft  |
                     |  (server / URL /  |
                     |  local storage)   |
                     +-------------------+
```

## 7. Dynamics

Whether a person can advance before the current step is valid splits into
two documented models. MUI's own Stepper documentation names them
directly, linear steppers require sequential completion, blocking
advancement until the current step is valid, while non-linear steppers
allow the user to enter a multi-step flow at any point, deferring
validation, and its own documentation states plainly that managing when
an optional step is skipped is left to the implementer.

Microsoft's own guidance gives an explicit rule for what happens when a
person goes back and changes an earlier answer, a person gives input,
clicks the commit button, clicks Back to review previous changes, changes
something, and clicks the commit button again, normally this should be
possible, and the second commit should redo the task with the changed
input, replacing or undoing the effect of the first, effectively a
specification for deferred re-validation on return.

Progress is persisted through one of three real, sourced mechanisms. A
server-side draft record tied to a resumable link, Stripe's own
account-update and save-for-later flow. URL or hash state, the
react-step-wizard library's own documented option to persist the current
step in the URL hash. Or an implicit server-side save-as-you-go model,
the UK Government's own one-thing-per-page pattern, which saves a
person's answers automatically as they go.

Skipping a step pushes real bookkeeping onto the underlying data model.
MUI's own documentation states this directly, it is up to you to manage
when an optional step is skipped, meaning each step's fields must be
represented as independently optional rather than assuming one required
linear fill order. Microsoft's own guidance gives the corollary for how a
skipped step should still be counted, treat optional steps as persistent
in the enumeration sequence, if a choice on page 2 makes pages 3 and 4
optional, show steps 1, 2, 5, and 6 of 6, do not renumber steps 5 and 6.

## 8. Implementation variants

Linear, fixed-order wizards are Microsoft's own stated preference, prefer
non-branching wizard design over branching, with a concrete numeric
ceiling on how far branching may go when it is genuinely needed, at most
one or two branches within a single wizard and never a branch nested
inside another branch, plus a technique for keeping a person oriented
inside a branch, enumerating sub-steps such as step 2a of 6.

Client-side, single-page-app step transitions have real, named, verified
tooling. The react-step-wizard library states its own purpose plainly, a
flexible multistep wizard built for React, exposing nextStep, previousStep,
goToStep, and an isLazyMount option that only mounts a step's component
when it is active, so every step is not rendered simultaneously. MUI's
Stepper is a second, independently confirmed library, providing horizontal
orientation, ideal when the contents of one step depend on an earlier
step, and vertical orientation, designed for narrow screens, alongside the
linear and non-linear modes already covered in section 7.

Server-rendered, one-page-per-step flows have their own real, sourced,
production-scale example, the U.S. Web Design System's own Step Indicator
component, audited and passing WCAG 2.1 AA, with explicit accessibility
attributes, aria-current set to true on the current step and aria-hidden
on unlabeled containers.

This entry attempted, and could not confirm, React Hook Form's own
official multi-step guidance, every attempted URL for it returned an
access error rather than content, so this entry does not attribute any
specific React Hook Form API to a live-verified source. It similarly
could not extract Angular Material's own Stepper API documentation, the
fetched page returned only a bare title with no body content, so no
specific Angular API name is asserted here as confirmed, only that MUI's
independently and successfully fetched documentation confirms the same
linear and non-linear concept is a named pattern in a major component
library.

## 9. Known production uses

Stripe Connect's hosted account onboarding is a real, named, currently
documented production wizard, and Stripe states its own engineering
rationale for the shape directly, the form is generated dynamically per
country and business type specifically because verification requirements
vary by jurisdiction, and Stripe recommends the hosted or embedded option
over a hand-rolled flow when a platform wants Stripe to own onboarding
and reduce the platform's own effort, a genuine, sourced why, not just an
assertion that Stripe uses a wizard.

The UK Government's entire digital service catalogue is a second, real,
government-wide production standard rather than a single product,
enforced through the GOV.UK Design System's one-thing-per-page pattern,
with an explicit, sourced rationale in the government's own words, it
helps users understand what they are being asked to do, lets a person's
answers be saved automatically as they go, and lets each individual
question be measured with analytics.

Microsoft's own guidance illustrates the pattern with real, named,
shipped Windows features, the Add Printer wizard and the Connect to a
Network wizard, and separately uses SQL Server 2008 Setup as a worked
example, contrasting a correctly-scoped page serving a technical audience
against an incorrectly-scoped, over-bundled three-tab page from the same
product family.

## 10. Consequences

Positive. A wizard lowers per-screen cognitive load by presenting one
piece of information, one decision, or one question per page, per the UK
Government's own stated rationale, and that same shape enables automatic
incremental saving and per-question analytics that a flat form does not
offer as naturally. Microsoft's own guidance states the broader intent
directly, wizards are one of the keys to simplifying the user experience,
letting each focused point carry its own explanation and controls.

Negative. The navigation overhead Microsoft calls a relatively heavy form
of user interface is real, more clicks, more page loads, and a person
cannot see the whole picture or jump directly to one field. Branching
wizards carry a further, named cost, Microsoft's own guidance calls them
inherently dislocating for users, since a person can lose track of how
many steps remain or where they currently sit. And per Baymard's own
finding, a wizard that reduces step count without reducing field count
per step has not actually fixed the usability problem it was reached for
in the first place.

## 11. Failure modes and misuse

Microsoft's own design-concepts guidance names four specific, documented
failure modes, unusually candid for a vendor UX guide. The burrito
wizard, bundling multiple sub-tasks onto one page, illustrated with a
labeled example of a three-tab SQL Server setup page crammed into one
wizard step, defeats the purpose of breaking the task apart in the first
place. Using a wizard as a bandage for a badly designed feature, a
badly designed feature does not warrant a wizard to explain and simplify
it, it warrants redesigning the feature itself. Mistaking rapid
Next-Next-Next-Finish clicking for evidence the wizard is well designed,
when it may instead mean the wizard was unnecessary because every choice
was left at its default. And excessive branching causing a person to
lose their place, if a wizard's decision points frequently result in
people losing track of their navigation path, a practical limit has been
exceeded.

This entry could not find a source directly naming a wizard that cannot
be exited without losing progress, or that cannot go back without losing
entered data, as a documented failure mode in so many words. The closest
available evidence is Microsoft's own positive-form guidance in section
7 that clicking Back should preserve previously entered values, implying
the anti-pattern by omission rather than describing it directly, and this
entry states that distinction honestly rather than inventing a citation
for it.

## 12. Trade-off matrix

| Approach | Per-screen cognitive load | Navigation overhead | Completion rate |
|---|---|---|---|
| Wizard, multi-step | Low, one focused sub-task per page, per the UK Government's own one-thing-per-page rationale | Higher, Microsoft's own guidance calls it a relatively heavy form of user interface, more clicks and page loads, harder to see the whole picture or jump to one field | No independently sourced controlled comparison was found, stated as an honest gap rather than an invented figure |
| Single flat form | High, all fields visible and competing for attention at once, implied by Baymard's own finding that field count, not step count, drives complexity | Lowest, everything reachable and editable on one page with no forward or back navigation needed | Same honest gap as above |
| Progressive disclosure, inline show or hide | Low for the default path, but a person must actively discover and expand any hidden advanced option | Low, content stays on one page, only the reveal interaction adds cost, and only for the person who opens it | Not directly comparable, this is an on-request reveal mechanism rather than a sequential completion flow, so completion rate is not the operative metric |

## 13. Related and incompatible patterns

Progressive disclosure is a genuinely related but structurally distinct
concept, and the Interaction Design Foundation draws the line precisely.
Progressive disclosure makes advanced features available upon request on
the same screen, while a separate, sibling technique it names staged
disclosure moves a person through the process in a straightforward,
step-by-step manner with all information revealed sequentially, citing
an e-commerce
checkout, shipping, payment, confirmation, as its own example of staged
disclosure. A wizard is closer to what this source calls staged
disclosure than to progressive disclosure itself, an adjacent concept
rather than something a wizard composes with, and this entry states that
distinction plainly rather than forcing a stronger relationship than the
source itself draws.

This entry attempted, and could not confirm, a genuine sourced connection
to inline validation, another pattern queued in this same family, and per
this catalogue's own guidance against forcing a connection that is not
real, none is asserted here.

## 14. Refactoring path in and out

Introducing a wizard into a flat form that has outgrown itself starts
with the one-thing-per-page split the UK Government's own guidance
describes, group the existing fields into the smallest set of coherent
sub-tasks, one piece of information, one decision, or one question per
page, then add a step indicator and the standard Back, Next, Finish, and
Cancel controls Microsoft's own 1999 guidance already codified. A
persisted draft, server-side where the data is sensitive per section 17,
is added at the same time so a person can leave and resume rather than
losing entered work.

Removing a wizard, when a task genuinely does not need one, most often
because it has become a task a person repeats often rather than an
infrequent one, per the applicability reasoning in section 4, means
collapsing its steps back into a single page or a tabbed dialog, the
correct alternative Microsoft's own guidance names directly for a set of
several probable but optional questions rather than a genuinely sequential
dependency.

## 15. Testing and verification

The Page Object Model, documented directly in Playwright's own official
guide, is the sourced testing shape this entry can point to, page objects
create a higher-level API suited to the application and capture element
selectors in one place to avoid repetition, and a worked example shows a
navigation method chained across pages, carrying state implicitly through
one shared page object instance across steps, a natural fit for a
multi-step flow.

This entry states honestly that Playwright's own fetched guidance did not
extend to wizard-specific assertions, such as confirming a draft persists
across a reload or that back-and-forward navigation preserves previously
entered values, and the same source explicitly states a countervailing
principle, each test should be completely isolated from another test and
run independently with its own storage, cookies, and data, in real
tension with the shared, carried-forward state a multi-step wizard test
actually needs to assert. This entry reports that tension rather than
smoothing it into a claim the source itself does not fully support.

## 16. Observability signals

PostHog's own funnel-analysis documentation is a real, named, currently
documented analytics product built specifically for this signal, for
every flow in a product, more people will start it than complete it
successfully, and funnels visualize the flow to reveal where the
friction points are. It distinguishes two per-step metrics directly
useful for a wizard, overall conversion, each step's conversion relative
to the first step, useful for understanding the entire funnel, and
relative conversion, each step's conversion relative to the previous
step, which shows which individual step carries the biggest opportunity
for improvement. This entry did not additionally source time-to-complete
per step as a separately itemized signal beyond PostHog's own general
mention that funnels reveal the steps with the highest friction and time
to convert.

## 17. Security and privacy implications

A wizard that persists a draft of partially entered, sensitive data
across steps carries a real, documented risk, and this entry grounds the
answer in two independent, live sources rather than a general assumption.

Stripe's own security documentation states directly that raw card
numbers are never held the way an ordinary form field would be, all card
numbers are encrypted at rest with AES-256, the decryption keys are held
on separate machines, and card numbers are tokenized internally and
isolated from the rest of Stripe's infrastructure, with none of Stripe's
own internal servers or daemons able to retrieve a card number in
plaintext, run inside infrastructure Stripe states is audited to the
strictest certification level possible in online payments. The
implication for a wizard's own implementation is direct, a payment step
should hand raw card data to a specialised, isolated, compliant subsystem
immediately rather than round-tripping it through the wizard's own
draft-persistence layer the way an address or a name field is handled.

For the sensitive-but-not-card-number fields that do need to survive
across steps, OWASP's own HTML5 Security Cheat Sheet gives the general
browser-storage guidance a wizard's client-side draft mechanism should
follow, avoid storing sensitive information in local storage, since a
single cross-site scripting vulnerability can be used to steal all the
data held there, and do not store secrets in IndexedDB unless they are
encrypted. Read together, the pattern that emerges is, never persist raw
card or credential data in a wizard's own draft state at all, and prefer
server-side draft storage, as Stripe's own account-update and
save-for-later mechanism does, over client-side storage for any other
field that is sensitive but must still survive a person leaving and
resuming.

## 18. References

1. Microsoft. "Wizards." Windows UX Guide.
   https://learn.microsoft.com/en-us/windows/win32/uxguide/win-wizards.
   Verified 2026-08-23.
2. Microsoft. "Windows User Experience, Wizards." Previous versions
   documentation. https://learn.microsoft.com/en-us/previous-versions/ms997609(v=msdn.10).
   Verified 2026-08-23.
3. Wikipedia contributors. "Wizard (software)." Wikipedia, The Free
   Encyclopedia. https://en.wikipedia.org/wiki/Wizard_(software). Verified
   2026-08-23.
4. Baymard Institute. "How Many Form Fields Should Your Checkout Have?"
   https://baymard.com/blog/checkout-flow-average-form-fields. Verified
   2026-08-23.
5. U.S. Web Design System. "Step Indicator."
   https://designsystem.digital.gov/components/step-indicator/. Verified
   2026-08-23.
6. UK Government. "Form structure." GOV.UK Service Manual.
   https://www.gov.uk/service-manual/design/form-structure. Verified
   2026-08-23.
7. Stripe. "Connect Onboarding." https://docs.stripe.com/connect/onboarding.
   Verified 2026-08-23.
8. Stripe. "Hosted onboarding." https://docs.stripe.com/connect/hosted-onboarding.
   Verified 2026-08-23.
9. Stripe. "Security at Stripe." https://docs.stripe.com/security.
   Verified 2026-08-23.
10. MUI. "React Stepper component." https://mui.com/material-ui/react-stepper/.
    Verified 2026-08-23.
11. jcmcneal. "react-step-wizard." GitHub repository, README.
    https://raw.githubusercontent.com/jcmcneal/react-step-wizard/master/README.md.
    Verified 2026-08-23.
12. Interaction Design Foundation. "Progressive Disclosure."
    https://ixdf.org/literature/topics/progressive-disclosure. Verified
    2026-08-23.
13. Playwright. "Page object models." https://playwright.dev/docs/pom.
    Verified 2026-08-23.
14. PostHog. "Funnels." https://posthog.com/docs/product-analytics/funnels.
    Verified 2026-08-23.
15. OWASP. "HTML5 Security Cheat Sheet."
    https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html.
    Verified 2026-08-23.

**Evidence grade.** high

**Most solid findings.** Microsoft's own 1999 and current Windows UX
guidance gives directly quoted, verbatim structural rules, button
conventions, and four named failure modes. Stripe's own onboarding and
security documentation gives a concrete, currently live production
example plus a directly sourced payment-data handling rationale. The UK
Government's own Service Manual gives a real, government-scale production
standard with its own stated rationale in writing.

**Unverified or unclear.** Jenifer Tidwell's Designing Interfaces could
not be reached across every attempted URL and is not relied on anywhere
in this entry. Nielsen Norman Group returned an access error on every
attempt. React Hook Form's own official multi-step guidance could not be
reached, so no specific API from that library is asserted as confirmed.
Angular Material's Stepper documentation returned only a page title with
no body content, so no specific Angular API name is asserted as
confirmed, only that MUI's independently fetched documentation confirms
the same concept exists as a named pattern in a comparable library. A
direct, controlled numeric comparison of wizard versus flat-form
completion or error rates could not be found.

## Code

TypeScript, a linear wizard manager with a persisted draft and step-skip
support, following the enumeration-preserving skip rule in section 7:

```typescript
interface StepDefinition {
  id: string;
  optional: boolean;
}

interface WizardDraft {
  currentIndex: number;
  values: Record<string, unknown>;
}

class WizardManager {
  private steps: StepDefinition[];
  private draft: WizardDraft;

  constructor(steps: StepDefinition[]) {
    this.steps = steps;
    this.draft = { currentIndex: 0, values: {} };
  }

  saveStep(stepId: string, value: unknown): void {
    this.draft.values[stepId] = value;
  }

  currentStep(): StepDefinition {
    return this.steps[this.draft.currentIndex];
  }

  next(): boolean {
    if (this.draft.currentIndex >= this.steps.length - 1) return false;
    this.draft.currentIndex += 1;
    while (
      this.draft.currentIndex < this.steps.length - 1 &&
      this.stepShouldBeSkipped(this.steps[this.draft.currentIndex])
    ) {
      this.draft.currentIndex += 1;
    }
    return true;
  }

  back(): boolean {
    if (this.draft.currentIndex <= 0) return false;
    this.draft.currentIndex -= 1;
    return true;
  }

  private stepShouldBeSkipped(step: StepDefinition): boolean {
    return step.optional && this.draft.values[step.id] === undefined;
  }

  stepLabel(): string {
    return "Step " + (this.draft.currentIndex + 1) + " of " + this.steps.length;
  }

  exportDraft(): WizardDraft {
    return { currentIndex: this.draft.currentIndex, values: { ...this.draft.values } };
  }
}

const wizard = new WizardManager([
  { id: "account-type", optional: false },
  { id: "business-details", optional: true },
  { id: "review", optional: false },
]);
wizard.saveStep("account-type", "individual");
wizard.next();
console.log(wizard.stepLabel(), wizard.currentStep());
```

Python, the same manager with server-side draft persistence, following
Stripe's own account-update and save-for-later shape described in
section 5:

```python
from dataclasses import dataclass, field


@dataclass
class StepDefinition:
    step_id: str
    optional: bool = False


@dataclass
class WizardDraft:
    current_index: int = 0
    values: dict = field(default_factory=dict)


class WizardManager:
    def __init__(self, steps: list) -> None:
        self.steps = steps
        self.draft = WizardDraft()

    def save_step(self, step_id: str, value) -> None:
        self.draft.values[step_id] = value

    def current_step(self) -> StepDefinition:
        return self.steps[self.draft.current_index]

    def _should_skip(self, step: StepDefinition) -> bool:
        return step.optional and step.step_id not in self.draft.values

    def next(self) -> bool:
        if self.draft.current_index >= len(self.steps) - 1:
            return False
        self.draft.current_index += 1
        while (
            self.draft.current_index < len(self.steps) - 1
            and self._should_skip(self.steps[self.draft.current_index])
        ):
            self.draft.current_index += 1
        return True

    def back(self) -> bool:
        if self.draft.current_index <= 0:
            return False
        self.draft.current_index -= 1
        return True

    def step_label(self) -> str:
        return "Step " + str(self.draft.current_index + 1) + " of " + str(len(self.steps))

    def persist(self) -> dict:
        return {"current_index": self.draft.current_index, "values": dict(self.draft.values)}

    def resume(self, saved: dict) -> None:
        self.draft.current_index = saved["current_index"]
        self.draft.values = dict(saved["values"])


if __name__ == "__main__":
    wizard = WizardManager([
        StepDefinition("account-type"),
        StepDefinition("business-details", optional=True),
        StepDefinition("review"),
    ])
    wizard.save_step("account-type", "individual")
    wizard.next()
    print(wizard.step_label(), wizard.current_step())
```

Go, the same manager with an explicit branching hook, following
Microsoft's own one-or-two-branch ceiling described in section 8:

```go
package main

import "fmt"

type StepDefinition struct {
	ID       string
	Optional bool
}

type WizardDraft struct {
	CurrentIndex int
	Values       map[string]string
}

type WizardManager struct {
	Steps []StepDefinition
	Draft WizardDraft
}

func NewWizardManager(steps []StepDefinition) *WizardManager {
	return &WizardManager{
		Steps: steps,
		Draft: WizardDraft{CurrentIndex: 0, Values: make(map[string]string)},
	}
}

func (m *WizardManager) SaveStep(stepID, value string) {
	m.Draft.Values[stepID] = value
}

func (m *WizardManager) CurrentStep() StepDefinition {
	return m.Steps[m.Draft.CurrentIndex]
}

func (m *WizardManager) shouldSkip(step StepDefinition) bool {
	if !step.Optional {
		return false
	}
	_, ok := m.Draft.Values[step.ID]
	return !ok
}

func (m *WizardManager) Next() bool {
	if m.Draft.CurrentIndex >= len(m.Steps)-1 {
		return false
	}
	m.Draft.CurrentIndex++
	for m.Draft.CurrentIndex < len(m.Steps)-1 && m.shouldSkip(m.Steps[m.Draft.CurrentIndex]) {
		m.Draft.CurrentIndex++
	}
	return true
}

func (m *WizardManager) Back() bool {
	if m.Draft.CurrentIndex <= 0 {
		return false
	}
	m.Draft.CurrentIndex--
	return true
}

func (m *WizardManager) StepLabel() string {
	return fmt.Sprintf("Step %d of %d", m.Draft.CurrentIndex+1, len(m.Steps))
}

func main() {
	wizard := NewWizardManager([]StepDefinition{
		{ID: "account-type"},
		{ID: "business-details", Optional: true},
		{ID: "review"},
	})
	wizard.SaveStep("account-type", "individual")
	wizard.Next()
	fmt.Println(wizard.StepLabel(), wizard.CurrentStep())
}
```
