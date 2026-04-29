import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.EventRouteMap = publicWidget.Widget.extend({
    selector: ".o_event_route_map",

    start() {
        this.eventId = this.el.dataset.eventId;

        this._map = null;
        this._initInProgress = false;

        this._initMap().catch(console.error);
    },

    destroy() {
        if (this._map) {
            this._map.remove();
            this._map = null;
        }
        return this._super(...arguments);
    },

    // Prevent double init
    _ensureNotInitialized() {
        if (this._initInProgress || this._map) {
            return false;
        }
        this._initInProgress = true;
        return true;
    },

    // -----------------------
    // INIT MAP
    // -----------------------

    async _initMap() {
        if (!this._ensureNotInitialized()) return;

        // -----------------------
        // UX: Loading state
        // -----------------------
        this.el.innerHTML = `
            <div class="o_map_loading" style="
                display:flex;
                align-items:center;
                justify-content:center;
                height:100%;
                font-size:14px;
                opacity:0.7;
            ">
                Loading route map...
            </div>
        `;

        const data = await this._fetchRoute();

        const route = data.route || [];
        const legs = data.legs || [];

        if (!route.length) return;

        // Clear loading UI
        this.el.innerHTML = "";

        // -----------------------
        // MAP INIT
        // -----------------------

        const map = (this._map = L.map(this.el, {
            zoomAnimation: true,
            fadeAnimation: true,
        }).setView([48.5, 2.5], 6));

        // Base layer
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap",
            maxZoom: 19,
            detectRetina: true,
        }).addTo(map);

        // OpenSeaMap overlay
        L.tileLayer("https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png", {
            attribution: "© OpenSeaMap",
        }).addTo(map);

        // -----------------------
        // ROUTE POLYLINE
        // -----------------------

        const polyline = L.polyline(route, {
            color: "#1f6feb",
            weight: 5,
            opacity: 0.9,
            lineJoin: "round",
        }).addTo(map);

        // NICE VISUAL: glow effect
        const pane = map.getPane("overlayPane");
        if (pane) {
            pane.style.filter = "drop-shadow(0 0 3px rgba(31,110,235,0.4))";
        }

        // -----------------------
        // UX: fit bounds with padding
        // -----------------------

        map.fitBounds(polyline.getBounds(), {
            padding: [20, 20],
        });

        // -----------------------
        // LEG TOOLTIPS
        // -----------------------

        legs.forEach((leg) => {
            L.marker([leg.lat, leg.lng])
                .addTo(map)
                .bindTooltip(
                    `
                    <div style="min-width:140px;">
                        <div><b>${leg.name}</b></div>
                        <div style="display:flex">
                            <span style="margin-left:auto;">${leg.distance || 0} nm</span>
                        </div>
                    </div>
                    `,
                    {
                        direction: "top",
                        opacity: 0.9,
                        sticky: true,
                        offset: [0, -5],
                    }
                );
        });

        this._initInProgress = false;
    },

    // -----------------------
    // DATA
    // -----------------------

    async _fetchRoute() {
        const response = await fetch(`/event/${this.eventId}/routejson`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });

        return await response.json();
    },
});