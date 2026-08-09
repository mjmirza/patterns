---
name: Peer-to-Peer
slug: peer-to-peer
family: 05-architectural
category: Architectural
aliases: [P2P, Overlay Network, Serverless Network Architecture]
first_described: "Schollmeier 2001"
maturity: canonical
related: [event-driven-architecture, publish-subscribe, gossip-protocol, circuit-breaker, saga]
incompatible_with: [layered-architecture]
verified: 2026-08-02
---

# Peer-to-Peer

## 1. Name, aliases, and lineage

The canonical name is Peer-to-Peer, almost always abbreviated P2P. Every
participant in the system, called a peer or a node, can act as both a client
that consumes a resource and a server that provides one, and no peer holds
structural authority over any other. The term predates the architecture
literature by decades as an informal industry phrase, but the first widely
cited formal definition comes from Rudiger Schollmeier, "A Definition of Peer
to Peer Networking for the Classification of Peer to Peer Architectures and
Applications", Proceedings of the First International Conference on Peer to
Peer Computing, IEEE, 2001. Schollmeier's definition separates a peer-to-peer
network from a client-server network on exactly one axis. Whether the
participating nodes share a subset of their own resources directly with each
other, without those resources passing through a dedicated, centrally
administered server ([IEEE Xplore abstract for Schollmeier 2001](https://ieeexplore.ieee.org/document/990434),
verified 2026-08-02).

The name overlay network is used almost interchangeably in the systems
literature, because a P2P system is nearly always built as a logical network
layered on top of the physical Internet, where the edges of the overlay graph
are application-level connections rather than physical links. The overlay is
the pattern's structural signature. Peers do not need to know the network
topology beneath them, only their logical neighbors in the overlay.

Two further distinctions recur throughout the literature and this entry uses
them precisely.

- **Unstructured P2P.** Peers connect to an arbitrary, ad hoc set of
  neighbors, and a query or a message is found or delivered by flooding,
  random walk, or gossip, with no guarantee on the number of hops. Early
  Gnutella is the textbook unstructured example.
- **Structured P2P.** Peers and data are placed at deterministic positions in
  a shared coordinate space, most often via consistent hashing onto a ring or
  a binary tree, and a lookup for a key is guaranteed to resolve in a bounded
  number of hops, typically logarithmic in the number of peers. Chord (Ion
  Stoica, Robert Morris, David Karger, M. Frans Kaashoek, and Hari
  Balakrishnan, "Chord, A Scalable Peer-to-peer Lookup Service for Internet
  Applications", ACM SIGCOMM Computer Communication Review, 2001) and
  Kademlia (Petar Maymounkov and David Mazieres, "Kademlia, A Peer-to-peer
  Information System Based on the XOR Metric", 2002) are the two most cited
  structured designs, and this entry treats a Distributed Hash Table, DHT, as
  the structured sub-pattern's canonical implementation
  ([Wikipedia summary of the Chord paper and its 2011 ACM SIGCOMM Test of
  Time award](https://en.wikipedia.org/wiki/Chord_(peer-to-peer)),
  verified 2026-08-02;
  [Wikipedia summary of the Kademlia paper](https://en.wikipedia.org/wiki/Kademlia),
  verified 2026-08-02).

A third, hybrid form sits between the two poles. A small set of nodes takes on
a coordination role (indexing, bootstrapping, or relaying) while the bulk of
the traffic still flows peer to peer. Napster is the historically important
example, and this entry treats it as a distinct, weaker pattern in the
applicability section rather than as pure P2P, because Napster's file index
lived on centrally administered servers even though the file transfers
themselves were direct between users
([Wikipedia's Napster article, describing the centralized index and the
2001 shutdown](https://en.wikipedia.org/wiki/Napster), verified 2026-08-02).

## 2. Problem and context

A system needs many participants to exchange data or share work, and at least
one of the following forces makes a single, dedicated server the wrong place
to put that coordination.

The first shape of the problem is scale that grows with adoption rather than
with budget. A file-distribution service whose most popular file is requested
by a hundred thousand clients at once cannot serve every byte from one origin
without either an enormous, mostly idle server fleet or an expensive content
delivery network, and both of those solutions still concentrate cost on the
publisher rather than distributing it across the people who actually want the
file. BitTorrent exists because the people downloading a large file have,
collectively, exactly the upload bandwidth needed to reseed it to each other,
and the publisher's job shrinks to seeding the first complete copy and letting
demand supply the rest.

The second shape is the absence of a natural, trusted party to run the server.
A currency, a naming system, or a content-addressed store that any single
organization operates is a currency, naming system, or store that the
organization can censor, tax, or shut down. Bitcoin's original description
states the requirement directly. An electronic payment system based on
cryptographic proof instead of trust, so that any two willing parties can
transact directly with each other without the need for a trusted third party
([Satoshi Nakamoto, "Bitcoin, A Peer-to-Peer Electronic Cash System", 2008,
the original whitepaper](https://bitcoin.org/bitcoin.pdf), the design itself is
a decentralized peer-to-peer accounting overlay running on top of a P2P
gossip network of nodes that relay transactions and blocks to their
neighbors).

The third shape is a real-time interaction between two specific parties where
routing the media through a server adds latency and cost for no benefit. A
voice call or a video call between two browsers gains nothing from bouncing
every packet through a relay when the two endpoints can, after a brief
signaling handshake through some other channel, open a direct connection.
WebRTC's data and media channels are designed around exactly this shape, and
they fall back to a relay, TURN, only when a direct path cannot be
established because of restrictive network address translation.

The fourth shape is content that should be addressable by what it is rather
than by where it currently happens to live, so that a link to it survives the
original host disappearing. The InterPlanetary File System, IPFS, motivates
its peer-to-peer content-routing layer on exactly this problem. Data is
addressed by its contents rather than by a location such as an IP address, and
a Kademlia-based distributed hash table running over the libp2p network stack
lets any peer discover which other peers currently hold a copy of a given
piece of content
([IPFS documentation, "How IPFS works"](https://docs.ipfs.tech/concepts/how-ipfs-works/),
verified 2026-08-02).

Across all four shapes, the common context is the same. The resource being shared,
whether it is bandwidth, storage, trust, or a direct low-latency channel, is
already distributed among the participants before the system exists. The
architecture's job is to let the participants find each other and exchange
that resource directly, rather than to manufacture a central point that owns
it.

## 3. Forces

**Scalability against a single origin's capacity.** A client-server system's
throughput is bounded by the server's provisioned capacity, which the
operator must pay for in advance of demand. A P2P system's aggregate capacity
grows automatically as new peers join, because each new peer arrives carrying
its own bandwidth, storage, and compute. This is the force P2P is built to
maximize, and it is the one most catalogs describe first.

**Resilience against a single point of failure.** No dedicated server means
no single machine, when it goes down, takes the whole system with it. A
structured overlay with redundant routing table entries survives a
substantial fraction of its peers churning, disconnecting and reconnecting,
without losing the ability to route lookups, because Kademlia and Chord both
maintain multiple redundant paths to any given point in the key space rather
than one.

**Latency for direct exchange versus latency for coordination.** A direct
peer-to-peer transfer between two nearby endpoints can beat a client-server
transfer that must round-trip through a distant data center. But finding the
right peer to talk to in the first place, especially in a structured overlay,
costs a logarithmic number of hops before the direct transfer can even begin,
and in an unstructured overlay a flooded query can cost far more than that
with no upper bound. P2P trades an upfront discovery cost for a cheaper
steady-state transfer cost, and the trade only pays off when the transfer is
large or repeated relative to the discovery cost.

**Consistency against availability under partition.** A single server can
maintain one authoritative view of the system's state trivially, because
there is only one copy of it. A P2P system has no single copy by
construction, so any piece of information that changes must either be
re-derived from a canonical, cryptographically verifiable source (as in
Bitcoin's blockchain, where every peer independently validates the same
chain), gossiped to eventual consistency (as in a distributed hash table's
key-value store, where a write is only as durable as the set of peers that
currently hold a replica), or accepted as genuinely inconsistent across the
network at any given instant. This is the CAP theorem's classic tension,
made structural rather than optional.

**Operability against no operator.** A client-server system has an operator
who can patch a bug, roll back a bad deploy, or ban an abusive client by
IP address, because the operator's machine mediates every interaction. A P2P
system with no privileged coordinating node has no equivalent lever. Fixing a
protocol bug requires every peer, or a decisive majority of them, to adopt a
new client version, and there is no way to force that adoption. This is the
force P2P sacrifices most visibly, and it is the reason a P2P architecture is
a governance decision as much as a technical one.

**Trust and incentive alignment among strangers.** A client-server system can
assume the server behaves correctly because the operator built it and is
accountable for it. A P2P system must assume every peer might behave
adversarially, might free-ride by consuming resources without contributing
any back, or might actively try to corrupt the shared state, and the protocol
has to be designed so that honest behavior is either enforced by cryptography
or made individually rational. BitTorrent's tit-for-tat choking algorithm,
where a peer preferentially uploads to peers that have recently uploaded to
it, exists specifically to make free-riding unprofitable
([Wikipedia's BitTorrent article on the tit-for-tat exchange scheme and
optimistic unchoking](https://en.wikipedia.org/wiki/BitTorrent),
verified 2026-08-02).

**Cost of ownership.** A P2P architecture that succeeds shifts most of the
running cost of bandwidth and storage from the publisher onto the collective
of participants, which is a direct financial force behind its adoption for
large-scale content distribution, and a direct reason regulated,
liability-bearing businesses generally avoid it for anything they must
remain accountable for.

## 4. Applicability and non-applicability

Reach for peer-to-peer when the following hold together, not individually.

- The resource to be shared, bandwidth, storage, or compute, scales with the
  number of participants, and demand for it also scales with the number of
  participants, so the two grow together rather than one outpacing the
  other. Large file distribution is the archetype.
- No single organization is a natural, trusted, permanent operator of the
  coordinating server, either because trust itself is the thing being
  removed from the design (a currency, a public ledger) or because no party
  wants the long-term liability and cost of running that server forever.
- The system must survive individual participants disappearing at any time,
  without a maintenance window and without an administrator noticing first.
- Direct participant-to-participant communication genuinely reduces latency
  or cost relative to relaying through a server, which is true for
  large-payload or long-lived transfers and false for small, sporadic
  interactions where the discovery overhead outweighs the transfer.
- The data or workload can tolerate eventual consistency, or the protocol
  design includes an explicit mechanism, such as a cryptographic proof
  chain, for every peer to independently verify a canonical state without a
  trusted intermediary.

Do NOT reach for peer-to-peer, and prefer a client-server or a managed
message-broker design instead, when any of these hold.

- **The workload is small, bursty, and short-lived relative to peer
  discovery cost.** If most interactions transfer a few kilobytes and happen
  once, the cost of finding the right peer, whether by a DHT lookup or by
  flooding, dwarfs the cost of the transfer itself, and a simple request to a
  known server wins on both latency and code complexity.
- **The system requires strong, immediate consistency.** A bank ledger, an
  inventory count, or any system where two conflicting writes must be
  resolved before either is acknowledged needs a single source of truth or a
  consensus protocol with a leader, not a P2P overlay that only converges
  eventually.
- **The organization needs to be able to patch, moderate, or shut the
  system down on short notice.** Regulatory compliance, abuse response, and
  incident recovery are all vastly easier with a server the organization
  controls. Napster's central index made it possible for a court to order
  Napster to filter infringing material; a purely decentralized successor
  had no equivalent lever, which is precisely why the file-sharing industry
  moved toward architectures like BitTorrent after Napster's 2001 shutdown
  ([Wikipedia's Napster article on the court order and its consequence for
  the network's design](https://en.wikipedia.org/wiki/Napster),
  verified 2026-08-02).
- **The team cannot afford NAT traversal and firewall complexity.** A
  meaningful fraction of real Internet hosts sit behind network address
  translation or restrictive firewalls that block unsolicited inbound
  connections, so any P2P design must budget for hole punching, relay
  fallback (as in WebRTC's TURN servers), or accept that some peers can only
  ever be reached, never dial out to. This is a substantial, often
  underestimated engineering cost that a client-server design does not pay,
  because the server's address is always public and reachable by
  construction.
- **Regulatory or liability exposure requires a single accountable
  operator.** Financial transactions, health data, and anything subject to a
  data-residency requirement generally need one party who can be held
  responsible, audited, and instructed to comply, which a leaderless overlay
  structurally cannot provide.
- **The team is small and the deadline is short.** A correct DHT
  implementation, or a correct gossip protocol with bounded convergence time,
  is genuinely hard distributed-systems engineering. A managed queue or a
  conventional API server, built by a small team on a normal schedule, is a
  better bet unless the P2P properties are the actual product requirement.

## 5. Structure

- **Peer (node).** The single participant type in a pure P2P system. Every
  peer carries the same code, the same protocol implementation, and the same
  set of responsibilities as every other peer. It can originate a request, it
  can serve a request from another peer, and it can relay a request or a
  piece of data on behalf of a third peer. Nothing in the protocol
  distinguishes one peer from another by role, only by the data or resources
  it currently happens to hold.
- **Overlay link (neighbor edge).** A logical, application-level connection
  between two peers, layered on top of an ordinary transport connection
  such as TCP or QUIC. The set of overlay links across all peers forms the
  overlay graph, and this graph, not the physical network topology beneath
  it, is what the routing or discovery algorithm actually reasons about.
- **Discovery or bootstrap mechanism.** Some way for a new peer to find its
  first few neighbors when it joins with no prior knowledge of the network.
  This is almost always the one piece of the system that is NOT purely
  peer-to-peer. A small, fixed set of well-known bootstrap addresses, a
  DNS seed list, or a rendezvous server. BitTorrent's tracker plays this
  role, and its presence is why BitTorrent is sometimes classified as hybrid
  rather than pure P2P at the discovery layer even though file transfer
  itself is peer to peer.
- **Routing or lookup algorithm.** In an unstructured overlay, this is
  flooding (forward to every neighbor, bounded by a time-to-live) or a random
  walk. In a structured overlay, this is a deterministic algorithm, most
  often built on consistent hashing, that maps a key to a specific peer or a
  small, well-defined set of peers responsible for it, in a bounded number of
  hops.
- **Routing table (structured overlays only).** Each peer's partial view of
  the overlay, sized so that a lookup takes on average a logarithmic number
  of hops rather than requiring every peer to know every other peer.
  Kademlia's routing table is organized as buckets keyed by XOR distance to
  the peer's own identifier; Chord's is a finger table of successor pointers
  at exponentially increasing offsets around a ring.
- **Local storage or cache.** What each peer actually holds and can serve,
  a file's data blocks, a fragment of a distributed hash table's key space, a
  copy of a shared ledger, or nothing more than routing state, depending on
  the system.
- **Message protocol.** The wire format for the operations peers perform on
  each other, PING, STORE, FIND_NODE, and FIND_VALUE in Kademlia, the
  handshake, choke, unchoke, have, and piece messages in BitTorrent's peer
  wire protocol; block and transaction relay messages in Bitcoin's network
  protocol.

## 6. ASCII structure diagram

```text
                UNSTRUCTURED (flood / random walk)

        +======+          +======+
        | Peer |..........| Peer |
        |  A   |          |  B   |
        +==+===+          +==+===+
           |     \       /    |
           |      \     /     |
        +==+===+   \   /   +==+===+
        | Peer |    \ /    | Peer |
        |  C   |=====X=====|  D   |
        +==+===+    / \    +==+===+
           |        each edge is
           |     a plain overlay
        +==+===+   connection, no
        | Peer |   central node
        |  E   |
        +======+

  Any peer can query any neighbor. A query with no target
  address is flooded outward, bounded by a hop count (TTL).


                STRUCTURED (DHT, consistent-hash ring)

              key space, mod 2^m, wraps around

        0 ====================================== 2^m-1
        |                                        |
        v                                        v
     +=====+        +=====+        +=====+    +=====+
     |Peer0|======> |Peer1|======> |Peer2|==> |Peer3|==+
     +=====+        +=====+        +=====+    +=====+  |
        ^                                               |
        +=================================================+
              successor pointer wraps back to Peer0

  key "invoice:1042" hashes into the ring; ownership goes
  to the first peer whose id is >= the key's hashed position.
  each peer also keeps a routing table of further-out peers
  (Chord's finger table, Kademlia's k-buckets) so a lookup
  resolves in O(log N) hops instead of walking the ring.
```

## 7. Dynamics

```text
STRUCTURED LOOKUP (a peer wants to find who owns key K)

  requesting peer P
        |
        | 1. compute hash(K), compare to own routing table
        v
   +=========+   2. forward to the closest known peer to hash(K)
   |  peer A |==============================+
   +=========+                              |
                                             v
                                        +=========+
                                        |  peer B |
                                        +=========+
                                             | 3. B is still not the
                                             |    owner, forwards to
                                             |    an even closer peer
                                             v
                                        +=========+
                                        |  peer C |   <= owner of K
                                        +=========+
                                             |
                                             | 4. C replies directly
                                             |    to P (not relayed
                                             |    back through A, B)
                                             v
        each hop halves (Chord) or roughly
        halves (Kademlia's XOR metric) the
        remaining distance to the target,
        so total hops ~ log2(N) for N peers


JOIN AND FAILURE (churn)

  new peer N joins
        |
        v
  contact a bootstrap peer  ====> ask it for neighbors
        |                              close to N's own id
        v
  N inserts itself into the ring / routing tables of
  the peers whose responsibility now overlaps with N's
  arrival; those peers transfer the key ranges N now
  owns to N
        |
        v
  an existing peer M disappears without warning
        |
        v
  the next periodic stabilization round on M's former
  neighbors notices missed pings, removes M from their
  routing tables, and re-routes M's former key range to
  M's successor, using the REDUNDANT copies that were
  already replicated onto multiple peers before M left


GOSSIP CONVERGENCE (anti-entropy, unstructured membership)

  round 1:  A knows {A,B}      B knows {A,B,C}    C knows {C,D}
  round 2:  A<>B exchange   =>  A knows {A,B,C}    B knows {A,B,C}
  round 3:  B<>C exchange   =>  B knows {A,B,C,D}  C knows {A,B,C,D}
  round 4:  A<>C exchange   =>  A knows {A,B,C,D}
  ... after O(log N) rounds every peer's view has converged
```

## 8. Implementation variants

**Unstructured flood, bounded by time-to-live.** The simplest variant. A peer
that wants to find something sends a query to every neighbor, each of which
forwards it to every neighbor it has not already sent it to, decrementing a
hop count each time, until the count reaches zero. This is what early
Gnutella did for file search. It is easy to implement and tolerates churn
well, because there is no routing state to keep consistent, but it does not
scale, the number of messages generated by a single query grows
combinatorially with the network's connectivity, and there is no guarantee
the query ever reaches the peer that has the answer.

**Random walk.** A variant of flooding where the query is forwarded to one
randomly chosen neighbor at a time instead of every neighbor, trading a
probabilistic, sometimes-slower discovery for a dramatic reduction in message
volume. Used as a lighter-weight alternative to flooding in several
Gnutella-derived designs and in some DHT bootstrap procedures.

**Gossip (epidemic) protocols for membership and state dissemination.**
Instead of routing a specific query, peers periodically pick a random
neighbor and exchange their current view of some shared state, such as which
peers are alive, or the latest version of a small piece of data. Convergence
across the whole network happens in a number of rounds that grows only
logarithmically with the number of peers, which is the same mathematical
shape as an epidemic spreading through a population, hence the name. Amazon's
Dynamo storage system uses exactly this technique for cluster membership and
failure detection, explicitly favoring decentralized peer-to-peer techniques
over centralized control so that the system avoids a centralized registry for
membership and liveness information
([Wikipedia's Dynamo article summarizing the gossip-based membership
protocol](https://en.wikipedia.org/wiki/Dynamo_(storage_system)),
verified 2026-08-02).

**Structured overlay via consistent hashing (Chord).** Every peer and every
data item is hashed into the same fixed-size identifier space, arranged as a
ring. A peer owns the range of the ring between itself and its predecessor.
Lookups walk successor pointers, accelerated by a finger table of
exponentially spaced shortcut pointers, giving O(log N) hop lookups and O(log
N) routing table size per peer.

**Structured overlay via XOR distance (Kademlia).** Peer and key identifiers
live in the same space, and the "distance" between two identifiers is their
bitwise XOR, interpreted as an integer. Each peer keeps a set of k-buckets,
one per bit of distance, holding up to k known peers at that distance. A
lookup iteratively queries the closest known peers to the target and refines
as closer peers are discovered, which parallelizes better than Chord's
single-successor walk and tolerates peer churn more gracefully because
multiple peers are queried at each step rather than one. Kademlia is the
design underneath BitTorrent's trackerless Mainline DHT and underneath IPFS's
content routing layer.

**Hybrid, indexed P2P.** A small, centrally operated set of servers indexes
what each peer holds, but the actual data transfer happens directly between
peers. Napster's central song index paired with direct file transfer is the
defining example. This variant sacrifices some of P2P's resilience and
censorship resistance in exchange for dramatically simpler, faster discovery,
because a single index lookup replaces a flood or a multi-hop DHT walk.

**Supernode hierarchy.** A subset of peers, chosen because they have
sufficient bandwidth, uptime, and a public IP address, take on extra
coordination responsibility, such as relaying signaling messages or indexing
which ordinary peers hold which resources, while remaining ordinary
participants otherwise. Skype's original architecture used exactly this
design. Any sufficiently capable client could become a supernode, each client
kept a cache of reachable supernodes, and user-directory data was distributed
across the supernode layer rather than held on a Skype-operated server. In
2012 Microsoft moved supernode responsibility onto Microsoft-operated data
centers, ending the design's pure peer-to-peer property for this specific
function
([Wikipedia's Skype protocol article on the original supernode design and
the 2012 transition](https://en.wikipedia.org/wiki/Skype_protocol),
verified 2026-08-02).

**Blockchain-backed peer-to-peer.** Every peer independently maintains and
validates a full or partial copy of a shared, append-only, cryptographically
linked ledger, and the network's gossip layer propagates new transactions and
blocks to all peers, with a consensus rule, such as proof of work, deciding
which of several competing views of the ledger is canonical when peers
temporarily disagree. Bitcoin's peer network is the reference example of this
variant, layering an economic incentive and a cryptographic proof on top of
an otherwise ordinary flood-gossip message-relay overlay.

## 9. Known production uses

- **BitTorrent.** Designed by Bram Cohen, first released July 2001, remains
  in wide use for large-file distribution, including Linux distribution
  images and game-patch delivery. Its swarm model has each downloading peer,
  called a leecher, immediately begin re-uploading the pieces it has already
  received to other peers in the same swarm, and a peer that holds the
  complete file, a seeder, continues uploading purely to sustain the swarm.
  The tit-for-tat choking algorithm preferentially serves peers that have
  recently uploaded in return, and optimistic unchoking periodically serves a
  random peer anyway so that new entrants to the swarm are not permanently
  starved out
  ([Wikipedia's BitTorrent article](https://en.wikipedia.org/wiki/BitTorrent),
  verified 2026-08-02).
- **IPFS (InterPlanetary File System).** Uses a Kademlia-based distributed
  hash table running over the libp2p network stack for content routing,
  letting any peer discover which other peers currently hold a copy of a
  given content-addressed block. Bitswap, the protocol that both routes and
  transfers the actual data between peers, also runs over libp2p
  ([IPFS documentation, "How IPFS works"](https://docs.ipfs.tech/concepts/how-ipfs-works/),
  verified 2026-08-02).
- **libp2p.** A modular system of protocols and libraries, extracted from
  IPFS's networking layer and now used independently by other projects, for
  building peer-to-peer applications with pluggable transports (TCP, QUIC,
  WebSocket, WebRTC), automatic protocol negotiation, and built-in
  transport-layer encryption via Noise or TLS 1.3
  ([libp2p project site](https://libp2p.io/), verified 2026-08-02).
- **Bitcoin's peer network.** Every full node maintains connections to a set
  of peers, relays new transactions and blocks by flooding them outward, and
  independently validates the canonical chain, with no server anywhere in
  the system that any node is required to trust. The design's stated
  purpose is to let two willing parties transact directly without a trusted
  third party
  ([bitcoin.org, "Bitcoin, A Peer-to-Peer Electronic Cash System"](https://bitcoin.org/bitcoin.pdf),
  the whitepaper's design description).
- **Amazon Dynamo.** Uses consistent hashing for data partitioning across
  storage nodes and a gossip-based membership and failure-detection protocol
  that explicitly avoids a centralized registry, so that every storage node
  carries the same set of responsibilities as every other node
  ([Wikipedia's Dynamo (storage system) article](https://en.wikipedia.org/wiki/Dynamo_(storage_system)),
  verified 2026-08-02). This entry judges the design as peer-to-peer at the
  cluster-membership layer even though the storage nodes are all operated by
  a single organization, because the coordination mechanism itself has no
  privileged member.
- **Skype (original architecture, 2003 to 2012).** Voice and video calls were
  routed through a self-organizing hierarchy of supernodes drawn from
  ordinary capable clients, with a login server handling authentication only,
  not media relay. Microsoft moved supernode responsibility onto its own
  data centers in 2012
  ([Wikipedia's Skype protocol article](https://en.wikipedia.org/wiki/Skype_protocol),
  verified 2026-08-02). This is included as a historically important,
  now-superseded production use, not as a currently running P2P system.
- **Napster (1999 to 2001), as the historically important hybrid, not pure
  P2P.** A centralized index server tracked which files each connected
  client held, and clients then transferred files directly to each other.
  The court order that ultimately shut Napster down could target the central
  index precisely because it existed
  ([Wikipedia's Napster article](https://en.wikipedia.org/wiki/Napster),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Aggregate system capacity, bandwidth, storage, and compute, scales with the
  number of participants rather than with a fixed budget, so a P2P system's
  cost curve for the operator can stay flat, or even shrink per user, as
  adoption grows.
- No single machine's failure takes the whole system down, because no
  machine is structurally required for the system to keep functioning,
  provided a sufficient number of the redundant copies of any given piece of
  data or routing state survive.
- Censorship and single-party control become structurally harder, because
  there is no server to subpoena, shut down, or coerce that would take the
  network with it. This is a deliberate design goal for Bitcoin and for
  IPFS, not a side effect.
- The system continues to function, sometimes at reduced capacity, under
  partial network partition, because peers that can still reach each other
  keep working even while cut off from the rest of the network.

Negative.

- Strong, immediate consistency is difficult to achieve and expensive to
  approximate; most P2P systems settle for eventual consistency, a
  cryptographically verifiable canonical log, or accept genuine, temporary
  disagreement between peers as a normal operating condition.
- There is no operator lever to patch a bug quickly, ban an abusive
  participant instantly, or force a protocol upgrade. Coordinating a change
  across an install base with no central update mechanism can take years, and
  a network that forks over a disagreement about the protocol, as several
  blockchain networks have, can split into two incompatible populations
  permanently.
- NAT traversal, firewall punching, and the cost of a fallback relay for the
  minority of peers that cannot be reached directly are a real, ongoing
  engineering tax that a client-server design does not pay at all, because
  the server's address is always dialable.
- The system must be engineered against adversarial and free-riding
  participants from day one, because there is no trusted operator vetting
  who joins; incentive mechanisms like tit-for-tat, or cryptographic proof
  mechanisms like proof of work, add real design and implementation
  complexity that has no equivalent in a trusted, single-operator server.
- Debugging and operating the system is genuinely harder, because there is no
  single log to tail, no single dashboard showing global state, and
  reproducing a bug that depends on the specific overlay topology a user's
  peer happened to have at the time can be close to impossible after the
  fact.

## 11. Failure modes and misuse

- **Symptom.** A lookup that should take a handful of hops instead times out
  or takes dozens of hops. **Cause.** The peer's routing table is stale,
  typically because churn has been faster than the protocol's stabilization
  interval, so a meaningful fraction of the peers it believes are its
  neighbors have actually left the network. **Fix.** Shorten the stabilization
  interval, or, in Kademlia-style designs, increase k, the bucket
  replication factor, so a bucket surviving a burst of departures is more
  likely, and add active liveness pings rather than relying only on
  passive discovery through incoming traffic.
- **Symptom.** The same message or query arrives at a peer many times, or
  floods the whole network even though the answer was found after two
  hops. **Cause.** An unstructured flood with no, or an insufficiently
  aggressive, duplicate-suppression mechanism, so the same message keeps
  being re-forwarded along every cycle in the overlay graph. **Fix.** Every
  relayed message needs a unique identifier and every peer needs to record
  identifiers it has already forwarded, dropping repeats immediately, which
  is the same technique the Go example in this entry implements explicitly.
- **Symptom.** A handful of well-connected peers end up carrying almost all
  the traffic, and the network's throughput collapses when one of them goes
  offline. **Cause.** An overlay whose neighbor-selection policy is biased,
  intentionally as with supernodes or accidentally as a side effect of a
  naive bootstrap procedure that always points new peers at the same few
  seed nodes, toward a small hub set. This reintroduces a single point of
  failure inside an architecture whose entire premise was to remove one.
  **Fix.** Bound the maximum fan-in any single peer is allowed to serve, and
  bias bootstrap toward diverse, recently-seen peers rather than a fixed
  seed list.
- **Symptom.** Two peers holding different, both internally consistent,
  copies of the same piece of shared state, with no automatic mechanism to
  reconcile them. **Cause.** Eventual consistency without a merge or
  conflict-resolution strategy, so a write accepted by two different
  replicas during a network partition simply diverges. **Fix.** Use a
  conflict-free replicated data type, a vector clock, or a
  reconciliation-on-read strategy, as Dynamo does, rather than assuming
  writes will never race.
- **Symptom.** The network is unusable within days of launch because it fills
  up with junk data, spam queries, or free-riding peers that consume far
  more than they contribute. **Cause.** No incentive or cost mechanism was
  designed in from the start, on the assumption that participants will
  behave cooperatively by default. **Fix.** This cannot be retrofitted cheaply. It has to be part of the initial protocol design, whether as an economic
  incentive like BitTorrent's tit-for-tat, a computational cost like proof
  of work, or a reputation system peers can consult before serving a
  request.
- **Symptom.** The team keeps having to add "one more" centrally
  operated service, a bootstrap list, a name resolution service, a
  reputation oracle, until the system that was supposed to be
  peer-to-peer is quietly load-bearing on a handful of servers the team
  operates. **Cause.** Pure P2P was chosen for its architectural purity
  rather than because the applicability criteria in dimension 4 were
  actually met, and each subsequent operational problem gets patched with a
  small, individually reasonable, centralizing fix. **Fix.** This is a scope
  decision, not a bug; either accept explicitly and document that the system
  is hybrid, as BitTorrent's trackers and Napster's index both were, or
  revisit whether P2P was the right architecture at all.

## 12. Trade-off matrix

| Force | Peer-to-Peer (structured, DHT) | Client-Server | Hybrid indexed P2P | Event-driven / message broker |
|---|---|---|---|---|
| Capacity scales with adoption | Yes, automatically | No, bounded by provisioned server capacity | Partially, transfer scales but index does not | No, broker capacity is provisioned |
| Single point of failure | None by design, redundant routing and replication | The server, or its cluster | The central index server | The broker cluster |
| Lookup or discovery latency | O(log N) hops, plus real network RTT per hop | O(1), a single request to a known address | O(1) for the index lookup | O(1) to publish, consumers pull independently |
| Consistency guarantee | Eventual, or cryptographically verifiable log | Strong, trivially, one copy of the truth | Strong for the index, direct transfer is out of band | Depends on broker; usually at-least-once delivery |
| Operator ability to patch, moderate, or ban | Effectively none | Full and immediate | Full for the index, none for the transfer | Full, the broker is centrally operated |
| Engineering cost to build correctly | High, NAT traversal, churn handling, adversarial peers | Low, decades of tooling and patterns | Medium, index is conventional, transfer needs P2P handling | Medium, broker operations expertise required |
| Cost distribution | Spread across participants | Concentrated on the operator | Split, index cost on operator, transfer cost on participants | Concentrated on the operator running the broker |
| Censorship or single-party takedown resistance | High | None | Low, index is a single target | None |

## 13. Related and incompatible patterns

- **Gossip Protocol.** The dissemination mechanism most unstructured P2P
  membership and state-propagation designs use internally; it is a component
  pattern that composes inside peer-to-peer rather than a separate
  architecture, and Dynamo's use of gossip for cluster membership shows the
  same technique applied inside a system that is not, at the storage-API
  layer, presented to its own clients as peer-to-peer at all.
- **Publish-Subscribe.** A P2P overlay is frequently used as the transport
  underneath a publish-subscribe messaging layer, where a topic's
  subscribers form their own overlay and a published message floods or
  gossips outward to them, so a topic behaves like a small, ephemeral P2P
  network layered on top of the main overlay. libp2p's gossipsub protocol is
  exactly this composition.
- **Event-Driven Architecture.** Compatible at the message-passing level;
  both patterns favor asynchronous, decoupled communication over
  synchronous request-response, but event-driven architecture typically
  still assumes a central broker or event bus, which is the one structural
  assumption pure P2P removes.
- **Circuit Breaker.** Applies unchanged inside a P2P system's per-neighbor
  connection handling, where a peer that has been unresponsive or has sent
  malformed messages repeatedly should be temporarily excluded from a
  peer's routing table, the same tripped-open behavior a circuit breaker
  gives a client talking to a flaky remote service.
- **Saga.** Composes uneasily. A saga coordinates a multi-step transaction
  and typically needs either a central orchestrator or a well-defined,
  ordered choreography of events, both of which are straightforward with a
  broker or a server but genuinely awkward to reason about across a
  leaderless, eventually-consistent P2P overlay where the very notion of
  "the next step has definitely happened everywhere" is not guaranteed.
- **Incompatible with Layered Architecture, in its strict form.** A strict
  layered architecture assumes a clear directional dependency, presentation
  calls business logic calls data access, with each layer only aware of the
  layer immediately beneath it, which implicitly assumes a single deployment
  boundary with an internal hierarchy. A P2P system has no such hierarchy
  between peers. Every peer is structurally the same layer as every other
  peer at the network level, even though any individual peer's own internal
  code can, and usually does, use a layered architecture for its own local
  application logic. The incompatibility is at the inter-node relationship,
  not inside a single node.

## 14. Refactoring path in and out

Introducing peer-to-peer into a system that currently has a central server.

1. Identify the single resource the server is the bottleneck for, most often
   outbound bandwidth for a popular, large, mostly-static artifact, and
   confirm it genuinely meets the applicability criteria in dimension 4
   rather than assuming P2P is the answer because the server is under load.
2. Introduce a discovery mechanism first, and accept that this piece will
   likely remain centralized. A tracker, a DNS seed list, or a small,
   well-known bootstrap peer set. This is the smallest, least risky first
   step and it can ship and be validated before any peer-to-peer transfer
   logic exists.
3. Add direct peer-to-peer transfer for the specific resource identified in
   step 1, while the server continues to serve everything else, including
   the discovery mechanism from step 2 and any small or latency-sensitive
   request. This produces the hybrid shape deliberately, rather than by
   accident.
4. Add the redundancy and verification the server used to provide for free.
   If a peer could always trust the server's copy of a file, peers must now
   verify each fragment they receive against a hash, and the system needs a
   policy for what happens when a fragment cannot be found because every
   peer that had it has left.
5. Only after the hybrid shape is running in production and the discovery
   server has become the visible bottleneck or the visible single point of
   failure, consider replacing it with a structured overlay, a DHT, and
   budget real time for it. Implementing Kademlia or Chord correctly,
   including churn handling and adversarial-peer resistance, is a
   multi-month effort for a team new to the domain, not a drop-in library
   swap in most languages.

Removing peer-to-peer from a system that has it and should not.

1. Confirm the actual reason for removal. The two honest reasons are
   operational, the team cannot debug or moderate the system, or economic,
   the P2P complexity is not earning back its engineering cost relative to
   simply provisioning a server, now that a server is affordable. Removing
   P2P purely because it is unfamiliar is not, by itself, sufficient
   justification, since it discards the resilience and cost-distribution
   benefits along with the complexity.
2. Stand up a conventional server that can answer every request the P2P
   overlay currently answers, and route a small percentage of production
   traffic to it first, comparing behavior against the P2P path before
   cutting over fully.
3. Migrate discovery first, since it is usually already partially
   centralized, then migrate data transfer, keeping both paths live and
   monitored during the transition so a regression in the new server-based
   path is caught before the P2P path is decommissioned.
4. Decommission the P2P protocol's listening ports and remove peer-discovery
   code last, once telemetry shows traffic on the P2P path has dropped to
   zero for a full deployment cycle, not merely to a low number, since a
   long-lived peer can sit dormant and reappear.

## 15. Testing and verification

Unit-testable in isolation. Routing-table update logic (does inserting a new
peer correctly place it in the right bucket or the right ring position),
duplicate-message suppression, and the pure functions that compute distance
or ownership, such as the consistent-hashing and XOR-distance functions shown
in the code examples below. These are ordinary deterministic functions once
extracted from the networking code around them, and they are the highest
value place to put unit tests, because a bug here corrupts the overlay's
correctness silently rather than crashing loudly.

Genuinely hard to test, and requiring dedicated infrastructure. Churn
behavior (does the system route correctly while peers are joining and
leaving concurrently), adversarial behavior (does a peer that lies about its
neighbors or refuses to forward messages get correctly excluded), and NAT
traversal (does the hole-punching or relay fallback actually work against
the diversity of real-world network address translators, which cannot be
fully reproduced in a lab). The standard technique for the first two is a
simulated network test rig, exactly the in-memory style used in this entry's
code examples, scaled up to hundreds or thousands of simulated peers with a
scripted churn schedule and a fraction of deliberately misbehaving peers
injected, so the test can assert on global properties, does every honest
peer's view converge, does every stored key remain retrievable, without
needing real sockets or real network latency. NAT traversal specifically is
usually validated with a small, dedicated integration-test lab of machines
placed behind real, varied consumer and enterprise NAT configurations, since
software-only NAT simulation reliably misses real-world edge cases.

Property-based testing is unusually well suited to the structured variant.
Generate a random sequence of peer joins, peer departures, and key
insertions, then assert the invariant that every key currently in the system
is retrievable from at least one live peer, and that the retrieved value
matches what was stored. This catches routing-table bugs that a handful of
hand-written example tests would not think to construct.

## 16. Observability signals

- **Routing table health per peer.** The fraction of a peer's routing-table
  entries that respond to a liveness check within a timeout. A healthy
  structured overlay keeps this consistently above roughly 80 to 90 percent;
  a sustained drop below that indicates either a churn spike the
  stabilization interval cannot keep up with, or a network-level problem
  isolating that peer from a portion of the overlay.
- **Lookup hop count distribution.** The number of hops a lookup takes
  before resolving, tracked as a histogram across all lookups in the
  network, not just one peer's. A healthy structured overlay's hop count
  stays close to its theoretical log2(N) bound; a distribution with a
  heavy tail of much longer lookups is the earliest external signal of
  routing-table staleness or of the hub-collapse failure mode described in
  dimension 11.
- **Duplicate-message rate.** In an unstructured, flood-based overlay, the
  ratio of duplicate arrivals to unique messages delivered at each peer.
  This is the direct, measurable cost of flooding, and a sudden increase
  usually means the overlay's connectivity has grown denser than intended,
  for instance because a churn-recovery procedure is adding neighbor
  connections faster than it is pruning stale ones.
- **Peer churn rate.** Joins plus departures per unit time, as a fraction of
  total network size. This is the input parameter every capacity-planning
  and stabilization-interval decision depends on, and it should be
  monitored as its own first-class metric rather than inferred after the
  fact from routing-table health degrading.
- **Data availability (structured overlays with a replicated store).** The
  fraction of previously-stored keys that a probe can still successfully
  retrieve. This is the metric that actually matters to the system's users,
  and it should be tracked directly with periodic synthetic retrieval
  probes rather than assumed to follow from routing-table health, because
  a routing table can look healthy while the peers that actually held the
  replicas of a specific key have all, coincidentally, left.
- **Free-rider or leech ratio (incentive-bearing systems).** The proportion
  of traffic served by a peer relative to the traffic it consumes,
  aggregated across the swarm. A rising ratio of pure consumers to
  contributors is the leading indicator that an incentive mechanism, such
  as tit-for-tat, is failing to hold, well before the network's total
  capacity visibly degrades.

## 17. Security and privacy implications

A peer-to-peer overlay exposes every participant's network address, and
often their approximate physical location by inference from IP geolocation,
to every other peer it interacts with, because there is no server in the
middle to anonymize the source of a request. This is a genuine privacy
regression relative to a client-server design where only the server, not
every other client, learns a client's address, and any system built for a
population with real anonymity needs, journalists communicating with
sources, or activists under surveillance, must layer an explicit anonymity
technique such as onion routing on top of the base P2P design rather than
assume the overlay provides it.

The overlay's routing and discovery mechanism is itself an attack surface.
A Sybil attack, where one adversary creates many fake peer identities to
gain disproportionate influence over routing decisions, is a first-class
threat to any structured overlay whose security assumes each identifier
represents one independent, honest party; both Chord and Kademlia's original
papers explicitly acknowledge this as an open problem the base protocol does
not solve, and production systems address it with either a proof-of-work
cost on generating a new identifier, as Bitcoin does implicitly through the
same mechanism that secures block production, or with an out-of-band
reputation or invitation system that limits how cheaply an adversary can
mint new identities.

Eclipse attacks, where an adversary controls enough of a target peer's
routing-table entries or overlay neighbors to isolate it from the honest
network and feed it a fabricated view of the system's state, are a related
and equally serious threat, and their mitigation, requiring routing-table
entries to be diverse across network prefixes and periodically refreshed
from multiple independent discovery sources, adds real implementation
complexity that a naive implementation of Chord or Kademlia will not include
by default.

Because content in structured overlays like a DHT is typically addressed by
a hash of its content rather than by who published it, the overlay itself
provides no built-in mechanism to remove or block a specific piece of data
once it has propagated, which is precisely the property that makes these
systems resistant to a single-party takedown and, for the same underlying
reason, difficult to use for any system that needs a mechanism for lawful,
compliant content removal. Any deployment with a legal removal obligation
needs a plan for this before launch, since it cannot be added afterward
without redesigning the addressing scheme.

Finally, any protocol that lets a peer relay traffic on behalf of another
peer, TURN relaying in WebRTC, or block and transaction relay in Bitcoin,
opens a bandwidth-amplification and traffic-analysis surface. A malicious
relay can observe, delay, or in some designs even tamper with traffic it
forwards, so relayed paths need either end-to-end encryption the relay
cannot inspect, or an explicit acceptance that the relay is a trusted party
for that specific connection, which is exactly the trust assumption pure
peer-to-peer is usually trying to avoid, and which is why WebRTC treats
relaying as a fallback of last resort rather than the default path.

## 18. References

- Rudiger Schollmeier, "A Definition of Peer to Peer Networking for the
  Classification of Peer to Peer Architectures and Applications", Proceedings
  of the First International Conference on Peer to Peer Computing, IEEE,
  2001. [IEEE Xplore abstract](https://ieeexplore.ieee.org/document/990434),
  verified 2026-08-02.
- Ion Stoica, Robert Morris, David Karger, M. Frans Kaashoek, and Hari
  Balakrishnan, "Chord, A Scalable Peer-to-peer Lookup Service for Internet
  Applications", ACM SIGCOMM Computer Communication Review, 2001.
  [Wikipedia summary, including the 2011 ACM SIGCOMM Test of Time
  award](https://en.wikipedia.org/wiki/Chord_(peer-to-peer)),
  verified 2026-08-02.
- Petar Maymounkov and David Mazieres, "Kademlia, A Peer-to-peer Information
  System Based on the XOR Metric", 2002.
  [Wikipedia summary](https://en.wikipedia.org/wiki/Kademlia),
  verified 2026-08-02.
- Satoshi Nakamoto, "Bitcoin, A Peer-to-Peer Electronic Cash System", 2008.
  [Original whitepaper PDF](https://bitcoin.org/bitcoin.pdf),
  verified 2026-08-02.
- Wikipedia, "BitTorrent", article covering Bram Cohen's original design,
  seeders and leechers, trackers, tit-for-tat, and optimistic unchoking.
  [https://en.wikipedia.org/wiki/BitTorrent](https://en.wikipedia.org/wiki/BitTorrent),
  verified 2026-08-02.
- Wikipedia, "Napster", article covering the centralized index, the hybrid
  architecture, and the 2001 court-ordered shutdown.
  [https://en.wikipedia.org/wiki/Napster](https://en.wikipedia.org/wiki/Napster),
  verified 2026-08-02.
- Wikipedia, "Skype protocol", article covering the original supernode
  architecture and the 2012 transition to Microsoft-operated data centers.
  [https://en.wikipedia.org/wiki/Skype_protocol](https://en.wikipedia.org/wiki/Skype_protocol),
  verified 2026-08-02.
- Wikipedia, "Dynamo (storage system)", article covering consistent-hash
  partitioning and gossip-based membership.
  [https://en.wikipedia.org/wiki/Dynamo_(storage_system)](https://en.wikipedia.org/wiki/Dynamo_(storage_system)),
  verified 2026-08-02.
- IPFS documentation, "How IPFS works", covering content addressing, the
  Kademlia DHT, and libp2p.
  [https://docs.ipfs.tech/concepts/how-ipfs-works/](https://docs.ipfs.tech/concepts/how-ipfs-works/),
  verified 2026-08-02.
- libp2p project site, covering the modular transport and protocol stack.
  [https://libp2p.io/](https://libp2p.io/), verified 2026-08-02.

## Code examples

The three examples below model the pattern's structural core, that every
node plays both client and server roles with no privileged party, rather
than opening real network sockets, so each one runs deterministically and
instantly in any environment, including CI, with no network access
required. All three were executed locally before this entry shipped.

### TypeScript: anti-entropy gossip convergence

Models the unstructured, gossip-based membership dissemination described in
dimensions 7 and 8. Eight peers, each seeded with knowledge of only one
neighbor, converge on a complete view of the network purely by repeatedly
picking a peer they already know and exchanging membership sets, with no
peer ever holding a privileged, complete view up front.

```typescript
type NodeId = string;

class Peer {
  readonly id: NodeId;
  readonly known: Set<NodeId>;
  constructor(id: NodeId, seeds: NodeId[]) {
    this.id = id;
    this.known = new Set([id, ...seeds]);
  }
  gossipRound(peers: Map<NodeId, Peer>): void {
    const target = pickRandom([...this.known].filter((p) => p !== this.id), this.id);
    if (!target) return;
    const partner = peers.get(target);
    if (!partner) return;
    for (const id of partner.known) this.known.add(id);
    for (const id of this.known) partner.known.add(id);
  }
}

function pickRandom<T>(items: T[], seedKey: string): T | undefined {
  if (items.length === 0) return undefined;
  let h = 0;
  for (const c of seedKey) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return items[h % items.length];
}

function buildNetwork(n: number): Map<NodeId, Peer> {
  const peers = new Map<NodeId, Peer>();
  for (let i = 0; i < n; i++) {
    const id = `n${i}`;
    const seed = i === 0 ? [] : [`n${i - 1}`];
    peers.set(id, new Peer(id, seed));
  }
  return peers;
}

function runGossip(peers: Map<NodeId, Peer>, rounds: number): void {
  for (let r = 0; r < rounds; r++) {
    for (const peer of peers.values()) peer.gossipRound(peers);
  }
}

const peers = buildNetwork(8);
runGossip(peers, 6);
const sizes = [...peers.values()].map((p) => p.known.size);
console.log(`converged=${sizes.every((s) => s === 8)} sizes=${sizes.join(",")}`);
```

Run with `npx tsc gossip.ts --target es2020 --module commonjs` then `node
gossip.js`. Output confirms all eight peers converge to full membership
knowledge, `converged=true sizes=8,8,8,8,8,8,8,8`, within six gossip rounds,
consistent with the O(log N) convergence bound described in dimension 7.

### Python: consistent-hashing ring ownership

Models the structured-overlay ownership rule described in dimensions 6 and
8, where a key belongs to the first peer whose identifier is greater than or equal
to the key's hashed position on the ring, wrapping around at the end.
Demonstrates the property that makes structured overlays practical at scale,
that adding a peer only reassigns the small slice of the key space adjacent
to it, not the whole ring.

```python
import hashlib
from bisect import bisect_left


def ring_position(key: str, bits: int = 16) -> int:
    digest = hashlib.sha1(key.encode()).hexdigest()
    return int(digest, 16) % (2 ** bits)


class Ring:
    def __init__(self, node_ids: list[str]) -> None:
        self.nodes = sorted((ring_position(n), n) for n in node_ids)
        self.positions = [p for p, _ in self.nodes]

    def owner_of(self, key: str) -> str:
        pos = ring_position(key)
        idx = bisect_left(self.positions, pos)
        if idx == len(self.positions):
            idx = 0
        return self.nodes[idx][1]


if __name__ == "__main__":
    ring = Ring([f"peer-{i}" for i in range(6)])
    keys = ["invoice:1042", "invoice:9981", "user:alice", "user:bob", "session:7"]
    for key in keys:
        print(f"{key} -> {ring.owner_of(key)}")
    stable = ring.owner_of("invoice:1042")
    ring2 = Ring([f"peer-{i}" for i in range(6)] + ["peer-6"])
    print(f"after join, invoice:1042 owner unchanged={ring2.owner_of('invoice:1042') == stable}")
```

Run with `python3 ring.py`. Output shows each key's owning peer, then
confirms that adding a seventh peer to the ring leaves an unrelated key's
ownership unchanged, `after join, invoice:1042 owner unchanged=True`, the
locality property consistent hashing exists to provide and that a naive
modulo-N hash assignment would not.

### Go: flooded broadcast with duplicate suppression

Models the unstructured flood described in dimensions 6, 7, and 11. Every
`Peer` both originates and relays messages, there is no distinguished server
type, and each peer tracks message identifiers it has already seen so a
message is delivered to the application layer exactly once per peer even
though the underlying mesh has cycles that would otherwise cause it to
arrive repeatedly.

```go
package main

import (
	"fmt"
	"sort"
)

type Message struct {
	ID      int
	Payload string
	TTL     int
}

type Peer struct {
	Name      string
	Neighbors []*Peer
	Seen      map[int]bool
	Delivered []string
}

func NewPeer(name string) *Peer {
	return &Peer{Name: name, Seen: map[int]bool{}}
}

func (p *Peer) Connect(other *Peer) {
	p.Neighbors = append(p.Neighbors, other)
	other.Neighbors = append(other.Neighbors, p)
}

func (p *Peer) Receive(msg Message) {
	if p.Seen[msg.ID] {
		return
	}
	p.Seen[msg.ID] = true
	p.Delivered = append(p.Delivered, msg.Payload)
	if msg.TTL <= 0 {
		return
	}
	next := Message{ID: msg.ID, Payload: msg.Payload, TTL: msg.TTL - 1}
	for _, n := range p.Neighbors {
		n.Receive(next)
	}
}

func (p *Peer) Broadcast(id int, payload string, ttl int) {
	p.Receive(Message{ID: id, Payload: payload, TTL: ttl})
}

func main() {
	names := []string{"a", "b", "c", "d", "e"}
	peers := map[string]*Peer{}
	for _, n := range names {
		peers[n] = NewPeer(n)
	}
	peers["a"].Connect(peers["b"])
	peers["b"].Connect(peers["c"])
	peers["c"].Connect(peers["d"])
	peers["d"].Connect(peers["e"])
	peers["e"].Connect(peers["a"])
	peers["b"].Connect(peers["d"])

	peers["c"].Broadcast(1, "block:9001", 4)

	reached := []string{}
	for _, n := range names {
		if len(peers[n].Delivered) > 0 {
			reached = append(reached, n)
		}
	}
	sort.Strings(reached)
	fmt.Printf("reached=%v duplicatesSuppressed=%v\n", reached, len(peers["b"].Delivered) == 1)
}
```

Run with `go run main.go`. Output confirms the flood reaches every peer in
the mesh exactly once each, `reached=[a b c d e]
duplicatesSuppressed=true`, despite peer `b` sitting on two independent
cycles in the graph (through `a`-`e`-`d` and directly through `c`) that
would otherwise deliver the broadcast to it twice.

Java, Rust, and Swift were not written for this entry. The three examples
above already demonstrate the pattern's three distinct structural
mechanisms, unstructured gossip convergence, structured-overlay ownership
by consistent hashing, and flooded broadcast with duplicate suppression,
and a fourth or fifth language would repeat one of those three shapes
rather than show a genuinely new one.
