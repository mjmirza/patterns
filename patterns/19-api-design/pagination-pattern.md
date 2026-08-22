---
name: Pagination Pattern
slug: pagination-pattern
family: 19-api-design
category: Data Fetching
aliases: [Page-Based Pagination, Offset and Limit Pagination]
first_described: 'Google, AIP-158; JSON:API specification'
maturity: canonical
related: [rest-resource-modeling, cursor-based-pagination]
incompatible_with: []
verified: 2026-08-22
---

# Pagination Pattern

## 1. Name, aliases, and lineage

Pagination Pattern. Also called Page-Based Pagination or Offset and Limit Pagination. The pattern is splitting a large collection response into a sequence of smaller, bounded pages, each identified by a page number or numeric offset and a page size, rather than returning an entire collection in one response. Google's own API Improvement Proposals name the reason a collection needs this in the first place. however, collections can often be arbitrarily sized, and also often grow over time, increasing lookup time as well as the size of the responses being sent over the wire (https://google.aip.dev/158).

The lineage runs from that same, plain observation about arbitrarily-sized collections toward the concrete query parameter conventions different API specifications settled on. The JSON:API specification states its own pagination convention directly. JSON API is agnostic about the pagination strategy used by a server, but the page query parameter family can be used regardless of the strategy employed, for example, a page-based strategy might use query parameters such as page number and page size, while a cursor-based strategy might use page cursor (https://jsonapi.org/format/#fetching-pagination).

## 2. Problem and context

A collection endpoint whose response includes every matching item, with no limit at all, works fine while the underlying collection is small, but degrades as the collection grows. The response payload grows unboundedly with the data, the server does more work assembling a larger response, and the client has to hold the entire result in memory before it can start acting on any of it, even when the client only actually needs the first handful of items.

The problem this pattern solves is letting a client retrieve a large collection in bounded, predictable chunks, each cheap for the server to produce and cheap for the client to consume, using a simple, stateless page number and page size the client controls directly, without either side needing to reason about the collection's full size up front.

## 3. Forces

- A page number and size are simple for a client to construct directly, including jumping straight to an arbitrary page, but that same simplicity assumes the underlying collection stays stable between requests.
- If items are inserted into or removed from the collection between two page requests, a numeric offset can silently skip an item or repeat one, since the offset counts a position in a collection that has since shifted.
- A very large offset, requesting a page deep into a large collection, can be expensive for the underlying data store to compute, since many implementations still have to walk past every earlier item to reach the requested offset.
- The page size the client requests has to be bounded by the server, or an unbounded page size request defeats the purpose of pagination entirely.
- A client that wants to know the total number of pages or items needs that count computed and returned separately, which itself can be an expensive operation on a large or frequently changing collection.

## 4. Applicability and non-applicability

Use Pagination Pattern for a collection endpoint whose clients commonly want to jump to a specific page directly, display a page-number-based navigation control, or otherwise benefit from a simple, human-meaningful position in the collection, and where the underlying collection does not change so quickly that a shifting offset would cause frequent, visible skipped or repeated items.

This pattern is a non-applicability fit for a collection that changes frequently while a client is actively paging through it, such as a live feed, where Cursor-based Pagination's stable-position guarantee matters more than page-number convenience. It is also unnecessary for a collection genuinely small and bounded enough that returning it in full never becomes a real cost.

## 5. Structure

- Page number or offset parameter. the client-supplied value identifying which page, or which starting position, the request wants.
- Page size parameter. the client-supplied, server-bounded value controlling how many items one page's response contains.
- Page response envelope. the returned items for the requested page, alongside metadata such as the total item count or the total page count.
- Server-side bound. the maximum page size the server enforces regardless of what the client requests.
- Collection query. the underlying data-store query that translates the page number or offset and the page size into the specific slice of the collection to return.

## 6. ASCII structure diagram

```

  GET /items?page=1&page_size=20   -> items 1 through 20
  GET /items?page=2&page_size=20   -> items 21 through 40
  GET /items?page=3&page_size=20   -> items 41 through 60

  Response envelope
  {
    "items": [ ... 20 items ... ],
    "page": 2,
    "page_size": 20,
    "total_items": 187,
    "total_pages": 10
  }

```

## 7. Dynamics

1. A client requests a collection endpoint, supplying a page number or offset and a requested page size.
2. The server clamps the requested page size to its own configured maximum, protecting against an unbounded request.
3. The server translates the page number and size into a specific slice of the underlying collection, since a page-based strategy might use query parameters such as page number and page size (https://jsonapi.org/format/#fetching-pagination).
4. The server returns that slice of items alongside metadata describing the page's position, and often the collection's total size.
5. The client uses that metadata to construct the next request, incrementing the page number or advancing the offset by the page size, or to jump directly to an arbitrary page the client already knows the number of.
6. If the underlying collection changes between two requests, an item can be skipped or repeated on the boundary between two pages, since the response payload's size growing with the collection is exactly the underlying cost pagination exists to bound (https://google.aip.dev/158), not to eliminate every consistency concern.

## 8. Implementation variants

- Page number and page size. the client requests page N of size S, the most human-friendly shape, well suited to a page-number navigation control.
- Raw numeric offset and limit. the client requests a starting offset and a maximum count directly, functionally equivalent to page-and-size but expressed as a position rather than a page index.
- Total-count-included response. every page response includes the collection's total item or page count, at the cost of the server computing that count on every request.
- Total-count-omitted response, with a has-more flag instead. the server skips the potentially expensive total-count computation and instead tells the client whether another page exists.

## 9. Known production uses

- Many REST APIs following Google's own AIP conventions expose page-size-bounded list endpoints across their public surface, with the page size clamped server-side.
- JSON:API-compliant servers commonly implement the page-number and page-size query parameter family the specification names explicitly.
- Many admin dashboards and content-management systems, across a wide range of platforms, use page-number pagination specifically because it maps directly onto a page-number navigation control in the user interface.

## 10. Consequences

Benefits.

- A client can jump directly to a specific, human-meaningful page, which a token-based cursor cannot offer without first walking through every earlier page.
- The response size stays bounded and predictable regardless of how large the underlying collection grows.
- The page-number and page-size parameters are simple to construct, simple to display in a navigation control, and simple to reason about.

Costs.

- A numeric offset is vulnerable to items shifting between requests, silently skipping or repeating an item near a page boundary.
- A very large offset can be expensive for the underlying data store to compute, particularly on a large collection.
- Computing an accurate total count alongside every page can itself be an expensive operation, especially on a large or frequently changing collection.

## 11. Failure modes

- Skipped or duplicated items. an item inserted or removed between two page requests shifts every later item's offset, causing a client paging sequentially to miss or see twice an item near the boundary.
- Unbounded page size. a server that does not clamp the client-requested page size can be asked to return an enormous single page, defeating the purpose of pagination and risking resource exhaustion.
- Expensive deep offset. a request for a page far into a large collection, on a data store that computes an offset by scanning past every earlier row, becomes progressively slower the deeper the requested page is.
- Stale total count. a total item or page count computed once and cached too long can mislead a client about how many pages actually remain, if the collection changes afterward.

## 12. Trade-off matrix

| Dimension | Page-based pagination | Cursor-based pagination |

|---|---|---|

| Jump directly to an arbitrary page | Simple, direct | Not possible without walking through prior pages |
| Stability under concurrent inserts and deletes | Vulnerable to skipped or repeated items | Stable relative to a fixed position |
| Deep-page query cost | Can grow with offset depth on some data stores | Stays roughly constant |
| Suitability for a page-number UI control | Direct fit | Awkward, no natural page count |
| Total count availability | Straightforward to compute and return | Often expensive or not offered |

## 13. Related and incompatible patterns

Related to REST Resource Modeling, whose collection endpoints are exactly where this pattern applies. Related to Cursor-based Pagination, the alternative approach for a collection that changes frequently or that never needs a jump-to-arbitrary-page control. Not incompatible with Cursor-based Pagination at the level of a single API. many APIs offer page-based pagination on a stable, rarely-changing collection and cursor-based pagination on a fast-changing one, side by side.

## 14. Refactoring path in and out

Introducing it.

1. Identify a collection endpoint currently returning every matching item with no limit, and confirm the collection is stable enough that offset-based skipping or repeating is an acceptable trade-off.
2. Add page number or offset, and page size, parameters to the endpoint, with a server-side maximum on page size.
3. Update the response to include the requested page's items alongside its position and size metadata.
4. Update every existing client to request pages explicitly, rather than assuming the endpoint returns the full collection.

Removing it.

1. Confirm the underlying collection is small and stable enough that returning it in full is genuinely acceptable, or that Cursor-based Pagination has replaced this pattern for the same endpoint.
2. Remove the page number and page size parameters from the endpoint's contract, coordinating the change with every client that currently sends them.
3. Remove the page-position metadata from the response, once no client depends on it.
4. Confirm the endpoint's response size stays acceptable without pagination before the change ships.

## 15. Testing and verification

- Test that requesting page N returns exactly the items expected at that position, for a known, fixed collection.
- Test that an oversized page-size request is clamped to the server's configured maximum rather than honored as requested.
- Test the boundary case of the final, partial page, asserting it returns fewer items than the requested page size without error.
- Test a page request past the end of the collection, asserting it returns an empty page rather than an error.

## 16. Observability signals

- Requested page-size distribution, showing whether clients commonly request the maximum allowed size, a useful signal for whether the server-side bound is well calibrated.
- Deep-offset request rate, the fraction of requests for a page far into a large collection, since these are the requests most likely to be expensive on some data stores.
- Total-count computation latency, tracked separately from the item-fetch latency, since it is often the more expensive part of building a page response.
- Page-size clamp rate, how often a client's requested page size exceeds the server's maximum, a useful signal for whether a client is misbehaving or the limit is set too low.

## 17. Security and privacy implications

A page size with no server-side maximum lets a client request an arbitrarily large single page, which can be used to exhaust server resources or to bulk-extract an entire collection in a single request when a smaller, rate-limited page size was intended to slow that down. A collection endpoint's pagination has to apply the same authorization filtering to every page consistently, since a page far into the collection is not a lesser-scrutinized request than the first page, and a client should never be able to see an item on a later page that authorization would have hidden from them on the first.

## 18. Code examples

### Swift

```swift

struct Page<Item> {
    let items: [Item]
    let page: Int
    let pageSize: Int
    let totalItems: Int
}

func fetchPage<Item>(from collection: [Item], page: Int, requestedSize: Int, maxSize: Int) -> Page<Item> {
    let size = min(requestedSize, maxSize)
    let start = min((page - 1) * size, collection.count)
    let end = min(start + size, collection.count)
    return Page(items: Array(collection[start..<end]), page: page, pageSize: size, totalItems: collection.count)
}

```

### Kotlin

```kotlin

data class Page<T>(val items: List<T>, val page: Int, val pageSize: Int, val totalItems: Int)

fun <T> fetchPage(collection: List<T>, page: Int, requestedSize: Int, maxSize: Int): Page<T> {
    val size = minOf(requestedSize, maxSize)
    val start = minOf((page - 1) * size, collection.size)
    val end = minOf(start + size, collection.size)
    return Page(collection.subList(start, end), page, size, collection.size)
}

```

### Python

```python

def fetch_page(collection, page, requested_size, max_size):
    """Returns the requested page, clamped to the server's maximum page size."""
    size = min(requested_size, max_size)
    start = min((page - 1) * size, len(collection))
    end = min(start + size, len(collection))
    return {
        "items": collection[start:end],
        "page": page,
        "page_size": size,
        "total_items": len(collection),
    }

```

## 19. References

- Google, API Improvement Proposals, AIP-158 Pagination, https://google.aip.dev/158
- JSON:API specification, Fetching, Pagination, https://jsonapi.org/format/#fetching-pagination
