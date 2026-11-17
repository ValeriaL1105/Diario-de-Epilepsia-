'use strict';
// API local de pruebas; no contiene ni debe contener claves de Supabase.
const API = 'http://127.0.0.1:8000';
const $ = (s) => document.querySelector(s);
let pacientesCache = [];
let factoresCache = [];
let episodiosCache = [];
let idPacienteEditando = null;
let idEpisodioEditando = null;

async function request(ruta, opciones = {}) {
  let res;
  try {
    res = await fetch(`${API}${ruta}`, {
      ...opciones,
      headers: opciones.body ? { 'Content-Type': 'application/json', ...(opciones.headers || {}) } : (opciones.headers || {}),
    });
  } catch {
    throw Error('No se pudo contactar FastAPI. Revisa que el servidor esté encendido.');
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail;
    let msg = typeof detail === 'string' ? detail : 'Datos inválidos o error de la solicitud';
    if (Array.isArray(detail)) msg = detail.map((d) => `${d.loc?.join('.') || 'campo'}: ${d.msg}`).join(' · ');
    throw Error(`HTTP ${res.status}: ${msg}`);
  }
  return data;
}
function avisar(texto, error = false) {
  const m = $('#mensaje'); m.textContent = texto; m.className = `message visible ${error ? 'error' : 'ok'}`;
  m.scrollIntoView({block: 'nearest', behavior: 'smooth'});
}
function mostrarVacio(selector, mensaje, columnas = null) {
  const el = $(selector); el.replaceChildren();
  if (columnas !== null) {
    const tr = el.insertRow(); const td = tr.insertCell(); td.colSpan = columnas; td.textContent = mensaje;
  } else { const span = document.createElement('span'); span.className = 'hint'; span.textContent = mensaje; el.append(span); }
}
function opcion(select, value, label) {
  const op = document.createElement('option'); op.value = value; op.textContent = label; select.append(op);
}
function fechaLocalActual() {
  const ahora = new Date(); return new Date(ahora.getTime() - ahora.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}
function inputFechaLocal(iso) { // ISO con zona horaria -> datetime-local en la computadora del usuario.
  const d = new Date(iso); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}
function idPaciente() { return Number($('#paciente-seleccionado').value) || null; }
function exigirSeleccion() {
  const id = idPaciente(); if (!id) throw Error('Selecciona o registra un paciente primero.'); return id;
}
async function cargarPacientes(preseleccionar = null) {
  const anterior = preseleccionar ?? idPaciente();
  pacientesCache = await request('/pacientes');
  const s = $('#paciente-seleccionado'); s.replaceChildren();
  opcion(s, '', pacientesCache.length ? 'Seleccionar paciente' : 'Registra o carga pacientes de prueba');
  pacientesCache.forEach(p => opcion(s, p.id_paciente, `${p.id_paciente} · ${p.nombre}`));
  if (anterior && pacientesCache.some(p => p.id_paciente === Number(anterior))) s.value = String(anterior);
  await cargarDatosPaciente();
}
async function cargarCatalogos() {
  const [factores, medicamentos] = await Promise.all([request('/desencadenantes'), request('/medicamentos')]);
  factoresCache = factores;
  const grid = $('#lista-desencadenantes'); grid.replaceChildren();
  factores.forEach(f => {
    const label = document.createElement('label'); label.className = 'check factor';
    const inp = document.createElement('input'); inp.type = 'checkbox'; inp.value = f.id_desencadenante; inp.name = 'factor';
    label.append(inp, document.createTextNode(`${f.categoria}: ${f.descripcion}`)); grid.append(label);
  });
  const meds = $('#medicamento'); meds.replaceChildren(); opcion(meds, '', 'Seleccionar medicamento');
  medicamentos.forEach(m => opcion(meds, m.id_medicamento, `${m.ingrediente_activo} · ${m.presentacion}`));
}
function factoresSeleccionados() {
  return [...document.querySelectorAll('input[name="factor"]:checked')].map(x => Number(x.value));
}
function etiquetasFactores(ids) {
  return ids.map(id => factoresCache.find(f => f.id_desencadenante === id)?.descripcion || `#${id}`).join(', ') || '—';
}
function filaTabla(tbody, valores, acciones) {
  const tr = tbody.insertRow();
  valores.forEach(v => { const celda = tr.insertCell(); celda.textContent = String(v ?? '—'); });
  if (acciones) {
    const td = tr.insertCell(); td.className = 'row-actions';
    acciones.forEach(({label, style, click}) => {
      const b = document.createElement('button'); b.type = 'button'; b.textContent = label;
      b.className = style; b.addEventListener('click', click); td.append(b);
    });
  }
}
async function cargarHistorial() {
  if (!idPaciente()) { episodiosCache = []; mostrarVacio('#historial', 'Selecciona un paciente.', 7); return; }
  const args = new URLSearchParams();
  if ($('#desde').value) args.set('desde', $('#desde').value);
  if ($('#hasta').value) args.set('hasta', $('#hasta').value);
  const qs = args.size ? `?${args}` : '';
  episodiosCache = await request(`/pacientes/${idPaciente()}/episodios${qs}`);
  const tbody = $('#historial'); tbody.replaceChildren();
  if (!episodiosCache.length) { mostrarVacio('#historial', 'Sin episodios para este periodo.', 7); return; }
  episodiosCache.forEach(ep => {
    filaTabla(tbody, [ep.id_episodio, new Date(ep.fecha_hora).toLocaleString('es-MX'), ep.tipo_crisis,
      `${ep.duracion_segundos} s`, etiquetasFactores(ep.ids_desencadenantes), ep.observaciones || '—'], [
        {label: 'Editar', style: 'secondary mini', click: () => editarEpisodio(ep)},
        {label: 'Eliminar', style: 'danger mini', click: () => borrarEpisodio(ep)}
    ]);
  });
}
async function cargarResumen() {
  const p = $('#resumen'); p.replaceChildren();
  if (!idPaciente()) { mostrarVacio('#resumen', 'Selecciona un paciente.'); return; }
  const r = await request(`/pacientes/${idPaciente()}/resumen`);
  const items = [
    ['Episodios totales', r.total_episodios], ['En el mes', r.episodios_mes],
    ['Duración promedio', r.duracion_promedio_segundos === null ? '—' : `${r.duracion_promedio_segundos} s`],
    ['Severidad promedio', r.severidad_promedio ?? '—'],
    ['Última crisis', r.ultima_crisis ? new Date(r.ultima_crisis).toLocaleString('es-MX') : '—']
  ];
  items.forEach(([etiqueta, valor]) => {
    const card = document.createElement('div'); card.className = 'stat';
    const k = document.createElement('small'); k.textContent = etiqueta;
    const v = document.createElement('strong'); v.textContent = String(valor);
    card.append(k, v); p.append(card);
  });
}
async function cargarPatrones() {
  const p = $('#patrones'); p.replaceChildren();
  if (!idPaciente()) { mostrarVacio('#patrones', 'Selecciona un paciente.'); return; }
  const rows = await request(`/pacientes/${idPaciente()}/patrones`);
  if (!rows.length) { mostrarVacio('#patrones', 'No hay factores asociados a los episodios.'); return; }
  rows.forEach(r => {
    const wrap = document.createElement('div'); wrap.className = 'pattern';
    const head = document.createElement('div'); head.className = 'pattern-head';
    const left = document.createElement('span'); left.textContent = `${r.descripcion} (${r.apariciones})`;
    const right = document.createElement('b'); right.textContent = `${r.porcentaje_episodios}%`;
    head.append(left, right);
    const rail = document.createElement('div'); rail.className = 'rail';
    const fill = document.createElement('div'); fill.className = 'fill';
    fill.style.width = `${Math.max(0, Math.min(100, Number(r.porcentaje_episodios) || 0))}%`;
    rail.append(fill); wrap.append(head, rail); p.append(wrap);
  });
}
async function cargarTratamientos() {
  if (!idPaciente()) { mostrarVacio('#tratamientos', 'Selecciona un paciente.', 6); return; }
  const rows = await request(`/pacientes/${idPaciente()}/tratamientos`);
  const tbody = $('#tratamientos'); tbody.replaceChildren();
  if (!rows.length) { mostrarVacio('#tratamientos', 'No hay tratamientos registrados.', 6); return; }
  rows.forEach(t => filaTabla(tbody, [t.id_tratamiento, `${t.ingrediente_activo} (${t.presentacion})`,
    t.dosis, t.frecuencia, t.fecha_inicio, t.fecha_fin || '—']));
}
async function cargarDatosPaciente() {
  if (!idPaciente()) {
    episodiosCache = [];
    mostrarVacio('#historial', 'Selecciona un paciente.', 7);
    mostrarVacio('#resumen', 'Selecciona un paciente.');
    mostrarVacio('#patrones', 'Selecciona un paciente.');
    mostrarVacio('#tratamientos', 'Selecciona un paciente.', 6);
    return;
  }
  // Las secciones siguen independientes: si una falla, se informa sin perder todas las demás.
  const results = await Promise.allSettled([cargarHistorial(), cargarResumen(), cargarPatrones(), cargarTratamientos()]);
  const errors = results.filter(x => x.status === 'rejected');
  if (errors.length) avisar(errors[0].reason.message || 'Error al consultar datos', true);
}

function resetPaciente() {
  idPacienteEditando = null; $('#form-paciente').reset();
  $('#titulo-form-paciente').textContent = 'Crear paciente';
  $('#guardar-paciente').textContent = 'Guardar paciente'; $('#cancelar-paciente').classList.add('hidden');
}
function resetEpisodio() {
  idEpisodioEditando = null; $('#form-episodio').reset(); $('#fecha_hora').value = fechaLocalActual();
  $('#guardar-episodio').textContent = 'Guardar episodio'; $('#cancelar-episodio').classList.add('hidden');
}
function editarEpisodio(ep) {
  idEpisodioEditando = ep.id_episodio;
  $('#fecha_hora').value = inputFechaLocal(ep.fecha_hora);
  $('#duracion').value = ep.duracion_segundos; $('#tipo_crisis').value = ep.tipo_crisis;
  $('#severidad').value = ep.nivel_severidad ?? '';
  $('#perdida_conocimiento').checked = ep.perdida_conocimiento;
  $('#observaciones').value = ep.observaciones || '';
  document.querySelectorAll('input[name="factor"]').forEach(ch => {
    ch.checked = ep.ids_desencadenantes.includes(Number(ch.value));
  });
  $('#guardar-episodio').textContent = 'Actualizar episodio';
  $('#cancelar-episodio').classList.remove('hidden');
  $('#panel-episodio').scrollIntoView({behavior: 'smooth'});
}
async function borrarEpisodio(ep) {
  if (!confirm(`¿Eliminar el episodio #${ep.id_episodio}? Esta acción no puede deshacerse.`)) return;
  try {
    await request(`/episodios/${ep.id_episodio}`, {method: 'DELETE'});
    if (idEpisodioEditando === ep.id_episodio) resetEpisodio();
    await cargarDatosPaciente(); avisar(`Episodio #${ep.id_episodio} eliminado.`);
  } catch (e) { avisar(e.message, true); }
}

$('#form-paciente').addEventListener('submit', async ev => {
  ev.preventDefault();
  try {
    const datos = {nombre: $('#nombre').value, fecha_nacimiento: $('#fecha_nacimiento').value || null,
      sexo: $('#sexo').value || null, telefono: $('#telefono').value || null};
    const editar = idPacienteEditando !== null;
    const res = await request(editar ? `/pacientes/${idPacienteEditando}` : '/pacientes', {
      method: editar ? 'PUT' : 'POST', body: JSON.stringify(datos)
    });
    resetPaciente(); await cargarPacientes(res.id_paciente);
    avisar(`Paciente #${res.id_paciente} ${editar ? 'actualizado' : 'creado'} correctamente.`);
  } catch (e) { avisar(e.message, true); }
});
$('#editar-paciente').addEventListener('click', () => {
  try {
    const id = exigirSeleccion(); const p = pacientesCache.find(x => x.id_paciente === id);
    if (!p) throw Error('Paciente no encontrado en la lista.');
    idPacienteEditando = id; $('#nombre').value = p.nombre;
    $('#fecha_nacimiento').value = p.fecha_nacimiento || '';
    $('#sexo').value = p.sexo || ''; $('#telefono').value = p.telefono || '';
    $('#titulo-form-paciente').textContent = `Editar paciente #${id}`;
    $('#guardar-paciente').textContent = 'Guardar cambios';
    $('#cancelar-paciente').classList.remove('hidden');
  } catch (e) { avisar(e.message, true); }
});
$('#cancelar-paciente').addEventListener('click', resetPaciente);
$('#borrar-paciente').addEventListener('click', async () => {
  try {
    const id = exigirSeleccion();
    if (!confirm(`¿Eliminar paciente #${id}? Solo se permite si no tiene episodios ni tratamientos asociados.`)) return;
    await request(`/pacientes/${id}`, {method: 'DELETE'});
    resetPaciente(); resetEpisodio(); await cargarPacientes();
    avisar(`Paciente #${id} eliminado.`);
  } catch (e) { avisar(e.message, true); }
});
$('#form-episodio').addEventListener('submit', async ev => {
  ev.preventDefault();
  try {
    const id = exigirSeleccion();
    const datos = {id_paciente: id, fecha_hora: new Date($('#fecha_hora').value).toISOString(),
      duracion_segundos: Number($('#duracion').value), tipo_crisis: $('#tipo_crisis').value,
      nivel_severidad: $('#severidad').value ? Number($('#severidad').value) : null,
      perdida_conocimiento: $('#perdida_conocimiento').checked,
      observaciones: $('#observaciones').value || null,
      ids_desencadenantes: factoresSeleccionados()};
    const editar = idEpisodioEditando !== null;
    const ep = await request(editar ? `/episodios/${idEpisodioEditando}` : '/episodios', {
      method: editar ? 'PUT' : 'POST', body: JSON.stringify(datos)
    });
    resetEpisodio(); await cargarDatosPaciente();
    avisar(`Episodio #${ep.id_episodio} ${editar ? 'actualizado' : 'guardado'} correctamente (${ep.ids_desencadenantes.length} factores).`);
  } catch (e) { avisar(e.message, true); }
});
$('#cancelar-episodio').addEventListener('click', resetEpisodio);
$('#form-tratamiento').addEventListener('submit', async ev => {
  ev.preventDefault();
  try {
    const id = exigirSeleccion();
    const t = await request(`/pacientes/${id}/tratamientos`, {method: 'POST', body: JSON.stringify({
      id_medicamento: Number($('#medicamento').value), dosis: $('#dosis').value,
      frecuencia: $('#frecuencia').value, fecha_inicio: $('#inicio-tratamiento').value,
      fecha_fin: $('#fin-tratamiento').value || null
    })});
    $('#form-tratamiento').reset(); await cargarTratamientos();
    avisar(`Tratamiento ficticio #${t.id_tratamiento} registrado.`);
  } catch (e) { avisar(e.message, true); }
});
$('#paciente-seleccionado').addEventListener('change', () => {
  resetEpisodio(); resetPaciente(); cargarDatosPaciente().catch(e => avisar(e.message, true));
});
$('#filtrar').addEventListener('click', () => cargarHistorial().catch(e => avisar(e.message, true)));
$('#recargar').addEventListener('click', () => cargarDatosPaciente().catch(e => avisar(e.message, true)));
$('#limpiar-filtros').addEventListener('click', () => {
  $('#desde').value = ''; $('#hasta').value = '';
  cargarHistorial().catch(e => avisar(e.message, true));
});

resetEpisodio();
(async function iniciar() {
  try { await cargarCatalogos(); await cargarPacientes(); }
  catch (e) { avisar(e.message, true); }
})();
