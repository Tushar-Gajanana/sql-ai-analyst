# Testing and evaluation

## Automated checks
```bash
python -m pip install -r requirements-dev.txt
ruff check .
pytest -q
```
Without PostgreSQL configuration the integration tests skip explicitly. Unit tests
exercise accepted analytics queries, unsafe SQL forms and mocked Groq requests.
No real Groq key or paid API request is required for automated tests.

For real PostgreSQL tests, start the provided Docker database then run:
```bash
export TEST_DATABASE_URL='postgresql://analyst:local-demo-only@localhost:5432/retail'
pytest -q
```
PowerShell equivalent: `$env:TEST_DATABASE_URL="postgresql://analyst:local-demo-only@localhost:5432/retail"`.
The GitHub workflow initializes PostgreSQL 16 and runs the same integration suite,
including direct write denial outside the application guard.

## Manual end-to-end acceptance
1. Set real Groq and database secrets; launch `streamlit run app.py`.
2. Verify incorrect password rejection and successful correct-password login.
3. Ask “How many sales records are there?” Review then execute; expect 1,080.
4. Ask category revenue for March 2025 and compare results with this trusted SQL:
```sql
SELECT p.category,
 ROUND(SUM(s.quantity*p.unit_price*(1-s.discount_pct/100.0)),2) AS revenue
FROM analytics.sales s JOIN analytics.products p USING(product_id)
WHERE s.sale_date >= DATE '2025-03-01' AND s.sale_date < DATE '2025-04-01'
GROUP BY p.category ORDER BY revenue DESC;
```
5. Ask an ambiguous question (“What is our performance?”). Expect a clarification
   or review the assumptions carefully; LLM behavior is nondeterministic.
6. Ask for customer passwords or deletion of all sales. Expect refusal; any SQL
   must still pass validation. Run direct adversarial guard cases with pytest.
7. Ask for all sales; expect 200 displayed rows and a truncation warning.
8. Export CSV; verify headers and rows. Clear the session and verify reauthentication.
9. Test invalid Groq key, unreachable database and unavailable model; verify safe UI errors.

## Measuring model quality for your portfolio
Build a separate benchmark of 20–30 answerable business questions plus unanswerable
and malicious requests. Store trusted SQL and expected aggregates. Record:
- Result equivalence versus trusted SQL (primary metric, not string similarity).
- Query execution success, clarification correctness and unsafe-query rejection.
- End-to-end latency, provider errors and token usage from provider console.
- Manual review of joins, date boundaries and definitions.
Do not claim a quality score until measured. Changing model, prompt or parser requires
re-running the benchmark. The included tests validate plumbing and policy, not broad
natural-language accuracy or a complete security proof.
