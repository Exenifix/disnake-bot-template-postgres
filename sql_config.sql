CREATE TABLE IF NOT EXISTS migrations
(
    id UUID PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS script_executed
(
    id              SMALLINT PRIMARY KEY,
    script_executed TIMESTAMP NOT NULL
);

INSERT INTO script_executed (id, script_executed)
VALUES (0, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;
