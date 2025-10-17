import os
import psycopg

DB = os.environ["DATABASE_URL"].replace("+psycopg", "")

SQL = """
with z as (
    select ks.*, -- normalize components per category
        (min(search_freq_rank) over (partition by category_id)) as sfr_min,
        (max(search_freq_rank) over (partition by category_id)) as sfr_max,
        (max(click_share) over (partition by category_id)) as cs_max,
        (max(conversion_share) over (partition by category_id)) as conv_max,
        (max(purchases) over (partition by category_id)) as pur_max,
        (max(cvr) over (partition by category_id)) as cvr_max,
        (max(acos) over (partition by category_id)) as acos_max
    from keyword_signals ks
)
select keyword_id,
    category_id,
    search_term,
    0.30 * (case when sfr_max>sfr_min then 1 - ((search_freq_rank - sfr_min)::float/(sfr_max - sfr_min)) else 0.0 end) +
    0.20 * coalesce(click_share/cs_max,0) +
    0.15 * coalesce(conversion_share/conv_max,0) +
    0.20 * coalesce(purchases/pur_max,0) +
    0.15 * coalesce(cvr/cvr_max,0) -
    0.15 * coalesce(acos/acos_max,0) as score
from z;
"""

if __name__ == "__main__":
    with psycopg.connect(DB, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("drop table if exists keyword_scores")
            cur.execute("create table keyword_scores as " + SQL)
            cur.execute("create index on keyword_scores(category_id, score desc)")
    print("keyword_scores refreshed")
