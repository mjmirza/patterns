# Family 13. Frontend and UI

Origin. Framework documentation

34 entries, 123,829 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Application Architecture

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Micro Frontends](micro-frontends.md) | established | 3,699 | A large, single frontend codebase shared by several teams commonly becomes a bottleneck as the organization grows, every team's change must pass through the same build pipeline ... |

## Behavioral

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Undo Stack](undo-stack.md) | canonical | 3,611 | An interactive application where every user action mutates state irreversibly forces a user who makes a mistake, whether a wrong edit, an accidental delete, or a change they ... |

## Component Architecture

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Atomic Design](atomic-design.md) | established | 3,682 | Before Atomic Design, a component library commonly organized components by feature or by page, a folder for the checkout flow next to a folder for the settings page, which left no ... |

## Component Composition

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Compound Components](compound-components.md) | established | 3,844 | A component with several configurable parts, a tab strip with a list of tabs and a panel of content, an accordion with several expandable sections, a select box with a list of ... |
| [Container Presentational](container-presentational.md) | deprecated | 3,861 | A component that both fetches data, manages loading and error state, and renders the resulting markup mixes two genuinely different concerns in one place. |
| [Higher-Order Component](higher-order-component.md) | established | 3,455 | Several components in a codebase often need the same cross-cutting behavior applied to them, subscribing to a data source, checking authentication before rendering, logging every ... |
| [Hooks](hooks.md) | canonical | 3,577 | Before Hooks, a function component in React could not hold its own state or run a side effect, so any component needing state, a lifecycle-tied effect, or access to context had to ... |
| [Provider Pattern](provider-pattern.md) | canonical | 3,428 | A value needed by several components scattered across a component tree, an authenticated user, a UI theme, a locale, a Redux store, would otherwise need to be passed as a prop ... |
| [Render Props](render-props.md) | established | 3,717 | A piece of stateful or side-effecting logic, tracking mouse position, managing a form field's validation state, fetching data, is often needed by more than one component, each of ... |

## Composition

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Command Palette UI](command-palette-ui.md) | established | 3,604 | An application with many features, settings, and navigation destinations forces a user relying purely on visual menus and clicks to remember where each specific action lives, and ... |
| [Form Action](form-action.md) | established | 3,655 | A form submitted the traditional way moves the browser to a new URL and reloads the whole page, while a form submitted through raw client-side JavaScript needs the developer to ... |
| [Headless Component](headless-component.md) | established | 3,488 | A component that bundles its behavior and its visual markup together forces every consumer to accept both, even when a consumer genuinely needs the same behavior, an accessible ... |
| [Slot and Children as API](slot-and-children-as-api.md) | canonical | 3,469 | A component that hard-codes every piece of its own content forces a consumer to accept exactly that content, or to duplicate the entire component only to change one piece of it. |

## Data Fetching

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Server Action](server-action.md) | canonical | 3,637 | A traditional client-server data mutation needs a developer to build and maintain a separate API endpoint, wire a client-side fetch call to that endpoint, and manually keep the ... |

## Delivery Strategy

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Progressive Enhancement](progressive-enhancement.md) | canonical | 3,686 | Before Progressive Enhancement was named, a common alternative approach, graceful degradation, started from the richest possible experience, built for the most capable browsers ... |

## Error Handling

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Error Boundary](error-boundary.md) | canonical | 3,556 | React's own documentation states the default behavior a rendering error causes plainly. |

## Event Handling

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Debounce and Throttle](debounce-and-throttle.md) | canonical | 3,669 | An event such as a keystroke, a scroll, or a window resize can fire many times in rapid succession, and attaching an expensive handler directly to that event, a network request, a ... |

## Interaction Pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Optimistic UI](optimistic-ui.md) | established | 3,623 | A user action that triggers a network request, liking a post, sending a message, adding an item to a list, commonly leaves the interface showing its prior, unchanged state until ... |

## Loading Strategy

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Code Splitting](code-splitting.md) | canonical | 3,663 | A JavaScript application that bundles its entire codebase into a single file forces every visitor to download, parse, and evaluate code for every feature the application has, even ... |
| [Hydration Island](hydration-island.md) | established | 3,564 | Even once a page has been structured into islands, a real choice remains for each individual island, exactly when its JavaScript should load and hydrate. |
| [Infinite Scroll](infinite-scroll.md) | established | 3,738 | A traditional, paginated list requires the user to explicitly click a next-page control and wait for a full page reload, or a partial page update, to see more content, an ... |
| [PRPL Pattern](prpl-pattern.md) | established | 3,773 | A web application's first visit on a slow or metered mobile network faces a real tension. |
| [Resource Hints](resource-hints.md) | canonical | 3,923 | A browser discovers most of a page's resources by parsing its HTML and CSS as it goes, which means a resource referenced deep in a stylesheet, or fetched only after a script runs ... |
| [Route-based Lazy Loading](route-based-lazy-loading.md) | canonical | 3,577 | A multi-route application whose routes are all bundled together forces every visitor to fetch and evaluate the code for every route, even the ones that specific visit never ... |
| [Skeleton and Suspense](skeleton-and-suspense.md) | canonical | 3,597 | A component whose data has not yet loaded commonly renders nothing at all, an empty region of the page, or a generic, centered spinner with no relation to the content that will ... |

## Rendering Strategy

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Islands Architecture](islands-architecture.md) | established | 3,638 | A single-page application that hydrates its entire page as one monolithic JavaScript bundle ships and executes JavaScript for every part of the page, including large static ... |
| [Server Components](server-components.md) | canonical | 3,834 | A component tree rendered entirely on the client, even one that is server-side rendered for the initial HTML, ships every component's own JavaScript to the browser for hydration ... |
| [Virtual List](virtual-list.md) | canonical | 3,802 | A list rendered in full, every item mounted as a real DOM node regardless of whether the user can currently see it, works fine for a short list but degrades badly as the list ... |

## State Management

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Context Selector](context-selector.md) | established | 3,677 | React's own documentation states plainly how context re-rendering works. |
| [Flux](flux.md) | deprecated | 3,629 | Traditional MVC-style architectures let a view update a model directly, and let multiple models observe and update one another, which becomes difficult to reason about as an ... |
| [Reducer Hook](reducer-hook.md) | canonical | 3,580 | A component whose state updates are spread across many individual event handlers, each directly calling its own state setter, becomes hard to reason about as the number of related ... |
| [Redux](redux.md) | canonical | 3,663 | Flux's original architecture solved unidirectional data flow with several independent stores, each holding its own slice of state and its own update logic, which worked but left ... |
| [Signals](signals.md) | established | 3,294 | A component-based UI framework built on a virtual DOM diff and re-render cycle, such as React, re-runs an entire component function whenever any piece of its state changes, then ... |
| [State Machine UI](state-machine-ui.md) | established | 3,616 | A component with several loading, error, and success conditions is commonly modeled with several independent boolean flags, such as isLoading, isError, and hasData, tracked as ... |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
