# Cooperadora Escolar – Guía de deploy gratuito en Render.com

## Estructura del proyecto

```
cooperadora_backend/
├── app.py              ← Backend Flask + SQLite (toda la lógica)
├── requirements.txt    ← Dependencias Python
├── Procfile            ← Comando de inicio para Render
├── render.yaml         ← Configuración automática de Render
├── static/
│   ├── css/main.css    ← Estilos del frontend
│   ├── api.js          ← Cliente fetch para la API
│   └── sidebar.js      ← Sidebar compartido
└── templates/
    ├── index.html      ← Panel principal
    ├── alumnos.html    ← Gestión de alumnos
    ├── cuotas.html     ← Cuotas y cobros
    ├── eventos.html    ← Eventos del año
    ├── indumentaria.html ← Inventario de prendas
    └── reservas.html   ← Reservas de indumentaria
```

---

## Paso a paso: subir a Render.com (GRATIS)

### 1. Crear cuenta en GitHub (si no tienen)
- Entrar a https://github.com y crear una cuenta gratuita

### 2. Subir el proyecto a GitHub
1. Entrar a https://github.com/new
2. Crear repositorio llamado `cooperadora-escolar` (privado o público)
3. Subir todos los archivos de esta carpeta

   **Opción fácil (sin línea de comandos):**
   - En la página del repositorio recién creado, hacer clic en "uploading an existing file"
   - Arrastrar todos los archivos y carpetas
   - Hacer clic en "Commit changes"

### 3. Crear cuenta en Render.com
- Entrar a https://render.com
- Registrarse con la cuenta de GitHub (más fácil)

### 4. Crear el servicio web
1. En el Dashboard de Render → "New +" → "Web Service"
2. Conectar el repositorio de GitHub `cooperadora-escolar`
3. Configurar:
   - **Name:** cooperadora-escolar
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1`
   - **Instance Type:** Free ✅
4. En "Advanced" → "Add Disk":
   - **Name:** db-disk
   - **Mount Path:** `/opt/render/project/src`
   - **Size:** 1 GB ✅ (gratis)
5. En "Environment Variables":
   - `DB_PATH` = `/opt/render/project/src/cooperadora.db`
6. Hacer clic en **"Create Web Service"**

### 5. Esperar el deploy (~3-5 minutos)
Render instalará las dependencias y levantará la app.
La URL final será algo como: `https://cooperadora-escolar.onrender.com`

---

## API disponible

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/dashboard` | Resumen del panel principal |
| GET/POST | `/api/alumnos` | Listar / crear alumnos |
| PUT | `/api/alumnos/<id>` | Editar alumno |
| GET/POST | `/api/cuotas` | Listar / registrar pagos |
| GET | `/api/cuotas/historial` | Historial de pagos |
| POST | `/api/cuotas/<id>/pagar` | Marcar cuota como pagada |
| GET/POST | `/api/eventos` | Listar / crear eventos |
| POST | `/api/eventos/<id>/cobros` | Registrar cobro de evento |
| GET/POST | `/api/prendas` | Listar / crear prendas |
| PATCH | `/api/prendas/<id>/stock` | Ajustar stock |
| GET/POST | `/api/reservas` | Listar / crear reservas |
| POST | `/api/reservas/<id>/cobrar-saldo` | Cobrar saldo de reserva |
| POST | `/api/reservas/<id>/entregar` | Marcar prenda como entregada |

---

## Importante sobre el plan gratuito de Render

- ✅ La app es gratuita
- ✅ La base de datos SQLite persiste en el disco
- ⚠️ El servidor se "duerme" tras 15 minutos de inactividad
- ⚠️ El primer acceso tras inactividad tarda ~30 segundos en despertar
- ✅ Esto es normal y no afecta el funcionamiento

---

## Desarrollo local (opcional)

```bash
# Instalar dependencias
pip install flask flask-cors gunicorn

# Ejecutar en modo desarrollo
python app.py

# Abrir en el navegador
# http://localhost:5000
```
