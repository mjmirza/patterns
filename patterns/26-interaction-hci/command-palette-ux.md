---
name: Command Palette
slug: command-palette-ux
family: 26-interaction-hci
category: Interaction and HCI
aliases: [Command Bar, Command Menu, Quick Open, Cmd K]
first_described: "Sublime Text popularized the term, exact origin unverifiable live, dedicated Wikipedia stub"
maturity: established
related: [breadcrumbs]
incompatible_with: []
verified: 2026-08-23
---

# Command Palette

## 1. Name, aliases, and lineage

A command palette, also called a command bar or a command menu, is a
keyboard-invoked, searchable overlay, typically triggered by a shortcut
such as Cmd+K or Ctrl+Shift+P, that lets a person search for and execute
any command, navigate to any page, or jump to any object in an
application via fuzzy text search, bypassing the normal menu or
navigation hierarchy entirely. Wikipedia carries a dedicated, if
explicitly marked incomplete, stub article for the pattern, defining it
as a searchable index of software commands, appearing as a modal palette
window with a search box and suggestions list, used entirely by keyboard,
possibly exposing commands unavailable elsewhere in the graphical
interface, and extensible. It names Visual Studio Code, Zed, and Obsidian
as applications carrying the pattern, and separately notes its use in
standalone launcher utilities such as Raycast.

VS Code's own documentation states its Command Palette, opened with
Ctrl+Shift+P or Cmd+Shift+P, is VS Code's central command interface,
providing access to all functionality within VS Code, including keyboard
shortcuts for the most common operations.

Sublime Text is very widely credited in developer folklore with
popularizing this exact pattern under this exact name, and this entry
made a genuine attempt to confirm that live and could not. Sublime's own
current documentation index lists 38 pages across its usage,
customization, miscellaneous, and package-development sections, and
neither Command Palette nor Goto Anything appears among them, with every
direct URL guess for either returning a not-found response. The closest
live confirmation is Sublime's own indexing documentation, describing
Goto Symbol in Project as a feature that lets a person fuzzy-search
through symbols, and Wikipedia's own Sublime Text article, which lists a
command palette with adaptive matching among the editor's notable
features without stating which version introduced it or crediting the
term's origin. This entry also checked whether VS Code's own documentation
or Wikipedia article credits Sublime Text directly for the name or the
shortcut, and found no such statement in either.

The interaction shape itself traces further back still. Quicksilver, per
its own Wikipedia article, was created by Nicholas Jitkoff starting 2003,
built around a distinctive three-pane object, action, and attribute
interaction model, with the article stating directly that many of its
features have subsequently been integrated into the modern macOS system
feature, Spotlight. Alfred, created in 2010, is described as operating
similarly to macOS's native Spotlight. Neither article states outright
that Alfred was directly inspired by Quicksilver, so this entry reports
both as independently documented, Spotlight-class successors to
Quicksilver's launcher paradigm rather than asserting a stronger, direct
lineage claim than the sources themselves make.

## 2. Problem and context

A traditional menu bar or sidebar hierarchy requires a person to know
where a command lives, which menu, which submenu, which settings page,
before they can use it. A command palette replaces that spatial recall
with textual recall, letting a person type what they want and get it
regardless of where it structurally lives. GitHub's own documentation
states this directly, the palette gives quick access to a wide range of
actions, without the need to remember keyboard shortcuts, and Zed's own
getting-started guide frames the same idea from the forgotten-shortcut
angle, if you forget a keyboard shortcut, you can search for the desired
action through the command palette instead.

The registry-maintenance cost side of the tension is visible in how
library authors describe their own value proposition, cmdk exists so a
developer does not have to hand-roll filtering, stating it automatically
filters and sorts items with zero configuration. The discoverability-cost
side shows up in VS Code's own extension-authoring guideline, which
explicitly warns against emoji in command names and mandates a clear
category prefix, precisely because a command palette is a flat, invisible
until invoked list where naming quality is the only discoverability lever
left.

## 3. Forces

