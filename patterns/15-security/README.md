# Family 15. Security

Origin. OWASP ASVS

35 entries, 221,559 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Authorization

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Attribute-Based Access Control](abac.md) | established | 6,251 | Authorization starts simple. A user has a role, a resource has an owner, and the application checks whether the role or owner permits the action. |
| [OAuth 2.1 Flows](oauth-2-1-flows.md) | established | 7,011 | A service needs to let software access protected resources without giving that software the resource owner's primary credential. |

## Injection Defense

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Parameterized Query](parameterized-query.md) | canonical | 7,342 | An application must issue a query whose predicate values come from runtime state: a user id, tenant id, search term, date range, account status, cursor, or authorization scope. |

## Security

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Audit Log](audit-log.md) | established | 6,336 | A system accepts actions whose history must survive beyond the request that performed them. |
| [CSRF Token](csrf-token.md) | established | 6,821 | A web application uses browser-sent ambient credentials for authentication. |
| [Complete Mediation](complete-mediation.md) | canonical | 7,097 | A system contains objects that are not public. |
| [Content Security Policy](content-security-policy.md) | established | 6,848 | A web page runs with large ambient power. |
| [Defense in Depth](defense-in-depth.md) | canonical | 6,502 | A system has assets that must remain confidential, correct, and available while being exposed to users, code, networks, dependencies, administrators, build systems, and other ... |
| [Envelope Encryption](envelope-encryption.md) | established | 6,273 | A system must encrypt many records, objects, files, messages, volumes, or tenant datasets. |
| [Fail Securely](fail-securely.md) | established | 6,856 | A program must make a decision that protects a resource, but the information needed for that decision can be absent, stale, malformed, contradictory, late, or produced by a ... |
| [Idempotency Key](idempotency-key.md) | established | 6,606 | A client sends a mutating request and then loses the answer. |
| [Input Validation](input-validation.md) | canonical | 6,182 | A program accepts bytes, strings, numbers, objects, headers, files, paths, identifiers, query parameters, form fields, JSON bodies, environment variables, messages, or records ... |
| [JWT](jwt.md) | established | 6,076 | A resource server needs to accept repeated calls without contacting the issuer for every request, yet it still needs an issuer, subject, audience, expiry, possibly scopes, and a ... |
| [Key Rotation](key-rotation.md) | established | 6,762 | A system depends on secret material that cannot be treated as permanent. |
| [Least Privilege](least-privilege.md) | canonical | 6,389 | A system needs trusted actions to happen, but the code, user, service account, container, or job that performs those actions can also fail, be tricked, or be taken over. |
| [Mutual TLS](mutual-tls.md) | established | 6,027 | A service accepts network calls from other machines. |
| [OpenID Connect](openid-connect.md) | established | 7,015 | The problem appears when an application needs to sign in users through an external identity system without copying passwords, duplicating multi-factor logic, or inventing its own ... |
| [Output Encoding](output-encoding.md) | established | 6,294 | A program has data that may contain characters with special meaning in the output grammar. |
| [Passkeys and WebAuthn](passkeys-and-webauthn.md) | established | 6,513 | A web service needs strong user authentication, but passwords have become the wrong primitive. |
| [Passwordless Authentication](passwordless-authentication.md) | established | 6,470 | A user-facing system needs to authenticate people without making a reusable shared secret the center of the login ceremony. |
| [Relationship-Based Access Control](rebac.md) | established | 6,005 | A collaborative system grants access because of how a subject is related to a particular object. |
| [Role-Based Access Control](rbac.md) | canonical | 6,897 | A system has many people, services, jobs, and automated agents, and each one needs different authority over many objects. |
| [STRIDE](stride.md) | established | 6,084 | A team has an architecture sketch, a data flow, a new feature, or a service boundary, and needs a disciplined way to ask security questions before the design becomes expensive to ... |
| [Secrets Management](secrets-management.md) | established | 2,742 | An application needs credentials to call a database, sign a token, decrypt a record, publish to a queue, or call a third-party API. |
| [Secure by Default](secure-by-default.md) | established | 6,822 | A system has settings, generated files, API defaults, permission rules, feature switches, installation steps, or project scaffolds. |
| [Separation of Duties](separation-of-duties.md) | canonical | 6,652 | A system has operations where one trusted actor can cause damage and hide it. |
| [Supply Chain SBOM](supply-chain-sbom.md) | established | 6,110 | A software artifact enters production with code from many origins. |
| [Threat Modeling](threat-modeling.md) | established | 6,225 | A software team is making a design choice that changes who can reach which asset, what data crosses which boundary, what authority a component holds, or what a failed control ... |
| [Token Binding and DPoP](token-binding-and-dpop.md) | established | 6,233 | Bearer tokens are convenient because a resource server can authorize a request by checking the token. |
| [Token-based Authentication](token-based-authentication.md) | established | 7,183 | The problem appears when a system must authenticate repeated requests without asking the caller to resend a long-lived secret, such as a password, private key, or root cloud ... |
| [Webhook Signature Verification](webhook-signature-verification.md) | established | 6,038 | A webhook endpoint receives requests from the public internet, usually without a browser session, an OAuth bearer token, or a mutual TLS client certificate. |
| [Zero Trust](zero-trust.md) | established | 6,642 | A system has users, services, jobs, devices, and partners that need access to resources from many networks. |

## Supply Chain Security

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [SLSA Provenance](slsa-provenance.md) | emerging | 3,928 | A person or a system consuming a software artifact, a compiled binary, a container image, a published package, has no way to answer a basic question from the artifact alone. |

## Transport Security

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Certificate Pinning](certificate-pinning.md) | established | 6,213 | TLS authenticates a server by building and validating a certificate chain from the server's leaf certificate to a trusted root. |

## Web Security

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Session Management](session-management.md) | established | 6,114 | HTTP requests arrive independently. A user signs in on one request, then clicks through pages, posts forms, uploads data, and calls APIs on later requests. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
