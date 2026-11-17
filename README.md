# Diario de Epilepsia
## Proyecto Integrador Final de Administración de Bases de Datos

**Universidad de Guadalajara · Centro Universitario de Ciencias Exactas e Ingenierías (CUCEI)**

## Presentación

Diario de Epilepsia es un prototipo académico para registrar pacientes, episodios epilépticos, factores desencadenantes y tratamientos ficticios.
El proyecto demuestra el diseño, la administración y la integración de una base de datos relacional mediante una API REST.

**Uso exclusivamente académico con datos ficticios. No es apto para uso clínico ni sustituye una evaluación médica.**

## Objetivo y funcionalidades

Organizar los registros y sus relaciones para consultar el historial de episodios de cada paciente y demostrar la integridad de los datos.

- Crear, consultar, editar y eliminar pacientes y episodios; el borrado de pacientes requiere que no tengan episodios ni tratamientos.
- Asociar varios factores a un episodio en una transacción y consultar el historial con filtros de fechas.
- Consultar resúmenes por paciente y frecuencias de factores mediante vistas SQL.
- Consultar los catálogos de medicamentos y desencadenantes, y registrar y listar tratamientos ficticios.

## Tecnologías y arquitectura

- **Frontend:** HTML, CSS y JavaScript sin framework; consume la API mediante `fetch`.
- **Backend:** Python y FastAPI; modelos de validación Pydantic y conexión PostgreSQL con Psycopg 3.
- **Base de datos:** PostgreSQL en Supabase; scripts SQL para tablas, restricciones, índices, vistas y datos de muestra.
- **Apoyo:** Uvicorn para servir la API, python-dotenv para configuración, pytest y HTTPX para pruebas.

```text
[HTML / CSS / JavaScript] -- HTTP/JSON --> [FastAPI / Python] -- SQL --> [PostgreSQL / Supabase]
       Presentación                          Aplicación                       Datos
```

El navegador se conecta a FastAPI en `http://127.0.0.1:8000`; las credenciales de PostgreSQL se configuran únicamente en el backend.

## Modelo de datos

Las seis tablas están en el esquema `public`:

| Tabla | Contenido y relación |
|---|---|
| `paciente` | Datos generales ficticios; un paciente tiene varios episodios y tratamientos. |
| `episodio` | Fecha, duración, tipo, severidad y observaciones; pertenece a un paciente. |
| `medicamento` | Catálogo de ingrediente activo y presentación; puede figurar en varios tratamientos. |
| `tratamiento` | Relaciona un paciente con un medicamento; registra dosis, frecuencia y fechas. |
| `desencadenante` | Catálogo de categorías y descripciones de posibles factores reportados. |
| `episodio_desencadenante` | Tabla puente con clave primaria compuesta para la relación N:M entre episodios y factores. |

Las claves foráneas protegen las relaciones; solo los vínculos de un episodio se eliminan en cascada al borrarlo.
Se incluyen restricciones `NOT NULL`, `UNIQUE` y `CHECK` e índices para búsquedas por paciente, fecha y relaciones.
Los `CHECK` validan, entre otros datos, duración de 1 a 86400 segundos, severidad de 1 a 5 y fechas coherentes de tratamiento.

**Vistas y función SQL:**

- `public.v_resumen_paciente`: total de episodios, episodios del mes, promedios de duración y severidad, y última crisis.
- `public.v_patrones_desencadenantes`: apariciones y porcentaje de episodios asociados a cada factor por paciente.
- `public.fn_resumen_paciente(BIGINT)`: devuelve el resumen de un paciente consultando la primera vista; la API consulta la vista directamente.

El resumen mensual usa `America/Mexico_City`. Los porcentajes de factores pueden sumar más de 100 % porque un episodio admite varios factores.
Estos resultados describen los registros de muestra y no establecen causalidad clínica.

## Estructura del proyecto

```text
Diario_epilepsia/
├── README.md                   # Presentación, instalación y guía del proyecto.
├── .gitignore                  # Exclusiones de credenciales y archivos generados.
├── backend/
│   ├── .env.example            # Plantilla de configuración con marcadores de ejemplo.
│   ├── requirements.txt        # Dependencias de ejecución y pruebas.
│   ├── app/
│   │   ├── __init__.py         # Identifica el paquete de la aplicación.
│   │   ├── main.py             # Crea FastAPI, configura CORS y routers, y expone /health.
│   │   ├── database.py         # Carga configuración y gestiona conexión y transacciones.
│   │   ├── schemas.py          # Modelos de entrada/salida y validaciones Pydantic.
│   │   └── routers/
│   │       ├── __init__.py     # Identifica el paquete de rutas.
│   │       ├── pacientes.py    # CRUD de pacientes, resumen y patrones.
│   │       ├── episodios.py    # CRUD de episodios, filtros y asociación de factores.
│   │       └── catalogos.py    # Consulta de catálogos y registro/listado de tratamientos.
│   └── tests/
│       ├── test_validaciones.py # Validaciones básicas de pacientes y episodios.
│       ├── test_v2.py          # Validaciones de factores, severidad y tratamientos.
│       └── test_api_contrato.py # Rutas OpenAPI y respuesta HTTP 422 con BD simulada.
├── database/
│   ├── schema.sql              # Seis tablas, restricciones, índices y declaraciones RLS.
│   ├── views.sql               # Dos vistas, función de resumen y revocaciones de permisos.
│   ├── seed.sql                # Catálogos, pacientes, episodios y tratamientos de muestra.
│   ├── check_modelo.sql        # Consultas de restricciones, índices y estadísticas.
│   └── test_integridad.sql     # Prueba tres CHECK e invoca la función de resumen.
└── frontend/
    ├── index.html              # Formularios y secciones de consulta.
    ├── styles.css              # Estilos y adaptación de la interfaz a pantallas pequeñas.
    ├── app.js                  # Peticiones REST, eventos y presentación de resultados.
    └── INSTRUCCIONES_EQUIPO.md  # Referencia del contrato JSON para el equipo.
```

