import os, time, requests

AMZ_BASE = {
    "na": "https://advertising-api.amazon.com",
    "eu": "https://advertising-api-eu.amazon.com",
    "fe": "https://advertising-api-fe.amazon.com",
    }[os.getenv("AMZADS_API_REGION","eu")]

REPORTS_VER = "2024-09-01"

def _oauth_token():
    r = requests.post("https://api.amazon.com/auth/o2/token", 
                      data={
                          "grant_type":"refresh_token",
                          "refresh_token":os.environ["AMZADS_REFRESH_TOKEN"],
                          "client_id":os.environ["AMZADS_CLIENT_ID"],
                          "client_secret":os.environ["AMZADS_CLIENT_SECRET"]
                        })
    r.raise_for_status()
    return r.json()["access_token"]

def _headers():
    return {
        "Authorization": f"Bearer {_oauth_token()}",
        "Amazon-Advertising-API-ClientId": os.environ["AMZADS_CLIENT_ID"],
        "Amazon-Advertising-API-Scope": os.environ["AMZADS_SCOPE_PROFILE_ID"]
        }

# Example: request a Sponsored Products daily performance report
def request_sp_report(start_date: str, end_date: str):
    body = {
        "configuration": {
            "adProduct": "SPONSORED_PRODUCTS",
            "groupBy": ["campaign","adGroup","keyword"],
            "columns": ["impressions","clicks","cost","purchases14d","sales14d"],
            "reportType": "PERFORMANCE",
            "timeUnit": "DAILY",
            "startDate": start_date, "endDate": end_date
        }
    }
    r = requests.post(f"{AMZ_BASE}/reports/{REPORTS_VER}/reports", headers={**_headers(),"Content-Type":"application/json"}, json=body)
    r.raise_for_status()
    report_id = r.json()["reportId"]
    for _ in range(60):
        s = requests.get(f"{AMZ_BASE}/reports/{REPORTS_VER}/reports/{report_id}", headers=_headers()).json()
        
        if s.get("status") == "SUCCESS":
            url = s["url"]
            data = requests.get(url).json()
            return data
        time.sleep(2)
        raise RuntimeError("Report polling timeout")
