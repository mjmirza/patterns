---
name: Secrets Management
slug: secrets-management
family: 15-security
category: Security
aliases: [Secret Management, Credential Management, Runtime Secret Injection]
first_described: "Saltzer and Schroeder 1975; OWASP Secrets Management Cheat Sheet"
maturity: established
related: [least-privilege, key-rotation, envelope-encryption, token-based-authentication, externalized-configuration]
incompatible_with: [hardcoded-secret, shared-credential]
verified: 2026-08-13
---

# Secrets Management

## 1. Name, aliases, and lineage

Secrets Management is the operational pattern of storing, distributing,
rotating, auditing, and revoking credentials outside application source code.
The term appears in current vendor and community documentation as secret
management, secrets management, and credential management. This entry uses
Secrets Management because it matches the OWASP cheat sheet title and common
cloud service naming.

The older lineage is not a single named pattern but a security principle.
Saltzer and Schroeder's 1975 paper, "The Protection of Information in Computer
Systems," argues for least privilege and complete mediation, two ideas this
pattern applies to machine credentials. Modern public guidance is more direct.
OWASP's Secrets Management Cheat Sheet defines secrets as sensitive values
such as passwords, API keys, tokens, and private keys, and gives practices for
storage, rotation, audit, and exposure reduction
([OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html),
verified 2026-08-13). NIST SP 800-57 Part 1 gives the key-management
lifecycle vocabulary for cryptographic keys, including generation,
distribution, storage, use, and destruction
([NIST SP 800-57 Part 1 Revision 5](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final),
verified 2026-08-13).

The pattern became common infrastructure once applications moved from one
long-lived server to elastic fleets, containers, serverless functions, and CI
pipelines. In that environment a secret pasted into a config file is not one
file. It is an accidental replication protocol.

## 2. Problem and context

An application needs credentials to call a database, sign a token, decrypt a
record, publish to a queue, or call a third-party API. Those credentials must
be available to the running program, but they must not be readable by every
developer, logged by every process, copied into every build artifact, or left
alive after they are no longer needed.

The failure usually starts small. A developer needs a database password for a
local test and puts it into a YAML file. The same style reaches staging. A CI
job gets a token through an environment variable that every step can read. A
container image is built with a private package token in a layer. A support
script writes the full environment to the log after a crash. Each step looks
convenient in isolation. Together they create a system where nobody can answer
which service has which secret, who read it, when it rotated, or how to revoke
it without breaking production.

Secrets Management fits when a system has more than one service, more than one
operator, or more than one runtime environment. It is less about choosing a
vault product than about making the secret lifecycle explicit. A secret should
have an owner, a scope, an issue path, a runtime delivery path, a rotation
plan, an audit trail, and a deletion path.

## 3. Forces

**Availability versus exposure.** A runtime must read the credential when it
needs to call a dependency. Every extra place that can read it is also a place
that can leak it. The pattern favours a narrow runtime path over broad
developer or build-time access.

**Developer speed versus revocation.** A copied `.env` file is fast today but
hard to revoke tomorrow. A central store with short-lived credentials adds
setup work, but it gives operators one place to disable access.

**Static simplicity versus rotation.** A long-lived password in a config file
is easy to reason about until it leaks. Dynamic credentials and automatic
rotation lower the blast radius, but they require clients to reload or renew
credentials without downtime.

**Local autonomy versus central policy.** Teams want to add integrations
without waiting on a central group. Security teams need audit, expiry, and
scope rules. The pattern works best when the platform provides self-service
secret creation under policy, not ticket-driven manual copying.

**Observability versus redaction.** Operators need to know whether secret
fetches are failing. They do not need the secret value. Logs and traces must
record identifiers, versions, and outcomes while redacting the value itself.

## 4. Applicability and non-applicability

Reach for Secrets Management when the following hold.

- The application uses database passwords, API tokens, signing keys, private
  keys, OAuth client secrets, webhook signing secrets, or service account
  credentials.
- The same secret would otherwise be copied into source code, CI variables,
  local files, container images, Kubernetes manifests, or manual runbooks.
