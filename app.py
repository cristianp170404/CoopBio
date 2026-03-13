from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

DB_PATH = os.environ.get('DB_PATH', 'cooperadora.db')

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def ok(data=None, status=200):
    return jsonify({'ok': True, 'data': data}), status

def err(msg, status=400):
    return jsonify({'ok': False, 'error': msg}), status

# ── Inicialización de la BD ───────────────────────────────────────────────────

def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS alumnos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            apellido  TEXT NOT NULL,
            nombre    TEXT NOT NULL,
            dni       TEXT NOT NULL UNIQUE,
            anio      TEXT NOT NULL,
            tel_alumno TEXT DEFAULT '',
            tel_tutor  TEXT NOT NULL,
            activo    INTEGER DEFAULT 1,
            creado_en TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS cuotas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            alumno_id   INTEGER NOT NULL REFERENCES alumnos(id),
            concepto    TEXT NOT NULL,         -- 'Cuota mensual' | 'Matrícula'
            mes         TEXT,                  -- 'Marzo 2026' (solo para cuotas)
            monto       REAL NOT NULL,
            estado      TEXT DEFAULT 'Pendiente', -- Pendiente | Pagado | Vencido
            forma_pago  TEXT DEFAULT '',
            obs         TEXT DEFAULT '',
            fecha_pago  TEXT,
            creado_en   TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS eventos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            fecha       TEXT,
            tipo        TEXT DEFAULT 'Otro',
            descripcion TEXT DEFAULT '',
            estado      TEXT DEFAULT 'Próximo', -- Próximo | Activo | Finalizado
            creado_en   TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS evento_cobros (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            evento_id   INTEGER NOT NULL REFERENCES eventos(id),
            alumno_id   INTEGER REFERENCES alumnos(id),
            alumno_txt  TEXT,   -- fallback si no existe en padrón
            tel_tutor   TEXT DEFAULT '',
            detalle     TEXT DEFAULT '',
            monto       REAL NOT NULL,
            forma_pago  TEXT DEFAULT 'Efectivo',
            estado      TEXT DEFAULT 'Pagado',
            fecha_pago  TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prendas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            talle       TEXT NOT NULL,
            color       TEXT DEFAULT '',
            stock       INTEGER DEFAULT 0,
            precio      REAL NOT NULL,
            creado_en   TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS reservas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            alumno_id   INTEGER REFERENCES alumnos(id),
            prenda_id   INTEGER REFERENCES prendas(id),
            alumno_txt  TEXT,
            prenda_txt  TEXT,
            tel_tutor   TEXT DEFAULT '',
            precio      REAL NOT NULL,
            sena        REAL DEFAULT 0,
            saldo       REAL DEFAULT 0,
            forma_pago  TEXT DEFAULT 'Efectivo',
            fecha_entrega TEXT,
            estado      TEXT DEFAULT 'Con seña', -- Con seña | Pagado | Entregado
            creado_en   TEXT DEFAULT (datetime('now','localtime'))
        );
        """)

        # Datos de ejemplo si la BD está vacía
        cur = conn.execute("SELECT COUNT(*) FROM alumnos")
        if cur.fetchone()[0] == 0:
            _seed_demo(conn)

def _seed_demo(conn):
    alumnos = [
        ('García','Lucía','38123456','3° año','11 1234-5678','11 8765-4321'),
        ('Pérez','Tomás','39456789','5° año','11 2345-6789','11 7654-3210'),
        ('López','Ana','40111222','2° año','11 3456-7890','11 6543-2109'),
        ('Martínez','Juan','41222333','1° año','11 4567-8901','11 5432-1098'),
        ('Romero','Valentina','37888999','4° año','11 5678-9012','11 4321-0987'),
        ('Ruiz','Martina','42333444','2° año','11 6789-0123','11 3210-9876'),
        ('Sosa','Diego','43444555','6° año','11 7890-1234','11 2109-8765'),
        ('Núñez','Sofía','44111000','3° año','11 8901-2345','11 1098-7654'),
        ('Vega','Carlos','36777888','6° año','11 9012-3456','11 0987-6543'),
    ]
    conn.executemany(
        "INSERT INTO alumnos (apellido,nombre,dni,anio,tel_alumno,tel_tutor) VALUES (?,?,?,?,?,?)",
        alumnos
    )

    prendas = [
        ('Campera','T12','Azul',5,8500),
        ('Campera','T14','Azul',3,8500),
        ('Campera','T16','Azul',2,8500),
        ('Buzo','T12','Gris',8,6500),
        ('Buzo','T14','Gris',4,6500),
        ('Buzo','T10','Gris',0,6500),
        ('Pantalón','T10','Azul marino',6,4200),
        ('Pantalón','T12','Azul marino',4,4200),
        ('Remera','T8','Blanca',10,2800),
        ('Remera','T10','Blanca',7,2800),
    ]
    conn.executemany(
        "INSERT INTO prendas (nombre,talle,color,stock,precio) VALUES (?,?,?,?,?)",
        prendas
    )

    cuotas_demo = [
        (1,'Cuota mensual','Marzo 2026',3500,'Pagado','Débito','05/03/2026'),
        (2,'Cuota mensual','Marzo 2026',3500,'Pagado','Efectivo','03/03/2026'),
        (3,'Cuota mensual','Marzo 2026',3500,'Pendiente','',''),
        (4,'Cuota mensual','Marzo 2026',3500,'Vencido','',''),
        (5,'Cuota mensual','Marzo 2026',3500,'Pagado','Efectivo','07/03/2026'),
        (6,'Cuota mensual','Marzo 2026',3500,'Pendiente','',''),
        (7,'Cuota mensual','Marzo 2026',3500,'Pagado','Débito','06/03/2026'),
        (8,'Cuota mensual','Marzo 2026',3500,'Pagado','Efectivo','04/03/2026'),
        (9,'Cuota mensual','Marzo 2026',3500,'Vencido','',''),
        (1,'Matrícula',None,5000,'Pagado','Débito','10/02/2026'),
        (2,'Matrícula',None,5000,'Pagado','Efectivo','08/02/2026'),
        (3,'Matrícula',None,5000,'Pendiente','',''),
        (4,'Matrícula',None,5000,'Vencido','',''),
    ]
    for c in cuotas_demo:
        conn.execute(
            "INSERT INTO cuotas (alumno_id,concepto,mes,monto,estado,forma_pago,fecha_pago) VALUES (?,?,?,?,?,?,?)",
            c
        )

    eventos = [
        ('Locro patriótico','25/05/2026','Venta de comida','Venta de porciones de locro – precio unitario $1.200','Activo'),
        ('Venta productos limpieza','Abril 2026','Venta de productos','Detergente, limpiador multiuso, esponja x3','Próximo'),
        ('Rifa anual','Agosto 2026','Rifas','Rifa con premios donados por comercios del barrio','Próximo'),
    ]
    conn.executemany(
        "INSERT INTO eventos (nombre,fecha,tipo,descripcion,estado) VALUES (?,?,?,?,?)",
        eventos
    )

    reservas = [
        (6,1,'Ruiz, Martina','Campera Azul T12','11 3210-9876',8500,6500,2000,'Efectivo','15/03/2026','Con seña'),
        (7,5,'Sosa, Diego','Buzo Gris T14','11 2109-8765',6500,5000,1500,'Débito','20/03/2026','Con seña'),
        (8,7,'Núñez, Sofía','Pantalón T10','11 1098-7654',4200,4200,0,'Efectivo','22/03/2026','Pagado'),
        (9,3,'Vega, Carlos','Campera Azul T16','11 0987-6543',8500,8500,0,'Débito','10/03/2026','Entregado'),
    ]
    for r in reservas:
        conn.execute(
            "INSERT INTO reservas (alumno_id,prenda_id,alumno_txt,prenda_txt,tel_tutor,precio,sena,saldo,forma_pago,fecha_entrega,estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            r
        )

# ── Servir el frontend ────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_html(filename):
    if filename.endswith('.html'):
        return render_template(filename)
    return send_from_directory('static', filename)

# ── API: ALUMNOS ──────────────────────────────────────────────────────────────

@app.route('/api/alumnos', methods=['GET'])
def listar_alumnos():
    q = request.args.get('q', '').lower()
    anio = request.args.get('anio', '')
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM alumnos WHERE activo=1 ORDER BY apellido,nombre").fetchall()
    alumnos = [dict(r) for r in rows]
    if q:
        alumnos = [a for a in alumnos if q in (a['apellido']+' '+a['nombre']+' '+a['dni']).lower()]
    if anio:
        alumnos = [a for a in alumnos if a['anio'] == anio]
    return ok(alumnos)

@app.route('/api/alumnos', methods=['POST'])
def crear_alumno():
    d = request.json or {}
    for campo in ['apellido', 'nombre', 'dni', 'anio', 'tel_tutor']:
        if not d.get(campo):
            return err(f'Campo requerido: {campo}')
    try:
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO alumnos (apellido,nombre,dni,anio,tel_alumno,tel_tutor) VALUES (?,?,?,?,?,?)",
                (d['apellido'], d['nombre'], d['dni'], d['anio'], d.get('tel_alumno',''), d['tel_tutor'])
            )
            alumno_id = cur.lastrowid
        return ok({'id': alumno_id, **d}, 201)
    except sqlite3.IntegrityError:
        return err('Ya existe un alumno con ese DNI')

@app.route('/api/alumnos/<int:id>', methods=['PUT'])
def editar_alumno(id):
    d = request.json or {}
    with get_db() as conn:
        conn.execute(
            "UPDATE alumnos SET apellido=?,nombre=?,dni=?,anio=?,tel_alumno=?,tel_tutor=? WHERE id=?",
            (d.get('apellido'), d.get('nombre'), d.get('dni'), d.get('anio'),
             d.get('tel_alumno',''), d.get('tel_tutor'), id)
        )
    return ok({'id': id})

@app.route('/api/alumnos/<int:id>', methods=['DELETE'])
def eliminar_alumno(id):
    with get_db() as conn:
        conn.execute("UPDATE alumnos SET activo=0 WHERE id=?", (id,))
    return ok()

# ── API: CUOTAS ───────────────────────────────────────────────────────────────

@app.route('/api/cuotas', methods=['GET'])
def listar_cuotas():
    concepto = request.args.get('concepto', 'Cuota mensual')
    mes = request.args.get('mes', '')
    with get_db() as conn:
        if mes:
            rows = conn.execute("""
                SELECT c.*, a.apellido, a.nombre, a.anio, a.tel_tutor
                FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
                WHERE c.concepto=? AND c.mes=? ORDER BY a.apellido,a.nombre
            """, (concepto, mes)).fetchall()
        else:
            rows = conn.execute("""
                SELECT c.*, a.apellido, a.nombre, a.anio, a.tel_tutor
                FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
                WHERE c.concepto=? ORDER BY a.apellido,a.nombre
            """, (concepto,)).fetchall()
    return ok([dict(r) for r in rows])

@app.route('/api/cuotas/historial', methods=['GET'])
def historial_cuotas():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT c.*, a.apellido, a.nombre, a.tel_tutor
            FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
            WHERE c.estado='Pagado'
            ORDER BY c.fecha_pago DESC LIMIT 100
        """).fetchall()
    return ok([dict(r) for r in rows])

