---
name: Envelope Encryption
slug: envelope-encryption
family: 15-security
category: Security
aliases: [Key Wrapping, Data Key Wrapping, DEK and KEK, Client-side Envelope Encryption]
first_described: "Established key management practice"
maturity: established
related: [secrets-management, key-rotation, least-privilege, defense-in-depth, fail-securely]
incompatible_with: [single-static-data-key, hardcoded-secret, homegrown-cryptography]
verified: 2026-08-02
---

# Envelope Encryption

## 1. Name, aliases, and lineage

The canonical name is Envelope Encryption. In security engineering speech it is
also called key wrapping, data key wrapping, the DEK and KEK model, client-side
envelope encryption, or application-layer envelope encryption. The common
vocabulary is that a data encryption key, or DEK, encrypts the protected data,
while a key encryption key, or KEK, encrypts the DEK. Google Cloud KMS uses
those names in its envelope encryption documentation and defines envelope
encryption as encrypting a key with another key
([https://docs.cloud.google.com/kms/docs/envelope-encryption](https://docs.cloud.google.com/kms/docs/envelope-encryption),
verified 2026-08-02). AWS KMS describes the same practice as encrypting
plaintext data with a data key and then encrypting that data key under another
key
([https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html](https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html),
verified 2026-08-02).

The pattern does not have a single catalog author in the way that the Gang of
Four patterns do. It is a mature key management pattern that appears in cloud
KMS systems, storage systems, encryption SDKs, and cluster control planes. NIST
SP 800-57 Part 1 Revision 5 is a general key management recommendation by
Elaine Barker, published by NIST in May 2020, and covers the management of
cryptographic keying material rather than naming Envelope Encryption as a
software design pattern
([https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final),
verified 2026-08-02). The lineage is therefore operational cryptography and
key hierarchy, not object-oriented pattern literature.

Three neighboring terms need separation. **Key wrapping** is the cryptographic
operation that protects one key with another. Envelope Encryption is the system
pattern around that operation, including where the wrapped key is stored, how
the KEK is addressed, how rotation works, and how failures are observed.
**Secrets Management** stores and distributes secret values. Envelope Encryption
may use a secret store or KMS, but it is specifically about protecting data by
placing a small wrapped DEK beside larger ciphertext. **Transparent storage
encryption** can use envelope encryption internally while hiding the pattern
from application code. Amazon S3 SSE-KMS and Amazon EBS encryption are examples
where the service uses a data key and an AWS KMS key under the service boundary
([https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html),
verified 2026-08-02;
[https://docs.aws.amazon.com/ebs/latest/userguide/how-ebs-encryption-works.html](https://docs.aws.amazon.com/ebs/latest/userguide/how-ebs-encryption-works.html),
verified 2026-08-02).

## 2. Problem and context

A system must encrypt many records, objects, files, messages, volumes, or
tenant datasets. The data is too large or too frequent to send through a remote
key service for every byte of encryption, yet the organization still wants
central control over the authority that can decrypt. The system also needs a
workable answer to rotation, audit, access control, and incident response.

The common failing design uses one long-lived application key to encrypt every
object. That looks simple until the first rotation, backup restore, tenant
split, or suspected key exposure. Re-encrypting every byte under a new root key
can take hours or days. Revoking one tenant may require touching every object.
An audit log may show that the application read a configuration key, but not
which object was decrypted. A single leaked key can expose the entire
historical corpus.

Envelope Encryption splits the problem. The local encryption operation uses a
fresh or narrowly scoped DEK because symmetric encryption is fast and can run
near the data. The DEK is then wrapped by a KEK held by a KMS, HSM, key vault,
or other protected boundary. The stored envelope carries the ciphertext, the
wrapped DEK, the KEK identifier, the encryption algorithm, and non-secret
associated metadata. A decryptor asks the key service to unwrap the DEK and then
uses the returned plaintext DEK only long enough to decrypt the data.

The context matters. This pattern belongs where encryption at rest is a product
requirement, where plaintext key material must not live in source code or
configuration files, and where operational control over the KEK has value.
OWASP's Cryptographic Storage Cheat Sheet recommends dedicated secret or key
management systems where available and describes DEK and KEK separation for
encrypting stored keys
([https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html),
verified 2026-08-02). The pattern is not a full authorization system. It
protects data when stored or moved through untrusted storage. It does not decide
whether a user should see the plaintext after decryption.

## 3. Forces

Engineering judgement. This dimension weighs operational pressures that vary by
system. The cited documents establish the mechanics and named uses, while the
force ranking below is design reasoning.

- **Latency.** The pattern favors local bulk encryption and sacrifices a network
  call for key wrapping or unwrapping. Caching can reduce unwrap calls, but it
  also increases plaintext key exposure.
- **Coupling.** The data plane depends on the envelope format and the key
  service API. In exchange, storage no longer depends on a single static
  plaintext key.
- **Consistency.** Each object can carry its own KEK identifier and algorithm
  metadata, so old and new objects can coexist during migration. The cost is a
  stricter envelope parser and migration logic.
- **Operability.** The pattern favors auditability because KEK unwraps can be
  logged centrally. It sacrifices simplicity because outages, throttling, grants,
  and key states now affect decryption.
- **Cost.** Encrypting large data locally keeps KMS traffic small. Large read
  rates can still create KMS cost or quota pressure if the system unwraps on
  every read. Amazon S3 documents S3 Bucket Keys as a way to reduce SSE-KMS
  request cost by reducing request traffic to AWS KMS
  ([https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html),
  verified 2026-08-02).
- **Team topology.** A platform security team can own KEKs, policies, and audit,
  while application teams own envelope creation and data classification. The
  boundary must be clear or incidents become slow handoffs.
- **Cognitive load.** Developers must understand two keys, two lifetimes, two
  failure surfaces, and one serialized envelope. That is more to learn than a
  single encryption call.
- **Blast radius.** The pattern favors small blast radius when DEKs are per
  object, per row, per message, or per tenant. It gives up some storage space
  because every envelope carries key material metadata.

The pattern sacrifices simplicity to gain key isolation, rotation options, and
central control over decryption authority.

## 4. Applicability and non-applicability

Reach for Envelope Encryption when the following hold.

- Many independent data items need encryption at rest, and each item can carry
  a wrapped DEK beside its ciphertext.
- The data is too large, too frequent, or too latency-sensitive to send through
  a remote KMS encrypt API directly. Google Cloud KMS documents a 64 KiB maximum
  input size for its Encrypt and Decrypt functions and frames Cloud KMS as a
  KEK manager for envelope encryption
  ([https://docs.cloud.google.com/kms/docs/envelope-encryption](https://docs.cloud.google.com/kms/docs/envelope-encryption),
  verified 2026-08-02).
- Central policy, audit, key disablement, or HSM-backed custody of KEKs is part
  of the threat model.
- Key rotation must be practical without rewriting every encrypted byte.
  Rewrapping DEKs can change KEK protection while leaving bulk ciphertext in
  place.
- Different tenants, regions, datasets, or product tiers need different KEKs
  while sharing the same envelope code.
- Multiple decrypting principals may need access through different wrapping
  keys. The AWS Encryption SDK supports encrypting the same data key under
  multiple wrapping keys and storing those encrypted data keys with the message
  ([https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/concepts.html](https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/concepts.html),
  verified 2026-08-02).

Do NOT reach for Envelope Encryption in these cases.

- **The data should not be stored.** If the business can avoid retaining the
  sensitive value, deletion beats encryption. OWASP's Cryptographic Storage
  Cheat Sheet states that avoiding storage is the best way to protect sensitive
  information
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html),
  verified 2026-08-02).
- **Password storage is the problem.** Passwords need password hashing, not
  reversible encryption. OWASP points readers from cryptographic storage to its
  password storage guidance for that case
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html),
  verified 2026-08-02).
