from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')

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
        dni TEXT DEFAULT '', anio TEXT NOT NULL,
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
        precio_tarjeta REAL DEFAULT 0,
        ganancia_tarjeta REAL DEFAULT 0,
        creado_en TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS evento_entregas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evento_id INTEGER NOT NULL REFERENCES eventos(id),
        alumno_id INTEGER NOT NULL REFERENCES alumnos(id),
        alumno_txt TEXT DEFAULT '',
        tel_tutor TEXT DEFAULT '',
        tarjeta_desde INTEGER NOT NULL,
        tarjeta_hasta INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        creado_en TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS evento_tarjetas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evento_id INTEGER NOT NULL REFERENCES eventos(id),
        entrega_id INTEGER NOT NULL REFERENCES evento_entregas(id),
        alumno_id INTEGER NOT NULL REFERENCES alumnos(id),
        alumno_txt TEXT DEFAULT '',
        numero INTEGER NOT NULL,
        tipo_rendicion TEXT DEFAULT NULL,
        monto_rendido REAL DEFAULT 0,
        forma_pago TEXT DEFAULT 'Efectivo',
        fecha_rendicion TEXT DEFAULT NULL,
        rendida INTEGER DEFAULT 0,
        UNIQUE(evento_id, numero)
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

    # Migraciones para bases existentes
    migraciones = [
        "ALTER TABLE alumnos ADD COLUMN dni TEXT DEFAULT ''",
        "ALTER TABLE eventos ADD COLUMN precio_tarjeta REAL DEFAULT 0",
        "ALTER TABLE eventos ADD COLUMN ganancia_tarjeta REAL DEFAULT 0",
    ]
    for m in migraciones:
        try: conn.execute(m)
        except: pass

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
    for c in [
        (1,'Cuota mensual','Marzo 2026',3500,'Pagado','Debito','05/03/2026'),
        (2,'Cuota mensual','Marzo 2026',3500,'Pagado','Efectivo','03/03/2026'),
        (3,'Cuota mensual','Marzo 2026',3500,'Pendiente','',''),
        (4,'Cuota mensual','Marzo 2026',3500,'Vencido','',''),
        (5,'Cuota mensual','Marzo 2026',3500,'Pagado','Efectivo','07/03/2026'),
        (1,'Matricula',None,5000,'Pagado','Debito','10/02/2026'),
        (2,'Matricula',None,5000,'Pagado','Efectivo','08/02/2026'),
    ]:
        conn.execute("INSERT INTO cuotas (alumno_id,concepto,mes,monto,estado,forma_pago,fecha_pago) VALUES (?,?,?,?,?,?,?)", c)
    # Evento demo con tarjetas
    conn.execute("INSERT INTO eventos (nombre,fecha,tipo,descripcion,estado,precio_tarjeta,ganancia_tarjeta) VALUES (?,?,?,?,?,?,?)",
        ('Rifa anual','Agosto 2026','Rifas','Rifa con premios donados','Activo',5000,2000))
    conn.execute("INSERT INTO eventos (nombre,fecha,tipo,descripcion,estado,precio_tarjeta,ganancia_tarjeta) VALUES (?,?,?,?,?,?,?)",
        ('Locro patriotico','25/05/2026','Venta de comida','Venta de porciones de locro','Proximo',1500,500))
    # Entrega demo
    conn.execute("INSERT INTO evento_entregas (evento_id,alumno_id,alumno_txt,tel_tutor,tarjeta_desde,tarjeta_hasta,cantidad) VALUES (?,?,?,?,?,?,?)",
        (1,1,'Garcia, Lucia','11 8765-4321',1,5,5))
    conn.execute("INSERT INTO evento_entregas (evento_id,alumno_id,alumno_txt,tel_tutor,tarjeta_desde,tarjeta_hasta,cantidad) VALUES (?,?,?,?,?,?,?)",
        (1,2,'Perez, Tomas','11 7654-3210',6,10,5))
    # Tarjetas demo
    for n in range(1, 6):
        conn.execute("INSERT INTO evento_tarjetas (evento_id,entrega_id,alumno_id,alumno_txt,numero) VALUES (?,?,?,?,?)",
            (1,1,1,'Garcia, Lucia',n))
    for n in range(6, 11):
        conn.execute("INSERT INTO evento_tarjetas (evento_id,entrega_id,alumno_id,alumno_txt,numero) VALUES (?,?,?,?,?)",
            (1,2,2,'Perez, Tomas',n))
    # Rendicion demo
    conn.execute("UPDATE evento_tarjetas SET rendida=1, tipo_rendicion='venta', monto_rendido=5000, forma_pago='Efectivo', fecha_rendicion=? WHERE evento_id=1 AND numero=1",
        (datetime.now().strftime('%d/%m/%Y'),))
    conn.execute("UPDATE evento_tarjetas SET rendida=1, tipo_rendicion='ganancia', monto_rendido=2000, forma_pago='Efectivo', fecha_rendicion=? WHERE evento_id=1 AND numero=2",
        (datetime.now().strftime('%d/%m/%Y'),))
    for r in [
        (6,1,'Ruiz, Martina','Campera Azul T12','11 3210-9876',8500,6500,2000,'Efectivo','15/03/2026','Con sena'),
        (7,5,'Sosa, Diego','Buzo Gris T14','11 2109-8765',6500,5000,1500,'Debito','20/03/2026','Con sena'),
    ]:
        conn.execute("INSERT INTO reservas (alumno_id,prenda_id,alumno_txt,prenda_txt,tel_tutor,precio,sena,saldo,forma_pago,fecha_entrega,estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)", r)