Discoverability sits against efficiency for a returning user, and this is
inherent to the pattern's own definition, Wikipedia's own article
describes it as a modal palette window, invisible until a person already
knows to invoke it, unlike a menu bar which is always visible. Zed's own
framing of the palette as a fallback for a forgotten shortcut confirms
the other side of the same trade, it is designed to complement, not
replace, keyboard-shortcut muscle memory for a person who returns to the
tool often.

The cost of maintaining a searchable command registry sits against the
payoff of that registry. VS Code requires every command an extension
exposes to be explicitly declared in that extension's own manifest before
it can appear in the palette at all, real, non-trivial engineering work
that must be kept in sync with the application's actual current
capabilities.

## 4. Applicability and non-applicability

Every verified named production example in this entry is a daily-use,
power-user tool, a code editor, a developer platform, or an OS-level
launcher explicitly marketed to power users. Microsoft's own PowerToys
Command Palette documentation states its target audience directly, built
for Windows power users, fully customizable, deeply extensible, and
designed to keep you in your flow. Obsidian's own help documentation
describes a pinning mechanism for frequently used commands and states
that as of version 1.8.3, recently used commands appear at the top, a
feature that only pays off for a person who returns to the tool
repeatedly and accumulates real usage history.

This entry could not find a live, direct source discussing when a command
palette is a poor fit. What it can state, reasoned from the pattern of
verified adopters rather than asserted as an external finding, is that
every real-world adopter reached live in this research is a tool used by
the same person daily over a long horizon, none of the sources reached
document a consumer, infrequent-use application shipping this pattern,
consistent with, though not proof of, the claim that it under-performs
there.

## 5. Structure

The trigger is a keyboard shortcut, confirmed across five real products,
Ctrl+Shift+P or Cmd+Shift+P for VS Code and Zed, Ctrl+P or Cmd+P for
Obsidian, Ctrl+K or Cmd+K, with a second combination for command-only
mode, for GitHub, and Win+Alt+Space for PowerToys.

VS Code's own UX guidelines name the underlying primitive directly, Quick
Pick, a text input field paired with a scrollable item list, where each
item can carry an icon, a description, and a detail field, organized into
sections using separators. The results are ranked by a real, concrete
fuzzy-matching algorithm, and this entry read VS Code's own production
source for it rather than asserting an algorithm from memory, every
query-character-to-target-character pair earns a point for any match, a
larger bonus for a match at the very start of the string, a bonus for a
match right after a separator character, a smaller bonus for a
camelCase-boundary match, and a further reward for consecutive matched
runs, with case-sensitivity earning one more point. fzf, a second, fully
independent implementation, documents an extended-search mode supporting
simultaneous fuzzy matching, exact quoted matches, prefix and suffix
anchors, and inversion, plus a flag to disable fuzzy matching entirely in
favor of pure exact matching.

Recency and pinning are part of the structure itself, not an
afterthought, per Obsidian's own documentation, recently used commands
surface at the top of the empty-input list, and a separate,
settings-driven pinning mechanism lets a person permanently favor a
command independent of the algorithm's own ranking. VS Code's own
documentation states the shortcut-learning benefit directly, the palette
displays default keyboard shortcuts alongside commands, helping a person
learn them over time.

## 6. ASCII structure diagram

```
   +---------------------------+
   | keyboard shortcut pressed |
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   | overlay opens, search      |
   | input shown (often pre-    |
   | filled with recent/pinned) |
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   |  person types query        |
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   |  fuzzy matcher ranks the   |
   |  full command registry     |
   |  against the typed input   |
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   |  filtered, ranked results  |
   |  list shown (often grouped |
   |  commands / pages / items) |
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   |  arrow keys navigate,      |
   |  enter executes selected   |
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   |  overlay closes, action    |
   |  runs or navigation happens|
   +---------------------------+
```

## 7. Dynamics

