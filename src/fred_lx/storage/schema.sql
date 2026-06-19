-- Canonical store for Treasury par yield data. One row per
-- (curve_date, maturity_code, source); re-ingesting the same date/source
-- overwrites the prior values via the upsert in postgres_store.py.
CREATE TABLE IF NOT EXISTS treasury_par_yields (
    curve_date      DATE NOT NULL,
    maturity_code   TEXT NOT NULL,
    maturity_years  NUMERIC NOT NULL,
    par_yield       NUMERIC,
    source          TEXT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (curve_date, maturity_code, source)
);
