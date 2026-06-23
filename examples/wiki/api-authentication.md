---
title: API Authentication
type: topic
status: example
tags:
  - api
  - security
  - authentication
---

# API Authentication

## Summary

This example page represents a neutral internal wiki topic about moving from API keys to OAuth clients.

## Source-Backed Claims

- API keys are simple to distribute but are hard to scope and rotate safely.
- OAuth clients can support scoped access, expiration, and centralized revocation.

## Open Questions

- Which systems still require API key compatibility?
- Who owns token rotation and incident response?
- What logs prove that deprecated credentials are no longer used?

## Related Pages

- [[incident-response]]
- [[coding-style]]