@app.route('/api/cuotas/<int:id>/pagar', methods=['POST'])
def pagar_cuota(id):
    d = request.json or {}
    fecha = d.get('fecha_pago', datetime.now().strftime('%d/%m/%Y'))
    with get_db() as conn:
        conn.execute(
            "UPDATE cuotas SET estado='Pagado', forma_pago=?, fecha_pago=?, obs=? WHERE id=?",
            (d.get('forma_pago','Efectivo'), fecha, d.get('obs',''), id)
        )
    return ok()

@app.route('/api/cuotas', methods=['POST'])
def registrar_pago():
    """Registra un pago libre (puede crear cuota nueva si no existe)."""
    d = request.json or {}
    alumno_id = d.get('alumno_id')
    concepto = d.get('concepto', 'Cuota mensual')
    mes = d.get('mes')
    monto = d.get('monto')
    if not alumno_id or not monto:
        return err('alumno_id y monto son requeridos')
    fecha = d.get('fecha_pago', datetime.now().strftime('%d/%m/%Y'))
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM cuotas WHERE alumno_id=? AND concepto=? AND mes IS ?",
            (alumno_id, concepto, mes)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE cuotas SET estado='Pagado',forma_pago=?,fecha_pago=?,monto=?,obs=? WHERE id=?",
                (d.get('forma_pago','Efectivo'), fecha, monto, d.get('obs',''), existing['id'])
            )
            return ok({'id': existing['id']})
        else:
            cur = conn.execute(
                "INSERT INTO cuotas (alumno_id,concepto,mes,monto,estado,forma_pago,fecha_pago,obs) VALUES (?,?,?,?,'Pagado',?,?,?)",
                (alumno_id, concepto, mes, monto, d.get('forma_pago','Efectivo'), fecha, d.get('obs',''))
            )
            return ok({'id': cur.lastrowid}, 201)

