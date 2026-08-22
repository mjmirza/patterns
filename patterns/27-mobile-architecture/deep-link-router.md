---
name: Deep Link Router
slug: deep-link-router
family: 27-mobile-architecture
category: Structural
aliases: [URL Router (Mobile), Route Table, Link Resolver]
first_described: 'Google Android Developers, "Deep link into your app with Navigation" architecture guidance'
maturity: canonical
related: [coordinator-pattern, feature-modules]
incompatible_with: []
verified: 2026-08-22
---

# Deep Link Router

## 1. Name and lineage

Deep Link Router. Also called a URL Router, a Route Table, or a Link Resolver in mobile codebases. The name describes the job directly. one component owns the mapping from an incoming URL, whether an Android implicit intent, an iOS Universal Link, or an in-app navigation call, to the screen or feature that should handle it.

The pattern grew out of two separate pressures that converged around the same period. On Android, the platform's own intent-filter matching gave every app a way to receive a link, but did nothing to resolve WHICH internal screen should open once the link arrived, so teams built their own resolution layer on top. On the web side, single-page-app routers (React Router, Vue Router) had already normalized the idea of a declarative URL-to-component table years earlier, and as mobile apps modularized into independent feature modules, that same declarative table became the obvious way to decouple a deep link from any one feature's internals. Flutter's go_router, built directly on the platform Router API, is a modern, explicit instance of the same idea applied to a single-codebase, multi-platform app.

## 2. Problem and context

An app receives a link from outside itself. a push notification, an email, a web page, a QR code, another app, or a Universal Link tapped in Safari. The operating system hands that link to the app, but the app still has to figure out what to DO with it. which screen to show, what data to load first, and what to do if the user is not logged in or the target no longer exists.

Google's own Android guide frames the starting point plainly. In Android, a deep link is a link that takes you directly to a specific destination within an app (https://developer.android.com/guide/navigation/design/deep-link). That destination-resolution step is exactly the job this pattern names. Without a dedicated router, resolution logic sprawls across every screen and every feature module that might be a link target, each one parsing URLs its own way, duplicating validation, and quietly diverging from its siblings. A modularized app makes this worse, not better: a feature module built to be independently buildable and independently testable cannot, by construction, know the internal route names of every OTHER feature module it might need to link into.

The problem sharpens further once the app has more than one link SOURCE (push, web, QR, in-app) and more than one link SHAPE per destination (a short-lived share link, a canonical deep link, a legacy scheme). Each source and each shape needs the same destination resolved the same way, which is a strong argument for one shared resolver rather than N copies of similar logic (per the https://developer.android.com/guide/navigation/design/deep-link matching rules for URI, action, and MIME type).

## 3. Forces

- A link can arrive while the app is cold-started, backgrounded, or already on the exact screen it targets, and the router has to produce the right navigation action in all three cases.
- The destination feature module may not be loaded yet, so resolution cannot assume the target screen's code is already resident.
- Link shapes evolve. a marketing team wants a new UTM-tagged variant, a legacy scheme must keep working for old installs, and the router is the one place that absorbs that churn without touching every feature.
- Deep links are a common attack surface (open redirect, unauthenticated access to a gated screen), so the router is also a natural place to enforce auth and input validation once, rather than trusting every feature to do it independently.
- Over-centralizing invites a god object that imports every feature module only to reference its screens, defeating the whole point of modularization.

## 4. Applicability

Use a deep link router when the app is modularized into independent feature modules and needs to open a specific screen from outside its own navigation flow (push notification, web link, another app, QR code, or a saved link). It is also the right fit for a single-module app that already has more than a handful of distinct external entry points, since even a small app benefits from one place that owns URI-to-screen resolution rather than parsing logic scattered across activities or view controllers.

## 5. Non-applicability

Skip a dedicated router for an app with a single, simple entry point (for example, only opening to the home screen regardless of the link received). A one-screen or two-screen app gains nothing from an indirection layer that a single conditional already covers, and adding one prematurely is over-engineering. It also does not replace a feature's own internal navigation. a router resolves an EXTERNAL link to an entry point; the feature module still owns everything that happens after the user lands on its first screen.

## 6. Structure

- Route table. a declarative list of path patterns (with typed parameters) mapped to a screen identifier, owned by the router, not by any single feature.
- Link parser. normalizes an incoming URI (Android intent data, iOS NSUserActivity or URL, or an in-app string) into a canonical form the route table can match against.
- Resolver. walks the route table against the parsed link and returns either a matched destination plus extracted parameters, or a not-found result.
- Feature registry. a lightweight, decoupled interface (a protocol, an interface, or a lazily-loaded module reference) that lets each feature module register its own routes without the router importing that feature's concrete types.
- Navigator adapter. the thin layer that turns a resolved destination into an actual navigation call on the platform's real navigation stack (Jetpack Navigation, UIKit or SwiftUI navigation, or a coordinator).
- Guard chain. optional, ordered checks (authentication, feature flag, onboarding-complete) the resolver runs before handing off to the navigator.

## 7. ASCII diagram

```
  external link (push, web, QR, another app)
        |
        v
  +-----------------+
  |   Link Parser   |  normalizes into a canonical URI
  +-----------------+
        |
        v
  +-----------------+      +---------------------+
  |     Resolver     |----->|   Route Table       |
  |  (match + guard) |<-----| (path -> screen id) |
  +-----------------+      +---------------------+
        |                          ^
        | matched dest + params    | registers routes
        v                          |
  +-----------------+      +---------------------+
  | Navigator Adapter|      | Feature A registry  |
  +-----------------+      +---------------------+
        |                  | Feature B registry   |
        v                  +---------------------+
  real navigation stack
```

## 8. Dynamics trace

1. The OS delivers an incoming link to the app (a tapped push notification opens the app with an intent extra, or a Universal Link is opened directly).
2. The app's entry point (an Activity, SceneDelegate, or the app's root composable) hands the raw link to the Link Parser.
3. The parser normalizes it into a canonical URI and passes it to the Resolver.
4. The Resolver walks the Route Table for a matching pattern. per Android's own documented matching order, URI argument matching is prioritized first, followed by action, and then MIME type (https://developer.android.com/guide/navigation/design/deep-link), so a scheme should follow the same priority order to stay consistent with platform behavior even when the router is fully custom.
5. If a match is found, the Resolver runs the Guard chain (for example, checking whether the user is authenticated for a gated screen).
6. If all guards pass, the Resolver hands a resolved destination plus parameters to the Navigator Adapter, which loads the target feature module if it is not already resident, then performs the real navigation call.
7. If no route matches, or a guard fails, the Resolver returns a fallback result, usually the app's home screen, or a login screen with the original link preserved to resume after authentication.

