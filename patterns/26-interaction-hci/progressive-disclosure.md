---
name: Progressive Disclosure
slug: progressive-disclosure
family: 26-interaction-hci
category: Interaction and HCI
aliases: [Show More, Advanced Options, Disclosure Widget]
first_described: "Kristina Hooper Woolsey, 1985, per Norman, Donald A., and Draper, Stephen W., editors, User Centered System Design: New Perspectives on Human-Computer Interaction, L. Erlbaum Associates, 1986, ISBN 0-89859-781-1"
maturity: canonical
related: [wizard]
incompatible_with: []
verified: 2026-08-23
---

# Progressive Disclosure

## 1. Name, aliases, and lineage

Progressive disclosure defers advanced, secondary, or rarely used options to a
place the reader must deliberately reveal, while the primary view shows only
what most people need most of the time. It is also called show more, advanced
options, or a disclosure widget, depending on the surface it appears on.

The earliest dated written source found for the term is Kristina Hooper
Woolsey, a founding member of Apple's Human Interface Group, quoted as writing
in 1985 that "in the design of interfaces one must also consider carefully how
one selectively informs a user about a particular system." That quote is cited
in the English Wikipedia article on the pattern to Norman, Donald A., and
Draper, Stephen W., editors, User Centered System Design: New Perspectives on
Human-Computer Interaction, L. Erlbaum Associates, 1986, ISBN 0-89859-781-1
(Wikipedia contributors, "Progressive disclosure," Wikipedia, The Free
Encyclopedia, https://en.wikipedia.org/wiki/Progressive_disclosure, verified
2026-08-23). The primary book text itself was not independently located for
this entry, so the 1985 attribution rests on that single tertiary citation
rather than a directly read primary source.

The pattern was popularized in its modern web and application form by Jakob
Nielsen, whose article "Progressive Disclosure" was published December 3,
2006, and remains the field's most cited single reference (Nielsen, Jakob,
"Progressive Disclosure," Nielsen Norman Group, December 3, 2006,
https://www.nngroup.com/articles/progressive-disclosure/, verified
2026-08-23). Nielsen's article is a continuation of an earlier Alertbox column
at the same publication's prior domain, confirmed by a live redirect chain
from https://www.useit.com/alertbox/progressive-disclosure.html through
https://www.nngroup.com/alertbox/progressive-disclosure.html to the current
URL, indicating one continuously maintained piece rather than two separate
texts.

## 2. Problem and context

An interface that serves both a person doing something for the first time and
a person who does it daily faces a direct conflict. The newcomer needs a small,
learnable surface with few choices. The frequent user wants every option
available without extra clicks once they know where things live. Showing every
option to everyone at once serves neither well: the newcomer is overwhelmed and
the frequent user still has to scan past options they rarely touch.

Nielsen names the underlying tension directly: users want both "power,
features, and enough options" and, at the same time, "simplicity" and freedom
from a lengthy learning curve (Nielsen, Jakob, "Progressive Disclosure,"
Nielsen Norman Group, December 3, 2006,
https://www.nngroup.com/articles/progressive-disclosure/, verified
2026-08-23). His stated resolution is a two-step split: show users only a few
of the most important options up front, then offer the larger set of
specialized options on request.

This problem shows up anywhere a form, a settings screen, or a piece of
content mixes a small common core with a longer tail of options that only some
readers will ever need, from a print dialog's page range and paper source to a
settings page's rarely touched security toggles.

## 3. Forces

Progressive disclosure balances several usability components against each
other, and the balance shifts depending on who is looking at the screen.

Learnability favors hiding rare options. Nielsen states that for novice users,
hiding the rarely used options "helps prioritize their attention" and prevents
mistakes made by encountering an unfamiliar control at the wrong moment
(Nielsen, Jakob, "Progressive Disclosure," Nielsen Norman Group, December 3,
2006, https://www.nngroup.com/articles/progressive-disclosure/, verified
2026-08-23).

Efficiency of use also favors hiding rare options, but for a different reason.
For advanced users, a streamlined initial display "saves them time because
they avoid having to scan past" features they rarely touch, per the same
source.

Error rate favors the same simplification, since fewer visible options at once
reduces the chance of selecting the wrong one.

