---
name: Bulk Action
slug: bulk-action
family: 26-interaction-hci
category: Interaction and HCI
aliases: [Batch Actions, Multi-Select Actions, Mass Action]
first_described: "Google Material Design's Selection pattern, archived at m1.material.io, circa 2014, for the checkbox-selection mechanics; the term batch actions is IBM Carbon's own naming for the same shape"
maturity: established
related: [undo]
incompatible_with: []
verified: 2026-08-23
---

# Bulk Action

## 1. Name, aliases, and lineage

Bulk action is the pattern where a person selects several items in a list,
table, or grid, typically via a checkbox per row or a range select, and then
applies one action to all of them at once through a contextual toolbar that
appears once at least one item is selected. It is also called batch actions,
multi-select actions, or, in Salesforce's own terminology, mass action.

There is no single credited inventor, and no dedicated Wikipedia article
exists for the pattern. Wikipedia's own Batch processing article is a real,
substantial page, but it describes an unrelated computing concept, the
running of a software job in an automated and unattended way, covering job
schedulers and unattended data pipelines rather than a person selecting
items in an interface (Wikipedia contributors, "Batch processing," Wikipedia,
The Free Encyclopedia, https://en.wikipedia.org/wiki/Batch_processing,
verified 2026-08-23).

The earliest documented, named design-system treatment found for this entry
is Google's Material Design Selection pattern, archived at its original
location. a long press, touch, or held mousedown reveals a per-item
checkbox on hover, and once any item is selected, checkboxes for every
remaining item in that set become visible too (Google, "Selection,"
Material Design, https://m1.material.io/patterns/selection.html, verified
2026-08-23).

Android's own developer documentation names the toolbar itself, the
contextual action bar, as a first-class platform concept. the contextual
action mode is a system implementation that focuses user interaction toward
performing contextual actions, and when a user selects an item, a
contextual action bar appears at the top of the screen to present actions
the user can perform on the selected items, with a separate note that this
mechanism supports batch contextual actions on groups of items (Android
Developers, "App bars,"
https://developer.android.com/develop/ui/views/components/menus, verified
2026-08-23).

IBM's Carbon Design System independently names the same concept batch
actions, and ships a dedicated component for it in its React
implementation, though this entry could not directly verify Carbon's own
prose guidance, since its documentation pages render client side and no
usable body text could be retrieved.

## 2. Problem and context

Applying the same operation to many similar items one at a time is
repetitive, and the more items a task touches, the more that repetition
costs. This problem shows up in any list, table, or grid a person manages at
volume, an inbox, a set of issues, a table of records, or a card board.

## 3. Forces

Repetition avoidance pulls toward letting one action apply as broadly as
possible. Google's own API design standard for batch methods states the
opposing force directly, framing it as a decision the API's own caller must
make. consider the perspective of the API consumer, and whether atomic
behavior is preferable for the given use case, even if it means a large
batch could fail due to issues with a single or a few entries (Google, "AIP
233: Batch methods: Create," https://google.aip.dev/233, verified
2026-08-23). the same tension exists one layer up, at the interface a person
actually clicks. the same broad selection that saves enormous repetition is
the exact selection that can apply a destructive action far beyond what was
visible on screen.

Trello's own documented cap on multi-select is real, sourced evidence that
this tension gets actively designed around rather than left theoretical.
Trello's support documentation caps both range select and discontiguous
multi-select at 20 cards, holding Shift and selecting two cards in a single
list with up to 20 cards between them, or holding a modifier key and
selecting up to 20 cards (Atlassian, "Move Cards or Lists," Trello Help
Center, https://support.atlassian.com/trello/docs/moving-cards-or-lists/,
verified 2026-08-23). a deliberate ceiling like this bounds the benefit of
the pattern in order to bound its risk.

## 4. Applicability and non-applicability

Bulk action earns its place when an operation is homogeneous and repetitive
across many similar items, tagging, archiving, moving, or exporting a set of
records that all need the identical treatment. Notion, Airtable, GitHub, and
Trello all fit this shape, described fully in dimension 9.

