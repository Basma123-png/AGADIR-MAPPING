/**
 * AGADIR MAPPING — CADRAN 2 : VISUALISATION DE LA TOURNÉE OPTIMISÉE
 * Affichage des 41 étapes, tracé orienté sur la carte, navigation et synchronisation.
 */

class Quadrant2Tour {
  constructor(appState) {
    this.appState = appState;
    this.stepCards = [];
    this.polyLines = [];
    this.activePolyline = null;
    this.isPathVisible = true;

    this.initTourView();
    this.bindEvents();
    this.drawTourOnMap();
  }

  initTourView() {
    console.log("[Cadran 2] Initialisation de la vue de la tournée...");
    const tour = this.appState.tour;
    if (!tour || !tour.steps) return;

    // Mise à jour des compteurs statistiques
    const distEl = document.getElementById("tour-dist-stat");
    const stopsEl = document.getElementById("tour-stops-stat");
    const gainEl = document.getElementById("tour-gain-stat");

    if (distEl) distEl.textContent = `${tour.total_distance_m.toLocaleString("fr-FR")} m`;
    if (stopsEl) stopsEl.textContent = `${tour.total_stops}`;
    if (gainEl && tour.metadata && tour.metadata.gain_percent) {
      gainEl.textContent = `-${tour.metadata.gain_percent}%`;
    }

    // Rendu de la liste des 41 étapes
    this.renderStepsList();
  }