The command registry is static at its base, VS Code's own documentation
describes an extension registering a command programmatically and
declaring it in its manifest's commands section, but membership can be
genuinely dynamic and context-conditional on top of that static base.
VS Code's own When Clause Contexts reference documents exactly this
mechanic, a command's visibility is gated by an expression evaluated
against live editor state, its own documented example gates a start
debugging command on a debugger being available and the editor not
already being in debug mode, and an extension can push its own custom
context at runtime so a command appears or disappears as application
state genuinely changes, precisely the close-file-only-appears-when-a-file-
is-open mechanic named in this entry's own scope.

Ranking blends several sourced factors. Fuzzy match quality, per VS
Code's own scoring algorithm in section 5. Exact substring override, per
fzf's own dedicated flag and quoted-term mode. Recency of use, per
Obsidian's own documented recently-used-commands-surface-first behavior,
and VS Code's own Quick Open independently exhibiting the same pattern,
repeatedly pressing the shortcut cycles through recently opened files.
Manual pinning as an override of the algorithmic ranking entirely, both
Obsidian and PowerToys let a person permanently fix an item's position.
And a tie-breaking rule, Obsidian's own documentation states shorter
command names take priority during a filtered search.

When the palette opens with no input typed yet, PowerToys' own
documentation describes a dedicated home page that surfaces the most
relevant commands, recent items, and a pinned-commands section
immediately, before any typing happens at all.

## 8. Implementation variants

VS Code deliberately keeps pure command execution and pure navigation as
two distinct features with two distinct shortcuts, its own documentation
names both on the same page, the Command Palette, which executes
commands, and Quick Open, which navigates to files and symbols, a real,
sourced design decision rather than an inference.

Most modern implementations combine the two instead, exactly as this
entry's own scope anticipates. GitHub's own Command Palette does both
explicitly, letting a person navigate to any page they have access to and
run a command directly from the keyboard, using prefix characters to
scope which kind of result is wanted. PowerToys' Command Palette combines
app launch, command run, file search, web search, a calculator, settings
navigation, window switching, and clipboard history in one flat
interface.

Three real, named, independently verified open-source libraries build
this pattern for web applications. cmdk, a React command-menu component
also usable as an accessible combobox, used in production for Vercel's
own command menu, deliberately unstyled with data-attribute hooks for
styling, documented to handle two to three thousand items effectively
without virtualization. kbar, a provider-based React library documented
to handle tens of thousands of actions efficiently, with built-in undo
and redo history, and a stated adopter list including Outline and
NextUI. ninja-keys, a framework-agnostic Web Component built explicitly
because existing libraries were too framework-specific, supporting flat
and nested action data with fuzzy search across nested menus.

This entry could not find a named, live-sourced example of a purely
search-only variant with zero command execution, every real product
reached either runs actions directly or is explicitly paired with a
sibling command-executing feature, and states that gap plainly rather
than inventing an example.

## 9. Known production uses

Five real, named, currently documented production uses, each sourced
directly to the vendor's own documentation. VS Code, Ctrl+Shift+P or
Cmd+Shift+P, its central command interface. GitHub, a combined navigate
and command and search palette, currently documented as being in public
preview with no exact launch date stated on the live page. Zed, described
in its own words as your gateway to every action in Zed. Obsidian, a
documented core plugin with fuzzy matching, recency ranking since version
1.8.3, and manual pinning. Microsoft PowerToys' own Command Palette, an
OS-level, extensible, power-user launcher.

This entry attempted, and could not confirm live, Sublime Text's own
current documentation of the feature, or an explicit statement of
Discord's use of the pattern beyond a single line in Wikipedia's own
dedicated stub article naming it. It also attempted Linear specifically,
since the brief for this research named it as a strong candidate, and
could not surface the feature from four separate live fetches of
Linear's own site, almost certainly a limitation of fetching a heavily
client-rendered marketing site rather than evidence the feature does not
exist, and states that distinction honestly rather than asserting the
feature from memory.

## 10. Consequences

Positive. A command palette lets a person execute an action directly from
the keyboard without navigating through a series of menus, per GitHub's
own stated rationale, and can surface commands not exposed anywhere else
in the graphical interface at all, per Wikipedia's own definition. VS
Code's own documentation states a further, real benefit, the palette
teaches keyboard shortcuts passively by displaying them alongside each
command as a person uses it.

