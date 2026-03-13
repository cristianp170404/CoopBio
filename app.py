from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

# Rutas absolutas para que funcione en cualquier entorno
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')

# CORS manual – sin flask-cors
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    return response

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

# DB_PATH: usa disco persistente en Render, o local si no está configurado
DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'cooperadora.db'))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def ok(data=None, status=200):
    return jsonify({'ok': True, 'data': data}), status

def err(msg, status=400):
    return jsonify({'ok': False, 'error': msg}), status

def init_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS alumnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        apellido TEXT NOT NULL, nombre TEXT NOT NULL,
        dni TEXT NOT NULL UNIQUE, anio TEXT NOT NULL,
        tel_alumno TEXT DEFAULT '', tel_tutor TEXT NOT NULL,
        activo INTEGER DEFAULT 1,
        creado_en TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS cuotas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER NOT NULL REFERENCES alumnos(id),
        concepto TEXT NOT NULL, mes TEXT,
        monto REAL NOT NULL, estado TEXT DEFAULT 'Pendiente',
        forma_pago TEXT DEFAULT '', obs TEXT DEFAULT '', fecha_pago TEXT,
        creado_en TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS eventos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL, fecha TEXT,
        tipo TEXT DEFAULT 'Otro', descripcion TEXT DEFAULT '',
        estado TEXT DEFAULT 'Proximo',
        creado_en TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS evento_cobros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evento_id INTEGER NOT NULL REFERENCES eventos(id),
        alumno_id INTEGER REFERENCES alumnos(id),
        alumno_txt TEXT DEFAULT '', tel_tutor TEXT DEFAULT '',
        detalle TEXT DEFAULT '', monto REAL NOT NULL,
        forma_pago TEXT DEFAULT 'Efectivo', estado TEXT DEFAULT 'Pagado',
        fecha_pago TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS prendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL, talle TEXT NOT NULL,
        color TEXT DEFAULT '', stock INTEGER DEFAULT 0, precio REAL NOT NULL,
        creado_en TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER REFERENCES alumnos(id),
        prenda_id INTEGER REFERENCES prendas(id),
        alumno_txt TEXT DEFAULT '', prenda_txt TEXT DEFAULT '',
        tel_tutor TEXT DEFAULT '', precio REAL NOT NULL,
        sena REAL DEFAULT 0, saldo REAL DEFAULT 0,
        forma_pago TEXT DEFAULT 'Efectivo',
        fecha_entrega TEXT DEFAULT '', estado TEXT DEFAULT 'Con sena',
        creado_en TEXT DEFAULT (datetime('now','localtime'))
    );
    """)
    cur = conn.execute("SELECT COUNT(*) FROM alumnos")
    if cur.fetchone()[0] == 0:
        _seed_demo(conn)
    conn.commit()
    conn.close()

def _seed_demo(conn):
    alumnos = [
        ('Garcia','Lucia','38123456','3 anio','11 1234-5678','11 8765-4321'),
        ('Perez','Tomas','39456789','5 anio','11 2345-6789','11 7654-3210'),
        ('Lopez','Ana','40111222','2 anio','11 3456-7890','11 6543-2109'),
        ('Martinez','Juan','41222333','1 anio','11 4567-8901','11 5432-1098'),
        ('Romero','Valentina','37888999','4 anio','11 5678-9012','11 4321-0987'),
        ('Ruiz','Martina','42333444','2 anio','11 6789-0123','11 3210-9876'),
        ('Sosa','Diego','43444555','6 anio','11 7890-1234','11 2109-8765'),
        ('Nunez','Sofia','44111000','3 anio','11 8901-2345','11 1098-7654'),
        ('Vega','Carlos','36777888','6 anio','11 9012-3456','11 0987-6543'),
    ]
    conn.executemany("INSERT INTO alumnos (apellido,nombre,dni,anio,tel_alumno,tel_tutor) VALUES (?,?,?,?,?,?)", alumnos)
    prendas = [
        ('Campera','T12','Azul',5,8500),('Campera','T14','Azul',3,8500),('Campera','T16','Azul',2,8500),
        ('Buzo','T12','Gris',8,6500),('Buzo','T14','Gris',4,6500),('Buzo','T10','Gris',0,6500),
        ('Pantalon','T10','Azul marino',6,4200),('Pantalon','T12','Azul marino',4,4200),
        ('Remera','T8','Blanca',10,2800),('Remera','T10','Blanca',7,2800),
    ]
    conn.executemany("INSERT INTO prendas (nombre,talle,color,stock,precio) VALUES (?,?,?,?,?)", prendas)
    cuotas_demo = [
        (1,'Cuota mensual','Marzo 2026',3500,'Pagado','Debito','05/03/2026'),
        (2,'Cuota mensual','Marzo 2026',3500,'Pagado','Efectivo','03/03/2026'),
        (3,'Cuota mensual','Marzo 2026',3500,'Pendiente','',''),
        (4,'Cuota mensual','Marzo 2026',3500,'Vencido','',''),
        (5,'Cuota mensual','Marzo 2026',3500,'Pagado','Efectivo','07/03/2026'),
        (6,'Cuota mensual','Marzo 2026',3500,'Pendiente','',''),
        (7,'Cuota mensual','Marzo 2026',3500,'Pagado','Debito','06/03/2026'),
        (8,'Cuota mensual','Marzo 2026',3500,'Pagado','Efectivo','04/03/2026'),
        (9,'Cuota mensual','Marzo 2026',3500,'Vencido','',''),
        (1,'Matricula',None,5000,'Pagado','Debito','10/02/2026'),
        (2,'Matricula',None,5000,'Pagado','Efectivo','08/02/2026'),
        (3,'Matricula',None,5000,'Pendiente','',''),
        (4,'Matricula',None,5000,'Vencido','',''),
    ]
    for c in cuotas_demo:
        conn.execute("INSERT INTO cuotas (alumno_id,concepto,mes,monto,estado,forma_pago,fecha_pago) VALUES (?,?,?,?,?,?,?)", c)
    eventos = [
        ('Locro patriotico','25/05/2026','Venta de comida','Venta de porciones de locro','Activo'),
        ('Venta productos limpieza','Abril 2026','Venta de productos','Detergente, limpiador, esponja','Proximo'),
        ('Rifa anual','Agosto 2026','Rifas','Rifa con premios donados','Proximo'),
    ]
    conn.executemany("INSERT INTO eventos (nombre,fecha,tipo,descripcion,estado) VALUES (?,?,?,?,?)", eventos)
    reservas = [
        (6,1,'Ruiz, Martina','Campera Azul T12','11 3210-9876',8500,6500,2000,'Efectivo','15/03/2026','Con sena'),
        (7,5,'Sosa, Diego','Buzo Gris T14','11 2109-8765',6500,5000,1500,'Debito','20/03/2026','Con sena'),
        (8,7,'Nunez, Sofia','Pantalon T10','11 1098-7654',4200,4200,0,'Efectivo','22/03/2026','Pagado'),
        (9,3,'Vega, Carlos','Campera Azul T16','11 0987-6543',8500,8500,0,'Debito','10/03/2026','Entregado'),
    ]
    for r in reservas:
        conn.execute("INSERT INTO reservas (alumno_id,prenda_id,alumno_txt,prenda_txt,tel_tutor,precio,sena,saldo,forma_pago,fecha_entrega,estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)", r)

# ── Servir frontend ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith('.html'):
        html_path = os.path.join(TEMPLATES_DIR, filename)
        if os.path.exists(html_path):
            return send_from_directory(TEMPLATES_DIR, filename)
    static_path = os.path.join(STATIC_DIR, filename)
    if os.path.exists(static_path):
        return send_from_directory(STATIC_DIR, filename)
    return jsonify({'error': 'Not found'}), 404

# ── Alumnos ───────────────────────────────────────────────────────────────────

@app.route('/api/alumnos', methods=['GET'])
def listar_alumnos():
    q = request.args.get('q', '').lower()
    anio = request.args.get('anio', '')
    conn = get_db()
    rows = conn.execute("SELECT * FROM alumnos WHERE activo=1 ORDER BY apellido,nombre").fetchall()
    conn.close()
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
            return err('Campo requerido: ' + campo)
    try:
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO alumnos (apellido,nombre,dni,anio,tel_alumno,tel_tutor) VALUES (?,?,?,?,?,?)",
            (d['apellido'], d['nombre'], d['dni'], d['anio'], d.get('tel_alumno',''), d['tel_tutor'])
        )
        alumno_id = cur.lastrowid
        conn.commit(); conn.close()
        return ok({'id': alumno_id}, 201)
    except sqlite3.IntegrityError:
        return err('Ya existe un alumno con ese DNI')

@app.route('/api/alumnos/<int:id>', methods=['PUT'])
def editar_alumno(id):
    d = request.json or {}
    conn = get_db()
    conn.execute(
        "UPDATE alumnos SET apellido=?,nombre=?,dni=?,anio=?,tel_alumno=?,tel_tutor=? WHERE id=?",
        (d.get('apellido'), d.get('nombre'), d.get('dni'), d.get('anio'),
         d.get('tel_alumno',''), d.get('tel_tutor'), id)
    )
    conn.commit(); conn.close()
    return ok({'id': id})

# ── Cuotas ────────────────────────────────────────────────────────────────────

@app.route('/api/cuotas', methods=['GET'])
def listar_cuotas():
    concepto = request.args.get('concepto', 'Cuota mensual')
    mes = request.args.get('mes', '')
    conn = get_db()
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
    conn.close()
    return ok([dict(r) for r in rows])

@app.route('/api/cuotas/historial', methods=['GET'])
def historial_cuotas():
    conn = get_db()
    rows = conn.execute("""
        SELECT c.*, a.apellido, a.nombre, a.tel_tutor
        FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
        WHERE c.estado='Pagado' ORDER BY c.id DESC LIMIT 100
    """).fetchall()
    conn.close()
    return ok([dict(r) for r in rows])

@app.route('/api/cuotas', methods=['POST'])
def registrar_pago():
    d = request.json or {}
    alumno_id = d.get('alumno_id')
    concepto = d.get('concepto', 'Cuota mensual')
    mes = d.get('mes')
    monto = d.get('monto')
    if not alumno_id or not monto:
        return err('alumno_id y monto son requeridos')
    fecha = d.get('fecha_pago', datetime.now().strftime('%d/%m/%Y'))
    conn = get_db()
    if mes:
        existing = conn.execute(
            "SELECT id FROM cuotas WHERE alumno_id=? AND concepto=? AND mes=?",
            (alumno_id, concepto, mes)
        ).fetchone()
    else:
        existing = conn.execute(
            "SELECT id FROM cuotas WHERE alumno_id=? AND concepto=? AND mes IS NULL",
            (alumno_id, concepto)
        ).fetchone()
    if existing:
        conn.execute(
            "UPDATE cuotas SET estado='Pagado',forma_pago=?,fecha_pago=?,monto=?,obs=? WHERE id=?",
            (d.get('forma_pago','Efectivo'), fecha, monto, d.get('obs',''), existing['id'])
        )
        result_id = existing['id']
    else:
        cur = conn.execute(
            "INSERT INTO cuotas (alumno_id,concepto,mes,monto,estado,forma_pago,fecha_pago,obs) VALUES (?,?,?,?,'Pagado',?,?,?)",
            (alumno_id, concepto, mes, monto, d.get('forma_pago','Efectivo'), fecha, d.get('obs',''))
        )
        result_id = cur.lastrowid
    conn.commit(); conn.close()
    return ok({'id': result_id})

# ── Eventos ───────────────────────────────────────────────────────────────────

@app.route('/api/eventos', methods=['GET'])
def listar_eventos():
    conn = get_db()
    eventos = [dict(r) for r in conn.execute("SELECT * FROM eventos ORDER BY id").fetchall()]
    for ev in eventos:
        cobros = conn.execute("""
            SELECT ec.*, a.apellido, a.nombre
            FROM evento_cobros ec LEFT JOIN alumnos a ON ec.alumno_id=a.id
            WHERE ec.evento_id=?
        """, (ev['id'],)).fetchall()
        ev['participantes'] = [dict(c) for c in cobros]
    conn.close()
    return ok(eventos)

@app.route('/api/eventos', methods=['POST'])
def crear_evento():
    d = request.json or {}
    if not d.get('nombre'):
        return err('El nombre es requerido')
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO eventos (nombre,fecha,tipo,descripcion,estado) VALUES (?,?,?,?,?)",
        (d['nombre'], d.get('fecha',''), d.get('tipo','Otro'), d.get('descripcion',''), d.get('estado','Proximo'))
    )
    conn.commit(); conn.close()
    return ok({'id': cur.lastrowid}, 201)

@app.route('/api/eventos/<int:id>/cobros', methods=['POST'])
def registrar_cobro_evento(id):
    d = request.json or {}
    monto = d.get('monto')
    if not monto:
        return err('El monto es requerido')
    conn = get_db()
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
    conn.commit(); conn.close()
    return ok()

# ── Prendas ───────────────────────────────────────────────────────────────────

@app.route('/api/prendas', methods=['GET'])
def listar_prendas():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.*,
            COALESCE((SELECT COUNT(*) FROM reservas r WHERE r.prenda_id=p.id AND r.estado != 'Entregado'),0) AS reservado
        FROM prendas p ORDER BY p.nombre, p.talle
    """).fetchall()
    conn.close()
    return ok([dict(r) for r in rows])

