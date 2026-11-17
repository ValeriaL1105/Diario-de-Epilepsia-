"""API de administración de datos relacionales — prototipo académico local."""
from typing import Annotated
import psycopg
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db
from app.routers import pacientes, episodios, catalogos

app = FastAPI(
    title='Registro de Episodios Epilépticos — Prototipo ABD',
    description='Solo datos ficticios. Sin autenticación: exclusivo para entorno local de demostración.',
    version='2.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5500', 'http://127.0.0.1:5500',
        'http://localhost:5173', 'http://127.0.0.1:5173',
    ],
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['Content-Type'],
)
app.include_router(pacientes.router)
app.include_router(episodios.router)
app.include_router(catalogos.router)


@app.get('/health', tags=['Sistema'])
def health(conn: Annotated[psycopg.Connection, Depends(get_db)]):
    with conn.cursor() as cur:
        cur.execute('SELECT 1 AS conectado')
        cur.fetchone()
    return {'api': 'ok', 'base_de_datos': 'conectada'}