# ── Servir frontend ─────────────────────────────────────────────────────────────

@app.route('/')
def index(): return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith('.html'):
        p = os.path.join(TEMPLATES_DIR, filename)
        if os.path.exists(p): return send_from_directory(TEMPLATES_DIR, filename)
    p = os.path.join(STATIC_DIR, filename)
    if os.path.exists(p): return send_from_directory(STATIC_DIR, filename)
    return jsonify({'error': 'Not found'}), 404

# ── Alumnos ──────────────────────────────────────────────────────────────────

@app.route('/api/alumnos', methods=['GET'])
def listar_alumnos():
    q = request.args.get('q', '').lower()
    anio = request.args.get('anio', '')
    conn = get_db()
    rows = conn.execute("SELECT * FROM alumnos WHERE activo=1 ORDER BY apellido,nombre").fetchall()
    conn.close()
    alumnos = [dict(r) for r in rows]
    if q: alumnos = [a for a in alumnos if q in (a['apellido']+' '+a['nombre']+' '+(a.get('dni') or '')).lower()]
    if anio: alumnos = [a for a in alumnos if a['anio'] == anio]
    return ok(alumnos)

@app.route('/api/alumnos', methods=['POST'])
def crear_alumno():
    d = request.json or {}
    for campo in ['apellido', 'nombre', 'anio', 'tel_tutor']:
        if not d.get(campo): return err('Campo requerido: ' + campo)
    conn = get_db()
    cur = conn.execute("INSERT INTO alumnos (apellido,nombre,dni,anio,tel_alumno,tel_tutor) VALUES (?,?,?,?,?,?)",
        (d['apellido'], d['nombre'], d.get('dni',''), d['anio'], d.get('tel_alumno',''), d['tel_tutor']))
    aid = cur.lastrowid; conn.commit(); conn.close()
    return ok({'id': aid}, 201)

@app.route('/api/alumnos/<int:id>', methods=['PUT'])
def editar_alumno(id):
    d = request.json or {}
    conn = get_db()
    conn.execute("UPDATE alumnos SET apellido=?,nombre=?,dni=?,anio=?,tel_alumno=?,tel_tutor=? WHERE id=?",
        (d.get('apellido'), d.get('nombre'), d.get('dni',''), d.get('anio'), d.get('tel_alumno',''), d.get('tel_tutor'), id))
    conn.commit(); conn.close()
    return ok({'id': id})

