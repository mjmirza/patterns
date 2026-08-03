<!-- freshness: frozen -->

# Security policy

This is a documentation catalogue: markdown pattern entries plus small,
non-networked code samples used to prove a pattern compiles. There is no
running service and no user data. Security reports here are almost always
about one of two things.

## What counts as a security concern

- A code sample in a published entry that demonstrates or normalizes an
  insecure practice (for example a hardcoded secret, a SQL string built by
  concatenation, disabled TLS verification) presented as if it were the
  recommended way to build the pattern.
- A citation or automation script (`tools/*.py`, `.github/workflows/*.yml`)
  that could be abused to run untrusted code or leak a token.

## How to report

Do not open a public issue for a live exploit or a token leak. Use GitHub's
private vulnerability reporting for this repository (Security tab, "Report a
vulnerability"), or use the `security-concern` issue template for anything
that does not need to stay private (for example, an insecure code sample in
an entry).

## Response

A maintainer acknowledges a private report within a reasonable time and, once
confirmed, ships a fix as a normal pull request through the same branch, PR,
CI-green, squash-merge workflow as any other change. Credit is given in the
fixing commit unless the reporter asks to stay anonymous.
