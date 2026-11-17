/**
 * AGADIR MAPPING — GESTIONNAIRE D'ÉTAT CENTRALISÉ (STATE MANAGEMENT)
 * Coordonne la synchronisation bidirectionnelle entre les quatre cadrans.
 */

const AppState = {
  // Données chargées depuis l'API REST
  points: [],
  tour: null,
  multiAgent: null,
  metrics: null,

  // Sélections et filtres actifs
  selectedPointId: null,
  selectedStepIndex: null,
  activeCategory: "ALL",
  searchQuery: "",
  isTourPathVisible: true,
  isPlayingTour: false,
  autoPlayTimer: null,

  // Souscriptions aux événements
  listeners: {},

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  },

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  },

  /**
   * Sélectionne un point géographique et notifie tous les cadrans.
   */
  selectPoint(pointId, source = "unknown") {
    this.selectedPointId = pointId;
    console.log(`[AppState] Point sélectionné : #${pointId} (source : ${source})`);

    // Synchronisation avec le cadran de la tournée : trouver l'étape correspondante
    if (this.tour && this.tour.steps) {
      const stepIdx = this.tour.steps.findIndex(s => s.to_point_id === pointId);
      if (stepIdx !== -1) {
        this.selectedStepIndex = stepIdx;
      }
    }

    this.emit("pointSelected", { pointId, source });
  },

  /**
   * Sélectionne une étape de tournée et notifie tous les cadrans.
   */
  selectStep(stepIndex, source = "unknown") {
    if (!this.tour || !this.tour.steps || stepIndex < 0 || stepIndex >= this.tour.steps.length) {
      return;
    }
    this.selectedStepIndex = stepIndex;
    const step = this.tour.steps[stepIndex];
    this.selectedPointId = step.to_point_id;
    console.log(`[AppState] Étape sélectionnée : ${step.step}/41 -> Point #${step.to_point_id} (source : ${source})`);

    this.emit("stepSelected", { stepIndex, step, source });
  },

  /**
   * Réinitialise toutes les sélections et filtres.
   */
  resetAll() {
    this.selectedPointId = null;
    this.selectedStepIndex = null;
    this.activeCategory = "ALL";
    this.searchQuery = "";
    if (this.isPlayingTour) {
      this.stopAutoPlay();
    }
    this.emit("reset", {});
  },

  /**
   * Démarre la lecture pas à pas de la tournée.
   */
  toggleAutoPlay() {
    if (this.isPlayingTour) {
      this.stopAutoPlay();
    } else {
      this.startAutoPlay();
    }
  },

  startAutoPlay() {
    if (!this.tour || !this.tour.steps || this.tour.steps.length === 0) return;
    this.isPlayingTour = true;
    this.emit("autoPlayChanged", { isPlaying: true });

    let current = this.selectedStepIndex !== null ? this.selectedStepIndex : -1;
    this.autoPlayTimer = setInterval(() => {
      current = (current + 1) % this.tour.steps.length;
      this.selectStep(current, "autoplay");
    }, 1800);
  },

  stopAutoPlay() {
    this.isPlayingTour = false;
    if (this.autoPlayTimer) {
      clearInterval(this.autoPlayTimer);
      this.autoPlayTimer = null;
    }
    this.emit("autoPlayChanged", { isPlaying: false });
  }
};

// Initialisation globale de l'application
document.addEventListener("DOMContentLoaded", async () => {
  console.log("[Dashboard] Initialisation du tableau de bord AGADIR MAPPING...");

  // Mise à jour de l'horodatage
  const updateTimestamp = () => {
    const el = document.getElementById("header-timestamp");
    if (el) {
      const now = new Date();
      el.textContent = `Actualisé : ${now.toLocaleTimeString("fr-FR")} UTC`;
    }
  };
  updateTimestamp();

  // Gestion du sélecteur de disposition de grille
  const selectLayout = document.getElementById("select-layout");
  const dashboardGrid = document.getElementById("dashboard-grid");
  if (selectLayout && dashboardGrid) {
    selectLayout.addEventListener("change", (e) => {
      const val = e.target.value;
      dashboardGrid.className = "dashboard-grid";
      if (val === "max-1") dashboardGrid.classList.add("maximized-1");
      else if (val === "max-2") dashboardGrid.classList.add("maximized-2");
      else if (val === "max-3") dashboardGrid.classList.add("maximized-3");
      else if (val === "max-4") dashboardGrid.classList.add("maximized-4");
      
      // Forcer le redimensionnement de la carte Leaflet et des graphiques
      setTimeout(() => {
        if (window.quadrantMap && window.quadrantMap.map) {
          window.quadrantMap.map.invalidateSize();
        }
        if (window.quadrantMetrics && typeof window.quadrantMetrics.renderAllCharts === "function") {
          window.quadrantMetrics.renderAllCharts();
        }
      }, 250);
    });
  }

  // Bouton de réinitialisation générale
  const btnSync = document.getElementById("btn-sync");
  if (btnSync) {
    btnSync.addEventListener("click", () => {
      AppState.resetAll();
    });
  }

  // Chargement des données depuis l'API REST
  try {
    const [pointsRes, tourRes, multiAgentRes, metricsRes] = await Promise.all([
      fetch("/api/points").then(r => r.json()),
      fetch("/api/tour").then(r => r.json()),
      fetch("/api/multi-agent").then(r => r.json()),
      fetch("/api/metrics").then(r => r.json())
    ]);

    AppState.points = pointsRes;
    AppState.tour = tourRes;
    AppState.multiAgent = multiAgentRes;
    AppState.metrics = metricsRes;

    console.log(`[Dashboard] ${AppState.points.length} points chargés avec succès.`);
    console.log(`[Dashboard] Tournée officielle de ${AppState.tour.total_distance_m} m chargée.`);

    // Initialisation des 4 Cadrans
    if (window.Quadrant1Map) {
      window.quadrantMap = new window.Quadrant1Map(AppState);
    }
    if (window.Quadrant2Tour) {
      window.quadrantTour = new window.Quadrant2Tour(AppState);
    }
    if (window.Quadrant3Agents) {
      window.quadrantAgents = new window.Quadrant3Agents(AppState);
    }
    if (window.Quadrant4Metrics) {
      window.quadrantMetrics = new window.Quadrant4Metrics(AppState);
    }

  } catch (error) {
    console.error("[Dashboard] Erreur critique lors du chargement des données :", error);
    alert("Erreur lors de la connexion à l'API du dashboard. Vérifiez que le serveur est démarré.");
  }
});