@app.route('/api/prendas', methods=['POST'])
def crear_prenda():
    d = request.json or {}
    if not d.get('nombre') or not d.get('precio'):
        return err('nombre y precio son requeridos')
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO prendas (nombre,talle,color,stock,precio) VALUES (?,?,?,?,?)",
        (d['nombre'], d.get('talle',''), d.get('color',''), int(d.get('stock',0)), float(d['precio']))
    )
    conn.commit(); conn.close()
    return ok({'id': cur.lastrowid}, 201)

@app.route('/api/prendas/<int:id>/stock', methods=['PATCH'])
def ajustar_stock(id):
    d = request.json or {}
    nuevo = d.get('stock')
    if nuevo is None:
        return err('stock requerido')
    conn = get_db()
    conn.execute("UPDATE prendas SET stock=? WHERE id=?", (int(nuevo), id))
    conn.commit(); conn.close()
    return ok()

# ── Reservas ──────────────────────────────────────────────────────────────────

@app.route('/api/reservas', methods=['GET'])
def listar_reservas():
    estado = request.args.get('estado', '')
    q = request.args.get('q', '').lower()
    conn = get_db()
    rows = conn.execute("SELECT * FROM reservas ORDER BY id DESC").fetchall()
    conn.close()
    reservas = [dict(r) for r in rows]
    if estado:
        reservas = [r for r in reservas if r['estado'] == estado]
    if q:
        reservas = [r for r in reservas if q in ((r.get('alumno_txt') or '') + ' ' + (r.get('prenda_txt') or '')).lower()]
    return ok(reservas)

