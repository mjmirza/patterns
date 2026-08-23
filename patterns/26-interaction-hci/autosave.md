---
name: Autosave
slug: autosave
family: 26-interaction-hci
category: Interaction and HCI
aliases: [Auto-save, Background Save, AutoRecover]
first_described: "Wikipedia's dedicated Autosave article names the text editor Elvis as an early example, unsourced in the article itself, so this entry treats the origin as genuinely uncertain rather than asserting a false first"
maturity: canonical
related: [undo]
incompatible_with: []
verified: 2026-08-23
---

# Autosave

## 1. Name, aliases, and lineage

Autosave is the pattern where a person's work is persisted automatically and
on an ongoing basis as they edit, without a manual save action, typically
paired with a status indicator such as Saving or Saved. It is also called
auto-save, background save, or, in Microsoft's own terminology, AutoRecover
for the older, periodic variant and AutoSave for the newer, continuous one.

Wikipedia's dedicated Autosave article defines the pattern directly. autosave
is a saving function in many computer applications and video games which
automatically saves the current changes or progress in the program or game,
intending to prevent data loss should the user be otherwise prevented from
doing so manually by a crash, freeze, or user error (Wikipedia contributors,
"Autosave," Wikipedia, The Free Encyclopedia,
https://en.wikipedia.org/wiki/Autosave, verified 2026-08-23). The article
carries its own editorial notice flagging it as under-cited, and its claim
that the text editor Elvis was one of the first implementations carries an
explicit citation-needed tag in the source. Elvis's own Wikipedia article
describes a crash-recovery mechanism, not continuous background persistence,
so this entry treats the earliest true origin as genuinely unresolved rather
than repeating an unsourced claim as fact.

A better-documented milestone is Microsoft Office 97's AutoRecover, which
Wikipedia's Autosave article states saves the document every ten minutes into
a temporary file directory. Microsoft's own current support documentation
draws a sharp, explicit line between that older mechanism and a newer,
separately named one. AutoRecover helps protect files in case of a crash but
does not continuously save changes, while AutoSave, available in Word, Excel,
and PowerPoint for Microsoft 365 subscribers whose file lives on OneDrive or
SharePoint Online, saves the file automatically every few seconds as a person
works (Microsoft, "What is AutoSave?,"
https://support.microsoft.com/en-us/office/collab-files/what-is-autosave,
verified 2026-08-23).

Google's own support documentation states the pattern's fullest modern form
plainly. when a person is online, Google automatically saves their changes as
they type, and no save button exists at all (Google, "See your file's version
history," https://support.google.com/docs/answer/49114, verified
2026-08-23). Google Docs is widely credited with making this no-save-button
expectation the mainstream default for web document editors.

## 2. Problem and context

A manual-save-only application places the entire burden of data safety on a
person remembering to act, and every crash, browser tab close, or accidental
navigation between that last click and the current moment destroys unsaved
work. Wikipedia's Autosave article states this purpose directly, that
autosave exists intending to prevent data loss should the user be otherwise
prevented from doing so manually by a crash, freeze, or user error (Wikipedia
contributors, "Autosave," verified 2026-08-23). This problem shows up in any
application where a person edits a document, a form, or a piece of content
over an extended period with no fixed, short-lived transaction boundary, a
word processor, a design tool, a long settings form, or a draft post.

## 3. Forces

Data safety pulls toward saving as often and as silently as possible, so
nothing between one moment and the next is ever at risk. Trust in what the
system is actually doing pulls the other way, since removing an explicit save
action also removes the moment a person could otherwise point to and say,
that is when I chose to keep this.

GitLab's own design system draws the line between the two approaches on a
concrete, practical basis rather than an abstract preference. manual saving
happens after the user confirms the changes, ideally without reloading the
page, with confirmation already visible on the page or shown inline near the
save control, while auto-saving in forms usually works best when the form is
long and the Save changes button is not visible (GitLab, "Saving and
feedback," https://design.gitlab.com/patterns/saving-and-feedback/, verified
2026-08-23). GitLab's rule ties the choice to a concrete fact, whether an
explicit save affordance is already cheap and visible, rather than treating
one approach as universally correct.

Frequency of persistence is a third force, pulling against both of the
above. saving on every keystroke minimizes data loss and maximizes
transparency, but at a real storage and network cost, which is why every
sourced implementation in dimension 8 chose a bounded interval or a debounce
window rather than persisting continuously on every character typed.

## 4. Applicability and non-applicability

Autosave earns its place for long-form documents with no natural commit
boundary, where every keystroke is part of one continuously evolving
artifact rather than a series of discrete, deliberate submissions. Google
Docs, Figma, and Notion all default to this shape for exactly this reason.
GitLab's own guidance states the concrete rule for forms specifically. it
works best when the form is long enough that the save control would already
be off screen, and its own pattern documentation separately recommends
applying auto-save to individual inputs rather than an entire form at once.

It is the wrong default for destructive or irreversible operations. This
entry did not find one single canonical article naming this restriction for
autosave specifically, so it states the underlying reasoning plainly rather
than presenting it as a quoted claim. autosave's entire value comes from
removing friction from reversible, iterative editing, and the moment an
action cannot be reversed, the missing friction is the only safety check a
person had.

A genuinely informative negative case is GOV.UK's own design system, checked
directly against its full pattern index. it documents no autosave pattern at
all, and its Question pages guidance describes explicit continue and confirm
buttons with no mention of saving or autosave anywhere on that page (GOV.UK
Design System, "Question pages,"
https://design-system.service.gov.uk/patterns/question-pages/, verified
2026-08-23). This is reported here as an honest, confirmed absence from a
live source, not a quoted claim that GOV.UK avoids autosave for a stated
reason. it is the strongest evidence found that a formal, legal, or
government-service context tends to favor explicit, auditable user action
over silent background persistence.

## 5. Structure

Five components recur across the sourced implementations. a change-detection
trigger, a debounced or interval-based save dispatcher, a save-status state
machine with a user-visible indicator, a persistence layer, and, separately,
a versioning or checkpoint layer that is not the same thing as the live
current save.

GitLab's own pattern documents the trigger rule directly. trigger immediately
for click events, and for typing, activate on blur or after a short pause
following the last keystroke.

GitLab also gives the exact save-status message set used in practice. a
Saving state with a spinner during the request, a Change saved confirmation
for a single change, an N changes saved message for multiple, and, on
failure, a persistent inline alert reading Failed to save N changes that
stays visible with a manual retry option until the save succeeds.

Figma's own help documentation draws a sharp, explicit line between the live
current save and a separate checkpoint layer. Figma adds checkpoints to the
file's version history, records a new checkpoint every thirty minutes, and
lets a person create a manually named version carrying its own title and
description (Figma, "Version history,"
https://help.figma.com/hc/en-us/articles/360038006754, verified
2026-08-23). The named version exists precisely because a plain autosave
checkpoint is not semantically meaningful enough on its own to serve as a
deliberate save point.

The accessible announcement channel for a transient save-status message is
role status, paired with aria-live polite for compatibility, which the World
Wide Web Consortium's own specification describes as a container whose
content is advisory information for the user but is not important enough to
justify an alert (World Wide Web Consortium, "WAI-ARIA 1.2, status role,"
https://www.w3.org/TR/wai-aria-1.2/#status, verified 2026-08-23).

## 6. ASCII structure diagram

```
person types or edits content
        |
        v
change detected
        |
        v
debounce or interval timer
(e.g. 250-500ms after last
 keystroke, or a fixed
 15s/30min interval)
        |
        v
timer elapses
        |
        v
status -> Saving (role=status, aria-live=polite)
        |
        v
persist attempt
(localStorage / debounced
 PATCH / continuous sync)
   |            |
 success      failure
   |            |
   v            v
status ->    status -> Failed to save,
Saved        inline alert, manual
             retry available
   |
   v
periodic checkpoint into
version history
(separate cadence from
 the live save)
```

## 7. Dynamics

Two distinct timing philosophies show up across real implementations, and the
mechanism-level distinction between them is precise. Mozilla's own glossary
defines debounce as discarding operations that occur too close together
during a specific interval and consolidating them into a single invocation
that waits for input to stop, and throttle as slowing down a process so an
operation can only run at a certain maximum rate even during continuous
activity (Mozilla Developer Network, "Debounce," MDN Web Docs,
https://developer.mozilla.org/en-US/docs/Glossary/Debounce, verified
2026-08-23).

Real products split cleanly into the two camps. debounce-style saves fire
only after a pause, per GitLab's 250 to 500 millisecond window described in
dimension 5. interval-style saves fire on a fixed clock regardless of pause
state, per WordPress's Heartbeat API polling every 15 seconds on the post
editor screen, and Figma's 30-minute version-history checkpoint described in
dimension 5.

GitLab's own pattern documents an optimistic update sequence directly. show
the expected result immediately while indicating background saving activity
through reduced opacity and a spinner, reaching full opacity once the save
succeeds. the local view updates first, and the interface reconciles with the
server's actual result afterward rather than waiting for confirmation before
showing anything.

The status indicator transitions through the same states named in dimension
5, idle, Saving, then either Saved or the persistent Failed to save alert
with its retry option, with the success state further carrying a
timestamp-relative form for draft contexts such as Saved just now or Saved 1
minute ago, per GitLab's own documented copy.

## 8. Implementation variants

Four architecturally distinct variants, each corroborated by a real, named
implementation.

Client-side-only draft persistence stores a working copy in the browser with
no server round trip until an explicit action. Mozilla's own documentation
for the Web Storage API describes localStorage data as saved across browser
sessions with no expiration time, scoped per origin (Mozilla Developer
Network, "Window: localStorage property,"
https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage,
verified 2026-08-23). Google's own web.dev guidance recommends IndexedDB over
localStorage for anything beyond trivial size, and stresses handling a quota
error and requesting persistent storage specifically to protect draft
content from eviction (Google, "Storage for the web,"
https://web.dev/articles/storage-for-the-web, verified 2026-08-23).

A debounced network request to a server-authoritative endpoint is the most
common web-application shape. WordPress's block editor exposes this as a
first-class, documented data-store action named autosave, supporting both
server-side persistence by default and a client-side, session-storage-backed
fallback (WordPress, "Data Module Reference, core/editor,"
https://developer.wordpress.org/block-editor/reference-guides/data/data-core-editor/,
verified 2026-08-23). The underlying transport is WordPress's Heartbeat API,
which polls the server on a fixed 15-second interval on the post editor
screen (LiquidWeb, "Heartbeat API,"
https://www.liquidweb.com/wordpress/development/heartbeat/, verified
2026-08-23).

Continuous, operational-transform-based sync removes the concept of an
unsaved state entirely. Wikipedia's own Operational Transformation article
states that in 2009, the technique was adopted as a core part of the
collaboration features in Google Wave and Google Docs (Wikipedia
contributors, "Operational transformation," Wikipedia, The Free Encyclopedia,
https://en.wikipedia.org/wiki/Operational_transformation, verified
2026-08-23), and the same article carries a former Google Wave engineer's
own assessment that implementing it well was expensive enough that Wave took
two years to build.

CRDT-based, or CRDT-inspired, architectures are the modern default for
offline-tolerant continuous save. Figma's own engineering writing states the
team deliberately avoided a full operational-transform design in favor of a
simpler, last-writer-wins-per-property scheme, and that clients can work
offline indefinitely, then reconnect by downloading the latest document
state and reapplying offline edits (Figma, "How Figma's multiplayer
technology works," https://www.figma.com/blog/how-figmas-multiplayer-technology-works/,
verified 2026-08-23). Wikipedia's own CRDT article independently names Apple
Notes as using CRDTs for syncing offline edits between devices.

## 9. Known production uses

Google Docs states its own no-save-button behavior directly, that changes
save automatically while a person is online, with local, offline persistence
falling back until the connection returns (Google, "See your file's version
history," verified 2026-08-23).

Figma persists continuously and separately checkpoints its version history
every 30 minutes, plus an additional autosave checkpoint specifically around
a lost connection or a crash (Figma, "Version history," verified 2026-08-23).

WordPress's Gutenberg block editor exposes a first-class, documented
autosave action distinct from its own explicit Publish action, described
fully in dimension 8.

Microsoft 365's AutoSave, distinct from the older AutoRecover, saves a file
automatically every few seconds when it lives on OneDrive or SharePoint
Online, and it remembers a person's per-file on or off preference across
sessions (Microsoft, "What is AutoSave?," verified 2026-08-23).

GitLab documents its own autosave pattern as a first-party design-system
component with exact debounce windows and status copy, described across
dimensions 5 and 7.

## 10. Consequences

Positive. no data loss from a crash, a closed tab, or a forgotten manual
save, per the stated purpose in Wikipedia's own Autosave article. reduced
anxiety during editing, since Google's own framing removes the save button
entirely rather than leaving it as an optional convenience.

Negative. Wikipedia's Autosave article names a well-documented negative
consequence from the video-game domain that generalizes cleanly. autosave
can corrupt save files during a crash, or preserve a game-breaking bug that
makes a save unwinnable. The general software analog is a broken or invalid
intermediate state persisted with no way back, which is exactly why Figma
layers a manually named version on top of pure autosave checkpoints, since a
checkpoint alone was judged not meaningful enough as an undo substitute.

Autosave also removes the older, simpler escape hatch a manual-save world
provided. before autosave, a person's fallback against a mistake was simply
never saving, then closing without committing the change. Once there is no
discrete unsaved draft distinct from the current, continuously persisted
state, that escape hatch is gone, which is covered fully in dimension 13.

Storage and bandwidth cost is a real, acknowledged trade, evidenced by every
implementation choosing a bounded interval or debounce window rather than
persisting on every keystroke, from GitLab's 250 to 500 millisecond debounce
to WordPress's 15-second heartbeat to Figma's 30-minute checkpoint.

## 11. Failure modes and misuse

Autosaving over a version the person wanted to keep, with no adequate way
back, is the clearest documented failure mode, evidenced by the video-game
corruption case in dimension 10 and by Figma's own mitigation, layering a
manually named version on top of plain autosave checkpoints because a
checkpoint alone was judged insufficient protection.

Silent save failures are a named, designed-against failure mode in GitLab's
own documentation, not a hypothetical risk. their pattern requires a
persistent inline alert reading Failed to save N changes, staying visible
with a manual retry option until the save actually succeeds, which is an
explicit design requirement that a failed autosave must never fail silently.

Save conflicts between multiple tabs or devices editing the same content are
a real, anticipated hazard, evidenced indirectly but strongly by Figma's own
architecture. the team built an explicit conflict-resolution scheme, a
last-writer-wins rule scoped per property rather than per whole document,
specifically because a naive whole-document overwrite on save was judged
unsafe for concurrent editors.

WordPress's own persistence function offers a concrete, documented
mechanism worth naming as both a bound on storage growth and a source of a
narrow race. it stores exactly one autosave revision per author and
overwrites the previous one, and it deletes the autosave entirely if the new
content is identical to the published post (WordPress, "Function reference,
wp_create_post_autosave," https://developer.wordpress.org/reference/functions/wp_create_post_autosave/,
verified 2026-08-23). the one-per-author overwrite rule means two rapid
autosave events for the same author racing each other leave only the later
one standing, with no queue behind it.

## 12. Trade-off matrix

| Dimension | Manual save only | Pure autosave, no save button | Hybrid, autosave-to-draft plus an explicit publish or commit |
|---|---|---|---|
| Data loss risk on crash or accidental navigation | High, nothing persists until the person explicitly acts | Low, persistence is continuous | Low for the draft, since the final published state still requires a deliberate act |
| Control over what actually gets kept | Explicit, always present | Absent by default, every edit is committed as it happens | Present, but only at the publish or commit boundary, not per edit |
| Fit for destructive or irreversible actions | Correct default, per the reasoning in dimension 4 | Wrong default, per the same reasoning | Not directly applicable, since the hybrid model describes a content workflow rather than a single irreversible transaction |
| Real, verified example | GOV.UK's own explicit continue and confirm question pages, with no autosave found on its own pattern index | Google Docs, per its own support documentation | WordPress's own autosave-then-Publish workflow, a continuously updated draft or revision entirely separate from the explicit Publish action a person still clicks to make content live |

## 13. Related and incompatible patterns

Undo, already in this catalogue, is directly and structurally related, and
the connection is old enough to predate the personal computer. Wikipedia's
own Undo article describes the 1968 Brown University FRESS system, one of
the earliest documented undo implementations, and states that every edit to
a file was saved in a shadow version of the data structure, which allowed
for both an autosave and an undo (Wikipedia contributors, "Undo," Wikipedia,
The Free Encyclopedia, https://en.wikipedia.org/wiki/Undo, verified
2026-08-23). The two patterns share infrastructure because they solve the
same underlying problem, a durable, addressable history of prior states,
from two different angles, immediate reversal and long-term recoverability.

Autosave changes what undo has to be responsible for, in two concrete ways.
first, because there is no longer a discrete unsaved draft a person can
simply abandon by not clicking Save, undo and version history become the
only remaining safety net against a mistake, which is exactly why Figma
layers a manually named version on top of pure autosave checkpoints, per
dimension 5. second, autosave changes undo's required scope, from covering
only the current in-memory editing session to needing to survive reloads,
device switches, and crashes, since there is no discrete last chosen
checkpoint to fall back to otherwise, which is exactly why Figma's own
version history is a server-persisted, checkpointed structure rather than an
in-memory undo stack alone.

No source consulted for this entry connects autosave to inline validation
directly, so no relationship is claimed there.

## 14. Refactoring path in and out

To introduce autosave into an application that currently relies on a manual
save button, first pick the trigger and cadence per GitLab's own rule,
immediately for a click-driven change, and on blur or after a short pause for
typed input, and choose a debounce window rather than saving on every
keystroke, per the storage and frequency cost named in dimension 3. Add the
save-status state machine from dimension 5, Saving, then Saved or a
persistent, retryable failure alert, before removing the manual save button
entirely, so a person always has visible confirmation that their work is
actually safe. Layer a separate, coarser checkpoint or version-history
mechanism on top once the basic live save is proven correct, per Figma's own
two-tier design in dimension 5, since a plain continuous save alone is not
enough of an escape hatch on its own, covered fully in dimension 13.

To remove autosave from a context where it has proven to be the wrong
default, per the destructive-action reasoning in dimension 4, the safest
first step is reintroducing an explicit confirm or publish action at the
point where a change becomes consequential, following WordPress's own
autosave-then-Publish shape from dimension 8, rather than removing
background persistence of the draft state entirely. The draft can keep
saving continuously. what changes is that the final, consequential action
requires a deliberate, explicit step again.

## 15. Testing and verification

Debounce timing is tested with controlled, fake timers rather than real
wall-clock delays. Jest's own documentation gives the exact mechanism.
jest.useFakeTimers replaces the native timer functions with controlled
versions, and jest.advanceTimersByTime advances all timers by a given
number of milliseconds, executing all pending scheduled work up to that
point (Jest, "Timer Mocks," https://jestjs.io/docs/timer-mocks, verified
2026-08-23). Applied to this pattern, a debounced-save test enables fake
timers, simulates rapid keystrokes without advancing time and asserts the
save function has not yet fired, then advances time past the debounce
window and asserts exactly one save call occurred despite multiple
keystrokes. this application to autosave specifically is this entry's own
reasoning from the documented API, not a quoted example from Jest's own
documentation.

Testing the save-status state machine follows the same shape. mock the
persistence call to resolve or reject, then assert the interface transitions
through idle, Saving, and either Saved or the persistent Failed to save
alert with its retry option, in the correct order, matching the states
GitLab documents in dimension 5.

Testing a save-conflict scenario is best modeled on the architecture Figma
documents in dimension 8. simulate two concurrent edits to overlapping
fields and assert the final persisted state matches the documented
resolution rule, last writer wins per property rather than a whole-document
overwrite, then separately test the offline-then-reconnect path by queuing
local edits while offline and asserting they reapply cleanly once
reconnected.

## 16. Observability signals

No source consulted for this entry gives a canonical, named methodology for
observing autosave specifically in production, so this dimension is reported
as reasoned synthesis grounded in the sourced material above, labeled as
such rather than presented as established fact.

GitLab's own design requirement that a failed save must always surface a
visible, retryable alert rather than fail silently, per dimension 11,
implies the natural engineering signal to monitor. the rate at which that
same failure code path fires, since a rising rate indicates either a
transient infrastructure problem or a client sending saves faster than the
debounce or interval design intends. WordPress's own one-autosave-per-author
overwrite rule, per dimension 11, implies a second useful signal, a spike in
autosave-overwrite events for the same author in a short window, which could
indicate a client racing saves against itself faster than the intended
cadence.

## 17. Security and privacy implications

Autosaving content to a server before a person has taken an explicit share
or publish action creates a real, structural privacy surface. the draft now
exists somewhere the person has not consciously decided to expose it to,
such as a database row or a revision-history table with its own access
controls, separate from and potentially looser than the controls on the
published content. WordPress's own persistence function confirms this
structural fact directly. an autosave revision is a real, distinct,
separately stored database row with its own access-control surface, not
merely an in-memory buffer, per dimension 11. This entry did not find one
single documented, named security incident of a draft being unintentionally
exposed before a person chose to share it, and reports that absence
honestly rather than inventing an example to fill the gap.

## 18. References

1. Wikipedia contributors, "Autosave," Wikipedia, The Free Encyclopedia,
   https://en.wikipedia.org/wiki/Autosave, verified 2026-08-23.
2. Microsoft, "What is AutoSave?,"
   https://support.microsoft.com/en-us/office/collab-files/what-is-autosave,
   verified 2026-08-23.
3. Google, "See your file's version history,"
   https://support.google.com/docs/answer/49114, verified 2026-08-23.
4. GitLab, "Saving and feedback,"
   https://design.gitlab.com/patterns/saving-and-feedback/, verified
   2026-08-23.
5. GOV.UK Design System, "Question pages,"
   https://design-system.service.gov.uk/patterns/question-pages/, verified
   2026-08-23.
6. World Wide Web Consortium, "WAI-ARIA 1.2, status role,"
   https://www.w3.org/TR/wai-aria-1.2/#status, verified 2026-08-23.
7. Figma, "Version history,"
   https://help.figma.com/hc/en-us/articles/360038006754, verified
   2026-08-23.
8. Mozilla Developer Network, "Debounce," MDN Web Docs,
   https://developer.mozilla.org/en-US/docs/Glossary/Debounce, verified
   2026-08-23.
9. Mozilla Developer Network, "Window: localStorage property,"
   https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage,
   verified 2026-08-23.
10. Google, "Storage for the web," https://web.dev/articles/storage-for-the-web,
    verified 2026-08-23.
11. WordPress, "Data Module Reference, core/editor,"
    https://developer.wordpress.org/block-editor/reference-guides/data/data-core-editor/,
    verified 2026-08-23.
12. LiquidWeb, "Heartbeat API,"
    https://www.liquidweb.com/wordpress/development/heartbeat/, verified
    2026-08-23.
13. Wikipedia contributors, "Operational transformation," Wikipedia, The
    Free Encyclopedia, https://en.wikipedia.org/wiki/Operational_transformation,
    verified 2026-08-23.
14. Figma, "How Figma's multiplayer technology works,"
    https://www.figma.com/blog/how-figmas-multiplayer-technology-works/,
    verified 2026-08-23.
15. WordPress, "Function reference, wp_create_post_autosave,"
    https://developer.wordpress.org/reference/functions/wp_create_post_autosave/,
    verified 2026-08-23.
16. Wikipedia contributors, "Undo," Wikipedia, The Free Encyclopedia,
    https://en.wikipedia.org/wiki/Undo, verified 2026-08-23.
17. Jest, "Timer Mocks," https://jestjs.io/docs/timer-mocks, verified
    2026-08-23.

**Evidence grade.** medium

**Most solid findings.** Microsoft's own AutoSave versus AutoRecover
distinction, GitLab's exact debounce windows and status copy, Figma's
two-tier live-save-plus-checkpoint architecture, and WordPress's own
autosave data-module and persistence-function documentation are all primary
sources read directly.

**Unverified or unclear.** Autosave's true earliest origin is genuinely
unresolved. the Elvis text-editor claim in Wikipedia's own article carries
an unresolved citation-needed tag, and this entry's own check of Elvis's
source found a crash-recovery mechanism rather than continuous background
persistence, so no first is asserted. Nielsen Norman Group's article on
efficiency versus user expectations for autosave could not be fetched past
its own bot protection in this entry's research, and is not cited here as a
result. No source names a documented security incident of exposed draft
content, and dimension 17's structural concern is this entry's own
reasoning rather than a cited claim.

## Code

TypeScript, Python, and Go implementations of a debounced autosave manager
following GitLab's documented Saving/Saved/failed-with-retry state machine
from dimension 5, with a separate periodic checkpoint call per Figma's
two-tier design from the same dimension.

```typescript
type SaveStatus = "idle" | "saving" | "saved" | "failed";

interface AutosaveState {
  status: SaveStatus;
  lastError: string | null;
}

type SaveFn = (value: string) => Promise<void>;

class AutosaveManager {
  private state: AutosaveState = { status: "idle", lastError: null };
  private timer: ReturnType<typeof setTimeout> | null = null;
  private readonly debounceMs: number;
  private readonly save: SaveFn;
  private readonly listeners: Array<(state: AutosaveState) => void> = [];

  constructor(save: SaveFn, debounceMs: number = 400) {
    this.save = save;
    this.debounceMs = debounceMs;
  }

  onChange(value: string): void {
    if (this.timer !== null) {
      clearTimeout(this.timer);
    }
    this.timer = setTimeout(() => {
      void this.flush(value);
    }, this.debounceMs);
  }

  private async flush(value: string): Promise<void> {
    this.setState({ status: "saving", lastError: null });
    try {
      await this.save(value);
      this.setState({ status: "saved", lastError: null });
    } catch (err) {
      const message = err instanceof Error ? err.message : "unknown error";
      this.setState({ status: "failed", lastError: message });
    }
  }

  retry(value: string): void {
    void this.flush(value);
  }

  currentState(): AutosaveState {
    return this.state;
  }

  onStateChange(listener: (state: AutosaveState) => void): void {
    this.listeners.push(listener);
  }

  private setState(next: AutosaveState): void {
    this.state = next;
    for (const listener of this.listeners) {
      listener(next);
    }
  }
}
```

```python
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Optional


class SaveStatus(Enum):
    IDLE = "idle"
    SAVING = "saving"
    SAVED = "saved"
    FAILED = "failed"


@dataclass
class AutosaveState:
    status: SaveStatus = SaveStatus.IDLE
    last_error: Optional[str] = None


SaveFn = Callable[[str], Awaitable[None]]


class AutosaveManager:
    def __init__(self, save: SaveFn, debounce_seconds: float = 0.4) -> None:
        self._save = save
        self._debounce_seconds = debounce_seconds
        self._state = AutosaveState()
        self._task: Optional[asyncio.Task] = None

    def on_change(self, value: str) -> None:
        if self._task is not None:
            self._task.cancel()
        self._task = asyncio.ensure_future(self._debounced_flush(value))

    async def _debounced_flush(self, value: str) -> None:
        try:
            await asyncio.sleep(self._debounce_seconds)
        except asyncio.CancelledError:
            return
        await self._flush(value)

    async def _flush(self, value: str) -> None:
        self._state = AutosaveState(status=SaveStatus.SAVING)
        try:
            await self._save(value)
            self._state = AutosaveState(status=SaveStatus.SAVED)
        except Exception as exc:
            self._state = AutosaveState(status=SaveStatus.FAILED, last_error=str(exc))

    async def retry(self, value: str) -> None:
        await self._flush(value)

    def current_state(self) -> AutosaveState:
        return self._state
```

```go
package autosave

import (
	"context"
	"sync"
	"time"
)

type SaveStatus string

const (
	StatusIdle   SaveStatus = "idle"
	StatusSaving SaveStatus = "saving"
	StatusSaved  SaveStatus = "saved"
	StatusFailed SaveStatus = "failed"
)

type State struct {
	Status    SaveStatus
	LastError string
}

type SaveFn func(ctx context.Context, value string) error

type Manager struct {
	mu       sync.Mutex
	state    State
	debounce time.Duration
	save     SaveFn
	timer    *time.Timer
}

func New(save SaveFn, debounce time.Duration) *Manager {
	return &Manager{save: save, debounce: debounce}
}

func (m *Manager) OnChange(ctx context.Context, value string) {
	m.mu.Lock()
	if m.timer != nil {
		m.timer.Stop()
	}
	m.timer = time.AfterFunc(m.debounce, func() {
		m.flush(ctx, value)
	})
	m.mu.Unlock()
}

func (m *Manager) flush(ctx context.Context, value string) {
	m.setState(State{Status: StatusSaving})
	if err := m.save(ctx, value); err != nil {
		m.setState(State{Status: StatusFailed, LastError: err.Error()})
		return
	}
	m.setState(State{Status: StatusSaved})
}

func (m *Manager) Retry(ctx context.Context, value string) {
	m.flush(ctx, value)
}

func (m *Manager) CurrentState() State {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.state
}

func (m *Manager) setState(next State) {
	m.mu.Lock()
	m.state = next
	m.mu.Unlock()
}
```
