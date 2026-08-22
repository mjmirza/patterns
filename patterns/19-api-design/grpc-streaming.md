---
name: gRPC Streaming
slug: grpc-streaming
family: 19-api-design
category: Data Fetching
aliases: [Server Streaming RPC, Client Streaming RPC, Bidirectional Streaming RPC]
first_described: 'Google, gRPC core concepts documentation'
maturity: canonical
related: [graphql-resolver-pattern, webhook-receiver]
incompatible_with: []
verified: 2026-08-22
---

# gRPC Streaming

## 1. Name, aliases, and lineage

gRPC Streaming. Also called Server Streaming RPC, Client Streaming RPC, or Bidirectional Streaming RPC, depending on which of the three streaming shapes a given call uses. The pattern is the use of gRPC's built-in streaming RPC types, alongside its default unary call, to exchange an ordered sequence of messages over one long-lived call instead of a single request and a single response. The official gRPC documentation names the server streaming shape directly. server streaming RPCs where the client sends a request to the server and gets a stream to read a sequence of messages back (https://grpc.io/docs/what-is-grpc/core-concepts/).

The lineage runs from gRPC's own core design, built by Google on top of HTTP/2, where streaming is a first-class RPC shape rather than something layered on top after the fact. The same documentation names the fourth and most general shape directly too. bidirectional streaming RPCs where both sides send a sequence of messages using a read-write stream, and the two streams operate independently, so clients and servers can read and write in whatever order they like (https://grpc.io/docs/what-is-grpc/core-concepts/).

## 2. Problem and context

A single request and response pair works well when a client wants exactly one answer to one question, but it forces an awkward shape onto any interaction that is naturally a sequence. a server pushing live updates as they happen, a client uploading a large amount of data incrementally, or two sides exchanging messages back and forth over time. Forcing any of these into repeated unary calls means opening a new connection, or at least a new request, for every single message, which adds overhead and loses the natural ordering between messages that belong together.

The problem this pattern solves is giving an API a native way to exchange a sequence of messages over one open call, in whichever direction the interaction actually needs, without the caller having to simulate a stream on top of a request and response protocol that was not designed for one.

## 3. Forces

- A streaming call stays open for the duration of the exchange, which means the server has to track and eventually release resources tied to every open stream, unlike a unary call that finishes and cleans up immediately.
- Backpressure has to be handled explicitly. a fast sender on one side of a stream can outpace a slow reader on the other side if nothing throttles the flow.
- A client or server that disconnects mid-stream leaves the other side needing to detect that loss and decide whether to resume, retry, or give up, since there is no single final response to simply wait for.
- Choosing the right one of the four RPC shapes, unary, server streaming, client streaming, or bidirectional streaming, for a given interaction is a real design decision, and choosing wrong forces an awkward workaround later.
- Message ordering within a single stream is guaranteed, but reasoning about ordering across multiple independent streams, or between the two directions of a bidirectional stream, is not automatic.

## 4. Applicability and non-applicability

Use gRPC Streaming for an interaction that is naturally a sequence of messages exchanged over time, live progress updates from a long-running server operation, an incremental upload from the client, or a genuinely two-way conversation such as a chat or a real-time collaboration session, where a single request and response pair would either lose ordering information or force many separate calls.

This pattern is a non-applicability fit for a plain request that genuinely has one answer, since a unary call is simpler to write, simpler to retry, and simpler to reason about than a stream with nothing to stream. It is also a poor fit for a client that cannot maintain a long-lived connection reliably, since a streaming call that drops partway through requires explicit resumption logic that a simple unary retry does not.

## 5. Structure

- Unary call. the default shape, one request message and one response message, included here as the baseline every streaming shape is compared against.
- Server streaming call. one request message from the client, followed by a sequence of response messages the server sends back over time.
- Client streaming call. a sequence of request messages the client sends over time, followed by one response message from the server once the client finishes sending.
- Bidirectional streaming call. both sides send a sequence of messages over the same open call, with the two directions operating independently of one another.
- Long-lived HTTP/2 stream. the single underlying connection every message in a given RPC, streaming or not, travels over.

## 6. ASCII structure diagram

```

  Unary
  Client --request-->  Server
  Client <--response-- Server

  Server streaming
  Client --request-->  Server
  Client <--msg 1----- Server
  Client <--msg 2----- Server
  Client <--msg N----- Server

  Client streaming
  Client --msg 1----->  Server
  Client --msg 2----->  Server
  Client --msg N----->  Server
  Client <--response-- Server

  Bidirectional streaming
  Client --msg 1----->  Server
  Client <--msg a----- Server
  Client --msg 2----->  Server
  Client <--msg b----- Server

```

