// api.js – cliente centralizado para todos los fetch al backend
const API = {
  base: '',  // mismo origen, Flask sirve el frontend

  async get(path) {
    const r = await fetch(this.base + path, {credentials: 'same-origin'});
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'Error del servidor');
    return j.data;
  },

  async post(path, body) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'Error del servidor');
    return j.data;
  },

  async put(path, body) {
    const r = await fetch(this.base + path, {
      method: 'PUT',
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'Error del servidor');
    return j.data;
  },

  async patch(path, body) {
    const r = await fetch(this.base + path, {
      method: 'PATCH',
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'Error del servidor');
    return j.data;
  },

  async delete(path) {
    const r = await fetch(this.base + path, {method: 'DELETE', credentials: 'same-origin'});
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'Error del servidor');
    return j.data;
  }
};

// Toast global
function showToast(msg, tipo) {
  var t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.style.display = 'block';
  t.style.background = tipo === 'error' ? 'var(--red,#ef4444)' : '';
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.style.display = 'none'; }, 3500);
}

// WhatsApp
function abrirWA(tel, msg) {
  var num = '549' + tel.replace(/\D/g, '');
  window.open('https://wa.me/' + num + '?text=' + encodeURIComponent(msg), '_blank');
}

function comprobante(alumno, concepto, monto, forma) {
  var fecha = new Date().toLocaleDateString('es-AR');
  return '🏫 Cooperadora Escolar\nComprobante de pago\n─────────────────────\n' +
    'Alumno/a: ' + alumno + '\nConcepto: ' + concepto +
    '\nMonto: $' + Number(monto).toLocaleString('es-AR') +
    '\nForma de pago: ' + forma + '\nFecha: ' + fecha +
    '\n─────────────────────\n¡Gracias por su pago!';
}