# ── API: EVENTOS ──────────────────────────────────────────────────────────────

@app.route('/api/eventos', methods=['GET'])
def listar_eventos():
    with get_db() as conn:
        eventos = [dict(r) for r in conn.execute("SELECT * FROM eventos ORDER BY id").fetchall()]
        for ev in eventos:
            cobros = conn.execute("""
                SELECT ec.*, a.apellido, a.nombre
                FROM evento_cobros ec
                LEFT JOIN alumnos a ON ec.alumno_id=a.id
                WHERE ec.evento_id=?
            """, (ev['id'],)).fetchall()
            ev['participantes'] = [dict(c) for c in cobros]
    return ok(eventos)

@app.route('/api/eventos', methods=['POST'])
def crear_evento():
    d = request.json or {}
    if not d.get('nombre'):
        return err('El nombre es requerido')
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO eventos (nombre,fecha,tipo,descripcion,estado) VALUES (?,?,?,?,?)",
            (d['nombre'], d.get('fecha',''), d.get('tipo','Otro'), d.get('descripcion',''), d.get('estado','Próximo'))
        )
    return ok({'id': cur.lastrowid}, 201)

@app.route('/api/eventos/<int:id>', methods=['PUT'])
def editar_evento(id):
    d = request.json or {}
    with get_db() as conn:
        conn.execute(
            "UPDATE eventos SET nombre=?,fecha=?,tipo=?,descripcion=?,estado=? WHERE id=?",
            (d.get('nombre'), d.get('fecha'), d.get('tipo'), d.get('descripcion'), d.get('estado'), id)
        )
    return ok()

