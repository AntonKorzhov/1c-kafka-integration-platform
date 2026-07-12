CREATE TABLE IF NOT EXISTS ownership_forms (
    id TEXT PRIMARY KEY,
    code TEXT,
    name TEXT NOT NULL,
    source_updated_at TIMESTAMPTZ,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS counterparties (
    id UUID PRIMARY KEY,
    code TEXT,
    name TEXT NOT NULL,
    inn TEXT,
    kpp TEXT,
    ownership_form_id TEXT REFERENCES ownership_forms(id),
    source_updated_at TIMESTAMPTZ,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted BOOLEAN NOT NULL DEFAULT false
);

-- Водяной знак producer: инкрементальная синхронизация не зависит от файлов
-- внутри временного контейнера и переживает его перезапуск.
CREATE TABLE IF NOT EXISTS sync_state (
    resource_name TEXT PRIMARY KEY,
    last_successful_sync_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_counterparties_ownership_form_id
    ON counterparties (ownership_form_id);
