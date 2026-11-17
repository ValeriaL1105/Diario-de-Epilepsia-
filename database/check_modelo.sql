-- Consultas de lectura para evidencias del proyecto (no modifican datos).
-- Restricciones de integridad de las 6 tablas.
SELECT c.conrelid::regclass AS tabla, c.conname AS restriccion,
       pg_get_constraintdef(c.oid) AS definicion
FROM pg_constraint c
WHERE c.connamespace = 'public'::regnamespace
  AND c.conrelid IN (
    'public.paciente'::regclass, 'public.episodio'::regclass,
    'public.medicamento'::regclass, 'public.tratamiento'::regclass,
    'public.desencadenante'::regclass, 'public.episodio_desencadenante'::regclass
  )
ORDER BY tabla, restriccion;

-- Índices que aceleran búsquedas por paciente y fecha.
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('episodio', 'tratamiento', 'episodio_desencadenante')
ORDER BY tablename, indexname;

-- Datos ficticios para mostrar estadística relacional (no modifica tablas).
SELECT * FROM public.v_resumen_paciente ORDER BY id_paciente;
SELECT * FROM public.v_patrones_desencadenantes
ORDER BY id_paciente, apariciones DESC;
