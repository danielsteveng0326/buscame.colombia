const form = document.getElementById("form-reporte");
const estadoGps = document.getElementById("estado-gps");
const gpsTexto = document.getElementById("gps-texto");
const gpsReintentar = document.getElementById("gps-reintentar");
const latInput = document.getElementById("lat");
const lngInput = document.getElementById("lng");
const inputFoto = document.getElementById("foto");
const preview = document.getElementById("preview");
const cajaError = document.getElementById("error");
const botonEnviar = document.getElementById("enviar");
const panelExito = document.getElementById("exito");

const MAX_FOTO = 5 * 1024 * 1024;

function pedirUbicacion() {
  estadoGps.dataset.estado = "buscando";
  gpsTexto.textContent = "📡 Obteniendo tu ubicación…";
  gpsReintentar.hidden = true;

  if (!navigator.geolocation) {
    fallaGps("Tu navegador no soporta geolocalización.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      latInput.value = pos.coords.latitude.toFixed(6);
      lngInput.value = pos.coords.longitude.toFixed(6);
      estadoGps.dataset.estado = "ok";
      gpsTexto.textContent = "✅ Ubicación lista";
    },
    () => fallaGps("No pudimos obtener tu ubicación. Activa el GPS y acepta el permiso."),
    { enableHighAccuracy: true, timeout: 12000 }
  );
}

function fallaGps(mensaje) {
  estadoGps.dataset.estado = "error";
  gpsTexto.textContent = `⚠️ ${mensaje}`;
  gpsReintentar.hidden = false;
}

function mostrarError(mensaje) {
  cajaError.textContent = mensaje;
  cajaError.hidden = false;
}

gpsReintentar.addEventListener("click", pedirUbicacion);
pedirUbicacion();

inputFoto.addEventListener("change", () => {
  const archivo = inputFoto.files[0];
  preview.hidden = true;
  if (!archivo) return;
  if (archivo.size > MAX_FOTO) {
    mostrarError("La foto supera los 5 MB. Elige una más liviana.");
    inputFoto.value = "";
    return;
  }
  cajaError.hidden = true;
  preview.src = URL.createObjectURL(archivo);
  preview.hidden = false;
});

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  cajaError.hidden = true;

  if (!form.descripcion.value.trim() || !form.telefono.value.trim()) {
    mostrarError("La descripción y el teléfono son obligatorios.");
    return;
  }
  if (!latInput.value || !lngInput.value) {
    mostrarError("Necesitamos tu ubicación para publicar el reporte.");
    return;
  }

  botonEnviar.disabled = true;
  botonEnviar.textContent = "Publicando…";

  try {
    const resp = await fetch("/api/reportes", {
      method: "POST",
      body: new FormData(form),
    });
    const datos = await resp.json();
    if (!resp.ok) {
      mostrarError(datos.error || "No se pudo publicar el reporte. Intenta de nuevo.");
      return;
    }
    form.hidden = true;
    panelExito.hidden = false;
  } catch (e) {
    mostrarError("Error de conexión. Revisa tu internet e intenta de nuevo.");
  } finally {
    botonEnviar.disabled = false;
    botonEnviar.textContent = "Publicar reporte";
  }
});