`backend/.env`, el entorno `.venv/` y las cachés son archivos locales excluidos de Git.

## API REST

Base local: `http://127.0.0.1:8000`. Los nombres de parámetros corresponden al código.

| Método | Ruta | Función |
|---|---|---|
| GET | `/health` | Comprueba la conexión con PostgreSQL. |
| GET / POST | `/pacientes` | Lista hasta 100 pacientes / registra uno. |
| GET / PUT / DELETE | `/pacientes/{id_paciente}` | Consulta / reemplaza / elimina sin dependencias. |
| POST | `/episodios` | Registra un episodio y sus factores en una transacción. |
| GET | `/pacientes/{id_paciente}/episodios` | Historial descendente; filtros opcionales `desde` y `hasta`. |
| GET / PUT / DELETE | `/episodios/{id_episodio}` | Consulta / reemplaza / elimina un episodio. |
| POST | `/episodios/{id_episodio}/factores` | Agrega asociaciones sin repetir vínculos existentes. |
| GET | `/desencadenantes`, `/medicamentos` | Consulta los dos catálogos. |
| GET | `/pacientes/{id_paciente}/resumen` | Consulta `v_resumen_paciente`. |
| GET | `/pacientes/{id_paciente}/patrones` | Consulta `v_patrones_desencadenantes`. |
| GET / POST | `/pacientes/{id_paciente}/tratamientos` | Lista / registra tratamientos ficticios. |

`PUT` reemplaza los datos; en episodios también sustituye la lista `ids_desencadenantes`, y `[]` elimina sus asociaciones.
La fecha y hora del episodio debe incluir zona horaria, por ejemplo `2026-11-16T14:30:00-06:00`.
Los filtros usan `AAAA-MM-DD` y ambos días son inclusivos según `APP_TIMEZONE`.
Las altas devuelven `201` y los borrados `204`; los errores previstos incluyen `404`, `409` por dependencias, `422` por validación y `503` por configuración o conexión.
Las consultas usan parámetros y los errores de una transacción provocan su reversión.

## Instalación y ejecución en Windows PowerShell

### 1. Preparar Python y dependencias

Requisitos: Python 3.12 (versión usada en el desarrollo y las pruebas) y PowerShell.
Abre PowerShell en la raíz del proyecto y ejecuta:

```powershell
python3 --version
cd backend
python3 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

Notas:

- Si `python3` no se reconoce en tu equipo, prueba con `python` o con el lanzador
  `py -3.12`. En Windows no siempre está instalado el lanzador `py`, por lo que la
  versión que funcione depende de cada instalación.
- `Set-ExecutionPolicy -Scope Process` permite activar el entorno virtual **solo en
  esa terminal**; hay que repetirlo cada vez que abras una nueva. Si no quieres usarlo,
  puedes llamar directamente a `.\.venv\Scripts\python.exe` en lugar de `python`.
- Al activarse el entorno debe aparecer `(.venv)` al inicio de la línea.
- El archivo `.env` contiene credenciales: no lo publiques ni lo incluyas en el ZIP.
  Debe quedar en `backend/`, junto a `requirements.txt`.
- El repositorio no fija una versión exacta de Python; `requirements.txt` declara
  rangos de dependencias.

### 2. Configurar Supabase y crear la base de datos

Crea un proyecto de Supabase para los datos ficticios y copia su cadena de conexión
**Session pooler** (botón *Connect*). Al crear el proyecto, en la sección de seguridad:
desactiva *Enable Data API* y *Automatically expose new tables*, y activa
*Enable automatic RLS*, porque el acceso a los datos es solo a través de la API.

En `backend/.env`, sustituye los marcadores de `DATABASE_URL` por los datos de esa
conexión, **sin comillas ni espacios** alrededor del `=`:

```
DATABASE_URL=postgresql://usuario:CONTRASEÑA@host:5432/postgres
```

- Si la contraseña contiene caracteres especiales (`:`, `@`, `#`, `/`, `%`, `^`, `<`),
  cámbiala por una solo con letras y números, o codifícala para URL
  (por ejemplo `:` → `%3A`, `@` → `%40`).
