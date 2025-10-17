import os, sys
from datetime import date, timedelta
import requests, time
import psycopg

AMZ_BASE = {
    "na": "https://advertising-api.amazon.com",
    "eu": "https://advertising-api-eu.amazon.com",
    "fe": "https://advertising-api-fe.amazon.com",
    }[os.getenv("AMZADS_API_REGION","eu")]
REPORTS_VER = "2024-09-01"

DATABASE_URL = os.environ["DATABASE_URL"].replace("+psycopg","")

def oauth_token():
    r = requests.post("https://api.amazon.com/auth/o2/token", data={
        "grant_type":"refresh_token",
        "refresh_token":os.environ["AMZADS_REFRESH_TOKEN"],
        "client_id":os.environ["AMZADS_CLIENT_ID"],
        "client_secret":os.environ["AMZADS_CLIENT_SECRET"],
        }
    )
    
    r.raise_for_status()
    return r.json()["access_token"]

def headers():
    return {
        "Authorization": f"Bearer {oauth_token()}",
        "Amazon-Advertising-API-ClientId": os.environ["AMZADS_CLIENT_ID"],
        "Amazon-Advertising-API-Scope": os.environ["AMZADS_SCOPE_PROFILE_ID"],
        "Content-Type":"application/json"
    }

def fetch_daily(day: str):
    body = {
        "configuration":{
        "adProduct":"SPONSORED_PRODUCTS",
        "groupBy":["campaign","adGroup","keyword"],
        "columns":["impressions","clicks","cost","purchases14d","sales14d"],
        "reportType":"PERFORMANCE","timeUnit":"DAILY",
        "startDate":day,"endDate":day
        }
    }
    r = requests.post(f"{AMZ_BASE}/reports/{REPORTS_VER}/reports", headers=headers(), json=body)
    r.raise_for_status()
    rid = r.json()["reportId"]
    for _ in range(60):
        s = requests.get(f"{AMZ_BASE}/reports/{REPORTS_VER}/reports/{rid}", headers=headers()).json()
        if s.get("status") == "SUCCESS":
            url = s["url"]
            data = requests.get(url).json()
            return data
        time.sleep(2)
        raise RuntimeError("Report polling timeout")

def load(rows):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for r in rows:
                et = "keyword" if r.get("keywordId") else ("adGroup" if r.get("adGroupId") else "campaign")
                eid = r.get("keywordId") or r.get("adGroupId") or r.get("campaignId")
                cur.execute(
                    """
                    insert into metrics_daily(date, entity_type, entity_id, impressions, clicks, cost, sales, orders)
                    values (%s,%s,%s,%s,%s,%s,%s,%s)
                    on conflict (date, entity_type, entity_id) do update set
                    impressions=excluded.impressions,
                    clicks=excluded.clicks,
                    cost=excluded.cost,
                    sales=excluded.sales,
                    orders=excluded.orders
                    """,
                (
                    r["date"], et, eid,
                    r.get("impressions",0), r.get("clicks",0), r.get("cost",0.0),
                    r.get("sales14d",0.0), r.get("purchases14d",0)
                ))
        conn.commit()

if __name__ == "__main__":
    day = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    rows = fetch_daily(day)
    load(rows)
    print(f"Ingested {len(rows)} rows for {day}")

