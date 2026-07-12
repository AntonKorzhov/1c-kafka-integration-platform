-- Выполнять после синхронизации: docker compose exec -T postgres psql -U integration -d integration < sql/checks.sql

SELECT 'ownership_forms' AS entity, count(*) AS total, count(*) FILTER (WHERE deleted) AS deleted
FROM ownership_forms
UNION ALL
SELECT 'counterparties', count(*), count(*) FILTER (WHERE deleted)
FROM counterparties;

SELECT c.id, c.code, c.name, c.inn, c.kpp, c.ownership_form_id, f.name AS ownership_form,
       c.deleted, c.source_updated_at, c.imported_at
FROM counterparties AS c
LEFT JOIN ownership_forms AS f ON f.id = c.ownership_form_id
ORDER BY c.code;

SELECT resource_name, last_successful_sync_at, updated_at
FROM sync_state
ORDER BY resource_name;
