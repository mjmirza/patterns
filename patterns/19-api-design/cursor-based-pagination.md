---
name: Cursor-based Pagination
slug: cursor-based-pagination
family: 19-api-design
category: Data Fetching
aliases: [Opaque Cursor Pagination, Keyset Pagination]
first_described: 'Stripe list API pagination; Relay GraphQL Cursor Connections Specification'
maturity: canonical
related: [pagination-pattern, graphql-resolver-pattern]
incompatible_with: []
verified: 2026-08-22
---

# Cursor-based Pagination

## 1. Name, aliases, and lineage

Cursor-based Pagination. Also called Opaque Cursor Pagination or Keyset Pagination. The pattern is paginating a collection using an opaque token derived from the current page's last item, rather than a numeric page number or offset, so a client requests the next page by handing that token back to the server. Stripe's own list API documentation describes the mechanism directly. starting after is an object id that defines your place in the list, for example, if you make a list request and receive 100 objects, ending with obj foo, your subsequent call can include starting after equal to obj foo to fetch the next page of the list (https://docs.stripe.com/api/pagination).

The lineage runs from the same underlying concern Pagination Pattern addresses, an arbitrarily large or growing collection, but solved with a token instead of a position. GraphQL's own Relay Cursor Connections Specification names the token's defining property directly. the result of this field should be considered opaque by the client, but will be passed back to the server as described in the arguments section (https://relay.dev/graphql/connections.htm).

## 2. Problem and context

A numeric offset identifies a position in a collection, but that position shifts the moment an item is inserted or removed anywhere before it. A client paging sequentially through a numerically-offset collection while it changes can silently skip an item that moved past the boundary, or see an item twice that shifted the other way. This is especially visible on a fast-changing collection, a live feed, an activity log, an auto-refreshing list.

The problem this pattern solves is giving a client a stable way to continue paging through a collection that may be changing underneath it, by anchoring each page request to a specific item the client has already seen, rather than to a numeric position that has no fixed meaning once the collection changes.

## 3. Forces

- The cursor has to be treated as opaque by the client, never parsed or constructed by hand, or the server loses the freedom to change its internal representation of the token later.
- A cursor cannot jump directly to an arbitrary page the way a numeric page number can, since it only encodes a position relative to a specific item the client already saw.
- The server has to derive a cursor from something that remains a stable ordering key even as the collection changes, or the cursor's stability guarantee breaks down.
- A client that stores a cursor for a long time, then resumes paging much later, may find the item the cursor was derived from has since been deleted, requiring the server to define what happens in that case.
- Total item or page count is often expensive or impossible to compute cheaply alongside cursor-based results, unlike a numeric offset scheme where it is comparatively straightforward.

## 4. Applicability and non-applicability

Use Cursor-based Pagination for a collection that changes frequently while a client may still be actively paging through it, or for any collection large enough that a numeric offset's cost of walking to a deep position becomes a real concern, favoring the pattern's position-stability guarantee over the convenience of jumping to an arbitrary page.

This pattern is a non-applicability fit for a use case that genuinely needs to jump to an arbitrary, specific page directly, a page-number navigation control being the clearest example, since a cursor offers no such capability without first walking through every earlier page. It is also unnecessary overhead for a small, rarely-changing collection where Pagination Pattern's simpler page-number scheme already works without any real drawback.

## 5. Structure

- Cursor token. the opaque value the server derives from a specific item, handed to the client and later returned to request the next page.
- Ordering key. the stable field, or combination of fields, the collection is sorted by, which the cursor is derived from and which must remain consistent across requests.
- Page size limit. the maximum number of items the server returns for a single cursor-based request.
- Has-more indicator. the signal telling the client whether requesting the next page with the returned cursor would yield any further items.
- Cursor decode and validate step. the server-side logic that turns an incoming cursor back into a position in the ordering, rejecting one that is malformed or refers to a deleted item.

## 6. ASCII structure diagram

```

  GET /items?limit=20
     -> items 1 through 20, cursor = "opaque-token-for-item-20"

  GET /items?limit=20&after=opaque-token-for-item-20
     -> items 21 through 40, cursor = "opaque-token-for-item-40"

  Response envelope
  {
    "items": [ ... 20 items ... ],
    "next_cursor": "opaque-token-for-item-40",
    "has_more": true
  }

```

## 7. Dynamics

1. A client requests the first page with no cursor, and the server returns the first slice of items ordered by the collection's stable ordering key.
2. The server derives a cursor from the last item in that page and includes it in the response, treating that cursor as opaque, per the same discipline the result of this field should be considered opaque by the client, but will be passed back to the server (https://relay.dev/graphql/connections.htm).
3. To fetch the next page, the client sends the returned cursor back to the server, matching the mechanism where an object id defines your place in the list and a subsequent call can include it to fetch the next page (https://docs.stripe.com/api/pagination).
4. The server decodes the cursor back into the corresponding position in the ordering, validates it, and returns the next slice of items starting immediately after that position.
5. The server derives a fresh cursor from the new page's last item and repeats, and the client continues this loop until the server signals no further items remain.
6. Because each page is anchored to a specific item's position rather than a numeric offset into the collection, an item inserted or removed elsewhere in the collection does not shift which items appear on subsequent pages.

## 8. Implementation variants

- Encoded single-column cursor. the cursor encodes just one ordering column's value, simple to implement but only works cleanly when that single column is genuinely unique.
- Encoded composite cursor. the cursor encodes multiple columns together, such as a timestamp plus a tie-breaking identifier, handling the common case where the primary ordering column alone is not unique.
- Bidirectional cursor pair. the server returns both a forward and a backward cursor, letting a client page in either direction from its current position.
- Cursor with an embedded integrity check. the cursor includes a signature or checksum over its encoded contents, letting the server detect and reject a tampered or corrupted cursor before attempting to decode it.

## 9. Known production uses

- Stripe's own list API endpoints across its entire public surface use this exact object-id-based cursor scheme, the reference implementation many developers learn this pattern from directly.
- Any GraphQL API following the Relay Cursor Connections Specification, a very widely adopted convention across the GraphQL ecosystem, implements this pattern by specification.
- Slack's own web API uses cursor-based pagination across many of its list endpoints, specifically to handle channels and conversations whose membership can change while a client is paging through them.

## 10. Consequences

Benefits.

- A client paging sequentially through a changing collection does not skip or see a duplicate item, because each page is anchored to a specific item's position.
- A cursor-based query typically stays roughly constant-cost regardless of how deep into the collection the client has paged, unlike a numeric offset that some data stores must scan past entirely.
- The server retains freedom to change its internal cursor encoding over time, since the client is contractually required to treat the cursor as opaque.

Costs.

- A client cannot jump directly to an arbitrary page, only forward or backward from a cursor it already has.
- Computing an accurate total item or page count alongside cursor-based results is often expensive or simply not offered.
- The server has to define, and the client has to handle, what happens when a cursor refers to an item that has since been deleted.

## 11. Failure modes

- Client-parsed cursor. a client that reverse-engineers the cursor's internal structure and constructs its own breaks the moment the server changes its encoding, exactly the risk the opaque-cursor contract exists to prevent.
- Non-unique ordering key. a cursor derived from an ordering column that is not actually unique across the collection can produce an ambiguous position, causing an item to be skipped or repeated even with cursor-based pagination in place.
- Unvalidated cursor input. a server that decodes an incoming cursor without validating it first can crash, or worse, expose internal state, when handed a malformed or tampered value.
- Deleted-item cursor. a stored cursor referring to an item deleted since it was issued, with no defined server behavior for that case, produces an undefined or inconsistent next page.

## 12. Trade-off matrix

| Dimension | Cursor-based pagination | Page-based pagination |

|---|---|---|

| Stability under concurrent inserts and deletes | Stable relative to a fixed position | Vulnerable to skipped or repeated items |
| Jump directly to an arbitrary page | Not possible without walking through prior pages | Simple, direct |
| Deep-page query cost | Stays roughly constant | Can grow with offset depth on some data stores |
| Suitability for a page-number UI control | Awkward, no natural page count | Direct fit |
| Total count availability | Often expensive or not offered | Straightforward to compute and return |

## 13. Related and incompatible patterns

Related to Pagination Pattern, the alternative page-number-based approach for a collection that changes rarely or where jumping to an arbitrary page matters more than stability under concurrent change. Related to the GraphQL Resolver Pattern, since a GraphQL API's own cursor-based connections build directly on top of a resolver returning a page of items alongside its cursor. Not incompatible with Pagination Pattern at the level of a single API. many APIs offer page-based pagination on a stable, rarely-changing collection and cursor-based pagination on a fast-changing one, side by side.

## 14. Refactoring path in and out

Introducing it.

1. Identify a collection endpoint whose accuracy currently suffers from concurrent inserts or deletes shifting a numeric offset.
2. Choose a stable ordering key, single-column or composite, the cursor will be derived from, confirming it is genuinely unique across the collection.
3. Implement cursor encoding and decoding on the server, treating the cursor as opaque, and add validation for a malformed or tampered incoming cursor.
4. Update every client currently constructing a numeric offset to instead store and pass back the returned cursor.

Removing it.

1. Confirm the collection genuinely no longer needs stability under concurrent change, or that jump-to-arbitrary-page has become the more important requirement.
2. Replace the cursor parameter with a page number or offset parameter in the endpoint's contract, coordinating the change with every client that currently sends a cursor.
3. Remove the cursor encoding and decoding logic, and the cursor validation step, once no client is expected to send one.
4. Confirm the replacement scheme's behavior under concurrent inserts and deletes is genuinely acceptable before the change ships.

## 15. Testing and verification

- Test that paging forward through the full collection using only the returned cursors visits every item exactly once, with no skipped or duplicated item.
- Test the behavior explicitly when an item is inserted or removed between two page requests, asserting the already-issued cursor still resolves to a stable, correct next position.
- Test that a malformed or tampered cursor is rejected cleanly rather than causing a crash or an undefined result.
- Test the deleted-item-cursor case directly, asserting the server's documented behavior actually occurs when a stored cursor refers to an item that no longer exists.

## 16. Observability signals

- Cursor decode failure rate, the fraction of incoming cursors that fail validation, a useful signal for a client bug or an attempted tampering attempt.
- Deleted-item-cursor rate, how often an incoming cursor refers to an item that has since been removed.
- Average and maximum pages paged per client session, useful for understanding real-world usage patterns and sizing the page size limit appropriately.
- Query latency by page depth, watched to confirm cursor-based queries genuinely stay roughly constant-cost as expected.

## 17. Security and privacy implications

A cursor that encodes sensitive internal identifiers or data in a recoverable, unencrypted form can leak information to a client that decodes it, even though the client is contractually expected to treat it as opaque. A server should encode a cursor with either an unrecoverable encoding or an integrity check, so a client cannot tamper with it to request items it should not be authorized to see. The same authorization filtering applied to the first page has to be applied consistently to every subsequent page a cursor requests, since a later page is not a lesser-scrutinized request than the first.

## 18. Code examples

### Swift

```swift

struct CursorPage<Item> {
    let items: [Item]
    let nextCursor: String?
    let hasMore: Bool
}

protocol OrderedById {
    var id: String { get }
}

func fetchAfter<Item: OrderedById>(collection: [Item], cursor: String?, limit: Int) -> CursorPage<Item> {
    let startIndex = cursor.flatMap { c in collection.firstIndex(where: { $0.id == c }).map { $0 + 1 } } ?? 0
    let end = min(startIndex + limit, collection.count)
    let page = Array(collection[startIndex..<end])
    let next = page.last?.id
    return CursorPage(items: page, nextCursor: next, hasMore: end < collection.count)
}

```

### Kotlin

```kotlin

data class CursorPage<T>(val items: List<T>, val nextCursor: String?, val hasMore: Boolean)
interface OrderedById { val id: String }

fun <T : OrderedById> fetchAfter(collection: List<T>, cursor: String?, limit: Int): CursorPage<T> {
    val startIndex = cursor?.let { c -> collection.indexOfFirst { it.id == c }.takeIf { it >= 0 }?.plus(1) } ?: 0
    val end = minOf(startIndex + limit, collection.size)
    val page = collection.subList(startIndex, end)
    val next = page.lastOrNull()?.id
    return CursorPage(page, next, end < collection.size)
}

```

### Python

```python

def fetch_after(collection, cursor, limit):
    """Returns the next page after the given opaque item-id cursor."""
    start = 0
    if cursor is not None:
        for i, item in enumerate(collection):
            if item["id"] == cursor:
                start = i + 1
                break
    end = min(start + limit, len(collection))
    page = collection[start:end]
    next_cursor = page[-1]["id"] if page else None
    return {
        "items": page,
        "next_cursor": next_cursor,
        "has_more": end < len(collection),
    }

```

## 19. References

- Stripe, list API pagination documentation, https://docs.stripe.com/api/pagination
- GraphQL Foundation, Relay Cursor Connections Specification, https://relay.dev/graphql/connections.htm
