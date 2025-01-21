import streamlit as st
import redis
import json
import pandas as pd
import time
import os
from dotenv import load_dotenv 

load_dotenv()

def fetch_data_from_redis():
    try:
        client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))
        
        client.ping()

        raw_data = client.get(os.getenv("REDIS_KEY"))
        
        if raw_data:
            return json.loads(raw_data)
        else:
            return None
    except Exception as e:
        st.error(f"Error connecting to Redis: {e}")
        return None

st.title("Dashboard")

placeholder = st.empty()

while True:
    data = fetch_data_from_redis()

    if data:
        timestamp = data.get("timestamp", "N/A")
        percent_network_egress = data.get("percent-network-egress", 0)
        percent_memory_caching = data.get("percent-memory-caching", 0)
        cpus_avg = data.get("cpus_avg", {})

        with placeholder.container():
            st.subheader("Metrics")
            st.metric(label="percent_network_egress", value=f"{percent_network_egress:.2f} %")
            st.metric(label="percent_memory_caching", value=f"{percent_memory_caching:.2f} %")
            st.write(f"last_update: {timestamp}")

            st.subheader("Average CPU Usage")
            cpu_df = pd.DataFrame.from_dict(cpus_avg, orient="index", columns=["avg (%)"])
            cpu_df.index.name = "CPU"
            st.dataframe(cpu_df)

            st.subheader("Plots")
            st.bar_chart(cpu_df)

    else:
        st.warning("No data found.")

    time.sleep(5)
