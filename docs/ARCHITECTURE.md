# Architecture (V0.1)

## Logical components

```
Web / Desktop clients ── Matrix Client API ── Synapse ── PostgreSQL
         │                                      │
         └── Platform API ── Agent Gateway ── Matrix Application Service
                   │               │
             Git Document     External Agent Runtime(s)
                 Service
                   │
               Git repos
```

## Ownership
- Matrix is authoritative for rooms, messaging and membership.
- Git is authoritative for Markdown content and version history.
- Platform metadata DB stores tasks, agent registration, grants, audit and task retry records.
- The local Git document spike stores document notification intent in commit metadata and notification receipts in local Git refs. See `GIT_DOCUMENTS.md`.
- Runtime owns model state and execution environment.

## Protocol guardrails
- App Service is an integration adapter, not a server-side event interception mechanism.
- Reject encrypted rooms for MVP agent context, pending E2EE permissions design.
- Task state survives gateway restart; inbound Matrix transaction IDs and event IDs must be deduplicated.
- Resource grants are server-validated references, never self-asserted permission.
- Git writes must compare versions, coordinate across processes and never force-push.

## Next spikes
1. Confirm Synapse + App Service event delivery, retry and identity namespaces.
2. Multi-process/remote-ref conflict, crash recovery and path / symlink hardening.
3. Custom Matrix event compatibility with a standard Matrix client.
