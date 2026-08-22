---
name: REST Resource Modeling
slug: rest-resource-modeling
family: 19-api-design
category: Structural
aliases: [Resource-Oriented Design, Noun-Based API Design, RESTful Resource Modeling]
first_described: 'Roy Fielding, Architectural Styles and the Design of Network-based Software Architectures, 2000'
maturity: canonical
related: [pagination-pattern, api-versioning]
incompatible_with: []
verified: 2026-08-22
---

# REST Resource Modeling

## 1. Name, aliases, and lineage

REST Resource Modeling. Also called Resource-Oriented Design, Noun-Based API Design, or RESTful Resource Modeling. The pattern is the practice of designing a REST API's URL structure and representations around nouns, called resources, rather than verbs, using the standard HTTP methods to express actions on those resources. Roy Fielding's doctoral dissertation, the original source that defines REST itself, names the core abstraction directly. the key abstraction of information in REST is a resource (https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm).

The lineage runs directly from that dissertation's own broad definition toward the practical, everyday design conventions teams actually use to build a real API. Fielding's dissertation states just how broad the resource abstraction is meant to be. any information that can be named can be a resource, a document or image, a temporal service, a collection of other resources, a non-virtual object, and so on (https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm). Modern API design guides, including Google's own API Improvement Proposals, turned that broad theoretical abstraction into the concrete, named-resource conventions this pattern describes.

## 2. Problem and context

An API whose endpoints are organized around actions, such as getUser or createOrder as distinct endpoint names, grows unpredictably as new actions are added, and gives a client developer no consistent structure to learn once and reuse across the whole API. Every new capability means learning a brand new endpoint shape, with no shared convention for how to find, read, update, or remove the underlying data.

The problem this pattern solves is giving an API a small, learnable, and consistent structure. Google's own API Improvement Proposals state the resulting principle directly. the fundamental building blocks of an API are individually named resources, nouns, and the relationships and hierarchy that exist between them (https://google.aip.dev/121). Once a client developer understands the resource hierarchy and the standard HTTP methods, they can predict how to interact with a resource they have never used before, without reading a new set of documentation for every single endpoint.

## 3. Forces

- Some real operations do not map cleanly onto a single resource and a standard HTTP method, such as an action that spans several resources at once or triggers an asynchronous process.
- A deeply nested resource hierarchy can accurately reflect real ownership between entities, but it also makes URLs longer and harder to construct correctly.
- A consistent resource naming convention has to be agreed and enforced across every team contributing to the API, or the consistency this pattern is meant to deliver breaks down in practice.
- Resources evolve over time, and the URL structure has to accommodate that evolution without breaking every existing client that already depends on it.
- Collection-level operations (searching, filtering, bulk actions) do not always fit neatly into a single-resource, single-method model.

## 4. Applicability and non-applicability

Use REST Resource Modeling for any API whose primary job is exposing create, read, update, and delete style operations over a set of real, nameable entities, especially when the API is meant to be consumed by many different clients over a long period, where predictability and a learnable structure matter more than raw flexibility. It fits especially well when the underlying domain already has a natural, real hierarchy between entities that the resource hierarchy can mirror directly.

Skip it for an API whose primary job is invoking discrete actions or long-running processes that do not map cleanly onto a resource (a computation, a workflow trigger, a real-time stream), since forcing that kind of operation into a resource shape often produces an awkward, unnatural design rather than a genuinely clearer one.

## 5. Structure

- Resource. the named noun the API exposes, matching Fielding's own definition of the key information abstraction in REST.
- Collection. a set of resources of the same kind, addressed by a plural path segment, that a client can list or add to.
- Resource identifier. the unique path segment that addresses one specific resource within its collection.
- Resource hierarchy. the parent-child relationships between resources, reflected directly in the nesting of the URL path.
- Standard method mapping. the fixed assignment of HTTP methods (GET, POST, PUT, PATCH, DELETE) to the standard actions a client can take on a resource or a collection.

## 6. ASCII structure diagram

```
  /orgs                          Collection (orgs)
  /orgs/{org_id}                 Resource (one org)
  /orgs/{org_id}/teams           Collection (teams within an org)
  /orgs/{org_id}/teams/{team_id} Resource (one team)

  GET    /orgs/{org_id}/teams        -> list the collection
  POST   /orgs/{org_id}/teams        -> create a resource in the collection
  GET    /orgs/{org_id}/teams/{id}   -> read one resource
  PATCH  /orgs/{org_id}/teams/{id}   -> partially update one resource
  DELETE /orgs/{org_id}/teams/{id}   -> remove one resource
```

## 7. Dynamics