Negative. Invisibility until invoked is inherent to the pattern's own
definition, a person must already know to summon it, the direct cost side
of the discoverability-versus-efficiency trade named in section 3.
Registry maintenance is real, non-trivial engineering work, VS Code
requires every command to be explicitly declared in an extension's own
manifest before it can appear at all, meaning an unregistered or
mis-registered action simply never surfaces to the person who needed it.

## 11. Failure modes and misuse

This entry could not find a live source directly discussing command
palette design as an anti-pattern in named, incident form, and states
that honestly rather than manufacturing one. What it can report is
structural evidence consistent with the failure modes a flat, growing,
searchable registry would plausibly exhibit.

A scale ceiling is real and vendor-acknowledged rather than hypothetical,
cmdk's own documentation states it handles two to three thousand items
effectively without virtualization, and states plainly that a developer
can implement custom virtualization if a registry needs to grow beyond
that, while kbar's own claim to handle tens of thousands of actions
efficiently implies this is a genuinely, actively engineered-around
concern across the ecosystem rather than a one-off library quirk, though
this entry presents that as an inference from two vendor claims rather
than a documented incident.

Context or registry drift, a command shown that is not actually valid in
the application's current state, is the exact failure VS Code's entire
when-clause-context mechanism in section 7 exists to prevent, the
existence of that whole subsystem is itself indirect evidence that
showing an unavailable command is a recognized, designed-against risk,
though no source names an actual incident where it went wrong. A noisy,
uncurated registry, growing without bound as more actions are
contributed, is reasoned from the pattern's own flat, per-extension
structure rather than sourced to any incident directly, and this entry
states that distinction plainly.

## 12. Trade-off matrix

| Approach | Discoverability, never used before | Execution speed for a known command | Screen space cost when closed |
|---|---|---|---|
| Command palette | Low, invisible until the shortcut is already known, per Wikipedia's own definition | Very high, one shortcut plus a few keystrokes plus enter, without navigating a series of menus, per GitHub's own stated rationale | Zero, no persistent chrome at all |
| Traditional menu bar | High, always visible and browsable by hovering or clicking | Low, multiple clicks through a hierarchy the person must remember | Persistent, the bar or ribbon occupies space on every screen at all times |
| Dedicated global search bar | Medium, usually a visible input, but its scope, content versus actions, is not obvious until used | Not directly comparable for actions, a search bar in this comparison finds content or data rather than executing commands, by the pattern's own definition | Persistent, the input field occupies space at all times |

## 13. Related and incompatible patterns

Breadcrumbs, this family's own entry, have a genuine, vendor-stated
connection worth recording precisely. VS Code's own breadcrumbs
documentation states directly that its breadcrumb feature complements
separate navigation features, naming Quick Open and Go to Symbol by name
as the ones it complements, a real, sourced relationship between the
command-palette family of features and breadcrumb navigation rather than
a forced or invented one.

This entry found no source connecting the command palette to wizard, this
family's own linear multi-step pattern, and asserts no such connection.

## 14. Refactoring path in and out

Introducing a command palette into an application that lacks one starts
from the registry, per VS Code's own model, every meaningful action is
declared once, with a name, a description, and, where the action is
context-dependent, a when-clause-style condition gating its visibility to
the application's current state, exactly the mechanism in section 7 that
prevents a stale or invalid command from ever surfacing. A fuzzy-matching
layer is then added over that registry, one of the real, named libraries
in section 8 for a client-rendered application, or a hand-rolled scorer
following VS Code's own documented algorithm for a from-scratch
implementation.

Removing a command palette, when an application's action count is small
enough that the pattern adds more invisible complexity than it saves,
follows directly from the applicability reasoning in section 4, collapse
the registry back into a conventional, always-visible menu bar, the
correct alternative for an infrequently used consumer application where
a person would never learn or remember a keyboard shortcut to invoke the
palette in the first place.

## 15. Testing and verification

