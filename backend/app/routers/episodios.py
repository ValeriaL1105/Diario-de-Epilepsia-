"""Registro, filtro, edición y eliminación de episodios; factores atómicos."""
from datetime import date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo
import os
import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db
from app.schemas import EpisodioCrear, EpisodioLeer, FactoresVincular
from app.routers.pacientes import exigir_paciente

router = APIRouter(tags=['Episodios'])
DB = Annotated[psycopg.Connection, Depends(get_db)]
CAMPOS = '''e.id_episodio, e.id_paciente, e.fecha_hora, e.duracion_segundos,
            e.tipo_crisis, e.nivel_severidad, e.perdida_conocimiento, e.observaciones,
            ARRAY(SELECT ed.id_desencadenante FROM public.episodio_desencadenante ed
                  WHERE ed.id_episodio=e.id_episodio ORDER BY ed.id_desencadenante)
            AS ids_desencadenantes'''


def validar_factores(conn: psycopg.Connection, ids: list[int]):
    if not ids:
        return
    with conn.cursor() as cur:
        cur.execute('SELECT id_desencadenante FROM public.desencadenante WHERE id_desencadenante = ANY(%s)', (ids,))
        encontrados = {r['id_desencadenante'] for r in cur.fetchall()}
    faltantes = sorted(set(ids) - encontrados)
    if faltantes:
        raise HTTPException(status_code=422, detail=f'Factores inexistentes: {faltantes}')


def guardar_asociaciones(conn: psycopg.Connection, id_episodio: int, ids: list[int]):
    if ids:
        with conn.cursor() as cur:
            cur.executemany('''
                INSERT INTO public.episodio_desencadenante (id_episodio, id_desencadenante)
                VALUES (%s, %s) ON CONFLICT DO NOTHING
            ''', [(id_episodio, i) for i in ids])


def obtener_episodio(conn: psycopg.Connection, id_episodio: int):
    with conn.cursor() as cur:
        cur.execute(f'SELECT {CAMPOS} FROM public.episodio e WHERE e.id_episodio=%s', (id_episodio,))
        resultado = cur.fetchone()
    if resultado is None:
        raise HTTPException(status_code=404, detail='Episodio no encontrado')
    return resultado


@router.post('/episodios', response_model=EpisodioLeer, status_code=201)
def crear_episodio(datos: EpisodioCrear, conn: DB):
    exigir_paciente(conn, datos.id_paciente)
    # No confirmar hasta terminar todos los INSERT; get_db revierte si algo falla.
    with conn.cursor() as cur:
        cur.execute('''
            INSERT INTO public.episodio
                (id_paciente, fecha_hora, duracion_segundos, tipo_crisis,
                 nivel_severidad, perdida_conocimiento, observaciones)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id_episodio
        ''', (datos.id_paciente, datos.fecha_hora, datos.duracion_segundos,
              datos.tipo_crisis, datos.nivel_severidad,
              datos.perdida_conocimiento, datos.observaciones))
        id_episodio = cur.fetchone()['id_episodio']
    validar_factores(conn, datos.ids_desencadenantes)
    guardar_asociaciones(conn, id_episodio, datos.ids_desencadenantes)
    episodio = obtener_episodio(conn, id_episodio)
    conn.commit()
    return episodio


@router.get('/pacientes/{id_paciente}/episodios', response_model=list[EpisodioLeer])
def historial_paciente(id_paciente: int, conn: DB,
                       desde: date | None = Query(default=None, description='Fecha inicial inclusive (hora local de la aplicación)'),
                       hasta: date | None = Query(default=None, description='Fecha final inclusive (hora local de la aplicación)')):
    exigir_paciente(conn, id_paciente)
    if desde and hasta and hasta < desde:
        raise HTTPException(status_code=422, detail='hasta debe ser mayor o igual que desde')
    tz = ZoneInfo(os.getenv('APP_TIMEZONE', 'America/Mexico_City'))
    condiciones = ['e.id_paciente=%s']
    params: list = [id_paciente]
    if desde:
        condiciones.append('e.fecha_hora >= %s')
        params.append(datetime.combine(desde, time.min, tzinfo=tz))
    if hasta == date.max:
        raise HTTPException(status_code=422, detail='La fecha hasta está fuera del rango admitido')
    if hasta:
        condiciones.append('e.fecha_hora < %s')
        params.append(datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=tz))
    with conn.cursor() as cur:
        cur.execute(f'''
            SELECT {CAMPOS} FROM public.episodio e
            WHERE {' AND '.join(condiciones)}
            ORDER BY e.fecha_hora DESC, e.id_episodio DESC
        ''', tuple(params))
        return cur.fetchall()


@router.get('/episodios/{id_episodio}', response_model=EpisodioLeer)
def detalle_episodio(id_episodio: int, conn: DB):
    return obtener_episodio(conn, id_episodio)


@router.put('/episodios/{id_episodio}', response_model=EpisodioLeer)
def actualizar_episodio(id_episodio: int, datos: EpisodioCrear, conn: DB):
    exigir_paciente(conn, datos.id_paciente)
    validar_factores(conn, datos.ids_desencadenantes)
    with conn.cursor() as cur:
        cur.execute('''
            UPDATE public.episodio
               SET id_paciente=%s, fecha_hora=%s, duracion_segundos=%s,
                   tipo_crisis=%s, nivel_severidad=%s, perdida_conocimiento=%s,
                   observaciones=%s
             WHERE id_episodio=%s RETURNING id_episodio
        ''', (datos.id_paciente, datos.fecha_hora, datos.duracion_segundos,
              datos.tipo_crisis, datos.nivel_severidad, datos.perdida_conocimiento,
              datos.observaciones, id_episodio))
        fila = cur.fetchone()
        if fila is None:
            raise HTTPException(status_code=404, detail='Episodio no encontrado')
        cur.execute('DELETE FROM public.episodio_desencadenante WHERE id_episodio=%s', (id_episodio,))
    guardar_asociaciones(conn, id_episodio, datos.ids_desencadenantes)
    episodio = obtener_episodio(conn, id_episodio)
    conn.commit()
    return episodio


@router.delete('/episodios/{id_episodio}', status_code=204)
def eliminar_episodio(id_episodio: int, conn: DB):
    # Únicamente los vínculos N:M se eliminan en cascada, no el paciente.
    with conn.cursor() as cur:
        cur.execute('DELETE FROM public.episodio WHERE id_episodio=%s RETURNING id_episodio', (id_episodio,))
        eliminado = cur.fetchone()
    if eliminado is None:
        raise HTTPException(status_code=404, detail='Episodio no encontrado')
    conn.commit()


@router.post('/episodios/{id_episodio}/factores', response_model=EpisodioLeer)
def vincular_factores(id_episodio: int, datos: FactoresVincular, conn: DB):
    obtener_episodio(conn, id_episodio)
    validar_factores(conn, datos.ids_desencadenantes)
    guardar_asociaciones(conn, id_episodio, datos.ids_desencadenantes)
    episodio = obtener_episodio(conn, id_episodio)
    conn.commit()
    return episodio