## 9. Implementation variants

- Declarative table with typed parameters. go_router's own approach lets developers parse path and query parameters using a template syntax such as user id (https://pub.dev/packages/go_router), which is the clearest modern example: routes are declared once, in one file, with compile-time-checked parameter extraction.
- Annotation or code-generation based. each feature module annotates its own destinations, and a build-time step aggregates them into one generated route table, avoiding a hand-maintained central file while still keeping resolution centralized at runtime.
- Runtime registry. feature modules register their routes imperatively at app startup (via a small shared interface), trading compile-time safety for looser coupling and easier dynamic feature loading.
- Platform-native plus thin wrapper. lean on the OS's own intent-filter or Universal Link matching for the outer layer, with a thin custom router underneath only for the app-internal resolution and guard logic.

## 10. Known production uses

- Android's Jetpack Navigation component ships first-class deep link support. Navigation automatically handles deep links by calling the handleDeepLink function to process any explicit or implicit deep links within the Intent (https://developer.android.com/guide/navigation/design/deep-link), used across Android apps as the default routing layer.
- Flutter's go_router package describes itself as a declarative routing package for Flutter that uses the Router API to provide a convenient, url-based API for switching between different screens (https://pub.dev/packages/go_router), and is the officially recommended routing solution referenced from Flutter's own navigation documentation, widely adopted across production Flutter apps that need deep link support.
- Large modularized apps at companies with many independent feature teams (e-commerce, banking, and media apps with dozens of feature modules) commonly build an internal equivalent of this pattern specifically so that marketing, push, and web teams can generate links without needing to know any feature module's internal route names.

## 11. Consequences

### Benefits

- One place owns URI-to-screen resolution, so link shape changes touch one file instead of every feature that might be a target.
- Feature modules stay independently buildable, since none of them needs to import another feature's concrete navigation types to be linked into.
- Auth and validation guards run once, centrally, instead of being reimplemented per feature with a risk of one feature forgetting the check.
- Marketing, push, and web teams get a single, stable contract (the route table) rather than needing engineering support for every new link.

### Costs

- The router becomes a shared dependency every feature module touches indirectly, so a bug in the router has app-wide blast radius.
- A poorly bounded route table can leak feature-specific parameter shapes into a supposedly generic layer, quietly recoupling the modules it was meant to decouple.
- Cold-start deep links (the app was not running) require extra care to defer navigation until the app's own startup sequence and any required data are ready, which adds real complexity the naive version of this pattern glosses over.

