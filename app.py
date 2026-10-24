import hmac
import os
import time
import httpx
import pandas as pd
import psycopg
import streamlit as st
from dotenv import load_dotenv
from pydantic import ValidationError
from analyst.config import Settings
from analyst.db import query
from analyst.guard import UnsafeSQL
from analyst.llm import generate
from analyst.schema import SCHEMA

load_dotenv()
st.set_page_config(page_title="AI Data Analyst", page_icon="📊", layout="wide")
try:
    for key in ("DATABASE_URL", "GROQ_API_KEY", "GROQ_MODEL", "APP_PASSWORD"):
        if key in st.secrets:
            os.environ[key] = str(st.secrets[key])
except FileNotFoundError:
    pass
st.title("📊 Chat with SQL — AI Data Analyst")
st.caption("Groq + PostgreSQL · synthetic retail analytics · review SQL before running")
password = os.getenv("APP_PASSWORD", "")
if not password:
    st.error("Set APP_PASSWORD before starting the application.")
    st.stop()
if not st.session_state.get("authenticated"):
    entered = st.text_input("Demo access password", type="password")
    if st.button("Sign in"):
        if hmac.compare_digest(entered, password):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()
try:
    settings = Settings.from_env()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
if "history" not in st.session_state:
    st.session_state.history = []
with st.sidebar:
    st.header("Dataset & controls")
    st.code(SCHEMA)
    st.info("Only questions and schema go to Groq. Query results stay in the app.")
    st.write("Try: Which category generated the most revenue in March 2025?")
    st.write("Try: Show monthly units sold by region.")
    if st.button("Clear session"):
        st.session_state.clear()
        st.rerun()
for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        st.write(item["explanation"])
        if item.get("sql"):
            st.code(item["sql"], language="sql")
        if "result" in item:
            result = item["result"]
            df = pd.DataFrame(result["rows"], columns=result["columns"])
            st.dataframe(df, hide_index=True, use_container_width=True)
            st.caption(f"Returned {len(df)} rows. " +
                       ("Result capped; add filters or aggregate." if result["truncated"] else ""))
            # Escape formula prefixes for safer spreadsheet export.
            export = df.map(lambda v: "'" + v if isinstance(v, str) and
                            v.startswith(("=", "+", "-", "@", "\t", "\r")) else v)
            st.download_button("Download CSV", export.to_csv(index=False),
                               "query-results.csv", "text/csv", key=f"csv-{item['id']}")
            if len(df.columns) >= 2:
                numeric = [c for c in df.columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
                if numeric and not df.empty:
                    st.bar_chart(df.set_index(df.columns[0])[numeric[:1]])
        if item.get("error"):
            st.warning(item["error"])
question = st.chat_input("Ask about retail sales", max_chars=2000,
                         disabled=bool(st.session_state.get("pending")))
if question:
    if time.monotonic() - st.session_state.get("last_request", 0) < 5:
        st.warning("Wait five seconds between requests.")
    else:
        st.session_state.last_request = time.monotonic()
        try:
            with st.spinner("Preparing SQL…"):
                plan = generate(settings, question, st.session_state.history)
            item = {"id": time.time_ns(), "question": question, **plan.model_dump()}
            st.session_state.history.append(item)
            st.session_state.history = st.session_state.history[-20:]
            st.session_state.pending = item["id"] if plan.sql else None
            st.rerun()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            st.error(f"Groq API returned HTTP {status}.")

            guidance = {
                400: "Groq rejected the request. Check model and request parameters.",
                401: "Invalid Groq API key. Check GROQ_API_KEY.",
                403: "Your account does not have permission to use this resource.",
                404: "The requested model or endpoint was not found.",
                429: "Rate limit or quota reached. Check your Groq console.",
            }
            st.warning(
                guidance.get(status, "Check Groq service status and try again.")
            )

        except httpx.RequestError:
            st.error(
                "Cannot connect to Groq. Check your internet connection, "
                "VPN, firewall, or proxy."
            )

        except ValidationError as exc:
            st.error("Groq responded, but its SQL plan had an invalid format.")
            st.json([
                {
                    "field": ".".join(str(part) for part in error["loc"]),
                    "issue": error["type"],
                }
                for error in exc.errors()
            ])

        except (ValueError, KeyError, IndexError):
            st.error(
                "Groq returned an unexpected response. "
                "Try: How many sales records are there?"
            )
if st.session_state.get("pending"):
    item = next(i for i in st.session_state.history if i["id"] == st.session_state.pending)
    st.info("Review the SQL above, then execute it or discard it.")
    run, cancel = st.columns(2)
    if run.button("Run approved query", type="primary"):
        try:
            item["result"] = query(settings.database_url, item["sql"])
        except UnsafeSQL as exc:
            item["error"] = f"SQL rejected: {exc}"
        except psycopg.Error:
            item["error"] = "Database query failed. Check connection, permissions, column names or timeout."
        finally:
            st.session_state.pending = None
        st.rerun()
    if cancel.button("Discard query"):
        st.session_state.pending = None
        st.rerun()
