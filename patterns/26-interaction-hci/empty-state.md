---
name: Empty State
slug: empty-state
family: 26-interaction-hci
category: Interaction and HCI
aliases: [Zero State, Blank Slate, No Data State]
first_described: "Craig Dennis, Codrops, January 9, 2013"
maturity: established
related: [wizard]
incompatible_with: []
verified: 2026-08-23
---

# Empty State

## 1. Name, aliases, and lineage

An empty state is the screen or region a person sees when there is no content
to show yet, whether because nothing has been created, everything has been
cleared, a search returned nothing, or something failed to load. It is also
called a zero state, a blank slate, or a no data state.

There is no single, widely credited inventor of the term. The earliest dated,
substantive discussion located for this entry is Craig Dennis's "Designing
For The Empty States," published on Codrops January 9, 2013, which defines
the pattern directly: empty states are places in apps that have no content or
data, they are empty, a blank page, and names three types, first use, user
cleared, and errors, citing Buffer, Timehop, Dropbox, Gmail, Sparrow, and
Safari as examples (Dennis, Craig, "Designing For The Empty States," Codrops,
January 9, 2013,
https://tympanus.net/codrops/2013/01/09/designing-for-the-empty-states/,
verified 2026-08-23).

Scott Hurff's "How to fix a bad user interface," published August 17, 2015,
models the blank state as one layer of a named conceptual sequence he calls
the UI Stack, running blank, loading, partial, error, and ideal, arguing the
blank layer functions as a transitional step deliberately designed to prevent
discouragement and motivate forward action toward the ideal state (Hurff,
Scott, "How to fix a bad user interface," scotthurff.com, August 17, 2015,
https://www.scotthurff.com/posts/why-your-user-interface-is-awkward-youre-ignoring-the-ui-stack/,
verified 2026-08-23). This is the earliest source located that treats an
empty screen as one state among several deliberately designed states, rather
than an edge case handled as an afterthought.

Material Design's own "Empty states" guidance is a later canonization of the
pattern inside a major design system, defining it as occurring when an item's
content cannot be shown (Google, "Empty states," Material Design,
https://m2.material.io/design/communication/empty-states.html, verified
2026-08-23).

## 2. Problem and context

A screen with no content and no explanation is indistinguishable from a
broken one. The Nielsen Norman Group's Kate Kaplan states the core risk
directly: an empty state's first guideline is to communicate system status,
clarifying whether content is loading, an error occurred, or genuinely no
results exist, because a specific message such as there are no records to
display for the selected date range prevents confusion and increases
confidence, where a blank region alone does not (Kaplan, Kate, "Designing
Empty States in Complex Applications: 3 Guidelines," Nielsen Norman Group,
September 19, 2021,
https://www.nngroup.com/articles/empty-state-interface-design/, verified
2026-08-23).

The UX Collective's Rosie Hoggmascall frames the stakes historically, opening
with three widely recognized bad blank or error moments, Chrome's offline
dinosaur, Windows' blue screen, and the classic spinning wait cursor, as
evoking frustration and dread, the negative baseline that a deliberately
designed empty state is meant to correct (Hoggmascall, Rosie, "The power of
empty states: How Slack drives user activation," UX Collective, March 11,
2025, https://uxdesign.cc/the-power-of-empty-states-how-slack-drives-user-activation-3a64dda73162,
verified 2026-08-23).

The context this problem shows up in is any screen or list whose content
depends on something the person has not yet done, a first-time dashboard, a
newly created project, a search box before a query, or a filtered view that
currently matches nothing.

## 3. Forces

Effort spent versus rarity of exposure is a real tension named directly by UX
Planet: only an estimated 2 to 5 percent of users encounter an empty state at
all, yet a well-designed one still improves usability and reinforces brand
personality, so the cost of a fully designed treatment must be weighed
against how few people will ever see it (Zhiyang, "Empty State Design: A
Practical Guide," UX Planet, June 17, 2025,
https://uxplanet.org/empty-state-design-a-practical-guide-94ad0adbda45,
verified 2026-08-23).