@app.route('/api/alumnos/importar', methods=['POST'])
def importar_alumnos():
    data = request.json or {}
    alumnos = data.get('alumnos', [])
    if not alumnos: return err('No se recibieron alumnos')
    insertados = 0; errores = []
    conn = get_db()
    for i, a in enumerate(alumnos):
        fila = i + 2
        apellido = str(a.get('apellido', '')).strip()
        nombre = str(a.get('nombre', '')).strip()
        anio = str(a.get('anio', '')).strip()
        tel_tutor = str(a.get('tel_tutor', '')).strip()
        if not apellido or not nombre or not anio or not tel_tutor:
            errores.append(f'Fila {fila}: faltan campos obligatorios'); continue
        try:
            conn.execute("INSERT INTO alumnos (apellido,nombre,dni,anio,tel_alumno,tel_tutor) VALUES (?,?,?,?,?,?)",
                (apellido, nombre, str(a.get('dni','')).strip(), anio, str(a.get('tel_alumno','')).strip(), tel_tutor))
            insertados += 1
        except Exception as e:
            errores.append(f'Fila {fila}: {str(e)}')
    conn.commit(); conn.close()
    return ok({'insertados': insertados, 'errores': errores})

# ── Cuotas ───────────────────────────────────────────────────────────────────

@app.route('/api/cuotas', methods=['GET'])
def listar_cuotas():
    concepto = request.args.get('concepto', 'Cuota mensual')
    mes = request.args.get('mes', '')
    conn = get_db()
    if mes:
        rows = conn.execute("""SELECT c.*, a.apellido, a.nombre, a.anio, a.tel_tutor
            FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
            WHERE c.concepto=? AND c.mes=? ORDER BY a.apellido,a.nombre""", (concepto, mes)).fetchall()
    else:
        rows = conn.execute("""SELECT c.*, a.apellido, a.nombre, a.anio, a.tel_tutor
            FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
            WHERE c.concepto=? ORDER BY a.apellido,a.nombre""", (concepto,)).fetchall()
    conn.close()
    return ok([dict(r) for r in rows])

@app.route('/api/cuotas/conceptos', methods=['GET'])
def listar_conceptos():
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT concepto FROM cuotas ORDER BY concepto").fetchall()
    conn.close()
    base = ['Cuota mensual', 'Matricula', 'Evento', 'Otro']
    existentes = [r['concepto'] for r in rows]
    return ok(list(dict.fromkeys(base + existentes)))

@app.route('/api/cuotas/historial', methods=['GET'])
def historial_cuotas():
    conn = get_db()
    rows = conn.execute("""SELECT c.*, a.apellido, a.nombre, a.tel_tutor
        FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
        WHERE c.estado='Pagado' ORDER BY c.id DESC LIMIT 100""").fetchall()
    conn.close()
    return ok([dict(r) for r in rows])

@app.route('/api/cuotas', methods=['POST'])
def registrar_pago():
    d = request.json or {}
    alumno_id = d.get('alumno_id'); concepto = d.get('concepto', 'Cuota mensual')
    mes = d.get('mes'); monto = d.get('monto')
    if not alumno_id or not monto: return err('alumno_id y monto son requeridos')
    fecha = d.get('fecha_pago', datetime.now().strftime('%d/%m/%Y'))
    conn = get_db()
    if mes:
        existing = conn.execute("SELECT id FROM cuotas WHERE alumno_id=? AND concepto=? AND mes=?", (alumno_id, concepto, mes)).fetchone()
    else:
        existing = conn.execute("SELECT id FROM cuotas WHERE alumno_id=? AND concepto=? AND mes IS NULL", (alumno_id, concepto)).fetchone()
    if existing:
        conn.execute("UPDATE cuotas SET estado='Pagado',forma_pago=?,fecha_pago=?,monto=?,obs=? WHERE id=?",
            (d.get('forma_pago','Efectivo'), fecha, monto, d.get('obs',''), existing['id']))
        result_id = existing['id']
    else:
        cur = conn.execute("INSERT INTO cuotas (alumno_id,concepto,mes,monto,estado,forma_pago,fecha_pago,obs) VALUES (?,?,?,?,'Pagado',?,?,?)",
            (alumno_id, concepto, mes, monto, d.get('forma_pago','Efectivo'), fecha, d.get('obs','')))
        result_id = cur.lastrowid
    conn.commit(); conn.close()
    return ok({'id': result_id})

# ── Eventos ──────────────────────────────────────────────────────────────────

