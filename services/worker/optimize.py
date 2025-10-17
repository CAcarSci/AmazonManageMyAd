import os
import psycopg

DB = os.environ["DATABASE_URL"].replace("+psycopg", "")
TARGET_ACOS = float(os.getenv("DEFAULT_TARGET_ACOS", "0.25"))
MIN_CLICKS = int(os.getenv("MIN_CLICKS_FOR_DECISION", "10"))
MIN_SPEND = float(os.getenv("MIN_SPEND_FOR_DOWNSIZE", "3.0"))

SQL = """
with agg as (
    select entity_type, entity_id,
        sum(clicks) clicks, sum(cost) cost, sum(sales) sales
    from metrics_daily
    where date >= current_date - interval '14 days'
    group by 1,2
)
select entity_type, entity_id, clicks, cost, sales,
    case when sales>0 then cost/sales end as acos
from agg
"""


def recommend(rows):
    out = []
    for et, eid, clicks, cost, sales, acos in rows:
        if clicks is None or clicks < MIN_CLICKS:
            continue
        if sales is None or sales == 0:
            if cost and cost > MIN_SPEND:
                out.append(
                    {
                        "entity_type": et,
                        "entity_id": eid,
                        "action": "decrease",
                        "percent": 0.15,
                        "reason": "No sales 14d",
                    }
                )
            continue
        if acos and acos > TARGET_ACOS:
            delta = max(0.10, min(0.25, (acos / TARGET_ACOS - 1) / 2))
            out.append(
                {
                    "entity_type": et,
                    "entity_id": eid,
                    "action": "decrease",
                    "percent": round(delta, 2),
                    "reason": f"High ACOS {acos:.2f}",
                }
            )
        elif acos and acos < TARGET_ACOS * 0.7 and sales > 0:
            out.append(
                {
                    "entity_type": et,
                    "entity_id": eid,
                    "action": "increase",
                    "percent": 0.10,
                    "reason": f"Efficient {acos:.2f}",
                }
            )
    return out


if __name__ == "__main__":
    with psycopg.connect(DB) as conn:
        with conn.cursor() as cur:
            cur.execute(SQL)
            changes = recommend(cur.fetchall())
    print(changes)
