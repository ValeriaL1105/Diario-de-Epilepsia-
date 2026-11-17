"""Validaciones de la versión 2 sin necesitar base de datos ni internet."""
import pytest
from datetime import date
from pydantic import ValidationError
from app.schemas import EpisodioCrear, FactoresVincular, TratamientoCrear

BASE = dict(id_paciente=1, fecha_hora='2026-11-16T14:30:00-06:00',
            duracion_segundos=65, tipo_crisis='Focal')


def test_factores_multiple_validos():
    ep = EpisodioCrear(**BASE, ids_desencadenantes=[1, 3])
    assert ep.ids_desencadenantes == [1, 3]


def test_factores_opcionales_vacios():
    assert EpisodioCrear(**BASE).ids_desencadenantes == []


@pytest.mark.parametrize('factores', [[1, 1], [0], [-3]])
def test_rechaza_factores_duplicados_o_invalidos(factores):
    with pytest.raises(ValidationError):
        EpisodioCrear(**BASE, ids_desencadenantes=factores)


def test_cuerpo_vincular_factores():
    assert FactoresVincular(ids_desencadenantes=[2, 4]).ids_desencadenantes == [2, 4]


def test_vincular_factores_vacios_rechazados():
    with pytest.raises(ValidationError):
        FactoresVincular(ids_desencadenantes=[])


def test_severidad_fuera_rango():
    with pytest.raises(ValidationError):
        EpisodioCrear(**BASE, nivel_severidad=6)


def test_fecha_final_invalida_tratamiento():
    with pytest.raises(ValidationError):
        TratamientoCrear(id_medicamento=1, dosis='Ejemplo', frecuencia='Ejemplo',
                        fecha_inicio=date(2026, 11, 16), fecha_fin=date(2026, 11, 15))


def test_tratamiento_sin_fin():
    t = TratamientoCrear(id_medicamento=1, dosis='Ejemplo', frecuencia='Ejemplo',
                        fecha_inicio=date(2026, 11, 16))
    assert t.fecha_fin is None
