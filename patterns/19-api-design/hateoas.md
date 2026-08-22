---
name: HATEOAS
slug: hateoas
family: 19-api-design
category: Data Fetching
aliases: [Hypermedia As The Engine Of Application State, Hypermedia-Driven API]
first_described: 'Roy Fielding, REST APIs must be hypertext-driven, 2008'
maturity: canonical
related: [rest-resource-modeling, api-versioning]
incompatible_with: []
verified: 2026-08-22
---

# HATEOAS

## 1. Name, aliases, and lineage

HATEOAS. Hypermedia As The Engine Of Application State, also called a Hypermedia-Driven API. The pattern is including links describing the available next actions or related resources directly in an API response, so a client discovers what it can do next by following links the server provides, rather than hardcoding URL structure the client learned out of band. Roy Fielding, who defined REST, wrote his own canonical clarification of this exact requirement. if the engine of application state, and hence the API, is not being driven by hypertext, then it cannot be RESTful and cannot be a REST API (https://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven).

The lineage runs directly from Fielding's own frustration that many APIs calling themselves RESTful never actually implemented this constraint, prompting the 2008 post that clarifies it plainly. Fielding states the reason directly, in terms of coupling. a REST API must not define fixed resource names or hierarchies, an obvious coupling of client and server, servers must have the freedom to control their own namespace (https://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven).

## 2. Problem and context

A client built against an API's documented URL structure, hardcoding every endpoint path it will ever call, is tightly coupled to that exact structure. If the server later reorganizes its URLs, moves a resource under a different path, or changes which actions are actually available given the current state of a resource, every client baked with the old structure breaks or silently attempts an action that is no longer valid.

The problem this pattern solves is decoupling the client from the server's specific URL structure, by having the server tell the client, in each response, exactly which related resources and next actions are currently available, as links the client follows rather than constructs. The client's logic becomes driven by what the server says is possible right now, not by a URL structure memorized in advance.

## 3. Forces

- A client that follows links dynamically is more resilient to a server-side URL restructuring, but that dynamic discovery is genuinely harder to implement than simply hardcoding a known set of endpoints.
- Every response carrying its own set of links adds real payload size and server-side construction cost that a plain data response without links does not carry.
- A client still has to know, in advance, what a given link relation name MEANS, even if it does not know the exact URL, so some out-of-band knowledge is never fully eliminated.
- Representing state-dependent availability correctly, only including a link for an action the current state genuinely allows, requires real server-side logic that a static response shape does not need.
- Tooling, documentation, and client libraries built around a fixed, known set of endpoints are more mature and more common than tooling built around dynamic link discovery, making this pattern a real departure from typical practice.

## 4. Applicability and non-applicability

Use HATEOAS for an API whose resources have genuinely state-dependent available actions, an order that can be canceled only while unshipped, a document that can be published only once approved, where telling the client exactly which actions are currently valid is more valuable than the added response size and implementation cost. It is also well suited to a long-lived API whose URL structure is genuinely expected to evolve over its lifetime.

This pattern is a non-applicability fit for an API whose clients are tightly coordinated with the same team that owns the API, where a URL structure change can simply be communicated and updated directly, without needing dynamic discovery to absorb it. It is also often unnecessary overhead for a small, stable API whose URL structure genuinely never changes and whose available actions do not meaningfully depend on resource state.

## 5. Structure

- Resource representation. the data payload describing one resource's current state.
- Link. one entry describing a related resource or an available action, carrying its own URL and a relation name describing what it means.
- Link relation name. the label, ideally a standard or documented one, telling the client what a given link is for, since the client still needs to know what to look for.
- State-dependent link inclusion. the server-side logic that decides which links to include based on the resource's current, real state.
- Client link-following logic. the client-side code that reads the response's links and acts on them, instead of constructing a URL from a hardcoded template.

## 6. ASCII structure diagram

```

  GET /orders/42

  {
    "id": 42,
    "status": "pending",
    "links": [
      { "rel": "self", "href": "/orders/42" },
      { "rel": "cancel", "href": "/orders/42/cancel" }
    ]
  }

  Once status becomes "shipped", the cancel link is no longer included,
  and the client never even considers attempting that action.

```

## 7. Dynamics

1. A client requests a resource, and the server responds with the resource's current data alongside a set of links.
2. The server derives which links to include from the resource's actual current state, including only a link for an action that is genuinely available right now.
3. The client reads the response's links, rather than constructing a URL from a hardcoded path template, treating the fixed resource names or hierarchies as something it must not assume, per the same discipline a REST API must not define fixed resource names or hierarchies, an obvious coupling of client and server (https://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven).
4. To take a next action, the client follows the corresponding link's URL directly, rather than assembling that URL itself from prior knowledge.
5. If the server later reorganizes its URL structure, a client built this way keeps working unchanged, because it never depended on the exact URL shape in the first place, only on the link relation names it already understood.
6. As the resource's state changes over time, the set of links the server includes changes with it, and the client's available actions change correspondingly, without any separate coordination between client and server.

## 8. Implementation variants

- Simple link array. each response carries a plain array of link objects, each with a relation name and a URL, the most straightforward variant to implement.
- Standardized hypermedia format. the response follows a documented hypermedia media type with its own conventions for representing links and embedded resources.
- Form-like action description. a link is accompanied by a description of what input the action expects, letting a client construct the follow-up request without prior knowledge of its shape.
- Partial hypermedia adoption. only the state-dependent, genuinely conditional actions carry links, while stable, always-available resource paths are still documented and used directly.

## 9. Known production uses

- PayPal's REST API includes hypermedia links in many of its responses, particularly around payment and order state transitions where the available next action genuinely depends on the current state.
- GitHub's REST API includes link relations in several of its responses and uses a dedicated header convention for paginated link discovery, a partial, targeted application of the same discovery idea.
- Amazon's own API Gateway and several AWS service APIs include hypermedia-style links in responses describing related and next-step resources for certain state-dependent operations.

## 10. Consequences

Benefits.

- A client is decoupled from the server's exact URL structure, surviving a server-side reorganization without breaking.
- The available actions a client sees always match the resource's actual current state, since the server derives the links dynamically rather than the client guessing.
- The server keeps the freedom to evolve its URL structure over time, per Fielding's own framing that servers must have the freedom to control their own namespace (https://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven).

Costs.

- Every response carries additional payload for its links, and the server does real extra work deciding which links currently apply.
- Implementing dynamic link-following on the client is genuinely more work than hardcoding a known set of endpoints.
- Tooling, documentation generators, and client SDK generators built around a fixed set of endpoints are more mature and more common than tooling built around this pattern.

## 11. Failure modes

- Client bypasses the links anyway. a client that still hardcodes URLs despite the server providing links gets none of this pattern's decoupling benefit, and breaks exactly when the server reorganizes.
- Stale or incorrect link inclusion. a server that includes a link for an action that is not actually currently valid misleads the client into attempting an action that then fails.
- Undocumented link relation names. a client that does not already know what a given relation name means cannot meaningfully act on the link, even though it is technically present in the response.
- Missing links on an error response. a server that omits links on a failure response leaves the client with no guidance on what to try next, exactly when that guidance would matter most.

## 12. Trade-off matrix

| Dimension | With HATEOAS | Without HATEOAS |

|---|---|---|

| Client coupling to server URL structure | Loose, follows links | Tight, hardcodes paths |
| Resilience to a server-side URL reorganization | High | Low, breaks existing clients |
| Response payload size | Larger, carries links | Smaller, data only |
| Client implementation complexity | Higher, must follow links dynamically | Lower, calls a known endpoint directly |
| Accuracy of available-action guidance | Reflects real current state | Client must infer or hardcode |

## 13. Related and incompatible patterns

Related to REST Resource Modeling, whose resource hierarchy this pattern's links describe and navigate dynamically rather than requiring the client to know in advance. Related to API Versioning, since a hypermedia-driven client absorbs a server-side URL change that would otherwise require a coordinated version bump for a client hardcoding the old structure. Not incompatible with either pattern. many mature APIs combine explicit resource modeling, versioning, and a hypermedia-driven response shape together.

## 14. Refactoring path in and out

Introducing it.

1. Identify the resources whose available actions genuinely depend on the resource's current state, where this pattern's benefit is real rather than cosmetic.
2. Define the link relation names the API will use, documenting what each one means so clients can act on them meaningfully.
3. Add server-side logic deriving which links to include from each resource's actual current state, for every response.
4. Update client code to follow the response's links rather than constructing URLs from a hardcoded template, coordinating the migration with every existing client.

Removing it.

1. Confirm the API's URL structure and available actions have genuinely stabilized enough that dynamic discovery no longer earns its cost.
2. Document the now-fixed set of endpoints and available actions directly, replacing what the links previously communicated dynamically.
3. Remove the link-generation logic from server responses, and the link-following logic from clients, once every client has migrated to the documented fixed structure.
4. Confirm no client still depends on following a response link before the removal ships.

## 15. Testing and verification

- Test that a resource's response includes exactly the links its current state should allow, and no others, across every meaningful state transition.
- Test that following a returned link genuinely performs the action or reaches the resource the link's relation name promised.
- Test a client's behavior when a previously available link disappears after a state change, confirming it correctly stops offering that action rather than attempting a stale one.
- Test that a server-side URL restructuring does not break a client that follows links correctly, as a regression test for the pattern's core promise.

## 16. Observability signals

- Rate of client requests to a URL not present as a link in any recent response, a useful signal for a client still hardcoding paths rather than following links.
- Link inclusion rate per relation name, showing how often a given action is actually available across real traffic.
- Attempted-action failure rate for an action whose link was present, which should stay near zero if the state-dependent link logic is correct.
- Response payload size attributable specifically to links, tracked to understand the real cost this pattern adds per response.

## 17. Security and privacy implications

A link included in a response is itself a hint about what actions and related resources exist, so a server has to apply the same authorization filtering to which links it includes as it applies to the underlying data, never revealing a link to an action or resource the requesting client is not actually authorized to reach. A link pointing at another party's resource, included by mistake due to a state-derivation bug, can leak the existence or identity of data the current client should never have been shown.

## 18. Code examples

### Swift

```swift

struct Link {
    let rel: String
    let href: String
}

struct OrderResponse {
    let id: Int
    let status: String
    let links: [Link]

    // Returns the URL for the given relation, or nil if that action is not currently available.
    func href(for rel: String) -> String? {
        links.first(where: { $0.rel == rel })?.href
    }
}

```

### Kotlin

```kotlin

data class Link(val rel: String, val href: String)
data class OrderResponse(val id: Int, val status: String, val links: List<Link>) {
    // Returns the URL for the given relation, or null if that action is not currently available.
    fun hrefFor(rel: String): String? {
        return links.firstOrNull { it.rel == rel }?.href
    }
}

```

### Python

```python

class OrderResponse:
    def __init__(self, order_id, status, links):
        self.id = order_id
        self.status = status
        self.links = links

    def href_for(self, rel):
        """Returns the URL for the given relation, or None if not currently available."""
        for link in self.links:
            if link["rel"] == rel:
                return link["href"]
        return None

```

## 19. References

- Roy Fielding, REST APIs must be hypertext-driven, https://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven
