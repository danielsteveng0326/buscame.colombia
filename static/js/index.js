const COLORES = { busco: "#e63946", avistada: "#2a9d8f" };
const ETIQUETAS = { busco: "🔍 Busco a mi mascota", avistada: "📍 Posible mascota perdida" };

const mapa = L.map("mapa").setView([4.57, -74.3], 6); // centro de Colombia
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap",
  maxZoom: 18,
}).addTo(mapa);

const capaReportes = L.layerGroup().addTo(mapa);

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = texto || "";
  return div.innerHTML;
}

function enlacesContacto(telefono) {
  const digitos = (telefono || "").replace(/\D/g, "");
  if (!digitos) return "";
  const whatsapp = digitos.length === 10 ? `57${digitos}` : digitos;
  return `<p class="popup-contacto">
    <a href="tel:${digitos}">📞 Llamar</a>
    <a href="https://wa.me/${whatsapp}" target="_blank" rel="noopener">💬 WhatsApp</a>
  </p>`;
}

function popupReporte(r) {
  const foto = r.foto ? `<img src="${r.foto}" class="popup-foto" alt="Foto de la mascota">` : "";
  const depto = r.departamento ? `<p class="popup-depto">📍 ${escapar(r.departamento)}</p>` : "";
  return `${foto}
    <p class="popup-tipo" style="color:${COLORES[r.tipo]}">${ETIQUETAS[r.tipo] || r.tipo}</p>
    <p>${escapar(r.descripcion)}</p>
    ${depto}
    ${enlacesContacto(r.telefono)}`;
}

async function cargarReportes() {
  try {
    const resp = await fetch("/api/reportes");
    const reportes = await resp.json();
    capaReportes.clearLayers();
    reportes.forEach((r) => {
      L.circleMarker([r.lat, r.lng], {
        radius: 9,
        color: "#fff",
        weight: 2,
        fillColor: COLORES[r.tipo] || "#555",
        fillOpacity: 0.9,
      })
        .bindPopup(popupReporte(r), { maxWidth: 240 })
        .addTo(capaReportes);
    });
  } catch (e) {
    /* sin conexión: se reintenta en el próximo ciclo */
  }
}

async function cargarStats() {
  try {
    const resp = await fetch("/api/stats");
    const stats = await resp.json();
    document.getElementById("contador-busco").textContent = stats.busco;
    document.getElementById("contador-avistada").textContent = stats.avistada;
  } catch (e) {
    /* sin conexión: se reintenta en el próximo ciclo */
  }
}

cargarReportes();
cargarStats();
setInterval(cargarStats, 10000);
setInterval(cargarReportes, 30000);