Discoverability pulls the opposite direction. The Nielsen Norman Group's
companion article on accordions, a common disclosure mechanism, states the
cost plainly: "hiding content behind navigation diminishes people's awareness
of it" (Nielsen Norman Group, "Accordions on Desktop and Mobile,"
https://www.nngroup.com/articles/accordions-complex-content/, verified
2026-08-23). An option a person never learns exists because it sits behind an
extra click is an option that never gets used, even by someone who would
genuinely benefit from it.

The pattern favors learnability, efficiency, and error rate for the common
case, and it sacrifices immediate discoverability of the uncommon case. Whether
that trade is correct depends entirely on getting the split between common and
rare right, which is the applicability question in the next dimension.

## 4. Applicability and non-applicability

Progressive disclosure earns its place when an application or an
information-rich page genuinely has a small set of frequently needed options
and a larger set of rarely needed ones, and the split between the two is
correct. Nielsen's own recommendation is direct: disclose everything that
users frequently need up front, reserving the disclosure mechanism only for
what is genuinely secondary (Nielsen, Jakob, "Progressive Disclosure," Nielsen
Norman Group, December 3, 2006,
https://www.nngroup.com/articles/progressive-disclosure/, verified
2026-08-23).

It does not earn its place past two levels of nesting. Nielsen states that when
a design requires three or more disclosure levels, users often get lost when
moving between the levels, and his explicit recommendation at that point is
to simplify the design rather than add another layer of reveal.

The UK Government Digital Service states the negative case even more sharply
for its own details component: "Do not use the details component to hide
information that the majority of your users will need" (GOV.UK Design System,
"Details," https://design-system.service.gov.uk/components/details/, verified
2026-08-23). The positive case from the same source: "Use the details
component to make a page easier to scan when it contains information that only
some users will need."

UXPin lists three further conditions where the pattern should not be reached
for: when users need all information visible simultaneously for comparison,
when hiding critical safety information could cause harm, and when the extra
steps create more friction than the complexity they reduce (UXPin, "What is
Progressive Disclosure? Show and Hide the Right Information," March 13, 2023,
https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/, verified
2026-08-23).

## 5. Structure

The pattern has three parts. A primary view carries everything used often. A
trigger control sits beside or below the primary view, clearly labeled so its
purpose is obvious before it is activated. A secondary view carries the
remainder, revealed only when the trigger is activated.

The World Wide Web Consortium's ARIA Authoring Practices Guide gives the exact
structural and accessibility contract for the trigger and the region it
controls, under the name Disclosure: "A disclosure is a widget that enables
content to be either collapsed (hidden) or expanded (visible). It has two
elements: a disclosure button and a section of content" (World Wide Web
Consortium, "Disclosure Pattern," WAI-ARIA Authoring Practices Guide,
https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/, verified 2026-08-23).

The same source lays out the required roles and states. The element that
shows and hides the content has role button. When the content is visible, that
button carries aria-expanded set to true; when hidden, aria-expanded is set to
false. The button may also carry aria-controls, referring to the element that
holds the content it toggles.