@app.route('/api/eventos', methods=['GET'])
def listar_eventos():
    conn = get_db()
    eventos = [dict(r) for r in conn.execute("SELECT * FROM eventos ORDER BY id DESC").fetchall()]
    for ev in eventos:
        entregas = conn.execute("""
            SELECT ee.*, a.apellido, a.nombre,
                COUNT(et.id) as tarjetas_total,
                SUM(CASE WHEN et.rendida=1 THEN 1 ELSE 0 END) as tarjetas_rendidas
            FROM evento_entregas ee
            JOIN alumnos a ON ee.alumno_id=a.id
            LEFT JOIN evento_tarjetas et ON et.entrega_id=ee.id
            WHERE ee.evento_id=?
            GROUP BY ee.id
        """, (ev['id'],)).fetchall()
        ev['entregas'] = [dict(e) for e in entregas]
        stats = conn.execute("""
            SELECT COUNT(*) as total,
                SUM(CASE WHEN rendida=1 THEN 1 ELSE 0 END) as rendidas,
                SUM(CASE WHEN rendida=1 AND tipo_rendicion='venta' THEN 1 ELSE 0 END) as por_venta,
                SUM(CASE WHEN rendida=1 AND tipo_rendicion='ganancia' THEN 1 ELSE 0 END) as por_ganancia,
                SUM(CASE WHEN rendida=1 THEN monto_rendido ELSE 0 END) as monto_rendido
            FROM evento_tarjetas WHERE evento_id=?
        """, (ev['id'],)).fetchone()
        ev['stats'] = dict(stats)
    conn.close()
    return ok(eventos)

@app.route('/api/eventos', methods=['POST'])
def crear_evento():
    d = request.json or {}
    if not d.get('nombre'): return err('El nombre es requerido')
    conn = get_db()
    cur = conn.execute("INSERT INTO eventos (nombre,fecha,tipo,descripcion,estado,precio_tarjeta,ganancia_tarjeta) VALUES (?,?,?,?,?,?,?)",
        (d['nombre'], d.get('fecha',''), d.get('tipo','Otro'), d.get('descripcion',''),
         d.get('estado','Proximo'), float(d.get('precio_tarjeta',0)), float(d.get('ganancia_tarjeta',0))))
    conn.commit(); conn.close()
    return ok({'id': cur.lastrowid}, 201)

@app.route('/api/eventos/<int:id>', methods=['PUT'])
def editar_evento(id):
    d = request.json or {}
    conn = get_db()
    conn.execute("UPDATE eventos SET nombre=?,fecha=?,tipo=?,descripcion=?,estado=?,precio_tarjeta=?,ganancia_tarjeta=? WHERE id=?",
        (d.get('nombre'), d.get('fecha',''), d.get('tipo','Otro'), d.get('descripcion',''),
         d.get('estado','Proximo'), float(d.get('precio_tarjeta',0)), float(d.get('ganancia_tarjeta',0)), id))
    conn.commit(); conn.close()
    return ok({'id': id})

# ── Entregas de tarjetas ──────────────────────────────────────────────────────

@app.route('/api/eventos/<int:ev_id>/entregas', methods=['POST'])
def crear_entrega(ev_id):
    d = request.json or {}
    alumno_id = d.get('alumno_id')
    desde = d.get('tarjeta_desde')
    hasta = d.get('tarjeta_hasta')
    if not alumno_id or not desde or not hasta:
        return err('alumno_id, tarjeta_desde y tarjeta_hasta son requeridos')
    desde = int(desde); hasta = int(hasta)
    if desde > hasta:
        return err('El número inicial debe ser menor o igual al final')
    conn = get_db()
    # Verificar que no haya superposición de números en el evento
    overlap = conn.execute("""
        SELECT et.numero FROM evento_tarjetas et
        WHERE et.evento_id=? AND et.numero BETWEEN ? AND ?
    """, (ev_id, desde, hasta)).fetchone()
    if overlap:
        conn.close()
        return err(f'El número de tarjeta {overlap["numero"]} ya está asignado en este evento')
    alumno = conn.execute("SELECT apellido, nombre, tel_tutor FROM alumnos WHERE id=?", (alumno_id,)).fetchone()
    if not alumno:
        conn.close(); return err('Alumno no encontrado')
    alumno_txt = f"{alumno['apellido']}, {alumno['nombre']}"
    cantidad = hasta - desde + 1
    cur = conn.execute("INSERT INTO evento_entregas (evento_id,alumno_id,alumno_txt,tel_tutor,tarjeta_desde,tarjeta_hasta,cantidad) VALUES (?,?,?,?,?,?,?)",
        (ev_id, alumno_id, alumno_txt, alumno['tel_tutor'], desde, hasta, cantidad))
    entrega_id = cur.lastrowid
    # Crear una fila por cada tarjeta
    for n in range(desde, hasta + 1):
        conn.execute("INSERT INTO evento_tarjetas (evento_id,entrega_id,alumno_id,alumno_txt,numero) VALUES (?,?,?,?,?)",
            (ev_id, entrega_id, alumno_id, alumno_txt, n))
    conn.commit(); conn.close()
    return ok({'id': entrega_id, 'cantidad': cantidad}, 201)

