-- V2. Catálogos y datos 100% ficticios para demostración.
-- Idempotente: puede ejecutarse más de una vez sin duplicar las filas de esta muestra.
-- Si ya tenías episodios reales de PRUEBA creados con la API, no se borran.

INSERT INTO public.desencadenante (categoria, descripcion) VALUES
 ('Sueño', 'Dormir menos de lo habitual'),
 ('Estrés', 'Estrés percibido'),
 ('Medicacion', 'Omisión reportada de medicamento'),
 ('Otros', 'Posible factor no determinado'),
 ('Estímulos', 'Luces intermitentes'),
 ('Salud', 'Fiebre reportada'),
 ('Hábitos', 'Consumo reportado de alcohol')
ON CONFLICT (categoria, descripcion) DO NOTHING;

INSERT INTO public.medicamento (ingrediente_activo, presentacion) VALUES
 ('Levetiracetam', 'Tableta 500 mg'),
 ('Lamotrigina', 'Tableta 100 mg'),
 ('Ácido valproico', 'Cápsula 250 mg'),
 ('Carbamazepina', 'Tableta 200 mg')
ON CONFLICT (ingrediente_activo, presentacion) DO NOTHING;

INSERT INTO public.paciente (nombre, fecha_nacimiento, sexo, telefono)
SELECT m.nombre, m.nacimiento::date, m.sexo, m.telefono FROM (
 VALUES
  ('MUESTRA - Paciente A', '2000-02-10', 'No especificado', 'DEMO-A'),
  ('MUESTRA - Paciente B', '1997-05-22', 'No especificado', 'DEMO-B'),
  ('MUESTRA - Paciente C', '2003-09-03', 'No especificado', 'DEMO-C'),
  ('MUESTRA - Paciente D', '1994-12-01', 'No especificado', 'DEMO-D')
) AS m(nombre, nacimiento, sexo, telefono)
WHERE NOT EXISTS (SELECT 1 FROM public.paciente p WHERE p.telefono=m.telefono);

WITH muestras (telefono, fecha_hora, duracion, tipo, severidad, conciencia, codigo) AS (
 VALUES
 ('DEMO-A','2026-09-06 10:20:00-06', 45,'Focal',2,false,'DEMO-EP-01'),
 ('DEMO-A','2026-10-10 14:30:00-06', 80,'Focal',3,false,'DEMO-EP-02'),
 ('DEMO-A','2026-11-06 09:25:00-06', 95,'Generalizada',4,true,'DEMO-EP-03'),
 ('DEMO-A','2026-11-12 18:40:00-06', 65,'Focal',2,false,'DEMO-EP-04'),
 ('DEMO-B','2026-08-19 08:10:00-06', 33,'Focal',1,false,'DEMO-EP-05'),
 ('DEMO-B','2026-10-03 22:15:00-06', 72,'No determinado',null,true,'DEMO-EP-06'),
 ('DEMO-B','2026-11-05 07:05:00-06', 57,'Focal',2,false,'DEMO-EP-07'),
 ('DEMO-C','2026-09-21 13:00:00-06', 61,'Focal',3,false,'DEMO-EP-08'),
 ('DEMO-C','2026-10-18 11:10:00-06', 41,'Focal',2,false,'DEMO-EP-09'),
 ('DEMO-C','2026-11-09 20:00:00-06', 78,'Generalizada',4,true,'DEMO-EP-10'),
 ('DEMO-D','2026-10-13 17:00:00-06', 30,'No determinado',null,false,'DEMO-EP-11'),
 ('DEMO-D','2026-11-14 12:45:00-06', 55,'Focal',2,false,'DEMO-EP-12')
)
INSERT INTO public.episodio
(id_paciente, fecha_hora, duracion_segundos, tipo_crisis, nivel_severidad, perdida_conocimiento, observaciones)
SELECT p.id_paciente, m.fecha_hora::timestamptz, m.duracion, m.tipo, m.severidad, m.conciencia, m.codigo
FROM muestras m JOIN public.paciente p ON p.telefono = m.telefono
WHERE NOT EXISTS (SELECT 1 FROM public.episodio e WHERE e.observaciones = m.codigo);

WITH enlaces (codigo, descripcion) AS (
 VALUES ('DEMO-EP-01','Estrés percibido'),
        ('DEMO-EP-02','Dormir menos de lo habitual'),
        ('DEMO-EP-03','Omisión reportada de medicamento'),
        ('DEMO-EP-04','Estrés percibido'),
        ('DEMO-EP-04','Dormir menos de lo habitual'),
        ('DEMO-EP-05','Posible factor no determinado'),
        ('DEMO-EP-06','Luces intermitentes'),
        ('DEMO-EP-07','Estrés percibido'),
        ('DEMO-EP-08','Fiebre reportada'),
        ('DEMO-EP-09','Dormir menos de lo habitual'),
        ('DEMO-EP-10','Consumo reportado de alcohol'),
        ('DEMO-EP-11','Posible factor no determinado'),
        ('DEMO-EP-12','Estrés percibido')
)
INSERT INTO public.episodio_desencadenante (id_episodio, id_desencadenante)
SELECT e.id_episodio, d.id_desencadenante
FROM enlaces m JOIN public.episodio e ON e.observaciones=m.codigo
JOIN public.desencadenante d ON d.descripcion=m.descripcion
ON CONFLICT DO NOTHING;

-- Tratamientos únicamente ficticios: NO son recomendaciones farmacológicas.
WITH muestras (telefono, ingrediente, presentacion, dosis, frecuencia, inicio) AS (
 VALUES
 ('DEMO-A','Levetiracetam','Tableta 500 mg','Ejemplo ficticio','Registro de muestra','2026-09-01'),
 ('DEMO-B','Lamotrigina','Tableta 100 mg','Ejemplo ficticio','Registro de muestra','2026-08-15'),
 ('DEMO-C','Ácido valproico','Cápsula 250 mg','Ejemplo ficticio','Registro de muestra','2026-09-20')
)
INSERT INTO public.tratamiento (id_paciente, id_medicamento, dosis, frecuencia, fecha_inicio)
SELECT p.id_paciente, med.id_medicamento, m.dosis, m.frecuencia, m.inicio::date
FROM muestras m JOIN public.paciente p ON p.telefono=m.telefono
JOIN public.medicamento med ON med.ingrediente_activo=m.ingrediente AND med.presentacion=m.presentacion
WHERE NOT EXISTS (
 SELECT 1 FROM public.tratamiento t
 WHERE t.id_paciente=p.id_paciente AND t.id_medicamento=med.id_medicamento
   AND t.fecha_inicio=m.inicio::date
);