VS Code's own extension-testing documentation is directly on point and
substantiates a real, sourced testing shape. Extensions, including their
palette-registered commands, are tested via integration tests run inside
a genuine extension development host instance with full API access, not
unit tests alone, using a documented tool combination run under Mocha,
and a command can be exercised directly inside a test by executing it
programmatically and asserting it completes without error, exactly the
every-registered-command-actually-executes shape this entry's own scope
anticipated.

This entry could not find a live source specifically describing an
automated test asserting that fuzzy search returns the expected top
result for a set of representative queries as a named testing practice,
and states that gap plainly rather than asserting one exists.

## 16. Observability signals

This entry could not find a live, named source, a product blog or an
engineering post, specifically discussing command-palette usage
analytics, invocation frequency, searched-but-not-found query logging, or
open-to-execute latency, and states that gap honestly rather than
inventing one. What it can state, sourced, is one concrete signal
PowerToys' own documentation names as a design feature rather than an
analytics metric, the palette's home page surfaces the most relevant
commands, recent items, and pinned commands the moment it opens, which
implies the underlying system is at minimum tracking recency and
frequency internally, even without a source describing that data being
surfaced back to a product team as a named analytics signal.

## 17. Security and privacy implications

This is the angle with the strongest direct citation in this entry.
Raycast's own developer documentation names the exact risk this entry's
own scope anticipated and documents the exact mitigation, its own alert
API reference states a developer should use a confirmation alert for an
action such as irreversibly deleting something, and specifically
recommends a destructive action style for confirmations of a destructive
action such as deleting a file, a documented, vendor-mandated
confirmation step specifically for a destructive command surfaced through
the palette.

Raycast's own separate security documentation confirms the broader
sandboxing context an extension runs inside, isolated engine instances
with their own event loops and limited heap memory, able to access only
a defined set of APIs through remote procedure calls, which constrains
what a fast-fingered, imprecise search-and-enter flow could accidentally
trigger, though that same security page does not itself discuss
confirmation dialogs directly, that guidance lives only in the separate
alert API documentation, and this entry states that distinction so the
citation is not overstated. No equivalent explicit statement about
destructive-command confirmation specifically in the palette context was
found for VS Code, GitHub, or Obsidian, though VS Code's own when-clause
context gating in section 7 reduces the surface area of what can even
appear at the wrong moment.

## 18. References

1. Wikipedia contributors. "Command palette." Wikipedia, The Free
   Encyclopedia. https://en.wikipedia.org/wiki/Command_palette. Verified
   2026-08-23.
2. Visual Studio Code. "User Interface."
   https://code.visualstudio.com/docs/getstarted/userinterface. Verified
   2026-08-23.
3. Visual Studio Code. "Command Palette." UX Guidelines.
   https://code.visualstudio.com/api/ux-guidelines/command-palette.
   Verified 2026-08-23.
4. Visual Studio Code. "When Clause Contexts."
   https://code.visualstudio.com/api/references/when-clause-contexts.
   Verified 2026-08-23.
5. Visual Studio Code. "fuzzyScorer.ts." microsoft/vscode, GitHub.
   https://github.com/microsoft/vscode/blob/main/src/vs/base/common/fuzzyScorer.ts.
   Verified 2026-08-23.
6. Visual Studio Code. "Testing extensions."
   https://code.visualstudio.com/api/working-with-extensions/testing-extension.
   Verified 2026-08-23.
7. GitHub Docs. "GitHub Command Palette."
   https://docs.github.com/en/get-started/accessibility/github-command-palette.
   Verified 2026-08-23.
8. Zed. "Getting started." https://zed.dev/docs/getting-started. Verified
   2026-08-23.
9. Obsidian. "Command palette." https://obsidian.md/help/plugins/command-palette.
   Verified 2026-08-23.
10. Microsoft. "Command Palette overview." PowerToys documentation.
    https://learn.microsoft.com/en-us/windows/powertoys/command-palette/overview.
    Verified 2026-08-23.