@app.route('/api/eventos/<int:ev_id>/entregas/<int:entrega_id>', methods=['DELETE'])
def eliminar_entrega(ev_id, entrega_id):
    conn = get_db()
    # Solo se puede eliminar si no hay tarjetas rendidas
    rendidas = conn.execute("SELECT COUNT(*) FROM evento_tarjetas WHERE entrega_id=? AND rendida=1", (entrega_id,)).fetchone()[0]
    if rendidas > 0:
        conn.close(); return err('No se puede eliminar: hay tarjetas ya rendidas en esta entrega')
    conn.execute("DELETE FROM evento_tarjetas WHERE entrega_id=?", (entrega_id,))
    conn.execute("DELETE FROM evento_entregas WHERE id=? AND evento_id=?", (entrega_id, ev_id))
    conn.commit(); conn.close()
    return ok()

# ── Tarjetas (rendición) ──────────────────────────────────────────────────────

@app.route('/api/eventos/<int:ev_id>/tarjetas', methods=['GET'])
def listar_tarjetas_evento(ev_id):
    alumno_id = request.args.get('alumno_id')
    conn = get_db()
    if alumno_id:
        rows = conn.execute("""SELECT * FROM evento_tarjetas WHERE evento_id=? AND alumno_id=? ORDER BY numero""",
            (ev_id, alumno_id)).fetchall()
    else:
        rows = conn.execute("""SELECT * FROM evento_tarjetas WHERE evento_id=? ORDER BY numero""", (ev_id,)).fetchall()
    conn.close()
    return ok([dict(r) for r in rows])

@app.route('/api/eventos/<int:ev_id>/tarjetas/<int:tarjeta_id>/rendir', methods=['PATCH'])
def rendir_tarjeta(ev_id, tarjeta_id):
    """Marcar una tarjeta como rendida (venta o ganancia) o desmarcarla"""
    d = request.json or {}
    rendida = 1 if d.get('rendida') else 0
    conn = get_db()
    if rendida:
        tipo = d.get('tipo_rendicion')  # 'venta' o 'ganancia'
        if tipo not in ('venta', 'ganancia'):
            conn.close(); return err("tipo_rendicion debe ser 'venta' o 'ganancia'")
        # Calcular monto según tipo
        ev = conn.execute("SELECT precio_tarjeta, ganancia_tarjeta FROM eventos WHERE id=?", (ev_id,)).fetchone()
        if not ev: conn.close(); return err('Evento no encontrado', 404)
        monto = ev['precio_tarjeta'] if tipo == 'venta' else ev['ganancia_tarjeta']
        # Permitir override de monto
        if d.get('monto_rendido') is not None:
            monto = float(d['monto_rendido'])
        conn.execute("""UPDATE evento_tarjetas
            SET rendida=1, tipo_rendicion=?, monto_rendido=?, forma_pago=?, fecha_rendicion=?
            WHERE id=? AND evento_id=?""",
            (tipo, monto, d.get('forma_pago','Efectivo'), datetime.now().strftime('%d/%m/%Y'), tarjeta_id, ev_id))
    else:
        conn.execute("""UPDATE evento_tarjetas
            SET rendida=0, tipo_rendicion=NULL, monto_rendido=0, forma_pago='Efectivo', fecha_rendicion=NULL
            WHERE id=? AND evento_id=?""", (tarjeta_id, ev_id))
    conn.commit(); conn.close()
    return ok()

