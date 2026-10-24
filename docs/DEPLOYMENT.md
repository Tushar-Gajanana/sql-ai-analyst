# GitHub and free-tier deployment

Recommended portfolio path: **GitHub + Streamlit Community Cloud + Neon PostgreSQL
+ Groq free-plan access**. Eligibility and quotas can change; review the linked
provider pages before enabling billing. No paid server is required for a small demo.
The project includes deployment instructions, not provisioned external accounts.

## 1. Push the project to GitHub
Create an empty repository named `sql-ai-analyst` at https://github.com/new.
Do not initialize its README if pushing this existing folder. Run inside this folder:
```bash
git init
git add .
git status
# Verify .env and .streamlit/secrets.toml are NOT staged.
git commit -m "Build Groq PostgreSQL AI data analyst"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sql-ai-analyst.git
git push -u origin main
```
GitHub may ask you to authenticate using its supported credential flow. Never paste
API keys into Git commits, issue descriptions, screenshots or README examples.

## 2. Create Neon PostgreSQL
1. Create a free project at https://neon.com. Select a region near the application.
2. Use the Neon SQL Editor as the owner to execute `sql/001_demo.sql`.
3. Execute the following once, replacing the password with a unique random secret.
   Use a dedicated demo database; schema privilege changes may affect other applications.
```sql
CREATE ROLE analyst LOGIN PASSWORD 'REPLACE_WITH_RANDOM_SECRET'
 NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA analytics FROM PUBLIC;
GRANT USAGE ON SCHEMA analytics TO analyst;
GRANT SELECT ON analytics.products, analytics.sales TO analyst;
ALTER ROLE analyst SET default_transaction_read_only = on;
ALTER ROLE analyst SET statement_timeout = '5s';
ALTER ROLE analyst SET search_path = pg_catalog;
```
4. Obtain the connection URI for **analyst**, never the owner, from Neon Connect.
   If assembling a URI, percent-encode special characters in the password.
   Keep `sslmode=require` and any provider-supplied TLS parameters.
   A pooled URI works for short transactions; a direct URI works for this small demo too.
5. Verify with `TEST_DATABASE_URL` and the integration suite before deploying.
   The test role must have no membership in owner/admin roles.

## 3. Deploy Streamlit
1. Visit https://share.streamlit.io and connect the GitHub repository.
2. Choose branch `main`, entry point `app.py`, and Python **3.11** in advanced settings.
3. Paste these TOML secrets into Advanced settings → Secrets:
```toml
GROQ_API_KEY = "YOUR_GROQ_KEY"
GROQ_MODEL = "llama-3.3-70b-versatile"
DATABASE_URL = "postgresql://analyst:ENCODED_PASSWORD@YOUR_HOST/neondb?sslmode=require"
APP_PASSWORD = "YOUR_LONG_RANDOM_DEMO_PASSWORD"
```
4. Deploy. Community Cloud installs root `requirements.txt`; no Docker is needed there.
5. Open the resulting `https://YOUR_APP.streamlit.app` URL, authenticate and ask
   “How many sales records are there?” Approve SQL; expect 1,080.
6. Check GitHub Actions: all unit and PostgreSQL integration tests must pass.
7. Share the demo password privately with reviewers; keep only synthetic data online.

## Free-plan expectations
Neon offers a free PostgreSQL plan. Streamlit Community Cloud provides community app
hosting. Groq free-plan requests are rate-limited by model and organization; read
https://console.groq.com/docs/rate-limits and your account limits. This design uses
one model request per question, no result-summarization request. Free quotas, sleep,
account requirements and model availability can change. No unlimited-usage promise.
GitHub Pages cannot host this Python application or hold its server secrets.

## Troubleshooting
- Connection refused locally: start Docker; check `docker compose ps` and port 5432.
- Authentication failure: verify role, password encoding and database name. Local
  Docker credentials differ from Neon credentials.
- Permission denied: grant only schema USAGE and SELECT on the two approved tables.
- Missing table: run the demo initialization against the correct database.
- Groq error: verify key, selected model access and quota. Wait after rate limits;
  no automatic retry loop is used to avoid request storms.
- Query rejected: simplify the question; the guard deliberately supports limited SQL.
- SQL execution failure: check proposed identifiers against the sidebar schema.
- Blank chart: numeric charts appear only when results have suitable numeric columns.
- Secrets missing: configure host secrets and reboot the app; never commit secrets.
