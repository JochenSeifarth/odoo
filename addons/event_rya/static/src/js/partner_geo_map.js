/** @odoo-module **/

import { loadCSS, loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onWillStart, onWillUnmount, useEffect, useRef, xml } from "@odoo/owl";

const LEAFLET_CSS_URL = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
const LEAFLET_JS_URL = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
const DEFAULT_CENTER = [20, 0];
const DEFAULT_ZOOM = 2;
const FOCUSED_ZOOM = 13;

function asCoordinate(value) {
    return typeof value === "number" && Number.isFinite(value) ? value : null;
}

class PartnerGeoMap extends Component {
    static template = xml`
        <div class="o_partner_geo_map">
            <div t-ref="map" class="o_partner_geo_map__canvas"/>
        </div>
    `;
    static props = { ...standardFieldProps };

    setup() {
        this.mapRef = useRef("map");
        this.map = null;
        this.marker = null;
        this.isFullscreenActive = false;
        this.resizeObserver = null;

        this.onMapClick = this.onMapClick.bind(this);
        this.onMarkerDragEnd = this.onMarkerDragEnd.bind(this);
        this.onFullscreenChange = this.onFullscreenChange.bind(this);

        onWillStart(async () => {
            await Promise.all([loadCSS(LEAFLET_CSS_URL), loadJS(LEAFLET_JS_URL)]);
        });

        useEffect(
            (el, lat, lng, readonly) => {
                if (!el) {
                    return;
                }
                if (!this.map) {
                    this.initMap();
                    this.observeMapVisibility();
                }
                this.syncMarker(lat, lng, readonly);
            },
            () => [this.mapRef.el, this.latitude, this.longitude, this.props.readonly]
        );

        onWillUnmount(() => this.destroyMap());
    }

    get latitude() {
        return asCoordinate(this.props.record.data.partner_latitude);
    }

    get longitude() {
        return asCoordinate(this.props.record.data.partner_longitude);
    }

    get hasCoordinates() {
        return this.latitude !== null && this.longitude !== null;
    }

    initMap() {
        const Leaflet = window.L;
        const center = this.hasCoordinates ? [this.latitude, this.longitude] : DEFAULT_CENTER;
        const zoom = this.hasCoordinates ? FOCUSED_ZOOM : DEFAULT_ZOOM;

        this.map = Leaflet.map(this.mapRef.el, {
            zoomControl: false,
        }).setView(center, zoom);

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
        osm.addTo(this.map);

        L.control.layers(
            {
                "Satellite": esri,
                "OpenStreetMap": osm,
            },
            {
                "OpenSeaMap": openSeaMap,
            },
            { position: "topright" }
        ).addTo(this.map);

        this.addHomeControl();
        Leaflet.control.zoom({ position: "topleft" }).addTo(this.map);
        this.addFullscreenControl();
        document.addEventListener("fullscreenchange", this.onFullscreenChange);
        this.map.on("click", this.onMapClick);
        this.map.whenReady(() => this.map.invalidateSize());
    }

    addHomeControl() {
        const Leaflet = window.L;
        const HomeControl = Leaflet.Control.extend({
            options: { position: "topleft" },

            onAdd: () => {
                const container = Leaflet.DomUtil.create("div");

                container.style.display = "flex";
                container.style.flexDirection = "column";
                container.style.gap = "6px";
                Leaflet.DomEvent.disableClickPropagation(container);
                Leaflet.DomEvent.disableScrollPropagation(container);

                const home = Leaflet.DomUtil.create("div", "leaflet-bar", container);

                home.innerHTML = "<i class='fa fa-home fa-lg'></i>";
                home.title = _t("Center on marker");
                home.setAttribute("role", "button");
                home.style =
                    "width:34px;height:34px;background:white;display:flex;align-items:center;justify-content:center;cursor:pointer;";

                Leaflet.DomEvent.on(home, "click", (event) => {
                    Leaflet.DomEvent.stop(event);
                    this.centerOnMarker();
                });

                return container;
            },
        });

        this.map.addControl(new HomeControl());
    }

    addFullscreenControl() {
        const Leaflet = window.L;
        const FullscreenControl = Leaflet.Control.extend({
            options: { position: "topright" },

            onAdd: () => {
                const el = Leaflet.DomUtil.create("div", "leaflet-bar");

                el.innerHTML = "⛶";
                el.title = _t("Fullscreen");
                el.setAttribute("role", "button");
                el.style =
                    "width:34px;height:34px;background:white;display:flex;align-items:center;justify-content:center;cursor:pointer;margin-bottom:6px;";
                Leaflet.DomEvent.disableClickPropagation(el);
                Leaflet.DomEvent.disableScrollPropagation(el);

                Leaflet.DomEvent.on(el, "click", (event) => {
                    Leaflet.DomEvent.stop(event);
                    this.toggleFullscreen();
                    setTimeout(() => this.refreshMapLayout(), 200);
                });

                return el;
            },
        });

        this.map.addControl(new FullscreenControl());
    }