@app.route('/api/eventos/<int:ev_id>/tarjetas/rendir-lote', methods=['POST'])
def rendir_tarjetas_lote(ev_id):
    """Rendir múltiples tarjetas de un alumno en un solo paso"""
    d = request.json or {}
    ids = d.get('ids', [])          # lista de tarjeta_id
    tipo = d.get('tipo_rendicion')  # 'venta' o 'ganancia'
    forma_pago = d.get('forma_pago', 'Efectivo')
    if not ids or tipo not in ('venta', 'ganancia'):
        return err("ids y tipo_rendicion ('venta' o 'ganancia') son requeridos")
    conn = get_db()
    ev = conn.execute("SELECT precio_tarjeta, ganancia_tarjeta FROM eventos WHERE id=?", (ev_id,)).fetchone()
    if not ev: conn.close(); return err('Evento no encontrado', 404)
    monto = ev['precio_tarjeta'] if tipo == 'venta' else ev['ganancia_tarjeta']
    fecha = datetime.now().strftime('%d/%m/%Y')
    for tid in ids:
        conn.execute("""UPDATE evento_tarjetas
            SET rendida=1, tipo_rendicion=?, monto_rendido=?, forma_pago=?, fecha_rendicion=?
            WHERE id=? AND evento_id=?""",
            (tipo, monto, forma_pago, fecha, tid, ev_id))
    conn.commit(); conn.close()
    return ok({'actualizadas': len(ids)})

# ── Reporte de evento ─────────────────────────────────────────────────────────

@app.route('/api/eventos/<int:id>/reporte', methods=['GET'])
def reporte_evento(id):
    conn = get_db()
    ev = conn.execute("SELECT * FROM eventos WHERE id=?", (id,)).fetchone()
    if not ev: conn.close(); return err('Evento no encontrado', 404)
    ev = dict(ev)

    entregas = conn.execute("""
        SELECT ee.*, a.apellido, a.nombre
        FROM evento_entregas ee JOIN alumnos a ON ee.alumno_id=a.id
        WHERE ee.evento_id=? ORDER BY ee.tarjeta_desde
    """, (id,)).fetchall()

    tarjetas = conn.execute("""
        SELECT et.*, a.apellido, a.nombre
        FROM evento_tarjetas et JOIN alumnos a ON et.alumno_id=a.id
        WHERE et.evento_id=? ORDER BY et.numero
    """, (id,)).fetchall()
    conn.close()

    tarjetas_list = [dict(t) for t in tarjetas]
    entregas_list = [dict(e) for e in entregas]

    total = len(tarjetas_list)
    rendidas = [t for t in tarjetas_list if t['rendida']]
    pendientes = [t for t in tarjetas_list if not t['rendida']]
    por_venta = [t for t in rendidas if t['tipo_rendicion'] == 'venta']
    por_ganancia = [t for t in rendidas if t['tipo_rendicion'] == 'ganancia']
    monto_venta = sum(t['monto_rendido'] for t in por_venta)
    monto_ganancia = sum(t['monto_rendido'] for t in por_ganancia)
    monto_total = monto_venta + monto_ganancia

    # Agrupar pendientes por alumno
    pendientes_por_alumno = {}
    for t in pendientes:
        aid = t['alumno_id']
        if aid not in pendientes_por_alumno:
            pendientes_por_alumno[aid] = {'alumno_txt': t['alumno_txt'], 'numeros': []}
        pendientes_por_alumno[aid]['numeros'].append(t['numero'])

    return ok({
        'evento': ev,
        'total_tarjetas_entregadas': total,
        'total_entregas': len(entregas_list),
        'rendidas': {
            'cantidad': len(rendidas),
            'por_venta': {'cantidad': len(por_venta), 'monto': monto_venta, 'numeros': [t['numero'] for t in por_venta]},
            'por_ganancia': {'cantidad': len(por_ganancia), 'monto': monto_ganancia, 'numeros': [t['numero'] for t in por_ganancia]},
            'monto_total': monto_total,
        },
        'pendientes': {
            'cantidad': len(pendientes),
            'monto_estimado_venta': len(pendientes) * ev['precio_tarjeta'],
            'monto_estimado_ganancia': len(pendientes) * ev['ganancia_tarjeta'],
            'numeros': [t['numero'] for t in pendientes],
            'por_alumno': list(pendientes_por_alumno.values()),
        },
        'entregas': entregas_list,
    })

