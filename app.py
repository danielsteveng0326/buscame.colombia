import os
import uuid

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    request,
    send_from_directory,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

db_url = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(BASE_DIR, 'buscame.db')}"
# Railway entrega postgres:// pero SQLAlchemy 2.x exige postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXTENSIONES = {"jpg", "jpeg", "png", "webp"}
TIPOS = {"busco", "avistada"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # fotos de máximo 5 MB

db = SQLAlchemy(app)


class Reporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False, index=True)
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
            "descripcion": self.descripcion,
            "telefono": self.telefono,
            "lat": self.lat,
            "lng": self.lng,
            "foto": f"/uploads/{self.foto}" if self.foto else None,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }


with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/reportar/<tipo>")
def reportar(tipo):
    if tipo not in TIPOS:
        abort(404)
    return render_template("reportar.html", tipo=tipo)


@app.route("/api/reportes", methods=["POST"])
def crear_reporte():
    tipo = request.form.get("tipo", "")
    descripcion = request.form.get("descripcion", "").strip()
    telefono = request.form.get("telefono", "").strip()

    if tipo not in TIPOS:
        return jsonify(error="Tipo de reporte inválido."), 400
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
        foto.save(os.path.join(UPLOAD_FOLDER, nombre_foto))

    reporte = Reporte(
        tipo=tipo,
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
    return send_from_directory(UPLOAD_FOLDER, nombre)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
