from __future__ import annotations

import json
import time

import requests
import streamlit as st


st.set_page_config(page_title="Workflow Metrics", layout="wide")
st.title("Workflow Dispatcher Metrics")

dispatcher_url = st.sidebar.text_input("Dispatcher URL", value="http://localhost:8000")
poll_interval = st.sidebar.slider("Poll interval (sec)", 1, 30, 3)

placeholder = st.empty()

while True:
    try:
        resp = requests.get(f"{dispatcher_url}/metrics", timeout=5)
        data = resp.json()
        with placeholder.container():
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Queued", data.get("queued", 0))
            col2.metric("Running", data.get("running", 0))
            col3.metric("Completed", data.get("completed", 0))
            col4.metric("Failed", data.get("failed", 0))
            st.json(data)
    except Exception as e:
        with placeholder.container():
            st.error(f"Error polling metrics: {e}")
    time.sleep(poll_interval)