@app.route('/api/eventos/<int:id>/cobros', methods=['POST'])
def registrar_cobro_evento(id):
    d = request.json or {}
    monto = d.get('monto')
    if not monto:
        return err('El monto es requerido')
    with get_db() as conn:
        existing = None
        if d.get('alumno_id'):
            existing = conn.execute(
                "SELECT id FROM evento_cobros WHERE evento_id=? AND alumno_id=?",
                (id, d['alumno_id'])
            ).fetchone()
        if existing:
            conn.execute(
                "UPDATE evento_cobros SET monto=?,forma_pago=?,estado='Pagado',fecha_pago=? WHERE id=?",
                (monto, d.get('forma_pago','Efectivo'), datetime.now().strftime('%d/%m/%Y'), existing['id'])
            )
        else:
            conn.execute(
                "INSERT INTO evento_cobros (evento_id,alumno_id,alumno_txt,tel_tutor,detalle,monto,forma_pago,fecha_pago) VALUES (?,?,?,?,?,?,?,?)",
                (id, d.get('alumno_id'), d.get('alumno_txt',''), d.get('tel_tutor',''),
                 d.get('detalle',''), monto, d.get('forma_pago','Efectivo'),
                 datetime.now().strftime('%d/%m/%Y'))
            )
    return ok()

