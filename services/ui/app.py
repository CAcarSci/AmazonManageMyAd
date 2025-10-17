import os
import pandas as pd
import psycopg
import requests
import streamlit as st

DB = os.environ["DATABASE_URL"].replace("+psycopg", "")
API = os.getenv("API_BASE", "http://api:8000")

st.set_page_config(page_title="Amazon Ads — Local Control Room", layout="wide")
st.title("Amazon Ads — Local Control Room")


@st.cache_data(ttl=120)
def kpis():
    with psycopg.connect(DB) as conn:
        q = """
        with d as (
            select * from metrics_daily where date >= current_date - interval '30 days'
        )
        select sum(impressions) imps, sum(clicks) clicks, sum(cost) cost,
            sum(sales) sales,
            case when sum(clicks)>0 then sum(cost)/sum(clicks) end as cpc,
            case when sum(sales)>0 then sum(cost)/sum(sales) end as acos
        from d
        """
        return pd.read_sql(q, conn)


m = kpis().iloc[0]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Clicks (30d)", int(m.clicks or 0))
col2.metric("Cost (30d)", f"€{(m.cost or 0):.2f}")
col3.metric("Sales (30d)", f"€{(m.sales or 0):.2f}")
col4.metric("ACOS (30d)", f"{(m.acos or 0)*100:.1f}%")

st.subheader("Entity Leaderboard (30d)")
with psycopg.connect(DB) as conn:
    df = pd.read_sql(
        """
        with agg as (
            select entity_type, entity_id,
                sum(impressions) imps, sum(clicks) clicks, sum(cost) cost, sum(sales) sales
            from metrics_daily
            where date >= current_date - interval '30 days'
            group by 1,2
        )
        select *, case when clicks>0 then cost/clicks end as cpc,
            case when sales>0 then cost/sales end as acos
        from agg
        order by sales desc nulls last
        """,
        conn,
    )
st.dataframe(df, use_container_width=True)

st.divider()
st.subheader("RAG: Category → Best-Seller Keywords")
category_id = st.text_input("Category ID (your naming)", value="socks-bamboo")
question = st.text_area(
    "Question", value="List high-impact keywords and actions for next week."
)
if st.button("Generate Recommendations"):
    r = requests.post(
        f"{API}/rag",
        json={"category_id": category_id, "question": question, "top_k": 12},
    )
    if r.ok:
        out = r.json()
        st.markdown(f"**Summary:** {out['summary']}")
        st.json(out.get("items", []))
    else:
        st.error(r.text)
