---
name: Event Queue
slug: event-queue
family: 29-realtime-simulation
category: Real-Time Simulation
aliases: [Message Queue, Mailbox]
first_described: "Robert Nystrom's Event Queue chapter in Game Programming Patterns, in the book's own Decoupling Patterns part"
maturity: canonical
related: [update-method]
incompatible_with: []
verified: 2026-08-23
---

# Event Queue

## 1. Name, aliases, and lineage

An event queue stores pending notifications or requests in first-in,
first-out order, so the moment a message is sent is decoupled from the
moment it is processed.

The clearest, directly verified source is Robert Nystrom's own chapter,
fetched directly (Nystrom, Robert, "Event Queue," Game Programming
Patterns, https://gameprogrammingpatterns.com/event-queue.html, verified
2026-08-23). the chapter's own stated intent, quoted directly. "Decouple
when a message or event is sent from when it is processed" (Nystrom,
"Event Queue," verified 2026-08-23). Nystrom's own book places the chapter
in its Decoupling Patterns part, confirmed via the book's own table of
contents (https://gameprogrammingpatterns.com/contents.html, verified
2026-08-23). the chapter's own See Also section names two established
alternate terms for the same idea, quoted in full under dimension 13,
"message queue" for the higher-level, cross-application case, and
"publish or subscribe" for larger distributed systems.

## 2. Problem and context

The chapter's own motivating example is an audio manager, and it names
three distinct problems with a naive, synchronous playSound call. "our
playSound method is synchronous, it doesn't return back to the caller
until bloops are coming out of the speakers," meaning the caller blocks.
two simultaneous calls to play the same sound stack into one sound "twice
as loud," which is "jarringly loud." and "since our API is synchronous, it
runs on the caller's thread. When we call it from different game systems,
we're hitting our API concurrently from multiple threads" (Nystrom, "Event
Queue," verified 2026-08-23). the chapter's own closing diagnosis names
the common root. "the audio engine interprets a call to playSound to
mean, drop everything and play the sound right now. Immediacy is the
problem" (Nystrom, "Event Queue," verified 2026-08-23).

## 3. Forces

The chapter's own push and pull framing states the tension directly. "you
have some code A that wants another chunk B to do some work... the
natural way for B to process that request is by pulling it in at a
convenient time in its own run cycle," and "when you have a push model on
one end and a pull model on the other, you need a buffer between them"
(Nystrom, "Event Queue," verified 2026-08-23), which is exactly the role
the queue itself plays.

## 4. Applicability and non-applicability

The chapter's own When to Use It section names five points directly. "if
you only want to decouple who receives a message from its sender,
patterns like Observer and Command will take care of this with less
complexity," so "you only need a queue when you want to decouple something
in time." "queues give control to the code that pulls from it, the
receiver can delay processing, aggregate requests, or discard them
entirely," which comes at the direct cost that "queues do this by taking
control away from the sender. All the sender can do is throw a request on
the queue and hope for the best," and "this makes queues a poor fit when
the sender needs a response" (Nystrom, "Event Queue," verified 2026-08-23).

The chapter's own Keep in Mind section names three further cautions
directly, one on ownership, one on staleness, one on reentrancy, each
covered fully under dimension 11.

## 5. Structure

The chapter's own definition, quoted directly. "a queue stores a series of
notifications or requests in first-in, first-out order. Sending a
notification enqueues the request and returns. The request processor then
processes items from the queue at a later time. Requests can be handled
directly or routed to interested parties. This decouples the sender from
the receiver both statically and in time" (Nystrom, "Event Queue," verified
2026-08-23). the chapter's own worked payload example is a PlayMessage
struct carrying a sound id and a volume.

## 6. ASCII structure diagram

```
  push side (sender)              pull side (receiver)

  playSound() call        enqueue         Audio::update()
       |                     |                   |
       v                     v                    v
  reify the request  -->  ring buffer  -->  dequeue on its
  into a PlayMessage       (head, tail)      own schedule

  the ring buffer wraps the tail back to index 0 when it
  runs off the end of the backing array, so a fixed-size
  array never needs to shift elements as items are
  dequeued from the head.

  full-queue guard, the assertion from the chapter itself:

  assert (tail + 1) mod MAX_PENDING is not equal to head
```

## 7. Dynamics

The chapter's own Sample Code section walks the full-queue case directly.
"as we run requests through the queue, the head and tail keep crawling to
the right. Eventually, tail hits the end of the array, and party time is
over." the chapter's own fix is the ring buffer from dimension 6. "we wrap
the tail back around to the beginning of the array when it runs off the
end. That's why it's called a ring buffer, it acts like a circular array
of cells" (Nystrom, "Event Queue," verified 2026-08-23), guarded by an
assertion so the tail can never overwrite the head. ordering is strict
first-in, first-out, and the chapter names no priority ordering beyond
that, treating "aggregating requests," collapsing duplicate or redundant
pending events, as a separate, optional refinement rather than a
reordering mechanism.

## 8. Implementation variants

