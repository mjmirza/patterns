---
name: Optimistic Undo
slug: optimistic-undo
family: 26-interaction-hci
category: Interaction and HCI
aliases: [Undo Toast, Undo Snackbar, Undo Send]
first_described: "Google, New in Labs. Undo Send, Official Gmail Blog, March 19, 2009"
maturity: established
related: [undo]
incompatible_with: []
verified: 2026-08-23
---

# Optimistic Undo

## 1. Name, aliases, and lineage

Optimistic undo is the pattern where an action, a delete, an archive, a
send, or a move, is performed immediately in the interface, before any
blocking confirmation, and a brief, dismissible notification appears with an
Undo affordance and a short time window, after which the action becomes
permanent. It is also called an undo toast or undo snackbar, and Gmail's own
implementation is named Undo Send. This is a distinct pattern from this
catalogue's own general Undo entry, which covers command-history,
Ctrl-Z-style reversal, and the two are compared directly in dimension 13.

The clearest, directly verified origin is Gmail's own announcement. this
entry fetched the live page directly and confirmed its title and date, New
in Labs. Undo Send, posted March 19, 2009 on the Official Gmail Blog (Google,
"New in Labs: Undo Send," Official Gmail Blog,
https://gmail.googleblog.com/2009/03/new-in-labs-undo-send.html, verified
2026-08-23). The feature reportedly graduated from an opt-in Labs experiment
to a permanent, default setting for all Gmail users around June 2015,
corroborated by several secondary sources this entry could not trace back to
a primary Google announcement, and that date is reported here with that
caveat stated plainly rather than presented as fully confirmed.