  renderStepsList() {
    const container = document.getElementById("tour-steps-list");
    if (!container || !this.appState.tour || !this.appState.tour.steps) return;

    container.innerHTML = "";
    this.stepCards = [];

    this.appState.tour.steps.forEach((step, idx) => {
      const isReturnToDepot = step.to_point_id === 0;
      const isCoastal = step.is_coastal || step.to_point_id === 40;

      const card = document.createElement("div");
      card.className = "tour-step-card";
      card.id = `step-card-${idx}`;

      card.innerHTML = `
        <div class="step-number">${step.step}</div>
        <div class="step-details">
          <div class="step-title">
            ${isReturnToDepot ? '🏁 Retour Dépôt #0' : (isCoastal ? '🌊 #40 ' + step.to_name : `#${step.to_point_id} ` + step.to_name)}
          </div>
          <div class="step-meta">
            <span>De #${step.from_point_id} ➔ #${step.to_point_id}</span>
            <span>• ${step.district}</span>
            <span>• ${step.category}</span>
          </div>
        </div>
        <div class="step-distance">
          +${step.leg_distance_m.toFixed(1)} m
          <div class="step-cumul">${(step.cumulative_distance_m / 1000).toFixed(2)} km</div>
        </div>
      `;

      card.addEventListener("click", () => {
        this.appState.selectStep(idx, "tour-list");
      });

      container.appendChild(card);
      this.stepCards.push(card);
    });
  }

  bindEvents() {
    // Bouton Étape Précédente
    const btnPrev = document.getElementById("btn-prev-step");
    if (btnPrev) {
      btnPrev.addEventListener("click", () => {
        const cur = this.appState.selectedStepIndex !== null ? this.appState.selectedStepIndex : 0;
        const target = (cur - 1 + this.appState.tour.steps.length) % this.appState.tour.steps.length;
        this.appState.selectStep(target, "tour-control");
      });
    }

    // Bouton Étape Suivante
    const btnNext = document.getElementById("btn-next-step");
    if (btnNext) {
      btnNext.addEventListener("click", () => {
        const cur = this.appState.selectedStepIndex !== null ? this.appState.selectedStepIndex : -1;
        const target = (cur + 1) % this.appState.tour.steps.length;
        this.appState.selectStep(target, "tour-control");
      });
    }

    // Bouton Lecture Automatique
    const btnAutoPlay = document.getElementById("btn-autoplay-tour");
    if (btnAutoPlay) {
      btnAutoPlay.addEventListener("click", () => {
        this.appState.toggleAutoPlay();
      });
    }

    // Bouton Afficher / Masquer Tracé
    const btnTogglePath = document.getElementById("btn-toggle-tour-path");
    if (btnTogglePath) {
      btnTogglePath.addEventListener("click", () => {
        this.toggleTourPath();
      });
    }

    // Réception des événements du State Manager
    this.appState.on("stepSelected", ({ stepIndex, step }) => {
      this.highlightStepCard(stepIndex);
      this.highlightStepOnMap(stepIndex);
      this.updateStepIndicator(stepIndex + 1);
    });

    this.appState.on("pointSelected", ({ pointId }) => {
      // Si un point est sélectionné dans Cadran 1, activer l'étape de tournée correspondante
      if (this.appState.tour && this.appState.tour.steps) {
        const stepIdx = this.appState.tour.steps.findIndex(s => s.to_point_id === pointId);
        if (stepIdx !== -1) {
          this.highlightStepCard(stepIdx);
          this.highlightStepOnMap(stepIdx);
          this.updateStepIndicator(stepIdx + 1);
        }
      }
    });

    this.appState.on("autoPlayChanged", ({ isPlaying }) => {
      const btn = document.getElementById("btn-autoplay-tour");
      if (btn) {
        btn.textContent = isPlaying ? "⏸️ Pause" : "⏯️ Lecture";
        btn.classList.toggle("btn-primary", isPlaying);
      }
    });

    this.appState.on("reset", () => {
      this.stepCards.forEach(c => c.classList.remove("active"));
      this.updateStepIndicator(null);
      if (this.activePolyline && window.quadrantMap && window.quadrantMap.map) {
        window.quadrantMap.map.removeLayer(this.activePolyline);
        this.activePolyline = null;
      }
    });
  }

  drawTourOnMap() {
    if (!window.quadrantMap || !window.quadrantMap.map || typeof L === "undefined") {
      // Réessayer dans 300 ms si Leaflet s'initialise
      setTimeout(() => this.drawTourOnMap(), 300);
      return;
    }

    const map = window.quadrantMap.map;
    const tourLayer = window.quadrantMap.tourPolylineLayer;
    if (!tourLayer) return;

    tourLayer.clearLayers();
    this.polyLines = [];

    const steps = this.appState.tour.steps;
    if (!steps || steps.length === 0) return;

    // Tracé complet de la tournée officielle (41 segments)
    const latlngs = [];
    steps.forEach(s => {
      if (latlngs.length === 0 && s.from_latitude && s.from_longitude) {
        latlngs.push([s.from_latitude, s.from_longitude]);
      }
      if (s.to_latitude && s.to_longitude) {
        latlngs.push([s.to_latitude, s.to_longitude]);
      }
    });

    // Ligne globale bleue semi-transparente
    const fullPolyline = L.polyline(latlngs, {
      color: "#2563eb",
      weight: 3.5,
      opacity: 0.75,
      dashArray: "6, 8",
      lineJoin: "round"
    });

    tourLayer.addLayer(fullPolyline);
    this.polyLines.push(fullPolyline);

    console.log(`[Cadran 2] Tracé de la tournée officielle injecté sur la carte (${latlngs.length} sommets).`);
  }

  highlightStepCard(stepIndex) {
    this.stepCards.forEach((card, idx) => {
      if (idx === stepIndex) {
        card.classList.add("active");
        card.scrollIntoView({ behavior: "smooth", block: "nearest" });
      } else {
        card.classList.remove("active");
      }
    });
  }

  highlightStepOnMap(stepIndex) {
    if (!window.quadrantMap || !window.quadrantMap.map || typeof L === "undefined") return;
    const map = window.quadrantMap.map;
    const step = this.appState.tour.steps[stepIndex];
    if (!step) return;

    // Supprimer l'ancien segment actif
    if (this.activePolyline) {
      map.removeLayer(this.activePolyline);
      this.activePolyline = null;
    }

    if (step.from_latitude && step.from_longitude && step.to_latitude && step.to_longitude) {
      const segmentCoords = [
        [step.from_latitude, step.from_longitude],
        [step.to_latitude, step.to_longitude]
      ];

      this.activePolyline = L.polyline(segmentCoords, {
        color: "#f43f5e",
        weight: 6,
        opacity: 0.95,
        lineCap: "round"
      }).addTo(map);

      // Animation de pulsation ou centrage léger
      map.panTo([step.to_latitude, step.to_longitude], { animate: true, duration: 0.5 });
    }
  }

  updateStepIndicator(stepNumber) {
    const el = document.getElementById("tour-step-indicator");
    if (el) {
      el.textContent = stepNumber !== null ? `Étape ${stepNumber} / 41` : "Étape -- / 41";
    }
  }

  toggleTourPath() {
    if (!window.quadrantMap || !window.quadrantMap.map) return;
    const tourLayer = window.quadrantMap.tourPolylineLayer;
    if (!tourLayer) return;

    this.isPathVisible = !this.isPathVisible;
    if (this.isPathVisible) {
      window.quadrantMap.map.addLayer(tourLayer);
    } else {
      window.quadrantMap.map.removeLayer(tourLayer);
    }

    const btn = document.getElementById("btn-toggle-tour-path");
    if (btn) {
      btn.textContent = this.isPathVisible ? "👁️ Tracé On" : "👁️ Tracé Off";
    }
  }
}

window.Quadrant2Tour = Quadrant2Tour;