- **A managed storage layer already meets the threat model.** If S3 SSE-KMS,
  Azure Storage service-side encryption, database TDE, or disk encryption covers
  the real risk, application-layer envelopes add code, metadata, and failure
  modes without buying much.
- **The KEK and DEK will be stored in the same compromised place.** Wrapping a
  DEK with a KEK beside it in the same config file is security theater. OWASP
  says the KEK must be stored separately from the DEK for the approach to be
  effective
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html),
  verified 2026-08-02).
- **The application cannot tolerate key service dependency.** A read path that
  must work during KMS unavailability needs a carefully bounded cache, a local
  escrow model, or a different design.
- **The team intends to design its own cipher or message format from scratch.**
  Use an audited library or a cloud SDK. The pattern is architectural, not a
  license to invent cryptography.
- **Search, range queries, or joins over plaintext are required.** Ordinary
  envelope encryption hides data from the storage engine. Deterministic or
  searchable encryption is a different topic with different leakage.
- **All readers share full data access forever.** A single service-side key may
  be enough if no principal, tenant, region, or incident boundary exists.

## 5. Structure

The participants are named by role.

- **Plaintext Data.** The bytes the system wants to protect. They may be a
  record, file chunk, queue message, object, volume key, or serialized secret.
- **Data Encryption Key.** A symmetric key used for one data item or a narrow
  group of items. Google Cloud recommends generating a new DEK every time data
  is written in its envelope encryption guidance
  ([https://docs.cloud.google.com/kms/docs/envelope-encryption](https://docs.cloud.google.com/kms/docs/envelope-encryption),
  verified 2026-08-02).
- **Bulk Encryptor.** Local cryptographic code that encrypts plaintext with the
  DEK and authenticates non-secret metadata as associated data. The encryptor
  should come from a maintained library.
- **Key Encryption Key.** A longer-lived wrapping key held by a KMS, HSM, key
  vault, or controlled key service. The KEK protects the DEK and is controlled
  through policy.
- **Key Service.** The boundary that creates, stores, unwraps, rotates, disables,
  audits, and authorizes KEK use. In cloud systems this is often AWS KMS, Google
  Cloud KMS, Azure Key Vault, or a Kubernetes KMS provider.
- **Envelope.** The serialized object that stores encrypted data plus enough
  non-secret metadata to decrypt later. It commonly includes version, algorithm,
  nonce or IV, ciphertext, authentication tag if the library separates it,
  wrapped DEK, KEK identifier, and associated data.
- **Envelope Repository.** The database, object store, message broker, volume
  metadata store, or backup that keeps envelopes.
- **Decryptor.** Code that parses the envelope, authorizes the read, asks the
  key service to unwrap the DEK, checks authenticated metadata, decrypts the
  ciphertext, and removes the plaintext DEK from memory as soon as practical.

The central relationship is asymmetric. The repository may store the wrapped
DEK beside the ciphertext, but it must not store the KEK. The application may
see a plaintext DEK briefly, but ordinary storage should see only wrapped keys
and ciphertext.

## 6. ASCII structure diagram

```text
  +----------------+        uses         +---------------------+
  | Plaintext Data | ------------------> |   Bulk Encryptor    |
  +----------------+                     |  AEAD with local DEK |
                                         +----------+----------+
                                                    |
                                                    | creates
                                                    v
  +----------------+      wraps via       +---------------------+
  | Key Service    | <------------------- | Data Encryption Key |
  | holds KEK      | -------------------> | plaintext in memory |
  +-------+--------+      wrapped DEK     +----------+----------+
          |                                           |
          | identifies KEK                            | encrypts
          v                                           v
  +----------------+                     +---------------------+
  | Key Encryption |                     |      Envelope       |
  | Key in KMS/HSM |                     | version, alg, nonce |
  +----------------+                     | aad, wrapped DEK    |
                                         | ciphertext, tag     |
                                         +----------+----------+
                                                    |
                                                    | stored as one unit
                                                    v
                                         +---------------------+
                                         | Envelope Repository |
                                         +---------------------+
```

## 7. Dynamics

Encryption and decryption are mirror flows. The data path does bulk encryption
locally. The control path asks the key service for key wrapping or unwrapping.

```text
Encrypt write path

Client        App Encryptor       Key Service       Repository
  |                |                   |                 |
  | plaintext ---->|                   |                 |
  |                | generate DEK      |                 |
  |                | encrypt data      |                 |
  |                | wrap DEK -------->|                 |
  |                |<---- wrapped DEK  |                 |
  |                | build envelope    |                 |
  |                | store envelope -------------------->|
  |<---------------| ack               |                 |

Decrypt read path

Client        App Decryptor       Key Service       Repository
  |                |                   |                 |
  | read request ->|                   |                 |
  |                | fetch envelope -------------------->|
  |                |<-------------------- envelope       |
  |                | unwrap DEK ------>|                 |
  |                |<---- plaintext DEK|                 |
  |                | verify AAD        |                 |
  |                | decrypt data      |                 |
  |<---------------| plaintext         |                 |
```

Two dynamic details matter. First, associated data must bind the envelope to its
context. The AWS Encryption SDK treats encryption context as non-secret
associated data and warns that it can appear in plaintext in audit records and
logs
([https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/crypto-cli-how-to.html](https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/crypto-cli-how-to.html),
verified 2026-08-02). Second, rotation has two paths. New writes can use a new
KEK immediately. Old envelopes can either be decrypted and re-encrypted, or the
stored DEKs can be rewrapped under the new KEK when the bulk ciphertext does
not need to change.

## 8. Implementation variants

**Client-side envelope encryption.** The application creates the DEK, encrypts
data locally, calls a key service to wrap the DEK, and stores the envelope. This
gives the application control over associated data and plaintext boundaries. It
also puts more responsibility on application code. Google Cloud's envelope
encryption guide focuses on this application-layer shape when using Cloud KMS
as the central key store
([https://docs.cloud.google.com/kms/docs/envelope-encryption](https://docs.cloud.google.com/kms/docs/envelope-encryption),
verified 2026-08-02).

**Service-side envelope encryption.** The storage service owns the envelope
mechanics. Amazon S3 SSE-KMS requests data keys from AWS KMS, uses the data key
to encrypt object data, and stores the encrypted data key as metadata with the
encrypted data
([https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html),
verified 2026-08-02). This variant reduces application code but gives the
application less control over envelope format and plaintext handling.

**Per-object DEK.** Each object, record, or message receives its own DEK. This
is the cleanest blast-radius boundary and the most direct rotation story. It
costs more envelope metadata and more wrap or unwrap operations.

**Per-tenant or per-dataset DEK.** A DEK protects a bounded group. This lowers
metadata and KMS traffic, but a leaked DEK exposes the whole group. Engineering
judgement. This variant belongs only where the grouping matches the threat
model and retention rules.

**Hierarchical keyring.** The system uses a branch key or intermediate wrapping
key so the hot path does fewer direct KMS calls. The AWS Encryption SDK
documents keyrings as components that generate, encrypt, and decrypt data keys,
and also supports multi-keyrings
([https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/choose-keyring.html](https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/choose-keyring.html),
verified 2026-08-02). This variant improves throughput at the price of another
key level and another cache policy.

**Multi-recipient envelope.** The same DEK is wrapped under several KEKs. This
allows different regions, break-glass roles, customers, or migration windows to
decrypt the same ciphertext without copying the data. It increases envelope
size and policy review work.

**Kubernetes KMS provider.** The API server encrypts resources in etcd using a
DEK, and the DEK is encrypted by a KEK stored in a remote KMS. Kubernetes KMS v2
is documented as stable in Kubernetes 1.29 and later
([https://kubernetes.io/docs/tasks/administer-cluster/kms-provider/](https://kubernetes.io/docs/tasks/administer-cluster/kms-provider/),
verified 2026-08-02). This is a control-plane variant with plugin health,
socket, and API version concerns.

**Local KEK fallback.** A process holds a local wrapping key, possibly from a
file or environment. This can be useful for development and offline tools. In
production it often violates the separation that makes the pattern useful.

## 9. Known production uses

**Amazon S3 SSE-KMS.** Amazon S3 documents that it uses AWS KMS features for
envelope encryption when objects are protected with SSE-KMS. The workflow asks
AWS KMS for a plaintext data key and encrypted copy, encrypts the object with
the data key, stores the encrypted data key as metadata, and uses AWS KMS
Decrypt on reads
([https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html),
verified 2026-08-02).

**Amazon EBS encryption.** Amazon EBS documents that encrypted volumes use a
data key generated by AWS KMS and encrypted under an AWS KMS key before being
stored with volume information. When an encrypted volume is attached, AWS KMS
decrypts the encrypted data key and Amazon EC2 uses the plaintext data key in
Nitro hardware for disk I/O encryption
([https://docs.aws.amazon.com/ebs/latest/userguide/how-ebs-encryption-works.html](https://docs.aws.amazon.com/ebs/latest/userguide/how-ebs-encryption-works.html),
verified 2026-08-02).

**Kubernetes Secrets encryption with a KMS provider.** Kubernetes documents that
its KMS encryption provider uses an envelope encryption scheme to encrypt data
in etcd. It stores data encrypted with a DEK and protects the DEK with a KEK in
a remote KMS
([https://kubernetes.io/docs/tasks/administer-cluster/kms-provider/](https://kubernetes.io/docs/tasks/administer-cluster/kms-provider/),
verified 2026-08-02).

**Google Cloud storage encryption at rest and Cloud KMS.** Google Cloud states
that customer content stored at rest is encrypted by default using envelope
encryption with Google's internal key management service as the central
keystore, and that Cloud KMS can act as the KEK manager for application-layer
envelope encryption
([https://docs.cloud.google.com/kms/docs/envelope-encryption](https://docs.cloud.google.com/kms/docs/envelope-encryption),
verified 2026-08-02).

**Azure Storage encryption.** Azure Storage documents automatic service-side
encryption for storage accounts, support for customer-managed keys in Azure Key
Vault or Key Vault Managed HSM, and client-side encryption v2 in Blob and Queue
client libraries using AES-GCM
([https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption](https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption),
verified 2026-08-02). The cited page does not call every Azure Storage mode
Envelope Encryption by name, so this entry treats Azure Storage as a production
use of managed keys and client-side encryption support, not as proof of a
specific internal envelope format beyond what Microsoft documents.

## 10. Consequences

Engineering judgement. These consequences follow from the structure and from
the behavior documented by the named systems above.

Positive.

- A large ciphertext can be protected by a small wrapped DEK, so KEK rotation
  can often rewrap keys rather than rewrite bulk data.
- A central key service can audit unwraps and enforce policy on KEK use.
- Per-object or per-tenant DEKs reduce blast radius compared with one static
  application key.
- The envelope can carry algorithm and KEK metadata, which makes mixed-version
  migration possible.
- Multiple wrapped copies of the same DEK can support migration, cross-region
  access, or break-glass access without duplicating ciphertext.
- Storage administrators can hold ciphertext and wrapped DEKs without holding
  KEKs, which creates a useful separation of duties when policy is narrow.

Negative.

- Every read can depend on KMS availability, latency, quotas, and key policy.
- Plaintext DEKs exist in application memory during encryption and decryption.
- The envelope format becomes a long-lived compatibility contract.
- Metadata mistakes can break old data, especially missing key identifiers,
  nonce values, algorithm identifiers, or associated data.
- KMS permissions become part of application correctness. A policy change can
  look like data corruption to callers.
- Caching plaintext DEKs improves read latency but expands the time window in
  which process compromise exposes data.
- Developers can misunderstand rotation and rotate only the KEK alias while old
  envelopes remain bound to older key versions or different key identifiers.

## 11. Failure modes and misuse

Engineering judgement. The triples below are written as operational failure
patterns a team can detect in logs, dashboards, tests, and incident reviews.

**Symptom.** KMS Decrypt returns access denied after a routine IAM or key policy
change, and the application reports unreadable objects. **Cause.** Envelope
decryption depends on the KEK policy, but the policy was changed without a
canary decrypt against existing envelopes. **Fix.** Add a rotation and policy
change runbook that performs decrypt probes for every active KEK and data class
before rollout.

**Symptom.** A restored backup contains ciphertext, but no code can decrypt it
because the key identifier points to a deleted KEK. **Cause.** Key deletion was
scheduled without checking backup retention and envelope age. **Fix.** Make KEK
deletion require an inventory query proving no retained envelope references the
key, or archive the key material under a controlled recovery process.

**Symptom.** Decrypt succeeds for the wrong tenant after a data move or
cross-tenant copy. **Cause.** Tenant, object path, or table identity was not
bound as associated data, so the ciphertext can be replayed in another context.
**Fix.** Include stable non-secret context in AAD and reject envelopes whose AAD
does not match the expected storage location and tenant.

**Symptom.** KMS cost and latency climb with read volume even though ciphertext
size is flat. **Cause.** The application unwraps the DEK on every read and has
no bounded cache or bucket-level key strategy. **Fix.** Add a short-lived,
capacity-bounded cache for permitted data classes, or use a managed service
feature such as S3 Bucket Keys where it fits.

**Symptom.** A production incident reveals plaintext DEKs in crash dumps, trace
spans, or debug logs. **Cause.** Key bytes were represented as strings,
included in structured error context, or retained after use. **Fix.** Keep keys
in byte arrays, redact by type, avoid logging envelope internals that carry key
material, and zero buffers where the runtime makes that meaningful.

**Symptom.** Old ciphertext cannot be decrypted after a library upgrade.
**Cause.** The envelope did not store algorithm version, nonce size, tag
encoding, or serialization version. **Fix.** Version the envelope from day one
and keep compatibility tests with golden encrypted fixtures for every shipped
version.

**Symptom.** Rotation completes fast, but audit shows old KEKs still used
months later. **Cause.** New writes moved to the new KEK, but existing
envelopes were not rewrapped or rewritten. **Fix.** Track old-key decrypt count
and run a rewrap worker until the old key reaches zero expected use.

**Symptom.** A database breach exposes both ciphertext and enough key material
to decrypt it. **Cause.** The KEK, KEK credential, or unwrapped DEK cache was
stored in the same database or backup as the envelopes. **Fix.** Move KEK use
behind a separate KMS boundary and separate access paths for data and keys.

## 12. Trade-off matrix

| Force | Envelope Encryption | Direct KMS encryption | Storage SSE-KMS | Database TDE | One static app key | Public-key per recipient |
|---|---|---|---|---|---|---|
| Bulk data latency | Good. Local symmetric encryption | Poor for large data | Good. Service handles it | Good. Engine handles it | Good | Poor for large data |
| KMS call volume | Medium. Wrap or unwrap per item or cache miss | High. Data path hits KMS | Medium to low with service features | Low to app | None after boot | Medium |
| Rotation cost | Good. Rewrap DEKs | Poor. Re-encrypt data | Good within service model | Engine-specific | Poor. Rewrite data | Medium. Rewrap recipient keys |
| Blast radius | Good with per-item DEKs | Good if per-item | Service-defined | Database scope | Poor | Good per recipient |
| App complexity | Medium | Low API shape, high cost | Low | Low | Low | High |
| Audit of decrypt authority | Strong at KEK unwrap | Strong | Strong via service logs | Often coarse | Weak | Medium |
| Search over plaintext | Poor | Poor | Storage dependent | Database dependent | Poor | Poor |
| Offline decrypt | Possible with local KEK variant | No | No | No | Yes | Yes for private key holder |
| Separation of duties | Strong if KMS is separate | Strong | Strong | Medium | Weak | Strong |
| Best fit | Large sensitive objects with key control | Tiny payloads | Cloud object storage | Whole database at rest | Local dev or low-risk data | Sharing to many recipients |

Reading the table. Envelope Encryption wins where large data must stay local
but key authority must stay central. Direct KMS encryption wins for tiny values
under the service's size limit. Storage SSE-KMS and database TDE win where the
managed layer matches the threat model. A single static application key is a
baseline to retire, not a serious production target for sensitive data.
Public-key recipient encryption wins when many independent recipients need
offline access and no central unwrap service exists.

## 13. Related and incompatible patterns

**Secrets Management** composes with Envelope Encryption. Secrets Management
stores credentials and may store KEK access credentials, while Envelope
Encryption protects application data and DEKs. The two are often deployed
together but solve different problems.

**Key Rotation** is the lifecycle partner. Envelope Encryption gives rotation a
cheap unit of work, the wrapped DEK. Key Rotation defines when and how old KEKs
or DEKs are retired, tested, and removed.

**Least Privilege** shapes the key policy. A workload should be able to unwrap
only the KEKs for the data classes it serves. Broad `Decrypt` access across all
production keys turns KMS into a central decryption oracle.

**Defense in Depth** is the security posture. Envelope Encryption can sit above
service-side storage encryption, but the second layer should protect a real
threat such as storage operator access, cloud account separation, or backup
exposure.

**Fail Securely** controls error handling. Decrypt failure must not return
partial plaintext, retry indefinitely with broader keys, or fall back to a
legacy static key.

**Homegrown Cryptography** is incompatible. The pattern should use established
AEAD modes and maintained libraries. Designing a cipher, nonce scheme, or
message authentication format without review defeats the point.

**Hardcoded Secret** is incompatible. A KEK in source code collapses the key
hierarchy into the repository.

**Single static data key** is the design Envelope Encryption replaces. If all
objects use the same long-lived data key, the system has no useful per-object
blast-radius boundary and rotation becomes bulk data migration.

## 14. Refactoring path in and out

Introducing Envelope Encryption into an existing system.

1. Inventory data classes, storage locations, retention windows, owners, and
   required decrypting services. Do not start by choosing a KMS product.
2. Pick the envelope boundary. For object stores, it is usually one object. For
   databases, it may be one row, one column group, or one tenant dataset. The
   boundary should match the blast radius you want.
3. Define an envelope version with explicit fields for algorithm, nonce, KEK
   identifier, wrapped DEK, associated data, and ciphertext. Add a parser that
   rejects unknown required fields.
4. Add a KMS or HSM adapter interface with `wrap` and `unwrap` operations. Keep
   cloud SDK details out of domain code.
5. Write encrypt and decrypt functions using an AEAD library. Bind stable
   metadata as associated data. Treat AAD as non-secret because providers can
   log it.
6. Write new data in envelope format while still reading old plaintext or old
   ciphertext format. This is the Strangler Fig migration shape from the
   refactoring family.
7. Backfill old data through a resumable worker. Store progress by object ID
   and make the worker idempotent.
8. Add decrypt canaries, old-format read metrics, and old-key use metrics. Do
   not delete legacy code until old-format reads reach zero for the retention
   period.
9. Rotate once in staging and once in production with a small data class before
   declaring the pattern adopted.

Removing the pattern when it stops earning its place.

1. Prove the managed storage layer now covers the threat model, or prove the
   data no longer needs reversible encryption.
2. Freeze writes to the old envelope format or route them to the new storage
   encryption path.
3. Decrypt and rewrite data into the target representation, or export and
   re-import through the managed service.
4. Keep old KEKs enabled for the longest backup restore window, unless a
   confirmed compromise requires a faster break.
5. Remove decrypt permissions before deleting code. That catches hidden
   dependencies while recovery is still easy.
6. Delete KEKs only after an inventory shows no envelope, backup, queue, or
   archive references them.

## 15. Testing and verification

Engineering judgement. The test strategy should prove both cryptography
contracts and operational contracts, because most envelope failures are metadata
or policy failures rather than broken AES.

Test the envelope format with golden fixtures. A fixture should include version,
algorithm, nonce, AAD, KEK identifier, wrapped DEK, and ciphertext. Keep at
least one fixture per released envelope version so parser changes cannot
silently orphan old data.

Test associated data binding. Encrypt an envelope for tenant A and attempt to
decrypt it under tenant B's AAD. The expected result is authentication failure,
not successful plaintext followed by a later authorization check.

Test key policy with positive and negative cases. A service that should decrypt
tenant A data should pass. A neighboring service should get access denied at
the key service. Do this against a staging KMS key, not only against a fake.

Test rotation as a behavior. Write data under KEK version one, rotate the KEK
selection, write new data under version two, and prove both old and new
envelopes decrypt. Then rewrap old envelopes and verify the old-key decrypt
counter falls.

Test failure paths. Corrupt the nonce, ciphertext, tag, wrapped DEK, key ID, and
version one at a time. The decrypt function should fail closed with typed errors
and without logging key bytes or plaintext.

Test concurrency. Rewrap workers and application reads can race. A read should
accept either the old or new wrapper during migration, while the write path must
publish an envelope atomically.

### TypeScript

```typescript
const { createCipheriv, createDecipheriv, randomBytes } = require("crypto");

type Envelope = {
  version: 1;
  keyId: string;
  nonce: any;
  wrappedDek: any;
  ciphertext: any;
  tag: any;
};

class LocalKek {
  constructor(readonly keyId: string, private readonly kek: any) {}

  wrap(dek: any): any {
    const nonce = Buffer.alloc(12, 0);
    const cipher = createCipheriv("aes-256-gcm", this.kek, nonce);
    cipher.setAAD(Buffer.from(this.keyId));
    return Buffer.concat([cipher.update(dek), cipher.final(), cipher.getAuthTag()]);
  }

  unwrap(wrapped: any): any {
    const nonce = Buffer.alloc(12, 0);
    const body = wrapped.subarray(0, wrapped.length - 16);
    const tag = wrapped.subarray(wrapped.length - 16);
    const decipher = createDecipheriv("aes-256-gcm", this.kek, nonce);
    decipher.setAAD(Buffer.from(this.keyId));
    decipher.setAuthTag(tag);
    return Buffer.concat([decipher.update(body), decipher.final()]);
  }
}

function encrypt(kms: LocalKek, plaintext: any, aad: any): Envelope {
  const dek = randomBytes(32);
  const nonce = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", dek, nonce);
  cipher.setAAD(aad);
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  return {
    version: 1,
    keyId: kms.keyId,
    nonce,
    wrappedDek: kms.wrap(dek),
    ciphertext,
    tag: cipher.getAuthTag(),
  };
}

function decrypt(kms: LocalKek, env: Envelope, aad: any): any {
  const dek = kms.unwrap(env.wrappedDek);
  const decipher = createDecipheriv("aes-256-gcm", dek, env.nonce);
  decipher.setAAD(aad);
  decipher.setAuthTag(env.tag);
  return Buffer.concat([decipher.update(env.ciphertext), decipher.final()]);
}

const kms = new LocalKek("local-test-kek", randomBytes(32));
const aad = Buffer.from("tenant=alpha;object=42");
const env = encrypt(kms, Buffer.from("invoice total: 41"), aad);
console.log(decrypt(kms, env, aad).toString());
```

### Go

```go
package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"fmt"
	"io"
)

type Envelope struct {
	KeyID      string
	Nonce      []byte
	WrappedDEK []byte
	Body       []byte
}

type LocalKMS struct {
	keyID string
	kek   []byte
}

func random(n int) []byte {
	out := make([]byte, n)
	if _, err := io.ReadFull(rand.Reader, out); err != nil {
		panic(err)
	}
	return out
}

func aead(key []byte) cipher.AEAD {
	block, err := aes.NewCipher(key)
	if err != nil {
		panic(err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		panic(err)
	}
	return gcm
}

func (k LocalKMS) wrap(dek []byte) []byte {
	nonce := make([]byte, 12)
	return aead(k.kek).Seal(nil, nonce, dek, []byte(k.keyID))
}

func (k LocalKMS) unwrap(wrapped []byte) ([]byte, error) {
	nonce := make([]byte, 12)
	return aead(k.kek).Open(nil, nonce, wrapped, []byte(k.keyID))
}

func encrypt(kms LocalKMS, plain, aad []byte) Envelope {
	dek := random(32)
	nonce := random(12)
	body := aead(dek).Seal(nil, nonce, plain, aad)
	return Envelope{kms.keyID, nonce, kms.wrap(dek), body}
}

func decrypt(kms LocalKMS, env Envelope, aad []byte) ([]byte, error) {
	dek, err := kms.unwrap(env.WrappedDEK)
	if err != nil {
		return nil, err
	}
	return aead(dek).Open(nil, env.Nonce, env.Body, aad)
}

func main() {
	kms := LocalKMS{"local-test-kek", random(32)}
	aad := []byte("tenant=alpha;object=42")
	env := encrypt(kms, []byte("invoice total: 41"), aad)
	plain, err := decrypt(kms, env, aad)
	if err != nil {
		panic(err)
	}
	fmt.Println(string(plain))
}
```

### Python

```python
from dataclasses import dataclass
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class Envelope:
    key_id: str
    nonce: bytes
    wrapped_dek: bytes
    body: bytes


class LocalKMS:
    def __init__(self, key_id: str, kek: bytes) -> None:
        self.key_id = key_id
        self._kek = kek

    def wrap(self, dek: bytes) -> bytes:
        nonce = b"\x00" * 12
        return AESGCM(self._kek).encrypt(nonce, dek, self.key_id.encode())

    def unwrap(self, wrapped: bytes) -> bytes:
        nonce = b"\x00" * 12
        return AESGCM(self._kek).decrypt(nonce, wrapped, self.key_id.encode())


def encrypt(kms: LocalKMS, plain: bytes, aad: bytes) -> Envelope:
    dek = os.urandom(32)
    nonce = os.urandom(12)
    body = AESGCM(dek).encrypt(nonce, plain, aad)
    return Envelope(kms.key_id, nonce, kms.wrap(dek), body)


def decrypt(kms: LocalKMS, env: Envelope, aad: bytes) -> bytes:
    dek = kms.unwrap(env.wrapped_dek)
    return AESGCM(dek).decrypt(env.nonce, env.body, aad)


if __name__ == "__main__":
    kms = LocalKMS("local-test-kek", os.urandom(32))
    aad = b"tenant=alpha;object=42"
    env = encrypt(kms, b"invoice total: 41", aad)
    print(decrypt(kms, env, aad).decode())
```

## 16. Observability signals

Engineering judgement. The pattern is invisible in a database row unless its
control-plane events are measured.

Record encrypt and decrypt counts by envelope version, KEK identifier, data
class, tenant class, and outcome. Keep tenant labels low-cardinality or hashed
if required by privacy policy. Record KMS wrap and unwrap latency separately
from local encryption latency so teams can tell a cryptographic CPU issue from
a key service issue.

Record key service errors by stable categories: access denied, key disabled,
key pending deletion, key not found, throttled, timeout, malformed wrapped key,
and authentication failure. For managed services, also watch provider-specific
audit logs. Amazon S3 points to CloudTrail logs for SSE-KMS cryptographic
operations such as GenerateDataKey and Decrypt
([https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html),
verified 2026-08-02).

Record old-key use after rotation. A healthy rotation has new writes on the new
KEK and a falling decrypt count on old KEKs. A failing rotation has old-key
decrypts that never drop, or a sudden rise in access denied for old data.

Record cache behavior when plaintext DEKs or branch keys are cached. Useful
signals are hit rate, miss rate, entry count, maximum age, eviction count, and
decrypts served while the key service is unavailable. Treat cache hit rate as a
risk signal too, because a high hit rate means plaintext key material is staying
in process memory long enough to matter.

A healthy dashboard shows stable decrypt latency, low authentication failure
rate, expected key distribution by data class, no use of disabled keys, and
successful decrypt canaries for every active KEK. A failing dashboard shows
timeouts from the key service, old KEKs that never age out, malformed envelopes
after a deploy, or decrypt attempts against a KEK outside the service's data
class.

## 17. Security and privacy implications

Engineering judgement, tied to the cited cryptographic storage and KMS guidance
where the guidance is specific.

Envelope Encryption closes one major attack path. A database, object store, or
backup leak that contains ciphertext and wrapped DEKs should not be enough to
recover plaintext unless the attacker also gets KEK use or key service
credentials. That statement depends on the KEK being separate from the stored
envelopes, which OWASP calls out as a condition for the approach to be
effective
([https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html),
verified 2026-08-02).

It opens a new control-plane attack surface. The key service becomes a
decryption oracle if policies are broad, logs are ignored, or workloads can ask
for any KEK. Least privilege must be applied to decrypt permission, not only to
the database. A useful policy says which service can unwrap which KEK for which
data class, and the application binds that data class into AAD.

Plaintext DEKs still exist. The pattern does not make application memory safe.
An attacker with code execution inside the decrypting process can read
plaintext, DEKs, or both. Hardware-backed KMS protects KEKs, not the data after
the application legitimately asks for a DEK. This is why local caches, crash
dumps, debug logs, support bundles, and traces are part of the security review.

Metadata is not automatically secret. Key identifiers, tenant labels, object
paths, and encryption context are often stored or logged in plaintext. AWS warns
that encryption context values are not secret and can appear in audit records
and logs
([https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/crypto-cli-how-to.html](https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/crypto-cli-how-to.html),
verified 2026-08-02). Do not put personal data, access tokens, or plaintext
secrets into AAD or key IDs.

Nonce discipline matters. AEAD modes such as AES-GCM require unique nonces for
a given key. The examples use random nonces for data encryption and a fixed
nonce only in the local KEK demo because the demo wraps random DEKs under a
local test key and keeps the code compact. Production systems should use a
reviewed KMS or encryption SDK for key wrapping rather than copying demo code.

Privacy gains depend on access paths. If every application service can decrypt
every envelope, encryption protects backups and storage operators but does not
protect tenants from confused internal access. Tie KEKs to data classes and
collect audit logs that can answer which workload decrypted which class of data
at which time.

## 18. References

1. Amazon Web Services. *AWS KMS cryptography essentials*, section "Envelope
   encryption".
   [https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html](https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html)
   Verified 2026-08-02. Source for the AWS KMS definition, root key wording,
   KMS boundary, and envelope benefits.
2. Google Cloud. *Envelope encryption, Cloud Key Management Service*.
   [https://docs.cloud.google.com/kms/docs/envelope-encryption](https://docs.cloud.google.com/kms/docs/envelope-encryption)
   Verified 2026-08-02. Source for DEK and KEK terminology, Cloud KMS as KEK
   manager, local DEK guidance, 64 KiB Cloud KMS input limit, and Google Cloud
   storage encryption statement.
3. Amazon Web Services. *Using server-side encryption with AWS KMS keys
   (SSE-KMS), Amazon Simple Storage Service*.
   [https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html)
   Verified 2026-08-02. Source for the Amazon S3 production use, SSE-KMS
   workflow, S3 Bucket Keys, permissions, encryption context, and audit signals.
4. Amazon Web Services. *How Amazon EBS encryption works, Amazon EBS*.
   [https://docs.aws.amazon.com/ebs/latest/userguide/how-ebs-encryption-works.html](https://docs.aws.amazon.com/ebs/latest/userguide/how-ebs-encryption-works.html)
   Verified 2026-08-02. Source for the Amazon EBS production use.
5. Kubernetes. *Using a KMS provider for data encryption*.
   [https://kubernetes.io/docs/tasks/administer-cluster/kms-provider/](https://kubernetes.io/docs/tasks/administer-cluster/kms-provider/)
   Verified 2026-08-02. Source for Kubernetes KMS envelope encryption, KMS v2
   status, per-encryption DEK behavior, caching notes, and verification prefix.
6. Microsoft. *Azure Storage encryption for data at rest*.
   [https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption](https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption)
   Verified 2026-08-02. Source for Azure Storage service-side encryption,
   customer-managed keys, Key Vault and Managed HSM support, and client-side
   encryption v2 support.
7. Amazon Web Services. *Concepts in the AWS Encryption SDK*.
   [https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/concepts.html](https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/concepts.html)
   Verified 2026-08-02. Source for AWS Encryption SDK envelope concepts,
   wrapping keys, encrypted messages, multi-wrapping, and key commitment.
8. Amazon Web Services. *Keyrings, AWS Encryption SDK*.
   [https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/choose-keyring.html](https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/choose-keyring.html)
   Verified 2026-08-02. Source for keyrings generating, encrypting, and
   decrypting data keys.
9. Amazon Web Services. *How to use an encryption context, AWS Encryption CLI*.
   [https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/crypto-cli-how-to.html](https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/crypto-cli-how-to.html)
   Verified 2026-08-02. Source for encryption context as non-secret associated
   data and logging cautions.
10. OWASP Cheat Sheet Series. *Cryptographic Storage Cheat Sheet*.
    [https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
    Verified 2026-08-02. Source for cryptographic storage architecture,
    password non-applicability, key storage, DEK and KEK separation, and
    rotation considerations.
11. OWASP Cheat Sheet Series. *Key Management Cheat Sheet*.
    [https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
    Verified 2026-08-02. Source for key lifecycle, key storage, cryptographic
    vault guidance, and KEK protection guidance.
12. Elaine Barker. *Recommendation for Key Management. Part 1, General*,
    NIST Special Publication 800-57 Part 1 Revision 5, May 2020.
    [https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final)
    Verified 2026-08-02. Source for general key management lineage and
    terminology context. No page number cited because the web verification used
    the NIST landing page rather than the paginated PDF.