## 7. Dynamics

1. The client opens a call against a service method whose signature, defined in the service's schema, declares which of the four RPC shapes it uses.
2. For a server streaming call, the client sends its single request message, and the server begins sending a sequence of messages back over the same open call, matching the documented shape of gets a stream to read a sequence of messages back (https://grpc.io/docs/what-is-grpc/core-concepts/).
3. For a client streaming call, the client instead sends its own sequence of messages over time, and the server waits until the client signals it is finished before sending its single response.
4. For a bidirectional streaming call, both sides send their own sequence of messages over the same open call, and the two streams operate independently, so clients and servers can read and write in whatever order they like (https://grpc.io/docs/what-is-grpc/core-concepts/).
5. Either side can signal the end of its own message sequence independently, and the call as a whole completes once both sides have finished and a final status is exchanged.
6. If the underlying connection drops before the exchange completes, both sides observe the stream ending early and have to decide, based on the application's own logic, whether to resume, retry from the beginning, or surface the failure.

## 8. Implementation variants

- Server streaming for live progress. a client kicks off a long-running server operation with one request and receives a sequence of progress updates until the operation finishes.
- Client streaming for incremental upload. a client sends a large payload as a sequence of chunks and receives a single confirmation once the server has assembled and processed the whole upload.
- Bidirectional streaming for a live session. both sides exchange messages for as long as the session is open, such as a chat, a collaborative editing session, or a live telemetry feed with acknowledgements flowing the other way.
- Streaming with an explicit heartbeat. one side sends a periodic empty or minimal message purely to signal the stream is still alive, letting the other side detect a silent disconnection faster than waiting for a transport-level timeout.

## 9. Known production uses

- Google's own internal services, and many of its public Cloud APIs, use gRPC streaming extensively for large data transfers and live update feeds, since gRPC itself was built and open sourced by Google.
- Netflix uses gRPC streaming across parts of its internal microservice mesh for high-throughput, low-latency service-to-service communication.
- Kubernetes itself uses gRPC streaming for the Container Runtime Interface, letting the kubelet exchange a live sequence of events with the container runtime rather than polling repeatedly.

## 10. Consequences

Benefits.

- A naturally sequential interaction is expressed directly, without the caller inventing a polling loop or a series of separate unary calls to simulate a stream.
- Message ordering within one stream is guaranteed by the protocol, removing a whole class of bugs a simulated stream built from repeated calls would have to solve by hand.
- One open connection carries the entire exchange, avoiding the repeated connection setup cost of many separate unary calls.

Costs.

- An open stream is a stateful resource the server has to track for as long as it stays open, unlike a unary call that completes and releases its resources immediately.
- Backpressure and flow control have to be designed for explicitly, or a fast sender can overwhelm a slow reader on the other end of the stream.
- Debugging a long-lived stream is harder than debugging a single request and response, since a failure can occur at any point in an arbitrarily long sequence of messages.

## 11. Failure modes

- Unbounded stream lifetime. a stream that is never explicitly closed on either error or success keeps consuming server resources indefinitely.
- Missing backpressure. a server streaming a large sequence of messages faster than a slow client can consume them exhausts memory buffering the unread backlog.
- Silent connection loss. a network failure that drops the underlying connection without either side sending an explicit close can leave both ends believing the stream is still open until a transport-level timeout eventually fires.
- Partial-message handling gaps. code written assuming every call has exactly one response message, later reused for a streaming call, silently processes only the first message in the sequence and drops the rest.

## 12. Trade-off matrix

| Dimension | With this pattern | Without this pattern (unary only) |

|---|---|---|

| Fit for a sequential interaction | Direct, native support | Simulated with repeated calls or polling |
| Connection overhead | One open connection for the whole exchange | New request overhead per message |
| Message ordering guarantee | Enforced by the protocol within one stream | Caller must reconstruct ordering by hand |
| Server-side resource tracking | Required for the life of each open stream | None, each call completes and releases immediately |
| Debugging complexity | Higher, failure can occur anywhere in a long sequence | Lower, one request and one response to reason about |

## 13. Related and incompatible patterns

Related to the GraphQL Resolver Pattern, which solves a different shape of the same underlying goal, letting a client describe exactly the data it wants, though GraphQL's own subscription mechanism is its closer analogue to a streaming call. Related to Webhook Receiver, an alternative way to deliver a sequence of events over time, pushing each event as its own separate call to a receiving endpoint rather than holding one connection open for the whole sequence. Not incompatible with a unary-only API. most real gRPC services mix unary calls for simple lookups with streaming calls only where a genuine sequence exists.

## 14. Refactoring path in and out

Introducing it.

1. Identify an existing interaction built from repeated unary calls or client polling that is genuinely exchanging a sequence of related messages over time.
2. Choose the correct one of the three streaming shapes based on which side, or both, is actually sending the sequence.
3. Update the service's schema to declare the method as streaming, and update both the client and server implementations to send and receive a sequence rather than a single message.
4. Add explicit handling for a stream ending early, on both success and failure, since there is no longer a single response to simply wait for.

Removing it.

1. Confirm the interaction genuinely no longer needs a sequence, typically because it has been redesigned around a single request and response.
2. Replace the streaming method in the service's schema with a unary one, and remove the per-message send and receive logic on both sides.
3. Migrate any client still calling the streaming method to the new unary method, keeping both available during a transition period if the API has external consumers.
4. Remove the streaming method from the schema only once no client still depends on it.

## 15. Testing and verification

- Test each streaming shape's happy path explicitly, asserting the full expected sequence of messages arrives in order on the receiving side.
- Test an early client disconnect mid-stream, asserting the server detects the loss and releases the resources it was holding for that stream.
- Test backpressure behavior directly, by having a test reader consume messages slower than the sender produces them, and asserting the sender does not silently drop messages.
- Test that a stream genuinely closes, on both success and error, rather than leaking an open connection past the point the test expects it to end.

## 16. Observability signals

- Count of currently open streams per service, the direct signal for whether streams are being cleaned up correctly or accumulating over time.
- Time-to-first-message and time-between-messages within a stream, distinguishing a slow server from a server that has stalled entirely.
- Stream close reason, tagged as a normal completion, a client cancellation, or an error, since these three outcomes need very different follow-up.
- Bytes buffered per open stream, the direct signal for a backpressure problem before it grows into an out-of-memory failure.

## 17. Security and privacy implications

A long-lived stream held open by a client that never sends further messages, and never closes the connection, can be used to exhaust server-side connection or memory resources if the server does not enforce a maximum stream duration or an idle timeout. Because authentication for a gRPC call typically happens once, at the start of the call, a streaming call that stays open for a very long time may outlive the validity of a short-lived credential, so a server handling long streams needs to re-check authorization periodically rather than assuming the initial check still holds for the entire lifetime of the stream.

## 18. Code examples

### Swift

```swift

protocol MessageStreamHandler {
    func onMessage(_ message: String)
    func onStreamClosed(error: Error?)
}

final class ServerStreamCall {
    private let handler: MessageStreamHandler
    private var isOpen = true

    init(handler: MessageStreamHandler) {
        self.handler = handler
    }

    // Called once per message as the server streams its sequence back.
    func receive(_ message: String) {
        guard isOpen else { return }
        handler.onMessage(message)
    }

    // Called once when the stream ends, on success or failure.
    func close(error: Error?) {
        guard isOpen else { return }
        isOpen = false
        handler.onStreamClosed(error: error)
    }
}

```

### Kotlin

```kotlin

interface MessageStreamHandler {
    fun onMessage(message: String)
    fun onStreamClosed(error: Throwable?)
}

class ServerStreamCall(private val handler: MessageStreamHandler) {
    private var isOpen = true

    // Called once per message as the server streams its sequence back.
    fun receive(message: String) {
        if (!isOpen) return
        handler.onMessage(message)
    }

    // Called once when the stream ends, on success or failure.
    fun close(error: Throwable?) {
        if (!isOpen) return
        isOpen = false
        handler.onStreamClosed(error)
    }
}

```

### Python

```python

class ServerStreamCall:
    def __init__(self, on_message, on_stream_closed):
        self.on_message = on_message
        self.on_stream_closed = on_stream_closed
        self.is_open = True

    def receive(self, message):
        """Called once per message as the server streams its sequence back."""
        if not self.is_open:
            return
        self.on_message(message)

    def close(self, error=None):
        """Called once when the stream ends, on success or failure."""
        if not self.is_open:
            return
        self.is_open = False
        self.on_stream_closed(error)

```

## 19. References

- Google, gRPC documentation, Core concepts, architecture and lifecycle, https://grpc.io/docs/what-is-grpc/core-concepts/
