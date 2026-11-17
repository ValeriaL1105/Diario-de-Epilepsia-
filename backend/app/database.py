"""Conexión a PostgreSQL en Supabase; un acceso transaccional por solicitud."""
from collections.abc import Generator
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi import HTTPException
from psycopg.rows import dict_row

# .env está junto a requirements.txt y no depende del directorio de ejecución.
load_dotenv(Path(__file__).resolve().parents[1] / '.env')


def get_db() -> Generator[psycopg.Connection, None, None]:
    """Abre una conexión; confirma la transacción al concluir sin errores."""
    dsn = os.getenv('DATABASE_URL', '')
    if not dsn or 'PROJECT_REF' in dsn or 'POOLER_HOST' in dsn:
        raise HTTPException(status_code=503, detail='Configura DATABASE_URL en backend/.env')

    try:
        conn = psycopg.connect(dsn, row_factory=dict_row, connect_timeout=8, sslmode='require')
    except psycopg.OperationalError as exc:
        raise HTTPException(status_code=503, detail='No se pudo conectar a PostgreSQL') from exc

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
