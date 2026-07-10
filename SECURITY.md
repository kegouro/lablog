# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.3.x   | ✅ |
| 0.2.x   | Security fixes on a best-effort basis |
| < 0.2   | ❌ |

## Scope

lablog is primarily a **local-first** scientific notebook (localhost API + browser UI).
That still implies:

- Untrusted LaTeX / cell source must not break out of intended sandboxes.
- Vault paths and download filenames must stay under configured roots.
- Export HTML must not inject unescaped user content (XSS).
- Soft-deleted pages must reject writes.

## Reporting a vulnerability

Please report security issues **privately**:

1. Email the maintainer via the GitHub profile linked on the repository, **or**
2. Use GitHub **Security Advisories** → “Report a vulnerability” on this repo.

Include:

- Affected version / commit
- Reproduction steps (minimal)
- Impact assessment (confidentiality / integrity / availability)

We aim to acknowledge within **7 days** and ship a fix or mitigation as soon as
practical. Please allow a reasonable window before public disclosure.

## Non-security bugs

Use normal GitHub Issues for crashes, UX bugs, and feature requests.