# ── Prendas ───────────────────────────────────────────────────────────────────

@app.route('/api/prendas', methods=['GET'])
def listar_prendas():
    conn = get_db()
    rows = conn.execute("""SELECT p.*,
        COALESCE((SELECT COUNT(*) FROM reservas r WHERE r.prenda_id=p.id AND r.estado != 'Entregado'),0) AS reservado
        FROM prendas p ORDER BY p.nombre, p.talle""").fetchall()
    conn.close()
    return ok([dict(r) for r in rows])

@app.route('/api/prendas', methods=['POST'])
def crear_prenda():
    d = request.json or {}
    if not d.get('nombre') or not d.get('precio'): return err('nombre y precio son requeridos')
    conn = get_db()
    cur = conn.execute("INSERT INTO prendas (nombre,talle,color,stock,precio) VALUES (?,?,?,?,?)",
        (d['nombre'], d.get('talle',''), d.get('color',''), int(d.get('stock',0)), float(d['precio'])))
    conn.commit(); conn.close()
    return ok({'id': cur.lastrowid}, 201)

@app.route('/api/prendas/<int:id>/stock', methods=['PATCH'])
def ajustar_stock(id):
    d = request.json or {}
    nuevo = d.get('stock')
    if nuevo is None: return err('stock requerido')
    conn = get_db()
    conn.execute("UPDATE prendas SET stock=? WHERE id=?", (int(nuevo), id))
    conn.commit(); conn.close()
    return ok()

# ── Reservas ──────────────────────────────────────────────────────────────────

@app.route('/api/reservas', methods=['GET'])
def listar_reservas():
    estado = request.args.get('estado', ''); q = request.args.get('q', '').lower()
    conn = get_db()
    rows = conn.execute("SELECT * FROM reservas ORDER BY id DESC").fetchall()
    conn.close()
    reservas = [dict(r) for r in rows]
    if estado: reservas = [r for r in reservas if r['estado'] == estado]
    if q: reservas = [r for r in reservas if q in ((r.get('alumno_txt') or '') + ' ' + (r.get('prenda_txt') or '')).lower()]
    return ok(reservas)

@app.route('/api/reservas', methods=['POST'])
def crear_reserva():
    d = request.json or {}
    precio = float(d.get('precio', 0)); sena = float(d.get('sena', 0))
    saldo = max(0, precio - sena)
    if not precio: return err('El precio es requerido')
    estado = 'Pagado' if saldo == 0 else 'Con sena'
    conn = get_db()
    cur = conn.execute("INSERT INTO reservas (alumno_id,prenda_id,alumno_txt,prenda_txt,tel_tutor,precio,sena,saldo,forma_pago,fecha_entrega,estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (d.get('alumno_id'), d.get('prenda_id'), d.get('alumno_txt',''), d.get('prenda_txt',''),
         d.get('tel_tutor',''), precio, sena, saldo, d.get('forma_pago','Efectivo'), d.get('fecha_entrega',''), estado))
    conn.commit(); conn.close()
    return ok({'id': cur.lastrowid, 'estado': estado, 'saldo': saldo}, 201)

@app.route('/api/reservas/<int:id>/cobrar-saldo', methods=['POST'])
def cobrar_saldo_reserva(id):
    d = request.json or {}
    monto = float(d.get('monto', 0))
    if not monto: return err('Monto requerido')
    conn = get_db()
    r = conn.execute("SELECT * FROM reservas WHERE id=?", (id,)).fetchone()
    if not r: conn.close(); return err('Reserva no encontrada', 404)
    nuevo_saldo = max(0, r['saldo'] - monto)
    nuevo_estado = 'Pagado' if nuevo_saldo == 0 else r['estado']
    conn.execute("UPDATE reservas SET saldo=?, sena=sena+?, estado=?, forma_pago=? WHERE id=?",
        (nuevo_saldo, monto, nuevo_estado, d.get('forma_pago', r['forma_pago']), id))
    conn.commit(); conn.close()
    return ok({'saldo': nuevo_saldo, 'estado': nuevo_estado})

