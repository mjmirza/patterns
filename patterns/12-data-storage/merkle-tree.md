---
name: Merkle Tree
slug: merkle-tree
family: 12-data-storage
category: Data Structure
aliases: [Hash Tree, Binary Hash Tree]
first_described: "Ralph Merkle 1979, US Patent 4,309,569"
maturity: canonical
related: [merkle-patricia-trie, content-addressable-storage, gossip-protocol, bloom-filter, event-sourcing]
incompatible_with: []
verified: 2026-08-02
---

# Merkle Tree

## 1. Name, aliases, and lineage

The canonical name is Merkle Tree, sometimes written Hash Tree, after the
inventor Ralph C. Merkle. The structure was first described in a patent
filing, Ralph C. Merkle, "Method of providing digital signatures", United
States Patent 4,309,569, filed September 5, 1979 (Google Patents record,
https://patents.google.com/patent/US4309569A/en, verified 2026-08-02). The
patent's own language calls the technique "tree authentication" and describes
computing a root value, denoted H(1,n,Y), from a binary tree of one way hash
functions applied to a set of leaf values Y sub i, so that a receiver holding
only the root can authenticate any single leaf against a short "authentication
path" of sibling hashes, without needing every other leaf. That authentication
path is exactly what the field now calls a Merkle proof, and the patent's own
text states plainly that the method "allows the receiver to selectively
authenticate any leaf" against the published root, which is the property that
gives the structure all of its later applications.

The two names, Merkle Tree and Hash Tree, are used interchangeably in the
literature and in production systems, and neither is considered more
authoritative than the other. Some texts reserve Hash Tree for the general
family, any tree of hashes, including one built over a flat list rather than a
binary tree, and Merkle Tree for the specific binary construction from the
patent, but this distinction is not consistently applied, and this entry
treats the two names as synonyms, as most production documentation does.

A structure called a Hash List predates and coexists with the Merkle Tree and
is worth naming here because it is routinely confused with it. A Hash List is
a flat array of leaf hashes with no internal tree, requiring a verifier to
either hold the full list or receive every hash to check one item. The Merkle
Tree's contribution over a Hash List is logarithmic proof size, discussed in
dimension 3.

## 2. Problem and context

A system holds a large, changing collection of data, and two parties, or two
replicas of the same system, need to agree that their copies of the collection
are identical, or a client needs to prove that one specific item belongs to a
collection it does not otherwise hold, without transferring or storing the
whole collection to do either.

The concrete situations that create this need recur across storage, networking,
and distributed systems.

- A peer-to-peer network distributes a large file or a large set of records
  across many untrusted machines, and a downloading node needs to verify each
  chunk as it arrives rather than waiting for the whole transfer, because a
  single corrupted or malicious chunk should be detectable and discardable
  immediately, not after the fact.
- Two replicas of a distributed database, or two nodes in a peer-to-peer
  version control system, hold nominally the same data set and need to find
  the specific records that differ, without comparing every record pairwise,
  because the sets are large and usually agree almost everywhere.
- A client of a service does not trust the service to answer honestly, and
  wants a compact, independently checkable proof that a specific record is
  part of a data set the service has committed to, without downloading the
  entire data set. A certificate transparency log and a cryptocurrency light
  client both sit in this situation.
- A version control system, or any content addressed store, needs a way to
  name a whole directory tree by a single identifier that changes if, and only
  if, any file anywhere under that tree changes, so that two commits can be
  compared for equality in constant time regardless of how large the tree is.

What these four situations share is the same shape of requirement, stated
generally. Verify membership or detect difference in a large collection using
work and data transfer proportional to the log of the collection size, and a
single small value, the root hash, that acts as a tamper evident summary of
the whole collection. A flat hash of the whole collection gives the tamper
evident summary but none of the incremental or proof-of-membership behaviour,
because changing any one byte anywhere forces recomputing and retransmitting
the entire hash input. The Merkle Tree exists to give both properties at once.

## 3. Forces

- **Proof size versus flat hashing.** Favoured strongly. A flat hash over N
  leaves needs to inspect all N leaves to verify any one of them or to prove
  it belongs. A Merkle Tree needs only the log base two of N sibling hashes,
  the authentication path from the patent's own description. For a collection
  of one million leaves that is roughly twenty hashes instead of one million.
  This is the central force the structure exists to win, at the cost below.
- **Storage and computation overhead versus a Hash List.** Sacrificed
  relative to a flat list of leaf hashes. A Merkle Tree stores, or must be able
  to recompute, an internal node for every pair of leaves, roughly N extra
  hashes for N leaves, where a Hash List stores none. Building the tree costs
  O(N) hash computations up front. This overhead buys the logarithmic proof
  size above, so the trade is proof size against build and storage cost, and it
  favours the tree whenever verification happens more often than the full
  collection is rebuilt from scratch, which is nearly always true in practice.
- **Incremental update cost versus a flat hash.** Favoured for read-heavy,
  write-light workloads, sacrificed for write-heavy ones. Changing one leaf in
  a Merkle Tree only invalidates the log N nodes on the path from that leaf to
  the root, so recomputation is O(log N). A flat hash of the whole collection
  must reprocess every byte on any change, O(N). This is why the structure
  suits anti-entropy repair and content addressed storage, both of which touch
  a small fraction of a large collection per operation, and suits it poorly for
  a workload that rewrites the entire collection on every update.
- **Coupling to a leaf ordering.** Sacrificed. The root hash is a function of
  both the leaf contents and their position in the tree, so two collections
  containing the identical set of items in a different order produce different
  roots unless the construction sorts leaves first. Sorting buys
  order-independence at the cost of an O(N log N) sort on every rebuild and the
  loss of any meaning the original order carried, such as append order in a
  transparency log.
- **Trust model.** Favoured heavily. The verifier needs to trust only the
  root, obtained through a channel assumed honest, such as a block header, a
  signed timestamp, or a value published by many independent observers. Every
  other value in the system, every leaf and every internal node, can come from
  an untrusted source, because the proof mechanically detects tampering. This
  is what makes the structure the load bearing primitive of systems that
  explicitly distrust the party serving the data.
- **Determinism and reproducibility.** Favoured. Given the same leaves in the
  same order and the same hash function, every implementation produces the
  same root, which is what allows independent parties to agree on the root
  without coordination, at the cost that the exact tree shape, padding rule,
  and domain separation convention (dimension 8) must be specified precisely
  and identically by every party, or roots silently disagree.

## 4. Applicability and non-applicability

Reach for a Merkle Tree when the following hold.

- The collection is large enough that a full comparison or a full transfer is
  expensive, and membership or equality needs to be checked far more often
  than the whole collection changes.
- At least one party in the protocol is untrusted, partially trusted, or
  physically remote and unreachable for a full data exchange, so the proof
  property, log N data to verify one item against a trusted root, is the point,
  not merely a performance nicety.
- The data is naturally chunkable into leaves of comparable size, such as file
  blocks, transactions, log entries, or key ranges.
- Two replicas are expected to agree almost everywhere and differ in a small,
  unknown subset, so a tree comparison can prune down to the differing leaves
  in O(log N) rounds instead of comparing every record.
- A tamper evident audit trail is required, where any retroactive edit to any
  past entry must be detectable by anyone holding only the current root.

Do NOT reach for a Merkle Tree in these cases, and the reason matters more
than the rule.

- **The collection is small.** Below a few hundred leaves, a flat hash, or
  simply resending the whole collection, is cheaper to build, cheaper to
  reason about, and has no proof-size problem worth solving. The log N saving
  is real only once N is large enough that log N is substantially smaller than
  N.
- **Every party in the protocol is fully trusted and co-located.** If both
  sides can simply exchange the full data set cheaply, a Merkle Tree adds
  build cost and code complexity for a proof property nobody needs. A checksum
  or a plain hash of the concatenated data answers "did anything change"
  equally well when nobody needs to prove which item changed without
  revealing the rest.
- **The workload rewrites the whole collection on every update.** If every
  write touches every leaf, the O(log N) incremental-update advantage never
  applies, and the tree's build overhead is paid on every operation for no
  benefit over a flat hash.
- **Order-independent equality is needed and leaves are not naturally
  sortable or hashable to a canonical key.** Without a stable leaf ordering
  the same logical collection produces different roots on different machines,
  which defeats the entire point of using the root as an agreement point. A
  content addressed multiset structure, or sorting by a canonical key first,
  is required, and if neither is available the pattern does not fit cleanly.
- **The requirement is confidentiality, not integrity.** A Merkle Tree proves
  a leaf is part of a committed collection and that nothing has been altered.
  It reveals the leaf's content and, along the authentication path, hashes of
  sibling data that can leak structural information (dimension 17). It is not
  an encryption mechanism and does not hide data on its own.
- **Random access to an arbitrary leaf by value, not by position, is the
  primary access pattern, and no ordering or content addressing scheme exists
  to locate leaves.** A Merkle Tree indexes by position, or by content hash in
  a Merkle Patricia Trie variant, not by an application level key, so looking
  up "the leaf whose amount field is 500" still needs a separate index.

## 5. Structure

- **Leaf.** The atomic unit of data being summarized, for example a file
  block, a transaction, a log record, or a key-value pair. A leaf is never
  hashed with the same input format as an internal node (dimension 11), and
  the specific leaf-hashing rule is a property of the concrete construction,
  not of the abstract pattern.
- **Leaf Hash.** The output of applying the hash function, usually with a
  domain-separating prefix, to a single leaf's serialized bytes. This is what
  actually lives at the bottom level of the tree, never the raw leaf.
- **Internal Node.** A value computed by hashing the concatenation of its two
  children's hashes, again usually with a distinguishing prefix. An internal
  node carries no data of its own beyond this single hash value.
- **Root.** The single hash at the top of the tree, computed from the two
  children of the topmost level. This is the one value a verifier must obtain
  through a trusted channel, and every other value in the tree is treated as
  data supplied by a potentially dishonest party until the proof mechanically
  confirms it is consistent with the root.
- **Authentication Path, also called a Merkle Proof or Merkle Branch.** The
  ordered list of sibling hashes from a specific leaf up to the root, along
  with, for each sibling, whether it sits to the left or the right of the
  path. A verifier recomputes the path from the leaf and the siblings and
  checks the result equals the trusted root.
- **Odd-node handling rule.** A binary tree over a leaf count that is not a
  power of two needs a defined rule for the unpaired node at each level. The
  two common choices, duplicating the last node and promoting it unpaired,
  have substantially different security properties, discussed in dimension
  11.

Relationships. A leaf is hashed once to produce a leaf hash. Leaf hashes are
paired left to right and each pair is hashed to produce the parent internal
node. This pairing repeats level by level until exactly one hash, the root,
remains. Every leaf has exactly one authentication path to the root, of length
equal to the tree's height, which for a balanced tree over N leaves is ceiling
of log base two of N.

## 6. ASCII structure diagram

```
  root  =  H(1|H01|H23)
   |
   +-- H01 = H(1|L0|L1)
   |     |
   |     +-- L0 = H(0|d0)   from data0
   |     +-- L1 = H(0|d1)   from data1
   |
   +-- H23 = H(1|L2|L3)
         |
         +-- L2 = H(0|d2)   from data2
         +-- L3 = H(0|d3)   from data3

  H(x)  = the underlying hash function, e.g. SHA-256
  0, 1  = domain-separating prefix bytes. 0 marks a leaf hash,
          1 marks an internal node hash (see dimension 11 for why)
  Only the root travels through a trusted channel. Every other
  node, and every data block, arrives from an untrusted source
  and is checked by recomputation, never assumed correct.
```

## 7. Dynamics

Two runtime flows matter, building and verifying, and they are used at very
different frequencies. Building happens once per collection version.
Verifying happens once per membership check and is designed to be cheap
enough to run on every incoming chunk, on a lightweight client, or inside a
smart contract with a tight gas budget.

```
BUILD (once per version of the collection)
  Leaves d0..d(N-1)
       |
       v
  hash each leaf  -->  level 0 = L0, L1, ..., L(N-1)
       |
       v
  pair and hash adjacent leaf hashes  -->  level 1 = H01, H23, ...
       |
       v
  repeat pairing until one hash remains  -->  ROOT
       |
       v
  publish ROOT through a trusted channel
  (a block header, a signed manifest, a transparency log STH)

VERIFY (a leaf, an authentication path, and the trusted root)
  Prover           Verifier
    |                 |
    |-- leaf, path -->|
    |                 |-- current = leafHash(leaf)
    |                 |-- for each (sibling, side) in path
    |                 |       if side == right
    |                 |         current = nodeHash(current, sibling)
    |                 |       else
    |                 |         current = nodeHash(sibling, current)
    |                 |-- accept iff current == trustedRoot
    |                 |
```

Two behavioural notes worth stating plainly. First, the prover in the verify
flow can be, and usually is, fully untrusted, because the verifier never trusts
a single value the prover sends without checking it against the independently
obtained root. Second, tree updates in a mutable Merkle Tree, used for
anti-entropy repair or a state trie, follow the build flow restricted to a
single path, recomputing only the log N nodes from the changed leaf to the
root and leaving every other subtree's cached hash untouched, which is the
source of the O(log N) update cost claimed in dimension 3.

## 8. Implementation variants

**Balanced binary tree, duplicate-last-node padding.** The classic
construction, and the one used by early Bitcoin. When a level has an odd
number of nodes, the last node is duplicated to form a pair with itself. This
is the simplest rule to implement and the one most tutorials show, and it
carries a known second-preimage weakness described in dimension 11 unless
combined with domain separation.

**Balanced binary tree, promote-unpaired-node.** The unpaired node at an odd
level is carried up to the next level unhashed, rather than duplicated, and
only paired once a sibling exists at a higher level. This avoids the
duplicate-node ambiguity at the cost of a slightly more irregular tree shape
and marginally more bookkeeping in the proof format.

**Domain-separated hashing.** A single leading byte, or a distinct hashing
function entirely, is applied differently to leaf hashes than to internal node
hashes, exactly as shown in the RFC 6962 Merkle Tree Hash definition, 0x00 for
a leaf, 0x01 for a node, RFC 6962 section 2.1,
https://datatracker.ietf.org/doc/html/rfc6962, verified 2026-08-02. Without
this separation an attacker can present an internal node's two children as if
they were themselves the leaves of a smaller two-leaf tree with the same root,
because a leaf hash and a node hash are otherwise computed by the identical
process on differently shaped input. This is the standard, current best
practice and should be treated as close to mandatory for any new
implementation, discussed further in dimension 11.

**Sparse Merkle Tree.** The tree is fixed at a very large, fixed depth,
usually 256 for a 256 bit key space, with every possible key position present
conceptually, and empty leaves given a well known default value so that the
vast majority of subtrees collapse to a small set of precomputed "empty
subtree" hashes that need not be stored. This variant supports efficient
non-membership proofs, proving a key is absent, which a dense binary Merkle
Tree cannot do without listing every leaf. It costs a fixed, larger number of
hash operations per proof, bounded by the fixed depth rather than log of the
live leaf count.

**Merkle Patricia Trie.** Combines the hash-tree authentication property with
a Patricia trie's radix-tree key compression, so that keys sharing a common
prefix share tree structure and the tree depth tracks key length rather than
leaf count. This is the state representation used by Ethereum, and it is
different enough in structure and trade-offs to warrant its own entry, cross
referenced in dimension 13.

**Merkle DAG, non-binary and non-balanced.** Some systems generalise from a
binary tree to a directed acyclic graph where a node may have any number of
children and the graph need not be balanced, most notably content addressed
storage systems where each node corresponds to an actual data block or
directory rather than an artificially paired hash. Git's object model is the
best known instance, where a tree object directly lists an arbitrary number of
blob and subtree entries by hash rather than pairing them into a strict
binary shape (Pro Git, "Git Objects", section on tree objects,
https://git-scm.com/book/en/v2/Git-Internals-Git-Objects, verified
2026-08-02). This variant sacrifices the clean log N proof-size guarantee of a
balanced binary tree in exchange for a structure that mirrors the actual data
shape being addressed, which is usually the more valuable property for a
content addressed file system.

**Incremental or streaming Merkle Tree.** The tree is built leaf by leaf as
data arrives, keeping only the O(log N) "frontier" of nodes needed to
integrate the next leaf, rather than the full O(N) tree. Certificate
Transparency logs use this shape because leaves, certificates, arrive
continuously and the log must be able to produce a new root after every
addition without recomputing from scratch.

**Language-idiomatic note.** The pattern has essentially the same shape in
every language, because the construction reduces to an array-of-hashes data
structure with two pure functions, leaf hash and node hash, rather than an
object-oriented pattern with polymorphic dispatch. The variation between
languages is almost entirely about how the byte concatenation and hashing API
is expressed, not about the algorithm.

## 9. Known production uses

**Certificate Transparency, RFC 6962.** The Merkle Tree Hash (MTH) algorithm
is defined recursively in RFC 6962 section 2.1, with SHA-256 as the hash
function and an explicit domain-separation prefix, 0x00 for a leaf and 0x01
for an internal node, stated precisely as MTH of an empty list equals
SHA-256 of the empty string, MTH of a single entry equals SHA-256 of 0x00
concatenated with the entry, and MTH of a longer list equals SHA-256 of 0x01
concatenated with the MTH of the left half and the MTH of the right half,
where the split point is the largest power of two smaller than the list
length. RFC 6962, "Certificate Transparency", section 2.1, Merkle Tree,
https://datatracker.ietf.org/doc/html/rfc6962, verified 2026-08-02. Every
publicly trusted TLS certificate is logged into one of these trees today, and
browsers and monitors verify inclusion proofs against the published Signed
Tree Head.

**Bitcoin, block header merkle root.** Every Bitcoin block header contains a
single 32 byte Merkle root summarizing every transaction in the block. The
Bitcoin protocol documentation states plainly that Bitcoin's Merkle trees use
a double SHA-256, the SHA-256 hash of the SHA-256 hash, and that the resulting
tree structure lets a node verify that a specific transaction is included in a
block without downloading every other transaction, the property used by
Simplified Payment Verification light clients. Bitcoin Wiki, "Protocol
Documentation", Merkle Trees section,
https://en.bitcoin.it/wiki/Protocol_documentation, verified 2026-08-02.

**Apache Cassandra, anti-entropy repair.** Cassandra's repair process compares
data held by different replicas using Merkle trees, described in the operator
documentation as comparing the data with "merkle trees, which are a hierarchy
of hashes", so that two replicas can locate the specific rows that differ by
exchanging only a small number of tree hashes rather than every row. Apache
Cassandra documentation, "Repair",
https://cassandra.apache.org/doc/stable/cassandra/managing/operating/repair.html
verified 2026-08-02.

**Git, tree objects.** Git's content-addressed object store represents every
directory as a tree object, and each tree object lists the SHA-1, or in newer
repositories SHA-256, hash of every blob (file content) or subtree
(subdirectory) it contains, together with the entry's mode, type, and
filename. This forms a hash tree in the general sense, a Merkle DAG per
dimension 8, rather than a strictly balanced binary tree, and it is what lets
`git diff`, `git status`, and commit comparison work by hash comparison rather
than byte-for-byte content comparison of every file. Pro Git, Scott Chacon and
Ben Straub, "Git Internals, Git Objects", section on tree objects,
https://git-scm.com/book/en/v2/Git-Internals-Git-Objects, verified
2026-08-02.

**IPFS and IPLD, the Merkle DAG.** InterPlanetary Linked Data, the data model
underneath IPFS, links blocks of data to one another using content identifiers
(CIDs) that embed the cryptographic hash of the target block, so that a graph
of linked blocks of unlimited size can be built and referenced with tamper
evident integrity throughout, exactly the Merkle DAG shape from dimension 8.
IPLD documentation, "IPLD Primer",
https://ipld.io/docs/intro/primer/, verified 2026-08-02.

## 10. Consequences

Positive.

- Membership or non-tampering of a single leaf can be proven with O(log N)
  data, independent of how the remaining N minus one leaves look, which makes
  the pattern practical at web scale where transmitting the whole collection
  is not an option.
- Two large, mostly-agreeing replicas can be compared and their differences
  located with O(log N) rounds of communication rather than O(N), which is the
  entire value proposition of anti-entropy repair in distributed databases.
- The root hash is a single, small, fixed-size value that acts as a
  cryptographically strong commitment to the entire collection, letting a
  small trusted value stand in for a large, potentially untrusted data set in
  any downstream protocol, a block header, a signed manifest, or a commit
  identifier.
- Updates to a single leaf only require recomputing the log N nodes on that
  leaf's path, so a mutable Merkle Tree supports far cheaper incremental
  maintenance than a flat hash of the whole collection.
- The construction composes cleanly with signatures. Signing the small root
  once effectively signs every leaf, because any leaf's authenticity reduces
  to checking its path against the signed root, which is the exact mechanism
  the original 1979 patent used to build a one-time signature scheme that
  could authenticate many messages from a single published value.

Negative.

- Building the full tree still costs O(N) hash operations, so a Merkle Tree
  offers no advantage over a flat hash for a one-shot, full-collection
  integrity check, only for repeated, partial checks against a stable root.
- The tree stores, or must be able to reconstruct on demand, roughly N extra
  internal-node hashes beyond the N leaf hashes, doubling the hash-storage or
  hash-computation footprint compared to a bare list of leaf hashes.
- Correctness depends entirely on an unambiguous, precisely specified
  construction, the odd-node rule, the domain-separation prefix, and the leaf
  serialization format, and two implementations that disagree on any of these
  produce different roots for identical data with no error raised anywhere,
  which is a silent interoperability failure rather than a loud one.
- The structure authenticates a leaf's presence and content but says nothing
  about the leaf's meaning or validity, so a Merkle Tree over invalid data
  faithfully and correctly proves inclusion of invalid data. The tree is an
  integrity mechanism, not a correctness or business-rule mechanism.
- A naive implementation is vulnerable to the second-preimage and duplicate-
  transaction classes of attack described in dimension 11, and these
  vulnerabilities have shipped in real, widely used software.

## 11. Failure modes and misuse

**Second-preimage attack via missing domain separation.** Symptom. Two
different data sets, one containing four leaves and one containing two
leaves whose values happen to equal an internal node's two children from the
first tree, produce the identical root. Cause. Leaf hashes and internal-node
hashes are computed by the same function with no distinguishing prefix, so an
attacker can present an internal node's two children as a valid two-leaf tree
with the same root as the real four-leaf tree, forging a proof of inclusion
for data that was never actually a leaf. This is a well known, general Merkle
Tree weakness against second-preimage forgery when leaf and node hashing are
not separated, and it is exactly the reason RFC 6962 mandates a distinguishing
0x00 or 0x01 prefix (RFC 6962 section 2.1, cited in dimension 9). Fix.
Prefix leaf hashes and node hashes with distinct, fixed bytes or use distinct
hash functions for the two roles, as shown in the code examples below.

**Duplicate-transaction, odd-leaf-count ambiguity (CVE-2012-2459 class).**
Symptom. A tree built by duplicating the last node to pair an odd level
allows two structurally different transaction lists, one with an extra
duplicated entry inserted, to hash to the same root, which historically let a
malicious Bitcoin node craft a block that different implementations disagreed
about. Cause. Duplicating a node to fill an odd pair makes the tree unable to
distinguish "this leaf legitimately appears twice" from "this level had an
odd count and the last leaf was mechanically duplicated to pad it," and the
two cases are computationally indistinguishable from the root alone. Fix.
Reject transaction or leaf lists containing an exact power-of-two-forced
duplicate pattern at that boundary, or, better, use the promote-unpaired-node
variant from dimension 8, which never duplicates data to pad a level.

**Root obtained from an untrusted source.** Symptom. Verification always
succeeds no matter what data is supplied, even data that was clearly
tampered with. Cause. The verifier fetched the "trusted" root from the same
untrusted party whose data it is checking, so the party can simply recompute
and resupply a matching root for whatever data it sends, defeating the entire
point of the proof. Fix. The root must arrive through a channel independent of
the party being checked, a signed block header, a value published by
multiple independent observers, or a value the verifier computed itself at an
earlier, trusted point in time.

**Proof format does not encode left-right sidedness.** Symptom. A
verification function accepts a proof where the sibling hashes are supplied
in the wrong order, silently producing a different, wrong recomputed root
that is then compared against a wrong expected value, or worse, an attacker
constructs an alternate valid-looking proof by permuting siblings. Cause. The
proof only lists sibling hash values, not which side, left or right, each
sibling sits on relative to the path, so the hash-concatenation order at each
step is ambiguous or attacker-controlled. Fix. Always encode, for every step
in the authentication path, which side the sibling occupies, and hash strictly
in that fixed order, as the code examples do explicitly.

**Unbounded proof depth on an unbalanced or adversarially grown tree.**
Symptom. Verification of a single leaf takes noticeably longer for some
leaves than others, or a denial of service becomes possible by growing one
branch of the tree far deeper than the rest. Cause. A tree construction that
is not kept balanced, or a Sparse Merkle Tree implementation that does not
bound its fixed depth, allows one path to the root to be far longer than log
N. Fix. Keep the tree provably balanced on every insertion, or, for a sparse
tree, fix the depth at construction time and never let it vary per key.

**Leaf serialization ambiguity across implementations.** Symptom. Two
services holding what their operators believe is the same data compute
different roots, and the mismatch is diagnosed as data corruption when the
actual data is byte-identical. Cause. The two implementations serialize a
leaf differently before hashing it, for example one includes a length prefix
and the other does not, or field ordering in a structured leaf differs. Fix.
Specify the exact leaf serialization as part of the tree's contract, with a
canonical encoding, and add a cross-implementation test vector as described
in dimension 15.

**Treating tree comparison as authoritative for conflict resolution.**
Symptom. An anti-entropy repair process silently overwrites data based purely
on which side's hash "wins" at a differing subtree, discarding a legitimate
concurrent update. Cause. The Merkle Tree only says two subtrees differ, it
says nothing about which side is correct, more recent, or should win, that
decision belongs to a separate conflict resolution policy, such as
last-write-wins timestamps or a CRDT merge rule. Fix. Use the tree strictly to
locate the minimal set of differing leaves, and apply an explicit, separately
reasoned reconciliation policy to those leaves.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Merkle Tree | Flat hash of whole collection | Hash List (flat array of leaf hashes) | Bloom Filter | Merkle Patricia Trie | Vector clock / version vector |
|---|---|---|---|---|---|---|
| Proof size for one leaf's inclusion | O(log N) | Not possible without full data | O(N), must send every hash | Not a membership proof, probabilistic set test only | O(key length), independent of N | Not applicable, tracks causality not content |
| Detects any single-leaf change | Yes, and localises it to O(log N) nodes | Yes, but localises nothing | Yes, but localises nothing beyond which single leaf hash changed | No, only tests presence, false positives possible | Yes, and localises via key path | No, tracks event ordering, not content |
| Cost to update one leaf | O(log N) hashes | O(N), full rehash | O(1) for that leaf, but comparison is still O(N) | O(k) hash insertions, k = hash function count | O(key length) hashes | O(1) counter increment |
| Supports non-membership proof | Only the sparse variant | No | No | Approximately, with false positives | Yes, via absence along the trie path | Not applicable |
| Order sensitivity of the summary value | Sensitive to leaf order unless sorted first | Sensitive to byte order of concatenation | Sensitive, same as Merkle Tree | Order-independent | Sensitive to key values, not insertion order | Order-independent by design |
| Fits key-value lookup by application key | Only with an external index | No | Only with an external index | No, membership only | Yes, that is its purpose | No |
| Best suited to | Log N proofs, anti-entropy repair, content addressing | One-shot full integrity check between trusted parties | Simple checksums when the full list is already cheap to send | Fast approximate membership pre-filter before an expensive lookup | Ethereum-style key-addressed authenticated state | Detecting concurrent, conflicting writes across replicas |

Reading of the table. A Merkle Tree wins whenever the requirement is
logarithmic proof of a single item against a large collection with an
untrusted counterparty. A flat hash wins when both parties are trusted and
already have the full data. A Hash List is a fair middle ground only when N
is small enough that O(N) proof data is acceptable. A Bloom Filter answers a
different question, approximate presence, not authenticated inclusion. A
Merkle Patricia Trie wins when the access pattern is by application key
rather than by position. A vector clock answers a different question again,
which write happened before which, not whether content matches.

## 13. Related and incompatible patterns

- **Merkle Patricia Trie.** A close relative, not a substitute in every
  context. It combines the authenticated-hash-tree property of a Merkle Tree
  with a Patricia trie's radix compression over keys, so lookups are by
  application key rather than by leaf position, and shared key prefixes share
  tree structure. Reach for it, rather than a plain Merkle Tree, when the
  access pattern is genuinely key based, such as Ethereum's account and
  storage state.
- **Content-Addressable Storage.** The broader architectural pattern that a
  Merkle DAG (dimension 8) typically implements underneath. Content addressed
  storage names every object by the hash of its content, and a Merkle Tree or
  Merkle DAG is the specific structure used when objects reference other
  objects by hash, forming the addressable graph. Git and IPFS both sit at
  this intersection.
- **Gossip Protocol.** Frequently paired in distributed databases. A gossip
  protocol propagates state changes between nodes; a Merkle Tree is layered on
  top as the anti-entropy mechanism that catches whatever gossip missed, by
  periodically comparing tree roots and walking down to the specific differing
  leaves. Neither replaces the other, they solve the propagation problem and
  the reconciliation problem respectively.
- **Bloom Filter.** Complementary, not competing, in systems that need both a
  fast negative answer and a strong positive proof. Some systems use a Bloom
  Filter as a cheap first check, "this item is definitely not here, skip the
  expensive Merkle proof", before falling back to a Merkle Tree lookup for a
  possible match, trading the filter's false-positive rate for a large
  reduction in expensive tree traversals.
- **Vector Clock, and other causality-tracking structures.** Solve an
  orthogonal problem and are frequently used alongside a Merkle Tree in the
  same distributed system, one tracking whether replicas agree on content, the
  other tracking the causal order of concurrent writes so that a genuine
  conflict, once located by the Merkle comparison, can be resolved correctly.
- **Digital Signature schemes, in particular hash-based signatures such as
  Lamport signatures and the later Merkle Signature Scheme.** The original
  1979 patent used the tree specifically to extend a single one-time
  signature primitive into a scheme capable of signing many messages, by
  publishing the tree root as the public key and revealing an authentication
  path alongside each individual one-time signature. This lineage is why
  hash-based, post-quantum signature schemes such as XMSS still build directly
  on the Merkle Tree structure today.
- **Incompatible, treating the tree as a source of truth for conflict
  resolution.** As dimension 11 states, a Merkle Tree answers "do these two
  collections differ" and "where", never "which side is correct". Any design
  that lets a tree comparison alone decide which replica's data survives is
  misusing the pattern, and the actual conflict resolution logic belongs to a
  separate, explicit mechanism such as last-write-wins or a CRDT merge.

## 14. Refactoring path in and out

Introducing a Merkle Tree into a system that currently compares or transfers
data naively.

1. Identify the actual comparison or verification bottleneck. Confirm the
   collection is genuinely large enough, and comparisons or proofs genuinely
   frequent enough, that O(log N) is worth the added build and storage cost
   over the current O(N) approach, per the applicability guidance in
   dimension 4.
2. Define the leaf boundary and leaf serialization precisely, in writing, as a
   versioned specification, because this is the detail most likely to drift
   silently between implementations (dimension 11).
3. Pick and document the exact construction. Hash function, domain-separation
   prefix bytes, and the odd-node rule. Do not leave any of these implicit.
4. Build the tree alongside the existing comparison mechanism, without
   removing it yet, and cross-validate that the Merkle root correctly detects
   every difference the old mechanism detects, on real production data, for a
   soak period.
5. Add the authentication-path generation and verification code paths, and
   exercise them against the test vectors from dimension 15 before they carry
   any real decision.
6. Cut over the actual comparison, repair, or proof logic to consume the tree,
   leaving the old mechanism available as a fallback behind a feature flag for
   at least one full operational cycle.
7. Remove the old mechanism once the tree-based path has run in production
   with no discrepancy for a full cycle, and record the removal in a
   changelog, since removing a fallback path is itself a risk-bearing change.

Removing a Merkle Tree once it stops earning its place. Signals include the
collection shrinking permanently below the size where log N substantially
beats N, the untrusted-party requirement disappearing (both sides became
fully trusted, co-located services), or the workload shifting to
full-collection rewrites on every update.

1. Confirm no external party, client, or contract still depends on the root or
   on authentication paths as a public interface. If one does, the tree is a
   published contract, not an internal implementation detail, and removing it
   is a breaking change requiring a deprecation cycle of its own.
2. Replace the tree-based comparison with the simpler alternative, a flat
   hash or a direct transfer, behind the same internal interface the tree
   previously implemented, so callers are unaffected.
3. Stop maintaining the tree incrementally on writes once nothing reads it.
4. Delete the tree-building and proof-verification code only after confirming,
   through logs or metrics, that no code path still calls it.

## 15. Testing and verification

Easier because of the pattern.

- The two pure functions at the core, leaf hash and node hash, are trivially
  unit tested in isolation with known input and output vectors, with no need
  to construct a full tree to test the hashing rules themselves.
- Build correctness for arbitrary leaf counts, including edge cases such as
  zero, one, and odd counts, can be property tested. generate a random list of
  byte strings, build the tree, rebuild it a second time from the same input,
  and assert the two roots are identical, which catches any nondeterminism.
- Tamper detection is directly testable. flip one bit anywhere in one leaf,
  rebuild, and assert the root changes; this single property test, run across
  many random leaf sets and many random flip positions, gives strong
  confidence the hash-tree construction is doing its job.
- A Merkle proof is independently verifiable without access to the tree
  builder's internals at all, which makes an extremely useful cross-
  implementation test. generate a proof with implementation A and verify it
  with implementation B, and vice versa, and any disagreement immediately
  reveals a serialization or construction mismatch of exactly the kind
  described in dimension 11.

Harder because of the pattern.

- Testing the odd-node and boundary behaviour thoroughly requires deliberately
  constructing leaf counts at and around every power of two, which is easy to
  under-test if the test suite only exercises "round" leaf counts.
- A subtle domain-separation bug, where leaf and internal-node hashing
  accidentally use the same function, produces a tree that still verifies
  correctly for legitimate proofs and only fails under the second-preimage
  attack from dimension 11, so a purely functional test suite that never
  attempts the attack will not catch it. A dedicated adversarial test is
  required in addition to a happy-path one.

Techniques that apply.

- **Cross-implementation test vectors.** Publish, alongside the code, a fixed
  set of leaves, the expected leaf hashes, the expected internal node hashes
  at every level, and the expected root, exactly as RFC 6962 itself does for
  the Certificate Transparency Merkle Tree Hash. This is the strongest defence
  against the silent serialization mismatch in dimension 11.
- **Adversarial second-preimage test.** Deliberately attempt the forgery
  from dimension 11, construct a two-leaf tree whose leaves equal an internal
  node's two children from a known four-leaf tree, and assert the roots do
  NOT match once domain separation is in place, and, before the fix, confirm
  they DO match, to prove the test can actually detect the bug.
- **Round-trip proof property test.** For every leaf index in a randomly
  generated tree, generate a proof, verify it against the true root, assert
  success, then flip one byte in the leaf and re-verify the same proof,
  asserting failure.
- **Fuzzing the proof format.** Feed a verifier randomly mutated proofs,
  wrong sibling values, swapped left-right sidedness, truncated or extended
  paths, and assert every mutation is rejected, never silently accepted.

## 16. Observability signals

What to record.

- On every tree build, the leaf count, the wall-clock build duration, and the
  resulting root, logged or exported as a metric labelled by the collection
  identifier. Root value itself is usually only logged at debug level or
  exported as a short truncated digest, since the full root changes on every
  build.
- A counter of verification attempts, split into succeeded and failed, labelled
  by the reason for failure where one exists, root mismatch, malformed proof,
  or hash function error. A rising failure rate that is not explained by an
  expected data change is the primary early warning signal for either a bug or
  an active tampering attempt.
- For an anti-entropy repair use, the number of differing leaves located per
  repair round, and the depth in the tree at which the difference was first
  detected, both as histograms. This tells an operator whether replicas are
  drifting a little (a few leaves, deep in the tree) or a lot (a difference
  detected near the root, meaning large swaths differ).
- Tree height and leaf count over time, to catch unexpected imbalance or
  unbounded growth described as a failure mode in dimension 11.
- Time between root publications, for any system where the root itself is
  periodically committed externally, such as a block header or a signed
  manifest, since a stalled root publication is itself an operational
  incident.

A healthy instance on a dashboard. Verification failures sit at or near zero,
with any nonzero baseline explained by a known, bounded source such as
expected proof expiry. Build duration scales in proportion to leaf count and
does not show step changes unrelated to a leaf-count change. In an
anti-entropy system, the differing-leaf count per repair round trends toward
zero shortly after any replica outage resolves, and stays near zero during
steady state.

A failing instance. A sudden, sustained rise in verification failures with no
corresponding data change points at either a bug in the leaf serialization
(dimension 11) or a real, active integrity violation and should be treated
with the same urgency as any other security alert. A repair round that keeps
finding the same set of differing leaves across many consecutive rounds means
repair is not actually converging, often because the reconciliation policy
layered on top of the tree (dimension 13) is oscillating rather than
resolving. Build duration growing faster than leaf count usually points at an
implementation regressed from O(N) to something worse, such as an
accidentally quadratic pairing loop.

## 17. Security and privacy implications

The security properties of a Merkle Tree are precisely as strong as its
underlying hash function's collision and second-preimage resistance, and no
stronger. Using a broken or weakened hash function, MD5 or SHA-1 in a new
design, transfers that weakness directly into forgeable proofs, since an
attacker who can find a collision in the hash function can construct two
different leaf sets, or two different internal subtrees, that hash to the
same value and are therefore indistinguishable to any Merkle proof built on
top.

**Second-preimage and duplicate-node forgery.** Covered in depth in dimension
11 as the leading failure mode, because it is a property of the pattern
itself and not merely an implementation slip. Any new Merkle Tree design
should apply domain separation, distinct hashing of leaves versus internal
nodes, as a default, not as an optional hardening step, per the RFC 6962
precedent cited in dimensions 8 and 9.

**Root provenance is the actual trust boundary.** The entire security model
collapses to a single question, where did the verifier's copy of the root
come from, and was that channel independent of the party supplying the leaves
and proof. A Merkle Tree provides zero security on its own if the root itself
is fetched from the same untrusted party being checked. The tree only moves
the trust requirement from "trust all the data" down to "trust this one small
value", and the system design around how that one value is obtained,
signed, timestamped, and cross-checked by independent observers, carries all
of the actual security weight.

**Information leakage through the authentication path.** A Merkle proof for
one leaf necessarily reveals the hash values of every sibling subtree along
the path to the root, which is not the leaf data itself but is structural
information, the existence and identity, by hash, of other entries in the
collection. In a system where the leaf set itself is sensitive, for example a
list of account balances or a list of certificate holders, a naive Merkle
proof leaks that other entries exist and their hash identities, even though
it does not reveal their content directly. Where this matters, zero-knowledge
proof constructions built on top of Merkle Trees, or blinding of sibling
hashes, are the mitigation, and a system with this requirement should not
assume a plain Merkle proof is privacy preserving.

**Denial of service through adversarial leaf submission.** In any system
where an untrusted party can influence what gets added as a leaf, such as a
public transparency log or a peer-to-peer content network, an attacker can
attempt to submit a very large number of leaves to force expensive rebuilds,
or to submit leaves crafted to trigger worst-case behaviour in a specific
implementation's odd-node handling. Rate limiting leaf submission and
bounding tree depth, as recommended in dimension 11, are the standard
mitigations.

On broader privacy, the pattern is otherwise neutral. It authenticates data
that is either already public or is shared with the verifier through some
other channel, and it does not itself encrypt or restrict access to leaf
content. Any confidentiality requirement over the leaf data needs a separate
mechanism layered alongside the tree, not derived from it.

## Code examples

Three languages, chosen because they cover the three shapes production
Merkle Tree code actually takes. Python shows the reference implementation
with the standard library's `hashlib`, no external dependency, matching how
most prototype and scripting implementations are built. Go shows the same
construction using the standard library's `crypto/sha256`, matching how
infrastructure and blockchain-adjacent tooling in Go is typically written.
Rust shows the construction with a from-scratch SHA-256 core so the example
compiles with plain `rustc` and no external crate, matching how a
performance-sensitive, memory-safe implementation is structured even though a
real project would depend on the audited `sha2` crate instead. All three
implement the identical
construction, domain-separated SHA-256, leaf prefix `0x00`, node prefix
`0x01`, matching the RFC 6962 convention cited in dimensions 8 and 9, over
the same five leaves, `tx-0` through `tx-4`, and all three were run and
produced the identical sixteen-hex-character root prefix `59c906ba9ad23b27`,
confirming the three implementations agree byte for byte on both the root
and a generated authentication path.

### Python

```python
import hashlib

LEAF_TAG = bytes([0])
NODE_TAG = bytes([1])


def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def leaf_hash(data: bytes) -> bytes:
    return _h(LEAF_TAG + data)


def node_hash(left: bytes, right: bytes) -> bytes:
    return _h(NODE_TAG + left + right)


class MerkleTree:
    def __init__(self, leaves: list[bytes]):
        if not leaves:
            raise ValueError("a merkle tree needs at least one leaf")
        self.levels: list[list[bytes]] = [[leaf_hash(d) for d in leaves]]
        while len(self.levels[-1]) > 1:
            level = self.levels[-1]
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else level[i]
                next_level.append(node_hash(left, right))
            self.levels.append(next_level)

    @property
    def root(self) -> bytes:
        return self.levels[-1][0]

    def proof(self, index: int) -> list[tuple[bytes, str]]:
        path = []
        for level in self.levels[:-1]:
            sibling_index = index ^ 1
            if sibling_index < len(level):
                sibling = level[sibling_index]
            else:
                sibling = level[index]
            side = "R" if sibling_index > index else "L"
            path.append((sibling, side))
            index //= 2
        return path


def verify(leaf: bytes, proof: list[tuple[bytes, str]], root: bytes) -> bool:
    current = leaf_hash(leaf)
    for sibling, side in proof:
        if side == "R":
            current = node_hash(current, sibling)
        else:
            current = node_hash(sibling, current)
    return current == root


if __name__ == "__main__":
    leaves = [f"tx-{i}".encode() for i in range(5)]
    tree = MerkleTree(leaves)
    proof = tree.proof(3)
    ok = verify(leaves[3], proof, tree.root)
    print("root", tree.root.hex()[:16])
    print("proof length", len(proof))
    print("verified", ok)

    tampered = verify(b"tx-tampered", proof, tree.root)
    print("tampered verified", tampered)
```

Run output on this machine.

```
root 59c906ba9ad23b27
proof length 3
verified True
tampered verified False
```

### Go

```go
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
)

type Tree struct {
	levels [][][]byte
}

func leafHash(data []byte) []byte {
	h := sha256.New()
	h.Write([]byte{0x00})
	h.Write(data)
	return h.Sum(nil)
}

func nodeHash(left, right []byte) []byte {
	h := sha256.New()
	h.Write([]byte{0x01})
	h.Write(left)
	h.Write(right)
	return h.Sum(nil)
}

func Build(leaves [][]byte) *Tree {
	level := make([][]byte, len(leaves))
	for i, l := range leaves {
		level[i] = leafHash(l)
	}
	t := &Tree{levels: [][][]byte{level}}
	for len(level) > 1 {
		next := make([][]byte, 0, (len(level)+1)/2)
		for i := 0; i < len(level); i += 2 {
			left := level[i]
			right := level[i]
			if i+1 < len(level) {
				right = level[i+1]
			}
			next = append(next, nodeHash(left, right))
		}
		t.levels = append(t.levels, next)
		level = next
	}
	return t
}

func (t *Tree) Root() []byte {
	last := t.levels[len(t.levels)-1]
	return last[0]
}

type step struct {
	sibling []byte
	right   bool
}

func (t *Tree) Proof(index int) []step {
	var path []step
	for _, level := range t.levels[:len(t.levels)-1] {
		siblingIndex := index ^ 1
		var sibling []byte
		if siblingIndex < len(level) {
			sibling = level[siblingIndex]
		} else {
			sibling = level[index]
		}
		path = append(path, step{sibling: sibling, right: siblingIndex > index})
		index /= 2
	}
	return path
}

func Verify(leaf []byte, path []step, root []byte) bool {
	current := leafHash(leaf)
	for _, s := range path {
		if s.right {
			current = nodeHash(current, s.sibling)
		} else {
			current = nodeHash(s.sibling, current)
		}
	}
	return string(current) == string(root)
}

func main() {
	leaves := [][]byte{}
	for i := 0; i < 5; i++ {
		leaves = append(leaves, []byte(fmt.Sprintf("tx-%d", i)))
	}
	tree := Build(leaves)
	proof := tree.Proof(3)
	ok := Verify(leaves[3], proof, tree.Root())
	rootHex := hex.EncodeToString(tree.Root())
	fmt.Println("root", rootHex[:16])
	fmt.Println("proof length", len(proof))
	fmt.Println("verified", ok)
}
```

Run output on this machine, via `go run merkle.go`.

```
root 59c906ba9ad23b27
proof length 3
verified true
```

### Rust

This sample deliberately avoids the `sha2` crate so it compiles with plain
`rustc --edition 2021`, no Cargo, no external dependency. The SHA-256 core is
a compact, from-scratch implementation of FIPS 180-4, so the whole example
stays self-contained. A production system would reach for the audited `sha2`
crate instead. this file only proves the Merkle construction with no crate
resolution step required to compile it.

```rust
struct Sha256 {
    state: [u32; 8],
    buffer: Vec<u8>,
    total_len: u64,
}

const K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
    0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

impl Sha256 {
    fn new() -> Self {
        Sha256 {
            state: [
                0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f,
                0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
            ],
            buffer: Vec::new(),
            total_len: 0,
        }
    }

    fn update(&mut self, data: &[u8]) {
        self.total_len += data.len() as u64;
        self.buffer.extend_from_slice(data);
        while self.buffer.len() >= 64 {
            let block: [u8; 64] = self.buffer[..64].try_into().unwrap();
            self.process_block(&block);
            self.buffer.drain(..64);
        }
    }

    fn process_block(&mut self, block: &[u8; 64]) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes(block[i * 4..i * 4 + 4].try_into().unwrap());
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16].wrapping_add(s0).wrapping_add(w[i - 7]).wrapping_add(s1);
        }

        let (mut a, mut b, mut c, mut d) = (self.state[0], self.state[1], self.state[2], self.state[3]);
        let (mut e, mut f, mut g, mut h) = (self.state[4], self.state[5], self.state[6], self.state[7]);

        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = h.wrapping_add(s1).wrapping_add(ch).wrapping_add(K[i]).wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);
            h = g; g = f; f = e; e = d.wrapping_add(temp1);
            d = c; c = b; b = a; a = temp1.wrapping_add(temp2);
        }

        self.state[0] = self.state[0].wrapping_add(a);
        self.state[1] = self.state[1].wrapping_add(b);
        self.state[2] = self.state[2].wrapping_add(c);
        self.state[3] = self.state[3].wrapping_add(d);
        self.state[4] = self.state[4].wrapping_add(e);
        self.state[5] = self.state[5].wrapping_add(f);
        self.state[6] = self.state[6].wrapping_add(g);
        self.state[7] = self.state[7].wrapping_add(h);
    }

    fn finalize(mut self) -> [u8; 32] {
        let bit_len = self.total_len * 8;
        let mut pad = vec![0x80u8];
        let rem = (self.buffer.len() + 1) % 64;
        let zeros = if rem <= 56 { 56 - rem } else { 120 - rem };
        pad.extend(std::iter::repeat(0u8).take(zeros));
        pad.extend_from_slice(&bit_len.to_be_bytes());
        self.buffer.extend_from_slice(&pad);
        while self.buffer.len() >= 64 {
            let block: [u8; 64] = self.buffer[..64].try_into().unwrap();
            self.process_block(&block);
            self.buffer.drain(..64);
        }
        let mut out = [0u8; 32];
        for (i, word) in self.state.iter().enumerate() {
            out[i * 4..i * 4 + 4].copy_from_slice(&word.to_be_bytes());
        }
        out
    }
}

fn sha256(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize()
}

fn leaf_hash(data: &[u8]) -> Vec<u8> {
    let mut buf = vec![0x00u8];
    buf.extend_from_slice(data);
    sha256(&buf).to_vec()
}

fn node_hash(left: &[u8], right: &[u8]) -> Vec<u8> {
    let mut buf = vec![0x01u8];
    buf.extend_from_slice(left);
    buf.extend_from_slice(right);
    sha256(&buf).to_vec()
}

struct MerkleTree {
    levels: Vec<Vec<Vec<u8>>>,
}

impl MerkleTree {
    fn build(leaves: &[Vec<u8>]) -> Self {
        let mut level: Vec<Vec<u8>> = leaves.iter().map(|d| leaf_hash(d)).collect();
        let mut levels = vec![level.clone()];
        while level.len() > 1 {
            let mut next = Vec::with_capacity((level.len() + 1) / 2);
            let mut i = 0;
            while i < level.len() {
                let left = &level[i];
                let right = if i + 1 < level.len() { &level[i + 1] } else { &level[i] };
                next.push(node_hash(left, right));
                i += 2;
            }
            levels.push(next.clone());
            level = next;
        }
        MerkleTree { levels }
    }

    fn root(&self) -> &Vec<u8> {
        self.levels.last().unwrap().last().unwrap()
    }

    fn proof(&self, mut index: usize) -> Vec<(Vec<u8>, bool)> {
        let mut path = Vec::new();
        for level in &self.levels[..self.levels.len() - 1] {
            let sibling_index = index ^ 1;
            let sibling = if sibling_index < level.len() {
                level[sibling_index].clone()
            } else {
                level[index].clone()
            };
            path.push((sibling, sibling_index > index));
            index /= 2;
        }
        path
    }
}

fn verify(leaf: &[u8], path: &[(Vec<u8>, bool)], root: &[u8]) -> bool {
    let mut current = leaf_hash(leaf);
    for (sibling, is_right) in path {
        current = if *is_right {
            node_hash(&current, sibling)
        } else {
            node_hash(sibling, &current)
        };
    }
    current == root
}

fn to_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

fn main() {
    let leaves: Vec<Vec<u8>> = (0..5).map(|i| format!("tx-{}", i).into_bytes()).collect();
    let tree = MerkleTree::build(&leaves);
    let proof = tree.proof(3);
    let ok = verify(&leaves[3], &proof, tree.root());
    let root_hex = to_hex(tree.root());
    println!("root {}", &root_hex[..16]);
    println!("proof length {}", proof.len());
    println!("verified {}", ok);
}
```

Run output on this machine, via `rustc --edition 2021 merkle.rs` then running
the binary.

```
root 59c906ba9ad23b27
proof length 3
verified true
```

## 18. References

1. Ralph C. Merkle. "Method of providing digital signatures". United States
   Patent 4,309,569. Filed September 5, 1979. Google Patents record,
   https://patents.google.com/patent/US4309569A/en
   Verified 2026-08-02. Source of the original tree-authentication
   construction, the authentication path concept, and the historical
   attribution in dimensions 1 and 13.
2. IETF. RFC 6962, "Certificate Transparency", Ben Laurie, Adam Langley, Emilia
   Kasper. Section 2.1, Merkle Tree Hash. https://datatracker.ietf.org/doc/html/rfc6962
   Verified 2026-08-02. Source of the exact MTH recursive definition, the
   0x00 and 0x01 domain-separation prefixes used in dimensions 8, 9, 11, and
   the code examples, and the Certificate Transparency production use.
3. Bitcoin Wiki contributors. "Protocol Documentation", Merkle Trees section.
   https://en.bitcoin.it/wiki/Protocol_documentation
   Verified 2026-08-02. Source of the Bitcoin double-SHA-256 Merkle root
   description in dimension 9 and background for the duplicate-node failure
   mode in dimension 11.
4. The Apache Software Foundation. Apache Cassandra documentation, "Repair".
   https://cassandra.apache.org/doc/stable/cassandra/managing/operating/repair.html
   Verified 2026-08-02. Source of the anti-entropy repair production use in
   dimension 9 and the repair-round observability guidance in dimension 16.
5. Scott Chacon, Ben Straub. *Pro Git*, 2nd edition. "Git Internals, Git
   Objects", section on tree objects. https://git-scm.com/book/en/v2/Git-Internals-Git-Objects
   Verified 2026-08-02. Source of the Git tree-object, Merkle DAG production
   use in dimensions 8 and 9.
6. Protocol Labs. "IPLD Primer". https://ipld.io/docs/intro/primer/
   Verified 2026-08-02. Source of the IPFS and IPLD content-addressed
   Merkle DAG production use in dimension 9 and the content-addressable
   storage relationship in dimension 13.

## Judgement notes

Dimension 3, the weighting of which force matters most in each trade, and
dimension 10's degree-of-cost claims, are engineering judgement drawn from
the well documented behaviour of the systems cited in dimension 9, not
independently sourced facts in themselves. Dimension 11's failure modes are
drawn from the CVE-2012-2459 class of vulnerability and the RFC 6962 domain-
separation rationale, both independently checkable, combined with general
implementation experience for the remaining entries, which is stated as
judgement rather than as a specific sourced incident. Dimensions 15 through 17
are practice and analysis, not sourced claims, per the template's own
guidance on judgement versus sourced claims.
