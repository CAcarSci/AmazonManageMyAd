-- Dimensions
create table
    if not exists profiles (
        profile_id bigint primary key,
        country varchar(2),
        currency varchar(8)
    );

create table
    if not exists campaigns (
        campaign_id bigint primary key,
        name text,
        type text,
        state text,
        daily_budget numeric,
        portfolio_id bigint,
        created_at timestamptz
    );

create table
    if not exists keywords (
        keyword_id bigint primary key,
        campaign_id bigint references campaigns (campaign_id),
        ad_group_id bigint,
        match_type text,
        state text,
        bid numeric
    );

create table
    if not exists targets (
        target_id bigint primary key,
        campaign_id bigint references campaigns (campaign_id),
        ad_group_id bigint,
        expression jsonb,
        state text,
        bid numeric
    );

create table
    if not exists categories (category_id text primary key, name text);

-- Facts
create table
    if not exists metrics_daily (
        date date,
        entity_type text,
        entity_id bigint,
        impressions bigint,
        clicks bigint,
        cost numeric,
        sales numeric,
        orders bigint,
        primary key (date, entity_type, entity_id)
    );

create table
    if not exists search_terms (
        date date,
        campaign_id bigint,
        ad_group_id bigint,
        source_entity_type text,
        source_entity_id bigint,
        query text,
        clicks int,
        cost numeric,
        sales numeric,
        orders int
    );

-- Keyword signals for RAG ranking (BA/SQP/Ads)
create table
    if not exists keyword_signals (
        keyword_id bigserial primary key,
        category_id text references categories (category_id),
        search_term text,
        period text, -- WEEK | MONTH | QUARTER | DAY
        source text, -- BA_TopSearch | SQP | ADS_V3
        search_freq_rank bigint,
        search_volume bigint,
        click_share numeric,
        conversion_share numeric,
        impressions bigint,
        clicks bigint,
        cart_adds bigint,
        purchases bigint,
        acos numeric,
        cpc numeric,
        ctr numeric,
        cvr numeric,
        top_clicked_asins jsonb,
        asof_date date not null
    );