Jakob Nielsen's own current, independent blog, distinct from the Nielsen
Norman Group he co-founded, names and argues for this exact pattern under
the heading Optimistic UI plus Guaranteed Undo. instead of asking are you
sure before every action, just do it immediately and offer easy undo
(Nielsen, Jakob, "Optimistic UI + Guaranteed Undo," UX Tigers,
https://uxtigers.com/post/think-time-ux, verified 2026-08-23). This entry
treats uxtigers.com and nngroup.com as two distinct publications, since
conflating them would misattribute a claim.

## 2. Problem and context

A blocking confirmation dialog interrupts every single invocation of an
action, whether that particular invocation was a mistake or not, which is
costly for actions a person takes often and can genuinely reverse. This
shows up anywhere a frequent, low-risk, reversible action, archiving an
email, deleting a card, sending a message, sits behind a confirmation step
that most people never actually needed.

## 3. Forces

Nielsen's own UX Tigers article names the central tension directly. every
invocation of a blocking dialog interrupts flow, whereas an immediate action
paired with an easy undo eliminates decision friction while maintaining
safety, at least for the reversible case (Nielsen, "Optimistic UI +
Guaranteed Undo," verified 2026-08-23).

Baymard Institute's own touch-device research names the same trade from a
different angle, and its finding is directly relevant since it is grounded
in a real usability study rather than opinion. all users are taxed with
increased UX friction by a confirmation dialog, whereas with an undo-based
approach a person simply performs the action, and if it happened to be
accidental, they can revert it (Baymard Institute, "Handling Accidental Taps
on Touch Devices," https://baymard.com/blog/handling-accidental-taps-on-touch-devices,
verified 2026-08-23). Baymard's own framing states this cost falls on every
user of the frequent action, not only the rare person who makes a mistake.

A genuine, documented tension exists inside the source material itself, and
this entry reports both sides rather than picking a winner. a separate
Nielsen Norman Group article on a related but distinct topic, closing an
editor with unsaved work, stays confirmation-first and never engages with an
undo alternative at all, stating plainly that this solution is ideal for
destructive cancel actions that would lose the user's work, and to always
ask for confirmation before committing destructive actions (Nielsen Norman
Group, "Cancel vs Close: Design to Distinguish the Difference,"
https://www.nngroup.com/articles/cancel-vs-close/, verified 2026-08-23).
whether an action is reversible enough for optimistic undo, or destructive
enough to need a blocking confirmation instead, is exactly the boundary
question dimension 4 addresses.

## 4. Applicability and non-applicability

Nielsen's own UX Tigers article states the applicable case directly. emails,
tasks, lightweight edits, and list operations, and social actions where
reversal carries minimal cost, and states the non-applicable case with equal
directness. permanent deletions, financial transactions, and broad
publishing require traditional confirmation due to higher reversal costs
(Nielsen, "Optimistic UI + Guaranteed Undo," verified 2026-08-23).

The sharper, structural boundary is whether the action's effect has already
left the system and become a fact somewhere else. Gmail's own current
support documentation confirms the mechanism directly. the setting offers a
send cancellation period of 5, 10, 20, or 30 seconds (Google, "Send or
unsend Gmail messages," https://support.google.com/mail/answer/2819488,
verified 2026-08-23), which is a delay before the message is transmitted at
all, not a retrieval of one that already left. Several secondary sources
converge on this exact framing, describing the feature as a delay-and-cancel
mechanism rather than a true recall, and this entry treats that convergence
as reasonable corroboration even though it could not independently confirm
the underlying mechanism against Google's own engineering documentation.

This catalogue's own general Undo entry states the identical boundary using
the same Gmail example, that the feature works by preventing the send from
ever completing during the delay, not by retrieving a message that already
left the server, and names the general principle plainly. any action with
the same shape sits outside true undo's reach for the identical structural
reason. once the delay window passes and the send actually fires, there is
nothing left for optimistic undo to reach either. the two entries share this
exact boundary because they are answering the same underlying question from
two different angles, described fully in dimension 13.

## 5. Structure

Four components recur across the sourced material. the immediate optimistic
state change, the toast or snackbar notification itself, an Undo action
inside it, and a timer governing how long that action stays available.

Material Design 3's own component guidelines describe the notification
directly. snackbars show short updates about app processes at the bottom of
the screen, and can either disappear or remain on screen until the user
takes action (Google, "Snackbar," Material Design 3,
https://m3.material.io/components/snackbar/specs, verified 2026-08-23). the
same guidelines state a precise, load-bearing split in timing behavior.
snackbars with actions should not auto-dismiss at all, while a snackbar
carrying no action button auto-dismisses on its own after 4 to 10 seconds.
strictly, an actionable undo toast should not be racing a fixed clock at
all, under Material Design's own accessibility-driven guidance, a rule real
products like Gmail deliberately deviate from by imposing a hard timeout
even on an actionable notification.

Android's own Jetpack Compose documentation gives a concrete, named worked
example matching this pattern exactly. after a user deletes an email or
message, a snackbar appears to confirm the action and offer an Undo option
(Android Developers, "Snackbar," Jetpack Compose,
https://developer.android.com/develop/ui/compose/components/snackbar,
verified 2026-08-23), and documents a distinct duration value,
SnackbarDuration.Indefinite, specifically for persisting until the person or
the program dismisses it rather than auto-dismissing on a short timer.

## 6. ASCII structure diagram

```
  person triggers action
  (delete / archive / send / move)
             |
             v
   UI updates IMMEDIATELY
   item disappears / marked sent
             |
             v
   toast or snackbar appears
   "Message sent."  [Undo]
   (timer running, if any)
             |
        +----+----+
        |         |
   person clicks   timer expires
      Undo        (no interaction)
        |         |
        v         v
   action        action
   REVERTED      COMMITTED
   UI restored   (network call
   to prior       fires, or
   state          soft-delete
        |         becomes
        |         permanent)
        v         v
   toast          toast
   dismissed      auto-dismisses
```

## 7. Dynamics

This entry could not find a source directly addressing whether the timer
resets on hover or interaction, and reports that as a genuine, unresolved
gap rather than guessing an answer. Material Design 3's own guidance
sidesteps the question for an actionable snackbar specifically, since its
own rule against auto-dismissing an actionable toast at all removes the
timer this question would apply to, for a strictly compliant implementation.
Gmail's own mechanism, per dimension 4, is a fixed countdown gating an
actual network send, architecturally distinct from a UI dismissal timer
reacting to focus or hover, though this entry could not confirm whether
navigating away or closing the tab during that window still lets the send
fire.

Accessibility requirements for the toast are well documented and carry real,
specific obligations. the Web Content Accessibility Guidelines' own Timing
Adjustable criterion requires that for content with a set time limit, at
least one of several accommodations applies, turning the limit off, extending
it to at least ten times the default, or a twenty-second warning with a
repeatable extension, unless one of three narrow exceptions holds (World
Wide Web Consortium, "Understanding Success Criterion 2.2.1: Timing
Adjustable,"
https://www.w3.org/WAI/WCAG21/Understanding/timing-adjustable.html, verified
2026-08-23). the same source states plainly that if a person has no other
way to discover the same information or perform the same function, the
message must meet this criterion, which applies directly to a toast whose
only path to the underlying recovery is the toast itself.

The toast is also a status message in the Web Content Accessibility
Guidelines' own sense, and its Status Messages criterion states the intent
directly, making people aware of important changes in content that are not
given focus, in a way that does not unnecessarily interrupt their work (World
Wide Web Consortium, "Understanding Success Criterion 4.1.3: Status
Messages," https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html,
verified 2026-08-23). a toast implemented as plain visual content with no
programmatic role or live-region wiring at all fails this criterion outright,
since an assistive-technology user has no way to be informed a status change
happened, let alone recover from it.

Which ARIA role a toast should carry is a genuine, sourced disagreement
between a very widely used implementation and its own surrounding
accessibility guidance. Material UI's own Snackbar documentation states its
component uses an alert role on the content container, an assertive,
interrupting announcement (MUI, "React Snackbar component,"
https://mui.com/material-ui/react-snackbar/, verified 2026-08-23), while
Material Design 3's own accessibility guidance recommends the opposite for
this exact use case. snackbars should be announced once they appear on the
screen, but should not grab focus or prevent people from completing their
current task, a polite, non-interrupting posture. this entry reports the
disagreement plainly rather than resolving it, since it is a real, sourced
tension between a shipped default and the design system it claims to
implement.

## 8. Implementation variants

Gmail's Undo Send is the clearest, most widely cited real implementation, and
it works by delaying the actual send rather than reversing one. Google's own
current support documentation confirms a send-cancellation period of 5, 10,
20, or 30 seconds, and clicking Undo during that window cancels the outbound
send before it leaves Google's servers, meaning no message was ever truly
sent to revert (Google, "Send or unsend Gmail messages,"
https://support.google.com/mail/answer/2819488, verified 2026-08-23). this is
a delay-not-recall implementation, the same structural family named in
dimension 4 and elaborated in dimension 13.

Jakob Nielsen's own UX Tigers article gives the pattern's canonical
illustrative example, contrasting it directly with the confirm-dialog
alternative it is meant to replace, "Email archived. Undo?" beats
"Are you sure you want to archive this email?" (Nielsen,
"Optimistic UI + Guaranteed Undo," https://uxtigers.com/post/think-time-ux,
verified 2026-08-23). the article uses this as its worked example of a
reversal-based, rather than delay-based, implementation.

Material Design 3's own component guidance treats the pattern as a structural
choice belonging to the snackbar component itself, not a separate mechanism.
an actionable snackbar carries an optional action button, commonly Undo, and
the same source's rule against auto-dismissing an actionable snackbar (per
dimension 5) means the implementation choice of delay-based versus
reversal-based Undo is orthogonal to the toast's own dismissal behavior
(Google, "Material Design 3: Snackbar,"
https://m3.material.io/components/snackbar/specs, verified 2026-08-23).

Android's own Jetpack Compose toolkit implements the indefinite-actionable
half of that rule at the code level, exposing a dedicated
`SnackbarDuration.Indefinite` value distinct from its `Short` and `Long`
timed durations specifically for a snackbar carrying an action a person must
be able to reach without a race against a clock (Android Developers,
"Snackbar,"
https://developer.android.com/develop/ui/compose/components/snackbar,
verified 2026-08-23).

GitHub's bulk-edit surfaces implement a third variant, a single Undo covering
a whole batch of committed changes rather than one change at a time, described
fully in dimension 13's cross-reference to this catalogue's own Bulk action
entry.

## 9. Known production uses

Gmail's Undo Send graduated from an opt-in Labs feature to Gmail's default,
on-by-default behavior in June 2015, per multiple independent secondary
sources, though this entry could not locate a primary Google announcement of
that specific graduation date despite several attempts, and reports the date
with that caveat rather than as a directly Google-confirmed fact.

A person's own experience of Gmail's star-toggle and archive actions is
the article's own worked example for the reversal-based half of the pattern,
per dimension 8, and this entry treats that as the closest available
production illustration for a reversal-based implementation, distinct from
Gmail's own delay-based send-cancellation mechanism described separately in
the same dimension.

GitHub's bulk-edit surfaces on project boards and issue lists ship a single
Undo action covering an entire committed batch of changes at once, rather
than one Undo per individual row, a production instance of the batch-scoped
variant of this pattern elaborated fully in dimension 13.

Jakob Nielsen's UX Tigers post on optimistic UI plus guaranteed undo, cited
across dimensions 1 and 3, treats the pattern as a named, general design
recommendation rather than describing one specific shipping product, and this
entry relies on it for the pattern's naming and rationale rather than as a
production-use citation in its own right.

## 10. Consequences

The pattern removes the confirmation dialog's interruption cost from the
common path entirely, letting the person's intended action complete at once
while the system holds a safety net in reserve rather than in front of them,
which is Nielsen's own stated rationale in dimension 3. this trades a
guaranteed, always-paid interruption cost for a rarely-paid recovery cost,
since most triggered actions are genuinely intended and the person never
touches the Undo control at all.

The trade is not free. it introduces a genuinely time-limited recovery window
where none previously existed under a pure confirm-first flow, and this
entry's dimension 7 already reports as an open, unresolved gap whether that
window's timer behaves consistently across interaction states such as hover
or focus. a person who is slow to notice the toast, or who is using assistive
technology that takes longer to reach the message, faces a real risk of the
window closing before they can act, which is precisely the concern WCAG's
Timing Adjustable criterion in dimension 7 exists to address.

For a delay-based implementation such as Gmail's, the consequence is
structurally different from a reversal-based one, per dimension 8. because
the underlying action, the actual send, never happens until the delay
elapses, there is no state to revert and no possibility of a failed or
partial undo. a reversal-based implementation instead genuinely reverts a
committed change, which reintroduces on a smaller, single-action scale the
same partial-failure question this catalogue's own Bulk action entry treats
as a first-class concern for a whole batch, an open question this entry does
not resolve for the single-action case and reports honestly as unaddressed.

## 11. Failure modes and misuse

The most direct misuse is applying the pattern to an action that cannot
genuinely be undone once its side effects have propagated, an email already
delivered to a third party's inbox, a payment already settled with a
processor, or a message already read by another person. offering an Undo
button on an action of this kind does not restore the prior state, it only
creates the false impression that it will, which is a worse outcome than
offering no undo at all, since the person now believes a recovery happened
when it did not.

A second failure mode is a toast that disappears before the person notices
it, whether from a too-short auto-dismiss timer on what should have been an
actionable, non-auto-dismissing snackbar per Material Design 3's own rule in
dimension 5, or from the person's attention being elsewhere at the moment the
toast appears and disappears. this is functionally the same failure as
offering no undo, since a control nobody can reach in time provides no real
safety net.

A third failure mode is the accessibility gap this entry's dimension 7
documents directly. a toast implemented with role="alert" that interrupts an
assistive-technology user's current task, or one with no programmatic role
or live-region wiring at all, fails the Status Messages criterion described
in dimension 7 and can leave a screen-reader user with no functional access
to the Undo control at all even though a sighted mouse user has full access
to it, an unequal-access failure rather than a merely inconvenient one.

A fourth, narrower failure mode applies specifically to a reversal-based
implementation covering a batch of changes rather than a single one, per
dimension 10's honestly-reported open question. a partial reversal that
succeeds for some items in the batch and fails for others, with no clear
per-item feedback to the person about which, leaves them uncertain whether
their undo actually worked, a state this entry does not know of a sourced,
general solution for.

## 12. Trade-off matrix

| Dimension | Optimistic action plus undo | Confirm-before-action dialog |
|---|---|---|
| Interruption cost on the common, intended path | None. the action completes immediately | Paid every single time, intended or not |
| Recovery cost on the rare, mistaken path | A time-limited window the person must notice and use in time | None needed. the mistake never happens because it was blocked upfront |
| Irreversible actions | Unsafe without a delay-based variant, per dimension 11's first failure mode | Safe by construction, since nothing happens until confirmed |
| Accessibility burden | Falls on getting the live region and timing right, per dimension 7 | Falls on a standard, well-understood modal-dialog pattern |
| Batch or bulk actions | Raises the partial-failure question from dimension 11's fourth failure mode | A single upfront confirmation covers the whole batch cleanly |
| Perceived speed | Immediate, since the interface does not wait for a decision first | Slower, since the person must read and respond before anything happens |

## 13. Related and incompatible patterns

This entry is closely related to, but structurally distinct from, this
catalogue's own Undo entry. Undo covers the general command-reversal
mechanism, typically keyboard-triggered and available on demand for a
sequence of past actions, tracing back to the FRESS-1968 shadow-copy
mechanism this catalogue's Autosave entry also traces its own lineage to,
per that entry's dimension 13. Optimistic undo is a narrower, specific
application of that same reversal idea, always paired with a toast or
snackbar surfacing exactly one recent action, and always time-limited rather
than available indefinitely on demand.

The two patterns share the Gmail delay-not-recall boundary condition directly.
this catalogue's own Undo entry uses Gmail's actual mechanism as its own
counter-example, since a delayed send that has not yet left Google's servers
is not really being reversed at all when cancelled, it is simply being
prevented from having ever happened, an important structural distinction this
entry's own dimension 8 makes explicit for the same reason.

This entry is also related to this catalogue's own Bulk action entry, sharing
GitHub's own documented single-undo-for-a-whole-bulk-table-edit guarantee as
a direct, load-bearing cross-reference. where Bulk action treats the question
of a whole batch succeeding or partially failing as a first-class concern
covered by Google's AIP-233 index-keyed failure-map contract, this entry's
own dimension 11 explicitly declines to claim a general, sourced solution
exists for the narrower question of what a person sees when their single Undo
click on a bulk action partially fails, reporting it honestly as an open gap
this catalogue's Bulk action entry addresses at the API level but this entry
does not resolve at the interface level.

This entry is incompatible with a pure confirm-before-action dialog applied
to the same trigger, per dimension 12's trade-off matrix, since the two
patterns solve the identical problem, preventing an unintended action's
consequences, by opposite means, one paying the cost upfront and the other
paying it only when actually needed. a single trigger should use one or the
other, not both, since stacking a confirmation dialog in front of an
optimistic action removes the very speed benefit the pattern exists to
provide.

## 14. Refactoring path in and out

Refactoring a confirm-before-action dialog into this pattern starts by
identifying which of the dialog's guarded actions are genuinely reversible
within a short window, distinguishing them from the irreversible actions
dimension 11 warns against converting. for each reversible action, remove the
blocking dialog, apply the change immediately, and surface an actionable
toast per Material Design 3's own non-auto-dismissing rule from dimension 5,
carrying an Undo control wired to the exact inverse of the applied change.
for actions found to be genuinely irreversible, either leave the confirm
dialog in place or convert to the delay-based variant from dimension 8, per
Gmail's own send-delay mechanism, rather than a reversal-based one.

The accessibility work from dimension 7 belongs in this same refactoring
pass, not as a follow-up. the live region backing the toast must satisfy
the WCAG Status Messages criterion from dimension 7, and the choice between
role="status" and role="alert" must be made
deliberately rather than defaulted, given the genuine, sourced disagreement
between Material UI's own shipped alert default and the accessibility
community's and Material Design 3's own recommendation toward a less
interrupting status role, both reported in dimension 7.

Refactoring out of this pattern, back toward a confirm-before-action dialog,
is most often driven by discovering that an action assumed reversible turns
out not to be, per dimension 11's first failure mode, or by a batch-scoped
use case surfacing the partial-failure ambiguity from dimension 11's fourth
failure mode with no acceptable resolution at the interface level. in either
case the safer, more conservative confirm-first flow is the correct fallback,
since a false sense of recoverability is a worse outcome than the interruption
cost this pattern exists to remove.

## 15. Testing and verification

Verify the optimistic path itself, that the triggering action updates the
interface immediately and shows the actionable toast, without waiting on any
network round trip to confirm the change before rendering it, which is the
whole premise the pattern exists to deliver.

Verify the Undo path, that clicking the Undo control within the window fully
reverts the applied change and dismisses the toast, and, for a delay-based
implementation such as Gmail's own send-delay mechanism, that the underlying
network call genuinely never fires when Undo is clicked in time.

Verify the timer's edge behavior directly, given dimension 7's own honestly
reported gap around whether interaction resets it. write a test asserting
whatever behavior the implementation actually chose, expiry-fires-the-action
at the boundary instant, and a second test confirming the toast does not
dismiss or the action does not commit one tick before that boundary.

Verify the accessibility requirements from dimension 7 as explicit,
automatable checks rather than manual spot-checks alone. the toast is
exposed to assistive technology per the WCAG Status Messages criterion, the
chosen role, whichever the implementation settled on between status and
alert per dimension 7's documented disagreement, is present on the correct
element, and the toast's effective visible duration, for any non-actionable
variant, meets or exceeds the extension WCAG's Timing Adjustable criterion
requires.

For a batch-scoped implementation, verify the partial-failure question from
dimension 11's fourth failure mode has some deliberate, tested answer, even a
minimal one, such as an explicit test asserting what the person sees when
some items in a bulk undo succeed and others fail, since dimension 11 reports
no general, sourced pattern to copy and the team must choose and test its own
answer.

## 16. Observability signals

The single most useful signal is the undo rate itself, the share of triggered
actions that are followed by an Undo click within the window, tracked per
action type. a persistently high undo rate on one specific action is a direct
signal that the action's own default behavior, its copy, or its trigger
placement is surprising people more often than intended, which is a design
problem this pattern's own safety net cannot fix on its own, it can only
soften the cost of it.

The undo-click timing distribution, how long after the action a person
actually clicks Undo, is the practical evidence needed to answer dimension
7's own open question about a reasonable window length and whether it should
reset on interaction, since a distribution clustered near the current
window's edge is direct evidence the window is too short for real people
using the real product, while one clustered early suggests room to shorten it.

For a delay-based implementation, instrument the send-cancellation event
separately from a simple undo click, distinguishing a person who clicked
Undo and had the underlying send genuinely cancelled from any edge case where
the click arrived after the delay had already elapsed, since the latter is a
silent failure of the whole safety guarantee and should alert loudly rather
than pass unnoticed.

For a batch-scoped implementation, instrument the partial-failure case from
dimension 11's fourth failure mode directly, a per-item success and failure
count on every bulk undo attempt, since without this signal a team has no way
to know whether the open, unresolved interface question from dimension 11 is
a rare theoretical concern or a frequent real one worth solving properly.

## 17. Security and privacy implications

A delay-based implementation such as Gmail's own send-delay mechanism has a
narrow but real security property worth stating plainly. because the
underlying network call genuinely has not fired yet, the window is a true
prevention opportunity, not merely a cosmetic one, and the server-side
enforcement of that delay, not a client-side timer alone, is what makes the
guarantee trustworthy. an implementation that only fakes the delay in the
client while the real request already went out at the moment of the
triggering click offers no real protection at all, only the false appearance
of it, which is the same category of harm dimension 11's first failure mode
describes for a genuinely irreversible action.

A reversal-based implementation, by contrast, has already let the underlying
change take effect by the time Undo is offered, so any downstream system,
webhook, notification, or search index that reacted to the original change
before the Undo click may have already propagated it elsewhere. an
implementation covering this class of action honestly should not claim the
Undo fully reverts the action's effects unless it also reverts or
compensates for those downstream reactions, a scope question this entry does
not know of a general, sourced answer to and reports as a genuine gap rather
than asserting an unverified guarantee.

For a bulk-scoped Undo, per dimension 13's cross-reference to this
catalogue's own Bulk action entry, the OWASP Broken Object Level Authorization
guidance that entry's dimension 17 cites for a bulk endpoint's per-item
identifier applies equally to an Undo endpoint reversing a batch. every
identifier in the undo request must be checked against the current person's
authorization independently, since a batch containing even one identifier the
person does not actually own must not silently revert that item alongside the
ones they do own.

## 18. References

1. Google, "New in Labs: Undo Send," Official Gmail Blog,
   https://gmail.googleblog.com/2009/03/new-in-labs-undo-send.html, verified
   2026-08-23.
2. Nielsen, Jakob, "Optimistic UI + Guaranteed Undo," UX Tigers,
   https://uxtigers.com/post/think-time-ux, verified 2026-08-23.
3. Baymard Institute, "Handling Accidental Taps on Touch Devices,"
   https://baymard.com/blog/handling-accidental-taps-on-touch-devices,
   verified 2026-08-23.
4. Nielsen Norman Group, "Cancel vs Close: Design to Distinguish the
   Difference," https://www.nngroup.com/articles/cancel-vs-close/, verified
   2026-08-23.
5. Google, "Send or unsend Gmail messages,"
   https://support.google.com/mail/answer/2819488, verified 2026-08-23.
6. Google, "Snackbar," Material Design 3,
   https://m3.material.io/components/snackbar/specs, verified 2026-08-23.
7. Android Developers, "Snackbar," Jetpack Compose,
   https://developer.android.com/develop/ui/compose/components/snackbar,
   verified 2026-08-23.
8. World Wide Web Consortium, "Understanding Success Criterion 2.2.1: Timing
   Adjustable," https://www.w3.org/WAI/WCAG21/Understanding/timing-adjustable.html,
   verified 2026-08-23.
9. World Wide Web Consortium, "Understanding Success Criterion 4.1.3: Status
   Messages," https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html,
   verified 2026-08-23.
10. MUI, "React Snackbar component," https://mui.com/material-ui/react-snackbar/,
    verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of an undo manager driving a
reversal-based optimistic undo, holding one pending action at a time, timing
its window, and reverting on demand rather than committing on expiry.

```typescript
interface PendingUndo<T> {
  id: string;
  revert: () => Promise<void>;
  commit: () => Promise<void>;
  windowMs: number;
}

type UndoState = "idle" | "pending" | "reverted" | "committed";

class UndoManager<T> {
  private state: UndoState = "idle";
  private timer: ReturnType<typeof setTimeout> | null = null;
  private pending: PendingUndo<T> | null = null;

  offer(pending: PendingUndo<T>): void {
    this.pending = pending;
    this.state = "pending";
    this.timer = setTimeout(() => {
      void this.expire();
    }, pending.windowMs);
  }

  async undo(): Promise<boolean> {
    if (this.state !== "pending" || !this.pending) {
      return false;
    }
    if (this.timer) clearTimeout(this.timer);
    await this.pending.revert();
    this.state = "reverted";
    this.pending = null;
    return true;
  }

  private async expire(): Promise<void> {
    if (this.state !== "pending" || !this.pending) {
      return;
    }
    await this.pending.commit();
    this.state = "committed";
    this.pending = null;
  }

  currentState(): UndoState {
    return this.state;
  }
}
```

```python
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class UndoState(Enum):
    IDLE = "idle"
    PENDING = "pending"
    REVERTED = "reverted"
    COMMITTED = "committed"


@dataclass
class PendingUndo(Generic[T]):
    id: str
    revert: Callable[[], Awaitable[None]]
    commit: Callable[[], Awaitable[None]]
    window_seconds: float


class UndoManager(Generic[T]):
    def __init__(self) -> None:
        self.state = UndoState.IDLE
        self._pending: Optional[PendingUndo[T]] = None
        self._task: Optional[asyncio.Task] = None

    def offer(self, pending: PendingUndo[T]) -> None:
        self._pending = pending
        self.state = UndoState.PENDING
        self._task = asyncio.create_task(self._expire_after(pending.window_seconds))

    async def undo(self) -> bool:
        if self.state != UndoState.PENDING or self._pending is None:
            return False
        if self._task:
            self._task.cancel()
        await self._pending.revert()
        self.state = UndoState.REVERTED
        self._pending = None
        return True

    async def _expire_after(self, delay: float) -> None:
        await asyncio.sleep(delay)
        if self.state != UndoState.PENDING or self._pending is None:
            return
        await self._pending.commit()
        self.state = UndoState.COMMITTED
        self._pending = None
```

```go
package undo

import (
	"context"
	"sync"
	"time"
)

type State int

const (
	Idle State = iota
	Pending
	Reverted
	Committed
)

type PendingUndo struct {
	ID       string
	Revert   func(ctx context.Context) error
	Commit   func(ctx context.Context) error
	Window   time.Duration
}

type Manager struct {
	mu      sync.Mutex
	state   State
	pending *PendingUndo
	cancel  context.CancelFunc
}

func NewManager() *Manager {
	return &Manager{state: Idle}
}

func (m *Manager) Offer(ctx context.Context, p *PendingUndo) {
	m.mu.Lock()
	m.pending = p
	m.state = Pending
	timerCtx, cancel := context.WithCancel(ctx)
	m.cancel = cancel
	m.mu.Unlock()

	go func() {
		select {
		case <-time.After(p.Window):
			m.expire(timerCtx)
		case <-timerCtx.Done():
			return
		}
	}()
}

func (m *Manager) Undo(ctx context.Context) (bool, error) {
	m.mu.Lock()
	if m.state != Pending || m.pending == nil {
		m.mu.Unlock()
		return false, nil
	}
	p := m.pending
	cancel := m.cancel
	m.mu.Unlock()

	cancel()
	if err := p.Revert(ctx); err != nil {
		return false, err
	}

	m.mu.Lock()
	m.state = Reverted
	m.pending = nil
	m.mu.Unlock()
	return true, nil
}

func (m *Manager) expire(ctx context.Context) {
	m.mu.Lock()
	if m.state != Pending || m.pending == nil {
		m.mu.Unlock()
		return
	}
	p := m.pending
	m.mu.Unlock()

	_ = p.Commit(ctx)

	m.mu.Lock()
	m.state = Committed
	m.pending = nil
	m.mu.Unlock()
}
```
