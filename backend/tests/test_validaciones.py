"""Pruebas de esquema que no requieren credenciales de Supabase."""
from datetime import date
import pytest
from pydantic import ValidationError

from app.schemas import EpisodioCrear, PacienteCrear


def test_paciente_valido():
    paciente = PacienteCrear(nombre='Paciente Ejemplo', fecha_nacimiento=date(2000, 1, 1))
    assert paciente.nombre == 'Paciente Ejemplo'


def test_paciente_nombre_vacio():
    with pytest.raises(ValidationError):
        PacienteCrear(nombre='  ')


def test_paciente_fecha_futura():
    with pytest.raises(ValidationError):
        PacienteCrear(nombre='Paciente Ejemplo', fecha_nacimiento=date(2999, 1, 1))


def test_episodio_valido():
    episodio = EpisodioCrear(
        id_paciente=1, fecha_hora='2026-11-16T14:30:00-06:00',
        duracion_segundos=75, tipo_crisis='No determinado',
    )
    assert episodio.duracion_segundos == 75


@pytest.mark.parametrize('duracion', [0, -1, 86401])
def test_rechazar_duracion_invalida(duracion):
    with pytest.raises(ValidationError):
        EpisodioCrear(
            id_paciente=1, fecha_hora='2026-11-16T14:30:00-06:00',
            duracion_segundos=duracion, tipo_crisis='Focal',
        )


def test_rechazar_fecha_sin_zona():
    with pytest.raises(ValidationError):
        EpisodioCrear(
            id_paciente=1, fecha_hora='2026-11-16T14:30:00',
            duracion_segundos=75, tipo_crisis='Focal',
        )
