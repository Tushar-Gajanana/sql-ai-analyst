# Security model

Treat every model output as untrusted SQL. The model prompt is guidance, not an
access-control mechanism. The strongest boundary is the non-owner PostgreSQL role
with explicit SELECT grants on approved tables and no admin membership.

## Implemented layers
1. Required shared demo password; compared using constant-time comparison.
2. Credentials loaded server-side from environment or Streamlit secrets.
3. Only schema and questions sent to Groq; no result rows, credentials or raw DB errors.
4. Pydantic validates planner JSON; null SQL is a supported clarification response.
5. Explicit human review before execution; guard validation still always runs.
6. SQLGlot AST policy accepts a narrow SELECT subset, explicit analytics tables and
   allowlisted functions. Blocks multi-statements, writable CTEs, SELECT INTO,
   locks, catalog reads, anonymous/custom functions and custom casts.
7. Each query starts a read-only transaction with a 5-second statement timeout,
   1-second lock timeout and `pg_catalog` search path. All user relations are qualified.
8. An outer LIMIT retrieves at most 201 rows; only 200 are displayed/exported.
9. Database errors are sanitized; results are session-local, not shared cached.
10. CSV strings with spreadsheet formula prefixes are escaped before export.

## Boundaries and residual risks
- Read-only does not mean harmless: a SELECT can consume resources. Timeouts and
  row caps help, but a cap does not bound aggregate scans or response byte size.
- The demo schema uses small fields; enforce field sizes and workload isolation
  before connecting large real datasets. Do not expose arbitrary text/blob columns.
- Prompt injection can still influence a permitted query. AST validation does not
  prove semantic correctness or authorization per user.
- The shared password is not SSO, individual authorization, brute-force protection,
  audit logging or a global API budget. A user can reset a session to bypass cooldown.
- Do not grant access to custom executable functions or unsafe views. SQL parser
  behavior and PostgreSQL semantics can differ; test any extension of the SQL subset.
- Schema/question text is sent to an external provider. Review its policies before
  using confidential business names or questions. Synthetic data is the default.
- No generated code is executed, no shell tool is exposed, and no files are uploaded.
- Never use the seeded local passwords on the internet. Do not publish local DB ports.

Before production: add OIDC, per-user authorization and row-level security, centralized
rate limits/spend controls, privacy-reviewed structured audit logs, TLS verification
appropriate to your provider, connection/workload budgets, dependency monitoring and
security review. For an incident rotate API and database secrets and revoke sessions.

Report a vulnerability privately to the repository maintainer. Do not include secrets
or actual personal data in public issues.
