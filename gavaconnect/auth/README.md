# Authentication Design — `gavaconnect` Python SDK

## Introduction

The SDK implements authentication as a **pluggable policy** so each endpoint family (`checkers`, `tax`, `payments`, `authorization`) can use the scheme it requires while sharing a common transport layer. The SDK supports:

- **Basic** (static header from `client_id:client_secret`) for getting the token.
- **Bearer** (OAuth2 Client Credentials) with **concurrency-safe caching**, **early refresh**, and **401-triggered single retry** for making API calls.

Design goals: **credential isolation per resource**, **safe token lifecycle**, **consistent retries/timeouts**, and **extensibility** (e.g., API-Key, HMAC, mTLS) without changing call sites.

---

## High-Level Architecture

- Each resource client is constructed with an **`AuthPolicy`**: `BasicAuthPolicy` or `BearerAuthPolicy(TokenProvider)`.
- The shared **AsyncTransport**:

  - Calls `authorize(request)` before send.
  - On **401**, calls `on_unauthorized()` (Bearer refresh), then **retries once**.
  - Applies **timeouts** and **retry/backoff** for **429/5xx** (honors `Retry-After`).

- Hooks provide **logging** (with redaction) and **OpenTelemetry** spans.

```mermaid
flowchart LR
  A[Your code] -->|calls| R[Resource Client like checkers]
  R -->|build request| T[AsyncTransport]
  T -->|authorize(request)| AP[AuthPolicy<br/>Basic or Bearer]
  AP -->|add Authorization header| T
  T -->|HTTP send| API[Service API]
  API -- 200/2xx --> T
  T -- return --> R --> A

  API -- 401 Unauthorized --> T
  T -->|on_unauthorized called| AP
  AP -->|refresh token for Bearer only| T
  T -->|retry once| API
```

---

## Why Per-Resource Auth?

- **Safety by construction:** Credentials for `payments` cannot be sent to `tax` endpoints (and vice versa). This prevents cross-tenant or scope leakage.
- **Clarity & DX:** The chosen auth scheme is explicit at the resource constructor—no hidden URL regex routing or magic defaults.
- **Heterogeneous schemes:** Some families can remain on **Basic** while others adopt **Bearer** with scopes/rotation, without affecting call sites.
- **Testability:** You can unit-test each resource with its auth policy, mock token refresh, and assert no credential cross-talk.
- **Compliance & least privilege:** Bind the **minimal** credentials/scopes to only the endpoints that require them, simplifying audits and rotation.
