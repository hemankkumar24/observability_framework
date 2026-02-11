import streamlit as st
import sqlite3
import pandas as pd
from graph import run_graph
from db import init_db
import json
import re

init_db()

st.set_page_config(page_title="Bridge-it Copilot", layout="wide")

st.title("Bridge-it AI Copilot")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_trace_id" not in st.session_state:
    st.session_state.last_trace_id = None

col_chat, col_obs = st.columns([3, 1])


with col_chat:
    chat_container = st.container(height=500, border=True)

    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    user_input = st.chat_input("Ask something...")

    if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        result, trace_id = run_graph(user_input)

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["response"]
        })

        st.session_state.last_result = result
        st.session_state.last_trace_id = trace_id

        st.rerun()


with col_obs:
    obs_container = st.container(height=500, border=True)

    with obs_container:
        st.subheader("Observability")

        conn = sqlite3.connect("observability.db")
        total_requests = pd.read_sql_query("SELECT COUNT(DISTINCT trace_id) as c FROM traces", conn)["c"][0]
        avg_latency = pd.read_sql_query("SELECT AVG(latency) as l FROM traces", conn)["l"][0]
        failure_rate = pd.read_sql_query("SELECT AVG(1 - success) as f FROM traces", conn)["f"][0]
        conn.close()

        st.metric("Total Requests", total_requests)
        st.metric("Avg Latency", round(avg_latency or 0, 4))
        st.metric("Failure Rate", round(failure_rate or 0, 3))

        st.divider()

        if st.session_state.last_result:

            result = st.session_state.last_result
            trace_id = st.session_state.last_trace_id

            used_retrieval = len(result.get("docs", [])) > 0
            st.metric("Retrieval Used", "Yes" if used_retrieval else "No")

            evaluation_raw = result.get("evaluation", "")

            def extract_json(text):
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    return match.group(0)
                return None

            json_block = extract_json(evaluation_raw)

            try:
                evaluation_json = json.loads(json_block)
                quality = float(evaluation_json.get("quality", 0))
                confidence = float(evaluation_json.get("confidence", 0))
                reason = evaluation_json.get("reason", "")
            except:
                quality = 0
                confidence = 0
                reason = "Evaluation parsing failed."

            st.metric("Quality", quality)
            st.metric("Confidence", confidence)

            with st.expander("Evaluation Reasoning"):
                st.write(reason)

            st.code(f"Trace ID: {trace_id}")

            st.divider()

            conn = sqlite3.connect("observability.db")
            df_trace = pd.read_sql_query(
                "SELECT * FROM traces WHERE trace_id = ?",
                conn,
                params=(trace_id,)
            )
            conn.close()

            st.subheader("Execution Trace (Current Request)")
            st.dataframe(df_trace, use_container_width=True)

        else:
            st.info("No conversation yet.")


st.divider()

st.subheader("All System Traces")

conn = sqlite3.connect("observability.db")
df_all = pd.read_sql_query("SELECT * FROM traces", conn)
conn.close()

st.dataframe(df_all, use_container_width=True)
