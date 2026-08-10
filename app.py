import os
import re
import uuid
from datetime import timedelta

import boto3
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

db_url = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(BASE_DIR, 'buscame.db')}"
# Railway entrega postgres:// pero SQLAlchemy 2.x exige postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Fotos: bucket S3 de Railway si hay credenciales; si no, carpeta local (desarrollo)
S3_BUCKET = os.environ.get("S3_BUCKET")
s3 = None
if S3_BUCKET:
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT"),
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("S3_REGION", "auto"),
    )

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or os.path.join(BASE_DIR, "uploads")
if not S3_BUCKET:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXTENSIONES = {"jpg", "jpeg", "png", "webp"}
TIPOS = {"busco", "avistada"}

DEPARTAMENTOS = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bogotá D.C.", "Bolívar",
    "Boyacá", "Caldas", "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó",
    "Córdoba", "Cundinamarca", "Guainía", "Guaviare", "Huila", "La Guajira",
    "Magdalena", "Meta", "Nariño", "Norte de Santander", "Putumayo", "Quindío",
    "Risaralda", "San Andrés y Providencia", "Santander", "Sucre", "Tolima",
    "Valle del Cauca", "Vaupés", "Vichada",
]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # fotos de máximo 5 MB

db = SQLAlchemy(app)


class Reporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False, index=True)
    departamento = db.Column(db.String(40), index=True)
    descripcion = db.Column(db.String(300), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    foto = db.Column(db.String(80))
    creado_en = db.Column(db.DateTime, server_default=func.now())

    def a_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "departamento": self.departamento,
            "descripcion": self.descripcion,
            "telefono": self.telefono,
            "lat": self.lat,
            "lng": self.lng,
            "foto": f"/uploads/{self.foto}" if self.foto else None,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }


with app.app_context():
    db.create_all()
    # Migración mínima: bases creadas antes de que existiera la columna departamento
    try:
        with db.engine.connect() as conexion:
            conexion.execute(text("ALTER TABLE reporte ADD COLUMN departamento VARCHAR(40)"))
            conexion.commit()
    except Exception:
        pass


@app.template_filter("hora_colombia")
def hora_colombia(fecha):
    """La BD guarda UTC; Colombia es UTC-5 todo el año."""
    if not fecha:
        return ""
    local = fecha - timedelta(hours=5)
    return local.strftime("%d/%m/%Y · %I:%M %p").lower()


@app.template_filter("solo_digitos")
def solo_digitos(telefono):
    return re.sub(r"\D", "", telefono or "")


@app.template_filter("whatsapp")
def whatsapp(telefono):
    digitos = re.sub(r"\D", "", telefono or "")
    return f"57{digitos}" if len(digitos) == 10 else digitos


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/listado/<tipo>")
def listado(tipo):
    if tipo not in TIPOS:
        abort(404)
    departamento = request.args.get("departamento", "")
    consulta = Reporte.query.filter_by(tipo=tipo)
    if departamento in DEPARTAMENTOS:
        consulta = consulta.filter_by(departamento=departamento)
    else:
        departamento = ""
    reportes = consulta.order_by(Reporte.creado_en.desc()).limit(200).all()
    conteo = dict(db.session.query(Reporte.tipo, func.count()).group_by(Reporte.tipo).all())
    return render_template(
        "listado.html",
        tipo=tipo,
        reportes=reportes,
        departamento=departamento,
        departamentos=DEPARTAMENTOS,
        total_busco=conteo.get("busco", 0),
        total_avistada=conteo.get("avistada", 0),
    )


@app.route("/reportar/<tipo>")
def reportar(tipo):
    if tipo not in TIPOS:
        abort(404)
    return render_template("reportar.html", tipo=tipo, departamentos=DEPARTAMENTOS)


@app.route("/api/reportes", methods=["POST"])
def crear_reporte():
    tipo = request.form.get("tipo", "")
    departamento = request.form.get("departamento", "")
    descripcion = request.form.get("descripcion", "").strip()
    telefono = request.form.get("telefono", "").strip()

    if tipo not in TIPOS:
        return jsonify(error="Tipo de reporte inválido."), 400
    if departamento not in DEPARTAMENTOS:
        return jsonify(error="Selecciona el departamento."), 400
    if not descripcion or not telefono:
        return jsonify(error="La descripción y el teléfono son obligatorios."), 400
    try:
        lat = float(request.form.get("lat", ""))
        lng = float(request.form.get("lng", ""))
    except ValueError:
        return jsonify(error="Ubicación inválida. Activa el GPS e intenta de nuevo."), 400

    nombre_foto = None
    foto = request.files.get("foto")
    if foto and foto.filename:
        ext = foto.filename.rsplit(".", 1)[-1].lower()
        if ext not in EXTENSIONES:
            return jsonify(error="La foto debe ser JPG, PNG o WEBP."), 400
        nombre_foto = f"{uuid.uuid4().hex}.{ext}"
        if s3:
            s3.upload_fileobj(
                foto,
                S3_BUCKET,
                nombre_foto,
                ExtraArgs={"ContentType": foto.mimetype or "image/jpeg"},
            )
        else:
            foto.save(os.path.join(UPLOAD_FOLDER, nombre_foto))

    reporte = Reporte(
        tipo=tipo,
        departamento=departamento,
        descripcion=descripcion[:300],
        telefono=telefono[:20],
        lat=lat,
        lng=lng,
        foto=nombre_foto,
    )
    db.session.add(reporte)
    db.session.commit()
    return jsonify(reporte.a_dict()), 201


@app.route("/api/reportes")
def listar_reportes():
    reportes = Reporte.query.order_by(Reporte.creado_en.desc()).limit(500).all()
    return jsonify([r.a_dict() for r in reportes])


@app.route("/api/stats")
def stats():
    filas = db.session.query(Reporte.tipo, func.count()).group_by(Reporte.tipo).all()
    conteo = dict(filas)
    return jsonify(busco=conteo.get("busco", 0), avistada=conteo.get("avistada", 0))


@app.route("/uploads/<path:nombre>")
def uploads(nombre):
    if s3:
        # El bucket de Railway no es público: se redirige a una URL firmada temporal
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": nombre},
            ExpiresIn=3600,
        )
        return redirect(url)
    return send_from_directory(UPLOAD_FOLDER, nombre)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