@app.route('/api/reservas', methods=['POST'])
def crear_reserva():
    d = request.json or {}
    precio = float(d.get('precio', 0))
    sena = float(d.get('sena', 0))
    saldo = max(0, precio - sena)
    if not precio:
        return err('El precio es requerido')
    estado = 'Pagado' if saldo == 0 else 'Con sena'
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO reservas (alumno_id,prenda_id,alumno_txt,prenda_txt,tel_tutor,precio,sena,saldo,forma_pago,fecha_entrega,estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (d.get('alumno_id'), d.get('prenda_id'), d.get('alumno_txt',''),
         d.get('prenda_txt',''), d.get('tel_tutor',''),
         precio, sena, saldo, d.get('forma_pago','Efectivo'),
         d.get('fecha_entrega',''), estado)
    )
    conn.commit(); conn.close()
    return ok({'id': cur.lastrowid, 'estado': estado, 'saldo': saldo}, 201)

@app.route('/api/reservas/<int:id>/cobrar-saldo', methods=['POST'])
def cobrar_saldo_reserva(id):
    d = request.json or {}
    monto = float(d.get('monto', 0))
    if not monto:
        return err('Monto requerido')
    conn = get_db()
    r = conn.execute("SELECT * FROM reservas WHERE id=?", (id,)).fetchone()
    if not r:
        conn.close(); return err('Reserva no encontrada', 404)
    nuevo_saldo = max(0, r['saldo'] - monto)
    nuevo_estado = 'Pagado' if nuevo_saldo == 0 else r['estado']
    conn.execute(
        "UPDATE reservas SET saldo=?, sena=sena+?, estado=?, forma_pago=? WHERE id=?",
        (nuevo_saldo, monto, nuevo_estado, d.get('forma_pago', r['forma_pago']), id)
    )
    conn.commit(); conn.close()
    return ok({'saldo': nuevo_saldo, 'estado': nuevo_estado})

