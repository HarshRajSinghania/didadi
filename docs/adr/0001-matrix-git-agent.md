# ADR 0001: Matrix, Git and external agents

Status: Accepted for MVP design (2026-10-15)

- Use Matrix protocol with an unmodified Synapse homeserver.
- Use a dedicated Matrix Application Service / Agent Gateway for managed agent actors.
- Treat Git as the only source of truth for Markdown files.
- Let external runtimes own agent execution; the gateway owns dispatch/identity and audit.
- Target developers and agent builders before general-purpose consumer use.

Consequences: client extensions need their own UX; Git conflicts are first-class; no E2EE agent auto-access in MVP; agent operations have separate scoped authorization.
