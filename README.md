# 🐾 buscame.colombia

Aplicación web para **conectar de manera rápida y directa a las mascotas perdidas con sus dueños**, creada en el marco de la emergencia registrada en Colombia.

Sin registro, sin fricción: entras, tocas un botón, y en menos de un minuto tu reporte está publicado en el mapa con foto, descripción, teléfono y ubicación GPS.

## ¿Cómo funciona?

La vista inicial tiene solo **2 botones**:

| Botón | ¿Para quién? |
|---|---|
| 🔍 **Busco a mi mascota** | Tu mascota se perdió y necesitas ayuda para encontrarla |
| 📍 **Esta mascota puede estar perdida** | Viste una mascota que parece extraviada y quieres reportarla |

Cada reporte captura:

- 📡 **Ubicación GPS** del navegador (automática)
- 📝 **Breve descripción** de la mascota
- 📞 **Teléfono de contacto** (con enlaces directos para llamar o escribir por WhatsApp)
- 📷 **Foto** (opcional, máx. 5 MB)

La página principal muestra además:

- **Contadores en tiempo real** de mascotas buscadas y posibles encontradas
- **Mapa de Colombia** (Leaflet + OpenStreetMap) con todos los reportes, diferenciados por color

## Stack

Pensado para ser **rápido de desplegar y fácil de mantener**:

- **Backend**: Python · [Flask](https://flask.palletsprojects.com/) + Flask-SQLAlchemy
- **Base de datos**: PostgreSQL (Railway) — SQLite automático en desarrollo local
- **Frontend**: HTML + CSS + JavaScript vanilla, mobile-first
- **Mapa**: [Leaflet](https://leafletjs.com/) con tiles de OpenStreetMap (gratis, sin API key)
- **Fotos**: volumen persistente de Railway (sin servicios externos)
- **Servidor**: Gunicorn

## Estructura del proyecto

```
buscame.colombia/
├── app.py              # App Flask: modelos, rutas y API
├── requirements.txt    # Dependencias
├── Procfile            # Comando de arranque para Railway
├── .env.example        # Variables de entorno de ejemplo
├── templates/
│   ├── base.html       # Layout común
│   ├── index.html      # Home: botones, contadores y mapa
│   └── reportar.html   # Formulario de reporte (ambos tipos)
└── static/
    ├── css/style.css
    └── js/
        ├── index.js    # Mapa + contadores (polling)
        └── reportar.js # GPS, preview de foto y envío
```

## API

| Ruta | Método | Descripción |
|---|---|---|
| `/` | GET | Vista inicial |
| `/reportar/<tipo>` | GET | Formulario (`busco` o `avistada`) |
| `/api/reportes` | POST | Crear reporte (multipart/form-data) |
| `/api/reportes` | GET | Últimos 500 reportes en JSON (para el mapa) |
| `/api/stats` | GET | Contadores por tipo |
| `/uploads/<archivo>` | GET | Fotos subidas |

**Modelo `Reporte`**: `id`, `tipo` (`busco` / `avistada`), `descripcion` (300), `telefono` (20), `lat`, `lng`, `foto`, `creado_en`.

## Correr en local

```bash
# 1. Clonar y entrar al proyecto
git clone git@github.com:danielsteveng0326/buscame.colombia.git
cd buscame.colombia

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / Mac
pip install -r requirements.txt

# 3. Ejecutar (usa SQLite automáticamente, no necesitas Postgres)
python app.py
```

Abre <http://localhost:5000>. El navegador pedirá permiso de ubicación al crear un reporte.

## Despliegue en Railway 🚂

1. **Crear el proyecto**: en [railway.app](https://railway.app) → *New Project* → *Deploy from GitHub repo* → selecciona `danielsteveng0326/buscame.colombia`. Railway detecta Python y usa el `Procfile` automáticamente.

2. **Agregar PostgreSQL**: en el proyecto → *Create* → *Database* → *PostgreSQL*. Luego, en el servicio web → *Variables* → agrega la referencia:
   ```
   DATABASE_URL = ${{Postgres.DATABASE_URL}}
   ```

3. **Montar el volumen para las fotos**: clic derecho sobre el servicio web → *Attach Volume* → mount path: `/app/uploads`. Luego agrega la variable:
   ```
   UPLOAD_FOLDER = /app/uploads
   ```

4. **Variables de entorno** (servicio web → *Variables*):

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
   | `UPLOAD_FOLDER` | `/app/uploads` |
   | `SECRET_KEY` | una cadena aleatoria larga |

5. **Dominio público**: servicio web → *Settings* → *Networking* → *Generate Domain*.

Con eso queda en línea. Cada push a `main` redespliega automáticamente.

## Roadmap

- [ ] Marcar reportes como resueltos ("¡ya apareció!")
- [ ] Filtro por ciudad / departamento
- [ ] Notificaciones cuando aparece un reporte cerca de tu búsqueda
- [ ] Moderación básica de reportes (eliminar spam)
- [ ] PWA instalable con soporte offline
- [ ] Compresión automática de fotos al subirlas

## Licencia

[MIT](LICENSE) — proyecto de código abierto con fines humanitarios. Úsalo, cópialo y mejóralo libremente. 🇨🇴
