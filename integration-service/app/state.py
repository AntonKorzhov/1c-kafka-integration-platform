from datetime import datetime

import psycopg

from .common import postgres_kwargs


def get_watermark(resource_name: str) -> datetime | None:
    with psycopg.connect(**postgres_kwargs()) as conn, conn.cursor() as cur:
        cur.execute("SELECT last_successful_sync_at FROM sync_state WHERE resource_name = %s", (resource_name,))
        row = cur.fetchone()
        return row[0] if row else None


def save_watermark(resource_name: str, value: datetime) -> None:
    with psycopg.connect(**postgres_kwargs()) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sync_state(resource_name, last_successful_sync_at)
            VALUES (%s, %s)
            ON CONFLICT (resource_name) DO UPDATE
              SET last_successful_sync_at = EXCLUDED.last_successful_sync_at,
                  updated_at = now()
            """,
            (resource_name, value),
        )