@app.route('/api/reservas/<int:id>/entregar', methods=['POST'])
def entregar_reserva(id):
    conn = get_db()
    r = conn.execute("SELECT * FROM reservas WHERE id=?", (id,)).fetchone()
    if not r: conn.close(); return err('Reserva no encontrada', 404)
    if r['saldo'] > 0: conn.close(); return err('Hay saldo pendiente de $' + str(r['saldo']))
    conn.execute("UPDATE reservas SET estado='Entregado' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return ok()

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    conn = get_db()
    try:
        alumnos_activos = conn.execute("SELECT COUNT(*) FROM alumnos WHERE activo=1").fetchone()[0]
        cuotas_mes = conn.execute("SELECT COUNT(*) as total, COALESCE(SUM(monto),0) as suma FROM cuotas WHERE concepto='Cuota mensual' AND estado='Pagado'").fetchone()
        pendientes = conn.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(monto),0) as suma FROM cuotas WHERE estado IN ('Pendiente','Vencido')").fetchone()
        stock_total = conn.execute("SELECT COALESCE(SUM(stock),0) as total FROM prendas").fetchone()
        reservado = conn.execute("SELECT COUNT(*) as cnt FROM reservas WHERE estado != 'Entregado'").fetchone()
        eventos_stats = conn.execute("""
            SELECT COUNT(DISTINCT e.id) as total_eventos,
                COALESCE(SUM(et.monto_rendido),0) as total_rendido,
                SUM(CASE WHEN et.rendida=0 THEN 1 ELSE 0 END) as tarjetas_pendientes
            FROM eventos e LEFT JOIN evento_tarjetas et ON et.evento_id=e.id
        """).fetchone()
        total_cuotas = conn.execute("SELECT COALESCE(SUM(monto),0) as suma FROM cuotas WHERE estado='Pagado'").fetchone()
        total_ev = conn.execute("SELECT COALESCE(SUM(monto_rendido),0) as suma FROM evento_tarjetas WHERE rendida=1").fetchone()
        total_res = conn.execute("SELECT COALESCE(SUM(sena),0) as suma FROM reservas").fetchone()
        ultimos_pagos = conn.execute("""SELECT c.*, a.apellido, a.nombre, a.tel_tutor
            FROM cuotas c JOIN alumnos a ON c.alumno_id=a.id
            WHERE c.estado='Pagado' ORDER BY c.id DESC LIMIT 5""").fetchall()
        reservas_pendientes = conn.execute("SELECT * FROM reservas WHERE estado IN ('Con sena','Pagado') ORDER BY id DESC LIMIT 4").fetchall()
        eventos = conn.execute("SELECT * FROM eventos ORDER BY id DESC LIMIT 4").fetchall()
        return ok({
            'alumnos_activos': alumnos_activos,
            'cuotas_cobradas_mes': {'total': cuotas_mes['suma'], 'cantidad': cuotas_mes['total']},
            'pendientes': {'cantidad': pendientes['cnt'], 'suma': pendientes['suma']},
            'stock': {'total': stock_total['total'], 'reservado': reservado['cnt']},
            'eventos_stats': {
                'total_eventos': eventos_stats['total_eventos'],
                'total_rendido': eventos_stats['total_rendido'],
                'tarjetas_pendientes': eventos_stats['tarjetas_pendientes'] or 0,
            },
            'recaudacion_total': total_cuotas['suma'] + total_ev['suma'] + total_res['suma'],
            'ultimos_pagos': [dict(r) for r in ultimos_pagos],
            'reservas_pendientes': [dict(r) for r in reservas_pendientes],
            'eventos': [dict(r) for r in eventos],
        })
    finally:
        conn.close()

@app.route('/api/health')
def health():
    try:
        conn = get_db(); conn.execute("SELECT 1").fetchone(); conn.close()
        return ok({'status': 'ok', 'db': DB_PATH})
    except Exception as e:
        return err(str(e), 500)

try:
    init_db()
    print("BD inicializada OK:", DB_PATH)
except Exception as e:
    print("ERROR init_db:", e)
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
