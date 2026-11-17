"""Contratos de API: información ficticia y validaciones de entrada."""
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PacienteCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    fecha_nacimiento: date | None = None
    sexo: str | None = Field(default=None, max_length=30)
    telefono: str | None = Field(default=None, max_length=25)

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, valor: str) -> str:
        valor = valor.strip()
        if len(valor) < 2:
            raise ValueError('El nombre debe tener al menos dos caracteres')
        return valor

    @field_validator('fecha_nacimiento')
    @classmethod
    def validar_fecha_nacimiento(cls, valor: date | None) -> date | None:
        if valor and valor > date.today():
            raise ValueError('La fecha de nacimiento no puede estar en el futuro')
        return valor


class PacienteLeer(PacienteCrear):
    id_paciente: int
    fecha_registro: datetime
    model_config = ConfigDict(from_attributes=True)


class EpisodioCrear(BaseModel):
    id_paciente: int = Field(gt=0)
    fecha_hora: datetime
    duracion_segundos: int = Field(gt=0, le=86400)
    tipo_crisis: str = Field(min_length=1, max_length=80)
    nivel_severidad: int | None = Field(default=None, ge=1, le=5)
    perdida_conocimiento: bool = False
    observaciones: str | None = Field(default=None, max_length=2000)
    ids_desencadenantes: list[int] = Field(default_factory=list, max_length=30)

    @field_validator('fecha_hora')
    @classmethod
    def validar_zona_horaria(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None or valor.utcoffset() is None:
            raise ValueError('Incluye zona horaria, por ejemplo -06:00')
        return valor

    @field_validator('tipo_crisis')
    @classmethod
    def validar_tipo(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError('Indica el tipo de crisis o No determinado')
        return valor

    @field_validator('ids_desencadenantes')
    @classmethod
    def validar_factores(cls, ids: list[int]) -> list[int]:
        if any(i <= 0 for i in ids) or len(ids) != len(set(ids)):
            raise ValueError('Los factores deben ser identificadores positivos sin duplicados')
        return ids


class EpisodioLeer(EpisodioCrear):
    id_episodio: int
    model_config = ConfigDict(from_attributes=True)


class FactoresVincular(BaseModel):
    ids_desencadenantes: list[int] = Field(min_length=1, max_length=30)

    @field_validator('ids_desencadenantes')
    @classmethod
    def validar_factores(cls, ids: list[int]) -> list[int]:
        if any(i <= 0 for i in ids) or len(ids) != len(set(ids)):
            raise ValueError('Los factores deben ser identificadores positivos sin duplicados')
        return ids


class DesencadenanteLeer(BaseModel):
    id_desencadenante: int
    categoria: str
    descripcion: str


class ResumenLeer(BaseModel):
    id_paciente: int
    total_episodios: int
    episodios_mes: int
    duracion_promedio_segundos: float | None
    severidad_promedio: float | None
    ultima_crisis: datetime | None


class PatronLeer(BaseModel):
    id_paciente: int
    id_desencadenante: int
    categoria: str
    descripcion: str
    apariciones: int
    porcentaje_episodios: float


class MedicamentoLeer(BaseModel):
    id_medicamento: int
    ingrediente_activo: str
    presentacion: str


class TratamientoCrear(BaseModel):
    id_medicamento: int = Field(gt=0)
    dosis: str = Field(min_length=1, max_length=100)
    frecuencia: str = Field(min_length=1, max_length=100)
    fecha_inicio: date
    fecha_fin: date | None = None

    @model_validator(mode='after')
    def fechas_coherentes(self):
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError('fecha_fin no puede ser anterior a fecha_inicio')
        return self


class TratamientoLeer(TratamientoCrear):
    id_tratamiento: int
    id_paciente: int
    ingrediente_activo: str
    presentacion: str