# ── API: PRENDAS / INDUMENTARIA ───────────────────────────────────────────────

@app.route('/api/prendas', methods=['GET'])
def listar_prendas():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT p.*,
                COALESCE((SELECT SUM(1) FROM reservas r WHERE r.prenda_id=p.id AND r.estado != 'Entregado'),0) AS reservado
            FROM prendas p ORDER BY p.nombre, p.talle
        """).fetchall()
    return ok([dict(r) for r in rows])

@app.route('/api/prendas', methods=['POST'])
def crear_prenda():
    d = request.json or {}
    if not d.get('nombre') or not d.get('precio'):
        return err('nombre y precio son requeridos')
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO prendas (nombre,talle,color,stock,precio) VALUES (?,?,?,?,?)",
            (d['nombre'], d.get('talle',''), d.get('color',''), int(d.get('stock',0)), float(d['precio']))
        )
    return ok({'id': cur.lastrowid}, 201)

@app.route('/api/prendas/<int:id>/stock', methods=['PATCH'])
def ajustar_stock(id):
    d = request.json or {}
    nuevo = d.get('stock')
    if nuevo is None:
        return err('stock requerido')
    with get_db() as conn:
        conn.execute("UPDATE prendas SET stock=? WHERE id=?", (int(nuevo), id))
    return ok()

# ── API: RESERVAS ─────────────────────────────────────────────────────────────

@app.route('/api/reservas', methods=['GET'])
def listar_reservas():
    estado = request.args.get('estado', '')
    q = request.args.get('q', '').lower()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM reservas ORDER BY creado_en DESC").fetchall()
    reservas = [dict(r) for r in rows]
    if estado:
        reservas = [r for r in reservas if r['estado'] == estado]
    if q:
        reservas = [r for r in reservas if q in (r.get('alumno_txt','') + ' ' + r.get('prenda_txt','')).lower()]
    return ok(reservas)

@app.route('/api/reservas', methods=['POST'])
def crear_reserva():
    d = request.json or {}
    precio = float(d.get('precio', 0))
    sena = float(d.get('sena', 0))
    saldo = max(0, precio - sena)
    if not precio:
        return err('El precio es requerido')
    estado = 'Pagado' if saldo == 0 else 'Con seña'
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO reservas (alumno_id,prenda_id,alumno_txt,prenda_txt,tel_tutor,precio,sena,saldo,forma_pago,fecha_entrega,estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (d.get('alumno_id'), d.get('prenda_id'), d.get('alumno_txt',''),
             d.get('prenda_txt',''), d.get('tel_tutor',''),
             precio, sena, saldo, d.get('forma_pago','Efectivo'),
             d.get('fecha_entrega',''), estado)
        )
    return ok({'id': cur.lastrowid, 'estado': estado, 'saldo': saldo}, 201)

@app.route('/api/reservas/<int:id>/cobrar-saldo', methods=['POST'])
def cobrar_saldo_reserva(id):
    d = request.json or {}
    monto = float(d.get('monto', 0))
    if not monto:
        return err('Monto requerido')
    with get_db() as conn:
        r = conn.execute("SELECT * FROM reservas WHERE id=?", (id,)).fetchone()
        if not r:
            return err('Reserva no encontrada', 404)
        nuevo_saldo = max(0, r['saldo'] - monto)
        nuevo_estado = 'Pagado' if nuevo_saldo == 0 else r['estado']
        conn.execute(
            "UPDATE reservas SET saldo=?, sena=sena+?, estado=?, forma_pago=? WHERE id=?",
            (nuevo_saldo, monto, nuevo_estado, d.get('forma_pago', r['forma_pago']), id)
        )
    return ok({'saldo': nuevo_saldo, 'estado': nuevo_estado})

@app.route('/api/reservas/<int:id>/entregar', methods=['POST'])
def entregar_reserva(id):
    with get_db() as conn:
        r = conn.execute("SELECT * FROM reservas WHERE id=?", (id,)).fetchone()
        if not r:
            return err('Reserva no encontrada', 404)
        if r['saldo'] > 0:
            return err(f"Hay saldo pendiente de ${r['saldo']:,.0f}")
        conn.execute("UPDATE reservas SET estado='Entregado' WHERE id=?", (id,))
    return ok()

# ── API: DASHBOARD ────────────────────────────────────────────────────────────

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    with get_db() as conn:
        alumnos_activos = conn.execute("SELECT COUNT(*) FROM alumnos WHERE activo=1").fetchone()[0]

        mes_actual = datetime.now().strftime('%B %Y').capitalize()
        meses_es = {
            'January':'Enero','February':'Febrero','March':'Marzo','April':'Abril',
            'May':'Mayo','June':'Junio','July':'Julio','August':'Agosto',
            'September':'Septiembre','October':'Octubre','November':'Noviembre','December':'Diciembre'
        }
        for en, es in meses_es.items():
            mes_actual = mes_actual.replace(en, es)

        cuotas_mes = conn.execute("""
            SELECT COUNT(*) as total, SUM(monto) as suma
            FROM cuotas WHERE concepto='Cuota mensual' AND mes LIKE ? AND estado='Pagado'
        """, (f'%{datetime.now().year}%',)).fetchone()

        pendientes = conn.execute("""
            SELECT COUNT(*) as cnt, SUM(monto) as suma
            FROM cuotas WHERE estado IN ('Pendiente','Vencido')
        """).fetchone()

        stock_total = conn.execute("""
            SELECT COALESCE(SUM(p.stock),0) as total,
                   COALESCE((SELECT COUNT(*) FROM reservas WHERE estado != 'Entregado'),0) as reservado
            FROM prendas p
        """).fetchone()

        ultimos_pagos = conn.execute("""
            SELECT c.*, a.apellido, a.nombre, a.tel_tutor
            FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
            WHERE c.estado='Pagado'
            ORDER BY c.fecha_pago DESC LIMIT 5
        """).fetchall()

        reservas_pendientes = conn.execute("""
            SELECT * FROM reservas WHERE estado IN ('Con seña','Pagado')
            ORDER BY creado_en DESC LIMIT 4
        """).fetchall()

        eventos = conn.execute(
            "SELECT * FROM eventos ORDER BY id LIMIT 4"
        ).fetchall()

    return ok({
        'alumnos_activos': alumnos_activos,
        'cuotas_cobradas_mes': {'total': cuotas_mes['suma'] or 0, 'cantidad': cuotas_mes['total'] or 0},
        'pendientes': {'cantidad': pendientes['cnt'] or 0, 'suma': pendientes['suma'] or 0},
        'stock': {'total': stock_total['total'], 'reservado': stock_total['reservado']},
        'ultimos_pagos': [dict(r) for r in ultimos_pagos],
        'reservas_pendientes': [dict(r) for r in reservas_pendientes],
        'eventos': [dict(r) for r in eventos],
    })

# ── Boot ──────────────────────────────────────────────────────────────────────

with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'false').lower() == 'true')