- Conserva `APP_TIMEZONE=America/Mexico_City`.
- No uses una API key como contraseña de PostgreSQL ni coloques credenciales en el
  frontend.

En el SQL Editor del proyecto ejecuta los archivos completos **en este orden**
(se requiere PostgreSQL 15 o superior por las vistas `security_invoker`):

1. `database/schema.sql`: crea el modelo de seis tablas.
2. `database/views.sql`: crea las dos vistas y la función.
3. `database/seed.sql`: carga los catálogos y datos ficticios.
4. `database/check_modelo.sql` (opcional): consulta restricciones, índices y resultados.
5. `database/test_integridad.sql` (opcional): comprueba rechazos de datos inválidos.

En una base nueva, el seed carga 7 factores, 4 medicamentos, 4 pacientes, 12 episodios
y 3 tratamientos. Puede repetirse sin duplicar su muestra mientras se conserven sus
identificadores de referencia.

Si ya tienes el modelo creado, no vuelvas a ejecutar `schema.sql` (no migra tablas
existentes); aplica solo `views.sql` y `seed.sql`.

Los scripts declaran RLS y revocaciones; los permisos efectivos deben comprobarse
manualmente en Supabase.

### 3. Iniciar backend y frontend

Se necesitan **dos terminales** de PowerShell abiertas al mismo tiempo.

**Terminal 1: backend.** Desde la carpeta `backend/`:

```powershell
cd backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Debe aparecer `(.venv)` al inicio de la línea. El permiso de `Set-ExecutionPolicy`
solo vale para esa terminal, así que hay que repetirlo cada vez que se abra una nueva.

**Terminal 2: frontend.** Desde la carpeta `frontend/`:

```powershell
cd frontend
python -m http.server 5500
```

> Probado en Windows con Python 3.12. Si `py -3.12` no se reconoce en tu equipo,
> usa `python` o `python3`: el launcher `py` no siempre está instalado.

Direcciones:

- Interfaz de prueba: `http://127.0.0.1:5500`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Verificación de conexión: `http://127.0.0.1:8000/health`, que debe responder
  `{"api":"ok","base_de_datos":"conectada"}`

Mantén ambas terminales abiertas. Selecciona `MUESTRA - Paciente A` para consultar
historial, estadísticas y tratamientos. Usa los identificadores devueltos por la API;
no presupongas valores consecutivos. Para detener un servidor, presiona `Ctrl+C`.

### 4. Ejecutar pruebas y preparar evidencias

Desde `backend/`, con el entorno activado:

```powershell
python -m pytest -q
```

Las pruebas de Python revisan validaciones y contrato HTTP sin conectarse a Supabase.
El flujo completo contra la base se verificó manualmente con esta lista:

1. `/health` responde `conectada`.
2. La interfaz muestra los cuatro pacientes de muestra.
3. Se consulta el historial de un paciente.
4. Se registra un episodio con dos desencadenantes.
5. Se filtran episodios por fecha y se edita uno.
6. El resumen y los patrones se actualizan.
7. Se registra un tratamiento con datos ficticios.
8. Al enviar un factor inexistente (por ejemplo `999999`) desde Swagger, el episodio
   no se guarda.

Para la presentación se pueden mostrar las seis tablas en Supabase, los resultados
de `check_modelo.sql` y `test_integridad.sql`, y el error `409` al intentar borrar
un paciente con registros dependientes.

## Alcance y trabajo futuro

Este proyecto se centra en el **backend**: la base de datos relacional y la API que
permite conectarla de forma sencilla con cualquier aplicación. La página incluida en
`frontend/` es únicamente una interfaz mínima de demostración para probar la API; no
es la aplicación final para pacientes ni médicos.

**Fuera del alcance de este proyecto:**

- Una aplicación web o móvil completa para pacientes, familiares o personal médico.
- Detección automática de crisis, diagnósticos o recomendaciones de tratamiento.
- Uso en un entorno clínico real: solo se manejan datos ficticios.

**Limitaciones actuales de la API:**

- No incluye autenticación ni permisos por usuario.
- El listado de pacientes se limita a 100 registros, sin paginación.
- Las versiones de las dependencias no están fijadas de forma exacta.

**Trabajo futuro:**

- Autenticación y permisos por usuario.
- Una aplicación cliente completa (web o móvil) que consuma esta API.
- Paginación y pruebas de integración automatizadas.
- Procedimientos de respaldo y restauración.

Ninguna de estas ampliaciones está implementada en el repositorio.

## Integrantes y créditos

- Anahí Ramírez Rodríguez
- Valeria Lizzeth Perez Molgado
- Esdras Israel García Guzmán

**Universidad de Guadalajara, CUCEI · Administración de Bases de Datos.**