Encouragement versus condescension is a second tension. Atlassian's own
content guidance states the tonal goal directly, to leave people feeling
motivated, supported, and delighted, framed as giving a pat on the back for a
job well done, but immediately qualifies it: remember not to overdo it, since
timing and repetition are critical (Atlassian, "Empty state," Atlassian
Design System,
https://atlassian.design/content/writing-guidelines/empty-state/, verified
2026-08-23). SetProduct's guide names the failure side of the same tension
directly, warning against generic, robotic messaging and against oversized or
generic illustrations that distract (Kamushken, Roman, "Empty State UI
Design," SetProduct, updated June 7, 2026,
https://www.setproduct.com/blog/empty-state-ui-design, verified 2026-08-23).

The pattern favors reassurance and a clear next step, and it sacrifices
elaboration; the moment must communicate quickly, since Nielsen's own
reasoning for progressive disclosure and this entry's own reasoning for empty
states share the same underlying constraint, that most readers spend very
little attention on a screen that has nothing in it yet.

## 4. Applicability and non-applicability

Five independent design systems and authors converge on treating first-use,
user-cleared, zero-results, and error states as genuinely distinct
sub-types, each requiring different treatment.

IBM's Carbon Design System names three basic types, no data empty states for
first-time use, user action empty states as feedback from a search or a
completed process, and error management empty states for permissions, system
problems, or configuration, and it invokes Jakob Nielsen's own error message
principle directly for the error type, that error messages should be
expressed in plain language with no codes, precisely indicate the problem,
and constructively suggest a solution (IBM, "Empty states pattern," Carbon
Design System, https://carbondesignsystem.com/patterns/empty-states-pattern/,
verified 2026-08-23).

GitHub's Primer design system names three scenarios calling for different
tone, a feature not yet used, which should sound welcoming and human, a
screen temporarily empty, which should be factual, and an error condition,
which should use alert icons rather than playful graphics and stay concise
(GitHub, "Empty states," Primer Design System,
https://primer.style/product/ui-patterns/empty-states/, verified 2026-08-23).

Pencil and Paper frames the applicability question functionally rather than
by trigger, distinguishing an information-focused empty state that only needs
to prevent confusion, an action-focused one that urges the person to fill the
space, and a celebration-focused one, the rarest kind, actually a good thing,
with an inbox reaching zero as the example (Vassilatos, Fanny, and Crawshaw,
Ceara, "Empty states," Pencil and Paper, May 6, 2024,
https://www.pencilandpaper.io/articles/empty-states, verified 2026-08-23).

Applicability is therefore conditional on correctly identifying which of
these sub-types is showing. Treating a genuine, celebratory user-cleared
state with the same call-to-action urgency as a first-use state is a
non-applicability case in itself, covered further in dimension 11.

## 5. Structure

Four design systems document nearly identical anatomy independently. Material
Design's base structure is a non-interactive image and a text tagline, with
the image carrying a neutral or humorous tone and the tagline conveying the
purpose of the screen without appearing actionable, since an empty region is
not itself interactive (Google, "Empty states," verified 2026-08-23). IBM's
Carbon Design System documents five parts, an optional image related to the
situation, a short and where possible positive title, a body explaining the
next action and why the space is empty, a primary action, and an optional
secondary action linking to documentation (IBM, "Empty states pattern,"
verified 2026-08-23). GitHub's Primer names the same five parts under
different labels, a graphic, primary text, secondary text, a primary action,
and a secondary action, plus an optional border that stays invisible by
default (GitHub, "Empty states," verified 2026-08-23).

Atlassian's writing guidance adds content-level rules on top of the shared
skeleton: the headline should be informative and scannable, written in
sentence case with no punctuation unless it is a question; body text should
run one to two sentences; and a call to action should use an imperative verb
such as try, remove, or create, limited to one or two words, and should
always complement the title (Atlassian, "Empty state," verified 2026-08-23).

SAP Concur's Human Interface Guidelines confirm the same three-part skeleton
at a more minimal level, an optional image, a title in sentence case with no
period, and an action that is either a button or descriptive text, with
named title patterns such as you do not have any items yet for a state
needing action and there are no items at this time for one that does not
(SAP Concur, "Empty state," Concur HIG, https://hig.concur.com, verified
2026-08-23).

## 6. ASCII structure diagram

```
Screen or list about to render
        |
        v
Is the data fetch still in flight?
        |
   +----+----+
   |         |
  yes        no
   |         |
   v         v
Render      Does real data exist?
LOADING          |
state       +----+----+
(never      |         |
the empty  yes        no
state)      |         |
   |        v         v
   |   Render      Which kind of empty is it?
   |   normal          |
   |   view       +----+----+----+----+
   |                |    |    |    |
   |                v    v    v    v
   |            FIRST  USER  ZERO  ERROR
   |            -USE   -CLE  -RES  or
   |                   ARED  ULTS  BROKEN
   |                |    |    |    |
   |                v    v    v    v
   |          welcoming  cong  no    alert
   |          tone, CTA  ratu  results  icon,
   |          to create  lat   for X,   plain
   |                     ory   try Y    language,
   |                     tone            retry
   +-----------------------------------------------+
                     |
                     v
              Confirm which state
              is showing, per dim 2
```

## 7. Dynamics

The loading and empty distinction is a documented, real concern, not a
hypothetical one. The Nielsen Norman Group's communicate-system-status
guideline names it directly: an interface must make clear which of loading,
an error, or genuinely empty currently applies, because conflating them
erodes the confidence dimension 2 names as the core risk (Kaplan,
"Designing Empty States in Complex Applications," verified 2026-08-23). A
person shown a blank region while a fetch is still in flight, with no
distinct loading indicator, reads that blank region as the finished, empty
answer rather than as work still happening, which is exactly the confusion
Kaplan's guideline exists to prevent.

No source consulted for this entry discusses avoiding layout shift as the
empty state is replaced by real content as its own named design concern. This
is reported as an honest gap rather than resolved by assumption, though it
follows logically from the general loading and empty separation documented
above.

## 8. Implementation variants

A minimal, text-only variant is a first-class option in dense, enterprise
tools rather than a lesser fallback. SAP Concur's guidelines document this
directly: the action element of an empty state can be a muted-style button,
or descriptive text in sentence case with a period, rather than a full
graphic-plus-call-to-action treatment (SAP Concur, "Empty state," verified
2026-08-23).

A fully illustrated variant is the default treatment documented by most
consumer-facing sources cited so far, Material Design's neutral or humorous
imagery, Carbon's optional illustration, and Primer's marketing-icon
graphics.

Seeded or sample data as an alternative to a message is independently
documented across five sources, an unusually strong convergence for a single
technique. Material Design calls it starter content, pre-populating screens
with sample items, especially effective for content-storage apps and
template-based tools (Google, "Empty states," verified 2026-08-23). Carbon
lists starter content as one of three alternative approaches for first-use
scenarios, pre-built content allowing users to explore without consequences
(IBM, "Empty states pattern," verified 2026-08-23). UX Planet and Soul
Design System, Emplifi's own system, each name the identical technique under
the same starter-content label (Zhiyang, "Empty State Design," verified
2026-08-23; Emplifi, "Empty states," Soul Design System,
https://soul.emplifi.io/latest/content/ux-writing-patterns/empty-states-JArDj65M,
verified 2026-08-23). LogRocket names a real product example directly,
Pinterest pre-populating personalized boards during onboarding based on user
interests, eliminating the blank slate entirely (Malymon, Yaroslav, "Empty
states in UX done right: 4 inspiring examples," LogRocket Blog, September 17,
2025, https://blog.logrocket.com/ux-design/empty-states-ux-examples/,
verified 2026-08-23).

## 9. Known production uses

GitHub's own Primer design system documents the exact reasoning from
dimension 4 as production practice, applying it for a feature not yet used, a
screen temporarily empty, and error conditions, each with distinct copy
rules, and a dedicated graphic variant plus a code-block variant for
setup-instructional empty states (GitHub, "Empty states," verified
2026-08-23).

Slack's own design team wrote directly about redesigning empty states as
part of a broader visual refresh, describing more dimensional empty states
and a subtler shaded theming system as part of creating a softer visual feel
throughout Slack's interface (Sultan, Zack, Chen, Tina, Mehta, Siddhant, and
Fernandez, Miguel, "A more focused, productive Slack," Slack Design, October
2023, https://slack.design/articles/a-more-focused-productive-slack/,
verified 2026-08-23).

Dropbox, Duolingo, and Pinterest are named as production examples by
LogRocket, a secondary source. Dropbox uses a large, clearly marked
drag-and-drop area alongside a friendly illustration, Duolingo pairs
motivational quotes with streak counts and bonus exercises, and Pinterest's
seeded-board approach is the source of the starter-content example in
dimension 8 (Malymon, "Empty states in UX done right," verified 2026-08-23).

## 10. Consequences

Positive. The Nielsen Norman Group states that intentionally designed empty
states can help increase user confidence, improve system learnability, and
help users get started with key tasks (Kaplan, "Designing Empty States in
Complex Applications," verified 2026-08-23). Starter content, per dimension
8, reduces the same first-week abandonment risk by showing rather than
describing what a populated screen looks like.

Negative. Baymard Institute's research on the related zero-results sub-type
is the most directly sourced negative finding for this entry: 68 percent of
e-commerce sites have a no-results-page implementation that is essentially a
dead end for users, offering no more than a generic set of search tips
(Baymard Institute, "35 Examples of No Search Results UX," https://baymard.com/ecommerce-design-examples/35-no-search-results-page,
verified 2026-08-23). SetProduct names two further failure modes directly,
generic, robotic messaging and messaging that implies user fault, both of
which erode the confidence dimension 2 says the pattern exists to build
(Kamushken, "Empty State UI Design," verified 2026-08-23).

## 11. Failure modes and misuse

Mistaken for broken is the core failure mode nearly every source in this
entry exists to prevent. SetProduct states the design goal directly:
explaining why the screen is empty so it never reads as a glitch (Kamushken,
"Empty State UI Design," verified 2026-08-23).

Dead-end call to action, a reveal with no recovery path, is the best
documented failure mode found for this entry, from an authoritative primary
source. Baymard Institute's filter-UI guidance names the exact mechanism:
allowing a person to select a filter combination that produces no result and
then showing an empty page is a dead end; the recommendation is either to
prevent the selection or to offer a clear recovery path, such as no results
for these filters, try removing X (Baymard Institute, "Guidelines for a
Better Filtering UX," https://baymard.com/learn/ecommerce-filter-ui, verified
2026-08-23). Carbon's own guidance states the same principle
prescriptively, not to lead the user into a dead end (IBM, "Empty states
pattern," verified 2026-08-23).

Over-designed or condescending tone is documented as a caution inside two
practitioner sources rather than as a single dedicated essay. Atlassian's own
writing guidance warns not to overdo the encouraging tone, and SetProduct
lists oversized or generic illustrations that distract among its common
mistakes (Atlassian, "Empty state," verified 2026-08-23; Kamushken, "Empty
State UI Design," verified 2026-08-23). No single canonical source dedicated
specifically to this critique was located, and this is stated here plainly
rather than papered over with a fabricated one.

Blaming the user is named explicitly by SetProduct as a mistake to avoid,
never phrase messages implying user fault, echoing the Nielsen Norman Group's
own error-message principle in dimension 4 that the proper usage of any
system lies with its creators, not its users.

Confusing an empty state with a loading or an error state, covered fully in
dimension 7, is the fourth failure mode, named directly by Kaplan as a
distinct problem when the two states are not visually and textually
differentiated.

## 12. Trade-off matrix

| Dimension | Minimal, text-only | Fully illustrated | Seeded or sample data |
|---|---|---|---|
| Implementation cost | Lowest, SAP Concur's pattern needs only a title plus an optional muted button or text link, no custom art asset | Higher, requires a custom or brand-consistent illustration per Material Design's neutral-or-humorous requirement, plus ongoing maintenance as a brand evolves | Highest ongoing complexity, requires generating and maintaining realistic dummy data or a real-data seeding path, per Material's and Carbon's starter-content guidance |
| Clarity of what is happening | High if the copy is precise, per Baymard's dead-end guidance, but relies entirely on text, weakest for a reader who skims | An illustration reinforces the message, but risks distraction if oversized or generic, per SetProduct's own caution | Arguably clearest of all, since the person sees exactly what populated content will look like, eliminating the blank slate entirely, per LogRocket's Pinterest example |
| Not-started-yet versus broken signal | Depends entirely on copy quality, the SAP Concur title patterns you do not have any items yet versus there are no items at this time are the whole signal | Strongest signal against looking broken, per SetProduct's core design goal, since a deliberate illustration reads as intentional | Strong, since showing a working example of the populated state signals the feature works, the person simply has not used it yet |

## 13. Related and incompatible patterns

Wizard has a real, sourced, but narrower connection than a first guess might
suggest. PatternFly's wizard design guidelines state that a wizard's
progress-or-completion screen can be constructed from a variation of the
empty state pattern by embedding a progress bar and appropriate messaging
within the body of the wizard (PatternFly, "Wizard, design guidelines,"
https://www.patternfly.org/components/wizard/design-guidelines, verified
2026-08-23). This describes the empty-state pattern being reused for a
wizard's end, its progress or completion screen, not its blank first page.
The Nielsen Norman Group's own dedicated wizard article does not mention
empty states or a blank first step at all, and its closest related guidance
concerns carrying forward a returning user's previous selections as
defaults, a different concern entirely (Budiu, Raluca, "Wizards: Definition
and Design Recommendations," Nielsen Norman Group, June 25, 2017,
https://www.nngroup.com/articles/wizards/, verified 2026-08-23). This entry
reports the connection at the narrower scope PatternFly actually documents,
rather than overstating it to cover a wizard's opening screen as well.

No source consulted relates progressive disclosure, inline validation, or a
command palette to empty states, so no relationship is claimed for any of
them here.

## 14. Refactoring path in and out

To introduce a designed empty state into a screen that currently renders
blank or shows a raw zero-length list, first identify which sub-type from
dimension 4 the screen actually needs, first-use, user-cleared, zero-results,
or error, since each carries a different tone per Primer's and Carbon's
guidance. Build the shared skeleton from dimension 5, a short title, one to
two sentences of explanation, and where applicable a single primary action,
before considering an illustration at all. Add starter content, per
dimension 8, only where the underlying feature can safely show sample data
without confusing it for a person's real data.

To remove or simplify an empty state that has grown ornate enough to distract
or read as gimmicky, per the over-designed failure mode in dimension 11, the
first step is stripping the illustration and keeping only the title, body,
and action, checking whether the plainer version still communicates the same
system status from dimension 2. If the sub-type in question is rare enough
that user research shows nobody benefits from a custom design, the minimal
text-only variant from dimension 8 is the correct landing point.

## 15. Testing and verification

Testing Library's standard query APIs give the exact mapping onto the three
assertions this pattern needs. For the absence assertion, that the empty
state renders when a fetch legitimately returns zero items, the standard
getBy methods throw an error when they cannot find an element, so an
assertion that an element is not present in the DOM uses the queryBy family
instead, paired with jest-dom's toBeInTheDocument matcher (Testing Library,
"Appearance and Disappearance," https://testing-library.com/docs/guide-disappearance/,
verified 2026-08-23). For the not-yet-loaded assertion, that the empty state
should not render while a fetch is still in flight, findBy queries wait for
appearance and return the element once it exists, and waitForElementToBeRemoved
is the dedicated helper for the loading-to-loaded transition.

Kent C. Dodds reinforces the correct-tool-for-the-job distinction directly:
the only reason the query variant of the queries is exposed is to have a
function that does not throw an error if no element is found, and query
should be used exclusively for non-existence assertions, while find is for
elements that will appear asynchronously, since it produces superior error
messages compared with wrapping get in a manual wait (Dodds, Kent C.,
"Common mistakes with React Testing Library," May 4, 2020,
https://kentcdodds.com/blog/common-mistakes-with-react-testing-library,
verified 2026-08-23).

Neither source discusses testing which of the four sub-type variants from
dimension 4 renders for a given condition, that composite assertion is this
entry's own inference built on the documented query APIs, not a direct claim
from either source.

## 16. Observability signals

No canonical, named source directly documenting production observability
practice specific to empty states was located for this entry. What follows
is reasoned synthesis grounded in the sourced material above, labeled as such
rather than presented as established fact.

Baymard Institute's own measurement, that 68 percent of e-commerce sites ship
a dead-end no-results implementation per dimension 10, implies the same kind
of per-screen auditing a team could run internally, tracking how often a
given empty-state's primary action is actually clicked versus how often the
person abandons the screen, and how long a first-use empty state is shown
before the person takes their first action. This entry could not verify a
specific figure for either metric at a primary source and reports the gap
plainly rather than inventing one.

## 17. Security and privacy implications

No source consulted for this entry directly discusses a security or privacy
concern specific to the empty-state pattern itself, and this entry does not
manufacture one. The adjacent, well-documented concept sits one layer down,
at the HTTP and access-control level rather than in the product-design
literature.

The Mozilla Developer Network's own documentation for the HTTP 404 status
states only that a 404 status code indicates a resource is missing, without
indicating whether this is temporary or permanent (Mozilla Developer
Network, "404 Not Found,"
https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/404,
verified 2026-08-23). It does not itself discuss using a uniform not-found
response to avoid confirming a resource's existence to an unauthorized
requester, an access-control practice that is real and well known in web
security engineering but that this entry could not verify at a primary
source discussing it by name in this session. Bridging that adjacent
practice, returning an identical empty result for both a genuinely absent
resource and one the requester is not authorized to see, to the UI-level
empty state pattern is this entry's own inference, not a claim any source
consulted states directly, and it is named here as a plausible but
unconfirmed connection rather than a sourced fact.

## 18. References

1. Dennis, Craig, "Designing For The Empty States," Codrops, January 9, 2013,
   https://tympanus.net/codrops/2013/01/09/designing-for-the-empty-states/,
   verified 2026-08-23.
2. Hurff, Scott, "How to fix a bad user interface," scotthurff.com, August 17,
   2015,
   https://www.scotthurff.com/posts/why-your-user-interface-is-awkward-youre-ignoring-the-ui-stack/,
   verified 2026-08-23.
3. Google, "Empty states," Material Design,
   https://m2.material.io/design/communication/empty-states.html, verified
   2026-08-23.
4. Kaplan, Kate, "Designing Empty States in Complex Applications: 3
   Guidelines," Nielsen Norman Group, September 19, 2021,
   https://www.nngroup.com/articles/empty-state-interface-design/, verified
   2026-08-23.
5. Hoggmascall, Rosie, "The power of empty states: How Slack drives user
   activation," UX Collective, March 11, 2025,
   https://uxdesign.cc/the-power-of-empty-states-how-slack-drives-user-activation-3a64dda73162,
   verified 2026-08-23.
6. Zhiyang, "Empty State Design: A Practical Guide," UX Planet, June 17,
   2025, https://uxplanet.org/empty-state-design-a-practical-guide-94ad0adbda45,
   verified 2026-08-23.
7. Atlassian, "Empty state," Atlassian Design System,
   https://atlassian.design/content/writing-guidelines/empty-state/, verified
   2026-08-23.
8. Kamushken, Roman, "Empty State UI Design," SetProduct, updated June 7,
   2026, https://www.setproduct.com/blog/empty-state-ui-design, verified
   2026-08-23.
9. IBM, "Empty states pattern," Carbon Design System,
   https://carbondesignsystem.com/patterns/empty-states-pattern/, verified
   2026-08-23.
10. GitHub, "Empty states," Primer Design System,
    https://primer.style/product/ui-patterns/empty-states/, verified
    2026-08-23.
11. Vassilatos, Fanny, and Crawshaw, Ceara, "Empty states," Pencil and
    Paper, May 6, 2024, https://www.pencilandpaper.io/articles/empty-states,
    verified 2026-08-23.
12. Emplifi, "Empty states," Soul Design System,
    https://soul.emplifi.io/latest/content/ux-writing-patterns/empty-states-JArDj65M,
    verified 2026-08-23.
13. SAP Concur, "Empty state," Concur HIG, https://hig.concur.com, verified
    2026-08-23.
14. Malymon, Yaroslav, "Empty states in UX done right: 4 inspiring
    examples," LogRocket Blog, September 17, 2025,
    https://blog.logrocket.com/ux-design/empty-states-ux-examples/, verified
    2026-08-23.
15. Sultan, Zack, Chen, Tina, Mehta, Siddhant, and Fernandez, Miguel, "A
    more focused, productive Slack," Slack Design, October 2023,
    https://slack.design/articles/a-more-focused-productive-slack/, verified
    2026-08-23.
16. Baymard Institute, "35 Examples of No Search Results UX,"
    https://baymard.com/ecommerce-design-examples/35-no-search-results-page,
    verified 2026-08-23.
17. Baymard Institute, "Guidelines for a Better Filtering UX,"
    https://baymard.com/learn/ecommerce-filter-ui, verified 2026-08-23.
18. PatternFly, "Wizard, design guidelines,"
    https://www.patternfly.org/components/wizard/design-guidelines, verified
    2026-08-23.
19. Budiu, Raluca, "Wizards: Definition and Design Recommendations," Nielsen
    Norman Group, June 25, 2017, https://www.nngroup.com/articles/wizards/,
    verified 2026-08-23.
20. Testing Library, "Appearance and Disappearance,"
    https://testing-library.com/docs/guide-disappearance/, verified
    2026-08-23.
21. Dodds, Kent C., "Common mistakes with React Testing Library," May 4,
    2020,
    https://kentcdodds.com/blog/common-mistakes-with-react-testing-library,
    verified 2026-08-23.
22. Mozilla Developer Network, "404 Not Found,"
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/404,
    verified 2026-08-23.

**Evidence grade.** medium

**Most solid findings.** The four-way sub-type taxonomy, first-use,
user-cleared, zero-results, and error, is independently corroborated across
five design systems and authors. The starter-content technique is
independently named by five sources with one named production example.
Baymard's dead-end statistics for the zero-results sub-type come from a
primary source read directly.

**Unverified or unclear.** No single canonical source was found dedicated to
the over-designed or condescending-tone critique; it is assembled here from
two adjacent practitioner cautions. The wizard connection in dimension 13 is
sourced but narrower than a first guess would suggest, and the security
angle in dimension 17 is this entry's own unconfirmed inference bridging two
separate literatures rather than a claim any source states directly.
Observability figures specific to this pattern were not located.

## Code

TypeScript, Python, and Go implementations of an empty-state resolver that
distinguishes loading, first-use, user-cleared, zero-results, and error per
the sub-type taxonomy from dimension 4, and the loading-versus-empty
separation from dimension 7.

```typescript
type EmptyKind = "loading" | "firstUse" | "userCleared" | "zeroResults" | "error";

interface ScreenInput {
  isLoading: boolean;
  hasEverHadContent: boolean;
  itemCount: number;
  hasActiveFilter: boolean;
  loadError: string | null;
}

interface EmptyStateContent {
  kind: EmptyKind;
  title: string;
  primaryActionLabel: string | null;
}

function resolveEmptyState(input: ScreenInput): EmptyStateContent | null {
  if (input.isLoading) {
    return { kind: "loading", title: "Loading", primaryActionLabel: null };
  }
  if (input.itemCount > 0) {
    return null;
  }
  if (input.loadError !== null) {
    return { kind: "error", title: input.loadError, primaryActionLabel: "Retry" };
  }
  if (input.hasActiveFilter) {
    return {
      kind: "zeroResults",
      title: "No results for these filters",
      primaryActionLabel: "Clear filters",
    };
  }
  if (input.hasEverHadContent) {
    return {
      kind: "userCleared",
      title: "All caught up",
      primaryActionLabel: null,
    };
  }
  return {
    kind: "firstUse",
    title: "Create your first item to get started",
    primaryActionLabel: "Create item",
  };
}
```

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EmptyKind(Enum):
    LOADING = "loading"
    FIRST_USE = "first_use"
    USER_CLEARED = "user_cleared"
    ZERO_RESULTS = "zero_results"
    ERROR = "error"


@dataclass
class ScreenInput:
    is_loading: bool
    has_ever_had_content: bool
    item_count: int
    has_active_filter: bool
    load_error: Optional[str]


@dataclass
class EmptyStateContent:
    kind: EmptyKind
    title: str
    primary_action_label: Optional[str]


def resolve_empty_state(screen: ScreenInput) -> Optional[EmptyStateContent]:
    if screen.is_loading:
        return EmptyStateContent(EmptyKind.LOADING, "Loading", None)
    if screen.item_count > 0:
        return None
    if screen.load_error is not None:
        return EmptyStateContent(EmptyKind.ERROR, screen.load_error, "Retry")
    if screen.has_active_filter:
        return EmptyStateContent(
            EmptyKind.ZERO_RESULTS, "No results for these filters", "Clear filters"
        )
    if screen.has_ever_had_content:
        return EmptyStateContent(EmptyKind.USER_CLEARED, "All caught up", None)
    return EmptyStateContent(
        EmptyKind.FIRST_USE, "Create your first item to get started", "Create item"
    )
```

```go
package emptystate

type Kind string

const (
	Loading      Kind = "loading"
	FirstUse     Kind = "first_use"
	UserCleared  Kind = "user_cleared"
	ZeroResults  Kind = "zero_results"
	ErrorKind    Kind = "error"
)

type ScreenInput struct {
	IsLoading         bool
	HasEverHadContent bool
	ItemCount         int
	HasActiveFilter   bool
	LoadError         string
}

type Content struct {
	Kind                Kind
	Title               string
	PrimaryActionLabel  string
	HasPrimaryAction    bool
}

func ResolveEmptyState(input ScreenInput) *Content {
	if input.IsLoading {
		return &Content{Kind: Loading, Title: "Loading"}
	}
	if input.ItemCount > 0 {
		return nil
	}
	if input.LoadError != "" {
		return &Content{
			Kind:               ErrorKind,
			Title:              input.LoadError,
			PrimaryActionLabel: "Retry",
			HasPrimaryAction:   true,
		}
	}
	if input.HasActiveFilter {
		return &Content{
			Kind:               ZeroResults,
			Title:              "No results for these filters",
			PrimaryActionLabel: "Clear filters",
			HasPrimaryAction:   true,
		}
	}
	if input.HasEverHadContent {
		return &Content{Kind: UserCleared, Title: "All caught up"}
	}
	return &Content{
		Kind:               FirstUse,
		Title:              "Create your first item to get started",
		PrimaryActionLabel: "Create item",
		HasPrimaryAction:   true,
	}
}
```
