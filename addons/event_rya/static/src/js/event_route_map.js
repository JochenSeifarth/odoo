import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.EventRouteMap = publicWidget.Widget.extend({
    selector: ".o_event_route_map",

    start() {
        this.eventId = this.el.dataset.eventId;

        this._map = null;
        this._initInProgress = false;

        this._zoomDisplay = null;
        this._updateZoomDisplay = this._updateZoomDisplay.bind(this);

        this._initMap().catch(console.error);
    },

    destroy() {
        if (this._map) {
            this._map.off();
            this._map.remove();
            this._map = null;
        }
        return this._super(...arguments);
    },

    _ensureNotInitialized() {
        if (this._initInProgress || this._map) return false;
        this._initInProgress = true;
        return true;
    },

    async _initMap() {
        if (!this._ensureNotInitialized()) return;

        this.el.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:center;height:100%;opacity:0.7;">
                Loading route map...
            </div>
        `;

        const data = await this._fetchRoute();

        const route = data.route || [];
        const legs = data.legs || [];

        if (!route.length) return;

        this.el.innerHTML = "";

        const map = (this._map = L.map(this.el, {
            zoomControl: false,
            zoomAnimation: true,
            fadeAnimation: true,
        }).setView([48.5, 2.5], 6));

        /* -----------------------------
           BASE LAYERS
        ----------------------------- */

        const natGeo = L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}",
            { attribution: "© Esri NatGeo", maxZoom: 18 }
        );

        const esri = L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            { attribution: "© Esri", maxZoom: 19 }
        );

        const osm = L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            { attribution: "© OpenStreetMap", maxZoom: 19 }
        );

        const openSeaMap = L.tileLayer(
            "https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
            { opacity: 0.85, attribution: "© OpenSeaMap" }
        );

        /* -----------------------------
           SMART LAYER (FIXED + ACTIVE)
        ----------------------------- */

        const SmartLayer = L.Layer.extend({
            onAdd: (map) => {
                this._map = map;
                this._current = null;

                this._switch = () => {
                    const z = map.getZoom();
                    const target = (z >= 13) ? esri : natGeo;

                    if (this._current !== target) {
                        if (this._current) map.removeLayer(this._current);
                        this._current = target;
                        map.addLayer(this._current);
                    }

                    this._updateZoomDisplay();
                };

                this._switch();
                map.on("zoomend", this._switch);
            },

            onRemove: (map) => {
                map.off("zoomend", this._switch);
                if (this._current) map.removeLayer(this._current);
            }
        });

        const smart = new SmartLayer();
        smart.addTo(map);

        /* -----------------------------
           ROUTE
        ----------------------------- */

        const polyline = L.polyline(route, {
            color: "#1f6feb",
            weight: 5,
            opacity: 0.9,
        }).addTo(map);

        this._routeBounds = polyline.getBounds();

        map.fitBounds(this._routeBounds, { padding: [20, 20] });

        /* -----------------------------
           SAFE LABELS
        ----------------------------- */

        const placements = [
            { dir: "top", offset: [0, -10] },
            { dir: "bottom", offset: [0, 10] },
            { dir: "left", offset: [-10, 0] },
            { dir: "right", offset: [10, 0] },
        ];

        const getSafePlacement = (latlng, preferred) => {
            const b = map.getBounds();

            if (preferred.dir === "top" && latlng[0] > b.getNorth() - 0.2) return placements[1];
            if (preferred.dir === "bottom" && latlng[0] < b.getSouth() + 0.2) return placements[0];
            if (preferred.dir === "left" && latlng[1] < b.getWest() + 0.2) return placements[3];
            if (preferred.dir === "right" && latlng[1] > b.getEast() + 0.2) return placements[2];

            return preferred;
        };

        legs.forEach((leg, i) => {
            const base = placements[i % placements.length];
            const latlng = [leg.lat, leg.lng];
            const p = getSafePlacement(latlng, base);

            L.marker(latlng)
                .addTo(map)
                .bindTooltip(
                    `<b>${leg.name}</b><br>${leg.distance || 0} nm`,
                    {
                        direction: p.dir,
                        offset: p.offset,
                        opacity: 0.95,
                        sticky: true,
                    }
                );
        });

        /* -----------------------------
           CONTROLS
        ----------------------------- */

        const HomeZoomControl = L.Control.extend({
            options: { position: "topleft" },

            onAdd: (map) => {
                const container = L.DomUtil.create("div");
                container.style.display = "flex";
                container.style.flexDirection = "column";
                container.style.gap = "6px";

                const home = L.DomUtil.create("div", "leaflet-bar", container);
                home.innerHTML = "<i class='fa fa-home fa-lg'></i>";
                home.title = "Fit route";

                home.style =
                    "width:34px;height:34px;background:white;display:flex;align-items:center;justify-content:center;cursor:pointer;";

                home.onclick = () => {
                    map.fitBounds(this._routeBounds, { padding: [20, 20] });
                };

                return container;
            },
        });

        map.addControl(new HomeZoomControl());
        L.control.zoom({ position: "topleft" }).addTo(map);

        /* -----------------------------
           LAYER CONTROL (FIXED)
        ----------------------------- */

        L.control.layers(
            {
                "Smart": smart,
                "Satellite": esri,
                "OpenStreetMap": osm,
            },
            {
                "OpenSeaMap": openSeaMap,
            },
            { position: "topright" }
        ).addTo(map);

        /* -----------------------------
           FULLSCREEN
        ----------------------------- */

        const FullscreenControl = L.Control.extend({
            options: { position: "topright" },

            onAdd: () => {
                const el = L.DomUtil.create("div", "leaflet-bar");

                el.innerHTML = "⛶";
                el.title = "Fullscreen";

                el.style =
                    "width:34px;height:34px;background:white;display:flex;align-items:center;justify-content:center;cursor:pointer;margin-bottom:6px;";

                el.onclick = () => {
                    const container = map.getContainer();

                    if (!document.fullscreenElement) {
                        container.requestFullscreen?.();
                    } else {
                        document.exitFullscreen?.();
                    }

                    setTimeout(() => map.invalidateSize(), 200);
                };

                return el;
            },
        });

        map.addControl(new FullscreenControl());

        /* -----------------------------
           ZOOM DISPLAY
        ----------------------------- */

        const ZoomDisplay = L.Control.extend({
            options: { position: "topleft" },

            onAdd: () => {
                const el = L.DomUtil.create("div");

                el.style =
                    "background:white;padding:4px 8px;font-size:12px;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,0.2);margin-top:6px;";

                this._zoomDisplay = el;
                this._updateZoomDisplay();

                return el;
            },
        });

        map.addControl(new ZoomDisplay());
        map.on("zoomend", this._updateZoomDisplay);

        this._initInProgress = false;
    },

    _updateZoomDisplay() {
        if (this._zoomDisplay && this._map) {
            this._zoomDisplay.innerHTML = `${this._map.getZoom()}`;
        }
    },

    async _fetchRoute() {
        const response = await fetch(`/event/${this.eventId}/routejson`, {
            headers: { "Content-Type": "application/json" },
        });

        return await response.json();
    },
});