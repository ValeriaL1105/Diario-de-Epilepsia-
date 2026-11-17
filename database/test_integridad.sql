-- Tests no destructivos. Ejecutar DESPUÉS de schema.sql, views.sql y seed.sql.
-- Los errores esperados se capturan con excepciones SQL; nunca guardan los datos incorrectos.
DO $$
DECLARE v_paciente BIGINT; v_medicamento BIGINT;
BEGIN
 SELECT id_paciente INTO v_paciente FROM public.paciente LIMIT 1;
 SELECT id_medicamento INTO v_medicamento FROM public.medicamento LIMIT 1;
 IF v_paciente IS NULL OR v_medicamento IS NULL THEN
   RAISE EXCEPTION 'Ejecuta seed.sql antes de probar la integridad';
 END IF;
 BEGIN
   INSERT INTO public.episodio (id_paciente, fecha_hora, duracion_segundos, tipo_crisis)
   VALUES (v_paciente, now(), 0, 'Prueba');
   RAISE EXCEPTION 'FALLÓ: se permitió duración=0';
 EXCEPTION WHEN check_violation THEN RAISE NOTICE 'OK: duración=0 rechazada'; END;
 BEGIN
   INSERT INTO public.episodio (id_paciente, fecha_hora, duracion_segundos, tipo_crisis, nivel_severidad)
   VALUES (v_paciente, now(), 60, 'Prueba', 8);
   RAISE EXCEPTION 'FALLÓ: se permitió severidad=8';
 EXCEPTION WHEN check_violation THEN RAISE NOTICE 'OK: severidad=8 rechazada'; END;
 BEGIN
   INSERT INTO public.tratamiento (id_paciente,id_medicamento,dosis,frecuencia,fecha_inicio,fecha_fin)
   VALUES (v_paciente,v_medicamento,'Prueba','Prueba','2026-11-15','2026-11-14');
   RAISE EXCEPTION 'FALLÓ: se permitió fecha_fin antes de fecha_inicio';
 EXCEPTION WHEN check_violation THEN RAISE NOTICE 'OK: fechas inconsistentes rechazadas'; END;
 RAISE NOTICE 'Comprobaciones de integridad terminadas';
END $$;

SELECT * FROM public.fn_resumen_paciente((SELECT id_paciente FROM public.paciente WHERE telefono='DEMO-A' LIMIT 1));