11. Wikipedia contributors. "Quicksilver (software)." Wikipedia, The Free
    Encyclopedia. https://en.wikipedia.org/wiki/Quicksilver_(software).
    Verified 2026-08-23.
12. Wikipedia contributors. "Alfred (software)." Wikipedia, The Free
    Encyclopedia. https://en.wikipedia.org/wiki/Alfred_(software).
    Verified 2026-08-23.
13. pacocoursey. "cmdk." GitHub repository.
    https://github.com/pacocoursey/cmdk. Verified 2026-08-23.
14. timc1. "kbar." GitHub repository. https://github.com/timc1/kbar.
    Verified 2026-08-23.
15. ssleptsov. "ninja-keys." GitHub repository.
    https://github.com/ssleptsov/ninja-keys. Verified 2026-08-23.
16. junegunn. "fzf." GitHub repository. https://github.com/junegunn/fzf.
    Verified 2026-08-23.
17. Raycast. "Alert." API Reference.
    https://developers.raycast.com/api-reference/feedback/alert. Verified
    2026-08-23.
18. Raycast. "Security." https://developers.raycast.com/information/security.
    Verified 2026-08-23.

**Evidence grade.** high

**Most solid findings.** VS Code's own production fuzzy-scoring source
and when-clause-context reference give concrete, quoted mechanics rather
than a general description of fuzzy matching. Three independently
verified open-source libraries, cmdk, kbar, and ninja-keys, corroborate
the ecosystem's real shape rather than resting on one example. Raycast's
own API documentation gives a directly quoted, vendor-mandated
confirmation step for destructive commands, the strongest single citation
in this entry.

**Unverified or unclear.** Sublime Text's own current documentation for
the Command Palette feature could not be reached, so this entry does not
assert Sublime originated the name from a primary Sublime source. Nielsen
Norman Group and Linear's own command-menu documentation could not be
reached live. A documented, named production incident of a command
palette failure mode could not be found, and the scale and registry-drift
failure modes in section 11 are reasoned from vendor claims rather than
from a described incident.

## Code

TypeScript, a fuzzy-scoring command registry with context-conditional
visibility, following VS Code's own scoring bonuses and when-clause
mechanism described in sections 5 and 7:

```typescript
interface Command {
  id: string;
  label: string;
  isAvailable: () => boolean;
  run: () => void;
}

interface ScoredResult {
  command: Command;
  score: number;
}

function fuzzyScore(query: string, target: string): number {
  const q = query.toLowerCase();
  const t = target.toLowerCase();
  let score = 0;
  let targetIndex = 0;
  let consecutiveRun = 0;
  for (let i = 0; i < q.length; i++) {
    const foundAt = t.indexOf(q[i], targetIndex);
    if (foundAt === -1) return 0;
    score += 1;
    if (foundAt === 0) score += 8;
    if (foundAt > 0 && "/_-.".includes(t[foundAt - 1])) score += 4;
    if (foundAt === targetIndex) {
      consecutiveRun += 1;
      score += consecutiveRun <= 3 ? 6 : 3;
    } else {
      consecutiveRun = 0;
    }
    targetIndex = foundAt + 1;
  }
  return score;
}

class CommandRegistry {
  private commands: Command[] = [];

  register(command: Command): void {
    this.commands.push(command);
  }

  search(query: string): ScoredResult[] {
    return this.commands
      .filter((c) => c.isAvailable())
      .map((command) => ({ command, score: fuzzyScore(query, command.label) }))
      .filter((r) => r.score > 0)
      .sort((a, b) => b.score - a.score);
  }
}

let hasOpenFile = false;
const registry = new CommandRegistry();
registry.register({
  id: "file.close",
  label: "Close File",
  isAvailable: () => hasOpenFile,
  run: () => console.log("closed"),
});
registry.register({
  id: "file.open",
  label: "Open File",
  isAvailable: () => true,
  run: () => console.log("opened"),
});
console.log(registry.search("close"));
hasOpenFile = true;
console.log(registry.search("close"));
```

Python, the same registry with recency-based ranking on top of the fuzzy
score, following Obsidian's own recent-commands-surface-first behavior
in section 7:

