---
name: API Versioning
slug: api-versioning
family: 19-api-design
category: Data Fetching
aliases: [Header-Based Versioning, Release-Based API Versioning]
first_described: 'Stripe, official API versioning documentation'
maturity: canonical
related: [cursor-based-pagination, rest-resource-modeling]
incompatible_with: []
verified: 2026-08-22
---

# API Versioning

## 1. Name, aliases, and lineage

API Versioning. Also called Header-Based Versioning or Release-Based API Versioning. The pattern is explicitly marking an API's compatibility contract with a version identifier, so a provider can evolve the API, including making a breaking change, without breaking every existing client that has not yet moved to the new version. Stripe's own versioning documentation describes its own release model directly. each major release, such as Acacia, includes changes that are not backward compatible with previous releases, upgrading to a new major release can require updates to existing code, each monthly release includes only backward compatible changes and uses the same name as the last major release, you can safely upgrade to a new monthly release without breaking any existing code (https://docs.stripe.com/api/versioning).

The lineage runs from the practical reality that an API used by many independent clients cannot simply change shape underneath them without warning, and every mature provider settles on some explicit mechanism for a client to declare which version's contract it was built against. Stripe's own mechanism is a request header the client can set explicitly. by default, requests made with curl use your Stripe account's default API version, controlled in Workbench, unless you override it by setting the Stripe Version header (https://docs.stripe.com/api/versioning).

## 2. Problem and context

An API that never changes never needs versioning, but a real API evolves. fields are added, renamed, or removed, behavior is corrected, new capabilities are introduced. If every change applied instantly and uniformly to every client, a single breaking change could silently fail every integration built against the API's previous shape, with no warning and no chance for the client's own team to prepare.

The problem this pattern solves is letting a provider ship a breaking change safely, by giving each client an explicit, stable contract, its declared version, that keeps behaving the way it always did until the client itself chooses to move to a newer version, rather than being forced onto a new contract without warning.

## 3. Forces

- Supporting multiple versions simultaneously means the provider carries real maintenance cost for every version still in active use, not just the newest one.
- A version identifier has to be simple enough for a client to set correctly, or clients end up on an unintended default version by accident.
- Deciding what counts as a breaking change, versus a safe, backward-compatible addition, is itself a real judgment call that has to be applied consistently across every release.
- A version that is supported forever accumulates unbounded maintenance burden, but deprecating and eventually retiring an old version risks breaking a client that never migrated.
- The versioning mechanism itself, a header, a URL segment, a media type, has to be chosen once and is difficult to change later without repeating the exact same compatibility problem this pattern exists to solve.

## 4. Applicability and non-applicability

Use API Versioning for any API with external, independently-deployed clients whose release cycles the provider does not control, especially a public API, where a breaking change without warning would break real integrations the provider cannot coordinate directly with.

This pattern is a non-applicability fit for a purely internal API where every client is deployed and controlled by the same team that owns the API, and where a breaking change can be coordinated directly with a synchronized deployment instead. It is also often unnecessary overhead for a genuinely short-lived or experimental API not yet relied on by any real external integration.

## 5. Structure

- Version identifier. the explicit value, a dated string, a semantic version, a named release, that names one specific version of the API's contract.
- Version transport mechanism. how the client communicates its chosen version, a header, a URL path segment, or a media type parameter.
- Default version. the version a request is treated as using when the client does not specify one explicitly.
- Breaking versus non-breaking change classification. the provider's own rule for which kind of change requires a new version and which can ship within the current one.
- Deprecation and sunset policy. the provider's documented timeline for how long an older version stays supported before it is retired.

## 6. ASCII structure diagram

```

  Client request
  GET /v1/resource
  Stripe-Version: 2025-11-01
     |
     v
  Provider
  +----------------------------------------------------+
  |  version 2024-06-01  (older, still supported)       |
  |  version 2025-11-01  (client's requested version)   |  <- routed here
  |  version 2026-07-29  (current, latest)               |
  +----------------------------------------------------+
     |
     v
  response shaped exactly as version 2025-11-01 promised

```

## 7. Dynamics

1. The provider ships a change to the API, and classifies it as either backward compatible or breaking.
2. A backward-compatible change ships within the current version, reachable by every existing client without any action on their part.
3. A breaking change instead ships as a new version, because each major release includes changes that are not backward compatible with previous releases, and upgrading to a new major release can require updates to existing code (https://docs.stripe.com/api/versioning).
4. A client declares which version it wants by setting the version transport mechanism on its request, or relies on the provider's default when it sets nothing, since by default requests use the account's default API version unless overridden by setting the version header explicitly (https://docs.stripe.com/api/versioning).
5. The provider routes the request to the logic matching the client's declared version, returning a response shaped exactly as that version's contract promises, regardless of how many newer versions have shipped since.
6. When a client is ready, it updates its declared version deliberately, on its own schedule, moving to the newer contract only when its own team has adapted to any breaking change along the way.

## 8. Implementation variants

- Header-based versioning. the client sets a dedicated request header naming its chosen version, keeping the URL itself stable across versions.
- URL path versioning. the version appears directly in the URL path, such as a leading version segment, the most visible and easiest-to-discover variant.
- Media type versioning. the version is encoded as a parameter on the Accept or Content Type header's media type value, keeping both the URL and a dedicated header out of the picture entirely.
- Dated, rolling versions. each version is named by the date it shipped, and the provider internally compresses each request forward through every intervening version's transformation logic to reach the current implementation.

## 9. Known production uses

- Stripe's own API is the reference implementation most developers learn this pattern from directly, with dated, named releases and header-based version selection.
- GitHub's REST API uses a dedicated version header with a documented default, applying the same explicit-version-or-fall-back-to-default model.
- Many public REST APIs, across a very wide range of providers, expose a leading version segment directly in their URL path, the most visible variant of this pattern.

## 10. Consequences

Benefits.

- A client's integration keeps working exactly as it did, even as the provider ships breaking changes to newer versions, because the client's declared version stays stable until it chooses to move.
- The provider can evolve the API meaningfully over time, including making genuinely breaking changes, without a single uncoordinated breaking change reaching every client at once.
- A client migrates to a new version on its own schedule, giving its own team time to adapt to whatever changed.

Costs.

- The provider carries real ongoing maintenance cost for every version still in active use, not only the newest one.
- Classifying a change as breaking or non-breaking consistently is a real judgment call, and getting it wrong in either direction has a real cost.
- An old version supported indefinitely accumulates unbounded maintenance burden, while retiring it too soon risks breaking a client that has not yet migrated.

## 11. Failure modes

- Silent breaking change. a change shipped within the current version that was actually breaking, misclassified by the provider, breaks every client on that version without warning, exactly the failure this pattern exists to prevent.
- Unintended default version. a client that never explicitly sets its version can be moved onto a newer default without realizing it, if the provider's default silently advances over time.
- Abandoned version never retired. a version kept supported indefinitely with no client actually using it any longer wastes the provider's ongoing maintenance effort.
- Premature version retirement. a version retired before every client has genuinely migrated off it breaks the exact clients this pattern was meant to protect.

## 12. Trade-off matrix

| Dimension | With versioning | Without versioning |

|---|---|---|

| Safety of a breaking change | Isolated to clients who opt into the new version | Reaches every client immediately |
| Client migration control | Client chooses its own schedule | No choice, forced onto the change |
| Provider maintenance burden | Must support multiple versions | Only one version to maintain |
| API evolution speed | Can move faster, breaking changes are safe | Must be extremely conservative |
| Discoverability of the active contract | Explicit, named, documented per version | Implicit, whatever the API currently does |

## 13. Related and incompatible patterns

Related to Cursor-based Pagination and REST Resource Modeling, both of whose own shape can itself be a source of a breaking change that this pattern's versioning contract has to accommodate cleanly. Not incompatible with any of the other family 19 patterns. API Versioning is orthogonal to how resources are modeled or how a collection is paginated, and sits alongside them as its own, independent concern.

## 14. Refactoring path in and out

Introducing it.

1. Choose a version transport mechanism, a header, a URL segment, or a media type parameter, and a version naming scheme.
2. Establish the provider's own rule for classifying a change as breaking versus backward-compatible, and document it.
3. Ship the current API behavior as an explicit initial version, so every existing client keeps working exactly as it always did.
4. Publish a deprecation and sunset policy stating how long an older version stays supported before it is retired.

Removing it.

1. Confirm every client genuinely no longer needs multiple simultaneously-supported versions, typically because the API has stabilized or moved to a fully internal-only surface.
2. Communicate a final sunset date for every version except the one being kept, giving every remaining client time to migrate.
3. Remove the version transport mechanism and the per-version routing logic once every client has confirmed migration.
4. Confirm no client is still sending an old version identifier before the removal ships.

## 15. Testing and verification

- Test that a request explicitly declaring an older version continues to receive that version's exact contract, even after a newer version has shipped.
- Test the default-version behavior explicitly, confirming a request with no version declared receives the documented default rather than an unintended one.
- Test that a breaking change genuinely only reaches clients on the new version, and never leaks into an older, still-supported version's behavior.
- Test the sunset behavior for a retired version, confirming it fails predictably and informatively rather than silently returning an unexpected shape.

## 16. Observability signals

- Request volume broken down by declared version, the direct signal for how much traffic each supported version still carries.
- Rate of requests with no version explicitly declared, falling back to the default.
- Time since each version's last real client request, useful for judging when a version is genuinely safe to retire.
- Error rate per version, watched separately, since a regression introduced for one version should never silently affect another.

## 17. Security and privacy implications

A retired, unsupported version left reachable, rather than genuinely decommissioned, can become a forgotten attack surface running old, unpatched logic that no longer receives security fixes applied to the current version. A provider that changes what data a field exposes between versions has to confirm the change does not accidentally leak more data to clients on an older version than that version's contract ever intended to expose.

## 18. Code examples

### Swift

```swift

enum APIVersion: String {
    case v20250101 = "2025-01-01"
    case v20260701 = "2026-07-01"
}

struct VersionedRequest {
    let version: APIVersion

    // Builds the header the server uses to route this request to the right version.
    func headers() -> [String: String] {
        ["API-Version": version.rawValue]
    }
}

```

### Kotlin

```kotlin

enum class ApiVersion(val value: String) {
    V20250101("2025-01-01"),
    V20260701("2026-07-01"),
}

class VersionedRequest(private val version: ApiVersion) {
    // Builds the header the server uses to route this request to the right version.
    fun headers(): Map<String, String> {
        return mapOf("API-Version" to version.value)
    }
}

```

### Python

```python

class VersionedRequest:
    def __init__(self, version):
        self.version = version

    def headers(self):
        """Builds the header the server uses to route this request to the right version."""
        return {"API-Version": self.version}

```

## 19. References

- Stripe, official API versioning documentation, https://docs.stripe.com/api/versioning