Node.js's own event loop documents a genuine, live-verified FIFO-queue
mechanism outside games. "each phase has a FIFO queue of callbacks to
execute," and the poll phase's own job is "processing events in the poll
queue" (Node.js, "The Node.js Event Loop, Timers, and process.nextTick,"
verified 2026-08-23). this entry explicitly checked and confirmed Node's
own docs use "FIFO queue" and "phase" language rather than the sender and
receiver, decoupled-in-time framing the book's own chapter uses, so the
structural match, a queue a request is placed onto and later pulled off
at the runtime's own convenience, is real and verified, while the
explicit design-pattern terminology is this entry's own bridge, not a
sentence Node's docs state.

RabbitMQ's own reliability documentation independently corroborates this
entry's own dimension 11 failure-mode findings with real production
delivery terminology the book itself never uses. "use of acknowledgements
guarantees at least once delivery," and "without acknowledgements, message
loss is possible during publish and consume operations and only at most
once delivery is guaranteed" (RabbitMQ, "Reliability Guide," verified
2026-08-23).

## 9. Known production uses

The chapter's own See Also section names the Go programming language's
channel type directly, "essentially an event or message queue" (Nystrom,
"Event Queue," verified 2026-08-23), quoted in full under dimension 13.
the chapter's own body also names a real, first-person production case,
distinct from a citation. "I ran into this exact issue working on Henry
Hatsworth in the Puzzling Adventure. My solution there is similar to what
we'll cover here" (Nystrom, "Event Queue," verified 2026-08-23).

## 10. Consequences

The chapter's own Pattern statement, already quoted in dimension 5, is
itself the benefit summary, decoupling sender from receiver both
statically and in time. the cost is named directly in two places. the
sender-control cost already quoted in dimension 4, and the chapter's own
warning against reaching for the pattern casually. "unlike some more
modest patterns in this book, event queues are complex and tend to have a
wide-reaching effect on the architecture of our games. That means you'll
want to think hard about how, or if, you use one," and "most of us
learned the hard way that global variables are bad... This pattern wraps
that state in a nice little protocol, but it's still a global, with all
of the danger that entails" (Nystrom, "Event Queue," verified 2026-08-23).

## 11. Failure modes and misuse

Queue overflow is the chapter's own first named failure mode, walked
through directly in its own sample code and quoted in full under
dimension 7. feedback loops and reentrancy are the chapter's own second
named failure mode, under its own heading. "all event and message systems
have to worry about cycles... when your messaging system is synchronous,
you find cycles quickly, they overflow the stack and crash your game.
With a queue, the asynchrony unwinds the stack, so the game may keep
running even though spurious events are sloshing back and forth in there.
A common rule to avoid this is to avoid sending events from within code
that's handling one" (Nystrom, "Event Queue," verified 2026-08-23).

A third, distinct failure mode is stale world state at processing time,
under the chapter's own heading. "when you receive an event, you have to
be careful not to assume the current state of the world reflects how the
world was when the event was raised. This means queued events tend to be
more data heavy than events in synchronous systems" (Nystrom, "Event
Queue," verified 2026-08-23). a fourth, related risk from the chapter's
own Design Decisions section is multi-writer cycles. "since anything can
potentially put something onto the queue, it's easier to accidentally
enqueue something in the middle of handling an event. If you aren't
careful, that may trigger a feedback loop" (Nystrom, "Event Queue,"
verified 2026-08-23).

## 12. Trade-off matrix

| Dimension | Event queue | Direct synchronous call |
|---|---|---|
| Caller blocking | Returns immediately, dimension 5 | Blocks until the callee finishes, dimension 2 |
| Concurrent callers | Serialized through the queue, dimension 2 | Runs on each caller's own thread, a real hazard |
| Ordering | Strict first-in first-out, dimension 7 | Whatever order the calls happened to arrive |
| Sender control | Lost once enqueued, dimension 4 | Full, the caller drives the call directly |
| Response to sender | Poor fit, per the chapter's own text, dimension 4 | Natural, the call can return a value |
| Architectural cost | Complex, wide-reaching, dimension 10 | Simple, but reentrancy-prone under load |

## 13. Related and incompatible patterns

Nystrom's own See Also section, transcribed in full. "in many ways, this
pattern is the asynchronous cousin to the well-known Observer pattern."
"one established term is message queue... where our event queues are
within an application, message queues are usually used for communicating
between them." "another term is publish or subscribe, sometimes
abbreviated to pubsub... it usually refers to larger distributed systems."
"a finite state machine, similar to the Gang of Four's State pattern,
requires a stream of inputs... if you want it to respond to those
asynchronously, it makes sense to queue them." "when you have a bunch of
state machines sending messages to each other, each with a little queue
of pending inputs, called a mailbox, then you've re-invented the actor
model of computation." "the Go programming language's built-in channel
type is essentially an event or message queue" (Nystrom, "Event Queue,"
verified 2026-08-23).

Observer is confirmed present, and it leads the list, the "asynchronous
cousin" framing the task of checking this cross-reference set out to
verify. inline, not in See Also, the chapter also references Command, "another
word for request is command, as in the Command pattern, and queues can be
used there too," Service Locator, Singleton for the audio-engine example
itself, Update Method for the `Audio::update` sample code, Data Locality
for why a plain array beats a linked structure as the queue's own backing
store, and Object Pool for the "the queue owns it" lifetime-management
design option.

