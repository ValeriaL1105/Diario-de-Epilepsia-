-- Proyecto Integrador ABD | Modelo entidad-relación final (6 tablas)
-- Ejecutar una sola vez desde Supabase > SQL Editor.
-- Todas las tablas usan el esquema public. Solo datos ficticios.

CREATE TABLE IF NOT EXISTS public.paciente (
    id_paciente BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL CHECK (length(trim(nombre)) >= 2),
    fecha_nacimiento DATE,
    sexo VARCHAR(30),
    telefono VARCHAR(25),
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.episodio (
    id_episodio BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_paciente BIGINT NOT NULL REFERENCES public.paciente(id_paciente) ON DELETE RESTRICT,
    fecha_hora TIMESTAMPTZ NOT NULL,
    duracion_segundos INTEGER NOT NULL CHECK (duracion_segundos > 0 AND duracion_segundos <= 86400),
    tipo_crisis VARCHAR(80) NOT NULL CHECK (length(trim(tipo_crisis)) > 0),
    nivel_severidad SMALLINT CHECK (nivel_severidad BETWEEN 1 AND 5),
    perdida_conocimiento BOOLEAN NOT NULL DEFAULT false,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS public.medicamento (
    id_medicamento BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ingrediente_activo VARCHAR(150) NOT NULL,
    presentacion VARCHAR(120) NOT NULL,
    CONSTRAINT uq_medicamento UNIQUE (ingrediente_activo, presentacion)
);

CREATE TABLE IF NOT EXISTS public.tratamiento (
    id_tratamiento BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_paciente BIGINT NOT NULL REFERENCES public.paciente(id_paciente) ON DELETE RESTRICT,
    id_medicamento BIGINT NOT NULL REFERENCES public.medicamento(id_medicamento) ON DELETE RESTRICT,
    dosis VARCHAR(100) NOT NULL,
    frecuencia VARCHAR(100) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    CONSTRAINT ck_fechas_tratamiento CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE TABLE IF NOT EXISTS public.desencadenante (
    id_desencadenante BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    categoria VARCHAR(80) NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    CONSTRAINT uq_desencadenante UNIQUE (categoria, descripcion)
);

CREATE TABLE IF NOT EXISTS public.episodio_desencadenante (
    id_episodio BIGINT NOT NULL REFERENCES public.episodio(id_episodio) ON DELETE CASCADE,
    id_desencadenante BIGINT NOT NULL REFERENCES public.desencadenante(id_desencadenante) ON DELETE RESTRICT,
    PRIMARY KEY (id_episodio, id_desencadenante)
);

CREATE INDEX IF NOT EXISTS idx_episodio_paciente_fecha
    ON public.episodio (id_paciente, fecha_hora DESC);
CREATE INDEX IF NOT EXISTS idx_tratamiento_paciente
    ON public.tratamiento (id_paciente);
CREATE INDEX IF NOT EXISTS idx_tratamiento_medicamento
    ON public.tratamiento (id_medicamento);
CREATE INDEX IF NOT EXISTS idx_ep_desencadenante_desencadenante
    ON public.episodio_desencadenante (id_desencadenante);

-- Proteger las tablas frente a solicitudes anónimas de la Data API de Supabase.
-- El backend se conecta mediante un usuario de PostgreSQL privilegiado SOLO en local.
-- Sin políticas RLS, las claves públicas (anon) no pueden leer/escribir estas tablas.
ALTER TABLE public.paciente ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.episodio ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medicamento ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tratamiento ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.desencadenante ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.episodio_desencadenante ENABLE ROW LEVEL SECURITY;
