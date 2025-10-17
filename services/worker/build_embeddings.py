import os, json
import psycopg
import requests

DB = os.environ["DATABASE_URL"].replace("+psycopg","")
OLLAMA = os.getenv("OLLAMA_BASE","http://ollama:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL","nomic-embed-text")

TEMPLATE = (
    "Category: {category}\n"
    "Keyword: {kw}\n"
    "Signals: SFR={sfr}, ClickShare={cs}, ConvShare={conv}, Purchases={p}, CTR={ctr}, CVR={cvr}, CPC={cpc}, ACOS={acos}\n"
    "TopASINs: {asins}\n"
)

def embed(txt: str):
    r = requests.post(f"{OLLAMA}/api/embeddings", json={"model": EMBED_MODEL, "prompt": txt}, timeout=60)
    r.raise_for_status()
    return r.json()["embedding"]

if __name__ == "__main__":
    with psycopg.connect(DB, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("select category_id, name from categories")
            cats = {cid: name for cid, name in cur.fetchall()}
            cur.execute("""
                select ks.keyword_id, ks.category_id, ks.search_term, ks.search_freq_rank, ks.click_share,
                    ks.conversion_share, ks.purchases, ks.ctr, ks.cvr, ks.cpc, ks.acos, ks.top_clicked_asins
                from keyword_signals ks
                join (
                    select category_id, search_term
                    from keyword_scores
                    qualify row_number() over (partition by category_id order by score desc) <= 200
                ) s using (category_id, search_term)
            """)
            rows = cur.fetchall()
            for (kid, cid, kw, sfr, cs, conv, p, ctr, cvr, cpc, acos, asins) in rows:
                chunk = TEMPLATE.format(category=cats.get(cid,cid), kw=kw, sfr=sfr, cs=cs, conv=conv, p=p, ctr=ctr, cvr=cvr, cpc=cpc, acos=acos, asins=json.dumps(asins)[:200])
                vec = embed(chunk)
                cur.execute("""
                    insert into keyword_chunks(category_id, chunk, meta, embedding)
                    values (%s,%s,%s,%s)
                    on conflict do nothing
                """, (cid, chunk, {"keyword_id": kid, "search_term": kw}, vec))
    print("Embeddings built/updated")
