/**
 * AGADIR MAPPING — CADRAN 1 : CARTOGRAPHIE GÉOGRAPHIQUE D'AGADIR
 * Gestion de la carte interactive Leaflet, des marqueurs, filtres et synchronisation.
 */

class Quadrant1Map {
  constructor(appState) {
    this.appState = appState;
    this.map = null;
    this.markers = {};
    this.markerLayerGroup = null;
    this.tourPolylineLayer = null;

    // Coordonnées du Dépôt Central (Place Al Amal)
    this.depotCoords = [30.4215, -9.5985];

    this.initMap();
    this.bindEvents();
    this.renderMarkers();
  }

  initMap() {
    console.log("[Cadran 1] Initialisation de la carte Leaflet...");
    const container = document.getElementById("leaflet-map");
    if (!container) return;

    if (typeof L === "undefined") {
      container.innerHTML = `
        <div style="padding: 30px; text-align: center; color: var(--accent-amber);">
          <h3>⚠️ Mode Cartographique Hors-Ligne</h3>
          <p>La bibliothèque cartographique Leaflet n'a pas pu être chargée depuis le CDN.</p>
          <p>Toutes les données des 41 points et de la tournée restent consultables dans les Cadrans 2, 3 et 4.</p>
        </div>
      `;
      return;
    }

    // Création de l'instance Leaflet centrée sur la Place Al Amal
    this.map = L.map("leaflet-map", {
      center: this.depotCoords,
      zoom: 14,
      zoomControl: true,
      minZoom: 12,
      maxZoom: 18
    });

    // Couche OpenStreetMap avec gestion des erreurs
    const tileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors | AGADIR MAPPING',
      maxZoom: 19
    });

    tileLayer.on("tileerror", (error) => {
      console.warn("[Cadran 1] Avertissement : échec du chargement d'une tuile cartographique :", error);
    });

    tileLayer.addTo(this.map);

    this.markerLayerGroup = L.layerGroup().addTo(this.map);
    this.tourPolylineLayer = L.layerGroup().addTo(this.map);
  }

  bindEvents() {
    // Bouton recentrer sur le dépôt
    const btnRecenter = document.getElementById("btn-recenter-depot");
    if (btnRecenter) {
      btnRecenter.addEventListener("click", () => {
        this.centerOnDepot();
      });
    }

    // Bouton vue globale (fitBounds)
    const btnFit = document.getElementById("btn-fit-bounds");
    if (btnFit) {
      btnFit.addEventListener("click", () => {
        this.fitAllPoints();
      });
    }

    // Recherche textuelle
    const searchInput = document.getElementById("map-search");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.appState.searchQuery = e.target.value.toLowerCase().trim();
        this.filterAndRenderMarkers();
      });
    }

    // Filtre par catégorie
    const categorySelect = document.getElementById("map-category-filter");
    if (categorySelect) {
      categorySelect.addEventListener("change", (e) => {
        this.appState.activeCategory = e.target.value;
        this.filterAndRenderMarkers();
      });
    }

    // Bouton fermer la fiche point sélectionné
    const btnCloseCard = document.getElementById("card-btn-close");
    if (btnCloseCard) {
      btnCloseCard.addEventListener("click", () => {
        this.hideSelectedCard();
      });
    }

    // Bouton voir dans la tournée
    const btnViewTour = document.getElementById("card-btn-view-in-tour");
    if (btnViewTour) {
      btnViewTour.addEventListener("click", () => {
        if (this.appState.selectedPointId !== null) {
          this.appState.selectPoint(this.appState.selectedPointId, "map-card");
        }
      });
    }

    // Écoute des événements du State Manager
    this.appState.on("pointSelected", ({ pointId, source }) => {
      if (source !== "map") {
        this.highlightPointOnMap(pointId, true);
      }
    });

    this.appState.on("stepSelected", ({ step, source }) => {
      if (source !== "map") {
        this.highlightPointOnMap(step.to_point_id, true);
      }
    });

    this.appState.on("reset", () => {
      this.hideSelectedCard();
      this.centerOnDepot();
      const search = document.getElementById("map-search");
      if (search) search.value = "";
      const cat = document.getElementById("map-category-filter");
      if (cat) cat.value = "ALL";
      this.filterAndRenderMarkers();
    });
  }

  renderMarkers() {
    if (!this.map || !this.markerLayerGroup) return;

    this.markerLayerGroup.clearLayers();
    this.markers = {};

    this.appState.points.forEach(point => {
      const isDepot = point.point_id === 0;
      const isCoastal = point.point_id === 40;

      // Construction du marqueur HTML personnalisé
      let iconClass = "custom-map-pin client-pin";
      let iconContent = `${point.point_id}`;
      let pinSize = [26, 26];

      if (isDepot) {
        iconClass = "custom-map-pin depot-pin";
        iconContent = "★ 0";
        pinSize = [34, 34];
      } else if (isCoastal) {
        iconClass = "custom-map-pin coastal-pin";
        iconContent = "🌊 40";
        pinSize = [30, 30];
      }

      const customIcon = L.divIcon({
        className: iconClass,
        html: `<span>${iconContent}</span>`,
        iconSize: pinSize,
        iconAnchor: [pinSize[0] / 2, pinSize[1] / 2],
        popupAnchor: [0, -pinSize[1] / 2]
      });

      const marker = L.marker([point.latitude, point.longitude], {
        icon: customIcon,
        title: point.name
      });

      // Construction du popup détaillé
      const popupContent = `
        <div style="font-family: inherit; font-size: 12px; min-width: 200px; color: #1e293b;">
          <div style="font-weight: 800; color: ${isDepot ? '#d97706' : (isCoastal ? '#0891b2' : '#2563eb')}; font-size: 13px;">
            ${isDepot ? 'DÉPÔT CENTRAL #0' : (isCoastal ? 'POINT LITTORAL #40' : `POINT #${point.point_id}`)}
          </div>
          <div style="font-weight: 700; margin: 3px 0; font-size: 13px;">${point.name}</div>
          <div style="color: #64748b; font-size: 11px;">📍 ${point.street} (${point.district})</div>
          <div style="margin-top: 4px; font-size: 11px;">Catégorie : <strong>${point.category}</strong></div>
          <div style="font-size: 11px;">Coordonnées : ${point.latitude.toFixed(5)}, ${point.longitude.toFixed(5)}</div>
          ${!isDepot ? `<div style="font-size: 11px; color: #059669;">Trajet OSRM depuis dépôt : <strong>${point.osrm_route_from_depot_m} m</strong> (~${point.osrm_route_from_depot_min} min)</div>` : ''}
          <div style="margin-top: 8px;">
            <button onclick="window.AppState.selectPoint(${point.point_id}, 'popup')" style="padding: 4px 8px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px; width: 100%;">
              Sélectionner ce point
            </button>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);

      marker.on("click", () => {
        this.appState.selectPoint(point.point_id, "map");
        this.showSelectedCard(point);
      });

      this.markers[point.point_id] = marker;
      this.markerLayerGroup.addLayer(marker);
    });

    this.updatePointsCountDisplay(this.appState.points.length);
  }

  filterAndRenderMarkers() {
    if (!this.map || !this.markerLayerGroup) return;

    const query = this.appState.searchQuery;
    const cat = this.appState.activeCategory;

    let visibleCount = 0;

    this.appState.points.forEach(point => {
      const marker = this.markers[point.point_id];
      if (!marker) return;

      const matchesQuery = !query || 
        point.name.toLowerCase().includes(query) ||
        point.street.toLowerCase().includes(query) ||
        point.district.toLowerCase().includes(query) ||
        String(point.point_id) === query ||
        `#${point.point_id}` === query;

      const matchesCat = cat === "ALL" || 
        point.category === cat ||
        (cat === "Dépôt Central" && point.point_id === 0) ||
        (cat === "Destination Littorale" && point.point_id === 40);

      if (matchesQuery && matchesCat) {
        if (!this.markerLayerGroup.hasLayer(marker)) {
          this.markerLayerGroup.addLayer(marker);
        }
        visibleCount++;
      } else {
        if (this.markerLayerGroup.hasLayer(marker)) {
          this.markerLayerGroup.removeLayer(marker);
        }
      }
    });

    this.updatePointsCountDisplay(visibleCount);
  }

  updatePointsCountDisplay(count) {
    const el = document.getElementById("map-points-count");
    if (el) {
      el.textContent = `${count} / ${this.appState.points.length} points`;
    }
  }

  highlightPointOnMap(pointId, shouldPan = true) {
    if (!this.map) return;

    // Réinitialiser les styles précédents
    Object.values(this.markers).forEach(m => {
      const el = m.getElement();
      if (el) el.classList.remove("highlighted-pin");
    });

    const targetMarker = this.markers[pointId];
    if (targetMarker) {
      const el = targetMarker.getElement();
      if (el) el.classList.add("highlighted-pin");

      const point = this.appState.points.find(p => p.point_id === pointId);
      if (point) {
        this.showSelectedCard(point);
        if (shouldPan) {
          this.map.panTo([point.latitude, point.longitude], { animate: true, duration: 0.6 });
        }
        targetMarker.openPopup();
      }
    }
  }

  showSelectedCard(point) {
    const card = document.getElementById("map-point-card");
    const badge = document.getElementById("card-point-badge");
    const name = document.getElementById("card-point-name");
    const desc = document.getElementById("card-point-desc");

    if (!card || !badge || !name || !desc) return;

    badge.textContent = point.point_id === 0 ? "DÉPÔT CENTRAL #0" : (point.point_id === 40 ? "POINT LITTORAL #40" : `DESTINATION #${point.point_id}`);
    name.textContent = point.name;
    desc.textContent = `📍 ${point.street} (${point.district}) • Catégorie : ${point.category} • GPS : ${point.latitude.toFixed(4)}, ${point.longitude.toFixed(4)}`;

    card.style.display = "flex";
  }

  hideSelectedCard() {
    const card = document.getElementById("map-point-card");
    if (card) card.style.display = "none";
  }

  centerOnDepot() {
    if (this.map) {
      this.map.flyTo(this.depotCoords, 15, { animate: true, duration: 0.8 });
      this.highlightPointOnMap(0, false);
    }
  }

  fitAllPoints() {
    if (this.map && this.appState.points.length > 0) {
      const bounds = L.latLngBounds(this.appState.points.map(p => [p.latitude, p.longitude]));
      this.map.fitBounds(bounds, { padding: [30, 30], animate: true });
    }
  }
}

window.Quadrant1Map = Quadrant1Map;