- Operators need audit records for read, write, rotate, and revoke actions.
- The system needs rotation without rebuilding or redeploying every dependent
  service.
- A credential should be scoped to one application, one environment, one
  dependency, or one operation.

Explicit non-applicability follows.

- Do not use a runtime secret store for public configuration such as feature
  names, page sizes, public URLs, or non-sensitive flags. Externalized
  Configuration is the related pattern for those values.
- Do not hide a value in a secret store when the real problem is identity.
  If every service shares the same powerful credential, use Least Privilege,
  RBAC, ABAC, or workload identity before adding vault plumbing.
- Do not treat encrypted source files as the full pattern. They can protect a
  repository from casual reading, but they do not by themselves give runtime
  delivery, audit, rotation, or revocation.
- Do not load secrets into client-side code. Browser and mobile applications
  cannot keep a server credential private once shipped to users.
- Do not add a vault to a one-off local script whose only secret is already
  supplied interactively by a human and never stored.

## 5. Structure

- **Secret producer.** The system or operator that creates the credential.
  Examples include a database issuing a user password, a cloud IAM service
  issuing a role token, or a payment provider issuing a webhook secret.
- **Secret store.** A protected service that stores the value or brokers access
  to a dynamic value. It applies authentication, authorization, encryption at
  rest, versioning, and audit.
- **Access policy.** The rule that maps an authenticated workload identity to a
  permitted secret name and operation.
- **Runtime workload.** The application process that needs the secret. It
  authenticates to the store through a workload identity rather than a copied
  human credential.
- **Delivery adapter.** The sidecar, library, platform mount, or environment
  injection path that makes the value available to the workload.
- **Rotation controller.** The job or store feature that creates a new version,
  updates dependent systems, and retires the old version.
- **Audit sink.** The log or event stream that records who read, wrote,
  rotated, or denied access to the secret.

## 6. ASCII structure diagram

```
+----------------+       +----------------+       +----------------+
| Secret Producer|------>|  Secret Store  |<------| Rotation       |
| DB, IdP, SaaS  | write | vault or cloud | update| Controller     |
+----------------+       +-------+--------+       +----------------+
                                  |
                           policy check
                                  |
                                  v
+----------------+       +-------+--------+       +----------------+
| Runtime        |<------| Delivery       |------>| Audit Sink     |
| Workload       | read  | Adapter        | event | logs, SIEM     |
+----------------+       +----------------+       +----------------+
```

## 7. Dynamics

```
1. Workload starts with a platform identity.
2. Workload asks the secret store for one named secret.
3. Store authenticates the workload identity.
4. Store checks policy for secret name, environment, and operation.
5. Store returns the current version or denies the read.
6. Delivery adapter passes the value to the process without logging it.
7. Audit sink records identity, secret id, version, decision, and time.
8. Rotation controller publishes a new version and retires the old one.
```

The useful runtime property is narrowness. A successful read should explain
which workload read which secret version, not reveal the secret value. A failed
read should be visible enough for operators to fix policy drift without
printing the requested value.

## 8. Implementation variants