@app.route('/api/reservas/<int:id>/entregar', methods=['POST'])
def entregar_reserva(id):
    conn = get_db()
    r = conn.execute("SELECT * FROM reservas WHERE id=?", (id,)).fetchone()
    if not r:
        conn.close(); return err('Reserva no encontrada', 404)
    if r['saldo'] > 0:
        conn.close(); return err('Hay saldo pendiente de $' + str(r['saldo']))
    conn.execute("UPDATE reservas SET estado='Entregado' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return ok()

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    conn = get_db()
    try:
        alumnos_activos = conn.execute("SELECT COUNT(*) FROM alumnos WHERE activo=1").fetchone()[0]
        cuotas_mes = conn.execute(
            "SELECT COUNT(*) as total, COALESCE(SUM(monto),0) as suma FROM cuotas WHERE concepto='Cuota mensual' AND estado='Pagado'"
        ).fetchone()
        pendientes = conn.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(monto),0) as suma FROM cuotas WHERE estado IN ('Pendiente','Vencido')"
        ).fetchone()
        stock_total = conn.execute("SELECT COALESCE(SUM(stock),0) as total FROM prendas").fetchone()
        reservado = conn.execute("SELECT COUNT(*) as cnt FROM reservas WHERE estado != 'Entregado'").fetchone()
        ultimos_pagos = conn.execute("""
            SELECT c.*, a.apellido, a.nombre, a.tel_tutor
            FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
            WHERE c.estado='Pagado' ORDER BY c.id DESC LIMIT 5
        """).fetchall()
        reservas_pendientes = conn.execute(
            "SELECT * FROM reservas WHERE estado IN ('Con sena','Pagado') ORDER BY id DESC LIMIT 4"
        ).fetchall()
        eventos = conn.execute("SELECT * FROM eventos ORDER BY id LIMIT 4").fetchall()
        return ok({
            'alumnos_activos': alumnos_activos,
            'cuotas_cobradas_mes': {'total': cuotas_mes['suma'], 'cantidad': cuotas_mes['total']},
            'pendientes': {'cantidad': pendientes['cnt'], 'suma': pendientes['suma']},
            'stock': {'total': stock_total['total'], 'reservado': reservado['cnt']},
            'ultimos_pagos': [dict(r) for r in ultimos_pagos],
            'reservas_pendientes': [dict(r) for r in reservas_pendientes],
            'eventos': [dict(r) for r in eventos],
        })
    finally:
        conn.close()

@app.route('/api/health')
def health():
    try:
        conn = get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        return ok({'status': 'ok', 'db': DB_PATH, 'templates': TEMPLATES_DIR, 'static': STATIC_DIR})
    except Exception as e:
        return err(str(e), 500)

# ── Boot ──────────────────────────────────────────────────────────────────────
try:
    init_db()
    print("BD inicializada OK:", DB_PATH)
except Exception as e:
    print("ERROR init_db:", e)
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