Google's own AIP-233 batch standard names the exact deciding factor for the
non-applicability case at the API layer. operations that are simple
passthrough database transactions should use an atomic operation, while
operations that manage complex resources should use partial success
operations. put differently, when every item genuinely needs individual
review or carries its own risk, uniform bulk treatment is not safe to
assume. Trello's own product is itself a documented non-applicability
signal. its native multi-select supports move only, with bulk delete or
bulk label and member assignment left to a separate, opt-in extension
rather than shipped as a core, native capability, which this entry reads as
an inference about risk tolerance from what Trello chose to ship natively
versus leave optional, not a directly stated design rationale.

## 5. Structure

Four components recur across the sourced implementations. a selection
mechanism, a selection count indicator, a contextual action bar, and the
action set itself.

Three selection variants are independently documented. a per-item checkbox
revealed on hover then persisted once any item is selected, per Material
Design's own pattern described in dimension 1, and matched by Notion's own
help documentation, hover over any row and click the checkbox that appears
next to it (Notion, "Use tables," https://www.notion.com/help/tables,
verified 2026-08-23). a shift-click range select plus a modifier-click
discontiguous select, documented identically down to the modifier keys by
Trello and by the World Wide Web Consortium's own multi-select listbox
pattern, which adds shift plus an arrow key to extend a selection while
moving focus, and a control-A shortcut to select every option in the list
(World Wide Web Consortium, "Listbox Pattern," WAI-ARIA Authoring Practices
Guide, https://www.w3.org/WAI/ARIA/apg/patterns/listbox/, verified
2026-08-23). and a two-stage select-all, select everything currently visible
first, then a distinct, second action to escalate to everything matching
the current view, covered fully in dimension 7.

The contextual action bar is most explicitly specified by Android's own
documentation, described in dimension 1, which states the bar carries a
close or done action, disappears when every item is deselected, and
operates independently of the app's normal top bar even though it visually
overtakes that position. The World Wide Web Consortium's own toolbar
pattern supplies the accessible grouping rationale for wrapping the action
bar's buttons together. use toolbar as a grouping element only if the group
contains three or more controls, consolidating several buttons into a
single tab stop with arrow-key navigation between them (World Wide Web
Consortium, "Toolbar Pattern," WAI-ARIA Authoring Practices Guide,
https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/, verified 2026-08-23).

A live selection count is not directly specified by any source with an
exact visual design, but its accessible mechanism is. an aria-live polite
region announces the changing count to assistive technology, with Mozilla's
own guidance carrying an important, easy-to-miss caveat. start with an
empty live region, then, in a separate step, change the content inside the
region, since the element must already exist in the document before its
content changes or the update will not be announced (Mozilla Developer
Network, "ARIA live regions,"
https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions,
verified 2026-08-23).

## 6. ASCII structure diagram

```
person browses list or table
        |
        v
clicks checkbox on item 1
(or shift/ctrl-click, or
 hover reveals it)
        |
        v
+----------------------------------+
| contextual action bar appears    |
| "1 selected"  [Action] [Action]  |
+----------------------------------+
        |
        v
selects more items, or escalates
"select all on page" to
"select all N matching this filter"
        |
        v
+----------------------------------+
| action bar count updates live    |
| "N selected"  [Action] [Action]  |
+----------------------------------+
        |
        v
person clicks one bulk action
        |
        v
   is it destructive?
        |
   +----+----+
   |         |
  yes        no
   |         |
   v         v
confirm    action applied
"Delete N   immediately, often
items?"     with an undo toast
   |
   v
confirmed
   |
   v
+----------------------------------+
| bulk action applied, one batch   |
| call or N sub-requests reported  |
| together                         |
+----------------------------------+
        |
        v
   any per-item failures?
        |
   +----+----+
   |         |
  yes        no
   |         |
   v         v
partial-    full-success toast
failure     "N items updated. Undo"
report
        |         |
        +----+----+
             |
             v
  selection cleared, action bar
  disappears, list re-renders
```

## 7. Dynamics

The sharpest, most consequential distinction in this pattern is between
selecting everything currently visible and selecting everything matching
the current view, and it is not a single binary toggle, it is a
progressive, two-stage escalation. this shape is documented via a
third-party explainer quoting Gmail's own interface copy directly, since
Google's own help pages for this specific mechanism could not be located.
clicking the header checkbox selects only the visible page, by default
Gmail displays 50 emails per page, then a distinct, second banner appears
reading select all conversations that match this search, letting a person
select every item matching a filter, beyond just what is currently on
screen (Mailmeteor, "How to select all emails in Gmail," secondary source,
verified via live fetch 2026-08-23). This entry treats this citation as
lower confidence than a primary Google source, since Google's own
documentation of the exact mechanic could not be independently confirmed.

