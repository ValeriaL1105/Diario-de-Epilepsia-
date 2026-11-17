"""Catálogos y asignación de tratamientos de demostración."""
from typing import Annotated
import psycopg
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.schemas import DesencadenanteLeer, MedicamentoLeer, TratamientoCrear, TratamientoLeer
from app.routers.pacientes import exigir_paciente

router = APIRouter(tags=['Catálogos y tratamientos'])
DB = Annotated[psycopg.Connection, Depends(get_db)]
TRATAMIENTO = '''t.id_tratamiento, t.id_paciente, t.id_medicamento,
     t.dosis, t.frecuencia, t.fecha_inicio, t.fecha_fin,
     m.ingrediente_activo, m.presentacion'''


@router.get('/desencadenantes', response_model=list[DesencadenanteLeer])
def listar_desencadenantes(conn: DB):
    with conn.cursor() as cur:
        cur.execute('''SELECT id_desencadenante, categoria, descripcion
                       FROM public.desencadenante ORDER BY categoria, descripcion''')
        return cur.fetchall()


@router.get('/medicamentos', response_model=list[MedicamentoLeer])
def listar_medicamentos(conn: DB):
    with conn.cursor() as cur:
        cur.execute('''SELECT id_medicamento, ingrediente_activo, presentacion
                       FROM public.medicamento ORDER BY ingrediente_activo, presentacion''')
        return cur.fetchall()


@router.post('/pacientes/{id_paciente}/tratamientos', response_model=TratamientoLeer, status_code=201)
def registrar_tratamiento(id_paciente: int, datos: TratamientoCrear, conn: DB):
    exigir_paciente(conn, id_paciente)
    with conn.cursor() as cur:
        cur.execute('SELECT 1 FROM public.medicamento WHERE id_medicamento=%s', (datos.id_medicamento,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=422, detail='El medicamento seleccionado no existe')
        cur.execute('''
            INSERT INTO public.tratamiento
            (id_paciente, id_medicamento, dosis, frecuencia, fecha_inicio, fecha_fin)
            VALUES (%s,%s,%s,%s,%s,%s) RETURNING id_tratamiento
        ''', (id_paciente, datos.id_medicamento, datos.dosis, datos.frecuencia,
              datos.fecha_inicio, datos.fecha_fin))
        id_tratamiento = cur.fetchone()['id_tratamiento']
        cur.execute(f'''SELECT {TRATAMIENTO} FROM public.tratamiento t
                        JOIN public.medicamento m ON t.id_medicamento=m.id_medicamento
                        WHERE t.id_tratamiento=%s''', (id_tratamiento,))
        resultado = cur.fetchone()
    conn.commit()
    return resultado


@router.get('/pacientes/{id_paciente}/tratamientos', response_model=list[TratamientoLeer])
def historial_tratamientos(id_paciente: int, conn: DB):
    exigir_paciente(conn, id_paciente)
    with conn.cursor() as cur:
        cur.execute(f'''SELECT {TRATAMIENTO} FROM public.tratamiento t
                        JOIN public.medicamento m ON t.id_medicamento=m.id_medicamento
                        WHERE t.id_paciente=%s ORDER BY t.fecha_inicio DESC, t.id_tratamiento DESC''',
                    (id_paciente,))
        return cur.fetchall()
