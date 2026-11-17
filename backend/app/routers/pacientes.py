"""Pacientes ficticios: CRUD, resumen SQL y patrones de factores."""
from typing import Annotated
import psycopg
from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from app.database import get_db
from app.schemas import PacienteCrear, PacienteLeer, PatronLeer, ResumenLeer

router = APIRouter(prefix='/pacientes', tags=['Pacientes'])
DB = Annotated[psycopg.Connection, Depends(get_db)]
CAMPOS = 'id_paciente, nombre, fecha_nacimiento, sexo, telefono, fecha_registro'


def exigir_paciente(conn: psycopg.Connection, id_paciente: int):
    with conn.cursor() as cur:
        cur.execute('SELECT 1 FROM public.paciente WHERE id_paciente = %s', (id_paciente,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail='Paciente no encontrado')


@router.post('', response_model=PacienteLeer, status_code=201)
def crear_paciente(datos: PacienteCrear, conn: DB):
    with conn.cursor() as cur:
        cur.execute(f'''
            INSERT INTO public.paciente (nombre, fecha_nacimiento, sexo, telefono)
            VALUES (%s, %s, %s, %s) RETURNING {CAMPOS}
        ''', (datos.nombre, datos.fecha_nacimiento, datos.sexo, datos.telefono))
        paciente = cur.fetchone()
    conn.commit()
    return paciente


@router.get('', response_model=list[PacienteLeer])
def listar_pacientes(conn: DB):
    with conn.cursor() as cur:
        cur.execute(f'SELECT {CAMPOS} FROM public.paciente ORDER BY id_paciente DESC LIMIT 100')
        return cur.fetchall()


@router.get('/{id_paciente}', response_model=PacienteLeer)
def detalle_paciente(id_paciente: int, conn: DB):
    with conn.cursor() as cur:
        cur.execute(f'SELECT {CAMPOS} FROM public.paciente WHERE id_paciente = %s', (id_paciente,))
        paciente = cur.fetchone()
    if paciente is None:
        raise HTTPException(status_code=404, detail='Paciente no encontrado')
    return paciente


@router.put('/{id_paciente}', response_model=PacienteLeer)
def actualizar_paciente(id_paciente: int, datos: PacienteCrear, conn: DB):
    with conn.cursor() as cur:
        cur.execute(f'''
            UPDATE public.paciente SET nombre=%s, fecha_nacimiento=%s, sexo=%s, telefono=%s
            WHERE id_paciente=%s RETURNING {CAMPOS}
        ''', (datos.nombre, datos.fecha_nacimiento, datos.sexo, datos.telefono, id_paciente))
        paciente = cur.fetchone()
    if paciente is None:
        raise HTTPException(status_code=404, detail='Paciente no encontrado')
    conn.commit()
    return paciente


@router.delete('/{id_paciente}', status_code=204)
def borrar_paciente(id_paciente: int, conn: DB):
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM public.paciente WHERE id_paciente=%s RETURNING id_paciente', (id_paciente,))
            eliminado = cur.fetchone()
        if eliminado is None:
            raise HTTPException(status_code=404, detail='Paciente no encontrado')
        conn.commit()
    except errors.ForeignKeyViolation as exc:
        raise HTTPException(status_code=409, detail='No se puede eliminar: el paciente tiene episodios o tratamientos asociados') from exc


@router.get('/{id_paciente}/resumen', response_model=ResumenLeer, tags=['Estadísticas'])
def resumen(id_paciente: int, conn: DB):
    # La vista incluye una fila por paciente aunque tenga cero episodios.
    with conn.cursor() as cur:
        cur.execute('''
            SELECT id_paciente, total_episodios, episodios_mes,
                   duracion_promedio_segundos, severidad_promedio, ultima_crisis
            FROM public.v_resumen_paciente WHERE id_paciente=%s
        ''', (id_paciente,))
        resultado = cur.fetchone()
    if resultado is None:
        raise HTTPException(status_code=404, detail='Paciente no encontrado')
    return resultado


@router.get('/{id_paciente}/patrones', response_model=list[PatronLeer], tags=['Estadísticas'])
def patrones(id_paciente: int, conn: DB):
    exigir_paciente(conn, id_paciente)
    with conn.cursor() as cur:
        cur.execute('''
            SELECT id_paciente, id_desencadenante, categoria, descripcion,
                   apariciones, porcentaje_episodios
            FROM public.v_patrones_desencadenantes
            WHERE id_paciente=%s ORDER BY apariciones DESC, categoria, descripcion
        ''', (id_paciente,))
        return cur.fetchall()