## 14. Refactoring path in and out

The chapter's own Sample Code section is itself an explicit, three-stage
refactor of the naive synchronous API from dimension 2. first, reify the
request into a PlayMessage struct and buffer it, removing the blocking
call. second, turn the fixed array into a ring buffer, per dimension 7,
adding correct dequeue-from-the-front semantics. third, make the queue
thread-safe, spanning threads. the chapter's own transition sentence,
quoted directly. "we want to defer that work until later so that
playSound can return quickly. To do that, we need to reify the request to
play a sound" (Nystrom, "Event Queue," verified 2026-08-23). this entry
did not find guidance on migrating back out of an event queue toward
direct calls, and reports that absence directly.

## 15. Testing and verification

This entry explicitly checked the full chapter for a discussed testing or
verification methodology and confirmed none exists, distinct from the
runtime assert guard from dimension 7, which is an invariant check
embedded in the code, not a testing methodology. reporting that
distinction and the absence directly rather than conflating the two.

## 16. Observability signals

The chapter's own text names one concrete recommendation directly. "a
little debug logging in your event system is probably a good idea too"
(Nystrom, "Event Queue," verified 2026-08-23), offered beside the
feedback-loop warning from dimension 11. this entry explicitly checked
and did not find a named metric such as queue depth or processing lag
anywhere in the fetched primary or secondary sources, reporting that
absence directly rather than inventing a metric name.

## 17. Security and privacy implications

This entry did not find the chapter addressing a security or privacy
concern directly. a reasoned, explicitly unsourced extension of the
pattern's own structure follows from dimension 14's own reification step.
a message that outlives the call that enqueued it holds any sensitive
payload data in memory for a longer, less deterministic window than a
direct synchronous call would, and in the queue-owns-it storage variant
from dimension 13, that memory may not be zeroed between reuses. this is
this entry's own structural reasoning, not a claim the chapter or either
fetched production source makes.

## 18. References

1. Nystrom, Robert, "Event Queue," Game Programming Patterns,
   https://gameprogrammingpatterns.com/event-queue.html, verified
   2026-08-23.
2. Nystrom, Robert, "Game Programming Patterns," table of contents,
   https://gameprogrammingpatterns.com/contents.html, verified 2026-08-23.
3. Node.js, "The Node.js Event Loop, Timers, and process.nextTick," Node.js
   documentation, verified 2026-08-23.
4. RabbitMQ, "Reliability Guide," verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of the ring-buffer event queue
from dimensions 6 and 7, with the full-queue assertion guard applied
directly.

```typescript
interface PlayMessage {
  soundId: number;
  volume: number;
}

class EventQueue {
  private buffer: (PlayMessage | undefined)[];
  private head = 0;
  private tail = 0;

  constructor(private capacity: number) {
    this.buffer = new Array(capacity);
  }

  enqueue(message: PlayMessage): void {
    if ((this.tail + 1) % this.capacity === this.head) {
      throw new Error("event queue is full");
    }
    this.buffer[this.tail] = message;
    this.tail = (this.tail + 1) % this.capacity;
  }

  dequeue(): PlayMessage | undefined {
    if (this.head === this.tail) {
      return undefined;
    }
    const message = this.buffer[this.head];
    this.head = (this.head + 1) % this.capacity;
    return message;
  }
}
```

```python
from typing import List, Optional, NamedTuple


class PlayMessage(NamedTuple):
    sound_id: int
    volume: int


class EventQueue:
    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._buffer: List[Optional[PlayMessage]] = [None] * capacity
        self._head = 0
        self._tail = 0

    def enqueue(self, message: PlayMessage) -> None:
        if (self._tail + 1) % self._capacity == self._head:
            raise RuntimeError("event queue is full")
        self._buffer[self._tail] = message
        self._tail = (self._tail + 1) % self._capacity

    def dequeue(self) -> Optional[PlayMessage]:
        if self._head == self._tail:
            return None
        message = self._buffer[self._head]
        self._head = (self._head + 1) % self._capacity
        return message
```

```go
package eventqueue

import "errors"

type PlayMessage struct {
	SoundID int
	Volume  int
}

type EventQueue struct {
	buffer   []PlayMessage
	capacity int
	head     int
	tail     int
}

func NewEventQueue(capacity int) *EventQueue {
	return &EventQueue{buffer: make([]PlayMessage, capacity), capacity: capacity}
}

func (q *EventQueue) Enqueue(message PlayMessage) error {
	if (q.tail+1)%q.capacity == q.head {
		return errors.New("event queue is full")
	}
	q.buffer[q.tail] = message
	q.tail = (q.tail + 1) % q.capacity
	return nil
}

func (q *EventQueue) Dequeue() (PlayMessage, bool) {
	if q.head == q.tail {
		return PlayMessage{}, false
	}
	message := q.buffer[q.head]
	q.head = (q.head + 1) % q.capacity
	return message, true
}
```