The World Wide Web Consortium's own multi-select listbox pattern documents
the keyboard-level version of the identical escalation tension, offering
two competing interaction models for a stated reason. a recommended model
where plain arrow-key movement toggles selection is fast but risks losing a
selection accidentally, while an alternative model requiring a modifier key
held down to move focus without changing selection is safer but needs more
keystrokes (World Wide Web Consortium, "Listbox Pattern," verified
2026-08-23). the trade-off is the same one Gmail's escalation embodies at
the mouse-click layer. convenience and blast-radius protection pull in
opposite directions at every layer of this pattern, not only the click
layer.

## 8. Implementation variants

At the server layer, the sharpest documented design decision is whether a
batch operation must be atomic, all items succeed or none do, or whether it
may report partial success. Google's own AIP-233 standard is explicit and
strict for the fast path. synchronous batch create must be atomic, while
asynchronous batch create may support atomic or partial success (Google,
"AIP 233: Batch methods: Create," verified 2026-08-23). For the
partial-success case, the same standard specifies the exact wire-level
contract, a map keyed by the index of the request in the original array,
carrying the status of each failed item, with an explicit refinement that a
transient, server-retryable error must not appear there, since it does not
represent a permanent failure.

Two protocol-level shapes for carrying that per-item detail in one response
are documented and worth distinguishing carefully. Google Cloud Storage's
own Batch Requests bundle up to 100 individual calls into one multipart
request, with the response likewise multipart, one part per sub-request,
each carrying its own status code, and a sharp, directly stated caveat. a
set of N requests batched together counts toward usage limits as N
requests, not as one (Google, "Batch Requests," Google Cloud Storage
documentation, https://docs.cloud.google.com/storage/docs/batch, verified
2026-08-23). the HTTP 207 Multi-Status code, by contrast, is not a general
REST convention. Mozilla's own documentation states plainly that this
response is used exclusively in the context of WebDAV, and browsers
accessing web pages will never encounter this status code (Mozilla
Developer Network, "207 Multi-Status,"
https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/207,
verified 2026-08-23). a bulk endpoint reaching for a bare 207 response
without reading the WebDAV specification is reaching for the wrong tool.
Google's own bespoke, index-keyed status map is closer to what a modern
REST or gRPC bulk API actually uses in practice.

## 9. Known production uses

GitHub's own issue list supports bulk milestone assignment. select the
checkbox next to each item, then use the Milestone dropdown to apply it to
every checked item at once (GitHub, "Associating milestones with issues and
pull requests,"
https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/associating-milestones-with-issues-and-pull-requests,
verified 2026-08-23). GitHub's Projects table takes this a step further,
with a built-in undo directly documented. when a person makes a bulk change
in the table layout, GitHub displays the option to undo that change (GitHub,
"Editing items in your project,"
https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/editing-items-in-your-project,
verified 2026-08-23), and its multi-select mechanics match the World Wide
Web Consortium's listbox pattern closely, modifier-click, shift plus
up/down, shift-click to range, and click-and-drag.

Airtable's own documentation states the mechanism plainly. select the
checkboxes next to the records intended for deletion, then right-click and
select delete all selected records (Airtable, "Adding, duplicating, and
deleting Airtable records,"
https://support.airtable.com/docs/adding-duplicating-and-deleting-airtable-records,
verified 2026-08-23), and the same page states a real, documented native
limitation, bulk duplication is not supported, only a copy-and-paste
workaround into a fresh blank record.

Notion's own help documentation describes checkbox selection revealing a
menu to edit any of the selected rows' database properties at once, per
dimension 5. Gmail's select-all-matching-query mechanism, per dimension 7,
is the most consequential real-world instance of the risk this pattern
carries when scaled without care.

## 10. Consequences

Positive. the pattern spares a person the friction of repeating an identical
click sequence N times, and it spares an API caller the round-trip cost of N
separate requests, per Google's own AIP-233 batch standard, which exists
specifically to avoid issues with a single or a few entries forcing that
repetition.