## 12. Failure modes

- Silent no-match. a link that matches no route falls through to a generic home screen with no feedback, so a broken marketing link looks like a working app rather than a bug.
- Guard-order bugs. an auth guard registered AFTER a data-loading guard can leak a gated screen's existence (or a flash of its content) before the redirect to login completes.
- Stale route table. a feature module renames or removes a screen without updating the shared route table, producing a resolved destination that no longer exists at runtime.
- Cold-start race. the router resolves a destination before the feature module's dependencies (a repository, a session token) are ready, crashing or silently discarding the navigation.
- Ambiguous matches. two feature modules register overlapping path patterns, and the outcome depends on undocumented registration order rather than an explicit precedence rule.

## 13. Trade-off matrix

| Dimension | Centralized declarative table | Runtime registry per feature |
|---|---|---|
| Compile-time safety | High, typed parameters caught at build time | Low, routes register imperatively at runtime |
| Coupling to feature internals | Low, route table only knows public path strings | Low, but registration order matters |
| Dynamic or on-demand feature loading | Harder, table is usually static | Easier, features register only once loaded |
| Onboarding a new feature | Edit one shared file | Add a self-contained registration call |
| Risk of stale entries | Higher, shared file can be forgotten | Lower, registration lives with the feature |

## 14. Related and incompatible patterns

### Related

- Coordinator Pattern. a router resolves an EXTERNAL link to an entry point; a coordinator then frequently takes over to drive the multi-screen flow that follows.
- Feature Modules. the router exists largely BECAUSE feature modules are independently buildable and cannot reference each other's internals directly.

### Incompatible with

- None. this pattern composes with essentially every mobile navigation architecture, since it operates one layer above internal navigation rather than replacing it.

## 15. Refactoring path

### Introducing it

1. Inventory every place in the codebase that currently parses an incoming URI or intent, across every feature module and the app shell.
2. Extract a single Route Table listing every existing destination as an explicit path pattern, even before wiring any resolution logic to it.
3. Build the Resolver and Link Parser, initially delegating to the OLD per-feature parsing as a fallback for anything not yet in the table.
4. Migrate one feature at a time onto the new table, removing its old parsing code once the table's entry is verified against real links.
5. Once every feature is migrated, delete the fallback path entirely.

### Removing it

1. Confirm the app has shrunk to few enough entry points that the indirection no longer earns its cost (rare, but possible after a large feature consolidation).
2. Inline each route table entry back into the single remaining call site that needs it.
3. Delete the router, resolver, and guard chain once no route table entries remain.

## 16. Testing and verification

- Unit-test the Resolver in isolation against a fixed route table, asserting that every known URI shape (including legacy schemes) resolves to the expected destination and parameters.
- Test the Guard chain independently, asserting that an unauthenticated request to a gated route is redirected rather than resolved directly.
- Cover the not-found path explicitly. an unrecognized URI must resolve to a defined fallback, never to a crash or an undefined navigation state.
- On Android, verify Android App Links with the platform's own verification tooling to confirm the OS actually routes matching links to the app instead of a browser disambiguation dialog.
- Add an integration test that simulates a cold start with a deep link present, asserting the app reaches the correct screen only after its startup dependencies are ready.

## 17. Observability signals

- Log every resolved link with its matched route pattern, so a spike in no-match results after a release surfaces a broken link shape quickly.
- Track guard-rejection counts per route (for example, how often a gated route is hit by an unauthenticated session), which distinguishes a healthy auth wall from a link that is being shared somewhere it should not be.
- Track cold-start-to-destination latency for deep links specifically, since this path is more failure-prone than warm navigation and regressions here are easy to miss in aggregate app-launch metrics.

## 18. Security and privacy implications

- Treat every incoming link as untrusted input. validate and sanitize path parameters before using them to fetch data, exactly as any other external input would be validated.
- Guard against open-redirect-style abuse where a crafted link parameter could be used to redirect the user somewhere unintended (including out of the app, via a parameter that is later used to build an outbound URL).
- Enforce authentication and authorization in the Guard chain for any gated route, never relying on the destination screen alone to re-check access, since a link can be constructed to target a screen directly and bypass any checks that only exist in the normal in-app navigation path.
- Avoid logging full incoming URIs when parameters may carry personal data (an email address or a token embedded in a share link); log the matched route pattern instead of the raw URI where possible.

## 19. Code examples

### Python

