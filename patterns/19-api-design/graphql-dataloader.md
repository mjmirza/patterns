---
name: GraphQL DataLoader
slug: graphql-dataloader
family: 19-api-design
category: Data Fetching
aliases: [Batch and Cache Loader, Per-Request Batching Loader]
first_described: 'Lee Byron and Facebook, the graphql/dataloader utility library'
maturity: canonical
related: [graphql-resolver-pattern, rest-resource-modeling]
incompatible_with: []
verified: 2026-08-22
---

# GraphQL DataLoader

## 1. Name, aliases, and lineage

GraphQL DataLoader. Also called Batch and Cache Loader or Per-Request Batching Loader. The pattern is a small utility, one instance created fresh per incoming request, that sits between a resolver and its underlying data source, collapsing many individual load calls issued within one tick of the event loop into a single batched fetch, while also caching any key already loaded during that same request. The official graphql/dataloader project will coalesce all individual loads which occur within a single frame of execution, a single tick of the event loop, and then call your batch function with all requested keys (https://github.com/graphql/dataloader).

The lineage runs directly from the GraphQL Resolver Pattern's own most common failure mode. a resolver attached to a field that appears once per item in a list issuing its own independent fetch for every single item. DataLoader was built at Facebook specifically to give every such resolver a shared, per-request batching and caching layer to call into instead, and it is first and foremost a data loading mechanism, and its cache only serves the purpose of not repeatedly loading the same data in the context of a single request (https://github.com/graphql/dataloader).

## 2. Problem and context

A resolver written for a single object works correctly and looks simple when tested in isolation, but the same resolver function runs once per instance whenever its field appears inside a list. If that resolver issues its own database or network call directly, a list of a hundred parent objects produces a hundred separate calls to answer one field, even though every one of those calls could have been answered by a single query for all hundred keys at once.

The problem this pattern solves is giving a resolver a way to ask for exactly the data it needs, one key at a time, from the resolver's own point of view, while the underlying calls are transparently combined into the fewest possible round trips to the real data source, and never repeated for a key already answered earlier in the same request.

## 3. Forces

- A resolver author wants to write simple, per-item code, load this one key, without personally reasoning about batching every time.
- Batching only helps when every individual load request within the same short window is actually captured before the underlying fetch fires, so the batching mechanism must defer its work by at least one tick of the event loop.
- A cache that lives longer than a single request risks serving one client stale data another client already knows is out of date, so the cache's lifetime has to be scoped correctly.
- The underlying data source's batch-fetch operation has to return values in the exact same order as the keys it was given, or a caller has no reliable way to match a value back to its key.
- A key that genuinely fails to load has to be represented distinctly from a key that resolved to an empty or missing value, so a caller can tell the two apart.

## 4. Applicability and non-applicability

Use GraphQL DataLoader wherever a GraphQL Resolver Pattern implementation has a field that appears inside a list, or is otherwise reachable many times within a single request, and that field's resolver would otherwise issue its own independent call to a database or another service for each occurrence.

This pattern is a non-applicability fit for a field that only ever resolves once per request, where there is nothing to batch, since wrapping a single-call resolver in a batching layer adds indirection without buying anything. It is also unnecessary in a server built around fixed REST endpoints rather than independently resolved fields, since the N-plus-one failure mode this pattern exists to solve is specific to the per-field resolver execution model.

## 5. Structure

- Batch function. the single function a caller provides, accepting an array of keys and returning a promise resolving to an array of values in the same order.
- Per-request instance. one DataLoader instance created fresh at the start of handling each incoming request, never shared or reused across requests.
- Load call. the per-key call a resolver makes, from its own point of view a simple request for one value.
- Dispatch queue. the internal list of keys requested so far within the current tick, collected until the event loop yields.
- Per-request cache. the memoized map from a key already loaded during this request to its resolved value, checked before any key is added to the dispatch queue a second time.

## 6. ASCII structure diagram

```

  Resolver calls, same tick:
    loader.load(1)   loader.load(2)   loader.load(1)   loader.load(3)
          |                |                |                |
          v                v                v                v
     +--------------------------------------------------------+
     |  dispatch queue collects unique keys: [1, 2, 3]         |
     |  (second call for key 1 is served from the cache)       |
     +--------------------------------------------------------+
                              |
                    event loop tick ends
                              |
                              v
                 batchFunction([1, 2, 3])
                              |
                              v
               one call to the underlying data source
                              |
                              v
            [value1, value2, value3]  (same order as keys)

```

## 7. Dynamics

1. A new DataLoader instance is created at the start of the request, wrapping a caller-provided batch function.
2. As resolvers execute during that request, each calls load with a single key, and every call is added to an internal dispatch queue rather than triggering an immediate fetch.
3. If a key has already been loaded, or is already queued, during this same request, the existing promise is returned instead of adding the key again, because DataLoader is first and foremost a data loading mechanism, and its cache only serves the purpose of not repeatedly loading the same data in the context of a single request (https://github.com/graphql/dataloader).
4. Once the current tick of the event loop finishes, DataLoader coalesces every distinct key collected so far and calls the batch function exactly once with the full list (https://github.com/graphql/dataloader).
5. The batch function performs one real call to the underlying data source for every queued key at once, and returns an array of values in the same order the keys were given.
6. Each individual load call's promise resolves with its corresponding value from that array, and every resolver that called load receives its answer exactly as if it had made its own independent call.

## 8. Implementation variants

- Per-request scoping via request context. the DataLoader instance is created once per incoming request and attached to a shared context object every resolver can reach.
- Explicit cache priming. a caller inserts a known key and value into the cache directly, before any resolver asks for it, to avoid a redundant fetch for data already known.
- Cache-disabled batching-only mode. the batching behavior is kept but the caching layer is turned off, for a data source whose values change too quickly within a single request for caching to be safe.
- Composed loaders. one DataLoader's batch function itself calls into another DataLoader, layering batching across a chain of dependent lookups.

## 9. Known production uses

- The graphql/dataloader library itself, originally built and open sourced by Facebook, is the reference implementation and is depended on directly by a large share of production GraphQL servers written in Node.js.
- GitHub's public GraphQL API relies on this batching and caching model across its own resolver layer to keep deeply nested queries over repositories, issues, and users efficient.
- Shopify's GraphQL Admin API uses the same batch-and-cache-per-request approach across its resolver layer to avoid repeated lookups when a query traverses related commerce entities.

## 10. Consequences

Benefits.

- A resolver author writes simple, per-key code and gets batching for free, without reasoning about the N-plus-one problem inside the resolver itself.
- Repeated requests for the same key within one request are served from the per-request cache instead of issuing a redundant fetch.
- The underlying data source sees one call per distinct set of keys per tick, instead of one call per individual load.

Costs.

- Every batch function has to return values in the exact same order as the keys it received, and a bug in that ordering silently mismatches values to the wrong keys rather than raising an obvious error.
- A DataLoader instance shared across requests, instead of created fresh per request, leaks one client's cached data into another client's response.
- Batching defers the underlying fetch by at least one tick, which is invisible at small scale but adds a real, if small, amount of latency to every request.

## 11. Failure modes

- Cross-request cache leakage. a DataLoader instance created once at server startup, instead of once per request, serves one user's cached values back to a different user.
- Ordering mismatch. a batch function that returns its results in a different order than the keys it was given silently attaches the wrong value to the wrong key.
- Stale cache within a long-lived request. a mutation performed partway through a request does not invalidate an already-cached read of the same key, so a later read in that same request still returns the old value.
- Unbounded batch size. a batch function with no limit on how many keys it accepts at once can be handed an unexpectedly large key list by a single pathological query, overwhelming the underlying data source in one call.

## 12. Trade-off matrix

| Dimension | With this pattern | Without this pattern |

|---|---|---|

| Calls per list of size N | One batched call | N independent calls |
| Resolver code complexity | Simple, per-key load calls | Simple until N-plus-one appears in production |
| Cache correctness risk | Requires correct per-request scoping | No shared cache to get wrong |
| Latency per individual load | Deferred by one event loop tick | Immediate, but multiplied by call count |
| Ordering discipline required | Batch function must preserve key order | Not applicable, one call per key |

## 13. Related and incompatible patterns

Related to the GraphQL Resolver Pattern, whose own most common failure mode, the N-plus-one problem, is exactly what this pattern exists to solve. Related to REST Resource Modeling, which sidesteps the problem differently, by letting a client request a bounded, fixed resource shape rather than an arbitrarily nested field graph in the first place. Not incompatible with any resolver-based system, since a resolver that never triggers repeated loads simply never benefits from batching, without any conflict.

## 14. Refactoring path in and out

Introducing it.

1. Identify every resolver whose field appears inside a list, or is otherwise reachable many times within one request, and that currently issues its own independent call to a data source.
2. Write a batch function for that data source, accepting an array of keys and returning a promise resolving to an array of values in the same order.
3. Wire a fresh DataLoader instance into the per-request context, so every resolver handling that request shares the same instance, and no instance survives past its own request.
4. Replace the resolver's direct call with a single load call against the shared loader, leaving the resolver's own logic otherwise unchanged.

Removing it.

1. Confirm the resolver in question genuinely no longer needs batching, typically because the field it backs no longer appears more than once per request.
2. Replace the load call with a direct call to the underlying data source.
3. Remove the now-unused DataLoader instance from the per-request context if nothing else still depends on it.
4. Confirm, with a test asserting call counts, that no other resolver was relying on the same loader instance's batching or caching behavior.

## 15. Testing and verification

- Unit test the batch function in isolation, asserting it returns values in exactly the same order as the keys it was given, including a case with a duplicate key in the input.
- Add an integration test that issues a query returning a list, asserting the underlying data source receives exactly one batched call rather than one call per list item.
- Test that two separate requests never share cached data, by asserting a fresh DataLoader instance is created per request rather than reused.
- Test the cache-clear or cache-prime path explicitly if the resolver layer performs a mutation mid-request that should invalidate a previously loaded key.

## 16. Observability signals

- Ratio of load calls to actual batch function invocations per request, the direct signal for how much a given loader is actually saving.
- Batch size distribution, since an unusually large batch on a single tick can indicate a pathological query worth investigating.
- Cache hit rate within a single request, showing how often a duplicate key was served from the cache instead of triggering another load.
- Time spent inside the batch function itself, tracked separately from the resolver's own execution time, since a slow batch function affects every resolver waiting on that tick's dispatch.

## 17. Security and privacy implications

A DataLoader instance that is accidentally shared across requests, rather than created fresh per request, can serve one user's previously loaded, permission-checked data straight back to a different user who never had access to it, entirely bypassing whatever authorization check the original load call passed through. Because the batch function receives the raw keys with no per-key context about who requested them, any per-key authorization decision has to be made before the key ever reaches the loader, not inside the batch function itself.

## 18. Code examples

### Swift

```swift

final class BatchLoader<Key: Hashable, Value> {
    private var pendingKeys: [Key] = []
    private var cache: [Key: Value] = [:]
    private let batchFetch: ([Key]) -> [Key: Value]

    init(batchFetch: @escaping ([Key]) -> [Key: Value]) {
        self.batchFetch = batchFetch
    }

    // Queues a key, or returns the cached value if this key was already loaded.
    func load(_ key: Key) -> Value? {
        if let cached = cache[key] {
            return cached
        }
        pendingKeys.append(key)
        return nil
    }

    // Dispatches every queued key as a single batched fetch.
    func dispatch() {
        let results = batchFetch(pendingKeys)
        for (key, value) in results {
            cache[key] = value
        }
        pendingKeys.removeAll()
    }
}

```

### Kotlin

```kotlin

class BatchLoader<K, V>(private val batchFetch: (List<K>) -> Map<K, V>) {
    private val pendingKeys = mutableListOf<K>()
    private val cache = mutableMapOf<K, V>()

    // Queues a key, or returns the cached value if this key was already loaded.
    fun load(key: K): V? {
        cache[key]?.let { return it }
        pendingKeys.add(key)
        return null
    }

    // Dispatches every queued key as a single batched fetch.
    fun dispatch() {
        val results = batchFetch(pendingKeys)
        cache.putAll(results)
        pendingKeys.clear()
    }
}

```

### Python

```python

class BatchLoader:
    def __init__(self, batch_fetch):
        self.batch_fetch = batch_fetch
        self.pending_keys = []
        self.cache = {}

    def load(self, key):
        """Queues a key, or returns the cached value if this key was already loaded."""
        if key in self.cache:
            return self.cache[key]
        self.pending_keys.append(key)
        return None

    def dispatch(self):
        """Dispatches every queued key as a single batched fetch."""
        results = self.batch_fetch(self.pending_keys)
        self.cache.update(results)
        self.pending_keys = []

```

## 19. References

- graphql/dataloader, official project README, https://github.com/graphql/dataloader