    observeMapVisibility() {
        if (!window.ResizeObserver || !this.mapRef.el) {
            return;
        }
        this.resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
                    this.map?.invalidateSize();
                }
            }
        });
        this.resizeObserver.observe(this.mapRef.el);
    }

    getFullscreenTarget() {
        return this.map?.getContainer() || this.mapRef.el;
    }

    ensureMarker(lat, lng, readonly) {
        const Leaflet = window.L;
        if (!this.marker) {
            this.marker = Leaflet.marker([lat, lng], { draggable: !readonly }).addTo(this.map);
            this.marker.on("dragend", this.onMarkerDragEnd);
            return;
        }
        this.marker.setLatLng([lat, lng]);
        if (readonly) {
            this.marker.dragging?.disable();
        } else {
            this.marker.dragging?.enable();
        }
    }

    syncMarker(lat, lng, readonly) {
        if (!this.map) {
            return;
        }

        if (lat === null || lng === null) {
            if (this.marker) {
                this.marker.off("dragend", this.onMarkerDragEnd);
                this.map.removeLayer(this.marker);
                this.marker = null;
            }
            this.map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
            this.map.invalidateSize();
            return;
        }

        this.ensureMarker(lat, lng, readonly);

        const currentCenter = this.map.getCenter();
        const hasMoved =
            Math.abs(currentCenter.lat - lat) > 0.000001 || Math.abs(currentCenter.lng - lng) > 0.000001;
        if (hasMoved) {
            this.map.setView([lat, lng], Math.max(this.map.getZoom(), FOCUSED_ZOOM));
        }
        this.map.invalidateSize();
    }

    centerOnMarker(options = {}) {
        if (!this.map || !this.marker) {
            return;
        }
        const { lat, lng } = this.marker.getLatLng();
        this.map.setView([lat, lng], Math.max(this.map.getZoom(), FOCUSED_ZOOM), options);
    }

    refreshMapLayout({ centerOnMarker = false } = {}) {
        if (!this.map) {
            return;
        }
        const center = this.map.getCenter();
        const zoom = this.map.getZoom();
        const markerLatLng = this.marker?.getLatLng();

        requestAnimationFrame(() => {
            this.map?.invalidateSize({ pan: false, animate: false });
            if (!this.map) {
                return;
            }
            if (markerLatLng && this.marker) {
                this.marker.setLatLng(markerLatLng);
            }
            if (centerOnMarker && markerLatLng) {
                this.centerOnMarker({ animate: false });
            } else {
                this.map.setView(center, zoom, { animate: false });
            }
        });
    }

    async toggleFullscreen() {
        const target = this.getFullscreenTarget();
        if (!target) {
            return;
        }

        if (document.fullscreenElement === target) {
            await document.exitFullscreen?.();
            return;
        }

        if (!document.fullscreenElement) {
            await target.requestFullscreen?.();
        }
    }

    onFullscreenChange() {
        const target = this.getFullscreenTarget();
        if (!target) {
            return;
        }
        const isFullscreen = document.fullscreenElement === target;
        const wasFullscreen = this.isFullscreenActive;

        if (document.fullscreenElement && !isFullscreen) {
            return;
        }

        this.isFullscreenActive = isFullscreen;

        if (!isFullscreen && !wasFullscreen) {
            return;
        }

        this.refreshMapLayout({ centerOnMarker: wasFullscreen && !isFullscreen });
    }

    onMapClick(event) {
        if (this.props.readonly) {
            return;
        }
        const { lat, lng } = event.latlng;
        this.updateCoords(lat, lng);
    }

    onMarkerDragEnd(event) {
        const { lat, lng } = event.target.getLatLng();
        this.updateCoords(lat, lng);
    }

    updateCoords(lat, lng) {
        this.props.record.update({
            partner_latitude: lat,
            partner_longitude: lng,
        });
    }

    destroyMap() {
        document.removeEventListener("fullscreenchange", this.onFullscreenChange);
        this.isFullscreenActive = false;
        this.resizeObserver?.disconnect();
        this.resizeObserver = null;

        if (this.marker) {
            this.marker.off("dragend", this.onMarkerDragEnd);
            this.marker = null;
        }

        if (this.map) {
            this.map.off("click", this.onMapClick);
            this.map.remove();
            this.map = null;
        }
    }
}

export const partnerGeoMapField = {
    component: PartnerGeoMap,
    displayName: _t("Partner geo map"),
    supportedTypes: ["float"],
};

registry.category("fields").add("partner_geo_map", partnerGeoMapField);