**Central vault.** HashiCorp Vault documents a secrets engine model where
clients authenticate and read secrets or dynamic credentials through policies
([HashiCorp Vault documentation](https://developer.hashicorp.com/vault/docs),
verified 2026-08-13). This variant works across clouds and datacenters, but
the vault itself becomes critical infrastructure.

**Cloud managed secret store.** AWS Secrets Manager, Google Secret Manager,
and Azure Key Vault give managed storage, IAM integration, audit events, and
rotation hooks. This variant cuts operating burden, but it couples the
application to cloud IAM and regional availability.

**Platform injection.** Kubernetes Secrets, CSI drivers, environment
variables, and mounted files deliver values to a process. This is easy to
consume, but environment variables and files can be inherited, dumped, or read
by side processes if the host boundary is weak. Kubernetes documents Secrets
as objects for sensitive data such as passwords, tokens, and keys
([Kubernetes Secrets documentation](https://kubernetes.io/docs/concepts/configuration/secret/),
verified 2026-08-13).

**Dynamic credentials.** The store issues a short-lived database user, cloud
token, or certificate on demand. This gives smaller leak windows, but clients
must handle renewal and expiry.

## 9. Known production uses

- Kubernetes has a first-class Secret resource used to hold sensitive data for
  pods, with several delivery paths including mounted volumes and environment
  variables ([Kubernetes Secrets documentation](https://kubernetes.io/docs/concepts/configuration/secret/),
  verified 2026-08-13).
- AWS Secrets Manager is a managed service for storing and rotating secrets,
  including database credentials and API keys
  ([AWS Secrets Manager User Guide](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html),
  verified 2026-08-13).
- HashiCorp Vault is a secrets management system with policy-based access and
  secret engines for static and dynamic secrets
  ([HashiCorp Vault documentation](https://developer.hashicorp.com/vault/docs),
  verified 2026-08-13).

## 10. Consequences

Positive consequences.

- Source code and build artifacts no longer need to carry secret values.
- Rotation becomes a planned workflow instead of a repository-wide search.
- Audit records can tie secret access to workload identity and version.
- A leaked secret can be revoked or scoped without changing unrelated systems.
- Teams can use short-lived credentials where the dependency supports them.

Negative consequences.

- The secret store becomes part of the production critical path.
- Bootstrap identity becomes a hard design question. A workload still needs a
  trustworthy way to prove who it is.
- Local development needs a policy, otherwise developers invent local copies.
- Rotation can break services that cache credentials forever.
- Logs, crash dumps, metrics tags, and traces need redaction discipline.

## 11. Failure modes and misuse

The most common misuse is storing a secret in a vault after it has already
been copied everywhere else. The dashboard says the secret is managed, but the
old value remains in shell history, CI logs, old container layers, and laptops.

A second failure mode is broad policy. If every production workload can read
`prod/*`, the vault is only a different filesystem. The symptom is a breach
where a low-value service exposes credentials for a high-value database.

A third failure mode is non-rotating clients. The store publishes a new
version, but the application reads once at boot and keeps a dead connection
pool. The symptom is a rotation that looks successful from the vault and fails
as soon as the old credential is disabled.

A fourth failure mode is secret value logging. A helper catches an exception
and prints the full configuration object. The symptom is an incident where the
secret store did its job and the observability stack leaked the value.

## 12. Trade-off matrix

| Option | Exposure | Rotation | Operability | Coupling | Best fit |
|---|---|---|---|---|---|
| Secrets Management | Low when policy is narrow | Strong | Medium cost | Store and IAM | Production credentials |
| Encrypted repo file | Medium | Weak | Low cost | Repository tooling | Small teams with manual deploys |
| Plain environment variable | High | Weak | Low cost | Process manager | Local development only |
| Dynamic workload identity | Lowest for supported calls | Strong | Medium cost | Cloud or platform IAM | Cloud-native service calls |
| Manual operator entry | Low at rest | Manual | High human cost | Runbook | Rare break-glass actions |

## 13. Related and incompatible patterns

Least Privilege shapes the policy. A secret should grant the smallest useful
scope rather than broad access that every service can reuse.

Key Rotation is the recurring maintenance behavior. Secrets Management gives
the storage and distribution path, while Key Rotation defines how old material
is replaced.

Envelope Encryption composes when the secret is a data encryption key or when
the store protects application keys with a key-encryption key.

Externalized Configuration is related but separate. Both move values out of
source code, but only Secrets Management treats the value as sensitive.

Hardcoded Secret and Shared Credential are incompatible. They defeat the point
by making the credential durable, copied, and hard to revoke.

## 14. Refactoring path in and out

To introduce the pattern, first inventory credentials by repository, runtime,
owner, dependency, and environment. Second, create one secret name per
application and environment rather than one global name. Third, add workload
identity and the narrowest read policy that lets the application start. Fourth,
replace source and build-time values with runtime reads. Fifth, add redaction
tests for configuration printing and error paths. Sixth, rotate the credential
once as a rehearsal before calling the migration complete.

To remove the pattern, prove that the value is no longer secret, no longer
used, or now supplied by a stronger identity mechanism. Then revoke access,
delete old versions, remove delivery adapters, and delete dead policy. Do not
replace a vault read with a hardcoded value unless the value has been
reclassified as public configuration.

## 15. Testing and verification

Test access policy with positive and negative cases. A workload that should
read `payments/prod/database` should succeed, and a neighboring workload
should fail. Test redaction by forcing configuration and exception paths and
asserting that the value does not appear in logs.

Test rotation in a staging environment using the same delivery path as
production. The useful assertion is not that a new value exists in the store.
The useful assertion is that the application picks it up without failed
requests beyond the planned overlap window.

```typescript
type SecretReader = (name: string) => string;

export function databaseUrl(readSecret: SecretReader): string {
  const password = readSecret("payments/prod/db-password");
  if (password.length < 12) {
    throw new Error("secret version is too short");
  }
  const encoded = encodeURIComponent(password);
  return `payments-db-password-length:${encoded.length}`;
}

const fakeReader: SecretReader = (name) => {
  if (name !== "payments/prod/db-password") throw new Error("denied");
  return "long-local-test-secret";
};

databaseUrl(fakeReader);
```

```python
from typing import Callable


def read_api_key(read_secret: Callable[[str], str]) -> str:
    value = read_secret("billing/prod/provider-key")
    if len(value) < 16:
        raise ValueError("secret version is too short")
    return value


def fake_reader(name: str) -> str:
    if name != "billing/prod/provider-key":
        raise PermissionError("denied")
    return "test-secret-value-123"


assert read_api_key(fake_reader).startswith("test-secret")
```

```go
package main

import "errors"

type SecretReader func(name string) (string, error)

func SigningKey(read SecretReader) (string, error) {
	key, err := read("web/prod/signing-key")
	if err != nil {
		return "", err
	}
	if len(key) < 16 {
		return "", errors.New("secret version is too short")
	}
	return key, nil
}

func main() {
	reader := func(name string) (string, error) {
		if name != "web/prod/signing-key" {
			return "", errors.New("denied")
		}
		return "test-signing-key-123", nil
	}
	_, _ = SigningKey(reader)
}
```

## 16. Observability signals

Log secret reads by secret id, version, workload identity, policy decision,
and latency. Never log the value. A healthy dashboard shows a stable read
rate, low denial rate, and successful rotations inside the planned window.

Failing signals include spikes in denied reads after a deploy, applications
reading old versions after a rotation, repeated reads from unexpected
workloads, secret-store latency rising with request latency, and redaction
tests catching secret-shaped values in logs.

## 17. Security and privacy implications

This pattern directly reduces exposure from source control, build systems,
artifact registries, and broad human access. It does not make the runtime safe
by itself. A compromised process that is allowed to read a secret can still
read it. The gain is narrower access, better audit, shorter lifetime, and a
clear revocation path.

Privacy impact depends on what the secret can reach. A database credential may
grant access to personal data even if the secret itself is only a password. Policies
must be written against the data and operation behind the secret, not only the
secret string.

## 18. References

1. Jerome H. Saltzer and Michael D. Schroeder, "The Protection of Information
   in Computer Systems," Proceedings of the IEEE, volume 63, number 9, 1975.
   https://web.mit.edu/Saltzer/www/publications/protection/
2. OWASP Cheat Sheet Series, "Secrets Management Cheat Sheet."
   https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html,
   verified 2026-08-13.
3. National Institute of Standards and Technology, "Recommendation for Key
   Management. Part 1. General," SP 800-57 Part 1 Revision 5.
   https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final, verified 2026-08-13.
4. Kubernetes Documentation, "Secrets."
   https://kubernetes.io/docs/concepts/configuration/secret/, verified
   2026-08-13.
5. AWS Documentation, "What is AWS Secrets Manager?"
   https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html,
   verified 2026-08-13.
6. HashiCorp Developer Documentation, "Vault documentation."
   https://developer.hashicorp.com/vault/docs, verified 2026-08-13.