A closely related but distinct structure, an accordion, stacks several such
disclosures in one column, each with its own heading (World Wide Web
Consortium, "Accordion Pattern," WAI-ARIA Authoring Practices Guide,
https://www.w3.org/WAI/ARIA/apg/patterns/accordion/, verified 2026-08-23).

Labeling the trigger is not cosmetic. GOV.UK's guidance is that the reveal's
link text be short and descriptive so users can quickly work out if they need
to click on it (GOV.UK Design System, "Details," verified 2026-08-23), and
GitHub's Primer design system pairs every icon-based reveal with descriptive
text for the same reason (GitHub, "Progressive Disclosure," Primer Design
System, https://primer.style/product/ui-patterns/progressive-disclosure/,
verified 2026-08-23).

## 6. ASCII structure diagram

```
DEFAULT / COLLAPSED STATE
+-------------------------------------------+
|  Account Settings                          |
|                                             |
|  Name    [ Jane Doe                 ]      |
|  Email   [ jane@example.com         ]      |
|                                             |
|  v  Advanced options                       |
+-------------------------------------------+
                     |
                     |  trigger activated
                     |  (aria-expanded false to true)
                     v
EXPANDED STATE
+-------------------------------------------+
|  Account Settings                          |
|                                             |
|  Name    [ Jane Doe                 ]      |
|  Email   [ jane@example.com         ]      |
|                                             |
|  ^  Advanced options                       |
|  +---------------------------------------+ |
|  | Two-factor auth      [ off        ]   | |
|  | API rate limit       [ 1000       ]   | |
|  | Session timeout      [ 30 min     ]   | |
|  +---------------------------------------+ |
+-------------------------------------------+
```

## 7. Dynamics

The reveal is always triggered by an explicit, person-initiated action, never
by the system guessing intent. The W3C's Authoring Practices Guide defines the
disclosure control's keyboard contract precisely: both Enter and Space
activate the disclosure control and toggle the visibility of the disclosure
content (World Wide Web Consortium, "Disclosure Pattern," verified
2026-08-23), so the mechanism must respond to keyboard activation the same way
it responds to a pointer click.

Once activated, the control's aria-expanded attribute flips and the previously
hidden region becomes part of the accessible view. If the region is populated
dynamically rather than merely shown and hidden, the same guide's Alert pattern
warns that screen readers do not inform users of alerts that are present on
the page before page load completes (World Wide Web Consortium, "Alert
Pattern," WAI-ARIA Authoring Practices Guide,
https://www.w3.org/WAI/ARIA/apg/patterns/alert/, verified 2026-08-23), which is
the reason the region must exist empty at load time and be filled only in
response to the trigger, rather than toggled between two pre-rendered states in
a way a screen reader cannot detect.

Whether an expanded state should persist across a return visit to the same
screen is a genuine open question this entry could not source. No design
system or usability source consulted stated a documented trade-off for
session-persisted versus always-reset disclosure state, and this is reported
here as an honest gap rather than resolved by assumption.

## 8. Implementation variants

The lightest-weight variant needs no script at all. The Mozilla Developer
Network documents the native HTML details and summary elements: the details
element creates a disclosure widget in which information is visible only when
the widget is toggled into an open state, and a summary or label must be
provided using the summary element (Mozilla Developer Network, "details: The
Details disclosure element,"
https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/details,
verified 2026-08-23). The element's default state is closed, its visibility is
controlled by the boolean open attribute, and it dispatches a native toggle
event whenever its state changes. GOV.UK's own details component is built
directly on these two elements (GOV.UK Design System, "Details," verified
2026-08-23).

A second variant reaches for a custom, script-driven accordion when more
visual control is needed than the native element offers, such as several
independently or exclusively expandable sections with custom animation. This
is the shape the W3C's Accordion pattern documents. GitHub's Primer design
system builds this variant in production and specifies a small vocabulary of
reveal icons rather than the browser's default triangle: a chevron for
collapsible content sections, a fold or unfold icon for expandable text used
on its own, and an ellipsis for a truncated inline string. Primer's guidance
explicitly discourages a text-only toggle in favor of an icon, because icons
provide better accessibility (GitHub, "Progressive Disclosure," verified
2026-08-23).

A third variant abandons in-place reveal entirely and moves the secondary
content to a fully separate view, most often a tab. GOV.UK draws this boundary
directly. Use the details component instead of tabs or an accordion when there
is only one section of content, since the details component is less visually
prominent than tabs and accordions, and tends to work better for content which
is not as important to users (GOV.UK Design System, "Details," verified
2026-08-23).

## 9. Known production uses

The macOS Print dialog is cited independently by two sources in agreement.
Wikipedia describes it directly: users see basic printing options initially,
with a Show Details button to access advanced settings (Wikipedia
contributors, "Progressive disclosure," verified 2026-08-23). Nielsen's own
article calls it the classic example, where an advanced options button
reveals specialized settings such as scaling and reverse printing.

GitHub's Primer design system documents its own production reasoning for the
pattern, distinguishing a welcoming tone for a feature not yet used, a
factual tone for content that is temporarily empty, and a concise, non-playful
tone for error conditions (GitHub, "Progressive Disclosure," verified
2026-08-23).

GOV.UK's design system states its details component has been used on a number
of services over an extended period, explicitly naming the passport renewal
service, and adds that the team is actively seeking further research on
client-side validation needs and screen reader compatibility with non-required
form fields (GOV.UK Design System, "Details," verified 2026-08-23).

Dropbox's file sharing dialog shows only an email field and a share button by
default, with a settings control revealing advanced permission and
link-visibility controls (UXPin, "What is Progressive Disclosure?," verified
2026-08-23). Google Search's Advanced Search page is cited by the same source
as the canonical example of complex filtering, language, region, and
date-range options reserved for the readers who seek them out.

## 10. Consequences

Positive. Learning burden and error rate fall for a new user, and scanning
time falls for an experienced one, per Nielsen's stated basis for the pattern.
A page becomes easier to scan when the hidden content is genuinely something
only some readers need, per GOV.UK's own guidance. The pattern also fits very
small spaces, including mobile screens, where showing everything at once is
not physically possible (Nielsen Norman Group, "Accordions on Desktop and
Mobile," verified 2026-08-23).

Negative. The Nielsen Norman Group's accordions article names the interaction
cost directly: forcing people to click on headings one at a time to display
full content can be cumbersome, especially if there are many topics. The same
article restates the discoverability cost from dimension 3, that hiding
content behind navigation reduces awareness of it. GOV.UK's own user research
found that some people avoid clicking a details link at all, since they think
it will take them away from the page, and separately notes that some users of
voice-assistive software cannot interact with the component if it is built
without care (GOV.UK Design System, "Details," verified 2026-08-23).

## 11. Failure modes and misuse

Hiding a feature nearly everyone needs behind an unnecessary reveal is the
most directly documented failure mode, sourced independently from two
authorities. GOV.UK states plainly not to hide information the majority of
users will need, and Nielsen's own requirement is that everything frequently
needed ship in the primary view, never behind the request gate. A reader who
must click to find something almost everyone wants experiences the click as
friction with no corresponding benefit.

A vague reveal control is the second failure mode. GOV.UK requires link text
short and descriptive enough that a reader can judge whether to click before
clicking, and the Nielsen Norman Group states the parallel requirement for
accordion headings, that they must be descriptive and enticing enough to
motivate people to spend clicks on them (Nielsen Norman Group, "Accordions on
Desktop and Mobile," verified 2026-08-23). A control labeled only more, or an
unlabeled chevron, fails this test.

Disorganized secondary content, a reveal that opens onto an uncategorized dump
of options with no internal grouping, is a plausible failure mode by extension
of the positive guidance above, since every structural source consulted
requires the split and the labeling to be deliberate. No source consulted
named this disorganization as a failure mode in those exact words, so it is
reported here as a reasonable inference rather than a directly sourced claim.

Stacking three or more disclosure levels is the fourth and most directly
sourced failure mode. Nielsen states that users often get lost when moving
between the levels past two, and his stated fix at that point is not a
fourth level of hierarchy but a simpler design.

## 12. Trade-off matrix

| Dimension | Progressive disclosure (reveal in place) | Flat, always visible | Fully separate basic/advanced views |
|---|---|---|---|
| Initial cognitive load | Low by design, Nielsen's stated goal of showing only the most important options first | High once the option count grows past a handful, the exact problem the pattern exists to solve | Low per view, but a navigation decision is added before content is even seen |
| Discoverability of hidden functionality | Reduced, per the Nielsen Norman Group's stated cost that hiding content behind navigation reduces awareness of it | Highest, nothing requires an action to be seen | Lower still, since a fully separate section requires a more deliberate choice than a local toggle |
| Implementation complexity | Low with the native details and summary elements, higher with a custom accordion needing full keyboard and aria-expanded management | Lowest, no widget state to manage at all | Moderate to high, requires the W3C Tabs pattern's roving focus and panel association, or fully separate routed views |

Each cell traces to the citations already given in dimensions 3, 8, and 11.

## 13. Related and incompatible patterns

Wizard is the pattern most often confused with progressive disclosure, and two
independent sources draw the same distinction in different words. The
Interaction Design Foundation states it directly. Progressive disclosure makes
advanced features or information available to the user on request, while
staged disclosure reveals all information one step at a time (Interaction
Design Foundation, "Progressive Disclosure,"
https://ixdf.org/literature/topics/progressive-disclosure, verified
2026-08-23). Nielsen's own article corroborates the same split independently.
Staged disclosure differs fundamentally, since it guides users through linear
task sequences rather than hierarchical option revelation, as exemplified by
wizards (Nielsen, Jakob, "Progressive Disclosure," verified 2026-08-23). A
wizard is the linear, sequential sibling that walks a person through required
steps in order; progressive disclosure is the hierarchical, optional reveal of
content that is not required at all.

No source consulted directly relates breadcrumbs or a command palette to
progressive disclosure, so no incompatible or composing relationship is
claimed for either here.

## 14. Refactoring path in and out

To introduce progressive disclosure into a screen that shows every option at
once, first separate the options into two lists by actual usage frequency,
never by guessing. Move the rarely used list behind a single, clearly labeled
reveal built on the native details and summary elements where the platform
supports them, and add the aria-expanded and role button contract by hand
where it does not. Confirm the primary view still contains everything most
readers need, per dimension 4, before shipping.

To remove progressive disclosure once a section has grown to the point that
most readers open it anyway, promote its contents back to the primary view and
delete the trigger. GOV.UK's own guidance to prefer tabs over a details
component once a screen has more than one section that most readers need is
the sourced signal that the disclosure has outgrown its usefulness (GOV.UK
Design System, "Details," verified 2026-08-23).

## 15. Testing and verification

The W3C's Disclosure pattern gives the exact contract to assert against: the
trigger carries role button, and its aria-expanded value toggles between false
and true as the region it controls is hidden and shown (World Wide Web
Consortium, "Disclosure Pattern," verified 2026-08-23). Testing Library's own
documentation confirms the concrete assertion mechanism used in practice, that
its role-based queries can be filtered by their expanded state by passing an
expanded option of true or false, with the documentation pointing at the same
aria-expanded specification as its authority (Testing Library, "byRole,"
https://testing-library.com/docs/queries/byrole/, verified 2026-08-23).

The composite assertions this supports are that the secondary content is
absent from the accessibility tree, or its trigger reports aria-expanded
false, in the default render; that a simulated activation of the trigger
flips aria-expanded to true and makes the secondary content queryable; and
that the same result is reachable by keyboard, tabbing to the trigger and
pressing Enter or Space, never only by a simulated pointer click.

## 16. Observability signals

No source consulted supplied empirical click-through data for reveal
controls. The Nielsen Norman Group's accordions article, asked directly,
confirms the absence rather than supplying a figure, since it contains no
empirical data quantifying how frequently users click to expand sections
(Nielsen Norman Group, "Accordions on Desktop and Mobile," verified
2026-08-23).

What the same source does supply is a qualitative signal a team can watch for
in its own instrumentation, since it names descriptive, enticing labeling as
the difference between a reveal that gets used and one that does not. The
underlying mechanism, a boolean aria-expanded toggle per dimension 15, is
exactly the kind of event a team would log to measure how often a given
reveal is actually activated per session, and whether a specific option
inside it is opened by nearly everyone, which would be a signal that option
belongs in the primary view instead. This instrumentation reasoning follows
from the cited mechanics rather than from a source that itself discusses
analytics.

## 17. Security and privacy implications

Two Common Weakness Enumeration entries and one applied security source
establish the relevant general principle, though none names progressive
disclosure by that term.

CWE-656, Reliance on Security Through Obscurity, states the mechanism
directly. The product uses a protection mechanism whose strength depends
heavily on its obscurity, such that knowledge of its algorithms or key data is
sufficient to defeat the mechanism (MITRE, "CWE-656," MITRE CWE List,
https://cwe.mitre.org/data/definitions/656.html, verified 2026-08-23), and its
own worked example is squarely on point, a hidden form field processed by a
modified client.

CWE-602, Client-Side Enforcement of Server-Side Security, states that when
the server relies on protection mechanisms placed on the client side, an
attacker can modify the client-side behavior to bypass the protection
mechanisms (MITRE, "CWE-602," MITRE CWE List,
https://cwe.mitre.org/data/definitions/602.html, verified 2026-08-23).
PortSwigger's Web Security Academy states the general principle these two
entries protect against, that a fundamentally flawed assumption is that users
will only interact with the application via the provided web interface, since
a request can be tampered with after the browser sends it, rendering the
client-side controls useless (PortSwigger, "Business logic vulnerabilities:
Examples," https://portswigger.net/web-security/logic-flaws/examples, verified
2026-08-23).

Applied to this pattern, a progressive disclosure implementation that hides a
sensitive control, a permission toggle or a pricing override, behind a merely
visually collapsed region while leaving the same request processed
identically on the server gives a false sense of protection, since the
control is still present in the markup and inspectable regardless of whether
it is shown. The hiding of a control is a usability choice, never an access
control decision, and the server must independently verify the requester is
authorized to change what the control represents. This specific application to
progressive disclosure is this entry's own reasoning built on the three cited
sources, not a claim any of them state directly.

## 18. References

1. Wikipedia contributors, "Progressive disclosure," Wikipedia, The Free
   Encyclopedia, https://en.wikipedia.org/wiki/Progressive_disclosure,
   verified 2026-08-23.
2. Norman, Donald A., and Draper, Stephen W., editors, User Centered System
   Design: New Perspectives on Human-Computer Interaction, L. Erlbaum
   Associates, 1986, ISBN 0-89859-781-1. Cited via Wikipedia contributors,
   "Progressive disclosure," verified 2026-08-23; the primary text was not
   independently read for this entry.
3. Nielsen, Jakob, "Progressive Disclosure," Nielsen Norman Group, December 3,
   2006, https://www.nngroup.com/articles/progressive-disclosure/, verified
   2026-08-23.
4. Nielsen Norman Group, "Accordions on Desktop and Mobile,"
   https://www.nngroup.com/articles/accordions-complex-content/, verified
   2026-08-23.
5. GOV.UK Design System, "Details,"
   https://design-system.service.gov.uk/components/details/, verified
   2026-08-23.
6. UXPin, "What is Progressive Disclosure? Show and Hide the Right
   Information," March 13, 2023,
   https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/, verified
   2026-08-23.
7. World Wide Web Consortium, "Disclosure Pattern," WAI-ARIA Authoring
   Practices Guide, https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/,
   verified 2026-08-23.
8. World Wide Web Consortium, "Accordion Pattern," WAI-ARIA Authoring
   Practices Guide, https://www.w3.org/WAI/ARIA/apg/patterns/accordion/,
   verified 2026-08-23.
9. World Wide Web Consortium, "Alert Pattern," WAI-ARIA Authoring Practices
   Guide, https://www.w3.org/WAI/ARIA/apg/patterns/alert/, verified
   2026-08-23.
10. GitHub, "Progressive Disclosure," Primer Design System,
    https://primer.style/product/ui-patterns/progressive-disclosure/,
    verified 2026-08-23.
11. Mozilla Developer Network, "details: The Details disclosure element,"
    https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/details,
    verified 2026-08-23.
12. Testing Library, "byRole,"
    https://testing-library.com/docs/queries/byrole/, verified 2026-08-23.
13. Interaction Design Foundation, "Progressive Disclosure,"
    https://ixdf.org/literature/topics/progressive-disclosure, verified
    2026-08-23.
14. MITRE, "CWE-656: Reliance on Security Through Obscurity,"
    https://cwe.mitre.org/data/definitions/656.html, verified 2026-08-23.
15. MITRE, "CWE-602: Client-Side Enforcement of Server-Side Security,"
    https://cwe.mitre.org/data/definitions/602.html, verified 2026-08-23.
16. PortSwigger, "Business logic vulnerabilities: Examples,"
    https://portswigger.net/web-security/logic-flaws/examples, verified
    2026-08-23.

**Evidence grade.** high

**Most solid findings.** The W3C ARIA Authoring Practices Guide's disclosure
contract, role button and aria-expanded, Nielsen's 2006 article and its
distinction from staged disclosure corroborated independently by the
Interaction Design Foundation, and GOV.UK's own applicability guidance are all
primary or near-primary sources read directly.

**Unverified or unclear.** The 1985 Woolsey attribution rests on a single
tertiary citation, the primary book text was not independently read. No source
was found discussing whether an expanded state should persist across a return
visit. No source names disorganized secondary content as a failure mode in
those words, that item is this entry's own inference.

## Code

TypeScript, Python, and Go implementations of a minimal disclosure toggle
following the W3C's role button and aria-expanded contract from dimension 5,
each exposing an expand and collapse method plus a query for the current
state, with no framework dependency.

```typescript
interface DisclosureState {
  expanded: boolean;
}

class Disclosure {
  private state: DisclosureState = { expanded: false };
  private readonly triggerLabel: string;
  private readonly listeners: Array<(state: DisclosureState) => void> = [];

  constructor(triggerLabel: string) {
    this.triggerLabel = triggerLabel;
  }

  toggle(): DisclosureState {
    this.state = { expanded: !this.state.expanded };
    this.notify();
    return this.state;
  }

  expand(): DisclosureState {
    if (!this.state.expanded) {
      this.state = { expanded: true };
      this.notify();
    }
    return this.state;
  }

  collapse(): DisclosureState {
    if (this.state.expanded) {
      this.state = { expanded: false };
      this.notify();
    }
    return this.state;
  }

  isExpanded(): boolean {
    return this.state.expanded;
  }

  ariaAttributes(): Record<string, string> {
    return {
      role: "button",
      "aria-expanded": String(this.state.expanded),
      "aria-label": this.triggerLabel,
    };
  }

  onChange(listener: (state: DisclosureState) => void): void {
    this.listeners.push(listener);
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener(this.state);
    }
  }
}

function handleKeyActivation(disclosure: Disclosure, key: string): boolean {
  if (key === "Enter" || key === " ") {
    disclosure.toggle();
    return true;
  }
  return false;
}
```

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class DisclosureState:
    expanded: bool = False


class Disclosure:
    def __init__(self, trigger_label: str) -> None:
        self._state = DisclosureState()
        self._trigger_label = trigger_label
        self._listeners: list[Callable[[DisclosureState], None]] = []

    def toggle(self) -> DisclosureState:
        self._state = DisclosureState(expanded=not self._state.expanded)
        self._notify()
        return self._state

    def expand(self) -> DisclosureState:
        if not self._state.expanded:
            self._state = DisclosureState(expanded=True)
            self._notify()
        return self._state

    def collapse(self) -> DisclosureState:
        if self._state.expanded:
            self._state = DisclosureState(expanded=False)
            self._notify()
        return self._state

    def is_expanded(self) -> bool:
        return self._state.expanded

    def aria_attributes(self) -> dict[str, str]:
        return {
            "role": "button",
            "aria-expanded": str(self._state.expanded).lower(),
            "aria-label": self._trigger_label,
        }

    def on_change(self, listener: Callable[[DisclosureState], None]) -> None:
        self._listeners.append(listener)

    def _notify(self) -> None:
        for listener in self._listeners:
            listener(self._state)


def handle_key_activation(disclosure: Disclosure, key: str) -> bool:
    if key in ("Enter", " "):
        disclosure.toggle()
        return True
    return False
```

```go
package disclosure

type State struct {
	Expanded bool
}

type Listener func(State)

type Disclosure struct {
	state        State
	triggerLabel string
	listeners    []Listener
}

func New(triggerLabel string) *Disclosure {
	return &Disclosure{triggerLabel: triggerLabel}
}

func (d *Disclosure) Toggle() State {
	d.state = State{Expanded: !d.state.Expanded}
	d.notify()
	return d.state
}

func (d *Disclosure) Expand() State {
	if !d.state.Expanded {
		d.state = State{Expanded: true}
		d.notify()
	}
	return d.state
}

func (d *Disclosure) Collapse() State {
	if d.state.Expanded {
		d.state = State{Expanded: false}
		d.notify()
	}
	return d.state
}

func (d *Disclosure) IsExpanded() bool {
	return d.state.Expanded
}

func (d *Disclosure) AriaAttributes() map[string]string {
	expanded := "false"
	if d.state.Expanded {
		expanded = "true"
	}
	return map[string]string{
		"role":          "button",
		"aria-expanded": expanded,
		"aria-label":    d.triggerLabel,
	}
}

func (d *Disclosure) OnChange(l Listener) {
	d.listeners = append(d.listeners, l)
}

func (d *Disclosure) notify() {
	for _, l := range d.listeners {
		l(d.state)
	}
}

func HandleKeyActivation(d *Disclosure, key string) bool {
	if key == "Enter" || key == " " {
		d.Toggle()
		return true
	}
	return false
}
```