1. A domain entity is identified as a resource, matching Fielding's own broad definition that any information that can be named can be a resource (https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm).
2. The resource is placed within a resource hierarchy, reflecting its real relationship to any parent resource it belongs to, and given a plural collection path and a unique identifier within that collection.
3. A client requests the collection or a specific resource using the standard method mapping, reading with GET, creating with POST against the collection, and updating or removing a specific resource with PATCH, PUT, or DELETE.
4. Because the fundamental building blocks are individually named resources and the relationships between them (https://google.aip.dev/121), a client that has learned this structure for one resource can predict how to interact with a new, unfamiliar resource in the same API.
5. As the domain evolves, new resources are added to the hierarchy following the same naming and nesting conventions, keeping the overall API's shape consistent even as its surface grows.

## 8. Implementation variants

- Flat resource collections. every resource type lives at the top level with no nesting, favoring simpler URLs over an exact mirror of domain ownership.
- Deeply nested hierarchy. resources are nested to reflect real domain ownership precisely, favoring an accurate, self documenting structure over shorter URLs.
- Custom methods alongside standard ones. a small number of named, non-CRUD actions are added on top of the standard method mapping for the operations that genuinely do not fit a resource shape, following Google's own accommodation for standard versus custom methods.
- Sub-resource for a relationship. a many to many or otherwise complex relationship between two resources is itself modeled as its own addressable resource, rather than being folded into either side of the relationship.

## 9. Known production uses

- Roy Fielding's own dissertation is the canonical origin of the resource abstraction this entire pattern is built on (https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm), and every subsequent REST API design guide traces its resource concept back to this source.
- Google's own API Improvement Proposals codify resource oriented design as the standard pattern across Google's public APIs (https://google.aip.dev/121), including the named-resource and hierarchy conventions this entry describes.
- Large public APIs across the industry, including GitHub's and Stripe's own REST APIs, follow this same resource and standard method convention, giving millions of API client developers a shared, learnable structure across otherwise unrelated services.

## 10. Consequences

### Benefits

- A client developer who understands the resource hierarchy for one part of the API can predict how to interact with an unfamiliar resource elsewhere in the same API.
- The API's surface area grows in a consistent, learnable shape as new resources are added, rather than each new capability requiring its own bespoke endpoint convention.
- Standard HTTP semantics (caching, idempotency of GET and PUT, status codes) apply naturally once the API is organized around resources and the standard method mapping.

### Costs

- An operation that does not map cleanly onto a resource has to be deliberately designed as an exception to the pattern, which takes real judgment to get right.
- A deeply nested resource hierarchy can produce long, unwieldy URLs for a resource several levels deep in the ownership chain.
- Enforcing a consistent naming and hierarchy convention across every team contributing to the API takes ongoing discipline and review.

## 11. Failure modes and misuse

- Verb-shaped endpoints layered on top of a nominally resource-oriented API, such as a `/users/{id}/activate` action endpoint that reintroduces the exact action-based inconsistency this pattern exists to remove.
- A resource hierarchy that does not actually match real domain ownership, misleading a client developer about how the underlying entities actually relate to each other.
- Inconsistent use of the standard method mapping, such as using POST for an update that should be a PATCH, breaking the predictability the pattern is meant to deliver.
- Forcing every operation into a resource shape even when a genuine non-resource action would be clearer, producing an awkward, contorted design rather than a genuinely simpler one.
- An inconsistent pluralization or naming convention across different resource collections, undermining the learnable structure a client developer relies on.

## 12. Trade-off matrix

| Dimension | Flat resource collections | Deeply nested hierarchy |
|---|---|---|
| URL length | Shorter | Longer, reflects the full ownership chain |
| Accuracy to real domain ownership | Lower | Higher |
| Ease of constructing a URL | Easier | Requires knowing every parent identifier |
| Fit for a shallow domain | Good | Unnecessary complexity |
| Fit for a genuinely deep domain hierarchy | Loses real structure | Matches the domain directly |

## 13. Related and incompatible patterns

### Related

- Pagination Pattern. a resource collection commonly needs pagination once it grows large, making the two patterns a natural pair on any real collection endpoint.
- API Versioning. a resource's shape and the standard method mapping still need to evolve safely over time, which is exactly what a versioning strategy governs.

### Incompatible with

- None directly, though an API whose endpoints are organized purely around actions rather than nouns works against this pattern's own intent, even though it may still be described as RESTful.

## 14. Refactoring path in and out

### Introducing it

1. Identify the real, nameable entities in the domain the API exposes, and treat each one as a resource.
2. Design the resource hierarchy to reflect real ownership between those entities, and assign each resource a plural collection path and a unique identifier.
3. Map the standard CRUD operations onto the standard HTTP methods for each resource, rather than inventing a new endpoint name per action.
4. Identify any operation that genuinely does not map onto a resource, and design it as a deliberate, clearly marked exception rather than forcing it into an awkward resource shape.
5. Document the resulting resource hierarchy and method conventions once, so every client developer learns one consistent structure rather than a new shape per endpoint.

### Removing it

1. Confirm the API is being retired or replaced by a fundamentally different interaction style (an action-oriented RPC API, a GraphQL API).
2. Retire the resource-based endpoints, communicating a clear migration path to existing client developers.
3. Remove the resource hierarchy documentation once no client is depending on it.

## 15. Testing and verification

- Test each resource's standard method mapping directly, confirming GET, POST, PATCH, PUT, and DELETE behave exactly as the standard convention specifies for that resource.
- Test the resource hierarchy's URL structure explicitly, confirming a nested resource is only reachable through its correct parent path.
- Review new endpoints against the established naming and hierarchy convention before they ship, catching a verb-shaped or inconsistent endpoint before it reaches real clients.
- Test standard HTTP semantics (idempotency of PUT, correct status codes) directly against each resource, confirming the API genuinely behaves the way its resource-oriented design implies.

## 16. Observability signals

- Track which HTTP methods are actually used against each resource endpoint, flagging an unexpected method usage pattern that might signal an inconsistent client integration.
- Track how often a genuinely non-resource, custom-method endpoint is added over time, as a signal of how well the resource model is actually fitting the evolving domain.
- Track client-reported confusion or support requests about a specific endpoint's shape, as a signal that its resource design may not be as predictable as intended.

## 17. Security and privacy implications

- A predictable, resource-oriented URL structure makes it easier for an attacker to guess or enumerate resource identifiers, so authorization needs to be checked on every request rather than relying on the URL structure itself as a barrier.
- A nested resource path that exposes a parent identifier in the URL should not leak information about resources the requester is not authorized to know exist.
- Standard HTTP method semantics, especially the idempotency expected of PUT and the safety expected of GET, should genuinely hold in the implementation, since a client or an intermediary cache may rely on those guarantees being true.

## Code examples

### Python

```python
from dataclasses import dataclass, field


@dataclass
class Team:
    team_id: str
    name: str


class TeamCollection:
    def __init__(self):
        self.teams = {}

    def list(self):
        return list(self.teams.values())

    def create(self, team_id, name):
        team = Team(team_id, name)
        self.teams[team_id] = team
        return team

    def get(self, team_id):
        return self.teams.get(team_id)

    def update(self, team_id, name):
        team = self.teams[team_id]
        team.name = name
        return team

    def delete(self, team_id):
        del self.teams[team_id]


collection = TeamCollection()
collection.create("t1", "Platform")
print('read', collection.get("t1"))
print('list', collection.list())
```

### Kotlin

```kotlin
data class Team(val teamId: String, var name: String)

class TeamCollection {
    private val teams = mutableMapOf<String, Team>()

    fun list(): List<Team> = teams.values.toList()

    fun create(teamId: String, name: String): Team {
        val team = Team(teamId, name)
        teams[teamId] = team
        return team
    }

    fun get(teamId: String): Team? = teams[teamId]

    fun update(teamId: String, name: String): Team {
        val team = teams.getValue(teamId)
        team.name = name
        return team
    }

    fun delete(teamId: String) {
        teams.remove(teamId)
    }
}

fun main() {
    val collection = TeamCollection()
    collection.create("t1", "Platform")
    println("read " + collection.get("t1"))
    println("list " + collection.list())
}
```

### Swift

```swift
struct Team {
    let teamID: String
    var name: String
}

final class TeamCollection {
    private var teams: [String: Team] = [:]

    func list() -> [Team] {
        Array(teams.values)
    }

    @discardableResult
    func create(teamID: String, name: String) -> Team {
        let team = Team(teamID: teamID, name: name)
        teams[teamID] = team
        return team
    }

    func get(teamID: String) -> Team? {
        teams[teamID]
    }

    func update(teamID: String, name: String) -> Team {
        teams[teamID]?.name = name
        return teams[teamID]!
    }

    func delete(teamID: String) {
        teams.removeValue(forKey: teamID)
    }
}

let collection = TeamCollection()
collection.create(teamID: "t1", name: "Platform")
print("read " + String(describing: collection.get(teamID: "t1")))
print("list count " + String(collection.list().count))
```

## 18. References

- Roy Fielding, Architectural Styles and the Design of Network-based Software Architectures, Chapter 5 (https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)
- Google, API Improvement Proposals, AIP-121, Resource-oriented design (https://google.aip.dev/121)
