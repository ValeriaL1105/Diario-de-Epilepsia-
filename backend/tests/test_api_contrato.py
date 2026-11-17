"""Pruebas del contrato OpenAPI y códigos de validación; sin conectar a Supabase."""
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db


def db_simulada():
    # Solicitudes inválidas se rechazan antes de llegar a la consulta SQL.
    yield object()


def test_openapi_endpoints_principales():
    caminos = app.openapi()['paths']
    assert 'post' in caminos['/episodios']
    assert 'put' in caminos['/episodios/{id_episodio}']
    assert 'delete' in caminos['/episodios/{id_episodio}']
    assert 'post' in caminos['/episodios/{id_episodio}/factores']
    assert 'get' in caminos['/pacientes/{id_paciente}/resumen']
    assert 'get' in caminos['/pacientes/{id_paciente}/patrones']
    assert 'post' in caminos['/pacientes/{id_paciente}/tratamientos']


def test_rechazo_http_422_sin_conexion_real():
    app.dependency_overrides[get_db] = db_simulada
    try:
        client = TestClient(app)
        respuesta = client.post('/episodios', json={
            'id_paciente': 1, 'fecha_hora': '2026-11-16T14:00:00-06:00',
            'duracion_segundos': 0, 'tipo_crisis': 'Focal'
        })
        assert respuesta.status_code == 422
    finally:
        app.dependency_overrides.clear()