Negative. the select-all trap named in dimension 7 is the clearest,
concrete risk. a click meant to act on what is visible on screen can, via a
second, deliberate escalation, apply to everything matching a filter,
however many items that spans. this entry could not locate a single, named,
documented incident narrative of someone losing real data this way, despite
a direct search, and reports that absence honestly rather than inventing an
anecdote. the mechanism's own documented existence, per dimension 7, is
evidence enough that the risk is real and designed for, even without a
named incident to point to.

## 11. Failure modes and misuse

No confirmation on a destructive bulk action is the most directly sourced
failure mode, at both the API and the interface layer. Google's AIP-233
mandates atomicity for the synchronous case specifically to prevent a
silently partial, destructive commit. at the interface layer, the World
Wide Web Consortium's own alertdialog pattern names the correct mechanism, a
modal dialog that interrupts the person's workflow to communicate an
important message and acquire a response, explicitly scoped to include
action confirmation prompts (World Wide Web Consortium, "Alert Dialog
Pattern," WAI-ARIA Authoring Practices Guide,
https://www.w3.org/WAI/ARIA/apg/patterns/alertdialog/, verified 2026-08-23).

Partial failures with unclear per-item feedback is the best documented
failure mode in this entry's research, sourced at the API layer two ways.
Amazon S3's own Batch Operations documentation states that a job can be
configured to generate a completion report describing the results of each
task performed by the job (Amazon Web Services, "Batch Operations basics,"
https://docs.aws.amazon.com/AmazonS3/latest/userguide/batch-ops.html,
verified 2026-08-23), and Google's AIP-233 supplies the equivalent
index-keyed failure map described in dimension 8. both exist precisely
because collapsing an N-item batch into a single success or fail boolean
discards the information a person or an administrator actually needs, which
item succeeded and which did not.

Losing selection state on an accidental page reload or filter change is a
plausible, commonly observed failure mode in real products, but this entry
found no source discussing it directly, and reports that gap honestly
rather than asserting it as a sourced fact.

## 12. Trade-off matrix

| Dimension | One-at-a-time action | Bulk action, select N then apply once | Select and preview before commit |
|---|---|---|---|
| Efficiency for the person | Lowest, N repetitions of the same click sequence | Highest, per the entire justification for this pattern in dimension 2 | Middle, one extra preview step compared with immediate bulk apply, but no per-item repetition |
| Blast-radius risk | Lowest, a mistake affects exactly one item, and per-item undo (this catalogue's own Undo entry) covers it cleanly | Highest without mitigation, per the select-all trap in dimension 10, mitigated in practice by confirmation dialogs, Trello's 20-item cap, and AIP-233's atomicity rule | Middle, the preview step itself functions as a richer form of confirmation, a last chance to see the actual scope before committing |
| Implementation complexity | Lowest, no batching or partial-failure reporting needed | Highest, requires an atomic-versus-partial-success decision, a partial-failure reporting design, and a bulk-aware undo per dimension 13 | Higher than plain bulk action, requires rendering a preview of the pending change across N items before commit |

## 13. Related and incompatible patterns

Undo, already in this catalogue, is directly and load-bearingly related, and
this entry found a real, primary-source answer to the specific question a
bulk operation raises for it. does undo need to reverse the whole batch as
one unit, or does a person have to invoke it N separate times. GitHub's own
documentation states the answer directly. when a person makes a bulk change
in the table layout, GitHub displays the option to undo that change, per
dimension 9, treating the entire bulk edit, which can touch many cells
across many rows, as one undoable unit surfaced through a single Undo
affordance, not as N separate undo entries. This is structurally the same
requirement this catalogue's own Undo entry names for a workspace-scoped
variant, that the system group N individual mutations into a single
reversible unit rather than wrapping each item's change in its own
independent command left for a person to undo one at a time. a bulk action
multiplies the blast radius of a mistake, so undo's guarantee has to scale
with it, grouping rather than multiplying the reversal effort.

No source consulted for this entry directly names a connection between bulk
action and empty state, though the structural link is obvious, a bulk
delete can leave a list at exactly the empty state this catalogue's own
Empty State entry describes as the user-cleared sub-type. this entry checked
that entry's own references and found none naming bulk-delete specifically
as a trigger, so this connection is reported as a plausible, unsourced
inference rather than a claim either entry's sources make directly.

## 14. Refactoring path in and out

To introduce bulk action into a list that currently supports only per-item
operations, first add the selection mechanism from dimension 5, a
per-item checkbox with a hover-then-persist reveal, before building the
action bar. Decide the server-side atomicity model up front, per Google's
AIP-233 distinction in dimension 8, atomic for a fast, simple synchronous
path or partial success for a slower path managing complex resources,
since retrofitting that decision after a naive whole-or-nothing endpoint
ships is far more disruptive than choosing it at the start. Add the bulk
undo guarantee from dimension 13 before removing any existing per-item
undo, so a person is never left worse off by gaining bulk capability. Add
the two-stage select-all escalation from dimension 7 last, once the basic,
bounded selection and action flow is proven correct, since it is the
highest-risk addition in the whole pattern.

To remove bulk action from a context where it has proven too risky, per the
non-applicability reasoning in dimension 4, the safest first step is
narrowing scope rather than removing the mechanism outright, dropping the
select-all-matching-query escalation while keeping select-all-on-page, or
capping the maximum selectable count the way Trello does, before removing
multi-select entirely.

## 15. Testing and verification

Testing the select-all-on-page versus select-all-matching-query distinction
from dimension 7 is best modeled directly on the World Wide Web
Consortium's own listbox specification of what select all should mean
state-wise. a test triggering the first-stage select-all should assert
every currently rendered option's accessible selected state flips to true,
and, separately, that a distinct, second, explicit action is required
before selection state expands beyond what is currently rendered.

Testing partial-failure handling is directly testable against the two
sourced, real contracts in dimension 8 and dimension 11. a synthetic batch
containing both a valid and an invalid item should populate Google's own
index-keyed failure map correctly, with the specific, checkable negative
case that a transient, server-retried error must never appear there. Amazon
S3's own completion report gives the equivalent assertion shape, every
object key in a manifest should appear exactly once in the report, tagged
either succeeded or failed.

Testing that the action bar shows the correct count relies on the same
accessible live-region ordering caveat named in dimension 5. the live
region element must exist in the document before the count-changing update
happens, so a test asserting accessible correctness needs to assert that
DOM-presence-before-mutation ordering specifically, not only that the
visible text on screen is correct.

## 16. Observability signals

No source consulted for this entry gives a canonical, named methodology for
observing bulk-action usage specifically in production, so this dimension is
reported as reasoned synthesis grounded in the sourced material above,
labeled as such rather than presented as established fact.

The partial-failure reporting contracts already sourced in dimensions 8 and
11, Google's index-keyed failure map and Amazon S3's completion report,
imply the natural engineering signal to monitor. the per-item failure rate
inside a batch, tracked over time, since a rising rate on a specific action
type points at a real, recurring problem rather than an isolated fluke. The
select-all-matching-query escalation named in dimension 7 implies a second
useful signal, tracking how often the escalated, unbounded selection is
actually invoked relative to the bounded, page-level selection, since a
disproportionately high rate of the riskier path could indicate the safer
default is not discoverable or not sufficient for how people actually use
the feature.

## 17. Security and privacy implications

Per-item authorization is the most directly sourced requirement for this
pattern. OWASP's own API Security guidance for Broken Object Level
Authorization states the governing principle plainly. every API endpoint
that receives an ID of an object and performs an action on it should
implement object-level authorization checks that validate the requester has
permission to act on that specific object, and failures in this mechanism
typically lead to unauthorized information disclosure, modification, or
destruction of all data (OWASP, "API3:2023 Broken Object Property Level
Authorization," OWASP API Security Top 10,
https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/,
verified 2026-08-23). the same page's own worked attack example uses a
mutation accepting an array of object IDs, which is directly on point for a
bulk endpoint. authorizing the caller once and then trusting every ID in
the array without re-checking each one individually is exactly this
vulnerability class, and the fix is checking authorization per item in the
batch, not once for the request as a whole.

Rate limiting a bulk destructive endpoint deserves its own attention rather
than being lumped in with single-item endpoints, since a bulk endpoint is
functionally a write analog of a list request, touching many resources per
call. OWASP's own Denial of Service guidance frames the general defensive
principle, controlling traffic rate from and to a server using load limits,
the number of users allowed to access a given resource at any given time
(OWASP, "Denial of Service Cheat Sheet,"
https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html,
verified 2026-08-23), a principle this entry applies to the bulk-action
case rather than a bulk-specific recommendation the source itself states.

Audit logging a partial-failure batch operation follows OWASP's own logging
guidance directly. the application logs must record when, where, who, and
what for each event, naming the affected object and the result status of
the action, plus an interaction identifier linking every event for a single
user interaction (OWASP, "Logging Cheat Sheet,"
https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html,
verified 2026-08-23). applied to a bulk action, each of the N per-item
outcomes is its own logged event, object equals the specific item ID,
result equals success or fail, all sharing one interaction identifier, so
an administrator can query everything that happened as a result of one
bulk request and reconstruct exactly which items succeeded and which
failed, matching the same shape as AIP-233's failure map and S3's
completion report from dimension 8.

## 18. References

1. Wikipedia contributors, "Batch processing," Wikipedia, The Free
   Encyclopedia, https://en.wikipedia.org/wiki/Batch_processing, verified
   2026-08-23.
2. Google, "Selection," Material Design,
   https://m1.material.io/patterns/selection.html, verified 2026-08-23.
3. Android Developers, "App bars,"
   https://developer.android.com/develop/ui/views/components/menus,
   verified 2026-08-23.
4. Google, "AIP 233: Batch methods: Create," https://google.aip.dev/233,
   verified 2026-08-23.
5. Atlassian, "Move Cards or Lists," Trello Help Center,
   https://support.atlassian.com/trello/docs/moving-cards-or-lists/,
   verified 2026-08-23.
6. Notion, "Use tables," https://www.notion.com/help/tables, verified
   2026-08-23.
7. World Wide Web Consortium, "Listbox Pattern," WAI-ARIA Authoring
   Practices Guide, https://www.w3.org/WAI/ARIA/apg/patterns/listbox/,
   verified 2026-08-23.
8. World Wide Web Consortium, "Toolbar Pattern," WAI-ARIA Authoring
   Practices Guide, https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/,
   verified 2026-08-23.
9. Mozilla Developer Network, "ARIA live regions,"
   https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions,
   verified 2026-08-23.
10. Google, "Batch Requests," Google Cloud Storage documentation,
    https://docs.cloud.google.com/storage/docs/batch, verified 2026-08-23.
11. Mozilla Developer Network, "207 Multi-Status,"
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/207,
    verified 2026-08-23.
12. GitHub, "Associating milestones with issues and pull requests,"
    https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/associating-milestones-with-issues-and-pull-requests,
    verified 2026-08-23.
13. GitHub, "Editing items in your project,"
    https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/editing-items-in-your-project,
    verified 2026-08-23.
14. Airtable, "Adding, duplicating, and deleting Airtable records,"
    https://support.airtable.com/docs/adding-duplicating-and-deleting-airtable-records,
    verified 2026-08-23.
15. World Wide Web Consortium, "Alert Dialog Pattern," WAI-ARIA Authoring
    Practices Guide, https://www.w3.org/WAI/ARIA/apg/patterns/alertdialog/,
    verified 2026-08-23.
16. Amazon Web Services, "Batch Operations basics,"
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/batch-ops.html,
    verified 2026-08-23.
17. OWASP, "API3:2023 Broken Object Property Level Authorization," OWASP
    API Security Top 10,
    https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/,
    verified 2026-08-23.
18. OWASP, "Denial of Service Cheat Sheet,"
    https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html,
    verified 2026-08-23.
19. OWASP, "Logging Cheat Sheet,"
    https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html,
    verified 2026-08-23.

**Evidence grade.** medium

**Most solid findings.** Google's AIP-233 batch standard, the W3C's listbox,
toolbar, and alertdialog patterns, GitHub's own documented bulk-undo
guarantee, and the OWASP object-level-authorization and logging guidance
are all primary sources read directly and squarely on point.

**Unverified or unclear.** GOV.UK's Design System carries no bulk-action
pattern on its live index, and no dedicated Wikipedia article exists for
this pattern, both confirmed absences rather than search failures. IBM
Carbon Design System's own prose pages could not be retrieved directly, and
the claims attributed to it rest on lower-confidence, indirectly indexed
text rather than a directly fetched quote. Gmail's own two-stage
select-all mechanism could not be confirmed against a primary Google
source and rests on a secondary explainer instead. No source names a
canonical, documented incident of a person losing data via a bulk
select-all mistake, and the empty-state connection in dimension 13 is this
entry's own inference, not a claim any consulted source states directly.

## Code

TypeScript, Python, and Go implementations of a selection manager and a
batch-apply function that returns a per-item outcome map, following Google's
AIP-233 index-keyed failure contract from dimension 8, rather than a single
success or fail boolean.

```typescript
interface BatchOutcome {
  index: number;
  id: string;
  ok: boolean;
  error: string | null;
}

class SelectionManager<T extends { id: string }> {
  private selected: Set<string> = new Set();

  toggle(item: T): void {
    if (this.selected.has(item.id)) {
      this.selected.delete(item.id);
    } else {
      this.selected.add(item.id);
    }
  }

  selectAllOnPage(items: T[]): void {
    for (const item of items) {
      this.selected.add(item.id);
    }
  }

  clear(): void {
    this.selected.clear();
  }

  count(): number {
    return this.selected.size;
  }

  ids(): string[] {
    return Array.from(this.selected);
  }
}

async function applyBulkAction<T extends { id: string }>(
  items: T[],
  action: (item: T) => Promise<void>
): Promise<BatchOutcome[]> {
  const results = await Promise.all(
    items.map(async (item, index) => {
      try {
        await action(item);
        return { index, id: item.id, ok: true, error: null };
      } catch (err) {
        const message = err instanceof Error ? err.message : "unknown error";
        return { index, id: item.id, ok: false, error: message };
      }
    })
  );
  return results;
}
```

```python
import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, TypeVar


T = TypeVar("T")


@dataclass
class BatchOutcome:
    index: int
    item_id: str
    ok: bool
    error: str | None


class SelectionManager(Generic[T]):
    def __init__(self) -> None:
        self._selected: set[str] = set()

    def toggle(self, item_id: str) -> None:
        if item_id in self._selected:
            self._selected.discard(item_id)
        else:
            self._selected.add(item_id)

    def select_all_on_page(self, item_ids: list[str]) -> None:
        self._selected.update(item_ids)

    def clear(self) -> None:
        self._selected.clear()

    def count(self) -> int:
        return len(self._selected)

    def ids(self) -> list[str]:
        return list(self._selected)


async def apply_bulk_action(
    items: list[T],
    get_id: Callable[[T], str],
    action: Callable[[T], Awaitable[None]],
) -> list[BatchOutcome]:
    async def run_one(index: int, item: T) -> BatchOutcome:
        try:
            await action(item)
            return BatchOutcome(index, get_id(item), True, None)
        except Exception as exc:
            return BatchOutcome(index, get_id(item), False, str(exc))

    return await asyncio.gather(*(run_one(i, item) for i, item in enumerate(items)))
```

```go
package bulkaction

import "sync"

type BatchOutcome struct {
	Index int
	ID    string
	OK    bool
	Error string
}

type SelectionManager struct {
	mu       sync.Mutex
	selected map[string]struct{}
}

func NewSelectionManager() *SelectionManager {
	return &SelectionManager{selected: make(map[string]struct{})}
}

func (s *SelectionManager) Toggle(id string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.selected[id]; ok {
		delete(s.selected, id)
	} else {
		s.selected[id] = struct{}{}
	}
}

func (s *SelectionManager) SelectAllOnPage(ids []string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, id := range ids {
		s.selected[id] = struct{}{}
	}
}

func (s *SelectionManager) Clear() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.selected = make(map[string]struct{})
}

func (s *SelectionManager) Count() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.selected)
}

func (s *SelectionManager) IDs() []string {
	s.mu.Lock()
	defer s.mu.Unlock()
	ids := make([]string, 0, len(s.selected))
	for id := range s.selected {
		ids = append(ids, id)
	}
	return ids
}

type Item struct {
	ID string
}

func ApplyBulkAction(items []Item, action func(Item) error) []BatchOutcome {
	outcomes := make([]BatchOutcome, len(items))
	var wg sync.WaitGroup
	for i, item := range items {
		wg.Add(1)
		go func(index int, it Item) {
			defer wg.Done()
			if err := action(it); err != nil {
				outcomes[index] = BatchOutcome{Index: index, ID: it.ID, OK: false, Error: err.Error()}
				return
			}
			outcomes[index] = BatchOutcome{Index: index, ID: it.ID, OK: true}
		}(i, item)
	}
	wg.Wait()
	return outcomes
}
```
