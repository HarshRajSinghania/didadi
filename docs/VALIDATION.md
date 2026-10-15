# Technical Risk Validation — 2026-10-14

## R1 — Matrix Application Service / client
**Status: spec validated, runtime not tested.** Matrix AS registration defines identity namespaces and a push transaction endpoint; retries reuse txn IDs. The AS may observe and inject events but cannot block or rewrite existing events. Design: AS transaction handler must durably commit incoming txn/event IDs and enqueue tasks before 200 ACK; processing each event idempotently prevents duplicate dispatch. Restrict service scopes, avoid catch-all namespaces. Standard m.room.message fallback preserves reading in regular clients, with custom namespaced events for optional task metadata.

Sources: https://spec.matrix.org/latest/application-service-api/ ; https://github.com/matrix-org/matrix-js-sdk ; https://github.com/element-hq/element-web

**UI decision:** build a slim React + matrix-js-sdk client for MVP; Element Web is dual/open/commercial licensed as documented, but a fork adds significant upstream maintenance. Do not treat this as benchmarked effort comparison.

## R2 — Git single source of truth
**Status: local proof passed, production not proven.** 4 Python unittest cases passed: create/version read, stale-write rejected, competing threads only one wins, path traversal blocked. Current lock is process-local. A production writer must implement per-repository cross-process serialization, external update handling, ref lock/remote CAS, push retry, durable outbox, immutable revision reference, authentication and authorization, sandboxed Git operations and symlink race mitigations. Content-addressable blob SHA checks do not by themselves guarantee a stable document identity or safe concurrent Git index access.

## R3 — E2EE + agents
**Status: deliberately out of MVP.** Only explicitly authorized, unencrypted collaboration rooms can be used with Agent AS. Encrypted room events are not plaintext accessible by an application service; future agent E2EE integration requires dedicated crypto-capable client identities, explicit key disclosure and trust design. Never silently downgrade a room.

## Decision gate before Phase 1
- Deploy real Synapse + PostgreSQL + AS container.
- Send one Matrix message and confirm exactly one durable Task even after replaying transaction and restarting AS.
- Test agent response represented as `m.room.message` with safe fallback and namespaced metadata.
- Run Git tests with two worker processes and externally updated remote branch.
- Verify E2EE rooms are rejected for agent tasks with clear UI feedback.

**No claims of end-to-end Matrix validation or production readiness are made.**


## Issue #1 implementation — 2026-10-15 (Asia/Shanghai)

Implemented Compose initialization, PostgreSQL persistence, Synapse registration, a scoped synchronous AS echo fixture, and a real Matrix smoke-test job. Exact commands and permission boundaries: [MATRIX_QUICKSTART.md](MATRIX_QUICKSTART.md).

Local evidence: `python -m unittest discover -s tests -v` passed **10 tests** (4 existing Git tests, 6 Matrix/configuration tests). `git diff --check` passed. Tests cover token rejection, retryable failure ACK, stable reply transaction IDs, invitation handling, filtering and fail-closed encryption-state lookup. These are unit/HTTP fixture tests, not evidence of a real Synapse deployment.

The editing environment has no Docker executable/daemon; real runtime validation was performed on GitHub Actions Ubuntu instead. **PASS**: [run 38664316060](https://github.com/douyixuan/didadi/actions/runs/38664316060), implementation commit `c4555f0764f699b75f21e4e59639f60df48f6517`, 2026-10-15 (Asia/Shanghai). Both jobs passed: 10 unit tests and the real Matrix integration job.

Runtime evidence: Compose configuration and image pulls succeeded; Synapse, PostgreSQL and AS became healthy; unauthenticated AS traffic was rejected; out-of-namespace human impersonation was rejected; Alice/Bob exchanged messages in both directions via `/sync`; AS received the trigger and replied as the managed echo identity; replay yielded one reply. Containers were removed and recreated while retaining volumes; both original user tokens could read the original room message; a second complete smoke run passed.

Two failures found during real CI were fixed before this passing run: initialize Synapse data volume ownership as 991:991, and permit the smoke fixture to persist its restart-check credentials. No runtime validation is claimed for macOS/ARM, production deployment, or long-outage exactly-once behavior. The Phase 1 durable task and Git concurrency gates above remain outstanding and are deliberately outside this change.