```python
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ResolvedRoute:
    screen_id: str
    params: dict


class DeepLinkRouter:
    def __init__(self) -> None:
        self._patterns = {}
        self._guards = []

    def register(self, pattern, screen_id):
        self._patterns[pattern] = screen_id

    def add_guard(self, guard):
        self._guards.append(guard)

    def resolve(self, path):
        for pattern, screen_id in self._patterns.items():
            params = _match(pattern, path)
            if params is None:
                continue
            for guard in self._guards:
                if not guard(screen_id):
                    return ResolvedRoute(screen_id='login', params={'return_to': path})
            return ResolvedRoute(screen_id=screen_id, params=params)
        return None


def _match(pattern, path):
    pattern_parts = pattern.strip('/').split('/')
    path_parts = path.strip('/').split('/')
    if len(pattern_parts) != len(path_parts):
        return None
    params = {}
    for p_part, v_part in zip(pattern_parts, path_parts):
        if p_part.startswith(':'):
            params[p_part[1:]] = v_part
        elif p_part != v_part:
            return None
    return params


router = DeepLinkRouter()
router.register('/user/:id', 'user_profile')
router.add_guard(lambda screen: screen != 'checkout' or user_is_authenticated())
resolved = router.resolve('/user/482')
print('opening', resolved.screen_id if resolved else 'fallback home')
```

### Kotlin

```kotlin
data class ResolvedRoute(val screenId: String, val params: Map<String, String>)

class DeepLinkRouter {
    private val patterns = mutableMapOf<String, String>()
    private val guards = mutableListOf<(String) -> Boolean>()

    fun register(pattern: String, screenId: String) {
        patterns[pattern] = screenId
    }

    fun addGuard(guard: (String) -> Boolean) {
        guards.add(guard)
    }

    fun resolve(path: String): ResolvedRoute? {
        for ((pattern, screenId) in patterns) {
            val params = match(pattern, path) ?: continue
            for (guard in guards) {
                if (!guard(screenId)) {
                    val fallback = mapOf('returnTo' to path)
                    return ResolvedRoute('login', fallback)
                }
            }
            return ResolvedRoute(screenId, params)
        }
        return null
    }

    private fun match(pattern: String, path: String): Map<String, String>? {
        val patternParts = pattern.trim('/').split('/')
        val pathParts = path.trim('/').split('/')
        if (patternParts.size != pathParts.size) return null
        val params = mutableMapOf<String, String>()
        patternParts.zip(pathParts).forEach { (p, v) ->
            if (p.startsWith(':')) params[p.drop(1)] = v
            else if (p != v) return null
        }
        return params
    }
}

val router = DeepLinkRouter()
router.register('/user/:id', 'user_profile')
router.addGuard { screenId -> screenId != 'checkout' || userIsAuthenticated() }
val resolved = router.resolve('/user/482')
val label = resolved?.screenId ?: 'fallback home'
println('opening ' + label)
```

### Swift

```swift
struct ResolvedRoute {
    let screenId: String
    let params: [String: String]
}

final class DeepLinkRouter {
    private var patterns: [String: String] = [:]
    private var guards: [(String) -> Bool] = []

    func register(pattern: String, screenId: String) {
        patterns[pattern] = screenId
    }

    func addGuard(_ check: @escaping (String) -> Bool) {
        guards.append(check)
    }

    func resolve(path: String) -> ResolvedRoute? {
        for (pattern, screenId) in patterns {
            guard let params = match(pattern: pattern, path: path) else { continue }
            for check in guards where !check(screenId) {
                let fallback = ["returnTo": path]
                return ResolvedRoute(screenId: "login", params: fallback)
            }
            return ResolvedRoute(screenId: screenId, params: params)
        }
        return nil
    }

    private func match(pattern: String, path: String) -> [String: String]? {
        let patternParts = pattern.split(separator: "/").map(String.init)
        let pathParts = path.split(separator: "/").map(String.init)
        guard patternParts.count == pathParts.count else { return nil }
        var params: [String: String] = [:]
        for (p, v) in zip(patternParts, pathParts) {
            if p.hasPrefix(":") {
                params[String(p.dropFirst())] = v
            } else if p != v {
                return nil
            }
        }
        return params
    }
}

let router = DeepLinkRouter()
router.register(pattern: "/user/:id", screenId: "user_profile")
router.addGuard { screenId in screenId != "checkout" || userIsAuthenticated() }
let resolved = router.resolve(path: "/user/482")
let label = resolved?.screenId ?? "fallback home"
print("opening " + label)
```

## 20. References

- Android Developers, Deep link into your app with Navigation (https://developer.android.com/guide/navigation/design/deep-link)
- go_router package, pub.dev (https://pub.dev/packages/go_router)
