-- V2. Ejecutar una vez (o repetir: CREATE OR REPLACE) en Supabase SQL Editor.
-- NO borra tablas ni registros. Se requiere PostgreSQL 15+ (Supabase Cloud).
-- Se usa security_invoker para no saltarse el control de filas de las tablas.

CREATE OR REPLACE VIEW public.v_resumen_paciente
WITH (security_invoker = true) AS
SELECT p.id_paciente,
       COUNT(e.id_episodio)::BIGINT AS total_episodios,
       COUNT(e.id_episodio) FILTER (
          WHERE e.fecha_hora >= (date_trunc('month', current_timestamp AT TIME ZONE 'America/Mexico_City') AT TIME ZONE 'America/Mexico_City')
            AND e.fecha_hora < ((date_trunc('month', current_timestamp AT TIME ZONE 'America/Mexico_City') + interval '1 month') AT TIME ZONE 'America/Mexico_City')
       )::BIGINT AS episodios_mes,
       ROUND(AVG(e.duracion_segundos)::numeric, 2) AS duracion_promedio_segundos,
       ROUND(AVG(e.nivel_severidad)::numeric, 2) AS severidad_promedio,
       MAX(e.fecha_hora) AS ultima_crisis
FROM public.paciente p
LEFT JOIN public.episodio e ON e.id_paciente = p.id_paciente
GROUP BY p.id_paciente;

-- Denominador del porcentaje: TODOS los episodios del mismo paciente.
-- Una crisis puede tener varios factores, por eso porcentajes sumados pueden pasar 100%.
CREATE OR REPLACE VIEW public.v_patrones_desencadenantes
WITH (security_invoker = true) AS
SELECT e.id_paciente,
       d.id_desencadenante,
       d.categoria,
       d.descripcion,
       COUNT(*)::BIGINT AS apariciones,
       ROUND(100.0 * COUNT(*) / NULLIF(total.total_episodios, 0), 2) AS porcentaje_episodios
FROM public.episodio_desencadenante ed
JOIN public.episodio e ON e.id_episodio = ed.id_episodio
JOIN public.desencadenante d ON d.id_desencadenante = ed.id_desencadenante
JOIN (
    SELECT id_paciente, COUNT(*) AS total_episodios
    FROM public.episodio GROUP BY id_paciente
) total ON total.id_paciente = e.id_paciente
GROUP BY e.id_paciente, d.id_desencadenante, d.categoria, d.descripcion, total.total_episodios;

-- Función SQL como ejemplo de consulta almacenada (sin parámetros externos construidos por texto).
CREATE OR REPLACE FUNCTION public.fn_resumen_paciente(p_id_paciente BIGINT)
RETURNS TABLE (
    id_paciente BIGINT, total_episodios BIGINT, episodios_mes BIGINT,
    duracion_promedio_segundos NUMERIC, severidad_promedio NUMERIC,
    ultima_crisis TIMESTAMPTZ
)
LANGUAGE sql STABLE SECURITY INVOKER
SET search_path = ''
AS $$
    SELECT v.id_paciente, v.total_episodios, v.episodios_mes,
           v.duracion_promedio_segundos, v.severidad_promedio, v.ultima_crisis
    FROM public.v_resumen_paciente v WHERE v.id_paciente = p_id_paciente
$$;

-- No exponer las vistas ni la función a las API keys públicas de Supabase.
-- FastAPI usa una conexión a PostgreSQL con las credenciales guardadas en backend/.env.
REVOKE ALL ON public.v_resumen_paciente, public.v_patrones_desencadenantes
    FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.fn_resumen_paciente(BIGINT)
    FROM PUBLIC, anon, authenticated;
