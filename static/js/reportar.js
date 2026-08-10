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

// Capital de cada departamento: se usa para sugerir la región según el GPS
const CAPITALES = {
  "Amazonas": [-4.215, -69.941],
  "Antioquia": [6.2442, -75.5812],
  "Arauca": [7.0847, -70.7591],
  "Atlántico": [10.9639, -74.7964],
  "Bogotá D.C.": [4.711, -74.0721],
  "Bolívar": [10.391, -75.4794],
  "Boyacá": [5.5353, -73.3678],
  "Caldas": [5.0703, -75.5138],
  "Caquetá": [1.6144, -75.6062],
  "Casanare": [5.3378, -72.3959],
  "Cauca": [2.4448, -76.6147],
  "Cesar": [10.4631, -73.2532],
  "Chocó": [5.6947, -76.6611],
  "Córdoba": [8.7479, -75.8814],
  "Cundinamarca": [4.8087, -74.3547],
  "Guainía": [3.8653, -67.9239],
  "Guaviare": [2.5729, -72.6459],
  "Huila": [2.9273, -75.2819],
  "La Guajira": [11.5444, -72.9072],
  "Magdalena": [11.2408, -74.199],
  "Meta": [4.142, -73.6266],
  "Nariño": [1.2136, -77.2811],
  "Norte de Santander": [7.8939, -72.5078],
  "Putumayo": [1.1478, -76.6481],
  "Quindío": [4.5339, -75.6811],
  "Risaralda": [4.8087, -75.6906],
  "San Andrés y Providencia": [12.5847, -81.7006],
  "Santander": [7.1193, -73.1227],
  "Sucre": [9.3047, -75.3978],
  "Tolima": [4.4389, -75.2322],
  "Valle del Cauca": [3.4516, -76.532],
  "Vaupés": [1.1983, -70.1733],
  "Vichada": [6.189, -67.4859],
};

function sugerirDepartamento(lat, lng) {
  const selector = document.getElementById("departamento");
  if (!selector || selector.value) return; // no pisar una elección manual
  let mejor = null;
  let mejorDistancia = Infinity;
  for (const [depto, [dLat, dLng]] of Object.entries(CAPITALES)) {
    const distancia = (lat - dLat) ** 2 + (lng - dLng) ** 2;
    if (distancia < mejorDistancia) {
      mejorDistancia = distancia;
      mejor = depto;
    }
  }
  if (mejor) selector.value = mejor;
}

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
      sugerirDepartamento(pos.coords.latitude, pos.coords.longitude);
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

  if (!form.departamento.value) {
    mostrarError("Selecciona el departamento.");
    return;
  }
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