```python
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Command:
    command_id: str
    label: str
    is_available: Callable[[], bool]


def fuzzy_score(query: str, target: str) -> int:
    q = query.lower()
    t = target.lower()
    score = 0
    target_index = 0
    consecutive_run = 0
    for ch in q:
        found_at = t.find(ch, target_index)
        if found_at == -1:
            return 0
        score += 1
        if found_at == 0:
            score += 8
        if found_at > 0 and t[found_at - 1] in "/_-.":
            score += 4
        if found_at == target_index:
            consecutive_run += 1
            score += 6 if consecutive_run <= 3 else 3
        else:
            consecutive_run = 0
        target_index = found_at + 1
    return score


class CommandRegistry:
    def __init__(self) -> None:
        self.commands: list = []
        self.recent_ids: list = []

    def register(self, command: Command) -> None:
        self.commands.append(command)

    def record_used(self, command_id: str) -> None:
        self.recent_ids = [c for c in self.recent_ids if c != command_id]
        self.recent_ids.insert(0, command_id)

    def search(self, query: str) -> list:
        results = []
        for command in self.commands:
            if not command.is_available():
                continue
            score = fuzzy_score(query, command.label)
            if score == 0:
                continue
            if command.command_id in self.recent_ids:
                score += 10 - self.recent_ids.index(command.command_id)
            results.append((command, score))
        results.sort(key=lambda pair: pair[1], reverse=True)
        return results


if __name__ == "__main__":
    registry = CommandRegistry()
    registry.register(Command("file.open", "Open File", lambda: True))
    registry.register(Command("file.save", "Save File", lambda: True))
    registry.record_used("file.save")
    print(registry.search("f"))
```

Go, the same registry with a context-gated command and a destructive-action
confirmation flag, following Raycast's own confirmation-step guidance in
section 17:

```go
package main

import (
	"fmt"
	"sort"
	"strings"
)

type Command struct {
	ID          string
	Label       string
	Destructive bool
	IsAvailable func() bool
}

type ScoredResult struct {
	Command Command
	Score   int
}

func fuzzyScore(query, target string) int {
	q := strings.ToLower(query)
	t := strings.ToLower(target)
	score := 0
	targetIndex := 0
	consecutiveRun := 0
	for _, ch := range q {
		foundAt := strings.IndexRune(t[targetIndex:], ch)
		if foundAt == -1 {
			return 0
		}
		foundAt += targetIndex
		score++
		if foundAt == 0 {
			score += 8
		}
		if foundAt > 0 && strings.ContainsRune("/_-.", rune(t[foundAt-1])) {
			score += 4
		}
		if foundAt == targetIndex {
			consecutiveRun++
			if consecutiveRun <= 3 {
				score += 6
			} else {
				score += 3
			}
		} else {
			consecutiveRun = 0
		}
		targetIndex = foundAt + 1
	}
	return score
}

type CommandRegistry struct {
	Commands []Command
}

func (r *CommandRegistry) Register(c Command) {
	r.Commands = append(r.Commands, c)
}

func (r *CommandRegistry) Search(query string) []ScoredResult {
	var results []ScoredResult
	for _, c := range r.Commands {
		if !c.IsAvailable() {
			continue
		}
		score := fuzzyScore(query, c.Label)
		if score == 0 {
			continue
		}
		results = append(results, ScoredResult{Command: c, Score: score})
	}
	sort.Slice(results, func(i, j int) bool { return results[i].Score > results[j].Score })
	return results
}

func main() {
	registry := &CommandRegistry{}
	registry.Register(Command{ID: "file.delete", Label: "Delete File", Destructive: true, IsAvailable: func() bool { return true }})
	registry.Register(Command{ID: "file.open", Label: "Open File", IsAvailable: func() bool { return true }})
	for _, result := range registry.Search("file") {
		if result.Command.Destructive {
			fmt.Println(result.Command.Label, "requires confirmation before running")
		} else {
			fmt.Println(result.Command.Label)
		}
	}
}
```
